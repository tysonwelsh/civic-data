#!/usr/bin/env python3
"""Clean a YouTube auto-caption (ASR) .vtt into readable markdown.

YouTube's automatic-caption VTT uses a "rolling" 2-line window: each cue repeats the
previous line plus one new line, and carries inline <timestamp><c> word-timing tags.
Naive text extraction therefore triples every line. This script:
  - strips WEBVTT header, NOTE blocks, cue-timing lines, and inline <...> tags
  - collapses the rolling duplicates to one clean stream of unique lines (in order)
  - wraps the result under the mandatory ASR-quality banner

It does NOT "fix" wording — ASR errors are preserved verbatim (per extraction discipline).

Usage: clean_vtt.py <in.vtt> <out.md> <date> <body_label> <video_url> <video_id>
"""
import re, sys, html

def parse(path):
    lines_out = []
    seen_recent = []  # small window to suppress rolling repeats
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    # Split into cue blocks by blank lines
    block = []
    def flush(block):
        # find text lines (skip the timing line containing '-->')
        texts = []
        for ln in block:
            if "-->" in ln:
                continue
            if ln.strip() in ("WEBVTT",) or ln.startswith("Kind:") or ln.startswith("Language:"):
                continue
            if ln.startswith("NOTE"):
                continue
            texts.append(ln)
        for ln in texts:
            # strip inline timing tags <00:00:01.234> and <c> ... </c>
            t = re.sub(r"<[^>]+>", "", ln)
            t = html.unescape(t).strip()
            if not t:
                continue
            # suppress if identical to any of the last few emitted lines (rolling dup)
            if t in seen_recent:
                continue
            lines_out.append(t)
            seen_recent.append(t)
            if len(seen_recent) > 4:
                seen_recent.pop(0)
    for ln in raw.splitlines():
        if ln.strip() == "":
            if block:
                flush(block)
                block = []
        else:
            block.append(ln)
    if block:
        flush(block)
    return lines_out

def main():
    inp, outp, date, body, url, vid = sys.argv[1:7]
    lines = parse(inp)
    text = "\n".join(lines)
    banner = ("**AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; "
              "NOT an official record.**")
    header = (f"# West Jordan {body} — {date}\n\n"
              f"{banner}\n\n"
              f"- Source video: {url}\n"
              f"- YouTube video id: `{vid}`\n"
              f"- Caption track: `en-orig` (YouTube automatic speech recognition)\n"
              f"- Extraction: yt-dlp --write-auto-sub --sub-lang en-orig (vtt), "
              f"rolling-dedup via clean_vtt.py\n\n"
              f"---\n\n")
    with open(outp, "w", encoding="utf-8") as f:
        f.write(header + text + "\n")
    print(f"{outp}: {len(lines)} lines, {len(text)} chars")

if __name__ == "__main__":
    main()
