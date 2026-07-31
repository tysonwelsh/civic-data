#!/usr/bin/env python3
"""
Herriman minutes harvester / incremental refresh — PrimeGov portal
(herriman.primegov.com) + a 2020 legacy-S3 backfill.

Datasets:
  meeting_minutes      City Council (committeeId 3) minutes  (body=Council; a few
                       2020 Community Development Agency docs tagged body=CDRA)
  planning_commission  Planning Commission (committeeId 14) minutes (body=PlanningCommission)

Sources
-------
* PrimeGov 2021-01-07 -> present (the portal's floor):
    List:     GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY  -> JSON
              each meeting: id, committeeId, meetingTypeId, dateTime, title,
              documentList[] ({templateName, templateId, id})
    Minutes = documentList entry whose templateName == "Minutes"
    Download: GET /Public/CompiledDocument?meetingTemplateId=<templateId>
              (302 -> short-lived Azure-blob SAS URL; urllib follows the redirect;
              the blob host needs a browser UA).  source=primegov
* 2020 floor (ABSENT from PrimeGov) — recovered from the still-live legacy AWS S3
  bucket `herriman-agendas` (us-west-1) whose LISTING is AccessDenied but whose
  individual objects serve HTTP 200.  The 2020 minutes keys were enumerated by
  probing the fixed YYYY_MM_DD[.suffix].pdf pattern for every 2020 date (a 200 =
  exists, a 403 = absent); the confirmed keys are hard-listed in S3_2020 below.
    https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/
        2020-city-council-minutes/YYYY_MM_DD[.suffix].pdf
        2020-planning-commission-minutes/YYYY_MM_DD.pdf
  source=s3-legacy.  A `_CDA` suffix = the Community Development Agency (body=CDRA).

Modes:
  --probe    (default) READ-ONLY: list PrimeGov meetings newer than the index max
             date; fetch nothing; write refresh_probe.json.
  --ingest   APPEND-ONLY refresh (the safe path): probe -> download ONLY the
             genuinely-new minutes -> convert each to markdown -> APPEND rows to
             minutes_index.csv via refresh_lib.append_index_rows (dedups on path,
             re-sorts, logs fetch_log.csv) -> run extract_votes.py ->
             extract_backfill_votes.py (REQUIRED PMN re-merge) -> validate_votes.py.
             It NEVER regenerates the index or the markdown corpus, so the curated /
             PMN-promoted / S3-2020 / recovered rows are preserved untouched.
  --full-build / --build-md   DESTRUCTIVE from-scratch index+markdown rebuilds that
             rewrite minutes_index.csv from the PrimeGov+S3 harvest lists — they DROP
             every curated / PMN-promoted / recovered row not in those lists (proven
             2026-07-19; the run was fully reverted).  REFUSED unless
             --force-full-rebuild is also passed; the index is auto-backed-up first.
             NOT a refresh step — use --ingest.

Resumable: skips any doc already on disk (by raw filename).  Downloads run in a
small thread pool (one-time academic harvest of a public record); PrimeGov listing
GETs are throttled through refresh_lib.
"""

import csv
import hashlib
import re
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://herriman.primegov.com"
LIST_API = HOST + "/api/v2/PublicPortal/ListArchivedMeetings?year={year}"
DOC_URL = HOST + "/Public/CompiledDocument?meetingTemplateId={tid}"
S3_BASE = "https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas"

DATASET_CFG = {
    "meeting_minutes": {"committee_id": 3, "default_body": "Council",
                        "s3_folder": "2020-city-council-minutes"},
    "planning_commission": {"committee_id": 14, "default_body": "PlanningCommission",
                            "s3_folder": "2020-planning-commission-minutes"},
}

