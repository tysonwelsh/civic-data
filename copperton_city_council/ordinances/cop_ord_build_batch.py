#!/usr/bin/env python3
"""cop_ord_build_batch.py — turn the in_scope rows of _s3_manifest.csv into a
polite_fetch batch (url,name).

Copperton reuses bare basenames across subfolders (e.g. `Ordinance 17-02-01.pdf`
lives in ordinances/ AND orddoc/), so the saved NAME is made collision-proof:
subfolder tag + sanitized basename, de-duped with a numeric suffix. The durable
join back to the S3 key/last_modified is by URL (see cop_ord_index.py), never by
the saved name — so a name clash can never conflate two distinct instruments.

Everything in_scope is fetched (every raw original retained), including
byte-identical re-uploads; sha256 dedup happens later, in the index, from the
fetch log. Cross-entity decoys are excluded at INDEX time (after caption
screening), not here — we retain their raw bytes too.

Writes ordinances/_fetch_batch.csv (url,name).
"""
import csv
import os
import re
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"


def sanitize(name):
    return re.sub(r"[^\w.\-]+", "_", name).strip("_")


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv"))))
    out = []
    seen = set()
    for r in rows:
        if r["in_scope"] != "yes":
            continue
        key = r["key"]
        sub = r["subfolder"]
        base = sanitize(r["filename"])
        # tag with subfolder only when it is NOT one of the two "canonical"
        # ord/res folders, to keep the common case tidy while guaranteeing
        # uniqueness for the scattered ones.
        name = base if sub in ("ordinances", "resolutions") else f"{sub}__{base}"
        if name in seen:
            stem, ext = os.path.splitext(name)
            i = 2
            while f"{stem}__{i}{ext}" in seen:
                i += 1
            name = f"{stem}__{i}{ext}"
        seen.add(name)
        url = BUCKET + urllib.parse.quote(key)
        out.append((url, name))
    with open(os.path.join(HERE, "_fetch_batch.csv"), "w", newline="") as f:
        w = csv.writer(f)
        for u, n in out:
            w.writerow([u, n])
    print(f"batch: {len(out)} in-scope instrument PDFs to fetch")


if __name__ == "__main__":
    main()
