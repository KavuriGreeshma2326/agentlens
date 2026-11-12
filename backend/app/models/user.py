"""User ORM model."""

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """Represents a registered user of the platform.

    Columns
    -------
    id              : surrogate primary key
    email           : unique login identifier
    hashed_password : bcrypt hash — the plain-text password is never stored
    created_at      : server-side UTC timestamp set on INSERT
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
