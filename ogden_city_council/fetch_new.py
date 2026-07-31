#!/usr/bin/env python3
"""
Ogden incremental refresh — CivicPlus, two listing surfaces.

Datasets:
  meeting_minutes      Council + RDA + MBA (+ special/canvass) minutes, from the
                       DocumentCenter "Approved Minutes" hub:
                       https://www.ogdencity.gov/2698/Approved-Minutes-for-City-Council-Redeve
                       2024+ meetings are per-meeting PDFs at
                       /DocumentCenter/View/<ID>/<MM-DD-YY>-<SUFFIX>
                       (suffix = body: CC, WS, JWS, RDA, MBA, BOC, FT, SS,
                       SPECIAL, SP-RDA; "Packet" links are agenda packets, NOT
                       minutes — excluded). Pre-2024 rows are annual
                       compilation PDFs (CC-2020 … CC-2023) — irrelevant for
                       forward refresh.
  planning_commission  PC minutes from the AgendaCenter:
                       /AgendaCenter/ViewFile/Minutes/_MMDDYYYY-<id>, enumerated
                       via /AgendaCenter/Search/?...&startDate=&endDate=
                       (results grouped under bare "<h2>Planning Commission</h2>"
                       headers — no " Agendas" suffix, unlike Nephi's portal).

UA note: ogdencity.gov 404s non-browser User-Agents (established in the Phase
2.8 liveness pass), so every request here sends rl.BROWSER_UA. Requests remain
throttled >= 1s via refresh_lib.

OCR caveat (planning_commission --fetch): Ogden PC minutes are SCANNED
(`format=ocr`; the historical pipeline re-rendered at 300 dpi + tesseract 5.5 —
see VERIFICATION.md "Remediation 2"). fetch() retains the raw PDF always, and
only writes a .md if pdftotext finds a usable embedded text layer; otherwise it
prints a loud instruction to OCR manually rather than ingesting garbage.
Any .md it does write should be spot-checked against the raw PDF.

Modes:
  --probe   (default) list minutes newer than the index max date; fetch nothing
  --fetch   download new PDFs -> <dataset>/raw/, convert, append index rows
            (+ fetch_log.csv retrieved_date), run extract_votes.py +
            validate_votes.py.

Probe verified live 2026-07-02 (HTTP 200, both datasets). Cross-check: the
AgendaCenter's own City Council category is sparse/stale — the DocumentCenter
hub is the authoritative council-minutes surface (recon.md §1).
"""

import datetime
import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://www.ogdencity.gov"
HUB = HOST + "/2698/Approved-Minutes-for-City-Council-Redeve"
SEARCH = (HOST + "/AgendaCenter/Search/?term=&CIDs=all"
          "&startDate={start}&endDate={end}")

# DocumentCenter suffix -> (title, slug); matches the bodies already in the index.
SUFFIX_MAP = {
    "CC": ("City Council Meeting", "city-council-meeting"),
    "WS": ("City Council Work Session", "city-council-work-session"),
    "JWS": ("City Council Joint Work Session", "city-council-joint-work-session"),
    "RDA": ("Redevelopment Agency Meeting", "redevelopment-agency"),
    "SP-RDA": ("Redevelopment Agency Special Meeting", "redevelopment-agency-special"),
    "MBA": ("Municipal Building Authority Meeting", "municipal-building-authority"),
    "BOC": ("Board of Canvassers", "board-of-canvassers"),
    "FT": ("City Council Field Trip", "city-council-field-trip"),
    "SS": ("City Council Special Session", "city-council-special-session"),
    "SPECIAL": ("City Council Special Meeting", "city-council-special-meeting"),
}
DOC_LINK_RE = re.compile(r'href="(?:https?://www\.ogdencity\.(?:gov|com))?'
                         r'(/DocumentCenter/View/\d+/(\d{2})-(\d{2})-(\d{2})-([A-Za-z-]+))"')
PC_MINUTES_RE = re.compile(
    r'href="(/AgendaCenter/ViewFile/Minutes/_(\d{8})-\d+)"', re.I)


def _norm_suffix(s):
    """'cc' -> 'CC'; strip clerk decorations like 'CC---APPROVED', 'WS-DRAFT'."""
    s = s.upper().strip("-")
    s = re.sub(r"-*(APPROVED|DRAFT|MINUTES|CORRECTED|REG)(-|$).*", "", s).strip("-")
    return s


