#!/usr/bin/env python3
"""
West Valley City incremental refresh — Hyland OnBase Agenda Online
(https://ob.wvc-ut.gov/OnBaseAgendaOnline; recon.md §1).

Datasets (one portal, one search request serves both):
  meeting_minutes      City Council Regular/Study/Special + Redevelopment
                       Agency (RDA_*) + Municipal Building Authority (BA_*)
                       + one-offs (Strategic Planning) — mirrors the bodies
                       already in minutes_index.csv.
  planning_commission  Planning Commission Regular/Study meetings (the PC
                       "Regular" minutes historically carry a Public_Hearing_*
                       filename — both prefixes are handled).

Portal pattern (verified live 2026-07-02):
  * Search is a plain GET (no CSRF/session needed):
      /Meetings/Search?dropid=11&mtids=all&dropsv=MM/DD/YYYY%2000:00:00&dropev=MM/DD/YYYY%2000:00:00
    Results are rows per meeting; published minutes are anchors whose href
    contains Documents/DownloadFile/<Prefix>_<id>_Minutes_..._.pdf?documentType=2
    and whose title attr is 'View PDF of Minutes for <name> on <M/D/YYYY ...>'.
    Unpublished minutes simply have no anchor (unlike Provo's commented-out
    links, but comments are stripped anyway for safety).
  * The recon warned ob.wvc-ut.gov 403s some non-browser requests; the
    research UA (rl.RESEARCH_UA) got HTTP 200 on 2026-07-02. If the portal
    starts blocking it, switch the requests to rl.BROWSER_UA and note the date.
  * Fallback if the portal dies: PMN mirrors WVC minutes
    (https://www.utah.gov/pmn/sitemap/publicbody/398.html) — not implemented.

The probe uses a 28-day overlap window behind each index max and treats an
item as new only if its (date, slug) is absent from minutes_index.csv —
minutes for same-day sibling meetings (Study vs Regular vs RDA) publish at
different times, so a strict date > max cutoff would miss stragglers.

Modes: --probe (default, read-only listing GET) / --fetch (download new
minutes PDFs -> raw/, pdftotext -layout -> .md, append index rows, then run
extract_votes.py + validate_votes.py).
"""

import datetime
import html as htmllib
import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://ob.wvc-ut.gov"
SEARCH = (HOST + "/OnBaseAgendaOnline/Meetings/Search"
          "?dropid=11&mtids=all&dropsv={start}%2000:00:00&dropev={end}%2000:00:00")
OVERLAP_DAYS = 28

# Minutes-PDF filename prefix -> (dataset, index title, slug).
# Qualifier ({q}) = Regular/Special/Study taken from the filename itself.
PREFIX_MAP = [
    (re.compile(r"^City_Council_(Regular|Study|Special)_"),
     ("meeting_minutes", "City Council {q} Meeting", "council-{ql}-meeting")),
    (re.compile(r"^RDA_(Regular|Special)_"),
     ("meeting_minutes", "Redevelopment Agency {q} Meeting", "redevelopment-agency-meeting")),
    (re.compile(r"^BA_(Regular|Special)_"),
     ("meeting_minutes", "Municipal Building Authority {q} Meeting",
      "municipal-building-authority-meeting")),
    (re.compile(r"^Strategic_Planning_"),
     ("meeting_minutes", "Strategic Planning Meeting", "strategic-planning-meeting")),
    (re.compile(r"^Planning_Commission_Study_"),
     ("planning_commission", "Planning Commission Study Meeting",
      "planning-commission-study-meeting")),
    (re.compile(r"^(Planning_Commission|Public_Hearing)_"),
     ("planning_commission", "Planning Commission Regular Meeting",
      "planning-commission-meeting")),
]

_search_cache = {}


def classify(filename):
    for rx, (dataset, title_t, slug_t) in PREFIX_MAP:
        m = rx.match(filename)
        if m:
            q = m.group(1) if m.groups() else ""
            title = title_t.format(q=q)
            slug = slug_t.format(ql=q.lower())
            # index vocabulary quirk: study slugs are council-study-meeting etc.
            return dataset, title, slug
    return None, None, None


def portal_minutes(start):
    """All published minutes in [start, today]: [(date, dataset, title, slug, url)].
    One cached GET per run."""
    key = start.isoformat()
    if key in _search_cache:
        return _search_cache[key]
    end = datetime.date.today()
    endpoint = SEARCH.format(start=urllib.parse.quote(f"{start:%m/%d/%Y}", safe=""),
                             end=urllib.parse.quote(f"{end:%m/%d/%Y}", safe=""))
    page = re.sub(r"<!--.*?-->", "",
                  rl.http_get(endpoint), flags=re.S)
    out, seen = [], set()
    for m in re.finditer(
            r'<a href="([^"]*Documents/DownloadFile[^"]*?([A-Za-z_]+_\d+_Minutes[^"?]*)\.pdf'
            r'[^"]*documentType=2[^"]*)"[^>]*'
            r'title="View PDF of Minutes for [^"]+? on (\d{1,2})/(\d{1,2})/(\d{4})', page):
        url, fname, mo, d, y = m.groups()
        date = f"{y}-{int(mo):02d}-{int(d):02d}"
        dataset, title, slug = classify(fname)
        if not dataset:
            continue
        if (date, slug) in seen:
            continue
        seen.add((date, slug))
        out.append((date, dataset, title, slug,
                    HOST + htmllib.unescape(url) if url.startswith("/") else htmllib.unescape(url)))
    # meetings with no published minutes yet, for the notes line
    pending = set()
    for m in re.finditer(r'title="View Agenda for ([^"]+?) on (\d{1,2})/(\d{1,2})/(\d{4})', page):
        name, mo, d, y = m.groups()
        date = f"{y}-{int(mo):02d}-{int(d):02d}"
        ds = ("planning_commission" if "Planning Commission" in name
              else "meeting_minutes")
        pending.add((date, ds, name.strip()))
    _search_cache[key] = (out, pending, endpoint)
    return _search_cache[key]


def probe(dataset, max_date):
    start = datetime.date.fromisoformat(max_date) - datetime.timedelta(days=OVERLAP_DAYS)
    minutes, pending, endpoint = portal_minutes(start)
    known = {(r["date"], r["slug"]) for r in rl.load_index(CITY_DIR / dataset)}
    new = [{"date": d, "title": t, "slug": s, "url": u}
           for d, ds, t, s, u in minutes
           if ds == dataset and (d, s) not in known]
    new.sort(key=lambda x: x["date"])
    have = {it["date"] for it in new}
    pending_dates = sorted({d for d, ds, _ in pending
                            if ds == dataset and d > max_date and d not in have
                            and d <= rl.today()})
    notes = (f"{len(pending_dates)} newer meeting date(s) have no published minutes yet"
             if pending_dates else "")
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    rows, n = [], 0
    for it in items:
        url = it["url"].replace("/DownloadFile/", "/DownloadFileBytes/")
        pdf = rl.http_get(url, binary=True,
                          referer=HOST + "/OnBaseAgendaOnline/Meetings/Search")
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {it['date']}: not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{it['date']}_{it['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(it["date"], it["slug"], "md",
                                  prefix=f"{dataset}/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": it["date"], "year": it["date"][:4], "title": it["title"],
                     "slug": it["slug"], "path": rel, "source": "onbase",
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
        "portal": "onbase",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: probe(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in ("meeting_minutes", "planning_commission")
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "West Valley City refresh (OnBase)")
