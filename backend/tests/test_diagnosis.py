"""Unit tests for the failure diagnosis (pure functions, no database)."""

import pytest

from app.agent.diagnosis import TraceStep, diagnose
from app.agent.mock_agent import FAILURE_MODES, generate_run

_EXPECTED = "The expected answer"


def _trace(items):
    return [
        TraceStep(number, step_type, content)
        for number, (step_type, content) in enumerate(items, start=1)
    ]


def _mock_trace(run):
    return [
        TraceStep(number, step.step_type, step.content)
        for number, step in enumerate(run.steps, start=1)
    ]


def _generate(task_id=1, version="mock-v1", difficulty="medium", force=None):
    return generate_run(
        task_id=task_id,
        task_name="Summarise a document",
        expected_output=_EXPECTED,
        difficulty=difficulty,
        agent_version=version,
        force_failure=force,
    )


@pytest.mark.parametrize("mode", FAILURE_MODES)
def test_diagnosis_names_each_forced_failure_mode(mode):
    diagnosis = diagnose(_mock_trace(_generate(force=mode)), _EXPECTED)
    assert diagnosis.label == mode
    assert diagnosis.summary
    assert diagnosis.step_numbers


def test_diagnosis_matches_every_failed_mock_run():
    checked = 0
    for task_id in range(1, 101):
        for version in ("mock-v1", "mock-v2"):
            run = _generate(task_id=task_id, version=version, difficulty="hard")
            if run.passed:
                continue
            checked += 1
            assert diagnose(_mock_trace(run), _EXPECTED).label == run.failure_mode
    assert checked > 50


def test_two_identical_calls_are_not_a_loop():
    steps = _trace(
        [
            ("thought", "t"),
            ("tool_call", "search(x)"),
            ("tool_result", "r"),
            ("tool_call", "search(x)"),
            ("tool_result", "r"),
            ("final", "something else"),
        ]
    )
    assert diagnose(steps, _EXPECTED).label == "bad_output"


def test_loop_evidence_lists_the_repeated_calls():
    steps = _trace(
        [
            ("tool_call", "a"),
            ("tool_result", "r"),
            ("tool_call", "a"),
            ("tool_result", "r"),
            ("tool_call", "a"),
            ("tool_result", "r"),
            ("final", "stopped"),
        ]
    )
    diagnosis = diagnose(steps, _EXPECTED)
    assert diagnosis.label == "loop"
    assert diagnosis.step_numbers == [1, 3, 5]


def test_wrong_tool_evidence_includes_the_call_and_the_error():
    steps = _trace(
        [
            ("thought", "t"),
            ("tool_call", "calculator(x)"),
            ("tool_result", "Error: cannot do that"),
            ("final", "42"),
        ]
    )
    diagnosis = diagnose(steps, _EXPECTED)
    assert diagnosis.label == "wrong_tool"
    assert diagnosis.step_numbers == [2, 3]


def test_gave_up_when_the_final_answer_admits_defeat():
    steps = _trace(
        [
            ("tool_call", "search(x)"),
            ("tool_result", "nothing found"),
            ("final", "I could not do this."),
        ]
    )
    assert diagnose(steps, _EXPECTED).label == "gave_up"


def test_bad_output_when_the_final_answer_differs():
    steps = _trace(
        [
            ("tool_call", "search(x)"),
            ("tool_result", "ok"),
            ("final", "something else"),
        ]
    )
    diagnosis = diagnose(steps, _EXPECTED)
    assert diagnosis.label == "bad_output"
    assert diagnosis.step_numbers == [3]


def test_run_without_a_final_step_is_incomplete():
    steps = _trace([("thought", "t"), ("tool_call", "search(x)")])
    assert diagnose(steps, _EXPECTED).label == "incomplete"


def test_empty_trace_is_incomplete():
    assert diagnose([], _EXPECTED).label == "incomplete"


def test_unknown_when_there_is_no_expected_output_to_check():
    steps = _trace(
        [
            ("tool_call", "search(x)"),
            ("tool_result", "ok"),
            ("final", "something"),
        ]
    )
    assert diagnose(steps, None).label == "unknown"