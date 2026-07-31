#!/usr/bin/env python3
"""Cross-body referral build — thin stub (REFACTOR_PLAN 4.2).

Shared logic lives in scripts/referrals_lib.py (repo root). Idempotent; run AFTER
build_db.py:  python3 db/build_referrals.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main

if __name__ == "__main__":
    # SLC stopwords (T1.4, 2026-07-12): "design review" is a generic PC final-action label
    # here (69 PC apps carry it) — as subject tokens it chain-linked the Council's Design
    # Review STANDARDS text amendment to unrelated per-project PC design reviews (2 FPs
    # suppressed in referral_overrides.csv before root-causing). Removing the tokens from
    # subject scoring kills the class; genuinely related items still share their
    # distinctive project/ordinance tokens.
    sys.exit(main(HERE, extra_stopwords=("design", "review")))
