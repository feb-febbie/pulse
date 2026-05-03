"""
PulseCare — Apple Health meets Zen aesthetic.

Views:
  ?view=caregiver  (default)  Sarah's dashboard — tabs: home / data / watch / report
  ?view=senior                Margaret's companion + garden
  ?view=setup                 Patient profile onboarding questionnaire
"""
from __future__ import annotations

import streamlit as st

from datetime import datetime, date as _date, timedelta, timezone

import config
from graph.workflow import get_graph
from graph.state import initial_state
from tools.memory_tools import (
    query_history, seed_demo_data, reset_health_data,
    record_family_view, get_last_family_view,
)
from tools.alert_tools import compute_risk_level, get_checkin_streak, generate_predictive_insight
from tools.report_tools import generate_health_timeline
from tools.watch_tools import (
    seed_watch_data, get_watch_summary,
    get_hr_series, get_steps_series, get_sleep_stages,
)
from tools.profile_tools import (
    seed_demo_profile, get_patient_profile, save_patient_profile,
)

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="PulseCare", page_icon="💚", layout="centered",
                   initial_sidebar_state="collapsed")

@st.cache_resource
def _seed():
    # Wipe only live demo check-ins; keep 14-day seeded arc + watch history intact
    reset_health_data()
    seed_demo_data()
    seed_watch_data()   # idempotent — only seeds if watch_data is empty
    seed_demo_profile() # always restores Margaret's profile
_seed()

# ── Demo reset (?reset=1) — wipes live entries, re-seeds, returns to caregiver home ──
if st.query_params.get("reset") == "1":
    reset_health_data()
    seed_demo_data()
    seed_watch_data()
    seed_demo_profile()
    st.cache_resource.clear()
    for _k in list(st.session_state.keys()):
        del st.session_state[_k]
    st.query_params.clear()
    st.query_params["view"] = "caregiver"
    st.rerun()

_view = st.query_params.get("view", "caregiver")
_tab  = st.query_params.get("tab",  "home")
_msg  = st.query_params.get("msg",  "")
if _msg:
    st.session_state._submit = _msg
    st.query_params.clear()
    st.query_params["view"] = "senior"

