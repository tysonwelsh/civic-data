#!/usr/bin/env python3
"""
validate_votes.py — South Jordan Planning Commission vote sanity report.

Reads the per-meeting vote JSONs (votes/**/*.json) produced by extract_votes.py
and reports the integrity checks required for every civic-data vote dataset
(extraction_standards.md §validate_votes). Never mutates data.

Checks:
  1. Totals: meetings, meetings-with->=1-motion, motions, member-vote rows,
     motion_type + action_kind (recommendation / final_action / procedural)
     distributions.
  2. Per-year observed-commissioner roster (name -> vote-row count) + any name
     that is NOT a known commissioner (should be none; CANON-gated at extract).
  3. Tally-vs-named consistency: for a motion that NAMES dissenter(s), the count of
     named Nay members must equal the printed tally's second number. Logged, never
     auto-corrected.
  4. Roster-size / plausibility: tally aye+nay in [1..7]; aye+nay+named-absent <= 7
     (the PC has ~7 seats). Flags out-of-range tallies (parse miss or source typo).
  5. Vote vocabulary conformance.
  6. The full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.
  7. Parse-quality: motions with no mover captured, motions with no numeric tally.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent"}
KNOWN = {  # canonical commissioner full names (mirror extract_votes.CANON values)
    "Michele Hollist", "Nathan Gedge", "Laurel Bevans", "Steven Catmull",
    "Trevor Darby", "Sean Morrissey", "Sam Bishop", "Aaron Starks", "Ray Wimmer",
    "Lori Harding", "Bryan Farnsworth", "Michael Peirce", "Brad Sanderson",
}


def main():
    meetings = motions = rows = 0
    meetings_with_motion = 0
    mtypes = Counter()
    actions = Counter()
    per_year_roster = defaultdict(Counter)   # year -> name -> count
    offroster = Counter()
    tally_mismatch = []
    range_flags = []
    vocab_flags = []
    contested = []
    no_mover = 0
    no_tally = 0
    unanimous = named_dissent = tallyonly_dissent = 0

    for jp in sorted(VOTES_DIR.rglob("*.json")):
        d = json.loads(jp.read_text(encoding="utf-8"))
        meetings += 1
        year = d["year"]
        if d["votes"]:
            meetings_with_motion += 1
        for v in d["votes"]:
            motions += 1
            mtypes[v["motion_type"]] += 1
            actions[v["action_kind"]] += 1
            if not v.get("mover"):
                no_mover += 1
            a, nn = v.get("tally_aye"), v.get("tally_nay")
            if a is None:
                no_tally += 1

            named = {"Nay": v["nay"], "Abstain": v["abstain"],
                     "Recuse": v["recuse"], "Absent": v["absent"], "Aye": v["aye"]}
            # per-year roster + vocab + off-roster
            emitted_any = False
            for label, members in named.items():
                for mnm in members:
                    emitted_any = True
                    per_year_roster[year][mnm] += 1
                    if label not in VOCAB:
                        vocab_flags.append((d["date"], v["motion_no"], label))
                    if mnm not in KNOWN:
                        offroster[mnm] += 1
            rows += len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) \
                + len(v["absent"]) + len(v["recuse"])
            if not emitted_any:
                rows += 1  # placeholder row

            # classification tallies (for the summary trichotomy)
            if a is not None and nn == 0:
                unanimous += 1
            elif (a is not None and nn and nn > 0) or v["nay"]:
                if v["nay"]:
                    named_dissent += 1
                else:
                    tallyonly_dissent += 1

            # (3) tally-vs-named consistency: named nays must equal printed nay count
            if nn is not None and v["nay"] and len(v["nay"]) != nn:
                tally_mismatch.append((d["date"], v["motion_no"],
                                       f"tally {a}-{nn} but {len(v['nay'])} named nay: {v['nay']}"))
            # (4) plausibility
            if a is not None:
                total = a + nn
                if not (1 <= total <= 7):
                    range_flags.append((d["date"], v["motion_no"],
                                        f"aye+nay={total} ({a}-{nn})"))
                if a + nn + len(v["absent"]) > 7:
                    range_flags.append((d["date"], v["motion_no"],
                                        f"aye+nay+absent={a+nn+len(v['absent'])} > 7"))

            # (6) contested
            if v["nay"] or v["abstain"] or v["recuse"] or (nn and nn > 0):
                contested.append((d["date"], v["motion_no"], v["result"],
                                  {"nay": v["nay"], "abstain": v["abstain"],
                                   "recuse": v["recuse"]}))

    _lines = []

    def P(*args):
        line = " ".join(str(a) for a in args)
        _lines.append(line)
        print(line)

    P("=" * 72)
    P("SOUTH JORDAN PLANNING COMMISSION — vote validation")
    P("=" * 72)
    P(f"meetings parsed            : {meetings}")
    P(f"meetings with >=1 motion   : {meetings_with_motion}")
    P(f"motions                    : {motions}")
    P(f"member-vote + placeholder rows (= all_votes.csv data rows): {rows}")
    P(f"body                       : PlanningCommission (all rows)")
    P("")
    P("motion_type distribution:")
    for k, c in mtypes.most_common():
        P(f"   {k:28s} {c}")
    P("action_kind distribution (recommendation vs final-action):")
    for k, c in actions.most_common():
        P(f"   {k:28s} {c}")
    P("")
    P(f"vote classification: unanimous={unanimous}  "
      f"contested-named-dissent={named_dissent}  "
      f"contested-tally-only(dissent unnamed)={tallyonly_dissent}")
    P("")
    P("parse quality:")
    P(f"   motions with no mover captured : {no_mover}")
    P(f"   motions with no numeric tally  : {no_tally}  (verbatim 'unanimous in favor')")
    P("")
    P("per-year observed commissioners (name -> vote rows):")
    for y in sorted(per_year_roster):
        items = ", ".join(f"{n}={c}" for n, c in per_year_roster[y].most_common())
        P(f"   {y}: {items}")
    P("")
    status = "PASS"
    if offroster:
        status = "FAIL"
        P(f"[FAIL] off-roster names (unknown commissioners): {dict(offroster)}")
    else:
        P("[ok] off-roster names: 0")
    if vocab_flags:
        status = "FAIL"
        P(f"[FAIL] out-of-vocabulary vote values: {vocab_flags}")
    else:
        P("[ok] vote-vocabulary: all in {Aye,Nay,Abstain,Recuse,Absent}")
    if tally_mismatch:
        status = "WARN" if status == "PASS" else status
        P(f"[WARN] named-nay vs printed-tally mismatches ({len(tally_mismatch)}):")
        for x in tally_mismatch:
            P(f"       {x[0]} m{x[1]}: {x[2]}")
    else:
        P("[ok] named-nay count == printed tally on every named-dissent motion")
    if range_flags:
        status = "WARN" if status == "PASS" else status
        P(f"[WARN] implausible tallies ({len(range_flags)}):")
        for x in range_flags:
            P(f"       {x[0]} m{x[1]}: {x[2]}")
    else:
        P("[ok] all tallies within 1..7 voters and <=7 seats")
    P("")
    P(f"contested motions (any Nay/Abstain/Recuse or dissent tally): {len(contested)}")
    for date, mn, result, dis in contested:
        detail = {k: v for k, v in dis.items() if v}
        P(f"   {date} m{mn}: {result[:64]}  {detail if detail else '(dissenters unnamed)'}")
    P("")
    P(f"RESULT: {status}")

    VOTES_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print(f"\nWrote {REPORT}")
    return status


if __name__ == "__main__":
    main()
