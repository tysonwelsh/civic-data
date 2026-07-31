#!/usr/bin/env python3
"""Clean sampled YouTube auto-caption VTTs -> transcripts/text/<date>.md with an ASR header.

YouTube auto-caption VTT rolls each line forward across cues (heavy duplication) and
embeds inline word-timing tags (<00:00:01.234>) plus positioning attrs. We strip cue
timing/tags and collapse the rolling duplication into readable running text. The raw
.vtt is retained untouched in raw/. Preserves ASR text verbatim (no LLM cleanup).

Reads index.csv, cleans every format=caption row. Idempotent.
"""
import csv, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))

TAG = re.compile(r'<[^>]+>')            # <c>, </c>, <00:00:01.234>
TSLINE = re.compile(r'^\d\d:\d\d:\d\d\.\d\d\d\s+-->')


def clean_vtt(path):
    lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("WEBVTT") or line.startswith("Kind:") or \
               line.startswith("Language:") or line.startswith("NOTE"):
                continue
            if TSLINE.match(line) or "-->" in line:
                continue
            if line.strip().isdigit():
                continue
            if not line.strip():
                continue
            txt = html.unescape(TAG.sub("", line)).strip()
            if txt:
                lines.append(txt)
    # collapse rolling-caption duplication: drop a line identical to the last kept one
    out = []
    for t in lines:
        if out and t == out[-1]:
            continue
        out.append(t)
    # join into paragraphs; YouTube ASR has no sentence punctuation, so wrap on word count
    words = " ".join(out).split()
    paras, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 80:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


HEADER = (
    "> **AUTOMATIC TRANSCRIPTION — ASR (YouTube auto-captions), expect word errors; "
    "NOT an official record.**\n"
    ">\n"
    "> Source: {url}  ·  video_id `{vid}`  ·  {body} meeting {date}\n"
    "> Retrieved {ret} via `yt-dlp --write-auto-sub` (en). The clerk's minutes in "
    "`meeting_minutes/` / `planning_commission/` remain the authoritative record.\n"
)


def main():
    idx = os.path.join(HERE, "index.csv")
    rows = [r for r in csv.DictReader(open(idx)) if r["format"] == "caption"]
    os.makedirs(os.path.join(HERE, "text"), exist_ok=True)
    for r in rows:
        vtt = os.path.join(HERE, r["path"])
        paras = clean_vtt(vtt)
        md = os.path.join(HERE, "text", f"{r['date']}.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write(HEADER.format(url=r["video_url"], vid=r["video_id"],
                                  body=r["body"], date=r["date"], ret=r["retrieved_date"]))
            f.write(f"\n# {r['title']}\n\n")
            for p in paras:
                f.write(p + "\n\n")
        print(f"{r['date']}  {len(paras):4d} paras  {os.path.getsize(md):8d} B  <- {r['path']}")


if __name__ == "__main__":
    main()
