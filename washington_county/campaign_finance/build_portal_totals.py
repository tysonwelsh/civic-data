#!/usr/bin/env python3
"""Transcribe the dollar totals the COUNTY ITSELF printed on its 2008-2010 clerk pages.

This is NOT a parse of any filing and NOT the SCHEMA.md structured money layer.  It is a
verbatim transcription of a second, INDEPENDENT statement of the same figures: the
`clerk/campaignReporting.php` pages rendered each candidate's submitted totals in HTML
right above the links to that candidate's Contribution/Expenditure PDFs.  Because every
county PDF is a handwritten scan (see CLAUDE.md), these portal figures are the only
machine-readable dollar amounts that exist for the 2008 cycle -- and they are the
reconciliation anchor a future vision pass should be scored against.

Input : batch/portal_captures/*.html  (archived captures, provenance in captures.csv)
Output: portal_stated_totals.csv      (COUNTY OFFICES only; school board ledgered elsewhere)
"""
import csv
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CAPS = os.path.join(ROOT, "batch", "portal_captures")
OUT_OF_SCOPE = re.compile(r"school", re.I)
MONEY = re.compile(r"(Contributions|Expenditures|Balance)\s*:?\s*\$?([\d,]+\.?\d*)")


def main():
    caps = json.load(open(os.path.join(CAPS, "captures.json")))
    rows, seen = [], set()
    for cap in caps:
        path = os.path.join(CAPS, cap["file"])
        if not os.path.exists(path):
            continue
        h = open(path, encoding="utf-8", errors="replace").read()
        i = h.find("FINANCIAL CAMPAIGN REPORTS")
        seg = h[i:] if i >= 0 else h
        seg = re.sub(r'<a [^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                     lambda m: f"\x01{m.group(1)}\x02", seg, flags=re.S)
        seg = re.sub(r"</?(tr|p|div|li|h[1-6]|td|th|table|br)[^>]*>", "\n", seg)
        seg = re.sub(r"<[^>]+>", " ", seg)
        seg = html.unescape(seg)
        lines = [re.sub(r"[ \t]+", " ", x).strip() for x in seg.split("\n")]
        lines = [x for x in lines if x]
        for k, line in enumerate(lines):
            if not line.startswith("Submitted:"):
                continue
            name = lines[k - 3] if k >= 3 else ""
            office = lines[k - 2] if k >= 2 else ""
            year = lines[k - 1] if k >= 1 else ""
            if OUT_OF_SCOPE.search(office):
                continue
            blk = " ".join(lines[k:k + 16])
            amts = MONEY.findall(blk)[:6]          # this candidate's OWN two trios only
            if len(amts) < 6:
                continue
            vals = [a[1].replace(",", "") for a in amts]
            links = [u for u in re.findall(r"\x01([^\x02]*)\x02", " ".join(lines[k:k + 18]))
                     if u.lower().endswith(".pdf")]
            key = (name, office, line, tuple(vals))
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(
                candidate=name, portal_office=office, reporting_year=year,
                submitted=line.replace("Submitted:", "").strip(),
                stated_contributions=vals[0], stated_expenditures=vals[1],
                stated_balance=vals[2],
                convention_contributions=vals[3], convention_expenditures=vals[4],
                convention_balance=vals[5],
                detail_pdfs=" ; ".join(links),
                source_url=cap["url"], wayback_timestamp=cap["timestamp"],
                capture_file=f"batch/portal_captures/{cap['file']}",
                basis="VERBATIM from the county's own rendered page - NOT parsed from any filing",
            ))
    rows.sort(key=lambda r: (r["candidate"], r["submitted"]))
    with open(os.path.join(ROOT, "portal_stated_totals.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"portal_stated_totals.csv: {len(rows)} county-office filing snapshots")


if __name__ == "__main__":
    sys.exit(main())
