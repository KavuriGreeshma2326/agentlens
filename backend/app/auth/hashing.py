"""Password hashing with bcrypt via passlib."""

from passlib.context import CryptContext

# bcrypt is intentionally slow (adaptive hashing).
# "deprecated='auto'" means older schemes (e.g. sha256_crypt) are
# automatically re-hashed to bcrypt on next login — good for migrations.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return the bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True iff *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)
