"""
Health log storage — SQLite (local) or Firestore (Cloud Run).

Public API:
  log_entry(date, symptoms, sleep_hours, severity, notes) → dict
  query_history(days)                                      → list[dict]
  get_baseline(days)                                       → dict
  seed_demo_data()                                         → None
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ── SQLite ────────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # allow concurrent reads across sessions
    conn.execute("PRAGMA synchronous=NORMAL") # faster writes, still crash-safe
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            symptoms    TEXT NOT NULL,
            sleep_hours REAL,
            severity    INTEGER,
            notes       TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _row_to_dict(row) -> dict:
    d = dict(row)
    if isinstance(d.get("symptoms"), str):
        try:
            d["symptoms"] = json.loads(d["symptoms"])
        except Exception:
            d["symptoms"] = [d["symptoms"]] if d["symptoms"] else []
    return d


def _sqlite_log(date, symptoms, sleep_hours, severity, notes) -> dict:
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO health_log (date,symptoms,sleep_hours,severity,notes,created_at) VALUES (?,?,?,?,?,?)",
        (date, json.dumps(symptoms), sleep_hours, severity, notes, now),
    )
    conn.commit()
    return {"status": "logged", "date": date, "symptoms": symptoms,
            "sleep_hours": sleep_hours, "severity": severity, "notes": notes}


def _sqlite_query(days: int) -> list[dict]:
    conn = _get_conn()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    rows = conn.execute(
        "SELECT * FROM health_log WHERE date >= ? ORDER BY date DESC, created_at DESC",
        (since,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Firestore ─────────────────────────────────────────────────────────────────

def _firestore_log(date, symptoms, sleep_hours, severity, notes) -> dict:
    from google.cloud import firestore
    db = firestore.Client()
    entry = {"date": date, "symptoms": symptoms, "sleep_hours": sleep_hours,
             "severity": severity, "notes": notes,
             "created_at": datetime.now(timezone.utc).isoformat()}
    db.collection(config.FIRESTORE_COLLECTION).add(entry)
    return {"status": "logged", **entry}


def _firestore_query(days: int) -> list[dict]:
    from google.cloud import firestore
    db = firestore.Client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    docs = (
        db.collection(config.FIRESTORE_COLLECTION)
        .where("date", ">=", since)
        .order_by("date", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


# ── Public API ────────────────────────────────────────────────────────────────

def log_entry(
    date: str,
    symptoms: list[str],
    sleep_hours: Optional[float] = None,
    severity: Optional[int] = None,
    notes: str = "",
) -> dict:
    if config.USE_FIRESTORE:
        return _firestore_log(date, symptoms, sleep_hours, severity, notes)
    return _sqlite_log(date, symptoms, sleep_hours, severity, notes)


def query_history(days: int = 30) -> list[dict]:
    if config.USE_FIRESTORE:
        return _firestore_query(days)
    return _sqlite_query(days)


def get_baseline(days: int = 30) -> dict:
    """Compute summary statistics over the past N days."""
    history = query_history(days=days)
    if not history:
        return {"total_entries": 0}

    sym_counts: dict[str, int] = {}
    sleep_vals, sev_vals = [], []
    for e in history:
        for s in e.get("symptoms", []):
            sym_counts[s.lower()] = sym_counts.get(s.lower(), 0) + 1
        if e.get("sleep_hours") is not None:
            sleep_vals.append(float(e["sleep_hours"]))
        if e.get("severity") is not None:
            sev_vals.append(int(e["severity"]))

    return {
        "total_entries": len(history),
        "avg_sleep_hours": round(sum(sleep_vals) / len(sleep_vals), 1) if sleep_vals else None,
        "avg_severity": round(sum(sev_vals) / len(sev_vals), 1) if sev_vals else None,
        "top_symptoms": sorted(sym_counts.items(), key=lambda x: -x[1])[:8],
        "days": days,
    }


def get_summarized_history(days: int = 60) -> dict:
    """
    Token-efficient history for AnalystAgent.
    ≤30 entries → raw. >30 entries → compress older entries into baseline stats,
    return last 7 days raw. Controls token cost as history grows.
    """
    all_history = query_history(days=days)
    recent = query_history(days=7)

    if len(all_history) <= 30:
        return {"mode": "raw", "entries": all_history}

    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    older = [e for e in all_history if e["date"] < cutoff]

    sym_counts: dict[str, int] = {}
    sleep_vals, sev_vals = [], []
    for e in older:
        for s in e.get("symptoms", []):
            sym_counts[s.lower()] = sym_counts.get(s.lower(), 0) + 1
        if e.get("sleep_hours") is not None:
            sleep_vals.append(float(e["sleep_hours"]))
        if e.get("severity") is not None:
            sev_vals.append(int(e["severity"]))

    return {
        "mode": "summarized",
        "baseline": {
            "description": f"Summary of {len(older)} entries older than 7 days",
            "top_symptoms": sorted(sym_counts.items(), key=lambda x: -x[1])[:5],
            "avg_sleep_hours": round(sum(sleep_vals) / len(sleep_vals), 1) if sleep_vals else None,
            "avg_severity": round(sum(sev_vals) / len(sev_vals), 1) if sev_vals else None,
        },
        "recent_raw": recent,
    }


def record_family_view() -> None:
    """Record that the caregiver just viewed the dashboard."""
    conn = _get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS family_activity (id INTEGER PRIMARY KEY AUTOINCREMENT, viewed_at TEXT NOT NULL)")
    conn.execute("INSERT INTO family_activity (viewed_at) VALUES (?)", (datetime.now(timezone.utc).isoformat(),))
    conn.commit()


def get_last_family_view() -> Optional[datetime]:
    """Return when the caregiver last opened the dashboard, or None."""
    conn = _get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS family_activity (id INTEGER PRIMARY KEY AUTOINCREMENT, viewed_at TEXT NOT NULL)")
    row = conn.execute("SELECT viewed_at FROM family_activity ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        ts = row["viewed_at"]
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None
    return None


def _ensure_seed_marker_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS demo_seed_marker (
            id        INTEGER PRIMARY KEY CHECK (id = 1),
            seeded_at TEXT NOT NULL
        )
    """)


