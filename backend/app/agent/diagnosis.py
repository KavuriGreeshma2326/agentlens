"""Failure diagnosis: names why a run failed using only its recorded steps.

Nothing here reads the mock agent or any stored failure label. The rules look
at the trace the way a person debugging a real agent would.

Rules run in order and the first match wins:
  1. loop        the same tool call three or more times in a row
  2. wrong_tool  a tool result that starts with "Error:"
  3. gave_up     a final answer that admits the agent could not finish
  4. bad_output  a final answer that differs from the task's expected output
Otherwise the label is "incomplete" (no final step) or "unknown".
"""

from dataclasses import dataclass

LOOP_THRESHOLD = 3
GIVE_UP_PHRASES = ("cannot complete", "could not", "unable to", "i cannot", "i can't")

# These four always appear in the stats, even with a count of zero.
MAIN_LABELS = ("loop", "wrong_tool", "gave_up", "bad_output")


@dataclass(frozen=True)
class TraceStep:
    step_number: int
    step_type: str
    content: str


@dataclass(frozen=True)
class Diagnosis:
    label: str
    summary: str
    step_numbers: list[int]  # the steps that are the evidence


def _find_loop(steps: list[TraceStep]) -> list[int] | None:
    """Return the step numbers of the longest run of identical tool calls."""
    best: list[TraceStep] = []
    streak: list[TraceStep] = []
    for step in steps:
        if step.step_type != "tool_call":
            continue
        if streak and step.content == streak[-1].content:
            streak.append(step)
        else:
            streak = [step]
        if len(streak) > len(best):
            best = streak
    if len(best) >= LOOP_THRESHOLD:
        return [s.step_number for s in best]
    return None


def _find_tool_errors(steps: list[TraceStep]) -> list[int]:
    """Return the failing results and the calls that caused them."""
    by_number = {s.step_number: s for s in steps}
    evidence: list[int] = []
    for step in steps:
        if step.step_type == "tool_result" and step.content.startswith("Error:"):
            previous = by_number.get(step.step_number - 1)
            if previous is not None and previous.step_type == "tool_call":
                evidence.append(previous.step_number)
            evidence.append(step.step_number)
    return evidence


def diagnose(steps: list[TraceStep], expected_output: str | None) -> Diagnosis:
    """Explain why a failed run failed. Call this only for failed runs."""
    loop_steps = _find_loop(steps)
    if loop_steps is not None:
        return Diagnosis(
            label="loop",
            summary=(
                f"The agent made the same tool call {len(loop_steps)} times "
                "in a row without making progress."
            ),
            step_numbers=loop_steps,
        )

    error_steps = _find_tool_errors(steps)
    if error_steps:
        return Diagnosis(
            label="wrong_tool",
            summary=(
                "A tool call failed with an error. This usually means the "
                "agent picked a tool that cannot do the job."
            ),
            step_numbers=error_steps,
        )

    final = steps[-1] if steps and steps[-1].step_type == "final" else None
    if final is None:
        return Diagnosis(
            label="incomplete",
            summary="The run ended without a final answer.",
            step_numbers=[steps[-1].step_number] if steps else [],
        )

    if any(phrase in final.content.lower() for phrase in GIVE_UP_PHRASES):
        return Diagnosis(
            label="gave_up",
            summary="The agent ended by saying it could not complete the task.",
            step_numbers=[final.step_number],
        )

    if expected_output is not None and final.content != expected_output:
        return Diagnosis(
            label="bad_output",
            summary=(
                "The agent finished, but its final answer does not match "
                "the expected output."
            ),
            step_numbers=[final.step_number],
        )

    return Diagnosis(
        label="unknown",
        summary=(
            "The run failed, but no rule matched. Set an expected output on "
            "the task so the answer can be checked."
        ),
        step_numbers=[final.step_number],
    )