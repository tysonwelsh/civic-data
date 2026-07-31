#!/usr/bin/env python3
"""
Logan incremental refresh — Revize CMS (static files, NO API; loganutah.gov).

Datasets:
  meeting_minutes      Logan Municipal Council (+ RDA, published in the same
                       council PDFs) minutes
  planning_commission  Planning Commission minutes

Portal pattern (recon.md §1; both listing pages verified live 2026-07-02):
  * Council listing: /government/city_council/minutes.php — one HTML page,
    minutes by year. Files are human-typed names under
    departments/admin/council/ (e.g. "26June02.pdf", "25August7 Truth In
    Taxation.pdf", "DRAFT Minutes 23January3.pdf") with a ?t=<cachetoken>
    querystring supplied by the page. Date is parsed from the
    <YY|YYYY><MonthName><D> token in the filename.
  * PC listing: /government/departments/community_development/
    planning_commission/minutes.php — files under
    departments/comdev/PC Minutes/ named "PC Minutes M.D.YY[ DRAFT][.N].pdf".
  * Both pages carry <base href="https://www.loganutah.gov/">, so hrefs are
    site-root-relative. Files also mirror on cms9files.revize.com/loganut/.
  * Fallback (not scripted): Utah Public Notice, council notices carry draft
    minutes as /pmn/files/<id>.pdf (see recon.md).

CAVEAT for --fetch (council): one council PDF often contains the Council
minutes AND a trailing Logan Redevelopment Agency section. The historical
corpus was split into separate council/RDA .md files by a script that is NOT
in the repo (VERIFICATION.md, Phase 1.7). This fetcher writes ONE .md per new
PDF (as a council meeting) — review each new file for an RDA tail and split
it manually (copy the existing convention: same date, slug
redevelopment-agency-meeting) before extracting votes.

Modes:
  --probe   (default) list minutes newer than the index max date; fetch nothing
  --fetch   download new PDFs -> <dataset>/raw/, pdftotext -layout -> .md,
            append minutes_index.csv rows (+ fetch_log.csv retrieved_date),
            then run the dataset's extract_votes.py + validate_votes.py.

Probe verified live 2026-07-02 (both datasets, HTTP 200).
"""

import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

BASE = "https://www.loganutah.gov/"
COUNCIL_LIST = BASE + "government/city_council/minutes.php"
PC_LIST = (BASE + "government/departments/community_development/"
           "planning_commission/minutes.php")

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

# Non-minutes files that share the listing pages.
EXCLUDE = ("agenda", "packet", "cancelled", "notice", "application", "guide")

COUNCIL_DATE_RE = re.compile(r"(\d{2}|\d{4})\s*([A-Za-z]+)\s*(\d{1,2})")
PC_DATE_RE = re.compile(r"PC[ _]*Minutes[ _]*(\d{1,2})\.(\d{1,2})\.(\d{2,4})", re.I)


def _abs_url(href):
    return urllib.parse.urljoin(BASE, urllib.parse.quote(href, safe="/:?=&%"))


def _pdf_hrefs(page_url):
    html = rl.http_get(page_url)
    return re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)


def _council_date(basename):
    for m in COUNCIL_DATE_RE.finditer(basename):
        yr, mon, day = m.group(1), m.group(2).lower(), int(m.group(3))
        if mon in MONTHS:
            y = int(yr) + (2000 if len(yr) == 2 else 0)
            try:
                return f"{y:04d}-{MONTHS[mon]:02d}-{day:02d}"
            except ValueError:
                return None
    return None


def probe_council(max_date):
    new = []
    for href in _pdf_hrefs(COUNCIL_LIST):
        name = urllib.parse.unquote(href.split("/")[-1].split("?")[0])
        if any(x in name.lower() for x in EXCLUDE):
            continue
        date = _council_date(name)
        if not date or (max_date and date <= max_date):
            continue
        title = "Logan City Council Meeting" + (" (DRAFT)" if "draft" in name.lower() else "")
        new.append({"date": date, "title": title, "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: x["date"])
    return {"new_items": new, "endpoint": COUNCIL_LIST,
            "notes": "council PDFs may embed an RDA section — split manually (see header)"}


def probe_pc(max_date):
    new = []
    for href in _pdf_hrefs(PC_LIST):
        if "pc minutes/" not in urllib.parse.unquote(href).lower():
            continue
        name = urllib.parse.unquote(href.split("/")[-1].split("?")[0])
        m = PC_DATE_RE.search(name)
        if not m:
            continue
        mo, day, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = yr + 2000 if yr < 100 else yr
        try:
            date = f"{y:04d}-{mo:02d}-{day:02d}"
        except ValueError:
            continue
        if max_date and date <= max_date:
            continue
        title = "Planning Commission" + (" (DRAFT)" if "draft" in name.lower() else "")
        new.append({"date": date, "title": title, "url": _abs_url(href), "file": name})
    new.sort(key=lambda x: x["date"])
    return {"new_items": new, "endpoint": PC_LIST, "notes": ""}


DATASET_CFG = {
    "meeting_minutes": {"probe": probe_council, "slug": "city-council-meeting",
                        "title": "Logan City Council Meeting"},
    "planning_commission": {"probe": probe_pc, "slug": "planning-commission-meeting",
                            "title": "Planning Commission"},
}


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    cfg = DATASET_CFG[dataset]
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{cfg['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, cfg["slug"], "md", prefix=f"{dataset}/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        fmt = "text-draft" if "DRAFT" in (it.get("title") or "") else "text"
        rows.append({"date": date, "year": date[:4], "title": cfg["title"],
                     "slug": cfg["slug"], "path": rel, "source": "revize",
                     "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    if dataset == "meeting_minutes" and n:
        print("  NOTE: review new council .md files for an RDA tail (see script header).")
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    name: {
        "portal": "revize",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: DATASET_CFG[d]["probe"](mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in DATASET_CFG
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Logan refresh (Revize static CMS)")
