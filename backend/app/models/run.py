"""Run ORM model - a single execution of a Task by an agent."""

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Run(Base):
    """One execution of a Task.

    Columns
    -------
    id               : surrogate primary key
    task_id          : FK -> tasks.id
    status           : queued | running | passed | failed
    agent_version    : label of the agent version that produced this run
    total_cost       : sum of step costs (USD)
    total_latency_ms : sum of step latencies
    created_at       : UTC timestamp when the run was created
    completed_at     : UTC timestamp when the run finished (nullable)
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, default="queued", nullable=True)
    agent_version: Mapped[str] = mapped_column(
        String, default="mock-v1", server_default="mock-v1", nullable=False
    )
    total_cost: Mapped[float] = mapped_column(
        Float, default=0.0, server_default=text("0"), nullable=False
    )
    total_latency_ms: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    completed_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )