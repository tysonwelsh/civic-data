#!/usr/bin/env python3
"""Kearns transcripts — build index.csv (SCHEMA_SPEC.md §9 transcripts contract).

Kearns is a HYBRID transcript entity:
  A. YouTube captioned video  — the city's own channel @KearnsCity posts city-era
     (2026+) council-meeting live-stream archives; 11 of 12 carry an English ASR
     caption track (fetched + cleaned to text/). These are `format=caption`,
     `caption_type=asr`, and the ONLY genuine transcripts in the repo.
  B. PMN meeting-audio archive — every Utah Public Notice on council body 5823 and
     PC body 1561 attaches a per-meeting MP3 (2016/2017 -> 2026). These have NO
     caption track (audio only) -> `format=na`, `caption_type=none`, Whisper
     candidates (owner-gated, NOT run). 58 pre-~2018-07 files are PMN-purged (404).

Inputs (all built by sibling scripts in this dir):
  kearns_audio_inventory.csv  (kearns_harvest_audio.py) — PMN MP3 audio->date map
  kearns_audio_sizes.csv      (HEAD probe) — liveness + bytes per audio file
  raw/_yt_map.tsv             — the 11 captioned YouTube videos (id, date, title)
  text/<date>_<id>.md         (kearns_clean_captions.py) — cleaned ASR transcripts

Emits index.csv. Contract columns FIRST, city extras after.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"
YT = "https://www.youtube.com/watch?v="

CONTRACT = ["date", "title", "body", "video_url", "video_id", "caption_type",
            "source_url", "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["media_source", "audio_url", "audio_filename", "media_type",
         "pmn_body_id", "pmn_file_id", "notice_url", "size_bytes",
         "http_status", "whisper_candidate"]
COLS = CONTRACT + EXTRA

# The single un-captioned YouTube video (has NO caption track as of retrieval).
YT_NOCAP = [("vgKXlTCdkkk", "2026-07-13", "Kearns City Council Meeting July 13, 2026")]


def load_sizes():
    m = {}
    p = os.path.join(HERE, "kearns_audio_sizes.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            m[r["audio_url"]] = (r["http"], r["bytes"], r["content_type"])
    return m


def yt_rows():
    rows = []
    # captioned
    for line in open(os.path.join(RAW, "_yt_map.tsv")):
        vid, date, title = line.rstrip("\n").split("\t")
        stem = f"{date}_{vid}.md"
        path = f"text/{stem}" if os.path.exists(os.path.join(HERE, "text", stem)) else ""
        rows.append({
            "date": date, "title": title, "body": "Council",
            "video_url": YT + vid, "video_id": vid, "caption_type": "asr",
            "source_url": YT + vid, "retrieved_date": RETRIEVED,
            "format": "caption",
            "extraction_method": "yt-dlp --write-auto-sub en (YouTube ASR); "
                                 "VTT->text via kearns_clean_captions.py",
            "path": path,
            "media_source": "youtube", "audio_url": "", "audio_filename": "",
            "media_type": "", "pmn_body_id": "", "pmn_file_id": "",
            "notice_url": "", "size_bytes": "", "http_status": "",
            "whisper_candidate": "no",
        })
    # un-captioned YouTube video (documented honestly, no transcript)
    for vid, date, title in YT_NOCAP:
        rows.append({
            "date": date, "title": title, "body": "Council",
            "video_url": YT + vid, "video_id": vid, "caption_type": "none",
            "source_url": YT + vid, "retrieved_date": RETRIEVED,
            "format": "na",
            "extraction_method": "none (YouTube video has no caption track as of retrieval)",
            "path": "",
            "media_source": "youtube", "audio_url": "", "audio_filename": "",
            "media_type": "", "pmn_body_id": "", "pmn_file_id": "",
            "notice_url": "", "size_bytes": "", "http_status": "",
            "whisper_candidate": "no",
        })
    return rows


def audio_rows(sizes):
    rows = []
    for r in csv.DictReader(open(os.path.join(HERE, "kearns_audio_inventory.csv"))):
        url = r["audio_url"]
        http, byts, ct = sizes.get(url, ("", "", ""))
        live = (http == "200")
        method = ("none (PMN audio MP3 — no caption track; Whisper candidate, not run)"
                  if live else
                  "none (PMN file purged/unavailable — HTTP 404; pre-~2018-07 blob rot)")
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
    rows = yt_rows() + audio_rows(sizes)
    rows.sort(key=lambda r: (r["date"] or "0000", r["media_source"], r["body"],
                             r["audio_filename"], r["video_id"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    cap = [r for r in rows if r["format"] == "caption"]
    aud = [r for r in rows if r["media_source"] == "pmn_audio"]
    live = [r for r in aud if r["http_status"] == "200"]
    print(f"index.csv: {len(rows)} rows")
    print(f"  YouTube caption transcripts: {len(cap)}")
    print(f"  YouTube video (no caption):  {sum(1 for r in rows if r['media_source']=='youtube' and r['format']=='na')}")
    print(f"  PMN audio rows: {len(aud)}  (live {len(live)}, purged/404 {len(aud)-len(live)})")
    tot = sum(int(r["size_bytes"]) for r in live if r["size_bytes"].isdigit())
    print(f"  live audio total: {tot/1e9:.2f} GB")


if __name__ == "__main__":
    main()
