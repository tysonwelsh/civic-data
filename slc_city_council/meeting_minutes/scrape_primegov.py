#!/usr/bin/env python3
"""
Scrape SLC City Council meeting minutes as plain text from the city's PrimeGov
portal (https://slc.primegov.com) -- the current/live agenda+minutes system.

Why PrimeGov over the Laserfiche portal (see scrape_laserfiche.py):
  - Minutes are born-digital HTML (clean text), not scanned OCR.
  - Current: covers through the latest meetings, incl. pending (unapproved) minutes.
  - Plain JSON listing API, no cookie/session dance.
Caveat: PrimeGov only has MINUTES for 2021+ (2018-2020 are agendas only). For
2020 and earlier, Laserfiche is the only minutes source.

Flow:
  1. GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY  -> meetings + docs.
  2. For each meeting of a wanted body that has an "HTML Minutes" document, take
     that doc's templateId and GET /Portal/Meeting?meetingTemplateId=<id> -- the
     page embeds the compiled minutes HTML; we slice out its <body> and de-tag it.

Scope: Council + CRA / RDA / LBA meetings (skip minor committees/commissions).

Output: one plain-text file per meeting, by year then week-start (Monday) date:
    minutes/<year>/<YYYY-MM-DD week start>/<YYYY-MM-DD>_<meeting-slug>.txt
The index (minutes_index.csv) is rebuilt from whatever .txt files exist on disk,
so it always reflects reality and includes other-source years (e.g. 2020 Laserfiche).

Usage:
    python3 scrape_primegov.py                 # default 2021-2026
    python3 scrape_primegov.py --years 2024-2026
    python3 scrape_primegov.py --years 2026
Re-running skips meetings whose .txt already exists (resumable).
"""

import argparse
import csv
import datetime
import hashlib
import html
import json
import re
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

from markdownify import markdownify as _md   # pip install markdownify

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "minutes"
INDEX_CSV = BASE_DIR / "minutes_index.csv"

HOST = "https://slc.primegov.com"
LIST_API = HOST + "/api/v2/PublicPortal/ListArchivedMeetings?year={year}"
MEETING_URL = HOST + "/Portal/Meeting?meetingTemplateId={tid}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DELAY = 0.3

DEFAULT_YEARS = range(2021, 2027)   # PrimeGov has minutes for 2021+

# Wanted meeting bodies: Council + the boards the same members sit on.
BODY_RE = re.compile(
    r"council|community reinvestment|\bcra\b|redevelopment agency|\brda\b|"
    r"local building authority|\blba\b", re.IGNORECASE)

# Where the compiled minutes text begins inside the meeting page.
MIN_START_RE = re.compile(
    r"PENDING MINUTES|MINUTES OF|Salt Lake City,?\s*Utah,?\s*met|"
    r"\bmet (?:in|on|as)\b", re.IGNORECASE)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    time.sleep(DELAY)
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")


def list_year(year):
    try:
        return json.loads(get(LIST_API.format(year=year)))
    except Exception as e:
        print(f"  {year}: listing failed ({e})")
        return []


def minutes_template_id(meeting):
    for d in meeting.get("documentList", []):
        if d.get("templateName") == "HTML Minutes":
            return d.get("templateId")
    return None


def extract_minutes(page):
    """
    Slice the embedded compiled-minutes <body> out of a meeting page and convert
    it to Markdown -- preserving tables (vote tallies/agenda structure), attachment
    links, and emphasis, while dropping the HTML's font/colour style noise.
    """
    m = MIN_START_RE.search(page)
    if not m:
        return None
    body_open = page.rfind("<body", 0, m.start())
    start = page.find(">", body_open) + 1 if body_open != -1 else m.start()
    end = page.find("</body>", m.start())
    seg = page[start:end if end != -1 else None]
    seg = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", seg, flags=re.S | re.I)
    # make root-relative attachment links absolute so they're usable later
    seg = re.sub(r'href="/', f'href="{HOST}/', seg)
    # PrimeGov nests tables purely for LAYOUT (agenda item # | text), not data, so
    # linearize them (cell -> space, row -> line break) before converting. Real
    # data (motions, "AYE:" tallies) is inline text/bold and is preserved.
    seg = re.sub(r"</t[dh]>\s*", " ", seg, flags=re.I)
    seg = re.sub(r"</tr>\s*", "<br>", seg, flags=re.I)
    seg = re.sub(r"</?(table|tbody|thead|tr|t[dh])[^>]*>", "", seg, flags=re.I)
    md = _md(seg, heading_style="ATX")
    md = md.replace("\xa0", " ")
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "meeting"


def parse_years(arg):
    if not arg:
        return list(DEFAULT_YEARS)
    out = []
    for token in arg.split(","):
        token = token.strip()
        if "-" in token:
            a, b = token.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif token:
            out.append(int(token))
    return out


