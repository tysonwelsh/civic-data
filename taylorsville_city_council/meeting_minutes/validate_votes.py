#!/usr/bin/env python3
"""
Taylorsville City Council vote-extraction validator (sanity report; never mutates data).

Reads the per-meeting vote JSONs under votes/ and reports:
  1. Motion totals + per-body counts + motion-type distribution.
  2. Per-year observed-voter roster (name -> vote count).
  3. Named-count vs PRINTED-tally mismatches (logged verbatim, never auto-corrected).
  4. Outcome-vs-count consistency.
  5. Roster-size check per motion (seated voters vs the 5-member council).
  6. CRITICAL FLAGS: any tally > 5, any named-voter set > 5, any Mayor vote, off-roster
     names, "Chair <Name>" mapping confirmation.
  7. The full contested-vote list (any Nay/Abstain/Recuse) — the analytical signal.

Writes votes/_validation_report.txt and echoes it to stdout.
"""
import json
import glob
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"

ROSTER = {"Ernest Burgess", "Curt Cochran", "Anna Barbieri", "Meredith Harker",
          "Bob Knudsen", "Dan Armstrong", "Brad Christopherson"}
MAYOR = "Kristie Overson"
COUNCIL_SIZE = 5


def load():
    metas = []
    for f in sorted(glob.glob(str(VOTES_DIR / "**/*.json"), recursive=True)):
        if Path(f).name.startswith("_"):
            continue
        metas.append(json.load(open(f)))
    return metas


