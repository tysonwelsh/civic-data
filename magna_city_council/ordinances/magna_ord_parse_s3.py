#!/usr/bin/env python3
"""magna_ord_parse_s3.py — parse MunicipalCodeOnline S3 XML listings for Magna
ordinances/resolutions. Dedupes by ETag (same doc re-uploaded under different
unix-ts filename prefixes). Writes a download manifest (url,name) + batch and stats.

Number families on the host (all normalized later by canon()):
  * township 2-digit-year month-seq   YY-MM-NN     e.g. 17-01-01, 21-09-03
  * township 4-digit-year month-seq   YYYY-MM-NN   e.g. 2022-04-01, 2024-01-01
  * city ordinance O-series           YYYY-O-NN / YY-O-NN  e.g. 2022-O-04, 22-O-01
  * city resolution R-series          RYYYY-NN     e.g. R2025-11, R2026-15 (+ 'A' re-issues)

Standing rule: lives INSIDE magna_city_council/ordinances/ with a unique name.
Usage: python3 magna_ord_parse_s3.py [scratch_dir]
"""
import re, sys, os, csv, urllib.parse

SC = sys.argv[1] if len(sys.argv) > 1 else ('/private/tmp/claude-501/'
    '-Users-tysonwelsh-civic-data/8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad')
BASE = 'https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/'
OUTDIR = os.path.dirname(os.path.abspath(__file__))


def is_instrument(stem):
    """True if the file is an adopted ordinance/resolution instrument (not a plan,
    fee schedule, housing packet, or county attachment)."""
    lo = stem.lower()
    if re.match(r'(ordinance|ordiance|resolution|resoluiton)\s', lo):
        return True
    # numbered instrument regardless of leading 'Magna '/'Signed '/'Title '
    if re.search(r'\br\s?20\d{2}-\d', lo):          # R-series
        return True
    if re.search(r'20?\d{2}\s*-\s*[o0]\s*-\s*\d', lo):  # O-series
        return True
    if re.search(r'(?<!\d)\d{2,4}\s*-\s*\d{1,2}\s*-\s*\d{1,3}(?!\d)', lo):  # month-seq
        return True
    if re.search(r'title\s*1[89]', lo):             # adopted code books
        return True
    if 'electronic signatures ordinance' in lo:      # un-numbered adopted ord
        return True
    return False


rows = []
for pref in ['ordinances', 'resolutions', 'plan', 'fees']:
    xml = open(os.path.join(SC, f'magna_s3_{pref}.xml')).read()
    for m in re.finditer(r'<Contents>(.*?)</Contents>', xml, re.S):
        blk = m.group(1)
        key = re.search(r'<Key>([^<]+)</Key>', blk).group(1)
        etag = re.search(r'<ETag>([^<]+)</ETag>', blk).group(1).replace('&quot;', '').strip('"')
        size = int(re.search(r'<Size>([0-9]+)</Size>', blk).group(1))
        lm = re.search(r'<LastModified>([^<]+)</LastModified>', blk).group(1)
        rows.append((key, etag, size, lm, pref))

# dedupe by etag: keep earliest lastmodified (original upload)
by_etag = {}
for key, etag, size, lm, pref in rows:
    base = os.path.basename(key)
    stem = re.sub(r'^\d{9,}_', '', base)          # strip unix-ts prefix
    rec = {'key': key, 'etag': etag, 'size': size, 'lm': lm,
           'pref': pref, 'stem': stem, 'base': base}
    if etag not in by_etag or lm < by_etag[etag]['lm']:
        by_etag[etag] = rec

manifest, skipped_nondoc = [], []
for etag, r in by_etag.items():
    if not is_instrument(r['stem']):
        skipped_nondoc.append(r)
        continue
    manifest.append(r)

manifest.sort(key=lambda r: r['stem'].lower())

seen_names = {}
with open(os.path.join(OUTDIR, 'magna_ord_manifest.csv'), 'w', newline='') as f, \
     open(os.path.join(OUTDIR, 'magna_ord_batch.csv'), 'w', newline='') as bf:
    w = csv.writer(f)
    b = csv.writer(bf)
    w.writerow(['url', 'name', 'etag', 'size', 'lastmodified', 's3_prefix', 'stem'])
    for r in manifest:
        url = BASE + urllib.parse.quote(r['key'])
        base = r['stem'].replace(' ', '_')
        root, extn = os.path.splitext(base)
        name = base
        if name in seen_names:
            name = f"{root}__{r['etag'][:6]}{extn}"
        seen_names[name] = 1
        w.writerow([url, name, r['etag'], r['size'], r['lm'], r['pref'], r['stem']])
        b.writerow([url, name])

print(f"total raw keys: {len(rows)}")
print(f"unique by etag: {len(by_etag)}")
print(f"manifest (ord/res instruments): {len(manifest)}")
print(f"skipped non-instrument (GP/fee/housing packet/attachment): {len(skipped_nondoc)}")
for r in sorted(skipped_nondoc, key=lambda r: r['stem'].lower()):
    print("  SKIP:", r['pref'], '/', r['stem'])
