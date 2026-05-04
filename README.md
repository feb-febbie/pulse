## 📄 Business Document

> **This project includes a formal business case** — a 3-page strategic document covering the market problem, unit economics (98.8% gross margin), competitor landscape, and how every technical architecture decision maps to a business requirement.

### 👉 [Read the Business Case (PDF)](./PulseCare_Business_Case.pdf)

### 👉 [View the Pitch Deck (PDF)](./PulseCare_Pitch_Deck.pdf)

*PulseCare: Strategic Business Case & Architecture Alignment — February Jiang*

---

# 🩺 PulseCare: AI-Powered Senior Health Monitoring

**PulseCare gives adult children the visibility they need to look after aging parents — without surveillance, without alarm, without friction.**

A senior describes how they're feeling in natural language. PulseCare listens, logs structured health data, surfaces patterns to the caregiver's dashboard, and predicts what is likely to happen next — before a small problem becomes an emergency.

> *"Your body has a story. Pulse remembers it."*

---

## 🔗 Live Demo Links

| Page | URL | Who uses it |
|------|-----|-------------|
| **Caregiver Dashboard** | https://pulse-health-y367agrziq-uc.a.run.app/?view=caregiver | Sarah — sees alerts, watch data, check-in history |
| **Senior Interface** | https://pulse-health-y367agrziq-uc.a.run.app/?view=senior | Margaret — talks to Pulse, grows the garden |
| **Patient Profile Setup** | https://pulse-health-y367agrziq-uc.a.run.app/?view=setup | Caregiver — fills in Margaret's medical background |

---

## 🎬 Demo Guide

### How to run the real-time demo

Open **two browser windows side by side**:

- **Left window** → https://pulse-health-y367agrziq-uc.a.run.app/?view=caregiver (Sarah's dashboard)
- **Right window** → https://pulse-health-y367agrziq-uc.a.run.app/?view=senior (Margaret's chat)

Talk to Pulse in the right window. Watch the left window update within 3 seconds — no refresh needed. The caregiver dashboard auto-refreshes live.

### Suggested demo script

1. Open both windows side by side.
2. In the senior window, tap **"A bit dizzy"** → Pulse responds clinically, referencing Margaret's blood pressure and Lisinopril.
3. Watch the caregiver dashboard refresh — a **fall risk alert** appears in real time.
4. Tap **"Didn't sleep well"** → adds a sleep alert. The **WHAT'S COMING** prediction card updates.
5. In the senior window, type *"I breathe heavily when I lie down"* → Pulse asks about swollen ankles (testing for edema). If confirmed, a **cardiovascular alert** fires on the caregiver side.

### 🔄 Reset the demo (clears all live check-ins, re-seeds 14-day history)

Visit: **https://pulse-health-y367agrziq-uc.a.run.app/?reset=1**

This wipes all check-ins added during the demo, restores the 14-day story arc (baseline → gradual decline → elevated fall risk), and lands you back on the caregiver home tab — ready to demo again in under 3 seconds. The seeded history stays intact; only the live entries you added are removed.

> Bookmark `?reset=1` before your presentation. One click, clean slate.

---

## 🔍 The Problem

72 million Americans are over 65. Most live independently. Their adult children — typically living across cities — have no visibility into daily health patterns until something goes wrong.

**What families do today:**

| Signal | What happens | The gap |
|--------|-------------|---------|
| Mom mentions dizziness once | Daughter worries for a day, then forgets | No longitudinal record |
| Mom downplays symptoms ("I don't want to worry you") | Caregiver never knows | No neutral third party |
| Pattern emerges over weeks | No one notices until a fall | No passive monitoring |

Falls are the leading cause of injury death in seniors over 65. Most are preceded by days of dizziness and sleep disruption — signals that vanish in conversation but accumulate in data.

**The gap PulseCare fills:** the visibility layer between "everything is fine" and "call 911."

---

## 📱 The Product

### Two views, one purpose

**Patient Profile Setup** (`?view=setup`) — one-time onboarding:

