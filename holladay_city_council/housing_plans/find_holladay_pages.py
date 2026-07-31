#!/usr/bin/env python3
"""Locate Holladay's physical page range inside a state HCD compilation PDF.

Scans each physical page's first ~8 non-empty lines for a city-name header. Prints
the physical page whose header names Holladay and the next-city header after it, so
the reviewer can bracket the excerpt. Helper for the housing_plans state-compilation
extraction; kept in-dataset (not shared scratchpad) per build rules.
"""
import subprocess, sys, re

pdf = sys.argv[1]
start = int(sys.argv[2])
end = int(sys.argv[3])

for p in range(start, end + 1):
    txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"],
                         capture_output=True, text=True).stdout
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    head = " | ".join(lines[:4])
    print(f"[p{p}] {head[:160]}")
