#!/usr/bin/env python3
"""Superset verification for Kearns council (5823) + PC (1561).
Parse the cumulative notices-list HTML, collect every attachment whose type
label OR filename says 'Meeting Minutes'/'Minutes', derive the MEETING date from
the FILENAME (minutes attach to the next meeting's notice, so the notice event
date is wrong), and set-diff against the repo minutes_index dates.
GET-only; consumes files already fetched into work/.
"""
import re, sys, csv, datetime, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kearns_pmn_parse import parse_notices

def fname_date(fn):
    """Best-effort meeting date from a minutes filename. Returns ISO or None."""
    # MM-DD-YYYY
    m = re.search(r'(\d{2})-(\d{2})-(\d{4})', fn)
    if m:
        mo, d, y = m.groups(); return f"{y}-{mo}-{d}"
    # YYYY-MM-DD
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', fn)
    if m:
        y, mo, d = m.groups(); return f"{y}-{mo}-{d}"
    # YYMMDD_KearnsPC  (MSD PC convention)
    m = re.search(r'(?<!\d)(\d{2})(\d{2})(\d{2})[_ ]', fn)
    if m:
        yy, mo, d = m.groups(); return f"20{yy}-{mo}-{d}"
    # MM-DD-YY (township council)
    m = re.search(r'(?<!\d)(\d{2})-(\d{2})-(\d{2})(?!\d)', fn)
    if m:
        mo, d, yy = m.groups(); return f"20{yy}-{mo}-{d}"
    return None

def is_minutes(att):
    lab = att["label"].lower(); fn = att["filename"].lower()
    if "minute" not in (lab + " " + fn):
        return False
    # exclude cancellation notices that mention 'minutes' meeting in title? none do
    if "agenda" in fn and "minute" not in fn:
        return False
    return True

def collect(html_path):
    rows = parse_notices(html_path)
    dates = {}   # iso_date -> [filenames]
    for r in rows:
        for a in r["attachments"]:
            if is_minutes(a):
                dt = fname_date(a["filename"])
                if dt:
                    dates.setdefault(dt, []).append(a["filename"])
                else:
                    dates.setdefault("UNPARSED:"+a["filename"], []).append(r["notice_id"])
    return dates

def repo_dates(idx_csv):
    return set(row["date"] for row in csv.DictReader(open(idx_csv)))

if __name__ == "__main__":
    body = sys.argv[1]           # 'council' or 'pc'
    html_path = sys.argv[2]
    idx_csv = sys.argv[3]
    pmn = collect(html_path)
    repo = repo_dates(idx_csv)
    pmn_dates = set(d for d in pmn if not d.startswith("UNPARSED"))
    unparsed = {d: pmn[d] for d in pmn if d.startswith("UNPARSED")}
    print(f"== {body} ==")
    print(f"PMN minutes-labeled meeting dates: {len(pmn_dates)}")
    print(f"Repo minutes_index dates:          {len(repo)}")
    def near(d, s, tol=4):
        dd = datetime.date.fromisoformat(d)
        return any(abs((dd - datetime.date.fromisoformat(x)).days) <= tol for x in s)
    in_pmn_not_repo = sorted(d for d in pmn_dates if not near(d, repo))
    in_repo_not_pmn = sorted(d for d in repo if not near(d, pmn_dates))
    print(f"\nPMN minutes NOT in repo (±4d) [{len(in_pmn_not_repo)}]:")
    for d in in_pmn_not_repo:
        print("   ", d, pmn[d])
    print(f"\nRepo minutes NOT matched to a PMN minutes-labeled att (±4d) [{len(in_repo_not_pmn)}]:")
    for d in in_repo_not_pmn:
        print("   ", d)
    if unparsed:
        print(f"\nUnparsed minutes filenames [{len(unparsed)}]:")
        for k, v in unparsed.items():
            print("   ", k, v)
