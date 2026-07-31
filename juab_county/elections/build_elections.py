#!/usr/bin/env python3
"""build_elections.py — derive the governance contest x candidate layer from the
canonical Juab County canvass long file (juab_results_long.csv).

Output: election_results_by_contest.csv — one row per contest x candidate, votes
summed across precinct, GOVERNANCE offices only (the task-scoped families:
MUNICIPAL council/mayor for all 5 Juab jurisdictions + COUNTY offices + SCHOOL
boards), jurisdiction_slug-tagged. This is what loads into gov.db election_result
(conforms to scripts/build_cities_db.load_election_result — 14 named columns +
the leading city/gov_level/state supplied by the loader).

Excluded from the derived layer (kept in the long file only): state/federal offices
(US President/Senate/House, Governor, statewide constitutional officers, State
Legislature), judicial retentions, and constitutional amendments — not Juab
local-governance jurisdictions. See recon.md / CLAUDE.md.

DERIVED + idempotent. Never hand-edit; rerun after build_long.py.
"""
import csv
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "juab_results_long.csv")
OUT = os.path.join(HERE, "election_results_by_contest.csv")

# Juab municipalities held in this canvass. (slug, regex on normalized contest).
MUNICIPAL = [
    ("nephi",       r"\bNEPHI CITY\b"),
    ("mona",        r"\bMONA CITY\b"),
    ("levan",       r"\bLEVAN TOWN\b"),
    ("rocky_ridge", r"\bROCKY RIDGE\b"),
    ("eureka",      r"\bEUREKA CITY\b"),
]


def parse_contest(contest):
    """(jurisdiction_slug, office, district) for a Juab governance contest;
    None to exclude (state/federal/judicial/amendment)."""
    up = " ".join(contest.upper().split())
    # strip partisan-primary prefixes for office parsing
    core = re.sub(r"^REPUBLICAN\s+FOR\s+|^REP\s+", "", up)

    # exclude non-governance contest kinds outright
    if up.startswith("SHALL ") or "JUDICIAL RETENTION" in up or "CONSTITUTIONAL AMENDMENT" in up:
        return None

    # --- MUNICIPAL (all at-large; council district = At-Large, mayor = '') ---
    for slug, pat in MUNICIPAL:
        if re.search(pat, up):
            if "MAYOR" in up:
                return slug, "Mayor", ""
            if "COUNCIL" in up:
                return slug, "Council", "At-Large"
            return None

    # --- COUNTY offices (partisan; jurisdiction = juab_county) ---
    if "COUNTY COMMISSION" in core:      # 'County Commission Seat C' / 'County Commissioner Seat A'
        m = re.search(r"SEAT\s+([A-Z])", core)
        return "juab_county", "Commission", (f"Seat {m.group(1)}" if m else "")
    if "COUNTY SHERIFF" in core:
        return "juab_county", "Sheriff", ""
    if "COUNTY ASSESSOR" in core:
        return "juab_county", "Assessor", ""
    if "COUNTY RECORDER" in core:
        return "juab_county", "Recorder/Surveyor", ""
    if "COUNTY TREASURER" in core:
        return "juab_county", "Treasurer", ""

    # --- SCHOOL boards ---
    m = re.search(r"JUAB COUNTY SCHOOL BOARD DISTRICT\s+(\d+)", core)
    if m:
        return "juab_school", "School Board", m.group(1)
    m = re.search(r"TINTIC SCHOOL BOARD DISTRICT\s+(\d+)", core)
    if m:
        return "tintic_school", "School Board", m.group(1)
    m = re.search(r"STATE BOARD OF EDUCATION DISTRICT\s+(\d+)", core)
    if m:
        return "utah_sboe", "State Board of Education", m.group(1)

    return None   # state/federal candidate offices — long-file only


def main():
    # group by (year, etype, contest_id) so the two identically-named 2023
    # 'Levan Town Council' contests (separate seats) never merge.
    # Votes come from the AUTHORITATIVE 'Certified Total' rows (== the canvass PDF);
    # 'Precinct' rows only feed n_precincts + the suppression flag.
    agg = defaultdict(lambda: defaultdict(lambda: {
        "votes": 0, "precincts": set(), "party": "", "source": "",
        "suppressed": False}))
    meta = {}
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            parsed = parse_contest(r["contest"])
            if not parsed:
                continue
            gkey = (r["year"], r["election_type"], r["contest_id"])
            meta[gkey] = (r["contest"], r["vote_for"], parsed)
            a = agg[gkey][r["candidate"]]
            if r["party"]:
                a["party"] = r["party"]
            if r["vote_method"] == "Certified Total":
                a["source"] = r["source_file"]
                try:
                    a["votes"] = int(round(float(r["votes"]))) if r["votes"] != "" else 0
                except ValueError:
                    pass
            elif r["vote_method"] == "Precinct":
                if str(r["suppressed"]).lower() == "true":
                    a["suppressed"] = True
                elif r["precinct"]:
                    a["precincts"].add(r["precinct"])

    rows = []
    for gkey, cands in agg.items():
        year, etype, _cid = gkey
        contest, seats, (juris, office, district) = meta[gkey]
        ranked = sorted(cands.items(), key=lambda kv: -kv[1]["votes"])
        for rank, (cand, a) in enumerate(ranked, start=1):
            rows.append({
                "year": year, "election_type": etype, "contest": contest,
                "jurisdiction_slug": juris, "office": office, "district": district,
                "seats": seats, "candidate": cand, "party": a["party"],
                "votes": a["votes"], "rank_in_contest": rank,
                "n_precincts": len(a["precincts"]),
                "suppressed": "true" if a["suppressed"] else "false",
                "source_file": a["source"],
            })

    rows.sort(key=lambda x: (x["year"], x["election_type"], x["jurisdiction_slug"],
                             x["office"], x["district"], x["rank_in_contest"]))
    cols = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes", "rank_in_contest",
            "n_precincts", "suppressed", "source_file"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    per = defaultdict(int)
    for r in rows:
        per[r["jurisdiction_slug"]] += 1
    print(f"Wrote {OUT}: {len(rows)} contest x candidate rows across "
          f"{len(agg)} governance contests")
    print("  per jurisdiction rows:", dict(sorted(per.items())))


if __name__ == "__main__":
    main()
