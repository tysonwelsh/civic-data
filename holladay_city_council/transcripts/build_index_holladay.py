#!/usr/bin/env python3
"""Assemble transcripts/index.csv (SCHEMA_SPEC.md §9 transcripts contract) for Holladay
from the two platforms:
  1. YouTube official channel @holladaycity4925 — 6 genuine body-meeting videos (2020-2021
     era), all with YouTube ASR captions FETCHED to raw/ + cleaned to text/.
  2. SuiteOne portal (holladayut.suiteonemedia.com) — 75 video-flagged events (2025-2026),
     video-only S3 MP4, NO captions -> format=na map rows (Whisper deferred).

Also writes raw/_fetch_log.jsonl (provenance for the 6 fetched YouTube caption tracks).

Usage: python3 build_index_holladay.py
"""
import csv, json, hashlib, os, datetime

RET = "2026-07-13"
YT_WATCH = "https://www.youtube.com/watch?v="

# (video_id, date, body, title, date_source)
YT = [
    ("sVCkXRjgTK8", "2021-01-14", "Council", "Council Work Meeting - Jan. 14", "title"),
    ("C7fwWXFObZA", "2021-01-07", "Council", "City Council Meeting", "description"),
    ("qM69rTmSnxE", "2020-12-15", "PlanningCommission", "Planning Commission Mtg: Dec 15, 2020", "title"),
    ("JuPHTPDs-sc", "2021-01-05", "PlanningCommission", "Planning Commission Mtg (Part 1 of 4)", "asr_spoken"),
    ("E7Wv0DN692w", "2021-01-19", "PlanningCommission", "Planning Commission Mtg - Jan. 19", "title"),
    ("W_YJNzoykV8", "2021-01-20", "ArtsCouncil", "Arts Council", "description"),
]

CONTRACT = ["date", "title", "body", "video_url", "video_id", "caption_type",
            "source_url", "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["platform", "date_source", "suiteone_event_id"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    rows, log = [], []
    # --- YouTube (fetched captions) ---
    for vid, date, body, title, dsrc in YT:
        path = f"raw/{date}_{vid}.en.vtt"
        assert os.path.exists(path), path
        rows.append({
            "date": date, "title": title, "body": body,
            "video_url": YT_WATCH + vid, "video_id": vid, "caption_type": "asr",
            "source_url": YT_WATCH + vid, "retrieved_date": RET, "format": "caption",
            "extraction_method": "yt-dlp --write-auto-sub (YouTube ASR, en) -> clean_captions_holladay.py",
            "path": path, "platform": "youtube", "date_source": dsrc,
            "suiteone_event_id": "",
        })
        log.append({"url": YT_WATCH + vid, "video_id": vid, "sub_lang": "en",
                    "bytes": os.path.getsize(path), "sha256": sha256(path),
                    "retrieved_utc": RET + "T00:00:00Z", "tool": "yt-dlp"})
    # --- SuiteOne (video-only, no captions) ---
    sv = list(csv.DictReader(open("_suiteone_video.csv")))
    for r in sv:
        vid = r["video_id"]
        mp4 = r["video_mp4"]
        if not vid:            # the one row that timed out on first pass, patched below
            if r["event_id"] == "3045":
                mp4 = "https://s3.amazonaws.com/suiteone.holladayut.videofiles/d037e975.mp4"
                vid = "d037e975"
            else:
                continue
        rows.append({
            "date": r["date"], "title": r["title"], "body": r["body"],
            "video_url": mp4, "video_id": vid, "caption_type": "none",
            "source_url": r["event_url"], "retrieved_date": RET, "format": "na",
            "extraction_method": "none (SuiteOne video-only MP4; no caption track; ASR via Whisper deferred)",
            "path": "", "platform": "suiteone", "date_source": "suiteone",
            "suiteone_event_id": r["event_id"],
        })
    rows.sort(key=lambda r: (r["date"], r["platform"], r["video_id"]))
    with open("index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRA)
        w.writeheader()
        w.writerows(rows)
    with open("raw/_fetch_log.jsonl", "w") as f:
        for e in log:
            f.write(json.dumps(e) + "\n")
    ncap = sum(1 for r in rows if r["format"] == "caption")
    nna = sum(1 for r in rows if r["format"] == "na")
    print(f"index.csv: {len(rows)} rows ({ncap} caption / {nna} na)")
    print(f"date range: {rows[0]['date']} -> {rows[-1]['date']}")
    import collections
    print("caption rows by body:", dict(collections.Counter(r["body"] for r in rows if r["format"] == "caption")))
    print("na rows by body:", dict(collections.Counter(r["body"] for r in rows if r["format"] == "na")))


if __name__ == "__main__":
    main()
