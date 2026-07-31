#!/usr/bin/env python3
"""
Vineyard incremental refresh — CivicClerk portal (vineyardut.api.civicclerk.com).

Datasets:
  meeting_minutes      City Council (regular + work meetings; categoryName)
  planning_commission  Planning Commission (categoryName)

Portal pattern (recon.md §1, verified live 2026-07-02):
  * List:  GET /v1/Events?$filter=categoryName eq '<body>' and
           startDateTime gt <max>T23:59:59Z&$orderby=startDateTime&$top=200
    Each event carries an inline publishedFiles[] array; minutes = the entry
    with type == "Minutes". The calendar contains FUTURE scheduled events
    (out to 2030) and CANCELLED placeholders — probe ignores both.
  * Download: GET /v1/Meetings/GetMeetingFileStream(fileId=<N>,plainText=true)
    -> clean extracted text (the city's established convention — most
    minutes_index source_urls carry plainText=true). The ,plainText= arg is
    REQUIRED; URLs without it 404. If the text stream comes back empty
    (occasional image-only file), fetch falls back to plainText=false PDF +
    pdftotext, matching the index's few plainText=false rows.

Modes:
  --probe   (default) list events newer than the index max date; fetch nothing
  --fetch   save minutes text (raw PDF also retained under <dataset>/raw/)
            -> minutes/<year>/<week>/<date>_<slug>.md, append minutes_index.csv
            rows (+ fetch_log.csv retrieved_date), then run the dataset's
            extract_votes.py + validate_votes.py.

Probe verified live 2026-07-02 (both datasets, HTTP 200).
"""

import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

API = "https://vineyardut.api.civicclerk.com/v1"
TEXT_URL = API + "/Meetings/GetMeetingFileStream(fileId={fid},plainText=true)"
PDF_URL = API + "/Meetings/GetMeetingFileStream(fileId={fid},plainText=false)"
CANCEL_RE = re.compile(r"cancel", re.I)

DATASET_CFG = {
    "meeting_minutes": {"category": "City Council"},
    "planning_commission": {"category": "Planning Commission"},
}


def list_events(category, max_date):
    since = f"{max_date}T23:59:59Z" if max_date else "2020-01-01T00:00:00Z"
    q = urllib.parse.quote(
        f"categoryName eq '{category}' and startDateTime gt {since}", safe="'()")
    url = f"{API}/Events?$filter={q}&$orderby=startDateTime&$top=200"
    events, endpoint = [], url
    while url:
        data = rl.http_get_json(url)
        events.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return events, endpoint


def probe(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    events, endpoint = list_events(cfg["category"], max_date)
    new, pending = [], []
    for e in events:
        date = (e.get("startDateTime") or "")[:10]
        name = e.get("eventName") or e.get("categoryName") or ""
        if not date or date > rl.today() or CANCEL_RE.search(name):
            continue
        mins = [f for f in e.get("publishedFiles", []) if f.get("type") == "Minutes"]
        if mins:
            new.append({"date": date, "title": name, "fid": mins[0]["fileId"],
                        "url": TEXT_URL.format(fid=mins[0]["fileId"])})
        else:
            pending.append(date)
    notes = (f"{len(pending)} held meeting(s) have no Minutes file yet "
             f"(unapproved): {', '.join(pending)}") if pending else ""
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    rows, n = [], 0
    for it in items:
        date, fid = it["date"], it["fid"]
        slug = rl.slugify(it["title"])
        src_url = TEXT_URL.format(fid=fid)
        text = rl.http_get(src_url)
        # always retain the original PDF too (raw retention policy)
        pdf = rl.http_get(PDF_URL.format(fid=fid), binary=True)
        if pdf.startswith(b"%PDF"):
            raw = rl.save_raw(ds_dir, f"{date}_{slug}.pdf", pdf)
            if len(re.sub(r"\s", "", text)) < 200:  # image-only file: text stream empty
                text = rl.pdf_to_text(raw)
                src_url = PDF_URL.format(fid=fid)
        rel = rl.minutes_rel_path(date, slug, "md")  # index paths are dataset-relative
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": slug, "path": rel, "source": "civicclerk",
                     "source_url": src_url, "format": "text"})
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
    rl.run_cli(CITY_DIR, DATASETS, "Vineyard refresh (CivicClerk)")
