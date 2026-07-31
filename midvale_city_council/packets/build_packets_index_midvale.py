#!/usr/bin/env python3
"""Harvest Midvale agenda-packet links from the two flat Revize landing pages
(council recorder page + P&Z page), parse date/body, resolve bare-relative paths,
and emit a candidate list for size-probing. Midvale-unique filename to avoid the
shared-scratchpad collision (six same-city agents run concurrently)."""
import re, os, json, csv
from urllib.parse import quote

BASE = "https://www.midvale.utah.gov/"
HERE = os.path.dirname(os.path.abspath(__file__))

MONTHS = {}

def parse_date(fname):
    """Extract a meeting date from a packet filename. Returns ISO or None."""
    stem = fname
    # 2025.04.23 PC Packet.pdf  -> YYYY.MM.DD
    m = re.search(r'(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})', stem)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    # CC Packet 7-7-2026.pdf / PC Packet - 3-25-2026.pdf -> M-D-YYYY
    m = re.search(r'(\d{1,2})[.\-](\d{1,2})[.\-](20\d{2})', stem)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    # CC Packet 10102017.pdf -> MMDDYYYY
    m = re.search(r'(\d{2})(\d{2})(20\d{2})', stem)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return None

def harvest(html_path):
    html = open(html_path, encoding="utf-8", errors="replace").read()
    links = re.findall(r'href="([^"]+)"', html, re.I)
    out = []
    for l in links:
        raw = l.split("#")[0]
        # drop cache-buster token
        raw_notoken = raw.split("?")[0]
        if not re.search(r'packet', raw_notoken, re.I):
            continue
        if not raw_notoken.lower().endswith(".pdf"):
            continue
        out.append(raw_notoken)
    return out

def resolve(rel, body_year_hint=None):
    """Return (full_path_unencoded, was_bare). full path relative to site root."""
    if rel.startswith("Document Center/"):
        return rel, False
    # bare-relative: resolve to canonical Document Center/<body-folder>/<YEAR>/Packets/<file>
    return rel, True  # caller builds candidates

def main():
    rows = []
    for html_path, body, folder, prefix in [
        (os.path.join(HERE, "raw", "council_landing.html"), "Council",
         "Recorders Office", "CC"),
        (os.path.join(HERE, "raw", "pc_landing.html"), "PC",
         "Planning & Zoning Commission", "PC"),
    ]:
        seen = set()
        for rel in harvest(html_path):
            fname = os.path.basename(rel)
            date = parse_date(fname)
            if not date:
                continue
            year = int(date[:4])
            if year < 2020:
                continue
            key = (body, date, fname)
            if key in seen:
                continue
            seen.add(key)
            full, bare = resolve(rel)
            rows.append({
                "body": body, "date": date, "year": year,
                "fname": fname, "rel": rel, "bare": bare,
                "folder": folder,
            })
    # de-dup by (body,date) keeping first; but log multiples
    print(f"harvested {len(rows)} packet links (2020+)")
    from collections import Counter
    byb = Counter((r["body"], r["year"]) for r in rows)
    for k in sorted(byb):
        print("  ", k, byb[k])
    print("bare-relative count:", sum(1 for r in rows if r["bare"]))
    for r in rows:
        if r["bare"]:
            print("   BARE:", r["body"], r["date"], r["rel"])
    # dump for the probe step
    with open(os.path.join(HERE, "_harvest.json"), "w") as f:
        json.dump(rows, f, indent=1)

if __name__ == "__main__":
    main()
