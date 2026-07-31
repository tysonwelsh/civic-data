#!/usr/bin/env python3
"""Magna PMN backfill — per-date set-difference of PMN minutes vs the audited repo.

Reads work/parsed_<body>.json (from magna_pmn_crawl.py), detects MINUTES attachments
by FILENAME (not the unreliable PMN type label), extracts each minutes' MEETING date
from the filename, and diffs against the repo minutes indexes (±tolerance).

Bodies:  5803 Council, 6925 CRA -> meeting_minutes/minutes_index.csv (body col)
         1559 PlanningCommission -> planning_commission/minutes_index.csv
Prints, per body: PMN minutes dates, repo dates, MISSING (on PMN, not repo),
and repo-only. Also lists the missing dates' file ids for fetching.
"""
import csv, json, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
CITY = os.path.abspath(os.path.join(HERE, ".."))
TOL = 4  # days

def load_repo_dates(index_path, body_filter=None):
    dates = {}
    with open(index_path, newline="") as f:
        for r in csv.DictReader(f):
            if body_filter and r.get("body") != body_filter:
                continue
            dates[r["date"]] = r
    return dates

def is_minutes(fn):
    low = fn.lower()
    if "minute" not in low:
        return False
    if "no minutes" in low or "no minute " in low:
        return False
    if low.strip().startswith("agenda") or "agenda with supporting" in low:
        return False
    if "cancel" in low:
        return False
    return True

def meeting_date_from_filename(fn, notice_dt):
    # prefer an explicit MM-DD-YYYY or M-D-YYYY at the start of the filename
    m = re.search(r'(\d{1,2})[-_/](\d{1,2})[-_/](20\d{2})', fn)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(yr, mo, da).isoformat()
        except ValueError:
            pass
    # YYYY-MM-DD or YYYYMMDD
    m = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', fn)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
    # MM-DD-YY (2-digit year, plausible 15..26) e.g. '08-01-17 Meeting Minutes.pdf'
    m = re.search(r'\b(\d{1,2})[-_/](\d{1,2})[-_/](1[5-9]|2[0-6])\b', fn)
    if m:
        mo, da, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(2000 + yy, mo, da).isoformat()
        except ValueError:
            pass
    if notice_dt:
        return notice_dt[:10].replace("/", "-")
    return ""

def pmn_minutes(body):
    with open(os.path.join(WORK, f"parsed_{body}.json")) as f:
        notices = json.load(f)
    # date -> list of {file_id,ext,filename,notice_id,approved/draft}
    byd = {}
    for n in notices:
        for a in n["attachments"]:
            if not is_minutes(a["filename"]):
                continue
            d = meeting_date_from_filename(a["filename"], n["meeting_dt"])
            if not d:
                continue
            rec = dict(a, notice_id=n["notice_id"], notice_dt=n["meeting_dt"],
                       approved="approved" in a["filename"].lower(),
                       draft="draft" in a["filename"].lower())
            byd.setdefault(d, []).append(rec)
    return byd

def near(d, repo_dates):
    dd = datetime.date.fromisoformat(d)
    for rd in repo_dates:
        try:
            if abs((datetime.date.fromisoformat(rd) - dd).days) <= TOL:
                return rd
        except ValueError:
            continue
    return None

def report(label, body, repo_dates):
    byd = pmn_minutes(body)
    print(f"\n===== {label} (body {body}) =====")
    print(f"PMN minutes meeting-dates: {len(byd)}   repo dates: {len(repo_dates)}")
    missing = []
    for d in sorted(byd):
        hit = near(d, repo_dates)
        if not hit:
            missing.append(d)
    print(f"MISSING from repo ({len(missing)}):")
    for d in missing:
        recs = byd[d]
        # prefer approved over draft
        recs_sorted = sorted(recs, key=lambda r: (not r["approved"], r["draft"]))
        best = recs_sorted[0]
        print(f"  {d}  file {best['file_id']}.{best['ext']}  "
              f"[{'APPROVED' if best['approved'] else 'DRAFT' if best['draft'] else '?'}]  "
              f"notice {best['notice_id']}  '{best['filename']}'"
              + (f"   (+{len(recs)-1} more copies)" if len(recs) > 1 else ""))
    # repo dates with no PMN minutes (informational)
    repo_only = [rd for rd in sorted(repo_dates) if not near(rd, list(byd.keys()))]
    print(f"repo-only dates (no PMN minutes match): {len(repo_only)}")
    return missing, byd

def main():
    mm = os.path.join(CITY, "meeting_minutes", "minutes_index.csv")
    pc = os.path.join(CITY, "planning_commission", "minutes_index.csv")
    council = load_repo_dates(mm, "Council")
    cra = load_repo_dates(mm, "CRA")
    canv = load_repo_dates(mm, "Canvassers")
    pcd = load_repo_dates(pc)
    report("Council", "5803", set(council) | set(canv))
    report("CRA", "6925", set(cra))
    report("Planning Commission", "1559", set(pcd))

if __name__ == "__main__":
    main()
