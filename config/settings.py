# config/settings.py
"""
Global configuration file for the Secure Encrypted Shadow Copy System (Ensha).
All backend modules should import settings from here to avoid hardcoding values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------
# Load Environment Variables
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load .env file if present (optional, but useful in deployment)
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# ---------------------------
# Database Settings
# ---------------------------

# Default: local SQLite (for testing)
DB_PATH = BASE_DIR / "backup_system.db"
DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_PATH}")
DB_NAME = os.getenv("DB_NAME", "backup_system.db")

# ---------------------------
# Backup & Storage Settings
# ---------------------------

# Default storage folder (can be NAS, mounted drive, or Ubuntu server path later)
BACKUP_STORAGE = os.getenv("BACKUP_STORAGE", str(BASE_DIR / "snapshots"))

# Max number of versions per file
MAX_VERSIONS = int(os.getenv("MAX_VERSIONS", "3"))

# ---------------------------
# OTP & Security Settings
# ---------------------------

OTP_LENGTH = int(os.getenv("OTP_LENGTH", "6"))   # Default: 6-digit OTP
OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))  # 5 min expiry
DEBUG_SHOW_OTP = os.getenv("DEBUG_SHOW_OTP", "True").lower() in ("true", "1", "yes")

# Number of login retries before lockout
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))

# Encryption key storage (in real deployment, use a vault)
ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", str(BASE_DIR / "keys/master.key"))
KEY_DIR = BASE_DIR / "keys"
if not KEY_DIR.exists():
    KEY_DIR.mkdir(parents=True)


# ---------------------------
# Telegram Bot Settings
# ---------------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your-chat-id")

# ---------------------------
# Logging Settings
# ---------------------------

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "system.log"

if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

# ---------------------------
# Disaster Recovery Settings
# ---------------------------

# DR backup export location (compressed archives)
DR_EXPORT_PATH = os.getenv("DR_EXPORT_PATH", str(BASE_DIR / "dr_exports"))
DR_DIR = Path(DR_EXPORT_PATH)
if not DR_DIR.exists():
    DR_DIR.mkdir(parents=True)

# ---------------------------
# Debug Mode
# ---------------------------

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
