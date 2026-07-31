#!/usr/bin/env python3
"""Emigration Canyon transcripts — harvest the PMN meeting-audio (MP3) inventory.

Emigration Canyon (~1,600 pop; metro township 2017 -> City 2024-05-01) is
AUDIO-ONLY (the audio-only branch of expand-city-sources, like siblings
Copperton / Magna / White City): there is NO captioned video source. No YouTube
channel carries Emigration Canyon meetings (every plausible @Emigration* handle
404s except a personal "Noah plays piano" account that is a name-collision decoy,
0 government videos; the Utah Record mirror has 0 Emigration uploads -- see
raw/_emig_youtube_probe.txt, raw/_emig_channel_videos.txt,
raw/_utah_record_channel_titles.txt). The only durable recording medium is a
per-meeting audio file attached to each Utah Public Notice (PMN):

    Council              PMN body 5809   -> raw/_probe_5809_list.html
    Planning Commission  PMN body 1562   -> raw/_probe_1562_list.html  (MSD-staffed)

The cumulative list view `/pmn/list/notices.html?id=<body>&page=<big>` returns a
body's ENTIRE notice history in one GET, WITH the file links and their category
labels inline -- so we never open the individual notice pages.

Each notice is a <tr>: a title <a href="/pmn/sitemap/notice/<id>.html">, a
datetime <td> (YYYY/MM/DD hh:mm AM/PM), and a <ul> of attachment <li>s. Each <li>
is
    <a href="/pmn/files/<fid>.<ext>" aria-label="Download <filename> ...">...</a>
    &nbsp;(<Category>)
We keep the attachments whose EXTENSION is an audio type (mp3/m4a/wav) -- audio is
decided by extension, NOT the PMN category label. NOTE: Emigration Canyon uses an
UPPERCASE `.MP3` extension; extension matching is case-insensitive. The meeting
date comes from the MM-DD-YYYY in the audio filename, falling back to the notice
datetime.

Emits emig_audio_inventory.csv (one row per audio file). NO audio is downloaded --
these MP3s carry NO caption track; Whisper is a PROPOSAL only.
"""
import csv
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
PMN = "https://www.utah.gov/pmn"
AUDIO_EXT = {"mp3", "m4a", "wav"}

BODIES = {
    "5809": "Council",
    "1562": "Planning Commission",
}

NOTICE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>', re.S)
DATETIME = re.compile(r'<td>(\d{4})/(\d{2})/(\d{2})\s+[\d:]+\s*[AP]M</td>')
ATTACH = re.compile(
    r'<a href="/pmn/files/(\d+)\.([A-Za-z0-9]+)"[^>]*aria-label="Download\s+(.*?)\s*\(opens',
    re.S,
)
CATEGORY = re.compile(r'\(([^)]+)\)')
FNAME_DATE = re.compile(r'(\d{2})-(\d{2})-(\d{4})')          # MM-DD-YYYY in filename


def notice_blocks(html):
    """Yield (notice_id, title, iso_date, block_html) per notice <tr>."""
    parts = re.split(r'(?=<a href="/pmn/sitemap/notice/\d+\.html">)', html)
    for p in parts:
        nm = NOTICE.search(p)
        if not nm:
            continue
        nid = nm.group(1)
        title = re.sub(r'\s+', ' ', nm.group(2)).strip()
        dm = DATETIME.search(p)
        iso = f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}" if dm else ""
        yield nid, title, iso, p


def filename_iso(name, fallback):
    m = FNAME_DATE.search(name)
    if m:
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    return fallback


def harvest():
    rows = []
    for body_id, body in BODIES.items():
        path = os.path.join(RAW, f"_probe_{body_id}_list.html")
        html = open(path, encoding="utf-8", errors="replace").read()
        for nid, title, iso, block in notice_blocks(html):
            for am in ATTACH.finditer(block):
                fid, ext, fname = am.group(1), am.group(2), am.group(3).strip()
                ext_l = ext.lower()
                tail = block[am.end():am.end() + 120]
                cm = CATEGORY.search(tail)
                category = cm.group(1).strip() if cm else ""
                if ext_l not in AUDIO_EXT:
                    continue
                rows.append({
                    "body": body,
                    "pmn_body_id": body_id,
                    "notice_id": nid,
                    "notice_url": f"{PMN}/sitemap/notice/{nid}.html",
                    "notice_title": title,
                    "date": filename_iso(fname, iso),
                    "notice_date": iso,
                    "audio_url": f"{PMN}/files/{fid}.{ext}",
                    "pmn_file_id": fid,
                    "audio_filename": fname,
                    "media_type": ext_l,
                    "category": category,
                })
    rows.sort(key=lambda r: (r["date"] or "0000", r["body"], r["audio_filename"]))
    out = os.path.join(HERE, "emig_audio_inventory.csv")
    cols = ["body", "pmn_body_id", "notice_id", "notice_url", "notice_title",
            "date", "notice_date", "audio_url", "pmn_file_id",
            "audio_filename", "media_type", "category"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"audio attachments found: {len(rows)}")
    print("by body:", dict(Counter(r["body"] for r in rows)))
    print("by media_type:", dict(Counter(r["media_type"] for r in rows)))
    dated = [r for r in rows if r["date"]]
    print(f"dated: {len(dated)}; undated: {len(rows) - len(dated)}")
    if dated:
        ds = sorted(r["date"] for r in dated)
        print(f"date range: {ds[0]} .. {ds[-1]}")
    for body in BODIES.values():
        dd = sorted({r["date"] for r in rows if r["body"] == body and r["date"]})
        print(f"  {body}: {len(dd)} distinct meeting-dates with audio")
    return rows


if __name__ == "__main__":
    harvest()
