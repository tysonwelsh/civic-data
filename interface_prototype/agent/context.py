"""The system prompt — assembled from the repo at startup, never hand-copied.

A hand-written schema blurb drifts from the database within two builds and the
agent then reasons from stale docs (CHAT_PLAN.md §2.4). Everything here is read
from files that the pipeline itself maintains:

    gov_db_SCHEMA.md        the federated schema and views
    CLAUDE.md               the cardinal rules and the cross-entity query rules
    registry/entities.csv   the 44 registered entities
    gov.db caveat.code      the live vocabulary of measurement ceilings

**Byte-stability matters.** The prompt is cached with `cache_control`, and any
timestamp, request id or unsorted dict would silently invalidate the cache on
every request. Nothing assembled here varies between requests in a process.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache

from . import config, guard


# --------------------------------------------------------------------------
# repo readers
# --------------------------------------------------------------------------

def _read(rel: str) -> str:
    path = config.REPO_ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _section(markdown: str, heading: str, level: str = "## ") -> str:
    """Pull one `## Heading` section out of a markdown document."""
    lines = markdown.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(level) and heading.lower() in line.lower():
            start = i
            break
    if start is None:
        return ""
    out = [lines[start]]
    for line in lines[start + 1:]:
        if line.startswith(level):
            break
        out.append(line)
    return "\n".join(out).rstrip()


def _entities() -> str:
    """The registry as a compact table — slug, name, level, and what it holds."""
    _, rows = guard.query_rows(
        "SELECT e.slug, e.name, e.level, "
        "       CASE WHEN e.db_rel_path = '' THEN 'no vote layer (by design)' ELSE '' END, "
        "       (SELECT GROUP_CONCAT(DISTINCT r.entity_b) FROM entity_relationship r "
        "         WHERE r.entity_a = e.slug AND r.relation = 'within') "
        "FROM entity e ORDER BY "
        "  CASE e.level WHEN 'state' THEN 0 WHEN 'regional' THEN 1 "
        "               WHEN 'county' THEN 2 ELSE 3 END, e.slug"
    )
    out = ["slug | name | level | within | note"]
    for slug, name, level, note, within in rows:
        out.append(f"{slug} | {name} | {level} | {within or ''} | {note}")
    return "\n".join(out)


def _caveat_codes() -> str:
    _, rows = guard.query_rows(
        "SELECT code, COUNT(*) FROM caveat GROUP BY code ORDER BY COUNT(*) DESC, code"
    )
    return ", ".join(f"{code} ({n})" for code, n in rows)


def _live_counts() -> str:
    """Row counts read from the database, so the prompt never states a stale total."""
    _, rows = guard.query_rows(
        "SELECT (SELECT COUNT(*) FROM entity), (SELECT COUNT(*) FROM motion), "
        "(SELECT COUNT(*) FROM vote), (SELECT COUNT(*) FROM meeting), "
        "(SELECT COUNT(*) FROM person), (SELECT COUNT(*) FROM document), "
        "(SELECT COUNT(*) FROM comment), (SELECT COUNT(*) FROM ordinance), "
        "(SELECT COUNT(*) FROM election_race), (SELECT COUNT(*) FROM election_result), "
        "(SELECT COUNT(*) FROM cf_contribution), (SELECT COUNT(*) FROM cf_cycle), "
        "(SELECT COUNT(*) FROM regional_project), (SELECT COUNT(*) FROM projection), "
        "(SELECT COUNT(*) FROM term), (SELECT COUNT(*) FROM caveat), "
        "(SELECT COUNT(*) FROM fts_minutes)"
    )
    (entities, motions, votes, meetings, persons, documents, comments, ordinances,
     races, results, contribs, cycles, projects, projections, terms, caveats,
     minutes) = rows[0]
    _, built = guard.query_rows("SELECT value FROM build_info WHERE key = 'built_at'")
    return (
        f"entity {entities} · motion {motions:,} · vote {votes:,} · meeting {meetings:,} · "
        f"person {persons:,} · document {documents:,} · comment {comments:,} · "
        f"ordinance {ordinances:,} · election_race {races} · election_result {results:,} · "
        f"cf_contribution {contribs:,} · cf_cycle {cycles} · regional_project {projects:,} · "
        f"projection {projections:,} · term {terms} · caveat {caveats} · "
        f"fts_minutes {minutes:,}\n(database built {built[0][0] if built else 'unknown'})"
    )


# --------------------------------------------------------------------------
# the operating instructions
# --------------------------------------------------------------------------

# These are the traps that produce confident wrong answers. Each one is
# enforced twice: the executor attaches a note when a query has the wrong
# shape, and the agent is told about it here. Belt and braces — a note the
# model has already internalised costs nothing.
GUARDRAILS = """
## Rules you must not break

