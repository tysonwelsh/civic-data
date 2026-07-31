#!/usr/bin/env python3
"""Holladay PMN full-history sweep (source-4 backfill).

For each Holladay PMN public body, parse the cumulative notices list
(/pmn/list/notices.html?id=<body>&page=300 — one GET returns the whole history)
and extract every attachment (file id, filename, type label) with the notice's
event date. Filename embeds the meeting date (MMDDYYYY) — we key on that, NOT the
label. Emits a machine-readable JSONL of all minutes-bearing attachments across
every body, then diffs vs the repo minutes indexes.

GET-only; the HTML is already fetched into _disc/ by polite_fetch.py.
"""
import re, json, csv, sys, os
from datetime import datetime

DISC = os.path.join(os.path.dirname(__file__), "_disc")

BODIES = {
    388: "City Council", 389: "Planning Commission", 791: "Redevelopment Agency (RDA)",
    9331: "Local Building Authority (LBA)", 390: "Board of Adjustments",
    392: "Design Review Board", 4813: "Administrative Appeals", 4823: "Arts Council",
    6055: "Historical Commission", 6211: "Tree Committee", 2398: "Housing Task Force",
    391: "Education Task Force", 7341: "Adopted Ordinances", 6605: "Bids & RFPs",
    8423: "Elections", 9191: "Elections/Board of Canvassers",
}

ROW_RE = re.compile(r'<tr class="(?:on|off)">(.*?)</tr>', re.S)
NOTICE_RE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>', re.S)
DATE_RE = re.compile(r'(\d{4}/\d{2}/\d{2})\s+\d{2}:\d{2}\s+[AP]M')
ATT_RE = re.compile(
    r'/pmn/files/(\d+)\.pdf"[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\s*\(([^)]+)\)', re.S)

# filename date patterns -> normalized YYYY-MM-DD
def date_from_filename(fn):
    # MMDDYYYY e.g. 04162026 or 04-16-2026 or 4.16.26
    m = re.search(r'(\d{1,2})[-_. ]?(\d{1,2})[-_. ]?(20\d{2})', fn)
    if m:
        mo, d, y = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # YYYY-MM-DD
    m = re.search(r'(20\d{2})[-_. ](\d{1,2})[-_. ](\d{1,2})', fn)
    if m:
        y, mo, d = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # MMDDYY (6-digit) e.g. 040121  -> ambiguous; only if surrounded
    m = re.search(r'\b(\d{2})(\d{2})(\d{2})\b', fn)
    if m:
        mo, d, yy = m.groups()
        try:
            return datetime(2000+int(yy), int(mo), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""

def event_date_norm(s):
    try:
        return datetime.strptime(s, "%Y/%m/%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""

def sweep():
    out = []
    for bid, bname in BODIES.items():
        path = os.path.join(DISC, f"notices_{bid}.html")
        if not os.path.exists(path):
            print(f"  MISSING html for body {bid} ({bname})", file=sys.stderr)
            continue
        html = open(path, encoding="utf-8", errors="replace").read()
        n_rows = 0
        for row in ROW_RE.finditer(html):
            block = row.group(1)
            nm = NOTICE_RE.search(block)
            if not nm:
                continue
            n_rows += 1
            notice_id, title = nm.group(1), re.sub(r'\s+', ' ', nm.group(2)).strip()
            dm = DATE_RE.search(block)
            ev_date = event_date_norm(dm.group(1)) if dm else ""
            for am in ATT_RE.finditer(block):
                fid, fn, label = am.group(1), am.group(2).strip(), am.group(3).strip()
                fn_date = date_from_filename(fn)
                out.append({
                    "body_id": bid, "body_name": bname, "notice_id": notice_id,
                    "notice_title": title, "event_date": ev_date,
                    "file_id": fid, "filename": fn, "label": label,
                    "filename_date": fn_date,
                    "meeting_date": fn_date or ev_date,
                })
        print(f"  body {bid:>5} {bname:<34} rows={n_rows}", file=sys.stderr)
    return out

if __name__ == "__main__":
    recs = sweep()
    outp = os.path.join(os.path.dirname(__file__), "_disc", "all_attachments.jsonl")
    with open(outp, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(recs)} attachment records -> {outp}", file=sys.stderr)
