#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the White City PLANNING COMMISSION vote layer (never mutates).

Re-reads the per-meeting JSONs + all_votes.csv and reports:
  1. Motion totals; per-body; named-vs-tally-only; unanimous-vs-contested; motion-type
     + vote-format-mode distribution (narrative / narrative-named-dissent / rollcall).
  2. JSON member-vote rows reconcile 1:1 with all_votes.csv.
  3. Per-year observed-member roster (name -> vote-row count).
  4. Off-roster names (a voter not on the canonical roster) — must be ZERO.
  5. MAX-TALLY / 6th-voter check: any motion with >5 named voters, or a tally-only
     present-count >5.  White City seats mayor/chair + 4 = 5.
  6. Mayor/Chair-vote row count (the chair/mayor VOTES in both eras).
  7. Tally-vs-result reconciliation (printed "X-Y" vs named roll-call counts, where
     both exist — note narrative-named-dissent motions name only the dissenter, so a
     printed tally legitimately exceeds the named-row count: those are NOT flagged).
  8. Full contested-vote list (any Nay / Abstain / Recuse).

Exit 0 = PASS (no off-roster names, no >5 tally, JSON<->CSV reconcile clean, body ok).
Writes votes/_validation_report.txt.
"""
import os, re, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

import extract_votes as E
FULLNAMES = set(E.SURNAME_TO_FULL.values())


def is_mayor_row(member, date):
    if member == "Paulina Flint":
        return True
    if member == "Allan Perry" and date >= "2026-01-01":
        return True
    return False


def load_meetings():
    return [json.load(open(f, encoding="utf-8"))
            for f in sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"),
                                      recursive=True))]


def main():
    meetings = load_meetings()
    lines = []
    def w(s=""): lines.append(s)

    motions = named = tally = unanimous = contested = 0
    mtype = collections.Counter()
    vmode = collections.Counter()
    body_ct = collections.Counter()
    by_year_voter = collections.defaultdict(collections.Counter)
    by_year_mode = collections.defaultdict(collections.Counter)
    csv_expected = 0
    offroster, over5, tally_mismatch, contested_list = [], [], [], []
    mayor_rows = 0
    with_motions = 0

    roster = {}
    if os.path.exists(ROSTER):
        for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
            roster[r["member"]] = (r["first_seen"], r["last_seen"])

    for o in meetings:
        yr = o["date"][:4]
        if o["votes"]:
            with_motions += 1
        for v in o["votes"]:
            motions += 1
            mtype[v["motion_type"]] += 1
            vmode[v.get("vote_mode", "?")] += 1
            body_ct[v["body"]] += 1
            by_year_mode[yr][v.get("vote_mode", "?")] += 1
            members = []
            for g, lab in (("aye","Aye"),("nay","Nay"),("abstain","Abstain"),
                           ("absent","Absent"),("recuse","Recuse")):
                for nm in v.get(g, []):
                    members.append((nm, lab))
            for nm, lab in members:
                if is_mayor_row(nm, o["date"]):
                    mayor_rows += 1
            if v["names_recorded"]:
                named += 1
                csv_expected += len(members)
                nvoters = len(v["aye"])+len(v["nay"])+len(v["abstain"])+len(v["recuse"])
                if nvoters > 5:
                    over5.append(f"{o['date']} m{v['motion_no']}: {nvoters} voters {v['result']}")
                if v["nay"] or v["abstain"] or v["recuse"]:
                    contested += 1
                    contested_list.append(
                        f"{o['date']} [{v['body']}] m{v['motion_no']} ({v.get('vote_mode')}) "
                        f"{v['result']}  nay={v['nay']} abstain={v['abstain']} "
                        f"recuse={v['recuse']} :: {v['motion'][:55]}")
                for nm, lab in members:
                    by_year_voter[yr][nm] += 1
                    if nm not in FULLNAMES:
                        offroster.append(f"{o['date']} m{v['motion_no']}: {nm!r}")
                # tally reconcile only for full roll-call mode (dissent-only naming is
                # legitimately partial)
                if v.get("vote_mode") == "rollcall":
                    mm = re.search(r"(\d+)-(\d+)", v["result"])
                    if mm:
                        a, n = int(mm.group(1)), int(mm.group(2))
                        if a != len(v["aye"]) or n != len(v["nay"]):
                            tally_mismatch.append(
                                f"{o['date']} m{v['motion_no']}: result {v['result']!r} "
                                f"but roll aye={len(v['aye'])} nay={len(v['nay'])}")
            else:
                tally += 1
                csv_expected += 1
                if v.get("tally_only", {}).get("unanimous"):
                    unanimous += 1
                pc = v.get("tally_only", {}).get("present_count")
                if pc and pc > 5:
                    over5.append(f"{o['date']} m{v['motion_no']}: tally present_count={pc}")

    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    bad_body = sum(1 for r in csv_rows if r["body"] not in ("Council", "PlanningCommission"))

    w("White City PLANNING COMMISSION — vote extraction validation")
    w("=" * 58); w()
    w(f"Meetings (JSON)         : {len(meetings)}")
    w(f"Meetings with >=1 vote  : {with_motions}")
    w(f"Motions                 : {motions}")
    w(f"  named roll-calls      : {named}")
    w(f"  tally-only            : {tally}  (of which unanimous: {unanimous})")
    w(f"Body split              : " + " · ".join(f"{k} {c}" for k,c in body_ct.items()))
    w(f"Contested motions       : {contested}")
    w(f"Mayor/Chair-vote rows   : {mayor_rows}  (chair/mayor VOTES in both eras)")
    w(f"Distinct members        : {len(roster)}")
    w()
    w(f"CSV rows                : {csv_count}")
    w(f"Expected (from JSON)    : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body not Council/PC     : {bad_body}")
    w()
    w("Vote-format mode distribution:")
    for k, c in vmode.most_common():
        w(f"    {k:26} {c}")
    w()
    w("Motion-type distribution:")
    for k, c in mtype.most_common():
        w(f"    {k:26} {c}")
    w()
    w("Vote-format mode by year (the ~2026 narrative->rollcall seam):")
    for yr in sorted(by_year_mode):
        w(f"    {yr}: " + ", ".join(f"{m}={c}" for m,c in by_year_mode[yr].most_common()))
    w()
    w(f">5-voter / 6th-voter flags : {len(over5)}   (expected 0 — max seat = 5)")
    for l in over5[:40]: w("    - " + l)
    w()
    w(f"Off-roster names        : {len(offroster)}   (expected 0)")
    for l in offroster[:40]: w("    - " + l)
    w()
    w(f"Roll-call tally mismatches : {len(tally_mismatch)}")
    for l in tally_mismatch[:40]: w("    - " + l)
    w()
    w("Per-year observed members (name: vote rows):")
    for yr in sorted(by_year_voter):
        w(f"  {yr}:")
        for nm, c in by_year_voter[yr].most_common():
            flag = "" if nm in FULLNAMES else "  <<OFF-ROSTER"
            w(f"      {nm:20} {c}{flag}")
    w()
    w(f"Contested votes ({len(contested_list)}):")
    for l in contested_list: w("    - " + l)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    passed = (not offroster) and (csv_count == csv_expected) and bad_body == 0 and not over5
    print("\n".join(lines[:34]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
