"""
Curated medical knowledge base for Pulse RAG.

Each document chunk is a dict with:
  id        — unique string
  title     — source label shown to user
  content   — text to embed and retrieve
  symptoms  — list of symptom tags for keyword fallback
  red_flags — True if chunk describes emergency warning signs
"""
from __future__ import annotations

MEDICAL_DOCUMENTS: list[dict] = [

    # ── HEADACHES ─────────────────────────────────────────────────────────────

    {
        "id": "headache_tension",
        "title": "Tension-Type Headache",
        "symptoms": ["headache", "head pain", "pressure"],
        "red_flags": False,
        "content": """
Tension-type headaches are the most common headache disorder, affecting up to 78% of the general population.
They are characterized by a dull, aching, steady pain that feels like a tight band or pressure around the head.
They are typically bilateral (both sides), not pulsating, and of mild to moderate intensity.

Common triggers:
- Sleep deprivation or disrupted sleep
- Stress and anxiety
- Dehydration (even mild, ~2% body weight fluid loss)
- Caffeine withdrawal — occurs 12–24 hours after last intake in habitual users
- Eye strain from prolonged screen time
- Skipped meals / low blood sugar
- Poor posture, neck tension

Pattern clues:
- Episodic tension headaches: fewer than 15 days per month
- Chronic tension headaches: 15 or more days per month for 3+ months
- Recurring at the same time of day (e.g., after long work sessions) suggests a specific trigger

Management:
- OTC analgesics: ibuprofen (400–600mg) or acetaminophen (500–1000mg) at onset
- Address the trigger: hydrate, sleep, take a screen break
- Do NOT overuse pain medication — rebound (medication overuse) headaches occur with >10 OTC doses/month
- Caffeine: a single dose of caffeine can relieve acute headache but causes rebound if used repeatedly
        """.strip(),
    },

    {
        "id": "headache_migraine",
        "title": "Migraine",
        "symptoms": ["migraine", "headache", "nausea", "light sensitivity", "aura"],
        "red_flags": False,
        "content": """
Migraines are recurrent, often unilateral headaches of moderate to severe intensity, lasting 4–72 hours.
They are frequently accompanied by nausea, vomiting, and sensitivity to light (photophobia) and sound (phonophobia).
About 25% of migraines are preceded by an aura — visual disturbances, tingling, or speech difficulty.

Common triggers:
- Sleep changes — both too little AND too much sleep can trigger migraines
- Hormonal changes (menstrual cycle)
- Caffeine: both excess intake and caffeine withdrawal
- Alcohol, especially red wine
- Certain foods: processed meats, aged cheeses, artificial sweeteners
- Bright or flickering lights
- Stress, then "let-down" after stress resolves

Frequency patterns:
- Episodic migraine: fewer than 15 headache days per month
- Chronic migraine: 15+ headache days per month, with 8+ being migraine
- Increasing frequency over weeks suggests a worsening pattern needing medical attention

When to seek care:
- 4+ migraine days per month consistently → preventive medication discussion warranted
- New aura symptoms you haven't had before
- See red flags below
        """.strip(),
    },

    {
        "id": "headache_rebound",
        "title": "Medication Overuse Headache (Rebound)",
        "symptoms": ["headache", "rebound", "daily headache"],
        "red_flags": False,
        "content": """
Medication overuse headache (MOH), also called rebound headache, is caused by frequent use of headache medications.
It is paradoxically caused by the treatment itself and is one of the most common causes of chronic daily headache.

Threshold for rebound:
- Simple analgesics (ibuprofen, acetaminophen): >15 days/month
- Triptans, opioids, combination analgesics: >10 days/month

Signs:
- Headache present on waking
- Headache improves with medication but returns as it wears off
- Headache is worse than the original headache type
- Medication stops working as well over time

Management: gradual withdrawal of the overused medication under guidance.
        """.strip(),
    },

    {
        "id": "headache_red_flags",
        "title": "Headache Red Flags — When to Seek Emergency Care",
        "symptoms": ["headache", "emergency", "red flag"],
        "red_flags": True,
        "content": """
SEEK IMMEDIATE EMERGENCY CARE for any of the following:

1. Thunderclap headache: sudden, severe headache that reaches maximum intensity within 60 seconds
   ("worst headache of my life") — possible subarachnoid hemorrhage

2. Headache + fever + stiff neck + rash — possible bacterial meningitis (medical emergency)

3. Headache + neurological symptoms: confusion, slurred speech, facial drooping, arm weakness,
   vision loss, difficulty walking — possible stroke (call 911 immediately)

4. Headache after head trauma — possible intracranial bleed

5. New severe headache in anyone over 50, especially on one side with scalp tenderness
   — possible temporal arteritis

6. Progressive headache that is steadily worsening over days/weeks — possible mass lesion

7. Headache that wakes you from sleep regularly — needs evaluation

NONE of the red flags above are present with typical tension or migraine headaches.
If you have a familiar headache pattern and no red flag features, it is almost certainly benign.
        """.strip(),
    },

    {
        "id": "headache_sleep_caffeine",
        "title": "Headache: Sleep Deprivation and Caffeine Connection",
        "symptoms": ["headache", "sleep", "caffeine", "coffee"],
        "red_flags": False,
        "content": """
Sleep and caffeine are two of the strongest modifiable headache triggers.

Sleep deprivation and headache:
- Even one night of poor sleep (<6 hours) significantly increases headache risk the next day
- Sleep deprivation lowers pain thresholds — you feel more pain from the same stimulus
- The connection is bidirectional: headache can also disrupt sleep
- Irregular sleep schedules (varying bedtime by >1 hour) increase migraine frequency

Caffeine and headache:
- Regular caffeine consumption (>200mg/day, roughly 2 cups coffee) creates physiological dependence
- Caffeine withdrawal headache begins 12–24 hours after last intake
- Peak intensity at 20–51 hours, resolves within 2–9 days of complete abstinence
- Pattern: headache reliably appears on days with less coffee than usual
- Solution: either taper caffeine gradually or maintain consistent daily intake

The sleep-caffeine-headache triangle:
- Poor sleep → more coffee to compensate → higher caffeine dependence → withdrawal headache when intake drops
- This creates a self-reinforcing cycle common in students and professionals under deadline pressure
        """.strip(),
    },

    # ── FATIGUE ───────────────────────────────────────────────────────────────

    {
        "id": "fatigue_general",
        "title": "Fatigue: Causes and Assessment",
        "symptoms": ["fatigue", "tired", "exhausted", "low energy"],
        "red_flags": False,
        "content": """
Fatigue is one of the most common presenting complaints. It is almost never a single-cause problem.

Most common causes in young adults (22–35):
1. Sleep debt — cumulative effect of insufficient sleep; cannot be recovered in a single night
2. Nutritional: iron deficiency (especially in women), vitamin D deficiency, B12 deficiency
3. Dehydration — mild dehydration causes measurable cognitive and energy decline
4. Sedentary lifestyle — paradoxically, low physical activity increases fatigue
5. High cognitive load / mental fatigue — screen-heavy academic or office work is genuinely tiring
6. Anemia — fatigue + pallor + dyspnea on exertion
7. Thyroid dysfunction (hypothyroidism) — fatigue + cold intolerance + weight gain + brain fog
8. Depression or anxiety — mental health conditions are the most common cause of persistent fatigue

Assessment questions:
- Is fatigue present on waking (not refreshed by sleep)? → suggests thyroid, depression, sleep apnea
- Does it develop during the day? → suggests sleep debt or nutritional issue
- Is it worse after exertion? → if severe, consider post-viral fatigue
- Duration: acute (<1 month) vs. subacute vs. chronic (>6 months)

Tracking: note sleep hours, meals skipped, and stress level alongside fatigue to identify patterns.
        """.strip(),
    },

    {
        "id": "fatigue_sleep_debt",
        "title": "Sleep Debt and Cumulative Fatigue",
        "symptoms": ["fatigue", "tired", "sleep debt", "sleep deprivation"],
        "red_flags": False,
        "content": """
Sleep debt is cumulative. Missing 2 hours of sleep per night for a week produces impairment
equivalent to 24 hours of total sleep deprivation — equivalent to a 0.10% blood alcohol level.

Key facts:
- Adults need 7–9 hours; individual needs are largely genetically determined
- Short sleep (<6 hours) is the strongest predictor of next-day fatigue and cognitive impairment
- "Catching up" on weekends partially restores performance but does not eliminate metabolic effects
- Chronic sleep debt increases risk of: headaches, impaired immune function, weight gain,
  mood dysregulation, and reduced academic/work performance

Signs of accumulated sleep debt:
- Falling asleep within 5 minutes of lying down
- Falling asleep in meetings or classes without intending to
- Needing an alarm to wake (well-rested people often wake naturally)
- Feeling significantly better after one long sleep

Recovery: estimated 4 days of full-duration sleep to recover from one week of partial sleep deprivation.
        """.strip(),
    },

    {
        "id": "fatigue_red_flags",
        "title": "Fatigue Red Flags — When to See a Doctor",
        "symptoms": ["fatigue", "tired", "red flag"],
        "red_flags": True,
        "content": """
See a doctor for fatigue if any of the following are present:

1. Fatigue lasting more than 2–4 weeks without an obvious cause (no sleep debt, no illness)
2. Fatigue + unexplained weight loss — possible malignancy, diabetes, thyroid disease
3. Fatigue + shortness of breath at rest or with minimal exertion — possible anemia or cardiac issue
4. Fatigue + cold intolerance + constipation + dry skin — possible hypothyroidism (very treatable)
5. Fatigue + persistent low mood, loss of interest, sleep changes — possible depression
6. Fatigue + joint pain + rash (especially butterfly rash on face) — possible autoimmune condition
7. Severe fatigue that crashes after physical activity (post-exertional malaise) — possible ME/CFS

For most young adults without red flags: track sleep hours and consistency for 2 weeks.
If fatigue resolves with adequate sleep, it was sleep debt. If it persists, get labs checked.
        """.strip(),
    },

    # ── SLEEP ─────────────────────────────────────────────────────────────────

    {
        "id": "sleep_hygiene",
        "title": "Sleep: Quantity, Quality, and Health Impact",
        "symptoms": ["sleep", "insomnia", "sleep quality"],
        "red_flags": False,
        "content": """
Sleep is the single most important recovery process in the body. During sleep:
- Brain clears metabolic waste products (glymphatic system)
- Memory consolidation occurs (REM sleep)
- Immune function is restored
- Hormones regulating hunger, stress, and growth are calibrated

Optimal sleep for adults: 7–9 hours at consistent times (same bedtime ±30 min).

Sleep architecture:
- NREM Stage 3 (deep sleep): peaks in first half of night. Critical for physical restoration.
- REM sleep: peaks in second half. Critical for emotional processing and memory.
- Cutting sleep short disproportionately eliminates REM sleep.

Common disruptors in students and young professionals:
- Screen use before bed: blue light suppresses melatonin for 2–3 hours
- Irregular schedules (social jet lag): varying sleep time by >90 min impairs sleep quality
- Alcohol: accelerates sleep onset but fragments the second half; reduces REM
- Caffeine: half-life 5–7 hours; 3pm coffee still has significant effect at midnight

Tracking sleep: note both bedtime and wake time. Sleep duration alone is less predictive
than sleep consistency (same schedule) and sleep efficiency (% of time in bed actually asleep).
        """.strip(),
    },

    # ── GI ISSUES ─────────────────────────────────────────────────────────────

    {
        "id": "gi_general",
        "title": "GI Issues: Nausea, Stomach Pain, Bloating",
        "symptoms": ["nausea", "stomach", "GI", "bloating", "stomach pain", "cramps"],
        "red_flags": False,
        "content": """
Gastrointestinal symptoms are extremely common and usually benign in young adults.

Common causes:
- Stress and anxiety: the gut-brain axis is highly sensitive. Stress causes nausea, cramping, diarrhea.
- Dietary triggers: fatty foods, excess caffeine, alcohol, artificial sweeteners (sorbitol, xylitol)
- Eating pattern changes: skipping meals → excess stomach acid → nausea
- Indigestion: eating too fast, large meals, eating while stressed
- IBS (irritable bowel syndrome): very common in students; alternating constipation/diarrhea with cramping,
  worsened by stress. Not dangerous, but significantly impacts quality of life.
- Gastroenteritis (stomach flu): nausea + vomiting + diarrhea, usually 24–72 hours, self-resolving

Pattern recognition:
- Always after coffee on empty stomach → coffee-induced gastritis or acid
- Always before a stressful event → stress-related IBS pattern
- After specific foods → food intolerance or sensitivity
- Waking up nauseated → morning cortisol response, low blood sugar, or acid reflux

Management (mild cases):
- Eat smaller, more frequent meals
- Reduce coffee on empty stomach
- BRAT diet for acute gastroenteritis (bananas, rice, applesauce, toast)
- OTC antacids or H2 blockers for acid-related symptoms
        """.strip(),
    },

    {
        "id": "gi_red_flags",
        "title": "GI Red Flags — When to Seek Medical Care",
        "symptoms": ["nausea", "stomach", "GI", "red flag", "blood"],
        "red_flags": True,
        "content": """
Seek medical care for GI symptoms if any of the following are present:

1. Blood in stool (red or black/tarry stool) — possible bleeding ulcer or GI bleed
2. Vomiting blood or material that looks like coffee grounds — upper GI bleed (emergency)
3. Severe abdominal pain that is constant and worsening — appendicitis, obstruction, other surgical emergency
4. Pain + fever — possible infection (appendicitis, diverticulitis, colitis)
5. Unintentional weight loss + GI symptoms — needs evaluation
6. GI symptoms + jaundice (yellowing of skin/eyes) — liver or gallbladder issue
7. Diarrhea lasting more than 2 weeks — especially if bloody or with mucus
8. Dysphagia (difficulty swallowing) — especially if progressive
9. Severe nausea/vomiting that prevents keeping any fluid down for >24 hours — risk of dehydration
        """.strip(),
    },

    # ── CORRELATIONS AND PATTERNS ─────────────────────────────────────────────

    {
        "id": "pattern_sleep_symptom",
        "title": "Symptom Patterns: The Sleep-Symptom Connection",
        "symptoms": ["pattern", "correlation", "sleep", "headache", "fatigue"],
        "red_flags": False,
        "content": """
Sleep is the most powerful single predictor of next-day symptom burden in young adults.

Evidence-based correlations:
- <6 hours of sleep: increases headache risk 2–3x compared to 7–8 hours
- <6 hours of sleep: increases next-day fatigue severity by ~40%
- Sleep deprivation reduces pain threshold — makes all physical symptoms feel worse
- REM-poor sleep (from alcohol or early waking) impairs emotional regulation → anxiety → more symptoms

Practical pattern analysis:
- If headaches cluster on days following short sleep: sleep debt is the primary driver
- If fatigue is worse after nights <7 hours: address sleep before any other intervention
- If both headache and fatigue appear after poor sleep: treat the sleep, not the symptoms

The crunch-period pattern (common in students):
  Week 1: sleep 5–6 hours → accumulate debt → headache and fatigue appear
  Week 2: compensate with more coffee → caffeine tolerance rises → withdrawal headaches
  Week 3: symptoms become "daily" → seems like a health problem → is actually a lifestyle pattern
  Resolution: 4–7 days of adequate sleep + caffeine taper eliminates most symptoms
        """.strip(),
    },

    # ── SLEEP SCIENCE & SUPPLEMENTS ──────────────────────────────────────────────

    {
        "id": "sleep_root_causes",
        "title": "What Actually Disrupts Sleep: Root Causes and Fixes",
        "symptoms": ["sleep", "insomnia", "wake up", "can't sleep", "poor sleep", "sleep quality"],
        "red_flags": False,
        "content": """
Sleep disruption has specific, addressable causes. Generic "sleep hygiene" advice fails because it ignores the user's actual pattern.

Root causes ranked by prevalence in young adults:

1. LATE CAFFEINE — caffeine half-life is 5–7 hours. A 3pm coffee still has 50% of its effect at 9pm,
   blocking adenosine receptors and preventing sleep pressure from building.
   Fix: cut caffeine after 1–2pm. Takes 3–5 days to see the full effect.

2. IRREGULAR SCHEDULE — varying sleep time by >60 minutes shifts your circadian rhythm, making sleep
   harder to initiate (social jet lag). Even one late night disrupts the following 2–3 nights.
   Fix: same wake time every day (including weekends) — this is the anchor. Bedtime will follow.

3. SCREEN LIGHT BEFORE BED — blue light suppresses melatonin production by 2–3 hours.
   Fix: dim screens 1 hour before target sleep time, or use night mode at maximum warmth.

4. HIGH EVENING CORTISOL — stress, intense exercise late in the day, or stimulating content
   (news, social media, arguments) spikes cortisol, which directly opposes melatonin.
   Fix: a wind-down routine 30–60 min before bed (dim light, no conflict content, light stretching).

5. ALCOHOL — alcohol feels sedating but fragments sleep in the second half of the night.
   It suppresses REM sleep and causes early waking. Even 1–2 drinks 3 hours before bed impacts quality.
   Fix: no alcohol within 3–4 hours of sleep.

6. EATING LATE — large meals within 2 hours of bed raise core body temperature (digestion is thermogenic),
   which delays sleep onset. The body needs to cool 1–2°F to initiate sleep.
   Fix: finish eating 2–3 hours before bed.

7. ROOM TEMPERATURE — ideal sleep temperature is 65–68°F / 18–20°C. Even slightly warm rooms
   significantly impair deep sleep stages.

8. LOW MAGNESIUM — magnesium is required for GABA activation (the main inhibitory neurotransmitter
   that enables sleep). Modern diets are frequently deficient. Deficiency causes light sleep, muscle
   cramps, and difficulty falling asleep. Lab testing is unreliable (intracellular levels).
   Fix: 300–400mg magnesium glycinate before bed. Glycinate form has highest absorption and
   fewest GI side effects. Takes 1–2 weeks for full effect.
        """.strip(),
    },

    {
        "id": "sleep_supplements",
        "title": "Sleep Supplements: Evidence-Based Guide with Doses",
        "symptoms": ["sleep", "supplement", "melatonin", "magnesium", "can't sleep"],
        "red_flags": False,
        "content": """
Evidence-based sleep supplements, ranked by evidence quality and safety:

1. MAGNESIUM GLYCINATE — strongest evidence for sleep improvement in people with deficiency.
   Dose: 300–400mg elemental magnesium, taken 30–60 min before bed.
   Effect: reduces time to fall asleep, improves sleep quality scores, reduces nighttime waking.
   Onset: 1–2 weeks of consistent use.
   Safety: very safe. May cause loose stools at high doses (switch to glycinate form to avoid).
   Best for: people with muscle tension, anxiety, irregular sleep, high stress.

2. MELATONIN — regulates circadian timing, not sleep depth. Widely misused.
   Correct dose: 0.5–1mg (NOT 5–10mg commonly sold). Higher doses cause next-day grogginess.
   Timing: 1–2 hours before desired sleep time.
   Best for: shifting sleep timing (jet lag, delayed sleep phase). Less effective for staying asleep.
   Note: over-the-counter melatonin in the US is often 3–10x the effective dose.

3. L-THEANINE — amino acid found in green tea. Promotes relaxation without sedation.
   Dose: 100–200mg before bed. Often combined with magnesium.
   Effect: reduces sleep latency, improves sleep quality scores. No tolerance or dependence.
   Safety: excellent. No next-day grogginess.

4. ASHWAGANDHA (KSM-66 extract) — adaptogen that reduces cortisol over time.
   Dose: 300–600mg KSM-66 extract, taken at night.
   Effect: improves sleep quality primarily by reducing stress hormones, not direct sedation.
   Onset: 4–8 weeks of consistent use for full cortisol-lowering effect.
   Best for: people whose sleep disruption is driven by high stress/anxiety.

5. GLYCINE — amino acid that lowers core body temperature, improving sleep onset and depth.
   Dose: 3g before bed.
   Evidence: 3 RCTs showing improved sleep quality, reduced daytime fatigue.

NOT recommended without medical evaluation:
   - Prescription sedatives (dependency risk)
   - Diphenhydramine (Benadryl) — tolerance develops within 3–4 days, worsens sleep long term

Interaction check: supplements above are all safe to combine. Avoid combining with alcohol.
        """.strip(),
    },

    {
        "id": "hrv_sleep_stress",
        "title": "HRV: What It Tells You About Sleep and Stress",
        "symptoms": ["HRV", "heart rate variability", "resting heart rate", "stress", "recovery"],
        "red_flags": False,
        "content": """
Heart Rate Variability (HRV) is the variation in time between consecutive heartbeats.
High HRV = nervous system can shift rapidly between sympathetic (alert) and parasympathetic (rest) states.
Low HRV = nervous system is stuck in stress mode, limiting recovery capacity.

HRV is the most sensitive early-warning signal for:
- Accumulated sleep debt (HRV drops before you feel tired)
- Overtraining or illness onset (HRV drops 1–2 days before symptoms appear)
- Chronic stress (sustained HRV suppression)
- Alcohol consumption the night before (consistent HRV suppressor)

Interpreting your HRV:
- Compare your HRV to YOUR baseline, not population norms (HRV is highly individual)
- A drop of >15–20% below your 30-day baseline is significant
- Consistent low HRV for 3+ days = meaningful signal, not noise
- HRV highest on nights with adequate sleep, no alcohol, low stress, cool room

HRV and sleep correlation:
- Nights with <6h sleep reliably suppress next-morning HRV by 15–30%
- Alcohol before bed suppresses HRV by 10–20% even with adequate sleep duration
- Magnesium supplementation has been shown to raise nocturnal HRV

Actionable thresholds:
- HRV ≥ your personal baseline: proceed normally, you're recovered
- HRV 15% below baseline: reduce intensity, prioritize sleep
- HRV >25% below baseline: rest day, investigate cause (sleep debt? illness? alcohol?)
        """.strip(),
    },

    {
        "id": "nutrition_energy_sleep",
        "title": "Nutrition: What You Eat Affects Sleep and Energy",
        "symptoms": ["fatigue", "energy", "brain fog", "sleep", "diet", "iron", "vitamin D", "B12"],
        "red_flags": False,
        "content": """
Nutritional deficiencies are a common, overlooked cause of fatigue and poor sleep in young adults.

KEY DEFICIENCIES TO CHECK (bloodwork):

1. IRON / FERRITIN — most common nutritional deficiency globally.
   Symptoms: fatigue, cold hands/feet, brain fog, restless legs at night (disrupts sleep).
   Ferritin below 30 ng/mL causes symptoms even if hemoglobin is normal.
   Fix: iron-rich foods (red meat, legumes, dark greens) + vitamin C to enhance absorption.
   Supplement: only with confirmed deficiency — excess iron is harmful.
   Note: Restless leg syndrome from iron deficiency is a significant, underdiagnosed sleep disruptor.

2. VITAMIN D — major deficiency in people who spend most of the day indoors.
   Symptoms: fatigue, low mood, increased illness frequency, muscle weakness.
   Affects sleep: vitamin D receptors are involved in sleep regulation; deficiency is associated
   with shorter sleep duration and poorer sleep quality.
   Fix: 1,000–2,000 IU daily (take with fat, in the morning — not at night, may disrupt sleep).
   Lab range: aim for 40–60 ng/mL serum 25-OH vitamin D.

3. VITAMIN B12 — critical for nerve function and energy production.
   Deficiency common in: vegetarians/vegans, people with GI issues, prolonged antacid use.
   Symptoms: fatigue, brain fog, tingling, mood changes.
   Fix: B12 is poorly absorbed orally above trace amounts. Methylcobalamin sublingual (under tongue)
   or injections are most effective. Standard oral supplements are largely ineffective.

4. MAGNESIUM — affects both sleep (see sleep supplements) and energy production.
   Most adults are deficient due to modern diet. Absorbed better as glycinate or malate.

BLOOD SUGAR AND ENERGY:
- Skipping meals causes blood sugar drops → fatigue, brain fog, irritability, poor concentration
- High-sugar meals cause energy spikes then crashes 2–3 hours later
- Protein + complex carbs + fat at each meal stabilizes energy throughout the day
- Eating within 1 hour of waking sets up better energy regulation for the whole day
        """.strip(),
    },

    {
        "id": "anxiety_stress_sleep",
        "title": "Anxiety and Stress: Impact on Sleep and Physical Symptoms",
        "symptoms": ["anxiety", "stress", "sleep", "racing mind", "heart racing", "fatigue"],
        "red_flags": False,
        "content": """
Anxiety is one of the most common causes of sleep disruption, fatigue, and physical symptoms in young adults.
It operates through two primary mechanisms: cortisol elevation and hyperarousal.

How anxiety disrupts sleep:
- Racing mind at bedtime (cognitive arousal) delays sleep onset
- Elevated cortisol at night prevents the natural cortisol drop needed to fall asleep
- Light, fragmented sleep — the anxious nervous system stays partially alert
- Early morning waking (4–5am) is a classic anxiety-related sleep pattern

Physical symptoms of anxiety that are often mistaken for other conditions:
- Heart palpitations / racing heart (not dangerous, very common with anxiety)
- Nausea and GI distress (gut-brain axis)
- Headaches (muscle tension + sympathetic overdrive)
- Fatigue (paradoxically — hyperarousal is exhausting)
- Chest tightness, shortness of breath

The anxiety-sleep-symptom cycle:
  Anxiety → poor sleep → more anxiety → more physical symptoms → more anxiety about symptoms → worse sleep

Breaking the cycle:
1. Address the sleep first — cognitive behavioral therapy for insomnia (CBT-I) is more effective
   than sleep medication for anxiety-related insomnia. Free apps: Sleepio, CBTI Coach.
2. Breathwork: 4-7-8 breathing (inhale 4s, hold 7s, exhale 8s) activates parasympathetic nervous system.
   Do 4 cycles at bedtime.
3. Reduce stimulants: caffeine amplifies anxiety significantly — caffeine after noon is
   often the single highest-leverage intervention for anxious people with sleep problems.
4. Ashwagandha (KSM-66, 300–600mg) reduces cortisol in people with chronic stress.
   Takes 4–8 weeks for full effect.
5. Magnesium glycinate 300mg at night — also has anxiolytic (anti-anxiety) properties.
        """.strip(),
    },

    {
        "id": "pattern_when_to_escalate",
        "title": "Decision Framework: When to See a Doctor",
        "symptoms": ["doctor", "escalate", "when to seek care"],
        "red_flags": False,
        "content": """
Most minor symptoms in young adults (22–35) resolve with lifestyle changes.
The key question is: does this symptom pattern suggest a modifiable cause, or something that needs investigation?

See a doctor if:
- Any red flag symptom is present (see individual red flag entries)
- Symptoms persist despite addressing the obvious cause for 2–4 weeks
- Symptoms are worsening progressively rather than fluctuating
- Symptoms significantly impair daily function (can't study, can't sleep, can't eat)
- You have a known medical condition that could be flaring
- You're worried — your judgment matters, and reassurance is a legitimate medical service

Do NOT see a doctor immediately if:
- Symptoms appeared after an obvious trigger (poor sleep, stress, dietary change)
- Symptoms improve after addressing the trigger
- Symptoms follow a familiar, previously-investigated pattern
- No red flags are present

When you do see a doctor, bring:
- A symptom log: dates, severity (1–10), duration, associated factors (sleep hours, stress, food, exercise)
- A clear timeline: when symptoms started, frequency, any changes over time
- What you've tried and whether it helped
Organized symptom data saves the doctor intake time and leads to faster, better diagnosis.
        """.strip(),
    },
]


def get_all_text_chunks() -> list[dict]:
    """Return all documents as flat list for FAISS indexing."""
    return MEDICAL_DOCUMENTS


def get_document_by_id(doc_id: str) -> dict | None:
    for doc in MEDICAL_DOCUMENTS:
        if doc["id"] == doc_id:
            return doc
    return None
