#!/usr/bin/env python3
"""For each video-flagged SuiteOne event (_suiteone_events.csv, has_video=yes), fetch the
event page and extract the S3 MP4 recording URL
(var src = 'https://s3.amazonaws.com/suiteone.holladayut.videofiles/<hash>.mp4').
Also detect a JWPlayer caption/<track> reference (there are none — SuiteOne serves
video-only). Polite: browser UA, >=1s/request. Writes _suiteone_video.csv.

Usage: python3 resolve_suiteone_video.py
"""
import csv, re, time, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")
BASE = "https://holladayut.suiteonemedia.com/event/?id="
SRC_RE = re.compile(r"var src\s*=\s*'([^']+\.mp4)'")
TRACK_RE = re.compile(r'(\.vtt|kind:\s*["\']?captions|<track\b|tracks:\s*\[)', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def main():
    events = [r for r in csv.DictReader(open("_suiteone_events.csv"))
              if r["has_video"] == "yes"]
    out = []
    for i, e in enumerate(events, 1):
        url = BASE + e["event_id"]
        mp4, vid, cap = "", "", "no"
        try:
            html = fetch(url)
            m = SRC_RE.search(html)
            if m:
                mp4 = m.group(1)
                vid = mp4.rsplit("/", 1)[-1].replace(".mp4", "")
            if TRACK_RE.search(html):
                cap = "yes"
        except Exception as ex:
            mp4 = f"ERROR: {ex}"
        out.append({**e, "event_url": url, "video_mp4": mp4,
                    "video_id": vid, "caption_track": cap})
        print(f"[{i}/{len(events)}] {e['date']} {e['body']:18s} id={e['event_id']} -> {vid or mp4}")
        time.sleep(1.1)
    with open("_suiteone_video.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    got = sum(1 for r in out if r["video_id"])
    capd = sum(1 for r in out if r["caption_track"] == "yes")
    print(f"\nresolved {got}/{len(out)} MP4 urls; {capd} with a caption track")


if __name__ == "__main__":
    main()
