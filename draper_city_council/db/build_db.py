#!/usr/bin/env python3
"""build_db.py — thin driver over the SHARED within-body exact core
(scripts/db_build_lib.py). Consumes meeting_minutes/all_votes.csv (Council) +
planning_commission/all_votes.csv and writes Draper's SQLite db + tables/
exports, with the fail-loud db/vote_overrides.csv reconciliation. Idempotent.

    python3 db/build_db.py        # then db/build_referrals.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
from db_build_lib import main

if __name__ == "__main__":
    sys.exit(main(HERE))
