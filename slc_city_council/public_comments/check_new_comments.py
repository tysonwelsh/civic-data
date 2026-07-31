#!/usr/bin/env python3
"""
Check slcdocs.com for newly published SLC Council public-comment PDFs.

Finds the latest weekly file we already have, then probes the city site forward
(week by week, allowing multi-week bundles and the occasional recess gap) for
files we don't have yet. New files are downloaded into the correct year folder
and appended to download_comments.sh.

This step is keyless (just HTTP HEAD/GET). After it downloads new files, run:
    python3 vision_extract.py --year <year>   # extract the new pages
    python3 clean_comments.py                 # fold them into the clean dataset

Usage:
    python3 check_new_comments.py             # probe, download, update scraper
    python3 check_new_comments.py --dry-run   # probe only, download nothing
"""

import argparse
import datetime
import re
import subprocess
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRAPER = BASE_DIR / "download_comments.sh"
SITE = "https://www.slcdocs.com/council/WebDoc/Public_Comments"

# Filename joiners seen on the site: "_" (<=2025) and " - " (2026+). Probe both.
JOINERS = ("%20-%20", "_")
MAX_BUNDLE_WEEKS = 6   # a single file can bundle up to ~6 weeks at recess
GAP_WEEKS = 8          # keep probing across up to this many empty weeks (recess)


def parse_dates(name):
    """Return [date, ...] from the MMDDYYYY/MDDYYYY tokens in a filename."""
    out = []
    for tok in re.findall(r"\d{7,8}", name):
        y = int(tok[-4:]); md = tok[:-4]
        try:
            mo, d = (int(md[:2]), int(md[2:])) if len(md) == 4 else (int(md[:1]), int(md[1:]))
            if 2015 <= y <= 2035:
                out.append(datetime.date(y, mo, d))
        except ValueError:
            pass
    return out


def latest_end():
    """Latest period-end date across all downloaded PDFs."""
    ends = []
    for pdf in BASE_DIR.glob("20*/*.pdf"):
        ds = parse_dates(pdf.name)
        if ds:
            ends.append(ds[-1])
    return max(ends) if ends else None


def head_ok(url):
    r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}",
                        "--max-time", "30", url], capture_output=True, text=True)
    return r.stdout.strip() == "200"


def candidate_url(start, end, joiner):
    fn = f"{start:%m%d%Y}{joiner}{end:%m%d%Y}.pdf"
    return f"{SITE}/{start.year}/{fn}"


def local_name(url):
    """Mirror download_comments.sh: urldecode, spaces -> underscores."""
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    return base.replace(" ", "_")


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl", "-sfL", "--max-time", "120", "-o", str(dest), url])
    return r.returncode == 0


def append_to_scraper(urls):
    if not SCRAPER.exists() or not urls:
        return
    text = SCRAPER.read_text()
    additions = "".join(f'download "{u}"\n' for u in urls if u not in text)
    if additions:
        SCRAPER.write_text(text.rstrip("\n") + "\n" + additions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="probe only; do not download")
    args = ap.parse_args()

    last = latest_end()
    if not last:
        print("No existing PDFs found; run download_comments.sh first.")
        return
    today = datetime.date.today()
    print(f"Latest file we have ends {last}. Probing forward to {today}...")

    cursor = last + datetime.timedelta(days=1)
    found = []          # (start, end, url)
    while cursor <= today:
        hit = None
        for weeks in range(1, MAX_BUNDLE_WEEKS + 1):
            end = cursor + datetime.timedelta(days=weeks * 7 - 1)
            for joiner in JOINERS:
                url = candidate_url(cursor, end, joiner)
                if head_ok(url):
                    hit = (cursor, end, url)
                    break
            if hit:
                break
        if hit:
            found.append(hit)
            print(f"  NEW: {hit[0]} -> {hit[1]}  ({local_name(hit[2])})")
            cursor = hit[1] + datetime.timedelta(days=1)
        else:
            cursor += datetime.timedelta(days=7)   # skip a (likely recess) week
            if (cursor - (found[-1][1] if found else last)).days > GAP_WEEKS * 7:
                break

    if not found:
        print("Up to date — no new files on the site.")
        return

    print(f"\n{len(found)} new file(s) found.")
    if args.dry_run:
        print("(dry-run: nothing downloaded)")
        return

    downloaded, years, urls = [], set(), []
    for start, end, url in found:
        dest = BASE_DIR / str(start.year) / local_name(url)
        if download(url, dest):
            downloaded.append(dest)
            years.add(start.year)
            urls.append(url)
            print(f"  downloaded -> {dest.relative_to(BASE_DIR)}")
        else:
            print(f"  FAILED -> {url}")

    append_to_scraper(urls)
    print(f"\nDownloaded {len(downloaded)} file(s); added to download_comments.sh.")
    print("AFFECTED_YEARS=" + ",".join(str(y) for y in sorted(years)))
    print("Next: python3 vision_extract.py --year <year>  then  python3 clean_comments.py")


if __name__ == "__main__":
    main()
