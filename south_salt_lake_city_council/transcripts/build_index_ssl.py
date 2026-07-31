#!/usr/bin/env python3
"""Assemble transcripts/index.csv for South Salt Lake (§9 transcripts contract).

Inputs:
  channel_videos.csv   video_id,title,duration,date,date_source,body,meeting_kind,is_meeting
  _listsubs_raw.txt     batched `yt-dlp --list-subs` output over all meeting videos
                        (android player_client) — ground-truth caption availability per video
  raw/<date>_<id>.en.vtt   the 10 fetched sample caption tracks (sample-only)

Output: index.csv, one row per MEETING video (is_meeting==yes). Non-meeting promotional
clips (State of the City, Mural Fest, celebrations) are excluded from index.csv but kept
in channel_videos.csv for provenance.

Caption availability is READ from the probe, never assumed: a video is caption-bearing only
if the probe listed an `en` automatic-caption track for it. Videos not reached by the probe
(should be none) get caption_type/ format blank so nothing is fabricated.
"""
import csv, os, re

RETRIEVED = "2026-07-13"
CH = "https://www.youtube.com/@SouthSaltLakeCity"

# --- parse probe: id -> has_en_auto (bool) / probed (bool) ---
probed, has_en = set(), set()
cur = None
with open("_listsubs_raw.txt", encoding="utf-8", errors="replace") as f:
    for ln in f:
        m = re.match(r"\[youtube\] ([\w-]+): Downloading webpage", ln)
        if m:
            cur = m.group(1); probed.add(cur); continue
        m = re.match(r"\[info\] Available automatic captions for ([\w-]+):", ln)
        if m:
            cur = m.group(1); probed.add(cur); continue
        if re.match(r"^en\s+English\b", ln) and cur:
            has_en.add(cur)

# --- which samples are fetched on disk ---
fetched = {}  # video_id -> raw relative path
for fn in os.listdir("raw"):
    m = re.match(r"(\d{4}-\d{2}-\d{2})_(.+)\.en\.vtt$", fn)
    if m:
        fetched[m.group(2)] = "raw/" + fn

FIELDS = ["date", "title", "body", "video_url", "video_id", "caption_type",
          "source_url", "retrieved_date", "format", "extraction_method", "path",
          "platform", "meeting_kind", "date_source", "duration_s"]

rows = []
n_cap = n_na = n_unprobed = n_fetched = 0
with open("channel_videos.csv") as f:
    for r in csv.DictReader(f):
        if r["is_meeting"] != "yes":
            continue
        vid = r["video_id"]
        url = f"https://www.youtube.com/watch?v={vid}"
        if vid not in probed:
            caption_type, fmt, method, path = "", "", "not probed", ""
            n_unprobed += 1
        elif vid in has_en:
            caption_type, fmt = "asr", "caption"
            n_cap += 1
            if vid in fetched:
                path = fetched[vid]
                method = "yt-dlp --write-auto-sub (android client, en) -> clean_captions_ssl.py"
                n_fetched += 1
            else:
                path = ""
                method = "yt-dlp --list-subs (android client): en ASR track available, not fetched (sample-only)"
        else:
            caption_type, fmt, method, path = "none", "na", "yt-dlp --list-subs (android client): no caption track", ""
            n_na += 1
        rows.append({
            "date": r["date"], "title": r["title"], "body": r["body"],
            "video_url": url, "video_id": vid, "caption_type": caption_type,
            "source_url": url, "retrieved_date": RETRIEVED, "format": fmt,
            "extraction_method": method, "path": path, "platform": "youtube",
            "meeting_kind": r["meeting_kind"], "date_source": r["date_source"],
            "duration_s": r["duration"],
        })

rows.sort(key=lambda x: (x["date"], x["body"], x["meeting_kind"]))
with open("index.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print(f"index rows (meetings): {len(rows)}")
print(f"  caption-bearing (asr): {n_cap}  (of which fetched samples: {n_fetched})")
print(f"  no caption (na): {n_na}")
print(f"  not probed: {n_unprobed}")