Before PulseCare can give real, specific advice, it needs to know the patient. The setup page is where the caregiver fills in Margaret's complete medical background: conditions (hypertension, Type 2 diabetes, osteoarthritis), medications (Lisinopril 10mg, Metformin 500mg, Atorvastatin 20mg, Vitamin D3), allergies, doctor contact, pharmacy, and a lifestyle note about who she is as a person. Once saved, every CompanionAgent response becomes specific — *"Oh, your Lisinopril? If it's still this morning, go ahead and take it now with a little something to eat."* — instead of generic. The demo ships with Margaret's profile pre-seeded. The profile page is accessible directly from the caregiver dashboard by tapping the patient name **(💚 Margaret Chen, 72 ✏️)** in the header — no separate link needed.

**Senior Interface** (`?view=senior`) — what Margaret sees:

A warm, conversational check-in companion. Large text, simple UI. A **🎤 Tap to speak** indicator above the chat bar signals voice capability — Margaret knows she can speak rather than type. She says "I forgot to take my medication" — and Pulse knows she means her Lisinopril (morning blood pressure tablet) and responds with the right guidance. She says "I felt dizzy this morning" — Pulse responds like a caring friend, logs the structured data behind the scenes, and sends nothing alarming to the senior. The next morning it opens with: *"Yesterday you mentioned feeling dizzy — how is that today?"*

The senior interface includes three engagement layers beyond the chat:

- **Zen Garden** that grows with every check-in. A Seed becomes a Sprout, Seedling, Sapling, Young Tree, and eventually a Flourishing garden (45+ check-ins). Water drops fall after each check-in. Missed days prompt softly — no guilt, no broken streaks.
- **Family Presence Banner** appears beneath the garden when Sarah has been on the caregiver dashboard recently: *"Sarah was thinking of you earlier today 💛."* Margaret feels accompanied, not monitored.
- **Daily Delight card** — a rotating prompt from a 10-item pool (Memory Lane questions, historical facts, gentle wellness prompts). Changes each morning. Gives Margaret a reason to open the app on days she feels fine.

**Caregiver Dashboard** (`?view=caregiver`) — what Sarah sees:

A clinical-but-human dashboard with a **live home screen** — the TL;DR, alerts, predictive insight card, and garden all auto-refresh every **3 seconds** via Streamlit's `@st.fragment(run_every="3s")`, with a `● LIVE · updated HH:MM:SS` indicator in the top-right corner. When Margaret checks in on her phone, Sarah sees the dashboard update within seconds — no manual refresh needed. This is the demo moment: two browser tabs open, one senior, one caregiver, watching the signal flow in real time.

At the top: a bold **At a Glance** synthesis sentence — not a summary, a synthesis: *"Margaret reported fatigue today, which correlates with a 15% drop in HRV overnight and only 4h of core sleep — this pattern suggests physical exhaustion, not a mood dip."*

Below the summary: one-tap action buttons (📞 Call, 💬 Quick SMS, 📅 Book Doctor Visit). Then real-time alerts with exact timestamps and severity badges, a **Predictive Insight** card, the two-stage garden, Apple Watch data, the 14-day check-in history, and a one-click doctor report. The most critical signal is always on top; everything else is in progressive disclosure.

The same check-in that appears as a warm conversation to Margaret appears as a cross-modal clinical signal to Sarah.

### ⚙️ Core features

**1. Patient Profile — Medical Context Engine**
`tools/profile_tools.py` stores the senior's complete medical background in SQLite: conditions, medications (with specific dosing notes and missed-dose guidance), allergies, doctor and pharmacy, lifestyle, and personality notes. This profile is injected into every CompanionAgent call so responses are specific, not generic. Without it, PulseCare is a chatbot. With it, it's a knowledgeable companion who knows which tablet Margaret takes in the morning and what to say if she's missed it. Pre-seeded for demo; editable by the caregiver at `?view=setup`.

**2. Companion Agent — Stateful, Personalised (senior-facing)**
Natural language check-in via text or voice. Extracts structured signals: symptoms, sleep hours, severity, notes. Responds warmly — never clinical, never alarming. Opens every conversation with continuity (`_build_recent_context()` injects last 48h of logs) and uses the patient profile to give specific, real answers. When Margaret asks about a missed medication, Pulse knows which one she means, what it's for, and exactly what to say. Maximises disclosure quality because seniors systematically under-report to avoid worrying family.

