#!/usr/bin/env python3
"""Convert a YouTube ASR .vtt caption track to a cleaned, de-duplicated markdown
transcript (Cottonwood Heights City). Strips <c>/<timestamp> inline tags and collapses
YouTube's rolling-caption repetition. Output is ASR-quality (word errors expected).

Usage: ch_clean_vtt.py <vtt> <out_md> <date> <body> <video_id>
"""
import sys, re, textwrap, html

HDR = ("**AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official "
       "record.** YouTube auto-generated captions from the Cottonwood Heights City "
       "channel; speaker labels are absent and proper nouns (member names, ordinance/"
       "case numbers) are frequently misrecognized. The authoritative record is the "
       "clerk's minutes under `meeting_minutes/` / `planning_commission/`.")


def clean(vtt_path):
    raw = open(vtt_path, encoding='utf-8').read()
    lines_out, last = [], None
    for block in re.split(r'\n\n+', raw):
        b = block.strip('\n')
        if not b or b.startswith(('WEBVTT', 'Kind:', 'Language:')):
            continue
        for ln in b.split('\n'):
            if '-->' in ln:                      # cue timing line
                continue
            t = re.sub(r'<[^>]+>', '', ln)       # drop <c>, <00:00:...> tags
            t = html.unescape(t)                 # &gt;&gt; -> >> speaker markers, &amp; -> &
            t = t.replace(' ', ' ').strip()
            if not t or t == last:               # rolling-caption duplicate
                continue
            lines_out.append(t)
            last = t
    return ' '.join(lines_out)


def main():
    vtt, out, date, body, vid = sys.argv[1:6]
    text = clean(vtt)
    wrapped = '\n'.join(textwrap.wrap(text, 100)) if text else '(no caption text extracted)'
    md = (f"# Cottonwood Heights City — {body} meeting stream, {date} (AUTOMATIC TRANSCRIPTION)\n\n"
          f"> {HDR}\n\n"
          f"- **Date:** {date}\n- **Body (inferred):** {body}\n"
          f"- **Video:** https://www.youtube.com/watch?v={vid}\n"
          f"- **Channel:** Cottonwood Heights City (youtube.com/channel/UCcOhqM97RmMrEpUz_6L84Cw)\n"
          f"- **Caption type:** automatic (YouTube ASR, en)\n\n---\n\n{wrapped}\n")
    open(out, 'w', encoding='utf-8').write(md)
    print(f"{date}: {len(text.split())} words -> {out}")


if __name__ == '__main__':
    main()
