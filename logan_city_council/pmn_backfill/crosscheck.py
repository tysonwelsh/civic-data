#!/usr/bin/env python3
"""Logan PMN cross-check: per-DATE set-difference of PMN Meeting-Minutes notices
against the repo's audited minutes indexes, for Council(494)/PC(487)/RDA(495).
Window 2020..2026. Falls back to an Agenda ('Other') attachment when no minutes exist."""
import json, csv, collections, datetime

REPO = "/Users/tysonwelsh/civic-data/logan_city_council"
YMIN, YMAX = 2020, 2026

def repo_dates(path, slug_filter=None):
    ds = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if slug_filter and r.get("slug") != slug_filter:
                continue
            try:
                ds.append(datetime.date.fromisoformat(r["date"][:10]))
            except Exception:
                pass
    return ds

def has_near(repo, d, tol=4):
    return any(abs((d - rd).days) <= tol for rd in repo)

def analyze(body_json, repo, label):
    notices = json.load(open(body_json))
    min_by_year = collections.Counter()
    recoverable = []
    for n in notices:
        if not n["date"]:
            continue
        d = datetime.date.fromisoformat(n["date"])
        if not (YMIN <= d.year <= YMAX):
            continue
        mins = [a for a in n["attachments"] if a["type"] == "Meeting Minutes"]
        if mins:
            min_by_year[d.year] += 1
            if not has_near(repo, d):
                # prefer minutes attachment
                recoverable.append({"date": n["date"], "title": n["title"],
                    "notice_id": n["notice_id"], "file_id": mins[0]["file_id"],
                    "filename": mins[0]["filename"], "att_type": "Meeting Minutes"})
    repo_by_year = collections.Counter(rd.year for rd in repo if YMIN <= rd.year <= YMAX)
    print(f"\n===== {label} =====")
    print("year | repo_minutes | pmn_notices_with_minutes")
    for y in range(YMIN, YMAX+1):
        print(f"{y} | {repo_by_year.get(y,0)} | {min_by_year.get(y,0)}")
    print(f"TOTAL in-window repo={sum(repo_by_year.values())}  pmn_with_minutes={sum(min_by_year.values())}")
    print(f"RECOVERABLE (PMN minutes, no repo minutes within 4 days): {len(recoverable)}")
    for row in sorted(recoverable, key=lambda x:x['date']):
        print("   ", row['date'], "|", row['title'][:55], "| notice", row['notice_id'], "| file", row['file_id'])
    return {"recoverable": recoverable, "repo_by_year": dict(repo_by_year), "pmn_by_year": dict(min_by_year)}

council_repo = repo_dates(f"{REPO}/meeting_minutes/minutes_index.csv", "city-council-meeting")
rda_repo     = repo_dates(f"{REPO}/meeting_minutes/minutes_index.csv", "redevelopment-agency-meeting")
pc_repo      = repo_dates(f"{REPO}/planning_commission/minutes_index.csv")

out = {}
out["council"] = analyze("body_494.json", council_repo, "MUNICIPAL COUNCIL (494)")
out["pc"]      = analyze("body_487.json", pc_repo,      "PLANNING COMMISSION (487)")
out["rda"]     = analyze("body_495.json", rda_repo,     "REDEVELOPMENT AGENCY (495)")
json.dump(out, open("recoverable.json", "w"), indent=1)
