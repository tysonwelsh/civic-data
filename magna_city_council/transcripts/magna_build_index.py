#!/usr/bin/env python3
"""Magna transcripts — build index.csv (SCHEMA_SPEC.md §9 transcripts contract).

Magna is an AUDIO-ONLY transcript entity (the audio-only branch of
expand-city-sources). There is NO captioned video source:
  - Meeting VIDEO is a Zoom webinar (live only, not archived).
  - No YouTube channel carries Magna meetings (@MagnaCity is empty; @MagnaUtah /
    @magnautah are a Cyprus High School decoy; Utah Record mirror has 0 Magna) —
    see raw/_magna_youtube_probe.txt + raw/_utah_record_channel_titles.txt.
So EVERY row is a PMN meeting-audio MP3 with NO caption track:
    format=na, caption_type=none, whisper_candidate = (live ? yes : no).
Nothing is downloaded — link-only inventory (a documented allowed exception; the
bytes are public + re-fetchable from audio_url). Whisper is a PROPOSAL only
(owner-gated, NOT run).

Inputs (sibling scripts in this dir):
  magna_audio_inventory.csv  (magna_harvest_audio.py) — PMN MP3 audio->date map
  magna_audio_sizes.csv      (magna_probe_sizes.py)   — HEAD liveness + bytes

Emits index.csv. Contract columns FIRST, city extras after.
"""
import csv
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-13"

CONTRACT = ["date", "title", "body", "video_url", "video_id", "caption_type",
            "source_url", "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["media_source", "audio_url", "audio_filename", "media_type",
         "pmn_body_id", "pmn_file_id", "notice_url", "size_bytes",
         "http_status", "whisper_candidate"]
COLS = CONTRACT + EXTRA


def load_sizes():
    m = {}
    p = os.path.join(HERE, "magna_audio_sizes.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            m[r["audio_url"]] = (r["http"], r["bytes"], r["content_type"])
    return m


def audio_rows(sizes):
    rows = []
    for r in csv.DictReader(open(os.path.join(HERE, "magna_audio_inventory.csv"))):
        url = r["audio_url"]
        http, byts, ct = sizes.get(url, ("", "", ""))
        live = (http == "200")
        method = ("none (PMN audio MP3 — no caption track; Whisper candidate, not run)"
                  if live else
                  "none (PMN file purged/unavailable — HTTP 404; pre-~2018 blob rot)")
        rows.append({
            "date": r["date"], "title": r["notice_title"], "body": r["body"],
            "video_url": "", "video_id": "", "caption_type": "none",
            "source_url": url, "retrieved_date": RETRIEVED,
            "format": "na", "extraction_method": method, "path": "",
            "media_source": "pmn_audio", "audio_url": url,
            "audio_filename": r["audio_filename"], "media_type": r["media_type"],
            "pmn_body_id": r["pmn_body_id"], "pmn_file_id": r["pmn_file_id"],
            "notice_url": r["notice_url"], "size_bytes": byts,
            "http_status": http, "whisper_candidate": "yes" if live else "no",
        })
    return rows


def main():
    sizes = load_sizes()
    rows = audio_rows(sizes)
    rows.sort(key=lambda r: (r["date"] or "0000", r["body"], r["audio_filename"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    live = [r for r in rows if r["http_status"] == "200"]
    purged = [r for r in rows if r["http_status"] == "404"]
    print(f"index.csv: {len(rows)} rows (all PMN audio; 0 captioned — audio-only entity)")
    print(f"  by body: {dict(Counter(r['body'] for r in rows))}")
    print(f"  live (HTTP 200): {len(live)}   purged (404): {len(purged)}")
    tot = sum(int(r["size_bytes"]) for r in live if (r["size_bytes"] or '').isdigit())
    print(f"  live audio total: {tot/1e9:.2f} GB")
    print(f"  whisper candidates (live): {sum(1 for r in rows if r['whisper_candidate']=='yes')}")


if __name__ == "__main__":
    main()