# 2020 S3 minutes keys, confirmed live by HTTP-200 probe 2026-07-11 (bucket listing
# is AccessDenied; these are the objects that individually serve).  Gaps are real
# (COVID-era cancellations / days with no meeting), not missed probes.
S3_2020 = {
    "meeting_minutes": [
        "2020_01_08", "2020_01_15", "2020_01_22", "2020_01_29", "2020_02_12",
        "2020_02_12_CDA", "2020_02_26", "2020_03_11_CDA", "2020_04_08",
        "2020_04_08_CDA", "2020_04_22", "2020_05_06", "2020_05_27", "2020_05_27_CDA",
        "2020_06_10", "2020_06_10_CDA", "2020_06_24", "2020_07_08", "2020_08_12",
        "2020_08_19", "2020_08_26", "2020_09_09_CDA", "2020_09_30_Joint",
        "2020_10_28", "2020_11_18_SCCM", "2020_12_16",
    ],
    "planning_commission": [
        "2020_01_02", "2020_02_06", "2020_02_20", "2020_03_05", "2020_04_02",
        "2020_04_16", "2020_05_07", "2020_05_21", "2020_06_04", "2020_06_18",
        "2020_07_16", "2020_08_06", "2020_08_20", "2020_09_03", "2020_09_17",
        "2020_10_01", "2020_10_15", "2020_11_05", "2020_11_19",
    ],
}

# ---------------------------------------------------------------------------
# WRONG-FILE PORTAL SLOTS — meetings whose PrimeGov "Minutes" document is NOT
# that meeting's minutes (a city-side clerk mis-upload).  Keyed
# (dataset, date, primegov meeting id).  The raw PDF is still downloaded and
# RETAINED under raw/ (originals are never deleted); it is simply never turned
# into an indexed minutes document, so a --force-full-rebuild cannot resurrect
# the phantom.  Each entry MUST be source-verified and ledgered in the dataset's
# minutes_unrecovered.csv.
#
#   ("meeting_minutes", "2021-03-12", 168)  — verified 2026-07-31.  PrimeGov
#   meetingTemplateId=857 serves the **March 18, 2021** special-meeting minutes
#   (header + narrative + Wendy Thorpe certification all say "Thursday, March 18,
#   2021", 2:30 p.m., approved April 14, 2021; only a stale page-2 footer reads
#   "March 12").  That is a byte-for-content duplicate of the pmn_backfill
#   2021-03-18 record (PMN notice 664571 / file 707985, meeting noticed
#   2021/03/18 01:30 PM).  A REAL but DIFFERENT March 12 meeting exists — PMN
#   notice 663195, 2021/03/12 09:00 AM, attachment "2021_03_12 SCCM Minutes.pdf"
#   (file 701319): "Friday, March 12, 2021", 11:00 a.m., approved March 24, 2021,
#   certified by City Recorder Jackie Nostrom.  Recovering 701319 into
#   pmn_backfill/ is the queued fix; until then 2021-03-12 is an honest gap.
WRONG_FILE_SLOTS = {
    ("meeting_minutes", "2021-03-12", 168),
}


def is_wrong_file_slot(dataset, item):
    try:
        mid = int(item.get("mid"))
    except (TypeError, ValueError):
        return False
    return (dataset, item.get("date"), mid) in WRONG_FILE_SLOTS


def body_for(dataset, title):
    if dataset == "planning_commission":
        return "PlanningCommission"
    t = (title or "").lower()
    if "cda" in t or "community development" in t or "redevelopment" in t:
        return "CDRA"
    if "hcsea" in t:
        return "HCSEA"
    if "hcfsa" in t:
        return "HCFSA"
    return "Council"


def s3_title(dataset, key):
    if dataset == "planning_commission":
        return "Planning Commission Meeting"
    if key.endswith("_CDA"):
        return "Community Development Agency Meeting"
    if key.endswith("_Joint"):
        return "Joint City Council Meeting"
    if key.endswith("_SCCM"):
        return "Special City Council Meeting"
    return "City Council Meeting"


def slug_for(dataset, title, key_suffix=""):
    base = rl.slugify(title)
    return (base + key_suffix) if key_suffix else base


def minutes_template(meeting):
    for d in meeting.get("documentList", []):
        if d.get("templateName") == "Minutes":
            return d.get("templateId")
    return None


