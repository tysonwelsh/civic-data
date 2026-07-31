#!/usr/bin/env python3
"""parse_suiteone_events_holladay.py — parse the SuiteOne portal landing/recent-events
HTML dump into an in-scope event list (Council / PlanningCommission / RDA / LBA) with
each event's agenda-packet (apid), agenda (aid), and minutes (mid) links.

Reads a saved SuiteOne HTML file (GET of https://holladayut.suiteonemedia.com/ — the
server-side-rendered Recent Events table). Emits a TSV: eventid, body, title, date(ISO),
apid, aid, mid, packet_url.

SuiteOne row shape (verified 2026-07-13):
  <a href="/event/?id=<EID>" ...>Title <span ...></a>
  <td data-sort="<ticks>"> Mon DD, YYYY | HH:MM AM/PM </td>
  <a href="/event/GetAgendaFile/Agenda?aid=<AID>">
  <a href="/event/GetAgendaPacketFile/Agenda%20Packet?apid=<APID>">
  <a href="/event/GetMinutesFile/Minutes?mid=<MID>">
"""
import csv
import datetime
import re
import sys

BASE = "https://holladayut.suiteonemedia.com"

# title substring -> body tag (order matters; first match wins)
BODY_RULES = [
    ("planning commission", "PlanningCommission"),
    ("local building authority", "LBA"),
    ("lba", "LBA"),
    ("rda board", "RDA"),
    ("& rda", "Council"),          # "City Council & RDA Meeting" -> Council (in-session RDA)
    ("council", "Council"),
    ("legislative meeting", "Council"),
]

IN_SCOPE = {"Council", "PlanningCommission", "RDA", "LBA"}


def classify(title):
    t = title.lower().replace("&amp;", "&")
    for key, body in BODY_RULES:
        if key in t:
            return body
    return None


def parse(path):
    html = open(path, encoding="utf-8", errors="replace").read()
    recs = []
    for chunk in re.split(r"<tr>", html):
        m = re.search(r'/event/\?id=(\d+)"[^>]*>([^<]+)<span', chunk)
        if not m:
            continue
        eid, title = m.group(1), m.group(2).strip().replace("&amp;", "&")
        dm = re.search(r'([A-Z][a-z]{2} \d{1,2}, \d{4}) \| ([\d:]+ [AP]M)', chunk)
        if not dm:
            continue
        try:
            date = datetime.datetime.strptime(dm.group(1), "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        aid = re.search(r'GetAgendaFile/[^?]*\?aid=(\d+)', chunk)
        apid = re.search(r'GetAgendaPacketFile/[^?]*\?apid=(\d+)', chunk)
        mid = re.search(r'GetMinutesFile/[^?]*\?mid=(\d+)', chunk)
        body = classify(title)
        recs.append({
            "eventid": eid, "body": body or "", "title": title, "date": date,
            "apid": apid.group(1) if apid else "",
            "aid": aid.group(1) if aid else "",
            "mid": mid.group(1) if mid else "",
            "packet_url": f"{BASE}/event/GetAgendaPacketFile/Packet?apid={apid.group(1)}" if apid else "",
        })
    return recs


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "suiteone_root.html"
    only_scope = "--all" not in sys.argv
    recs = parse(src)
    if only_scope:
        recs = [r for r in recs if r["body"] in IN_SCOPE]
    recs.sort(key=lambda r: (r["date"], r["body"]))
    w = csv.DictWriter(sys.stdout, fieldnames=["date", "body", "eventid", "title", "apid", "aid", "mid", "packet_url"], delimiter="\t")
    w.writeheader()
    for r in recs:
        w.writerow({k: r[k] for k in w.fieldnames})
    sys.stderr.write(f"{len(recs)} records; with packet apid: {sum(1 for r in recs if r['apid'])}\n")
