#!/usr/bin/env python3
"""Per-DATE set-difference of PMN minutes vs the repo's coverage, for each Sandy body.
Council minutes come from Legistar-built minutes_index.csv; PC/RDA have no minutes files
on disk, so we diff against the dates the repo covers in any form (all_votes.csv).
Emits recoverable.json (in-scope PMN minutes the repo lacks)."""
import json, csv, collections, datetime, sys

REPO = "/Users/tysonwelsh/civic-data/sandy_city_council"
FLOOR = 2020

def dates_from_csv(path, col="date"):
    ds = set()
    try:
        for r in csv.DictReader(open(path)):
            v = (r.get(col) or "")[:10]
            try:
                ds.add(datetime.date.fromisoformat(v))
            except Exception:
                pass
    except FileNotFoundError:
        pass
    return ds

def has_near(repo, d, tol=4):
    return any(abs((d - rd).days) <= tol for rd in repo)

def valid(dstr):
    try:
        y = int(dstr[:4])
        return 2000 <= y <= 2027
    except Exception:
        return False

def analyze(body_json, repo_dates, label, min_type="Meeting Minutes"):
    notices = json.load(open(body_json))
    min_by_year = collections.Counter()
    recoverable = []
    for n in notices:
        if not n["date"] or not valid(n["date"]):
            continue
        d = datetime.date.fromisoformat(n["date"])
        mins = [a for a in n["attachments"] if a["type"] == min_type]
        if mins:
            min_by_year[d.year] += 1
            if d.year >= FLOOR and not has_near(repo_dates, d):
                recoverable.append((n["date"], n["title"], n["notice_id"],
                                    mins[0]["file_id"], mins[0]["filename"]))
    repo_by_year = collections.Counter(rd.year for rd in repo_dates if rd.year >= FLOOR)
    print(f"\n===== {label} =====")
    print("year | repo_coverage | pmn_notices_with_minutes")
    years = sorted(set(list(repo_by_year) + [y for y in min_by_year if y >= FLOOR]))
    for y in years:
        print(f"{y} | {repo_by_year.get(y,0)} | {min_by_year.get(y,0)}")
    print(f"TOTAL(2020+) repo={sum(repo_by_year.values())}  pmn_minutes={sum(v for y,v in min_by_year.items() if y>=FLOOR)}  (pre-2020 pmn_minutes={sum(v for y,v in min_by_year.items() if y<FLOOR)})")
    print(f"RECOVERABLE (in-scope PMN minutes, no repo coverage within 4 days): {len(recoverable)}")
    for row in sorted(recoverable):
        print("   ", row[0], "|", row[1][:55], "| notice", row[2], "| file", row[3])
    return recoverable

council_repo = dates_from_csv(f"{REPO}/meeting_minutes/minutes_index.csv")
pc_repo = dates_from_csv(f"{REPO}/planning_commission/all_votes.csv")
rda_repo = dates_from_csv(f"{REPO}/meeting_minutes/all_votes.csv")  # RDA folded into council minutes if anywhere

rc = analyze("council.json", council_repo, "CITY COUNCIL (464)")
rp = analyze("pc.json", pc_repo, "PLANNING COMMISSION (466)")
rr = analyze("rda.json", rda_repo, "REDEVELOPMENT AGENCY (465)")
rb = analyze("boa.json", set(), "BOARD OF ADJUSTMENTS (467)")

json.dump({"council": rc, "pc": rp, "rda": rr, "boa": rb}, open("recoverable.json", "w"), indent=1)
print("\n-> recoverable.json")