**3. Analyst Agent — Cross-Modal Synthesis (caregiver-only)**
Runs only when a meaningful health signal is detected (symptoms present, or severity ≥ 5). Retrieves 60-day conversation history AND Apple Watch biometrics (HR, SpO₂, HRV, sleep stages, steps). Synthesises across both modalities: when conversational reports and biometric data converge, it says so explicitly; when they diverge, it flags the discrepancy. Grounds reasoning in a geriatric medical knowledge base via hybrid RAG. Produces a structured assessment: RISK LEVEL / PATTERN / ATTRIBUTION / RECOMMENDATION / ESCALATE IF.

**4. Conditional Routing (LangGraph)**
`CompanionAgent → [conditional edge] → AnalystAgent → END`. AnalystAgent costs money; it only runs when needed. A "I'm fine" check-in costs ~$0.001. A dizziness event with cross-modal pattern analysis costs ~$0.015. This is the architecture that keeps per-user LLM costs near $0.05/month.

**5. Predictive Insight Engine**
`generate_predictive_insight()` scans the last 14 days for three leading-indicator patterns — sleep debt accumulation (3+ consecutive nights below threshold → fatigue likely within 48h), accelerating dizziness frequency (this week vs last), and multi-symptom co-occurrence (dizziness + fatigue + low appetite together). Renders as a purple **WHAT'S COMING** card on the caregiver home tab, above the garden, with a confidence percentage. This is the feature that turns PulseCare from reactive monitoring into predictive care.

**6. Rule-Based Alert Engine**
`compute_risk_level()` runs on every dashboard load. Compares this week's signals against the personal baseline — dizziness frequency, sleep deviation, symptom spike ratio. Surfaces structured alerts with clinical attribution ("orthostatic hypotension or dehydration most likely") not just counts.

**7. Live Caregiver Dashboard with Timestamped Alerts**
The caregiver home screen auto-refreshes every **3 seconds** using `@st.fragment(run_every="3s")`. Each rerun opens a fresh SQLite connection (WAL mode enabled — `PRAGMA journal_mode=WAL` — so concurrent writes from the senior's session are immediately visible to the caregiver's reader). The full dashboard — TL;DR, alerts, predictive insight card, and garden — all update within 3 seconds of a senior check-in, with no manual refresh needed. A `● LIVE · updated HH:MM:SS` indicator makes the polling visible.

The home screen is intentionally concise: TL;DR synthesis sentence, one-tap action buttons, and alerts. No metrics bar or wellbeing status pill — these add visual clutter without adding signal.

Alerts include a colour-coded severity badge (**CRITICAL** / **HIGH** / **WATCH**) and the exact `created_at` timestamp of the triggering entry (e.g. *"🕐 Detected May 1 at 14:23 UTC"*). When Margaret checks in with dizziness, the caregiver sees the alert appear within 3 seconds — with the precise time it was detected and how serious it is.

