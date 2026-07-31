#!/usr/bin/env python3
"""Draper weekly-bundle build — thin config stub (REFACTOR_PLAN 4.1).

Shared logic lives in scripts/weeks_lib.py. Derived + regenerable.
Usage:  python3 build_weeks.py
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent / "scripts"))
from weeks_lib import build

if __name__ == "__main__":
    build(BASE, city_name='Draper', meeting_weekday=1)
