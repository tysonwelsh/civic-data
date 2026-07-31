#!/usr/bin/env python3
"""
Corpus-screen gate (MANDATORY, both bodies). Fails loudly on silent scanned stubs.

For each body it walks minutes_index.csv and, for every markdown, measures the BODY text
length (bytes after the provenance header). It reports:
  * STUBS: any doc whose body text < 200 bytes  (a scan that never OCR'd / an empty convert).
  * per-YEAR text-length stats (count, min, median) so a year of thin/garbled docs surfaces
    against its own baseline.
  * format tallies (text vs ocr) from the index.
Exit code 1 if any stub is found, so a build cannot silently ship empty minutes.

Run:  python3 scripts_screen_corpus.py
"""
import csv, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
BODIES = {"City Council": REPO / "meeting_minutes",
          "Planning Commission": REPO / "planning_commission"}
STUB_BYTES = 200


def body_len(md):
    txt = md.read_text(encoding="utf-8", errors="replace")
    parts = txt.split("\n---\n", 1)
    return len(parts[1].strip()) if len(parts) == 2 else len(txt.strip())


def screen(label, ddir, out):
    idx = ddir / "minutes_index.csv"
    if not idx.exists():
        out.append(f"[{label}] NO minutes_index.csv"); return 0, 0
    rows = list(csv.DictReader(idx.open()))
    by_year = {}
    fmt = {}
    stubs = []
    for r in rows:
        fmt[r["format"]] = fmt.get(r["format"], 0) + 1
        md = ddir / r["path"]
        n = body_len(md) if md.exists() else 0
        by_year.setdefault(r["year"], []).append(n)
        if n < STUB_BYTES:
            stubs.append((r["date"], r["path"], n, r["format"]))
    out.append(f"\n===== {label} =====")
    out.append(f"docs: {len(rows)}   formats: {fmt}")
    out.append(f"{'year':6} {'n':>4} {'min':>7} {'median':>8}")
    for y in sorted(by_year):
        v = by_year[y]
        out.append(f"{y:6} {len(v):>4} {min(v):>7} {int(statistics.median(v)):>8}")
    out.append(f"STUBS (<{STUB_BYTES}B body): {len(stubs)}")
    for d, p, n, f in stubs:
        out.append(f"   STUB {d} {n}B [{f}] {p}")
    return len(rows), len(stubs)


def main():
    out = ["Midvale corpus screen (stub<200B + per-year length baseline)",
           "=" * 62]
    total_stubs = 0
    for label, ddir in BODIES.items():
        _, s = screen(label, ddir, out)
        total_stubs += s
    text = "\n".join(out)
    print(text)
    (REPO / "CORPUS_SCREEN.txt").write_text(text + f"\n\nTOTAL STUBS: {total_stubs}\n")
    if total_stubs:
        print(f"\nSCREEN FAIL: {total_stubs} stub(s)", file=sys.stderr)
        sys.exit(1)
    print("\nSCREEN PASS: no stubs")


if __name__ == "__main__":
    main()
