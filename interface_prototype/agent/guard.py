"""Guarded read-only SQL execution against gov.db.

The executor — not the model — is responsible for safety. Four independent
layers, any one of which would hold on its own:

1. The connection is opened ``file:gov.db?mode=ro``. SQLite itself refuses
   every write.
2. A SQLite authorizer whitelists SELECT / READ / FUNCTION / RECURSIVE and a
   single internal PRAGMA (``data_version``, which FTS5's vtable constructor
   issues). Everything else — ATTACH, DETACH, any DDL or DML — is denied
   inside the engine, before a byte is read.
3. A textual prefilter: one statement, must open with SELECT or WITH, no
   forbidden keyword anywhere outside a string literal.
4. Row, byte and wall-clock caps on the result, with truncation reported
   explicitly so a partial answer can never pass for a complete one.

Every query is logged with its row count — the audit trail a journalist needs
when an editor asks where a number came from.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Sequence

from . import config


# --------------------------------------------------------------------------
# errors
# --------------------------------------------------------------------------

class QueryRejected(Exception):
    """The query was refused before or during execution."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class QueryTimeout(Exception):
    """The query exceeded config.QUERY_TIMEOUT_MS."""


# --------------------------------------------------------------------------
# result
# --------------------------------------------------------------------------

@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    truncation_reason: str | None
    elapsed_ms: int
    sql_submitted: str
    sql_executed: str
    limit_applied: int | None = None
    notices: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# textual prefilter
# --------------------------------------------------------------------------

# Anything that is not a read. Matched as whole words against SQL with its
# comments and string literals blanked out, so a query *searching* for the
# word "delete" in minutes text is not mistaken for a DELETE statement.
FORBIDDEN_KEYWORDS = (
    "attach", "detach", "pragma", "create", "drop", "alter", "insert",
    "update", "delete", "replace", "truncate", "vacuum", "reindex",
    "analyze", "begin", "commit", "rollback", "savepoint", "release",
    "trigger", "grant", "revoke",
)
FORBIDDEN_FUNCTIONS = ("load_extension", "readfile", "writefile", "edit", "fts3_tokenizer")

_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(FORBIDDEN_KEYWORDS + FORBIDDEN_FUNCTIONS) + r")\b",
    re.IGNORECASE,
)
_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)
_LEADING_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


def scrub(sql: str) -> str:
    """Blank out comments and quoted spans, preserving length and structure.

    Returns a same-length string where every character inside a comment,
    string literal, or quoted identifier has been replaced by a space. Keyword
    and semicolon scanning runs against this, never against the raw text.
    """
    out = list(sql)
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                out[i] = " "
                i += 1
        elif ch == "/" and i + 1 < n and sql[i + 1] == "*":
            out[i] = out[i + 1] = " "
            i += 2
            while i < n and not (sql[i] == "*" and i + 1 < n and sql[i + 1] == "/"):
                out[i] = " "
                i += 1
            for j in range(i, min(i + 2, n)):
                out[j] = " "
            i += 2
        elif ch in "'\"`":
            quote = ch
            out[i] = " "
            i += 1
            while i < n:
                if sql[i] == quote:
                    out[i] = " "
                    i += 1
                    if i < n and sql[i] == quote:      # doubled = escaped
                        out[i] = " "
                        i += 1
                        continue
                    break
                out[i] = " "
                i += 1
        elif ch == "[":
            out[i] = " "
            i += 1
            while i < n and sql[i] != "]":
                out[i] = " "
                i += 1
            if i < n:
                out[i] = " "
                i += 1
        else:
            i += 1
    return "".join(out)


_LITERAL_RE = re.compile(r"'((?:[^']|'')*)'")


def string_literals(sql: str) -> list[str]:
    """Every single-quoted literal in the query, unescaped.

    The caveat layer reads these to spot entity names written out in full
    (``WHERE name = 'Salt Lake City'``) rather than as slugs.
    """
    return [m.group(1).replace("''", "'") for m in _LITERAL_RE.finditer(sql)]


def validate(sql: str) -> tuple[str, str]:
    """Reject anything that is not a single read-only statement.

    Returns ``(sql_stripped, scrubbed)``. Raises QueryRejected otherwise.
    """
    if not sql or not sql.strip():
        raise QueryRejected("empty query")

    stripped = sql.strip()
    scrubbed = scrub(stripped)

    # Trailing semicolon is fine; an interior one means a second statement.
    # Walk back only over characters that are semicolons/whitespace in BOTH the
    # raw and scrubbed text — a blanked closing quote reads as a space in the
    # scrubbed copy, and chopping it would corrupt the query.
    end = len(stripped)
    while end and stripped[end - 1] in "; \t\r\n" and scrubbed[end - 1] in "; \t\r\n":
        end -= 1
    if end != len(stripped):
        stripped = stripped[:end]
        scrubbed = scrubbed[:end]
    if ";" in scrubbed:
        raise QueryRejected(
            "multiple statements are not allowed",
            "submit one SELECT (or WITH ... SELECT) per call",
        )

    if not _LEADING_RE.match(scrubbed):
        first = stripped.split(None, 1)[0] if stripped.split() else stripped
        raise QueryRejected(
            "only SELECT and WITH queries are allowed",
            f"query begins with {first!r}; this layer is read-only",
        )

    hit = _FORBIDDEN_RE.search(scrubbed)
    if hit:
        raise QueryRejected(
            f"forbidden keyword {hit.group(1).upper()!r}",
            "gov.db is derived and opened read-only; it is never written from this layer",
        )

    return stripped, scrubbed


