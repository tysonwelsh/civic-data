#!/usr/bin/env python3
"""Parse the Holladay SuiteOne portal home page (_suiteone_home.html) into an event
table: (event_id, title, date, body, has_video). The SuiteOne portal
(holladayut.suiteonemedia.com) lists 2025-2026 events grouped by year; a row carries a
`fa-video-camera` link to its own /event/?id=N when a recording exists. The actual video
is an S3 MP4 resolved from the event page (resolve_suiteone_video.py).

Usage: python3 parse_suiteone.py            # writes _suiteone_events.csv
"""
import re, csv, sys, datetime

HTML = "_suiteone_home.html"


def classify(title):
    t = title.lower()
    if "planning commission" in t or "planning comm" in t:
        return "PlanningCommission"
    if "local building authority" in t or "lba" in t:
        return "LBA"
    if "rda board" in t:
        return "RDA"
    if "council" in t and "rda" in t:
        return "Council"          # in-session RDA inside the council evening
    if "arts council" in t:
        return "ArtsCouncil"
    if "city council" in t or "council work" in t or "council retreat" in t \
       or "council legislative" in t or "legislative meeting" in t:
        return "Council"
    if "historical commission" in t:
        return "HistoricalCommission"
    if "tree committee" in t:
        return "TreeCommittee"
    if "admin hearing" in t:
        return "AdminHearingOfficer"
    if "canvass" in t:
        return "Canvass"
    if "swearing" in t or "ceremony" in t:
        return "Ceremony"
    if "quorum" in t:
        return "Council"          # potential-quorum council notices
    return "Other"


def main():
    html = open(HTML, encoding="utf-8", errors="replace").read()
    # Set of event ids that carry a video-camera icon link (recording present).
    video_ids = set(re.findall(
        r'/event/\?id=(\d+)"[^>]*>\s*<span[^>]*fa-video-camera', html))
    seen = {}
    for m in re.finditer(
            r'/event/\?id=(\d+)"[^>]*title="Navigate to ([^"]+)"[^>]*>', html):
        eid, raw_title = m.group(1), m.group(2)
        title = (raw_title.replace("&amp;", "&").strip())
        # date lives in the next cell: ">Mon DD, YYYY | HH:MM PM"
        tail = html[m.end():m.end() + 700]
        dm = re.search(r'>\s*([A-Z][a-z]{2} \d{1,2}, \d{4}) \|', tail)
        date = ""
        if dm:
            date = datetime.datetime.strptime(dm.group(1), "%b %d, %Y").strftime("%Y-%m-%d")
        # first occurrence wins; keep a date if a later dup has one
        if eid not in seen or (not seen[eid]["date"] and date):
            seen[eid] = {"event_id": eid, "title": title, "date": date,
                         "body": classify(title),
                         "has_video": "yes" if eid in video_ids else "no"}
    rows = sorted(seen.values(), key=lambda r: (r["date"], r["event_id"]))
    with open("_suiteone_events.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "title", "date", "body", "has_video"])
        w.writeheader()
        w.writerows(rows)
    nvid = sum(1 for r in rows if r["has_video"] == "yes")
    print(f"parsed {len(rows)} unique events; {nvid} with video-camera flag")
    import collections
    print("by body (video-flagged only):")
    c = collections.Counter(r["body"] for r in rows if r["has_video"] == "yes")
    for b, n in c.most_common():
        print(f"  {n:4d}  {b}")


if __name__ == "__main__":
    main()
