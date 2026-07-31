#!/usr/bin/env python3
"""Cottonwood Heights transcripts: parse the yt-dlp channel enumeration into
channel_videos.csv (every video) + the meeting-video rows for index.csv.

Reads the two flat-playlist dumps (enum_streams.tsv, enum_videos.tsv). NOTE: yt-dlp
--print emits a LITERAL two-char backslash-t as the field separator (not a real TAB),
so we split on the literal r"\t". timestamp/upload_date are NA in --flat-playlist mode,
so dates come from the TITLE; the handful of undated meeting videos are left date-blank
(resolved by an individual --print probe only if sampled).

Usage: python3 ch_transcripts_build.py
Outputs (in this dir): channel_videos.csv
"""
import csv, re, os
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-13"
CHANNEL = "UCcOhqM97RmMrEpUz_6L84Cw"  # resolved from @CottonwoodHeights (see AVAILABILITY.md)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_date(title):
    """Return (iso_date or '', date_source). Title-first."""
    t = title.strip()
    # 1) ISO leading: 2026-07-07 ...
    m = re.match(r'^(20\d\d)-(\d{1,2})-(\d{1,2})\b', t)
    if m:
        y, mo, d = map(int, m.groups())
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", "title_iso"
    # 1b) ISO anywhere: "... Work Session 2025-12-02"
    m = re.search(r'\b(20\d\d)-(\d{1,2})-(\d{1,2})\b', t)
    if m:
        y, mo, d = map(int, m.groups())
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", "title_iso"
    # 2) space YMD leading: 2025 05 07 ...
    m = re.match(r'^(20\d\d)\s+(\d{1,2})\s+(\d{1,2})\b', t)
    if m:
        y, mo, d = map(int, m.groups())
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", "title_ymd"
    # 3) Month name D, YYYY  (Aug. 3, 2021 / June 4, 2019 / May 18, 2021)
    m = re.search(r'\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(20\d\d)\b', t)
    if m:
        mon = m.group(1).lower()[:3]
        if mon in MONTHS:
            mo, d, y = MONTHS[mon], int(m.group(2)), int(m.group(3))
            if 1 <= d <= 31:
                return f"{y:04d}-{mo:02d}-{d:02d}", "title_monthname"
    # 4) M-D-YY or M/D/YY embedded (Cottonwood Heights ... 8-28-18)
    m = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', t)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        if 1 <= mo <= 12 and 1 <= d <= 31 and 2015 <= y <= 2030:
            return f"{y:04d}-{mo:02d}-{d:02d}", "title_mdy"
    return "", ""


def classify_body(title):
    t = title.lower()
    joint = ("joint" in t) and ("planning" in t or "commission" in t) and "council" in t
    is_pc = ("planning commission" in t or re.search(r'\bpc\b', t)
             or "planning comm" in t)
    is_arc = ("architectural review" in t or re.search(r'\barc\b', t))
    is_cdra = ("cdra" in t or "renewal agency" in t or "redevelopment" in t
               or re.search(r'\brda\b', t))
    is_council = "council" in t or re.search(r'\bcwh council\b', t)
    if joint:
        return "Joint"
    if is_cdra:
        return "CDRA"
    if is_pc:
        return "PlanningCommission"
    if is_arc:
        return "ARC"
    if is_council:
        return "Council"
    return ""  # non-meeting / other


# Recurring placeholder / test / non-meeting title markers => not a real dated meeting
NONMEETING_RE = re.compile(
    r'\b(test|light the night|monster mash|all america|business award|marathon|'
    r'police message|celebration|new year|localscapes|preparedness|breakfast|'
    r'candidates night|oath of office|visits|traffic guidelines|spotlight|'
    r'1st tue|3rd tue|1st wed|3rd wed|4th thurs|wednesdays|7pm|6pm|5pm)\b',
    re.I)


def load(path, tab):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split(r"\t")
            if len(parts) < 5:
                continue
            vid, up, ts, dur, title = parts[0], parts[1], parts[2], parts[3], r"\t".join(parts[4:])
            try:
                dur = int(float(dur)) if dur not in ("NA", "") else ""
            except ValueError:
                dur = ""
            rows.append({"video_id": vid, "upload_date": up, "timestamp": ts,
                         "duration_sec": dur, "title": title, "tab": tab})
    return rows


