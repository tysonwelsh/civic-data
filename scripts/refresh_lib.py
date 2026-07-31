#!/usr/bin/env python3
"""
refresh_lib — shared plumbing for the per-city incremental-refresh scripts
(`<city>_city_council/fetch_new.py`). Stdlib-only.

Each city's fetch_new.py is vendor-specific (PrimeGov / Granicus / Legistar /
CivicClerk / CivicPlus-AgendaCenter / OnBase / Revize / slcdocs), but they all
share this structure, provided here:

  * read the refresh baseline: max(date) in <dataset>/minutes_index.csv
  * polite throttled HTTP (>= 1s between requests, research-tool User-Agent)
  * probe/fetch CLI (`--probe` is the default and fetches NOTHING;
    `--fetch` downloads new docs, converts, appends index rows, runs the
    city's extract_votes.py + validate_votes.py, then reminds about db/weeks)
  * raw retention: every fetched original is kept under <dataset>/raw/
  * provenance: index rows appended with source_url; retrieved_date recorded
    in <dataset>/fetch_log.csv (the standard index schema has no
    retrieved_date column — the log carries it, one row per fetched doc)
  * machine-readable probe results in <city>/refresh_probe.json, which
    scripts/refresh_status.py aggregates into the repo-root refresh_status.md.

Vendor scripts implement, per dataset, a `probe()` returning
    {"new_items": [ {date,title,url, ...}, ... ],   # meetings newer than index max
     "endpoint": "<listing URL actually hit>",
     "notes": "free text"}
and optionally a `fetch(new_items)` that lands files + index rows. probe()
must be strictly read-only on both sides (listing GETs only, no downloads).
"""

import argparse
import csv
import datetime
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- HTTP layer

# Default UA: identifies this as a research tool (with contact), in the
# Mozilla-compatible form most municipal CDNs accept.
RESEARCH_UA = ("Mozilla/5.0 (compatible; civic-data-refresh/1.0; "
               "municipal-records research tool; contact tysonwelsh@gmail.com)")
# Some portals (e.g. ogdencity.gov, Granicus DocumentViewer) 404/403 any
# non-browser UA. City scripts may pass ua=BROWSER_UA — document why in the
# script header when you do.
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

THROTTLE_SECONDS = 1.0
_last_request = [0.0]


