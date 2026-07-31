#!/usr/bin/env python3
"""
Build the Town of Alta municipal-election CSVs from the canonical Salt Lake County
SOVC (Statement of Votes Cast) long file. Do NOT re-download — this filters the
shared archive slice retained under raw/.

Alta is a Utah TOWN: a townwide (VOTING) Mayor + a 4-member AT-LARGE Town Council
(no districts). Council seats are staggered 4-year terms, so each odd-year general
fills 2 at-large seats. Data floor 2020 -> in-scope generals are 2021 and 2023.

Sources / provenance
--------------------
Reads the county canonical DIRECTLY (re-point 2026-07-19):
    salt_lake_county/elections/slco_municipal_results_long.csv
    filtered in-code to the GENUINE Town-of-Alta contests. The "ALTA CANYON REC*"
    rows (Alta Canyon Recreation Special Service District, a Sandy-area rec district
    — NOT the Town) are EXCLUDED on the CANYON token; the workbook `Cumulative`
    rollup rows are EXCLUDED (never a precinct). The old per-city slice copy
    (raw/municipal_results_long_alta.csv) was retired after this re-point.

Two data realities in scope:
  * 2023 general (Council At-Large, 2 seats) : real per-precinct counts, no
    suppression -> summed straight from the long file.
  * 2021 general (Mayor + Council At-Large)  : the county originally SUPPRESSED every
    candidate tally ("**** - INSUFFICIENT TURNOUT TO PROTECT VOTER PRIVACY") because
    Alta's precinct is tiny. **RECOVERED 2026-07-19:** the upstream family-C
    Total-recovery fix released each precinct's own un-suppressed `vote_method='Total'`
    sub-row (the In-Person / Vote-By-Mail method SPLIT remains county-suppressed).
    The pipeline now fills the real tallies from those Total rows (Mayor Bourke 85;
    Council — Byrne 73, Anctil 59, Margaret Bourke 53). The external cross-check
    (ALTA_2021_EXTERNAL) is retained ONLY as a defensive fallback for a contest that
    is suppressed with NO Total recovered; the `note` column records the recovery
    provenance. Never fabricated — the counts are the county's own released Totals.

2025: the Nov-2025 SLCo general SOVC contains NO Alta contest at all (verified) — the
Town held no 2025 county-run municipal election. Documented in CLAUDE.md, not written.

Multi-seat (at-large) convention (matches sandy/logan/nephi siblings):
  winner       = top vote-getter
  runner_up    = FIRST LOSER (highest-polling non-winner)
  margin_votes = (last winning seat) - (first loser)
  is_winner    = True for every seat filled (top n_seats candidates)
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent
# County canonical (read directly since the 2026-07-19 re-point); filtered to Town-of-Alta in load().
RAW = BASE.parent.parent / "salt_lake_county" / "elections" / "slco_municipal_results_long.csv"

# Recovery provenance stamped on the 2021 rows whose tallies were released 2026-07-19.
RECOVER_MSG = ("Tallies RECOVERED 2026-07-19 from the previously privacy-suppressed county "
               "SOVC: the workbook released each precinct's un-suppressed Total sub-row "
               "(the In-Person/Vote-By-Mail method split remains county-suppressed).")

RACES_HDR = ["year","election_type","office","district","contest","contest_verbatim",
    "n_seats","n_candidates","voting_method","total_votes","total_first_choice_votes",
    "winner","winner_votes","winner_pct","runner_up","runner_up_votes","margin_votes",
    "margin_pct","registered_voters","ballots_cast","turnout_pct","uncontested",
    "suppressed_precincts","note","source_file"]
CAND_HDR = ["year","election_type","office","district","contest","candidate","votes",
    "pct","rank","is_winner"]
PREC_HDR = ["year","election_type","office","district","contest","precinct","candidate",
    "votes","suppressed"]

# ---- external cross-check for the county-SUPPRESSED 2021 general -------------------
# Sources: Deseret News & ABC4 2021 Utah municipal results; Town of Alta canvass notice
# on Utah PMN. Counts are unofficial/external and appear ONLY in the note column (never
# in the numeric vote fields, which the county did not release).
ALTA_2021_EXTERNAL = {
    "mayor": {
        "candidates": [("ROGER BOURKE", True)],   # unopposed (Harris Sondak withdrew)
        "note": "Roger Bourke ran unopposed after Harris Sondak withdrew; external "
                "sources report ~60 votes.",
    },
    "council": {
        "candidates": [("JOHN BYRNE", True),        # ordered by external finish
                       ("CAROLYN ANCTIL", True),
                       ("MARGARET E. BOURKE", False)],
        "note": "Winners per external cross-check (Deseret News/ABC4/Town canvass "
                "notice): John Byrne (~53) & Carolyn Anctil (~45); Margaret E. Bourke "
                "(~36) did not win.",
    },
}
SUPPRESS_MSG = ("County SOVC suppressed candidate tallies (insufficient turnout to "
                "protect voter privacy); winners are external/unofficial, not "
                "county-certified. ")


def norm_name(n):
    n = " ".join(n.split())
    for tag in ["(NP )", "(NP)", "(NON )", "(NON)"]:
        n = n.replace(tag, "")
    return " ".join(n.split()).strip()


def fnum(s):
    s = (s or "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def load():
    rows = []
    with open(RAW, newline="") as f:
        for r in csv.DictReader(f):
            if (fnum(r["year"]) or 0) < 2020:
                continue
            cu = r["contest"].upper()
            if "ALTA" not in cu or "CANYON" in cu:   # Town of Alta only (drop Alta Canyon Rec district)
                continue
            rows.append(r)
    return rows


def build():
    contests = {}
    for r in load():
        key = (r["year"], r["contest"])
        c = contests.setdefault(key, {"prec": {}, "source": r["source_file"],
            "vote_for": r["vote_for"], "reg": {}, "method_tc": {}, "suppressed": False})
        cand = norm_name(r["candidate"])
        prec = r["precinct"]
        if prec == "Cumulative":               # workbook rollup label, never a precinct
            continue
        supp = r["suppressed"].strip().lower() == "true"
        votes = fnum(r["votes"])
        reg = fnum(r["registered_voters"])
        tc = fnum(r["times_cast"])
        method = r["vote_method"]
        if reg and reg > 0:
            c["reg"][prec] = max(c["reg"].get(prec, 0.0), reg)
        if tc and tc > 0 and method != "Total":  # per (precinct, method) ballot count; Total is a
            c["method_tc"][(prec, method)] = max(c["method_tc"].get((prec, method), 0.0), tc)  # rollup, skip
        pc = c["prec"].setdefault(prec, {})
        pc.setdefault(cand, {"v": 0.0, "supp": False, "real": False})
        if supp:
            c["suppressed"] = True
            pc[cand]["supp"] = True
        elif votes is not None:
            pc[cand]["v"] += votes
            pc[cand]["real"] = True             # a real (un-suppressed) count exists for this cell

    races, cands, precs = [], [], []
    for (year, contest_verbatim), c in sorted(contests.items()):
        is_mayor = "MAYOR" in contest_verbatim.upper()
        office = "Mayor" if is_mayor else "Council"
        district = "" if is_mayor else "At-Large"
        contest = "Town of Alta Mayor" if is_mayor else "Town of Alta Council At-Large"
        vf = fnum(c["vote_for"])
        n_seats = int(vf) if vf else (1 if is_mayor else 2)
        precincts = sorted(c["prec"].keys())

        totals = {}
        for prec in precincts:
            for cand, d in c["prec"][prec].items():
                totals[cand] = totals.get(cand, 0.0) + d["v"]

        # A contest is only treated as SUPPRESSED (external winners, blank tallies) when it
        # carried suppressed rows AND no real (un-suppressed Total) count was recovered.
        had_real = any(d["real"] for p in c["prec"] for d in c["prec"][p].values())
        use_external = c["suppressed"] and not had_real
        recovered = c["suppressed"] and had_real   # was suppressed; Totals released 2026-07-19

        if use_external:
            ext = ALTA_2021_EXTERNAL["mayor" if is_mayor else "council"]
            order = [nm for nm, _ in ext["candidates"]]
            win = {nm for nm, w in ext["candidates"] if w}
        else:
            order = sorted(totals, key=lambda k: (-totals[k], k))
            win = set(order[:n_seats])

        n_candidates = len(order)
        tot = sum(totals.values())
        total_fcv = "" if use_external else int(tot)
        reg = int(sum(c["reg"].values())) if c["reg"] else ""
        ballots = int(sum(c["method_tc"].values())) if c["method_tc"] else ""
        turnout = round(100.0 * ballots / reg, 2) if (ballots and reg) else ""

        winner = norm_name(order[0]) if order else ""
        losers = [nm for nm in order if nm not in win]
        runner_up = norm_name(losers[0]) if losers else ""
        last_win = order[n_seats - 1] if len(order) >= n_seats else (order[-1] if order else None)

        if use_external:
            winner_votes = winner_pct = runner_up_votes = margin_votes = margin_pct = ""
        else:
            winner_votes = int(totals[order[0]])
            winner_pct = round(100.0 * totals[order[0]] / tot, 2) if tot else ""
            runner_up_votes = int(totals[losers[0]]) if losers else ""
            if losers and last_win is not None:
                margin_votes = int(totals[last_win] - totals[losers[0]])
                margin_pct = round(100.0 * (totals[last_win] - totals[losers[0]]) / tot, 2) if tot else ""
            else:
                margin_votes = margin_pct = ""

        uncontested = n_candidates <= n_seats
        if use_external:
            note = SUPPRESS_MSG + ext["note"]
        elif n_seats > 1:
            note = (f"{n_seats} seats. Winners: " +
                    " & ".join(f"{norm_name(nm)} ({int(totals[nm])})" for nm in order if nm in win) +
                    ". margin = last winning seat - first loser.")
            if recovered:
                note += " " + RECOVER_MSG
        elif recovered:
            note = RECOVER_MSG
        else:
            note = ""

        races.append({"year": year, "election_type": "municipal general", "office": office,
            "district": district, "contest": contest, "contest_verbatim": contest_verbatim,
            "n_seats": n_seats, "n_candidates": n_candidates,
            "voting_method": "plurality" if is_mayor else f"plurality at-large (vote-for-{n_seats})",
            "total_votes": "", "total_first_choice_votes": total_fcv,
            "winner": winner, "winner_votes": winner_votes, "winner_pct": winner_pct,
            "runner_up": runner_up, "runner_up_votes": runner_up_votes,
            "margin_votes": margin_votes, "margin_pct": margin_pct,
            "registered_voters": reg, "ballots_cast": ballots, "turnout_pct": turnout,
            "uncontested": uncontested,
            "suppressed_precincts": ";".join(precincts) if use_external else "",
            "note": note, "source_file": c["source"]})

        for rk, nm in enumerate(order, 1):
            cands.append({"year": year, "election_type": "municipal general", "office": office,
                "district": district, "contest": contest, "candidate": norm_name(nm),
                "votes": "" if use_external else int(totals.get(nm, 0)),
                "pct": "" if (use_external or not tot) else round(100.0 * totals[nm] / tot, 2),
                "rank": rk, "is_winner": nm in win})

        for prec in precincts:
            for nm in order:
                d = c["prec"][prec].get(nm)
                if d is None:
                    continue
                cell_supp = use_external or (d["supp"] and not d["real"])
                precs.append({"year": year, "election_type": "municipal general", "office": office,
                    "district": district, "contest": contest, "precinct": prec,
                    "candidate": norm_name(nm),
                    "votes": "" if cell_supp else int(d["v"]),
                    "suppressed": bool(cell_supp)})

    # Preserve any hand-added cancelled-certification override rows (e.g. the 2025 election
    # cancelled under Utah Code 20A-1-206, Res 2025-R-26 — documented in CLAUDE.md). They are
    # NOT county-derived; carry them through as RAW BYTES (original line endings intact) so a
    # rebuild stays byte-for-byte idempotent. Captured BEFORE the rewrite below.
    cancelled_raw = _read_cancelled_raw(BASE / "alta_races.csv")

    _write(BASE / "alta_races.csv", RACES_HDR, races)
    if cancelled_raw:
        with open(BASE / "alta_races.csv", "ab") as f:
            f.write(cancelled_raw)
    _write(BASE / "alta_results_by_candidate.csv", CAND_HDR, cands)
    _write(BASE / "alta_results_by_precinct.csv", PREC_HDR, precs)
    print(f"races={len(races)} candidates={len(cands)} precinct_rows={len(precs)}")
    for r in races:
        print(f"  {r['year']} {r['contest']:30s} seats={r['n_seats']} n_cand={r['n_candidates']} "
              f"winner={r['winner']:16s} rv={r['registered_voters']} bc={r['ballots_cast']} "
              f"turn={r['turnout_pct']} supp={bool(r['suppressed_precincts'])}")


def _read_cancelled_raw(path):
    """Return the RAW BYTES of any cancelled_certification override lines already on disk
    (hand-maintained per the documented Utah Code 20A-1-206 convention), preserving their exact
    line endings so a rebuild reproduces them byte-for-byte."""
    if not path.exists():
        return b""
    out = []
    with open(path, "rb") as f:
        for line in f:
            if b"cancelled_certification (Utah Code 20A-1-206" in line:
                out.append(line)
    return b"".join(out)


def _write(path, hdr, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    build()
