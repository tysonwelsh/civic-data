#!/usr/bin/env python3
"""
Emigration Canyon incremental refresh — Utah Public Notice (PMN) probe.

There is **no city document CMS**. Utah PMN is the canonical acquisition source:

  meeting_minutes      City / Metro Township Council   PMN public body 5809
  planning_commission  Planning Commission             PMN public body 1562  (MSD-staffed)

Portal facts (recon.md; re-verified 2026-07-12):
  * Recent-notice list: https://www.utah.gov/pmn/list/notices.html?id=<bodyId>&page=N
      - the **&page=N form is required** (the bare ?id= endpoint intermittently 500s
        "Technical Difficulties"). The list shows notices upcoming or in the past ~6
        months; walk page 0,1,2,... until the notice-id set stops growing.
      - Sitemap fallback (stable, recent only):
        https://www.utah.gov/pmn/sitemap/publicbody/<bodyId>.html
  * Notice page:  https://www.utah.gov/pmn/sitemap/notice/<noticeId>.html
  * File store:   https://www.utah.gov/pmn/files/<fileId>.pdf   (audio: .MP3)
      - fileIds are non-sequential / non-guessable — harvest the labeled links off each
        notice; do NOT synthesize ids.
  * PMN serves clean born-digital (DocuSign) PDFs to a plain browser UA.

⚠ VERIFIED-PURGED BACK-CATALOG (do NOT re-flag as recoverable — this is the OPPOSITE of the
  Kearns false gap). Recovered coverage begins **2018-10-25** (council) / **2018-11-15** (PC).
  The pre-2018-10 minutes (2017 + scattered 2018-19) were **published** but their PMN file
  blob is **purged**: every /pmn/files/<id> for those meetings returns a 315-byte 404 (tested
  2026-07-12: 406463, 391513, 269375, 362997 all 404), while 2018-10+ files download 200. The
  purge boundary is file-id ≈ 450000 (~July 2018) — a collection-wide PMN file-rot trait also
  documented for Kearns. Those meetings live in minutes_unrecovered.csv as an HONEST gap; the
  MSD AgendaCenter secondary mirror is the only backfill avenue. This probe re-asserts that
  they are purged so a refresh never mistakes them for a missed harvest.

WHAT THIS DOES (read-only probe; does not mutate the repo):
  1. For each body, walk the paginated notices list (sitemap fallback), collect notice ids.
  2. GET each notice; find its "Meeting Minutes" attachment file link(s).
  3. Compare against the dataset's minutes_index.csv (source_url + date + pmn_notice_id)
     and minutes_unrecovered.csv (pmn_notice_id). Print, per body:
       - NEW minutes not yet on disk (candidates to fetch)
       - notices with only agenda/audio (nothing to fetch yet)
No downloads are performed; acquisition + carving is a separate, reviewed step.

DEDUP FIX (2026-07-19, Q3 refresh — read-only semantics preserved):
  A single PMN notice for EC bundles MANY attachments — the agenda plus the PRIOR
  meetings' approved minutes, and the SAME minutes doc is frequently re-uploaded under a
  second, unrelated fileId (verified: notice 743839 links both the recorded minutes fid
  827423 *and* a duplicate "Meeting Minutes" fid 827715 with no date in its filename).
  The old dedup keyed ONLY on (source_url fileId) OR a date parsed from the FILENAME, so
  every such duplicate/re-upload whose filename lacked a parseable date (printed date "?")
  was wrongly flagged NEW — the probe over-claimed 42 council / 47 PC "new" minutes when
  EC's coverage was in fact complete (diagnosed against minutes_index.csv +
  minutes_unrecovered.csv; 0 were genuinely new).
  The index already carries the true meeting identity in `pmn_notice_id`, and notices are
  reused across meetings (one notice → up to 3 index rows). The fix DEDUPES BY NOTICE
  DISPOSITION: a notice whose id already appears in minutes_index.csv (harvested) OR in
  minutes_unrecovered.csv (reviewed → honest gap) has been fully dispositioned, so none of
  its attachments are "new" — skip the whole notice. A genuinely-new meeting arrives on a
  never-before-seen notice id, which is still surfaced. The url/filename-date checks are
  retained as belt-and-suspenders (and filename_date now also parses MM-DD-YY). Late-posted
  minutes ON AN ALREADY-DISPOSITIONED date are the dedicated job of scripts/pmn_crosscheck.py
  (date-based, report-only), not this probe.

Usage:
  python3 fetch_new.py                # probe both bodies, print a report
  python3 fetch_new.py --body 5809    # one body only
"""
import csv
import os
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive")
HERE = os.path.dirname(os.path.abspath(__file__))
PMN = "https://www.utah.gov/pmn"