def probe_mm(max_date):
    html = rl.http_get(HUB, ua=rl.BROWSER_UA)
    seen, new, unknown = set(), [], set()
    for m in DOC_LINK_RE.finditer(html):
        path, mm, dd, yy, rawsuf = m.groups()
        suf = _norm_suffix(rawsuf)
        if suf in ("PACKET", ""):
            continue
        date = f"20{yy}-{mm}-{dd}"
        if max_date and date <= max_date:
            continue
        if suf not in SUFFIX_MAP:
            unknown.add(f"{date}-{rawsuf}")
            continue
        key = (date, suf)
        if key in seen:
            continue
        seen.add(key)
        new.append({"date": date, "title": SUFFIX_MAP[suf][0], "url": HOST + path,
                    "suffix": suf})
    new.sort(key=lambda x: x["date"])
    notes = ("council minutes typically post ~4-6 weeks after the meeting; "
             "the hub is the authoritative surface (AgendaCenter CC category is stale)")
    if unknown:
        notes += f"; UNRECOGNIZED suffixes skipped: {sorted(unknown)}"
    return {"new_items": new, "endpoint": HUB, "notes": notes}


def probe_pc(max_date):
    start_d = (datetime.date.fromisoformat(max_date) + datetime.timedelta(days=1)
               if max_date else datetime.date(2020, 1, 1))
    endpoint = SEARCH.format(start=start_d.strftime("%m/%d/%Y"),
                             end=datetime.date.today().strftime("%m/%d/%Y"))
    html = rl.http_get(endpoint, ua=rl.BROWSER_UA)
    parts = re.split(r"<h2[^>]*>\s*(.*?)\s*</h2>", html)
    new = []
    for i in range(1, len(parts) - 1, 2):
        if parts[i].strip() != "Planning Commission":
            continue
        for m in PC_MINUTES_RE.finditer(parts[i + 1]):
            href, mmddyyyy = m.groups()
            date = f"{mmddyyyy[4:]}-{mmddyyyy[:2]}-{mmddyyyy[2:4]}"
            if date > (max_date or ""):
                new.append({"date": date, "title": "Planning Commission",
                            "url": HOST + href})
    new.sort(key=lambda x: x["date"])
    return {"new_items": new, "endpoint": endpoint,
            "notes": "PC minutes are scanned (format=ocr) — see OCR caveat in header"}


def fetch_mm(items):
    ds_dir = CITY_DIR / "meeting_minutes"
    rows, n = [], 0
    for it in items:
        date, suf = it["date"], it["suffix"]
        title, slug = SUFFIX_MAP[suf]
        pdf = rl.http_get(it["url"], binary=True, ua=rl.BROWSER_UA)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}-{suf}: not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{slug}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, slug, "md", prefix="meeting_minutes/minutes")
        out = CITY_DIR / rel
        if out.exists():
            print(f"  SKIP {date}: {rel} already exists")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": title, "slug": slug,
                     "path": rel, "source": "civicplus", "source_url": it["url"],
                     "format": "per-meeting", "from_compilation": "N"})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def fetch_pc(items):
    ds_dir = CITY_DIR / "planning_commission"
    slug = "planning-commission-meeting"
    rows, n, needs_ocr = [], 0, []
    for it in items:
        date = it["date"]
        pdf = rl.http_get(it["url"], binary=True, ua=rl.BROWSER_UA)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{slug}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        # scanned docs yield a near-empty text layer -> require OCR, don't fake it
        if len(re.sub(r"\s", "", text)) < 500:
            needs_ocr.append(str(raw))
            continue
        rel = rl.minutes_rel_path(date, slug, "md", prefix="planning_commission/minutes")
        out = CITY_DIR / rel
        if out.exists():
            print(f"  SKIP {date}: {rel} already exists")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": "Planning Commission",
                     "slug": slug, "path": rel, "source": "civicplus",
                     "source_url": it["url"], "format": "ocr"})
        n += 1
        print(f"  fetched {rel} (embedded text layer — spot-check vs raw PDF)")
    rl.append_index_rows(ds_dir, rows)
    if needs_ocr:
        print("\n" + "!" * 70)
        print("OCR REQUIRED — these scanned PDFs have no usable text layer.")
        print("Raw files retained; NOT converted, NOT indexed. Re-render at 300 dpi")
        print("+ tesseract 5.5 (see VERIFICATION.md 'Remediation 2'), then add the")
        print(".md + index row manually:")
        for p in needs_ocr:
            print(f"  {p}")
        print("!" * 70)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    "meeting_minutes": {
        "portal": "civicplus-documentcenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": probe_mm,
        "fetch": fetch_mm,
        "post_fetch": lambda: post_fetch("meeting_minutes"),
    },
    "planning_commission": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": probe_pc,
        "fetch": fetch_pc,
        "post_fetch": lambda: post_fetch("planning_commission"),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Ogden refresh (CivicPlus DocumentCenter + AgendaCenter)")
