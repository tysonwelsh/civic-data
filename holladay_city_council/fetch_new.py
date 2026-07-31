#!/usr/bin/env python3
"""
Holladay incremental refresh — Utah Public Notice (PMN) is the machine-readable
spine (recon.md §a; SOURCES.md). Both datasets live on one portal, two public
bodies (verified live 2026-07-12):

  meeting_minutes      Holladay City Council  (PMN public body **388**)
                       + in-session RDA / LBA sessions (SAME council docs — the
                       extractor re-tags body=RDA / body=LBA via a section walk,
                       so there is NOTHING extra to fetch for those bodies; a
                       standalone RDA "Board Meeting" doc also posts to body 388).
  planning_commission  Holladay Planning Commission (PMN public body **389**)

Portal pattern (utah.gov/pmn; every URL verified against the live site):
  * Public-body notice listing (the enumeration surface):
      https://www.utah.gov/pmn/sitemap/publicbody/<BODY>.html
    Each notice row carries a human meeting title + an event date/time and links
    to a per-notice page /pmn/sitemap/notice/<noticeId>.html.
  * Per-notice page lists the attachments (Agenda / Packet / **Meeting Minutes**),
    each a born-digital PDF at /pmn/files/<fileId>.pdf. The <fileId> is the
    trailing token in every on-disk filename and the source_url in the index.
  * ⚠ MINUTES LAG. PMN posts the agenda/packet BEFORE the meeting and the
    approved MINUTES weeks later (often attached to a LATER notice). So a forward
    probe keyed on the meeting date will surface a meeting whose minutes are not
    yet posted — that is the normal "pending" state (logged, never stubbed, in
    minutes_unrecovered.csv), NOT a fetch bug. --fetch only writes a doc when a
    real Meeting-Minutes attachment (recorded motion prose) is found.
  * ⚠ WRONG-FILE UPLOADS. The city has attached the WRONG minutes PDF to a notice
    at least once: PMN notice 990511 (Council 2025-05-01) carries a Meeting-Minutes
    attachment literally named "051525 CC Mtg.pdf" (file 1282121) that is
    BYTE-IDENTICAL to file 1282125, the 2025-05-15 minutes. Ingesting it created a
    phantom 2025-05-01 meeting that double-counted 3 motions (removed 2026-07-31;
    the true 05-01 minutes were recovered from SuiteOne mid=1156). The same defect
    class is logged for PC 2020-04-07 in pmn_backfill/unrecovered.csv. --fetch
    therefore HASHES every downloaded PDF and REFUSES to index one whose bytes
    already exist under another meeting date (see _known_pdf_hashes / _fetch).
  * ⚠ PC PMN GAP. Holladay posts PC minutes to PMN only intermittently — 2020,
    2021, and 2023 PC minutes were never posted as Meeting-Minutes attachments
    (89 honest gaps). A forward refresh cannot recover those; they would need the
    city Revize Document Center / SuiteOne portal (recon.md §b).

Modes (shared scripts/refresh_lib CLI):
  --probe  (default) list PMN notices with a meeting date newer than the index
           max per dataset; fetch nothing. Writes refresh_probe.json.
  --fetch  for each new notice, open its page, download a Meeting-Minutes PDF ->
           raw/, pdftotext -layout -> markdown (+ provenance header), append
           minutes_index.csv (+ fetch_log.csv), then run the dataset's
           extract_votes.py + validate_votes.py. Rebuild db / motions_std / weeks
           afterwards (the CLI prints the reminder).
  --dataset meeting_minutes|planning_commission  limit to one dataset.

Idempotent + resumable: a raw PDF / md already on disk is reused, and
append_index_rows skips any path already indexed; a relaunch only does the
outstanding work. Read-only GETs of public records throughout.
"""

import hashlib
import re
import sys
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

PMN = "https://www.utah.gov"
UA = rl.BROWSER_UA  # PMN serves fine to browser-like UAs; be a good citizen

