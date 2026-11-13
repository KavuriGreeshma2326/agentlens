"""Mock agent - produces realistic, reproducible agent traces without an LLM.

The same (task, agent_version) always produces the same trace, so results
can be compared between agent versions and tests stay stable.

The agent fails in four distinct ways on purpose. The failure type is NOT
stored anywhere: the Day 4 diagnosis has to work it out from the steps alone,
exactly like a real diagnosis tool would.
"""

import random
from dataclasses import dataclass

COST_PER_TOKEN = 0.000002  # USD per token ($2 per million tokens)

FAILURE_MODES = ("loop", "wrong_tool", "gave_up", "bad_output")

# Chance that a run passes. Newer versions are better, easy tasks are easier.
_BASE_PASS_RATE = {"mock-v1": 0.5, "mock-v2": 0.75}
_DEFAULT_PASS_RATE = 0.6
_DIFFICULTY_ADJUSTMENT = {"easy": 0.15, "medium": 0.0, "hard": -0.2}

# (min, max) per step type
_LATENCY_MS = {
    "thought": (300, 1500),
    "tool_call": (50, 300),
    "tool_result": (100, 2000),
    "final": (400, 1800),
}
_TOKENS = {
    "thought": (60, 250),
    "tool_call": (30, 120),
    "tool_result": (80, 400),
    "final": (40, 300),
}

_WRONG_ANSWER = "I believe the answer is 42."


@dataclass(frozen=True)
class MockStep:
    step_type: str
    content: str
    latency_ms: int
    tokens: int


@dataclass(frozen=True)
class MockRun:
    steps: list[MockStep]
    passed: bool
    failure_mode: str | None  # only for tests; never saved to the database


def _step(rng: random.Random, step_type: str, content: str) -> MockStep:
    return MockStep(
        step_type=step_type,
        content=content,
        latency_ms=rng.randint(*_LATENCY_MS[step_type]),
        tokens=rng.randint(*_TOKENS[step_type]),
    )


def _work_cycle(rng: random.Random, task_name: str) -> list[MockStep]:
    """One normal unit of work: think, call a tool, read the result."""
    tool = rng.choice(["search", "read_file", "run_tests"])
    return [
        _step(rng, "thought", f"I should use {tool} to make progress on: {task_name}"),
        _step(rng, "tool_call", f'{tool}(input="{task_name}")'),
        _step(rng, "tool_result", f"{tool} returned useful information for: {task_name}"),
    ]


def _passing_steps(rng, task_name, expected_output) -> list[MockStep]:
    steps: list[MockStep] = []
    for _ in range(rng.randint(1, 2)):
        steps += _work_cycle(rng, task_name)
    answer = expected_output or "Task completed successfully."
    steps.append(_step(rng, "final", answer))
    return steps


def _loop_steps(rng, task_name, expected_output) -> list[MockStep]:
    """The agent repeats the exact same tool call until it hits a step limit."""
    call = f'search(input="{task_name}")'
    steps = [_step(rng, "thought", f"I will search for: {task_name}")]
    for _ in range(3):
        steps.append(_step(rng, "tool_call", call))
        steps.append(_step(rng, "tool_result", "search returned no new information"))
    steps.append(_step(rng, "final", "Stopped: step limit reached without an answer."))
    return steps


def _wrong_tool_steps(rng, task_name, expected_output) -> list[MockStep]:
    """The agent picks a tool that cannot do the job and gets an error."""
    return [
        _step(rng, "thought", f"I need to read the source file to solve: {task_name}"),
        _step(rng, "tool_call", 'calculator(input="read the source file")'),
        _step(rng, "tool_result", "Error: calculator cannot read files"),
        _step(rng, "thought", "That did not work, so I will answer from what I already know."),
        _step(rng, "final", _WRONG_ANSWER),
    ]


def _gave_up_steps(rng, task_name, expected_output) -> list[MockStep]:
    """The agent finds nothing and ends early with no real answer."""
    return [
        _step(rng, "thought", f"I will search for: {task_name}"),
        _step(rng, "tool_call", f'search(input="{task_name}")'),
        _step(rng, "tool_result", "search found no results"),
        _step(
            rng,
            "final",
            "I could not find enough information, so I cannot complete this task.",
        ),
    ]


def _bad_output_steps(rng, task_name, expected_output) -> list[MockStep]:
    """The agent works normally but finishes with the wrong answer."""
    steps: list[MockStep] = []
    for _ in range(rng.randint(1, 2)):
        steps += _work_cycle(rng, task_name)
    steps.append(_step(rng, "final", _WRONG_ANSWER))
    return steps


_FAILURE_BUILDERS = {
    "loop": _loop_steps,
    "wrong_tool": _wrong_tool_steps,
    "gave_up": _gave_up_steps,
    "bad_output": _bad_output_steps,
}


def generate_run(
    *,
    task_id: int,
    task_name: str,
    expected_output: str | None,
    difficulty: str,
    agent_version: str,
    force_failure: str | None = None,
) -> MockRun:
    """Produce the full trace for one run.

    ``force_failure`` exists for tests: it forces a specific failure mode.
    """
    if force_failure is not None and force_failure not in FAILURE_MODES:
        raise ValueError(f"Unknown failure mode: {force_failure}")

    # A string seed is hashed the same way on every machine, so the trace is
    # identical across runs, processes and computers.
    rng = random.Random(f"{task_id}:{agent_version}")

    pass_rate = _BASE_PASS_RATE.get(agent_version, _DEFAULT_PASS_RATE)
    pass_rate += _DIFFICULTY_ADJUSTMENT.get(difficulty, 0.0)

    # Both draws always happen, in this order, so forcing a failure mode
    # never changes the random numbers used for the rest of the trace.
    roll = rng.random()
    picked_mode = rng.choice(FAILURE_MODES)

    passed = force_failure is None and roll < pass_rate
    if passed:
        steps = _passing_steps(rng, task_name, expected_output)
        return MockRun(steps=steps, passed=True, failure_mode=None)

    mode = force_failure or picked_mode
    steps = _FAILURE_BUILDERS[mode](rng, task_name, expected_output)
    return MockRun(steps=steps, passed=False, failure_mode=mode)