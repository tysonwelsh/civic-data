#!/usr/bin/env python3
"""
Murray City incremental refresh — CivicPlus Archive Center (murray.utah.gov).

Datasets:
  meeting_minutes      City Council (regular/special/work/study) minutes  [AMID 31]
  planning_commission  Planning Commission minutes                        [AMID 33]

Portal pattern (recon.md / SOURCES.md, verified in production 2026-07-11):
  * List:  GET /Archive.aspx?AMID=<id>  -> HTML listing; each item is
           `href="Archive.aspx?ADID=<ADID>" ... <span>TITLE</span>`.
           TITLE carries a "<Month> <D>, <YYYY> ..." date we parse.
  * Doc:   GET /Archive/ViewFile/Item/<ADID>  -> a born-digital text PDF.
  * The Archive host serves a browser UA; refresh_lib.BROWSER_UA is used
    (mirrors meeting_minutes/fetch_minutes.py, which the build used live).

Conversion mirrors meeting_minutes/convert_minutes.py: pdftotext -layout, a
standard provenance header, filed under minutes/<year>/<week-monday>/<date>_<slug>.md,
source="civicplus", format="pdf-text".

Modes:
  --probe   (default) list meetings newer than each dataset's index max date;
            fetch nothing. Writes refresh_probe.json.
  --fetch   download new minutes PDFs -> <dataset>/raw/, convert -> markdown,
            append minutes_index.csv rows (+ fetch_log.csv), then run the
            dataset's extract_votes.py + validate_votes.py.

KNOWN GAPS (expected empty probes, NOT bugs): 2023 council minutes and all
post-2022-11 PC minutes moved off the Archive to a Tyler Minutes Management SPA,
so the Archive listing does not expose them. See VERIFICATION.md §(c).
"""

import csv
import datetime
import html
import re
import subprocess
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

BASE = "https://www.murray.utah.gov"
LIST_URL = BASE + "/Archive.aspx?AMID={amid}"
DOC_URL = BASE + "/Archive/ViewFile/Item/{adid}"

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

DATASET_CFG = {
    "meeting_minutes": {"amid": 31, "body": "council"},
    "planning_commission": {"amid": 33, "body": "pc"},
}

# --- Utah Public Notice (PMN) read-only cross-check ---------------------------
# Murray's 2023 council minutes (the Tyler-TMM gap) and its 2023-2026 Planning
# Commission minutes (the CivicPlus AMID=33 archive ends 2022-11-17) live ONLY on
# PMN — council body 735, PC body 983 (entity 213; seeded in
# pmn_backfill/pmn_bodies.csv). The CivicPlus Archive above remains the
# authoritative FETCH path; PMN is probed READ-ONLY and its findings surface in
# the probe NOTES (never fed to fetch()). Mirrors white_city's PMN cross-check.
PMN_BASE = "https://www.utah.gov"
PMN_BODY = {"meeting_minutes": "735", "planning_commission": "983"}
# page=300 returns the full cumulative notice history for these low-volume bodies
PMN_NOTICES = PMN_BASE + "/pmn/list/notices.html?id={body}&page=300"

# The four 2026 PC dates that were agenda-only at the 2026-07-13 promotion wave
# (pmn_backfill/coverage.md). Re-probed read-only every refresh so a late-posted
# minutes doc surfaces as a recovery LEAD (not auto-ingested). 2026-02-05 was
# subsequently ruled a NOTICE OF CANCELLATION (pmn_backfill/pmn_exceptions.csv),
# so a persistent agenda-only/cancelled status there is the expected outcome.
PMN_PC_AGENDA_ONLY_WATCH = ["2026-02-05", "2026-05-21", "2026-06-18", "2026-07-02"]

_RE_PMN_ROW = re.compile(
    r'<tr class="(?:on|off)">\s*<td>\s*'
    r'<a href="/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>\s*</td>\s*'
    r'<td>(\d{4}/\d{2}/\d{2})[^<]*</td>\s*<td>(.*?)</td>\s*</tr>', re.S)
_RE_PMN_ATT = re.compile(
    r'<a href="(/pmn/files/[^"]+)"[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\(([^)]+)\)', re.S)
_RE_PMN_CANCEL = re.compile(r'cancel|postpone|reschedul', re.I)
_RE_PMN_MIN_LABEL = re.compile(r'meeting minutes', re.I)
_RE_PMN_MIN_FNAME = re.compile(r'minutes?\b', re.I)


