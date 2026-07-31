#!/usr/bin/env python3
"""Parse Midvale PMN cumulative notices HTML (_work/notices_<body>.html) into rows.
Extracts per-attachment: body, event_date, notice_id, notice_url, file_id, filename, type_label.
Filename-based minutes detection (NOT the type label — labels mislabel/undercount)."""
import re, sys, csv, os, json

BODIES = {
    "753": "City Council", "754": "Planning Commission", "756": "Redevelopment Agency",
    "757": "Municipal Building Authority", "755": "Board of Adjustments",
    "9155": "Appeal Authority", "758": "Midvale Community Council",
    "760": "Union Community Council", "9179": "White City Council",
}

WORK = os.path.join(os.path.dirname(__file__), "_work")

# a <tr> block. Notice title/url, event date, then any number of <li> attachments.
ROW_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
NOTICE_RE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html"[^>]*>([^<]*)</a>')
DATE_RE = re.compile(r'(\d{4}/\d{2}/\d{2})\s+[\d:]+\s*[AP]M')
ATT_RE = re.compile(r'/pmn/files/(\d+)\.pdf"[^>]*>([^<]+)</a>\s*(?:&nbsp;\s*\(([^)]*)\))?', re.S)

def minutes_like(fn):
    f = fn.lower()
    return ("minute" in f) or re.search(r'\bmin(s)?\b', f) is not None

def parse(body):
    path = os.path.join(WORK, f"notices_{body}.html")
    if not os.path.exists(path):
        return []
    html = open(path).read()
    rows = []
    for tr in ROW_RE.finditer(html):
        block = tr.group(1)
        nm = NOTICE_RE.search(block)
        if not nm:
            continue
        notice_id, title = nm.group(1), nm.group(2).strip()
        dm = DATE_RE.search(block)
        edate = dm.group(1).replace("/", "-") if dm else ""
        for am in ATT_RE.finditer(block):
            fid, fn, typ = am.group(1), am.group(2).strip(), (am.group(3) or "").strip()
            rows.append(dict(body=body, body_name=BODIES.get(body, body),
                             event_date=edate, notice_id=notice_id, title=title,
                             file_id=fid, filename=fn, type_label=typ,
                             minutes_like=minutes_like(fn)))
    return rows

def main():
    allrows = []
    for b in BODIES:
        allrows += parse(b)
    out = os.path.join(os.path.dirname(__file__), "_work", "attachments_all.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["body","body_name","event_date","notice_id","title","file_id","filename","type_label","minutes_like"])
        w.writeheader()
        for r in allrows:
            w.writerow(r)
    # summary
    from collections import Counter
    print(f"total attachments: {len(allrows)}")
    for b in BODIES:
        br = [r for r in allrows if r["body"]==b]
        ml = [r for r in br if r["minutes_like"]]
        if br:
            print(f"  {b} {BODIES[b]}: {len(br)} attach, {len(ml)} minutes-like filenames")
    print("wrote", out)

if __name__ == "__main__":
    main()
