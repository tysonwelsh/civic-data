#!/usr/bin/env python3
"""Kearns transcripts — clean YouTube ASR .vtt caption tracks to readable text.

The city's own YouTube channel (@KearnsCity, "Kearns City Government") posts
city-era (2026+) council-meeting live-stream archives, most of which carry an
English AUTOMATIC (ASR) caption track. yt-dlp fetched the raw en .vtt into raw/
(files cap_<date>_<videoid>.en.vtt). This collapses YouTube's rolling-caption
format (each phrase restated as it builds, plus inline <timestamp><c> word tags)
into de-duplicated plain paragraphs, and writes text/<date>_<videoid>.md with a
mandatory ASR-quality header (NOT an official record).
"""
import glob
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
os.makedirs(TEXT, exist_ok=True)

TS = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->")
INLINE = re.compile(r"<[^>]+>")            # <00:00:00.200> and <c>/<\c>
STEM = re.compile(r"^cap_(\d{4}-\d{2}-\d{2})_(.+)\.en\.vtt$")

HEADER = (
    "# AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record\n\n"
    "Source: YouTube automatic (ASR) captions, channel @KearnsCity "
    "(\"Kearns City Government\"). Cleaned from the raw `.vtt` in `raw/`.\n"
    "Meeting date: {date}  ·  video: https://www.youtube.com/watch?v={vid}\n"
    "The official record is the clerk's minutes in `meeting_minutes/`.\n\n"
    "---\n\n"
)


def clean_vtt(path):
    lines = []
    for raw in open(path, encoding="utf-8", errors="replace"):
        s = raw.rstrip("\n")
        if s.startswith("WEBVTT") or s.startswith("Kind:") or s.startswith("Language:"):
            continue
        if TS.match(s) or "-->" in s:
            continue
        if not s.strip():
            continue
        s = INLINE.sub("", s)                 # strip inline word-timestamp tags
        s = html.unescape(s)                  # &gt;&gt; -> >>  (speaker-change marker)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        # YouTube ASR emits each line twice (the "building" cue then the settled
        # cue). Drop a line identical to the last kept line, and drop a line that
        # is a prefix of the previous (partial build-up).
        if lines and s == lines[-1]:
            continue
        if lines and lines[-1].startswith(s):
            continue
        if lines and s.startswith(lines[-1]):
            lines[-1] = s                     # replace partial with fuller build
            continue
        lines.append(s)
    # wrap into loose paragraphs (~40 cues each) for readability
    text = "\n".join(lines)
    return text


def main():
    n = 0
    for vtt in sorted(glob.glob(os.path.join(RAW, "cap_*.en.vtt"))):
        m = STEM.match(os.path.basename(vtt))
        if not m:
            continue
        date, vid = m.group(1), m.group(2)
        body = clean_vtt(vtt)
        out = os.path.join(TEXT, f"{date}_{vid}.md")
        with open(out, "w") as f:
            f.write(HEADER.format(date=date, vid=vid))
            f.write(body)
            f.write("\n")
        words = len(body.split())
        print(f"  {date} {vid}: {words} words -> text/{date}_{vid}.md")
        n += 1
    print(f"cleaned {n} caption tracks")


if __name__ == "__main__":
    main()
