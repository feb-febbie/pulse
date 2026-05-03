"""
TriageAgent — pre-flight check node for Pulse.

Sits between the router and the listener/analyst nodes.
Implements the "clarification loop" pattern:

  • For analysis requests with insufficient history → return a gentle
    prompt asking the user to log more entries before pattern analysis.

  • For vague log entries (too short, no health content) → ask a
    specific clarifying question before logging garbage data.

  • Otherwise → pass through state unchanged and let the router's
    next field determine where execution continues.

This demonstrates recursive agent control via conditional edges in
LangGraph: the graph can return to the user without ever reaching
the listener or analyst, keeping data quality high.
"""
from __future__ import annotations

from graph.state import HealthState
from tools.memory_tools import query_history

# Minimum entries before pattern analysis is meaningful
_MIN_ANALYSIS_ENTRIES = 2

# Words that indicate health content in a log entry
_HEALTH_WORDS = {
    "headache", "migraine", "tired", "fatigue", "sleep", "slept", "hours",
    "pain", "nausea", "dizzy", "fever", "sore", "ache", "feel", "feeling",
    "felt", "stomach", "cramp", "bloat", "caffeine", "coffee", "energy",
    "brain", "fog", "eye", "strain", "stress", "anxious", "anxiety",
    "congestion", "cough", "throat", "cold", "flu", "vomit", "diarrhea",
}


def triage_node(state: HealthState) -> HealthState:
    """
    Pre-flight check. Returns state unchanged (pass-through) or short-circuits
    with a clarifying question by setting next='done' and response=<question>.
    """
    intent = state.get("intent", "analyze")
    user_input = state.get("user_input", "").strip()

    # ── Analysis: need enough history to find a pattern ───────────────────────
    if intent in ("analyze", "export"):
        history = query_history(days=30)
        if len(history) < _MIN_ANALYSIS_ENTRIES:
            return {
                **state,
                "next": "done",
                "response": (
                    "I don't have enough history to find a pattern yet — "
                    f"I only have {len(history)} entr{'y' if len(history) == 1 else 'ies'} logged. "
                    "Log a few more days of how you're feeling first, then ask me again. "
                    "Even a quick note like \"felt fine today, slept 7 hours\" helps.\n\n"
                    "Try: *\"Headache today, started at 2pm, slept 5 hours last night.\"*"
                ),
            }

    # ── Log entry: reject entries that are too vague to be useful ─────────────
    elif intent == "log":
        words = set(user_input.lower().split())
        has_health_content = bool(words & _HEALTH_WORDS)
        is_too_short = len(user_input) < 12

        if is_too_short and not has_health_content:
            return {
                **state,
                "next": "done",
                "response": (
                    "Can you tell me a bit more so I can log this properly?\n\n"
                    "For example:\n"
                    "- What symptoms are you feeling?\n"
                    "- How many hours did you sleep last night?\n"
                    "- How severe is it on a scale of 1–10?\n\n"
                    "Even a short note like *\"headache, slept 6 hours, severity 5\"* works perfectly."
                ),
            }

    # ── Pass through — proceed to listener or analyst ─────────────────────────
    return state