for k, v in [("messages", []), ("report_text", ""), ("last_analyst_response", ""),
              ("watch_connected", True), ("just_checked_in", False), ("cg_tab", "home")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# GARDEN ENGINE
# ══════════════════════════════════════════════════════════════════════════════

_STAGES = [
    (0,  "Seed",        "🌱", "Just planted — waiting to bloom"),
    (3,  "Sprout",      "🌼", "Starting to bloom with each check-in"),
    (7,  "Budding",     "🌷", "Growing steadily, day by day"),
    (14, "Blooming",    "🌸", "In full bloom — getting lovelier every week"),
    (21, "Flourishing", "🌺", "Flourishing — a truly beautiful habit"),
    (30, "Garden",      "💐", "A garden in full flower — truly thriving"),
    (45, "Paradise",    "🌻", "An extraordinary garden — paradise!"),
]

def get_garden_state(history: list) -> dict:
    total = len(history)
    stage = _STAGES[0]
    for s in _STAGES:
        if total >= s[0]:
            stage = s
    threshold, name, emoji, desc = stage
    idx = next((i for i, s in enumerate(_STAGES) if s[0] == threshold), 0)
    nxt = _STAGES[idx + 1] if idx + 1 < len(_STAGES) else None
    return {
        "name": name, "emoji": emoji, "desc": desc, "total": total,
        "idx": idx,
        "to_next": (nxt[0] - total) if nxt else 0,
        "next_name": nxt[1] if nxt else None,
        "current_thresh": threshold,
    }


def _garden_html(state: dict, animate_water: bool, compact: bool = False) -> str:
    """Return garden HTML using block/flex layout only — no position:absolute, no <style> block."""
    g = state
    idx = g["idx"]

    sky_map = {
        "Seed":        ("#D4C8D8", "#E8D4E0"),
        "Sprout":      ("#C4D8EC", "#E4D4C4"),
        "Budding":     ("#B4D4EC", "#ECC4C4"),
        "Blooming":    ("#A4C8EC", "#F4B8C8"),
        "Flourishing": ("#90BCEC", "#F0A8BC"),
        "Garden":      ("#7EB4EC", "#F498B0"),
        "Paradise":    ("#68A8EC", "#F4D060"),
    }
    sky_top, sky_btm = sky_map.get(g["name"], ("#A0CCEC", "#B8E498"))

    h_sky   = 50 if compact else 72
    h_plant = 74 if compact else 108
    h_grass = 16 if compact else 22
    h_soil  = 32 if compact else 40
    p_sz    = 54 if compact else 88
    sun_sz  = 24 if compact else 32
    font_sm = 13 if compact else 17
    cloud2  = "☁️ " if idx >= 2 and not compact else ""
    bf      = ('<span style="display:inline-block;animation:gdn-flutter 2.8s ease-in-out infinite;font-size:16px;">🦋</span> '
               if idx >= 4 and not compact else "")
    fl      = ("🌼" if idx >= 5 else "")
    fr      = ("🌸" if idx >= 5 else "")
    glow    = "box-shadow:0 0 0 3px rgba(107,158,120,0.45);" if animate_water else ""

    drops = ""
    if animate_water:
        drops = ('<span style="font-size:17px;display:inline-block;animation:gdn-drop 1.4s 0s ease-in both;">💧</span>'
                 '<span style="font-size:17px;display:inline-block;animation:gdn-drop 1.4s 0.25s ease-in both;">💧</span>'
                 '<span style="font-size:17px;display:inline-block;animation:gdn-drop 1.4s 0.5s ease-in both;">💧</span>')

    if g["to_next"] and g["next_name"]:
        stage_range = max(g["to_next"] + g["total"] - g["current_thresh"], 1)
        pct = max(6, min(94, int((g["total"] - g["current_thresh"]) / stage_range * 100)))
        progress = (
            f'<div style="padding:12px 18px 4px;font-family:-apple-system,sans-serif;">'
            f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:700;color:#6B9E78;margin-bottom:6px;">'
            f'<span>{g["name"]}</span><span>{g["to_next"]} to {g["next_name"]}</span></div>'
            f'<div style="background:#D4EAD9;border-radius:6px;height:6px;overflow:hidden;">'
            f'<div style="width:{pct}%;background:linear-gradient(to right,#6B9E78,#90C49C);height:100%;border-radius:6px;"></div>'
            f'</div></div>'
        )
    else:
        progress = '<div style="padding:10px 18px 2px;text-align:center;font-size:13px;color:#6B9E78;font-weight:700;font-family:-apple-system,sans-serif;">🌺 Flourishing — the full garden achieved!</div>'

    return (
        f'<div style="border-radius:24px;overflow:hidden;{glow}">'
        # ── Sky row ──────────────────────────────────────────────────────────
        f'<div style="height:{h_sky}px;background:linear-gradient(to bottom,{sky_top},{sky_btm});'
        f'display:flex;align-items:flex-start;justify-content:space-between;'
        f'padding:12px 14px 0 14px;box-sizing:border-box;">'
        f'<div style="display:flex;align-items:center;gap:6px;font-size:{font_sm}px;opacity:0.8;">'
        f'☁️ {cloud2}{bf}</div>'
        f'<div style="width:{sun_sz}px;height:{sun_sz}px;flex-shrink:0;'
        f'background:radial-gradient(circle at 36% 35%,#FFF0A8,#FFB300);border-radius:50%;'
        f'animation:gdn-sun 3.5s ease-in-out infinite;"></div>'
        f'</div>'
        # ── Plant row ─────────────────────────────────────────────────────────
        f'<div style="height:{h_plant}px;background:{sky_btm};'
        f'display:flex;flex-direction:column;align-items:center;justify-content:flex-end;">'
        f'<div style="height:22px;display:flex;align-items:center;justify-content:center;gap:2px;">{drops}</div>'
        f'<div style="font-size:{p_sz}px;line-height:1;display:inline-block;margin-bottom:-4px;'
        f'animation:gdn-sway 4.5s ease-in-out infinite;transform-origin:bottom center;'
        f'filter:drop-shadow(0 4px 10px rgba(0,0,0,0.18));">{g["emoji"]}</div>'
        f'</div>'
        # ── Grass strip ───────────────────────────────────────────────────────
        f'<div style="height:{h_grass}px;background:linear-gradient(to bottom,#88C060,#6BA840);"></div>'
        # ── Soil strip + label ────────────────────────────────────────────────
        f'<div style="height:{h_soil}px;background:linear-gradient(to bottom,#8D6E63,#6D4C41);'
        f'display:flex;align-items:center;justify-content:center;gap:8px;">'
        f'<span style="font-size:{font_sm}px;opacity:0.75;">{fl}</span>'
        f'<span style="font-size:{"10" if compact else "11"}px;font-weight:800;'
        f'color:rgba(255,255,255,0.9);letter-spacing:0.8px;font-family:-apple-system,sans-serif;">'
        f'{g["name"].upper()} · {g["total"]} CHECK-INS</span>'
        f'<span style="font-size:{font_sm}px;opacity:0.75;">{fr}</span>'
        f'</div>'
        f'</div>'
        f'{progress}'
    )


def _garden_split_html(state: dict, animate_water: bool, compact: bool = False) -> str:
    """Two-panel garden: emoji plant grid LEFT, scenic animated garden RIGHT."""
    g = state
    _plants = {
        "Seed":        ["🌱"],
        "Sprout":      ["🌼", "🌱"],
        "Budding":     ["🌷", "🌼", "🌷"],
        "Blooming":    ["🌸", "🌷", "🌸", "🌸"],
        "Flourishing": ["🌺", "🌸", "🌺", "🌸", "🌺"],
        "Garden":      ["💐", "🌺", "🌸", "💐", "🌸", "🌺"],
        "Paradise":    ["🌻", "💐", "🌺", "🌻", "🌸", "💐", "🌻"],
    }

    sky_map = {
        "Seed":        ("#D4C8D8", "#E8D4E0"),
        "Sprout":      ("#C4D8EC", "#E4D4C4"),
        "Budding":     ("#B4D4EC", "#ECC4C4"),
        "Blooming":    ("#A4C8EC", "#F4B8C8"),
        "Flourishing": ("#90BCEC", "#F0A8BC"),
        "Garden":      ("#7EB4EC", "#F498B0"),
        "Paradise":    ("#68A8EC", "#F4D060"),
    }
    sky_top, sky_btm = sky_map.get(g["name"], ("#A0CCEC", "#B8E498"))

    # Progress within current stage
    if g["to_next"] and g["current_thresh"] is not None:
        span   = g["to_next"]
        earned = max(0, g["total"] - g["current_thresh"])
        pct    = min(100, int(earned / span * 100)) if span else 100
    else:
        pct = 100

    # Left panel: emoji grid + progress
    plants = _plants.get(g["name"], ["🌱"])
    grid_html = "".join(
        f'<span style="font-size:{"18" if compact else "22"}px;margin:2px;">{p}</span>'
        for p in plants)
    next_badge = ""
    if g["next_name"]:
        next_badge = (
            f'<div style="margin-top:8px;background:rgba(107,158,120,0.15);'
            f'border-radius:10px;padding:3px 8px;display:inline-block;'
            f'font-size:10px;font-weight:800;color:#5A8A6A;">'
            f'{g["to_next"]} → {g["next_name"]}</div>'
        )
    progress_bar = (
        f'<div style="height:4px;background:#E8F0EA;border-radius:3px;overflow:hidden;margin-top:6px;">'
        f'<div style="width:{pct}%;height:100%;'
        f'background:linear-gradient(90deg,#6B9E78,#90C49C);border-radius:3px;"></div>'
        f'</div>'
    ) if g["to_next"] else ""

    left = (
        f'<div style="flex:0 0 42%;padding:{"10" if compact else "14"}px 6px '
        f'{"10" if compact else "14"}px 10px;'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
        f'border-right:1px solid rgba(0,0,0,0.06);background:#FAFDF9;'
        f'border-radius:24px 0 0 24px;">'
        f'<div style="font-size:9px;font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1px;color:#9CA3AF;margin-bottom:6px;">My Garden</div>'
        f'<div style="line-height:1.6;text-align:center;">{grid_html}</div>'
        f'<div style="font-size:{"11" if compact else "13"}px;font-weight:700;'
        f'color:#2D2D2D;margin-top:5px;">{g["name"]}</div>'
        f'<div style="font-size:10px;color:#9CA3AF;margin-top:1px;">{g["total"]} check-ins</div>'
        f'{progress_bar}{next_badge}'
        f'</div>'
    )

    # Right panel: scenic garden (no progress bar — inline)
    h_sky   = 44 if compact else 62
    h_plant = 60 if compact else 88
    h_grass = 13 if compact else 18
    h_soil  = 26 if compact else 34
    p_sz    = 42 if compact else 66
    sun_sz  = 18 if compact else 24
    font_sm = 11 if compact else 14

    drops = ""
    if animate_water:
        drops = (
            '<span style="font-size:14px;display:inline-block;animation:gdn-drop 1.4s 0s ease-in both;">💧</span>'
            '<span style="font-size:14px;display:inline-block;animation:gdn-drop 1.4s 0.25s ease-in both;">💧</span>'
            '<span style="font-size:14px;display:inline-block;animation:gdn-drop 1.4s 0.5s ease-in both;">💧</span>'
        )
    glow = "box-shadow:inset 0 0 0 2px rgba(107,158,120,0.45);" if animate_water else ""
    bf = ('<span style="display:inline-block;animation:gdn-flutter 2.8s ease-in-out infinite;'
          'font-size:12px;">🦋</span>' if g["idx"] >= 4 and not compact else "")
    fl = "🌼" if g["idx"] >= 5 else ""
    fr = "🌸" if g["idx"] >= 5 else ""

    right = (
        f'<div style="flex:1;overflow:hidden;border-radius:0 24px 24px 0;{glow}">'
        # sky
        f'<div style="height:{h_sky}px;background:linear-gradient(to bottom,{sky_top},{sky_btm});'
        f'display:flex;align-items:flex-start;justify-content:space-between;'
        f'padding:8px 10px 0 10px;box-sizing:border-box;">'
        f'<div style="font-size:{font_sm}px;opacity:0.8;">☁️ {bf}</div>'
        f'<div style="width:{sun_sz}px;height:{sun_sz}px;flex-shrink:0;'
        f'background:radial-gradient(circle at 36% 35%,#FFF0A8,#FFB300);border-radius:50%;'
        f'animation:gdn-sun 3.5s ease-in-out infinite;"></div>'
        f'</div>'
        # plant
        f'<div style="height:{h_plant}px;background:{sky_btm};'
        f'display:flex;flex-direction:column;align-items:center;justify-content:flex-end;">'
        f'<div style="height:18px;display:flex;align-items:center;gap:1px;">{drops}</div>'
        f'<div style="font-size:{p_sz}px;line-height:1;display:inline-block;margin-bottom:-3px;'
        f'animation:gdn-sway 4.5s ease-in-out infinite;transform-origin:bottom center;'
        f'filter:drop-shadow(0 3px 8px rgba(0,0,0,0.15));">{g["emoji"]}</div>'
        f'</div>'
        # grass
        f'<div style="height:{h_grass}px;background:linear-gradient(to bottom,#88C060,#6BA840);"></div>'
        # soil
        f'<div style="height:{h_soil}px;background:linear-gradient(to bottom,#8D6E63,#6D4C41);'
        f'display:flex;align-items:center;justify-content:center;gap:5px;">'
        f'<span style="font-size:{font_sm}px;opacity:0.75;">{fl}</span>'
        f'<span style="font-size:{"9" if compact else "10"}px;font-weight:800;'
        f'color:rgba(255,255,255,0.85);letter-spacing:0.6px;font-family:-apple-system,sans-serif;">'
        f'{g["name"].upper()}</span>'
        f'<span style="font-size:{font_sm}px;opacity:0.75;">{fr}</span>'
        f'</div>'
        f'</div>'
    )

    outer_h = 174 if compact else 240
    return (
        f'<div style="display:flex;border-radius:24px;overflow:hidden;'
        f'height:{outer_h}px;background:#fff;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.09);">'
        f'{left}{right}'
        f'</div>'
    )


def _garden_two_stage_html(state: dict, compact: bool = False) -> str:
    """Equal-split two-panel garden: current stage LEFT, next stage RIGHT."""
    g = state
    _plants = {
        "Seed":        ["🌱"],
        "Sprout":      ["🌼", "🌱"],
        "Budding":     ["🌷", "🌼", "🌷"],
        "Blooming":    ["🌸", "🌷", "🌸", "🌸"],
        "Flourishing": ["🌺", "🌸", "🌺", "🌸", "🌺"],
        "Garden":      ["💐", "🌺", "🌸", "💐", "🌸", "🌺"],
        "Paradise":    ["🌻", "💐", "🌺", "🌻", "🌸", "💐", "🌻"],
    }

    em_sz  = "18px" if compact else "22px"
    hd_sz  = "9px"  if compact else "10px"
    nm_sz  = "12px" if compact else "14px"
    sub_sz = "10px" if compact else "11px"
    bi_sz  = "28px" if compact else "36px"
    pad    = "10px 8px" if compact else "16px 10px"

    def _grid(name: str) -> str:
        plants = _plants.get(name, ["🌱"])
        return "".join(f'<span style="font-size:{em_sz};margin:2px;">{p}</span>' for p in plants)

    # Progress % within current stage
    if g["to_next"] and g["current_thresh"] is not None:
        span   = g["to_next"]
        earned = max(0, g["total"] - g["current_thresh"])
        pct    = min(100, int(earned / span * 100)) if span else 100
    else:
        pct = 100

    # Current stage panel
    cur_panel = (
        f'<div style="flex:1;background:rgba(107,158,120,0.10);border-radius:14px;'
        f'padding:{pad};text-align:center;">'
        f'<div style="font-size:{hd_sz};font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1.2px;color:#9CA3AF;margin-bottom:6px;">Today</div>'
        f'<div style="font-size:{bi_sz};animation:gdn-sway 4.5s ease-in-out infinite;'
        f'display:inline-block;transform-origin:bottom center;">{g["emoji"]}</div>'
        f'<div style="font-size:{nm_sz};font-weight:700;color:#2D2D2D;margin-top:5px;">{g["name"]}</div>'
        f'<div style="font-size:{sub_sz};color:#9CA3AF;margin-top:2px;">{g["total"]} days</div>'
        f'<div style="margin-top:8px;line-height:1.9;">{_grid(g["name"])}</div>'
        f'</div>'
    )

    # Next stage panel
    if g["next_name"] and g["idx"] + 1 < len(_STAGES):
        nxt_emoji = _STAGES[g["idx"] + 1][2]
        days_lbl  = f'{g["to_next"]} day{"s" if g["to_next"] != 1 else ""} away'
        next_panel = (
            f'<div style="display:flex;align-items:center;justify-content:center;'
            f'color:#C8C2BC;font-size:14px;padding:0 3px;flex-shrink:0;">→</div>'
            f'<div style="flex:1;background:rgba(245,242,238,0.75);border-radius:14px;'
            f'padding:{pad};text-align:center;opacity:0.6;">'
            f'<div style="font-size:{hd_sz};font-weight:800;text-transform:uppercase;'
            f'letter-spacing:1.2px;color:#9CA3AF;margin-bottom:6px;">Coming up</div>'
            f'<div style="font-size:{bi_sz};">{nxt_emoji}</div>'
            f'<div style="font-size:{nm_sz};font-weight:700;color:#6B7280;margin-top:5px;">'
            f'{g["next_name"]}</div>'
            f'<div style="margin-top:5px;background:rgba(107,158,120,0.18);border-radius:8px;'
            f'padding:3px 8px;display:inline-block;'
            f'font-size:{sub_sz};font-weight:800;color:#5A8A6A;">{days_lbl}</div>'
            f'<div style="margin-top:8px;line-height:1.9;">{_grid(g["next_name"])}</div>'
            f'</div>'
        )
    else:
        next_panel = (
            f'<div style="flex:1;text-align:center;padding:{pad};'
            f'background:rgba(107,158,120,0.06);border-radius:14px;">'
            f'<div style="font-size:28px;">🌺</div>'
            f'<div style="font-size:{nm_sz};font-weight:700;color:#6B9E78;margin-top:6px;">'
            f'Flourishing!</div>'
            f'<div style="font-size:{sub_sz};color:#9CA3AF;margin-top:2px;">Full garden achieved</div>'
            f'</div>'
        )

    progress_bar = (
        f'<div style="padding:8px 14px 4px;font-family:-apple-system,sans-serif;">'
        f'<div style="height:5px;background:#EDE9E4;border-radius:3px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;'
        f'background:linear-gradient(90deg,#6B9E78,#90C49C);border-radius:3px;"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:10px;color:#9CA3AF;margin-top:4px;">'
        f'<span>{g["name"]}</span>'
        f'<span>{pct}% → {g["next_name"] or "Max"}</span>'
        f'</div></div>'
    ) if g["to_next"] else ""

    outer_pad = "10px 14px 8px" if compact else "14px 16px 8px"
    return (
        f'<div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
        f'<div style="padding:{outer_pad};">'
        f'<div style="font-size:10px;font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1.2px;color:#6B9E78;margin-bottom:10px;">🌱 Garden</div>'
        f'<div style="display:flex;align-items:stretch;gap:6px;">'
        f'{cur_panel}'
        f'{next_panel}'
        f'</div>'
        f'</div>'
        f'{progress_bar}'
        f'</div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMPATHETIC SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def _tldr(risk_data: dict, name: str, avg_sleep, symp_days: int) -> str:
    level  = risk_data.get("level", "low")
    alerts = risk_data.get("alerts", [])
    types  = {a["type"] for a in alerts}
    if level == "low":
        return f"{name} is having a good week — all her signals look normal. 💚"
    if "fall_risk" in types and "sleep" in types:
        return f"{name} hasn't been sleeping well lately, which may be connected to the dizziness she's been feeling."
    if "fall_risk" in types:
        return f"{name} has felt dizzy a few times this week — worth a gentle check-in call today."
    if "sleep" in types:
        slp = f"{avg_sleep}h" if avg_sleep else "lighter than usual"
        return f"{name} is sleeping only {slp} on average — she may be feeling tired and off."
    if "symptom_spike" in types:
        return f"{name} has had more symptoms than usual — she might be coming down with something."
    if "isolation" in types:
        return f"{name} seems to be staying in more and eating less — a gentle check-in might brighten her day."
    return f"{name} is a little off her usual baseline this week — worth keeping a gentle eye on."


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Garden animations ───────────────────────────────────────────────────── */
@keyframes gdn-sway{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(2.5deg) translateY(-5px)}}
@keyframes gdn-flutter{0%,100%{transform:translate(0,0) rotate(-10deg)}50%{transform:translate(4px,-6px) rotate(10deg)}}
@keyframes gdn-sun{0%,100%{box-shadow:0 0 14px 3px rgba(255,210,50,0.35)}50%{box-shadow:0 0 28px 8px rgba(255,210,50,0.55)}}
@keyframes gdn-drop{0%{opacity:0;transform:translateY(-8px)}15%{opacity:1}100%{opacity:0;transform:translateY(28px)}}

/* ── Hide chrome ─────────────────────────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stSidebar"], [data-testid="collapsedControl"],
.stDeployButton { display: none !important; }

/* ── Page background ─────────────────────────────────────────────────────── */
html, body, [data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"], section[data-testid="stMain"] {
    background: #0D0D0D !important;
    overflow: visible !important;
    height: auto !important;
}

/* ── Phone frame ─────────────────────────────────────────────────────────── */
[data-testid="stMainBlockContainer"] {
    max-width: 390px !important;
    margin: 24px auto !important;
    padding: 0 !important;
    background: #F2F2F7 !important;
    border-radius: 52px !important;
    overflow-x: hidden !important;
    overflow-y: visible !important;
    height: auto !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    box-shadow:
        0 0 0 1px #3A3A3C,
        0 0 0 5px #222,
        0 50px 120px rgba(0,0,0,0.9) !important;
}
[data-testid="stMainBlockContainer"]::-webkit-scrollbar { display: none !important; }
[data-testid="stVerticalBlock"] { padding: 0 !important; gap: 0 !important; }

/* ── Dynamic Island + Status Bar ─────────────────────────────────────────── */
.di-wrap { background:#fff;display:flex;justify-content:center;padding:14px 0 0 0; }
.di-pill { width:120px;height:34px;background:#000;border-radius:18px; }
.sbar    { display:flex;align-items:center;justify-content:space-between;
           padding:6px 28px 10px 28px;font-size:13px;font-weight:700;
           font-family:-apple-system,BlinkMacSystemFont,sans-serif;
           background:#fff;color:#1C1C1E; }

/* ── Full-width section (no floating) ────────────────────────────────────── */
.fwsec {
    background:#fff;
    border-top:1px solid rgba(0,0,0,0.07);
    border-bottom:1px solid rgba(0,0,0,0.07);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}
.fwsec-pad { padding:16px 20px; }
.fwsec-divider { height:1px;background:rgba(0,0,0,0.06);margin:0 20px; }

/* ── Horizontal blocks: shared reset ─────────────────────────────────────── */
[data-testid="stHorizontalBlock"] { gap:0 !important;margin:0 !important; }

/* ── Tab bar: the 4-column stHorizontalBlock at the bottom ──────────────── */
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) {
    background:rgba(247,245,242,0.96) !important;
    backdrop-filter:blur(20px) !important;-webkit-backdrop-filter:blur(20px) !important;
    border-top:1px solid rgba(0,0,0,0.08) !important;
    padding:4px 0 22px 0 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) [data-testid="stColumn"] {
    padding:0 !important;min-width:0 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button {
    background:transparent !important;border:none !important;box-shadow:none !important;
    border-radius:0 !important;height:52px !important;width:100% !important;
    font-family:-apple-system,BlinkMacSystemFont,sans-serif !important;
    padding:0 !important;color:#C0BAB4 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button p {
    margin:0 !important;line-height:1.2 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button p:first-child {
    font-size:22px !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button p:last-child {
    font-size:10px !important;font-weight:700 !important;letter-spacing:0.3px !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button:hover {
    background:rgba(0,0,0,0.03) !important;color:#C0BAB4 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button[kind="primary"],
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) .stButton > button[kind="primary"]:hover {
    background:transparent !important;color:#6B9E78 !important;
    border:none !important;box-shadow:none !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(4)) [data-testid="stMarkdownContainer"] {
    display:flex !important;flex-direction:column !important;
    align-items:center !important;gap:1px !important;
}

/* ── Page header row: the 2-column back-button + title stHorizontalBlock ── */
[data-testid="stHorizontalBlock"]:not(:has([data-testid="stColumn"]:nth-child(4))) {
    background:#fff !important;border-bottom:1px solid rgba(0,0,0,0.07) !important;
    padding:8px 12px 8px 4px !important;align-items:center !important;
}
[data-testid="stHorizontalBlock"]:not(:has([data-testid="stColumn"]:nth-child(4))) .stButton > button {
    background:transparent !important;border:none !important;box-shadow:none !important;
    border-radius:0 !important;height:44px !important;
    font-size:22px !important;font-weight:700 !important;color:#6B9E78 !important;padding:0 !important;
}

/* ── Cards ───────────────────────────────────────────────────────────────── */
.card {
    background:#fff;border-radius:16px;
    margin:0 16px 12px 16px;padding:18px;
    box-shadow:0 1px 6px rgba(0,0,0,0.07);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}

/* ── Page header (non-home tabs) ─────────────────────────────────────────── */
.pg-header {
    display:flex;align-items:center;gap:14px;
    background:#fff;padding:14px 20px;
    border-bottom:1px solid rgba(0,0,0,0.07);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}
.pg-back { font-size:22px;text-decoration:none;color:#6B9E78;font-weight:700; }
.pg-title { font-size:19px;font-weight:800;color:#2D2D2D; }
.pg-sub   { font-size:13px;color:#9CA3AF;margin-top:2px; }

/* ── Caregiver home header ───────────────────────────────────────────────── */
.cg-header {
    background:#fff;
    padding:16px 20px 14px 20px;
    border-bottom:1px solid rgba(0,0,0,0.07);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}
.cg-lbl  { font-size:11px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:4px; }
.cg-name { font-size:26px;font-weight:800;color:#2D2D2D;margin-bottom:2px; }
.cg-sub  { font-size:14px;color:#6B7280; }

/* ── Wellbeing pill ──────────────────────────────────────────────────────── */
.wb-pill { display:inline-flex;align-items:center;gap:7px;padding:8px 18px;
           border-radius:24px;font-size:15px;font-weight:700;margin-top:10px;
           font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.wb-well  { background:#EAF4EE;color:#3D6B47;border:1.5px solid #A8D4A8; }
.wb-watch { background:#EFF3F7;color:#4A6278;border:1.5px solid #B0C4D8; }
.wb-attn  { background:#FDF5F2;color:#7A4232;border:1.5px solid #DDB0A0; }
.wb-care  { background:#FDF0ED;color:#6B2D1E;border:1.5px solid #D49080; }

/* ── TL;DR card ──────────────────────────────────────────────────────────── */
.tldr-card {
    background:#fff;border-radius:16px;
    margin:12px 16px 0 16px;padding:16px 18px;
    border-left:4px solid #6B9E78;
    box-shadow:0 1px 6px rgba(0,0,0,0.07);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}
.tldr-lbl  { font-size:11px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px; }
.tldr-text { font-size:16px;font-weight:600;color:#2D2D2D;line-height:1.5; }
.tldr-attn { border-left-color:#C9785A; }

/* ── Action buttons ──────────────────────────────────────────────────────── */
.action-row { display:flex;gap:8px;margin:12px 16px 14px 16px; }
.action-btn {
    flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;
    padding:12px 6px;background:#fff;
    border-radius:16px;border:1px solid rgba(0,0,0,0.09);
    text-decoration:none;box-shadow:0 1px 5px rgba(0,0,0,0.06);
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
}
.action-btn .ai { font-size:22px; }
.action-btn .al { font-size:11px;font-weight:700;color:#2D2D2D;text-align:center; }

/* ── Metric row ──────────────────────────────────────────────────────────── */
.mrow  { display:flex;background:#fff;border-bottom:1px solid rgba(0,0,0,0.06); }
.mtile { flex:1;text-align:center;padding:14px 8px;border-right:1px solid rgba(0,0,0,0.06);
         font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.mtile:last-child { border-right:none; }
.mv    { font-size:22px;font-weight:800;color:#2D2D2D;line-height:1; }
.ml    { font-size:10px;font-weight:700;color:#9CA3AF;margin-top:4px;
         text-transform:uppercase;letter-spacing:0.5px; }

/* ── Alert card ──────────────────────────────────────────────────────────── */
.acrd   { border-radius:16px;padding:14px 16px;margin-bottom:10px;
          font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.acrd-h { background:#FDF5F2;border-left:4px solid #C9785A; }
.acrd-m { background:#EFF3F7;border-left:4px solid #7B8FA3; }
.acrd-c { background:#FDF0ED;border-left:4px solid #B05040; }
.acrd-t { font-size:15px;font-weight:700;color:#2D2D2D;margin-bottom:4px; }
.acrd-b { font-size:13px;color:#4B5563;line-height:1.55; }

/* ── Alert icon rows ─────────────────────────────────────────────────────── */
.alrt-row { display:flex;align-items:center;gap:12px;padding:12px 16px;
            border-bottom:1px solid rgba(0,0,0,0.05);font-family:-apple-system,sans-serif; }
.alrt-row:last-child { border-bottom:none; }
.alrt-ico { width:36px;height:36px;border-radius:50%;display:flex;align-items:center;
            justify-content:center;font-size:17px;flex-shrink:0; }
.alrt-ico-h { background:#FDF5F2; }
.alrt-ico-c { background:#FDF0ED; }
.alrt-ico-m { background:#EFF3F7; }
.alrt-body { flex:1;min-width:0; }
.alrt-msg { font-size:14px;font-weight:700;color:#2D2D2D;line-height:1.3; }
.alrt-att { font-size:12px;color:#9CA3AF;margin-top:2px;line-height:1.4; }
.alrt-badge { font-size:10px;font-weight:800;padding:3px 8px;border-radius:8px;flex-shrink:0; }
.alrt-badge-h { background:#FDF5F2;color:#C9785A; }
.alrt-badge-c { background:#FDF0ED;color:#B05040; }
.alrt-badge-m { background:#EFF3F7;color:#7B8FA3; }

/* ── Check-in timeline rows ──────────────────────────────────────────────── */
.ci-row { display:flex;align-items:center;gap:0;padding:10px 16px;
          border-bottom:1px solid rgba(0,0,0,0.05);
          font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.ci-row:last-child { border-bottom:none; }
.ci-dot { width:4px;height:36px;border-radius:3px;flex-shrink:0;margin-right:12px; }
.ci-date { width:42px;flex-shrink:0; }
.ci-day  { font-size:17px;font-weight:800;color:#2D2D2D;line-height:1; }
.ci-mon  { font-size:10px;font-weight:700;color:#9CA3AF;text-transform:uppercase;
           letter-spacing:0.5px;margin-top:1px; }
.ci-chips { flex:1;min-width:0;display:flex;flex-wrap:wrap;gap:4px;align-items:center; }
.ci-right { display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0;margin-left:8px; }
.ci-slp  { font-size:12px;font-weight:700;color:#6B7280; }
.ci-sev  { font-size:11px;font-weight:800;color:#9CA3AF; }
.chip   { display:inline-block;border-radius:20px;padding:3px 9px;font-size:12px;
          font-weight:700;margin:0;background:#EAF4EE;color:#3D6B47; }
.chip-d { background:#FDF5F2;color:#7A4232; }
.chip-f { background:#FDF0ED;color:#6B2D1E; }

/* ── Report action cards ─────────────────────────────────────────────────── */
.rpt-act { display:flex;align-items:flex-start;gap:12px;padding:14px 16px;
           border-bottom:1px solid rgba(0,0,0,0.05);
           font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.rpt-act:last-child { border-bottom:none; }
.rpt-act-ico { font-size:22px;flex-shrink:0;width:32px;text-align:center; }
.rpt-act-title { font-size:14px;font-weight:700;color:#2D2D2D;margin-bottom:2px; }
.rpt-act-sub   { font-size:12px;color:#6B7280;line-height:1.4; }

/* ── Log card (kept for fallback) ────────────────────────────────────────── */
.lcrd { background:#fff;border-radius:14px;padding:14px 16px;
        margin-bottom:10px;box-shadow:0 1px 5px rgba(0,0,0,0.06);
        font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.lcrd-date { font-size:12px;font-weight:700;color:#9CA3AF;text-transform:uppercase;margin-bottom:8px; }
.lcrd-note { font-size:13px;color:#6B7280;font-style:italic;line-height:1.5;margin-top:5px; }
.slb    { display:inline-block;border-radius:20px;padding:2px 8px;font-size:12px;
          font-weight:700;margin-left:4px; }
.slb-g  { background:#EAF4EE;color:#3D6B47; }
.slb-w  { background:#FDF5F2;color:#7A4232; }
.slb-b  { background:#FDF0ED;color:#6B2D1E; }

/* ── Calendar ────────────────────────────────────────────────────────────── */
.cgrid { display:flex;flex-wrap:wrap;gap:4px;padding:4px 0 12px 0; }
.cday  { width:38px;height:44px;border-radius:10px;
         display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px; }
.cnum  { font-size:11px;font-weight:700; }
.csym  { font-size:15px; }

/* ── Watch cards ─────────────────────────────────────────────────────────── */
.whead { background:linear-gradient(135deg,#1C1C1E,#2A2A2E);border-radius:18px;
         padding:16px 18px;display:flex;align-items:center;gap:14px;
         margin-bottom:14px;font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.wface { width:52px;height:64px;background:#000;border-radius:16px;border:2px solid #3A3A3C;
         display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0; }
.bgrid { display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px; }
.bcrd  { background:#fff;border-radius:14px;padding:14px;
         box-shadow:0 1px 5px rgba(0,0,0,0.06);
         font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.bcrd-attn { border-top:3px solid #C9785A; }
.b-ico { font-size:20px;margin-bottom:5px; }
.b-val { font-size:26px;font-weight:800;line-height:1; }
.b-unt { font-size:11px;color:#9CA3AF;font-weight:600; }
.b-lbl { font-size:11px;font-weight:700;color:#9CA3AF;text-transform:uppercase;
         letter-spacing:0.5px;margin-top:5px; }
.b-attn{ font-size:12px;font-weight:700;color:#C9785A;margin-top:4px; }
.stgbar { display:flex;border-radius:10px;overflow:hidden;height:20px;margin:12px 0 8px 0; }
.sg     { display:flex;align-items:center;justify-content:center;
          font-size:10px;font-weight:700;color:rgba(255,255,255,0.9);min-width:3px; }
.sg-deep  { background:#6B6BC9; }
.sg-core  { background:#6B9EC9; }
.sg-rem   { background:#6BC9C9; }
.sg-awake { background:#C9C9C9; }
.sleg { display:flex;gap:10px;flex-wrap:wrap; }
.si   { display:flex;align-items:center;gap:5px;font-size:13px;
        color:#6B7280;font-family:-apple-system,sans-serif; }
.sd   { width:9px;height:9px;border-radius:50%;flex-shrink:0; }

/* ── Senior hero ─────────────────────────────────────────────────────────── */
.hero { background:linear-gradient(160deg,#3D6B47 0%,#6B9E78 55%,#8DBFA0 100%);
        padding:18px 28px 22px 28px;text-align:center; }
.hero-greeting { font-size:13px;font-weight:700;color:rgba(255,255,255,0.7);
                 text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;
                 font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.hero-name { font-size:28px;font-weight:800;color:#fff;margin-bottom:2px;
             font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.hero-tag  { font-size:14px;color:rgba(255,255,255,0.75);
             font-family:-apple-system,BlinkMacSystemFont,sans-serif; }

/* ── Feeling buttons ─────────────────────────────────────────────────────── */
.feel-q { font-size:22px;font-weight:800;color:#2D2D2D;text-align:center;
          padding:24px 24px 16px 24px;font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.feel-grid-sentinel { display:none; }
div.feel-grid-sentinel ~ div[data-testid="stHorizontalBlock"] button,
div.feel-grid-sentinel ~ div[data-testid="stHorizontalBlock"] button:focus,
div.feel-grid-sentinel ~ div[data-testid="stHorizontalBlock"] button:active {
    background: white !important;
    border: 2px solid rgba(107,158,120,0.22) !important;
    border-radius: 26px !important;
    padding: 24px 14px !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #2D2D2D !important;
    font-family: -apple-system,BlinkMacSystemFont,sans-serif !important;
    box-shadow: 0 3px 12px rgba(0,0,0,0.09) !important;
    min-height: 130px !important;
    white-space: pre-line !important;
    line-height: 1.75 !important;
}
div.feel-grid-sentinel ~ div[data-testid="stHorizontalBlock"] button:hover {
    background: rgba(107,158,120,0.07) !important;
    border-color: rgba(107,158,120,0.5) !important;
    transform: scale(1.02) !important;
}

/* ── Chat bubbles ────────────────────────────────────────────────────────── */
.bub-u { display:flex;justify-content:flex-end;padding:0 18px 12px 18px; }
.bub-p { display:flex;align-items:flex-end;gap:10px;padding:0 18px 12px 18px; }
.bc-u  { background:#6B9E78;color:#fff;border-radius:22px 5px 22px 22px;
          padding:14px 17px;max-width:80%;font-size:17px;line-height:1.55;
          font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.bc-p  { background:#fff;color:#2D2D2D;
          border-radius:5px 22px 22px 22px;padding:14px 17px;max-width:80%;
          font-size:17px;line-height:1.55;box-shadow:0 1px 6px rgba(0,0,0,0.08);
          font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
.pulse-av { width:36px;height:36px;background:linear-gradient(135deg,#3D6B47,#6B9E78);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:18px;flex-shrink:0; }

/* ── Streamlit widget overrides ──────────────────────────────────────────── */
[data-testid="stExpander"] { border:none !important;border-radius:0 !important;
    box-shadow:none !important;background:transparent !important; }
[data-testid="stExpander"] > div:first-child {
    background:#fff !important;
    border-bottom:1px solid rgba(0,0,0,0.07) !important;padding:16px 22px !important; }
details summary p { font-size:17px !important;font-weight:700 !important;
    color:#2D2D2D !important;font-family:-apple-system,BlinkMacSystemFont,sans-serif !important; }
[data-testid="stExpanderDetails"] { padding:16px 16px 20px 16px !important;
    background:#F2F2F7 !important; }
.stButton > button { border-radius:14px !important;font-weight:700 !important;
    font-size:16px !important;height:52px !important;
    font-family:-apple-system,BlinkMacSystemFont,sans-serif !important; }
[data-testid="stDownloadButton"] > button {
    background:#6B9E78 !important;color:#fff !important;border:none !important;
    border-radius:14px !important;font-weight:700 !important;
    width:100% !important;height:52px !important; }
.element-container iframe { pointer-events:none !important;height:0 !important;
    min-height:0 !important;display:block !important;overflow:hidden !important; }



</style>
""", unsafe_allow_html=True)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _phone_top():
    now = datetime.now().strftime("%H:%M")
    st.markdown(f"""
    <div class="di-wrap"><div class="di-pill"></div></div>
    <div class="sbar"><span>{now}</span>
    <div style="display:flex;gap:5px;font-size:12px;">⚡ WiFi 🔋</div></div>
    """, unsafe_allow_html=True)


def _bottom_nav(active: str, tabs: list) -> None:
    cols = st.columns(len(tabs))
    for i, (icon, label, tab_key) in enumerate(tabs):
        with cols[i]:
            btn_type = "primary" if tab_key == active else "secondary"
            if st.button(f"{icon}\n\n{label}", key=f"_nav_{tab_key}",
                         use_container_width=True, type=btn_type):
                st.session_state.cg_tab = tab_key
                st.rerun()


def _section_label(text: str) -> None:
    st.markdown(f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:1.2px;color:#9CA3AF;padding:16px 22px 8px 22px;'
                f'font-family:-apple-system,sans-serif;">{text}</div>', unsafe_allow_html=True)


# ── Daily Delight content pool ────────────────────────────────────────────────
_DAILY_DELIGHTS = [
    {"emoji": "🎵", "tag": "Memory Lane",
     "text": "What was your all-time favourite song when you were young — the one that always made you want to get up and dance?"},
    {"emoji": "🍳", "tag": "Memory Lane",
     "text": "What's the most delicious meal your mother or grandmother used to cook? The one that made the whole house smell wonderful?"},
    {"emoji": "📺", "tag": "Memory Lane",
     "text": "What was your favourite TV show back in the day — the one you'd never dream of missing?"},
    {"emoji": "👗", "tag": "Memory Lane",
     "text": "Do you remember your favourite outfit from when you were young? The one that made you feel like a million dollars?"},
    {"emoji": "🌙", "tag": "On This Day",
     "text": "In 1969, 600 million people stopped everything to watch Neil Armstrong take his first steps on the Moon. A moment the whole world shared together."},
    {"emoji": "🎸", "tag": "On This Day",
     "text": "In 1963, The Beatles recorded their entire first album in just one single day. The whole world was never quite the same after that."},
    {"emoji": "📷", "tag": "On This Day",
     "text": "In 1972, the Polaroid camera let people hold a photo in their hands just two minutes after taking it. People called it absolute magic."},
    {"emoji": "☀️", "tag": "Today's Thought",
     "text": "Even five minutes by the window with a warm cup of tea can do wonders for your spirits. Is the sun shining where you are today?"},
    {"emoji": "🎶", "tag": "Today's Thought",
     "text": "Did you know that humming a favourite song slows your breathing and calms your heart? Try it — and tell Pulse which song you chose!"},
    {"emoji": "🌿", "tag": "Today's Thought",
     "text": "A little bit of green — a plant on the windowsill or a walk past the garden — is one of the best things you can do for a good mood today."},
]


def _family_presence_banner(caregiver_name: str) -> str:
    """Return HTML for the family hug banner, or '' if caregiver hasn't been on recently."""
    from datetime import timezone as _tz
    last = get_last_family_view()
    if last is None:
        return ""
    now = datetime.now(_tz.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=_tz.utc)
    delta = now - last
    mins  = int(delta.total_seconds() / 60)
    hours = int(delta.total_seconds() / 3600)
    days  = delta.days
    if mins < 5:
        msg = f"{caregiver_name} is on the app right now — thinking of you 💖"
    elif hours < 1:
        msg = f"{caregiver_name} checked in on your garden {mins} minutes ago 🌻"
    elif hours < 3:
        msg = f"{caregiver_name} sent you a hug {hours} hour{'s' if hours > 1 else ''} ago 💖"
    elif days < 1:
        msg = f"{caregiver_name} was thinking of you earlier today 💛"
    elif days == 1:
        msg = f"{caregiver_name} checked in on you yesterday 🌿"
    elif days <= 3:
        msg = f"{caregiver_name} was here {days} days ago — she'll be back soon 💛"
    else:
        return ""
    return (
        '<div style="margin:10px 16px 0 16px;padding:13px 16px;'
        'background:linear-gradient(135deg,rgba(255,240,248,0.95),rgba(255,250,235,0.95));'
        'border-radius:18px;border:1.5px solid rgba(220,160,190,0.3);'
        'display:flex;align-items:center;gap:10px;'
        'font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
        '<span style="font-size:22px;flex-shrink:0;">👨‍👩‍👧</span>'
        f'<span style="font-size:14px;font-weight:600;color:#7A3B5E;line-height:1.4;">{msg}</span>'
        '</div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# PATIENT PROFILE SETUP
# ══════════════════════════════════════════════════════════════════════════════

if _view == "setup":
    _phone_top()
    profile = get_patient_profile()

    # ── Header ────────────────────────────────────────────────────────────────
    col_b, col_t = st.columns([1, 5])
    with col_b:
        if st.button("←", key="back_setup", use_container_width=True):
            st.query_params["view"] = "caregiver"
            st.rerun()
    with col_t:
        st.markdown('<div class="pg-title" style="padding:14px 0 2px 0;">Patient Profile</div>'
                    '<div class="pg-sub">Helps Pulse give specific, personalised advice</div>',
                    unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    with st.form("profile_form"):
        # ── Basic info ────────────────────────────────────────────────────────
        st.markdown('<div class="fwsec"><div class="fwsec-pad">'
                    '<div style="font-size:13px;font-weight:800;text-transform:uppercase;'
                    'letter-spacing:1px;color:#9CA3AF;margin-bottom:12px;">👤 Basic Info</div>',
                    unsafe_allow_html=True)
        p_name = st.text_input("Full name", value=profile.get("name", ""), label_visibility="visible")
        p_age  = st.number_input("Age", value=int(profile.get("age", 70)), min_value=50, max_value=120)
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Medical conditions ────────────────────────────────────────────────
        st.markdown('<div class="fwsec"><div class="fwsec-pad">'
                    '<div style="font-size:13px;font-weight:800;text-transform:uppercase;'
                    'letter-spacing:1px;color:#9CA3AF;margin-bottom:10px;">🩺 Medical Conditions</div>'
                    '<div style="font-size:12px;color:#9CA3AF;margin-bottom:8px;">One per line</div>',
                    unsafe_allow_html=True)
        conditions_default = "\n".join(profile.get("conditions", []))
        p_conditions = st.text_area("Conditions", value=conditions_default,
                                    height=110, label_visibility="collapsed")
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Medications ───────────────────────────────────────────────────────
        st.markdown('<div class="fwsec"><div class="fwsec-pad">'
                    '<div style="font-size:13px;font-weight:800;text-transform:uppercase;'
                    'letter-spacing:1px;color:#9CA3AF;margin-bottom:6px;">💊 Medications</div>'
                    '<div style="font-size:12px;color:#9CA3AF;margin-bottom:8px;">'
                    'Format: Name, Dose, When taken, Purpose, Any notes<br>'
                    'One medication per line</div>',
                    unsafe_allow_html=True)
        meds_lines = []
        for m in profile.get("medications", []):
            parts = [m.get("name",""), m.get("dose",""), m.get("time",""),
                     m.get("purpose",""), m.get("notes","")]
            meds_lines.append(", ".join(p for p in parts if p))
        p_meds = st.text_area("Medications", value="\n".join(meds_lines),
                              height=160, label_visibility="collapsed")
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Allergies + Doctor + Pharmacy ─────────────────────────────────────
        st.markdown('<div class="fwsec"><div class="fwsec-pad">'
                    '<div style="font-size:13px;font-weight:800;text-transform:uppercase;'
                    'letter-spacing:1px;color:#9CA3AF;margin-bottom:12px;">⚠️ Allergies & Care Team</div>',
                    unsafe_allow_html=True)
        p_allergies = st.text_input("Allergies (comma-separated)",
                                    value=", ".join(profile.get("allergies", [])))
        doc = profile.get("doctor", {})
        p_doc_name  = st.text_input("Doctor name", value=doc.get("name", ""))
        p_doc_phone = st.text_input("Doctor phone", value=doc.get("phone", ""))
        p_doc_spec  = st.text_input("Specialty / practice", value=f"{doc.get('specialty','')} · {doc.get('practice','')}")
        p_pharmacy  = st.text_input("Pharmacy", value=profile.get("pharmacy", ""))
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Lifestyle & notes ─────────────────────────────────────────────────
        st.markdown('<div class="fwsec"><div class="fwsec-pad">'
                    '<div style="font-size:13px;font-weight:800;text-transform:uppercase;'
                    'letter-spacing:1px;color:#9CA3AF;margin-bottom:10px;">🌿 About the Patient</div>'
                    '<div style="font-size:12px;color:#9CA3AF;margin-bottom:8px;">'
                    'Living situation, hobbies, personality — helps Pulse sound like a real friend</div>',
                    unsafe_allow_html=True)
        p_lifestyle = st.text_area("Lifestyle & personality",
                                   value=profile.get("lifestyle", "") + "\n\n" + profile.get("personality_notes", ""),
                                   height=130, label_visibility="collapsed")
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("💾  Save Profile", use_container_width=True, type="primary")

    if submitted:
        # Parse medications back into list of dicts
        meds_parsed = []
        for line in p_meds.strip().splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            meds_parsed.append({
                "name":      parts[0] if len(parts) > 0 else "",
                "dose":      parts[1] if len(parts) > 1 else "",
                "time":      parts[2] if len(parts) > 2 else "",
                "purpose":   parts[3] if len(parts) > 3 else "",
                "notes":     parts[4] if len(parts) > 4 else "",
                "frequency": "Daily",
            })

        # Parse doctor spec back
        spec_parts = [s.strip() for s in p_doc_spec.split("·")]
        updated = {
            **profile,
            "name":       p_name,
            "age":        int(p_age),
            "conditions": [c.strip() for c in p_conditions.splitlines() if c.strip()],
            "medications": meds_parsed,
            "allergies":   [a.strip() for a in p_allergies.split(",") if a.strip()],
            "doctor": {
                "name":      p_doc_name,
                "phone":     p_doc_phone,
                "specialty": spec_parts[0] if spec_parts else "",
                "practice":  spec_parts[1] if len(spec_parts) > 1 else "",
            },
            "pharmacy":          p_pharmacy,
            "lifestyle":         p_lifestyle,
            "personality_notes": "",
        }
        save_patient_profile(updated)
        st.success("Profile saved! Pulse now knows exactly who she's talking to.")
        if st.button("→ Back to Dashboard", key="back_after_save", type="primary",
                     use_container_width=True):
            st.query_params["view"] = "caregiver"
            st.rerun()

    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CAREGIVER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

elif _view == "caregiver":

    record_family_view()   # stamp that Sarah is here — shown to Margaret later

    # URL param overrides session state (supports back-links and direct URLs)
    if st.query_params.get("tab"):
        st.session_state.cg_tab = st.query_params.get("tab")
    _tab = st.session_state.get("cg_tab", "home")

    CAREGIVER_TABS = [("🏠","Home","home"),("📋","Check-ins","data"),("⌚","Watch","watch"),("📄","Report","report")]

    _phone_top()

    # ── HOME TAB — live fragment, auto-refreshes every 8s ─────────────────────
    if _tab == "home":

        @st.fragment(run_every="3s")
        def _live_home():
            try:
              _render_live_home()
            except Exception as _frag_err:
              st.markdown(
                f'<div style="padding:20px 24px;text-align:center;color:#9CA3AF;'
                f'font-size:13px;font-family:-apple-system,sans-serif;">'
                f'⟳ Dashboard updating… <code style="font-size:11px;">{_frag_err}</code></div>',
                unsafe_allow_html=True)

        def _render_live_home():
            # Pull fresh data from SQLite on every run — this is what makes it real-time
            h7  = query_history(days=7)
            h30 = query_history(days=30)
            rd  = compute_risk_level(days_baseline=30)
            als = rd.get("alerts", [])
            gdn = get_garden_state(h30)

            rl = rd.get("level", "low")
            last_ci = h7[0]["date"] if h7 else "No check-ins yet"
            sv_vals = [float(e["sleep_hours"]) for e in h7 if e.get("sleep_hours") is not None]
            avg_slp = round(sum(sv_vals) / len(sv_vals), 1) if sv_vals else None
            symp_d  = len([e for e in h7 if e.get("symptoms")])
            tldr    = _tldr(rd, config.PARENT_NAME, avg_slp, symp_d)
            phone_raw = config.PARENT_PHONE.replace("-", "").replace(" ", "")
            accent  = "#C9785A" if rl in ("high", "critical") else "#6B9E78"
            now     = datetime.now().strftime("%H:%M:%S")

            # ── Live indicator ────────────────────────────────────────────────
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:flex-end;'
                f'padding:6px 20px 0;font-family:-apple-system,sans-serif;">'
                f'<span style="font-size:10px;font-weight:800;color:#EF4444;'
                f'letter-spacing:0.5px;">● LIVE</span>'
                f'<span style="font-size:10px;color:#C0BAB4;margin-left:5px;">updated {now}</span>'
                f'</div>',
                unsafe_allow_html=True)

            # ── Header ────────────────────────────────────────────────────────
            st.markdown(f"""
            <div class="cg-header">
                <div class="cg-lbl">PulseCare · Caregiver</div>
                <a href="?view=setup" style="text-decoration:none;" class="cg-name">💚 {config.PARENT_NAME}, {config.PARENT_AGE} ✏️</a>
                <div class="cg-sub">Last check-in: <b>{last_ci}</b></div>
            </div>""", unsafe_allow_html=True)

            # ── TL;DR + actions ───────────────────────────────────────────────
            st.markdown(f"""
            <div style="margin-top:8px;" class="fwsec">
                <div class="fwsec-pad" style="border-left:4px solid {accent};">
                    <div style="font-size:16px;font-weight:600;color:#2D2D2D;line-height:1.5;">{tldr}</div>
                </div>
                <div class="fwsec-divider"></div>
                <div style="display:flex;gap:0;padding:0;">
                    <a class="action-btn" style="border-radius:0;border:none;border-right:1px solid rgba(0,0,0,0.07);padding:14px 6px;box-shadow:none;" href="tel:{phone_raw}">
                        <span class="ai">📞</span><span class="al">Call<br>{config.PARENT_NAME}</span>
                    </a>
                    <a class="action-btn" style="border-radius:0;border:none;border-right:1px solid rgba(0,0,0,0.07);padding:14px 6px;box-shadow:none;" href="sms:{phone_raw}?body=Hi+Mom%2C+just+checking+in+%F0%9F%92%9A">
                        <span class="ai">💬</span><span class="al">Quick<br>SMS</span>
                    </a>
                    <a class="action-btn" style="border-radius:0;border:none;padding:14px 6px;box-shadow:none;" href="https://calendar.google.com/calendar/r/eventedit" target="_blank">
                        <span class="ai">📅</span><span class="al">Book<br>Doctor</span>
                    </a>
                </div>
            </div>""", unsafe_allow_html=True)

            # ── Alerts ────────────────────────────────────────────────────────
            def _alert_timestamp(alert_type: str) -> str:
                """Find created_at of most recent entry relevant to this alert type."""
                for e in h7:
                    syms = [s.lower() for s in e.get("symptoms", [])]
                    matched = False
                    if alert_type == "sleep" and e.get("sleep_hours") is not None and float(e["sleep_hours"]) < config.SLEEP_WARNING_HOURS:
                        matched = True
                    elif alert_type == "fall_risk" and "dizziness" in syms:
                        matched = True
                    elif alert_type == "symptom_spike" and syms:
                        matched = True
                    elif alert_type == "isolation" and any(s in ("low appetite", "stayed in", "skipped", "not eating") for s in syms):
                        matched = True
                    elif alert_type == "medication" and any("skip" in s and "medic" in s or s in ("skipped medications", "missed medications") for s in syms):
                        matched = True
                    elif alert_type == "mental_crisis" and any(s in ("wants to die", "suicidal ideation", "self-harm", "hopeless") for s in syms):
                        matched = True
                    elif alert_type == "mental_health" and any(s in ("lonely", "low mood", "depression") for s in syms):
                        matched = True
                    elif alert_type == "cardiovascular" and any(s in ("orthopnea", "shortness of breath", "edema") for s in syms):
                        matched = True
                    if matched:
                        ts = e.get("created_at", "")
                        try:
                            dt = datetime.fromisoformat(ts)
                            return dt.strftime("%b %d at %H:%M UTC").replace(" 0", " ")
                        except Exception:
                            return e.get("date", "")
                return ""

            if als:
                _sev_map = {
                    "critical": ("alrt-ico-c", "alrt-badge-c", "CRITICAL"),
                    "high":     ("alrt-ico-h", "alrt-badge-h", "HIGH"),
                    "medium":   ("alrt-ico-m", "alrt-badge-m", "WATCH"),
                }
                header_html = (f'<div style="padding:12px 16px 6px 16px;font-size:11px;font-weight:800;'
                               f'text-transform:uppercase;letter-spacing:1px;color:#C9785A;'
                               f'font-family:-apple-system,sans-serif;">⚠ {len(als)} Alert{"s" if len(als)>1 else ""}</div>')
                rows = ""
                for a in als:
                    asv = a.get("severity", "medium")
                    ico_cls, badge_cls, badge_lbl = _sev_map.get(asv, _sev_map["medium"])
                    _ts = _alert_timestamp(a.get("type", ""))
                    ts_html = (f'<div style="font-size:10px;color:#9CA3AF;margin-top:3px;">'
                               f'🕐 Detected {_ts}</div>') if _ts else ""
                    rows += (f'<div class="alrt-row">'
                             f'<div class="alrt-ico {ico_cls}">{a.get("icon","🍂")}</div>'
                             f'<div class="alrt-body">'
                             f'<div class="alrt-msg">{a["message"]}</div>'
                             f'<div class="alrt-att">{a["attribution"]}</div>'
                             f'{ts_html}'
                             f'</div>'
                             f'<div class="alrt-badge {badge_cls}">{badge_lbl}</div>'
                             f'</div>')
                st.markdown(f'<div class="fwsec">{header_html}{rows}</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="fwsec" style="border-left:4px solid #6B9E78;">
                    <div class="fwsec-pad">
                        <div style="font-size:15px;font-weight:700;color:#3D6B47;">✅ All clear this week</div>
                        <div style="font-size:13px;color:#6B7280;margin-top:4px;">No concerning patterns detected.</div>
                    </div>
                </div>""", unsafe_allow_html=True)

            # ── Predictive insight ────────────────────────────────────────────
            _prediction = generate_predictive_insight()
            if _prediction:
                st.markdown(
                    f'<div style="margin:8px 16px 0 16px;padding:16px 18px;border-radius:18px;'
                    f'background:linear-gradient(135deg,#F3F0FF,#EBE8FF);'
                    f'border:1.5px solid rgba(130,100,220,0.2);'
                    f'font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
                    f'<div style="font-size:11px;font-weight:800;text-transform:uppercase;'
                    f'letter-spacing:1px;color:#7B5EA7;">{_prediction["icon"]} WHAT\'S COMING</div>'
                    f'<div style="font-size:10px;font-weight:700;color:#9B8FBF;'
                    f'background:rgba(123,94,167,0.1);padding:2px 8px;border-radius:8px;">'
                    f'{_prediction["confidence"]}% likelihood</div>'
                    f'</div>'
                    f'<div style="font-size:14px;font-weight:700;color:#2D2D2D;margin-bottom:5px;">'
                    f'{_prediction["title"]}</div>'
                    f'<div style="font-size:13px;color:#4B5563;line-height:1.55;">'
                    f'{_prediction["body"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

            # ── Garden (two-stage interactive) ───────────────────────────────
            st.markdown(
                f'<div class="fwsec">{_garden_two_stage_html(gdn, compact=False)}</div>',
                unsafe_allow_html=True)
            _gc1, _gc2 = st.columns(2)
            with _gc1:
                if st.button("💧 Water", use_container_width=True, key="cg_water"):
                    st.session_state["_garden_action"] = "water"
            with _gc2:
                if st.button("🌱 Fertilize", use_container_width=True, key="cg_fertilize"):
                    st.session_state["_garden_action"] = "fertilize"
            _ga = st.session_state.get("_garden_action")
            if _ga == "water":
                st.success("💧 Watered! Margaret's garden thanks you — she'll see this 🌱")
            elif _ga == "fertilize":
                st.success("🌱 Fertilized! The garden will grow a little faster today 🌿")

            # ── Clinical reasoning (hidden, only if available) ─────────────────
            if st.session_state.last_analyst_response:
                with st.expander("🧠  Clinical reasoning (AI)"):
                    st.markdown(
                        f'<div style="font-size:13px;color:#374151;line-height:1.7;white-space:pre-wrap;'
                        f'font-family:-apple-system,sans-serif;">'
                        f'{st.session_state.last_analyst_response}</div>', unsafe_allow_html=True)

        _live_home()

    # ── CHECK-INS TAB ─────────────────────────────────────────────────────────
    elif _tab == "data":
        history14 = query_history(days=14)
        col_b, col_t = st.columns([1, 5])
        with col_b:
            if st.button("←", key="back_data", use_container_width=True):
                st.session_state.cg_tab = "home"; st.rerun()
        with col_t:
            st.markdown(f'<div class="pg-title" style="padding:14px 0 2px 0;">'
                        f'Check-In History</div>'
                        f'<div class="pg-sub">{config.PARENT_NAME} · last 14 days</div>',
                        unsafe_allow_html=True)

        # 14-day calendar
        _section_label("14-Day Overview")
        cal_dates = [(_date.today() - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
        ebd: dict = {}
        for e in history14:
            ebd.setdefault(e["date"], []).append(e)

        def _ds(d):
            ents = ebd.get(d, [])
            if not ents: return "#F2F0ED", "#C0BAB4", "—"
            syms = [s.lower() for e in ents for s in e.get("symptoms", [])]
            sevs = [int(e["severity"]) for e in ents if e.get("severity")]
            ms = max(sevs) if sevs else 0
            if "dizziness" in syms or ms >= 6: return "#FDF0ED", "#9A5040", "❗"
            if syms or ms >= 3:               return "#FDF8ED", "#8A7040", "·"
            return "#EAF4EE", "#3D6B47", "✓"

        cal = '<div style="padding:0 16px;"><div class="cgrid">'
        for d in cal_dates:
            bg, fg, sym = _ds(d)
            cal += (f'<div class="cday" style="background:{bg};">'
                    f'<span class="cnum" style="color:{fg};">{d[8:]}</span>'
                    f'<span class="csym">{sym}</span></div>')
        cal += '</div>'
        cal += ('<div style="display:flex;gap:12px;font-size:11px;color:#9CA3AF;'
                'font-family:-apple-system,sans-serif;padding-bottom:14px;">'
                '<span>✓ Good</span><span style="color:#8A7040;">· Mild</span>'
                '<span style="color:#9A5040;">❗ Concern</span><span>— None</span></div></div>')
        st.markdown(cal, unsafe_allow_html=True)

        # Sleep trend
        if history14:
            _section_label("Sleep (14 days)")
            import pandas as pd
            slp_rows = []
            for d in sorted({e["date"] for e in history14}):
                day_e = [e for e in history14 if e["date"] == d]
                slp = next((float(e["sleep_hours"]) for e in day_e if e.get("sleep_hours") is not None), None)
                if slp is not None:
                    slp_rows.append({"Date": d, "Sleep (h)": slp})
            if len(slp_rows) >= 2:
                df = pd.DataFrame(slp_rows)
                df["Date"] = pd.to_datetime(df["Date"])
                st.line_chart(df.set_index("Date"), color="#6B9E78", height=110, use_container_width=True)

        # Compact timeline log
        if history14:
            _section_label("Daily Log")
            by_d: dict = {}
            for e in history14:
                by_d.setdefault(e["date"], []).append(e)
            rows_html = ""
            for d in sorted(by_d.keys(), reverse=True):
                entries = by_d[d]
                syms = list(dict.fromkeys(s.lower() for e in entries for s in e.get("symptoms", []) if s))
                slp  = next((e["sleep_hours"] for e in entries if e.get("sleep_hours") is not None), None)
                sev  = next((e["severity"] for e in entries if e.get("severity") is not None), None)
                dot_c = "#C9785A" if "dizziness" in syms or (sev and int(sev) >= 6) else (
                         "#B0A068" if syms else "#6B9E78")
                day_num = d[8:]   # "15"
                mon_str = _date.fromisoformat(d).strftime("%b").upper()  # "MAY"
                chips_html = "".join(
                    f'<span class="chip {"chip-d" if s=="dizziness" else "chip-f" if "fall" in s else ""}">{s}</span>'
                    for s in syms
                ) or '<span style="font-size:12px;color:#C0BAB4;">No symptoms</span>'
                slp_html = f'<span class="ci-slp">💤 {slp}h</span>' if slp else ""
                sev_html = f'<span class="ci-sev">{sev}/10</span>' if sev else ""
                rows_html += (
                    f'<div class="ci-row">'
                    f'<div class="ci-dot" style="background:{dot_c};"></div>'
                    f'<div class="ci-date"><div class="ci-day">{day_num}</div>'
                    f'<div class="ci-mon">{mon_str}</div></div>'
                    f'<div class="ci-chips">{chips_html}</div>'
                    f'<div class="ci-right">{slp_html}{sev_html}</div>'
                    f'</div>'
                )
            st.markdown(f'<div class="fwsec">{rows_html}</div>', unsafe_allow_html=True)

    # ── WATCH TAB ─────────────────────────────────────────────────────────────
    elif _tab == "watch":
        watch = get_watch_summary(days=7)
        col_b, col_t = st.columns([1, 5])
        with col_b:
            if st.button("←", key="back_watch", use_container_width=True):
                st.session_state.cg_tab = "home"; st.rerun()
        with col_t:
            st.markdown('<div class="pg-title" style="padding:14px 0 2px 0;">Apple Watch</div>'
                        f'<div class="pg-sub">{config.PARENT_NAME} · live biometrics</div>',
                        unsafe_allow_html=True)

        if not st.session_state.watch_connected:
            st.markdown("""
            <div style="text-align:center;padding:40px 24px;">
                <div style="font-size:56px;margin-bottom:14px;">⌚</div>
                <div style="font-size:20px;font-weight:800;color:#2D2D2D;margin-bottom:8px;">Connect Apple Watch</div>
                <div style="font-size:15px;color:#6B7280;line-height:1.6;">
                    Sync heart rate, SpO₂, HRV, sleep stages and steps automatically.
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("⌚  Pair Apple Watch", type="primary", use_container_width=True):
                import time; time.sleep(1)
                st.session_state.watch_connected = True; st.rerun()
        else:
            hr    = watch.get("heart_rate", {}); spo2 = watch.get("spo2", {})
            hrv   = watch.get("hrv", {});       steps = watch.get("steps", {})
            stages = get_sleep_stages()
            spo2_warn = spo2.get("value") is not None and spo2["value"] < 95
            hrv_warn  = hrv.get("value")  is not None and hrv["value"]  < 22
            hr_warn   = hr.get("value")   is not None and hr["value"]   > 78
            sync_t = datetime.now().strftime("%H:%M")

            st.markdown(f"""
            <div style="padding:14px 16px 2px 16px;">
            <div class="whead">
                <div class="wface">⌚</div>
                <div>
                    <div style="font-size:16px;font-weight:800;color:#fff;">{config.PARENT_NAME}'s Apple Watch</div>
                    <div style="font-size:13px;color:#8E8E93;margin-top:2px;">Series 9 · watchOS 11</div>
                    <div style="font-size:12px;font-weight:700;color:#6B9E78;margin-top:5px;">● Connected · {sync_t}</div>
                </div>
            </div>
            <div class="bgrid">
                <div class="bcrd {'bcrd-attn' if hr_warn else ''}">
                    <div class="b-ico">❤️</div>
                    <div><span class="b-val" style="color:#C9785A;">{int(hr.get('value') or 0)}</span>
                         <span class="b-unt">bpm</span></div>
                    <div class="b-lbl">Resting HR</div>
                    {'<div class="b-attn">↑ Above baseline</div>' if hr_warn else ''}
                </div>
                <div class="bcrd {'bcrd-attn' if spo2_warn else ''}">
                    <div class="b-ico">🫁</div>
                    <div><span class="b-val" style="color:{'#C9785A' if spo2_warn else '#6B9E78'};">{spo2.get('value') or '—'}</span>
                         <span class="b-unt">%</span></div>
                    <div class="b-lbl">Blood Oxygen</div>
                    {'<div class="b-attn">⚠ Below 95%</div>' if spo2_warn else ''}
                </div>
                <div class="bcrd {'bcrd-attn' if hrv_warn else ''}">
                    <div class="b-ico">🫀</div>
                    <div><span class="b-val" style="color:#7B8FA3;">{hrv.get('value') or '—'}</span>
                         <span class="b-unt">ms</span></div>
                    <div class="b-lbl">HRV</div>
                    {'<div style="font-size:12px;color:#B0A068;font-weight:700;margin-top:4px;">Low recovery</div>' if hrv_warn else ''}
                </div>
                <div class="bcrd">
                    <div class="b-ico">🚶</div>
                    <div><span class="b-val" style="color:#6B9E78;">{int(steps.get('value') or 0):,}</span></div>
                    <div class="b-lbl">Steps Today</div>
                </div>
            </div></div>""", unsafe_allow_html=True)

            if stages:
                deep = stages.get("deep", 0); core = stages.get("core", 0)
                rem  = stages.get("rem",  0); awake = stages.get("awake", 0)
                total = max(deep + core + rem + awake, 1)
                hrs   = round((deep + core + rem) / 60, 1)
                q_c   = "#C9785A" if hrs < 6 else ("#B0A068" if hrs < 6.5 else "#6B9E78")
                st.markdown(
                    f'<div style="padding:0 16px 4px 16px;">'
                    f'<div class="card" style="padding:16px;">'
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                    f'<span style="font-size:20px;font-weight:800;color:#2D2D2D;">{hrs}h '
                    f'<span style="font-size:13px;color:#6B7280;font-weight:500;">sleep</span></span>'
                    f'<span style="font-size:13px;font-weight:700;color:{q_c};">{"Poor" if hrs<6 else "Low" if hrs<6.5 else "Good"}</span>'
                    f'</div>'
                    f'<div class="stgbar">'
                    f'<div class="sg sg-deep" style="width:{deep/total*100:.0f}%;">{deep}m</div>'
                    f'<div class="sg sg-core" style="width:{core/total*100:.0f}%;">{core}m</div>'
                    f'<div class="sg sg-rem"  style="width:{rem/total*100:.0f}%;">{rem}m</div>'
                    f'<div class="sg sg-awake" style="width:{awake/total*100:.0f}%;">{awake}m</div>'
                    f'</div>'
                    f'<div class="sleg">'
                    f'<div class="si"><div class="sd" style="background:#6B6BC9;"></div>Deep {deep}m</div>'
                    f'<div class="si"><div class="sd" style="background:#6B9EC9;"></div>Core {core}m</div>'
                    f'<div class="si"><div class="sd" style="background:#6BC9C9;"></div>REM {rem}m</div>'
                    f'<div class="si"><div class="sd" style="background:#C9C9C9;"></div>Awake {awake}m</div>'
                    f'</div></div></div>', unsafe_allow_html=True)

            import pandas as pd
            hr_ser = get_hr_series(days=7)
            if hr_ser:
                _section_label("Heart Rate · 7 Days")
                st.line_chart(pd.DataFrame(hr_ser).set_index("date"), color="#C9785A", height=100, use_container_width=True)
            st_ser = get_steps_series(days=7)
            if st_ser:
                _section_label("Steps · 7 Days")
                st.line_chart(pd.DataFrame(st_ser).set_index("date"), color="#6B9E78", height=100, use_container_width=True)

            if spo2_warn or hrv_warn:
                body = ""
                if spo2_warn: body += f"Blood oxygen averaging <b>{spo2.get('avg')}%</b> — below the 95% threshold.<br>"
                if hrv_warn:  body += f"HRV averaging <b>{hrv.get('avg')} ms</b> — indicates recovery stress."
                st.markdown(f'<div style="padding:0 16px 12px 16px;"><div class="acrd acrd-h">'
                            f'<div class="acrd-t">⌚ Watch signals need attention</div>'
                            f'<div class="acrd-b">{body}</div></div></div>', unsafe_allow_html=True)

            if st.button("Disconnect Watch", use_container_width=True):
                st.session_state.watch_connected = False; st.rerun()

    # ── REPORT TAB ────────────────────────────────────────────────────────────
    elif _tab == "report":
        col_b, col_t = st.columns([1, 5])
        with col_b:
            if st.button("←", key="back_report", use_container_width=True):
                st.session_state.cg_tab = "home"; st.rerun()
        with col_t:
            st.markdown('<div class="pg-title" style="padding:14px 0 2px 0;">Doctor Report</div>'
                        '<div class="pg-sub">30-day health summary</div>',
                        unsafe_allow_html=True)

        # Auto-generate on first open
        if not st.session_state.report_text:
            with st.spinner("Building 30-day report…"):
                st.session_state.report_text = generate_health_timeline(days=30)

        # What to do with this report — shown first
        st.markdown("""<div class="fwsec">
<div class="rpt-act">
  <div class="rpt-act-ico">🏥</div>
  <div><div class="rpt-act-title">Bring to the next doctor visit</div>
       <div class="rpt-act-sub">Saves 10 min of intake questions — hand it to the nurse at check-in</div></div>
</div>
<div class="rpt-act">
  <div class="rpt-act-ico">📲</div>
  <div><div class="rpt-act-title">Share with the care team</div>
       <div class="rpt-act-sub">Screenshot or forward the download — works for remote care coordinators too</div></div>
</div>
<div class="rpt-act">
  <div class="rpt-act-ico">💊</div>
  <div><div class="rpt-act-title">Review medication timing</div>
       <div class="rpt-act-sub">If dizziness spikes align with dose times, flag it for the pharmacist</div></div>
</div>
</div>""", unsafe_allow_html=True)

        # Download button (primary CTA)
        if st.session_state.report_text:
            st.download_button("⬇️  Download Report (.md)", st.session_state.report_text,
                               f"pulsecare_{_date.today()}.md", "text/markdown",
                               use_container_width=True, type="primary")
            with st.expander("Preview report"):
                st.markdown(st.session_state.report_text)

    _bottom_nav(_tab, CAREGIVER_TABS)
    st.markdown(
        '<div style="padding:10px 20px 10px 20px;font-family:-apple-system,sans-serif;">'
        '<a href="?view=senior" style="font-size:13px;color:#9CA3AF;text-decoration:none;">'
        '→ Senior Interface</a>'
        '</div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SENIOR INTERFACE — Zen Garden + check-in
# ══════════════════════════════════════════════════════════════════════════════

else:

    history30     = query_history(days=30)
    history_today = query_history(days=1)
    garden        = get_garden_state(history30)
    checked_today = bool(history_today)
    animate_water = st.session_state.just_checked_in
    if animate_water:
        st.session_state.just_checked_in = False

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    _phone_top()

    # Family presence banner — shown when caregiver has been on recently
    _banner = _family_presence_banner(config.CAREGIVER_NAME)
    if _banner:
        st.markdown(_banner, unsafe_allow_html=True)

    # ── Zen Garden ────────────────────────────────────────────────────────────
    in_chat = bool(st.session_state.messages)
    st.markdown(
        f'<div style="padding:{"10px 16px 4px 16px" if in_chat else "16px 16px 4px 16px"};">'
        f'{_garden_two_stage_html(garden, compact=in_chat)}</div>',
        unsafe_allow_html=True)

    # Post-check-in / missed-day prompts
    if animate_water:
        st.markdown("""
        <div style="background:rgba(234,244,238,0.9);border-radius:16px;
                    margin:8px 16px 0 16px;padding:12px 16px;text-align:center;
                    font-family:-apple-system,sans-serif;">
            <span style="font-size:15px;font-weight:700;color:#3D6B47;">
                🌧 Watered! Your garden is growing 💚
            </span>
        </div>""", unsafe_allow_html=True)
    elif not checked_today and not in_chat:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.7);backdrop-filter:blur(10px);
                    border-radius:16px;margin:8px 16px 0 16px;padding:14px 16px;
                    text-align:center;border:1.5px solid rgba(107,158,120,0.2);
                    font-family:-apple-system,sans-serif;">
            <span style="font-size:14px;color:#5A8A6A;font-weight:600;">
                Your garden missed you yesterday 🌿<br>
                <span style="font-weight:400;color:#6B7280;">Check in today to keep it growing!</span>
            </span>
        </div>""", unsafe_allow_html=True)

    # ── Chat or feeling buttons ───────────────────────────────────────────────
    if in_chat:
        col_b, col_t = st.columns([1, 5])
        with col_b:
            if st.button("←", key="senior_back", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col_t:
            st.markdown('<div style="padding:10px 0 6px 0;font-size:15px;font-weight:700;'
                        'color:#2D2D2D;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
                        'Your check-in</div>', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="bub-u"><div class="bc-u">{msg["content"]}</div></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bub-p"><div class="pulse-av">💚</div>'
                            f'<div class="bc-p">{msg["content"]}</div></div>',
                            unsafe_allow_html=True)
    else:
        st.markdown('<div class="feel-q">How are you feeling today?</div>', unsafe_allow_html=True)
        st.markdown('<div class="feel-grid-sentinel"></div>', unsafe_allow_html=True)
        # (label shown on button, message actually sent to the AI)
        feelings = [
            ("😊", "Feeling good",          "I'm feeling good today!"),
            ("😵‍💫", "A bit dizzy",          "I've been feeling a bit dizzy."),
            ("😴", "Didn't sleep well",     "I didn't sleep very well last night."),
            ("😣", "Some pain",             "I'm having some pain today."),
            ("💊", "Medication question",   "I have a question about my medications. Can you remind me what I'm supposed to be taking and when? And can you check if I've missed anything?"),
            ("👍", "All normal",            "Everything is fine today, all normal!"),
        ]
        def _make_feel_cb(msg):
            def _cb():
                st.session_state["_submit"] = msg
            return _cb

        _fc1, _fc2 = st.columns(2, gap="small")
        for i, (emoji, label, message) in enumerate(feelings):
            with (_fc1 if i % 2 == 0 else _fc2):
                st.button(f"{emoji}\n{label}", key=f"feel_{i}",
                          use_container_width=True, on_click=_make_feel_cb(message))

        # Daily Delight — rotates by day so it changes naturally each morning
        _delight = _DAILY_DELIGHTS[_date.today().toordinal() % len(_DAILY_DELIGHTS)]
        st.markdown(
            f'<div style="margin:4px 16px 16px 16px;padding:16px 18px;border-radius:18px;'
            f'background:linear-gradient(135deg,#FFF9F0,#FFF0E8);'
            f'border:1.5px solid rgba(255,180,100,0.25);'
            f'font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
            f'<div style="font-size:11px;font-weight:800;text-transform:uppercase;'
            f'letter-spacing:1px;color:#C9785A;margin-bottom:6px;">'
            f'{_delight["emoji"]} {_delight["tag"].upper()}</div>'
            f'<div style="font-size:15px;font-weight:600;color:#2D2D2D;line-height:1.55;">'
            f'{_delight["text"]}</div></div>',
            unsafe_allow_html=True)

    # Process submitted message — from feeling buttons (URL param) or chat input
    _url_submit = st.session_state.pop("_submit", None)
    st.markdown(
        '<div style="text-align:center;padding:6px 0 2px 0;">'
        '<div style="display:inline-flex;align-items:center;gap:7px;'
        'background:rgba(107,158,120,0.12);border-radius:20px;'
        'padding:7px 16px;font-family:-apple-system,sans-serif;">'
        '<span style="font-size:20px;">🎤</span>'
        '<span style="font-size:12px;font-weight:600;color:#5A8A6A;">Tap to speak</span>'
        '</div></div>',
        unsafe_allow_html=True)
    _chat_submit = st.chat_input("Tell Pulse how you're feeling…")
    user_input = _url_submit or _chat_submit
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Show user bubble immediately so they know it was received
        st.markdown(f'<div class="bub-u"><div class="bc-u">{user_input}</div></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="bub-p"><div class="pulse-av">💚</div>'
                    '<div class="bc-p" style="color:#9CA3AF;font-style:italic;font-size:15px;">'
                    '✓ Got it — Pulse is listening…</div></div>',
                    unsafe_allow_html=True)
        with st.status("Pulse is with you…", expanded=True) as _st_status:
            st.write("Listening carefully…")
            try:
                # Pass all prior turns so the LLM has in-session memory
                _history = st.session_state.messages[:-1]  # exclude the just-appended user msg
                result   = get_graph().invoke(initial_state(user_input, chat_history=_history))
                response = result.get("companion_response") or "Thank you for sharing that with me."
                if result.get("analyst_response"):
                    st.session_state.last_analyst_response = result["analyst_response"]
                # Surface what the pipeline did — proves backend intelligence
                entry = result.get("new_entry", {})
                syms  = entry.get("symptoms", [])
                slp   = entry.get("sleep_hours")
                if syms or slp is not None:
                    parts = []
                    if syms: parts.append(", ".join(syms))
                    if slp is not None: parts.append(f"sleep {slp}h")
                    st.write(f"Health markers noted — {' · '.join(parts)}")
                if result.get("route_to_analyst"):
                    st.write("Pattern analysis complete — comparing to your recent baseline")
                _st_status.update(label="✓ All done", state="complete", expanded=False)
            except Exception as _e:
                import traceback
                response = "Oh, I'm sorry — something went wrong on my end. Could you try again in a moment?"
                _st_status.update(label="⚠ Error", state="error", expanded=True)
                st.write(f"Error: {_e}")
                st.code(traceback.format_exc(), language="text")
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.just_checked_in = True
        st.rerun()

    st.markdown('<div style="text-align:center;padding:8px 0 16px 0;">'
                '<a href="?view=caregiver" style="font-size:13px;color:#9CA3AF;'
                'text-decoration:none;">→ Family Dashboard</a></div>',
                unsafe_allow_html=True)
