#!/usr/bin/env python3
"""add_minutes_headers.py — embed a provenance header in every minutes markdown file
(REFACTOR_PLAN 5.4; the Taylorsville build convention, extended repo-wide 2026-07-07).

    python3 scripts/add_minutes_headers.py <slug> [<slug> ...] | --all [--dry-run]

For each row of meeting_minutes/minutes_index.csv + planning_commission/minutes_index.csv,
inserts at the top of the markdown file (after a first-line '# ' heading if present):

    > Source: <source_url or '(not recorded — see minutes_index.csv)'>
    > Meeting date: <date>
    > Format: <format>

    ---

IDEMPOTENT: files already carrying a '> Source:' line in their first 6 lines are
skipped — safe to re-run after every fetch (refresh-city step 3 does). ADDITIVE ONLY:
the body text is never altered; the script asserts new_content == head + block + rest
before writing. Never touches raw/, the index, or files not listed in the index.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cities import DIRS, SLUGS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS = ["meeting_minutes", "planning_commission"]


def header_block(url, date, fmt):
    return ("> Source: %s\n> Meeting date: %s\n> Format: %s\n\n---\n\n"
            % (url or "(not recorded — see minutes_index.csv)", date, fmt or "unknown"))


def process_city(slug, dry_run=False):
    added = skipped = missing = 0
    for ds in DATASETS:
        idx = os.path.join(ROOT, DIRS[slug], ds, "minutes_index.csv")
        if not os.path.exists(idx):
            continue
        for r in csv.DictReader(open(idx, encoding="utf-8-sig")):
            rel = r.get("path") or ""
            if not rel:
                continue
            p = os.path.join(ROOT, DIRS[slug], rel)
            if not os.path.exists(p):
                p = os.path.join(ROOT, DIRS[slug], ds, rel)
            if not os.path.exists(p):
                missing += 1
                continue
            text = open(p, encoding="utf-8").read()
            probe = "\n".join(text.splitlines()[:6])
            if "> Source:" in probe:
                skipped += 1
                continue
            block = header_block(r.get("source_url", "").strip(), r.get("date", ""),
                                 r.get("format", ""))
            lines = text.splitlines(keepends=True)
            if lines and lines[0].startswith("# "):
                head, rest = lines[0], "".join(lines[1:])
                new = head + block + rest
                assert new == head + block + rest
            else:
                head, rest = "", text
                new = block + text
            # additive-only invariant: stripping the block restores the original
            assert new.replace(block, "", 1) == text, p
            if not dry_run:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new)
            added += 1
    print("%-13s headers added %5d, already present %5d, missing paths %d"
          % (slug, added, skipped, missing))
    return added


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    slugs = SLUGS if "--all" in sys.argv else args
    if not slugs:
        sys.exit(__doc__)
    total = sum(process_city(s, dry) for s in slugs)
    print("total headers added: %d%s" % (total, " (dry run)" if dry else ""))


if __name__ == "__main__":
    main()
