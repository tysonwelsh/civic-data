"""The agent loop — Claude Opus 5 over the Phase 0 tool surface.

A manual tool-use loop rather than the SDK's tool runner, because the browser
needs Server-Sent Events with our own event vocabulary and we want per-turn
control of spend (CHAT_PLAN.md §3).

Everything the browser needs to render the answer *and* audit it comes out of
:func:`run` as a stream of dicts: text deltas, tool calls, tool results with
their caveats, and a final usage/cost record.

API decisions, verified against the current reference:

* `claude-opus-5`, adaptive thinking (on by default — do NOT pass
  `budget_tokens`, which is rejected with a 400).
* No `temperature` / `top_p` / `top_k` — also rejected with a 400.
* `output_config.effort` controls depth; `medium` to start, then sweep.
* `cache_control` on the last system block. The prompt is byte-stable, so the
  second request onward should report `cache_read_input_tokens > 0`.
* `stop_reason == "refusal"` is checked before reading content, and
  `fallbacks: "default"` is opted into so a refused request is re-run
  server-side rather than simply stopping.
"""

from __future__ import annotations

import inspect
import json
import time
from typing import Any, Iterator

from . import config, context, tools


# --------------------------------------------------------------------------
# model configuration
# --------------------------------------------------------------------------

MODEL = "claude-opus-5"
EFFORT = "medium"

# Thinking and visible text share this cap. Opus 5 thinks by default, so the
# plan's original 16000 risks truncating an answer mid-sentence once adaptive
# thinking takes its share — 32000 leaves room for both without inviting an
# essay. Tune with the sweep.
MAX_TOKENS = 32000

# A journalist question should resolve in a handful of tool calls. The cap is a
# spend guard, not a capability limit; hitting it is reported, never hidden.
MAX_TURNS = 12

# $ per million tokens (claude-opus-5). Cache reads bill at ~0.1x input,
# cache writes at ~1.25x.
PRICE_IN = 5.00
PRICE_OUT = 25.00

BETAS = ["server-side-fallback-2026-07-01"]


