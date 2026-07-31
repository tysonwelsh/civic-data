#!/usr/bin/env python3
"""Parse the cumulative PMN council-body (2147) notices HTML into a flat list of
attachments, one row per (notice, attachment). Ordinance-adoption PDFs are posted as
attachments on Cottonwood Heights City Council meeting notices (there is no dedicated
PMN "ordinances" body). Idempotent, no network — reads a saved HTML file.

Usage: python3 ch_ord_parse_pmn.py <notices.html> <out.csv>
"""
import csv
import html as htmllib
import re
import sys

NOTICE_RE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>', re.S)
ATTACH_RE = re.compile(
    r'/pmn/files/(\d+)\.pdf"[^>]*>(.*?)</a>.*?&nbsp;\((.*?)\)', re.S)
DATE_RE = re.compile(r'<td>(\d{4}/\d{2}/\d{2}[^<]*)</td>')


def parse(html):
    """Split on notice rows; for each notice collect its attachments (in the same <tr>)."""
    rows = []
    # Each notice begins at a sitemap/notice anchor. Slice the doc into notice segments.
    anchors = list(NOTICE_RE.finditer(html))
    for idx, m in enumerate(anchors):
        nid = m.group(1)
        ntitle = htmllib.unescape(re.sub(r'\s+', ' ', m.group(2)).strip())
        seg_start = m.end()
        seg_end = anchors[idx + 1].start() if idx + 1 < len(anchors) else len(html)
        seg = html[seg_start:seg_end]
        dm = DATE_RE.search(seg)
        edate = dm.group(1).strip() if dm else ''
        for am in ATTACH_RE.finditer(seg):
            fid, fname, label = am.group(1), am.group(2), am.group(3)
            fname = htmllib.unescape(re.sub(r'\s+', ' ', fname).strip())
            label = htmllib.unescape(label.strip())
            rows.append({
                'notice_id': nid,
                'notice_title': ntitle,
                'event_date': edate,
                'file_id': fid,
                'filename': fname,
                'label': label,
            })
    return rows


def main():
    html = open(sys.argv[1], encoding='utf-8').read()
    rows = parse(html)
    with open(sys.argv[2], 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['notice_id', 'notice_title', 'event_date',
                                          'file_id', 'filename', 'label'])
        w.writeheader()
        w.writerows(rows)
    print(f"notices with attachments parsed; {len(rows)} attachment rows -> {sys.argv[2]}")


if __name__ == '__main__':
    main()
