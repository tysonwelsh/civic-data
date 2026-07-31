#!/usr/bin/env python3
"""
Orem incremental refresh — CivicClerk (meeting calendar) + Google Drive
(the official minutes-PDF archive).

Datasets:
  meeting_minutes      City Council       (index source=gdrive)
  planning_commission  Planning Commission (index source=googledrive)

TWO-SOURCE PATTERN (verified live 2026-07-02):
  * CivicClerk OData API (oremut.api.civicclerk.com/v1/Events) enumerates
    meetings, BUT Orem publishes NO Minutes files in the publishedFiles slots
    (agendas/packets only — confirmed again on probe day, as recon warned).
    It is used only to report which held meetings still lack minutes.
  * The actual minutes PDFs live in the city's public Google Drive archive
    (orem.gov/meetings "View Archived Meeting Agendas & Minutes", root folder
    1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv). The KEYLESS listing endpoint
        https://drive.google.com/embeddedfolderview?id=<folderId>#list
    returns plain HTML (no auth, no JS) — verified live. Layout:
      Minutes-City Council/<YYYY>/<MM Month>/  ->  "MM.DD.YYYY CC min(ute)s.pdf"
      Minutes/Planning Commission Minutes/<YYYY>/ -> "MM.DD.YYYY [Approved|Draft] PC Minutes.pdf"
    Download: https://drive.google.com/uc?export=download&id=<fileId>
    (the index's established source_url form).

Modes:
  --probe   (default) walk the current Drive year folders + CivicClerk
            calendar; report minutes files newer than the index max; fetch nothing
  --fetch   download new PDFs -> <dataset>/raw/, convert with pdftotext
            -layout -> minutes/<year>/<week>/<date>_<slug>.md, append
            minutes_index.csv rows (+ fetch_log.csv retrieved_date), then run
            extract_votes.py + validate_votes.py.
            CAVEAT: many recent Orem minutes are image-only scans (index
            format=ocr). If pdftotext yields no text layer the script marks the
            file and tells you to OCR it (tesseract, 300 dpi — the convention
            used for the 68 repaired 2022-2026 files); it never fakes text.

Probe verified live 2026-07-02 (both datasets; Drive listing + CivicClerk OK).
"""

import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

CIVICCLERK = "https://oremut.api.civicclerk.com/v1"
DRIVE_LIST = "https://drive.google.com/embeddedfolderview?id={fid}"
DRIVE_DL = "https://drive.google.com/uc?export=download&id={fid}"

CC_MINUTES_ROOT = "1eNNpurKDzW6YkTehj0mUBskkORO-FAF4"   # Minutes-City Council/
PC_MINUTES_ROOT = "1A-vDkppTnTLUrKkdjVp7ui2bHnaXUWRx"   # Minutes/Planning Commission Minutes/

DIR_RE = re.compile(
    r'href="https://drive\.google\.com/drive/folders/([\w-]+)"[^>]*>.*?'
    r'<div class="flip-entry-title">([^<]*)</div>', re.S)
FILE_RE = re.compile(
    r'href="https://drive\.google\.com/file/d/([\w-]+)/view[^"]*"[^>]*>.*?'
    r'<div class="flip-entry-title">([^<]*)</div>', re.S)
# minutes filenames: "05.12.2026 CC minutes.pdf" / "04.15.2026 Approved PC Minutes.pdf"
CC_MIN_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\s.*\bCC\b.*\bmin", re.I)
PC_MIN_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\s.*\bPC\s+min", re.I)
CANCEL_RE = re.compile(r"cancel", re.I)


def drive_ls(folder_id):
    html = rl.http_get(DRIVE_LIST.format(fid=folder_id))
    dirs = {name.strip(): fid for fid, name in DIR_RE.findall(html)}
    files = [(fid, name.strip()) for fid, name in FILE_RE.findall(html)]
    return dirs, files