**Guaranteed logging:** the CompanionAgent forces a `log_health_entry` tool call on every first turn (Gemini Flash's `tool_choice` is pinned to the function), then strips tools from the second turn so the model can only generate the warm conversational response. This eliminates the failure mode where the model skips the tool call and logs nothing.

**9. Pipeline Transparency**
When Margaret submits a check-in, `st.status()` surfaces the LangGraph steps live: health markers extracted, whether the AnalystAgent ran, baseline comparison complete. The senior sees it warm and brief; graders see proof that the backend is doing real work — not just forwarding messages to an LLM.

**10. 14-Day Health Calendar**
Day-by-day visual: green (good), amber (mild symptoms), red (dizziness or severity ≥ 6), grey (no check-in). Instantly shows whether symptoms are isolated or trending.

**11. Doctor Report Export**
One-click structured health timeline: symptom frequency, severity trends, sleep patterns, notable entries. Reduces doctor intake time. Generates automatically on first open of the Report tab.

**12. Interactive Two-Role Garden — Retention Engine**
Margaret's check-in habit is the product. The garden makes that habit tangible — and gives each role a distinct action.

Both the senior and caregiver see the same **equal-split two-panel layout**: current stage on the left (large swaying emoji + plant grid + day count) and next stage on the right (dimmed, with a *"X days away"* badge). A progress bar runs underneath. Seven stages: Seed 🌱 → Sprout 🌼 → Budding 🌷 → Blooming 🌸 → Flourishing 🌺 → Garden 💐 → Paradise 🌻. The progression is a full flower garden journey — from a single seedling to paradise — visible across both views so both family members share the same goal.

**Senior (plants trees):** every check-in grows the garden. The "Coming up" panel is deliberately dimmed and shows exactly how many days until the next stage — a clear, low-pressure goal.

**Caregiver (waters and fertilizes):** two action buttons — **💧 Water** and **🌱 Fertilize** — appear below the garden on the caregiver dashboard. Tapping them shows a warm confirmation: *"💧 Watered! Margaret's garden thanks you"*. This turns the caregiver into an active participant in the senior's habit, not just a passive monitor.

**13. Family Presence + Daily Delight**
Two senior-facing engagement signals that reframe PulseCare as a *shared ritual* rather than a monitoring tool. The presence banner (`get_last_family_view()`) shows Margaret that Sarah was here; the daily delight card gives her something to look forward to each morning. Both appear before the chat — reducing the transactional feeling of a daily health log.

**14. Apple Watch Integration**
Syncs heart rate, SpO₂, HRV, sleep stages (deep/core/REM/awake), and step count from Apple Watch. 14-day trend data auto-seeded for demo. Clinically calibrated thresholds: SpO₂ < 95%, HRV < 22ms, resting HR > 78bpm each trigger inline attention flags. 7-day HR and steps line charts included. Watch data is fed directly into the AnalystAgent for cross-modal synthesis.

**15. Voice Input**
Web Speech API (Chrome/Edge). No external service, zero API cost. Transcript flows into the chat bar and submits as a normal message. Critical for seniors with low mobile typing fluency.

---

## 🧠 Why This Architecture Wins

A single-agent system fails this use case:

- One agent can't be both warm (senior UX) and clinical (caregiver credibility)
- One agent runs even when no health signal was logged — wasting compute on "I'm fine"
- One agent can't synthesise across conversation and biometrics independently

PulseCare splits responsibilities:

| Agent | Audience | Optimised For |
|-------|----------|---------------|
| `CompanionAgent` | Senior | Disclosure quality — empathy → daily engagement → data accumulation |
| `AnalystAgent` | Caregiver | Decision quality — cross-modal synthesis, RAG grounding, no hallucination |

The conditional router is the economic engine: AnalystAgent (the expensive cross-modal reasoning step) only fires on significant signals. A "I'm fine" check-in costs ~$0.001. A dizziness event with watch-corroborated pattern analysis costs ~$0.015.

---

## 📋 Grading Rubric Mapping

| Category | How PulseCare Delivers |
| :--- | :--- |
| **Deployed & Working** | Live on Google Cloud Run. Vertex AI ADC for keyless Gemini 2.0 Flash inference. |
| **Business Case** | In Business One-Pager. $29/month caregiver subscription. Break-even at ~15 users. |
| **Class Concepts (≥3)** | Multi-Agent Patterns, RAG (hybrid FAISS+BM25), Context Engineering (HealthState + stateful memory), Tool Calling. All 4 mapped below with file references. |
| **Technical Justification** | Every technical choice maps to a business need. See "Why This Architecture Wins" above. |

---

## 📚 Class Concepts Applied

| # | Concept | Lecture | File | Justification |
|---|---------|---------|------|---------------|
| 1 | **Multi-Agent Patterns** | Mar 23 - Multi-Agent Patterns.pdf | `agents/companion.py`, `agents/analyst.py`, `graph/workflow.py` | Senior-facing intake requires empathy (low friction = daily engagement = data accumulation). Caregiver-facing analysis requires clinical structure (correctness = trust = willingness to pay). One agent degrades both. Conditional routing ensures AnalystAgent only runs on meaningful signals — and AnalystAgent receives Apple Watch biometrics for cross-modal synthesis the CompanionAgent never touches. |
| 2 | **RAG** | Feb 23 - Retrieval Augmented Generation.pdf | `tools/rag_tools.py` → `MedicalRAG`, `data/geriatric_knowledge.py` | Caregivers will not trust an agent that hallucinates medical information. PulseCare uses **hybrid retrieval**: FAISS dense vector search + BM25 sparse keyword scoring, fused via Reciprocal Rank Fusion (RRF). Dense handles semantic queries ("my head hurts"); BM25 handles exact terminology ("orthostatic hypotension"). Red-flag chunks are injected on serious symptom queries. |
| 3 | **Tool Calling** | Feb 16 - Tool Calling.pdf | `tools/memory_tools.py` → `log_entry()`, `get_summarized_history()` · `tools/report_tools.py` → `generate_health_timeline()` | Agents must act outside the conversation — write to DB, query history, generate documents. Without tool calls, PulseCare is a chatbot. `log_entry()` is what makes the health history real. `get_summarized_history()` compresses history older than 7 days into a statistical baseline, controlling token costs as history grows. |
| 4 | **Context Engineering** | Feb 02 - Context Engineering.pdf | `graph/state.py` → `HealthState`, `agents/companion.py` → `_build_recent_context()`, `agents/analyst.py` | Two layers of context engineering: (1) CompanionAgent receives the last 48h of check-ins so it opens with continuity rather than amnesia — *"Yesterday you mentioned dizziness, how is that today?"* (2) AnalystAgent receives compressed 60-day history (raw last 7 days + statistical baseline for older entries) AND Apple Watch biometrics in a single structured prompt. Context engineering is what makes PulseCare feel like a system that knows the patient, not just a chatbot that processes messages. |

---

## 🏗️ Architecture

```
Patient Profile Setup (?view=setup)  ← one-time onboarding
    │  Caregiver fills in: conditions, medications (with dosing notes),
    │  allergies, doctor, pharmacy, lifestyle, personality
    │  Saved to SQLite patient_profile table
    │  Demo profile for Margaret pre-seeded on first run
    │
    ▼ (profile available to all agents)

Senior types/speaks in Senior Interface (?view=senior)
    │
    │  Web Speech API (voice) or st.chat_input (text)
    │  Quick-start feeling buttons for low-friction first interaction
    │  Family Presence Banner — "Sarah was thinking of you earlier today 💛"
    │  Daily Delight card — rotating Memory Lane / historical fact / wellness prompt
    │
    ▼
┌──────────────────────────────────────┐
│  companion_node  (CompanionAgent)    │  ← LangGraph entry point
│                                      │
│  1. get_patient_profile()            │  ← medications, conditions, doctor
│     → specific, personalised answers│
│  2. _build_recent_context(days=2)    │  ← last 48h for stateful greeting
│  3. Warm conversational response     │
│  4. tool call: log_entry() → SQLite  │
│     or Firestore                     │
│  5. Sets route_to_analyst=True if    │
│     symptoms or severity ≥ 5         │
└────────────────┬─────────────────────┘
                 │
                 │  Conditional edge: _route_after_companion()
                 │
         ┌───────┴────────────────────┐
         │                            │
         ▼ (significant signal)       ▼ (no signal → END)
┌────────────────────────────────────┐
│  analyst_node  (AnalystAgent)      │  ← caregiver-only
│                                    │
│  1. get_summarized_history(days=60)│  ← conversation history
│  2. get_watch_summary(days=7)      │  ← Apple Watch biometrics
│     + get_sleep_stages()           │
│  3. MedicalRAG hybrid retrieval    │  ← FAISS + BM25 → RRF
│     (FAISS + BM25 → RRF)           │
│  4. Cross-modal synthesis:         │
│     conversation ↔ biometrics      │
│  5. Structured risk assessment:    │
│     RISK LEVEL / PATTERN /         │
│     ATTRIBUTION / RECOMMENDATION / │
│     ESCALATE IF                    │
└────────────────┬───────────────────┘
                 │
                END
                 │
                 ▼
Caregiver Dashboard (?view=caregiver)
  ├─ ● LIVE indicator (auto-refreshes every 3s)
  ├─ At a Glance — cross-modal empathetic synthesis sentence
  ├─ One-tap actions: 📞 Call · 💬 SMS · 📅 Book Doctor Visit
  ├─ Timestamped alerts — CRITICAL / HIGH / WATCH with exact detected time
  ├─ 🔮 Predictive Insight card — leading-indicator forecast with confidence %
  ├─ Two-stage Garden (current stage left · next stage right · 💧 Water · 🌱 Fertilize)
  ├─ Clinical reasoning expander (AnalystAgent full output)
  ╔══ Check-ins tab ══════════════════════════════════════╗
  ║  14-day calendar · sleep trend chart · compact log   ║
  ╚═══════════════════════════════════════════════════════╝
  ╔══ Watch tab ══════════════════════════════════════════╗
  ║  HR · SpO₂ · HRV · steps · sleep stages bar         ║
  ║  7-day HR and steps line charts                      ║
  ╚═══════════════════════════════════════════════════════╝
  ╔══ Report tab ═════════════════════════════════════════╗
  ║  Auto-generates on open · action guidance on top     ║
  ║  Download .md for doctor visit                       ║
  ╚═══════════════════════════════════════════════════════╝

Storage: SQLite (local dev) → Firestore (Cloud Run, auto-detected via K_SERVICE)
RAG:     geriatric_knowledge.py chunks → FAISS + BM25 → RRF → top-k context
```

---

## 🎬 Demo Script

**Setup:** Open three tabs. Tab 1: `?view=setup`. Tab 2: `?view=senior`. Tab 3: `?view=caregiver`.

**0:00–0:15** Hook:
> "ChatGPT doesn't know your mom's on Lisinopril for blood pressure, or that she missed her morning tablet. PulseCare does — and it gives her the right answer, not a generic response."

**0:15–0:40** Caregiver tab → tap **💚 Margaret Chen, 72 ✏️** in the header to open the profile:
→ Margaret's profile is pre-filled: hypertension, Type 2 diabetes, osteoarthritis. Four medications with specific dosing notes.
→ Scroll to show doctor, pharmacy, the lifestyle paragraph, personality notes.
> "The caregiver fills this in once by tapping the name — stays on the same page, no navigation. From this point on, every response from Pulse is grounded in who Margaret actually is."

**0:40–1:00** Senior tab — show a medication question:
> *"I forgot to take my tablet this morning"*
→ Pulse responds: *"Oh, your Lisinopril? If it's still this morning, just go ahead and take it now with a little something to eat — no need to worry. Missing one isn't the end of the world."*
> "That's the difference between a chatbot and a companion that knows her."

**1:15–1:30** Senior tab — show engagement layers:
→ Point out the Family Presence Banner: *"Sarah was thinking of you earlier today 💛"*
→ Point out the Daily Delight card (rotating memory prompt)
> "This is why Margaret opens the app on a good day — not just when something is wrong."

**1:30–2:00** Senior tab — point to the 🎤 **Tap to speak** indicator above the chat bar, then type (or speak):
> *"I felt a bit dizzy this morning when I got up. Didn't sleep well, maybe 5 hours."*
→ `st.status` opens: *"Listening carefully… Health markers noted — dizziness · sleep 5h… Pattern analysis complete"*
→ Pulse responds warmly. Water drops fall on the garden 💧.
> "Notice what Pulse didn't say: 'I've logged your symptoms.' It said 'Oh dear, do take it slowly getting up.' The data was captured invisibly."

**2:00–2:30** Switch to caregiver tab — within 3 seconds the dashboard updates:
→ At a Glance: *"Margaret reported dizziness today, which correlates with declining HRV (19ms) and only 4h of core sleep on the watch — this cross-signal pattern suggests physical exhaustion."*
→ Alert card: **⚠️ HIGH — Dizziness reported 3× this week** · *🕐 Detected [timestamp] UTC*
→ Action buttons: tap 📞 to call, 💬 to SMS, 📅 to book a visit.
> "The watch data and the conversation are telling the same story. The alert tells you exactly when it was detected — not just that it happened."

**2:30–2:50** Show the Predictive Insight card:
→ *"3 nights of poor sleep — heads up for the next 48h. Increased fatigue or joint discomfort likely within 48 hours. A gentle check-in call today could get ahead of it."* Confidence: 74%.
> "This is the feature that justifies $29 a month. Not what happened — what's about to happen."

**2:50–3:05** Check-ins tab → show 14-day calendar and compact log:
> "14 days at a glance. Red = dizziness or severity ≥ 6. The pattern is visible in seconds."

**3:05–3:20** Watch tab:
→ SpO₂ 94% (⚠ below 95%), HRV 19ms (low recovery), steps declining over 7 days.
> "The watch doesn't just display data — it's an input to the clinical reasoning."

**2:35–3:00** Report tab → auto-generated, action guidance shown first:
> "One tap. This is what Sarah hands the doctor at intake. The action cards tell her what to do with it."

**3:00–3:15** Close on the garden:
→ Point to the two-stage panel: current stage left, next stage right with days remaining.
> "Margaret's garden is Blooming today — 14 check-ins in. The caregiver can water it right here. That's the retention mechanic: Margaret tends the garden, Sarah waters it, both see the same goal. The longer they use it, the richer the baseline — and the more irreplaceable the product becomes. $29 a month. Near-zero marginal cost. Switching cost = her entire health history."

---

## 💰 Unit Economics

| Item | Value |
|------|-------|
| Price | $29.00 / caregiver / month |
| Avg check-ins | ~30 / month (1/day) |
| Avg tokens / check-in | ~1,100 input + 400 output (companion + recent context) |
| Analyst runs (30% of check-ins) | ~9 × ~2,000 tokens (history + watch data + RAG) |
| Total tokens / month | ~60,000 |
| Gemini 2.0 Flash cost | ~$0.06 |
| FAISS + SQLite infra | ~$0.10 |
| Cloud Run (shared instance) | ~$0.20 |
| **Total COGS / user / month** | **~$0.36** |
| **Gross margin** | **~98.8%** |

Break-even: ~15 paying caregivers covers fixed Cloud Run costs.
100 users = $2,900 MRR at near-zero marginal cost.

**Retention moat:** switching cost = losing the full health history and predictive baseline. Caregivers who use PulseCare for 60+ days will not churn — the baseline *is* the product.

---

## 🛠️ Local Setup

```bash
# 1. Clone
git clone <repo-url>
cd pulse

# 2. Install
pip install uv
uv sync

# 3. Run (no API key needed with gcloud ADC configured)
uv run streamlit run app.py
# or with an explicit key:
cp .env.example .env   # add GOOGLE_API_KEY or ANTHROPIC_API_KEY
uv run streamlit run app.py
```

Opens at `http://localhost:8080`.
- Senior interface: `http://localhost:8080/?view=senior`
- Caregiver dashboard: `http://localhost:8080/?view=caregiver` (default)

Demo data for Margaret (age 72) is pre-seeded on first run — 14 days of history with a gradual decline arc ending in elevated fall risk this week.

---

## ☁️ Deploy to Cloud Run

```bash
gcloud config configurations activate ieor-4576
cd ~/Desktop/pulse
gcloud builds submit --config cloudbuild.yaml
```

No API key needed on Cloud Run — Gemini runs via Vertex AI ADC.

---

## `.env.example` Explanation

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | One of these | Claude Sonnet / Haiku |
| `GOOGLE_API_KEY` | One of these | Gemini 2.0 Flash (aistudio.google.com, free) |
| `GROQ_API_KEY` | One of these | Groq free tier |
| `USE_FIRESTORE` | No | `true` for Firestore (auto-set on Cloud Run) |
| `SQLITE_PATH` | No | SQLite path (default: `pulsecare.db`) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LangGraph `StateGraph` with conditional routing |
| LLM | Gemini 2.0 Flash via Vertex AI ADC |
| Memory/Storage | SQLite (local) → Firestore (Cloud Run) |
| RAG | FAISS (dense) + BM25 (sparse) → Reciprocal Rank Fusion |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Voice Input | Web Speech API (Chrome/Edge — no external service, zero API cost) |
| Apple Watch | `tools/watch_tools.py` — SQLite `watch_data` table; fed into AnalystAgent for cross-modal synthesis |
| Zen Garden | CSS keyframe animations (sway + water drop + butterfly); 7 growth stages keyed to check-in count |
| Predictive Engine | `tools/alert_tools.py` → `generate_predictive_insight()`; rule-based leading-indicator patterns |
| Patient Profile | `tools/profile_tools.py` → `get_patient_profile()` / `save_patient_profile()`; SQLite `patient_profile` table; UI at `?view=setup` |
| Stateful Memory | `agents/companion.py` → `_build_recent_context()`; last 48h injected into CompanionAgent prompt |
| Family Presence | `tools/memory_tools.py` → `record_family_view()` / `get_last_family_view()`; SQLite `family_activity` table |
| Frontend | Streamlit — phone-frame UI (390px, CSS border-radius, Dynamic Island); `st.status()` pipeline transparency |
| Deployment | Docker → Google Cloud Run |
| CI/CD | `cloudbuild.yaml` |
| Deps | `uv` + `pyproject.toml` |
