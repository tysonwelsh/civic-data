#!/usr/bin/env python3
"""
Nephi incremental refresh — CivicPlus CivicEngage AgendaCenter
(https://www.nephi.utah.gov/AgendaCenter).

Datasets:
  meeting_minutes      City Council (regular + work session) minutes
  planning_commission  Planning Commission minutes

Portal pattern (recon.md §1, verified live 2026-07-02):
  * Enumerate: GET /AgendaCenter/Search/?term=&CIDs=all&startDate=MM/DD/YYYY&endDate=MM/DD/YYYY
    -> HTML grouped under "<h2>City Council Agendas</h2>" / "<h2>Planning
    Commission Agendas</h2>" sections; each meeting row that has approved
    minutes carries an anchor
      <a href="/AgendaCenter/ViewFile/Minutes/_MMDDYYYY-<id>"
         aria-label="June 09, 2026, Work Session. Minutes">
    The date is authoritative in the _MMDDYYYY token; the meeting title
    ("City Council Meeting" / "Work Session" / "Planning Commission") comes
    from the aria-label between the year and ". Minutes".
  * Download: GET the ViewFile/Minutes URL -> born-digital text PDF.

Modes:
  --probe   (default) list minutes newer than the index max date; fetch nothing
  --fetch   download new PDFs -> <dataset>/raw/, pdftotext -layout -> .md,
            append minutes_index.csv rows (+ fetch_log.csv retrieved_date),
            run extract_votes.py + validate_votes.py.

Nephi quirk: the PC index's `slug` column embeds the date
("2026-02-11_planning-commission-meeting") while the council slug is the bare
"city-council-meeting" — both conventions are mirrored here. PC minutes are
posted sparsely (agendas appear promptly, minutes often months later); a probe
showing 0 new PC minutes while agendas exist is normal.

Probe verified live 2026-07-02 (HTTP 200, both datasets).
"""

import datetime
import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://www.nephi.utah.gov"
SEARCH = (HOST + "/AgendaCenter/Search/?term=&CIDs=all"
          "&startDate={start}&endDate={end}")

DATASET_CFG = {
    "meeting_minutes": {
        "category": "City Council",
        "default_title": "City Council Meeting",
        "slug": lambda date: "city-council-meeting",
    },
    "planning_commission": {
        "category": "Planning Commission",
        "default_title": "Planning Commission",
        "slug": lambda date: f"{date}_planning-commission-meeting",
    },
}

# --- known CITY MIS-UPLOADS (portal slot serves another meeting's document) -----
# AgendaCenter slot _10012024-346 ("October 01, 2024 ... Minutes") serves the
# SEPTEMBER 17, 2024 minutes verbatim — byte-identical business to slot
# _09172024-345 (in-body header + recorder certification both read
# "September 17, 2024"). Ingesting it created a phantom 2024-10-01 meeting with
# 10 duplicate motions; removed 2026-07-31. The real 2024-10-01 meeting IS held
# (agenda in packets/, minutes approved at 2024-10-15) but no minutes document
# is published on any channel — it is ledgered in
# meeting_minutes/minutes_unrecovered.csv. Skip the slot so any full re-ingest
# (or a reset of the index max date) cannot re-create the phantom.
KNOWN_MISUPLOAD_URLS = {
    "/AgendaCenter/ViewFile/Minutes/_10012024-346":
        "city mis-upload: serves the 2024-09-17 minutes (see "
        "meeting_minutes/minutes_unrecovered.csv, 2024-10-01)",
}

MINUTES_ROW_RE = re.compile(
    r'href="(/AgendaCenter/ViewFile/Minutes/_(\d{8})-\d+)"\s+'
    r'aria-label="([^"]*?)\.?\s*Minutes"', re.I)


def _parse_section(html, category):
    """Yield (iso_date, title, url) for minutes links inside one category
    section of the AgendaCenter search results."""
    parts = re.split(r"<h2[^>]*>\s*(.*?)\s*Agendas\s*</h2>", html)
    for i in range(1, len(parts) - 1, 2):
        if parts[i].strip() != category:
            continue
        for m in MINUTES_ROW_RE.finditer(parts[i + 1]):
            href, mmddyyyy, label = m.groups()
            if href in KNOWN_MISUPLOAD_URLS:
                print(f"  SKIP {href}: {KNOWN_MISUPLOAD_URLS[href]}")
                continue
            date = f"{mmddyyyy[4:]}-{mmddyyyy[:2]}-{mmddyyyy[2:4]}"
            # label: "June 09, 2026, Work Session" -> title after the year
            title = re.sub(r"^.*?\d{4},\s*", "", label).strip()
            yield date, title, HOST + href


def list_new(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    start_d = (datetime.date.fromisoformat(max_date) + datetime.timedelta(days=1)
               if max_date else datetime.date(2020, 1, 1))
    end_d = datetime.date.today()
    endpoint = SEARCH.format(start=start_d.strftime("%m/%d/%Y"),
                             end=end_d.strftime("%m/%d/%Y"))
    html = rl.http_get(endpoint)
    new = [{"date": d, "title": t or cfg["default_title"], "url": u}
           for d, t, u in _parse_section(html, cfg["category"]) if d > (max_date or "")]
    new.sort(key=lambda x: x["date"])
    notes = ""
    if dataset == "planning_commission" and not new:
        notes = "PC minutes lag agendas by months on this portal — 0 new is normal"
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    cfg = DATASET_CFG[dataset]
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        slug_ix = cfg["slug"](date)                       # index slug (PC embeds date)
        slug_fn = "planning-commission-meeting" if dataset == "planning_commission" \
            else slug_ix                                  # filename slug (bare)
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{slug_fn}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, slug_fn, "md", prefix=f"{dataset}/minutes")
        out = CITY_DIR / rel
        if out.exists():
            print(f"  SKIP {date}: {rel} already exists")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": slug_ix, "path": rel, "source": "civicplus",
                     "source_url": url, "format": "text"})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    name: {
        "portal": "civicplus-agendacenter",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: list_new(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Nephi refresh (CivicPlus AgendaCenter)")
