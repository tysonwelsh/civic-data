#!/usr/bin/env python3
"""
White City incremental refresh — **Streamline CMS** (whitecity.utah.gov), with
Utah Public Notice (PMN) **body 5805** as a read-only cross-check / fallback.

ONE body, ONE CMS. White City publishes only **Council** minutes (its Planning
Commission posts no minutes series — see planning_commission/AVAILABILITY.md), so
this refresher drives the single `meeting_minutes` dataset.

Portal facts (recon.md §1, re-verified at build 2026-07-12):

  * **Host / access:** `https://whitecity.utah.gov` (Streamline SPA; document PDFs
    served from a Cloudfront CDN at `/files/<hex-hash>/<filename>.pdf`). Fetches
    succeed with a **browser User-Agent** (bare bots may be blocked); use `UA` on
    every request. A legacy mirror exists at `whitecity.specialdistrict.org`.

  * **Year listings (three shapes):**
      - current year:      /council-meetings
      - 2022..current-1:   /council-meeting?year=<YYYY>
      - pre-2022 bucket:   /meetings-archive   (2017 agendas + 2018-2021 minutes,
                           and some early Planning-Commission docs mixed in)
    Each meeting-day typically lists Agenda + Packet + Minutes(+ APPROVED) + an
    audio MP3. **Filenames are date-labeled and human** (e.g.
    `09-04-2025+WC+Minutes+APPROVED.pdf`, `05-02-24+Minutes.pdf`,
    `06-01-23+Minutes.pdf`). Hashes are opaque — **harvest the labeled <a href>
    links; never guess the hash.**

  * **Minutes vs the rest.** Keep only links whose filename says *minutes* and
    NOT *agenda* / *packet* / *pc* / *.mp3*; prefer an *APPROVED* minutes file when
    both a draft and an approved copy are present for the same date.

  * **PMN cross-check:** Utah Public Notice council body **5805**
    (utah.gov/pmn/sitemap/publicbody/5805.html = "White City Council"). Streamline
    is the authoritative FETCH source; PMN is probed read-only and its new-notice
    count surfaces in the probe notes only (mirrors the Taylorsville / South Jordan
    model). Use PMN by hand if a Streamline year page blocks or a meeting is missing.

  * **OCR seam.** A run of mid/late-2024 minutes were image-only scans (index
    `format=ocr`). `_convert` is OCR-aware: pdftotext -layout first, Tesseract
    fallback when the text layer is thin.

Modes (shared refresh_lib CLI):
  --probe  (default) list Streamline minutes documents newer than the index max
           (excluding dates already indexed or logged in minutes_unrecovered.csv)
           + the PMN new-notice count; fetch nothing. Writes refresh_probe.json.
  --fetch  download each new date's minutes doc -> raw/, convert (OCR-aware), write
           markdown, append minutes_index.csv, then run extract_votes.py +
           validate_votes.py. Rebuild db / weeks afterwards (the CLI prints the
           reminder).

Idempotent + resumable: a raw PDF or md already on disk is re-used/skipped, and
append_index_rows skips any path already indexed; a relaunch only does outstanding work.
"""

import datetime
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://whitecity.utah.gov"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact tysonwelsh@gmail.com)")
PMN_COUNCIL_BODY_ID = "5805"   # Utah Public Notice public body: White City Council
PMN_PC_BODY_ID = "5879"        # Utah Public Notice public body: White City Planning Commission
                               # (the body the ENTIRE PC layer was recovered from, 2026-07-16)
LOWTEXT = 800      # < this many chars of text layer -> treat as image-only scan, OCR
MIN_MINUTES = 1200  # shorter than this -> a cancellation notice / stub / agenda, not minutes
FIRST_MINUTES_YEAR = 2018  # 2017 is agenda-only (logged in minutes_unrecovered.csv)

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

# a document link on a Streamline year page: /files/<hash>/<filename>, + link text
_DOC_RE = re.compile(
    r'href="([^"]*/files/[0-9a-f]+/([^"]+?\.pdf))"[^>]*>(.*?)</a>', re.S | re.I)


# ------------------------------------------------------------------ label parse

def _clean(html_fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_fragment)).strip()


def _label_to_iso(text):
    """'09-04-2025 …' | '05-02-24 …' | '06-01-23' | 'September 4, 2025' -> ISO, else None.
    Streamline filenames are usually MM-DD-YY(YY); 2-digit years are 20xx here."""
    t = _clean(text).replace("+", " ")
    m = re.search(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b', t)
    if m:
        mo, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        year = int(yy) if len(yy) == 4 else 2000 + int(yy)
        if 1 <= mo <= 12 and 1 <= dd <= 31 and 2017 <= year <= 2100:
            return f"{year:04d}-{mo:02d}-{dd:02d}"
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})', t)
    if m and m.group(1).lower() in _MONTHS:
        return f"{m.group(3)}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return None


def _is_minutes(fname, label):
    """True for a minutes doc; drop agendas, packets, PC docs, audio."""
    s = (fname + " " + label).lower()
    if not re.search(r"minute", s):
        return False
    if re.search(r"agenda|packet|\.mp3|planning|(?:^|[_\W])pc(?:[_\W]|$)", s):
        return False
    return True


