from __future__ import annotations

from datetime import timedelta
from typing import Any

import jwt
from django.conf import settings
from django.utils import timezone

from .models import User

ALGORITHM = "HS256"


def _expiration(delta: timedelta) -> int:
    expires_at = timezone.now() + delta
    return int(expires_at.timestamp())


def create_access_token(user: User) -> str:
    payload: dict[str, Any] = {
        "sub": str(user.pk),
        "type": "access",
        "role": user.role,
        "email": user.email,
        "exp": _expiration(timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES)),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def validate_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("type") != "access":
        msg = "Invalid access token"
        raise jwt.InvalidTokenError(msg)
    return payload


def build_role_claims(user: User) -> dict[str, Any]:
    return {"role": user.role, "user_id": str(user.pk)}
