#!/usr/bin/env python3
"""
South Jordan incremental refresh — CivicPlus / CivicEngage ArchiveCenter
(www.sjc.utah.gov == ut-southjordan.civicplus.com).

Datasets (BOTH live on the same CivicPlus portal, different Archive lists):
  meeting_minutes      City Council minutes  — ArchiveCenter list /484
  planning_commission  Planning Commission   — ArchiveCenter list /486

Portal pattern (recon.md §1/§3, verified live 2026-07-06):
  * The minutes archive is a CivicPlus **ArchiveCenter** page. Its friendly URL
    (`/484/City-Council-Meeting-Minutes-Archive`, `/486/Planning-Commission-
    Meeting-Minutes-Arch`) renders one year's list and links the other years as
    `Archive.aspx?AMID=<yearListId>` tabs. Each item in a year list is an
    `Archive.aspx?ADID=<docId>` link whose title carries the meeting date+type
    (e.g. "03-18-2025-South-Jordan-City-Council-Meeting-Minutes"). Older items
    (~2021-23) drop the "South-Jordan-" slug prefix; both forms parse.
    `Archive.aspx?ADID=<id>` 302-redirects to the born-digital minutes PDF.
    Some items are served instead as `DocumentCenter/View/<id>/<slug>` — both
    link shapes are harvested here.  This is the exact pattern the build used
    (index `source=civicplus`, source_url `.../Archive.aspx?ADID=<id>`).
  * PMN (utah.gov/pmn, SJ body — Council + Planning Commission) was the **2020
    backfill** route (index rows with `source=pmn`), used only where CivicPlus
    has no coverage (pre-2021). The coverage floor (2020-08) is already met, so
    the forward refresh below probes **CivicPlus only** — anything newer than the
    index max is on CivicPlus. (To re-open the 2020 PMN backfill see
    meeting_minutes/minutes_unrecovered.csv + recon.md §5.)

Modes (shared refresh_lib CLI):
  --probe   (default) list ArchiveCenter items newer than the index max; fetch
            nothing.  Writes refresh_probe.json.
  --fetch   download each new ADID/DocumentCenter PDF -> raw/, pdftotext -layout
            -> markdown, append minutes_index.csv (+ fetch_log.csv), then run the
            dataset's extract_votes.py + validate_votes.py.  Rebuild db/weeks/
            motions_std afterwards (the CLI prints the reminder).

Idempotent + resumable: append_index_rows skips any path already indexed, and a
raw PDF already on disk is re-used; a relaunch only does outstanding work.
"""

import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://www.sjc.utah.gov"

# Per-dataset ArchiveCenter landing page + default slug + on-disk dir.
ARCHIVE = {
    "meeting_minutes": {
        "landing": f"{HOST}/484/City-Council-Meeting-Minutes-Archive",
        "default_slug": "city-council-regular-meeting",
        "title": "City Council Meeting",
    },
    "planning_commission": {
        "landing": f"{HOST}/486/Planning-Commission-Meeting-Minutes-Arch",
        "default_slug": "planning-commission",
        "title": "Planning Commission",
    },
}

# CivicPlus serves the portal only to browser-like UAs.
UA = rl.BROWSER_UA

_DATE_RE = re.compile(r"(\d{1,2})[-/](\d{1,2})[-/](20\d{2})")
_ADID_RE = re.compile(r'Archive\.aspx\?ADID=(\d+)', re.I)
_DOCV_RE = re.compile(r'DocumentCenter/View/(\d+)(?:/([^"\'<>\s]+))?', re.I)
_AMID_RE = re.compile(r'Archive\.aspx\?AMID=(\d+)', re.I)


def _iso(mm, dd, yyyy):
    return f"{yyyy}-{int(mm):02d}-{int(dd):02d}"


def _slug_from_title(text, default_slug):
    """Turn an item title/slug into the repo's meeting-type slug."""
    t = text.lower()
    if "study" in t:
        return "city-council-study-meeting"
    if "budget" in t:
        return "city-council-budget-meeting"
    if "redevelopment" in t or "combined" in t:
        return "city-council-combined-rda-meeting"
    if "strategic" in t:
        return "city-council-strategic-planning-meeting"
    if "planning" in t:
        return "planning-commission"
    return default_slug


def _parse_list_page(html, default_slug):
    """(iso_date, slug, title, absolute_url) for every dated ADID/DocumentCenter
    item on one ArchiveCenter list page."""
    items = {}
    # Split into anchor-ish chunks so each date pairs with its own link.
    for chunk in re.split(r'(?=<a\b)', html, flags=re.I):
        link = _ADID_RE.search(chunk) or _DOCV_RE.search(chunk)
        if not link:
            continue
        d = _DATE_RE.search(chunk)
        if not d:
            continue
        iso = _iso(*d.groups())
        if link.re is _ADID_RE:
            url = f"{HOST}/Archive.aspx?ADID={link.group(1)}"
        else:
            tail = link.group(2) or ""
            url = f"{HOST}/DocumentCenter/View/{link.group(1)}/{tail}".rstrip("/")
        slug = _slug_from_title(chunk, default_slug)
        items[(iso, slug)] = (iso, slug, chunk, url)
    return list(items.values())


def _year_list_amids(html):
    """AMIDs of the other year-tab lists linked from a landing page."""
    return sorted(set(_AMID_RE.findall(html)))


def _all_items(dataset):
    cfg = ARCHIVE[dataset]
    landing = rl.http_get(cfg["landing"], ua=UA)
    items = _parse_list_page(landing, cfg["default_slug"])
    seen = {(i[0], i[1]) for i in items}
    for amid in _year_list_amids(landing):
        page = rl.http_get(f"{HOST}/Archive.aspx?AMID={amid}", ua=UA)
        for it in _parse_list_page(page, cfg["default_slug"]):
            if (it[0], it[1]) not in seen:
                seen.add((it[0], it[1]))
                items.append(it)
    return items


def probe(dataset, max_date):
    items = _all_items(dataset)
    new = []
    for iso, slug, title, url in items:
        if not iso or (max_date and iso <= max_date) or iso > rl.today():
            continue
        new.append({"date": iso, "slug": slug,
                    "title": f"{ARCHIVE[dataset]['title']} ({slug})", "url": url})
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new,
            "endpoint": ARCHIVE[dataset]["landing"],
            "notes": ("CivicPlus ArchiveCenter; PMN (utah.gov/pmn) was the 2020 "
                      "backfill only — floor already met, not re-probed.")}


def _fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    default_title = ARCHIVE[dataset]["title"]
    rows, n = [], 0
    for it in items:
        iso, slug = it["date"], it["slug"]
        rel = rl.minutes_rel_path(iso, slug, "md", prefix="minutes")
        out = ds_dir / rel
        if out.exists():
            continue  # resumable: already extracted
        pdf = rl.http_get(it["url"], binary=True, ua=UA)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {iso} {slug}: response not a PDF ({it['url']})")
            continue
        rl.save_raw(ds_dir, f"{iso}_{slug}.pdf", pdf)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rl.pdf_to_text(ds_dir / "raw" / f"{iso}_{slug}.pdf"),
                       encoding="utf-8")
        rows.append({"date": iso, "year": iso[:4], "title": default_title,
                     "slug": slug, "path": rel, "source": "civicplus",
                     "source_url": it["url"], "format": "pdf-text"})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def _post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir,
                         f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir,
                         f"{dataset} validate_votes")


def _dataset(name):
    return {
        "portal": "civicplus",
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
    rl.run_cli(CITY_DIR, DATASETS, "South Jordan refresh (CivicPlus ArchiveCenter)")
