"""
Patient profile storage for PulseCare.

Stores the senior's medical background — conditions, medications, doctor info,
lifestyle — so CompanionAgent can give personalised, specific responses rather
than generic health advice.

Public API:
  seed_demo_profile()          → None  (idempotent — only seeds if empty)
  get_patient_profile()        → dict
  save_patient_profile(dict)   → None
  format_profile_for_prompt()  → str   (compact LLM-readable block)
"""
from __future__ import annotations

import json
import sqlite3

import config


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_profile (
            id   INTEGER PRIMARY KEY CHECK (id = 1),
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# ── Margaret's complete demo profile ─────────────────────────────────────────
_MARGARET_DEMO: dict = {
    "name": "Margaret Chen",
    "age": 72,
    "conditions": [
        "Hypertension (Stage 1, well-managed on Lisinopril)",
        "Type 2 Diabetes (diet + Metformin, blood sugar stable)",
        "Mild osteoarthritis (knees and hips — worse in cold weather or after stairs)",
    ],
    "medications": [
        {
            "name": "Lisinopril",
            "dose": "10mg",
            "frequency": "Once daily",
            "time": "Morning with breakfast",
            "purpose": "Blood pressure",
            "notes": (
                "If she misses a morning dose, she can take it as soon as she remembers — "
                "but skip it if it's nearly evening. Never double up."
            ),
        },
        {
            "name": "Metformin",
            "dose": "500mg",
            "frequency": "Twice daily",
            "time": "With breakfast and with dinner",
            "purpose": "Blood sugar (Type 2 Diabetes)",
            "notes": (
                "Always with food — empty stomach causes nausea. "
                "If she forgets, take it with the next meal. Missing one dose is fine."
            ),
        },
        {
            "name": "Atorvastatin",
            "dose": "20mg",
            "frequency": "Once daily",
            "time": "Evening (any time after 6pm)",
            "purpose": "Cholesterol",
            "notes": (
                "Evening timing is preferred but not critical. "
                "Missing a day occasionally is fine. No grapefruit juice with this one."
            ),
        },
        {
            "name": "Vitamin D3",
            "dose": "1000 IU",
            "frequency": "Once daily",
            "time": "Morning",
            "purpose": "Bone health and mood",
            "notes": "Over-the-counter supplement — no harm if occasionally missed.",
        },
    ],
    "allergies": [
        "Penicillin (causes rash — noted on pharmacy records)",
    ],
    "doctor": {
        "name": "Dr. Patricia Huang",
        "phone": "212-555-0150",
        "specialty": "Internal Medicine",
        "practice": "Riverside Medical Group",
    },
    "pharmacy": "CVS on 5th Avenue — offers free home delivery, call 212-555-0299",
    "lifestyle": (
        "Lives alone in a 2-story house (bedroom upstairs, bathroom has grab bars). "
        "Former schoolteacher — very independent, loves reading, crosswords, and the garden. "
        "Enjoys birdwatching from the kitchen window. "
        "Attends the senior centre on Tuesdays and Thursdays. "
        "Daughter Sarah visits once a month; they speak by phone every Sunday evening. "
        "Walks to the mailbox most mornings — her main daily exercise."
    ),
    "emergency_contacts": [
        {"name": "Sarah Chen", "relation": "Daughter", "phone": "+1-212-555-0190"},
    ],
    "personality_notes": (
        "Tends to downplay symptoms — says 'it's nothing' or 'I don't want to worry anyone.' "
        "Very proud and independent; doesn't like to feel like a burden. "
        "Responds warmly to friendly, unhurried conversation. "
        "Gets anxious if she feels she's being medically managed rather than listened to."
    ),
}


# ── Public API ────────────────────────────────────────────────────────────────

def seed_demo_profile() -> None:
    """Restore Margaret's complete demo profile on every launch."""
    save_patient_profile(_MARGARET_DEMO)


def get_patient_profile() -> dict:
    """Return the saved patient profile, or the demo default if none saved."""
    try:
        conn = _get_conn()
        row = conn.execute("SELECT data FROM patient_profile WHERE id = 1").fetchone()
        if row:
            return json.loads(row["data"])
    except Exception:
        pass
    return _MARGARET_DEMO.copy()


def save_patient_profile(profile: dict) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO patient_profile (id, data) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET data = excluded.data",
        (json.dumps(profile),),
    )
    conn.commit()


def format_profile_for_prompt(profile: dict) -> str:
    """
    Format the patient profile as a compact LLM-readable block for injection
    into the CompanionAgent system prompt.
    """
    lines = []

    if profile.get("conditions"):
        lines.append("MEDICAL CONDITIONS:\n" +
                     "\n".join(f"  • {c}" for c in profile["conditions"]))

    if profile.get("medications"):
        med_lines = []
        for m in profile["medications"]:
            base = (f"  • {m['name']} {m['dose']} — {m['purpose']} — "
                    f"{m['frequency']}, {m['time']}")
            if m.get("notes"):
                base += f"\n    → {m['notes']}"
            med_lines.append(base)
        lines.append(
            "MEDICATIONS (use these for specific, accurate advice when asked):\n" +
            "\n".join(med_lines)
        )

    if profile.get("allergies"):
        lines.append("ALLERGIES: " + "; ".join(profile["allergies"]))

    if profile.get("doctor"):
        d = profile["doctor"]
        lines.append(
            f"DOCTOR: {d.get('name')} ({d.get('specialty')}, {d.get('practice')}) "
            f"— {d.get('phone')}"
        )

    if profile.get("pharmacy"):
        lines.append(f"PHARMACY: {profile['pharmacy']}")

    if profile.get("lifestyle"):
        lines.append(f"ABOUT HER: {profile['lifestyle']}")

    if profile.get("personality_notes"):
        lines.append(f"PERSONALITY: {profile['personality_notes']}")

    return "\n\n".join(lines)
