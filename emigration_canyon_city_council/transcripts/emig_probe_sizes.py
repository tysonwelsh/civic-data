#!/usr/bin/env python3
"""Emigration Canyon transcripts — HEAD-probe every PMN audio URL for liveness + size.

Reads emig_audio_inventory.csv, issues a polite throttled HTTP HEAD per audio URL
(NO body GET — we never download the MP3s), and writes emig_audio_sizes.csv
(audio_url, http, content_type, bytes). This is the liveness check (live 200 vs
purged 404 — the pre-~mid-2018 PMN blob rot that also took the township-era
2017/2018 minutes, see meeting_minutes/minutes_unrecovered.csv) and the Whisper
cost basis. GET-only policy: HEAD is lighter than GET and touches no bytes. Fetch
host is www.utah.gov (pmn.utah.gov 302-redirects to the PMN home HTML).
"""
import csv
import os
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def head(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return (str(r.status), r.headers.get("Content-Type", ""),
                    r.headers.get("Content-Length", ""))
    except urllib.error.HTTPError as e:
        return (str(e.code), "", "")
    except Exception as e:
        return ("ERR", type(e).__name__, "")


def main():
    inv = os.path.join(HERE, "emig_audio_inventory.csv")
    urls = []
    seen = set()
    for r in csv.DictReader(open(inv)):
        u = r["audio_url"]
        if u not in seen:
            seen.add(u)
            urls.append(u)
    out = os.path.join(HERE, "emig_audio_sizes.csv")
    live = purged = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["audio_url", "http", "content_type", "bytes"])
        for i, u in enumerate(urls, 1):
            http, ct, byts = head(u)
            w.writerow([u, http, ct, byts])
            if http == "200":
                live += 1
            elif http == "404":
                purged += 1
            if i % 25 == 0:
                print(f"  {i}/{len(urls)} probed (live {live}, 404 {purged})")
            time.sleep(0.4)
    print(f"probed {len(urls)} urls: live {live}, 404 {purged}, "
          f"other {len(urls) - live - purged}")


if __name__ == "__main__":
    main()
