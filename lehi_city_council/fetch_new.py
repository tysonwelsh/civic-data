#!/usr/bin/env python3
"""
Lehi incremental refresh — Granicus ViewPublisher (lehi.granicus.com).

Datasets:
  meeting_minutes      City Council (+ Work Session / Budget / Joint / Amended)
                       and Local Building Authority (slug building-authority-meeting)
  planning_commission  Planning Commission

Portal pattern (recon.md §1, verified in production):
  * ONE combined HTML table for all bodies:
      GET https://lehi.granicus.com/ViewPublisher.php?view_id=1
    Each <tr class="listingRow"> carries the meeting name, a date like
    "May 28, 2026", and — where minutes exist — a link
      //lehi.granicus.com/MinutesViewer.php?view_id=1&clip_id=<id>&doc_id=<uuid>
  * MinutesViewer 302-redirects to DocumentViewer.php?file=lehi_<hash>.pdf
    (a born-digital PDF). Bare/tool requests get a 14-byte "Redirecting..."
    stub — Granicus requires a BROWSER User-Agent + Referer, so this script
    uses rl.BROWSER_UA (documented exception to the research-tool UA).

Scope decisions (mirror the existing corpus):
  * "Lehi City RDA Meeting" rows are SKIPPED (counted in probe notes): the
    corpus records body=RDA as 0 by design — Lehi's in-council RDA recesses
    carry no motions (see CLAUDE.md); RDA was never part of meeting_minutes.
  * Known Granicus double-event pathology (Phase 1.9 removed 8 duplicate
    pairs): probe dedupes exact (date, name, doc_id) repeats and NOTES any
    same-(date,name) rows with different doc_ids for hands-on review at fetch
    time (2024-06-18 proved to be two real meetings — don't auto-drop).

Modes:
  --probe   (default) list minutes-bearing rows newer than the index max; no fetching
  --fetch   follow each MinutesViewer redirect -> <dataset>/raw/<date>_<slug>.pdf,
            pdftotext -layout -> minutes/<year>/<week>/<date>_<slug>.md, append
            minutes_index.csv rows (source=granicus, source_url=MinutesViewer URL)
            + fetch_log.csv retrieved_date, then run extract_votes.py +
            validate_votes.py for the dataset.

Probe verified live 2026-07-02 (listing HTTP 200 with browser UA). Finding that
day: the CITY has posted no council Minutes links after 2026-01-27 — 19 newer
council meetings sat minutes-less on the portal (PC current through 2026-05-28,
one unposted). The index staleness is source-side, not a scraper gap; re-probe
periodically until Lehi catches up on posting.
"""

import datetime
import html as html_mod
import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://lehi.granicus.com"
LISTING = HOST + "/ViewPublisher.php?view_id=1"

ROW_RE = re.compile(r'<tr class="listingRow">(.*?)</tr>', re.S)
NAME_RE = re.compile(r'headers="Name"[^>]*>\s*(.*?)\s*</td>', re.S)
DATE_RE = re.compile(r'headers="Date[^"]*"[^>]*>([^<]+)</td>')
MIN_RE = re.compile(r'href="(//lehi\.granicus\.com/MinutesViewer\.php\?'
                    r'view_id=1&(?:amp;)?clip_id=(\d+)&(?:amp;)?doc_id=([0-9a-f-]+))"')

PC_RE = re.compile(r"planning commission", re.I)
LBA_RE = re.compile(r"building authority", re.I)
RDA_RE = re.compile(r"\bRDA\b", re.I)
COUNCIL_RE = re.compile(r"council|budget", re.I)


