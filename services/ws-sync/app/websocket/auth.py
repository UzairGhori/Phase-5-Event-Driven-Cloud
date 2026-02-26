# Task: T-A023 — WebSocket JWT validation
# Plan: §2.6

import jwt

from app.config import get_settings

settings = get_settings()


def validate_ws_token(token: str) -> str | None:
    """Validate JWT from WebSocket query parameter.

    Returns user_id if valid, None if invalid.
    Invalid token → close with 4001.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None