def reset_health_data() -> None:
    """
    Delete only check-ins added after the last seed run (live demo entries).
    The 14-day seeded demo arc stays intact so the app always looks in-use.
    """
    conn = _get_conn()
    _ensure_seed_marker_table(conn)
    row = conn.execute("SELECT seeded_at FROM demo_seed_marker WHERE id = 1").fetchone()
    if row:
        # Only delete entries logged after seeding completed
        conn.execute("DELETE FROM health_log WHERE created_at > ?", (row["seeded_at"],))
    # Family presence always resets so the banner doesn't show stale activity
    conn.execute("""
        CREATE TABLE IF NOT EXISTS family_activity
        (id INTEGER PRIMARY KEY AUTOINCREMENT, viewed_at TEXT NOT NULL)
    """)
    conn.execute("DELETE FROM family_activity")
    conn.commit()


def seed_demo_data() -> None:
    """
    Pre-load 14 days of health history for Margaret Chen (72).
    Story arc: normal baseline → gradual decline → elevated fall risk this week.
    Only seeds if DB is empty.
    """
    existing = query_history(days=60)
    if existing:
        return

    today = datetime.now(timezone.utc).date()

    entries = [
        # ── Week 2 ago: baseline, normal ────────────────────────────────────
        {"date": (today - timedelta(days=14)).isoformat(),
         "symptoms": [], "sleep_hours": 7.5, "severity": None,
         "notes": "Good day. Walked to the mailbox, had lunch with neighbor."},
        {"date": (today - timedelta(days=13)).isoformat(),
         "symptoms": ["fatigue"], "sleep_hours": 7.0, "severity": 2,
         "notes": "A little tired after church but nothing unusual."},
        {"date": (today - timedelta(days=12)).isoformat(),
         "symptoms": [], "sleep_hours": 8.0, "severity": None,
         "notes": "Slept well. Felt good. Watched the birds in the garden."},
        {"date": (today - timedelta(days=11)).isoformat(),
         "symptoms": [], "sleep_hours": 7.5, "severity": None,
         "notes": "Normal day. Cooked dinner. No complaints."},
        {"date": (today - timedelta(days=10)).isoformat(),
         "symptoms": ["fatigue"], "sleep_hours": 6.5, "severity": 2,
         "notes": "A bit tired, maybe coming down with something. Had tea and rested."},
        {"date": (today - timedelta(days=9)).isoformat(),
         "symptoms": [], "sleep_hours": 7.5, "severity": None,
         "notes": "Better today. Gardened for a bit."},
        {"date": (today - timedelta(days=8)).isoformat(),
         "symptoms": [], "sleep_hours": 7.0, "severity": None,
         "notes": "Fine. Nothing to report."},
        # ── Past week: gradual decline ───────────────────────────────────────
        {"date": (today - timedelta(days=7)).isoformat(),
         "symptoms": ["dizziness", "fatigue"], "sleep_hours": 6.5, "severity": 4,
         "notes": "Felt dizzy when I got up this morning. Had to sit down for a few minutes. "
                  "Felt tired all day. Skipped my walk."},
        {"date": (today - timedelta(days=6)).isoformat(),
         "symptoms": ["fatigue"], "sleep_hours": 6.0, "severity": 3,
         "notes": "Didn't sleep well. Woke up twice. Tired in the morning but felt better by afternoon."},
        {"date": (today - timedelta(days=5)).isoformat(),
         "symptoms": ["dizziness", "fatigue"], "sleep_hours": 5.5, "severity": 5,
         "notes": "Dizzy again this morning, worse than before. I was standing at the sink and had to "
                  "hold on. Felt off balance. Tired. I don't want to worry Sarah."},
        {"date": (today - timedelta(days=4)).isoformat(),
         "symptoms": ["fatigue"], "sleep_hours": 5.5, "severity": 3,
         "notes": "Another rough night. Not much appetite. Stayed in most of the day."},
        {"date": (today - timedelta(days=3)).isoformat(),
         "symptoms": ["dizziness", "fatigue", "low appetite"], "sleep_hours": 5.0, "severity": 6,
         "notes": "Very dizzy this morning when I stood up. Had to grab the wall. "
                  "Didn't eat much. I'm sure it will pass. Don't want to make a fuss."},
        {"date": (today - timedelta(days=2)).isoformat(),
         "symptoms": ["fatigue"], "sleep_hours": 6.0, "severity": 3,
         "notes": "A little better today. Still tired. Dizziness was less bad."},
        {"date": (today - timedelta(days=1)).isoformat(),
         "symptoms": ["dizziness", "fatigue", "low appetite"], "sleep_hours": 5.0, "severity": 5,
         "notes": "Dizzy again when getting out of bed. Had to sit on the edge for a while before I "
                  "could stand. Not eating much. Skipped the senior center today."},
    ]

    for e in entries:
        log_entry(
            date=e["date"],
            symptoms=e["symptoms"],
            sleep_hours=e["sleep_hours"],
            severity=e.get("severity"),
            notes=e["notes"],
        )

    # Stamp the seed marker so reset_health_data() knows what to keep
    conn = _get_conn()
    _ensure_seed_marker_table(conn)
    conn.execute(
        "INSERT INTO demo_seed_marker (id, seeded_at) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET seeded_at = excluded.seeded_at",
        (datetime.now(timezone.utc).isoformat(),),
    )
    conn.commit()


# ── LLM tool schemas ──────────────────────────────────────────────────────────

LOG_ENTRY_TOOL = {
    "name": "log_health_entry",
    "description": (
        "Log a structured health entry from the senior's natural language check-in. "
        "Call once per message. Extract all health signals mentioned."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "ISO date YYYY-MM-DD. Use today unless user says otherwise."},
            "symptoms": {
                "type": "array", "items": {"type": "string"},
                "description": "Symptoms in lowercase short phrases: 'dizziness', 'fatigue', 'confusion', etc.",
            },
            "sleep_hours": {"type": "number", "description": "Hours of sleep last night if mentioned. Null otherwise."},
            "severity": {"type": "integer", "minimum": 1, "maximum": 10,
                         "description": "1-10 severity if mentioned or implied. Null if unclear."},
            "notes": {"type": "string", "description": "Senior's own words, lightly cleaned."},
        },
        "required": ["date", "symptoms", "notes"],
    },
}
