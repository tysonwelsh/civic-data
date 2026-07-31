#!/usr/bin/env python3
"""
Town of Alta — minutes acquisition + incremental refresh.

Alta's `/meetings/` page (Juniper CMS) renders document links client-side (a JS
search app; wp-json/admin-ajax 404), so it CANNOT be scraped for doc URLs. The
enumerable archive is **Utah Public Notice (PMN)** — born-digital (and some
scanned) PDFs, one opaque file id each, full history via one saturated browse
page. See recon.md for the portal map; this driver reuses the PMN enumeration
method shared with riverton_city_council/fetch_new.py.

PMN body ids (Alta = tenant 130 on Juniper; PMN bodies below):
    Town Council        body 1601  -> dataset meeting_minutes
    Planning Commission body 1602  -> dataset planning_commission
(The advisory Budget / Capital committee is a DIFFERENT PMN body and is NOT the
Town Council — deliberately excluded here.)

Method per dataset:
  1. GET /pmn/list/notices.html?id=<body>&page=300   (full history, one page)
     -> cached to <dataset>/raw/_notices_<body>.html
  2. Parse each notice's attachments. Alta posts Agenda + Meeting Packet +
     Approved Minutes as separate PDFs; select the MINUTES doc (drop agenda /
     packet / handout). A draft + an approved/corrected re-post of the same
     meeting -> keep the approved/corrected one.
  3. Download https://www.utah.gov/pmn/files/<file_id>.pdf -> <dataset>/raw/,
     pdftotext -layout -> markdown with a provenance header, append
     minutes_index.csv (source=pmn).  Image-only scans (<200B text) -> OCR
     (pdftoppm 300dpi + tesseract), format=ocr.
Resumable: an already-indexed file id (source_url) or an on-disk md is skipped,
so re-running continues a partial backfill.

Sparse by design: Alta Town Council meets ~monthly (2nd Wednesday, ~12/yr) and
the Planning Commission meets 4th Wednesday AS-NEEDED (frequently cancelled) —
a probe that returns nothing for a quiet month is correct, not a failure.

The Mayor VOTES in Alta (Utah Town form) — this driver only fetches/converts;
the vote grammar (max roll = 5, Mayor + 4 councilmembers) lives in each
dataset's extract_votes.py, invoked here with its body arg.

Usage:
  python3 fetch_new.py --probe    [--dataset meeting_minutes|planning_commission]  # default, read-only
  python3 fetch_new.py --fetch    [--dataset ...]   # fetch new since index max, then extract+validate
  python3 fetch_new.py --backfill [--dataset ...]   # (re)enumerate full >=FLOOR history
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

FLOOR = "2020-01-01"
PMN = "https://www.utah.gov"
NOTICES = PMN + "/pmn/list/notices.html?id={body}&page=300"
FILE_URL = PMN + "/pmn/files/{fid}.pdf"
NOTICE_URL = PMN + "/pmn/sitemap/notice/{nid}.html"

DATASETS = {
    "meeting_minutes":     {"body": 1601, "kind": "council", "arg": "council",
                            "title": "Alta Town Council Meeting", "slug": "town-council"},
    "planning_commission": {"body": 1602, "kind": "pc", "arg": "pc",
                            "title": "Alta Planning Commission Meeting",
                            "slug": "planning-commission"},
}

_DROP = re.compile(r"agenda|packet|handout|exhibit|notice of|cancel", re.I)
_MIN = re.compile(r"min", re.I)


def _is_minutes(att):
    fn = att["filename"].lower()
    typ = att["type"].lower()
    if _DROP.search(fn) and not _MIN.search(fn):
        return False
    return "minutes" in typ or _MIN.search(fn) is not None


def _pick(cands):
    """draft + approved/corrected re-post of the same meeting -> keep the
    corrected/approved one; ties broken by longest (most descriptive) filename."""
    def score(a):
        low = a["filename"].lower()
        return (2 if "correct" in low else 1 if "approv" in low else 0, len(a["filename"]))
    return sorted(cands, key=score)[-1]


def parse_notices(html):
    m = re.search(r"<tbody>(.*)</tbody>", html, re.S)
    body = m.group(1) if m else html
    out = []
    for r in re.split(r'<tr class="(?:on|off)">', body)[1:]:
        nm = re.search(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>', r, re.S)
        if not nm:
            continue
        dm = re.search(r"(\d{4}/\d{2}/\d{2})", r)
        atts = []
        for am in re.finditer(
                r'/pmn/files/(\d+)\.pdf"[^>]*>(.*?)</a>\s*(?:&nbsp;)?\s*\(([^)]*)\)', r, re.S):
            atts.append({"file_id": am.group(1),
                         "filename": re.sub(r"\s+", " ", am.group(2)).strip(),
                         "type": am.group(3).strip()})
        out.append({"notice_id": nm.group(1),
                    "title": re.sub(r"\s+", " ", nm.group(2)).strip(),
                    "date": dm.group(1).replace("/", "-") if dm else "",
                    "attachments": atts})
    return out


def _notices_html(dataset, refresh=False):
    ds = DATASETS[dataset]
    cache = CITY_DIR / dataset / "raw" / f"_notices_{ds['body']}.html"
    if cache.exists() and not refresh:
        return cache.read_text(encoding="utf-8", errors="replace")
    html = rl.http_get(NOTICES.format(body=ds["body"]), ua=rl.BROWSER_UA)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(html, encoding="utf-8")
    return html


def enumerate_meetings(dataset, refresh=False):
    """date -> chosen minutes attachment (one per meeting date), >= FLOOR."""
    notices = parse_notices(_notices_html(dataset, refresh))
    perdate = {}
    for n in notices:
        if not n["date"] or n["date"] < FLOOR:
            continue
        mins = [a for a in n["attachments"] if _is_minutes(a)]
        if not mins:
            continue
        chosen = dict(_pick(mins), notice_id=n["notice_id"])
        if n["date"] in perdate:
            perdate[n["date"]] = _pick([perdate[n["date"]], chosen])
        else:
            perdate[n["date"]] = chosen
    return dict(sorted(perdate.items()))


def _ocr(pdf_path):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", str(pdf_path),
                        str(Path(td) / "p")], check=True, timeout=600)
        parts = []
        for png in sorted(Path(td).glob("p*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            parts.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(parts)


def _markdown(title, date, source_url, notice_url, body_name, fmt, text):
    return (f"# {title} — {date}\n"
            f"> Source: {source_url}\n"
            f"> Meeting date: {date}\n"
            f"> Body: {body_name}\n"
            f"> PMN notice: {notice_url}\n"
            f"> Format: {fmt}\n\n" + text)


def fetch(dataset, since=None, refresh_notices=False):
    ds = DATASETS[dataset]
    ds_dir = CITY_DIR / dataset
    body_name = "PlanningCommission" if ds["kind"] == "pc" else "Council"
    prior = rl.load_index(ds_dir)
    have_urls = {r.get("source_url") for r in prior}
    have_paths = {r.get("path") for r in prior}
    meetings = enumerate_meetings(dataset, refresh=refresh_notices)
    index_rows, n, stubs = [], 0, []
    for date, att in meetings.items():
        if since and date <= since:
            continue
        url = FILE_URL.format(fid=att["file_id"])
        if url in have_urls:
            continue
        rel = rl.minutes_rel_path(date, ds["slug"], "md", prefix="minutes")
        if rel in have_paths or (ds_dir / rel).exists() or any(r["path"] == rel for r in index_rows):
            continue
        try:
            pdf = rl.http_get(url, binary=True, ua=rl.BROWSER_UA,
                              referer=NOTICE_URL.format(nid=att["notice_id"]))
        except Exception as e:
            print(f"  ERR  {date}: {type(e).__name__} — retry later")
            continue
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: {len(pdf)} bytes, not a PDF")
            continue
        raw = rl.save_raw(ds_dir, f"{date}_{ds['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        fmt = "pdf-text"
        if len(text.strip()) < 200:
            print(f"  OCR  {date}: {len(text.strip())}B text — OCR scanned PDF")
            text = _ocr(raw)
            fmt = "ocr"
            if len(text.strip()) < 200:
                stubs.append(date)
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_markdown(ds["title"], date, url,
                                 NOTICE_URL.format(nid=att["notice_id"]),
                                 body_name, fmt, text), encoding="utf-8")
        index_rows.append({"date": date, "year": date[:4], "title": ds["title"],
                           "slug": ds["slug"], "path": rel, "source": "pmn",
                           "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched {rel} [{fmt}]  (pmn file {att['file_id']})")
    rl.append_index_rows(ds_dir, index_rows)
    print(f"{dataset}: fetched {n} new document(s); on-disk total now "
          f"{len(prior) + n}. stubs={stubs}")
    return n, stubs


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    arg = DATASETS[dataset]["arg"]
    rl.run_pipeline_step(["python3", "extract_votes.py", arg], ds_dir,
                         f"{dataset} extract_votes {arg}")
    rl.run_pipeline_step(["python3", "validate_votes.py", arg], ds_dir,
                         f"{dataset} validate_votes {arg}")


def probe(dataset):
    ds_dir = CITY_DIR / dataset
    body = DATASETS[dataset]["body"]
    mx, nrows = rl.index_max_date(ds_dir)
    try:
        meetings = enumerate_meetings(dataset)
    except Exception as e:  # noqa: BLE001
        print(f"=== {dataset} [pmn body {body}] === PROBE FAILED: {type(e).__name__}: {e}")
        rl.write_probe(CITY_DIR, dataset, {
            "probe_date": rl.today(), "portal": "pmn",
            "index_max_date": mx, "index_rows": nrows, "status": "fail",
            "new_count": None, "new_items": [], "error": f"{type(e).__name__}: {e}",
            "notes": f"PMN body {body} notice enumeration failed",
            "fetch_cmd": f"python3 fetch_new.py --fetch --dataset {dataset}",
        })
        return []
    new = [d for d in meetings if not mx or d > mx]
    print(f"=== {dataset} [pmn body {body}] ===")
    print(f"index: {nrows} rows, max date {mx}; PMN enumerates {len(meetings)} "
          f"meetings >= {FLOOR}; {len(new)} newer than index")
    for d in new:
        print(f"  NEW {d}")
    rl.write_probe(CITY_DIR, dataset, {
        "probe_date": rl.today(), "portal": "pmn",
        "index_max_date": mx, "index_rows": nrows, "status": "ok",
        "new_count": len(new),
        "new_items": [{"date": d, "title": DATASETS[dataset]["title"], "url": ""}
                      for d in new],
        "notes": (f"PMN body {body}; {len(meetings)} meetings enumerated >= {FLOOR} from "
                  f"the cached notice list (run --fetch/--refresh-notices to refresh it). "
                  f"Alta is sparse (~12 council mtgs/yr) — an empty result is normal."),
        "fetch_cmd": f"python3 fetch_new.py --fetch --dataset {dataset}",
    })
    return new


if __name__ == "__main__":
    sel = None
    if "--dataset" in sys.argv:
        sel = sys.argv[sys.argv.index("--dataset") + 1]
    datasets = [sel] if sel else list(DATASETS)
    if "--backfill" in sys.argv:
        for ds in datasets:
            print(f"\n### backfill {ds} ###")
            fetch(ds, refresh_notices="--refresh-notices" in sys.argv)
            post_fetch(ds)
    elif "--fetch" in sys.argv:
        for ds in datasets:
            mx, _ = rl.index_max_date(CITY_DIR / ds)
            n, _ = fetch(ds, since=mx, refresh_notices=True)
            if n:
                post_fetch(ds)
        print("\nReminder: rebuild derived layers — "
              "python3 db/build_db.py && python3 db/build_referrals.py && python3 build_weeks.py")
    else:  # --probe (default, read-only)
        for ds in datasets:
            probe(ds)
