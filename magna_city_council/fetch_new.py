#!/usr/bin/env python3
"""
fetch_new.py — incremental refresh probe for Magna City civic data.

Magna council minutes live on TWO portals and the PC on a third body:
  - CivicPlus AgendaCenter  : https://magna.utah.gov/AgendaCenter  (catID 3 = City Council;
                              the same Agenda Center also carries CRA meetings)  -> 2022+
  - Utah PMN body 5803      : https://www.utah.gov/pmn/sitemap/publicbody/5803.html  (Council)
                              -> township-era archive (2018-2021) + ongoing cross-check
  - Utah PMN body 1559      : https://www.utah.gov/pmn/sitemap/publicbody/1559.html  (Planning
                              Commission, MSD-staffed)

⚠ ALWAYS fetch PMN files from the `www.utah.gov/pmn/files/<id>.pdf` host — `pmn.utah.gov/...`
  302-redirects to the PMN home page and returns HTML, not the PDF.

Default action is a READ-ONLY probe: list documents newer than the current index max for each
dataset, excluding dates already indexed or logged in minutes_unrecovered.csv. `--fetch` (not
implemented here as a network-mutating step) would download new dates' minutes into raw/, convert
(OCR-aware) -> markdown -> minutes_index.csv, then run the dataset's extract_votes.py +
validate_votes.py. Rebuild db + motions_std + weeks afterward.

Usage:
  python3 fetch_new.py --probe        # default; read-only; prints candidate new documents
  python3 fetch_new.py --probe --json # machine-readable probe result
"""
import argparse, csv, json, os, re, sys, urllib.request
from datetime import date
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36 civic-data-archive/1.0")

# Shared refresh plumbing — used ONLY to emit the standard machine-readable probe
# JSON (<city>/refresh_probe.json) that scripts/refresh_status.py consumes; the
# stdout report below is unchanged. No fetching happens here.
sys.path.insert(0, os.path.join(HERE, os.pardir, "scripts"))
import refresh_lib as rl  # noqa: E402

PORTALS = {
    "meeting_minutes": {
        "civicplus": "https://magna.utah.gov/AgendaCenter",   # catID 3 (Council) + CRA
        "pmn_body": "5803",
        "pmn_url": "https://www.utah.gov/pmn/sitemap/publicbody/5803.html",
    },
    "planning_commission": {
        "civicplus": None,   # CivicPlus does not carry a Magna PC tab
        "pmn_body": "1559",
        "pmn_url": "https://www.utah.gov/pmn/sitemap/publicbody/1559.html",
    },
}
PMN_FILE = "https://www.utah.gov/pmn/files/{id}.pdf"   # www. host, never pmn.

# The standalone Community Reinvestment Agency (CRA) files on its OWN PMN body 6925
# (discovered 2026-07-14; NOT on CivicPlus). CRA minutes land in meeting_minutes as
# body=CRA (audited in-recess captures) + pmn_backfill (promoted standalone docs), so
# this body has no dataset folder of its own — probe it directly against the CRA dates
# already recorded across all_votes.csv / pmn_backfill/index.csv / pmn_exceptions.csv.
# Added 2026-07-17 (wave-2): fetch_new previously never probed 6925, so CRA-only gaps
# (e.g. the 2024-12-10 cancellation, 2026-05-12) were invisible to --probe.
PMN_CRA = {"body": "6925",
           "url": "https://www.utah.gov/pmn/sitemap/publicbody/6925.html"}


def _index_paths(dataset):
    """(max_date, {indexed dates}, {unrecovered dates})."""
    idx = os.path.join(HERE, dataset, "minutes_index.csv")
    unrec = os.path.join(HERE, dataset, "minutes_unrecovered.csv")
    dates, unrec_dates, mx = set(), set(), "0000-00-00"
    if os.path.exists(idx):
        for r in csv.DictReader(open(idx)):
            d = r.get("date", "")
            if d:
                dates.add(d)
                mx = max(mx, d)
    if os.path.exists(unrec):
        for r in csv.DictReader(open(unrec)):
            if r.get("date"):
                unrec_dates.add(r["date"])
    return mx, dates, unrec_dates


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "replace")


class _Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                self.links.append(href)


