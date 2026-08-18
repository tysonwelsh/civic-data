#!/usr/bin/env python3
"""Measure an entity's on-disk file tree and emit it as annotated JSON + a
self-contained HTML tree graphic.

    python3 interface_prototype/build_entity_tree.py            # default: slc
    python3 interface_prototype/build_entity_tree.py slc lehi alta
    python3 interface_prototype/build_entity_tree.py --all-cities

Everything numeric here is MEASURED from the files (counts, bytes, CSV rows).
The prose annotations are curated, keyed by filename/dirname; anything without a
curated note simply carries none rather than a guessed one.

Outputs:
    interface_prototype/data/<slug>_tree.json   one per entity
    interface_prototype/entity_tree.html        all requested entities, inlined

Stdlib only, like the rest of the core pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SLUG = "south_jordan"   # the entity the page opens on; override with --default=<slug>
OUT_DIR = Path(__file__).resolve().parent / "data"
HTML_OUT = Path(__file__).resolve().parent / "entity_tree.html"

# ---------------------------------------------------------------- walk limits

SKIP_NAMES = {"__pycache__", "node_modules", ".git"}
MAX_DEPTH = 4
# Entries shown per directory before collapsing into a "… more" node. The entity's
# own top level is never truncated — that list IS the answer to "what does a city
# hold?" — and it tightens with depth.
MAX_CHILDREN_BY_DEPTH = {0: 999, 1: 16}
MAX_CHILDREN_DEFAULT = 10
ROW_COUNT_MAX_BYTES = 80 * 1024 * 1024   # don't line-count anything bigger

# ------------------------------------------------------------------ role map
# The repo's central distinction: canonical vs derived vs the correction and
# gap records that keep both honest. Cardinal rules 2 and 3, made visible.

ROLE_ORDER = ["canonical", "derived", "override", "gap", "index", "code", "doc", "raw", "other"]

OVERRIDE_FILES = {
    "vote_overrides.csv", "overrides.csv", "referral_overrides.csv",
    "disposition_overrides.csv", "finance_overrides.csv", "roster_overrides.csv",
    "donor_aliases.csv", "vintage_overrides.csv", "contest_overrides.csv",
}
GAP_FILES = {
    "minutes_unrecovered.csv", "unrecovered.csv", "gaps.csv",
    "dropped_oversize.csv", "text_extraction.csv", "fetch_log.csv",
}
INDEX_FILES = {
    "index.csv", "minutes_index.csv", "minutes_index_legacy.csv",
    "index_laserfiche.csv", "sources.csv", "contest_inventory.csv",
}
DERIVED_FILES = {
    "motions_std.csv", "roster.csv", "_validation_report.txt",
    "referrals_audit.csv", "cycle_totals.csv",
}
DERIVED_DIRS = {"db", "weeks", "derived", "tables", "text"}
RAW_DIRS = {"raw", "raw_pdf", "batch", "work", "shapefile"}


def role_for(path: Path, is_dir: bool, rel_parts: tuple[str, ...]) -> str:
    name = path.name
    if any(p in RAW_DIRS for p in rel_parts) or (is_dir and name in RAW_DIRS):
        return "raw"
    if is_dir:
        if name in DERIVED_DIRS:
            return "derived"
        return "canonical"
    if any(p in DERIVED_DIRS for p in rel_parts):
        return "derived"
    if name in OVERRIDE_FILES:
        return "override"
    if name in GAP_FILES:
        return "gap"
    if name in INDEX_FILES:
        return "index"
    if name in DERIVED_FILES:
        return "derived"
    if name.endswith(".py"):
        return "code"
    if name.endswith(".md"):
        return "doc"
    if name.endswith((".csv", ".geojson", ".gpkg", ".json")):
        return "canonical"
    if name.endswith(".db"):
        return "derived"
    return "other"


# ------------------------------------------------------------- annotations
# Keyed by exact name; <city> is substituted with the entity slug at build time.

# Display order for the entity's top level — the datasets that carry the story, in the
# order they should be read. Anything not listed keeps the default sort and falls in
# below (audits, recovery folders, pipeline scripts, per-layer docs).
TOP_ORDER = [
    "db",
    "campaign_finance",
    "election_results",
    "geo",
    "housing_plans",
    "meeting_minutes",
    "ordinances",
    "packets",
    "planning_commission",
    "public_comments",
    "roster",
    "weeks",
    "sources.csv",
]

ROOT_NOTES = {
    "city": "One government, one folder. Each subfolder below is a dataset that stands on its "
            "own — its own source manifest, its own build script, its own documented limit on "
            "what the city actually publishes.",
    "county": "Counties are built on their own terms rather than forced into the city shape: "
              "a legislative body, its land-use commissions, the agencies it sits as, and the "
              "canonical election canvass the cities inside it depend on.",
    "regional": "A metropolitan planning organization is programmed projects and growth "
                "projections, not roll calls. Its board minutes record no member votes — the "
                "source never names them — so the analytic surface here is the project layer.",
    "state": "The state tier is a targeted land-use and housing subset: the bills, their named "
             "roll calls, the Property Rights Ombudsman's opinions, and the statutes themselves.",
}

DIR_NOTES = {
    "meeting_minutes": "The council's own record — minutes as markdown, plus the roll-call votes extracted from them.",
    "planning_commission": "Same shape as meeting_minutes, for the appointed land-use body. Referrals link the two.",
    "public_comments": "What residents said on the record. An empty file here means the city publishes none — an honest zero, not a gap.",
    "election_results": "Municipal races filtered out of the county canvass: winners, margins, turnout.",
    "roster": "Who held which seat when — half-open tenure intervals with per-row confidence, plus versioned district boundaries.",
    "campaign_finance": "Disclosure filings: who funded whom, itemized where the filing was machine-readable or vision-transcribed.",
    "packets": "Agenda packets and staff reports — the analysis councils actually read before voting.",
    "ordinances": "Adopted ordinances, linked to their enacting motion where that link is unambiguous.",
    "housing_plans": "Moderate-income housing plans and the general plan — the city's own stated growth policy.",
    "transcripts": "Meeting-video transcripts where the city publishes them.",
    "pmn_backfill": "Documents recovered from the Utah Public Notice Website after the city's own portal lost or never posted them.",
    "geo": "Address-to-district lookup: precinct geometry plus the precinct→district crosswalk, versioned across redistrictings.",
    "db": "DERIVED. The per-entity SQLite database, rebuilt from the flat CSVs. Never hand-edited.",
    "weeks": "DERIVED. One bundle per week — a plain-language summary with that week's votes and comments beside it.",
    "minutes": "The canonical minutes, as markdown, filed by year.",
    "votes": "Per-meeting extracted vote files that roll up into all_votes.csv.",
    "raw": "Original source PDFs. Kept locally, never committed — re-fetchable from the source_url in the index.",
    "text": "Extracted plain text from the raw originals — what the search layer actually indexes.",
    "tables": "DERIVED. Each database table exported to CSV for diff-friendly review.",
    "derived": "DERIVED. Regenerated outputs, not source.",
    "shapefile": "Source geographic boundary files.",
}

FILE_NOTES = {
    "all_votes.csv": "CANONICAL. One row per member per motion — the vote spine everything else is built on.",
    "motions_std.csv": "DERIVED. The normalization layer: each city's own motion labels mapped to a shared vocabulary, stored ALONGSIDE the verbatim originals rather than replacing them.",
    "roster.csv": "DERIVED. Who appears in the vote record, regenerated from the votes themselves.",
    "minutes_index.csv": "The provenance manifest: every minutes file, its meeting date, body, and source URL.",
    "minutes_index_legacy.csv": "Provenance manifest for the older portal era.",
    "index_laserfiche.csv": "Provenance manifest for the Laserfiche-era documents.",
    "minutes_unrecovered.csv": "HONEST GAP. Meetings that demonstrably happened but whose minutes could not be recovered from any channel. The gap is recorded as data.",
    "unrecovered.csv": "HONEST GAP. Documents known to exist but not retrievable.",
    "gaps.csv": "HONEST GAP. Enumerated holes in this dataset's coverage.",
    "dropped_oversize.csv": "HONEST GAP. Files skipped for size, with enough identifying detail to fetch them by hand.",
    "vote_overrides.csv": "CORRECTION FILE. Where a source contradicts itself, the fix lives here — never as an in-place edit to the city's own values.",
    "overrides.csv": "CORRECTION FILE. Documented corrections applied at build time, leaving the source values intact.",
    "referral_overrides.csv": "CORRECTION FILE. Hand-verified planning-commission→council links.",
    "disposition_overrides.csv": "CORRECTION FILE. Hand-checked approve/deny/continue classifications.",
    "finance_overrides.csv": "CORRECTION FILE. Verified campaign-finance corrections.",
    "roster_overrides.csv": "CORRECTION FILE. Confirmed roster changes — appointments, resignations, redistrictings.",
    "donor_aliases.csv": "Donor name normalization — the same contributor written five ways, reconciled without touching the filed spelling.",
    "referrals_audit.csv": "DERIVED. Every reconstructed cross-body link with its confidence score.",
    "contributions.csv": "CANONICAL. Itemized contributions as filed. Empty means NOT TRANSCRIBED — never 'no donors'.",
    "expenditures.csv": "CANONICAL. Itemized expenditures as filed.",
    "filing_totals.csv": "The totals each filing states on its own cover. Never sum these — filings overlap.",
    "cycle_totals.csv": "DERIVED. The only sanctioned per-candidate totals, built to avoid the overlap problem above.",
    "all_comments_clean.csv": "CANONICAL. Public comments, email- and phone-redacted per PRIVACY.md.",
    "council_terms.csv": "CANONICAL. Seat tenures as half-open intervals, with VACANT stretches recorded rather than smoothed over.",
    "district_versions.csv": "Districts as they existed in each redistricting era.",
    "district_precincts.csv": "Which precincts composed each district, per era.",
    "precinct_to_district.csv": "The crosswalk behind address→district lookup.",
    "index.csv": "The provenance manifest for this dataset: every file, its date, and where it came from.",
    "sources.csv": "Machine-readable source registry for the whole entity.",
    "CLAUDE.md": "The authoritative read-me for this layer — what it contains, how it was built, and what it cannot answer.",
    "SOURCES.md": "Where every file came from, in prose.",
    "AVAILABILITY.md": "What the source publishes versus what it withholds — the ceiling on this dataset.",
    "SCHEMA.md": "The database schema for this entity.",
    "VERIFICATION.md": "The checks run against this entity and their results.",
    "COVERAGE.md": "The measured coverage ledger, including what is genuinely missing.",
    "recon.md": "Reconciliation record — doubly-stored facts checked against each other.",
    "_validation_report.txt": "DERIVED. Output of the validator's last run.",
    "address_to_district.py": "The lookup tool: an address in, a council district out.",
    "extract_votes.py": "The deterministic extractor that turns minutes text into vote rows.",
    "validate_votes.py": "Checks the extracted votes against the minutes they came from.",
    "build_db.py": "Rebuilds this entity's database from the flat CSVs. Idempotent.",
    "build_referrals.py": "Reconstructs planning-commission→council links and scores each one.",
    "build_weeks.py": "Rebuilds the weekly bundles.",
    "fetch_new.py": "Probes the city's portal for documents published since the last run.",
    "index.md": "Human-readable index of the weekly bundles.",
    "summary.md": "The week in plain language, with that week's votes and comments linked beside it.",
}

ROLE_BLURBS = {
    "canonical": "Canonical — the primary record. City-faithful values here are never overwritten.",
    "derived": "Derived — regenerated from the canonical layer by a script. Never hand-edited.",
    "override": "Correction file — documented fixes applied at build time, leaving source values intact.",
    "gap": "Gap record — something known to be missing, recorded as data rather than silently absent.",
    "index": "Provenance manifest — what each file is and where it came from.",
    "code": "Pipeline code — the script that produces or checks this layer.",
    "doc": "Documentation — what this layer contains and what it cannot answer.",
    "raw": "Raw original — kept locally, not committed, re-fetchable from its source URL.",
    "other": "",
}


# ------------------------------------------------------------------ measuring

def count_rows(path: Path) -> int | None:
    """Data rows in a CSV (excluding the header). None if not worth counting."""
    if path.suffix.lower() != ".csv":
        return None
    try:
        if path.stat().st_size > ROW_COUNT_MAX_BYTES:
            return None
        with path.open("rb") as fh:
            n = sum(1 for _ in fh)
        return max(n - 1, 0)
    except OSError:
        return None


def dir_totals(path: Path) -> tuple[int, int]:
    """(file count, total bytes) beneath a directory, recursively."""
    files = 0
    size = 0
    for root, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES and not d.startswith(".")]
        for n in names:
            if n.startswith("."):
                continue
            files += 1
            try:
                size += (Path(root) / n).stat().st_size
            except OSError:
                pass
    return files, size


def note_for(name: str, is_dir: bool, slug: str) -> str:
    table = DIR_NOTES if is_dir else FILE_NOTES
    note = table.get(name)
    if note is None and not is_dir:
        # per-entity filenames: <slug>_races.csv, <slug>.db, ...
        if name.endswith("_races.csv"):
            note = "CANONICAL. The audited race table — authoritative winners and margins."
        elif name.endswith("_results_by_candidate.csv"):
            note = "Per-candidate tallies as the county canvass reported them."
        elif name.endswith("_results_by_precinct.csv"):
            note = "Precinct-level tallies from the canvass."
        elif name.endswith(".db"):
            note = "DERIVED. This entity's SQLite database, rebuilt from the flat CSVs."
    return (note or "").replace("<city>", slug)


def build_node(path: Path, slug: str, depth: int, rel_parts: tuple[str, ...]) -> dict:
    is_dir = path.is_dir()
    role = role_for(path, is_dir, rel_parts)
    node: dict = {
        "name": path.name,
        "type": "dir" if is_dir else "file",
        "role": role,
        "note": note_for(path.name, is_dir, slug),
    }

    if not is_dir:
        try:
            node["bytes"] = path.stat().st_size
        except OSError:
            node["bytes"] = 0
        rows = count_rows(path)
        if rows is not None:
            node["rows"] = rows
        return node

    files, size = dir_totals(path)
    node["files"] = files
    node["bytes"] = size

    def sort_key(p: Path):
        # Directories before files, alphabetical — except at the entity's own top level,
        # where TOP_ORDER puts the headline datasets first in reading order.
        if depth == 0 and p.name in TOP_ORDER:
            return (0, TOP_ORDER.index(p.name), "")
        return (1, p.is_file(), p.name.lower())

    try:
        entries = sorted(
            (p for p in path.iterdir()
             if not p.name.startswith(".") and p.name not in SKIP_NAMES),
            key=sort_key,
        )
    except OSError:
        entries = []

    if depth >= MAX_DEPTH:
        if entries:
            node["children"] = [{
                "name": f"… {len(entries)} entries",
                "type": "more", "role": "other", "note": "",
            }]
        return node

    cap = MAX_CHILDREN_BY_DEPTH.get(depth, MAX_CHILDREN_DEFAULT)
    shown = entries[:cap]
    node["children"] = [
        build_node(p, slug, depth + 1, rel_parts + (p.name,)) for p in shown
    ]
    hidden = len(entries) - len(shown)
    if hidden > 0:
        kinds = "entries" if any(p.is_dir() for p in entries[cap:]) else "files"
        node["children"].append({
            "name": f"… {hidden} more {kinds}",
            "type": "more", "role": "other", "note": "",
        })
    return node


# --------------------------------------------------------------- entity meta

def load_registry() -> dict[str, dict]:
    import csv
    with (REPO / "registry" / "entities.csv").open(newline="", encoding="utf-8") as fh:
        return {r["slug"]: r for r in csv.DictReader(fh)}


def db_facts(slug: str) -> dict:
    """Headline federated counts for this entity, straight from gov.db."""
    import sqlite3
    gov = REPO / "gov.db"
    if not gov.exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{gov}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    facts: dict[str, int] = {}
    queries = {
        "motions": "SELECT COUNT(*) FROM motion WHERE city=?",
        "member_votes": "SELECT COUNT(*) FROM vote WHERE city=?",
        "meetings": "SELECT COUNT(*) FROM meeting WHERE city=?",
        "documents": "SELECT COUNT(*) FROM document WHERE city=?",
        "comments": "SELECT COUNT(*) FROM comment WHERE city=?",
        "ordinances": "SELECT COUNT(*) FROM ordinance WHERE city=?",
        "races": "SELECT COUNT(*) FROM election_race WHERE city=?",
        "contributions": "SELECT COUNT(*) FROM cf_contribution WHERE city=?",
        "terms": "SELECT COUNT(*) FROM term WHERE city=?",
        "searchable_minutes": "SELECT COUNT(*) FROM fts_minutes WHERE city=?",
    }
    try:
        for key, sql in queries.items():
            facts[key] = con.execute(sql, (slug,)).fetchone()[0]
        facts["caveats"] = [
            {"dataset": d, "code": c, "text": t}
            for d, c, t in con.execute(
                "SELECT dataset, code, caveat FROM caveat WHERE city=? ORDER BY dataset, code",
                (slug,),
            )
        ]
    except sqlite3.Error:
        pass
    finally:
        con.close()
    return facts


def build_entity(slug: str, registry: dict) -> dict | None:
    row = registry.get(slug)
    if row is None:
        print(f"  ! {slug}: not in registry/entities.csv", file=sys.stderr)
        return None
    entity_dir = REPO / row["dir"]
    if not entity_dir.is_dir():
        print(f"  ! {slug}: no directory ({row['dir']})", file=sys.stderr)
        return None

    tree = build_node(entity_dir, slug, 0, ())
    tree["note"] = ROOT_NOTES.get(row["level"], "")
    payload = {
        "slug": slug,
        "name": row["name"],
        "level": row["level"],
        "dir": row["dir"],
        "portal": row.get("portal", ""),
        "gov_form": row.get("gov_form", ""),
        "registry_notes": row.get("notes", ""),
        "facts": db_facts(slug),
        "tree": tree,
        "role_blurbs": ROLE_BLURBS,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}_tree.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"  · {slug}: {tree['files']} files, {tree['bytes']/1e9:.2f} GB → {out.name}")
    return payload


# ------------------------------------------------------------------ html out

def write_html(payloads: list[dict]) -> None:
    tpl = (Path(__file__).resolve().parent / "entity_tree.template.html").read_text(encoding="utf-8")
    data = json.dumps({p["slug"]: p for p in payloads}, separators=(",", ":"))
    order = json.dumps([p["slug"] for p in payloads])
    html = tpl.replace("/*__DATA__*/null", data).replace("/*__ORDER__*/null", order)
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"\n  → {HTML_OUT.relative_to(REPO)}  ({len(payloads)} entities, {len(html)/1024:.0f} KB)")


def main(argv: list[str]) -> int:
    registry = load_registry()
    args = argv[1:]

    # The page opens on the first entity built. --default pins one to the front so the
    # landing entity survives a rebuild with different arguments.
    default = DEFAULT_SLUG
    rest = []
    for a in args:
        if a.startswith("--default="):
            default = a.split("=", 1)[1]
        else:
            rest.append(a)
    args = rest or [default]
    if args == ["--all-cities"]:
        slugs = [s for s, r in registry.items() if r["level"] == "city"]
    elif args == ["--all"]:
        slugs = [s for s, r in registry.items() if r["build_status"] != "registered_only"]
    else:
        slugs = args
    if default in slugs:
        slugs = [default] + [s for s in slugs if s != default]

    print(f"Measuring {len(slugs)} entit{'y' if len(slugs) == 1 else 'ies'} …")
    payloads = [p for p in (build_entity(s, registry) for s in slugs) if p]
    if not payloads:
        print("nothing built", file=sys.stderr)
        return 1
    write_html(payloads)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
