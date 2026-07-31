#!/usr/bin/env python3
"""
Bluffdale incremental refresh — CivicPlus / CivicEngage **AgendaCenter**
(www.bluffdale.gov).

Two datasets, ONE portal (AgendaCenter), distinct category IDs (from recon.md,
re-verify live against the landing page's category panels):

  meeting_minutes      City Council  (AgendaCenter category **CID=2**) — the
                       council minutes doc ALSO carries the in-session RDA and
                       LBA sessions (the Council adjourns/reconvenes as the
                       Redevelopment Agency and Local Building Authority inside
                       the SAME minutes PDF). The council `extract_votes.py`
                       walks the in-doc section headers and tags each motion
                       `body ∈ Council / RDA / LBA` — there is NO separate
                       RDA/LBA category or portal to probe.
  planning_commission  Planning Commission (AgendaCenter category **CID=3**)

Portal pattern (recon.md, re-verify live):
  * Minutes doc URL:  https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<docId>
    (`<docId>` is NOT date-ordered — harvest links, never guess IDs). Docs are a
    mix of born-digital text PDFs, a few Word .docx, and scanned image PDFs.
  * Enumeration: the static /AgendaCenter landing HTML carries the current
    time-window of every category as
    `<td class="minutes"><a href=".../ViewFile/Minutes/_<date>-<id>"
    aria-label="<Month D, YYYY>, <Item Title> (PDF). Minutes">`. Each Minutes
    anchor sits inside its category's `id="catN"` panel, so items route to the
    right dataset by panel position; the aria-label carries the item title. For a
    *forward* refresh (anything newer than the index max) the current window is
    exactly what's needed — full-history back-harvest is a build-time concern.
    If a future gap needs paged views they are `/AgendaCenter/Search` and
    `/AgendaCenter/PreviousVersions`.

This script is SELF-CONTAINED (it does not depend on the build-time
`_manifest.json` that `convert_minutes.py` reads): it downloads each new PDF to
`raw/`, converts it (pdftotext -layout / textutil for .docx / pdftoppm+tesseract
for image-only scans), and writes markdown whose header is byte-compatible with
`convert_minutes.py` (`> Source:` / `> Meeting date:` / `> Body:` / `> Format:`),
then appends `minutes_index.csv` and runs the dataset's extractor + validator.

Modes (shared refresh_lib CLI):
  --probe  (default) list AgendaCenter Minutes items newer than the index max per
           dataset; fetch nothing. Writes refresh_probe.json.
  --fetch  download each new Minutes doc -> raw/, convert (OCR-aware) -> markdown,
           append minutes_index.csv, then run the dataset's extract_votes.py +
           validate_votes.py. Rebuild db / weeks / motions_std afterwards (the
           CLI prints the reminder).

Idempotent + resumable: a raw file or md already on disk is re-used/skipped, and
append_index_rows skips any path already indexed; a relaunch only does the
outstanding work.

TODO (deferred): add a read-only Utah Public Notice (PMN) cross-check like the
Millcreek/South Jordan siblings once Bluffdale's PMN public-body ids are
confirmed. The base build sourced 100% of minutes from CivicPlus, so CivicPlus is
the authoritative fetch source regardless.
"""

import datetime
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://www.bluffdale.gov"
LANDING = f"{HOST}/AgendaCenter"
UA = rl.BROWSER_UA  # CivicPlus serves the portal only to browser-like UAs

# AgendaCenter category id -> (dataset, raw-file body prefix, header body label).
# From recon.md (CID=2 council, CID=3 PC); re-verify against the live landing
# category-panel headings on refresh.
CATS = {
    "2": ("meeting_minutes", "council", "City Council"),
    "3": ("planning_commission", "pc", "Planning Commission"),
}
LOWTEXT = 200  # < this many chars of text layer -> treat as image-only scan, OCR

_MIN_RE = re.compile(
    r'href="(/AgendaCenter/ViewFile/Minutes/_(\d{2})(\d{2})(\d{4})-(\d+))"'
    r'(?:\s+aria-label="([^"]*)")?', re.I)
_CAT_RE = re.compile(r'id="cat(\d+)"', re.I)


# ------------------------------------------------------------------ landing parse

def _title_from_aria(aria, body_label):
    """'May 14, 2025, City Council Meeting Agenda (PDF). Minutes'
    -> 'City Council Meeting Agenda'."""
    if aria:
        t = re.sub(r'^\s*\w+ \d{1,2}, \d{4},\s*', "", aria)
        t = re.sub(r'\s*\(PDF\)\.?\s*Minutes\s*$', "", t, flags=re.I)
        t = re.sub(r'\s*\.?\s*Minutes\s*$', "", t, flags=re.I).strip(" .")
        if t:
            return t
    return f"{body_label} Meeting"


def _week_monday(iso):
    y, m, d = map(int, iso.split("-"))
    dt = date(y, m, d)
    return (dt - timedelta(days=dt.weekday())).isoformat()


