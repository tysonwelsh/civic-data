#!/usr/bin/env python3
"""ec_ord_build_batch.py — turn _s3_manifest.csv into a polite_fetch batch file.

Fetches EVERY object verbatim (RETAIN EVERY RAW ORIGINAL) — dedup/exclusion is a
LATER, index-time decision, never a fetch-time drop. Writes _fetch_batch.csv with
`url,localname` rows. The S3 key is percent-encoded for the URL; the local name is
the key basename with spaces/odd chars -> underscore (the S3 upload-id prefix keeps
same-named instruments from colliding on disk).

Usage: python3 ec_ord_build_batch.py
"""
import csv
import os
import re
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"


def localname(fn):
    base = re.sub(r"[^0-9A-Za-z._-]+", "_", fn).strip("_")
    return base


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv"))))
    seen = {}
    out = os.path.join(HERE, "_fetch_batch.csv")
    n = 0
    with open(out, "w", newline="") as f:
        for r in rows:
            key = r["key"]
            url = BUCKET + urllib.parse.quote(key)
            name = localname(r["filename"])
            # guard against any (unexpected) local-name collision
            if name in seen and seen[name] != key:
                stem, ext = os.path.splitext(name)
                name = f"{stem}_{n}{ext}"
            seen[name] = key
            f.write(f"{url},{name}\n")
            n += 1
    print(f"wrote {out} ({n} rows)")


if __name__ == "__main__":
    main()
