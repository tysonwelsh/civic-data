"""Shared config for the meeting-minutes project (PrimeGov scrape + vote analysis)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MINUTES_DIR = BASE_DIR / "minutes"

MODEL = "claude-sonnet-4-6"   # see ../public_comments for the model-retirement note
MAX_TOKENS = 8000


def _load_dotenv():
    """Load ANTHROPIC_API_KEY (and any KEY=VAL) from a gitignored .env."""
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
