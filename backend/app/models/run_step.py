"""RunStep ORM model — one atomic step within a Run (the core diagnosis unit)."""

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class RunStep(Base):
    """A single observable step produced by an agent during a Run.

    This is the primary unit of diagnosis — when a run fails, we inspect
    individual steps to find where the agent went wrong.

    Columns
    -------
    id          : surrogate primary key
    run_id      : FK → runs.id
    step_number : ordering index (1-based)
    description : human-readable label for the step
    status      : pending | running | completed | failed
    output      : raw text output / tool call result for this step
    created_at  : UTC timestamp
    """

    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.id"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