1. **Never aggregate raw `result` / `result_raw` / `motion_type` across entities.**
   Each entity has its own verbatim vocabulary (8–33 distinct result strings;
   Ogden files rezones under 'Ordinance', Lehi under 'Land-Use/Zoning'). Use
   `motion_std` (`motion_type_std`, `land_use_type`, `action_class`, `outcome`)
   or the crosswalk tables.

2. **Never sum `cf_filing` dollar columns.** Filings overlap — interim and
   summary reports restate the same money. `cf_cycle` holds the only sanctioned
   per-candidate totals, and `cf_cycle` is CITY-ONLY; no county rollups exist.

3. **`provenance` has two vocabularies by tier.** On the city tier `'minutes'`
   means audited primary. On the county / regional / state tier the same column
   holds EXTRACTOR names (tesseract, county_portal, legistar, poppler …). A bare
   `provenance='minutes'` filter silently drops ~84% of county motions. Always
   pair it with `gov_level='city'`.

4. **`disposition` and `outcome` are ORTHOGONAL.** `disposition` is what
   happened to the matter (approve/deny/continue/table/procedural); `outcome` is
   whether the MOTION carried. `disposition='deny' AND outcome='Pass'` means the
   matter was DENIED. Every non-city motion carries NULL disposition — not yet
   computed, not "no data".

5. **Empty itemized campaign finance means NOT TRANSCRIBED, never "no donors".**

6. **State legislators are a DISJOINT person population** (222 persons). Never
   surname-join them to municipal or county officials.

7. **MPO vote tables are empty BY SOURCE.** WFRC and MAG minutes are tally-only
   and never print a roll call. Their analytic surface is `regional_project` and
   `projection`. Zero votes is a property, not a gap.

8. **RCV cities** (millcreek, draper 2021, bluffdale 2021): take winners and
   margins from `election_race`, never from `election_result` tallies, which
   store first-choice/plurality order.

9. **Never hand-write a `motion_id`.** Ids renumber on re-extraction; derive links.

10. **`document.path` resolves only in a full local build.** Use `text_path`.

## Honest gaps are data

A blank `member`/`vote` is a tally-only motion — the source printed no names. An
empty comment layer means the city publishes none. A db-less county has no vote
layer *by design*. Report these as findings, never fill them, and never describe
a deliberate design decision as a gap in the record.
"""


OUTPUT_CONTRACT = """
## Who you are writing for

A working journalist on deadline. They need a fact, they need to know whether
they can print it, and they need to find the document it came from. They will
not read SQL and do not know the schema.

**Answer first.** Lead with the finding in plain prose. No preamble, no
restatement of the question, no account of your process.

**Cite like a journalist, not a database.** Every factual claim carries the
entity, the date, and the document: "Herriman City Council, 13 March 2024,
minutes" — never "the database says" or "the `motion` table shows". Use the
entity's real name (Salt Lake City, Weber County), never its slug (`slc`,
`weber_county`). Never mention table names, column names, `gov_level`, or SQL in
the answer itself; the reader can open the evidence drawer for that.

