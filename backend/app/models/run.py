"""Run ORM model — a single execution of a Task by an agent."""

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Run(Base):
    """One execution of a Task.

    Columns
    -------
    id           : surrogate primary key
    task_id      : FK → tasks.id
    status       : lifecycle state: pending | running | completed | failed
    created_at   : UTC timestamp when the run was created
    completed_at : UTC timestamp when the run finished (nullable)
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, default="pending", nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    completed_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
