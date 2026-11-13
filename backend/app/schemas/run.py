"""Pydantic schemas for run endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    """Optional body for starting a run."""

    agent_version: str = Field(default="mock-v1", min_length=1, max_length=50)


class RunStepResponse(BaseModel):
    id: int
    step_number: int
    step_type: str
    content: str | None = None
    latency_ms: int
    tokens: int

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: int
    task_id: int
    status: str | None = None
    agent_version: str
    total_cost: float
    total_latency_ms: int
    created_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class RunDetailResponse(RunResponse):
    """A run together with every recorded step, in order."""

    steps: list[RunStepResponse] = []