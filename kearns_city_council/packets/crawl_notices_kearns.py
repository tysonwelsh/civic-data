#!/usr/bin/env python3
"""
Kearns packets crawler — enumerate every notice on a PMN public body from the
CUMULATIVE list view (a single high-page GET returns the body's full notice
history; the body page + 6-month list otherwise hide older notices), parse each
notice row's event date, title, and ALL attachments (file id, ext, filename),
and classify each attachment as PACKET (keep) / AGENDA / MINUTES / AUDIO / OTHER.

GET-only, polite. Writes _candidates_<body>.csv (one row per attachment) so a
human/Claude can review the classification before any download.

Council packet  = PMN body 5823, filename ~ "... Supporting Documents ...",
                  "... Meeting Packet ...", "... Agenda Packet ...".
PC packet/staff = PMN body 1561, filename ~ "... Packet ...", "... Staff Report ...".

Usage: python3 crawl_notices_kearns.py 5823 Council
       python3 crawl_notices_kearns.py 1561 PC
"""
import csv
import os
import re
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive")
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def classify(name, body):
    n = name.lower()
    if n.endswith(".mp3") or "audio" in n:
        return "AUDIO"
    if "minute" in n:
        return "MINUTES"
    if "cancel" in n:
        return "CANCELLED"
    # staff analysis packaged for the meeting
    if "staff report" in n or "staffreport" in n or "staff_report" in n:
        return "STAFF_REPORT"
    # bundled packet: "Supporting Documents", "... Packet ..." (incl. KearnsPC_Packet)
    if "supporting document" in n or "packet" in n:
        return "PACKET"
    if "meeting schedule" in n:
        return "SCHEDULE"
    if "agenda" in n:
        return "AGENDA"
    if "notice of public" in n or "public hearing notice" in n or "hearing notice" in n:
        return "NOTICE"
    return "OTHER"


def parse(html):
    """Yield (notice_id, event_date 'YYYY-MM-DD', title, [(fid,ext,fname),...])."""
    # split into notice rows: each row starts at a notice link
    rows = re.split(r'(?=<a href="/pmn/sitemap/notice/\d+\.html">)', html)
    for row in rows:
        m = re.search(r'/pmn/sitemap/notice/(\d+)\.html">([^<]*)</a>', row)
        if not m:
            continue
        nid, title = m.group(1), m.group(2).strip()
        dm = re.search(r'(\d{4})/(\d{2})/(\d{2})', row)
        date = f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}" if dm else ""
        atts = []
        for a in re.finditer(r'/pmn/files/(\d+)\.(pdf|docx|mp3)', row):
            fid, ext = a.group(1), a.group(2)
            seg = row[a.start():a.start() + 500]
            lt = re.search(r'>\s*([^<>]+?\.(?:pdf|docx|mp3))\s*</a>', seg, re.I)
            al = re.search(r'aria-label="Download ([^"]+?) \(opens', seg)
            fname = (lt.group(1) if lt else (al.group(1) if al else "")).strip()
            atts.append((fid, ext, fname))
        yield nid, date, title, atts


def main():
    body = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else body
    html = get(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page=400")
    time.sleep(1)
    out = os.path.join(HERE, f"_candidates_{body}.csv")
    n_notices = n_att = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["body_label", "pmn_body_id", "notice_id", "event_date",
                    "notice_title", "file_id", "ext", "filename", "class"])
        for nid, date, title, atts in parse(html):
            n_notices += 1
            for fid, ext, fname in atts:
                n_att += 1
                w.writerow([label, body, nid, date, title, fid, ext, fname,
                            classify(fname, body)])
    print(f"body {body} ({label}): {n_notices} notices, {n_att} attachments -> {out}")


if __name__ == "__main__":
    main()
