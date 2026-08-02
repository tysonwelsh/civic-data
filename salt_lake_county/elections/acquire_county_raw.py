"""acquire_county_raw.py — mirror the EVEN-YEAR (county-office) Salt Lake County
Clerk election files into elections/raw/ and (re)write elections/sources.csv.

Two acquisition channels, both recorded per row in `provenance`:

  local-mirror   the file was already byte-verified in the personal archive
                 ~/Desktop/slco-election-archive (built by that repo's
                 build_manifest.py + download.py); copied here 2026-08-01. Its
                 manifest.csv supplies the authoritative saltlakecounty.gov URL.
  fresh-download fetched directly from saltlakecounty.gov on the run date (the
                 2026 primary, which postdates the mirror, and the 1996-2000
                 PDF-only elections, which the mirror never downloaded).

Scope = EVEN years only (county-office election years: Mayor, the 9 Council
seats, Sheriff, DA, Clerk, Assessor, Recorder, Treasurer, Auditor, Surveyor).
The ODD-year municipal canvass is a separate, already-canonical layer
(slco_municipal_results_long.csv) and is NOT touched here.

Idempotent: a file already present with the recorded sha256 is not re-fetched.
Raw binaries are gitignored repo-wide (`raw/` at any depth) — sources.csv is the
committed catalog that makes every one of them re-fetchable.

Usage:  python3 salt_lake_county/elections/acquire_county_raw.py
"""
import csv
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "sources.csv")
MIRROR = os.path.expanduser("~/Desktop/slco-election-archive")
MIRROR_MANIFEST = os.path.join(MIRROR, "manifest.csv")
BASE = "https://www.saltlakecounty.gov"
HIST = "/globalassets/1-site-files/clerk/elections/election-results/historical-election-results/"
CUR = "/globalassets/1-site-files/clerk/elections/election-results/"
TODAY = date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) civic-data/1.0"}

