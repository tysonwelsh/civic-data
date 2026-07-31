#!/usr/bin/env python3
"""Recover and record the **Wayback snapshot URL** for every legislative minutes document
whose live county URL is dead.

WHY (audit 2026-07-25 F16, repaired 2026-07-29)
-----------------------------------------------
`fetch_minutes.py` falls back to the Internet Archive when a county URL 404s, and it tags
the resulting row `provenance=wayback_minutes` / `wayback_ocr` -- but it stored only the
**dead live URL** and threw the snapshot address away.  The county deleted its whole 2024
`countycouncil/2024/Minutes/` folder, so those 25 documents had **no reproducible
provenance pointer at all**: following `source_url` gives a 404 and there was nothing else
to follow.

This script re-derives the pointer from the Wayback **CDX API** -- the same public channel
`ut_state` used for its advisory opinions and statutes -- and records it as an ADDITION:

  * `legislative/minutes_index.csv` gains `snapshot_url` + `snapshot_timestamp`
    (blank for documents still served live).
  * each recovered document's markdown front-matter gains the same two keys.
  * `legislative/wayback_snapshots.csv` is the standalone provenance ledger: live URL,
    its measured HTTP status, the chosen snapshot, its byte size, and how many distinct
    snapshots the archive holds.

**`source_url` is never overwritten.**  A dead live URL is a true historical fact -- it is
where the county published the document -- and the snapshot is an addition beside it.

Snapshot choice: the EARLIEST `statuscode:200` `application/pdf` capture, i.e. the one
closest to the document's own publication.  All captures are counted in the ledger so a
re-verifier can pick another.

Politeness: one CDX request per document, 1.5 s apart, no parallelism.

Idempotent -- rerun any time; re-running refreshes statuses and adds nothing twice.
Usage:  python3 legislative/recover_snapshots.py
"""
import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
INDEX = os.path.join(HERE, "minutes_index.csv")
LEDGER = os.path.join(HERE, "wayback_snapshots.csv")

UA = {"User-Agent": "civic-data-archive/1.0 (provenance recovery; +cache_county)"}
CDX = ("https://web.archive.org/cdx/search/cdx?url=%s&output=json"
       "&filter=statuscode:200&filter=mimetype:application/pdf"
       "&fl=timestamp,original,mimetype,length&collapse=digest")
DELAY = 1.5

LEDGER_COLS = ["date", "body", "basename", "provenance", "live_url", "live_status",
               "snapshot_url", "snapshot_timestamp", "snapshot_bytes", "snapshot_count",
               "note"]


def http_status(url):
    enc = urllib.parse.quote(url, safe=":/?&=%")
    try:
        req = urllib.request.Request(enc, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception as e:                                    # network/DNS/TLS
        return "ERR:%s" % type(e).__name__


def cdx_snapshots(url):
    q = CDX % urllib.parse.quote(url, safe="")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(q, headers=UA),
                                        timeout=60) as resp:
                data = json.loads(resp.read().decode() or "[]")
            return data[1:] if len(data) > 1 else []
        except Exception as e:
            print("    cdx retry (%s)" % type(e).__name__)
            time.sleep(5)
    return []


def snapshot_url(timestamp, original):
    """`id_` = the raw archived bytes, no Wayback banner/rewriting."""
    return "https://web.archive.org/web/%sid_/%s" % (
        timestamp, urllib.parse.quote(original, safe=":/%?&="))


def patch_front_matter(md_path, snap_url, snap_ts):
    """Insert/refresh snapshot_url + snapshot_timestamp directly under source_url."""
    path = os.path.join(COUNTY, md_path)
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    body = re.sub(r"^snapshot_(url|timestamp): .*\n", "", text, flags=re.M)
    new = re.sub(r"^(source_url: .*\n)",
                 r"\1snapshot_url: %s\nsnapshot_timestamp: %s\n"
                 % (snap_url.replace("\\", "\\\\"), snap_ts),
                 body, count=1, flags=re.M)
    if new == body and "snapshot_url:" not in new:
        return False
    if new != text:
        open(path, "w", encoding="utf-8").write(new)
    return True


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    cols = list(rows[0].keys())
    for extra in ("snapshot_url", "snapshot_timestamp"):
        if extra not in cols:
            cols.append(extra)
    for r in rows:
        r.setdefault("snapshot_url", "")
        r.setdefault("snapshot_timestamp", "")

    targets = [r for r in rows if r["provenance"].startswith("wayback")]
    print("wayback-recovered documents: %d of %d" % (len(targets), len(rows)))

    ledger, recovered, unrecoverable = [], 0, []
    for r in targets:
        live = r["source_url"]
        status = http_status(live)
        snaps = cdx_snapshots(live)
        note = ""
        if snaps:
            ts, original, _mime, length = snaps[0][0], snaps[0][1], snaps[0][2], snaps[0][3]
            url = snapshot_url(ts, original)
            r["snapshot_url"], r["snapshot_timestamp"] = url, ts
            patch_front_matter(r["md_path"], url, ts)
            recovered += 1
        else:
            ts = url = length = ""
            note = ("NO Wayback capture -- unrecoverable on every known channel "
                    "(live 404 + archive miss); the repo's markdown IS the only copy")
            unrecoverable.append(r["date"])
        ledger.append({"date": r["date"], "body": r["body"], "basename": r["basename"],
                       "provenance": r["provenance"], "live_url": live,
                       "live_status": status, "snapshot_url": url,
                       "snapshot_timestamp": ts, "snapshot_bytes": length,
                       "snapshot_count": len(snaps), "note": note})
        print("  %s  live=%s  snapshots=%d  %s" % (r["date"], status, len(snaps), ts))
        time.sleep(DELAY)

    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(LEDGER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        w.writeheader()
        w.writerows(ledger)

    print("snapshot URLs recovered: %d / %d" % (recovered, len(targets)))
    if unrecoverable:
        print("UNRECOVERABLE (honest gap, logged in wayback_snapshots.csv): %s"
              % ", ".join(unrecoverable))


if __name__ == "__main__":
    main()
