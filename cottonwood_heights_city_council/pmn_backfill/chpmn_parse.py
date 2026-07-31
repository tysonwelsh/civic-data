#!/usr/bin/env python3
"""Parse Cottonwood Heights PMN cumulative notices HTML (_work/notices_<body>.html) into
per-attachment rows. Filename comes from the anchor aria-label (full, untruncated).
Minutes detection is FILENAME-based (NOT the PMN type label — labels mislabel/undercount).
Writes _work/attachments_all.csv."""
import re, csv, os

BODIES = {
    "2147": "City Council", "2148": "Planning Commission",
    "2150": "Architectural Review Commission", "3085": "Board of Adjustments",
    "3287": "Administrative Hearings", "6511": "Parks Trails & Open Spaces Committee",
    "7091": "Appeals Hearing Officer", "8699": "Health in the Heights Coalition",
    "9027": "Historic Committee", "9035": "Arts Council", "9491": "Citizen Budget Committee",
}
HERE = os.path.dirname(__file__)
WORK = os.path.join(HERE, "_work")

ROW_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
NOTICE_RE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html"[^>]*>([^<]*)</a>')
DATE_RE = re.compile(r'(\d{4}/\d{2}/\d{2})\s+[\d:]+\s*[AP]M')
# attachment: file id + full filename from aria-label (strip " (opens in new window)")
ATT_RE = re.compile(r'/pmn/files/(\d+)\.pdf"[^>]*aria-label="Download ([^"]+?)(?: \(opens in new window\))?"', re.S)

def minutes_like(fn):
    f = fn.lower()
    if "agenda" in f and "minute" not in f:
        return False
    return ("minute" in f) or bool(re.search(r'\bmin(s)?\b', f))

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
            fid, fn = am.group(1), am.group(2).strip()
            rows.append(dict(body=body, body_name=BODIES.get(body, body),
                             event_date=edate, notice_id=notice_id, title=title,
                             file_id=fid, filename=fn, minutes_like=minutes_like(fn)))
    return rows

def main():
    allrows = []
    for b in BODIES:
        allrows += parse(b)
    out = os.path.join(WORK, "attachments_all.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["body", "body_name", "event_date", "notice_id",
                                          "title", "file_id", "filename", "minutes_like"])
        w.writeheader()
        for r in allrows:
            w.writerow(r)
    print(f"total attachments: {len(allrows)}")
    for b in BODIES:
        br = [r for r in allrows if r["body"] == b]
        ml = [r for r in br if r["minutes_like"]]
        if br:
            print(f"  {b} {BODIES[b]}: {len(br)} attach, {len(ml)} minutes-like filenames")
    print("wrote", out)

if __name__ == "__main__":
    main()
