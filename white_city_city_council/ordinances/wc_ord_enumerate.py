#!/usr/bin/env python3
"""wc_ord_enumerate.py — enumerate White City adopted ordinances + resolutions
on MunicipalCodeOnline (public S3 bucket), GET-only.

Writes ordinances/_s3_manifest.csv with columns:
    prefix,key,filename,size,last_modified

Usage: python3 wc_ord_enumerate.py
"""
import csv
import os
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PREFIXES = ["whitecity/ordinances/", "whitecity/resolutions/"]
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
            size = c.findtext(f"{NS}Size")
            lm = c.findtext(f"{NS}LastModified")
            if key.endswith("/"):
                continue
            rows.append((prefix, key, os.path.basename(key), size, lm))
        if root.findtext(f"{NS}IsTruncated") == "true":
            token = root.findtext(f"{NS}NextContinuationToken")
        else:
            break
    return rows


def main():
    import urllib.parse  # noqa
    all_rows = []
    for p in PREFIXES:
        rows = list_prefix(p)
        print(f"{p}: {len(rows)} objects")
        all_rows.extend(rows)
    out = os.path.join(HERE, "_s3_manifest.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prefix", "key", "filename", "size", "last_modified"])
        w.writerows(all_rows)
    print(f"wrote {out} ({len(all_rows)} rows)")


if __name__ == "__main__":
    import urllib.parse
    main()
