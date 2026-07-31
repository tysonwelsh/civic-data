#!/usr/bin/env python3
"""
Scrape SLC City Council meeting minutes as plain text from the city's Laserfiche
WebLink portal (https://webdme.slcgov.com/AgendasMinutes).

The portal is a JS/cookie app, but its data API is reachable with a session
cookie. Minutes are scanned pages that already carry an OCR text layer, so we can
pull clean plain text directly -- no Claude Vision / API cost.

Flow (all confirmed working):
  1. GET a Browse URL with a cookie jar -> clears the cookie-check, yields session.
  2. FolderListingService.aspx/GetFolderListing2  -> folder children (year folders,
     then per-meeting minute docs).
  3. DocumentService.aspx/GetBasicDocumentInfo    -> page count for a doc.
  4. DocumentService.aspx/GetTextHtmlForPage      -> {"text": ...} per page.

Output: one plain-text file per meeting, organized by year then the week-start
(Monday) date of that meeting's week:
    minutes/<year>/<YYYY-MM-DD week start>/<YYYY-MM-DD>_<meeting-type>.txt
Plus index_laserfiche.csv with per-page provenance for every file (the repo-standard
minutes_index.csv is maintained by scrape_primegov.py's rebuild_index()).

Usage:
    python3 scrape_minutes.py --years 2026            # one year
    python3 scrape_minutes.py --years 2020-2026       # range
    python3 scrape_minutes.py --all                   # every year (1982-2026)
    python3 scrape_minutes.py --list                  # just list available years
Re-running skips meetings whose .txt already exists (safe + resumable).
"""

import argparse
import csv
import datetime
import hashlib
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "minutes"
# NB (2026-07-02 retrofit): this scraper's rich per-page schema (pages/chars/entry_id)
# is kept in its OWN index file. The repo-standard minutes_index.csv is rebuilt by
# scrape_primegov.py's rebuild_index() from what's on disk — don't clobber it here.
INDEX_CSV = BASE_DIR / "index_laserfiche.csv"

HOST = "https://webdme.slcgov.com/AgendasMinutes"
REPO = "SLC"
COUNCIL_FOLDER_ID = 2877637            # the "City Council" folder (year subfolders)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DELAY = 0.3                            # politeness pause between requests (seconds)

# "01/02/2024 - Formal Meeting - Minutes (Council Retreat)" -> date, type, extra
NAME_RE = re.compile(
    r"(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{4})\s*-\s*"
    r"(?P<type>.+?)\s*-\s*Minutes\s*(?:\((?P<extra>[^)]*)\))?",
    re.IGNORECASE,
)

_opener = None


def _build_opener():
    """One urllib opener with a cookie jar, reused for the whole run."""
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", UA)]
    return op


def ensure_session():
    """Prime cookies by hitting a Browse URL (clears the cookie-check redirect)."""
    global _opener
    _opener = _build_opener()
    url = f"{HOST}/Browse.aspx?id={COUNCIL_FOLDER_ID}&dbid=0&repo={REPO}"
    _opener.open(url, timeout=40).read()


def api(path, payload, referer_id):
    """POST a JSON body to a WebLink service endpoint, return parsed JSON['data']."""
    referer = f"{HOST}/Browse.aspx?id={referer_id}&dbid=0&repo={REPO}"
    req = urllib.request.Request(
        f"{HOST}/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": UA,
            "Referer": referer,
        },
        method="POST",
    )
    time.sleep(DELAY)
    raw = _opener.open(req, timeout=40).read().decode("utf-8")
    obj = json.loads(raw)
    return obj.get("data", obj)   # responses wrap payload in "data" (+ a junk "__breach")


def list_folder(folder_id):
    """Return all child entries of a folder as [{name, entryId, type}], paginated."""
    entries, start, total = [], 0, None
    while total is None or start < total:
        data = api(
            "FolderListingService.aspx/GetFolderListing2",
            {"repoName": REPO, "folderId": folder_id, "getNewListing": start == 0,
             "start": start, "end": start + 100, "sortColumn": "", "sortAscending": True},
            folder_id,
        )
        total = data.get("totalEntries", 0)
        chunk = data.get("results", [])
        if not chunk:
            break
        for r in chunk:
            entries.append({"name": r["name"], "entryId": r["entryId"], "type": r["type"]})
        start += len(chunk)
    return entries


def page_count(entry_id):
    data = api("DocumentService.aspx/GetBasicDocumentInfo",
               {"repoName": REPO, "entryId": entry_id}, entry_id)
    return data.get("pageCount", 0)


