#!/usr/bin/env python3
"""White City transcripts — build the SCHEMA_SPEC §9 index.csv.

White City is an AUDIO-FIRST small entity: its Streamline site posts a per-meeting
MP3/M4A audio recording, and there is NO video / NO caption track anywhere (no
YouTube channel, absent from the Utah Record mirror — see AVAILABILITY.md). So every
index row is an audio recording with caption_type=none and format=na (no caption
stored). The §9 media-URL slot (video_url) is blank because these are audio, not
video; the audio URL lives in source_url + the audio_url extra.

Nothing is downloaded (audio bytes are public + re-fetchable; ~1.3 GB total) — this
is a link-only inventory. Whisper is a PROPOSAL only (owner-gated).

Reads wc_audio_inventory.csv (+ wc_audio_sizes.csv for byte sizes) -> index.csv.
"""
import csv, os

HERE = os.path.dirname(__file__)
RETRIEVED = "2026-07-13"

sizes = {}
sp = os.path.join(HERE, "wc_audio_sizes.csv")
if os.path.exists(sp):
    with open(sp, newline="") as f:
        for r in csv.DictReader(f):
            sizes[r["date"]] = r.get("bytes", "")

CONTRACT = ["date", "title", "body", "video_url", "video_id", "caption_type",
            "source_url", "retrieved_date", "format", "extraction_method", "path"]
EXTRAS = ["audio_url", "audio_filename", "media_type", "size_bytes",
          "whisper_candidate", "source_page_year"]

rows_out = []
with open(os.path.join(HERE, "wc_audio_inventory.csv"), newline="") as f:
    for r in csv.DictReader(f):
        rows_out.append({
            "date": r["date"],
            "title": r["title"],
            "body": "Council",
            "video_url": "",                         # audio-only entity — no video
            "video_id": "",
            "caption_type": "none",                  # audio has NO captions
            "source_url": r["audio_url"],            # the audio file is the source
            "retrieved_date": RETRIEVED,
            "format": "na",                          # no caption stored
            "extraction_method": "none (audio MP3/M4A — no caption track; Whisper candidate, not run)",
            "path": "",                              # not stored (link-only; owner-gated)
            "audio_url": r["audio_url"],
            "audio_filename": r["audio_filename"],
            "media_type": r["ext"],
            "size_bytes": sizes.get(r["date"], ""),
            "whisper_candidate": "yes",
            "source_page_year": r["source_page_year"],
        })

out = os.path.join(HERE, "index.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRAS)
    w.writeheader()
    for r in sorted(rows_out, key=lambda x: x["date"]):
        w.writerow(r)

print(f"index.csv rows: {len(rows_out)}")
tot = sum(int(r["size_bytes"]) for r in rows_out if r["size_bytes"].isdigit())
print(f"total audio: {tot/1048576:.1f} MB")
