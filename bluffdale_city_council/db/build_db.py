#!/usr/bin/env python3
"""build_db.py — thin driver over scripts/db_build_lib.py (Council + RDA + LBA +
PlanningCommission). Idempotent.  python3 db/build_db.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
from db_build_lib import main
if __name__ == "__main__":
    sys.exit(main(HERE))
