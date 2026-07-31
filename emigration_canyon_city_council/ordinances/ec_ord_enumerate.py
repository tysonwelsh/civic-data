#!/usr/bin/env python3
"""ec_ord_enumerate.py — enumerate Emigration Canyon adopted ordinances +
resolutions on MunicipalCodeOnline (public AWS S3 bucket), GET-only.

The correct S3 slug is `emigrationcanyon` (the bare `emigration` slug is empty).
The `ordinances/` and `resolutions/` prefixes both mix ordinance + resolution
PDFs (the vendor filed them loosely), so we page BOTH.

Writes ordinances/_s3_manifest.csv: prefix,key,filename,size,last_modified

Usage: python3 ec_ord_enumerate.py
"""
import csv
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
SLUG = "emigrationcanyon"
# harvest ALL adopted-instrument prefixes. Unlike the white_city sibling, EC's
# vendor also uses `orddoc/` (city-era 2025-O/2026-O signed ordinances + an
# "Ordinance Log.xlsx") and `policies/` (2 stray adopted instruments).
PREFIXES = [f"{SLUG}/ordinances/", f"{SLUG}/resolutions/",
            f"{SLUG}/orddoc/", f"{SLUG}/policies/"]
PROBE_ONLY = [f"{SLUG}/plan/", f"{SLUG}/fees/", f"{SLUG}/"]
UA = "Mozilla/5.0 (civic-data ordinances harvest; polite GET)"
HERE = os.path.dirname(os.path.abspath(__file__))


def list_prefix(prefix):
    rows = []
    token = None
    while True:
        url = f"{BUCKET}?list-type=2&prefix={urllib.parse.quote(prefix)}&max-keys=1000"
        if token:
            url += f"&continuation-token={urllib.parse.quote(token)}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            xml = r.read()
        root = ET.fromstring(xml)
        for c in root.findall(f"{NS}Contents"):
            key = c.findtext(f"{NS}Key")
            if key.endswith("/"):
                continue
            rows.append((prefix, key, os.path.basename(key),
                         c.findtext(f"{NS}Size"), c.findtext(f"{NS}LastModified")))
        if root.findtext(f"{NS}IsTruncated") == "true":
            token = root.findtext(f"{NS}NextContinuationToken")
        else:
            break
    return rows


def main():
    all_rows = []
    for p in PREFIXES:
        rows = list_prefix(p)
        print(f"{p}: {len(rows)} objects")
        all_rows.extend(rows)
    for p in PROBE_ONLY:
        try:
            rows = list_prefix(p)
            subs = sorted({r[1][len(p):].split('/')[0] for r in rows})
            print(f"PROBE {p}: {len(rows)} objects; sub-keys: {subs[:20]}")
        except Exception as e:
            print(f"PROBE {p}: ERROR {e}")
    out = os.path.join(HERE, "_s3_manifest.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prefix", "key", "filename", "size", "last_modified"])
        w.writerows(all_rows)
    print(f"wrote {out} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
