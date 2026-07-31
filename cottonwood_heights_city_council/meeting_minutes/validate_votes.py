#!/usr/bin/env python3
"""Validate Cottonwood Heights CITY COUNCIL vote JSONs + (re)build roster.csv.
Council roll = 5 (4 districts + the VOTING Mayor). Run: python3 validate_votes.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ch_validate  # noqa: E402
from extract_votes import ROSTER, MAYOR_TOKENS  # noqa: E402

MAYOR_NAMES = {ROSTER[t] for t in MAYOR_TOKENS}
ROSTER_NAMES = set(ROSTER.values())

if __name__ == "__main__":
    ch_validate.run(Path(__file__).resolve().parent, ROSTER_NAMES, MAYOR_NAMES,
                    seat_max=5, seat_label="Council Member")
