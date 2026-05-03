"""
SafetyNode — response guardrail for Pulse.

Sits at the end of every execution path (listener → safety → END,
analyst → safety → END). Pattern-matches the agent's response for:

  1. Definitive diagnostic claims  ("you have X", "this is definitely Y")
  2. Anti-escalation overrides     ("you don't need a doctor", "skip the ER")
  3. Dosage / prescription advice  ("take 800mg of X")

If any pattern fires, the response is amended with a clear disclaimer.
This is a lightweight, zero-latency guardrail — no LLM call required.

A production system would layer this with a separate evaluator LLM call
for edge cases. For this scope, pattern matching covers the highest-risk
failure modes.
"""
from __future__ import annotations

import re

from graph.state import HealthState

# Patterns that indicate a response is making a definitive medical claim
_DANGEROUS_PATTERNS = [
    r"\byou (definitely |certainly |clearly )?(have|has|are suffering from)\b",
    r"\bdiagnos(ed|is|tic)\b",
    r"\bthis is (definitely|certainly|clearly|100%)\b",
    r"\b(don'?t|do not|no need to) (see|visit|go to|consult) (a |the )?(doctor|physician|er|emergency|urgent care)\b",
    r"\byou (don'?t|do not) need (medical|a doctor|a physician|care)\b",
    r"\btake \d+\s?mg\b",
    r"\bprescrib",
]

_DISCLAIMER = (
    "\n\n---\n*Pulse provides pattern-based information, not medical advice. "
    "If you're concerned, consult a healthcare provider — this summary can help them understand your history faster.*"
)


def safety_node(state: HealthState) -> HealthState:
    """
    Append a safety disclaimer if the response contains diagnostic language.
    Pass-through otherwise — no latency added for clean responses.
    """
    response = state.get("response", "")
    if not response:
        return state

    flagged = any(re.search(p, response, flags=re.IGNORECASE) for p in _DANGEROUS_PATTERNS)

    if flagged and _DISCLAIMER not in response:
        response = response + _DISCLAIMER

    logs = list(state.get("status_logs", []))
    logs.append(f"SafetyNode: {'flagged + disclaimer appended' if flagged else 'clean'}")

    return {**state, "response": response, "status_logs": logs}
