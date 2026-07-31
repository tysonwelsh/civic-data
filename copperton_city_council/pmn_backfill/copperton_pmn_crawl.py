#!/usr/bin/env python3
"""Copperton PMN backfill — crawl a public body's cumulative notices list and parse
every notice + its attachments (GET-only, via the cumulative page=N trick).

Usage:  python3 copperton_pmn_crawl.py <body_id> [<body_id> ...]
Writes work/notices_<body>.html (raw) and work/parsed_<body>.json.

Type labels on PMN are UNRELIABLE (a Magna CRA draft-minutes doc was labeled
"Public Information Handout") — so we keep every attachment's filename + label and
let the caller detect minutes by FILENAME + CONTENT. Modeled on magna_pmn_crawl.py.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
FETCH = "/Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/polite_fetch.py"


def fetch(url, name):
    subprocess.run([sys.executable, FETCH, "--out", WORK, "--name", name, url],
                   check=True, capture_output=True)
    with open(os.path.join(WORK, name), encoding="utf-8", errors="replace") as f:
        return f.read()


def parse(html):
    """Return list of notices: {notice_id,title,meeting_dt,attachments:[{file_id,ext,filename,label}]}"""
    notices = []
    rows = re.split(r'<tr class="(?:on|off)">', html)
    for row in rows[1:]:
        m = re.search(r'sitemap/notice/(\d+)\.html">([^<]*)</a>', row)
        if not m:
            continue
        nid, title = m.group(1), m.group(2).strip()
        dtm = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2} [AP]M)', row)
        meeting_dt = dtm.group(1) if dtm else ""
        atts = []
        for am in re.finditer(
            r'/pmn/files/(\d+)\.(\w+)"[^>]*aria-label="Download (.*?) \(opens in new window\)"'
            r'[^<]*</a>(?:\s*<[^>]*>)*\s*(?:&nbsp;\(([^)]*)\))?', row, re.S):
            atts.append({"file_id": am.group(1), "ext": am.group(2).lower(),
                         "filename": am.group(3).strip(), "label": (am.group(4) or "").strip()})
        notices.append({"notice_id": nid, "title": title,
                        "meeting_dt": meeting_dt, "attachments": atts})
    return notices


def main():
    os.makedirs(WORK, exist_ok=True)
    for body in sys.argv[1:]:
        html = fetch(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page=500",
                     f"notices_{body}.html")
        notices = parse(html)
        out = os.path.join(WORK, f"parsed_{body}.json")
        with open(out, "w") as f:
            json.dump(notices, f, indent=1)
        dts = [n["meeting_dt"] for n in notices if n["meeting_dt"]]
        natt = sum(len(n["attachments"]) for n in notices)
        print(f"body {body}: {len(notices)} notices, {natt} attachments, "
              f"date range {min(dts) if dts else '?'} .. {max(dts) if dts else '?'} -> {out}")


if __name__ == "__main__":
    main()
