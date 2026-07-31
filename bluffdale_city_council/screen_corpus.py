#!/usr/bin/env python3
"""Corpus-screen gate for both bodies. Flags any markdown whose body text (after the
provenance header) is a stub (<200 chars) — i.e. a silently-failed scan/OCR. Exit 1 if
any stub is found, so the build cannot pass with silent stubs."""
import glob, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUB = 200
flagged = []
counts = {}
for body, d in (("council", "meeting_minutes"), ("pc", "planning_commission")):
    mds = sorted((ROOT / d / "minutes").rglob("*.md"))
    counts[body] = len(mds)
    for md in mds:
        txt = md.read_text(encoding="utf-8", errors="replace")
        body_txt = txt.split("---\n\n", 1)[1] if "---\n\n" in txt else txt
        n = len(body_txt.strip())
        if n < STUB:
            flagged.append((str(md.relative_to(ROOT)), n))

print(f"council md={counts['council']}  pc md={counts['pc']}  screened={sum(counts.values())}")
if flagged:
    print(f"STUBS FOUND ({len(flagged)}):")
    for p, n in flagged:
        print(f"  {n:4d}B  {p}")
    sys.exit(1)
print("SCREEN CLEAN — 0 stubs")