def dedupe_output():
    """Drop byte-identical minute files that share a meeting date."""
    by_key = defaultdict(list)
    for f in list(OUT_DIR.rglob("*.md")) + list(OUT_DIR.rglob("*.txt")):
        by_key[(f.name[:10], hashlib.md5(f.read_bytes()).hexdigest())].append(f)
    removed = 0
    for paths in by_key.values():
        if len(paths) < 2:
            continue
        keeper = min(paths, key=lambda p: (len(p.name), p.name))
        for p in paths:
            if p != keeper:
                p.unlink()
                removed += 1
    for d in sorted(OUT_DIR.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return removed


def rebuild_index(scraped_meta):
    """
    Rebuild minutes_index.csv from every minutes file on disk, in the repo-standard
    schema (date,year,title,slug,path,source,source_url,format — same as the other
    cities; retrofit 2026-07-02). Legacy extras (chars/ref_id/week_start) live in
    minutes_index_legacy.csv, frozen.

    scraped_meta maps file-path -> dict of API metadata for files pulled this run;
    files from other sources/years (e.g. 2020 from Laserfiche) are derived from
    the filename, with title/source_url carried over from the existing index so a
    partial-year re-run never blanks earlier provenance.
    """
    cols = ["date", "year", "title", "slug", "path", "source", "source_url", "format"]
    existing = {}
    if INDEX_CSV.exists():
        with open(INDEX_CSV, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if "path" in r:
                    existing[r["path"]] = r
    rows = []
    for f in list(OUT_DIR.rglob("*.md")) + list(OUT_DIR.rglob("*.txt")):
        rel = str(f.relative_to(BASE_DIR))
        meta = scraped_meta.get(rel)
        old = existing.get(rel, {})
        date = f.stem[:10]
        slug = f.stem[11:]
        # Freshly scraped this run => authoritative primegov. Otherwise PRESERVE the
        # existing index's source/format so a re-run never overwrites non-primegov
        # provenance (e.g. the PMN-recovered .md minutes carry source=pmn/format=text;
        # deriving source from the .md suffix alone would mislabel them primegov/ocr).
        if meta:
            source, fmt = "primegov", "text"
        elif old.get("source"):
            source, fmt = old["source"], (old.get("format") or "text")
        else:
            source = "primegov" if f.suffix == ".md" else "laserfiche"
            fmt = "text" if source == "primegov" else "ocr"
        rows.append({
            "date": date, "year": f.parts[-3],
            "title": meta["title"] if meta else (old.get("title") or slug.replace("-", " ").title()),
            "slug": slug, "path": rel, "source": source,
            "source_url": meta["url"] if meta else old.get("source_url", ""),
            "format": fmt,
        })
    rows.sort(key=lambda r: (r["date"], r["slug"]))
    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Scrape SLC Council minutes from PrimeGov")
    ap.add_argument("--years", help="e.g. 2026, 2021-2026, or 2024,2026")
    args = ap.parse_args()
    years = parse_years(args.years)

    OUT_DIR.mkdir(exist_ok=True)
    scraped_meta = {}
    scraped = skipped = nominutes = failed = 0

    for year in years:
        meetings = list_year(year)
        wanted = [m for m in meetings if BODY_RE.search(m.get("title", ""))]
        print(f"\n=== {year}: {len(meetings)} meetings, {len(wanted)} in-scope bodies ===")

        for m in sorted(wanted, key=lambda x: x.get("dateTime", "")):
            tid = minutes_template_id(m)
            if not tid:
                nominutes += 1
                continue
            mdate = datetime.date.fromisoformat(m["dateTime"][:10])
            week_start = mdate - datetime.timedelta(days=mdate.weekday())
            slug = slugify(m.get("title", "meeting"))
            out_dir = OUT_DIR / str(mdate.year) / week_start.isoformat()
            out_file = out_dir / f"{mdate.isoformat()}_{slug}.md"
            rel = str(out_file.relative_to(BASE_DIR))

            if out_file.exists():
                skipped += 1
                scraped_meta[rel] = {"title": m.get("title", ""), "tid": tid,
                                     "url": MEETING_URL.format(tid=tid)}
                continue
            try:
                text = extract_minutes(get(MEETING_URL.format(tid=tid)))
                if not text:
                    raise ValueError("no minutes body found")
            except Exception as e:
                print(f"  FAIL {m['date']} {m.get('title','')}: {e}")
                failed += 1
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(text + "\n", encoding="utf-8")
            scraped_meta[rel] = {"title": m.get("title", ""), "tid": tid,
                                 "url": MEETING_URL.format(tid=tid)}
            scraped += 1
            print(f"  {rel}  ({len(text)} chars)")

    removed = dedupe_output()
    total = rebuild_index(scraped_meta)
    print(f"\nDone. Scraped {scraped}, skipped {skipped} (already had), "
          f"no-minutes {nominutes}, failed {failed}, deduped {removed}.")
    print(f"Index: {INDEX_CSV.name} ({total} minute files on disk)")


if __name__ == "__main__":
    main()
