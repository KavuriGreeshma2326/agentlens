"""JWT creation and decoding via python-jose."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encode *data* into a signed JWT.

    The ``exp`` (expiry) claim is added automatically.
    ``sub`` should be a string representation of the user's primary key.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify *token*.

    Returns the payload dict on success, or None if the token is invalid
    or expired (so callers never have to catch JWTError themselves).
    """
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None
