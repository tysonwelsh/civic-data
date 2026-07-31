#!/usr/bin/env python3
"""
Validate the Planning Commission vote extraction.

Checks (must pass = 0 hard errors; tally mismatches are listed, not auto-fixed):
  0. off-roster members      every member in all_votes.csv appears in some meeting's
                             present/absent roster (no votes by people never seated).
  1. out-of-range dates      every meeting date is within [2020-01-01, today].
  2. tally consistency       for names_recorded=true motions, the aye/nay/abstain/recuse
                             list lengths match the recorded tally and the result's N:N.
  3. JSON<->CSV reconcile    member-vote rows in the JSONs == rows in all_votes.csv.
  4. coverage report         names_recorded (named) vs tally-only share, by source-year.

Exit code 0 if no hard errors (off-roster, out-of-range, JSON/CSV mismatch). Tally
mismatches and tally-only motions are reported but do not fail the run (per the cardinal
rule we flag, never fabricate).
"""

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

PC_DIR = Path(__file__).resolve().parent
VOTES_DIR = PC_DIR / "votes"
ALL_CSV = PC_DIR / "all_votes.csv"

DATA_FLOOR = "2020-01-01"
TODAY = date.today().isoformat()


def load_jsons():
    out = []
    for jf in sorted(VOTES_DIR.rglob("*.json")):
        out.append((jf, json.loads(jf.read_text(encoding="utf-8"))))
    return out