def apply_limit(sql: str, scrubbed: str, limit: int) -> tuple[str, int | None]:
    """Wrap a LIMIT-less query so SQLite can stop early.

    If the query already carries a LIMIT anywhere we leave it alone — the
    fetch-side cap in :func:`run_query` is the actual guarantee, this is only
    an optimisation.

    Note the ``limit + 1``: fetching one row beyond the cap is what lets
    :func:`run_query` tell "exactly n rows" apart from "n rows and more behind
    them". Reporting a truncated result as complete is the one failure mode
    this layer cannot have.
    """
    if _LIMIT_RE.search(scrubbed):
        return sql, None
    return f"SELECT * FROM (\n{sql}\n) LIMIT {limit + 1}", limit


# --------------------------------------------------------------------------
# engine-level guard
# --------------------------------------------------------------------------

_ALLOWED_ACTIONS = frozenset({
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
})

# FTS5's vtable constructor reads this on every MATCH. Nothing else gets through.
_ALLOWED_PRAGMAS = frozenset({"data_version"})


def _make_authorizer(denials: list[str]):
    def authorizer(action, arg1, arg2, dbname, source):
        if action in _ALLOWED_ACTIONS:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_PRAGMA and (arg1 or "").lower() in _ALLOWED_PRAGMAS:
            return sqlite3.SQLITE_OK
        denials.append(f"action={action} arg1={arg1!r} arg2={arg2!r}")
        return sqlite3.SQLITE_DENY
    return authorizer


def connect() -> sqlite3.Connection:
    """A fresh read-only connection. Callers must close it."""
    conn = sqlite3.connect(config.DB_URI, uri=True, timeout=5.0)
    conn.isolation_level = None
    return conn


# --------------------------------------------------------------------------
# value coercion
# --------------------------------------------------------------------------

def coerce(value: Any) -> Any:
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    text = value if isinstance(value, str) else str(value)
    if len(text) > config.MAX_CELL_CHARS:
        return text[: config.MAX_CELL_CHARS] + f"… [cell truncated, {len(text)} chars]"
    return text


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------

def run_query(sql: str, limit: int | None = None, log: bool = True) -> QueryResult:
    """Validate, execute and cap one read-only statement."""
    row_limit = config.DEFAULT_ROW_LIMIT if limit is None else int(limit)
    row_limit = max(1, min(row_limit, config.MAX_ROW_LIMIT))

    stripped, scrubbed = validate(sql)
    executed, limit_applied = apply_limit(stripped, scrubbed, row_limit)

    denials: list[str] = []
    started = time.monotonic()
    deadline = started + config.QUERY_TIMEOUT_MS / 1000.0
    timed_out = False

    def progress():
        nonlocal timed_out
        if time.monotonic() > deadline:
            timed_out = True
            return 1
        return 0

    conn = connect()
    try:
        conn.set_authorizer(_make_authorizer(denials))
        conn.set_progress_handler(progress, config.PROGRESS_HANDLER_STEPS)
        try:
            cur = conn.execute(executed)
            columns = [d[0] for d in cur.description] if cur.description else []

            rows: list[list[Any]] = []
            truncated = False
            reason: str | None = None
            nbytes = 0
            while True:
                raw = cur.fetchone()
                if raw is None:
                    break
                if len(rows) >= row_limit:
                    truncated = True
                    reason = f"row cap: showing first {row_limit} rows"
                    break
                row = [coerce(v) for v in raw]
                nbytes += len(json.dumps(row, default=str))
                if nbytes > config.MAX_RESULT_BYTES and rows:
                    truncated = True
                    reason = (
                        f"byte cap: showing first {len(rows)} rows "
                        f"(~{config.MAX_RESULT_BYTES // 1024} KB)"
                    )
                    break
                rows.append(row)
            cur.close()
        except sqlite3.ProgrammingError as exc:
            if "one statement at a time" in str(exc):
                raise QueryRejected("multiple statements are not allowed", str(exc)) from exc
            raise QueryRejected("query error", str(exc)) from exc
        except sqlite3.Error as exc:
            if timed_out:
                raise QueryTimeout(
                    f"query exceeded {config.QUERY_TIMEOUT_MS} ms and was aborted"
                ) from exc
            if denials:
                raise QueryRejected(
                    "query denied by the read-only authorizer", "; ".join(denials[:3])
                ) from exc
            raise QueryRejected("query error", str(exc)) from exc
    finally:
        conn.set_progress_handler(None, 0)
        conn.close()

    elapsed_ms = int((time.monotonic() - started) * 1000)
    result = QueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        truncation_reason=reason,
        elapsed_ms=elapsed_ms,
        sql_submitted=stripped,
        sql_executed=executed,
        limit_applied=limit_applied,
    )
    if log:
        log_query(stripped, result=result)
    return result


# --------------------------------------------------------------------------
# audit trail
# --------------------------------------------------------------------------

def log_query(sql: str, result: QueryResult | None = None, error: str | None = None) -> None:
    """Append one line to interface_prototype/logs/queries.jsonl."""
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sql": sql,
        "rows": result.row_count if result else None,
        "truncated": result.truncated if result else None,
        "elapsed_ms": result.elapsed_ms if result else None,
        "error": error,
    }
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with config.QUERY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break a query


def query_rows(sql: str, params: Sequence[Any] = ()) -> tuple[list[str], list[tuple]]:
    """Internal helper for the tool layer's own parameterised queries.

    Not reachable from user input — the tools construct these — so it skips the
    textual prefilter, but keeps mode=ro and the authorizer.
    """
    denials: list[str] = []
    conn = connect()
    try:
        conn.set_authorizer(_make_authorizer(denials))
        cur = conn.execute(sql, params)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        cur.close()
        return columns, rows
    finally:
        conn.close()
