"""Stats router - compare agent versions across the user's finished runs."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.diagnosis import MAIN_LABELS, TraceStep, diagnose
from app.database import get_db
from app.dependencies import get_current_user
from app.models.run import Run
from app.models.run_step import RunStep
from app.models.task import Task
from app.models.user import User
from app.schemas.stats import StatsResponse, VersionStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse, summary="Compare agent versions")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatsResponse:
    """Pass rate, average cost and latency, and failure causes per version.

    Only finished runs (passed or failed) are counted. Each failed run is
    diagnosed from its steps, so the failure counts come from the traces.
    """
    rows = (
        db.query(Run, Task.expected_output)
        .join(Task, Run.task_id == Task.id)
        .filter(
            Task.created_by == current_user.id,
            Run.status.in_(["passed", "failed"]),
        )
        .all()
    )

    # Load the steps of every failed run in one query.
    failed_ids = [run.id for run, _ in rows if run.status == "failed"]
    steps_by_run: dict[int, list[TraceStep]] = {}
    if failed_ids:
        steps = (
            db.query(RunStep)
            .filter(RunStep.run_id.in_(failed_ids))
            .order_by(RunStep.run_id, RunStep.step_number)
            .all()
        )
        for step in steps:
            steps_by_run.setdefault(step.run_id, []).append(
                TraceStep(step.step_number, step.step_type, step.content or "")
            )

    grouped: dict[str, list[tuple[Run, str | None]]] = {}
    for run, expected in rows:
        grouped.setdefault(run.agent_version, []).append((run, expected))

    versions: list[VersionStats] = []
    for version in sorted(grouped):
        items = grouped[version]
        total = len(items)
        passed = sum(1 for run, _ in items if run.status == "passed")

        counts = {label: 0 for label in MAIN_LABELS}
        for run, expected in items:
            if run.status == "failed":
                label = diagnose(steps_by_run.get(run.id, []), expected).label
                counts[label] = counts.get(label, 0) + 1

        versions.append(
            VersionStats(
                agent_version=version,
                runs=total,
                passed=passed,
                failed=total - passed,
                pass_rate=round(passed / total, 4),
                avg_cost=round(sum(run.total_cost for run, _ in items) / total, 6),
                avg_latency_ms=round(
                    sum(run.total_latency_ms for run, _ in items) / total
                ),
                failure_counts=counts,
            )
        )

    return StatsResponse(total_runs=len(rows), versions=versions)