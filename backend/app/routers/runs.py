"""Run router - start a run for a task, and read a run with its steps."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agent.runner import execute_run
from app.database import SessionLocal, get_db
from app.dependencies import get_current_user
from app.models.run import Run
from app.models.run_step import RunStep
from app.models.task import Task
from app.models.user import User
from app.schemas.run import RunCreate, RunDetailResponse, RunResponse, RunStepResponse

router = APIRouter(tags=["runs"])


def get_session_factory():
    """Dependency: the factory background tasks use to open their own session.

    Tests override this so background work uses the test database.
    """
    return SessionLocal


@router.post(
    "/tasks/{task_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a run",
)
def create_run(
    task_id: int,
    background_tasks: BackgroundTasks,
    payload: RunCreate | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_factory=Depends(get_session_factory),
) -> Run:
    """Create a queued run and execute the mock agent in the background.

    Returns 202 Accepted straight away. Read the result with GET /runs/{id}.
    """
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.created_by == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    agent_version = payload.agent_version if payload else "mock-v1"
    run = Run(task_id=task.id, agent_version=agent_version, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(execute_run, session_factory, run.id)
    return run


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponse,
    summary="Get a run with its steps",
)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunDetailResponse:
    """Return a run and all its steps. Only the task's owner can read it.

    A run owned by someone else gets the same 404 as a run that does not
    exist, so the API never reveals which run ids exist.
    """
    run = (
        db.query(Run)
        .join(Task, Run.task_id == Task.id)
        .filter(Run.id == run_id, Task.created_by == current_user.id)
        .first()
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
        )

    steps = (
        db.query(RunStep)
        .filter(RunStep.run_id == run.id)
        .order_by(RunStep.step_number)
        .all()
    )
    return RunDetailResponse(
        **RunResponse.model_validate(run).model_dump(),
        steps=[RunStepResponse.model_validate(s) for s in steps],
    )

@router.get("/runs", response_model=list[RunResponse], summary="List my runs")
def list_runs(
    task_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Run]:
    """Return the current user's runs, newest first.

    Pass ``?task_id=`` to list only the runs of one task.
    """
    query = (
        db.query(Run)
        .join(Task, Run.task_id == Task.id)
        .filter(Task.created_by == current_user.id)
    )
    if task_id is not None:
        query = query.filter(Run.task_id == task_id)
    return query.order_by(Run.id.desc()).all()