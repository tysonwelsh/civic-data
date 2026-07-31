#!/usr/bin/env python3
"""
Draper incremental refresh + initial backfill — Granicus ViewPublisher
(draper.granicus.com, single view_id=1 listing all bodies).

Datasets:
  meeting_minutes      City Council (regular / meeting / special / retreat variants)
  planning_commission  Planning Commission (Thursday)

Portal pattern (recon.md; verified in production 2026-07-11):
  * ONE combined HTML table lists EVERY body:
      GET https://draper.granicus.com/ViewPublisher.php?view_id=1
    Each <tr class="listingRow"> carries the body name (headers="Name"), a date
    like "Tuesday, December 3, 2024 - 05:40 PM", and minutes links.
  * Minutes docs are reachable EITHER as a plain
        <a href="//draper.granicus.com/MinutesViewer.php?...&doc_id=<uuid>">Minutes</a>
    (older meetings) OR — for 2023-08+ meetings — as a JS "Documents Selector"
        <option value="//draper.granicus.com/MinutesViewer.php?...">CC 6.9 Minutes</option>
    listing BOTH a tally-only "… Recap" AND the full "… Minutes".
  * MinutesViewer.php returns raw born-digital PDF bytes directly (%PDF-1.6),
    despite the .php URL. A browser UA is used (Azure edge in front of the site;
    Granicus itself served fine, UA kept as a precaution).

RECAP-vs-MINUTES TRAP (recon HIGH risk): the "… Recap" doc is stamped "does not
constitute the meeting minutes" and carries NO named roll call. We ALWAYS resolve
each meeting to its full "… Minutes" doc and DROP the Recap. A meeting that has a
Recap but no Minutes yet (pre-adoption) is recorded as pending in
<dataset>/minutes_unrecovered.csv (kind=recap_only_pending), never fetched.

Bodies deliberately OUT of scope here (separate Granicus bodies, not acquired by
this task): RDA / MBA / CRA / Historic Preservation / Zoning Administrator / etc.

Structure:
  * Council: Mayor Troy Walker PRESIDES but does NOT vote — roll grids list exactly
    the 5 at-large members (max tally 5).
  * Named per-member grid — Council: Yes|No|Absent ; PC: Yes|No|Abstained|
    Not Participating|Absent. Parsed by <dataset>/extract_votes.py.

Modes:
  --probe   (default) list usable-Minutes rows newer than the index max; fetch nothing.
  --fetch   backfill/refresh: download every usable Minutes doc >= FLOOR not already on
            disk -> <dataset>/raw/<date>_<slug>.pdf, pdftotext -layout -> markdown with a
            provenance header, append minutes_index.csv, record honest gaps in
            minutes_unrecovered.csv, then run extract_votes.py + validate_votes.py.
Resumable: files already on disk are skipped, so re-running continues a partial backfill.
"""

import csv
import datetime
import html as html_mod
import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

HOST = "https://draper.granicus.com"
LISTING = HOST + "/ViewPublisher.php?view_id=1"
FLOOR = "2020-01-01"

ROW_RE = re.compile(r'<tr class="listingRow">(.*?)</tr>', re.S)
NAME_RE = re.compile(r'headers="Name"[^>]*>\s*(.*?)\s*</td>', re.S)
DATE_RE = re.compile(r'headers="Date[^"]*"[^>]*>(.*?)</td>', re.S)
DOC_RE = re.compile(
    r'(?:<a\s+href|<option\s+value)="(//draper\.granicus\.com/MinutesViewer\.php\?'
    r'view_id=1&(?:amp;)?clip_id=(\d+)&(?:amp;)?doc_id=([0-9a-f-]+))"[^>]*>(.*?)</(?:a|option)>',
    re.S)

PC_RE = re.compile(r"planning commission", re.I)
COUNCIL_RE = re.compile(r"city council", re.I)
RECAP_RE = re.compile(r"recap", re.I)
MINUTES_RE = re.compile(r"minutes", re.I)
DRAFT_RE = re.compile(r"draft", re.I)

_LISTING_CACHE = [None]


