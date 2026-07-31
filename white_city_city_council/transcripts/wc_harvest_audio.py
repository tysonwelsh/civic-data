#!/usr/bin/env python3
"""White City transcripts — harvest the Streamline audio (MP3/M4A) inventory.

Parses the saved Streamline council year pages + meetings-archive (in raw/,
files _page_*.html) for audio attachments. Each attachment anchor carries an
aria-label of the form:
    "<filename> attachment for <YYYY-MM-DD> <Meeting Title> Meeting"
which yields the meeting date + title without guessing the opaque /files/<hash>/.

Emits wc_audio_inventory.csv (audio->date map). Audio-first entity: NO captions
exist on these MP3s (per the audio-only-city branch of expand-city-sources) ->
Whisper is a PROPOSAL only; nothing is downloaded here.
"""
import re, csv, glob, os

RAW = os.path.join(os.path.dirname(__file__), "raw")
BASE = "https://whitecity.utah.gov"

# <li class="attachment"><a href="/files/<hash>/<file>" aria-label="<label>" ...>
ANCHOR = re.compile(
    r'<a href="(?P<href>/files/[a-z0-9]+/[^"]+)"\s+aria-label="(?P<label>[^"]*)"',
    re.I,
)
LABEL = re.compile(
    r'^(?P<fname>.+?)\s+attachment for\s+(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<title>.*?)\s*$'
)

def source_year(fname):
    m = re.search(r'_page_council_(\d{4})\.html', fname)
    if m: return m.group(1)
    if 'archive' in fname: return 'archive'
    if 'current' in fname: return 'current'
    return '?'

rows = {}
for pg in sorted(glob.glob(os.path.join(RAW, "_page_*.html"))):
    html = open(pg, encoding="utf-8", errors="replace").read()
    yr = source_year(os.path.basename(pg))
    for a in ANCHOR.finditer(html):
        href = a.group("href")
        ext = href.rsplit(".", 1)[-1].lower()
        if ext not in ("mp3", "m4a"):
            continue
        label = a.group("label")
        lm = LABEL.match(label)
        date = ""
        if lm:
            date = lm.group("date")
        # Titles in the aria-label are noisy ("Council Meeting Council Meeting");
        # normalize to a clean, date-stamped council-meeting title.
        title = f"{date} White City Council Meeting" if date else "White City Council Meeting"
        fname = href.rsplit("/", 1)[-1]
        key = href
        rows[key] = {
            "date": date,
            "title": title,
            "audio_filename": fname,
            "audio_url": BASE + href,
            "ext": ext,
            "source_page_year": yr,
        }

out = os.path.join(os.path.dirname(__file__), "wc_audio_inventory.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date","title","audio_filename","audio_url","ext","source_page_year"])
    w.writeheader()
    for r in sorted(rows.values(), key=lambda x: (x["date"] or "0000", x["audio_filename"])):
        w.writerow(r)

print(f"audio attachments found: {len(rows)}")
dated = [r for r in rows.values() if r["date"]]
print(f"dated: {len(dated)}; undated: {len(rows)-len(dated)}")
if dated:
    ds = sorted(r["date"] for r in dated)
    print(f"date range: {ds[0]} .. {ds[-1]}")
from collections import Counter
print("by ext:", dict(Counter(r["ext"] for r in rows.values())))
print("by source page:", dict(Counter(r["source_page_year"] for r in rows.values())))
