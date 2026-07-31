#!/usr/bin/env python3
"""
Millcreek incremental refresh — CivicPlus / CivicEngage **AgendaCenter**
(www.millcreekut.gov; the legacy millcreek.us host 301-redirects here).

Two datasets, ONE portal (AgendaCenter), distinct category IDs (verified live
2026-07-06 against the landing page's category panels):

  meeting_minutes      City Council  (AgendaCenter category **cat3**)
                       + Community Reinvestment Agency / CRA (category **cat7**)
                       — the build folds Council + CRA into one folder (the
                       council extractor tags each file's `body` from front
                       matter: 314 Council + 58 CRA files), so this dataset
                       probes BOTH cat3 and cat7.
  planning_commission  Planning Commission (category **cat2**)

Portal pattern (recon.md §1, re-verified live 2026-07-06):
  * Minutes doc URL:  https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<docId>
    (`<docId>` is NOT date-ordered — harvest links, never guess IDs). The doc is
    a large combined Agenda + Packet PDF (8-35 MB); the minutes text is the front.
  * Enumeration: the JS category app POSTs `/AgendaCenter/UpdateCategoryList`,
    but that endpoint 404s to a plain client; the **static /AgendaCenter landing
    HTML still carries the current time-window** of every category as
    `<td class="minutes"><a href=".../ViewFile/Minutes/_<date>-<id>"
    aria-label="<Month D, YYYY>, <Item Title> (PDF). Minutes">`. Each Minutes
    anchor sits inside its category's `id="catN"` panel, so items route to the
    right body by panel position; the aria-label carries the item title.
    For a *forward* refresh (anything newer than the index max) the current
    window is exactly what's needed — full-history back-harvest (2016-2019) is a
    build-time concern, not a refresh one. If a future gap needs the paged views,
    they are `/AgendaCenter/Search` and `/AgendaCenter/PreviousVersions`.
  * **PMN secondary probe (meeting_minutes only):** the Utah Public Notice
    listing for the Millcreek City Council public body (id **5741**),
    `https://www.utah.gov/pmn/list/notices.html?id=5741&page=0`, is probed
    read-only as a cross-check for council meetings that might post to PMN before
    CivicPlus. The build sourced 100% of minutes from CivicPlus, so CivicPlus is
    the authoritative fetch source; PMN new-notice counts surface only in the
    probe notes (never fetched from here) — mirror the sibling South Jordan model.

Datasets differ in how a new doc is converted (Millcreek's two pipelines are not
symmetric — unlike the South Jordan sibling):
  * meeting_minutes has NO convert.py (the build converted council/CRA inline);
    this script therefore converts a new council/CRA PDF itself (pdftotext
    -layout, OCR fallback for image-only scans) and writes the council/CRA
    front-matter the extractor reads (`**Body:** Council|CRA`).
  * planning_commission HAS an authoritative, resumable `convert.py` driven by
    `_pc_links.json`; a new PC doc is appended there + dropped in raw/, then
    `convert.py` rebuilds the md + index. We reuse that tested code rather than
    re-implement PC front matter.

Modes (shared refresh_lib CLI):
  --probe  (default) list AgendaCenter Minutes items newer than the index max per
           dataset + the PMN new-notice count; fetch nothing. Writes refresh_probe.json.
  --fetch  download each new Minutes PDF -> raw/, convert (OCR-aware) -> markdown,
           append minutes_index.csv (+ fetch_log.csv), then run the dataset's
           extract_votes.py + validate_votes.py. Rebuild db / weeks / motions_std
           afterwards (the CLI prints the reminder).

Idempotent + resumable: a raw PDF or md already on disk is re-used/skipped, and
append_index_rows skips any path already indexed; a relaunch only does the
outstanding work.
"""

import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://www.millcreekut.gov"
LANDING = f"{HOST}/AgendaCenter"
UA = rl.BROWSER_UA  # CivicPlus serves the portal only to browser-like UAs

# AgendaCenter category id -> (dataset, council-body-tag). Verified from the
# landing page category-panel headings 2026-07-06.
CATS = {
    "3": ("meeting_minutes", "Council"),
    "7": ("meeting_minutes", "CRA"),
    "2": ("planning_commission", "Planning Commission"),
}
# Utah Public Notice public bodies (live entity chain 2026-07-06: municipality
# id=1279 -> publicBodies). The council probe uses 5741; PC/CRA ids recorded for
# completeness (the older "1031" id was stale and has been corrected).
PMN_COUNCIL_BODY_ID = "5741"  # Millcreek City Council
PMN_PC_BODY_ID = "5815"       # Planning Commission
PMN_CRA_BODY_ID = "6367"      # Community Reinvestment Agency
LOWTEXT = 800  # < this many chars of text layer -> treat as image-only scan, OCR