def _pmn_fname_dates(fname):
    """ISO dates printed inside a PMN minutes FILENAME (minutes ride the NEXT
    meeting's notice, so the filename date is the true meeting date). Handles
    murray's 'September 16, 2025 …minutes.pdf' + '2026.02.05 …Minutes.pdf' forms."""
    out = []
    for m in re.finditer(
            r'(January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+(\d{1,2}),?\s+(20\d{2})', fname, re.I):
        try:
            out.append(datetime.date(int(m.group(3)), MONTHS[m.group(1).title()],
                                     int(m.group(2))).isoformat())
        except (ValueError, KeyError):
            pass
    for m in re.finditer(r'(20\d{2})[.\-_](\d{1,2})[.\-_](\d{1,2})', fname):
        try:
            out.append(datetime.date(int(m.group(1)), int(m.group(2)),
                                     int(m.group(3))).isoformat())
        except ValueError:
            pass
    for m in re.finditer(r'\b(\d{1,2})[.\-_](\d{1,2})[.\-_](20\d{2})\b', fname):
        try:
            out.append(datetime.date(int(m.group(3)), int(m.group(1)),
                                     int(m.group(2))).isoformat())
        except ValueError:
            pass
    return out


def _pmn_minutes_index(body):
    """READ-ONLY crawl of PMN body <body>'s cumulative notice list. Returns
    (minutes_dates, cancelled_dates): meeting dates that carry a Meeting-Minutes
    attachment (keyed by filename date, falling back to the notice event date),
    and event dates whose notice/attachment says cancelled/postponed."""
    listing = rl.http_get(PMN_NOTICES.format(body=body), ua=rl.BROWSER_UA)
    minutes_dates, cancelled = set(), set()
    for _nid, title, d, att in _RE_PMN_ROW.findall(listing):
        ev = d.replace("/", "-")
        if _RE_PMN_CANCEL.search(title):
            cancelled.add(ev)
        for _href, fname, label in _RE_PMN_ATT.findall(att):
            if _RE_PMN_CANCEL.search(fname):
                cancelled.add(ev)
                continue
            if _RE_PMN_MIN_LABEL.search(label) or _RE_PMN_MIN_FNAME.search(fname):
                minutes_dates.update(_pmn_fname_dates(fname) or [ev])
    return minutes_dates, cancelled