# --------------------------------------------------------------------------
# tool schemas
# --------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "run_sql",
        "description": (
            "Run one read-only SELECT (or WITH ... SELECT) against gov.db and get "
            "back the rows PLUS every caveat row that governs how they may be read. "
            "The caveats are attached by the executor, not chosen by you — read "
            "them. Results are capped (default 200 rows); `truncated` tells you when "
            "the answer is partial. Prefer the caveat-aware views v_contested_all, "
            "v_member_record_all, v_landuse_outcomes and v_coverage over raw tables."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "One SELECT or WITH statement."},
                "limit": {
                    "type": "integer",
                    "description": f"Row cap, 1–{config.MAX_ROW_LIMIT}. Default {config.DEFAULT_ROW_LIMIT}.",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "search_text",
        "description": (
            "Full-text search (FTS5) across the corpora, returning snippet passages "
            "and repo-relative paths you can open with read_document. Counts are "
            "matching DOCUMENTS, one row per file — a meeting that mentions a term "
            "ten times counts once. Use FTS5 syntax: \"exact phrase\" in double "
            "quotes, OR, NEAR."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "FTS5 query."},
                "corpus": {
                    "type": "string",
                    "enum": list(tools.CORPORA),
                    "description": (
                        "minutes = meeting minutes, statutes and advisory opinions; "
                        "packets = agenda packets and staff reports; ordinances = "
                        "adopted ordinance text; comments = public comments; "
                        "motions = motion text."
                    ),
                },
                "entity": {"type": "string", "description": "Slug or name. Omit for all."},
                "dataset": {"type": "string", "description": "minutes/packets corpora only."},
                "date_from": {"type": "string", "description": "YYYY-MM-DD inclusive."},
                "date_to": {"type": "string", "description": "YYYY-MM-DD inclusive."},
                "limit": {"type": "integer", "description": f"Max {config.SEARCH_MAX_LIMIT}."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_document",
        "description": (
            "Open a primary text file — minutes, a statute, an advisory opinion, a "
            "staff report — so you can quote the source rather than paraphrase a "
            "database row. Use the `path` returned by search_text, or a text_path "
            "from the document catalog. Confined to the repository. Long files "
            "page: pass the returned next_offset to continue."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repo-relative path."},
                "offset": {"type": "integer", "description": "Character offset. Default 0."},
                "max_chars": {"type": "integer", "description": f"Max {config.DOC_MAX_CHARS}."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_schema",
        "description": (
            "DDL and column lists for tables and views in gov.db. Call with no "
            "arguments to list every object; call with names for full CREATE "
            "statements. Use this rather than guessing a column name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Table or view names. Omit to list everything.",
                },
                "with_counts": {"type": "boolean", "description": "Include row counts."},
            },
        },
    },
    {
        "name": "list_coverage",
        "description": (
            "What an entity actually holds: datasets, motion counts, date floors and "
            "ceilings, and its caveat rows. Use it when the question is about what "
            "exists, or when a query returns nothing and you need to know whether "
            "that is a true zero or an absent layer. A '(no vote layer)' row is an "
            "honest property of a db-less entity, not a gap."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Slug or name. Omit for all."},
            },
        },
    },
    {
        "name": "resolve_entity",
        "description": (
            "Turn a place name into entity slugs, ambiguity preserved. Call this "
            "FIRST whenever the question names a place that could be more than one "
            "government — 'Salt Lake' is both a city and a county. Also reports "
            "which county an entity sits in, whether it straddles two, and whether "
            "it has a vote layer at all."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Place name as the user said it."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "grep_repo",
        "description": (
            "Search the repository's own TEXT files for a pattern and get back "
            "file, line number and the matching line. This reaches what search_text "
            "CANNOT: the documentation and provenance layer — CLAUDE.md, TODO.md, "
            "LEADS.md, COVERAGE.md, AVAILABILITY.md, each dataset's index.csv "
            "manifest, the build scripts. Use search_text for what governments SAID "
            "(minutes, packets, ordinances, comments); use grep_repo for what the "
            "REPO says about its own coverage, methods and known gaps. Always pass "
            "path= (an entity directory such as 'nephi_city_council') when you know "
            "which entity you mean — a repo-wide sweep can hit its deadline and "
            "return a PARTIAL result, in which case absence is not evidence of "
            "absence and `truncation_reason` will say so."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string",
                            "description": "Literal text by default; a regular expression "
                                           "when regex=true."},
                "path": {"type": "string",
                         "description": "Repo-relative directory or file to confine the "
                                        "search to, e.g. 'nephi_city_council'. Defaults "
                                        "to the whole repo."},
                "glob": {"type": "string",
                         "description": "Filename glob, e.g. '*.csv' or 'CLAUDE.md'."},
                "regex": {"type": "boolean", "description": "Treat pattern as a regex. Default false."},
                "ignore_case": {"type": "boolean", "description": "Default true."},
                "limit": {"type": "integer",
                          "description": f"Max matching lines, 1–{config.GREP_MAX_LIMIT}. "
                                         f"Default {config.GREP_DEFAULT_LIMIT}."},
            },
            "required": ["pattern"],
        },
    },
]

DISPATCH = {
    "run_sql": lambda a: tools.run_sql(a.get("sql", ""), limit=a.get("limit")),
    "search_text": lambda a: tools.search_text(
        a.get("query", ""), corpus=a.get("corpus", "minutes"), entity=a.get("entity"),
        dataset=a.get("dataset"), date_from=a.get("date_from"), date_to=a.get("date_to"),
        limit=a.get("limit", config.SEARCH_DEFAULT_LIMIT)),
    "read_document": lambda a: tools.read_document(
        a.get("path", ""), offset=a.get("offset", 0),
        max_chars=a.get("max_chars", config.DOC_MAX_CHARS)),
    "get_schema": lambda a: tools.get_schema(a.get("tables"), with_counts=a.get("with_counts", False)),
    "list_coverage": lambda a: tools.list_coverage(a.get("entity")),
    "resolve_entity": lambda a: tools.resolve_entity(a.get("name", "")),
    "grep_repo": lambda a: tools.grep_repo(
        a.get("pattern", ""), path=a.get("path"), glob=a.get("glob"),
        regex=a.get("regex", False), ignore_case=a.get("ignore_case", True),
        limit=a.get("limit", config.GREP_DEFAULT_LIMIT)),
}


# --------------------------------------------------------------------------
# client
# --------------------------------------------------------------------------

