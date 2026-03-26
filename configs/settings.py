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
# BASE DIRECTORIES
# =========================================================

DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

# =========================================================
# RUNTIME DIRECTORIES
# =========================================================

INCOMING_DIR = DATA_DIR / "incoming"
STAGING_DIR = DATA_DIR / "staging"
OUTPUT_DIR = DATA_DIR / "output"
VALIDATION_DIR = DATA_DIR / "validation"
STATE_DIR = DATA_DIR / "state"

# =========================================================
# REFERENCE DIRECTORIES
# =========================================================

REFERENCE_DIR = DATA_DIR / "reference"
EMAIL_TEMPLATES_DIR = REFERENCE_DIR / "email_templates"

# =========================================================
# FUTURE / RESERVED DIRECTORIES (contracts-cleanup stage)
# =========================================================

BASE_PRICE_SNAPSHOTS_DIR = REFERENCE_DIR / "base_price_snapshots"
SEND_MANIFESTS_DIR = STATE_DIR / "send_manifests"
SEND_HISTORY_DIR = STATE_DIR / "send_history"
OUTPUT_PROFILES_DIR = OUTPUT_DIR / "profiles"

# =========================================================
# ENSURE DIRECTORIES EXIST
# =========================================================

for directory in [
    # Runtime
    INCOMING_DIR,
    STAGING_DIR,
    OUTPUT_DIR,
    VALIDATION_DIR,
    STATE_DIR,

    # Reference
    REFERENCE_DIR,
    EMAIL_TEMPLATES_DIR,

    # Future reserved
    BASE_PRICE_SNAPSHOTS_DIR,
    SEND_MANIFESTS_DIR,
    SEND_HISTORY_DIR,
    OUTPUT_PROFILES_DIR,

    # Logs
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
# IMAP CONFIG
# =========================================================

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_EMAIL = os.getenv("IMAP_EMAIL")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

# =========================================================
# SMTP CONFIG
# =========================================================

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# =========================================================
# MYSQL CONFIG
# =========================================================

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}