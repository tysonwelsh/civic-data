#!/usr/bin/env python3
"""Per-DATE set difference of PMN Meeting-Minutes notices vs the repo's audited
minutes indexes, for Park City City Council (653), Planning Commission (1860),
and Redevelopment Agency (654). Window >= 2020 (repo data floor).

Council/PC: diff PMN minutes dates against that body's repo minutes_index.csv
  (tolerance +-4 days for posted-date vs meeting-date offset).
RDA: the repo has NO standalone RDA minutes layer (RDA runs as an in-council
  recess in the council minutes). Every PMN RDA Meeting-Minutes doc is therefore
  net-new; we still report whether its date coincides with a repo COUNCIL meeting
  (context: the RDA recess for that date is likely embedded there).
"""
import json, csv, collections, datetime

REPO = "/Users/tysonwelsh/civic-data/park_city_city_council"
FLOOR = datetime.date(2020, 1, 1)

def repo_dates(path):
    ds = []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                ds.append(datetime.date.fromisoformat(r["date"][:10]))
            except Exception:
                pass
    return ds

def near(dates, d, tol=4):
    return [rd for rd in dates if abs((d - rd).days) <= tol]

def load_min_notices(body_json):
    """Return list of (date_obj, title, notice_id, file_id, filename) for notices
    carrying a Meeting Minutes attachment, valid date only."""
    out = []
    for n in json.load(open(body_json)):
        if not n["date"]:
            continue
        try:
            d = datetime.date.fromisoformat(n["date"])
        except ValueError:
            continue
        if d.year < 100:   # site typo artifact (e.g. 0019-12-05)
            continue
        mins = [a for a in n["attachments"] if a["type"] == "Meeting Minutes"]
        if mins:
            out.append((d, n["title"], n["notice_id"], mins[0]["file_id"], mins[0]["filename"]))
    return out

council_repo = repo_dates(f"{REPO}/meeting_minutes/minutes_index.csv")
pc_repo      = repo_dates(f"{REPO}/planning_commission/minutes_index.csv")

def report_body(body_json, repo, label, is_rda=False):
    notices = load_min_notices(body_json)
    by_year = collections.Counter(d.year for d,*_ in notices)
    recoverable = []
    for d, title, nid, fid, fn in notices:
        if d < FLOOR:
            continue
        if is_rda:
            coincide = near(council_repo, d)
            recoverable.append((d.isoformat(), title, nid, fid, fn,
                                "council-date-match" if coincide else "no-council-date"))
        else:
            if not near(repo, d):
                recoverable.append((d.isoformat(), title, nid, fid, fn, ""))
    print(f"\n===== {label} =====")
    repo_by_year = collections.Counter(rd.year for rd in repo) if repo else {}
    years = sorted(set(list(repo_by_year)+list(by_year)))
    print("year | repo_minutes | pmn_notices_w_minutes")
    for y in years:
        print(f"  {y} | {repo_by_year.get(y,0)} | {by_year.get(y,0)}")
    print(f"  PMN minutes total (all yrs)={sum(by_year.values())}  in-scope(>=2020)={sum(v for y,v in by_year.items() if y>=2020)}")
    print(f"  RECOVERABLE in-scope: {len(recoverable)}")
    for row in sorted(recoverable):
        print("    ", row[0], "|", row[1][:55], "| notice", row[2], "| file", row[3], "|", row[5])
    return recoverable

rc = report_body("council.json", council_repo, "CITY COUNCIL (653)")
rp = report_body("pc.json",      pc_repo,      "PLANNING COMMISSION (1860)")
rr = report_body("rda.json",     None,         "REDEVELOPMENT AGENCY (654) [net-new: no repo RDA minutes layer]", is_rda=True)

json.dump({"council": rc, "pc": rp, "rda": rr}, open("recoverable.json", "w"), indent=1)
print("\n-> recoverable.json")