def _landing_items():
    """Every Minutes anchor on the AgendaCenter landing, routed to its category
    panel. Returns list of dicts: {dataset, body, label, iso, docid, title, url}."""
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
        dataset, body, label = CATS[cid]
        mm, dd, yyyy, docid = m.group(2), m.group(3), m.group(4), m.group(5)
        iso = f"{yyyy}-{mm}-{dd}"
        items.append({"dataset": dataset, "body": body, "label": label, "iso": iso,
                      "docid": docid, "title": _title_from_aria(m.group(6), label),
                      "url": f"{HOST}{m.group(1)}"})
    return items


# ---------------------------------------------------------------------- probe

def probe(dataset, max_date):
    items = [it for it in _landing_items() if it["dataset"] == dataset]
    new = []
    for it in sorted(items, key=lambda x: (x["iso"], x["docid"])):
        if not it["iso"] or (max_date and it["iso"] <= max_date) or it["iso"] > rl.today():
            continue
        new.append({"date": it["iso"], "title": it["title"], "url": it["url"],
                    "docid": it["docid"]})
    notes = ("CivicPlus AgendaCenter landing (current window); CID=2 = City Council "
             "(RDA/LBA are in-session in the same doc, split by the extractor)."
             if dataset == "meeting_minutes" else
             "CivicPlus AgendaCenter landing (current window); CID=3 = Planning Commission.")
    return {"new_items": new, "endpoint": LANDING, "notes": notes}


# --------------------------------------------------------------------- convert

def _detect(fpath):
    with open(fpath, "rb") as fh:
        head = fh.read(4)
    if head[:2] == b"PK":
        return "docx"
    n = len(subprocess.run(["pdftotext", "-layout", str(fpath), "-"],
                           capture_output=True, text=True).stdout.strip())
    return "text" if n >= LOWTEXT else "ocr"


def _convert_text(fpath):
    return subprocess.run(["pdftotext", "-layout", str(fpath), "-"],
                          capture_output=True, text=True).stdout


def _convert_docx(fpath):
    tmp = str(fpath) + ".docx"
    shutil.copy(fpath, tmp)
    try:
        return subprocess.run(["textutil", "-convert", "txt", "-stdout", tmp],
                              capture_output=True, text=True).stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


def _convert_ocr(fpath):
    tdir = tempfile.mkdtemp(prefix="blf_ocr_")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(fpath),
                        str(Path(tdir) / "p")], check=False, capture_output=True)
        chunks = []
        for pg in sorted(Path(tdir).glob("p*.png")):
            r = subprocess.run(["tesseract", str(pg), "-", "--psm", "6"],
                               capture_output=True, text=True)
            chunks.append(r.stdout)
        return "\n\n".join(chunks)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def _convert(fpath):
    """(text, format, engine) — matches convert_minutes.py vocabulary."""
    fmt = _detect(fpath)
    if fmt == "docx":
        return _convert_docx(fpath), "text", "textutil-docx"
    if fmt == "text":
        return _convert_text(fpath), "text", "pdftotext"
    return _convert_ocr(fpath), "ocr", "tesseract-ocr"


# ----------------------------------------------------------------------- fetch

def _fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    body = CATS_BY_DATASET[dataset]["body"]
    label = CATS_BY_DATASET[dataset]["label"]
    n = 0
    rows = []
    for it in items:
        iso, docid = it["date"], it["docid"]
        year = iso[:4]
        base = f"{body}_{iso}_{docid}"                       # council_2025-05-14_1621
        rel = f"minutes/{year}/{_week_monday(iso)}/{base}.md"
        out = ds_dir / rel
        if out.exists():
            continue  # resumable
        raw = ds_dir / "raw" / f"{base}.pdf"
        if not raw.exists():
            data = rl.http_get(it["url"], binary=True, ua=UA)
            if not (data.startswith(b"%PDF") or data[:2] == b"PK"):
                print(f"  SKIP {iso} {docid}: response not a PDF/DOCX ({it['url']})")
                continue
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(data)
        text, fmt, engine = _convert(raw)
        title = it["title"]
        hdr = (f"# {iso} {title}\n"
               f"> Source: {it['url']}\n"
               f"> Meeting date: {iso}\n"
               f"> Body: {label}\n"
               f"> Format: {fmt} ({engine})\n\n---\n\n")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(hdr + text, encoding="utf-8")
        rows.append({"date": iso, "year": year, "title": title, "slug": base,
                     "path": rel, "source": "civicplus", "source_url": it["url"],
                     "format": fmt})
        n += 1
        print(f"  fetched {rel}  [{fmt}]")
    rl.append_index_rows(ds_dir, rows)
    return n


def _post(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir,
                         f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir,
                         f"{dataset} validate_votes")


# ----------------------------------------------------------------- dataset wiring

CATS_BY_DATASET = {ds: {"body": body, "label": label}
                   for _cid, (ds, body, label) in CATS.items()}

DATASETS = {
    "meeting_minutes": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": lambda mx: probe("meeting_minutes", mx),
        "fetch": lambda items: _fetch("meeting_minutes", items),
        "post_fetch": lambda: _post("meeting_minutes"),
    },
    "planning_commission": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": lambda mx: probe("planning_commission", mx),
        "fetch": lambda items: _fetch("planning_commission", items),
        "post_fetch": lambda: _post("planning_commission"),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Bluffdale refresh (CivicPlus AgendaCenter)")
