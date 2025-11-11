import hashlib
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Response

from .dependencies import JWTAuth, require_role
from .models import AuthAuditLog, RefreshToken, User
from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    UserResponse,
)
from .tokens import create_access_token
from .utils import get_client_ip, get_user_agent, log_event, split_full_name

jwt_auth = JWTAuth()
router = Router(tags=["Auth"])


@router.get("status", summary="Authentication service heartbeat")
def auth_status(request) -> dict[str, str]:
    return {"service": "auth", "status": "ok"}


def _access_expiration() -> datetime:
    return timezone.now() + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES)


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    access_expires: datetime,
    refresh_token: str,
    refresh_expires: datetime,
) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        expires=access_expires,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        expires=refresh_expires,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def _user_payload(user: User) -> dict[str, str]:
    return UserResponse(
        id=str(user.pk),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    ).dict(by_alias=True)


@router.post("register", response=UserResponse, summary="Register a new user account")
def register(request, payload: RegisterRequest) -> Response:
    first_name, last_name = split_full_name(payload.full_name)
    first_name = first_name[:150]
    last_name = last_name[:150]
    try:
        validate_password(payload.password)
    except ValidationError as exc:
        log_event(
            request=request,
            action=AuthAuditLog.Action.REGISTER,
            email=payload.email,
            user=None,
            successful=False,
            metadata={"errors": exc.messages},
        )
        raise HttpError(400, {"password": exc.messages}) from exc

    try:
        user = User.objects.create_user(
            email=payload.email,
            password=payload.password,
            first_name=first_name,
            last_name=last_name,
        )
    except IntegrityError as exc:
        log_event(
            request=request,
            action=AuthAuditLog.Action.REGISTER,
            email=payload.email,
            user=None,
            successful=False,
            metadata={"reason": "email_conflict"},
        )
        raise HttpError(400, {"email": ["A user with that email already exists."]}) from exc

    log_event(
        request=request,
        action=AuthAuditLog.Action.REGISTER,
        email=user.email,
        user=user,
        successful=True,
    )

    return Response(_user_payload(user), status=201)


@router.post("login", response=LoginResponse, summary="Authenticate a user and issue tokens")
def login(request, payload: LoginRequest) -> Response:
    user = authenticate(request, email=payload.email, password=payload.password)
    if user is None:
        log_event(
            request=request,
            action=AuthAuditLog.Action.LOGIN,
            email=payload.email,
            user=None,
            successful=False,
            metadata={"reason": "invalid_credentials"},
        )
        raise HttpError(401, "Invalid credentials")

    if not user.is_active:
        log_event(
            request=request,
            action=AuthAuditLog.Action.LOGIN,
            email=user.email,
            user=user,
            successful=False,
            metadata={"reason": "inactive"},
        )
        raise HttpError(403, "User account is inactive")

    access_token = create_access_token(user)
    access_expires = _access_expiration()
    refresh_lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
    refresh_record, refresh_token = RefreshToken.create_for_user(
        user,
        lifetime=refresh_lifetime,
        user_agent=get_user_agent(request),
        ip_address=get_client_ip(request),
    )

    log_event(
        request=request,
        action=AuthAuditLog.Action.LOGIN,
        email=user.email,
        user=user,
        successful=True,
        metadata={"refresh_id": refresh_record.pk},
    )

    response = Response(
        LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_expires,
            role=user.role,
        ).dict(),
        status=200,
    )
    _set_auth_cookies(
        response,
        access_token=access_token,
        access_expires=access_expires,
        refresh_token=refresh_token,
        refresh_expires=refresh_record.expires_at,
    )
    return response


@router.get("me", response=UserResponse, auth=jwt_auth, summary="Return the current authenticated user")
def me(request) -> dict[str, str]:
    user: User = request.user  # type: ignore[assignment]
    return _user_payload(user)


@router.post("refresh", response=RefreshResponse, summary="Refresh access token using a valid refresh token")
def refresh(request) -> Response:
    raw_token = request.COOKIES.get("refresh_token")
    if not raw_token:
        log_event(
            request=request,
            action=AuthAuditLog.Action.REFRESH,
            email="",
            user=None,
            successful=False,
            metadata={"reason": "missing_cookie"},
        )
        raise HttpError(401, "Refresh token missing")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    try:
        token = RefreshToken.objects.select_related("user").get(token_hash=token_hash)
    except RefreshToken.DoesNotExist as exc:
        log_event(
            request=request,
            action=AuthAuditLog.Action.REFRESH,
            email="",
            user=None,
            successful=False,
            metadata={"reason": "unknown_token"},
        )
        raise HttpError(401, "Invalid refresh token") from exc

    if token.revoked or token.expires_at <= timezone.now():
        token.revoke()
        log_event(
            request=request,
            action=AuthAuditLog.Action.REFRESH,
            email=token.user.email,
            user=token.user,
            successful=False,
            metadata={"reason": "expired_or_revoked"},
        )
        raise HttpError(401, "Refresh token expired")

    user = token.user
    if not user.is_active:
        token.revoke()
        log_event(
            request=request,
            action=AuthAuditLog.Action.REFRESH,
            email=user.email,
            user=user,
            successful=False,
            metadata={"reason": "inactive"},
        )
        raise HttpError(403, "User account is inactive")

    token.mark_used()
    token.revoke()

    access_token = create_access_token(user)
    access_expires = _access_expiration()
    refresh_lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
    new_refresh, new_refresh_token = RefreshToken.create_for_user(
        user,
        lifetime=refresh_lifetime,
        user_agent=get_user_agent(request),
        ip_address=get_client_ip(request),
    )

    log_event(
        request=request,
        action=AuthAuditLog.Action.REFRESH,
        email=user.email,
        user=user,
        successful=True,
        metadata={"refresh_id": new_refresh.pk},
    )

    response = Response(
        RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_at=access_expires,
            role=user.role,
        ).dict(),
        status=200,
    )
    _set_auth_cookies(
        response,
        access_token=access_token,
        access_expires=access_expires,
        refresh_token=new_refresh_token,
        refresh_expires=new_refresh.expires_at,
    )
    return response


@router.post("logout", summary="Revoke the active refresh token and clear cookies")
def logout(request) -> Response:
    raw_token = request.COOKIES.get("refresh_token")
    response = Response(None, status=204)
    _clear_auth_cookies(response)

    if not raw_token:
        log_event(
            request=request,
            action=AuthAuditLog.Action.LOGOUT,
            email="",
            user=None,
            successful=True,
            metadata={"reason": "missing_cookie"},
        )
        return response

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = RefreshToken.objects.filter(token_hash=token_hash).first()
    if token:
        token.revoke()
        log_event(
            request=request,
            action=AuthAuditLog.Action.LOGOUT,
            email=token.user.email,
            user=token.user,
            successful=True,
            metadata={"refresh_id": token.pk},
        )
    else:
        log_event(
            request=request,
            action=AuthAuditLog.Action.LOGOUT,
            email="",
            user=None,
            successful=True,
            metadata={"reason": "unknown_token"},
        )

    return response


admin_required = require_role(User.Role.ADMIN)
user_required = require_role(User.Role.USER)
