from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .models import AuthAuditLog, User


def get_client_ip(request: HttpRequest) -> str:
    header = request.META.get("HTTP_X_FORWARDED_FOR")
    if header:
        return header.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent(request: HttpRequest) -> str:
    return request.META.get("HTTP_USER_AGENT", "")


def log_event(
    *,
    request: HttpRequest,
    action: AuthAuditLog.Action,
    email: str,
    user: User | None,
    successful: bool,
    metadata: dict[str, Any] | None = None,
) -> None:
    AuthAuditLog.log(
        user=user,
        email=email,
        action=action,
        successful=successful,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata=metadata,
    )


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    first_name = parts[0]
    last_name = " ".join(parts[1:])
    return first_name, last_name
