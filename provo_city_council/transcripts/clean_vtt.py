#!/usr/bin/env python3
"""De-duplicate YouTube auto-caption VTT rolling-window triplication -> clean markdown.

YouTube ASR VTT repeats each spoken line ~2-3x: once WITH inline <HH:MM:SS><c>word</c>
timing tags (the freshly-spoken version), then again as plain context in the next cue(s).
We keep only the tag-carrying lines, strip the tags, and collapse to prose. A trailing
consecutive-dedup guards the rare line that lacks inline tags.

Usage: clean_vtt.py <raw.vtt> <out.md> <date> <body_label> <video_url>
"""
import re, sys, html

TAG = re.compile(r'<(\d{2}:\d{2}:\d{2}\.\d{3})>')       # inline word timestamp
CTAG = re.compile(r'</?c[^>]*>')                          # <c>...</c>
CUEHDR = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->')

def clean(vtt_path):
    lines = []
    for raw in open(vtt_path, encoding='utf-8', errors='replace'):
        line = raw.rstrip('\n')
        if not line or line.startswith(('WEBVTT', 'Kind:', 'Language:')):
            continue
        if CUEHDR.match(line):
            continue
        # keep only "fresh" lines that carry inline word timing
        if not TAG.search(line):
            continue
        txt = CTAG.sub('', TAG.sub('', line))
        txt = html.unescape(txt)
        txt = re.sub(r'\s+', ' ', txt).strip()
        if txt:
            lines.append(txt)
    # drop accidental consecutive duplicates
    out = []
    for l in lines:
        if not out or out[-1] != l:
            out.append(l)
    return out

def main():
    vtt, outp, date, body, url = sys.argv[1:6]
    lines = clean(vtt)
    text = ' '.join(lines)
    # re-wrap into paragraphs ~ every 60 words for readability
    words = text.split()
    paras, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 60:
            paras.append(' '.join(cur)); cur = []
    if cur:
        paras.append(' '.join(cur))
    header = (
        f"# Provo — {body} — {date}\n\n"
        "**AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; NOT an official record.**\n\n"
        f"- Source: YouTube auto-captions (en-orig), {url}\n"
        f"- Meeting date: {date}\n"
        f"- Body: {body}\n"
        f"- Caption type: asr (YouTube automatic speech recognition)\n"
        f"- De-duplicated from rolling-window VTT ({len(lines)} caption segments).\n\n"
        "---\n\n"
    )
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n\n'.join(paras))
        f.write('\n')
    print(f"{outp}: {len(words)} words, {len(lines)} segments")

if __name__ == '__main__':
    main()
