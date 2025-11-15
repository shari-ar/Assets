from __future__ import annotations

from typing import Any, Callable

import jwt
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import HttpBearer

from .constants import is_auth_exempt_path
from .models import AuthAuditLog, User
from .tokens import validate_access_token
from .utils import get_client_ip, get_user_agent


class JWTAuth(HttpBearer):
    def __call__(self, request: HttpRequest) -> dict[str, Any]:
        if is_auth_exempt_path(request.path):
            return {}

        auth_value = request.headers.get(self.header)
        token: str | None = None
        if auth_value:
            parts = auth_value.split(" ")
            if parts[0].lower() == self.openapi_scheme and len(parts) > 1:
                token = " ".join(parts[1:]).strip()
        if not token:
            token = request.COOKIES.get("access_token")
        if not token:
            _record_denied(request, None, "Missing bearer token")
            raise HttpError(401, "Authentication credentials were not provided")
        return self.authenticate(request, token)

    def authenticate(self, request: HttpRequest, token: str) -> dict[str, Any]:
        try:
            payload = validate_access_token(token)
        except jwt.ExpiredSignatureError as exc:  # pragma: no cover - library message
            _record_denied(request, None, "Expired signature")
            raise HttpError(401, "Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            _record_denied(request, None, "Invalid token")
            raise HttpError(401, "Invalid authentication token") from exc

        try:
            user = User.objects.get(pk=payload["sub"])
        except User.DoesNotExist as exc:
            _record_denied(request, None, "Unknown user")
            raise HttpError(401, "User not found") from exc

        if not user.is_active:
            _record_denied(request, user, "Inactive user")
            raise HttpError(403, "User account is inactive")

        request.auth = payload
        request.user = user
        return payload


def require_role(role: User.Role) -> Callable[[HttpRequest], User]:
    def dependency(request: HttpRequest) -> User:
        user = getattr(request, "user", None)
        if user is None or not isinstance(user, User):
            _record_denied(request, None, "Missing user context")
            raise HttpError(401, "Authentication required")
        if user.role != role:
            _record_denied(request, user, f"Role {user.role} lacks access")
            raise HttpError(403, "You do not have permission to perform this action")
        return user

    return dependency


def _record_denied(request: HttpRequest, user: User | None, reason: str) -> None:
    AuthAuditLog.log(
        user=user,
        email=user.email if user else "",
        action=AuthAuditLog.Action.ACCESS_DENIED,
        successful=False,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={"reason": reason},
    )