def parse_listing():
    """Yield {name, date, url|None, clip_id, doc_id} for every dated row
    (url=None where the row has no Minutes link yet — unposted minutes)."""
    page = rl.http_get(LISTING, ua=rl.BROWSER_UA)
    rows = []
    for block in ROW_RE.findall(page):
        m_name, m_date, m_min = NAME_RE.search(block), DATE_RE.search(block), MIN_RE.search(block)
        if not (m_name and m_date):
            continue
        name = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m_name.group(1)))).strip()
        try:
            date = datetime.datetime.strptime(
                re.sub(r"\s+", " ", m_date.group(1)).strip(), "%b %d, %Y").date().isoformat()
        except ValueError:
            continue
        rows.append({"name": name, "date": date,
                     "url": "https:" + html_mod.unescape(m_min.group(1)) if m_min else None,
                     "clip_id": m_min.group(2) if m_min else None,
                     "doc_id": m_min.group(3) if m_min else None})
    if not any(r["url"] for r in rows):
        raise RuntimeError("ViewPublisher listing parsed to 0 minutes rows — markup changed?")
    return rows


def classify(name):
    if PC_RE.search(name):
        return "planning_commission"
    if RDA_RE.search(name):
        return "rda"          # skipped by design (empty in-council recesses)
    if LBA_RE.search(name) or COUNCIL_RE.search(name):
        return "meeting_minutes"
    return None


def probe(dataset, max_date):
    rows = parse_listing()
    new, rda_skipped, pending, seen = [], 0, 0, set()
    dupes = []
    for r in rows:
        cls = classify(r["name"])
        if cls == "rda" and dataset == "meeting_minutes" and r["date"] > (max_date or ""):
            rda_skipped += 1
        if cls != dataset:
            continue
        if not r["date"] or (max_date and r["date"] <= max_date) or r["date"] > rl.today():
            continue
        if not r["url"]:
            pending += 1          # meeting listed, minutes not posted yet
            continue
        key = (r["date"], r["name"], r["doc_id"])
        if key in seen:
            continue
        if any(k[0] == r["date"] and k[1] == r["name"] for k in seen):
            dupes.append(f"{r['date']} {r['name']}")
        seen.add(key)
        new.append({"date": r["date"], "title": r["name"], "url": r["url"],
                    "clip_id": r["clip_id"]})
    new.sort(key=lambda x: x["date"])
    notes = []
    if pending:
        notes.append(f"{pending} newer meeting(s) listed with no Minutes link yet (unposted)")
    if rda_skipped:
        notes.append(f"{rda_skipped} newer RDA row(s) skipped by design (RDA=0 corpus decision)")
    if dupes:
        notes.append("possible Granicus double-events (same date+name, different doc_id) — "
                     "review before fetch: " + "; ".join(dupes))
    return {"new_items": new, "endpoint": LISTING, "notes": "; ".join(notes)}


def slug_for(dataset, title):
    if dataset == "planning_commission":
        return "planning-commission-meeting"
    return "building-authority-meeting" if LBA_RE.search(title) else "city-council-meeting"


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    rows, n = [], 0
    for it in items:
        date, title = it["date"], it["title"]
        slug = slug_for(dataset, title)
        pdf = rl.http_get(it["url"], binary=True, ua=rl.BROWSER_UA, referer=LISTING)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date} {title}: got {len(pdf)} bytes, not a PDF (redirect stub?)")
            continue
        base = f"{date}_{slug}"
        rel = rl.minutes_rel_path(date, slug, "md", prefix=f"{dataset}/minutes")
        if (CITY_DIR / rel).exists():   # same-date second meeting -> clip-suffixed name
            base = f"{date}_{slug}_clip{it['clip_id']}"
            rel = rl.minutes_rel_path(date, f"{slug}_clip{it['clip_id']}",
                                      "md", prefix=f"{dataset}/minutes")
        raw = rl.save_raw(ds_dir, base + ".pdf", pdf)
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rl.pdf_to_text(raw), encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": title, "slug": slug,
                     "path": rel, "source": "granicus", "source_url": it["url"],
                     "format": "text"})
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
        "portal": "granicus",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: probe(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in ("meeting_minutes", "planning_commission")
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Lehi refresh (Granicus ViewPublisher)")
