#!/usr/bin/env python3
import json, csv, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/tmp")
from parse_dates import parse, body_of

DEN = ZoneInfo("America/Denver")
RET = "2026-07-13"
DS = "/Users/tysonwelsh/civic-data/alta_city_council/transcripts"

# stored samples: date -> (video_id, path)
STORED = {}
for f in os.listdir(os.path.join(DS, "raw")):
    if f.endswith(".en.vtt"):
        date = f[:10]; vid = f[11:].replace(".en.vtt", "")
        STORED[vid] = (date, f"raw/{f}")

# undated release timestamps
REL = {}
if os.path.exists("/tmp/undated_meta.tsv"):
    for line in open("/tmp/undated_meta.tsv"):
        p = line.rstrip("\n").split("\\t")   # yt-dlp wrote a LITERAL backslash-t
        if len(p) >= 2 and p[1].isdigit():
            REL[p[0]] = int(p[1])

def denver_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(DEN).strftime("%Y-%m-%d")

def load(jf):
    out = []
    for line in open(jf):
        try: d = json.loads(line)
        except: continue
        out.append(d)
    return out

# ---- YouTube index ----
rows = []
for src, kind in [("/tmp/yt_videos.jsonl", "video"), ("/tmp/yt_streams.jsonl", "stream")]:
    for d in load(src):
        vid = d.get("id"); title = (d.get("title") or "").strip()
        dur = d.get("duration")
        iso, prec = parse(title)
        date_source = "title"
        if not iso:
            if vid in REL:
                iso = denver_date(REL[vid]); prec = "day"; date_source = "release_timestamp(Denver)"
            else:
                iso = ""; prec = ""; date_source = "unknown"
        url = f"https://www.youtube.com/watch?v={vid}"
        body = body_of(title)
        stored = vid in STORED
        if stored:
            date = STORED[vid][0]; path = STORED[vid][1]
            fmt = "caption"; xmethod = "yt-dlp --write-auto-sub (en) + vtt-clean -> text/<date>.md"
        else:
            date = iso; path = ""; fmt = "na"; xmethod = "flat-playlist catalog (caption not downloaded)"
        rows.append(dict(
            date=date, title=title, body=body, video_url=url, video_id=vid,
            caption_type="asr", source_url=url, retrieved_date=RET, format=fmt,
            extraction_method=xmethod, path=path,
            platform="youtube", tab=kind, duration_sec=("" if dur is None else int(dur)),
            stored=("yes" if stored else "no"), captions_available="asr",
            date_source=date_source, date_precision=prec, title_raw=title))

# sort newest first by date then title
rows.sort(key=lambda r: (r["date"], r["title"]), reverse=True)

cols = ["date","title","body","video_url","video_id","caption_type","source_url",
        "retrieved_date","format","extraction_method","path",
        "platform","tab","duration_sec","stored","captions_available",
        "date_source","date_precision","title_raw"]
with open(os.path.join(DS, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow(r)

stored_n = sum(1 for r in rows if r["stored"]=="yes")
undated_n = sum(1 for r in rows if not r["date"])
print(f"YouTube index: {len(rows)} rows, {stored_n} stored captions, {undated_n} undated")
from collections import Counter
print("by body:", dict(Counter(r["body"] for r in rows)))
dates = [r["date"] for r in rows if r["date"]]
print("date range:", min(dates), "->", max(dates))

# ---- SoundCloud sidecar ----
sc = load("/tmp/sc_tracks.jsonl")
screws = []
for d in sc:
    title = (d.get("title") or "").strip()
    url = d.get("url") or ""
    slug = url.rstrip("/").split("/")[-1]
    iso, prec = parse(title)
    body = body_of(title)
    # whisper candidate: a genuine council/PC/budget meeting (not Other/dog/test)
    wc = "yes" if body in ("Council","PlanningCommission","BudgetCommittee") else "no"
    screws.append(dict(
        date=(iso or ""), date_precision=(prec or ""), title=title, body=body,
        url=url, track_slug=slug, source_url=url, platform="soundcloud",
        caption_type="none", whisper_candidate=wc,
        notes="audio only - no captions; Whisper transcription candidate" if wc=="yes" else "audio only - no captions"))
screws.sort(key=lambda r: (r["date"] or "0000", r["title"]), reverse=True)
sccols = ["date","date_precision","title","body","url","track_slug","source_url",
          "platform","caption_type","whisper_candidate","notes"]
with open(os.path.join(DS, "soundcloud_audio.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sccols); w.writeheader()
    for r in screws: w.writerow(r)
scd = [r["date"] for r in screws if r["date"]]
print(f"\nSoundCloud sidecar: {len(screws)} tracks, {sum(1 for r in screws if r['whisper_candidate']=='yes')} whisper candidates")
print("SC date range:", min(scd), "->", max(scd), "| undated SC:", sum(1 for r in screws if not r["date"]))
print("SC by body:", dict(Counter(r["body"] for r in screws)))
