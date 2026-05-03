"""
LangGraph shared state for PulseCare.

HealthState flows through every node. The full longitudinal health history
is injected on every analyst turn — this is the context engineering layer
that makes personalized pattern detection possible across sessions.
"""
from __future__ import annotations

from typing_extensions import TypedDict


class HealthState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────
    user_input: str       # raw message from senior
    chat_history: list    # prior turns: [{"role": "user"|"assistant", "content": str}]

    # ── Routing ────────────────────────────────────────────────────────────
    route_to_analyst: bool  # set by companion when significant signal logged

    # ── Health data ────────────────────────────────────────────────────────
    new_entry: dict       # entry just written to DB by CompanionAgent

    # ── Agent outputs ──────────────────────────────────────────────────────
    companion_response: str   # warm reply shown to senior
    analyst_response: str     # risk assessment (shown on caregiver dashboard)
    risk_level: str           # "low" | "medium" | "high" | "critical"
    alerts: list[dict]        # structured alerts for caregiver
    rag_context: str          # geriatric KB passages retrieved for analyst

    # ── Export ─────────────────────────────────────────────────────────────
    report_text: str      # health timeline document

    # ── Debug ──────────────────────────────────────────────────────────────
    status_logs: list[str]


def initial_state(user_input: str, chat_history: list | None = None) -> HealthState:
    return HealthState(
        user_input=user_input,
        chat_history=chat_history or [],
        route_to_analyst=False,
        alerts=[],
        status_logs=[],
    )
