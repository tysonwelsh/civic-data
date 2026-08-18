"""The tool surface the agent sees (CHAT_PLAN.md §2.3).

Seven tools over guard.py and caveats.py. Every one of them returns caveat rows
alongside its data — including read_document and search_text, because a quote
pulled from a tally-only city's minutes needs its ceiling attached just as much
as a count does.

Each function returns a plain JSON-serialisable dict and raises nothing the
caller has to catch: failures come back as ``{"error": ...}`` so a tool result
can always be handed straight to the model.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable, Iterator

from . import caveats, config, guard


# --------------------------------------------------------------------------
# 1. run_sql
# --------------------------------------------------------------------------

def run_sql(sql: str, limit: int | None = None) -> dict:
    """Execute one read-only SELECT and attach everything that limits it."""
    try:
        result = guard.run_query(sql, limit=limit)
    except guard.QueryRejected as exc:
        guard.log_query(sql, error=exc.reason)
        return {"error": "rejected", "reason": exc.reason, "detail": exc.detail}
    except guard.QueryTimeout as exc:
        guard.log_query(sql, error="timeout")
        return {"error": "timeout", "reason": str(exc)}

    payload = result.to_dict()
    payload.update(caveats.applicable(sql, result.columns, result.rows))
    return payload


# --------------------------------------------------------------------------
# 2. search_text
# --------------------------------------------------------------------------

# Each corpus: the FTS table, the column snippet() should quote, and the SQL
# that turns an FTS hit into a citable row with a repo-root-relative path.
# The tier-dependent path prefix (entity.dir) is resolved HERE so the model
# never has to reconstruct it.
_CORPORA: dict[str, dict[str, Any]] = {
    "minutes": {
        "table": "fts_minutes",
        "snippet_col": 0,
        "sql": """
            SELECT f.city, e.name AS entity_name, e.level AS gov_level,
                   f.dataset, f.date, NULL AS title,
                   e.dir || '/' || f.path AS path,
                   snippet(fts_minutes, 0, '>>', '<<', '…', {tokens}) AS passage
            FROM fts_minutes f
            JOIN entity e ON e.slug = f.city
            WHERE fts_minutes MATCH ?
        """,
        "date_col": "f.date",
        "city_col": "f.city",
        "dataset_col": "f.dataset",
    },
    "packets": {
        "table": "fts_packet",
        "snippet_col": 1,
        "sql": """
            SELECT f.city, e.name AS entity_name, e.level AS gov_level,
                   f.packet_kind AS dataset, f.date, f.title,
                   e.dir || '/' || f.text_path AS path,
                   snippet(fts_packet, 1, '>>', '<<', '…', {tokens}) AS passage
            FROM fts_packet f
            JOIN entity e ON e.slug = f.city
            WHERE fts_packet MATCH ?
        """,
        "date_col": "f.date",
        "city_col": "f.city",
        "dataset_col": "f.packet_kind",
    },
    "ordinances": {
        "table": "fts_ordinance",
        "snippet_col": 1,
        "sql": """
            SELECT f.city, e.name AS entity_name, e.level AS gov_level,
                   'ordinances' AS dataset, NULL AS date,
                   f.ordinance_no || ' — ' || COALESCE(f.title, '') AS title,
                   CASE WHEN f.text_path IS NULL OR f.text_path = '' THEN NULL
                        ELSE e.dir || '/' || f.text_path END AS path,
                   snippet(fts_ordinance, 1, '>>', '<<', '…', {tokens}) AS passage
            FROM fts_ordinance f
            JOIN entity e ON e.slug = f.city
            WHERE fts_ordinance MATCH ?
        """,
        "date_col": None,
        "city_col": "f.city",
        "dataset_col": None,
    },
    "comments": {
        "table": "fts_comment",
        "snippet_col": 2,
        "sql": """
            SELECT cm.city, e.name AS entity_name, e.level AS gov_level,
                   'public_comments' AS dataset, cm.date_normalized AS date,
                   cm.subject AS title, NULL AS path,
                   snippet(fts_comment, 2, '>>', '<<', '…', {tokens}) AS passage
            FROM fts_comment f
            JOIN comment cm ON cm.comment_id = f.rowid
            JOIN entity e ON e.slug = cm.city
            WHERE fts_comment MATCH ?
        """,
        "date_col": "cm.date_normalized",
        "city_col": "cm.city",
        "dataset_col": None,
    },
    "motions": {
        "table": "fts_motion",
        "snippet_col": 0,
        "sql": """
            SELECT m.city, e.name AS entity_name, m.gov_level,
                   COALESCE(b.name, '') AS dataset, mt.meeting_date AS date,
                   m.motion_type AS title, NULL AS path,
                   snippet(fts_motion, 0, '>>', '<<', '…', {tokens}) AS passage
            FROM fts_motion f
            JOIN motion m ON m.motion_id = f.rowid
            JOIN entity e ON e.slug = m.city
            LEFT JOIN meeting mt ON mt.meeting_id = m.meeting_id
            LEFT JOIN body b ON b.body_id = m.body_id
            WHERE fts_motion MATCH ?
        """,
        "date_col": "mt.meeting_date",
        "city_col": "m.city",
        "dataset_col": None,
    },
}

CORPORA = tuple(_CORPORA)


def _resolve_slug(name: str) -> str | None:
    idx = caveats.index()
    key = (name or "").strip()
    if key in idx.entities:
        return key
    return idx.by_name.get(key.lower())


def search_text(query: str, corpus: str = "minutes", entity: str | None = None,
                dataset: str | None = None, date_from: str | None = None,
                date_to: str | None = None, limit: int = config.SEARCH_DEFAULT_LIMIT) -> dict:
    """FTS5 sweep over one corpus, returning passages and openable paths."""
    if corpus not in _CORPORA:
        return {"error": "bad_corpus", "reason": f"corpus must be one of {list(CORPORA)}"}
    if not (query or "").strip():
        return {"error": "empty_query", "reason": "search_text needs a query"}

    spec = _CORPORA[corpus]
    limit = max(1, min(int(limit), config.SEARCH_MAX_LIMIT))

    where: list[str] = []
    params: list[Any] = [query]

    slug = None
    if entity:
        slug = _resolve_slug(entity)
        if slug is None:
            return {
                "error": "unknown_entity",
                "reason": f"no entity matches {entity!r}",
                "hint": "call resolve_entity first",
            }
        where.append(f"{spec['city_col']} = ?")
        params.append(slug)

    if dataset:
        if spec["dataset_col"] is None:
            return {"error": "no_dataset_filter",
                    "reason": f"the {corpus} corpus has no dataset axis"}
        where.append(f"{spec['dataset_col']} = ?")
        params.append(dataset)

    if (date_from or date_to) and spec["date_col"] is None:
        return {"error": "no_date_filter",
                "reason": f"the {corpus} corpus carries no date column"}
    if date_from:
        where.append(f"{spec['date_col']} >= ?")
        params.append(date_from)
    if date_to:
        where.append(f"{spec['date_col']} <= ?")
        params.append(date_to)

    sql = spec["sql"].format(tokens=config.SNIPPET_TOKENS)
    if where:
        sql += " AND " + " AND ".join(where)
    sql += f" ORDER BY rank LIMIT {limit + 1}"

    try:
        columns, rows = guard.query_rows(sql, params)
    except sqlite3.OperationalError as exc:
        # FTS5 rejects some bare punctuation; retry the input as a phrase so a
        # natural-language query is not simply lost.
        if "fts5" in str(exc).lower() or "syntax error" in str(exc).lower():
            phrase = '"' + query.replace('"', "") + '"'
            params[0] = phrase
            try:
                columns, rows = guard.query_rows(sql, params)
            except sqlite3.Error as exc2:
                return {"error": "search_failed", "reason": str(exc2)}
            return _search_payload(query, corpus, columns, rows, limit, slug,
                                   requoted=phrase)
        return {"error": "search_failed", "reason": str(exc)}
    except sqlite3.Error as exc:
        return {"error": "search_failed", "reason": str(exc)}

    return _search_payload(query, corpus, columns, rows, limit, slug)


def _search_payload(query: str, corpus: str, columns: list[str], rows: list[tuple],
                    limit: int, slug: str | None, requoted: str | None = None) -> dict:
    truncated = len(rows) > limit
    rows = rows[:limit]
    results = [dict(zip(columns, [guard.coerce(v) for v in row])) for row in rows]

    hit_slugs = {r["city"] for r in results if r.get("city")}
    if slug:
        hit_slugs.add(slug)

    caveat_rows: list[dict] = []
    for s in sorted(hit_slugs):
        caveat_rows.extend(caveats.for_entity(s))

    payload = {
        "query": query,
        "corpus": corpus,
        "result_count": len(results),
        "truncated": truncated,
        "results": results,
        "caveats": caveat_rows[: config.MAX_CAVEATS],
        "caveat_count": len(caveat_rows),
        "note": (
            "Counts here are matching DOCUMENTS, one row per file — a meeting that "
            "mentions the term ten times counts once. Open `path` with read_document "
            "for full context before quoting."
        ),
    }
    if requoted:
        payload["requoted_as"] = requoted
        payload["requote_note"] = (
            "FTS5 rejected the raw query, so it was retried as an exact phrase."
        )
    if truncated:
        payload["truncation_note"] = f"more matches exist beyond the first {limit}"
    return payload


# --------------------------------------------------------------------------
# 3. read_document
# --------------------------------------------------------------------------

_TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".html", ".xml", ".yml", ".yaml", ""}


def _confine(path: str, tool: str) -> tuple[Path | None, dict | None]:
    """Resolve a caller-supplied path inside the repo.

    Returns ``(resolved, None)`` or ``(None, error_dict)``. Shared by
    read_document and grep_repo so the escape rules cannot drift apart — the
    check order matters and is asserted by verify_phase0.sh: an escaping path
    is `outside_repo` (403) whether or not it exists, so probing for files
    outside the repo cannot be distinguished from probing for absent ones.
    """
    if not (path or "").strip():
        return None, {"error": "empty_path", "reason": f"{tool} needs a path"}

    root = config.REPO_ROOT.resolve()
    candidate = Path(path.strip())
    if not candidate.is_absolute():
        candidate = root / candidate

    try:
        resolved = candidate.resolve()
    except OSError as exc:
        return None, {"error": "bad_path", "reason": str(exc)}

    # resolve() has already followed every symlink, so this also blocks a link
    # inside the repo that points outside it.
    if not resolved.is_relative_to(root):
        return None, {"error": "outside_repo",
                      "reason": f"{tool} is confined to the civic-data repository"}
    if not resolved.exists():
        return None, {"error": "not_found",
                      "reason": f"no file at {resolved.relative_to(root)}"}
    return resolved, None


def _entity_of(rel: str) -> str | None:
    """The entity a repo-relative path belongs to, by its first segment."""
    idx = caveats.index()
    first = rel.split("/", 1)[0]
    return next((s for s, e in idx.entities.items() if e["dir"] == first), None)


def read_document(path: str, offset: int = 0,
                  max_chars: int = config.DOC_MAX_CHARS) -> dict:
    """Open a primary text file, confined to the repo root."""
    resolved, error = _confine(path, "read_document")
    if error is not None:
        return error
    root = config.REPO_ROOT.resolve()

    if not resolved.is_file():
        return {"error": "not_a_file", "reason": "path is a directory"}
    if resolved.suffix.lower() not in _TEXT_SUFFIXES:
        return {"error": "not_text",
                "reason": f"{resolved.suffix} is not a readable text format; "
                          "use the document catalog's text_path instead"}

    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"error": "read_failed", "reason": str(exc)}

    rel = str(resolved.relative_to(root))
    offset = max(0, int(offset))
    max_chars = max(1, min(int(max_chars), config.DOC_MAX_CHARS))
    chunk = text[offset: offset + max_chars]
    end = offset + len(chunk)

    # The first path segment is the entity directory — attach that entity's
    # ceilings to the quote, the same way a query result gets them.
    slug = _entity_of(rel)

    return {
        "path": rel,
        "entity": slug,
        "entity_name": caveats.index().name_of(slug) if slug else None,
        "total_chars": len(text),
        "offset": offset,
        "chars_returned": len(chunk),
        "truncated": end < len(text),
        "next_offset": end if end < len(text) else None,
        "text": chunk,
        "caveats": caveats.for_entity(slug) if slug else [],
    }


# --------------------------------------------------------------------------
# 4. get_schema
# --------------------------------------------------------------------------

_SHADOW_RE = re.compile(r"_(data|idx|docsize|config|content)$")
_schema_cache: dict[str, Any] | None = None


def _schema_index() -> dict[str, Any]:
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    _, rows = guard.query_rows(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
    )
    objects = {}
    for kind, name, sql in rows:
        if _SHADOW_RE.search(name):
            continue          # FTS5 shadow tables are an implementation detail
        objects[name] = {"name": name, "kind": kind, "sql": sql}
    _schema_cache = objects
    return objects


def get_schema(tables: list[str] | str | None = None,
               with_counts: bool = False) -> dict:
    """DDL on demand, so the system prompt stays small."""
    objects = _schema_index()

    if isinstance(tables, str):
        tables = [t.strip() for t in tables.split(",") if t.strip()]

    if not tables:
        listing = []
        for name, obj in objects.items():
            entry = {"name": name, "kind": obj["kind"]}
            if with_counts:
                try:
                    _, rows = guard.query_rows(f'SELECT COUNT(*) FROM "{name}"')
                    entry["rows"] = rows[0][0]
                except sqlite3.Error:
                    entry["rows"] = None
            listing.append(entry)
        return {
            "objects": listing,
            "object_count": len(listing),
            "hint": "call get_schema with table names for full DDL",
        }

    out, unknown = [], []
    for name in tables:
        obj = objects.get(name) or objects.get(name.lower())
        if obj is None:
            unknown.append(name)
            continue
        entry = dict(obj)
        try:
            cols, _ = guard.query_rows(f'SELECT * FROM "{obj["name"]}" LIMIT 0')
            entry["columns"] = cols
        except sqlite3.Error:
            entry["columns"] = []
        if with_counts:
            try:
                _, rows = guard.query_rows(f'SELECT COUNT(*) FROM "{obj["name"]}"')
                entry["rows"] = rows[0][0]
            except sqlite3.Error:
                entry["rows"] = None
        out.append(entry)

    result: dict[str, Any] = {"objects": out}
    if unknown:
        result["unknown"] = unknown
        result["hint"] = "call get_schema with no arguments to list every table and view"
    return result


# --------------------------------------------------------------------------
# 5. list_coverage
# --------------------------------------------------------------------------

def list_coverage(entity: str | None = None) -> dict:
    """What exists, what is deferred by design, and where the floors are."""
    idx = caveats.index()
    slug = None
    if entity:
        slug = _resolve_slug(entity)
        if slug is None:
            return {"error": "unknown_entity", "reason": f"no entity matches {entity!r}",
                    "hint": "call resolve_entity first"}

    sql = ("SELECT city, dataset, motions, passed, outcome_unknown, "
           "first_date, last_date, caveats FROM v_coverage")
    params: list[Any] = []
    if slug:
        sql += " WHERE city = ?"
        params.append(slug)
    sql += " ORDER BY city, dataset"

    columns, rows = guard.query_rows(sql, params)
    coverage = [dict(zip(columns, [guard.coerce(v) for v in r])) for r in rows]

    payload: dict[str, Any] = {
        "entity": slug,
        "entity_name": idx.name_of(slug) if slug else None,
        "rows": coverage,
        "row_count": len(coverage),
        "note": (
            "A '(no vote layer)' or '(no motion_std layer)' row is an HONEST "
            "PROPERTY of that entity, not a gap to be filled: db-less counties and "
            "the MPOs were incorporated on their own terms, and ut_state's missing "
            "motion_std layer is an owner ruling."
        ),
    }
    if slug:
        entity_row = idx.entities[slug]
        payload["level"] = entity_row["level"]
        payload["has_vote_db"] = bool(entity_row["db_rel_path"])
        payload["caveats"] = caveats.for_entity(slug)
    return payload


# --------------------------------------------------------------------------
# 6. resolve_entity
# --------------------------------------------------------------------------

_STOPWORDS = {"city", "town", "of", "the", "county", "utah", "ut"}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _normalize(text).split() if t and t not in _STOPWORDS}


def resolve_entity(name: str) -> dict:
    """Turn a journalist's phrasing into entity slugs, ambiguity included.

    "Salt Lake" has to come back as BOTH the city and the county — silently
    picking one is the most likely wrong answer in the whole system.
    """
    idx = caveats.index()
    raw = (name or "").strip()
    if not raw:
        return {"error": "empty_name", "reason": "resolve_entity needs a name"}

    norm = _normalize(raw)
    squashed = norm.replace(" ", "_")
    query_tokens = _tokens(raw)

    scored: list[tuple[int, str]] = []
    for slug, entity in idx.entities.items():
        entity_name = entity["name"] or ""
        norm_name = _normalize(entity_name)
        score = 0
        if raw == slug or squashed == slug:
            score = 100
        elif norm == norm_name:
            score = 100
        elif norm and (norm_name.startswith(norm) or slug.startswith(squashed)):
            score = 80
        elif norm and (norm in norm_name or squashed in slug):
            score = 70
        else:
            overlap = query_tokens & _tokens(entity_name)
            if overlap and overlap == query_tokens:
                score = 60
            elif overlap:
                score = 40
        if score:
            scored.append((score, slug))

    if not scored:
        return {
            "error": "no_match",
            "reason": f"no registered entity matches {raw!r}",
            "hint": "the registry holds 31 cities/towns, 8 counties, 2 MPOs and the State of Utah",
        }

    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    top = scored[0][0]

    _, rel_rows = guard.query_rows(
        "SELECT entity_a, relation, entity_b, note FROM entity_relationship"
    )

    candidates = []
    for score, slug in scored:
        entity = idx.entities[slug]
        within = [b for a, r, b, _ in rel_rows if a == slug and r == "within"]
        member_of = [b for a, r, b, _ in rel_rows if a == slug and r == "member_of"]
        contains = [a for a, r, b, _ in rel_rows if b == slug and r == "within"]
        note = next((n for a, r, b, n in rel_rows
                     if a == slug and r == "within" and n), "")
        candidates.append({
            "slug": slug,
            "name": entity["name"],
            "level": entity["level"],
            "directory": entity["dir"],
            "has_vote_db": bool(entity["db_rel_path"]),
            "match_score": score,
            "within": within,
            "member_of": member_of,
            "contains_count": len(contains),
            "relationship_note": note,
            "caveat_count": len(caveats.for_entity(slug)),
        })

    strong = [c for c in candidates if c["match_score"] >= 70]
    ambiguous = len(strong) > 1 and len([c for c in strong if c["match_score"] == top]) != 1

    payload: dict[str, Any] = {
        "query": raw,
        "candidates": candidates[:8],
        "ambiguous": ambiguous or len(strong) > 1,
        "best": candidates[0]["slug"] if not ambiguous else None,
    }

    levels = {c["level"] for c in strong}
    if {"city", "county"} <= levels:
        payload["disambiguation"] = (
            f"{raw!r} matches both a city and a county — they are separate "
            "governments with separate records. Ask which one, or say which you used."
        )
    multi_county = [c for c in strong if len(c["within"]) > 1]
    if multi_county:
        names = ", ".join(c["slug"] for c in multi_county)
        payload["straddle_note"] = (
            f"{names} sits in more than one county; elections and county-level "
            "records may come from only the primary one."
        )
    no_db = [c for c in strong if not c["has_vote_db"]]
    if no_db:
        payload["no_vote_layer"] = [c["slug"] for c in no_db]
        payload["no_vote_layer_note"] = (
            "These entities are federated but db-less BY DESIGN — they carry "
            "elections/text/campaign-finance layers, not a vote spine. Absence of "
            "votes is not a gap. Use list_coverage to see what they do hold."
        )
    return payload


# --------------------------------------------------------------------------
# 7. grep_repo
# --------------------------------------------------------------------------

_RG_CACHE: str | None | bool = False


def ripgrep_path() -> str | None:
    """A real `rg` binary on PATH, or None. Cached for the process.

    shutil.which deliberately cannot see a shell function, which is what `rg`
    often is on a developer machine — so this returns None there and the
    stdlib engine runs, rather than the tool believing in an rg that a
    subprocess could never invoke.
    """
    global _RG_CACHE
    if _RG_CACHE is False:
        _RG_CACHE = shutil.which("rg")
    return _RG_CACHE


def _grep_scope(root: Path, glob: str | None) -> Iterator[Path]:
    """Walk the committed text layer under `root`, honouring the exclusions."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in config.GREP_EXCLUDE_DIRS]
        for name in filenames:
            if Path(name).suffix.lower() not in config.GREP_SUFFIXES:
                continue
            if glob and not fnmatch.fnmatch(name, glob):
                continue
            yield Path(dirpath) / name


