#!/usr/bin/env python3
"""Parse Cottonwood Heights CivicEngage agendas/packets/minutes landing HTML.

Extracts, per meeting-date row, every labeled showpublisheddocument anchor
(Agenda | Packet | Minutes | Amended... | Cancelled). Emits JSON of Packet
anchors only, keyed by (date, title). Kept inside packets/ per the concurrency
rule (unique name).
"""
import re, json, sys, datetime

MONTHS = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], start=1)}

def parse_date(text):
    # e.g. "July 7, 2026 Work Session and Business Meeting"
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})",
                  text, re.I)
    if not m:
        return None
    mo = MONTHS[m.group(1).lower()]
    return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}"

def parse(html_path):
    html = open(html_path, encoding="utf-8").read()
    # isolate the data table body
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    out = []
    for row in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(tds) < 2:
            continue
        desc = re.sub(r"<[^>]+>", " ", tds[0])
        desc = re.sub(r"&nbsp;", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        date = parse_date(desc)
        if not date:
            continue
        anchors = re.findall(
            r'<a\s+href="([^"]*showpublisheddocument/\d+[^"]*)"[^>]*>(.*?)</a>',
            tds[1], re.S)
        links = []
        for url, label in anchors:
            label = re.sub(r"<[^>]+>", "", label)
            label = re.sub(r"&nbsp;", " ", label).strip()
            links.append({"label": label, "url": url})
        out.append({"date": date, "title": desc, "links": links})
    return out

if __name__ == "__main__":
    result = parse(sys.argv[1])
    json.dump(result, sys.stdout, indent=1)
