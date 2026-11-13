"""Tests for starting runs and reading them back, including ownership."""

import pytest

from app.agent.mock_agent import COST_PER_TOKEN

_PASSWORD = "s3cr3t!"
_EXPECTED = "A short summary"


def _headers(client, email):
    """Register a user and return an Authorization header for them."""
    resp = client.post("/auth/register", json={"email": email, "password": _PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_task(client, headers, **overrides):
    body = {
        "name": "Summarise a document",
        "expected_output": _EXPECTED,
        "difficulty": "medium",
    }
    body.update(overrides)
    return client.post("/tasks", json=body, headers=headers).json()["id"]


def _start(client, headers, task_id, **body):
    return client.post(f"/tasks/{task_id}/runs", json=body, headers=headers)


def _finished_run(client, headers, task_id, **body):
    """Start a run and read it back.

    The test client waits for background tasks, so the run is already
    finished by the time the POST returns.
    """
    run_id = _start(client, headers, task_id, **body).json()["id"]
    return client.get(f"/runs/{run_id}", headers=headers).json()


def _find_run(client, headers, wanted_status, difficulty, version):
    """Try up to 30 tasks until a run ends with ``wanted_status``."""
    for _ in range(30):
        task_id = _make_task(client, headers, difficulty=difficulty)
        run = _finished_run(client, headers, task_id, agent_version=version)
        if run["status"] == wanted_status:
            return run
    return None


# -- Starting a run ---------------------------------------------------------


def test_start_run_returns_202_and_a_queued_run(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    resp = _start(client, h, task_id)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "queued"
    assert data["task_id"] == task_id
    assert data["agent_version"] == "mock-v1"


def test_start_run_without_a_body_uses_the_default_version(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    resp = client.post(f"/tasks/{task_id}/runs", headers=h)
    assert resp.status_code == 202
    assert resp.json()["agent_version"] == "mock-v1"


def test_start_run_stores_the_requested_agent_version(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    resp = _start(client, h, task_id, agent_version="mock-v2")
    assert resp.json()["agent_version"] == "mock-v2"


def test_start_run_with_empty_agent_version_returns_422(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    assert _start(client, h, task_id, agent_version="").status_code == 422


# -- Reading a finished run -------------------------------------------------


def test_finished_run_is_passed_or_failed_with_ordered_steps(client):
    h = _headers(client, "a@example.com")
    run = _finished_run(client, h, _make_task(client, h))
    assert run["status"] in ("passed", "failed")
    assert run["completed_at"] is not None
    steps = run["steps"]
    assert 4 <= len(steps) <= 8
    assert [s["step_number"] for s in steps] == list(range(1, len(steps) + 1))
    assert steps[-1]["step_type"] == "final"


def test_run_totals_match_the_steps(client):
    h = _headers(client, "a@example.com")
    run = _finished_run(client, h, _make_task(client, h))
    steps = run["steps"]
    assert run["total_latency_ms"] == sum(s["latency_ms"] for s in steps)
    expected_cost = sum(s["tokens"] for s in steps) * COST_PER_TOKEN
    assert run["total_cost"] == pytest.approx(expected_cost)


def test_same_task_and_version_give_the_same_trace(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    first = _finished_run(client, h, task_id)
    second = _finished_run(client, h, task_id)
    assert first["id"] != second["id"]
    assert first["status"] == second["status"]
    trace_1 = [(s["step_type"], s["content"]) for s in first["steps"]]
    trace_2 = [(s["step_type"], s["content"]) for s in second["steps"]]
    assert trace_1 == trace_2


def test_passed_run_ends_with_the_expected_output(client):
    h = _headers(client, "a@example.com")
    run = _find_run(client, h, "passed", difficulty="easy", version="mock-v2")
    assert run is not None, "no passing run found in 30 tasks"
    assert run["steps"][-1]["content"] == _EXPECTED


def test_failed_run_does_not_end_with_the_expected_output(client):
    h = _headers(client, "a@example.com")
    run = _find_run(client, h, "failed", difficulty="hard", version="mock-v1")
    assert run is not None, "no failing run found in 30 tasks"
    assert run["steps"][-1]["content"] != _EXPECTED


# -- Ownership and errors ---------------------------------------------------


def test_cannot_start_a_run_on_someone_elses_task(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    task_id = _make_task(client, a)
    assert _start(client, b, task_id).status_code == 404


def test_start_run_on_missing_task_returns_404(client):
    h = _headers(client, "a@example.com")
    assert _start(client, h, 9999).status_code == 404


def test_start_run_without_token_returns_401(client):
    assert client.post("/tasks/1/runs").status_code == 401


def test_other_user_cannot_read_a_run(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    run_id = _start(client, a, _make_task(client, a)).json()["id"]
    assert client.get(f"/runs/{run_id}", headers=b).status_code == 404
    assert client.get(f"/runs/{run_id}", headers=a).status_code == 200


def test_get_missing_run_returns_404(client):
    h = _headers(client, "a@example.com")
    assert client.get("/runs/9999", headers=h).status_code == 404


def test_get_run_without_token_returns_401(client):
    assert client.get("/runs/1").status_code == 401


def test_task_with_runs_cannot_be_deleted(client):
    h = _headers(client, "a@example.com")
    task_id = _make_task(client, h)
    _start(client, h, task_id)
    assert client.delete(f"/tasks/{task_id}", headers=h).status_code == 409
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 200