import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Hard Compliance & Guardrail Constraints
MAX_RETRIES_ALLOWED = 3
MAX_DISCOUNT_PERCENT = 5.0
NPCI_WINDOW_START_HOUR = 8   # 08:00 AM IST
NPCI_WINDOW_END_HOUR = 20    # 08:00 PM IST
DEFAULT_MODEL = "gemini-2.5-flash"