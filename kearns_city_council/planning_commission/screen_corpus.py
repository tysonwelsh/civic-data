#!/usr/bin/env python3
"""
screen_corpus.py — corpus-screen gate for a Kearns minutes dataset (meeting_minutes/
or planning_commission/). Anomaly-screens every markdown file in minutes/ against its
own statistical baseline to catch extraction failures BEFORE the data is trusted:

  * STUB       — body (post-header) < 200 bytes -> re-OCR / wrong-doc candidate.
  * LOW-ALPHA  — alphabetic ratio < 0.50 (garbled OCR / encoding failure).
  * SHORT      — body char-length < 25% of the dataset's per-year median (informational).
  * NO-VOTE    — substantial doc with no motion/vote grammar (work session; informational).

Exit 0 = clean; exit 1 = STUB / LOW-ALPHA anomalies needing action.
"""
import os, re, statistics, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN = os.path.join(ROOT, "minutes")
BODY = os.path.basename(ROOT)

def body_text(md):
    parts = md.split("\n\n---\n\n", 2)
    return parts[2] if len(parts) > 2 else (md.split("---", 1)[1] if "---" in md else md)

def main():
    per_year = defaultdict(list); files = []
    for dp, _, fns in os.walk(MIN):
        for fn in fns:
            if fn.endswith(".md"):
                raw = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
                bt = body_text(raw)
                files.append((fn, bt)); per_year[fn[:4]].append(len(bt))
    med = {y: statistics.median(v) for y, v in per_year.items()}
    stubs, lowalpha, shorts, novote = [], [], [], []
    for fn, bt in files:
        n = len(bt.strip())
        if n < 200:
            stubs.append((fn, n)); continue
        alpha = sum(c.isalpha() or c.isspace() for c in bt) / max(len(bt), 1)
        if alpha < 0.50:
            lowalpha.append((fn, round(alpha, 2)))
        if n < 0.25 * med[fn[:4]]:
            shorts.append((fn, n, int(med[fn[:4]])))
        if n > 1500 and not re.search(r"moved|motion|vote|second|unanimous", bt, re.I):
            novote.append(fn)
    print(f"=== {BODY} corpus screen: {len(files)} files, {len(per_year)} years ===")
    print("per-year median body length: "
          + ", ".join(f"{y}:{int(med[y])}" for y in sorted(med)))
    print(f"STUB(<200B): {len(stubs)}  LOW-ALPHA(<0.50): {len(lowalpha)}  "
          f"SHORT(<25% yr median): {len(shorts)}  NO-VOTE-KEYWORD: {len(novote)}")
    for label, rows in [("STUB", stubs), ("LOW-ALPHA", lowalpha),
                        ("SHORT (informational)", shorts),
                        ("NO-VOTE (informational)", novote)]:
        if rows:
            print(f"-- {label} --")
            for r in rows:
                print("   ", r)
    critical = bool(stubs or lowalpha)
    print("SCREEN:", "FIXED/CLEAN" if not critical else "NEEDS RE-OCR")
    return 1 if critical else 0

if __name__ == "__main__":
    sys.exit(main())
