#!/usr/bin/env python3
"""
Build the Town of Copperton municipal-election CSVs from the retained Salt Lake County
SOVC slice (raw/municipal_results_long_copperton.csv), normalized to the SLC/Sandy/Alta
sibling schema. Writes three CSVs. Idempotent — do NOT hand-edit the outputs; rerun this.

Copperton (Salt Lake County) is a tiny (~800-resident) place: a **metro township**
2017-01-01 -> a **Town** 2024-05-01. All council seats are **AT-LARGE** (lettered A-E,
NOT districts); the mayor seat is new with the 2024 town conversion (first elected 2025).

GENUINE council contests in the county archive (2015-2023 snapshot):
  2017  COPPERTON MT CNCL @ LRG              -> 1 at-large contest, vote-for-2 (see note)
  2021  ...COUNCIL AT-LARGE D / E            -> 2 single-seat contests
  2023  ...COUNCIL AT-LARGE A / B / C        -> 3 single-seat contests

EXCLUDED decoys (NOT the Town/Township council):
  2015  COPPERTON METRO TOWNSHIP-CITY        (incorporation ballot question)
  2015  COPPERTON MSD                        (municipal-services-district ballot question)
  2017  COPPERTON IMPROVEMENT DIST           (water/improvement-district board)
  2023  COPPERTON IMPROVEMENT DISTRICT BOARD OF TRUSTEES AT-LARGE

GAPS (documented, never fabricated):
  2019  council (seats A/B/C prior term)     absent from the county archive
  2025  first Mayor race (Sean Clayton, unopposed) + council D/E:  Copperton is entirely
        absent from the Nov-2025 SLCo SOVC and Cast-Vote-Record (all seats unopposed ->
        the county did not tabulate them). Election occurred; no county tally exists.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw" / "municipal_results_long_copperton.csv"
ETYPE = "municipal general"

# --- genuine council contest metadata (keyed by the verbatim county contest string) ----
# n_seats / voting_method are set here because the SOVC's vote_for field is blank/1.0 and
# does not by itself encode the 2017 multi-seat reality (recovered from the roster, below).
CONTESTS = {
    "COPPERTON MT CNCL @ LRG": dict(
        year="2017", n_seats=2, voting_method="plurality at-large (vote-for-2)",
        contest="Copperton Metro Township Council At-Large",
        note=("2017 founding at-large contest. SOVC labeled it only '@ LRG' with a blank "
              "vote_for; modeled as VOTE-FOR-2 (the D/E-cycle seats) because the Feb-2018 "
              "council roster seats both APOLLO PAZELL (111) and KEVIN SEVERSON (96) but "
              "NOT JP BAXTER (90, first loser). margin = last winning seat (Severson 96) - "
              "first loser (Baxter 90). D/E cycle = 2017/2021/2025."),
    ),
    "COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE D": dict(
        year="2021", n_seats=1, voting_method="plurality",
        contest="Copperton Metro Township Council At-Large D", note="Seat D (D/E cycle).",
    ),
    "COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE E": dict(
        year="2021", n_seats=1, voting_method="plurality",
        contest="Copperton Metro Township Council At-Large E",
        note=("Seat E (D/E cycle). KEVIN SEVERSON won as a QUALIFIED WRITE-IN (63) over "
              "RONALD PATRICK (62) by 1 vote."),
    ),
    "COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE A": dict(
        year="2023", n_seats=1, voting_method="plurality",
        contest="Copperton Metro Township Council At-Large A", note="Seat A (A/B/C cycle).",
    ),
    "COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE B": dict(
        year="2023", n_seats=1, voting_method="plurality",
        contest="Copperton Metro Township Council At-Large B",
        note="Seat B (A/B/C cycle). Winner SEAN CLAYTON (later elected first Town Mayor, 2025).",
    ),
    "COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE C": dict(
        year="2023", n_seats=1, voting_method="plurality",
        contest="Copperton Metro Township Council At-Large C", note="Seat C (A/B/C cycle).",
    ),
}

RACES_HDR = ["year", "election_type", "office", "district", "contest", "contest_verbatim",
             "n_seats", "n_candidates", "voting_method", "total_votes",
             "total_first_choice_votes", "winner", "winner_votes", "winner_pct",
             "runner_up", "runner_up_votes", "margin_votes", "margin_pct",
             "registered_voters", "ballots_cast", "turnout_pct", "uncontested",
             "suppressed_precincts", "note", "source_file"]
CAND_HDR = ["year", "election_type", "office", "district", "contest", "candidate",
            "votes", "pct", "rank", "is_winner"]
PREC_HDR = ["year", "election_type", "office", "district", "contest", "precinct",
            "candidate", "votes", "suppressed"]


def norm_name(raw):
    """Normalize a candidate name alongside the verbatim source (never overwrites raw)."""
    n = re.sub(r"\s+", " ", raw).strip()
    n = re.sub(r"\s*\((?:NP|NON|NP )\)\s*$", "", n, flags=re.I).strip()
    n = re.sub(r"\s*\(NP\s*\)\s*$", "", n, flags=re.I).strip()
    n = re.sub(r"\s+Qualified Write[- ]?In$", "", n, flags=re.I).strip()
    n = re.sub(r"\s*\(NP\s*\)$", "", n).strip()
    return n


def main():
    rows = list(csv.DictReader(RAW.open()))
    # aggregate votes per (contest, candidate) and per (contest, precinct, candidate)
    by_cand = defaultdict(float)
    by_prec = defaultdict(float)
    regv = {}
    srcfile = {}
    order = defaultdict(list)  # preserve candidate first-seen order
    for x in rows:
        cv = x["contest"]
        if cv not in CONTESTS:
            continue
        cand = norm_name(x["candidate"])
        v = float(x["votes"] or 0)
        by_cand[(cv, cand)] += v
        by_prec[(cv, x["precinct"], cand)] += v
        if cand not in order[cv]:
            order[cv].append(cand)
        r = x["registered_voters"]
        if r and float(r) > 0:
            regv[cv] = int(float(r))
        srcfile[cv] = x["source_file"]

    races, cands_out, precs_out = [], [], []
    # emit in a stable (year, contest) order
    for cv in sorted(CONTESTS, key=lambda c: (CONTESTS[c]["year"], CONTESTS[c]["contest"])):
        m = CONTESTS[cv]
        yr = m["year"]
        # ranked candidates
        ranked = sorted(((c, by_cand[(cv, c)]) for c in order[cv]),
                        key=lambda t: -t[1])
        n_cand = len(ranked)
        n_seats = m["n_seats"]
        total_fc = sum(v for _, v in ranked)
        winners = [c for c, _ in ranked[:n_seats]]
        winner, winner_votes = ranked[0]
        winner_pct = round(100 * winner_votes / total_fc, 2) if total_fc else ""
        uncontested = n_cand <= n_seats
        # runner_up = first loser (highest non-winner); margin = last winning seat - first loser
        if n_cand > n_seats:
            ru_name, ru_votes = ranked[n_seats]
            last_win_votes = ranked[n_seats - 1][1]
            margin_votes = int(last_win_votes - ru_votes)
            margin_pct = round(100 * margin_votes / total_fc, 2) if total_fc else ""
        else:
            ru_name, ru_votes, margin_votes, margin_pct = "", "", "", ""

        note = m["note"]
        if n_seats > 1:
            note = (f"{n_seats} seats. Winners: " +
                    "; ".join(f"{c} ({int(v)})" for c, v in ranked[:n_seats]) +
                    ". " + note)

        races.append({
            "year": yr, "election_type": ETYPE, "office": "Council", "district": "At-Large",
            "contest": m["contest"], "contest_verbatim": cv, "n_seats": n_seats,
            "n_candidates": n_cand, "voting_method": m["voting_method"], "total_votes": "",
            "total_first_choice_votes": int(total_fc), "winner": winner,
            "winner_votes": int(winner_votes),
            "winner_pct": winner_pct, "runner_up": ru_name,
            "runner_up_votes": (int(ru_votes) if ru_votes != "" else ""),
            "margin_votes": margin_votes, "margin_pct": margin_pct,
            "registered_voters": regv.get(cv, ""), "ballots_cast": "", "turnout_pct": "",
            "uncontested": uncontested, "suppressed_precincts": False, "note": note,
            "source_file": srcfile[cv],
        })
        for rank, (c, v) in enumerate(ranked, 1):
            pct = round(100 * v / total_fc, 2) if total_fc else ""
            cands_out.append({
                "year": yr, "election_type": ETYPE, "office": "Council",
                "district": "At-Large", "contest": m["contest"], "candidate": c,
                "votes": int(v), "pct": pct, "rank": rank,
                "is_winner": c in winners})
        for (ccv, prec, c), v in sorted(by_prec.items()):
            if ccv != cv:
                continue
            precs_out.append({
                "year": yr, "election_type": ETYPE, "office": "Council",
                "district": "At-Large", "contest": m["contest"], "precinct": prec,
                "candidate": c, "votes": int(v), "suppressed": False})

    _write(BASE / "copperton_races.csv", RACES_HDR, races)
    _write(BASE / "copperton_results_by_candidate.csv", CAND_HDR, cands_out)
    _write(BASE / "copperton_results_by_precinct.csv", PREC_HDR, precs_out)
    print(f"races={len(races)}  candidates={len(cands_out)}  precinct_rows={len(precs_out)}")
    for r in races:
        print(f"  {r['year']} {r['contest']}: {r['n_candidates']}cand/{r['n_seats']}seat "
              f"winner={r['winner']} ({r['winner_votes']}) uncontested={r['uncontested']}")


def _write(path, hdr, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