def download(url):
    """Fetch bytes following redirects, browser UA (blob + S3 host)."""
    req = urllib.request.Request(url, headers={"User-Agent": rl.BROWSER_UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


# ------------------------------------------------------------------ listing
def list_primegov(dataset):
    """All PrimeGov meetings for this dataset's committee that carry a Minutes doc,
    2021..current year.  Returns list of dicts {date,title,url,body,slug}."""
    cfg = DATASET_CFG[dataset]
    y1 = int(rl.today()[:4])
    out, no_min = [], 0
    for year in range(2021, y1 + 1):
        try:
            meetings = rl.http_get_json(LIST_API.format(year=year))
        except Exception as e:
            print(f"  list {year}: {e}")
            continue
        for m in meetings:
            if m.get("committeeId") != cfg["committee_id"]:
                continue
            date = (m.get("dateTime") or "")[:10]
            if not date:
                continue
            tid = minutes_template(m)
            if not tid:
                no_min += 1
                continue
            title = (m.get("title") or "").strip()
            out.append({"date": date, "title": title,
                        "url": DOC_URL.format(tid=tid), "body": body_for(dataset, title),
                        "slug": slug_for(dataset, title), "source": "primegov",
                        "mid": m.get("id")})
    return out, no_min


def list_s3(dataset):
    cfg = DATASET_CFG[dataset]
    out = []
    for key in S3_2020[dataset]:
        m = re.match(r"(\d{4})_(\d{2})_(\d{2})(.*)", key)
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        suffix = m.group(4)  # e.g. _CDA
        title = s3_title(dataset, key)
        slug = slug_for(dataset, title)
        out.append({"date": date, "title": title,
                    "url": f"{S3_BASE}/{cfg['s3_folder']}/{key}.pdf",
                    "body": body_for(dataset, title), "slug": slug,
                    "source": "s3-legacy", "mid": key})
    return out


# ------------------------------------------------------------------ fetch
def raw_name(item):
    # unique raw filename per meeting: <date>_<mid>.pdf
    return f"{item['date']}_{item['mid']}.pdf"


def fetch_items(dataset, items):
    ds_dir = CITY_DIR / dataset
    raw_dir = ds_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    # resumable: skip items whose raw pdf already exists
    todo = [it for it in items if not (raw_dir / raw_name(it)).exists()]
    print(f"  {dataset}: {len(items)} listed, {len(todo)} to download")

    def _dl(it):
        try:
            data = download(it["url"])
        except Exception as e:
            return it, None, str(e)
        return it, data, None

    fetched = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for it, data, err in ex.map(_dl, todo):
            if err or not data or not data.startswith(b"%PDF"):
                print(f"    SKIP {it['date']} {it['mid']}: {err or 'not a PDF'}")
                continue
            (raw_dir / raw_name(it)).write_bytes(data)
            fetched.append(it)
    print(f"  downloaded {len(fetched)} new PDFs")
    # (re)build markdown + index from everything on disk
    return build_from_raw(dataset, items)


def build_from_raw(dataset, items):
    """Convert every raw PDF that has a listed item into markdown (resumable) and
    rewrite minutes_index.csv.  Dedups byte-identical PDFs across meeting slots."""
    ds_dir = CITY_DIR / dataset
    raw_dir = ds_dir / "raw"
    seen_hash = {}
    index_rows = []
    n_new_md = 0
    for it in sorted(items, key=lambda x: (x["date"], str(x["mid"]))):
        rp = raw_dir / raw_name(it)
        if not rp.exists():
            continue
        if is_wrong_file_slot(dataset, it):
            # portal slot serves another meeting's minutes — raw kept, never indexed
            print(f"    WRONG-FILE SLOT, not indexed: {it['date']} mid={it['mid']} "
                  f"(see WRONG_FILE_SLOTS + {dataset}/minutes_unrecovered.csv)")
            continue
        h = hashlib.sha256(rp.read_bytes()).hexdigest()
        if h in seen_hash:
            # byte-identical to an already-kept doc (Part1/Part2 or dup slot) -> skip
            continue
        seen_hash[h] = it
        slug = it["slug"]
        rel = f"minutes/{it['date'][:4]}/{rl.week_start(it['date'])}/{it['date']}_{slug}.md"
        out = ds_dir / rel
        # avoid same-date same-slug collision (distinct meetings, distinct content)
        n = 1
        while out.exists() and _md_source(out) not in (raw_name(it), None):
            n += 1
            rel = (f"minutes/{it['date'][:4]}/{rl.week_start(it['date'])}/"
                   f"{it['date']}_{slug}-{n}.md")
            out = ds_dir / rel
        fmt = "text"
        if not out.exists():
            text = rl.pdf_to_text(rp)
            if len(text.strip()) < 200:
                # image-only PDF -> OCR fallback
                text = ocr_pdf(rp)
                fmt = "ocr"
            out.parent.mkdir(parents=True, exist_ok=True)
            header = (f"# {it['title']}\n\n"
                      f"**Date:** {it['date']}\n"
                      f"**Body:** {it['body']}\n"
                      f"**Source:** {it['source']} | {it['url']}\n"
                      f"**Raw:** raw/{raw_name(it)}\n"
                      f"**Format:** {fmt}\n"
                      f"**Retrieved:** {rl.today()}\n\n---\n\n")
            out.write_text(header + text, encoding="utf-8")
            n_new_md += 1
        index_rows.append({"date": it["date"], "year": it["date"][:4],
                           "title": it["title"], "slug": out.stem.split("_", 1)[1],
                           "path": rel, "source": it["source"],
                           "source_url": it["url"], "format": _md_format(out)})
    # rewrite index
    idx = ds_dir / "minutes_index.csv"
    index_rows.sort(key=lambda r: (r["date"], r["slug"]))
    with open(idx, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rl.INDEX_COLS)
        w.writeheader()
        w.writerows(index_rows)
    print(f"  wrote {len(index_rows)} index rows ({n_new_md} new markdown files)")
    return len(index_rows)


def _md_source(path):
    try:
        head = path.read_text(encoding="utf-8")[:600]
        m = re.search(r"\*\*Raw:\*\*\s*raw/(\S+)", head)
        return m.group(1) if m else None
    except Exception:
        return None


def _md_format(path):
    head = path.read_text(encoding="utf-8")[:600]
    m = re.search(r"\*\*Format:\*\*\s*(\w+)", head)
    return m.group(1) if m else "text"


def ocr_pdf(pdf_path):
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(pdf_path),
                        f"{td}/p"], check=True, timeout=600)
        texts = []
        for png in sorted(Path(td).glob("p*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            texts.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(texts)


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


def run_full_build():
    for dataset in DATASET_CFG:
        print(f"\n=== BUILD {dataset} ===")
        pg, no_min = list_primegov(dataset)
        s3 = list_s3(dataset)
        items = s3 + pg
        print(f"  PrimeGov: {len(pg)} w/minutes ({no_min} w/o); S3 2020: {len(s3)}")
        fetch_items(dataset, items)
        post_fetch(dataset)


def _probe_new(dataset):
    """READ-ONLY.  Returns (new_items, index_max_date, index_rows, no_minutes_count)
    for one dataset: the PrimeGov minutes-bearing meetings strictly NEWER than the
    index max date and not already indexed.  Shared by probe() and ingest()."""
    idx = CITY_DIR / dataset / "minutes_index.csv"
    have, mx, nrows = set(), "", 0
    if idx.exists():
        with open(idx, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = (r.get("date") or "")[:10]
                if d:
                    have.add(d)
                    mx = max(mx, d)
                    nrows += 1
    pg, no_min = list_primegov(dataset)
    new = [it for it in pg if it["date"] not in have and it["date"] > mx]
    return new, mx, nrows, no_min


def probe():
    """READ-ONLY probe: list PrimeGov meetings with a Minutes doc newer than the
    index, print + write the standard refresh_probe.json.  Touches NOTHING else —
    unlike --build-md/--full-build (destructive full index rebuilds; proven
    2026-07-19).  Ingest with the append-only --ingest."""
    import json as _json
    result = {}
    for dataset in DATASET_CFG:
        new, mx, nrows, no_min = _probe_new(dataset)
        print(f"== {dataset} ==  index max {mx or '(empty)'} ({nrows} rows); "
              f"NEW newer-than-index: {len(new)}")
        for it in new:
            print(f"   NEW {it['date']}  {it['title'][:70]}")
        result[dataset] = dict(
            probe_date=rl.today(), portal="primegov",
            index_max_date=mx or None, index_rows=nrows, status="ok",
            new_count=len(new),
            new_items=[{k: it[k] for k in ("date", "title", "url")} for it in new],
            notes="read-only probe; ingest via `fetch_new.py --ingest` (append-only) "
                  "— NEVER --build-md/--full-build (destructive full rebuild)")
    (CITY_DIR / "refresh_probe.json").write_text(
        _json.dumps(result, indent=1), encoding="utf-8")
    print(f"Probe results written to {CITY_DIR / 'refresh_probe.json'}")


# ---------------------------------------------------------- append-only ingest
def _convert_item(dataset, item):
    """Convert ONE downloaded raw PDF -> markdown (single-file, idempotent) and return
    its 8-col index-row dict, or None if the raw is missing.  Mirrors build_from_raw's
    per-item logic (provenance header, OCR fallback, same-date/slug collision suffix)
    but writes ONLY this doc and NEVER rewrites the index or touches other files."""
    ds_dir = CITY_DIR / dataset
    rp = ds_dir / "raw" / raw_name(item)
    if not rp.exists():
        return None
    slug = item["slug"]
    rel = f"minutes/{item['date'][:4]}/{rl.week_start(item['date'])}/{item['date']}_{slug}.md"
    out = ds_dir / rel
    n = 1
    while out.exists() and _md_source(out) not in (raw_name(item), None):
        n += 1
        rel = (f"minutes/{item['date'][:4]}/{rl.week_start(item['date'])}/"
               f"{item['date']}_{slug}-{n}.md")
        out = ds_dir / rel
    if not out.exists():
        text = rl.pdf_to_text(rp)
        fmt = "text"
        if len(text.strip()) < 200:
            text = ocr_pdf(rp)
            fmt = "ocr"
        out.parent.mkdir(parents=True, exist_ok=True)
        header = (f"# {item['title']}\n\n"
                  f"**Date:** {item['date']}\n"
                  f"**Body:** {item['body']}\n"
                  f"**Source:** {item['source']} | {item['url']}\n"
                  f"**Raw:** raw/{raw_name(item)}\n"
                  f"**Format:** {fmt}\n"
                  f"**Retrieved:** {rl.today()}\n\n---\n\n")
        out.write_text(header + text, encoding="utf-8")
    return {"date": item["date"], "year": item["date"][:4], "title": item["title"],
            "slug": out.stem.split("_", 1)[1], "path": rel, "source": item["source"],
            "source_url": item["url"], "format": _md_format(out)}


def post_ingest(dataset):
    """Extract chain for a dataset that just gained rows.  extract_votes.py runs
    WITHOUT --force so only the NEW meetings (no JSON yet) are parsed — every existing
    meeting's JSON (hence its curated movers/results) is left untouched.  Then the
    PMN re-merge, then validate."""
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir,
                         f"{dataset} extract_votes")
    if (ds_dir / "extract_backfill_votes.py").exists():
        # CRITICAL: extract_votes.py REWRITES all_votes.csv from the audited JSON only;
        # without this re-merge the 949 PMN-recovered rows (mm 677 + pc 272,
        # provenance=pmn_minutes) SILENTLY DROP OUT.  Always chained here.
        rl.run_pipeline_step(["python3", "extract_backfill_votes.py"], ds_dir,
                             f"{dataset} extract_backfill_votes (PMN re-merge — REQUIRED)")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir,
                         f"{dataset} validate_votes")


def ingest(only=None):
    """APPEND-ONLY incremental refresh.  Probes for minutes-bearing PrimeGov meetings
    newer than the index max, downloads ONLY those, converts each to markdown, and
    APPENDS index rows via refresh_lib.append_index_rows (dedups on path, re-sorts,
    logs fetch_log.csv).  Never regenerates the index or the corpus, so the curated /
    PMN-promoted / S3-2020 / recovered rows are preserved.  Then runs post_ingest."""
    datasets = [only] if only else list(DATASET_CFG)
    touched = []
    for dataset in datasets:
        new, mx, nrows, _ = _probe_new(dataset)
        print(f"\n=== INGEST {dataset} ===  index max {mx or '(empty)'} "
              f"({nrows} rows); {len(new)} new PrimeGov minutes")
        if not new:
            print("  nothing new — minutes_index.csv left byte-for-byte untouched")
            continue
        ds_dir = CITY_DIR / dataset
        (ds_dir / "raw").mkdir(parents=True, exist_ok=True)
        rows = []
        for it in new:
            rp = ds_dir / "raw" / raw_name(it)
            if not rp.exists():
                try:
                    data = download(it["url"])
                except Exception as e:
                    print(f"  SKIP {it['date']} {it['mid']}: {e}")
                    continue
                if not data or not data.startswith(b"%PDF"):
                    print(f"  SKIP {it['date']} {it['mid']}: not a PDF")
                    continue
                rp.write_bytes(data)
            row = _convert_item(dataset, it)
            if row:
                rows.append(row)
                print(f"  + {row['date']}  {row['title'][:60]}")
        added = rl.append_index_rows(ds_dir, rows)
        print(f"  appended {added} new index row(s) (of {len(rows)} converted; "
              f"append_index_rows dedups on path)")
        if added:
            touched.append(dataset)
    for dataset in touched:
        post_ingest(dataset)
    if touched:
        print("\nREMINDER: rebuild the derived layers when done:\n"
              "  python3 db/build_db.py && python3 db/build_referrals.py\n"
              "  python3 build_weeks.py\n"
              "  python3 ../scripts/normalize_motions.py --all   (motions_std refresh)")
    else:
        print("\nNo new documents ingested — indexes untouched, nothing to rebuild.")


# --------------------------------------------------------- destructive guards
def backup_index(dataset):
    """Copy a dataset's minutes_index.csv to _backups/<date>-herriman-fetch/ before any
    destructive rewrite.  Returns the backup path (or None if there is no index yet)."""
    idx = CITY_DIR / dataset / "minutes_index.csv"
    if not idx.exists():
        return None
    bk = CITY_DIR.parent / "_backups" / f"{rl.today()}-herriman-fetch" / dataset
    bk.mkdir(parents=True, exist_ok=True)
    dest = bk / "minutes_index.csv"
    shutil.copy2(idx, dest)
    print(f"  backed up {dataset}/minutes_index.csv -> {dest}")
    return dest


def _destructive_refuse(flag):
    sys.stderr.write(
        "\n" + "=" * 74 + "\n"
        f"REFUSED: {flag} is a DESTRUCTIVE full index+markdown rebuild.\n"
        "It rewrites minutes_index.csv from the PrimeGov+S3 harvest lists, DROPPING\n"
        "every curated / PMN-promoted / recovered row not in those lists (proven\n"
        "2026-07-19: it clobbered the curated index; the run was fully reverted).\n\n"
        "For a normal refresh use the APPEND-ONLY path instead:\n"
        "    python3 fetch_new.py --probe      # read-only: what's new on the portal\n"
        "    python3 fetch_new.py --ingest     # append-only fetch + full extract chain\n\n"
        "If you REALLY intend a from-scratch rebuild (and will RE-CURATE the index and\n"
        "RE-RUN the PMN promotion afterward), pass --force-full-rebuild; the index is\n"
        "auto-backed-up to _backups/<date>-herriman-fetch/ first.\n"
        + "=" * 74 + "\n")
    sys.exit(2)


def _destructive_banner(flag):
    print("\n" + "!" * 74)
    print(f"!!! DESTRUCTIVE {flag} (--force-full-rebuild given): rewriting")
    print("!!! minutes_index.csv from the harvest lists.  Curated / PMN-promoted /")
    print("!!! recovered rows NOT in the harvest are LOST.  Re-curate + re-run the")
    print("!!! PMN promotion (extract_backfill_votes.py) afterward.  Index backed up:")
    print("!" * 74 + "\n")


if __name__ == "__main__":
    argv = sys.argv[1:]
    ds_arg = None
    if "--dataset" in argv:
        i = argv.index("--dataset")
        ds_arg = argv[i + 1] if i + 1 < len(argv) else None
        if ds_arg not in DATASET_CFG:
            sys.exit(f"--dataset must be one of {list(DATASET_CFG)}")
    if "--ingest" in argv:
        ingest(ds_arg)
    elif "--probe" in argv:
        probe()
    elif "--full-build" in argv:
        if "--force-full-rebuild" not in argv:
            _destructive_refuse("--full-build")
        for d in DATASET_CFG:
            backup_index(d)
        _destructive_banner("--full-build")
        run_full_build()
    elif "--build-md" in argv:
        # reconvert markdown+index from raw already on disk (no network).
        if "--force-full-rebuild" not in argv:
            _destructive_refuse("--build-md")
        for d in DATASET_CFG:
            backup_index(d)
        _destructive_banner("--build-md")
        for dataset in DATASET_CFG:
            pg, _ = list_primegov(dataset)
            build_from_raw(dataset, list_s3(dataset) + pg)
    else:
        print("usage:")
        print("  fetch_new.py --probe        READ-ONLY: list new PrimeGov minutes vs index")
        print("  fetch_new.py --ingest [--dataset D]   APPEND-ONLY refresh (fetch new +")
        print("                              append index + extract_votes + backfill re-merge)")
        print("  fetch_new.py --full-build --force-full-rebuild   initial harvest (DESTRUCTIVE)")
        print("  fetch_new.py --build-md --force-full-rebuild     reconvert from raw/ (DESTRUCTIVE)")
