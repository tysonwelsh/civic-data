#!/usr/bin/env python3
"""
Taylorsville incremental refresh — CivicPlus / CivicEngage **Central** (Granicus)
portal at www.taylorsvilleut.gov, with Utah Public Notice (PMN) as a read-only
cross-check.

Two datasets, ONE CMS (CivicEngage Central), two SEPARATE landing pages, each
laid out as **year folders** (`/-folder-<N>`):

  meeting_minutes      City Council + RDA
                       landing: /government/elected-officials/city-council-agendas-minutes
                       (index `source=civicplus`)
  planning_commission  Planning Commission
                       landing: /government/planning-commission/planning-commission-meeting-minutes
                       (index `source=civicengage`)

Portal facts (recon.md §1/§3, RE-VERIFIED live 2026-07-06 — recon's folder ids
were off by one column; see the correction below):

  * **Access:** the site sits behind an **Akamai edge that 403s bare bots** (curl
    with a plain UA, urllib's default UA, and WebFetch are all blocked). It DOES
    serve a browser-style UA carrying the archive tag (`UA` below) — verified
    live returning 200 for the landing pages, the year folders, and the PDFs.
    Use `UA` on EVERY request.

  * **Minutes-doc URL:** `/home/showpublisheddocument/<docId>/<versionToken>`
    (older docs also `/Home/ShowDocument?id=<n>`). `<docId>` is publish-order, not
    date-order — harvest the labeled links, never guess ids.

  * **Year-folder columns (THE recon correction).** The Council "Agendas &
    Minutes" landing renders THREE parallel columns of year folders
    (Agendas | Minutes | Audio Recordings), so each year has THREE different
    `-folder-<N>` ids. recon.md listed the Minutes ids as 2020=151 … 2026=437 —
    those are actually the **Audio/Agendas** column. The true **Minutes** column
    (verified: folder-150 for 2020 contains docId 3943 = the built 2020-01-08
    council minutes) is **2020=150, 2021=192, 2022=256, 2023=287, 2024=311,
    2025=341, 2026=436**. This script does NOT hard-code them: it parses the
    landing page and takes the **first `-folder-<N>` seen per year in DOM order**,
    which is the Minutes column (stable + verified live). The PC minutes landing
    has a **single** Minutes column (2020=155 … 2026=439), so no ambiguity there.

  * **Agenda / minutes both live in the Council Minutes folder.** A given council
    meeting-date shows up TWICE inside its Minutes year folder — once as the
    agenda (lower docId, posted earlier) and once as the approved minutes (higher
    docId, posted later) — both with the SAME "Month D, YYYY" label, so they are
    indistinguishable by label alone. The fetch step therefore downloads the
    candidate docId(s) for a new date and keeps only the one whose text is
    genuine minutes (motion/roll-call prose), dropping agendas and 1-page
    cancellation notices. (The PC folder is minutes-only — no such mixing.)

  * **PMN secondary probe (meeting_minutes only):** every council meeting is also
    mirrored on Utah Public Notice, **council public body id 720**
    (utah.gov/pmn/sitemap/publicbody/720.html; minutes at utah.gov/pmn/files/
    <fileId>.pdf). The build sourced 100% of minutes from CivicEngage, so
    CivicEngage is the authoritative FETCH source; PMN is probed read-only as a
    cross-check and its new-notice count surfaces only in the probe notes (never
    fetched from here) — mirrors the South Jordan / Millcreek model.

  * **Mid-2025 RICOH-OCR switch.** Taylorsville swapped its minutes production to
    scanned RICOH output mid-2025, so recent council/PC minutes are image-only
    PDFs (index `format=ocr`). `_convert` is OCR-aware: pdftotext -layout first,
    Tesseract fallback when the text layer is thin.

Modes (shared refresh_lib CLI):
  --probe  (default) list Minutes-folder items newer than the index max per
           dataset (excluding dates already indexed or logged in
           minutes_unrecovered.csv) + the PMN new-notice count; fetch nothing.
           Writes refresh_probe.json.
  --fetch  download each new date's candidate doc(s) -> raw/, resolve the minutes
           doc (OCR-aware), write markdown, append minutes_index.csv (+
           fetch_log.csv), then run the dataset's extract_votes.py +
           validate_votes.py. Rebuild db / weeks / motions_std afterwards (the CLI
           prints the reminder).

Idempotent + resumable: a raw PDF or md already on disk is re-used/skipped, and
append_index_rows skips any path already indexed; a relaunch only does the
outstanding work.
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

HOST = "https://www.taylorsvilleut.gov"
# Akamai edge 403s the default research UA and bare bots; this browser+archive UA
# is served (verified live 2026-07-06 via urllib for HTML folders + PDFs).
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact tysonwelsh@gmail.com)")
PMN_COUNCIL_BODY_ID = "720"  # Utah Public Notice public body: Taylorsville City Council
LOWTEXT = 800     # < this many chars of text layer -> treat as image-only scan, OCR
MIN_MINUTES = 1500  # shorter than this -> a cancellation notice / stub, not minutes

DATASETS_CFG = {
    "meeting_minutes": {
        "landing": f"{HOST}/government/elected-officials/city-council-agendas-minutes",
        "source": "civicplus",
        "title": "City Council Meeting",
        "slug": "city-council",
    },
    "planning_commission": {
        "landing": f"{HOST}/government/planning-commission/planning-commission-meeting-minutes",
        "source": "civicengage",
        "title": "Planning Commission",
        "slug": "planning-commission",
    },
}

# a labeled document link inside a year folder: docId, versionToken, inner label
_DOC_RE = re.compile(
    r'href="[^"]*showpublisheddocument/(\d+)/(\d+)"[^>]*>(.*?)</a>', re.S | re.I)
# a year-folder link on a landing page: url, folderId, 4-digit year label
_FOLDER_RE = re.compile(
    r'href="([^"]*-folder-(\d+)[^"]*)"[^>]*>\s*(\d{4})\s*</a>', re.I)
_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


# ------------------------------------------------------------------ label parse

def _clean(html_fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_fragment)).strip()


def _label_to_iso(label):
    """'June 3, 2026' | 'June 03, 2026' | '06-03-2026' | '6/3/2026' | leading
    '01-08-2020 City Council' -> ISO date, else None."""
    t = _clean(label)
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})', t)
    if m and m.group(1).lower() in _MONTHS:
        return f"{m.group(3)}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b', t)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


# ---------------------------------------------------------------- folder harvest

def _minutes_folders(landing_html):
    """{year(int): folderId} — the Minutes-column folder per year. The Council
    landing has 3 columns (Agendas | Minutes | Audio); the FIRST -folder- link
    seen per year in DOM order is the Minutes column (verified live). The PC
    landing has a single column, so first-seen is trivially correct."""
    out = {}
    for _url, fid, year in _FOLDER_RE.findall(landing_html):
        y = int(year)
        if y not in out:          # first-seen per year == Minutes column
            out[y] = fid
    return out


def _folder_items(dataset, landing_html, year_from):
    """Every dated document link in the Minutes folders for year >= year_from.
    Returns list of {iso, docid, token, url}."""
    cfg = DATASETS_CFG[dataset]
    items = []
    for year, fid in sorted(_minutes_folders(landing_html).items()):
        if year < year_from:
            continue
        html = rl.http_get(f"{cfg['landing']}/-folder-{fid}", ua=UA)
        seen = set()
        for m in _DOC_RE.finditer(html):
            docid, token, label = m.group(1), m.group(2), m.group(3)
            iso = _label_to_iso(label)
            if not iso or (docid, iso) in seen:
                continue
            seen.add((docid, iso))
            items.append({"iso": iso, "docid": docid, "token": token,
                          "url": f"{HOST}/home/showpublisheddocument/{docid}/{token}"})
    return items


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
               f"index max (cross-check only — CivicEngage is the authoritative fetch "
               f"source; PMN exposes only the most-recent window via GET)")


# ---------------------------------------------------------------------- probe

def probe(dataset, max_date):
    cfg = DATASETS_CFG[dataset]
    ds_dir = CITY_DIR / dataset
    landing = rl.http_get(cfg["landing"], ua=UA)
    year_from = int(max_date[:4]) if max_date else 2020
    items = _folder_items(dataset, landing, year_from)

    indexed = {r["date"] for r in rl.load_index(ds_dir)}
    unrec = _unrecovered_dates(ds_dir)

    by_date = {}
    for it in items:
        by_date.setdefault(it["iso"], []).append(it)

    new = []
    for iso in sorted(by_date):
        if not iso or (max_date and iso <= max_date) or iso > rl.today():
            continue
        if iso in indexed or iso in unrec:
            continue          # already have it, or an honest logged gap/cancellation
        cands = sorted(by_date[iso], key=lambda d: int(d["docid"]), reverse=True)
        new.append({
            "date": iso,
            "title": f"{cfg['title']} (candidate — agenda/minutes resolved at fetch)",
            "url": cands[0]["url"],
            "candidates": [{"docid": c["docid"], "url": c["url"]} for c in cands],
        })

    notes = (f"CivicEngage Central Minutes year folders (first-column = Minutes, "
             f"verified live); dates already indexed or in minutes_unrecovered.csv "
             f"are excluded.")
    if dataset == "meeting_minutes":
        _, pmn_note = _pmn_new_count(max_date)
        notes += " | " + pmn_note
    return {"new_items": new, "endpoint": cfg["landing"], "notes": notes}


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
    """(text, format) — pdftotext -layout, OCR fallback for the mid-2025+ RICOH
    image-only scans. format uses this repo's index vocabulary ('pdf-text'/'ocr')."""
    txt = _pdf_text(pdf_path)
    if len(txt.strip()) < LOWTEXT:
        return _ocr(pdf_path), "ocr"
    return txt, "pdf-text"