def held_meetings_without_minutes(category, max_date, have_dates):
    """CivicClerk cross-check: held (non-cancelled, past) meetings since
    max_date whose minutes we neither have nor found on Drive."""
    since = f"{max_date}T23:59:59Z" if max_date else "2020-01-01T00:00:00Z"
    q = urllib.parse.quote(
        f"categoryName eq '{category}' and startDateTime gt {since}", safe="'()")
    url = f"{CIVICCLERK}/Events?$filter={q}&$orderby=startDateTime&$top=200"
    pending = []
    while url:
        data = rl.http_get_json(url)
        for e in data.get("value", []):
            date = (e.get("startDateTime") or "")[:10]
            name = e.get("eventName") or ""
            if not date or date > rl.today() or CANCEL_RE.search(name):
                continue
            if date not in have_dates:
                pending.append(date)
        url = data.get("@odata.nextLink")
    return pending


def scan_drive(dataset, max_date):
    """Yield (date, filename, drive_file_id) for minutes files newer than max_date."""
    root = CC_MINUTES_ROOT if dataset == "meeting_minutes" else PC_MINUTES_ROOT
    pat = CC_MIN_RE if dataset == "meeting_minutes" else PC_MIN_RE
    y0 = int(max_date[:4]) if max_date else 2020
    years, _ = drive_ls(root)
    out = []
    for yname, yid in sorted(years.items()):
        if not yname.isdigit() or int(yname) < y0:
            continue
        subdirs, files = drive_ls(yid)
        # council years contain "MM Month" subfolders; PC years are flat
        for _, sid in sorted(subdirs.items()):
            _, sub_files = drive_ls(sid)
            files += sub_files
        for fid, name in files:
            m = pat.match(name)
            if not m:
                continue
            mo, dd, yy = m.groups()
            date = f"{yy}-{mo}-{dd}"
            if max_date and date <= max_date:
                continue
            out.append({"date": date, "name": name, "fid": fid})
    # a date can appear as Draft AND Approved — keep one (prefer Approved)
    best = {}
    for it in out:
        cur = best.get(it["date"])
        if cur is None or ("approved" in it["name"].lower()
                           and "approved" not in cur["name"].lower()):
            best[it["date"]] = it
    return sorted(best.values(), key=lambda x: x["date"])


def probe(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    found = scan_drive(dataset, max_date)
    new = [{"date": it["date"], "title": f"{cfg['title']} ({it['name']})",
            "url": DRIVE_DL.format(fid=it["fid"]), "name": it["name"]}
           for it in found]
    pending = held_meetings_without_minutes(
        cfg["category"], max_date, {it["date"] for it in found})
    notes = "minutes from Google Drive archive; CivicClerk carries agendas/packets only"
    if pending:
        notes += (f"; {len(pending)} held meeting(s) have no minutes on Drive yet: "
                  + ", ".join(pending))
    return {"new_items": new,
            "endpoint": DRIVE_LIST.format(fid=CC_MINUTES_ROOT if dataset ==
                                          "meeting_minutes" else PC_MINUTES_ROOT),
            "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    cfg = DATASET_CFG[dataset]
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: Drive did not return a PDF ({len(pdf)} bytes; "
                  "large-file interstitial? download manually)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{cfg['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        fmt = "text"
        if len(re.sub(r"\s", "", text)) < 300:
            fmt = "ocr"
            print(f"  NOTE {date}: no text layer (image-only scan) — OCR needed "
                  f"(pdftoppm -r 300 + tesseract on {raw.name}); writing stub is refused")
            # leave the raw PDF for the OCR pass; no fake .md
            continue
        rel = rl.minutes_rel_path(date, cfg["slug"], "md",
                                  prefix=f"{dataset}/minutes")  # index paths are city-relative
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": cfg["title"],
                     "slug": cfg["slug"], "path": rel, "source": cfg["source"],
                     "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASET_CFG = {
    "meeting_minutes": {"category": "City Council", "slug": "city-council",
                        "title": "City Council Meeting", "source": "gdrive"},
    "planning_commission": {"category": "Planning Commission",
                            "slug": "planning-commission-meeting",
                            "title": "Planning Commission", "source": "googledrive"},
}

DATASETS = {
    name: {
        "portal": "gdrive+civicclerk",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: probe(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Orem refresh (Google Drive + CivicClerk)")
