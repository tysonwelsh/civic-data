#!/usr/bin/env python3
"""Find physical pages containing a search string in a PDF (city-boundary bracketing).

Usage: find_city_boundary.py <pdf> <start> <end> <needle> [needle2 ...]
Prints each physical page in [start,end] whose text contains any needle (case-insensitive).
Helper for state-compilation excerpt bracketing; kept in-dataset per build rules.
"""
import subprocess, sys

pdf, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
needles = [n.lower() for n in sys.argv[4:]]
for p in range(start, end + 1):
    txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"],
                         capture_output=True, text=True).stdout.lower()
    hits = [n for n in needles if n in txt]
    if hits:
        print(f"[p{p}] hits: {hits}")