def _looks_like_minutes(txt):
    """True for genuine minutes; False for an agenda or a 1-page cancellation."""
    low = txt.lower()
    if len(txt.strip()) < MIN_MINUTES:
        return False                      # cancellation notice / stub
    if re.search(r"\bmoved\b", low) and re.search(r"second", low):
        return True                       # recorded motion prose == minutes
    # a minutes doc with no motion (rare, e.g. a hearing-only session) still says
    # "minutes" near the top and is not an agenda listing
    head = low[:800]
    return ("minutes" in head and "agenda" not in head)


# ------------------------------------------------------------------------ fetch

def _md_header(dataset, iso, url, fmt):
    if dataset == "meeting_minutes":
        return (f"# {DATASETS_CFG[dataset]['title']}\n"
                f"> Source: {url}\n> Meeting date: {iso}\n> Format: {fmt}\n\n---\n\n")
    return (f"# Taylorsville Planning Commission — {iso}\n\n"
            f"> Source URL: {url}\n> Retrieved: {rl.today()} · Format: {fmt}\n\n---\n\n")


def _fetch(dataset, items):
    cfg = DATASETS_CFG[dataset]
    ds_dir = CITY_DIR / dataset
    slug = cfg["slug"]
    rows, n = [], 0
    for it in items:
        iso = it["date"]
        year = iso[:4]
        rel = rl.minutes_rel_path(iso, slug, "md", prefix="minutes")
        out = ds_dir / rel
        if out.exists():
            continue  # resumable
        chosen = None
        for cand in it["candidates"]:            # largest docId (=minutes) first
            data = rl.http_get(cand["url"], binary=True, ua=UA)
            if not data.startswith(b"%PDF"):
                continue
            raw_pdf = ds_dir / "raw" / f"{iso}_{slug}_{cand['docid']}.pdf"
            raw_pdf.parent.mkdir(parents=True, exist_ok=True)
            raw_pdf.write_bytes(data)          # raw retention — never deleted
            txt, fmt = _convert(raw_pdf)
            if _looks_like_minutes(txt):
                chosen = (cand["url"], txt, fmt)
                break
        if not chosen:
            print(f"  SKIP {iso}: only agenda/cancellation available "
                  f"(minutes not yet posted) — left for a later run")
            continue
        url, txt, fmt = chosen
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_md_header(dataset, iso, url, fmt) + txt.rstrip() + "\n",
                       encoding="utf-8")
        rows.append({"date": iso, "year": year, "title": cfg["title"], "slug": slug,
                     "path": rel, "source": cfg["source"], "source_url": url,
                     "format": fmt})
        n += 1
        print(f"  fetched {rel}  [{fmt}]")
    rl.append_index_rows(ds_dir, rows)
    return n


def _post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


# ----------------------------------------------------------------- dataset wiring

def _dataset(name):
    return {
        "portal": "civicengage-central",
        "baseline": lambda: rl.index_max_date(CITY_DIR / name),
        "probe": lambda mx: probe(name, mx),
        "fetch": lambda items: _fetch(name, items),
        "post_fetch": lambda: _post_fetch(name),
    }


DATASETS = {
    "meeting_minutes": _dataset("meeting_minutes"),
    "planning_commission": _dataset("planning_commission"),
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Taylorsville refresh (CivicEngage Central + PMN cross-check)")
