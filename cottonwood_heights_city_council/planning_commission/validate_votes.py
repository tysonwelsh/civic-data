#!/usr/bin/env python3
"""Validate Cottonwood Heights PLANNING COMMISSION vote JSONs + (re)build roster.csv.
5-7 seated Commissioners (Chair is a voting Commissioner); no Mayor.
Run: python3 validate_votes.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ch_validate  # noqa: E402
from extract_votes import ROSTER  # noqa: E402

if __name__ == "__main__":
    # CH PC seated up to 8 (7 commissioners + chair/alternate; confirmed by a printed
    # "7-to-1" = 8 real named voters in 2021), so >8 is the true anomaly threshold.
    ch_validate.run(Path(__file__).resolve().parent, set(ROSTER.values()), set(),
                    seat_max=8, seat_label="Commissioner")
