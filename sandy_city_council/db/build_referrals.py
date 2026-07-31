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
    sys.exit(main(HERE))
