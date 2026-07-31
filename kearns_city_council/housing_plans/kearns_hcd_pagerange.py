#!/usr/bin/env python3
"""Locate Kearns's page range inside a statewide HCD compilation PDF and extract a
clean text sidecar. Kearns-specific helper for the housing_plans dataset (kept
in-folder per the standing rule). Kearns reports as "Kearns" and/or "Kearns Metro
Township"; alphabetical neighbors are Kanab/Kaysville (before) and
Kingston/LaVerkin/Layton (after). Usage:

    python3 kearns_hcd_pagerange.py raw/hcd-23reports.pdf            # scan/report
    python3 kearns_hcd_pagerange.py raw/hcd-23reports.pdf text/kearns-2023.txt <start0> <end0>
"""
import sys, fitz

TARGET = "kearns"

def main():
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    d = fitz.open(pdf)
    if out and len(sys.argv) > 4:
        start, end = int(sys.argv[3]), int(sys.argv[4])
        txt = [d.load_page(i).get_text("text") for i in range(start, end + 1)]
        with open(out, "w") as f:
            f.write("\f".join(txt))
        print(f"wrote {out} (0-based {start}..{end}, {end-start+1} pages)")
        return
    hits = []
    for i in range(d.page_count):
        t = d.load_page(i).get_text("text").lower()
        n = t.count(TARGET)
        if n:
            hits.append((i, n))
    if not hits:
        print("NO Kearns pages found in", pdf)
        return
    print(f"{pdf}: {d.page_count} pages; pages mentioning 'kearns' (0-based):")
    for i, n in hits:
        print(f"  page {i} (1-based {i+1}): {n} mentions")

if __name__ == "__main__":
    main()
