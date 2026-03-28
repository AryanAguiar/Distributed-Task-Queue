import os 
from dotenv import load_dotenv
import sys

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

JOB_QUEUE_KEY = "jobs:queue"
DEAD_LETTER_KEY = "jobs:dead_letter"

JOB_RESULT_TTL = 60 * 60 * 24
VISIBILITY_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_BASE = 2

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def validate():
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

# Call validate() explicitly at startup (in main.py / worker.py)
# rather than at import time, so tests and other imports don't crash.