def load_probe():
    """video_id -> iso date in America/Denver from the release/publish timestamp.
    America/Denver = UTC-7 (MDT) for the meeting months here; use a fixed -7h offset
    so a UTC timestamp near local midnight does not roll to the wrong calendar day
    (the murray gotcha). release_timestamp (stream start) preferred over timestamp."""
    out = {}
    p = os.path.join(HERE, "undated_probe.tsv")
    if not os.path.exists(p):
        return out
    denver = timezone(timedelta(hours=-7))
    for line in open(p):
        parts = line.rstrip("\n").split(r"\t")
        if len(parts) < 4:
            continue
        vid, ts, up, rts = parts[0], parts[1], parts[2], parts[3]
        epoch = None
        for cand in (rts, ts):
            if cand and cand != "NA":
                try:
                    epoch = int(cand); break
                except ValueError:
                    pass
        if epoch is not None:
            out[vid] = datetime.fromtimestamp(epoch, denver).strftime("%Y-%m-%d")
        elif up and up != "NA" and len(up) == 8:
            out[vid] = f"{up[:4]}-{up[4:6]}-{up[6:8]}"  # UTC upload_date fallback
    return out


def main():
    probe = load_probe()
    seen = {}
    order = []
    for path, tab in [(os.path.join(HERE, "enum_streams.tsv"), "streams"),
                      (os.path.join(HERE, "enum_videos.tsv"), "videos")]:
        for r in load(path, tab):
            if r["video_id"] in seen:
                seen[r["video_id"]]["tab"] += "+" + tab
                continue
            seen[r["video_id"]] = r
            order.append(r["video_id"])

    out = []
    for vid in order:
        r = seen[vid]
        title = r["title"]
        date, dsrc = parse_date(title)
        body = classify_body(title)
        # meeting = has a body keyword AND is not a recurring-placeholder/PR title,
        #   OR has a real title date AND a body keyword.
        placeholder = bool(NONMEETING_RE.search(title)) and not date
        is_meeting = bool(body) and not placeholder
        if is_meeting and not date and vid in probe:
            date, dsrc = probe[vid], "yt_release_ts_local"
        r["date"] = date
        r["date_source"] = dsrc
        r["body"] = body if is_meeting else ("NonMeeting" if not body else "Other")
        r["is_meeting"] = "yes" if is_meeting else "no"
        r["video_url"] = f"https://www.youtube.com/watch?v={vid}"
        out.append(r)

    cols = ["date", "date_source", "body", "is_meeting", "video_id", "video_url",
            "title", "duration_sec", "tab"]
    with open(os.path.join(HERE, "channel_videos.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in cols})

    # ---- index.csv (§9 transcripts contract header + extras) ----
    # fetched.csv (optional): video_id,path  for the sampled caption files.
    fetched = {}
    fp = os.path.join(HERE, "fetched.csv")
    if os.path.exists(fp):
        for r in csv.DictReader(open(fp)):
            fetched[r["video_id"]] = r["path"]

    meetings = [r for r in out if r["is_meeting"] == "yes"]
    # sort by date (undated last), then title
    meetings_sorted = sorted(meetings, key=lambda r: (r["date"] or "9999", r["title"]))
    contract = ["date", "title", "body", "video_url", "video_id", "caption_type",
                "source_url", "retrieved_date", "format", "extraction_method", "path"]
    extras = ["duration_sec", "tab", "date_source"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(contract + extras)
        for r in meetings_sorted:
            vid = r["video_id"]
            if vid in fetched:
                fmt, method, path = "caption", ("yt-dlp --write-auto-sub (YouTube ASR "
                    "auto-captions), cleaned to text/"), fetched[vid]
            else:
                fmt, method, path = "na", "mapped_not_fetched", ""
            title = f'{r["title"]} (ASR transcript)'
            w.writerow([r["date"], title, r["body"], r["video_url"], vid, "asr",
                        r["video_url"], RETRIEVED, fmt, method, path,
                        r["duration_sec"], r["tab"], r["date_source"]])

    dated = [r for r in meetings if r["date"]]
    print(f"total videos: {len(out)}")
    print(f"meeting videos: {len(meetings)}  (dated: {len(dated)}, undated: {len(meetings)-len(dated)})")
    from collections import Counter
    print("body:", dict(Counter(r["body"] for r in meetings)))
    print("date_source:", dict(Counter(r["date_source"] for r in dated)))
    if dated:
        ds = sorted(r["date"] for r in dated)
        print("date range:", ds[0], "->", ds[-1])


if __name__ == "__main__":
    main()