_MIN_RE = re.compile(
    r'href="(/AgendaCenter/ViewFile/Minutes/_(\d{2})(\d{2})(\d{4})-(\d+))"'
    r'(?:\s+aria-label="([^"]*)")?', re.I)
_CAT_RE = re.compile(r'id="cat(\d+)"', re.I)


# ------------------------------------------------------------------ landing parse

def _title_from_aria(aria, body_tag):
    """'May 26, 2026, City Council Meeting Agenda and Packet (PDF). Minutes'
    -> 'City Council Meeting Agenda and Packet'."""
    if aria:
        t = re.sub(r'^\s*\w+ \d{1,2}, \d{4},\s*', "", aria)
        t = re.sub(r'\s*\(PDF\)\.?\s*Minutes\s*$', "", t, flags=re.I)
        t = re.sub(r'\s*\.?\s*Minutes\s*$', "", t, flags=re.I).strip(" .")
        if t:
            return t
    return {"Council": "City Council Meeting", "CRA": "Community Reinvestment Agency Meeting",
            "Planning Commission": "Planning Commission Meeting"}[body_tag]


def _landing_items():
    """Every Minutes anchor on the AgendaCenter landing, routed to its category
    panel. Returns list of dicts: {dataset, body, iso, docid, title, url}."""
    html = rl.http_get(LANDING, ua=UA)
    cat_pos = sorted(((m.group(1), m.start()) for m in _CAT_RE.finditer(html)),
                     key=lambda x: x[1])

    def cat_for(pos):
        cid = None
        for c, p in cat_pos:
            if p <= pos:
                cid = c
            else:
                break
        return cid

    items = []
    for m in _MIN_RE.finditer(html):
        cid = cat_for(m.start())
        if cid not in CATS:
            continue
        dataset, body = CATS[cid]
        mm, dd, yyyy, docid = m.group(2), m.group(3), m.group(4), m.group(5)
        iso = f"{yyyy}-{mm}-{dd}"
        items.append({"dataset": dataset, "body": body, "iso": iso, "docid": docid,
                      "title": _title_from_aria(m.group(6), body),
                      "url": f"{HOST}{m.group(1)}"})
    return items


def _pmn_new_count(max_date):
    """Read-only PMN cross-check: how many Millcreek City Council notices are
    dated after the index max. Best-effort; returns (count, note)."""
    try:
        html = rl.http_get(
            f"https://www.utah.gov/pmn/list/notices.html?id={PMN_COUNCIL_BODY_ID}&page=0")
    except Exception as e:  # noqa: BLE001
        return None, f"PMN probe skipped ({type(e).__name__})"
    n = 0
    for mo, dd, yy in re.findall(r'(\w+)\s+(\d{1,2}),\s+(20\d{2})', html):
        try:
            iso = datetime.datetime.strptime(f"{mo} {dd} {yy}", "%B %d %Y").date().isoformat()
        except ValueError:
            continue
        if (not max_date or iso > max_date) and iso <= rl.today():
            n += 1
    return n, (f"PMN body {PMN_COUNCIL_BODY_ID}: {n} council notice(s) newer than index "
               f"max (cross-check only — CivicPlus is the authoritative fetch source)")


# ---------------------------------------------------------------------- probe

def probe(dataset, max_date):
    items = [it for it in _landing_items() if it["dataset"] == dataset]
    new = []
    for it in sorted(items, key=lambda x: (x["iso"], x["docid"])):
        if not it["iso"] or (max_date and it["iso"] <= max_date) or it["iso"] > rl.today():
            continue
        new.append({"date": it["iso"], "title": f"{it['title']} ({it['body']})",
                    "url": it["url"], "body": it["body"], "docid": it["docid"],
                    "raw_title": it["title"]})
    notes = ("CivicPlus AgendaCenter landing (current window); cat3=Council + cat7=CRA."
             if dataset == "meeting_minutes" else
             "CivicPlus AgendaCenter landing (current window); cat2=Planning Commission.")
    if dataset == "meeting_minutes":
        pmn_n, pmn_note = _pmn_new_count(max_date)
        notes += " | " + pmn_note
    return {"new_items": new, "endpoint": LANDING, "notes": notes}


# ---------------------------------------------------------------------- convert

def _pdf_text(pdf_path):
    return subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                          capture_output=True, timeout=300).stdout.decode("utf-8", "replace")


