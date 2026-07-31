"""Shared configuration for vision-based PDF extraction."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # the project dir, wherever it lives


def _load_dotenv():
    """Load KEY=VALUE lines from a local .env so scripts pick up ANTHROPIC_API_KEY
    automatically. A value already in the environment takes precedence."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()
PROGRESS_DIR = BASE_DIR / "progress"
RAW_DIR = PROGRESS_DIR / "raw"
PROGRESS_FILE = PROGRESS_DIR / "progress.json"
OUTPUT_CSV = BASE_DIR / "all_comments_vision.csv"

MODEL = "claude-sonnet-4-6"  # was claude-sonnet-4-20250514 (retired); update as models evolve
MAX_TOKENS = 16384
RENDER_SCALE = 2.0
JPEG_QUALITY = 85
# Anthropic rejects images with any dimension > 8000px and internally downscales
# anything with a long edge > 1568px. Cap the long edge so large pages don't error.
MAX_IMAGE_DIM = 1568

UNIFIED_COLUMNS = [
    "date", "contact_name", "subject", "topic", "comment",
    "district", "source", "has_attachment", "source_file", "page_number",
]

SYSTEM_PROMPT = """You are a data extraction specialist. You will be shown a single page from a Salt Lake City Council public comment PDF. Your job is to extract structured data from the page.

Each page falls into one of two categories:
1. TABLE PAGE: Contains a table of public comments with columns like Date, Name, Subject, Comment, District, etc. Extract every row.
2. NON-TABLE PAGE: Contains an attachment (letter, scanned image, form, petition, etc.) or is blank. Return an empty comments array.

Rules:
- Extract ALL rows visible on the page, even partial rows at the top or bottom
- For partial rows (text cut off at page boundary), extract what is visible and set "is_partial": true
- If a row contains continuation markers like "Continued 1/2", "2/2", "(Continued)", or "CONTINUED!!", set "is_continuation": true and include the part number in "continuation_marker"
- Preserve the EXACT text from each cell. Do not summarize, paraphrase, or truncate comments.
- If a cell is empty, use an empty string ""
- If a row mentions attachments (e.g., "**Attachment", "*See Corresponding Attachment"), set "has_attachment": true
- The column layout varies by year. Map whatever columns you see to the closest matching field names below.

Respond with ONLY valid JSON (no markdown fences, no commentary) in this exact structure:
{
  "page_type": "table" or "non_table",
  "columns_detected": ["list", "of", "column", "headers", "visible"],
  "comments": [
    {
      "date": "",
      "contact_name": "",
      "subject": "",
      "topic": "",
      "comment": "",
      "district": "",
      "source": "",
      "has_attachment": false,
      "is_continuation": false,
      "is_partial": false,
      "continuation_marker": ""
    }
  ]
}

Field mapping guidance:
- "date": Date/Time Opened, Date Submitted & Format, Date, CreationDate
- "contact_name": Contact Name, Name, Names
- "subject": Subject
- "topic": Topic, Popular Topic
- "comment": Comment, Description, Message, or the main body of text in the widest column
- "district": District, District (Optional)
- "source": Source (e.g., Online Forum, Email, Voicemail, Phone Call, Council Comments)
- "has_attachment": true if attachment markers are present in the row"""
