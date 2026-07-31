#!/usr/bin/env python3
"""
Park City incremental refresh — CivicClerk portal (parkcityut.api.civicclerk.com).

Datasets:
  meeting_minutes      City Council (categoryId 26)
  planning_commission  Planning Commission (categoryName)

Portal pattern (recon.md §1, verified live 2026-07-02):
  * List:  GET /v1/Events?$filter=<category> and startDateTime gt <max>T23:59:59Z
           &$orderby=startDateTime&$top=100   (OData, open, no auth)
    Each event carries an inline publishedFiles[] array; the minutes doc is the
    entry with type == "Minutes" (top-level minutesFile slots are usually empty).
    The calendar contains FUTURE scheduled events — probe ignores dates > today.
  * Download: GET /v1/Meetings/GetMeetingFileStream(fileId=<N>,plainText=false)
    -> born-digital PDF (the ,plainText= arg is REQUIRED — URLs without it 404).

Modes:
  --probe   (default) list events newer than the index max date; fetch nothing
  --fetch   download new minutes PDFs -> <dataset>/raw/, convert with
            pdftotext -layout -> minutes/<year>/<week>/<date>_<slug>.md,
            append minutes_index.csv rows (+ fetch_log.csv retrieved_date),
            then run the dataset's extract_votes.py + validate_votes.py.

Probe verified live 2026-07-02 (both datasets, HTTP 200).
"""

import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

API = "https://parkcityut.api.civicclerk.com/v1"
FILE_URL = API + "/Meetings/GetMeetingFileStream(fileId={fid},plainText=false)"
CANCEL_RE = re.compile(r"cancel", re.I)

DATASET_CFG = {
    "meeting_minutes": {
        "filter": "categoryId eq 26",
        "slug": "city-council-meeting",
    },
    "planning_commission": {
        "filter": "categoryName eq 'Planning Commission'",
        "slug": "planning-commission-meeting",
    },
}


def list_events(odata_filter, max_date):
    since = f"{max_date}T23:59:59Z" if max_date else "2020-01-01T00:00:00Z"
    q = urllib.parse.quote(f"{odata_filter} and startDateTime gt {since}", safe="'()")
    url = f"{API}/Events?$filter={q}&$orderby=startDateTime&$top=200"
    events, endpoint = [], url
    while url:
        data = rl.http_get_json(url)
        events.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return events, endpoint


def probe(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    events, endpoint = list_events(cfg["filter"], max_date)
    new, pending = [], []
    for e in events:
        date = (e.get("startDateTime") or "")[:10]
        name = e.get("eventName") or e.get("categoryName") or ""
        if not date or date > rl.today() or CANCEL_RE.search(name):
            continue
        mins = [f for f in e.get("publishedFiles", []) if f.get("type") == "Minutes"]
        if mins:
            new.append({"date": date, "title": name,
                        "url": FILE_URL.format(fid=mins[0]["fileId"])})
        else:
            pending.append(date)
    notes = (f"{len(pending)} held meeting(s) have no Minutes file yet "
             f"(unapproved): {', '.join(pending)}") if pending else ""
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    cfg = DATASET_CFG[dataset]
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{cfg['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, cfg["slug"], "md")  # index paths are dataset-relative
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": cfg["slug"], "path": rel, "source": "civicclerk",
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
        "portal": "civicclerk",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: probe(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Park City refresh (CivicClerk)")
