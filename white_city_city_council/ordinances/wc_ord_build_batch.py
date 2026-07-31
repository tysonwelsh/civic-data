#!/usr/bin/env python3
"""wc_ord_build_batch.py — turn _s3_manifest.csv into a polite_fetch batch
(url,name), excluding cross-entity/out-of-scope decoys.

Excludes (documented in CLAUDE.md):
  - Copperton subdivision amendment (wrong entity)
  - the two 2019 Moderate-Income-Housing PDFs (housing_plans dataset scope)
Everything else — including exact re-upload duplicates of the same instrument
number — is fetched so every raw original is retained.

Writes ordinances/_fetch_batch.csv (url,name).
"""
import csv
import os
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"

EXCLUDE_SUBSTR = [
    "Copperton",
    "Moderate Income Housing",
    "Moderate-Income Housing",
]


def sanitize(name):
    return name.replace(" ", "_")


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv"))))
    out = []
    skipped = []
    seen = {}
    for r in rows:
        key = r["key"]
        fn = r["filename"]
        if any(s.lower() in fn.lower() for s in EXCLUDE_SUBSTR):
            skipped.append(fn)
            continue
        url = BUCKET + urllib.parse.quote(key)
        name = sanitize(fn)
        # guard against name collisions (shouldn't happen given ts prefixes)
        if name in seen:
            base, ext = os.path.splitext(name)
            name = f"{base}__dup{ext}"
        seen[name] = key
        out.append((url, name))
    with open(os.path.join(HERE, "_fetch_batch.csv"), "w", newline="") as f:
        w = csv.writer(f)
        for u, n in out:
            w.writerow([u, n])
    print(f"batch: {len(out)} to fetch; skipped {len(skipped)} decoys/out-of-scope:")
    for s in skipped:
        print("   SKIP", s)


if __name__ == "__main__":
    main()
