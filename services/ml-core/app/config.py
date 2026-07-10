"""Central configuration loaded from environment (.env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- LLM ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

# Rolling tokens-per-minute budget. Kept under Groq's free-tier 6000 TPM.
GROQ_TPM_BUDGET: int = int(os.getenv("GROQ_TPM_BUDGET", "5000"))

# Circuit breaker: consecutive failures before we stop calling the LLM.
LLM_FAILURE_THRESHOLD: int = int(os.getenv("LLM_FAILURE_THRESHOLD", "3"))

# --- Resume / profile ---
RESUME_PDF_PATH: str = os.getenv("RESUME_PDF_PATH", "")
PROFILE_PATH = DATA_DIR / "profile.json"
RESUME_ASSET_PATH = DATA_DIR / "resume.pdf"  # served to the extension for uploads

# --- Storage ---
DB_PATH = DATA_DIR / "career_os.db"

# --- Notifications (optional, free) ---
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Behavior flags ---
# When True, the agent fills everything but pauses for the user to confirm final submit.
REVIEW_BEFORE_SUBMIT: bool = os.getenv("REVIEW_BEFORE_SUBMIT", "false").lower() == "true"

# CORS origins allowed to call the backend (the extension + localhost tooling).
ALLOWED_ORIGINS = ["*"]