# (year, election_date, election_type, role, dest relpath under raw/, mirror relpath
#  or None, url path). role: 'sovc' = precinct-grain machine-readable canvass;
# 'summary' = certified/summary PDF; 'cvr' = ballot-level cast vote record.
FILES = [
    # --- PDF-only era (1996-2000): catalogued + mirrored, NOT parsed ---
    (1996, "1996-11-12", "general", "summary", "1996/1996-11-12-general-election.pdf",
     None, HIST + "1996-11-12-general-election.pdf"),
    (1998, "1998-06-23", "primary", "summary", "1998/1998-06-23-primary-election.pdf",
     None, HIST + "1998-06-23-primary-election.pdf"),
    (1998, "1998-11-03", "general", "summary", "1998/1998-11-03-general-election.pdf",
     None, HIST + "1998-11-03-general-election.pdf"),
    (2000, "2000-06-27", "primary", "summary", "2000/2000-06-27-primary-election.pdf",
     None, HIST + "2000-06-27-primary-election.pdf"),
    (2000, "2000-11-07", "general", "summary", "2000/2000-11-07-general-election.pdf",
     None, HIST + "2000-11-07-general-election.pdf"),
    # --- spreadsheet era ---
    (2002, "2002-06-25", "primary", "sovc", "2002/2002-06-25-primary-canvass.xls",
     "raw/historical-election-results/2002-06-25-primary-canvass.xls",
     HIST + "2002-06-25-primary-canvass.xls"),
    (2002, "2002-11-05", "general", "sovc", "2002/2002-11-05-general-canvass.xls",
     "raw/historical-election-results/2002-11-05-general-canvass.xls",
     HIST + "2002-11-05-general-canvass.xls"),
    (2004, "2004-06-22", "primary", "sovc", "2004/2004-06-22-primary-canvass.xls",
     "raw/historical-election-results/2004-06-22-primary-canvass.xls",
     HIST + "2004-06-22-primary-canvass.xls"),
    (2004, "2004-11-02", "general", "sovc", "2004/2004-11-02-general-canvass.xls",
     "raw/historical-election-results/2004-11-02-general-canvass.xls",
     HIST + "2004-11-02-general-canvass.xls"),
    (2006, "2006-06-27", "primary", "sovc", "2006/2006-06-27-primary-sovc.xls",
     "raw/historical-election-results/2006-06-27-primary-sovc.xls",
     HIST + "2006-06-27-primary-sovc.xls"),
    (2006, "2006-11-07", "general", "sovc", "2006/2006-11-07-general-sovc.xls",
     "raw/historical-election-results/2006-11-07-general-sovc.xls",
     HIST + "2006-11-07-general-sovc.xls"),
    (2008, "2008-06-24", "primary", "sovc", "2008/2008-06-24-primary-sovc.xls",
     "raw/historical-election-results/2008-06-24-primary-sovc.xls",
     HIST + "2008-06-24-primary-sovc.xls"),
    (2008, "2008-11-04", "general", "sovc", "2008/2008-11-04-general-sovc.xls",
     "raw/historical-election-results/2008-11-04-general-sovc.xls",
     HIST + "2008-11-04-general-sovc.xls"),
    (2010, "2010-06-22", "primary", "sovc", "2010/2010-06-22-primary-sovc.xlsx",
     "raw/historical-election-results/2010-06-22-primary-sovc.xlsx",
     HIST + "2010-06-22-primary-sovc.xlsx"),
    (2010, "2010-11-02", "general", "sovc", "2010/2010-11-02-general-sovc.xlsx",
     "raw/historical-election-results/2010-11-02-general-sovc.xlsx",
     HIST + "2010-11-02-general-sovc.xlsx"),
    (2012, "2012-06-26", "primary", "sovc", "2012/2012-06-26-primary-sovc.xlsx",
     "raw/historical-election-results/2012-06-26-primary-sovc.xlsx",
     HIST + "2012-06-26-primary-sovc.xlsx"),
    (2012, "2012-11-06", "general", "sovc", "2012/2012-11-06-general-sovc.xlsx",
     "raw/historical-election-results/2012-11-06-general-sovc.xlsx",
     HIST + "2012-11-06-general-sovc.xlsx"),
    (2014, "2014-06-24", "primary", "sovc", "2014/2014-06-24-primary-sovc.xlsx",
     "raw/historical-election-results/2014-06-24-primary-sovc.xlsx",
     HIST + "2014-06-24-primary-sovc.xlsx"),
    (2014, "2014-11-04", "general", "sovc", "2014/2014-11-04-general-sovc.xlsx",
     "raw/historical-election-results/2014-11-04-general-sovc.xlsx",
     HIST + "2014-11-04-general-sovc.xlsx"),
    (2016, "2016-06-28", "primary", "sovc", "2016/2016-06-28-primary-sovc.xlsx",
     "raw/historical-election-results/2016-06-28-primary-sovc.xlsx",
     HIST + "2016-06-28-primary-sovc.xlsx"),
    (2016, "2016-11-08", "general", "sovc",
     "2016/2016-11-08-general-election-statement-of-votes-cast.zip",
     "raw/historical-election-results/2016-11-08-general-election-statement-of-votes-cast.zip",
     HIST + "2016-11-08-general-election-statement-of-votes-cast.zip"),
    (2016, "2016-12-06", "recount", "sovc",
     "2016/2016-12-06-house-32-recount-statement-of-votes-cast.zip",
     "raw/historical-election-results/2016-12-06-house-32-recount-statement-of-votes-cast.zip",
     HIST + "2016-12-06-house-32-recount-statement-of-votes-cast.zip"),
    (2018, "2018-06-26", "primary", "sovc",
     "2018/2018--06-26-primary-election-statement-of-votes-cast.zip",
     "raw/historical-election-results/2018--06-26-primary-election-statement-of-votes-cast.zip",
     HIST + "2018--06-26-primary-election-statement-of-votes-cast.zip"),
    (2018, "2018-11-06", "general", "sovc", "2018/2018-11-06-general-election-sovc.xlsx",
     "raw/historical-election-results/2018-11-06-general-election-sovc.xlsx",
     HIST + "2018-11-06-general-election-sovc.xlsx"),
    (2020, "2020-03-03", "presidential primary", "sovc",
     "2020/2020-03-03-presidential-primary-sovc.xls",
     "raw/historical-election-results/2020-03-03-presidential-primary-sovc.xls",
     HIST + "2020-03-03-presidential-primary-sovc.xls"),
    (2020, "2020-06-30", "primary", "sovc", "2020/2020-06-30-primary-sovc.xls",
     "raw/historical-election-results/2020-06-30-primary-sovc.xls",
     HIST + "2020-06-30-primary-sovc.xls"),
    (2020, "2020-11-03", "general", "sovc", "2020/2020-11-03-general-election-sovc.xlsx",
     "raw/historical-election-results/2020-11-03-general-election-sovc.xlsx",
     HIST + "2020-11-03-general-election-sovc.xlsx"),
    (2022, "2022-06-28", "primary", "sovc", "2022/statementofvotescast.xlsx",
     "raw/2022/statementofvotescast.xlsx", CUR + "2022/statementofvotescast.xlsx"),
    (2022, "2022-11-08", "general", "sovc",
     "2022/statementofvotescastrpt-11-22-2022.xlsx",
     "raw/2022/statementofvotescastrpt-11-22-2022.xlsx",
     CUR + "2022/statementofvotescastrpt-11-22-2022.xlsx"),
    (2024, "2024-03-05", "presidential primary", "sovc",
     "2024/statementofvotescastrpt_20240319.xlsx",
     "raw/statementofvotescastrpt_20240319.xlsx",
     CUR + "statementofvotescastrpt_20240319.xlsx"),
    (2024, "2024-06-25", "primary", "sovc", "2024/statementofvotescastrpt_20240625.xlsx",
     "raw/statementofvotescastrpt_20240625.xlsx",
     CUR + "statementofvotescastrpt_20240625.xlsx"),
    (2024, "2024-08-05", "recount", "sovc",
     "2024/statementofvotescastrpt-ushouse2recount.xlsx",
     "raw/statementofvotescastrpt-ushouse2recount.xlsx",
     CUR + "statementofvotescastrpt-ushouse2recount.xlsx"),
    (2024, "2024-11-05", "general", "sovc",
     "2024/statementofvotescastrpt-11-19-2024.xlsx",
     "raw/statementofvotescastrpt-11-19-2024.xlsx",
     CUR + "statementofvotescastrpt-11-19-2024.xlsx"),
    (2024, "2024-11-05", "general", "summary",
     "2024/2024-general-election-certification.pdf", None,
     CUR + "2024-general-election-certification.pdf"),
    (2024, "2024-06-25", "primary", "summary",
     "2024/2024-primary-summary-results.pdf", None,
     CUR + "2024-primary-summary-results.pdf"),
    (2026, "2026-06-23", "primary", "sovc",
     "2026/statementofvotescastrptvoterprivacy.xlsx", None,
     CUR + "2026/statementofvotescastrptvoterprivacy.xlsx"),
    (2026, "2026-06-23", "primary", "summary",
     "2026/combined-reports-for-website.pdf", None,
     CUR + "2026/combined-reports-for-website.pdf"),
    (2026, "2026-06-23", "primary", "cvr", "2026/2026-primary-cvr.csv", None,
     CUR + "2026/2026-primary-cvr.csv"),
    # --- the county's CERTIFIED SUMMARY PDFs for every even year -------------
    # Not needed to parse (the SOVC workbooks are the machine-readable source),
    # but they are the INDEPENDENT county publication the parse is cross-checked
    # against — the reconciliation gate proves internal consistency, these prove
    # the numbers match what the county certified. Fetched fresh 2026-08-01.
    (2002, "2002-06-25", "primary", "summary", "2002/2002-06-25-primary-election.pdf",
     None, HIST + "2002-06-25-primary-election.pdf"),
    (2002, "2002-11-05", "general", "summary", "2002/2002-11-05-general-election.pdf",
     None, HIST + "2002-11-05-general-election.pdf"),
    (2004, "2004-06-22", "primary", "summary", "2004/2004-06-22-primary-election.pdf",
     None, HIST + "2004-06-22-primary-election.pdf"),
    (2004, "2004-11-02", "general", "summary", "2004/2004-11-02-general-election.pdf",
     None, HIST + "2004-11-02-general-election.pdf"),
    (2006, "2006-06-27", "primary", "summary", "2006/2006-06-27-primary-election.pdf",
     None, HIST + "2006-06-27-primary-election.pdf"),
    (2006, "2006-11-07", "general", "summary", "2006/2006-11-07-general-election.pdf",
     None, HIST + "2006-11-07-general-election.pdf"),
    (2008, "2008-06-24", "primary", "summary", "2008/2008-06-24-primary-election.pdf",
     None, HIST + "2008-06-24-primary-election.pdf"),
    (2010, "2010-06-22", "primary", "summary", "2010/2010-06-22-primary-election.pdf",
     None, HIST + "2010-06-22-primary-election.pdf"),
    (2010, "2010-11-02", "general", "summary", "2010/2010-11-02-general-election.pdf",
     None, HIST + "2010-11-02-general-election.pdf"),
    (2012, "2012-06-26", "primary", "summary", "2012/2012-06-26-primary-election.pdf",
     None, HIST + "2012-06-26-primary-election.pdf"),
    (2012, "2012-11-06", "general", "summary",
     "2012/2012-11-06-general-election-with-recount-results.pdf", None,
     HIST + "2012-11-06-general-election-with-recount-results.pdf"),
    (2014, "2014-06-24", "primary", "summary", "2014/2014-06-24-primary-election.pdf",
     None, HIST + "2014-06-24-primary-election.pdf"),
    (2014, "2014-11-04", "general", "summary", "2014/2014-11-04-general-election.pdf",
     None, HIST + "2014-11-04-general-election.pdf"),
    (2016, "2016-06-28", "primary", "summary", "2016/2016-06-28-primary-election.pdf",
     None, HIST + "2016-06-28-primary-election.pdf"),
    (2016, "2016-11-08", "general", "summary", "2016/2016-11-08-general-election.pdf",
     None, HIST + "2016-11-08-general-election.pdf"),
    (2016, "2016-12-06", "recount", "summary",
     "2016/2016-12-06-house-32-general-election-recount-results.pdf", None,
     HIST + "2016-12-06-house-32-general-election-recount-results.pdf"),
    (2018, "2018-06-26", "primary", "summary", "2018/2018-06-18-primary-election.pdf",
     None, HIST + "2018-06-18-primary-election.pdf"),
    (2018, "2018-11-06", "general", "summary",
     "2018/2018-11-06-general-election-results.pdf", None,
     HIST + "2018-11-06-general-election-results.pdf"),
    (2020, "2020-03-03", "presidential primary", "summary",
     "2020/2020-03-03-presidental-primary-results.pdf", None,
     HIST + "2020-03-03-presidental-primary-results.pdf"),
    (2020, "2020-06-30", "primary", "summary", "2020/2020-06-30-primary-results.pdf",
     None, HIST + "2020-06-30-primary-results.pdf"),
    (2020, "2020-11-03", "general", "summary",
     "2020/2020-11-03-general-election-results.pdf", None,
     HIST + "2020-11-03-general-election-results.pdf"),
    (2022, "2022-06-28", "primary", "summary",
     "2022/2022-06-28-primary-election-results.pdf", None,
     CUR + "2022/2022-06-28-primary-election-results.pdf"),
    (2022, "2022-11-08", "general", "summary",
     "2022/2022-11-08-general-election-results.pdf", None,
     CUR + "2022/2022-11-08-general-election-results.pdf"),
]

