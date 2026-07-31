#!/usr/bin/env python3
"""Parse a saturated PMN /pmn/list/notices.html page into structured notice rows.
Outputs JSON: [{notice_id,title,date,time,attachments:[{file_id,filename,type}]}]"""
import re, json, sys

def parse(path):
    html = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r'<tbody>(.*)</tbody>', html, re.S)
    body = m.group(1) if m else html
    rows = re.split(r'<tr class="(?:on|off)">', body)[1:]
    out = []
    for r in rows:
        nm = re.search(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>', r, re.S)
        if not nm:
            continue
        nid = nm.group(1)
        title = re.sub(r'\s+', ' ', nm.group(2)).strip()
        dm = re.search(r'(\d{4}/\d{2}/\d{2})\s+([\d:]+\s*[AP]M)', r)
        date = dm.group(1).replace('/', '-') if dm else ''
        time = dm.group(2) if dm else ''
        atts = []
        for am in re.finditer(r'/pmn/files/(\d+)\.pdf"[^>]*>(.*?)</a>\s*(?:&nbsp;)?\s*\(([^)]*)\)', r, re.S):
            atts.append({"file_id": am.group(1),
                         "filename": re.sub(r'\s+', ' ', am.group(2)).strip(),
                         "type": am.group(3).strip()})
        out.append({"notice_id": nid, "title": title, "date": date,
                    "time": time, "attachments": atts})
    return out

if __name__ == "__main__":
    data = parse(sys.argv[1])
    json.dump(data, open(sys.argv[2], "w"), indent=1)
    dated = [d for d in data if d["date"]]
    ds = sorted(d["date"] for d in dated)
    print(f"{len(data)} notices -> {sys.argv[2]}  range {ds[0] if ds else '-'} .. {ds[-1] if ds else '-'}")
