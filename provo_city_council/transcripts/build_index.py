#!/usr/bin/env python3
"""Clean each sampled VTT -> text/<date>_<body>.md and build index.csv.

Reads sample.txt (date body video_id) + channel_videos.csv for titles.
Only videos whose raw VTT actually downloaded get caption_type=asr rows; a sampled
video with no caption file is logged to unrecovered.csv.
"""
import csv, os, subprocess, sys

RETRIEVED = "2026-07-03"
BODY_LABEL = {"council": "Municipal Council", "council_work": "Municipal Council Work Meeting"}
BODY_SLUG  = {"council": "council", "council_work": "council_work"}

titles = {}
for r in csv.DictReader(open("channel_videos.csv")):
    titles[r["video_id"]] = r["title"]

sample = []
for line in open("sample.txt"):
    line = line.strip()
    if not line: continue
    date, body, vid = line.split()
    sample.append((date, body, vid))

rows = []
unrec = []
for date, body, vid in sample:
    title = titles.get(vid, "")
    url = f"https://www.youtube.com/watch?v={vid}"
    vtt = f"raw/{vid}.en-orig.vtt"
    if not os.path.exists(vtt):
        unrec.append({"date": date, "title": title, "body": BODY_LABEL[body],
                      "video_url": url, "video_id": vid,
                      "reason": "no en-orig auto-caption returned by yt-dlp"})
        continue
    slug = BODY_SLUG[body]
    md = f"text/{date}_{slug}.md"
    subprocess.run([sys.executable, "clean_vtt.py", vtt, md, date, BODY_LABEL[body], url], check=True)
    rows.append({
        "date": date, "title": title, "body": BODY_LABEL[body],
        "video_url": url, "video_id": vid,
        "caption_type": "asr", "source_url": url,
        "retrieved_date": RETRIEVED, "format": "caption",
        "extraction_method": "yt-dlp auto-sub en-orig vtt; rolling-window dedup (clean_vtt.py)",
        "path": vtt,
    })

cols = ["date","title","body","video_url","video_id","caption_type","source_url",
        "retrieved_date","format","extraction_method","path"]
rows.sort(key=lambda x: x["date"])
with open("index.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow(r)

if unrec:
    with open("unrecovered.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","title","body","video_url","video_id","reason"])
        w.writeheader()
        for r in unrec: w.writerow(r)

print(f"index rows: {len(rows)}  unrecovered: {len(unrec)}")
