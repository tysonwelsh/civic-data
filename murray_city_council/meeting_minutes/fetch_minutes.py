#!/usr/bin/env python3
"""Murray City CivicPlus Archive Center minutes scraper (resumable).

Enumerates an Archive.aspx?AMID=<id> listing, harvests every (ADID, title, date),
filters to the 2020-01-01 floor, downloads Archive/ViewFile/Item/<ADID> into the
target raw/ dir (skipping files already present), and writes a manifest CSV.

Usage: python3 fetch_minutes.py <AMID> <raw_dir> <manifest_csv>
  council = AMID 31 ; planning commission = AMID 33
Provenance: born-digital PDFs from https://www.murray.utah.gov (verified 2026-07-11).
"""
import sys, re, os, csv, html, hashlib, subprocess, datetime

BASE = "https://www.murray.utah.gov"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
FLOOR = datetime.date(2020, 1, 1)
MONTHS = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August",
     "September","October","November","December"], 1)}

def curl(url, out=None):
    cmd = ["curl", "-sL", "-A", UA, url]
    if out:
        cmd += ["-o", out]
        subprocess.run(cmd, check=True)
        return None
    return subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")

def parse_date(title):
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(20\d{2})", title)
    if not m:
        return None
    mo, d, y = m.group(1), int(m.group(2)), int(m.group(3))
    if mo not in MONTHS:
        return None
    try:
        return datetime.date(y, MONTHS[mo], d)
    except ValueError:
        return None

def slug(title):
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return s[:60]

def main():
    amid, raw_dir, manifest = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(raw_dir, exist_ok=True)
    listing = curl(f"{BASE}/Archive.aspx?AMID={amid}")
    # each item: <a href="Archive.aspx?ADID=NNNN" ...>...<span>TITLE</span>...</a>
    items = re.findall(
        r'href="Archive\.aspx\?ADID=(\d+)"[^>]*>\s*<span>(.*?)</span>',
        listing, re.S)
    rows, seen = [], set()
    for adid, raw_title in items:
        title = html.unescape(re.sub(r"\s+", " ", raw_title)).strip()
        if adid in seen:
            continue
        seen.add(adid)
        dt = parse_date(title)
        if not dt or dt < FLOOR:
            continue
        fname = f"{dt.isoformat()}_{slug(title)}_adid{adid}.pdf"
        path = os.path.join(raw_dir, fname)
        url = f"{BASE}/Archive/ViewFile/Item/{adid}"
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print(f"  fetch {dt} adid={adid} -> {fname}")
            curl(url, path)
        b = open(path, "rb").read()
        rows.append(dict(adid=adid, date=dt.isoformat(), title=title,
                         filename=fname, url=url, bytes=len(b),
                         sha256=hashlib.sha256(b).hexdigest(),
                         is_pdf=b[:4] == b"%PDF"))
    rows.sort(key=lambda r: r["date"])
    with open(manifest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["adid","date","title","filename",
                                          "url","bytes","sha256","is_pdf"])
        w.writeheader()
        w.writerows(rows)
    npdf = sum(1 for r in rows if r["is_pdf"])
    print(f"AMID={amid}: {len(rows)} items >= {FLOOR} ({npdf} valid PDFs) -> {manifest}")

if __name__ == "__main__":
    main()