# PMN public body ids (recon.md §a/§b; SOURCES.md). Verified live 2026-07-12.
BODY = {"meeting_minutes": "388", "planning_commission": "389"}
DEFAULT_TITLE = {"meeting_minutes": "City Council Meeting",
                 "planning_commission": "Planning Commission Meeting"}
DEFAULT_SLUG = {"meeting_minutes": "city-council-meeting",
                "planning_commission": "planning-commission"}

# A notice row on the public-body page: title, then an event date YYYY/MM/DD, and
# a link to /pmn/sitemap/notice/<id>.html. The public-body HTML is a simple table.
_NOTICE_RE = re.compile(
    r'/pmn/sitemap/notice/(\d+)\.html"[^>]*>(.*?)</a>.*?(\d{4})/(\d{2})/(\d{2})',
    re.I | re.S)
# Attachment links on a per-notice page: /pmn/files/<id>.pdf, often preceded by a
# label ("Meeting Minutes", "Agenda", "Agenda Packet", "Public Hearing", ...).
_FILE_RE = re.compile(r'/pmn/files/(\d+)\.pdf', re.I)
_MIN_LABEL_RE = re.compile(r'(minute)', re.I)


def _clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def _list_notices(dataset):
    """[(iso_date, title, notice_id)] from the public-body listing (newest first
    as the site orders them). Meeting-date keyed."""
    url = f"{PMN}/pmn/sitemap/publicbody/{BODY[dataset]}.html"
    html = rl.http_get(url, ua=UA)
    out = []
    for m in _NOTICE_RE.finditer(html):
        nid, title, y, mo, d = m.group(1), _clean(m.group(2)), m.group(3), m.group(4), m.group(5)
        out.append((f"{y}-{mo}-{d}", title or DEFAULT_TITLE[dataset], nid))
    return out, url


def _is_minutes_notice(title):
    """Skip pure hearing/quorum/candidate notices — we want the meeting itself.
    (A 'Public Hearing' or 'Notice of Potential Quorum' row is not a minutes
    source.)"""
    t = title.lower()
    if any(k in t for k in ("public hearing", "quorum", "candidate", "canvass notice")):
        return False
    return "meeting" in t or "council" in t or "commission" in t


def probe(dataset):
    def _probe(max_date):
        notices, endpoint = _list_notices(dataset)
        new = []
        for iso, title, nid in notices:
            if max_date and iso <= max_date:
                continue
            if not _is_minutes_notice(title):
                continue
            new.append({"date": iso, "title": title, "notice_id": nid,
                        "notice_url": f"{PMN}/pmn/sitemap/notice/{nid}.html"})
        new.sort(key=lambda r: r["date"])
        note = ("PMN posts minutes AFTER the meeting — a listed meeting whose "
                "notice has only an agenda/packet is 'pending', logged in "
                "minutes_unrecovered.csv, not fetched.")
        if dataset == "planning_commission":
            note += (" PC PMN coverage is intermittent (no 2020/2021/2023 minutes "
                     "on PMN — city Revize/SuiteOne would be needed).")
        return {"new_items": new, "endpoint": endpoint, "notes": note}
    return _probe


def _minutes_pdf_id(notice_url):
    """Open a notice page, return the fileId of its Meeting-Minutes attachment, or
    None if only an agenda/packet is posted (=> minutes pending)."""
    html = rl.http_get(notice_url, ua=UA)
    # Prefer a link whose nearby label mentions "minute"; else, if the notice has
    # a single attachment and the notice title itself says minutes, take it.
    best = None
    for m in _FILE_RE.finditer(html):
        window = html[max(0, m.start() - 160):m.start() + 40]
        if _MIN_LABEL_RE.search(window):
            best = m.group(1)
            break
    return best


