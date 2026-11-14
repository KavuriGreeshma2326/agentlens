"""Pydantic schemas for the stats endpoint."""

from pydantic import BaseModel


class VersionStats(BaseModel):
    agent_version: str
    runs: int
    passed: int
    failed: int
    pass_rate: float
    avg_cost: float
    avg_latency_ms: float
    failure_counts: dict[str, int]


class StatsResponse(BaseModel):
    total_runs: int
    versions: list[VersionStats]