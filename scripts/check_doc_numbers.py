#!/usr/bin/env python3
"""Doc-vs-db drift gate (SHIP_GATE.md predicate 3, created 2026-07-31, G4).

Every headline number a reader will quote from README.md / CLAUDE.md /
gov_db_SCHEMA.md is asserted here against the live gov.db. Run after every
federation; exit 1 on any mismatch (or on a pattern no longer found — a doc
rewrite must keep these claims greppable or update this file in the same
session).
"""
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "gov.db")

# (name, file, regex-with-N-capture-groups, [N queries returning one number each])
CHECKS = [
    ("README motions row", "README.md",
     r"\| \*\*motions\*\* \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \|",
     ["SELECT COUNT(*) FROM motion WHERE gov_level='city'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='county'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='regional'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='state'"]),
    ("README member-votes row", "README.md",
     r"\| \*\*member-votes\*\* \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \|",
     ["SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='city'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='county'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='regional'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='state'"]),
    ("README elections row", "README.md",
     r"`election_race` ([\d,]+) .*`election_result` ([\d,]+)",
     ["SELECT COUNT(*) FROM election_race",
      "SELECT COUNT(*) FROM election_result"]),
    ("README fts_minutes", "README.md",
     r"`fts_minutes` — ([\d,]+) documents",
     ["SELECT COUNT(*) FROM fts_minutes"]),
    ("README entity count", "README.md",
     r"\*\*(\d+) registered entities in a 4-tier model\*\* \((\d+) built",
     ["SELECT COUNT(*) FROM entity",
      "SELECT COUNT(*) FROM entity WHERE slug NOT IN ('udot','uta','wasatch_county')"]),
    ("CLAUDE.md motions line", "CLAUDE.md",
     r"motions ([\d,]+) city / ([\d,]+) county / ([\d,]+) regional / ([\d,]+) state",
     ["SELECT COUNT(*) FROM motion WHERE gov_level='city'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='county'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='regional'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='state'"]),
    ("CLAUDE.md member-votes line", "CLAUDE.md",
     r"member-votes ([\d,]+) city / ([\d,]+) county / ([\d,]+) regional / ([\d,]+) state",
     ["SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='city'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='county'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='regional'",
      "SELECT COUNT(*) FROM vote v JOIN motion m USING(motion_id) WHERE m.gov_level='state'"]),
    ("CLAUDE.md motion_std total", "CLAUDE.md",
     r"tiers, ([\d,]+) rows joined to `motion` at 100%",
     ["SELECT COUNT(*) FROM motion_std"]),
    ("CLAUDE.md ut_state fts rows", "CLAUDE.md",
     r"`fts_minutes` carries (\d+) ut_state rows",
     ["SELECT COUNT(*) FROM fts_minutes WHERE city='ut_state'"]),
    ("CLAUDE.md fts_minutes total", "CLAUDE.md",
     r"\*\*([\d,]+) docs\*\* from (\d+) entities",
     ["SELECT COUNT(*) FROM fts_minutes",
      "SELECT COUNT(DISTINCT city) FROM fts_minutes"]),
    ("gov_db_SCHEMA caveat count", "gov_db_SCHEMA.md",
     r"The `caveat` table \((\d+) rows\)",
     ["SELECT COUNT(*) FROM caveat"]),
    ("gov_db_SCHEMA motion split", "gov_db_SCHEMA.md",
     r"\*\*motion ([\d,]+)\*\* — city ([\d,]+) / county ([\d,]+) /\s*regional ([\d,]+) / state ([\d,]+)",
     ["SELECT COUNT(*) FROM motion",
      "SELECT COUNT(*) FROM motion WHERE gov_level='city'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='county'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='regional'",
      "SELECT COUNT(*) FROM motion WHERE gov_level='state'"]),
    ("gov_db_SCHEMA term count", "gov_db_SCHEMA.md",
     r"\*\*term (\d+)\*\*",
     ["SELECT COUNT(*) FROM term"]),
    # --- county cycle reducer (2026-08-23). The county rollup's headline numbers are
    # gated like every other: total rows, the publish/gap split, and the flagged floors.
    # A floor miscounted as a total is the failure mode this layer exists to prevent.
    ("gov_db_SCHEMA cf_cycle_county rows", "gov_db_SCHEMA.md",
     r"\*\*`cf_cycle_county` ([\d,]+) — the COUNTY tier\*\*",
     ["SELECT COUNT(*) FROM cf_cycle_county"]),
    ("gov_db_SCHEMA cf_cycle_county split", "gov_db_SCHEMA.md",
     r"\*\*([\d,]+) rows publish a figure;\s*([\d,]+) are honest GAP rows\*\*",
     ["SELECT COUNT(*) FROM cf_cycle_county WHERE raised_gross IS NOT NULL",
      "SELECT COUNT(*) FROM cf_cycle_county WHERE raised_gross IS NULL"]),
    ("gov_db_SCHEMA cf_cycle_county floors", "gov_db_SCHEMA.md",
     r"`is_floor`=1 on \*\*([\d,]+) rows whose",
     ["SELECT COUNT(*) FROM cf_cycle_county WHERE is_floor='1'"]),
    ("CLAUDE.md cf_cycle_county", "CLAUDE.md",
     r"\*\*`cf_cycle_county` is the COUNTY tier\*\* \(([\d,]+) candidate-cycles",
     ["SELECT COUNT(*) FROM cf_cycle_county"]),
    ("CLAUDE.md cf_cycle_county gaps", "CLAUDE.md",
     r"and \*\*([\d,]+) honest GAP rows\*\*",
     ["SELECT COUNT(*) FROM cf_cycle_county WHERE raised_gross IS NULL"]),
    ("README cf_cycle_county", "README.md",
     r"`cf_cycle_county` \(counties, ([\d,]+)\s*\n?candidate-cycles",
     ["SELECT COUNT(*) FROM cf_cycle_county"]),
]


def main():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    failures = 0
    for name, fname, pattern, queries in CHECKS:
        path = os.path.join(ROOT, fname)
        text = open(path, encoding="utf-8").read()
        m = re.search(pattern, text, re.DOTALL if ".*" in pattern else 0)
        if not m:
            print(f"FAIL  {name}: pattern not found in {fname} (doc rewrite must "
                  f"update scripts/check_doc_numbers.py in the same session)")
            failures += 1
            continue
        doc_vals = [int(g.replace(",", "")) for g in m.groups()]
        db_vals = [db.execute(q).fetchone()[0] for q in queries]
        if doc_vals == db_vals:
            print(f"PASS  {name}: {doc_vals}")
        else:
            print(f"FAIL  {name}: {fname} says {doc_vals}, gov.db says {db_vals}")
            failures += 1
    built = db.execute("SELECT value FROM build_info WHERE key='built_at'").fetchone()[0]
    print(f"\ngov.db built_at: {built}")
    if failures:
        print(f"{failures} check(s) FAILED — reconcile the doc(s) or note why.")
        return 1
    print("All doc-vs-db checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
