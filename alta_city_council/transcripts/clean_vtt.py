#!/usr/bin/env python3
"""Convert a YouTube auto-caption VTT into a de-duplicated plain-text markdown
transcript with the mandatory ASR header. YouTube auto-subs stream each line
twice (rolling caption effect) with inline word-timing tags; we strip the tags,
drop the rolling duplicates, and keep readable paragraphs with periodic
timestamps."""
import re, sys, os

def clean(vtt_path):
    lines = open(vtt_path, encoding="utf-8").read().splitlines()
    seen = []
    cur_ts = None
    for ln in lines:
        m = re.match(r"(\d{2}:\d{2}:\d{2})\.\d{3}\s*-->", ln)
        if m:
            cur_ts = m.group(1)
            continue
        if ln.strip() in ("", "WEBVTT") or ln.startswith("Kind:") or ln.startswith("Language:"):
            continue
        # strip inline timing tags <00:00:00.400><c> word</c>
        txt = re.sub(r"<[^>]+>", "", ln)
        txt = txt.replace("&gt;&gt;", ">>").replace("&nbsp;", " ").strip()
        if not txt:
            continue
        seen.append((cur_ts, txt))
    # de-dup rolling repeats: keep a line only if it isn't a prefix-continuation
    out = []
    last = ""
    for ts, txt in seen:
        if txt == last:
            continue
        # rolling caption: previous is a prefix of current -> replace
        if last and txt.startswith(last):
            out[-1] = (out[-1][0], txt)
            last = txt
            continue
        out.append((ts, txt))
        last = txt
    return out

def render(rows, meta):
    hdr = [
        f"# {meta['title']}",
        "",
        "> **AUTOMATIC TRANSCRIPTION — ASR, expect word errors; NOT an official record.**",
        f"> Source: YouTube auto-generated English captions (`en`).",
        f"> Video: {meta['video_url']} (id `{meta['video_id']}`)  ·  Body: {meta['body']}  ·  Meeting date: {meta['date']}",
        f"> Retrieved: {meta['retrieved']} via yt-dlp --write-auto-sub.  The authoritative record is the clerk's minutes in `meeting_minutes/`.",
        "",
        "---",
        "",
    ]
    body = []
    para = []
    last_stamp = None
    for i, (ts, txt) in enumerate(rows):
        if last_stamp is None or (ts and ts[:5] != last_stamp):
            if para:
                body.append(" ".join(para)); para = []
            if ts:
                body.append(f"\n**[{ts}]**\n")
                last_stamp = ts[:5]
        para.append(txt)
    if para:
        body.append(" ".join(para))
    return "\n".join(hdr) + "\n".join(body) + "\n"

if __name__ == "__main__":
    raw, out_md, date, vid, title, body, url, retrieved = sys.argv[1:9]
    rows = clean(raw)
    meta = dict(title=title, video_url=url, video_id=vid, body=body,
                date=date, retrieved=retrieved)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(render(rows, meta))
    print(f"wrote {out_md}: {len(rows)} caption lines")
