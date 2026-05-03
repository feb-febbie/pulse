# PulseCare: AI Health Monitoring for Aging Parents

**Columbia MSOR — AI Agent Engineering — Spring 2025**
**GitHub:** *(link to repo)* · **Live URL:** `https://pulse-health-[hash]-uc.a.run.app`

---

## The User

The primary customer of PulseCare is not the person whose health is being tracked. It is their adult child.

In the United States, there are approximately 48 million family caregivers — adults who provide unpaid care to a parent or older relative. Most of them live separately from the parent they worry about. They have demanding jobs, families of their own, and a persistent, low-grade anxiety that something is wrong with mom and they won't find out until it's too late. The specific user PulseCare is designed for is a 35–50 year old adult child who has a parent living independently, cannot be present daily, and has tried calling more frequently — only to hear "I'm fine" and nothing else.

The friction is structural. Aging parents systematically underreport symptoms. They don't want to worry their children. They don't notice gradual decline. And even when they do notice, they lack the vocabulary to communicate health patterns over a phone call. The adult child, in turn, receives a single data point — today's "I'm fine" — and has no way to see the trend.

PulseCare creates the visibility layer that phone calls cannot. It gives the adult child what they actually want: not a device, not a medication tracker, not a life alert button — but a longitudinal window into their parent's daily health, surfaced as actionable signals rather than raw data.

---

## The Problem

The adult child's problem is not that they lack access to information about their parent's health. It is that the information is invisible.

When Margaret (72) woke up dizzy on Monday, she told no one. When she woke up dizzy again on Thursday and had to hold the wall, she told no one. When she skipped the senior center for the third time in a week because she wasn't feeling well, she told no one. By the time her daughter Sarah noticed something was wrong — during a Sunday phone call, three weeks in — Margaret had already fallen once (minor) and the pattern was fully established.

The tools available to Sarah today do not solve this problem. Apple Health requires Margaret to actively use it. Medication reminders assume the problem is adherence, not detection. Life Alert addresses emergencies, not trends. And a phone call — however frequent — is a point-in-time sample of whatever Margaret chooses to report.

What's missing is not monitoring hardware. It's a conversational interface that a 72-year-old will actually use daily, combined with pattern recognition that turns daily reports into actionable caregiver signals.

The specific failure mode that PulseCare targets is fall risk. Falls are the leading cause of injury death in Americans over 65. They are largely predictable: dizziness, balance problems, and sleep disruption are the three most common precursors, and they typically appear over a 5–14 day window before a serious fall. That window is PulseCare's product. It is wide enough to intervene, narrow enough to matter, and currently invisible to every caregiver who relies on phone calls.

---

## The Economics

PulseCare is a caregiver subscription product priced at $29 per month. The customer is Sarah, not Margaret. This is the correct pricing architecture: the person experiencing anxiety and willing to pay is the adult child, not the senior, and the unit of value delivered — peace of mind, early warning — is worth substantially more to a caregiver than a tracking tool is worth to the person being tracked.

The cost structure is structurally favorable because of how the product is used. Margaret checks in once a day. Each check-in involves a warm conversational response from the CompanionAgent (~800 input / 400 output tokens) plus, on days when meaningful health signals are detected, an analyst run (~1,500 tokens). At current Gemini 2.0 Flash pricing, the monthly LLM cost per user is approximately $0.05. Infrastructure — Cloud Run, SQLite, FAISS — adds another $0.30. Total COGS is approximately $0.35 per user per month, yielding a gross margin of approximately 98.8%.

The economics survive significant cost inflation. At 10× the current LLM cost, margin falls to approximately 88%, still excellent for a software business. The unit economics do not depend on usage volume within a month; a caregiver who checks the dashboard fifty times costs the same as one who checks it once, because the check-ins are senior-side, not caregiver-side.

