"""Task router - CRUD for evaluation tasks, scoped to the logged-in user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.run import Run
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(db: Session, task_id: int, user: User) -> Task:
    """Return the task if it belongs to ``user``, otherwise raise 404.

    A task owned by someone else gets the same 404 as a task that does not
    exist, so the API never reveals which task ids exist.
    """
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.created_by == user.id)
        .first()
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = Task(**payload.model_dump(), created_by=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskResponse], summary="List my tasks")
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.created_by == current_user.id)
        .order_by(Task.id)
        .all()
    )


@router.get("/{task_id}", response_model=TaskResponse, summary="Get one task")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return _get_owned_task(db, task_id, current_user)


@router.put("/{task_id}", response_model=TaskResponse, summary="Replace a task")
def update_task(
    task_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = _get_owned_task(db, task_id, current_user)
    for field, value in payload.model_dump().items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = _get_owned_task(db, task_id, current_user)
    # Runs hold the recorded traces, so a task that has runs is protected
    # from deletion instead of silently destroying that history.
    if db.query(Run).filter(Run.task_id == task.id).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task has runs and cannot be deleted",
        )
    db.delete(task)
    db.commit()