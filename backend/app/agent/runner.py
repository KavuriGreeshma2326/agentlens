"""Executes a run: asks the mock agent for a trace and saves every step."""

import logging
from datetime import datetime, timezone

from app.agent.mock_agent import COST_PER_TOKEN, generate_run
from app.models.run import Run
from app.models.run_step import RunStep
from app.models.task import Task

logger = logging.getLogger(__name__)


def execute_run(session_factory, run_id: int) -> None:
    """Run the mock agent for ``run_id`` and store the result.

    This runs as a background task AFTER the HTTP response was sent, so it
    opens its own database session instead of reusing the request's session.
    """
    db = session_factory()
    try:
        run = db.get(Run, run_id)
        if run is None:
            return
        task = db.get(Task, run.task_id)

        run.status = "running"
        db.commit()

        result = generate_run(
            task_id=task.id,
            task_name=task.name,
            expected_output=task.expected_output,
            difficulty=task.difficulty,
            agent_version=run.agent_version,
        )

        total_latency = 0
        total_tokens = 0
        for number, step in enumerate(result.steps, start=1):
            db.add(
                RunStep(
                    run_id=run_id,
                    step_number=number,
                    step_type=step.step_type,
                    content=step.content,
                    latency_ms=step.latency_ms,
                    tokens=step.tokens,
                )
            )
            db.commit()  # saved one by one, as the agent produces them
            total_latency += step.latency_ms
            total_tokens += step.tokens

        run.total_latency_ms = total_latency
        run.total_cost = round(total_tokens * COST_PER_TOKEN, 6)
        run.status = "passed" if result.passed else "failed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        logger.exception("Run %s crashed", run_id)
        db.rollback()
        crashed = db.get(Run, run_id)
        if crashed is not None:
            crashed.status = "failed"
            crashed.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()