def _year_pages(year_from):
    """The Streamline listing URLs to scan for minutes >= year_from."""
    this_year = int(rl.today()[:4])
    pages = []
    if year_from < 2022:
        pages.append(f"{HOST}/meetings-archive")          # 2018-2021 minutes bucket
    for y in range(max(year_from, 2022), this_year):
        pages.append(f"{HOST}/council-meeting?year={y}")
    pages.append(f"{HOST}/council-meetings")              # current year
    return pages


# ---------------------------------------------------------------- harvest

def _minutes_items(year_from):
    """Every minutes-doc link across the relevant year pages, newest label wins,
    APPROVED preferred. Returns {iso: {'url','fname'}}."""
    best = {}
    for page in _year_pages(year_from):
        try:
            html = rl.http_get(page, ua=UA)
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {page}: {type(e).__name__})")
            continue
        for href, fname, label in _DOC_RE.findall(html):
            if not _is_minutes(fname, label):
                continue
            iso = _label_to_iso(fname) or _label_to_iso(label)
            if not iso or int(iso[:4]) < max(year_from, FIRST_MINUTES_YEAR):
                continue
            url = href if href.startswith("http") else HOST + href
            approved = "approved" in (fname + label).lower()
            cur = best.get(iso)
            # prefer an APPROVED copy; otherwise keep the first seen
            if cur is None or (approved and not cur["approved"]):
                best[iso] = {"url": url, "fname": fname, "approved": approved}
    return best


def _unrecovered_dates(ds_dir):
    p = ds_dir / "minutes_unrecovered.csv"
    if not p.exists():
        return set()
    import csv
    with open(p, newline="", encoding="utf-8") as fh:
        return {r["date"] for r in csv.DictReader(fh) if r.get("date")}


def _pmn_new_count(max_date):
    """Read-only PMN cross-check: council notices dated after the index max."""
    try:
        html = rl.http_get(
            f"https://www.utah.gov/pmn/sitemap/publicbody/{PMN_COUNCIL_BODY_ID}.html",
            ua=UA)
    except Exception as e:  # noqa: BLE001
        return None, f"PMN probe skipped ({type(e).__name__})"
    dates = set()
    for mo, dd, yy in re.findall(r'([A-Za-z]+)\s+(\d{1,2}),\s+(20\d{2})', html):
        if mo.lower() not in _MONTHS:
            continue
        iso = f"{yy}-{_MONTHS[mo.lower()]:02d}-{int(dd):02d}"
        if (not max_date or iso > max_date) and iso <= rl.today():
            dates.add(iso)
    n = len(dates)
    return n, (f"PMN body {PMN_COUNCIL_BODY_ID}: {n} council notice date(s) newer than "
               f"index max (cross-check only — Streamline is the authoritative fetch source)")


def _pmn_pc_new_count(pc_max, pc_indexed, pc_unrec):
    """Read-only PMN cross-check on the **Planning Commission body 5879** — the body
    White City's entire PC layer was recovered from (2026-07-16). Reports PC notice
    dates newer than the PC index max that are not already indexed or logged
    unrecovered. Cross-check only: the PC series is sporadic and many notices are
    agenda-only, so a lead here must be opened to confirm it is minutes before any
    (separate, reviewed) ingest — this probe NEVER fetches."""
    try:
        html = rl.http_get(
            f"https://www.utah.gov/pmn/sitemap/publicbody/{PMN_PC_BODY_ID}.html", ua=UA)
    except Exception as e:  # noqa: BLE001
        return None, f"PMN PC body {PMN_PC_BODY_ID} probe skipped ({type(e).__name__})"
    dates = set()
    for mo, dd, yy in re.findall(r'([A-Za-z]+)\s+(\d{1,2}),\s+(20\d{2})', html):
        if mo.lower() not in _MONTHS:
            continue
        iso = f"{yy}-{_MONTHS[mo.lower()]:02d}-{int(dd):02d}"
        if iso <= rl.today() and (not pc_max or iso > pc_max) \
                and iso not in pc_indexed and iso not in pc_unrec:
            dates.add(iso)
    n = len(dates)
    lead = f" ({', '.join(sorted(dates))})" if dates else ""
    return n, (f"PMN PC body {PMN_PC_BODY_ID}: {n} PC notice date(s) newer than the PC "
               f"index max{lead} — cross-check only (open to confirm minutes vs agenda; "
               f"the sporadic PC series is never auto-ingested)")


# ---------------------------------------------------------------------- probe

