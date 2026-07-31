#!/usr/bin/env python3
"""Locate White City's page range inside a statewide HCD compilation PDF and
extract a clean text sidecar. White-City-specific helper for the housing_plans
dataset (kept in-folder per the standing rule). Usage:

    python3 wc_hcd_pagerange.py raw/hcd-23reports.pdf            # report page span
    python3 wc_hcd_pagerange.py raw/hcd-23reports.pdf text/white_city-2023.txt
"""
import sys, fitz

TARGET = "white city"

def main():
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    d = fitz.open(pdf)
    hits = []
    for i in range(d.page_count):
        t = d.load_page(i).get_text("text")
        low = t.lower()
        # a page is "White City's" if White City dominates and no other city header.
        n = low.count(TARGET)
        if n:
            hits.append((i, n))
    if not hits:
        print("NO White City pages found in", pdf)
        return
    pages = [h[0] for h in hits]
    # Contiguous run(s): report the min..max but also print per-page counts so a
    # stray single mention (index/TOC) can be excluded by eye.
    print(f"{pdf}: pages with 'white city' (0-based): {pages}")
    for i, n in hits:
        print(f"  page {i} (1-based {i+1}): {n} mentions")
    # Heuristic body range = pages where count>=2 (a real report section), contiguous.
    body = [i for i, n in hits if n >= 2]
    if body:
        start, end = min(body), max(body)
        print(f"  => body range 0-based {start}..{end}  (1-based {start+1}..{end+1})")
        if out:
            txt = []
            for i in range(start, end + 1):
                txt.append(d.load_page(i).get_text("text"))
            with open(out, "w") as f:
                f.write("\f".join(txt))
            print(f"  wrote {out} ({end-start+1} pages)")

if __name__ == "__main__":
    main()
