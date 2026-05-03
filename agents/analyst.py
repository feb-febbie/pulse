"""
AnalystAgent — risk assessment agent for PulseCare caregiver dashboard.

Responsibilities:
  1. Compare the new log entry against the senior's personal baseline
  2. Retrieve relevant geriatric knowledge via RAG
  3. Produce a structured risk assessment for the caregiver
  4. Never surface output to the senior — this is caregiver-only information

Design principle: the AnalystAgent optimizes for DECISION QUALITY.
It is clinical, precise, and specific — the opposite of CompanionAgent.
This is the separation of concerns that makes the two-agent architecture work.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from graph.state import HealthState
from tools.llm_client import get_llm_client
from tools.memory_tools import get_summarized_history

_SYSTEM_PROMPT = """\
You are the AnalystAgent for PulseCare — a geriatric health monitoring system.

Your audience: the adult child / caregiver, NOT the senior patient.
Your output will appear on a caregiver dashboard, not shown to the patient.

You have just received a new health check-in from {name} (age {age}).
You also have access to their full health history and the geriatric knowledge base.

Your task:
1. Compare the new entry against the personal baseline
2. Identify any concerning patterns (compound signals are more important than single events)
3. Provide a concise risk assessment in the following structure:

RISK LEVEL: [LOW / MEDIUM / HIGH / CRITICAL]

PATTERN:
[2-4 bullet points identifying specific signals from the history. Be precise — include
numbers, dates, frequencies. "Dizziness reported 3× this week (0× in prior baseline)"
is good. "Patient has dizziness" is not.]

ATTRIBUTION:
[1-2 sentences explaining what the pattern likely means in geriatric context.
Ground in the medical knowledge provided. Reference specific mechanisms.]

RECOMMENDATION:
[1-3 specific, concrete actions for the caregiver. Not generic health advice.
Examples: "Call mom today and ask if dizziness occurs when standing up."
"Request a medication review with her physician — diuretic + summer heat = dehydration risk."]

ESCALATE IF:
[One sentence: specific symptoms or combination that should trigger immediate action —
calling 911 or taking to urgent care. Make it concrete.]

CROSS-MODAL SYNTHESIS (when Apple Watch data is present):
Always look for convergent or divergent signals between the conversation and the biometrics:
- {name} reports fatigue AND HRV is below 25ms → compound signal, physical not psychological
- {name} reports poor sleep AND deep sleep stage < 20% of total → watch corroborates subjective report
- {name} reports dizziness AND resting HR is above 78bpm → possible cardiovascular component
- {name} says "I feel fine" BUT SpO₂ < 95% → flag the discrepancy — under-reporting is common
When biometrics and conversation converge on the same signal, say so explicitly.
When they diverge, flag it — divergence is clinically informative.

Rules:
- Never use hedging language like "may" or "might" for clear signals
- Never hallucinate symptoms that aren't in the history
- If the situation is genuinely low risk, say so clearly — do not inflate risk
- Be specific with numbers: "3 times this week" not "several times recently"

Geriatric knowledge context:
{rag_context}
"""


def analyst_node(state: HealthState) -> HealthState:
    """LangGraph node: assess risk from new entry + history, update caregiver alerts."""
    from config import PARENT_NAME, PARENT_AGE
    from tools.rag_tools import MedicalRAG

    client = get_llm_client()
    new_entry = state.get("new_entry", {})
    symptoms = new_entry.get("symptoms", [])
    today = datetime.now(timezone.utc).date().isoformat()

    # ── RAG: retrieve geriatric context ──────────────────────────────────────
    try:
        rag = MedicalRAG()
        query = f"{' '.join(symptoms)} elderly fall risk sleep" if symptoms else "elderly health monitoring"
        rag_context = rag.retrieve(query, top_k=3)
    except Exception:
        rag_context = "Geriatric knowledge base unavailable for this query."

    # ── Build history context ─────────────────────────────────────────────────
    history_data = get_summarized_history(days=60)
    history_json = json.dumps(history_data, indent=2)

    # ── Apple Watch biometrics ────────────────────────────────────────────────
    try:
        from tools.watch_tools import get_watch_summary, get_sleep_stages
        watch_raw = get_watch_summary(days=7)
        stages = get_sleep_stages()
        watch_data = {
            "heart_rate_bpm":  watch_raw.get("heart_rate", {}).get("value"),
            "hr_avg_7d":       watch_raw.get("heart_rate", {}).get("avg"),
            "spo2_pct":        watch_raw.get("spo2", {}).get("value"),
            "spo2_avg_7d":     watch_raw.get("spo2", {}).get("avg"),
            "hrv_ms":          watch_raw.get("hrv", {}).get("value"),
            "hrv_avg_7d":      watch_raw.get("hrv", {}).get("avg"),
            "steps_today":     watch_raw.get("steps", {}).get("value"),
            "steps_avg_7d":    watch_raw.get("steps", {}).get("avg"),
            "sleep_stages_min": stages,
        }
        watch_json = json.dumps(watch_data, indent=2)
    except Exception:
        watch_json = "Watch data unavailable."

    new_entry_str = json.dumps(new_entry, indent=2)

    system = _SYSTEM_PROMPT.format(
        name=PARENT_NAME,
        age=PARENT_AGE,
        rag_context=rag_context,
    )

    user_message = f"""New check-in entry just logged for {PARENT_NAME}:

{new_entry_str}

Health history (last 60 days):
{history_json}

Apple Watch biometrics (last 7 days):
{watch_json}

Synthesise across both the conversational check-in and the biometric data. \
Note where they converge or diverge. Provide your risk assessment."""

    response = client.messages_create(
        system=system,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1200,
    )

    analyst_text = next((b.text for b in response.content if b.type == "text"), "")

    # Parse risk level from response
    risk_level = "low"
    upper = analyst_text.upper()
    if "CRITICAL" in upper:
        risk_level = "critical"
    elif "HIGH" in upper and "RISK LEVEL" in upper:
        risk_level = "high"
    elif "MEDIUM" in upper and "RISK LEVEL" in upper:
        risk_level = "medium"

    logs = list(state.get("status_logs", []))
    logs.append(f"AnalystAgent: risk={risk_level}, symptoms={symptoms}")

    return {
        **state,
        "analyst_response": analyst_text,
        "risk_level": risk_level,
        "rag_context": rag_context,
        "status_logs": logs,
    }
