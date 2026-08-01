#!/usr/bin/env python3
"""build_db.py — thin driver over the SHARED within-body exact core
(scripts/db_build_lib.py). Consumes meeting_minutes/all_votes.csv (Council + RDA)
+ planning_commission/all_votes.csv and writes Midvale's SQLite db + tables/
exports, with the fail-loud db/vote_overrides.csv reconciliation. Idempotent.

    python3 db/build_db.py        # then db/build_referrals.py

PERSON-ALIAS HOOK (2026-07-31). `db/person_aliases.csv` is the DOCUMENTED
person-resolution path for same-person name variants the city itself prints
(cardinal rule 2: the flat all_votes.csv keeps every verbatim spelling; the
unification is a db concern, and it lives in an override file, never as an
in-place edit). The shared library has no alias slot of its own, so this driver
wraps `db_build_lib.norm_person` — the single funnel every member / mover /
seconder string passes through in `read_motions` — leaving the shared library
untouched. Same file name + `raw_name,canonical_name,evidence` header as the
cache_county / utah_county / wfrc_mpo builders, which own this convention.
Aliasing at `norm_person` (rather than at `person_key`) also fixes the DISPLAY
name, so `person.full_name` is the canonical spelling instead of whichever
variant happened to sort first.
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
import db_build_lib
from db_build_lib import main


def _load_aliases():
    p = os.path.join(HERE, "person_aliases.csv")
    d = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            raw, canon = r["raw_name"].strip(), r["canonical_name"].strip()
            if raw and canon:
                d[db_build_lib.person_key(raw)] = canon
    return d


ALIAS = _load_aliases()
_norm_person = db_build_lib.norm_person


def norm_person(name):
    """Shared role-prefix normalization, then the documented alias map."""
    n = _norm_person(name)
    return ALIAS.get(db_build_lib.person_key(n), n) if n else n


db_build_lib.norm_person = norm_person

if __name__ == "__main__":
    if ALIAS:
        print(f"person_aliases.csv: {len(ALIAS)} documented alias(es) applied "
              f"({', '.join(sorted(set(ALIAS.values())))})")
    sys.exit(main(HERE))
