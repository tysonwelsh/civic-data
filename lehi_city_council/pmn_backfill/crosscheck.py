#!/usr/bin/env python3
import json, csv, collections, datetime, sys

REPO = "/Users/tysonwelsh/civic-data/lehi_city_council"

def repo_dates(path):
    ds = []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                ds.append(datetime.date.fromisoformat(r["date"][:10]))
            except Exception:
                pass
    return ds

def has_near(repo, d, tol=4):
    return any(abs((d - rd).days) <= tol for rd in repo)

def analyze(body_json, repo_csv, label):
    notices = json.load(open(body_json))
    repo = repo_dates(repo_csv)
    # PMN "meetings" = notices that either are a Meeting Agenda OR carry a Meeting Minutes attachment
    min_by_year = collections.Counter()       # PMN notices carrying a Meeting Minutes attachment
    recoverable = []                           # PMN minutes for a date repo lacks
    for n in notices:
        if not n["date"]:
            continue
        d = datetime.date.fromisoformat(n["date"])
        mins = [a for a in n["attachments"] if a["type"] == "Meeting Minutes"]
        if mins:
            min_by_year[d.year] += 1
            if not has_near(repo, d):
                recoverable.append((n["date"], n["title"], n["notice_id"],
                                    mins[0]["file_id"], mins[0]["filename"]))
    repo_by_year = collections.Counter(rd.year for rd in repo)
    print(f"\n===== {label} =====")
    print("year | repo_minutes | pmn_notices_with_minutes")
    years = sorted(set(list(repo_by_year) + list(min_by_year)))
    for y in years:
        print(f"{y} | {repo_by_year.get(y,0)} | {min_by_year.get(y,0)}")
    print(f"TOTAL repo={sum(repo_by_year.values())}  pmn_with_minutes={sum(min_by_year.values())}")
    print(f"RECOVERABLE (PMN minutes, no repo minutes within 4 days): {len(recoverable)}")
    for row in sorted(recoverable):
        print("   ", row[0], "|", row[1][:60], "| notice", row[2], "| file", row[3], "|", row[4])
    return recoverable

rc = analyze("council.json", f"{REPO}/meeting_minutes/minutes_index.csv", "CITY COUNCIL (2512)")
rp = analyze("pc.json", f"{REPO}/planning_commission/minutes_index.csv", "PLANNING COMMISSION (2651)")
json.dump({"council": rc, "pc": rp}, open("recoverable.json", "w"), indent=1)
