"""Tests for the diagnosis on GET /runs/{id} and for GET /stats."""

import pytest

from app.agent.mock_agent import FAILURE_MODES

_PASSWORD = "s3cr3t!"
_EXPECTED = "A short summary"


def _headers(client, email):
    resp = client.post("/auth/register", json={"email": email, "password": _PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_task(client, headers, difficulty="medium"):
    body = {
        "name": "Summarise a document",
        "expected_output": _EXPECTED,
        "difficulty": difficulty,
    }
    return client.post("/tasks", json=body, headers=headers).json()["id"]


def _finished_run(client, headers, task_id, version="mock-v1"):
    """Start a run and read it back (background tasks finish before the POST returns)."""
    run_id = client.post(
        f"/tasks/{task_id}/runs", json={"agent_version": version}, headers=headers
    ).json()["id"]
    return client.get(f"/runs/{run_id}", headers=headers).json()


def _find_run(client, headers, wanted, difficulty, version):
    for _ in range(30):
        task_id = _make_task(client, headers, difficulty)
        run = _finished_run(client, headers, task_id, version)
        if run["status"] == wanted:
            return run
    return None


# -- Diagnosis on a single run ----------------------------------------------


def test_failed_run_has_a_diagnosis_with_valid_evidence(client):
    h = _headers(client, "a@example.com")
    run = _find_run(client, h, "failed", "hard", "mock-v1")
    assert run is not None, "no failing run found in 30 tasks"
    diagnosis = run["diagnosis"]
    assert diagnosis["label"] in FAILURE_MODES
    assert diagnosis["summary"]
    assert diagnosis["step_numbers"]
    real_steps = {s["step_number"] for s in run["steps"]}
    assert set(diagnosis["step_numbers"]) <= real_steps


def test_passed_run_has_no_diagnosis(client):
    h = _headers(client, "a@example.com")
    run = _find_run(client, h, "passed", "easy", "mock-v2")
    assert run is not None, "no passing run found in 30 tasks"
    assert run["diagnosis"] is None


# -- Stats --------------------------------------------------------------------


def test_stats_without_token_returns_401(client):
    assert client.get("/stats").status_code == 401


def test_stats_is_empty_without_runs(client):
    h = _headers(client, "a@example.com")
    assert client.get("/stats", headers=h).json() == {
        "total_runs": 0,
        "versions": [],
    }


def test_stats_group_runs_by_agent_version(client):
    h = _headers(client, "a@example.com")
    for _ in range(6):
        task_id = _make_task(client, h, "hard")
        _finished_run(client, h, task_id, "mock-v1")
        _finished_run(client, h, task_id, "mock-v2")

    stats = client.get("/stats", headers=h).json()
    assert stats["total_runs"] == 12
    assert [v["agent_version"] for v in stats["versions"]] == ["mock-v1", "mock-v2"]
    for version in stats["versions"]:
        assert version["runs"] == 6
        assert version["passed"] + version["failed"] == 6
        assert version["pass_rate"] == pytest.approx(version["passed"] / 6, abs=1e-3)
        assert sum(version["failure_counts"].values()) == version["failed"]
        for label in FAILURE_MODES:
            assert label in version["failure_counts"]
        assert version["avg_cost"] > 0
        assert version["avg_latency_ms"] > 0


def test_stats_only_count_the_users_own_runs(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    _finished_run(client, a, _make_task(client, a))
    assert client.get("/stats", headers=b).json()["total_runs"] == 0