def main():
    jsons = load_jsons()
    print(f"Loaded {len(jsons)} meeting JSONs.")

    # roster universe from present/absent
    roster = set()
    for _, d in jsons:
        m = d.get("meta", {})
        for n in (m.get("present", []) or []) + (m.get("absent", []) or []):
            roster.add(n.strip())

    hard_errors = []
    tally_mismatches = []
    off_roster = []
    out_of_range = []

    n_motions = 0
    n_member_rows = 0
    named = tally_only = 0
    by_year = defaultdict(lambda: {"named": 0, "tally_only": 0})
    recs = finals = procedural = 0
    contested = 0

    for jf, d in jsons:
        meta = d.get("meta", {})
        dt = meta.get("date", "")
        src = meta.get("source", "?")
        yr = meta.get("year", dt[:4])
        if not (DATA_FLOOR <= dt <= TODAY):
            out_of_range.append(f"{jf.name}: date {dt!r}")
        for i, v in enumerate(d.get("votes", []), 1):
            n_motions += 1
            ac = v.get("action_class", "")
            if ac == "recommendation":
                recs += 1
            elif ac == "final_action":
                finals += 1
            else:
                procedural += 1
            nr = bool(v.get("names_recorded"))
            if nr:
                named += 1
                by_year[(src, yr)]["named"] += 1
            else:
                tally_only += 1
                by_year[(src, yr)]["tally_only"] += 1

            lists = {k: [x.strip() for x in (v.get(k, []) or [])]
                     for k in ("aye", "nay", "abstain", "recuse", "absent")}
            for k in ("aye", "nay", "abstain", "recuse"):
                n_member_rows += len(lists[k])
            # contested = any recorded nay (named)
            if lists["nay"]:
                contested += 1

            # off-roster
            for k, members in lists.items():
                for mname in members:
                    if mname and mname not in roster:
                        off_roster.append(f"{dt} m{i}: {mname!r} ({k}) not in roster")

            # tally consistency (only when names recorded)
            tally = v.get("tally", {}) or {}
            if nr:
                for k, tk in (("aye", "yes"), ("nay", "no"), ("abstain", "abstain"),
                              ("recuse", "recuse")):
                    tv = tally.get(tk)
                    if tv is not None and tv != len(lists[k]):
                        tally_mismatches.append(
                            f"{dt} m{i}: {k} list={len(lists[k])} but tally.{tk}={tv} "
                            f"[{v.get('result','')}]")
                # result N:N vs tally
                mres = re.search(r"(\d+)\s*:\s*(\d+)", v.get("result", ""))
                if mres:
                    ry, rn = int(mres.group(1)), int(mres.group(2))
                    if ry != len(lists["aye"]) or rn != len(lists["nay"]):
                        tally_mismatches.append(
                            f"{dt} m{i}: result {ry}:{rn} but aye/nay lists "
                            f"{len(lists['aye'])}/{len(lists['nay'])} "
                            f"[{v.get('motion','')[:50]}]")

    # JSON <-> CSV reconcile
    csv_rows = 0
    if ALL_CSV.exists():
        with open(ALL_CSV, newline="", encoding="utf-8") as f:
            csv_rows = sum(1 for _ in csv.DictReader(f))

    print("\n=== HARD CHECKS ===")
    print(f"off-roster members : {len(off_roster)}")
    for e in off_roster[:50]:
        print("   ", e)
    print(f"out-of-range dates : {len(out_of_range)}")
    for e in out_of_range:
        print("   ", e)
    print(f"JSON member rows={n_member_rows}  CSV rows={csv_rows}  "
          f"{'OK' if n_member_rows == csv_rows else 'MISMATCH'}")
    if n_member_rows != csv_rows:
        hard_errors.append("JSON/CSV row mismatch")

    print("\n=== TALLY MISMATCHES (flagged, not fabricated) ===")
    print(f"count: {len(tally_mismatches)}")
    for e in tally_mismatches[:80]:
        print("   ", e)

    print("\n=== COVERAGE ===")
    print(f"motions={n_motions}  named={named}  tally_only={tally_only}  "
          f"member_rows={n_member_rows}")
    print(f"recommendations={recs}  final_actions={finals}  procedural={procedural}  "
          f"contested(named nay)={contested}")
    print("by source-year (named / tally-only):")
    for (src, yr) in sorted(by_year):
        c = by_year[(src, yr)]
        print(f"   {src:11s} {yr}: {c['named']:3d} / {c['tally_only']:3d}")

    hard = len(off_roster) + len(out_of_range) + len(hard_errors)
    print("\n=== RESULT ===")
    if hard == 0:
        print("PASS (0 hard errors). "
              f"{len(tally_mismatches)} tally mismatches flagged for review.")
    else:
        print(f"FAIL: {hard} hard errors "
              f"(off_roster={len(off_roster)}, out_of_range={len(out_of_range)}, "
              f"other={len(hard_errors)}).")

    # appointment cross-check: PC commissioners confirmed by the City Council appear as
    # appointment rows in ../meeting_minutes/all_votes.csv (matches expected for 2021+).
    appt = {}
    council_csv = PC_DIR.parent / "meeting_minutes" / "all_votes.csv"
    surnames = {n: n.split()[-1].lower() for n in roster}
    if council_csv.exists():
        with open(council_csv, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                blob = (r.get("motion", "") + " " + r.get("motion_type", "")).lower()
                if "planning commission" in blob and re.search(r"appoint", blob):
                    for n, sn in surnames.items():
                        if re.search(r"\b" + re.escape(sn) + r"\b", r.get("motion", "").lower()):
                            appt.setdefault(n, []).append(r.get("date", ""))
    print(f"\n=== APPOINTMENT CROSS-CHECK (council confirmations) ===")
    print(f"PC commissioners with a council appointment row: {len(appt)}")
    for n in sorted(appt):
        print(f"   {n}: {sorted(set(appt[n]))}")

    distinct = len({n for _, d in jsons for n in (d.get('meta', {}).get('present', []) or [])})
    summary = {
        "pc_meetings_parsed": len(jsons),
        "motions": n_motions,
        "member_vote_rows": n_member_rows,
        "recommendations": recs,
        "final_actions": finals,
        "contested": contested,
        "tally_only_motions": tally_only,
        "distinct_commissioners": distinct,
        "roster_path": "planning_commission/roster.csv",
        "validation": "PASS" if hard == 0 else "FAIL",
        "tally_mismatches": len(tally_mismatches),
        "appointment_crosscheck": {n: sorted(set(v)) for n, v in appt.items()},
        "all_votes_csv": "planning_commission/all_votes.csv",
        "notes": ("Pure-regex extraction (no LLM). Named per-member votes where the minutes "
                  "enumerate them (2024-2026 tables/bullets, slcdocs narrative); tally-only "
                  "with names_recorded=false where the minutes give only a count or a "
                  "non-unanimous linearized 'x' table (dissenter unknown, never guessed)."),
    }
    print("\n```json")
    print(json.dumps(summary, indent=2))
    print("```")
    return 0 if hard == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
