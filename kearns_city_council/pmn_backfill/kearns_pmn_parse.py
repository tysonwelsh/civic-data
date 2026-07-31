#!/usr/bin/env python3
"""Kearns pmn_backfill helper: parse a PMN notices-list HTML into rows of
(notice_id, event_date, notice_title, [(file_url, filename, label)...]).
GET-only artifacts already fetched via polite_fetch.py live in work/.
Usage: python3 kearns_pmn_parse.py work/<notices>.html
"""
import re, sys, json, html

def parse_notices(path):
    d = open(path, encoding="utf-8", errors="replace").read()
    # split into <tr ...> ... </tr> rows within tbody
    rows = []
    # Each notice row starts with a notice link
    # Use a robust split on '/pmn/sitemap/notice/'
    parts = re.split(r'(<tr[^>]*>)', d)
    # simpler: find each row block by notice anchor
    for m in re.finditer(
        r'<a href="/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>.*?'
        r'<td>\s*(\d{4}/\d{2}/\d{2}[^<]*)</td>(.*?)(?=<a href="/pmn/sitemap/notice/|</tbody>)',
        d, re.S):
        nid, title, evdate, attblock = m.groups()
        title = html.unescape(re.sub(r'\s+', ' ', title)).strip()
        evdate = evdate.strip()
        atts = []
        for a in re.finditer(
            r'<a href="/pmn/files/([^"]+)"[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\s*(?:\(([^)]*)\))?',
            attblock):
            fid_ext, fname, label = a.groups()
            atts.append({
                "file": fid_ext.strip(),
                "filename": html.unescape(fname).strip(),
                "label": (label or "").strip(),
            })
        rows.append({
            "notice_id": nid,
            "title": title,
            "event_date": evdate,
            "attachments": atts,
        })
    return rows

if __name__ == "__main__":
    rows = parse_notices(sys.argv[1])
    print(json.dumps(rows, indent=2))
    print(f"\n# {len(rows)} notices parsed", file=sys.stderr)
