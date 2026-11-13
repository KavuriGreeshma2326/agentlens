"""Unit tests for the mock agent (pure functions, no database)."""

import pytest

from app.agent.mock_agent import FAILURE_MODES, generate_run

_STEP_TYPES = {"thought", "tool_call", "tool_result", "final"}
_EXPECTED = "The expected answer"


def _run(task_id=1, version="mock-v1", difficulty="medium", force=None):
    return generate_run(
        task_id=task_id,
        task_name="Summarise a document",
        expected_output=_EXPECTED,
        difficulty=difficulty,
        agent_version=version,
        force_failure=force,
    )


def test_same_inputs_give_identical_trace():
    assert _run(task_id=7) == _run(task_id=7)


def test_step_count_is_between_4_and_8_for_every_outcome():
    for task_id in range(1, 41):
        for version in ("mock-v1", "mock-v2"):
            assert 4 <= len(_run(task_id=task_id, version=version).steps) <= 8
    for mode in FAILURE_MODES:
        assert 4 <= len(_run(force=mode).steps) <= 8


def test_every_trace_ends_with_a_final_step_and_uses_valid_types():
    for task_id in range(1, 41):
        steps = _run(task_id=task_id).steps
        assert steps[-1].step_type == "final"
        assert {s.step_type for s in steps} <= _STEP_TYPES


def test_latency_and_tokens_are_positive():
    for step in _run().steps:
        assert step.latency_ms > 0
        assert step.tokens > 0


def test_passed_run_ends_with_the_expected_output():
    passed = [r for r in (_run(task_id=i) for i in range(1, 41)) if r.passed]
    assert passed, "expected at least one passing run among 40 tasks"
    for run in passed:
        assert run.failure_mode is None
        assert run.steps[-1].content == _EXPECTED


def test_failed_run_has_a_failure_mode_and_a_wrong_final_answer():
    failed = [r for r in (_run(task_id=i) for i in range(1, 41)) if not r.passed]
    assert failed, "expected at least one failing run among 40 tasks"
    for run in failed:
        assert run.failure_mode in FAILURE_MODES
        assert run.steps[-1].content != _EXPECTED


def test_loop_mode_repeats_the_same_tool_call_three_times():
    steps = _run(force="loop").steps
    calls = [s.content for s in steps if s.step_type == "tool_call"]
    assert len(calls) >= 3
    assert len(set(calls)) == 1


def test_wrong_tool_mode_produces_a_tool_error():
    steps = _run(force="wrong_tool").steps
    assert any(
        s.step_type == "tool_result" and s.content.startswith("Error:") for s in steps
    )


def test_gave_up_mode_ends_early_without_an_answer():
    steps = _run(force="gave_up").steps
    assert len(steps) == 4
    assert "cannot complete" in steps[-1].content


def test_bad_output_mode_finishes_with_a_wrong_answer():
    steps = _run(force="bad_output").steps
    assert steps[-1].step_type == "final"
    assert steps[-1].content != _EXPECTED


def test_forced_failure_is_never_a_pass():
    for mode in FAILURE_MODES:
        run = _run(force=mode)
        assert run.passed is False
        assert run.failure_mode == mode


def test_unknown_failure_mode_raises():
    with pytest.raises(ValueError):
        _run(force="explode")


def test_newer_version_passes_more_often():
    def passes(version):
        return sum(_run(task_id=i, version=version).passed for i in range(1, 301))

    assert passes("mock-v2") > passes("mock-v1")


def test_easy_tasks_pass_more_often_than_hard_ones():
    def passes(difficulty):
        return sum(_run(task_id=i, difficulty=difficulty).passed for i in range(1, 301))

    assert passes("easy") > passes("hard")