#!/usr/bin/env python3
"""build_emigration_elections.py — derive Emigration Canyon's audited election slice
from the canonical Salt Lake County SOVC long file.

Input  (canonical, never hand-edited):
    ../../salt_lake_county/elections/slco_municipal_results_long.csv
    (Salt Lake County Clerk Statement of Votes Cast, tidy long, precinct x candidate x
     vote-method, 2007-2025, EVERY SLCo municipality.)

Output (this repo, DERIVED — regenerate, never hand-edit):
    emigration_canyon_races.csv            25-col audited race summary (header == south_jordan)
    emigration_canyon_results_by_candidate.csv
    emigration_canyon_results_by_precinct.csv

WHAT COUNTS AS AN EMIGRATION CANYON COUNCIL RACE
------------------------------------------------
Emigration Canyon incorporated as a Metro Township (voters approved Nov 2015, effective
Jan 1 2017) and converted to a CITY effective 2024-05-01 (H.B. 35). Same 5-member body,
ALL elected AT-LARGE, throughout. The GENUINE council contests in the SOVC are:

    2017 general   EMIGRATION CANYON MT CNCL @ LRG               (Metro Township)
    2019 general   EMG At-Large                                  (Metro Township, sheet-code era)
    2023 general   EMIGRATION CANYON METRO TOWNSHIP COUNCIL AT-LARGE
    2025 primary   CITY OF EMIGRATION CANYON COUNCIL AT-LARGE
    2025 general   CITY OF EMIGRATION CANYON COUNCIL AT-LARGE     (City)

EXCLUDED — NOT council seats (decoys / ballot questions):
  * EMIGRATION IMPROVEMENT / EMIGRATION IMPROVEMENT DIST / EMIGRATION IMPROVEMENT DISTRICT
    BOARD OF TRUSTEES AT-LARGE  — the separate sewer/water special district's own elected
    board (2015, 2017, 2021). NOT the Township/City Council.
  * EMIGRATION CANYON MSD (2015)               — a YES/NO Municipal-Services-District ballot
                                                  question, not a seat.
  * EMIGRATION CYN METRO TWNSHP-CTY (2015)      — the incorporation referendum (a ballot
                                                  CHOICE: "Metro Township" 594 vs "City" 16;
                                                  township chosen). An incorporation event,
                                                  not a council seat.

2019 — RECOVERED (was a documented gap; closed 2026-07-17):
  The 2019 general At-Large township contest is real (HAWKES 300 / BREMS 271 / HARRIS 241
  elected, TIPPETTS 193 lost; Total Votes 1,005). It was originally ABSENT/privacy-suppressed
  from the SOVC, so this generator dropped it and the row was briefly hand-appended
  (2026-07-17). The 2026-07-12 SLCo Clerk normalizer fix (which recovered the 2019/2011
  "sheet-code" eras — the 2019 SOVC tab is literally named "EMG At-Large") re-materialized the
  four un-suppressed candidate rows INTO the canonical long file, so the generator now
  reproduces the contest from its own primary input — no hand-edit. A deterministic fallback
  to salt_lake_county/elections/election_results_by_contest.csv is wired below and fires ONLY
  if the long file is ever re-suppressed for this contest (see the FALLBACK block in main()).
  n_seats=3 is NOT read from either file (the sheet-code era leaves vote_for/seats blank) — it
  is fixed by the township's 2019-11-19 Board of Canvassers minutes ("Vote For 3").

KNOWN GAPS (honest, documented — never fabricated):
  * 2021: only the Improvement District (decoy) ran; NO township council contest present
    (plausibly real — staggered at-large seats not up that cycle).
  * The INITIAL 5-member council (Staggers, Raile, Smolka, Bowen, Christensen) was elected at
    the Nov 2016 GENERAL — an even-year ballot NOT in this municipal-only SOVC archive; a
    structural absence, not a defect.

N_SEATS SOURCING:
  2023 (vote_for=3) and 2025 (vote_for=1) are taken from the source `vote_for` field.
  2017 has a BLANK `vote_for` in the source zip. n_seats=2 is INFERRED: exactly two
  candidates ran (Joe Smolka, Gary Bowen), both sitting members of the initial 2016 council;
  the field is documented as inferred in the race `note` and here.
  2019 also has a BLANK `vote_for` (sheet-code era). n_seats=3 is NOT inferred — it is
  CONFIRMED by the township's 2019-11-19 Board of Canvassers minutes ("Vote For 3"), a
  primary source; carried in the GENUINE config (seats_inferred=False) and the race `note`.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(
    HERE, "..", "..", "salt_lake_county", "elections", "slco_municipal_results_long.csv"))
# Contest-level canvass file — read-only fallback for a contest whose per-candidate rows are
# privacy-suppressed in the long file above. Same canonical SLCo Clerk SOVC, aggregated to
# contest x candidate (no precinct/registered-voter detail). Used only by the FALLBACK block.
BY_CONTEST = os.path.abspath(os.path.join(
    HERE, "..", "..", "salt_lake_county", "elections", "election_results_by_contest.csv"))

# (year, election_type, contest_verbatim) -> config for the GENUINE council contests.
GENUINE = {
    ("2017", "municipal general", "EMIGRATION CANYON MT CNCL @ LRG"): {
        "n_seats": 2, "seats_inferred": True,
        "contest": "Emigration Canyon Metro Township Council At-Large",
    },
    # 2019 sheet-code era: source contest label is the terse SOVC tab name "EMG At-Large"
    # (kept verbatim in contest_verbatim). vote_for is blank in this era, so n_seats=3 is
    # fixed by the 2019-11-19 Board of Canvassers minutes, NOT inferred. Recovered into the
    # long file by the 2026-07-12 normalizer; election_results_by_contest.csv is the wired
    # fallback if it is ever re-suppressed (see FALLBACK in main()).
    ("2019", "municipal general", "EMG At-Large"): {
        "n_seats": 3, "seats_inferred": False,
        "contest": "Emigration Canyon Metro Township Council At-Large",
        "note_extra": ("n_seats=3 CONFIRMED by the 2019-11-19 Township Board of Canvassers "
                       "('Vote For 3'; Total Votes 1,005), not inferred. Sheet-code-era "
                       "contest recovered into the county SOVC long file by the 2026-07-12 "
                       "SLCo normalizer fix (previously privacy-suppressed / a documented "
                       "gap); regenerated here 2026-07-17, superseding the interim hand-"
                       "appended row."),
    },
    ("2023", "municipal general", "EMIGRATION CANYON METRO TOWNSHIP COUNCIL AT-LARGE"): {
        "n_seats": 3, "seats_inferred": False,
        "contest": "Emigration Canyon Metro Township Council At-Large",
    },
    ("2025", "municipal primary", "CITY OF EMIGRATION CANYON COUNCIL AT-LARGE"): {
        "n_seats": 1, "seats_inferred": False,
        "contest": "City of Emigration Canyon Council At-Large",
    },
    ("2025", "municipal general", "CITY OF EMIGRATION CANYON COUNCIL AT-LARGE"): {
        "n_seats": 1, "seats_inferred": False,
        "contest": "City of Emigration Canyon Council At-Large",
    },
}

RACES_COLS = ["year", "election_type", "office", "district", "contest", "contest_verbatim",
              "n_seats", "n_candidates", "voting_method", "total_votes",
              "total_first_choice_votes", "winner", "winner_votes", "winner_pct",
              "runner_up", "runner_up_votes", "margin_votes", "margin_pct",
              "registered_voters", "ballots_cast", "turnout_pct", "uncontested",
              "suppressed_precincts", "note", "source_file"]
CAND_COLS = ["year", "election_type", "office", "district", "contest",
             "candidate", "votes", "pct", "rank", "is_winner"]
PREC_COLS = ["year", "election_type", "office", "district", "contest",
             "precinct", "candidate", "votes", "suppressed"]


def main():
    # agg[(year,etype,contest_verbatim)] -> per-candidate votes, per-precinct votes, meta
    agg = defaultdict(lambda: {
        "cand": defaultdict(float),
        "prec": defaultdict(lambda: defaultdict(float)),   # precinct -> candidate -> votes
        "prec_supp": defaultdict(bool),                    # precinct -> any suppressed
        "reg": 0.0, "source": "",
    })
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["year"], r["election_type"], r["contest"])
            if key not in GENUINE:
                continue
            a = agg[key]
            cand = r["candidate"].strip()
            v = float(r["votes"]) if r["votes"] else 0.0
            a["cand"][cand] += v
            a["prec"][r["precinct"]][cand] += v
            if str(r["suppressed"]).lower() == "true":
                a["prec_supp"][r["precinct"]] = True
            try:
                reg = float(r["registered_voters"]) if r["registered_voters"] else 0.0
            except ValueError:
                reg = 0.0
            a["reg"] = max(a["reg"], reg)
            a["source"] = r["source_file"]

    # ---- FALLBACK: contest-level canvass for a re-suppressed long-file contest -----------
    # The 2019 general ("EMG At-Large") had privacy-suppressed candidate rows in the long file
    # before the 2026-07-12 normalizer fix; that fix now supplies them, so this block is a
    # no-op today. It fires ONLY if the long file is empty/all-zero for a GENUINE contest,
    # deterministically re-sourcing that ONE contest from election_results_by_contest.csv
    # (same canonical SLCo SOVC, contest x candidate; no precinct/registered-voter detail).
    # n_seats still comes from the GENUINE config (canvass-confirmed), never from this file.
    FALLBACK = {  # GENUINE key -> (year, election_type, contest) as they appear in BY_CONTEST
        ("2019", "municipal general", "EMG At-Large"): ("2019", "municipal general",
                                                        "EMG At-Large"),
    }
    for key, bc_key in FALLBACK.items():
        a = agg.get(key)
        if a and any(v > 0 for v in a["cand"].values()):
            continue  # long file already carries real tallies — nothing to recover
        with open(BY_CONTEST, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (r["year"], r["election_type"], r["contest"]) != bc_key:
                    continue
                b = agg[key]
                cand = r["candidate"].strip()
                v = float(r["votes"]) if r["votes"] else 0.0
                b["cand"][cand] += v
                # No precinct detail in the contest file — attribute to one synthetic precinct
                # so by_precinct stays populated; suppression is false by construction here.
                b["prec"]["EMG-CONTEST"][cand] += v
                b["source"] = r["source_file"]

    races, cand_rows, prec_rows = [], [], []
    for key in sorted(GENUINE):
        year, etype, verbatim = key
        cfg = GENUINE[key]
        a = agg.get(key)
        if not a:
            continue
        n_seats = cfg["n_seats"]
        contest = cfg["contest"]

        ranked = sorted(a["cand"].items(), key=lambda kv: kv[1], reverse=True)
        total = int(round(sum(v for _, v in ranked)))
        n_candidates = len(ranked)
        winners = [name for name, _ in ranked[:n_seats]]
        losers = ranked[n_seats:]

        top_name, top_v = ranked[0]
        last_win_v = ranked[n_seats - 1][1] if len(ranked) >= n_seats else (
            ranked[-1][1] if ranked else 0)
        first_loser = losers[0] if losers else ("", 0.0)
        uncontested = n_candidates <= n_seats
        # Decisive margin: last elected seat vs highest non-winner (0 if uncontested).
        margin_votes = int(round(last_win_v - first_loser[1])) if not uncontested else ""
        margin_pct = (round(100 * (last_win_v - first_loser[1]) / total, 2)
                      if (total and not uncontested) else "")

        note_bits = [f"At-large, {n_seats} seat{'s' if n_seats != 1 else ''}.",
                     "Elected: " + ", ".join(winners) + "."]
        if cfg["seats_inferred"]:
            note_bits.append("n_seats INFERRED (source vote_for blank; 2 candidates = 2 "
                             "incumbents of the initial 2016 council, both re-elected).")
        if etype == "municipal primary":
            adv = [n for n, _ in ranked[:2]]
            note_bits.append("Primary — top 2 (" + ", ".join(adv) + ") advanced to general.")
        if cfg.get("note_extra"):
            note_bits.append(cfg["note_extra"])
        # tie note
        tie_at_cut = (not uncontested and len(ranked) > n_seats
                      and ranked[n_seats - 1][1] == ranked[n_seats][1])
        vals = [v for _, v in ranked]
        if len(set(vals)) < len(vals):
            note_bits.append("Contains tied vote totals (see by_candidate).")

        races.append({
            "year": year, "election_type": etype, "office": "Council",
            "district": "At-Large", "contest": contest, "contest_verbatim": verbatim,
            "n_seats": n_seats, "n_candidates": n_candidates, "voting_method": "plurality",
            "total_votes": total, "total_first_choice_votes": "",
            "winner": top_name, "winner_votes": int(round(top_v)),
            "winner_pct": round(100 * top_v / total, 2) if total else 0,
            "runner_up": first_loser[0], "runner_up_votes": (
                int(round(first_loser[1])) if losers else ""),
            "margin_votes": margin_votes, "margin_pct": margin_pct,
            "registered_voters": int(round(a["reg"])) if a["reg"] else "",
            "ballots_cast": "", "turnout_pct": "",
            "uncontested": "True" if uncontested else "False",
            "suppressed_precincts": sum(1 for p, s in a["prec_supp"].items() if s),
            "note": " ".join(note_bits), "source_file": a["source"],
        })

        for rank, (name, v) in enumerate(ranked, 1):
            cand_rows.append({
                "year": year, "election_type": etype, "office": "Council",
                "district": "At-Large", "contest": contest, "candidate": name,
                "votes": int(round(v)),
                "pct": round(100 * v / total, 2) if total else 0,
                "rank": rank, "is_winner": "True" if rank <= n_seats else "False",
            })

        for prec in sorted(a["prec"]):
            for name, v in sorted(a["prec"][prec].items(), key=lambda kv: kv[1], reverse=True):
                prec_rows.append({
                    "year": year, "election_type": etype, "office": "Council",
                    "district": "At-Large", "contest": contest, "precinct": prec,
                    "candidate": name, "votes": int(round(v)),
                    "suppressed": "True" if a["prec_supp"][prec] else "False",
                })

    def write(path, cols, rows):
        with open(os.path.join(HERE, path), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    write("emigration_canyon_races.csv", RACES_COLS, races)
    write("emigration_canyon_results_by_candidate.csv", CAND_COLS, cand_rows)
    write("emigration_canyon_results_by_precinct.csv", PREC_COLS, prec_rows)
    print(f"races={len(races)}  candidate_rows={len(cand_rows)}  precinct_rows={len(prec_rows)}")
    for r in races:
        print(f"  {r['year']} {r['election_type']:17s} seats={r['n_seats']} "
              f"cands={r['n_candidates']} WIN={r['winner']} ({r['winner_votes']}) "
              f"unc={r['uncontested']}")


if __name__ == "__main__":
    main()