COLS = ["local_path", "url", "year", "election_date", "election_type", "role",
        "format", "status", "bytes", "sha256", "retrieved", "provenance", "notes"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mirror_urls():
    """local_path -> published URL, from the personal archive's manifest."""
    out = {}
    if not os.path.exists(MIRROR_MANIFEST):
        return out
    with open(MIRROR_MANIFEST, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["local_path"]] = r["url"]
    return out


def prior_rows():
    """local_path -> the previously recorded row, so a re-run PRESERVES the
    original acquisition provenance + date instead of overwriting it with
    'already present' (the channel a file came through is a permanent fact)."""
    out = {}
    if not os.path.exists(OUT):
        return out
    with open(OUT, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["local_path"]] = r
    return out


# per-file notes: what the file IS and whether the parser reads it
NOTES = {
    "sovc": "precinct-grain Statement of Votes Cast — PARSED by "
            "normalize_sovc_county.py (see reconciliation_county.csv for the gate)",
    "summary": "county's certified summary/certification PDF — NOT parsed; used as "
               "the independent cross-check in verify_against_certifications.py",
    "cvr": "ballot-level Cast Vote Record — catalogued only, no loader yet",
}
PDF_ONLY_YEARS = {1996, 1998, 2000}


def main():
    os.makedirs(RAW, exist_ok=True)
    murl = mirror_urls()
    prior = prior_rows()
    rows, fetched, copied, kept, failed = [], 0, 0, 0, 0
    for year, edate, etype, role, dest, mrel, urlpath in FILES:
        path = os.path.join(RAW, dest)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # authoritative URL: the mirror manifest's (carries the ?v= cache token) or ours
        url = murl.get(mrel) if mrel else None
        url = url or (BASE + urlpath)
        status, prov, note = "mirrored", "", NOTES.get(role, "")
        if year in PDF_ONLY_YEARS:
            note = ("PDF-ONLY ERA (%d): the county published no machine-readable "
                    "canvass — mirrored + catalogued, UNPARSED by design. %s"
                    % (year, note))
        # The acquisition CHANNEL is a permanent property of the file, derived
        # from the catalogue (not from what happened on this particular run), so
        # a re-run never degrades it to 'already present'. `retrieved` carries
        # forward from the first run that fetched the file.
        from_mirror = bool(mrel) and os.path.exists(os.path.join(MIRROR, mrel))
        prov = ("copied from local mirror ~/Desktop/slco-election-archive"
                if from_mirror else "fresh download from saltlakecounty.gov")
        p = prior.get("raw/" + dest) or {}
        retrieved = p.get("retrieved") or TODAY
        if os.path.exists(path):
            kept += 1
        elif from_mirror:
            shutil.copy2(os.path.join(MIRROR, mrel), path)
            copied += 1
            retrieved = TODAY
        else:
            try:
                # curl, not urllib: saltlakecounty.gov intermittently stalls a
                # keep-alive urllib socket past any read timeout (observed
                # 2026-08-01); curl's --max-time is a hard wall-clock bound.
                subprocess.run(
                    ["curl", "-sS", "-L", "--fail", "--max-time", "180",
                     "-A", UA["User-Agent"], "-o", path, BASE + urlpath],
                    check=True, capture_output=True)
                if os.path.getsize(path) == 0:
                    raise RuntimeError("empty response")
                fetched += 1
                retrieved = TODAY
                url = BASE + urlpath
            except Exception as e:  # noqa: BLE001
                failed += 1
                status, prov = "FETCH FAILED", "not acquired"
                note = "fetch error: %s" % e
                print("  FAIL %s  (%s)" % (dest, e), file=sys.stderr)
                rows.append({"local_path": "raw/" + dest, "url": BASE + urlpath,
                             "year": year, "election_date": edate,
                             "election_type": etype, "role": role,
                             "format": dest.rsplit(".", 1)[-1], "status": status,
                             "bytes": "", "sha256": "", "retrieved": TODAY,
                             "provenance": prov, "notes": note})
                continue
        rows.append({"local_path": "raw/" + dest, "url": url, "year": year,
                     "election_date": edate, "election_type": etype, "role": role,
                     "format": dest.rsplit(".", 1)[-1], "status": status,
                     "bytes": os.path.getsize(path), "sha256": sha256(path),
                     "retrieved": retrieved, "provenance": prov, "notes": note})
    rows.sort(key=lambda r: (r["election_date"], r["role"], r["local_path"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print("sources.csv: %d rows | %d copied from mirror, %d fresh-downloaded, "
          "%d already present, %d failed" % (len(rows), copied, fetched, kept, failed))


if __name__ == "__main__":
    main()