def _pmn_candidates(url, after_date):
    """Return PMN notice/file links whose visible date parses newer than after_date.
    Best-effort: PMN listing HTML pairs a date with each notice; we surface raw links so the
    operator can resolve the exact minutes file id."""
    try:
        html = _get(url)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "candidates": []}
    p = _Links(); p.feed(html)
    dates = sorted(set(re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", html)))
    newer = [d for d in dates if d > after_date and d <= date.today().isoformat()]
    notices = [l for l in p.links if "/pmn/sitemap/notice/" in l or "/pmn/files/" in l]
    return {"newer_dates_on_page": newer, "notice_links": notices[:40]}


def _cra_known_dates():
    """CRA meeting dates already accounted for (structured, promoted, or ledgered)."""
    dates = set()
    av = os.path.join(HERE, "meeting_minutes", "all_votes.csv")
    if os.path.exists(av):
        for r in csv.DictReader(open(av)):
            if r.get("body") == "CRA" and r.get("date"):
                dates.add(r["date"])
    idx = os.path.join(HERE, "pmn_backfill", "index.csv")
    if os.path.exists(idx):
        for r in csv.DictReader(open(idx)):
            if r.get("body") == "CRA" and r.get("date"):
                dates.add(r["date"])
    exc = os.path.join(HERE, "pmn_backfill", "pmn_exceptions.csv")
    if os.path.exists(exc):
        for r in csv.DictReader(open(exc)):
            if r.get("body_id") == PMN_CRA["body"] and r.get("date"):
                dates.add(r["date"])       # cancelled / draft / agenda-only, all handled
    return dates


def _cra_probe():
    """Surface PMN body-6925 (CRA) dates not yet in any CRA ledger."""
    known = _cra_known_dates()
    try:
        html = _get(PMN_CRA["url"])
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "known": len(known)}
    on_page = sorted(set(re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", html)))
    on_page += ["/".join(m) for m in []]  # (dates render as YYYY/MM/DD in listing rows)
    slash = sorted(set(re.findall(r"\b(20\d{2})/(\d{2})/(\d{2})\b", html)))
    norm = {f"{y}-{m}-{d}" for y, m, d in slash} | set(on_page)
    unknown = sorted(d for d in norm if d not in known and d <= date.today().isoformat())
    return {"body": PMN_CRA["body"], "known": len(known),
            "unknown_dates_on_page": unknown}


def probe():
    out = {}
    for ds, cfg in PORTALS.items():
        mx, indexed, unrec = _index_paths(ds)
        entry = {"index_max_date": mx, "indexed": len(indexed),
                 "unrecovered_logged": len(unrec), "pmn_body": cfg["pmn_body"]}
        entry["pmn"] = _pmn_candidates(cfg["pmn_url"], mx)
        if cfg["civicplus"]:
            try:
                html = _get(cfg["civicplus"])
                dts = sorted(set(re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", html)))
                entry["civicplus_newer_dates"] = [d for d in dts if d > mx]
            except Exception as e:
                entry["civicplus_error"] = f"{type(e).__name__}: {e}"
        else:
            entry["civicplus"] = "n/a (Magna PC has no CivicPlus tab; PMN 1559 only)"
        out[ds] = entry
    out["cra"] = _cra_probe()   # standalone CRA body 6925 (no dataset folder of its own)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="read-only: list new portal documents (default)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    result = probe()   # probe is the only implemented (read-only) action

    # Emit the standard machine-readable probe JSON for scripts/refresh_status.py
    # (the two core datasets; the standalone CRA body 6925 is folded into the
    # meeting_minutes notes since it has no dataset folder of its own).
    cra = result.get("cra", {})
    if "error" in cra:
        cra_note = f" | CRA body {cra.get('body', '6925')} probe error: {cra['error']}"
    elif cra.get("unknown_dates_on_page"):
        cra_note = (f" | CRA body {cra.get('body')} unhandled date(s): "
                    f"{', '.join(cra['unknown_dates_on_page'])} (cross-check — confirm at source)")
    else:
        cra_note = f" | CRA body {cra.get('body', '6925')}: no unhandled dates"
    for ds in ("meeting_minutes", "planning_commission"):
        e = result[ds]
        pmn = e.get("pmn", {})
        new_dates = sorted(set(e.get("civicplus_newer_dates") or [])
                           | set(pmn.get("newer_dates_on_page") or []))
        mx, nrows = rl.index_max_date(os.path.join(HERE, ds))
        note = f"PMN body {e.get('pmn_body')}"
        if ds == "meeting_minutes":
            note += " + CivicPlus catID 3"
        note += (f"; {len(new_dates)} newer portal date(s) (cross-check — open to confirm "
                 f"minutes vs agenda before ingesting)")
        if "error" in pmn:
            note += f"; PMN error: {pmn['error']}"
        if "civicplus_error" in e:
            note += f"; CivicPlus error: {e['civicplus_error']}"
        if ds == "meeting_minutes":
            note += cra_note
        rl.write_probe(HERE, ds, {
            "probe_date": rl.today(),
            "portal": "civicplus+pmn" if ds == "meeting_minutes" else "pmn",
            "index_max_date": mx, "index_rows": nrows, "status": "ok",
            "new_count": len(new_dates),
            "new_items": [{"date": d, "title": "Magna meeting", "url": ""}
                          for d in new_dates],
            "notes": note,
            "fetch_cmd": "download new dates' minutes to raw/ then extract (see docstring)",
        })

    if args.json:
        print(json.dumps(result, indent=2))
        return
    for ds, e in result.items():
        if ds == "cra":
            continue    # printed separately below (no dataset folder / index_max)
        print(f"\n=== {ds} === (index max {e['index_max_date']}, {e['indexed']} indexed, "
              f"{e['unrecovered_logged']} unrecovered logged)")
        cp = e.get("civicplus_newer_dates")
        if cp is not None:
            print(f"  CivicPlus catID 3 newer dates: {cp or 'none'}")
        elif "civicplus_error" in e:
            print(f"  CivicPlus: {e['civicplus_error']}")
        else:
            print(f"  CivicPlus: {e.get('civicplus')}")
        pmn = e["pmn"]
        if "error" in pmn:
            print(f"  PMN {e['pmn_body']}: {pmn['error']}")
        else:
            print(f"  PMN {e['pmn_body']} newer dates on page: {pmn['newer_dates_on_page'] or 'none'}")
    cra = result.get("cra", {})
    print(f"\n=== cra === (standalone PMN body {cra.get('body', PMN_CRA['body'])}, "
          f"{cra.get('known', 0)} CRA dates already ledgered)")
    if "error" in cra:
        print(f"  PMN {PMN_CRA['body']}: {cra['error']}")
    else:
        print(f"  PMN {cra.get('body')} unhandled dates on page: "
              f"{cra.get('unknown_dates_on_page') or 'none'}")
    print("\n(Read-only probe. To ingest a new date: download its minutes into raw/, convert "
          "OCR-aware -> markdown, append to minutes_index.csv, run extract_votes.py + "
          "validate_votes.py, then rebuild db + motions_std + weeks.)")


if __name__ == "__main__":
    main()