def _clean(s):
    return re.sub(r"\s+", " ", html_mod.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def parse_date(cell):
    s = _clean(cell).replace("\xa0", " ").split(" - ")[0].strip()
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if not m:
        return None
    try:
        return datetime.datetime.strptime(
            f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date().isoformat()
    except ValueError:
        return None


def classify(name):
    if PC_RE.search(name):
        return "planning_commission"
    if COUNCIL_RE.search(name):
        return "meeting_minutes"
    return None            # RDA/MBA/CRA/HPC/etc — out of scope for this task


def pick_minutes(cands):
    """cands: list of (label, clip_id, doc_id). Resolve to the full Minutes doc,
    NEVER the Recap. Returns (label, clip_id, doc_id, kind) or (None, None, None, kind)
    where kind in {minutes, draft, recap_only_pending, no_doc}."""
    nonrecap = [c for c in cands if not RECAP_RE.search(c[0])]
    if not nonrecap:
        return None, None, None, ("recap_only_pending" if cands else "no_doc")
    mins = [c for c in nonrecap if MINUTES_RE.search(c[0]) and not DRAFT_RE.search(c[0])]
    if mins:
        c = mins[-1]
        return c[0], c[1], c[2], "minutes"
    draft = [c for c in nonrecap if MINUTES_RE.search(c[0])]
    if draft:
        c = draft[-1]
        return c[0], c[1], c[2], "draft"
    c = nonrecap[-1]          # e.g. "Action Taken" / "Approved Minutes" fallbacks
    return c[0], c[1], c[2], "minutes"


def parse_listing():
    if _LISTING_CACHE[0] is None:
        _LISTING_CACHE[0] = rl.http_get(LISTING, ua=rl.BROWSER_UA)
    page = _LISTING_CACHE[0]
    rows = []
    for block in ROW_RE.findall(page):
        mn, md = NAME_RE.search(block), DATE_RE.search(block)
        if not (mn and md):
            continue
        name = _clean(mn.group(1))
        date = parse_date(md.group(1))
        if not date:
            continue
        seen, cands = set(), []
        for m in DOC_RE.finditer(block):
            doc_id = m.group(3)
            if doc_id in seen:
                continue
            seen.add(doc_id)
            cands.append((_clean(m.group(4)), m.group(2), doc_id))
        label, clip, doc, kind = pick_minutes(cands)
        rows.append({"name": name, "date": date, "label": label,
                     "clip_id": clip, "doc_id": doc, "kind": kind,
                     "has_any": bool(cands)})
    if not any(r["kind"] in ("minutes", "draft") for r in rows):
        raise RuntimeError("ViewPublisher parsed to 0 usable Minutes rows — markup changed?")
    return rows


def slug_for(name):
    n = name.lower()
    if "planning commission" in n:
        return "planning-commission"
    if "retreat" in n:
        return "city-council-retreat"
    if "special" in n:
        return "city-council-special"
    if "canvass" in n:
        return "city-council-canvassers"
    return "city-council"


def _dataset_rows(dataset):
    return [r for r in parse_listing() if classify(r["name"]) == dataset]


def probe(dataset, max_date):
    rows = _dataset_rows(dataset)
    today = rl.today()
    new, pending, gaps, future = [], [], [], 0
    for r in rows:
        if r["date"] < FLOOR:
            continue
        if r["date"] > today:
            future += 1
            continue
        if r["kind"] in ("minutes", "draft"):
            if max_date and r["date"] <= max_date:
                continue
            new.append({"date": r["date"], "title": r["name"],
                        "url": "https:" + _url(r),
                        "clip_id": r["clip_id"], "doc_id": r["doc_id"],
                        "kind": r["kind"], "slug": slug_for(r["name"])})
        elif r["kind"] == "recap_only_pending":
            pending.append(r)
        else:
            gaps.append(r)
    new.sort(key=lambda x: x["date"])
    notes = []
    if pending:
        notes.append(f"{len(pending)} meeting(s) with only a tally-only Recap (minutes "
                     "not yet adopted) — recorded pending, NOT fetched")
    if gaps:
        notes.append(f"{len(gaps)} past meeting(s) with no minutes doc on the portal "
                     "(honest gap)")
    if future:
        notes.append(f"{future} future meeting row(s) skipped")
    return {"new_items": new, "endpoint": LISTING, "notes": "; ".join(notes),
            "_pending": pending, "_gaps": gaps}


def _url(r):
    return (f"//draper.granicus.com/MinutesViewer.php?view_id=1"
            f"&clip_id={r['clip_id']}&doc_id={r['doc_id']}")


def to_markdown(title, date, source_url, fmt, body_text):
    header = (f"# {title}\n"
              f"> Source: {source_url}\n"
              f"> Meeting date: {date}\n"
              f"> Format: {fmt}\n\n")
    return header + body_text


# Dates that must NEVER be (re-)logged as unrecovered, even though the Granicus
# listing still carries a doc-less row for them (verified 2026-07-16 promotion pass):
#   * PHANTOM listing rows — the event row itself is wrong; no such meeting existed.
#     2023-10-15 (a Sunday): both Granicus and PMN hold only the real 2023-10-17
#     minutes (indexed); PMN's complete Oct-2023 notice history shows meetings on
#     10-03 / 10-05 / 10-17 only.
#   * Dates whose minutes are IN minutes_index.csv via another source (e.g. the
#     2021-07-20 PMN promotion, source=pmn) — handled dynamically below.
PHANTOM_LISTING_DATES = {
    "meeting_minutes": {"2023-10-15"},
    "planning_commission": set(),
}


def _write_unrecovered(dataset, pending, gaps, broken=None):
    ds_dir = CITY_DIR / dataset
    path = ds_dir / "minutes_unrecovered.csv"
    existing = set()
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                rows.append(row)
                existing.add((row["date"], row["title"], row["reason"]))
    # a date already indexed (recovered via another source, e.g. PMN promotion)
    # or known-phantom is never an honest gap — drop it from the candidates
    indexed_dates = set()
    idx_path = ds_dir / "minutes_index.csv"
    if idx_path.exists():
        with open(idx_path, newline="", encoding="utf-8") as fh:
            indexed_dates = {row["date"] for row in csv.DictReader(fh)}
    skip = indexed_dates | PHANTOM_LISTING_DATES.get(dataset, set())
    pending = [r for r in pending if r["date"] not in skip]
    gaps = [r for r in gaps if r["date"] not in skip]
    broken = [r for r in (broken or []) if r["date"] not in skip]
    today = rl.today()
    for r in pending:
        reason = "recap_only_pending"
        note = ("only a tally-only Recap posted; full minutes not yet adopted — "
                "re-fetch after adoption")
        key = (r["date"], r["name"], reason)
        if key not in existing:
            rows.append({"date": r["date"], "year": r["date"][:4], "title": r["name"],
                         "body": "PlanningCommission" if dataset == "planning_commission"
                         else "Council", "reason": reason, "note": note})
            existing.add(key)
    for r in gaps:
        recent = r["date"] >= (datetime.date.fromisoformat(today)
                               - datetime.timedelta(days=45)).isoformat()
        reason = "pending_adoption" if recent else "no_minutes_posted"
        note = ("recent meeting; minutes likely not yet adopted"
                if recent else "no minutes document published on Granicus portal")
        key = (r["date"], r["name"], reason)
        if key not in existing:
            rows.append({"date": r["date"], "year": r["date"][:4], "title": r["name"],
                         "body": "PlanningCommission" if dataset == "planning_commission"
                         else "Council", "reason": reason, "note": note})
            existing.add(key)
    for r in (broken or []):
        reason = "doc_unretrievable"
        note = ("minutes doc listed on the portal but Granicus serves a non-PDF stub "
                "(~299 bytes) — the document itself is broken/empty on the host")
        key = (r["date"], r["name"], reason)
        if key not in existing:
            rows.append({"date": r["date"], "year": r["date"][:4], "title": r["name"],
                         "body": "PlanningCommission" if dataset == "planning_commission"
                         else "Council", "reason": reason, "note": note})
            existing.add(key)
    rows.sort(key=lambda x: (x["date"], x["title"]))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "year", "title", "body",
                                           "reason", "note"])
        w.writeheader()
        w.writerows(rows)
    return len([r for r in rows])


