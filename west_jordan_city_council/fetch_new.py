#!/usr/bin/env python3
"""
West Jordan incremental refresh — PrimeGov portal (westjordan.primegov.com).

Datasets:
  meeting_minutes      City Council (regular/special) minutes
  planning_commission  Planning Commission minutes

Portal pattern (recon.md §1, verified in production):
  * List:  GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY  -> JSON
           each meeting: id, title, dateTime, documentList[] (templateName/templateId)
  * Minutes doc = documentList entry with templateName == "Minutes"
    (NOT "HTML Minutes" — that's SLC; WJ minutes are PDFs).
  * Download: GET /Public/CompiledDocument?meetingTemplateId=<templateId>
    which 302s to a short-lived Azure-blob SAS URL — resolve + download in one
    pass (urllib follows the redirect). Browser UA required by the blob host.

Modes:
  --probe   (default) list meetings newer than the index max date; fetch nothing
  --fetch   download new minutes PDFs -> <dataset>/raw/, convert with
            pdftotext -layout -> minutes/<year>/<week>/<date>_<slug>.md,
            append minutes_index.csv rows (+ fetch_log.csv retrieved_date),
            then run the dataset's extract_votes.py + validate_votes.py.

Probe verified live 2026-07-02 (both datasets, HTTP 200).
"""

import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://westjordan.primegov.com"
LIST_API = HOST + "/api/v2/PublicPortal/ListArchivedMeetings?year={year}"
DOC_URL = HOST + "/Public/CompiledDocument?meetingTemplateId={tid}"

DATASET_CFG = {
    "meeting_minutes": {
        "title_re": re.compile(r"city council", re.I),
        "slug": "city-council-regular-meeting",
        "title_out": "City Council Regular Meeting",
        "format": "pdf-text",
    },
    "planning_commission": {
        "title_re": re.compile(r"planning commission", re.I),
        "slug": "planning-commission-meeting",
        "title_out": "Planning Commission",
        "format": "text",
    },
}


def minutes_template(meeting):
    for d in meeting.get("documentList", []):
        if d.get("templateName") == "Minutes":
            return d.get("templateId")
    return None


def list_new(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    y0 = int(max_date[:4]) if max_date else 2020
    y1 = int(rl.today()[:4])
    new, pending = [], 0
    endpoint = LIST_API.format(year=y1)
    for year in range(y0, y1 + 1):
        meetings = rl.http_get_json(LIST_API.format(year=year))
        for m in meetings:
            date = (m.get("dateTime") or "")[:10]
            if not date or (max_date and date <= max_date):
                continue
            if not cfg["title_re"].search(m.get("title", "")):
                continue
            tid = minutes_template(m)
            if not tid:
                pending += 1          # meeting happened, minutes not posted yet
                continue
            new.append({"date": date, "title": m.get("title", ""),
                        "url": DOC_URL.format(tid=tid)})
    new.sort(key=lambda x: x["date"])
    notes = f"{pending} newer meeting(s) have no Minutes doc yet (unapproved)" if pending else ""
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def title_slug(base_slug, title):
    """Derive the slug from the PrimeGov meeting title so same-date sibling
    meetings never collide (Q3-2026 finding: a PC Work Session + Regular
    Meeting on 2026-06-16 both wrote the fixed slug's path — the second fetch
    silently overwrote the first; 3 earlier 2026 dates had the same defect)."""
    t = (title or "").lower()
    for token, suffix in (("work session", "work-session"),
                          ("study", "study-meeting"),
                          ("special", "special-meeting")):
        if token in t:
            return f"{base_slug.rsplit('-meeting', 1)[0].rsplit('-regular', 1)[0]}-{suffix}"
    return base_slug


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    cfg = DATASET_CFG[dataset]
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        pdf = rl.http_get(url, binary=True, ua=rl.BROWSER_UA)  # blob host rejects tool UA
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        slug = title_slug(cfg["slug"], it.get("title"))
        raw = rl.save_raw(ds_dir, f"{date}_{slug}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, slug, "md", prefix=f"{dataset}/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"] or cfg["title_out"],
                     "slug": slug, "path": rel, "source": "primegov",
                     "source_url": url, "format": cfg["format"]})
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
        "portal": "primegov",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: list_new(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "West Jordan refresh (PrimeGov)")