def clean(text):
    """Strip tags, unescape entities, normalize nbsp + whitespace."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = text.replace(" ", " ").replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def doc_text(entry_id, n_pages):
    parts = []
    for p in range(1, n_pages + 1):
        data = api("DocumentService.aspx/GetTextHtmlForPage",
                   {"repoName": REPO, "documentId": entry_id, "pageNum": p,
                    "showAnn": False, "searchUuid": ""}, entry_id)
        raw = data if isinstance(data, dict) else json.loads(data)
        parts.append(clean(raw.get("text", "")))
    return "\n\n".join(parts).strip()


def slugify(meeting_type, extra):
    s = meeting_type.strip()
    if extra:
        s += " " + extra.strip()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "meeting"


def parse_name(name):
    """Return (date, meeting_type, extra) for a minutes doc, or None if not one."""
    m = NAME_RE.search(name)
    if not m:
        return None
    try:
        d = datetime.date(int(m["y"]), int(m["m"]), int(m["d"]))
    except ValueError:
        return None
    return d, m["type"].strip(), (m["extra"] or "").strip()


def parse_years(args):
    if args.all:
        return None  # sentinel: every available year
    out = []
    for token in (args.years or "").split(","):
        token = token.strip()
        if "-" in token:
            a, b = token.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif token:
            out.append(int(token))
    return out


def dedupe_output():
    """
    Remove byte-identical minute files that share a meeting date.

    The portal sometimes stores the same minutes twice (e.g. "Minutes" and
    "Minutes (2)" with identical content). Genuinely distinct same-day meetings
    (e.g. a Limited Formal + a Formal meeting) have different text, so they hash
    differently and are kept. Within a duplicate group the cleanest filename
    wins: prefer no numeric "-2" suffix, prefer a real meeting type over the
    generic "_meeting" fallback, then the shorter name.
    """
    by_key = defaultdict(list)   # (meeting_date, content_hash) -> [paths]
    for f in OUT_DIR.rglob("*.txt"):
        h = hashlib.md5(f.read_bytes()).hexdigest()
        by_key[(f.name[:10], h)].append(f)

    def rank(p):
        n = p.name
        return (bool(re.search(r"-\d+\.txt$", n)), n.endswith("_meeting.txt"), len(n), n)

    removed = 0
    for paths in by_key.values():
        if len(paths) < 2:
            continue
        keeper = min(paths, key=rank)
        for p in paths:
            if p != keeper:
                p.unlink()
                removed += 1
    # prune any now-empty week folders
    for d in sorted(OUT_DIR.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return removed


def main():
    ap = argparse.ArgumentParser(description="Scrape SLC Council meeting minutes to text")
    ap.add_argument("--years", help="e.g. 2026, 2020-2026, or 2024,2026")
    ap.add_argument("--all", action="store_true", help="scrape every available year")
    ap.add_argument("--list", action="store_true", help="list available years and exit")
    args = ap.parse_args()

    print("Connecting to Laserfiche portal...")
    ensure_session()

    year_folders = {e["name"]: e["entryId"] for e in list_folder(COUNCIL_FOLDER_ID)
                    if e["name"].isdigit()}
    available = sorted(year_folders)
    print(f"Available years: {available[0]}–{available[-1]} ({len(available)} folders)")

    if args.list:
        return

    wanted = parse_years(args)
    if wanted is None:
        wanted = [int(y) for y in available]
    elif not wanted:
        print("Specify --years (e.g. 2026 or 2020-2026) or --all. Use --list to see years.")
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)
    index_rows = []
    scraped = skipped = failed = 0

    for year in wanted:
        key = str(year)
        if key not in year_folders:
            print(f"  {year}: no folder on the portal, skipping")
            continue
        docs = list_folder(year_folders[key])
        meetings = [(d, parse_name(d["name"])) for d in docs]
        meetings = [(d, p) for d, p in meetings if p]
        print(f"\n=== {year}: {len(meetings)} minute documents ===")

        for d, (mdate, mtype, extra) in sorted(meetings, key=lambda x: x[1][0]):
            week_start = mdate - datetime.timedelta(days=mdate.weekday())  # Monday
            slug = slugify(mtype, extra)
            out_dir = OUT_DIR / key / week_start.isoformat()
            out_file = out_dir / f"{mdate.isoformat()}_{slug}.txt"

            if out_file.exists():
                skipped += 1
                continue

            try:
                n = page_count(d["entryId"])
                text = doc_text(d["entryId"], n)
            except Exception as e:                       # network / parse hiccup
                print(f"  FAIL {d['name']}: {e}")
                failed += 1
                continue

            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(text + "\n", encoding="utf-8")
            scraped += 1
            print(f"  {out_file.relative_to(BASE_DIR)}  ({n}p, {len(text)} chars)")

            index_rows.append({
                "year": year, "week_start": week_start.isoformat(),
                "meeting_date": mdate.isoformat(),
                "meeting_type": mtype, "variant": extra, "pages": n,
                "chars": len(text), "entry_id": d["entryId"],
                "source_url": f"{HOST}/DocView.aspx?id={d['entryId']}&dbid=0&repo={REPO}",
                "file": str(out_file.relative_to(BASE_DIR)),
            })

    # Remove byte-identical same-date duplicates the portal stores.
    removed = dedupe_output()
    if removed:
        print(f"De-duplicated {removed} identical same-date file(s).")

    # Merge with any existing index, de-duped on entry_id; drop rows whose file
    # no longer exists (e.g. removed as a duplicate above).
    cols = ["year", "week_start", "meeting_date", "meeting_type", "variant", "pages",
            "chars", "entry_id", "source_url", "file"]
    existing = []
    if INDEX_CSV.exists():
        with open(INDEX_CSV, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    by_id = {r["entry_id"]: r for r in existing}
    for r in index_rows:
        by_id[str(r["entry_id"])] = r
    surviving = [r for r in by_id.values() if (BASE_DIR / r["file"]).exists()]
    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(surviving, key=lambda x: (x["meeting_date"], x["meeting_type"])):
            w.writerow(r)

    print(f"\nDone. Scraped {scraped}, skipped {skipped} (already had), failed {failed}.")
    print(f"Index: {INDEX_CSV.relative_to(BASE_DIR)} ({len(surviving)} meetings total)")


if __name__ == "__main__":
    main()
