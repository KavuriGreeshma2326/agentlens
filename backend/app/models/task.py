"""Task ORM model - an evaluation task that agents run against."""

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Task(Base):
    """An evaluation task (e.g. 'Fix the failing test in this repo').

    Columns
    -------
    id              : surrogate primary key
    name            : short label
    description     : longer natural-language description of the task
    expected_output : what a correct final answer looks like
    difficulty      : easy | medium | hard
    created_by      : FK -> users.id, owner of the task
    created_at      : UTC timestamp
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(
        String, default="medium", server_default="medium", nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )