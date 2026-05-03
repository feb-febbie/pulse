"""Central configuration for PulseCare."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Storage ────────────────────────────────────────────────────────────────────
IS_CLOUD_RUN = bool(os.environ.get("K_SERVICE", ""))
USE_FIRESTORE = os.environ.get("USE_FIRESTORE", "true" if IS_CLOUD_RUN else "false").lower() == "true"
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "pulsecare_health_log")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "pulsecare.db")

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vectorstore")

# ── App constants ──────────────────────────────────────────────────────────────
MAX_HISTORY_DAYS = 60
APP_TITLE = "PulseCare"

# ── Demo persona ───────────────────────────────────────────────────────────────
PARENT_NAME = "Margaret"
PARENT_AGE = 72
CAREGIVER_NAME = "Sarah"
PARENT_PHONE = "+1-212-555-0190"   # replace with real number for SMS/call links

# ── Alert thresholds ───────────────────────────────────────────────────────────
SLEEP_WARNING_HOURS = 6.5        # below this = poor sleep night
SLEEP_CONSECUTIVE_THRESHOLD = 3  # consecutive poor nights before alerting
FALL_RISK_SYMPTOM = "dizziness"  # key symptom triggering fall risk pathway
FALL_RISK_WEEKLY_THRESHOLD = 2   # occurrences/week above baseline triggers alert
SYMPTOM_SPIKE_RATIO = 2.0        # this week vs baseline ratio to alert
SLEEP_DEVIATION_PCT = 0.15       # % drop from baseline to alert
