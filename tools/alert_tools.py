"""
Alert computation for PulseCare caregiver dashboard.

compute_risk_level() is the core signal-processing function. It compares
the current week against the senior's personal baseline, applies geriatric
thresholds, and returns a structured risk assessment.

This is what transforms raw health logs into the actionable caregiver signal
that justifies the $29/month price point.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

import config
from tools.memory_tools import query_history


def compute_risk_level(days_baseline: int = 30) -> dict:
    """
    Compare this week's health signals against the senior's personal baseline.

    Returns:
        {
            level: "low" | "medium" | "high" | "critical",
            score: int (0-100),
            alerts: list[{type, message, severity, attribution}],
            baseline_sleep: float | None,
            recent_sleep: float | None,
            sufficient_data: bool,
        }
    """
    today = datetime.now(timezone.utc).date()
    week_ago = (today - timedelta(days=7)).isoformat()
    baseline_end = week_ago

    history_all = query_history(days=days_baseline)
    history_week = [e for e in history_all if e["date"] >= week_ago]
    history_baseline = [e for e in history_all if e["date"] < baseline_end]

    if len(history_all) < 4:
        return {"level": "low", "score": 0, "alerts": [], "sufficient_data": False}

    score = 0
    alerts: list[dict] = []

    # ── Sleep analysis ────────────────────────────────────────────────────────
    def _avg_sleep(entries):
        vals = [float(e["sleep_hours"]) for e in entries if e.get("sleep_hours") is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    baseline_sleep = _avg_sleep(history_baseline) or _avg_sleep(history_all)
    recent_sleep = _avg_sleep(history_week)

    # Consecutive poor sleep nights
    poor_sleep_nights = [
        e for e in history_week
        if e.get("sleep_hours") is not None and float(e["sleep_hours"]) < config.SLEEP_WARNING_HOURS
    ]
    consecutive = len(poor_sleep_nights)

    if consecutive >= config.SLEEP_CONSECUTIVE_THRESHOLD:
        sleep_pts = min(35, consecutive * 10)
        score += sleep_pts
        alerts.append({
            "type": "sleep",
            "severity": "high" if consecutive >= 4 else "medium",
            "message": (
                f"{consecutive} consecutive nights below {config.SLEEP_WARNING_HOURS}h "
                f"(averaging {recent_sleep}h vs baseline {baseline_sleep}h)"
            ),
            "attribution": "Chronic sleep deprivation in elderly → impaired balance and reaction time → elevated fall risk.",
            "icon": "😴",
        })
    elif baseline_sleep and recent_sleep:
        pct = (baseline_sleep - recent_sleep) / baseline_sleep
        if pct >= config.SLEEP_DEVIATION_PCT:
            score += 15
            alerts.append({
                "type": "sleep",
                "severity": "medium",
                "message": f"Sleep averaging {recent_sleep}h this week vs {baseline_sleep}h baseline ({int(pct*100)}% drop)",
                "attribution": "Sleep decline correlates with increased fall risk and cognitive impairment in elderly.",
                "icon": "😴",
            })

    # ── Dizziness / fall risk ─────────────────────────────────────────────────
    all_syms_week = [s.lower() for e in history_week for s in e.get("symptoms", []) if s]
    all_syms_baseline = [s.lower() for e in history_baseline for s in e.get("symptoms", []) if s]

    week_dizziness = all_syms_week.count("dizziness")
    if history_baseline:
        baseline_rate = all_syms_baseline.count("dizziness") / max(len(history_baseline), 1)
        expected = baseline_rate * 7
    else:
        expected = 0

    if week_dizziness >= config.FALL_RISK_WEEKLY_THRESHOLD:
        diz_pts = min(40, week_dizziness * 13)
        score += diz_pts
        pct_above = int((week_dizziness / max(expected, 0.1) - 1) * 100) if expected > 0 else None
        above_str = f" (↑ {pct_above}% vs baseline)" if pct_above else ""
        alerts.append({
            "type": "fall_risk",
            "severity": "high" if week_dizziness >= 3 else "medium",
            "message": f"Dizziness reported {week_dizziness}× this week{above_str}",
            "attribution": (
                "Dizziness + poor sleep is a compound fall risk signal. "
                "Orthostatic hypotension or dehydration most likely causes. "
                "Recommend check-in call and physician review if persisting."
            ),
            "icon": "⚠️",
        })

    # ── Symptom frequency spike ───────────────────────────────────────────────
    symp_days_week = len([e for e in history_week if e.get("symptoms")])
    if history_baseline:
        baseline_symp_rate = len([e for e in history_baseline if e.get("symptoms")]) / max(len(history_baseline), 1)
        expected_symp_days = baseline_symp_rate * 7
        if expected_symp_days > 0 and symp_days_week / expected_symp_days >= config.SYMPTOM_SPIKE_RATIO:
            score += 15
            alerts.append({
                "type": "symptom_spike",
                "severity": "medium",
                "message": (
                    f"{symp_days_week} symptom days this week "
                    f"(baseline: ~{round(expected_symp_days, 1)}/week)"
                ),
                "attribution": "Symptom frequency above historical baseline — pattern warrants monitoring.",
                "icon": "📈",
            })

    # ── Reduced activity / appetite signals ───────────────────────────────────
    isolation_signals = sum(
        1 for s in all_syms_week
        if s in ("low appetite", "stayed in", "skipped", "not eating")
    )
    if isolation_signals >= 2:
        score += 10
        alerts.append({
            "type": "isolation",
            "severity": "medium",
            "message": "Reduced appetite and activity reported multiple times this week",
            "attribution": "Social withdrawal and reduced appetite are early warning signs of depression or illness in elderly.",
            "icon": "🏠",
        })

    # ── Medication non-adherence ──────────────────────────────────────────────
    _MED_EXACT = {
        "skipped medications", "missed medications", "missed dose", "missed doses",
        "skipped meds", "missed meds", "skipped pills", "missed pills",
        "forgot medication", "forgot medications", "medication non-adherence",
        "non-adherence", "nonadherence", "hasn't taken medications",
        "not taking medications", "not taken medications",
    }
    _MED_WORDS  = ("medic", "pill", "tablet", "dose", "drug", "prescription", "med")
    _SKIP_WORDS = ("skip", "miss", "forgot", "haven't", "not tak", "didn't tak",
                   "not been tak", "haven't been", "a week", "days without")

    def _is_med_skip(sym: str) -> bool:
        s = sym.lower()
        if s in _MED_EXACT:
            return True
        has_med  = any(w in s for w in _MED_WORDS)
        has_skip = any(w in s for w in _SKIP_WORDS)
        return has_med and has_skip

    med_skip_entries = [
        e for e in history_week
        if any(_is_med_skip(s) for s in e.get("symptoms", []))
    ]
    if med_skip_entries:
        days    = len(med_skip_entries)
        max_sev = max((int(e.get("severity") or 0) for e in med_skip_entries), default=0)
        # severity 7+ means the senior reported a multi-day gap in a single entry
        is_crit = days >= 5 or max_sev >= 7
        is_high = days >= 2 or max_sev >= 5
        sev_label = "critical" if is_crit else ("high" if is_high else "medium")
        score += min(60, days * 15 + max(0, max_sev - 4) * 8)
        duration_note = f" (severity {max_sev}/10 — possible multi-day gap)" if max_sev >= 7 else (
                        f" (severity {max_sev}/10)" if max_sev else "")
        alerts.append({
            "type": "medication",
            "severity": sev_label,
            "message": (
                f"Medications skipped — reported {days} time{'s' if days > 1 else ''} this week"
                + duration_note
            ),
            "attribution": (
                "Non-adherence to Lisinopril (blood pressure) and Metformin (blood sugar) "
                "can cause BP spikes or glucose instability within 24–48h. "
                "A gentle reminder call or pharmacy check-in is recommended."
            ),
            "icon": "💊",
        })

    # ── Cardiovascular compound signal (orthopnea + edema) ───────────────────
    orthopnea_entries = [
        e for e in history_week
        if any(s.lower() in ("orthopnea", "shortness of breath") for s in e.get("symptoms", []))
    ]
    edema_entries = [
        e for e in history_week
        if any(s.lower() == "edema" for s in e.get("symptoms", []))
    ]
    if orthopnea_entries and edema_entries:
        score += 55
        alerts.append({
            "type": "cardiovascular",
            "severity": "critical",
            "message": (
                f"Orthopnea + edema both reported this week — compound cardiovascular signal"
            ),
            "attribution": (
                "Breathing difficulty when lying flat (orthopnea) combined with ankle or leg "
                "swelling (edema) is a classic presentation of fluid retention, and a possible "
                "indicator of congestive heart failure exacerbation or significant blood pressure "
                "instability. Physician review is strongly recommended — do not wait for a "
                "scheduled appointment."
            ),
            "icon": "🫀",
        })
    elif orthopnea_entries:
        score += 25
        alerts.append({
            "type": "cardiovascular",
            "severity": "high",
            "message": "Breathing difficulty when lying flat (orthopnea) reported this week",
            "attribution": (
                "Orthopnea in someone with hypertension and diabetes can indicate fluid "
                "retention or cardiovascular strain. Ask about ankle swelling and whether "
                "propping up with pillows helps — if swelling is confirmed, escalate promptly."
            ),
            "icon": "🫀",
        })

    # ── Mental health crisis signals ──────────────────────────────────────────
    _CRISIS = {"wants to die", "suicidal ideation", "self-harm", "hopeless"}
    _LONELY = {"lonely", "low mood", "depression"}

    crisis_entries = [
        e for e in history_week
        if any(s.lower() in _CRISIS for s in e.get("symptoms", []))
    ]
    if crisis_entries:
        score += 80
        alerts.append({
            "type": "mental_crisis",
            "severity": "critical",
            "message": f"Crisis language detected — {config.PARENT_NAME} expressed distress",
            "attribution": (
                "Expressions of wanting to die require immediate caregiver response. "
                "Call Margaret now. If she may be in immediate danger, "
                "contact the 988 Suicide & Crisis Lifeline or call 911."
            ),
            "icon": "🆘",
        })
    else:
        lonely_entries = [
            e for e in history_week
            if any(s.lower() in _LONELY for s in e.get("symptoms", []))
        ]
        if lonely_entries:
            days = len(lonely_entries)
            score += min(30, days * 12)
            alerts.append({
                "type": "mental_health",
                "severity": "high" if days >= 2 else "medium",
                "message": (
                    f"Loneliness or low mood reported {days} time{'s' if days > 1 else ''} this week"
                ),
                "attribution": (
                    "Social isolation and persistent low mood are significant risk factors "
                    "for depression in elderly adults. A phone call or visit can have an "
                    "outsized impact — even a short conversation helps."
                ),
                "icon": "💙",
            })

    score = min(100, score)
    level = "critical" if score >= 75 else ("high" if score >= 50 else ("medium" if score >= 25 else "low"))

    return {
        "level": level,
        "score": score,
        "alerts": alerts,
        "baseline_sleep": baseline_sleep,
        "recent_sleep": recent_sleep,
        "sufficient_data": True,
    }


def generate_predictive_insight() -> dict | None:
    """
    Scan the last 14 days for leading-indicator patterns and return a
    forward-looking prediction card, or None if no prediction is warranted.

    Returns:
        {"icon", "title", "body", "confidence"} or None
    """
    today = datetime.now(timezone.utc).date()
    history14 = query_history(days=14)
    history7  = [e for e in history14 if e.get("date", "") >= (today - timedelta(days=7)).isoformat()]
    history_prior = [e for e in history14 if e.get("date", "") < (today - timedelta(days=7)).isoformat()]

    if len(history14) < 4:
        return None

    # ── Pattern 1: Sleep debt accumulation → fatigue / pain likely in 48h ────
    sorted_recent = sorted(history7, key=lambda x: x.get("date", ""), reverse=True)
    low_streak = 0
    low_sleep_vals = []
    for e in sorted_recent:
        slp = e.get("sleep_hours")
        if slp is not None and float(slp) < config.SLEEP_WARNING_HOURS:
            low_streak += 1
            low_sleep_vals.append(float(slp))
        else:
            break

    if low_streak >= 3:
        avg_slp = round(sum(low_sleep_vals) / len(low_sleep_vals), 1)
        return {
            "icon": "🔮",
            "title": f"{low_streak} nights of poor sleep — heads up for the next 48h",
            "body": (
                f"{config.PARENT_NAME} has had {low_streak} consecutive nights below "
                f"{config.SLEEP_WARNING_HOURS}h (averaging {avg_slp}h). "
                f"This pattern is a leading indicator for increased fatigue and joint discomfort "
                f"within 48 hours. A gentle check-in call today could get ahead of it."
            ),
            "confidence": 74,
        }

    # ── Pattern 2: Dizziness accelerating → elevated fall risk this week ─────
    diz_recent = sum(1 for e in history7 for s in e.get("symptoms", []) if s.lower() == "dizziness")
    diz_prior  = sum(1 for e in history_prior for s in e.get("symptoms", []) if s.lower() == "dizziness")

    if diz_recent >= 3 and diz_recent > diz_prior:
        return {
            "icon": "📈",
            "title": "Dizziness trend is accelerating — fall risk elevated",
            "body": (
                f"Dizziness reported {diz_recent}× this week vs {diz_prior}× the prior week — "
                f"an upward trajectory. If the trend continues, fall risk increases significantly. "
                f"Recommend confirming {config.PARENT_NAME} is hydrating well and that grab bars "
                f"are within reach in the bathroom."
            ),
            "confidence": 68,
        }

    # ── Pattern 3: Multi-symptom co-occurrence → possible illness onset ───────
    syms_this_week = [s.lower() for e in history7 for s in e.get("symptoms", [])]
    unique_syms = set(syms_this_week)
    compound = {"dizziness", "fatigue", "low appetite"} & unique_syms
    if len(compound) >= 3:
        return {
            "icon": "🩺",
            "title": "3 symptoms co-occurring — possible illness onset",
            "body": (
                f"Dizziness, fatigue, and low appetite have all been reported this week. "
                f"This triad — rather than any single symptom — can indicate an underlying "
                f"illness, dehydration, or medication side-effect. Worth a check-in call and "
                f"potentially a physician review if the pattern persists past today."
            ),
            "confidence": 65,
        }

    return None


def get_checkin_streak() -> int:
    """Number of consecutive days with at least one log entry."""
    history = query_history(days=30)
    if not history:
        return 0

    dates = sorted({e["date"] for e in history}, reverse=True)
    today = datetime.now(timezone.utc).date().isoformat()

    streak = 0
    expected = today
    for d in dates:
        if d == expected:
            streak += 1
            dt = datetime.fromisoformat(expected) - timedelta(days=1)
            expected = dt.strftime("%Y-%m-%d")
        else:
            break
    return streak
