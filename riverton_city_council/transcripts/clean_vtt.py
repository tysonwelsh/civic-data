#!/usr/bin/env python3
"""Convert a YouTube ASR .vtt caption track to a cleaned, de-duplicated markdown
transcript (Riverton City). Strips <c>/<timestamp> inline tags and collapses
YouTube's rolling-caption repetition. Output is ASR-quality (word errors expected).

Usage: clean_vtt.py <vtt> <out_md> <date> <body> <video_id> <channel_label>
  channel_label e.g. "Riverton City (official, youtube.com/rivertonutahgov)"
"""
import sys, re, textwrap

HDR = ("**AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official "
       "record.** YouTube auto-generated captions; speaker labels are absent and "
       "proper nouns (names, street/case numbers, dollar figures, vote tallies) are "
       "frequently misrecognized. The authoritative record is the clerk's minutes "
       "under `meeting_minutes/` / `planning_commission/`; the authoritative video is "
       "the Granicus clip (see index.csv granicus_* columns / granicus_clips.csv).")


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
            t = t.replace('&nbsp;', ' ').strip()
            if not t or t == last:               # rolling-caption duplicate
                continue
            lines_out.append(t)
            last = t
    return ' '.join(lines_out)


def main():
    vtt, out, date, body, vid, chan = sys.argv[1:7]
    text = clean(vtt)
    wrapped = '\n'.join(textwrap.wrap(text, 100)) if text else '(no caption text extracted)'
    md = (f"# Riverton City — {body} meeting, {date} (AUTOMATIC TRANSCRIPTION)\n\n"
          f"> {HDR}\n\n"
          f"- **Date:** {date}\n- **Body:** {body}\n"
          f"- **Video:** https://www.youtube.com/watch?v={vid}\n"
          f"- **Channel:** {chan}\n"
          f"- **Caption type:** automatic (YouTube ASR, en)\n\n---\n\n{wrapped}\n")
    open(out, 'w', encoding='utf-8').write(md)
    print(f"{date}: {len(text.split())} words -> {out}")


if __name__ == '__main__':
    main()
