#!/usr/bin/env python3
"""Parse MunicipalCodeOnline S3 XML listings for Kearns ordinances/resolutions.
Dedupes by ETag (same doc re-uploaded under different unix-ts filename prefixes).
Writes a download manifest (url,name) and prints stats.
Standing rule: lives INSIDE kearns_city_council/ordinances/ with a unique name.
"""
import re, sys, os, csv, urllib.parse

SC = sys.argv[1] if len(sys.argv) > 1 else '/private/tmp/claude-501/-Users-tysonwelsh-civic-data/8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad'
BASE = 'https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/'
OUTDIR = os.path.dirname(os.path.abspath(__file__))

rows = []  # (key, etag, size, lastmod, prefix)
for pref in ['ordinances', 'resolutions', 'plan', 'fees']:
    xml = open(os.path.join(SC, f's3_{pref}.xml')).read()
    for m in re.finditer(r'<Contents>(.*?)</Contents>', xml, re.S):
        blk = m.group(1)
        key = re.search(r'<Key>([^<]+)</Key>', blk).group(1)
        etag = re.search(r'<ETag>([^<]+)</ETag>', blk).group(1).replace('&quot;', '').strip('"')
        size = int(re.search(r'<Size>([0-9]+)</Size>', blk).group(1))
        lm = re.search(r'<LastModified>([^<]+)</LastModified>', blk).group(1)
        rows.append((key, etag, size, lm, pref))

# dedupe by etag: keep the earliest lastmodified (original upload)
by_etag = {}
for key, etag, size, lm, pref in rows:
    base = os.path.basename(key)
    # strip leading unix-ts prefix "1567618156_"
    stem = re.sub(r'^\d{9,}_', '', base)
    rec = {'key': key, 'etag': etag, 'size': size, 'lm': lm, 'pref': pref, 'stem': stem, 'base': base}
    if etag not in by_etag or lm < by_etag[etag]['lm']:
        # prefer a copy whose prefix matches its doc-type name if possible
        by_etag[etag] = rec

# For plan/fees prefixes: only keep ordinance/resolution PDFs (skip General Plan / fee schedule docs)
def is_ord_res(stem):
    return re.match(r'(Ordinance|Resolution)\s', stem, re.I) is not None

manifest = []
skipped_nondoc = []
for etag, r in by_etag.items():
    if r['pref'] in ('plan', 'fees') and not is_ord_res(r['stem']):
        skipped_nondoc.append(r)
        continue
    manifest.append(r)

# sort by stem
manifest.sort(key=lambda r: r['stem'].lower())

seen_names = {}
with open(os.path.join(OUTDIR, 'kearns_ord_manifest.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['url', 'name', 'etag', 'size', 'lastmodified', 's3_prefix', 'stem'])
    for r in manifest:
        url = BASE + urllib.parse.quote(r['key'])
        # local name: keep stem but ensure unique on collision (append short etag)
        base = r['stem'].replace(' ', '_')
        root, extn = os.path.splitext(base)
        name = base
        if name in seen_names:
            name = f"{root}__{r['etag'][:6]}{extn}"
        seen_names[name] = 1
        w.writerow([url, name, r['etag'], r['size'], r['lm'], r['pref'], r['stem']])

print(f"total raw keys: {len(rows)}")
print(f"unique by etag: {len(by_etag)}")
print(f"manifest (ord/res docs): {len(manifest)}")
print(f"skipped non-doc plan/fees (GP/fee schedules): {len(skipped_nondoc)}")
for r in skipped_nondoc:
    print("  SKIP:", r['stem'])
# format breakdown
from collections import Counter
ext = Counter(os.path.splitext(r['stem'])[1].lower() for r in manifest)
print("ext breakdown:", dict(ext))
# doctype breakdown by stem
dt = Counter('ordinance' if r['stem'].lower().startswith('ordinance') else ('resolution' if r['stem'].lower().startswith('resolution') else 'other') for r in manifest)
print("doctype (by stem):", dict(dt))
# name collisions
names = Counter(r['stem'].replace(' ', '_') for r in manifest)
print("name collisions:", {k: v for k, v in names.items() if v > 1})