class ChatUnavailable(Exception):
    """No usable client — missing SDK, missing credentials, or an SDK too old."""


def _import_sdk():
    try:
        import anthropic
    except ImportError as exc:
        raise ChatUnavailable(
            "The `anthropic` package is not installed. Run: pip install -U anthropic"
        ) from exc
    return anthropic


def sdk_capabilities() -> dict:
    """What the installed SDK can express natively vs. what needs extra_body.

    The repo pins `anthropic>=0.51.0` for the SLC extraction scripts, and 0.51
    predates `output_config` and `fallbacks` entirely. Rather than fail, we pass
    those through `extra_body` when the installed SDK has no typed parameter for
    them — the wire format is identical either way.
    """
    try:
        anthropic = _import_sdk()
    except ChatUnavailable:
        return {"installed": False}
    try:
        params = set(inspect.signature(anthropic.Anthropic().beta.messages.create).parameters)
    except Exception:
        params = set()
    return {
        "installed": True,
        "version": getattr(anthropic, "__version__", "unknown"),
        "native_output_config": "output_config" in params,
        "native_fallbacks": "fallbacks" in params,
        "native_betas": "betas" in params,
    }


NO_CREDENTIAL_HELP = (
    "No Anthropic credentials found. Put ANTHROPIC_API_KEY=... in "
    "interface_prototype/.env (untracked, the repo convention), or export it, "
    "or run `ant auth login` to store a profile the SDK picks up automatically. "
    "Phase 0 (the console at /console.html) needs no credentials and keeps working."
)


def credentials_status() -> dict:
    """Is a credential actually resolvable?

    Constructing the client proves nothing — the SDK defers auth resolution to
    request time, so a bare `Anthropic()` succeeds with no key at all and the
    failure only surfaces once you have already started streaming. Probe the
    resolution order the SDKs document: env var, auth token, then an
    `ant auth login` profile on disk.
    """
    import os

    if os.environ.get("ANTHROPIC_API_KEY"):
        # Distinguish a shell export from the untracked .env config.load_env()
        # read, so "where is this key coming from" is answerable without
        # printing the key.
        via_file = "ANTHROPIC_API_KEY" in config.LOADED_ENV_KEYS
        return {"ready": True,
                "source": "interface_prototype/.env" if via_file else "ANTHROPIC_API_KEY"}
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return {"ready": True, "source": "ANTHROPIC_AUTH_TOKEN"}

    config_dir = os.environ.get("ANTHROPIC_CONFIG_DIR")
    from pathlib import Path
    base = Path(config_dir) if config_dir else Path.home() / ".config" / "anthropic"
    creds = base / "credentials"
    if creds.is_dir() and any(creds.glob("*.json")):
        profile = os.environ.get("ANTHROPIC_PROFILE", "default")
        return {"ready": True, "source": f"ant auth profile ({profile})"}

    # The SDK may still resolve something we do not know how to look for; if the
    # constructed client carries a key, believe it over our own probe.
    try:
        client = _import_sdk().Anthropic()
        if getattr(client, "api_key", None) or getattr(client, "auth_token", None):
            return {"ready": True, "source": "sdk-resolved"}
    except Exception:
        pass

    return {"ready": False, "source": None, "reason": NO_CREDENTIAL_HELP}


def _client():
    anthropic = _import_sdk()
    status = credentials_status()
    if not status["ready"]:
        raise ChatUnavailable(status["reason"])
    try:
        # A bare constructor resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or
        # an `ant auth login` profile — do not require the env var specifically.
        return anthropic.Anthropic()
    except Exception as exc:
        raise ChatUnavailable(f"Could not construct the Anthropic client: {exc}") from exc


def _request_kwargs(caps: dict) -> tuple[dict, dict]:
    """Split the newer parameters between native kwargs and extra_body."""
    native: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    (native if caps.get("native_output_config") else extra)["output_config"] = {"effort": EFFORT}
    (native if caps.get("native_fallbacks") else extra)["fallbacks"] = "default"
    return native, extra


# --------------------------------------------------------------------------
# result shaping for the browser
# --------------------------------------------------------------------------