def fetch(dataset, items, broken=None):
    ds_dir = CITY_DIR / dataset
    # RESUMABILITY by DOC IDENTITY: an already-indexed source_url (which carries the unique
    # doc_id) means this exact document is on disk — skip it. This must be checked BEFORE
    # the same-date path-collision fallback, or a re-run would clip-suffix an already-
    # fetched doc into a duplicate file.
    prior = rl.load_index(ds_dir)
    have_urls = {r.get("source_url") for r in prior}
    have_paths = {r.get("path") for r in prior}
    index_rows, n = [], 0
    for it in items:
        if it["url"] in have_urls:
            continue                          # exact doc already fetched
        date, title, slug = it["date"], it["title"], it["slug"]
        rel = rl.minutes_rel_path(date, slug, "md", prefix="minutes")
        clipname = f"{date}_{slug}"
        # a GENUINE second meeting sharing date+slug (different doc) -> clip-suffixed name
        if rel in have_paths or (ds_dir / rel).exists() or any(r["path"] == rel
                                                               for r in index_rows):
            slug2 = f"{slug}-clip{it['clip_id']}"
            rel = rl.minutes_rel_path(date, slug2, "md", prefix="minutes")
            clipname = f"{date}_{slug2}"
        if rel in have_paths or (ds_dir / rel).exists():
            continue                          # resumable: already converted
        try:
            pdf = rl.http_get(it["url"], binary=True, ua=rl.BROWSER_UA, referer=LISTING)
        except Exception as e:                # transient network error
            print(f"  ERR  {date} {title}: {type(e).__name__} — retry later")
            continue
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date} {title}: {len(pdf)} bytes, not a PDF (broken Granicus doc)")
            if broken is not None:
                broken.append({"date": date, "name": title})
            continue
        raw = rl.save_raw(ds_dir, clipname + ".pdf", pdf)
        body_text = rl.pdf_to_text(raw)
        fmt = "text"
        if len(body_text.strip()) < 200:      # image-only PDF -> OCR fallback
            body_text = _ocr(raw)
            fmt = "ocr"
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(to_markdown(title, date, it["url"], fmt, body_text),
                       encoding="utf-8")
        index_rows.append({"date": date, "year": date[:4], "title": title, "slug": slug,
                           "path": rel, "source": "granicus", "source_url": it["url"],
                           "format": fmt})
        n += 1
        print(f"  fetched {rel} [{it['kind']}, {fmt}]")
    rl.append_index_rows(ds_dir, index_rows)
    return n


