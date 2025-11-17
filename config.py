"""
Configuration file for University Merch Bot.

All project-wide settings, paths, and constants are defined here.
Sensitive credentials are loaded from .env file.
"""

from pathlib import Path
from typing import List
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
UNIVERSITIES_RAW_JSON = DATA_DIR / "universities_raw.json"
EMAILS_EXTRACTED_CSV = DATA_DIR / "emails_extracted.csv"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# API endpoints
UNIVERSITIES_API_URL = "https://universities.hipolabs.com/search?country=United+States"

# Crawling settings
CONTACT_PAGE_PATHS: List[str] = [
    "/contact",
    "/contact-us",
    "/admissions",
    "/international",
    "/undergraduate",
    "/graduate",
    "/student-services",
    "/about"
]

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "8"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))  # seconds between requests

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Email extraction patterns
VALID_EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
VALID_DOMAIN_SUFFIX_PATTERN = r'.*@(.*\.edu|.*university\.org)'

INVALID_EMAIL_PREFIXES: List[str] = [
    "careers@",
    "jobs@",
    "hr@",
    "press@",
    "newsroom@",
    "security@",
    "webmaster@",
    "abuse@",
    "marketing@"
]

PRIORITY_EMAIL_PREFIXES: List[str] = [
    "admissions@",
    "info@",
    "international@",
    "contact@",
    "outreach@",
    "global@"
]

# Email sending settings (from environment variables)
EMAIL_THROTTLE_DELAY = float(os.getenv("EMAIL_THROTTLE_DELAY", "40"))  # seconds between emails
EMAIL_JITTER_MIN = float(os.getenv("EMAIL_JITTER_MIN", "3"))  # seconds
EMAIL_JITTER_MAX = float(os.getenv("EMAIL_JITTER_MAX", "7"))  # seconds
EMAIL_MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", "2"))

# Gmail SMTP settings (loaded from .env file)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")  # Load from .env
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")  # Load from .env
SENDER_NAME = os.getenv("SENDER_NAME", "Gaurav Sharma")

# Sender information
SENDER_INFO = {
    "name": SENDER_NAME,
    "address": """Gaurav Sharma
670, Nature Villa, Manglam Grand City
Opp. Pink Pearl Water Park, Mahapura
Jaipur, Rajasthan, India — 302026"""
}

# Database statuses
STATUS_PENDING = "PENDING"
STATUS_SENT = "SENT"
STATUS_FAILED = "FAILED"
STATUS_RETRYING = "RETRYING"
STATUS_COMPLETE = "COMPLETE"

# Logging settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
