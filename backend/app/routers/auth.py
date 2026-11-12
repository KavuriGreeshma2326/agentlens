"""Authentication router — register, login, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a new user account and return a JWT access token.

    Returns 400 if the email is already registered.
    """
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Login")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate and return a JWT access token.

    Returns 401 for unrecognised email or wrong password.
    Intentionally returns the same error message for both cases to avoid
    leaking whether an email exists in the system (user enumeration).
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Current user")
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile.

    Requires a valid Bearer token in the Authorization header.
    """
    return current_user