def _ocr(pdf_path):
    """Re-OCR a scanned image-only PDF (pdftoppm -r 300 + tesseract)."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(pdf_path),
                        str(Path(td) / "p")], check=True, timeout=600)
        parts = []
        for png in sorted(Path(td).glob("p*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            parts.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(parts)


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


def backfill(dataset):
    """Initial full acquisition (resumable): fetch every usable Minutes doc >= FLOOR,
    record honest gaps, then extract + validate."""
    pr = probe(dataset, None)
    print(f"\n=== backfill {dataset}: {len(pr['new_items'])} usable minutes docs to "
          f"consider (already-on-disk skipped) ===")
    broken = []
    n = fetch(dataset, pr["new_items"], broken=broken)
    _write_unrecovered(dataset, pr["_pending"], pr["_gaps"], broken=broken)
    print(f"fetched {n} new document(s) for {dataset}  (broken/unretrievable: {len(broken)})")
    post_fetch(dataset)
    return n


DATASETS = {
    name: {
        "portal": "granicus",
        "baseline": (lambda d=name: rl.index_max_date(CITY_DIR / d)),
        "probe": (lambda mx, d=name: probe(d, mx)),
        "fetch": (lambda items, d=name: fetch(d, items)),
        "post_fetch": (lambda d=name: post_fetch(d)),
    }
    for name in ("meeting_minutes", "planning_commission")
}

if __name__ == "__main__":
    if "--backfill" in sys.argv:
        which = None
        if "--dataset" in sys.argv:
            which = sys.argv[sys.argv.index("--dataset") + 1]
        for ds in ([which] if which else ["meeting_minutes", "planning_commission"]):
            backfill(ds)
    else:
        rl.run_cli(CITY_DIR, DATASETS, "Draper refresh (Granicus ViewPublisher)")
