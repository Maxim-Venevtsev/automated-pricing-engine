from pathlib import Path
import os
from dotenv import load_dotenv

# =========================================================
# PROJECT ROOT (auto-detect)
# =========================================================

# settings.py лежит в:
# project_root/configs/settings.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# =========================================================
# DATA DIRECTORIES (new structure)
# =========================================================

DATA_DIR = PROJECT_ROOT / "data"

INCOMING_DIR = DATA_DIR / "incoming"
STAGING_DIR = DATA_DIR / "staging"
OUTPUT_DIR = DATA_DIR / "output"
VALIDATION_DIR = DATA_DIR / "validation"
REFERENCE_DIR = DATA_DIR / "reference"
STATE_DIR = DATA_DIR / "state"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [
    INCOMING_DIR,
    STAGING_DIR,
    OUTPUT_DIR,
    VALIDATION_DIR,
    REFERENCE_DIR,
    STATE_DIR,
    LOG_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# =========================================================
# REFERENCE FILES
# =========================================================

BASE_PRICE_FILE = REFERENCE_DIR / "base_price.xlsx"
LIQUIDITY_COEF_FILE = REFERENCE_DIR / "liquidity_coef.xlsx"
LIQUIDITY_CATEGORY_FILE = REFERENCE_DIR / "liquidity_category.xlsx"
ALLOWED_PRICE_GROUPS_FILE = REFERENCE_DIR / "allowed_price_groups.xlsx"

# =========================================================
# STATE FILES
# =========================================================

ITEMS_PRESENCE_REGISTRY = STATE_DIR / "items_presence_registry.csv"

# =========================================================
# PRICING CONSTANTS
# =========================================================

NEW_DAYS = 14
RESTART_THRESHOLD_DAYS = 90
LIQUIDITY_WINDOW_DAYS = 28

# =========================================================
# IMAP
# =========================================================

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_EMAIL = os.getenv("IMAP_EMAIL")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

# =========================================================
# SMTP
# =========================================================

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# =========================================================
# MYSQL
# =========================================================

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}