def probe(max_date):
    ds_dir = CITY_DIR / "meeting_minutes"
    year_from = int(max_date[:4]) if max_date else FIRST_MINUTES_YEAR
    items = _minutes_items(year_from)

    indexed = {r["date"] for r in rl.load_index(ds_dir)}
    unrec = _unrecovered_dates(ds_dir)

    new = []
    for iso in sorted(items):
        if (max_date and iso <= max_date) or iso > rl.today():
            continue
        if iso in indexed or iso in unrec:
            continue
        new.append({"date": iso, "title": "White City Council Meeting",
                    "url": items[iso]["url"]})

    notes = ("Streamline year pages (/meetings-archive + /council-meeting?year=YYYY + "
             "/council-meetings); minutes docs only (agendas/packets/PC/audio excluded); "
             "dates already indexed or in minutes_unrecovered.csv are excluded.")
    _, pmn_note = _pmn_new_count(max_date)
    notes += " | " + pmn_note
    # read-only PC-body 5879 cross-check (the body the PC layer was recovered from).
    # White City's fetch path only drives meeting_minutes, so ALSO emit a dedicated
    # planning_commission probe entry (via write_probe) so the 5879 cross-check
    # surfaces on the PC row of scripts/refresh_status.py rather than showing "no probe".
    pc_dir = CITY_DIR / "planning_commission"
    pc_indexed = {r["date"] for r in rl.load_index(pc_dir) if r.get("date")}
    pc_unrec = _unrecovered_dates(pc_dir)
    pc_max = max(pc_indexed) if pc_indexed else None
    pc_count, pc_note = _pmn_pc_new_count(pc_max, pc_indexed, pc_unrec)
    notes += " | " + pc_note
    rl.write_probe(CITY_DIR, "planning_commission", {
        "probe_date": rl.today(), "portal": "pmn-5879-crosscheck",
        "index_max_date": pc_max, "index_rows": len(pc_indexed),
        "status": "ok" if pc_count is not None else "fail",
        "new_count": pc_count if pc_count is not None else None,
        "new_items": [], "notes": pc_note,
        "fetch_cmd": "PC minutes are PMN-recovered (body 5879) — a separate reviewed step",
    })
    return {"new_items": new, "endpoint": f"{HOST}/council-meetings", "notes": notes}


# ---------------------------------------------------------------------- convert

def _pdf_text(pdf_path):
    return subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                          capture_output=True, timeout=300).stdout.decode("utf-8", "replace")


def _ocr(pdf_path):
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-png", "-r", "300", str(pdf_path),
                        str(Path(td) / "p")], check=True, timeout=1800)
        for png in sorted(Path(td).glob("p*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(out)


def _convert(pdf_path):
    """(text, format) — pdftotext -layout, OCR fallback for image-only scans.
    format uses this repo's index vocabulary ('text'/'ocr')."""
    txt = _pdf_text(pdf_path)
    if len(txt.strip()) < LOWTEXT:
        return _ocr(pdf_path), "ocr"
    return txt, "text"


def _looks_like_minutes(txt):
    low = txt.lower()
    if len(txt.strip()) < MIN_MINUTES:
        return False
    if re.search(r"\bmov(e|ed|ing)?\b", low) and re.search(r"second", low):
        return True
    head = low[:1000]
    return ("minutes" in head and "agenda" not in head)


# ------------------------------------------------------------------------ fetch

def _md_header(iso, url, fmt):
    return (f"# White City Council Meeting\n"
            f"> Source: {url}\n> Meeting date: {iso}\n> Format: {fmt}\n\n---\n\n")


def _fetch(items):
    ds_dir = CITY_DIR / "meeting_minutes"
    slug = "council-meeting"
    rows, n = [], 0
    for it in items:
        iso = it["date"]
        year = iso[:4]
        rel = rl.minutes_rel_path(iso, slug, "md", prefix="minutes")
        out = ds_dir / rel
        if out.exists():
            continue  # resumable
        data = rl.http_get(it["url"], binary=True, ua=UA)
        if not data.startswith(b"%PDF"):
            print(f"  SKIP {iso}: not a PDF ({it['url']})")
            continue
        raw_pdf = ds_dir / "raw" / f"{iso}_{slug}.pdf"
        raw_pdf.parent.mkdir(parents=True, exist_ok=True)
        raw_pdf.write_bytes(data)               # raw retention — never deleted
        txt, fmt = _convert(raw_pdf)
        if not _looks_like_minutes(txt):
            print(f"  SKIP {iso}: doc is not genuine minutes (agenda/cancellation/stub)")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_md_header(iso, it["url"], fmt) + txt.rstrip() + "\n",
                       encoding="utf-8")
        rows.append({"date": iso, "year": year, "title": "White City Council Meeting",
                     "slug": slug, "path": rel, "source": "streamline",
                     "source_url": it["url"], "format": fmt})
        n += 1
        print(f"  fetched {rel}  [{fmt}]")
    rl.append_index_rows(ds_dir, rows)
    return n


def _post_fetch():
    ds_dir = CITY_DIR / "meeting_minutes"
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, "meeting_minutes extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, "meeting_minutes validate_votes")


# ----------------------------------------------------------------- dataset wiring

DATASETS = {
    "meeting_minutes": {
        "portal": "streamline",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": lambda mx: probe(mx),
        "fetch": lambda items: _fetch(items),
        "post_fetch": lambda: _post_fetch(),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS,
               "White City refresh (Streamline + PMN 5805 council / 5879 PC cross-check)")