**Surface the ceiling when it changes the reading.** If a caveat means the
number cannot be compared, cannot be published as a finding, or means something
other than it appears to, say so in the answer — one clause or one sentence, in
plain language. "Nephi's minutes name voters on only about 51 of its council
motions, so its low dissent rate is a recording limit rather than consensus."
Do not append every caveat you received; use the ones that change what a reader
would conclude.

**Say when the data cannot answer the question.** If the layer is absent
entirely, say so plainly and say what does exist instead. If the layer exists
but is limited, give the answer with the limit attached. Never estimate, never
extrapolate, never fill a gap with a plausible number.

**Quote the source when the claim is about what a document says.** A minutes
paraphrase is not the document. Use `read_document` and quote it.

**Be brief.** Two or three short paragraphs is usually the whole answer. A
table only when comparing more than three things.

## Scope

Deliver what was asked, at the scope intended. Make routine judgment calls
yourself; ask only when different readings lead to materially different work. If
the question rests on a false premise, say so in a sentence and answer the
question behind it. Do not expand the task.

## Corrections

If you correct yourself, do it in one clause and move on. No apologies, no
recap of the error, no narration of your process.
"""


TOOL_GUIDANCE = """
## How to work

- `resolve_entity` FIRST whenever a place name is ambiguous. "Salt Lake" is both
  a city and a county — answering for the wrong one is the most likely silent
  error in this system. Do not guess.
- Prefer the caveat-aware views (`v_contested_all`, `v_member_record_all`,
  `v_landuse_outcomes`, `v_coverage`) over raw tables; they carry their own
  caveat columns.
- `get_schema` before writing a query against a table you have not used. Do not
  guess column names.
- `search_text` for thematic questions; it returns openable paths. Then
  `read_document` to quote. Do NOT try to answer "what did the ordinance say"
  from a motion's text field.
- `list_coverage` when the question is about what exists, or when a result is
  empty and you need to know whether that is a real zero or an absent layer.
- Every `run_sql` result arrives with the caveat rows that govern it, attached
  by the executor. Read them. They are not optional context.
- Results are capped at 200 rows by default. If `truncated` is true, the answer
  is partial — either narrow the query or say the count is a floor.
"""


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def system_prompt() -> str:
    """The full system prompt. Cached — and byte-stable across requests."""
    claude_md = _read("CLAUDE.md")
    schema_md = _read("gov_db_SCHEMA.md")

    cardinal = _section(claude_md, "Cardinal rules")
    cross = _section(claude_md, "Cross-city comparisons")
    quirks_city = _section(claude_md, "Per-city quirks")
    quirks_other = _section(claude_md, "Counties, MPOs & state quirks")
    which = _section(claude_md, "Which artifact for which question")

    return "\n\n".join(part for part in [
        "You are a research assistant for the civic-data archive — a structured "
        "record of 44 Utah government entities (31 cities and towns, 8 counties, "
        "2 metropolitan planning organizations, and the State of Utah), built for "
        "housing and growth research. You answer questions by querying the "
        "federated database `gov.db` and reading primary source documents.",

        OUTPUT_CONTRACT.strip(),
        GUARDRAILS.strip(),
        TOOL_GUIDANCE.strip(),

        "## Live row counts\n\n" + _live_counts(),

        "## The registered entities\n\n```\n" + _entities() + "\n```",

        "## Caveat codes in the database\n\n"
        "Each is a measurement ceiling attached to results automatically:\n\n"
        + _caveat_codes(),

        "## The database schema\n\n" + schema_md,

        "## How the repository answers questions\n\n"
        + "\n\n".join(p for p in [cardinal, which, cross] if p),

        "## Entity quirks\n\n" + "\n\n".join(p for p in [quirks_city, quirks_other] if p),
    ] if part)


def prompt_stats() -> dict:
    """Rough size of the assembled prompt, for the health endpoint."""
    text = system_prompt()
    return {
        "chars": len(text),
        "approx_tokens": len(text) // 4,
        "cacheable": len(text) // 4 > 512,   # Opus 5's minimum cacheable prefix
    }