def _date_of_raw(p):
    """Meeting date encoded in a raw/ filename (raw names are <iso>_<slug>_<tok>.pdf)."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", p.name)
    return m.group(1) if m else ""


def _known_pdf_hashes(dataset_dir):
    """{sha256: meeting_date} for every raw PDF already on disk for this dataset.

    Guards the WRONG-FILE-UPLOAD defect (module docstring): the city has attached one
    meeting's minutes PDF to another meeting's PMN notice, which — since the date comes
    from the NOTICE and the content from the ATTACHMENT — silently mints a phantom
    meeting whose motions double-count. Byte identity is the cheapest sound test.
    """
    out = {}
    for p in sorted((dataset_dir / "raw").glob("*.pdf")):
        out.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), _date_of_raw(p))
    return out


def fetch(dataset):
    dataset_dir = CITY_DIR / dataset

    def _fetch(new_items):
        n = 0
        seen = _known_pdf_hashes(dataset_dir)
        for it in new_items:
            fid = _minutes_pdf_id(it["notice_url"])
            if not fid:
                print(f"    pending (no minutes attachment yet): {it['date']} {it['title']}")
                continue
            iso, slug = it["date"], DEFAULT_SLUG[dataset]
            fname = f"{iso}_{slug}_{fid}.pdf"
            pdf_url = f"{PMN}/pmn/files/{fid}.pdf"
            raw = dataset_dir / "raw" / fname
            if not raw.exists():
                body = rl.http_get(pdf_url, binary=True, ua=UA)
                digest = hashlib.sha256(body).hexdigest()
                other = seen.get(digest)
                if other and other != iso:
                    # Same bytes already indexed under a DIFFERENT meeting date =>
                    # the notice carries the wrong attachment. Refuse to index; a
                    # phantom meeting is worse than a logged gap (cardinal rule 1).
                    print(f"    ⚠ WRONG-FILE UPLOAD, NOT INDEXED: {iso} {it['title']} — "
                          f"{pdf_url} is byte-identical to the already-indexed {other} "
                          f"minutes. Log {iso} in minutes_unrecovered.csv, or recover the "
                          f"true minutes from the city SuiteOne portal "
                          f"(holladayut.suiteonemedia.com, /event/GetMinutesFile/"
                          f"Minutes?mid=<mid>) as was done for 2025-05-01 on 2026-07-31.")
                    continue
                rl.save_raw(dataset_dir, fname, body)
                seen.setdefault(digest, iso)
            else:
                seen.setdefault(hashlib.sha256(raw.read_bytes()).hexdigest(), iso)
            text = rl.pdf_to_text(raw)
            rel = rl.minutes_rel_path(iso, f"{slug}_{fid}", ext="md", prefix="minutes")
            md = dataset_dir / rel
            md.parent.mkdir(parents=True, exist_ok=True)
            header = (f"<!-- source: PMN body {BODY[dataset]} · {pdf_url} · "
                      f"retrieved {rl.today()} -->\n\n")
            md.write_text(header + text, encoding="utf-8")
            rl.append_index_rows(dataset_dir, [{
                "date": iso, "year": iso[:4], "title": it["title"], "slug": slug,
                "path": rel, "source": "pmn", "source_url": pdf_url,
                "format": "pdf-text",
                "body": "Council" if dataset == "meeting_minutes" else "PlanningCommission",
            }])
            n += 1
            print(f"    fetched minutes: {iso} -> {rel}")
        return n
    return _fetch


def post_fetch(dataset):
    def _post():
        d = CITY_DIR / dataset
        rl.run_pipeline_step(["python3", "extract_votes.py"], d, "extract_votes")
        rl.run_pipeline_step(["python3", "validate_votes.py"], d, "validate_votes")
        print("\n>>> Rebuild derived layers after a fetch:")
        print("    python3 db/build_db.py && python3 db/build_referrals.py")
        print("    python3 build_weeks.py")
        print("    (then re-run scripts/build_cities_db.py at the repo root to re-federate)")
    return _post


DATASETS = {
    ds: {"portal": f"pmn/body-{BODY[ds]}",
         "baseline": (lambda d=ds: rl.index_max_date(CITY_DIR / d)),
         "probe": probe(ds), "fetch": fetch(ds), "post_fetch": post_fetch(ds)}
    for ds in ("meeting_minutes", "planning_commission")
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Holladay refresh (Utah Public Notice bodies 388/389)")