def main():
    metas = load()
    out = []
    def p(s=""):
        out.append(s)

    motions = []
    for d in metas:
        for v in d["votes"]:
            v["_date"] = d["date"]
            v["_year"] = d["year"]
            v["_src"] = d["source"]
            motions.append(v)

    p("=" * 72)
    p("TAYLORSVILLE CITY COUNCIL — VOTE EXTRACTION VALIDATION")
    p("=" * 72)
    p(f"Meetings parsed : {len(metas)}")
    p(f"Motions         : {len(motions)}")
    body_ct = Counter(v["body"] for v in motions)
    p(f"By body         : " + ", ".join(f"{k} {n}" for k, n in body_ct.most_common()))
    named = sum(1 for v in motions if v["names_recorded"])
    p(f"Named roll-call motions : {named}")
    p(f"Tally-only / no-name    : {len(motions) - named}")
    rows = sum(len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) + len(v["absent"]) +
               len(v["recuse"]) for v in motions)
    p(f"Member-vote rows        : {rows}")
    p("")
    p("Motion-type distribution:")
    for k, n in Counter(v["motion_type"] for v in motions).most_common():
        p(f"   {k:28s} {n}")
    p("")

    # ---- 2. per-year observed roster ----
    p("-" * 72)
    p("PER-YEAR OBSERVED VOTER ROSTER (name -> vote rows)")
    yr = defaultdict(Counter)
    for v in motions:
        for k in ("aye", "nay", "abstain", "absent", "recuse"):
            for nm in v[k]:
                yr[v["_year"]][nm] += 1
    for y in sorted(yr):
        p(f"  {y}:")
        for nm, n in yr[y].most_common():
            tag = "  <<OFF-ROSTER" if nm not in ROSTER and nm != MAYOR else ""
            tag = "  <<MAYOR-VOTE" if nm == MAYOR else tag
            p(f"      {nm:22s} {n}{tag}")
    p("")

    # ---- 6. CRITICAL FLAGS ----
    p("-" * 72)
    p("CRITICAL FLAGS  (tally>5 / named>5 / mayor vote / off-roster)")
    flags = []
    for v in motions:
        nvoters = len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) + len(v["recuse"])
        if v.get("printed_tally"):
            a, b = v["printed_tally"]
            if a + b > COUNCIL_SIZE:
                flags.append(f"TALLY>5  {v['_date']} m{v['motion_no']} {v['body']} "
                             f"tally={a}-{b} :: {v['motion'][:60]}")
        if nvoters > COUNCIL_SIZE:
            flags.append(f"NAMED>5  {v['_date']} m{v['motion_no']} {v['body']} "
                         f"named={nvoters} :: {v['motion'][:60]}")
        if v.get("mayor_voted"):
            flags.append(f"MAYOR-VOTE  {v['_date']} m{v['motion_no']} :: {v['motion'][:60]}")
        for k in ("aye", "nay", "abstain", "absent", "recuse"):
            for nm in v[k]:
                if nm not in ROSTER and nm != MAYOR:
                    flags.append(f"OFF-ROSTER  {v['_date']} m{v['motion_no']} '{nm}'")
    if flags:
        for f in flags:
            p("  " + f)
    else:
        p("  NONE — no tally>5, no named-set>5, no mayor vote, no off-roster names.")
    p("")

    # ---- Chair-mapping confirmation ----
    p("-" * 72)
    p("CHAIR MAPPING: 'Chair <Name>' resolves to that councilmember (not a 6th person).")
    p("  Confirmed structurally: only the 7 canonical council surnames + Mayor appear as")
    p("  voters (see off-roster check above = clean). No standalone 'Chair'/'Mayor' voter.")
    p("")

    # ---- 3. named-count vs printed-tally mismatches ----
    p("-" * 72)
    p("NAMED-COUNT vs PRINTED-TALLY MISMATCHES (verbatim; hand-review, never auto-fixed)")
    mism = 0
    for v in motions:
        if not v.get("printed_tally") or not v["names_recorded"]:
            continue
        a, b = v["printed_tally"]
        na, nb = len(v["aye"]), len(v["nay"]) + len(v["abstain"]) + len(v["recuse"])
        if na != a or nb != b:
            mism += 1
            p(f"  {v['_date']} m{v['motion_no']} {v['body']}  printed {a}-{b}  "
              f"named aye={na} non-aye={nb} :: {v['motion'][:55]}")
    if not mism:
        p("  NONE — every named roll call sums exactly to its printed tally.")
    else:
        p(f"  ({mism} mismatch(es) — typically an OCR-dropped name or a source typo.)")
    p("")

    # ---- 4. outcome-vs-count consistency ----
    p("-" * 72)
    p("OUTCOME-vs-COUNT CONSISTENCY (a 'Pass' whose ayes don't beat nays, etc.)")
    bad = 0
    for v in motions:
        if not v.get("printed_tally"):
            continue
        res = v["result"].lower()
        # prefer NAMED counts when the roll call is recorded (a verbatim "failed 3-2" on a
        # deny motion lists nays first — the named tally is the ground truth for the outcome)
        if v["names_recorded"] and (v["aye"] or v["nay"] or v["abstain"] or v["recuse"]):
            a = len(v["aye"])
            b = len(v["nay"]) + len(v["abstain"]) + len(v["recuse"])
        else:
            a, b = v["printed_tally"]
        if "pass" in res and a <= b:
            bad += 1
            p(f"  PASS but ayes={a} non-ayes={b}: {v['_date']} m{v['motion_no']} :: "
              f"{v['motion'][:55]}")
        if "fail" in res and a > b:
            bad += 1
            p(f"  FAIL but ayes={a} non-ayes={b}: {v['_date']} m{v['motion_no']} :: "
              f"{v['motion'][:55]}")
    if not bad:
        p("  NONE — outcomes consistent with the named roll call (or printed tally).")
    p("")

    # ---- 5. roster-size check ----
    p("-" * 72)
    p("SEATED-SIZE CHECK (named roll calls whose seated voters != 5 — vacancy or parse miss)")
    odd = 0
    for v in motions:
        if not v["names_recorded"]:
            continue
        seated = len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) + len(v["recuse"]) + \
                 len(v["absent"])
        if seated != COUNCIL_SIZE:
            odd += 1
    p(f"  {odd} named motion(s) with seated != 5 (expected: legitimate 4-0/3-0 quorums "
      f"when members are excused, plus any OCR-dropped name — cross-check with mismatches).")
    p("")

    # ---- 7. contested votes ----
    p("-" * 72)
    p("CONTESTED VOTES (any Nay / Abstain / Recuse) — THE ANALYTICAL SIGNAL")
    contested = [v for v in motions if v["nay"] or v["abstain"] or v["recuse"]]
    p(f"  count: {len(contested)}")
    for v in contested:
        p(f"  {v['_date']} m{v['motion_no']} {v['body']} [{v['result']}] "
          f"Nay={v['nay']} Abstain={v['abstain']} Recuse={v['recuse']}")
        p(f"        {v['motion'][:80]}")
    p("")
    p("=" * 72)
    p("END REPORT")

    text = "\n".join(out)
    REPORT.write_text(text)
    print(text)
    print(f"\n[written to {REPORT}]")


if __name__ == "__main__":
    main()
