#!/usr/bin/env python3
"""Convert a YouTube ASR .vtt caption track to cleaned markdown (South Salt Lake).

Strips <c>/<timestamp> inline tags, unescapes HTML entities (YouTube ASR sometimes
embeds &gt;&gt; speaker markers), and collapses YouTube's rolling-caption
triple-repetition. Output is ASR quality (word errors expected) — never an official record.

Usage: clean_captions_ssl.py <vtt> <out_md> <date> <body> <video_id>
"""
import sys, re, html, textwrap

HDR = ("**AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official "
       "record.** YouTube auto-generated captions from the official South Salt Lake "
       "City channel (@SouthSaltLakeCity, UCnIf0PqrH3cERoBB-vyhrbA); speaker labels are "
       "absent and proper nouns (member names, street/case/ordinance numbers) are "
       "frequently misrecognized. The authoritative record is the clerk's minutes under "
       "`meeting_minutes/` / `planning_commission/` — and note the SSL coverage cliff: for "
       "2021-mid..2025 recorded minutes were often not published, so for many of these "
       "meetings this ASR stream is the ONLY substantive record of the deliberation.")


def clean(vtt_path):
    raw = open(vtt_path, encoding="utf-8").read()
    out, last = [], None
    for block in re.split(r"\n\n+", raw):
        b = block.strip("\n")
        if not b or b.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        for ln in b.split("\n"):
            if "-->" in ln:
                continue
            t = re.sub(r"<[^>]+>", "", ln)          # drop <c>, <00:00:..> tags
            t = html.unescape(t).replace("\xa0", " ").strip()
            if not t or t == last:                  # rolling-caption duplicate
                continue
            out.append(t)
            last = t
    return " ".join(out)


def main():
    vtt, outp, date, body, vid = sys.argv[1:6]
    text = clean(vtt)
    wrapped = "\n".join(textwrap.wrap(text, 100)) if text else "(no caption text extracted)"
    md = (f"# South Salt Lake City — {body} meeting stream, {date} (AUTOMATIC TRANSCRIPTION)\n\n"
          f"> {HDR}\n\n"
          f"- **Date:** {date}\n- **Body (inferred):** {body}\n"
          f"- **Video:** https://www.youtube.com/watch?v={vid}\n"
          f"- **Channel:** South Salt Lake City (youtube.com/@SouthSaltLakeCity)\n"
          f"- **Caption type:** automatic (YouTube ASR, en)\n\n---\n\n{wrapped}\n")
    open(outp, "w", encoding="utf-8").write(md)
    print(f"{date} {body}: {len(text.split())} words -> {outp}")


if __name__ == "__main__":
    main()