def grep_repo(pattern: str, path: str | None = None, glob: str | None = None,
              regex: bool = False, ignore_case: bool = True,
              limit: int = config.GREP_DEFAULT_LIMIT) -> dict:
    """Search the repo's committed TEXT for a pattern, with the file and line.

    This is the layer FTS does not reach. `fts_minutes` and its siblings index
    what governments published; this indexes nothing and reads what the
    *repository* says — CLAUDE.md, TODO.md, LEADS.md, COVERAGE.md, the
    per-dataset index.csv provenance manifests. Narrow with `path` to one
    entity directory and it returns in well under a second.
    """
    started = time.monotonic()
    pattern = (pattern or "").strip()
    if not pattern:
        return {"error": "empty_query", "reason": "grep_repo needs a pattern"}
    if len(pattern) > config.GREP_MAX_PATTERN_CHARS:
        return {"error": "rejected",
                "reason": f"pattern exceeds {config.GREP_MAX_PATTERN_CHARS} characters"}

    root_str = path if (path or "").strip() else "."
    resolved, error = _confine(root_str, "grep_repo")
    if error is not None:
        return error

    repo = config.REPO_ROOT.resolve()
    limit = max(1, min(int(limit), config.GREP_MAX_LIMIT))
    deadline = started + config.GREP_DEADLINE_MS / 1000.0

    if regex:
        try:
            re.compile(pattern)
        except re.error as exc:
            return {"error": "rejected", "reason": f"not a valid regular expression: {exc}"}

    engine = "ripgrep" if ripgrep_path() else "stdlib"
    runner = _grep_ripgrep if engine == "ripgrep" else _grep_stdlib
    try:
        matches, stopped, scanned = runner(
            pattern, resolved, repo, glob, regex, ignore_case, limit, deadline)
    except OSError as exc:
        return {"error": "search_failed", "reason": f"{type(exc).__name__}: {exc}"}

    # Byte ceiling, applied after the engines so both obey the same one.
    budget = config.GREP_MAX_RESULT_BYTES
    kept: list[dict] = []
    for match in matches:
        budget -= len(match["path"]) + len(match["line"]) + 40
        if budget < 0:
            stopped = stopped or "bytes"
            break
        kept.append(match)

    slugs = {m["entity"] for m in kept if m["entity"]}
    attached: list[dict] = []
    for slug in sorted(slugs):
        attached.extend(caveats.for_entity(slug))

    files = sorted({m["path"] for m in kept})
    payload = {
        "pattern": pattern,
        "mode": "regex" if regex else "literal",
        "ignore_case": bool(ignore_case),
        "engine": engine,
        "path": str(resolved.relative_to(repo)) or ".",
        "glob": glob or None,
        "match_count": len(kept),
        "files_matched": len(files),
        "files_scanned": scanned,
        "matches": kept,
        "truncated": bool(stopped),
        "truncation_reason": stopped,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "caveats": attached[: config.MAX_CAVEATS],
        "entities": sorted(slugs),
    }
    if stopped == "deadline":
        payload["hint"] = (
            f"the sweep stopped at {config.GREP_DEADLINE_MS / 1000:.0f}s — this is a "
            "PARTIAL result, and absence here is not evidence of absence. Narrow it "
            "with path= (one entity directory) or glob= and run it again."
        )
    elif stopped == "limit":
        payload["hint"] = (f"more matches exist beyond limit={limit}; raise it "
                           f"(max {config.GREP_MAX_LIMIT}) or narrow with path=/glob=")
    return payload


