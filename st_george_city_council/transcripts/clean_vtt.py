#!/usr/bin/env python3
"""Convert a YouTube ASR .vtt caption track to a cleaned, de-duplicated markdown
transcript. Strips <c>/<timestamp> inline tags and collapses YouTube's rolling-
caption repetition. Output is ASR-quality (word errors expected)."""
import sys, re, textwrap

HDR = ("**AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; "
       "NOT an official record.**")

def clean(vtt_path):
    raw = open(vtt_path, encoding='utf-8').read()
    lines_out = []
    last = None
    for block in re.split(r'\n\n+', raw):
        b = block.strip('\n')
        if not b or b.startswith('WEBVTT') or b.startswith('Kind:') or b.startswith('Language:'):
            continue
        for ln in b.split('\n'):
            if '-->' in ln:            # timestamp line
                continue
            t = re.sub(r'<[^>]+>', '', ln)      # drop <c>, <00:00:...> tags
            t = t.replace('&nbsp;', ' ').strip()
            if not t:
                continue
            if t == last:              # rolling-caption duplicate
                continue
            lines_out.append(t)
            last = t
    return ' '.join(lines_out)

def main():
    vtt, out, date, title, url, vid = sys.argv[1:7]
    body = clean(vtt)
    wrapped = '\n'.join(textwrap.wrap(body, 100)) if body else '(no caption text extracted)'
    md = (f"# St. George City Council — {date}\n\n{HDR}\n\n"
          f"- **Meeting:** {title}\n- **Date:** {date}\n- **Body:** CityCouncil\n"
          f"- **Video:** {url}\n- **Video ID:** {vid}\n"
          f"- **Caption type:** automatic (YouTube ASR, en-orig)\n\n---\n\n{wrapped}\n")
    open(out, 'w', encoding='utf-8').write(md)
    print(f"{date}: {len(body.split())} words -> {out}")

if __name__ == '__main__':
    main()
