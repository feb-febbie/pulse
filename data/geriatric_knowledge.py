"""
Geriatric medical knowledge base for PulseCare's RAG pipeline.

Curated for the eldercare use case: fall risk, dizziness, sleep disorders,
medication safety, cognitive decline, cardiac red flags, and isolation.

Each chunk is a self-contained passage that can be retrieved independently.
"""
from __future__ import annotations


_CHUNKS = [
    {
        "topic": "fall_risk",
        "text": """Fall Risk in Older Adults — Composite Signal Detection

Falls are the leading cause of injury-related death in adults over 65. The most dangerous
aspect is that falls are predictable — they result from compounding risk factors, not single events.

High-Risk Symptom Combinations:
- Dizziness + poor sleep (>2 consecutive nights) = 3x baseline fall risk
- Dizziness + new medication = medication-induced orthostatic hypotension until proven otherwise
- Dizziness + fatigue + low activity = deconditioning spiral
- Nighttime awakening + confusion = highest-risk window for falls

Orthostatic Hypotension (Most Common Fall Cause):
- Systolic BP drops >20 mmHg when standing from seated or lying position
- Causes: dehydration, antihypertensive medications, diuretics, Parkinson's
- Presentation: dizziness or lightheadedness on standing, often within 3 minutes
- Prevention: sit at edge of bed for 30 seconds before standing, adequate hydration

Environmental + Physical Factors:
- Muscle weakness after even 1-2 days of reduced activity
- Footwear: socks on hardwood or tile are high-risk
- Nighttime trips to bathroom without lights = fall risk window
- No grab bars in bathroom = structural risk

Clinical Escalation Threshold:
Dizziness reported 2+ times in one week with no prior history → recommend physician evaluation.
Dizziness + any fall (even minor) → urgent evaluation same day.""",
    },
    {
        "topic": "dizziness_elderly",
        "text": """Dizziness in Elderly — Causes, Patterns, and Red Flags

Dizziness is the #1 complaint in outpatient visits for patients over 75. It is usually multifactorial.

Positional Dizziness (BPPV — Most Common, 40% of cases):
- Brief spinning sensation (seconds to 1-2 minutes) triggered by head position change
- Occurs when lying down, rolling over, or looking up
- Epley maneuver is curative in most cases — can be performed by patient or clinician
- NOT dangerous but increases fall risk

Non-Positional Dizziness (More Concerning):
- Constant dizziness unrelated to position → vascular, medication, or metabolic cause
- Dizziness on standing (orthostatic) → blood pressure issue (see orthostatic hypotension)
- Dizziness with hearing changes → Menière's disease or acoustic neuroma
- New dizziness with no obvious trigger → needs workup

Medication-Induced Dizziness (Second Most Common):
- Any antihypertensive, diuretic, or sedating medication can cause dizziness
- Peak risk: first 2 weeks after starting or dose increase
- Diuretics in summer heat → dehydration + dizziness compound risk

Dehydration-Related Dizziness:
- Elderly have blunted thirst — chronically under-hydrated
- Even mild dehydration (2% body weight loss) causes dizziness and fatigue
- Dark urine is a reliable indicator; target pale yellow

RED FLAGS — Call 911 or Go to ER:
- Dizziness + chest pain or palpitations → cardiac emergency
- Dizziness + sudden severe headache → hemorrhagic stroke
- Dizziness + face drooping, arm weakness, or slurred speech → stroke (FAST)
- Dizziness + high fever + stiff neck → meningitis
- First occurrence of severe dizziness with vomiting → urgent evaluation

Monitoring Pattern: Dizziness recurring >2 times in one week warrants physician contact.""",
    },
    {
        "topic": "sleep_elderly",
        "text": """Sleep Disorders in Aging Adults — What's Normal vs. Concerning

Normal aging changes sleep architecture but poor sleep is NOT a normal part of aging.

Normal Changes (Not Concerning):
- Lighter sleep — more time in stages 1 and 2, less deep sleep
- Earlier natural bedtime and wake time (circadian shift)
- More brief awakenings through the night (but should return to sleep within minutes)
- Takes 15-30 minutes to fall asleep (vs. 5-10 minutes in younger adults)

Abnormal at Any Age — Requires Attention:
- Consistently sleeping fewer than 6 hours
- Waking unrefreshed most mornings
- Daytime fatigue that interferes with daily function
- Excessive daytime sleepiness (falling asleep involuntarily)
- 3+ consecutive nights of poor sleep

High-Risk Drug Classes for Sleep in Elderly:
- Benzodiazepines (Xanax, Valium, Ativan) — rebound insomnia, fall risk, dependence
- Z-drugs (Ambien, Lunesta) — complex sleep behaviors, confusion, falls
- Diphenhydramine (Benadryl, OTC sleep aids) — anticholinergic effects, cognitive impairment
- Alcohol — fragments sleep, suppresses REM

Sleep Apnea in Elderly:
- Affects 40-60% of adults over 65, most undiagnosed
- Presentation: daytime fatigue, cognitive slowing, morning headaches, nocturia
- CPAP use reduces dementia risk by 36% in elderly with OSA

Sleep and Cognitive Health:
- Brain clears amyloid beta (Alzheimer's marker) during deep sleep via glymphatic system
- Chronic poor sleep is an independent risk factor for Alzheimer's disease
- Sleep disruption + cognitive complaints = prioritize sleep evaluation

PulseCare Alert Threshold: 3 consecutive nights below 6.5 hours → caregiver notification.""",
    },
    {
        "topic": "medication_safety_elderly",
        "text": """High-Risk Medications in Elderly — Beers Criteria Summary

The American Geriatrics Society Beers Criteria identifies medications that are potentially
inappropriate in adults over 65 due to disproportionate risk.

Avoid in Most Elderly (High Risk):
- Benzodiazepines (all: Xanax, Valium, Ativan, Klonopin) — falls, cognitive impairment, dependence
- Non-BZD hypnotics (Ambien, Lunesta, Sonata) — same risks, complex behaviors
- Diphenhydramine (Benadryl, Tylenol PM, Advil PM) — strong anticholinergic, confusion, urinary retention
- Oral NSAIDs long-term (ibuprofen, naproxen, Aleve) — GI bleeding, acute kidney injury, fluid retention
- Muscle relaxants (Flexeril, Soma) — sedation, falls, limited efficacy in elderly
- Meperidine (Demerol) — toxic metabolite accumulates, seizure risk

Use with Caution — Require Monitoring:
- Diuretics (furosemide, HCTZ) — dehydration, electrolyte imbalance, dizziness (especially in heat)
- Antihypertensives — orthostatic hypotension, especially with dose changes or illness
- Antidepressants (SSRIs) — hyponatremia, falls, QT prolongation
- Tricyclic antidepressants — high fall risk, anticholinergic effects — generally avoid
- Warfarin/anticoagulants — bleeding risk amplified by drug and dietary interactions
- Digoxin — narrow therapeutic window; renal impairment increases toxicity

New Symptom + Recent Medication Change:
Dizziness, confusion, or falls appearing within 2 weeks of starting or dose-changing any
medication → report to prescribing physician; likely medication effect until proven otherwise.""",
    },
    {
        "topic": "dehydration_elderly",
        "text": """Dehydration in Elderly — Underrecognized, Frequently Dangerous

Physiologic changes create unique dehydration vulnerability in adults over 65:
- Blunted thirst sensation — do not feel thirsty even when significantly dehydrated
- Reduced kidney concentrating ability — more urine produced at lower dehydration levels
- Less total body water (45% vs. 60% in younger adults) — smaller buffer
- Many are on diuretics — increase urinary losses further

Severity and Consequences:
- Mild (1-2% body weight): Fatigue, reduced concentration, mild headache
- Moderate (3-5%): Dizziness, confusion, muscle cramps, constipation, dark urine
- Severe (>5%): Rapid heart rate, hypotension, delirium, acute kidney injury, falls

Recognizing Dehydration:
- Urine color: target pale yellow; dark yellow or amber = dehydrated
- Dry mouth, sticky saliva, chapped lips
- Headache or dizziness especially on position change
- Unusual fatigue or confusion without another clear cause
- Skin tenting: skin slow to return when gently pinched on back of hand

Daily Fluid Target:
- Minimum 1.5 liters (approximately 6 cups) daily
- Increase with fever, hot weather, vomiting, or diarrhea
- Coffee and tea count toward total (mild diuretic effect is offset by water content)

PulseCare Pattern: Dizziness + fatigue without obvious cause → encourage hydration; if not
improving within 12-24 hours or worsening → recommend medical evaluation.""",
    },
    {
        "topic": "cognitive_decline_early",
        "text": """Early Warning Signs of Cognitive Decline — Normal vs. Pathological

Early detection of cognitive decline is the single most high-value intervention window.
Mild Cognitive Impairment (MCI) to dementia transition takes 3-5 years — early action matters.

Normal Aging (Not Concerning):
- Occasionally misplacing keys or glasses
- Forgetting a name but recalling it later
- Slower processing speed for new or complex information
- Needing more time to learn new technology

Early Warning Signs — Track and Report:
- Forgetting recent conversations, not just names
- Repeating the same questions or stories within minutes
- Getting confused about dates, days, or time of year
- Difficulty with familiar tasks: following a recipe, managing finances, taking medications correctly
- Getting lost in previously familiar places or routes
- Noticeable personality change without clear cause (increased irritability, anxiety, or passivity)
- Withdrawal from social activities previously enjoyed

Symptom Language in Conversation to Flag:
"I forgot," "I can't remember," "I'm confused," "I got lost," "Where did I...,"
"What day is it" = early disclosure signals CompanionAgent should acknowledge and log.

Treatable Conditions That Mimic Dementia (Always Rule Out):
- Hypothyroidism — simple blood test, highly treatable
- Vitamin B12 deficiency — very common in elderly, injection reverses deficits
- Depression (pseudodementia) — treat depression first; cognitive symptoms often resolve
- Sleep apnea — CPAP may restore significant cognitive function within weeks
- Medication side effects — anticholinergics, benzodiazepines, high-dose beta-blockers

PulseCare Action: Confusion or memory complaints logged 2+ times in one week → flag for
caregiver review and recommend physician visit.""",
    },
    {
        "topic": "cardiac_red_flags",
        "text": """Cardiac Red Flags in Elderly — Atypical Presentations

Cardiovascular disease is the leading cause of death in adults over 65. Presentation is
frequently atypical — elderly often do not have classic chest pain.

Atypical Heart Attack Presentations in Elderly:
- No chest pain in up to 40% of elderly myocardial infarctions
- Instead: extreme unexplained fatigue, jaw or shoulder pain, nausea, shortness of breath
- "Silent MI" — discovered only on ECG during routine visit
- Confusion or feeling "not right" without obvious cause

Call 911 Immediately for Any of These:
- Sudden extreme fatigue at rest (new onset, severe)
- New palpitations or sensation of irregular heartbeat
- Fainting or near-fainting, especially with palpitations
- Shortness of breath at rest or with minimal exertion (new onset)
- Ankle swelling + fatigue + shortness of breath together → heart failure triad
- Any chest, jaw, or left arm pain or pressure

Atrial Fibrillation (AFib) — Common in Elderly:
- Affects 10% of adults over 80
- Presentation: fatigue, dizziness, palpitations, or reduced exercise tolerance
- High stroke risk — first presentation is often stroke
- Irregular pulse is a warning sign family members can detect

Stroke (FAST — Act Within Minutes):
- Face drooping (ask person to smile — is one side drooping?)
- Arm weakness (ask to raise both arms — does one drift down?)
- Speech difficulty (slurred, strange, or unable to speak)
- Time — call 911 immediately; every minute counts

PulseCare Escalation: Dizziness + palpitations + fatigue in same 48-hour period → alert
caregiver immediately with recommendation to call parent and evaluate symptoms.""",
    },
    {
        "topic": "depression_isolation",
        "text": """Depression and Social Isolation in Elderly — The Invisible Risk

Depression affects 15-20% of adults over 65 but is diagnosed and treated in fewer than half.
Social isolation compounds depression risk and independently predicts health decline.

Why Depression Is Frequently Missed:
- Patient and family normalize it ("of course she's quiet, she's 72")
- Elderly present with somatic complaints, not sadness: fatigue, aches, memory problems
- Primary care visits focused on physical conditions, missing emotional wellbeing
- Elderly less likely to self-identify as depressed due to stigma

Presentation in Elderly — Look For:
- Persistent fatigue and low energy (most common presenting complaint)
- Loss of interest in previously enjoyed activities (cooking, gardening, visits)
- Sleep disruption — typically early morning awakening (before 4-5am)
- Appetite loss with weight loss
- Increased pain complaints without new physical cause
- Withdrawal and reduced communication
- Increased irritability or emotional flatness

Social Isolation Health Consequences:
- Equivalent health risk to smoking 15 cigarettes per day (Holt-Lunstad, 2015)
- 50% increased dementia risk
- 29% increased coronary heart disease risk
- Faster functional decline across all chronic conditions
- Reduced medication adherence and help-seeking

PulseCare Role:
- Daily CompanionAgent conversation provides structured social contact
- Caregiver dashboard prompts family engagement when alerts fire
- Reducing isolation is itself a therapeutic intervention

Monitoring Signal: Reduced disclosure quality (shorter answers, "fine" to everything),
withdrawal language, or consistent low mood logged over 5+ days → caregiver check-in needed.""",
    },
    {
        "topic": "fall_prevention_actions",
        "text": """Fall Prevention — Actionable Steps for Seniors and Families

Evidence-based interventions that reduce fall risk by 30-50%:

For the Senior:
1. Hydration: 6+ cups of fluid daily; drink a glass of water before getting up in the morning
2. Standing protocol: Always sit at edge of bed or chair for 30 seconds before standing
3. Footwear: Never walk on hardwood or tile floors in socks; wear non-slip slippers at home
4. Nighttime: Keep a nightlight on the path from bed to bathroom; never rush to bathroom
5. Medications: Review all medications with doctor annually; ask specifically about fall risk
6. Exercise: Balance and strength training (chair yoga, tai chi) reduce falls 30% over 6 months
7. Vision: Annual eye exam; cataracts and poor glasses prescriptions are modifiable fall risks

For the Home Environment:
- Remove loose rugs or secure edges with non-slip tape
- Install grab bars in bathroom (toilet, shower, tub entry)
- Move frequently used items to waist height — avoid reaching high or bending low
- Ensure good lighting throughout, especially stairs and hallways
- Telephone/cell phone always within reach (floor is most common fall location)

For the Caregiver:
- Home safety assessment — many local senior services provide free evaluations
- Medical alert device for solo seniors
- Regular medication review with physician, especially after any fall
- Ensure annual vision and hearing checks

Immediate Action After a Fall (Even Minor):
- Do not minimize. Even a "minor" fall indicates elevated risk for the next one.
- Physician evaluation within 24-48 hours to identify modifiable causes
- Document: time, location, what they were doing, any symptoms immediately before""",
    },
]


def get_all_text_chunks() -> list[dict]:
    """Return all knowledge chunks for FAISS + BM25 indexing."""
    return _CHUNKS
