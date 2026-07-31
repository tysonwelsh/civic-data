#!/usr/bin/env python3
"""
St George incremental refresh — Revize CMS (static files, NO API; sgcityutah.gov).

Datasets:
  meeting_minutes      City Council (Regular / Work / Special / joint) minutes
  planning_commission  Planning Commission minutes

Portal pattern (recon.md §1; both listing pages verified live 2026-07-02):
  * Council listing: /government/city_council/agendas_and_minutes.php — one
    HTML page (~2 MB) listing Agendas / Agenda Packets / Minutes / Notices /
    Recordings. Current minutes live under
    "Documents/Government/City Council/Agendas And Minutes/<YEAR>/Minutes/"
    named "YYYY.MM.DD  Minutes <type>.pdf" (occasionally .docx/.doc, plus
    typo'd names like "Work Meeting Minues.doc" — matched loosely).
  * PC listing: /departments/community_development/planning_commission.php —
    PC minutes are mostly SITE-ROOT-LEVEL files ("PC Minutes MM.DD.YYYY.pdf",
    "PC Minutes M.D.YY.pdf", "PC  YYYY.MM.DD Minutes.pdf",
    "YYYY.MM.DD  Minutes Joint PC CC Meeting.pdf") plus some under
    "Documents/Agendas and Minutes/Planning Commission/<YEAR>/".
  * Both pages carry <base href="https://sgcityutah.gov/">; hrefs are
    root-relative with a ?t=<cachetoken> querystring supplied by the page.
  * Fallback (not scripted): Utah Public Notice (utah.gov/pmn) public bodies
    241/242 mirror council minutes — the documented source for pre-2022.

Notes:
  * meeting_minutes/minutes_unrecovered.csv records the one known
    irrecoverable meeting (2025-10-09 work) — leave it alone.
  * --fetch converts PDFs with pdftotext -layout; .docx/.doc files are
    retained in raw/ and converted via macOS `textutil` if available,
    otherwise flagged for manual conversion (the corpus has 8 docx rows).

Modes:
  --probe   (default) list minutes newer than the index max date; fetch nothing
  --fetch   download new docs -> <dataset>/raw/, convert -> .md, append
            minutes_index.csv rows (+ fetch_log.csv retrieved_date), then run
            extract_votes.py + validate_votes.py.

Probe verified live 2026-07-02 (both datasets, HTTP 200).
"""

import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

BASE = "https://sgcityutah.gov/"
COUNCIL_LIST = BASE + "government/city_council/agendas_and_minutes.php"
PC_LIST = BASE + "departments/community_development/planning_commission.php"

EXCLUDE = ("agenda", "packet", "notice", "recording", "resolution", "ordinance")
# "Minutes" with observed clerk typos ("Minues", "Minutess").
MINUTES_RE = re.compile(r"minu\w{1,4}s", re.I)
YMD_RE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
MDY_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
MDYY_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2})\b")


def _abs_url(href):
    return urllib.parse.urljoin(BASE, urllib.parse.quote(href, safe="/:?=&%"))


def _hrefs(page_url):
    html = rl.http_get(page_url)
    return re.findall(r'href="([^"]+)"', html)


def _parse_date(name):
    m = YMD_RE.search(name)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = MDY_RE.search(name)
        if m:
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            m = MDYY_RE.search(name)
            if not m:
                return None
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3)) + 2000
    if not (2000 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _minutes_candidates(page_url):
    """(date, basename, href) for every minutes-looking file on the page."""
    out = []
    for href in _hrefs(page_url):
        dec = urllib.parse.unquote(href)
        name = dec.split("/")[-1].split("?")[0]
        low = name.lower()
        if not MINUTES_RE.search(low):
            continue
        if any(x in low for x in EXCLUDE):
            continue
        date = _parse_date(name)
        if date:
            out.append((date, name, href))
    return out


def _council_kind(name):
    low = name.lower()
    if "joint" in low or re.search(r"\bpc\b|pc\.cc", low):
        return "City Council Planning Commission Meeting", "city-council-planning-commission-meeting"
    if "rda" in low:
        return "Rda City Council Meeting", "rda-city-council-meeting"
    if "work" in low:
        return "City Council Work Meeting", "city-council-work-meeting"
    if "special" in low:
        return "City Council Special Meeting", "city-council-special-meeting"
    return "City Council Regular Meeting", "city-council-regular-meeting"


def probe_council(max_date):
    new = []
    for date, name, href in _minutes_candidates(COUNCIL_LIST):
        dec = urllib.parse.unquote(href)
        # council-side files only: the CC Minutes folders, or root-level
        # legacy links that aren't PC-titled
        in_cc = "/city council/" in dec.lower()
        rootlevel = "/" not in dec.split("?")[0]
        if not (in_cc or rootlevel):
            continue
        if rootlevel and name.lower().startswith("pc"):
            continue
        if max_date and date <= max_date:
            continue
        title, slug = _council_kind(name)
        new.append({"date": date, "title": title, "slug": slug,
                    "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": COUNCIL_LIST, "notes": ""}


def probe_pc(max_date):
    new = []
    for date, name, href in _minutes_candidates(PC_LIST):
        dec = urllib.parse.unquote(href)
        low = f"{dec.lower()} {name.lower()}"
        if not ("pc" in re.findall(r"[a-z]+", low) or "planning commission" in low):
            continue
        if "/city council/" in dec.lower():
            continue
        if max_date and date <= max_date:
            continue
        slug = ("planning-commission-joint-meeting" if "joint" in low
                else "planning-commission-work-meeting" if "work" in low
                else "planning-commission-meeting")
        new.append({"date": date, "title": "Planning Commission", "slug": slug,
                    "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": PC_LIST, "notes": ""}


def _to_text(raw_path):
    if raw_path.suffix.lower() == ".pdf":
        return rl.pdf_to_text(raw_path)
    # .docx/.doc — macOS textutil, if present
    r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(raw_path)],
                       capture_output=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"textutil failed on {raw_path.name}; convert manually")
    return r.stdout.decode("utf-8", "replace")


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    rows, n = [], 0
    for it in items:
        date, url, name = it["date"], it["url"], it["file"]
        ext = Path(name.split("?")[0]).suffix.lower().lstrip(".") or "pdf"
        blob = rl.http_get(url, binary=True)
        raw = rl.save_raw(ds_dir, f"{date}_{it['slug']}.{ext}", blob)
        try:
            text = _to_text(raw)
        except Exception as e:
            print(f"  RAW-ONLY {date} ({name}): {e}")
            continue
        rel = rl.minutes_rel_path(date, it["slug"], "md", prefix=f"{dataset}/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        fmt = ("text" if dataset == "planning_commission"
               else ("docx" if ext in ("docx", "doc") else "pdf"))
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": it["slug"], "path": rel, "source": "revize",
                     "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched {rel}")
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
    rl.run_cli(CITY_DIR, DATASETS, "St George refresh (Revize static CMS)")