def _summarize(name: str, result: dict) -> dict:
    """A compact, renderable description of what a tool call produced."""
    if "error" in result:
        return {"kind": "error", "error": result["error"], "reason": result.get("reason", "")}
    if name == "run_sql":
        return {
            "kind": "sql", "sql": result.get("sql_submitted"),
            "columns": result.get("columns", []), "rows": result.get("rows", [])[:50],
            "row_count": result.get("row_count", 0), "truncated": result.get("truncated"),
            "elapsed_ms": result.get("elapsed_ms"),
        }
    if name == "search_text":
        return {
            "kind": "search", "query": result.get("query"), "corpus": result.get("corpus"),
            "result_count": result.get("result_count", 0),
            "results": [
                {k: r.get(k) for k in ("city", "entity_name", "date", "title", "path", "passage")}
                for r in result.get("results", [])[:12]
            ],
        }
    if name == "read_document":
        return {
            "kind": "document", "path": result.get("path"),
            "entity_name": result.get("entity_name"),
            "chars_returned": result.get("chars_returned"),
            "total_chars": result.get("total_chars"),
        }
    if name == "resolve_entity":
        return {
            "kind": "entity", "query": result.get("query"),
            "ambiguous": result.get("ambiguous"),
            "candidates": [
                {k: c.get(k) for k in ("slug", "name", "level", "has_vote_db")}
                for c in result.get("candidates", [])[:6]
            ],
        }
    if name == "list_coverage":
        return {
            "kind": "coverage", "entity": result.get("entity"),
            "row_count": result.get("row_count", 0), "rows": result.get("rows", [])[:30],
        }
    if name == "get_schema":
        return {
            "kind": "schema",
            "names": [o.get("name") for o in result.get("objects", [])][:60],
        }
    if name == "grep_repo":
        return {
            "kind": "grep", "pattern": result.get("pattern"),
            "path": result.get("path"), "engine": result.get("engine"),
            "match_count": result.get("match_count", 0),
            "files_matched": result.get("files_matched", 0),
            # A partial sweep must reach the reader as partial: the evidence
            # panel is the audit trail, and a truncated grep that renders like
            # a complete one is exactly the silent-absence failure this layer
            # exists to prevent.
            "truncated": result.get("truncated"),
            "truncation_reason": result.get("truncation_reason"),
            "matches": [
                {k: m.get(k) for k in ("path", "entity", "line_no", "line")}
                for m in result.get("matches", [])[:12]
            ],
        }
    return {"kind": name}


def _tool_result_text(result: dict) -> str:
    """What the model sees. Trimmed so a wide result set can't blow the window."""
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) > 120_000:
        text = text[:120_000] + '\n… [tool result truncated by the harness]'
    return text


def _cost(usage_total: dict) -> float:
    read = usage_total.get("cache_read_input_tokens", 0)
    write = usage_total.get("cache_creation_input_tokens", 0)
    plain = usage_total.get("input_tokens", 0)
    out = usage_total.get("output_tokens", 0)
    return (
        plain * PRICE_IN / 1e6
        + write * PRICE_IN * 1.25 / 1e6
        + read * PRICE_IN * 0.10 / 1e6
        + out * PRICE_OUT / 1e6
    )


# --------------------------------------------------------------------------
# the loop
# --------------------------------------------------------------------------

