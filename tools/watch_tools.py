"""
Apple Watch / HealthKit data layer for PulseCare.

Stores biometric time-series in a separate SQLite table (or Firestore).
Seeded with realistic demo data for Margaret (72) showing:
  - HR baseline ~70bpm, slight elevation in symptomatic week
  - SpO2 dipping to 94-95% on poor-sleep nights (clinically notable)
  - HRV declining through the symptomatic week (stress marker)
  - Sleep: good stages baseline, fragmented last week
  - Steps declining in symptomatic period

Public API:
  seed_watch_data()           → None
  get_watch_summary(days)     → dict  (latest + trend for each metric)
  get_sleep_stages(date)      → dict  (deep/core/rem/awake minutes)
  get_hr_series(days)         → list[dict]
  get_steps_series(days)      → list[dict]
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

_WATCH_DB = config.SQLITE_PATH  # same DB, separate table


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_WATCH_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watch_data (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            metric      TEXT NOT NULL,
            value       REAL NOT NULL,
            unit        TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _row(date, metric, value, unit=""):
    return (date, metric, value, unit, datetime.now(timezone.utc).isoformat())


def reset_watch_data() -> None:
    """Wipe watch biometrics so every demo starts clean."""
    conn = _get_conn()
    conn.execute("DELETE FROM watch_data")
    conn.commit()


def seed_watch_data() -> None:
    """Pre-load 14 days of Apple Watch biometrics for Margaret."""
    conn = _get_conn()
    existing = conn.execute("SELECT COUNT(*) FROM watch_data").fetchone()[0]
    if existing > 0:
        return

    today = datetime.now(timezone.utc).date()
    rows = []

    # ── Resting heart rate (bpm) ──────────────────────────────────────────────
    hr_baseline = [72, 70, 71, 73, 70, 71, 72]   # days 14-8
    hr_recent   = [75, 77, 79, 76, 80, 78, 82]   # days 7-1 (elevated)
    for i, hr in enumerate(hr_baseline + hr_recent):
        d = (today - timedelta(days=14 - i)).isoformat()
        rows.append(_row(d, "heart_rate", hr, "bpm"))

    # ── SpO2 (%) ──────────────────────────────────────────────────────────────
    spo2_baseline = [98, 97, 98, 99, 98, 97, 98]
    spo2_recent   = [97, 95, 94, 96, 94, 95, 94]   # dipping — clinically notable
    for i, v in enumerate(spo2_baseline + spo2_recent):
        d = (today - timedelta(days=14 - i)).isoformat()
        rows.append(_row(d, "spo2", v, "%"))

    # ── HRV (ms) ─────────────────────────────────────────────────────────────
    hrv_baseline = [32, 35, 31, 33, 34, 32, 30]
    hrv_recent   = [28, 24, 22, 26, 20, 23, 19]   # declining = stress/poor recovery
    for i, v in enumerate(hrv_baseline + hrv_recent):
        d = (today - timedelta(days=14 - i)).isoformat()
        rows.append(_row(d, "hrv", v, "ms"))

    # ── Steps (count) ────────────────────────────────────────────────────────
    steps_baseline = [4200, 3800, 5100, 4600, 3900, 4700, 4100]
    steps_recent   = [3200, 2900, 2100, 3400, 1800, 2300, 1600]   # declining
    for i, v in enumerate(steps_baseline + steps_recent):
        d = (today - timedelta(days=14 - i)).isoformat()
        rows.append(_row(d, "steps", v, "steps"))

    # ── Sleep stages (minutes) ────────────────────────────────────────────────
    # Format: deep, core, rem, awake — summing to ~total sleep time
    sleep_data = [
        # baseline week (good nights)
        {"deep": 85, "core": 195, "rem": 95, "awake": 25},   # day-14
        {"deep": 80, "core": 200, "rem": 90, "awake": 30},   # day-13
        {"deep": 90, "core": 210, "rem": 100, "awake": 20},  # day-12
        {"deep": 82, "core": 198, "rem": 92, "awake": 28},   # day-11
        {"deep": 78, "core": 192, "rem": 85, "awake": 35},   # day-10
        {"deep": 88, "core": 205, "rem": 97, "awake": 22},   # day-9
        {"deep": 84, "core": 196, "rem": 90, "awake": 30},   # day-8
        # recent week (fragmented)
        {"deep": 60, "core": 160, "rem": 70, "awake": 60},   # day-7
        {"deep": 55, "core": 155, "rem": 65, "awake": 75},   # day-6
        {"deep": 48, "core": 145, "rem": 60, "awake": 80},   # day-5
        {"deep": 52, "core": 152, "rem": 63, "awake": 73},   # day-4
        {"deep": 40, "core": 138, "rem": 55, "awake": 87},   # day-3
        {"deep": 50, "core": 148, "rem": 62, "awake": 80},   # day-2
        {"deep": 38, "core": 130, "rem": 50, "awake": 92},   # day-1
    ]
    for i, s in enumerate(sleep_data):
        d = (today - timedelta(days=14 - i)).isoformat()
        for metric, val in s.items():
            rows.append(_row(d, f"sleep_{metric}", val, "min"))

    conn.executemany(
        "INSERT INTO watch_data (date,metric,value,unit,created_at) VALUES (?,?,?,?,?)",
        rows,
    )
    conn.commit()


def get_watch_summary(days: int = 7) -> dict:
    """Latest value + 7-day trend for HR, SpO2, HRV, steps, sleep."""
    conn = _get_conn()
    today = datetime.now(timezone.utc).date()
    since = (today - timedelta(days=days)).isoformat()

    rows = conn.execute(
        "SELECT date, metric, value FROM watch_data WHERE date >= ? ORDER BY date DESC",
        (since,),
    ).fetchall()

    metrics: dict[str, list[float]] = {}
    for r in rows:
        metrics.setdefault(r["metric"], []).append(r["value"])

    def _latest(m): return metrics[m][0] if m in metrics and metrics[m] else None
    def _avg(m):    return round(sum(metrics[m]) / len(metrics[m]), 1) if m in metrics and metrics[m] else None
    def _trend(m):
        vals = metrics.get(m, [])
        if len(vals) < 2: return "stable"
        # vals are newest-first
        recent_avg = sum(vals[:3]) / min(3, len(vals))
        older_avg  = sum(vals[3:]) / max(len(vals) - 3, 1)
        diff = recent_avg - older_avg
        pct = diff / max(older_avg, 1) * 100
        if pct > 5:  return "up"
        if pct < -5: return "down"
        return "stable"

    sleep_metrics = ["sleep_deep", "sleep_core", "sleep_rem", "sleep_awake"]
    total_sleep_mins = sum(_avg(m) or 0 for m in sleep_metrics)

    return {
        "heart_rate":  {"value": _latest("heart_rate"),  "avg": _avg("heart_rate"),  "trend": _trend("heart_rate"),  "unit": "bpm"},
        "spo2":        {"value": _latest("spo2"),         "avg": _avg("spo2"),         "trend": _trend("spo2"),         "unit": "%"},
        "hrv":         {"value": _latest("hrv"),          "avg": _avg("hrv"),          "trend": _trend("hrv"),          "unit": "ms"},
        "steps":       {"value": _latest("steps"),        "avg": _avg("steps"),        "trend": _trend("steps"),        "unit": "steps"},
        "sleep_hours": {"value": round(total_sleep_mins / 60, 1) if total_sleep_mins else None, "unit": "h"},
        "sleep_deep":  {"value": _latest("sleep_deep"),   "avg": _avg("sleep_deep"),   "unit": "min"},
        "sleep_core":  {"value": _latest("sleep_core"),   "avg": _avg("sleep_core"),   "unit": "min"},
        "sleep_rem":   {"value": _latest("sleep_rem"),    "avg": _avg("sleep_rem"),    "unit": "min"},
        "sleep_awake": {"value": _latest("sleep_awake"),  "avg": _avg("sleep_awake"),  "unit": "min"},
    }


def get_hr_series(days: int = 7) -> list[dict]:
    conn = _get_conn()
    since = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT date, value FROM watch_data WHERE metric='heart_rate' AND date >= ? ORDER BY date",
        (since,),
    ).fetchall()
    return [{"date": r["date"], "HR (bpm)": r["value"]} for r in rows]


def get_steps_series(days: int = 7) -> list[dict]:
    conn = _get_conn()
    since = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT date, value FROM watch_data WHERE metric='steps' AND date >= ? ORDER BY date",
        (since,),
    ).fetchall()
    return [{"date": r["date"], "Steps": int(r["value"])} for r in rows]


def get_sleep_stages(date: Optional[str] = None) -> dict:
    """Get sleep stage breakdown for a specific date (default: most recent)."""
    conn = _get_conn()
    if date:
        rows = conn.execute(
            "SELECT metric, value FROM watch_data WHERE metric LIKE 'sleep_%' AND date=?",
            (date,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT metric, value FROM watch_data
               WHERE metric LIKE 'sleep_%'
               AND date = (SELECT MAX(date) FROM watch_data WHERE metric LIKE 'sleep_%')"""
        ).fetchall()
    return {r["metric"].replace("sleep_", ""): int(r["value"]) for r in rows}
