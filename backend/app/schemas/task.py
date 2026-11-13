"""Pydantic schemas for task endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]


class TaskCreate(BaseModel):
    """Body for creating or replacing a task."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    expected_output: str | None = None
    difficulty: Difficulty = "medium"


class TaskResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    expected_output: str | None = None
    difficulty: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}