def _record(rel: str, line_no: int, text: str) -> dict:
    text = text.rstrip("\n\r")
    if len(text) > config.GREP_MAX_LINE_CHARS:
        text = text[: config.GREP_MAX_LINE_CHARS] + " …[line truncated]"
    return {"path": rel, "entity": _entity_of(rel), "line_no": line_no, "line": text}


def _grep_ripgrep(pattern, root, repo, glob, regex, ignore_case, limit, deadline):
    """Delegate to ripgrep. argv is a list — no shell, ever."""
    # --with-filename is NOT redundant: ripgrep omits the path when it is
    # searching a single explicit file, which silently broke the `path=<file>`
    # form — the parser saw "line:content" where it expected "path\0line:content"
    # and discarded every match. Caught by engine-parity testing, not by any
    # error, because the tool returned a confident zero.
    argv = [ripgrep_path(), "--line-number", "--no-heading", "--with-filename",
            "--color", "never", "--no-messages", "--null",
            "--max-count", str(config.GREP_MAX_PER_FILE)]
    if not regex:
        argv.append("--fixed-strings")
    if ignore_case:
        argv.append("--ignore-case")
    # Globs apply to an explicitly named file too, so a caller who points
    # `path` straight at one would otherwise get silence when its suffix is not
    # in the allow-list. An explicit file is already the caller's choice.
    if not root.is_file():
        for directory in sorted(config.GREP_EXCLUDE_DIRS):
            argv += ["--glob", f"!{directory}/**", "--glob", f"!**/{directory}/**"]
        argv += ["--glob", glob] if glob else [
            arg for suffix in sorted(config.GREP_SUFFIXES) for arg in ("--glob", f"*{suffix}")]
    argv += ["--regexp", pattern, "--", str(root)]

    timeout = max(0.1, deadline - time.monotonic())
    stopped = None
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              errors="replace", timeout=timeout, shell=False)
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else \
              (exc.stdout or b"").decode("utf-8", "replace")
        stopped = "deadline"

    matches: list[dict] = []
    for row in out.splitlines():
        if len(matches) >= limit:
            stopped = stopped or "limit"
            break
        file_part, _, rest = row.partition("\0")
        number, _, text = rest.partition(":")
        if not number.isdigit():
            continue
        try:
            rel = str(Path(file_part).resolve().relative_to(repo))
        except (ValueError, OSError):
            continue
        matches.append(_record(rel, int(number), text))
    return matches, stopped, None


