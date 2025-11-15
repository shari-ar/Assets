from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone


logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    """Custom manager that uses the email address as the unique identifier."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> "User":
        if not email:
            msg = "The email address must be set"
            raise ValueError(msg)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Application user with a role attribute for RBAC enforcement."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "User"

    email = models.EmailField("email address", unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return self.email

    def get_full_name(self) -> str:
        parts = [self.first_name.strip(), self.last_name.strip()]
        return " ".join(part for part in parts if part).strip()

    @property
    def full_name(self) -> str:
        return self.get_full_name()

    def email_user(self, subject: str, message: str, from_email: str | None = None, **kwargs: Any) -> None:
        send_mail(subject, message, from_email, [self.email], **kwargs)


class RefreshToken(models.Model):
    """Persistent refresh tokens that can be revoked individually."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.CharField(max_length=64, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked"]),
            models.Index(fields=["expires_at"]),
        ]

    @staticmethod
    def build_token() -> tuple[str, str]:
        raw_token = secrets.token_urlsafe(48)
        hashed = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return raw_token, hashed

    @classmethod
    def create_for_user(
        cls,
        user: User,
        *,
        lifetime: timedelta,
        user_agent: str = "",
        ip_address: str = "",
    ) -> tuple["RefreshToken", str]:
        raw_token, token_hash = cls.build_token()
        expires_at = timezone.now() + lifetime
        token = cls.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent[:500],
            ip_address=ip_address[:64],
        )
        return token, raw_token

    def mark_used(self) -> None:
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])

    def revoke(self) -> None:
        if not self.revoked:
            self.revoked = True
            self.save(update_fields=["revoked"])


class AuthAuditLog(models.Model):
    """Audit events for authentication and authorization operations."""

    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        REGISTER = "register", "Register"
        LOGOUT = "logout", "Logout"
        REFRESH = "refresh", "Refresh"
        ACCESS_DENIED = "access_denied", "Access Denied"
        TOKEN_REVOKED = "token_revoked", "Token Revoked"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    action = models.CharField(max_length=32, choices=Action.choices)
    successful = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def log(
        cls,
        *,
        user: User | None,
        email: str,
        action: "AuthAuditLog.Action",
        successful: bool,
        ip_address: str = "",
        user_agent: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "AuthAuditLog | None":
        try:
            return cls.objects.create(
                user=user,
                email=email,
                action=action,
                successful=successful,
                ip_address=ip_address[:64],
                user_agent=user_agent[:500],
                metadata=metadata or {},
            )
        except (ProgrammingError, OperationalError):
            logger.warning(
                "Skipping authentication audit log write because the database table is missing."
            )
            return None
