import os 
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

JOB_QUEUE_KEY = "jobs:queue"
JOB_RESULTS_KEY = "job:results"
DEAD_LETTER_KEY = "jobs:dead_letter"

JOB_RESULT_TTL = 60 * 60 * 24
VISIBILITY_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_BASE = 2

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
