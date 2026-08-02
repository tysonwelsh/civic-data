"""build_county_elections.py — derive the Salt Lake County COUNTY-OFFICE layers
from the canonical even-year long file.

Input:  slco_county_results_long.csv   (canonical; normalize_sovc_county.py)
Output: county_results_by_contest.csv  one row per contest × candidate, votes
                                       summed across precinct + vote-method
        county_races.csv               STAGED audited race summaries in the
                                       uniform 25-column election_race shape
                                       (SCHEMA_SPEC §9). NOT YET FEDERATED —
                                       scripts/build_cities_db.py's
                                       load_election_race() reads only
                                       level=='city' entities today.

This script NEVER touches the odd-year municipal layer
(slco_municipal_results_long.csv / election_results_by_contest.csv /
build_elections.py) — those stay byte-identical.

DERIVED + idempotent. Never hand-edit the outputs; rerun this.

Usage:  python3 salt_lake_county/elections/build_county_elections.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from county_contest_map import classify           # noqa: E402

csv.field_size_limit(1 << 30)
SRC = os.path.join(HERE, "slco_county_results_long.csv")
RECON = os.path.join(HERE, "reconciliation_county.csv")
OUT_CONTEST = os.path.join(HERE, "county_results_by_contest.csv")
OUT_RACES = os.path.join(HERE, "county_races.csv")

# `votes` is the PRECINCT SUM (the election_result convention, comparable with
# the odd-year municipal layer). `certified_votes` is the workbook's OWN
# contest-total row for the same candidate — the county's certified figure, which
# is LARGER wherever '****' privacy suppression hid precinct cells (2024/2026).
# The two agree on 3,624 of 3,811 audited candidate columns; where they differ,
# certified_votes is authoritative and is what county_races.csv reports.
CONTEST_COLS = ["year", "election_date", "election_type", "contest",
                "jurisdiction_slug", "office", "district", "seats", "candidate",
                "party", "votes", "certified_votes", "votes_basis",
                "rank_in_contest", "n_precincts", "suppressed", "source_file"]
# the uniform 25-column election_race superset, in SCHEMA_SPEC §9 order
RACE_COLS = ["year", "election_type", "office", "district", "contest",
             "contest_verbatim", "n_seats", "n_candidates", "voting_method",
             "total_votes", "total_first_choice_votes", "winner", "winner_votes",
             "winner_pct", "runner_up", "runner_up_votes", "margin_votes",
             "margin_pct", "registered_voters", "ballots_cast", "turnout_pct",
             "uncontested", "suppressed_precincts", "note", "source_file"]

# 2024/2026 print the party in DOUBLED parentheses ('NATALIE PINKNEY ((DEM))') —
# the workbook's own form, kept verbatim in `candidate`; tolerate it here.
PARTY_RE = re.compile(r"[\(\[]+\s*([A-Z]{1,4})\s*[\)\]]+\s*$")
# A 'Write-In for <office>' contest is a write-in TALLY ADDENDUM the canvass
# prints beside the real race (2004 general), not a race with a winner: it is
# kept in the by-contest layer and excluded from county_races.csv.
WRITE_IN_CONTEST_RE = re.compile(r"^\s*WRITE[\s-]?INS?\b", re.I)
# The canvass prints an aggregate write-in BUCKET as if it were a candidate
# ('WRITE-IN', 'WRITE-IN (NP)', 'Unresolved Write-In'). Kept verbatim as a row
# (washington_county precedent for 'OVER VOTES'/'UNDER VOTES'), but never read
# as a named opponent — races where it lands in the top two are noted.
WRITE_IN_BUCKET_RE = re.compile(r"^\s*(unresolved\s+)?write[\s-]?ins?\b", re.I)
# the 2002/2004 canvass prints the party as a bare (often column-clipped) suffix
TRAIL_PARTY_RE = re.compile(r"\s(DEM|REP|GRN|LIB|IAP|CON|UNA|NP|NON|DE|RE|GR|LI|"
                            r"P|U|C|S|G|L|D|R)$")
# ballot-measure "candidates" are the options, not people
MEASURE_OPTIONS = re.compile(r"^\s*(FOR|AGAINST|YES|NO)\b", re.I)


def party_of(candidate):
    m = PARTY_RE.search(candidate.strip())
    if m:
        return m.group(1)
    m = TRAIL_PARTY_RE.search(candidate.strip())
    return m.group(1) if m else ""


def pct(a, b):
    return "" if not b else "%.4f" % (a / b)


def load_certified():
    """(year, election_type, contest, candidate) -> (certified_total, status)
    from the reconciliation ledger the normalizer writes."""
    out = {}
    if not os.path.exists(RECON):
        return out
    with open(RECON, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["candidate"] == "*" or r["certified_total"] == "":
                continue
            out[(r["year"], r["election_type"], r["contest"], r["candidate"])] = (
                int(r["certified_total"]), r["status"])
    return out


def main():
    certified = load_certified()
    agg = defaultdict(lambda: {"votes": 0, "precincts": set(), "suppressed": 0,
                               "sup_precincts": set(), "source": "", "seats": ""})
    reg = defaultdict(dict)      # (year,etype,contest) -> precinct -> registered
    bal = defaultdict(dict)      # (year,etype,contest) -> precinct -> times_cast
    meta = {}
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["year"], r["election_type"], r["contest"])
            meta[key] = (r["election_date"], r["source_file"])
            if r["precinct"] == "Cumulative":
                continue          # the workbooks' all-zero rollup label, never a precinct
            a = agg[key + (r["candidate"],)]
            try:
                a["votes"] += int(r["votes"]) if r["votes"] else 0
            except ValueError:
                pass
            a["precincts"].add(r["precinct"])
            a["source"] = r["source_file"]
            a["seats"] = r["vote_for"]
            if str(r["suppressed"]).lower() == "true":
                a["suppressed"] += 1
                a["sup_precincts"].add(r["precinct"])
            if r["registered_voters"]:
                try:
                    reg[key][r["precinct"]] = max(reg[key].get(r["precinct"], 0),
                                                  int(r["registered_voters"]))
                except ValueError:
                    pass
            if r["times_cast"]:
                try:
                    bal[key][r["precinct"]] = max(bal[key].get(r["precinct"], 0),
                                                  int(r["times_cast"]))
                except ValueError:
                    pass

    by_contest = defaultdict(list)
    for (year, etype, contest, cand), a in agg.items():
        by_contest[(year, etype, contest)].append((cand, a))

    contest_rows, race_rows = [], []
    for key, cands in sorted(by_contest.items()):
        year, etype, contest = key
        edate, _src = meta[key]
        office, district, kind = classify(contest)
        # rank on the CERTIFIED total where the workbook printed one (identical to
        # the precinct sum except where privacy suppression hid cells)
        def eff(a_cand, a):
            hit = certified.get((year, etype, contest, a_cand))
            return hit[0] if hit else a["votes"]
        cands.sort(key=lambda ca: (-eff(ca[0], ca[1]), ca[0]))
        seats = ""
        if cands[0][1]["seats"]:
            try:
                seats = str(int(float(cands[0][1]["seats"])))
            except ValueError:
                seats = cands[0][1]["seats"]
        for rank, (cand, a) in enumerate(cands, start=1):
            hit = certified.get((year, etype, contest, cand))
            contest_rows.append({
                "year": year, "election_date": edate, "election_type": etype,
                "contest": contest, "jurisdiction_slug": "salt_lake_county",
                "office": office, "district": district, "seats": seats,
                "candidate": cand, "party": party_of(cand), "votes": a["votes"],
                "certified_votes": hit[0] if hit else "",
                "votes_basis": hit[1] if hit else "no certified-total row",
                "rank_in_contest": rank, "n_precincts": len(a["precincts"]),
                "suppressed": "true" if a["suppressed"] else "false",
                "source_file": a["source"]})

        if kind != "office" or WRITE_IN_CONTEST_RE.match(contest):
            continue                      # ballot measures / write-in addenda are not races
        # county_races.csv reports the county's CERTIFIED figures
        vote_of = {c: eff(c, a) for c, a in cands}
        total = sum(vote_of[c] for c, _a in cands)
        win, wa = cands[0]
        run, ra = (cands[1] if len(cands) > 1 else ("", None))
        win_v = vote_of[win]
        run_v = vote_of[run] if ra else None
        no_cert = [c for c, _a in cands
                   if (year, etype, contest, c) not in certified]
        sup_prec = set()
        for _c, a in cands:
            sup_prec |= a["sup_precincts"]
        registered = sum(reg[key].values()) or ""
        ballots = sum(bal[key].values()) or ""
        turnout = pct(ballots, registered) if (ballots and registered) else ""
        notes = []
        named = [c for c, _a in cands if not WRITE_IN_BUCKET_RE.match(c)]
        if len(named) != len(cands):
            notes.append("%d of %d canvass columns are NAMED candidates; the rest "
                         "are the canvass's aggregate write-in bucket"
                         % (len(named), len(cands)))
        if WRITE_IN_BUCKET_RE.match(win) or (run and WRITE_IN_BUCKET_RE.match(run)):
            notes.append("AUDIT FLAG: the write-in bucket is in the top two — "
                         "runner_up/margin are against an aggregate write-in "
                         "total, not a named opponent")
        if etype.endswith("primary"):
            notes.append("PRIMARY: this is the party ballot's plurality leader "
                         "(the nominee), NOT an election winner")
        if len(cands) == 1:
            notes.append("single candidate on the canvass (unopposed)")
        if sup_prec:
            notes.append("%d precinct(s) carry '****' privacy-suppressed cells; "
                         "the votes here are the workbook's own CERTIFIED contest "
                         "totals (larger than the precinct sums in "
                         "county_results_by_contest.csv by the suppressed amount)"
                         % len(sup_prec))
        if no_cert:
            notes.append("AUDIT FLAG: %d candidate column(s) had no certified-total "
                         "row in the workbook; their figures are precinct sums"
                         % len(no_cert))
        if not seats:
            notes.append("n_seats not printed by the workbook; all Salt Lake "
                         "County offices in this file are single-seat")
        race_rows.append({
            "year": year, "election_type": etype, "office": office,
            "district": district, "contest": "%s%s" % (office,
                                                       " " + district if district else ""),
            "contest_verbatim": contest, "n_seats": seats or "1",
            "n_candidates": len(cands), "voting_method": "plurality",
            "total_votes": total, "total_first_choice_votes": "",
            "winner": win, "winner_votes": win_v,
            "winner_pct": pct(win_v, total),
            "runner_up": run, "runner_up_votes": (run_v if ra else ""),
            "margin_votes": (win_v - run_v) if ra else "",
            "margin_pct": pct(win_v - run_v, total) if ra else "",
            "registered_voters": registered, "ballots_cast": ballots,
            "turnout_pct": turnout,
            "uncontested": "true" if len(cands) == 1 else "false",
            "suppressed_precincts": len(sup_prec),
            "note": "; ".join(notes), "source_file": wa["source"]})

    contest_rows.sort(key=lambda x: (x["election_date"], x["election_type"],
                                     x["office"], x["district"],
                                     x["rank_in_contest"]))
    with open(OUT_CONTEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CONTEST_COLS)
        w.writeheader()
        w.writerows(contest_rows)
    race_rows.sort(key=lambda x: (x["year"], x["election_type"], x["office"],
                                  x["district"]))
    with open(OUT_RACES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RACE_COLS)
        w.writeheader()
        w.writerows(race_rows)

    n_off = sum(1 for r in race_rows if r["election_type"] == "general")
    print("Wrote %s: %d contest x candidate rows, %d contests"
          % (os.path.basename(OUT_CONTEST), len(contest_rows), len(by_contest)))
    print("Wrote %s: %d STAGED county-office races (%d general, %d primary/other)"
          % (os.path.basename(OUT_RACES), len(race_rows), n_off, len(race_rows) - n_off))
    per = defaultdict(int)
    for r in race_rows:
        per[r["office"]] += 1
    print("  per office:", dict(sorted(per.items())))


if __name__ == "__main__":
    main()
