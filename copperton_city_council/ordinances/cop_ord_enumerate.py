#!/usr/bin/env python3
"""cop_ord_enumerate.py — enumerate Town of Copperton adopted ordinances +
resolutions on MunicipalCodeOnline (public S3 bucket), GET-only.

Copperton spreads adopted instruments across MANY subprefixes (not just the two
white_city/kearns use): ordinances/, resolutions/, orddoc/, fees/,
landordinances/, policies/, plan/. This lists the WHOLE `copperton/` tree once,
then classifies each object as:
  in_scope=yes  — an adopted ordinance/resolution INSTRUMENT PDF (fetch it)
  in_scope=no   — display image (png/jpg), site asset, or a non-instrument PLAN /
                  FEE-SCHEDULE / POLICY-PLAN exhibit that belongs to the
                  housing_plans/general-plan scope, not ordinances (note, don't fetch)

Writes ordinances/_s3_manifest.csv:
    prefix,subfolder,key,filename,size,last_modified,in_scope,scope_reason

Usage: python3 cop_ord_enumerate.py
"""
import csv
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PREFIX = "copperton/"
UA = "Mozilla/5.0 (civic-data ordinances harvest; polite GET)"
HERE = os.path.dirname(os.path.abspath(__file__))

# Non-instrument exhibit docs (plans / bare fee schedules) — real, but they are
# housing_plans/general-plan territory, NOT adopted ord/res instrument texts.
NONINSTRUMENT_RE = re.compile(
    r"(general\s*plan|gp_adopted|annexation\s*policy\s*plan|"
    r"final\s*fee\s*schedule|copperton\s*20\d{2}\s*fee\s*schedule)", re.I)

# An adopted instrument PDF: filename carries "Ordinance"/"Resolution"/"Ord " or an
# O-series / R-series / NN-NN-NN instrument token.
INSTRUMENT_RE = re.compile(
    r"(ordinance|resolution|\bord\b|"
    r"\b20\d{2}-O-\d|\bR20\d{2}-\d|\b\d{2,4}-\d{1,2}-\d)", re.I)


def list_all():
    rows = []
    token = None
    while True:
        url = (f"{BUCKET}?list-type=2&prefix={urllib.parse.quote(PREFIX)}"
               f"&max-keys=1000")
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
            size = c.findtext(f"{NS}Size")
            lm = c.findtext(f"{NS}LastModified")
            rows.append((key, size, lm))
        if root.findtext(f"{NS}IsTruncated") == "true":
            token = root.findtext(f"{NS}NextContinuationToken")
        else:
            break
    return rows


def classify(key, filename):
    lo = filename.lower()
    ext = os.path.splitext(lo)[1]
    if ext != ".pdf":
        return "no", f"not a pdf ({ext or 'no-ext'})"
    if "/images/" in key or key.endswith(("/logo.png",)):
        return "no", "display image / site asset"
    if NONINSTRUMENT_RE.search(filename):
        return "no", "non-instrument plan/fee-schedule exhibit (housing_plans/general-plan scope)"
    if INSTRUMENT_RE.search(filename):
        return "yes", "adopted ordinance/resolution instrument"
    return "no", "unclassified non-instrument pdf"


def main():
    rows = list_all()
    out = []
    for key, size, lm in rows:
        parts = key.split("/")
        subfolder = parts[1] if len(parts) > 1 else ""
        filename = os.path.basename(key)
        scope, reason = classify(key, filename)
        out.append((PREFIX, subfolder, key, filename, size, lm[:10], scope, reason))
    out.sort(key=lambda r: (r[1], r[3]))
    p = os.path.join(HERE, "_s3_manifest.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prefix", "subfolder", "key", "filename", "size",
                    "last_modified", "in_scope", "scope_reason"])
        w.writerows(out)
    from collections import Counter
    total = len(out)
    inscope = [r for r in out if r[6] == "yes"]
    print(f"total objects: {total}")
    print(f"in_scope instrument PDFs: {len(inscope)}")
    print("by subfolder (in_scope):",
          dict(Counter(r[1] for r in inscope)))
    print("EXCLUDED (not fetched):")
    for r in out:
        if r[6] == "no":
            print(f"  - {r[1]:14s} {r[3]:60s} [{r[7]}]")
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