Break-even is approximately 15 paying subscribers, covering fixed Cloud Run costs. At 100 subscribers — reachable through a single university's alumni network — monthly recurring revenue is $2,900 at near-zero marginal cost. The 500-subscriber milestone, approximately $14,500 MRR, is achievable through a targeted content and referral strategy within the eldercare space within 12–18 months of launch.

The retention mechanism is the product itself. The value of PulseCare is proportional to the length of the personal baseline. A caregiver whose parent has been logging for 60 days has a baseline that makes every new signal interpretable. A caregiver who is 6 months in has something that cannot be exported or replicated. Churn requires abandoning that data. In user research on comparable health-tracking tools, 6-week retention rates exceed 80% for users who have passed the 14-day mark. PulseCare's retention moat is not a lock-in feature — it is an accumulation of irreplaceable personal health history.

---

## Why These Technical Choices

Every technical decision in PulseCare was made to serve either the caregiver's need for accurate signals or the senior's need for a low-friction daily interaction. These two requirements point in opposite directions, and the architecture was designed to satisfy both simultaneously.

**Two agents instead of one.** A single agent cannot be both warm and clinical. An agent that responds empathetically to "I felt a little dizzy this morning" is poorly calibrated to produce a structured risk assessment citing geriatric fall-risk literature. An agent calibrated for clinical precision will not feel like a "kind, attentive friend" to a 72-year-old. PulseCare uses two agents — CompanionAgent for the senior, AnalystAgent for the caregiver — each with a distinct system prompt, optimized for a different output quality. The shared state (HealthState TypedDict passed through the LangGraph StateGraph) ensures that what CompanionAgent logs, AnalystAgent reasons over, without any duplicated data handling.

**Conditional routing.** The AnalystAgent is the expensive reasoning step. It calls the LLM with a 60-day health history and a geriatric medical knowledge base. Running it on every check-in — including "I'm fine" days — would triple monthly LLM costs without adding caregiver value. LangGraph's conditional edges allow the graph to route to AnalystAgent only when CompanionAgent detected a meaningful health signal: symptoms present, or severity ≥ 5. This single routing decision reduces AnalystAgent invocations by approximately 60%, keeping the monthly cost structure viable.

**Hybrid RAG over a geriatric knowledge base.** Medical credibility is the difference between a health journaling app and a tool a caregiver trusts enough to act on. PulseCare grounds every AnalystAgent response in a curated geriatric knowledge base using hybrid retrieval: FAISS dense vector search (semantic queries — "my head hurts") combined with BM25 sparse keyword scoring (exact terminology — "orthostatic hypotension"), fused via Reciprocal Rank Fusion. Neither retrieval method alone is sufficient: dense retrieval misses exact medical terms; sparse retrieval misses semantic paraphrases. RRF combines both without requiring score normalization.

**Tool calling as the persistence layer.** PulseCare's core product is the health history. Without tool calls, CompanionAgent could have a warm conversation and forget it immediately. The `log_health_entry()` tool call is what writes structured data to SQLite — turning a natural language conversation into a longitudinal medical record. `get_summarized_history()` performs the inverse: compresses that record into a token-efficient representation for injection into AnalystAgent's context. This compression (raw entries for the last 7 days; statistical baseline for older history) controls the token cost as the history grows, without sacrificing the personalization that makes the analysis valuable.

**Context engineering as the differentiator.** The entire value proposition of PulseCare rests on a single architectural decision: injecting the senior's full personal health history into every AnalystAgent prompt. Without this context, every analysis is generic — identical to what any LLM would produce for any 72-year-old patient. With it, the analysis is specific: "This is Margaret's fourth dizziness episode in 14 days, compared to her prior baseline of one per month. The pattern began 8 days ago, coinciding with a persistent drop in sleep hours from her baseline of 7.4h to an average of 5.3h this week." That sentence is the product. It is not possible with a stateless model. It requires deliberately injecting the right history in the right compressed format at the right point in the agent pipeline — which is what the HealthState TypedDict and the context engineering layer in AnalystAgent do.