def _throttle():
    wait = THROTTLE_SECONDS - (time.monotonic() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    _last_request[0] = time.monotonic()


def http_get(url, binary=False, timeout=60, ua=None, referer=None, headers=None,
             method="GET", data=None):
    """Throttled GET (>=1s between any two requests, process-wide)."""
    _throttle()
    hdrs = {"User-Agent": ua or RESEARCH_UA}
    if referer:
        hdrs["Referer"] = referer
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs, method=method, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        if binary:
            return body
        return body.decode("utf-8", "replace")


def http_get_json(url, **kw):
    return json.loads(http_get(url, **kw))


# ---------------------------------------------------------------- index layer

INDEX_COLS = ["date", "year", "title", "slug", "path", "source", "source_url", "format"]


def load_index(dataset_dir):
    """Rows of <dataset>/minutes_index.csv (list of dicts; [] if absent)."""
    idx = Path(dataset_dir) / "minutes_index.csv"
    if not idx.exists():
        return []
    with open(idx, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def index_max_date(dataset_dir, date_col="date"):
    """(max ISO date, row count) from minutes_index.csv. (None, 0) if absent."""
    rows = load_index(dataset_dir)
    dates = sorted(r[date_col] for r in rows if r.get(date_col))
    return (dates[-1] if dates else None), len(rows)


def csv_max_date(csv_path, date_col="date"):
    """Fallback baseline for datasets without a minutes_index (e.g. sandy PC:
    Legistar-API-built all_votes.csv)."""
    p = Path(csv_path)
    if not p.exists():
        return None, 0
    with open(p, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    dates = sorted(r[date_col] for r in rows if r.get(date_col))
    return (dates[-1] if dates else None), len(rows)


def append_index_rows(dataset_dir, new_rows):
    """Append rows to minutes_index.csv, preserving that file's own header
    (cities with extra columns keep them; missing keys become \"\"), then
    rewrite sorted by (date, slug). Also logs retrieved_date provenance to
    <dataset>/fetch_log.csv."""
    dataset_dir = Path(dataset_dir)
    idx = dataset_dir / "minutes_index.csv"
    if idx.exists():
        with open(idx, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            cols = reader.fieldnames
            rows = list(reader)
    else:
        cols, rows = list(INDEX_COLS), []
    existing_paths = {r.get("path") for r in rows}
    added = []
    for r in new_rows:
        if r.get("path") in existing_paths:
            continue
        # add the new path to the seen-set IMMEDIATELY so a portal listing that
        # links the same document twice cannot create a duplicate index row (which
        # would make extract_votes.py process the file twice and double every vote
        # — the st_george 2026-06-18 case, Q3-2026 refresh)
        existing_paths.add(r.get("path"))
        rows.append({c: r.get(c, "") for c in cols})
        added.append(r)
    rows.sort(key=lambda r: (r.get("date", ""), r.get("slug", "")))
    with open(idx, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    if added:
        log = dataset_dir / "fetch_log.csv"
        new_log = not log.exists()
        with open(log, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new_log:
                w.writerow(["retrieved_date", "date", "path", "source_url"])
            for r in added:
                w.writerow([today(), r.get("date", ""), r.get("path", ""),
                            r.get("source_url", "")])
    return len(added)


# ------------------------------------------------------------- file helpers

def today():
    return datetime.date.today().isoformat()


def week_start(iso_date):
    """Monday of the given ISO date's week (the repo's minutes dir convention)."""
    d = datetime.date.fromisoformat(iso_date)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "meeting"


def minutes_rel_path(iso_date, slug, ext="md", prefix="minutes"):
    """Standard on-disk layout: <prefix>/<year>/<week-monday>/<date>_<slug>.<ext>.
    Cities whose index paths carry the dataset dir (e.g.
    'meeting_minutes/minutes/...') pass prefix='meeting_minutes/minutes'."""
    return f"{prefix}/{iso_date[:4]}/{week_start(iso_date)}/{iso_date}_{slug}.{ext}"


def save_raw(dataset_dir, filename, content):
    """Retain a fetched original verbatim under <dataset>/raw/."""
    raw = Path(dataset_dir) / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    out = raw / filename
    if isinstance(content, str):
        out.write_text(content, encoding="utf-8")
    else:
        out.write_bytes(content)
    return out


def pdf_to_text(pdf_path, layout=True):
    """pdftotext -layout extraction (the repo's minutes-conversion default)."""
    cmd = ["pdftotext"]
    if layout:
        cmd.append("-layout")
    cmd += [str(pdf_path), "-"]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"pdftotext failed on {pdf_path}: {r.stderr.decode()[:200]}")
    return r.stdout.decode("utf-8", "replace")


# --------------------------------------------------------------- probe layer

def write_probe(city_dir, dataset, result):
    """Merge one dataset's probe result into <city>/refresh_probe.json."""
    city_dir = Path(city_dir)
    pj = city_dir / "refresh_probe.json"
    data = {}
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
        except json.JSONDecodeError:
            data = {}
    data[dataset] = result
    pj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    return pj


def run_pipeline_step(cmd, cwd, label):
    print(f"\n--- {label}: {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(cwd))
    if r.returncode != 0:
        print(f"    WARNING: {label} exited {r.returncode} — review before rebuilding db/weeks.")
    return r.returncode


# ----------------------------------------------------------------- CLI layer

def run_cli(city_dir, datasets, description):
    """Shared entrypoint. `datasets` maps dataset name -> dict with keys:
        portal      vendor label ("primegov", "granicus", ...)
        baseline    () -> (max_date, n_rows)          [index baseline]
        probe       (max_date) -> {"new_items": [...], "endpoint": str,
                                   "notes": str}      [read-only]
        fetch       (new_items) -> n_fetched, or None if not implemented
        post_fetch  optional () -> None  (extract/validate steps)
    """
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--probe", action="store_true",
                    help="report what's new on the portal vs the index; fetch nothing (default)")
    ap.add_argument("--fetch", action="store_true",
                    help="download new docs, convert, index, extract + validate votes")
    ap.add_argument("--dataset", choices=list(datasets),
                    help="limit to one dataset (default: all)")
    args = ap.parse_args()
    mode = "fetch" if args.fetch else "probe"
    selected = {args.dataset: datasets[args.dataset]} if args.dataset else datasets

    city_dir = Path(city_dir)
    any_fail = False
    for name, ds in selected.items():
        max_date, n_rows = ds["baseline"]()
        print(f"\n=== {city_dir.name} / {name} [{ds['portal']}] ===")
        print(f"index: {n_rows} rows, max date {max_date}")
        result = {
            "probe_date": today(), "portal": ds["portal"],
            "index_max_date": max_date, "index_rows": n_rows,
            "fetch_cmd": f"python3 fetch_new.py --fetch --dataset {name}",
        }
        try:
            pr = ds["probe"](max_date)
            items = pr.get("new_items", [])
            result.update(status="ok", endpoint=pr.get("endpoint", ""),
                          new_count=len(items), notes=pr.get("notes", ""),
                          new_items=[{k: it.get(k) for k in ("date", "title", "url")}
                                     for it in items])
            print(f"portal: {len(items)} new item(s) since {max_date}")
            for it in items:
                print(f"  NEW {it.get('date')}  {it.get('title', '')}")
            if pr.get("notes"):
                print(f"note: {pr['notes']}")
        except Exception as e:
            any_fail = True
            result.update(status="fail", endpoint=ds.get("endpoint", ""),
                          new_count=None, error=f"{type(e).__name__}: {e}",
                          new_items=[])
            print(f"PROBE FAILED: {type(e).__name__}: {e}")
            write_probe(city_dir, name, result)
            continue
        write_probe(city_dir, name, result)

        if mode == "fetch" and items:
            if not ds.get("fetch"):
                print("fetch: not implemented for this dataset (see script header)")
                continue
            n = ds["fetch"](items)
            print(f"fetched {n} document(s)")
            if ds.get("post_fetch"):
                ds["post_fetch"]()
            print("\nREMINDER: rebuild the derived layers when done:\n"
                  "  python3 db/build_db.py   (+ build_referrals.py where present)\n"
                  "  python3 build_weeks.py\n"
                  "  python3 ../scripts/normalize_motions.py --all (motions_std refresh)")
    print(f"\nProbe results written to {city_dir / 'refresh_probe.json'}")
    if any_fail:
        sys.exit(1)
