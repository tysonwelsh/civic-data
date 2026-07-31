#!/usr/bin/env python3
"""build_packets_index_wc.py — harvest White City council/PC agenda PACKET anchors
from the Streamline site HTML (already fetched into packets/html/) and emit a
candidate list of packet documents to fetch.

White City Streamline exposes two page layouts:
  * per-year council pages /council-meeting?year=YYYY  (2022-2026) — anchors carry an
    aria-label "<file> attachment for <ISO-date> Council Meeting <full title>".
  * /meetings-archive (2019-2021 packets) — anchors carry NO aria-label; the date lives
    in the inner <span> text, e.g. "Council Meeting Packet 1.7.2021".

A PACKET is any anchor whose filename OR label contains 'packet' (case-insensitive),
excluding agenda/minutes docs. General-plan element PDFs and the standalone General Plan
are NOT packets and are excluded.

Emits packets/_candidates.csv: date,body,meeting_type,packet_kind,title,filename,url
Run:  python3 build_packets_index_wc.py
"""
import csv
import html as htmllib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(HERE, "html")
BASE = "https://whitecity.utah.gov"

ANCHOR_RE = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.DOTALL | re.IGNORECASE)
HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
ARIA_RE = re.compile(r'aria-label="([^"]*)"', re.IGNORECASE)
TAG_RE = re.compile(r'<[^>]+>')
ATTACH_RE = re.compile(r'attachment for (\d{4}-\d{2}-\d{2})\s+(.*)$')
# date like 1.7.2021 or 11.18.2021 in archive span text
DOTDATE_RE = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')


def norm_date(m, d, y):
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def classify_body(title):
    t = title.lower()
    if "planning commission" in t:
        return "PlanningCommission"
    if "board of canvass" in t or "canvass" in t:
        return "Council"  # canvass is a council function
    return "Council"


def classify_meeting_type(title):
    t = title.lower()
    if "special" in t:
        return "Special"
    if "workshop" in t or "retreat" in t:
        return "Workshop"
    if "canvass" in t:
        return "Canvass"
    return "Regular"


def is_packet(fname, label):
    s = (fname + " " + label).lower()
    if "packet" not in s:
        return False
    # exclude decoys that merely contain 'packet' in a general-plan filename? none here
    return True


def parse_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        htmltext = f.read()
    rows = []
    for attrs, inner in ANCHOR_RE.findall(htmltext):
        hm = HREF_RE.search(attrs)
        if not hm:
            continue
        href = hm.group(1)
        if "/files/" not in href:
            continue
        # only same-host cloudfront docs (skip specialdistrict general-plan mirror)
        if href.startswith("http") and "whitecity.utah.gov" not in href:
            continue
        fname = href.rsplit("/", 1)[-1]
        fname_dec = htmllib.unescape(fname).replace("+", " ")
        aria = ARIA_RE.search(attrs)
        inner_text = htmllib.unescape(TAG_RE.sub("", inner)).strip()
        label = htmllib.unescape(aria.group(1)) if aria else inner_text
        if not is_packet(fname_dec, label):
            continue
        # determine date + title
        date = None
        title = label
        am = ATTACH_RE.search(label)
        if am:
            date = am.group(1)
            title = am.group(2).strip()
        else:
            dm = DOTDATE_RE.search(label) or DOTDATE_RE.search(fname_dec)
            if dm:
                date = norm_date(dm.group(1), dm.group(2), dm.group(3))
            title = inner_text
        if not date:
            # last resort: date in filename like 12-7-2023 or 5.7.2020
            dm = re.search(r'(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})', fname_dec)
            if dm:
                y = dm.group(3)
                if len(y) == 2:
                    y = "20" + y
                date = norm_date(dm.group(1), dm.group(2), y)
        url = href if href.startswith("http") else BASE + href
        rows.append({
            "date": date or "",
            "body": classify_body(title),
            "meeting_type": classify_meeting_type(title),
            "packet_kind": "full_packet",
            "title": title,
            "filename": fname_dec,
            "url": url,
        })
    return rows


def main():
    seen = {}  # url -> row (dedup)
    files = ([os.path.join(HTML_DIR, f"council_{y}.html") for y in range(2022, 2027)]
             + [os.path.join(HTML_DIR, "meetings_archive.html")])
    for fp in files:
        if not os.path.exists(fp):
            continue
        for r in parse_file(fp):
            key = r["url"]
            if key not in seen:
                seen[key] = r
    rows = sorted(seen.values(), key=lambda r: (r["date"], r["body"], r["filename"]))
    out = os.path.join(HERE, "_candidates.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "body", "meeting_type",
                                          "packet_kind", "title", "filename", "url"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} packet candidates -> {out}")
    from collections import Counter
    yrs = Counter(r["date"][:4] for r in rows)
    bodies = Counter(r["body"] for r in rows)
    print("by year:", dict(sorted(yrs.items())))
    print("by body:", dict(bodies))
    missing = [r for r in rows if not r["date"]]
    if missing:
        print("NO DATE:", len(missing))
        for r in missing:
            print("  ", r["filename"])


if __name__ == "__main__":
    main()
