"""
ListenerAgent — intake agent for Pulse.

Responsibilities:
  1. Parse the user's natural language health entry
  2. Call log_health_entry() tool to write structured data to the DB
  3. Return a warm, low-friction confirmation

This agent uses a persona that is empathetic and frictionless — designed to
make daily logging feel effortless so users actually build a history.
Low friction = daily engagement = data accumulation = Pulse's core value.

Uses LangGraph node pattern: receives HealthState, returns updated HealthState.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from graph.state import HealthState
from tools.llm_client import get_llm_client
from tools.memory_tools import log_entry, LOG_ENTRY_TOOL

_SYSTEM_PROMPT = """\
You are Pulse's ListenerAgent — the intake side of a personal health memory system.

Your job: extract a structured health log entry from what the user just told you, \
then call log_health_entry() to save it. Do this in one step without preamble.

Extraction rules:
- date: today unless user says "yesterday", "last night", etc. Use ISO format YYYY-MM-DD.
- symptoms: short lowercase phrases. Extract everything mentioned, even vaguely. Examples:
    physical: "headache", "migraine", "fatigue", "nausea", "stomach ache", "eye strain", "back pain", "chest tightness"
    mood/cognitive: "anxiety", "stress", "brain fog", "low mood", "irritability", "panic"
    illness: "sore throat", "fever", "congestion", "cough"
  Empty list is fine if no symptoms are mentioned.
- sleep_hours: extract if any sleep duration is mentioned. "slept 5 hours" → 5.0. Null if not mentioned.
- severity: 1–10. Infer from language if not explicit. "terrible" → 7–8. "mild" or "a bit" → 2–3. "can't function" → 9. Null if unclear.
- notes: the user's exact words, lightly cleaned. Preserve their voice.

After logging, respond with a brief warm confirmation (2–3 sentences max).
Acknowledge what was logged. If sleep was short, gently note it — no lecture.
Never ask follow-up questions. Never add disclaimers about seeing a doctor.
Keep it human, not clinical.
"""


def listener_node(state: HealthState) -> HealthState:
    """LangGraph node: parse health entry, log it, return confirmation."""
    client = get_llm_client()
    user_input = state.get("user_input", "")
    today = datetime.now(timezone.utc).date().isoformat()

    messages = [
        {"role": "user", "content": f"Today is {today}.\n\n{user_input}"}
    ]

    tools = [LOG_ENTRY_TOOL]
    logged_entry: dict = {}

    # Tool-use loop: LLM calls log_health_entry, we execute it, then get final reply
    max_rounds = 3
    for _ in range(max_rounds):
        response = client.messages_create(
            system=_SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
            max_tokens=1024,
        )

        # Collect assistant content blocks for the message history
        assistant_content = []
        tool_calls_made = []

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                tool_calls_made.append(block)

        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason != "tool_use" or not tool_calls_made:
            # Final text response — extract it
            final_text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            break

        # Execute tool calls
        tool_results = []
        for call in tool_calls_made:
            if call.name == "log_health_entry":
                inp = call.input
                result = log_entry(
                    date=inp.get("date", today),
                    symptoms=inp.get("symptoms", []),
                    sleep_hours=inp.get("sleep_hours"),
                    severity=inp.get("severity"),
                    notes=inp.get("notes", user_input),
                )
                logged_entry = result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})

    else:
        final_text = "Logged. Keep tracking — patterns take time to see."

    logs = list(state.get("status_logs", []))
    logs.append(f"ListenerAgent: logged entry for {logged_entry.get('date', today)}")

    return {
        **state,
        "response": final_text,
        "new_entry": logged_entry,
        "status_logs": logs,
    }
