#!/usr/bin/env python3
"""Map @SouthSaltLakeCity video titles -> (date, body, meeting_kind).

Input:  enum_videos.psv  (id|title|duration  from `yt-dlp --flat-playlist --print`)
Output: channel_videos.csv  (video_id,title,duration,date,date_source,body,meeting_kind,is_meeting)

Titles are like "2026 7 9 Planning Commission Meeting" (space) or
"2023-7-13 Planning Commission" (dash). Promotional videos (State of the City,
Mural Fest, celebrations) carry no leading date -> is_meeting=no, date blank.
No title-date is fabricated; a video without a parseable leading date is left blank
for a separate release_timestamp probe.
"""
import csv, re

DATE_RE = re.compile(r"^\s*(20\d{2})[ \-.](\d{1,2})[ \-.](\d{1,2})\b")


def classify(t):
    s = t.lower()
    if "planning commission" in s:
        return "PlanningCommission", "PC"
    if "civilian review" in s:
        return "CivilianReviewBoard", "CRB"
    if "redevelopment" in s or re.search(r"\brda\b", s):
        return "RDA", "RDA"
    if "board of canvassers" in s:
        return "CityCouncil", "BoC"
    if "council" in s:
        if "work" in s:
            return "CityCouncil", "WM"
        if "regular" in s:
            return "CityCouncil", "RC"
        return "CityCouncil", "RC"  # bare "Council Meeting"
    return "", ""


rows = []
with open("enum_videos.psv") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|")
        vid = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        dur = parts[2] if len(parts) > 2 else ""
        m = DATE_RE.match(title)
        date, dsrc = "", ""
        if m:
            y, mo, d = m.groups()
            date = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
            dsrc = "title"
        body, kind = classify(title)
        is_meeting = "yes" if (date and body) else "no"
        rows.append({
            "video_id": vid, "title": title, "duration": dur,
            "date": date, "date_source": dsrc, "body": body,
            "meeting_kind": kind, "is_meeting": is_meeting,
        })

with open("channel_videos.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["video_id", "title", "duration", "date",
                                      "date_source", "body", "meeting_kind", "is_meeting"])
    w.writeheader()
    w.writerows(rows)

meet = [r for r in rows if r["is_meeting"] == "yes"]
nomeet = [r for r in rows if r["is_meeting"] == "no"]
print(f"total={len(rows)} meetings={len(meet)} non_meetings={len(nomeet)}")
from collections import Counter
print("by body:", dict(Counter(r["body"] for r in meet)))
if meet:
    ds = sorted(r["date"] for r in meet)
    print("date range:", ds[0], "->", ds[-1])
print("\nnon-meeting / undated titles:")
for r in nomeet:
    print(" ", r["video_id"], r["title"])
