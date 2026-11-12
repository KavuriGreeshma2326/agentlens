"""FastAPI shared dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database import get_db
from app.models.user import User

# tokenUrl tells the OpenAPI UI where to POST credentials to get a token.
# Our login route is at /auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the Bearer JWT, then return the matching User.

    Raises HTTP 401 for:
    - Missing / malformed token
    - Expired token
    - Token whose ``sub`` doesn't map to an existing user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user