# Shared refresh plumbing — used ONLY to emit the standard machine-readable probe
# JSON (<city>/refresh_probe.json) that scripts/refresh_status.py consumes; the
# stdout report below is unchanged. No fetching happens here.
sys.path.insert(0, os.path.join(HERE, os.pardir, "scripts"))
import refresh_lib as rl  # noqa: E402

BODIES = {
    "5809": ("meeting_minutes", "City / Metro Township Council"),
    "1562": ("planning_commission", "Planning Commission"),
}

# The verified purge boundary — file ids below this were 404 on 2026-07-12.
PURGE_FILE_ID_CEILING = 450000
EARLIEST_RECOVERED = {"meeting_minutes": "2018-10-25", "planning_commission": "2018-11-15"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def notice_ids(body_id):
    """All notice ids from the paginated list (sitemap fallback), dedup, keep order."""
    ids, seen = [], set()
    # Paginated list — the &page=N form; walk until the id set stops growing.
    try:
        page, stale = 0, 0
        while page < 60 and stale < 2:
            html = get(f"{PMN}/list/notices.html?id={body_id}&page={page}")
            before = len(seen)
            for m in re.finditer(r"/pmn/sitemap/notice/(\d+)\.html", html):
                if m.group(1) not in seen:
                    seen.add(m.group(1))
                    ids.append(m.group(1))
            stale = stale + 1 if len(seen) == before else 0
            page += 1
    except Exception as e:  # noqa: BLE001
        print(f"  ! paginated list unavailable ({e}); falling back to sitemap page")
    if not ids:
        html = get(f"{PMN}/sitemap/publicbody/{body_id}.html")
        for m in re.finditer(r"/pmn/sitemap/notice/(\d+)\.html", html):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                ids.append(m.group(1))
    return ids


def minutes_files(notice_id):
    """(fileId, filename) pairs whose PMN category/label is Meeting Minutes."""
    html = get(f"{PMN}/sitemap/notice/{notice_id}.html")
    out = []
    for m in re.finditer(r"/pmn/files/(\d+)\.(pdf|docx?|PDF|DOCX?)", html):
        fid = m.group(1)
        window = html[max(0, m.start() - 400): m.end() + 400]
        name = ""
        nm = re.search(r'>([^<>]*\.(?:pdf|docx?))<', window, re.I)
        if nm:
            name = nm.group(1).strip()
        is_min = ("Meeting Minutes" in window) or bool(re.search(r"minutes", name, re.I))
        is_cancel = bool(re.search(r"cancel", name + window, re.I))
        is_agenda = bool(re.search(r"agenda", name, re.I)) and "Meeting Minutes" not in window
        if is_min and not is_agenda and not is_cancel:
            out.append((fid, name or f"{fid}.pdf"))
    return out


def _col(dataset, col):
    p = os.path.join(HERE, dataset, "minutes_index.csv")
    vals = set()
    if os.path.exists(p):
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                if row.get(col):
                    vals.add(row[col].strip())
    return vals


def filename_date(name):
    """Best-effort ISO meeting date from a PMN minutes filename, or ''."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)              # YYYY-MM-DD
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", name)              # MM-DD-YYYY
    if m:
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = re.search(r"\b(\d{2})-(\d{2})-(\d{2})\b", name)          # MM-DD-YY (EC city era)
    if m:
        return f"20{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = re.match(r"(\d{2})(\d{2})(\d{2})_", name)                # YYMMDD_ (PC style)
    if m:
        return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def _unrecovered_notice_ids(dataset):
    """pmn_notice_id set from minutes_unrecovered.csv (dispositioned honest gaps)."""
    p = os.path.join(HERE, dataset, "minutes_unrecovered.csv")
    vals = set()
    if os.path.exists(p):
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("pmn_notice_id"):
                    vals.add(row["pmn_notice_id"].strip())
    return vals


def _write_probe_json(dataset, status, new_items, note, portal="pmn"):
    """Emit the standard probe shape scripts/refresh_status.py consumes."""
    mx, nrows = rl.index_max_date(os.path.join(HERE, dataset))
    rl.write_probe(HERE, dataset, {
        "probe_date": rl.today(), "portal": portal,
        "index_max_date": mx, "index_rows": nrows, "status": status,
        "new_count": (len(new_items) if new_items is not None else None),
        "new_items": new_items or [],
        "notes": note,
        "fetch_cmd": "acquisition is a separate reviewed step (see recon.md)",
    })


def probe(body_id):
    dataset, label = BODIES[body_id]
    print(f"\n=== {label}  (PMN body {body_id} -> {dataset}/) ===")
    have_urls = _col(dataset, "source_url")
    have_dates = _col(dataset, "date")
    # Notice-disposition dedup (2026-07-19 fix): a notice already harvested (its id is in
    # minutes_index.csv) or already reviewed as an honest gap (its id is in
    # minutes_unrecovered.csv) is fully dispositioned — none of its bundled/re-uploaded
    # attachments are new. See the module docstring.
    done_notices = _col(dataset, "pmn_notice_id") | _unrecovered_notice_ids(dataset)
    try:
        nids = notice_ids(body_id)
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not read notices: {e}")
        _write_probe_json(dataset, "fail", None,
                          f"PMN body {body_id} notices unreadable: {type(e).__name__}: {e}")
        return
    print(f"  {len(nids)} notices enumerated; {len(have_urls)} minutes already on disk "
          f"(coverage begins {EARLIEST_RECOVERED[dataset]}).")
    new = []
    for nid in nids:
        if nid in done_notices:
            # Already harvested or reviewed-as-gap — its attachments are dispositioned.
            continue
        try:
            mins = minutes_files(nid)
        except Exception as e:  # noqa: BLE001
            print(f"  ! notice {nid}: {e}")
            continue
        for fid, name in mins:
            url = f"{PMN}/files/{fid}.pdf"
            d = filename_date(name)
            known = (url in have_urls
                     or f"{PMN}/files/{fid}.docx" in have_urls
                     or (d and d in have_dates))
            if known:
                continue
            if int(fid) < PURGE_FILE_ID_CEILING:
                # A verified-purged-era file id: the blob is 404 — do NOT queue it.
                continue
            new.append((nid, fid, name, d or "?"))
    if new:
        print(f"  NEW minutes to fetch ({len(new)}):")
        for nid, fid, name, d in new:
            print(f"    {d}  notice {nid} -> files/{fid}  ({name})")
    else:
        print("  No new minutes among the enumerated notices "
              "(all recent meeting dates already on disk).")
    print(f"  (pre-{EARLIEST_RECOVERED[dataset]} is VERIFIED-PURGED on PMN — honest gap in "
          f"minutes_unrecovered.csv; backfill only via the MSD AgendaCenter mirror.)")
    _write_probe_json(
        dataset, "ok",
        [{"date": d, "title": label, "url": f"{PMN}/files/{fid}.pdf"}
         for nid, fid, name, d in new],
        f"PMN body {body_id}: {len(nids)} notices enumerated; {len(new)} new minutes lead(s) "
        f"(coverage begins {EARLIEST_RECOVERED[dataset]}; pre-floor is verified-purged).")


def main():
    args = sys.argv[1:]
    if "--body" in args:
        probe(args[args.index("--body") + 1])
    else:
        for b in BODIES:
            probe(b)
    print("\nProbe complete. Downloads/carving are a separate reviewed step "
          "(see recon.md + the build-city-data skill).")


if __name__ == "__main__":
    main()
