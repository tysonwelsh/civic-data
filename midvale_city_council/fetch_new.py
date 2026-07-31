#!/usr/bin/env python3
"""
Midvale incremental refresh — Revize "Document Center" (static files, NO API;
midvale.utah.gov).

Datasets:
  meeting_minutes      City Council (+ in-session RDA) minutes
  planning_commission  Planning & Zoning Commission minutes

Portal pattern (recon.md §Portal / §Planning Commission; SOURCES.md — verified at
build time 2026-07-12):
  * Council listing: a single flat Revize page listing every year in-line —
    /government/departments/recorder_s_office/agendas___minutes.php
    Minutes files live under
      Document Center/Agendas & Minutes/Recorders Office/<YEAR>/Minutes/
    named "CC Minutes <M-D-YYYY>.pdf" (recent) — plus a few flat-path
    "Document Center/Agendas & Minutes/CC Minutes <M-D-YYYY>.pdf" (no year folder)
    and legacy separator-less "CC Minutes <MDYYYY>.pdf" / .docx (all pre-floor,
    already indexed).
  * PC listing: /government/departments/community_development/planning_and_zoning/
    planning___zoning_commission.php (itself the flat listing). Files under
      Document Center/Agendas & Minutes/Planning & Zoning Commission/<YEAR>/Minutes/
    named "<M.D.YY>_Minutes_APPROVED.pdf" (dot-dates, 2-digit year; sometimes
    "_w_votes").
  * All Document Center hrefs carry spaces + a literal "&" and a ?t=<token>
    cache-buster — the driver URL-encodes and uses refresh_lib.BROWSER_UA.

Conversion mirrors convert_minutes.py: pdftotext -layout, OCR fallback
(pdftoppm 300dpi + tesseract) for scanned PDFs, .docx via macOS textutil; each
doc gets the standard provenance header the extractor expects, filed under
<dataset>/minutes/<year>/<week-monday>/<date>_<slug>.md, source="revize".

Modes:
  --probe   (default) list minutes newer than each dataset's index max date;
            fetch nothing. Writes refresh_probe.json.
  --fetch   download new minutes -> <dataset>/raw/, convert -> .md, append
            minutes_index.csv rows (+ fetch_log.csv), then run the dataset's
            extract_votes.py + validate_votes.py.

After --fetch, rebuild the derived layers:
    python3 db/build_db.py && python3 db/build_referrals.py
    python3 build_weeks.py
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

BASE = "https://www.midvale.utah.gov/"
COUNCIL_LIST = BASE + "government/departments/recorder_s_office/agendas___minutes.php"
PC_LIST = (BASE + "government/departments/community_development/"
           "planning_and_zoning/planning___zoning_commission.php")

EXCLUDE = ("agenda", "packet", "presentation", "notice", "ordinance", "resolution")
MINUTES_RE = re.compile(r"minut", re.I)

# separated date forms (legacy separator-less MDYYYY are all pre-floor, so they
# never pass the "> index max" gate and need no parser)
YMD_RE = re.compile(r"(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})")   # 2025.12.02 / 2025-12-02
MDY_RE = re.compile(r"(\d{1,2})[.\-](\d{1,2})[.\-](20\d{2})")   # 12-2-2025 / 12.2.2025
MDYY_RE = re.compile(r"(\d{1,2})[.\-](\d{1,2})[.\-](\d{2})(?!\d)")  # 3.12.25 / 6.24.26_Minutes


def _parse_date(name):
    for rx, order in ((YMD_RE, "ymd"), (MDY_RE, "mdy"), (MDYY_RE, "mdyy")):
        m = rx.search(name)
        if not m:
            continue
        if order == "ymd":
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        elif order == "mdy":
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3)) + 2000
        if 2000 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def _abs_url(href):
    return urllib.parse.urljoin(BASE, urllib.parse.quote(href, safe="/:?=&%"))


def _hrefs(page_url):
    page = rl.http_get(page_url, ua=rl.BROWSER_UA)
    return re.findall(r'href="([^"]+)"', page)


def _candidates(page_url, path_needle):
    """(date, basename, href) for every minutes-looking file whose decoded href
    contains `path_needle`."""
    out = []
    for href in _hrefs(page_url):
        dec = urllib.parse.unquote(href)
        if path_needle.lower() not in dec.lower():
            continue
        name = dec.split("/")[-1].split("?")[0]
        low = name.lower()
        if not MINUTES_RE.search(low) and "cc minutes" not in low:
            continue
        if any(x in low for x in EXCLUDE):
            continue
        date = _parse_date(name)
        if date:
            out.append((date, name, href))
    return out


def _council_kind(name):
    low = name.lower()
    if "truth" in low:
        return "City Council Truth In Taxation", "city-council-truth-in-taxation"
    if "budget" in low and "retreat" in low:
        return "City Council Budget Retreat", "city-council-budget-retreat"
    if "budget" in low:
        return "City Council Budget Meeting", "city-council-budget-meeting"
    if "legislative" in low or "breakfast" in low:
        return "City Council Legislative Breakfast", "city-council-legislative-breakfast"
    if "special" in low:
        return "City Council Special Meeting", "city-council-special-meeting"
    if "work" in low or "study" in low:
        return "City Council Work Meeting", "city-council-work-meeting"
    return "City Council Regular Meeting", "city-council-regular-meeting"


def probe_council(max_date):
    seen, new = set(), []
    # year-folder form and flat "CC Minutes" form both live off the same page
    for needle in ("Recorders Office", "Agendas & Minutes/CC Minutes"):
        for date, name, href in _candidates(COUNCIL_LIST, needle):
            if "planning" in urllib.parse.unquote(href).lower():
                continue
            if max_date and date <= max_date:
                continue
            title, slug = _council_kind(name)
            key = (date, slug)
            if key in seen:
                continue
            seen.add(key)
            new.append({"date": date, "title": title, "slug": slug,
                        "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": COUNCIL_LIST, "notes": ""}


def probe_pc(max_date):
    new, seen = [], set()
    for href in _hrefs(PC_LIST):
        dec = urllib.parse.unquote(href)
        name = dec.split("/")[-1].split("?")[0]
        low = name.lower()
        if "minute" not in low:                       # PC minutes files only
            continue
        if any(x in low for x in EXCLUDE):            # drop agenda/packet/notice/cancelled
            continue
        if "cc minutes" in low or "recorders office" in dec.lower():
            continue                                   # not a council file
        date = _parse_date(name)
        if not date or (max_date and date <= max_date):
            continue
        if date in seen:
            continue
        seen.add(date)
        slug = ("planning-commission-work-meeting" if "work" in low
                else "planning-commission-special-meeting" if "special" in low
                else "planning-commission-regular-meeting")
        # The page sets <base href="https://www.midvale.utah.gov/">, so both the
        # older full Document-Center paths and the recent BARE-RELATIVE root-level
        # minutes (e.g. '6.24.26_Minutes_Approved.pdf', served at site root)
        # resolve correctly via _abs_url. (NB: the build's stored source_url for
        # some recent bare-relative PC files points at a canonical Document-Center
        # path that 404s live — the working URL is the root-level one used here.)
        new.append({"date": date, "title": slug.replace("-", " ").title(),
                    "slug": slug, "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": PC_LIST,
            "notes": ("recent PC minutes are bare-relative root-level files served "
                      "at the site root")}


# ------------------------------------------------------------- conversion

def _ocr_pdf(path):
    tmp = tempfile.mkdtemp(prefix="mvocr_")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(path),
                        os.path.join(tmp, "pg")], capture_output=True, timeout=1200)
        out = []
        for png in sorted(glob.glob(os.path.join(tmp, "pg*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
        return "\n".join(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _get_text(raw_path):
    """Return (text, format) with format in {text, ocr}. Raises if unrecoverable."""
    if raw_path.suffix.lower() in (".docx", ".doc"):
        r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(raw_path)],
                           capture_output=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("textutil failed; convert manually")
        return r.stdout.decode("utf-8", "replace"), "text"
    txt = rl.pdf_to_text(raw_path)
    if len(re.sub(r"\s", "", txt)) >= 200:
        return txt, "text"
    otxt = _ocr_pdf(raw_path)
    if len(re.sub(r"\s", "", otxt)) < 50:
        raise RuntimeError("unrecoverable (corrupt/blank scan)")
    return otxt, "ocr"


def _body_name(dataset):
    return "Planning Commission" if dataset == "planning_commission" else "City Council"


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    body_name = _body_name(dataset)
    rows, n = [], 0
    for it in items:
        date, url, name, slug = it["date"], it["url"], it["file"], it["slug"]
        ext = Path(name.split("?")[0]).suffix.lower().lstrip(".") or "pdf"
        blob = rl.http_get(url, binary=True, ua=rl.BROWSER_UA, referer=BASE)
        raw_name = f"{date}_{slug}.{ext}"
        raw = rl.save_raw(ds_dir, raw_name, blob)
        try:
            text, fmt = _get_text(raw)
        except Exception as e:
            print(f"  RAW-ONLY {date} ({name}): {e}")
            continue
        rel = rl.minutes_rel_path(date, slug, "md", prefix="minutes")
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        hdr = (f"# {it['title']}\n> Body: {body_name}\n> Meeting date: {date}\n"
               f"> Source: {url}\n> Source vendor: revize\n> Raw file: raw/{raw_name}\n"
               f"> Format: {fmt}\n> Retrieved: {rl.today()}\n\n---\n\n")
        out.write_text(hdr + text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": slug, "path": rel, "source": "revize",
                     "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched [{fmt}] {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    "meeting_minutes": {
        "portal": "revize",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": probe_council,
        "fetch": lambda items: fetch("meeting_minutes", items),
        "post_fetch": lambda: post_fetch("meeting_minutes"),
    },
    "planning_commission": {
        "portal": "revize",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": probe_pc,
        "fetch": lambda items: fetch("planning_commission", items),
        "post_fetch": lambda: post_fetch("planning_commission"),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Midvale refresh (Revize Document Center)")
