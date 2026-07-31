#!/usr/bin/env python3
"""
screen_corpus.py — MANDATORY corpus-screen gate for a Holladay minutes dataset
(meeting_minutes/ or planning_commission/). Anomaly-screens every markdown file in
minutes/ against its own statistical baseline to catch extraction failures BEFORE the
data is trusted:

  * STUB      — body (post-header) < 200 bytes  -> re-OCR candidate.
  * SHORT     — body char-length < 25% of the dataset's per-year median.
  * LOW-ALPHA — alphabetic ratio < 0.55 (garbled OCR / encoding failure).
  * NO-VOTE-KEYWORD in a substantial doc — no motion/vote grammar at all (usually a
    work session or special meeting; listed, not failed).

Exit 0 = clean; exit 1 = anomalies needing action (stubs / low-alpha). SHORT / no-vote
are informational (Holladay work sessions are legitimately short & vote-free).
"""
import os, re, statistics, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN = os.path.join(ROOT, "minutes")
BODY = os.path.basename(ROOT)

def body_text(md):
    return md.split("---", 1)[1] if "---" in md else md

def main():
    per_year = defaultdict(list)
    files = []
    for dp, _, fns in os.walk(MIN):
        for fn in fns:
            if fn.endswith(".md"):
                p = os.path.join(dp, fn)
                raw = open(p, encoding="utf-8", errors="replace").read()
                bt = body_text(raw)
                year = fn[:4]
                files.append((p, fn, bt))
                per_year[year].append(len(bt))
    med = {y: statistics.median(v) for y, v in per_year.items()}
    stubs, shorts, lowalpha, novote = [], [], [], []
    for p, fn, bt in files:
        year = fn[:4]
        n = len(bt.strip())
        if n < 200:
            stubs.append((fn, n)); continue
        alpha = sum(c.isalpha() or c.isspace() for c in bt) / max(len(bt), 1)
        if alpha < 0.55:
            lowalpha.append((fn, round(alpha, 2)))
        if n < 0.25 * med[year]:
            shorts.append((fn, n, int(med[year])))
        if n > 1500 and not re.search(r"moved|motion|vote|second|unanimous", bt, re.I):
            novote.append(fn)
    print(f"=== {BODY} corpus screen: {len(files)} files, {len(per_year)} years ===")
    print(f"per-year median body length: "
          + ", ".join(f"{y}:{int(med[y])}" for y in sorted(med)))
    print(f"STUB(<200B): {len(stubs)}  LOW-ALPHA(<0.55): {len(lowalpha)}  "
          f"SHORT(<25% yr median): {len(shorts)}  NO-VOTE-KEYWORD: {len(novote)}")
    for label, rows in [("STUB", stubs), ("LOW-ALPHA", lowalpha),
                        ("SHORT (informational)", shorts), ("NO-VOTE (informational)", novote)]:
        if rows:
            print(f"-- {label} --")
            for r in rows:
                print("   ", r)
    critical = bool(stubs or lowalpha)
    print("SCREEN:", "FIXED/CLEAN" if not critical else "NEEDS RE-OCR")
    return 1 if critical else 0

if __name__ == "__main__":
    sys.exit(main())