def _grep_stdlib(pattern, root, repo, glob, regex, ignore_case, limit, deadline):
    """The no-ripgrep fallback. Correct, slower, and honest about stopping."""
    needle = pattern.lower() if ignore_case else pattern
    rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0) if regex else None

    matches: list[dict] = []
    stopped = None
    scanned = 0
    targets: Iterable[Path] = [root] if root.is_file() else _grep_scope(root, glob)

    for target in targets:
        if len(matches) >= limit:
            stopped = "limit"
            break
        if time.monotonic() > deadline:
            stopped = "deadline"
            break
        scanned += 1
        try:
            rel = str(target.resolve().relative_to(repo))
        except (ValueError, OSError):
            continue
        # Streamed, not slurped. A whole-buffer literal prefilter and an 8-way
        # thread pool were both measured here and neither earned its keep (1%
        # and 22%): the sweep is I/O-bound on ~2 GB of text, so the honest fix
        # for repo-wide work is ripgrep, not a cleverer fallback.
        in_file = 0
        try:
            with target.open("r", encoding="utf-8", errors="replace") as handle:
                for line_no, line in enumerate(handle, 1):
                    # Bound the slice a regex may examine: catastrophic
                    # backtracking is a property of the input length, and the
                    # deadline below cannot interrupt a single match attempt.
                    probe = line[: config.GREP_MAX_LINE_CHARS * 4]
                    hit = rx.search(probe) if rx else (
                        needle in (probe.lower() if ignore_case else probe))
                    if not hit:
                        continue
                    matches.append(_record(rel, line_no, line))
                    in_file += 1
                    if in_file >= config.GREP_MAX_PER_FILE or len(matches) >= limit:
                        break
                    if not line_no % 2000 and time.monotonic() > deadline:
                        stopped = "deadline"
                        break
        except OSError:
            continue
    return matches, stopped, scanned


