"""Authentication configuration constants."""

from __future__ import annotations

AUTH_EXEMPT_PATHS: tuple[str, ...] = (
    "/api/auth/login",
    "/api/auth/register",
)


def is_auth_exempt_path(path: str | None) -> bool:
    """Return True when *path* should skip authentication requirements."""

    if not path:
        return False

    normalized = path.rstrip("/") or "/"
    return any(
        normalized == candidate or normalized.startswith(f"{candidate}/")
        for candidate in AUTH_EXEMPT_PATHS
    )

