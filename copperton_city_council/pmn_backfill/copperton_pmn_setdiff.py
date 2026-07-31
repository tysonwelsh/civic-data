#!/usr/bin/env python3
"""Copperton PMN backfill — per-date set-difference of PMN minutes vs the audited repo.

Reads work/parsed_<body>.json (from copperton_pmn_crawl.py), detects MINUTES attachments
by FILENAME (not the unreliable PMN type label), extracts each minutes' MEETING date
from the filename (falling back to the notice event date), and diffs against the repo
minutes indexes (±TOL days). Copperton's minutes_index.csv is the 8-col standard with NO
body column (council = whole file); PC has its own index.

Bodies:  5831 Copperton Council -> meeting_minutes/minutes_index.csv
         1560 Copperton Planning Commission -> planning_commission/minutes_index.csv

Also loads meeting_minutes/minutes_unrecovered.csv so the known 2017-02->2018-06 purge
gap is reported separately from genuinely-missing recoverable dates.
Prints per body: PMN minutes dates, repo dates, MISSING (on PMN, not repo & not in the
purge gap), purge-gap overlaps, and repo-only. Emits work/missing_<body>.json for fetch.
"""
import csv, json, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
CITY = os.path.abspath(os.path.join(HERE, ".."))
TOL = 4  # days


def load_repo_dates(index_path):
    dates = {}
    with open(index_path, newline="") as f:
        for r in csv.DictReader(f):
            dates[r["date"]] = r
    return dates


def load_unrecovered(path):
    out = set()
    if not os.path.exists(path):
        return out
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out.add(r["date"])
    return out


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
    m = re.search(r'(\d{1,2})[-_/](\d{1,2})[-_/](20\d{2})', fn)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(yr, mo, da).isoformat()
        except ValueError:
            pass
    m = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', fn)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
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
    byd = {}
    for n in notices:
        for a in n["attachments"]:
            if not is_minutes(a["filename"]):
                continue
            d = meeting_date_from_filename(a["filename"], n["meeting_dt"])
            if not d:
                continue
            # guard against the 0017 bad-parse (PMN prints '0017/07/19')
            if not d.startswith(("2017", "2018", "2019", "2020", "2021",
                                 "2022", "2023", "2024", "2025", "2026")):
                continue
            rec = dict(a, notice_id=n["notice_id"], notice_dt=n["meeting_dt"],
                       approved="approv" in a["filename"].lower(),
                       draft="draft" in a["filename"].lower())
            byd.setdefault(d, []).append(rec)
    return byd


def near(d, dates):
    dd = datetime.date.fromisoformat(d)
    for rd in dates:
        try:
            if abs((datetime.date.fromisoformat(rd) - dd).days) <= TOL:
                return rd
        except ValueError:
            continue
    return None


def report(label, body, repo_dates, unrecovered):
    byd = pmn_minutes(body)
    print(f"\n===== {label} (body {body}) =====")
    print(f"PMN minutes meeting-dates: {len(byd)}   repo dates: {len(repo_dates)}   "
          f"unrecovered-logged: {len(unrecovered)}")
    missing, purge = [], []
    for d in sorted(byd):
        if near(d, repo_dates):
            continue
        if near(d, unrecovered):
            purge.append(d)
        else:
            missing.append(d)
    print(f"GENUINELY MISSING from repo (recoverable candidates) ({len(missing)}):")
    out = []
    for d in missing:
        recs = sorted(byd[d], key=lambda r: (not r["approved"], r["draft"]))
        best = recs[0]
        tag = 'APPROVED' if best['approved'] else 'DRAFT' if best['draft'] else '?'
        print(f"  {d}  file {best['file_id']}.{best['ext']}  [{tag}]  "
              f"notice {best['notice_id']}  '{best['filename']}'"
              + (f"   (+{len(recs)-1} more)" if len(recs) > 1 else ""))
        out.append({"date": d, "body": label, "file_id": best["file_id"],
                    "ext": best["ext"], "notice_id": best["notice_id"],
                    "filename": best["filename"], "label": best.get("label", ""),
                    "approved": best["approved"], "draft": best["draft"]})
    print(f"PMN minutes that fall inside the logged purge gap ({len(purge)}): "
          + (", ".join(purge) if purge else "none"))
    repo_only = [rd for rd in sorted(repo_dates) if not near(rd, list(byd.keys()))]
    print(f"repo-only dates (no PMN minutes match): {len(repo_only)}")
    with open(os.path.join(WORK, f"missing_{body}.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


def main():
    mm = os.path.join(CITY, "meeting_minutes", "minutes_index.csv")
    pc = os.path.join(CITY, "planning_commission", "minutes_index.csv")
    unrec = load_unrecovered(os.path.join(CITY, "meeting_minutes", "minutes_unrecovered.csv"))
    council = load_repo_dates(mm)
    pcd = load_repo_dates(pc)
    report("Council", "5831", set(council), unrec)
    report("PlanningCommission", "1560", set(pcd), set())  # PC has no purge log


if __name__ == "__main__":
    main()
