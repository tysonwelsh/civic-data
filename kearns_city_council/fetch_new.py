#!/usr/bin/env python3
"""
Kearns incremental refresh — Utah Public Notice (PMN) probe.

The city site (kearns.utah.gov) is a Cloudflare-blocked custom CMS and is NOT
scrapable; **Utah PMN is the canonical acquisition source** for this repo:

  meeting_minutes      City Council           PMN public body 5823
  planning_commission  Planning Commission    PMN public body 1561  (MSD-staffed)

Portal facts (recon.md; re-verified 2026-07-12):
  * Body page:   https://www.utah.gov/pmn/sitemap/publicbody/<bodyId>.html
                 — shows only the ~10-11 most RECENT notices (no pagination /
                 archive link). Older notices are reachable only via
                 https://www.utah.gov/pmn/search.html or by known notice id.
  * Notice page: https://www.utah.gov/pmn/sitemap/notice/<noticeId>.html
  * Files:       https://www.utah.gov/pmn/files/<fileId>.pdf  (also .docx for
                 2017-era council minutes)
  * Each notice carries an Agenda ("Other"), a "Meeting Minutes" attachment
    (posted weeks later, usually on the NEXT meeting's notice), and an MP3.
    Minutes filenames: council "MM-DD-YYYY Kearns CC Meeting Minutes ...pdf" or
    "MMDDYY.docx"/"MM-DD-YY.pdf"; PC "YYMMDD_KearnsPC_MinutesApproved.pdf".
  * PMN serves clean-text PDFs to a plain browser UA (no Cloudflare challenge).

WHAT THIS DOES (read-only probe; does not mutate the repo):
  1. For each body, GET the body page, extract recent notice ids.
  2. GET each notice; find its "Meeting Minutes" file link(s).
  3. Compare against the dataset's minutes_index.csv `source_url`s and its
     minutes_unrecovered.csv. Print, per body:
       - NEW minutes not yet on disk (candidates to fetch)
       - notices with only agenda/audio (nothing to fetch yet)
  4. Surface the KNOWN 2017-2023 COUNCIL BACK-CATALOG: every council notice in
     minutes_unrecovered.csv was found (2026-07-12 audit) to carry a "Meeting
     Minutes" attachment on PMN — i.e. it is HARVESTABLE, not absent. This probe
     re-flags that backlog so a refresh does not treat it as an honest gap.

Usage:
  python3 fetch_new.py              # probe both bodies, print a report
  python3 fetch_new.py --body 5823  # one body only
No downloads are performed; acquisition + carving is a separate, reviewed step.
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
    "5823": ("meeting_minutes", "City Council"),
    "1561": ("planning_commission", "Planning Commission"),
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def notice_ids(body_id):
    """Recent notice ids linked from a body page (dedup, keep order)."""
    html = get(f"{PMN}/sitemap/publicbody/{body_id}.html")
    ids, seen = [], set()
    for m in re.finditer(r"/pmn/sitemap/notice/(\d+)\.html", html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            ids.append(m.group(1))
    return ids


def minutes_files(notice_id):
    """(fileId, filename) pairs whose PMN category is Meeting Minutes.

    The notice page renders each attachment near its category label; we take any
    /pmn/files/<id>.<ext> link that sits close to the words 'Meeting Minutes'.
    Falls back to filename heuristics for minutes-looking names.
    """
    html = get(f"{PMN}/sitemap/notice/{notice_id}.html")
    out = []
    for m in re.finditer(r"/pmn/files/(\d+)\.(pdf|docx?|PDF|DOCX?)", html):
        fid = m.group(1)
        window = html[max(0, m.start() - 400): m.end() + 400]
        name = ""
        nm = re.search(r'>([^<>]*\.(?:pdf|docx?))<', window, re.I)
        if nm:
            name = nm.group(1).strip()
        is_min = ("Meeting Minutes" in window) or bool(
            re.search(r"minutes", name, re.I)) or bool(
            re.search(r"KearnsPC_MinutesApproved", window))
        is_agenda = re.search(r"agenda", name, re.I) and "Meeting Minutes" not in window
        if is_min and not is_agenda:
            out.append((fid, name or f"{fid}.pdf"))
    return out


def indexed_urls(dataset):
    p = os.path.join(HERE, dataset, "minutes_index.csv")
    urls = set()
    if os.path.exists(p):
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("source_url"):
                    urls.add(row["source_url"].strip())
    return urls


def indexed_dates(dataset):
    p = os.path.join(HERE, dataset, "minutes_index.csv")
    dates = set()
    if os.path.exists(p):
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("date"):
                    dates.add(row["date"].strip())
    return dates


def filename_date(name):
    """Extract an ISO meeting date from a PMN minutes filename, or ''.

    Council: 'MM-DD-YYYY ...' or 'MMDDYY.docx'/'MM-DD-YY.pdf'.
    PC:      'YYMMDD_KearnsPC_MinutesApproved.pdf'.
    """
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", name)          # MM-DD-YYYY
    if m:
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = re.match(r"(\d{2})(\d{2})(\d{2})_KearnsPC", name)     # YYMMDD_ (PC)
    if m:
        return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"(\d{2})-?(\d{2})-?(\d{2})\.", name)        # MM-DD-YY / MMDDYY
    if m:
        return f"20{m.group(3)}-{m.group(1)}-{m.group(2)}"
    return ""


def unrecovered_rows(dataset):
    p = os.path.join(HERE, dataset, "minutes_unrecovered.csv")
    rows = []
    if os.path.exists(p):
        with open(p, newline="") as f:
            rows = list(csv.DictReader(f))
    return rows


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
    have = indexed_urls(dataset)
    have_dates = indexed_dates(dataset)
    try:
        nids = notice_ids(body_id)
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not read body page: {e}")
        _write_probe_json(dataset, "fail", None,
                          f"PMN body {body_id} body page unreadable: {type(e).__name__}: {e}")
        return
    print(f"  {len(nids)} recent notices on the body page; "
          f"{len(have)} minutes already indexed on disk.")
    new = []
    for nid in nids:
        try:
            mins = minutes_files(nid)
        except Exception as e:  # noqa: BLE001
            print(f"  ! notice {nid}: {e}")
            continue
        for fid, name in mins:
            url = f"{PMN}/files/{fid}.pdf"
            d = filename_date(name)
            known = (url in have or f"{PMN}/files/{fid}.docx" in have
                     or (d and d in have_dates))
            if not known:
                new.append((nid, fid, name, d or "?"))
    if new:
        print(f"  NEW minutes to fetch ({len(new)}):")
        for nid, fid, name, d in new:
            print(f"    {d}  notice {nid} -> files/{fid}  ({name})")
    else:
        print("  No new minutes among the recent notices "
              "(all recent meeting dates already on disk).")
    _write_probe_json(
        dataset, "ok",
        [{"date": d, "title": label, "url": f"{PMN}/files/{fid}.pdf"}
         for nid, fid, name, d in new],
        f"PMN body {body_id}: {len(nids)} recent notices; {len(new)} new minutes lead(s). "
        f"Back-catalog / acquisition detail in stdout.")

    unrec = unrecovered_rows(dataset)
    if dataset == "meeting_minutes":
        pre = [r for r in unrec if r.get("year", "") and r["year"] <= "2023"]
        if pre:
            print(f"  ** BACK-CATALOG (fix-first): {len(pre)} township council "
                  f"meetings 2017-2023 are logged 'unrecovered' but the 2026-07-12 "
                  f"audit found each PMN notice DOES carry a 'Meeting Minutes' "
                  f"attachment -> HARVESTABLE, not absent. Harvest their notice ids "
                  f"from minutes_unrecovered.csv (source_url column).")


def main():
    args = sys.argv[1:]
    if "--body" in args:
        b = args[args.index("--body") + 1]
        probe(b)
    else:
        for b in BODIES:
            probe(b)
    print("\nProbe complete. Downloads/carving are a separate reviewed step "
          "(see recon.md + the build-city-data skill).")


if __name__ == "__main__":
    main()