def _unrecovered_dates(dataset):
    p = CITY_DIR / dataset / "minutes_unrecovered.csv"
    out = set()
    if p.exists():
        with open(p, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("date"):
                    out.add(r["date"].strip())
    return out


def _pmn_config(body):
    """(floor ISO, {exception dates}) for a PMN body from pmn_backfill/ — the same
    per-city config the authoritative scripts/pmn_crosscheck.py reads, so this
    cross-check honors the data floor and the verified false-positive ledger and
    does NOT re-surface out-of-scope / pre-floor / cancelled dates."""
    pb = CITY_DIR / "pmn_backfill"
    floor = ""
    bf = pb / "pmn_bodies.csv"
    if bf.exists():
        with open(bf, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if (r.get("body_id") or "") == body:
                    floor = (r.get("floor") or "").strip()
    exc = set()
    ef = pb / "pmn_exceptions.csv"
    if ef.exists():
        with open(ef, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if (r.get("body_id") or "") == body and r.get("date"):
                    exc.add(r["date"].strip())
    return floor, exc


def pmn_note(dataset):
    """Read-only PMN cross-check string for the probe notes. Never fetches docs.
    Honors the data floor + exception ledger; the AUTHORITATIVE minutes-gap diff
    (filename-date rescue, cancellation detection) is scripts/pmn_crosscheck.py."""
    body = PMN_BODY[dataset]
    indexed = {r["date"] for r in rl.load_index(CITY_DIR / dataset) if r.get("date")}
    unrec = _unrecovered_dates(dataset)
    floor, exc = _pmn_config(body)
    try:
        mdates, cancelled = _pmn_minutes_index(body)
    except Exception as e:  # noqa: BLE001
        return f"PMN body {body} cross-check skipped ({type(e).__name__}: {e})"
    today = datetime.date.today().isoformat()
    fresh = sorted(d for d in mdates
                   if (not floor or d >= floor) and d not in indexed
                   and d not in unrec and d not in exc and d <= today)
    shown = ", ".join(fresh[:12]) + (f" (+{len(fresh) - 12} more)" if len(fresh) > 12 else "")
    parts = [f"PMN body {body} (floor {floor or 'none'}): {len(fresh)} minutes-bearing "
             f"date(s) >= floor not in index/unrecovered/exceptions"
             + (f" ({shown}) — raw candidate LEAD(s), NOT ingested; verify against "
                f"scripts/pmn_crosscheck.py (authoritative diff)" if fresh
                else "; CivicPlus Archive is the authoritative fetch source")]
    if dataset == "planning_commission":
        watch = []
        for d in PMN_PC_AGENDA_ONLY_WATCH:
            if d in indexed:
                st = "MINUTES NOW INDEXED"
            elif d in mdates:
                st = "MINUTES NOW POSTED ON PMN (recovery lead — not ingested)"
            elif d in cancelled:
                st = "cancelled notice (no minutes expected)"
            else:
                st = "still agenda-only"
            watch.append(f"{d}={st}")
        parts.append("2026 agenda-only PC watch: " + "; ".join(watch))
    return " | ".join(parts)


def parse_date(title):
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(20\d{2})", title)
    if not m or m.group(1) not in MONTHS:
        return None
    try:
        return datetime.date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    except ValueError:
        return None


def slugify(title, body):
    """Match meeting_minutes/convert_minutes.py slug convention."""
    t = title.lower()
    base = "planning-commission" if body == "pc" else "city-council"
    if "work" in t:
        kind = "work-session"
    elif "study" in t:
        kind = "study-session"
    elif "special" in t:
        kind = "special-meeting"
    elif "canvass" in t:
        kind = "canvass"
    else:
        kind = "meeting"
    return f"{base}-{kind}"


def enumerate_listing(amid):
    """(adid, title, date) for every dated item on the AMID Archive page."""
    listing = rl.http_get(LIST_URL.format(amid=amid), ua=rl.BROWSER_UA)
    items, seen = [], set()
    for adid, raw_title in re.findall(
            r'href="Archive\.aspx\?ADID=(\d+)"[^>]*>\s*<span>(.*?)</span>',
            listing, re.S):
        if adid in seen:
            continue
        seen.add(adid)
        title = html.unescape(re.sub(r"\s+", " ", raw_title)).strip()
        dt = parse_date(title)
        if dt:
            items.append((adid, title, dt))
    return items


def list_new(dataset, max_date):
    cfg = DATASET_CFG[dataset]
    endpoint = LIST_URL.format(amid=cfg["amid"])
    floor = datetime.date(2020, 1, 1)
    new = []
    cp_note = ""
    try:
        listing = enumerate_listing(cfg["amid"])
    except Exception as e:  # noqa: BLE001
        # The CivicPlus Archive host was HTTP-500 site-wide on 2026-07-19 (platform
        # outage, not link rot). Keep going so the PMN cross-check + agenda-only
        # watch still report — never mark anything dead on a transient portal 500.
        listing = []
        cp_note = (f"CivicPlus Archive UNREACHABLE ({type(e).__name__}: {e}) — treat as "
                   f"a transient portal outage (murray was HTTP-500 site-wide 2026-07-19), "
                   f"not link rot; the PMN cross-check below still ran")
    for adid, title, dt in listing:
        if dt < floor:
            continue
        iso = dt.isoformat()
        if max_date and iso <= max_date:
            continue
        new.append({"date": iso, "title": title,
                    "url": DOC_URL.format(adid=adid), "adid": adid})
    new.sort(key=lambda x: x["date"])
    notes = ("2023 council + post-2022 PC minutes live on a Tyler Minutes "
             "Management SPA, not this Archive — an empty result there is expected.")
    if cp_note:
        notes = cp_note + " | " + notes
    # read-only PMN cross-check (bodies 735 council / 983 PC) — NOTES only
    notes += " | " + pmn_note(dataset)
    return {"new_items": new, "endpoint": endpoint, "notes": notes}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    body = DATASET_CFG[dataset]["body"]
    rows, n = [], 0
    for it in items:
        date, url, adid = it["date"], it["url"], it["adid"]
        pdf = rl.http_get(url, binary=True, ua=rl.BROWSER_UA)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        slug = slugify(it["title"], body)
        raw = rl.save_raw(ds_dir, f"{date}_{slug}_adid{adid}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, slug, "md", prefix="minutes")
        out = ds_dir / rel
        if out.exists():  # date+slug collision with an already-indexed doc
            rel = rl.minutes_rel_path(date, f"{slug}-adid{adid}", "md", prefix="minutes")
            out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        title = re.sub(r"\s+", " ", it["title"]).strip()
        hdr = (f"# {title}\n"
               f"> Source: {url}\n"
               f"> Meeting date: {date}\n"
               f"> Format: pdf-text (CivicPlus Archive, born-digital)\n\n---\n\n")
        out.write_text(hdr + text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": title,
                     "slug": slug, "path": rel, "source": "civicplus",
                     "source_url": url, "format": "pdf-text"})
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
        "portal": "civicplus-archive",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: list_new(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Murray City refresh (CivicPlus Archive Center)")