def _ocr(pdf_path):
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-png", "-r", "200", str(pdf_path),
                        str(Path(td) / "p")], check=True, timeout=1800)
        for png in sorted(Path(td).glob("p*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(out)


def _convert(pdf_path):
    """(text, format) — pdftotext -layout, OCR fallback for image-only scans.
    format uses the meeting_minutes vocabulary ('text' / 'scanned')."""
    txt = _pdf_text(pdf_path)
    if len(txt.strip()) < LOWTEXT:
        return _ocr(pdf_path), "scanned"
    return txt, "text"


# ------------------------------------------------------- fetch: meeting_minutes

def _fetch_council(items):
    ds_dir = CITY_DIR / "meeting_minutes"
    n = 0
    rows = []
    for it in items:
        iso, docid, body = it["date"], it["docid"], it["body"]
        year = iso[:4]
        slug = f"{rl.slugify(it['raw_title'])}-{docid}"
        rel = f"minutes/{year}/{iso}/{iso}_{slug}.md"
        out = ds_dir / rel
        if out.exists():
            continue  # resumable
        pdf_name = f"{iso}_{body}_{docid}.pdf"
        raw_pdf = ds_dir / "raw" / year / pdf_name
        if not raw_pdf.exists():
            data = rl.http_get(it["url"], binary=True, ua=UA)
            if not data.startswith(b"%PDF"):
                print(f"  SKIP {iso} {body} {docid}: response not a PDF ({it['url']})")
                continue
            raw_pdf.parent.mkdir(parents=True, exist_ok=True)
            raw_pdf.write_bytes(data)
        txt, fmt = _convert(raw_pdf)
        d = datetime.date.fromisoformat(iso)
        date_ok = "YES" if re.search(
            rf"{d.strftime('%B')}\s+0?{d.day}\D{{0,4}}{d.year}", txt, re.I) else "NO"
        header = (f"# {it['raw_title']}\n\n"
                  f"**Body:** {body}\n**Date:** {iso}\n"
                  f"**Source:** civicplus (AgendaCenter)\n**Source URL:** {it['url']}\n"
                  f"**Format:** {fmt}\n**In-body date match:** {date_ok}\n\n---\n\n")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(header + txt.rstrip() + "\n", encoding="utf-8")
        rows.append({"date": iso, "year": year, "title": it["raw_title"], "slug": slug,
                     "path": rel, "source": "civicplus", "source_url": it["url"],
                     "format": fmt})
        n += 1
        print(f"  fetched {rel}  [{fmt}]")
    rl.append_index_rows(ds_dir, rows)
    return n


def _post_council():
    ds_dir = CITY_DIR / "meeting_minutes"
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, "council extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, "council validate_votes")


# --------------------------------------------------- fetch: planning_commission

def _fetch_pc(items):
    """Drop new PC PDFs in raw/, register them in _pc_links.json, then let the
    authoritative convert.py rebuild the md + index."""
    ds_dir = CITY_DIR / "planning_commission"
    links_path = ds_dir / "_pc_links.json"
    links = json.loads(links_path.read_text())
    known = {(mmdd, docid) for _yr, mmdd, docid, _lbl in links}
    n = 0
    for it in items:
        iso, docid = it["date"], it["docid"]
        mmdd = f"{iso[5:7]}{iso[8:10]}{iso[:4]}"
        year = iso[:4]
        raw_pdf = ds_dir / "raw" / year / f"{iso}_pc_{docid}.pdf"
        if (mmdd, docid) in known and raw_pdf.exists():
            continue  # resumable
        if not raw_pdf.exists():
            data = rl.http_get(it["url"], binary=True, ua=UA)
            if not data.startswith(b"%PDF"):
                print(f"  SKIP {iso} PC {docid}: response not a PDF ({it['url']})")
                continue
            raw_pdf.parent.mkdir(parents=True, exist_ok=True)
            raw_pdf.write_bytes(data)
        if (mmdd, docid) not in known:
            # label mirrors _pc_links.json shape: "<Month D, YYYY>, <Title>. Minutes"
            label = (f"{datetime.date.fromisoformat(iso).strftime('%B %-d, %Y')}, "
                     f"{it['raw_title']}. Minutes")
            links.append([year, mmdd, docid, label])
            known.add((mmdd, docid))
        n += 1
        print(f"  staged raw/{year}/{iso}_pc_{docid}.pdf")
    links.sort(key=lambda x: (x[1][4:8], x[1][0:2], x[1][2:4], x[2]))
    links_path.write_text(json.dumps(links, ensure_ascii=False, indent=0) + "\n",
                          encoding="utf-8")
    return n


def _post_pc():
    ds_dir = CITY_DIR / "planning_commission"
    rl.run_pipeline_step(["python3", "convert.py"], ds_dir, "PC convert (md + index)")
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, "PC extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, "PC validate_votes")


# ----------------------------------------------------------------- dataset wiring

DATASETS = {
    "meeting_minutes": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": lambda mx: probe("meeting_minutes", mx),
        "fetch": _fetch_council,
        "post_fetch": _post_council,
    },
    "planning_commission": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": lambda mx: probe("planning_commission", mx),
        "fetch": _fetch_pc,
        "post_fetch": _post_pc,
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Millcreek refresh (CivicPlus AgendaCenter)")
