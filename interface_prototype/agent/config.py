"""Paths and caps for the read-only data layer. Stdlib only."""

import os
from pathlib import Path

# interface_prototype/agent/config.py -> repo root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_DIR = REPO_ROOT / "interface_prototype"

# --- credentials -------------------------------------------------------
# The repo's convention is an untracked per-dataset `.env` (see the root
# .gitignore); this layer's lives in interface_prototype/. Load it here rather
# than in chat.py so the credential is present no matter which entry point
# imports us — server, a REPL, or a verify script.
#
# An already-exported variable always wins, so `ANTHROPIC_API_KEY=... python3
# server.py` still overrides the file, and no secret is ever written back out.
ENV_FILES = (PROTOTYPE_DIR / ".env", REPO_ROOT / ".env")


def load_env(paths=ENV_FILES) -> list[str]:
    """Fill unset environment variables from `KEY=value` files. Returns the
    names actually set, so a caller can report the source without the value."""
    loaded: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue                      # absent or unreadable is not an error
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.removeprefix("export ").strip()
            value = value.strip().strip('"').strip("'")
            if key and value and not os.environ.get(key):
                os.environ[key] = value
                loaded.append(key)
    return loaded


LOADED_ENV_KEYS = load_env()

DB_PATH = REPO_ROOT / "gov.db"
DB_URI = f"file:{DB_PATH}?mode=ro"

LOG_DIR = PROTOTYPE_DIR / "logs"
QUERY_LOG = LOG_DIR / "queries.jsonl"

# One line per completed question: tokens, cost, turns, which tools ran. The
# `done` event carries these to the browser and they vanish there, so nothing
# persisted the cost of a real question — and a spend ceiling cannot be sized
# from a guess. This file is the evidence the ceiling gets set from.
CHAT_LOG = LOG_DIR / "chat.jsonl"

# --- result caps -------------------------------------------------------
# A journalist gets a fact, not a data dump; the model gets a bounded tool
# result. Truncation is always reported so neither mistakes a partial answer
# for a complete one.
DEFAULT_ROW_LIMIT = 200
MAX_ROW_LIMIT = 1000
MAX_RESULT_BYTES = 256_000
MAX_CELL_CHARS = 2_000

# Wall-clock ceiling for one statement, enforced via a progress handler.
QUERY_TIMEOUT_MS = 15_000
PROGRESS_HANDLER_STEPS = 2_000

# --- caveat injection --------------------------------------------------
MAX_CAVEATS = 40

# --- document reading --------------------------------------------------
DOC_MAX_CHARS = 40_000

# --- full-text search --------------------------------------------------
SEARCH_DEFAULT_LIMIT = 20
SEARCH_MAX_LIMIT = 100
SNIPPET_TOKENS = 18

# --- repo grep ---------------------------------------------------------
# Content search over the committed text layer — the documentation and
# provenance files FTS does not index (CLAUDE.md, TODO.md, index.csv, the
# per-entity dataset docs). Two engines, same contract:
#
#   ripgrep   preferred, and what production should install. Its matcher is a
#             finite automaton, so a hostile pattern cannot backtrack — the
#             reason `regex=True` is safe to expose on a public endpoint.
#   stdlib    the fallback when no rg binary is on PATH. Correct but slower: a
#             measured full-repo literal sweep is ~16s against ripgrep's ~2s.
#
# Both honour GREP_DEADLINE_MS and report *why* a result stopped rather than
# trimming silently, so a partial sweep is never mistaken for a complete one.
GREP_DEFAULT_LIMIT = 60
GREP_MAX_LIMIT = 300
GREP_MAX_PER_FILE = 20            # one file cannot flood the whole result
GREP_MAX_PATTERN_CHARS = 400
GREP_MAX_LINE_CHARS = 400         # a matched line is a citation, not a payload
GREP_MAX_RESULT_BYTES = 120_000
GREP_DEADLINE_MS = 15_000

# The committed text layer. `raw/` and `_backups/` are excluded here as well as
# by .gitignore — they are 42 GB and 7.7 GB of re-fetchable originals, and a
# hosted deployment does not carry them at all.
GREP_SUFFIXES = frozenset({
    ".md", ".txt", ".csv", ".json", ".geojson", ".html", ".xml",
    ".yml", ".yaml", ".sql", ".py", ".sh", ".cff",
})
GREP_EXCLUDE_DIRS = frozenset({
    "raw", "raw_pdf", "_backups", ".git", "__pycache__", ".claude", ".vscode",
})

# --- server ------------------------------------------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
