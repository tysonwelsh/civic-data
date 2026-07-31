#!/usr/bin/env python3
"""White City PMN notice-list parser (pmn_backfill helper).

Parses a saved /pmn/list/notices.html?id=<body>&page=N page into rows of
(notice_id, event_date, title, [ (file_id, filename, type_label), ... ]).
GET-only artifacts already fetched via polite_fetch.py. Unique name per standing rule.
"""
import re, sys, json, csv

def parse(path):
    html = open(path, encoding="utf-8", errors="replace").read()
    # split into <tr ...> ... </tr> blocks inside tbody
    tbody = html.split("<tbody>", 1)[-1].split("</tbody>", 1)[0]
    rows = re.split(r'<tr[^>]*>', tbody)
    out = []
    for r in rows:
        nm = re.search(r'/pmn/sitemap/notice/(\d+)\.html">([^<]*)</a>', r)
        if not nm:
            continue
        notice_id = nm.group(1)
        title = nm.group(2).strip()
        dm = re.search(r'<td>\s*(\d{4}/\d{2}/\d{2})[^<]*</td>', r)
        date = dm.group(1).replace("/", "-") if dm else ""
        atts = []
        for am in re.finditer(
            r'/pmn/files/(\d+)\.(pdf|PDF|docx?|DOCX?)"[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\s*(?:\(([^)]*)\))?',
            r):
            fid, ext, fname, label = am.group(1), am.group(2), am.group(3).strip(), (am.group(4) or "").strip()
            # attempt to grab the parenthetical type label that follows on next lines
            if not label:
                after = r[am.end():am.end()+200]
                lm = re.search(r'\(([^)]{2,40})\)', after)
                label = lm.group(1).strip() if lm else ""
            atts.append({"file_id": fid, "ext": ext.lower(), "filename": fname, "label": label})
        out.append({"notice_id": notice_id, "date": date, "title": title, "attachments": atts})
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        rows = parse(p)
        print(f"### {p}: {len(rows)} notices")
        for row in rows:
            labels = ",".join(a["label"] for a in row["attachments"])
            print(json.dumps(row))