# --------------------------------------------------------------------------
# health
# --------------------------------------------------------------------------

def health() -> dict:
    """Live facts about the database this layer is serving. Nothing hardcoded."""
    _, rows = guard.query_rows(
        "SELECT key, value FROM build_info WHERE key IN "
        "('built_at','script','note')"
    )
    info = dict(rows)
    _, counts = guard.query_rows(
        "SELECT (SELECT COUNT(*) FROM entity), (SELECT COUNT(*) FROM motion), "
        "(SELECT COUNT(*) FROM vote), (SELECT COUNT(*) FROM caveat), "
        "(SELECT COUNT(*) FROM fts_minutes)"
    )
    entities, motions, votes, caveat_rows, minutes_docs = counts[0]
    return {
        "ok": True,
        "database": str(config.DB_PATH),
        "database_mode": "read-only (file:...?mode=ro)",
        "db_bytes": config.DB_PATH.stat().st_size if config.DB_PATH.exists() else None,
        "built_at": info.get("built_at"),
        "builder": info.get("script"),
        "entities": entities,
        "motions": motions,
        "votes": votes,
        "caveat_rows": caveat_rows,
        "fts_minutes_docs": minutes_docs,
        "corpora": list(CORPORA),
        "row_limit_default": config.DEFAULT_ROW_LIMIT,
        "row_limit_max": config.MAX_ROW_LIMIT,
        "query_timeout_ms": config.QUERY_TIMEOUT_MS,
    }
