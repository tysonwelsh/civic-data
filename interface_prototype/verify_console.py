#!/usr/bin/env python3
"""Contract check between console.html and the Phase 0 API.

The page reads specific fields off each endpoint's JSON. A rename on the server
side would leave the page rendering "undefined" with no error anywhere — the
kind of break that is invisible until someone opens it. This asserts every
field the JavaScript actually touches, against a running server.

    python3 interface_prototype/server.py &
    python3 interface_prototype/verify_console.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8787"
PAGE = Path(__file__).resolve().parent / "console.html"

PASS, FAIL = 0, 0


def call(path: str, params: dict | None = None, body: dict | None = None):
    url = BASE + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode({k: v for k, v in params.items() if v not in (None, "")})
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data,
        headers={"content-type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read()), exc.code


def check(label: str, payload, fields: list[str], where=""):
    """Assert every dotted field resolves to something other than missing."""
    global PASS, FAIL
    missing = []
    for field in fields:
        node = payload
        for part in field.split("."):
            if part == "[]":
                if not isinstance(node, list) or not node:
                    node = KeyError
                    break
                node = node[0]
            elif isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = KeyError
                break
        if node is KeyError:
            missing.append(field)
    if missing:
        FAIL += 1
        print(f"  \033[31mFAIL\033[0m  {label:<44} missing: {', '.join(missing)}")
    else:
        PASS += 1
        print(f"  \033[32mPASS\033[0m  {label:<44} {where}")


print(f"\nconsole.html ↔ API contract — {BASE}\n")

# --- what the page reads at boot -----------------------------------------
d, _ = call("/api/health")
check("boot: /api/health facts row", d, [
    "built_at", "db_bytes", "query_timeout_ms", "entities", "motions", "votes",
    "fts_minutes_docs", "caveat_rows", "row_limit_default", "row_limit_max"])

# --- runQuery -------------------------------------------------------------
d, _ = call("/api/query", body={"sql": "SELECT COUNT(*) AS m FROM motion WHERE city='nephi'"})
check("runQuery: result + caveat fields", d, [
    "sql_executed", "row_count", "elapsed_ms", "truncated", "truncation_reason",
    "columns", "rows", "notes", "caveat_count", "caveats_truncated", "caveats_omitted",
    "caveats.[].code", "caveats.[].entity", "caveats.[].entity_name", "caveats.[].caveat"],
    f"{d['caveat_count']} caveats render")
d, st = call("/api/query", body={"sql": "DROP TABLE motion"})
check("runQuery: rejection card fields", d, ["error", "reason", "detail"], f"HTTP {st}")

d, _ = call("/api/query", body={"sql": "SELECT city, SUM(stated_total_contributions) "
                                       "FROM cf_filing GROUP BY city"})
check("runQuery: notes list is populated", d, ["notes.[]"], f"{len(d['notes'])} note(s)")

# --- runSearch ------------------------------------------------------------
d, _ = call("/api/search", {"q": '"accessory dwelling"', "limit": 3})
check("runSearch: hit fields", d, [
    "result_count", "truncated", "note", "caveat_count",
    "results.[].city", "results.[].entity_name", "results.[].date",
    "results.[].dataset", "results.[].title", "results.[].passage", "results.[].path"])
marks = re.search(r">>.*?<<", d["results"][0]["passage"] or "")
check("runSearch: passage carries >> << marks", {"m": bool(marks)},
      ["m"] if marks else ["missing_marks"])
for corpus in ("packets", "ordinances", "comments", "motions"):
    d2, _ = call("/api/search", {"q": '"density bonus"', "corpus": corpus, "limit": 2})
    check(f"runSearch: corpus={corpus}", d2, [
        "result_count", "results.[].city", "results.[].passage"],
        f"{d2.get('result_count')} hits")
d, st = call("/api/search", {"q": "x", "corpus": "bogus"})
check("runSearch: error card fields", d, ["error", "reason"], f"HTTP {st}")

# --- runGrep --------------------------------------------------------------
d, _ = call("/api/grep", {"pattern": "tally-only", "path": "nephi_city_council",
                          "limit": 5})
check("runGrep: match fields", d, [
    "match_count", "files_matched", "engine", "truncated", "truncation_reason",
    "matches.[].path", "matches.[].entity", "matches.[].line_no", "matches.[].line",
    "caveats"])
d, _ = call("/api/grep", {"pattern": "the", "limit": 2})
check("runGrep: partial sweep carries its hint", d, ["truncated", "hint"],
      d.get("truncation_reason"))
d, st = call("/api/grep", {"pattern": "x", "path": "/etc"})
check("runGrep: error card fields", d, ["error", "reason"], f"HTTP {st}")

# --- runEntity ------------------------------------------------------------
d, _ = call("/api/entity", {"name": "Salt Lake"})
check("runEntity: ambiguous case", d, [
    "ambiguous", "best", "disambiguation",
    "candidates.[].name", "candidates.[].slug", "candidates.[].level",
    "candidates.[].has_vote_db", "candidates.[].caveat_count",
    "candidates.[].within", "candidates.[].member_of",
    "candidates.[].contains_count", "candidates.[].relationship_note"])
d, _ = call("/api/entity", {"name": "Park City"})
check("runEntity: straddle_note", d, ["straddle_note"])
d, _ = call("/api/entity", {"name": "Juab"})
check("runEntity: no_vote_layer_note", d, ["no_vote_layer_note"])
d, st = call("/api/entity", {"name": "Kanab"})
check("runEntity: no-match card", d, ["error", "reason"], f"HTTP {st}")

# --- runCoverage ----------------------------------------------------------
d, _ = call("/api/coverage", {"entity": "nephi"})
check("runCoverage: entity case", d, [
    "row_count", "entity", "entity_name", "level", "has_vote_db", "note",
    "rows.[].city", "rows.[].dataset", "rows.[].motions", "rows.[].passed",
    "rows.[].outcome_unknown", "rows.[].first_date", "rows.[].last_date",
    "caveats.[].code"])
d, _ = call("/api/coverage")
check("runCoverage: all-entities case", d, ["row_count", "rows.[].city", "note"],
      f"{d['row_count']} rows")

# --- runDoc ---------------------------------------------------------------
d, _ = call("/api/document", {"path": "CLAUDE.md", "max_chars": 500})
check("runDoc: reader fields", d, [
    "chars_returned", "total_chars", "offset", "truncated", "text", "next_offset"])
d, _ = call("/api/document", {"path": "nephi_city_council/CLAUDE.md", "max_chars": 500})
check("runDoc: entity + caveats attach", d, ["entity_name", "caveats.[].code"],
      f"{d['entity_name']}, {len(d['caveats'])} caveats")
d, st = call("/api/document", {"path": "/etc/passwd"})
check("runDoc: confinement error card", d, ["error", "reason"], f"HTTP {st}")

# --- runSchema ------------------------------------------------------------
d, _ = call("/api/schema", {"tables": "caveat", "counts": "1"})
check("runSchema: detail view", d, [
    "objects.[].name", "objects.[].kind", "objects.[].rows",
    "objects.[].columns", "objects.[].sql"])
d, _ = call("/api/schema", {"counts": "1"})
check("runSchema: list view", d, ["object_count", "objects.[].name", "objects.[].kind"],
      f"{d['object_count']} objects")
d, _ = call("/api/schema", {"tables": "nope"})
check("runSchema: unknown list", d, ["unknown"])

# --- the page itself is reachable and self-contained ----------------------
page = PAGE.read_text(encoding="utf-8")
external = re.findall(r'(?:src|href)\s*=\s*["\'](https?:)?//', page)
check("console.html has no external assets",
      {"ok": True} if not external else {}, ["ok"],
      "fully self-contained" if not external else f"{len(external)} external refs")

# /console.html is the stable address. `/` serves chat.html once Phase 1 exists,
# and falls back to the console before that.
with urllib.request.urlopen(BASE + "/console.html") as resp:
    served = resp.read().decode()
check("/console.html serves it byte-identical",
      {"ok": True} if served == page else {}, ["ok"], f"{len(served)} bytes")

# Endpoints the page calls must all exist.
called = set(re.findall(r'api\("(/api/[a-z]+)"', page))
_, listing = call("/api/nope")
d, _ = call("/api/nope")
available = {"/api/" + e for e in d["endpoints"]}
check("every endpoint the page calls exists",
      {"ok": True} if called <= available else {}, ["ok"],
      " ".join(sorted(called)))

print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