def run(question: str, history: list[dict] | None = None,
        log: bool = True) -> Iterator[dict]:
    """Answer one question, yielding events for the browser.

    Event types: ``status``, ``text``, ``tool_use``, ``tool_result``,
    ``refusal``, ``error``, ``done``.

    ``log=False`` suppresses the logs/chat.jsonl record — the same switch
    guard.run_query carries, and for the same reason: a run driven by a stub
    model must not write a fabricated cost into the file the spend ceiling is
    sized from. Only the gates pass False.
    """
    caps = sdk_capabilities()
    try:
        client = _client()
    except ChatUnavailable as exc:
        yield {"type": "error", "message": str(exc), "fatal": True}
        return

    native, extra = _request_kwargs(caps)
    system = [{
        "type": "text",
        "text": context.system_prompt(),
        "cache_control": {"type": "ephemeral"},
    }]

    messages: list[dict] = list(history or [])
    messages.append({"role": "user", "content": question})

    totals = {"input_tokens": 0, "output_tokens": 0,
              "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    started = time.monotonic()
    turns = 0
    tool_calls: list[str] = []
    stop_reason: str | None = None

    while True:
        turns += 1
        if turns > MAX_TURNS:
            stop_reason = "max_turns"
            yield {"type": "error", "fatal": False, "message": (
                f"Stopped after {MAX_TURNS} tool-use rounds — a spend guard, not a "
                "limit of the data. The partial answer above stands; ask a narrower "
                "question to go further."
            )}
            break

        yield {"type": "status", "status": "thinking", "turn": turns}

        try:
            with client.beta.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                tools=TOOL_SCHEMAS,
                messages=messages,
                betas=BETAS,
                extra_body=extra or None,
                **native,
            ) as stream:
                for event in stream:
                    etype = getattr(event, "type", None)
                    if etype == "content_block_start":
                        block = getattr(event, "content_block", None)
                        btype = getattr(block, "type", None)
                        if btype == "thinking":
                            yield {"type": "status", "status": "reasoning"}
                        elif btype == "tool_use":
                            yield {"type": "status", "status": "tool",
                                   "name": getattr(block, "name", "")}
                    elif etype == "content_block_delta":
                        delta = getattr(event, "delta", None)
                        if getattr(delta, "type", None) == "text_delta":
                            yield {"type": "text", "text": delta.text}
                message = stream.get_final_message()
        except Exception as exc:
            yield {"type": "error", "fatal": True,
                   "message": f"{type(exc).__name__}: {exc}"}
            return

        # Refusals arrive as a successful response — check before reading content.
        if getattr(message, "stop_reason", None) == "refusal":
            stop_reason = "refusal"
            details = getattr(message, "stop_details", None)
            yield {"type": "refusal",
                   "category": getattr(details, "category", None),
                   "message": "The request was declined by the model's safeguards."}
            break

        usage = getattr(message, "usage", None)
        if usage is not None:
            for key in totals:
                totals[key] += getattr(usage, key, 0) or 0

        content = list(getattr(message, "content", []) or [])
        messages.append({"role": "assistant", "content": content})

        tool_uses = [b for b in content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses:
            break

        results_block = []
        for block in tool_uses:
            name = getattr(block, "name", "")
            args = dict(getattr(block, "input", {}) or {})
            tool_calls.append(name)
            yield {"type": "tool_use", "name": name, "input": args}

            fn = DISPATCH.get(name)
            if fn is None:
                result = {"error": "unknown_tool", "reason": f"no tool named {name!r}"}
            else:
                try:
                    result = fn(args)
                except Exception as exc:                 # a tool must never kill the turn
                    result = {"error": "tool_failed",
                              "reason": f"{type(exc).__name__}: {exc}"}

            yield {
                "type": "tool_result",
                "name": name,
                "summary": _summarize(name, result),
                "caveats": result.get("caveats", []),
                "caveat_count": result.get("caveat_count", 0),
                "notes": result.get("notes", []),
            }
            results_block.append({
                "type": "tool_result",
                "tool_use_id": getattr(block, "id", ""),
                "content": _tool_result_text(result),
                "is_error": "error" in result,
            })

        messages.append({"role": "user", "content": results_block})

    done = {
        "type": "done",
        "turns": turns,
        "elapsed_s": round(time.monotonic() - started, 1),
        "usage": totals,
        "cost_usd": round(_cost(totals), 4),
        "cache_hit": totals["cache_read_input_tokens"] > 0,
        "model": MODEL,
        "effort": EFFORT,
    }
    if log:
        log_question(question, done, tool_calls, stop=stop_reason)
    yield done


def log_question(question: str, done: dict, tool_calls: list[str],
                 stop: str | None = None) -> None:
    """Append one line to logs/chat.jsonl. Never raises into the stream."""
    counts: dict[str, int] = {}
    for name in tool_calls:
        counts[name] = counts.get(name, 0) + 1
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "question": question,
        "model": done.get("model"),
        "effort": done.get("effort"),
        "turns": done.get("turns"),
        "elapsed_s": done.get("elapsed_s"),
        "cost_usd": done.get("cost_usd"),
        "usage": done.get("usage"),
        "cache_hit": done.get("cache_hit"),
        "tools": counts,
        "tool_calls": len(tool_calls),
        "stop": stop,
    }
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with config.CHAT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass  # logging must never break an answer
