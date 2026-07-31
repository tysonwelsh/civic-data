#!/usr/bin/env python3
"""Kearns weekly-bundle build — thin stub over scripts/weeks_lib.py."""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent / "scripts"))
from weeks_lib import build
if __name__ == "__main__":
    build(BASE, city_name='Kearns', meeting_weekday=0)
