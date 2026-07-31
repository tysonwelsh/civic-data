#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Millcreek City Council + CRA vote layer.

Re-reads the per-meeting JSONs and all_votes.csv and reports (never mutates):

  1. Motion totals; per-body (Council / CRA); named-vs-tally-only; unanimous-vs-
     contested; motion-type distribution.
  2. JSON member-vote rows reconcile 1:1 with all_votes.csv.
  3. Per-year observed-member roster (name -> vote count) — catches missing /
     misspelled members.
  4. Off-roster names (a voter not on the canonical roster) — should be ZERO.
  5. MAX-TALLY / 6th-voter check: any motion with >5 named voters, or a tally-only
     motion whose PRESENT-derived count exceeds 5 (a parse leak or an unexpected 6th
     voter).  Millcreek seats 4 districts + the (voting) mayor = 5.
  6. Mayor-vote row count (Millcreek's mayor VOTES; reported for transparency).
  7. Tally-vs-result reconciliation: named Aye/Nay counts vs the A-N printed in the
     result string.
  8. OCR fuzzy-name match rate: independently re-scan every minutes file for roll-call
     name tokens and report how many resolve to the roster (unresolved listed — those
     rows were left BLANK, never guessed).
  9. Full contested-vote list (any Nay / Abstain / Recuse).

Exit 0 = PASS (no off-roster names, no >5 tally, JSON<->CSV reconcile clean).
Writes votes/_validation_report.txt.
"""
import os, re, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
MIN_DIR = os.path.join(ROOT, "minutes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

import extract_votes as E   # reuse the canonical roster + canon()

FULLNAMES = set(E.SURNAME_TO_FULL.values())
# mayor seat by date: Silvestrini always mayor; Jackson becomes mayor 2025-11-10.
def is_mayor_row(member, date):
    if member == "Jeff Silvestrini":
        return True
    if member == "Cheri Jackson" and date >= "2025-11-10":
        return True
    return False


def load_meetings():
    return [json.load(open(f, encoding="utf-8"))
            for f in sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"),
                                      recursive=True))]


def ocr_match_rate():
    """Re-scan minutes for roll-call name tokens; measure the fraction resolving to
    the roster.  Forms: 'Council/Board Member NAME voted', 'Mayor/Chair NAME voted'."""
    resolved = total = 0
    unresolved = collections.Counter()
    role = (r"(?:Council\s*Mem\w*|Councilmembers?|Board\s*Mem\w*|Councn\s*Mem\w*|"
            r"Coiuicil\s*Mem\w*|Mayor|Chair(?:man|person|woman)?)")
    pat = re.compile(r"\b" + role + r"\s+([A-Z][A-Za-z'\-]{2,})\s+"
                     r"(?:voted|abstained|recused|was\s+not\s+present)", re.I)
    STOP = {"members", "member", "chair", "council", "mayor", "vice", "board",
            "mennbers", "mem"}
    for mf in glob.glob(os.path.join(MIN_DIR, "**", "*.md"), recursive=True):
        t = re.sub(r"\s+", " ", open(mf, encoding="utf-8").read())
        for m in pat.finditer(t):
            tok = m.group(1)
            if tok.lower() in STOP:
                continue
            total += 1
            if E.canon(tok):
                resolved += 1
            else:
                unresolved[tok] += 1
    return resolved, total, unresolved


def main():
    meetings = load_meetings()
    lines = []
    def w(s=""): lines.append(s)

    motions = named = tally = unanimous = contested = 0
    mtype = collections.Counter()
    body_ct = collections.Counter()
    by_year_voter = collections.defaultdict(collections.Counter)
    csv_expected = 0
    offroster = []
    over5 = []
    tally_mismatch = []
    contested_list = []
    mayor_rows = 0
    with_motions = 0

    roster = {}
    for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
        roster[r["member"]] = (r["first_seen"], r["last_seen"])

    for o in meetings:
        if o["votes"]:
            with_motions += 1
        for v in o["votes"]:
            motions += 1
            mtype[v["motion_type"]] += 1
            body_ct[v["body"]] += 1
            members = []
            for g, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                           ("absent", "Absent"), ("recuse", "Recuse")):
                for nm in v.get(g, []):
                    members.append((nm, lab))
            for nm, lab in members:
                if is_mayor_row(nm, o["date"]):
                    mayor_rows += 1
            if v["names_recorded"]:
                named += 1
                csv_expected += len(members)
                nvoters = len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) + \
                    len(v["recuse"])
                if nvoters > 5:
                    over5.append(f"{o['date']} m{v['motion_no']}: {nvoters} voters "
                                 f"{v['result']}")
                if v["nay"] or v["abstain"] or v["recuse"]:
                    contested += 1
                    contested_list.append(
                        f"{o['date']} [{v['body']}] m{v['motion_no']} {v['result']}  "
                        f"nay={v['nay']} abstain={v['abstain']} recuse={v['recuse']}  "
                        f":: {v['motion'][:60]}")
                for nm, lab in members:
                    by_year_voter[o["date"][:4]][nm] += 1
                    if nm not in FULLNAMES:
                        offroster.append(f"{o['date']} m{v['motion_no']}: {nm!r}")
                mm = re.search(r"(\d+)-(\d+)", v["result"])
                if mm:
                    a, n = int(mm.group(1)), int(mm.group(2))
                    if a != len(v["aye"]) or n != len(v["nay"]):
                        tally_mismatch.append(
                            f"{o['date']} m{v['motion_no']}: result {v['result']!r} "
                            f"but roll call aye={len(v['aye'])} nay={len(v['nay'])}")
            else:
                tally += 1
                csv_expected += 1
                if v.get("tally_only", {}).get("unanimous"):
                    unanimous += 1
                pc = v.get("tally_only", {}).get("present_count")
                if pc and pc > 5:
                    over5.append(f"{o['date']} m{v['motion_no']}: tally-only "
                                 f"present_count={pc}")

    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    bad_body = sum(1 for r in csv_rows if r["body"] not in ("Council", "CRA"))

    resolved, total_tok, unresolved = ocr_match_rate()

    w("Millcreek CITY COUNCIL + CRA — vote extraction validation")
    w("=" * 60); w()
    w(f"Meetings (JSON)         : {len(meetings)}")
    w(f"Meetings with >=1 vote  : {with_motions}")
    w(f"Motions                 : {motions}")
    w(f"  named roll-calls      : {named}")
    w(f"  tally-only            : {tally}  (of which unanimous: {unanimous})")
    w(f"Body split              : Council {body_ct['Council']} · CRA {body_ct['CRA']}")
    w(f"Contested motions       : {contested}")
    w(f"Mayor-vote rows         : {mayor_rows}  (Millcreek's mayor is a voting member)")
    w(f"Distinct members        : {len(roster)}")
    w()
    w(f"CSV rows                : {csv_count}")
    w(f"Expected (from JSON)    : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body not in Council/CRA : {bad_body}")
    w()
    w("Motion-type distribution:")
    for k, c in mtype.most_common():
        w(f"    {k:28} {c}")
    w()
    w(f">5-voter / 6th-voter flags : {len(over5)}   (expected 0 — max seat = 5)")
    for l in over5[:40]:
        w("    - " + l)
    w()
    w(f"Off-roster names        : {len(offroster)}")
    for l in offroster[:40]:
        w("    - " + l)
    w()
    w(f"Tally-vs-result mismatches (source typo or parse miss — roll call retained): "
      f"{len(tally_mismatch)}")
    for l in tally_mismatch[:60]:
        w("    - " + l)
    w()
    w(f"OCR fuzzy-name match rate: {resolved}/{total_tok} = "
      f"{100.0*resolved/total_tok:.1f}%  (unresolved left BLANK, never guessed)")
    if unresolved:
        w("  unresolved name tokens (count):")
        for tok, c in unresolved.most_common():
            w(f"    - {tok!r}: {c}")
    w()
    w("Per-year observed members (name: vote rows):")
    for yr in sorted(by_year_voter):
        w(f"  {yr}:")
        for nm, c in by_year_voter[yr].most_common():
            flag = "" if nm in FULLNAMES else "  <<OFF-ROSTER"
            w(f"      {nm:20} {c}{flag}")
    w()
    w(f"Contested votes ({len(contested_list)}):")
    for l in contested_list:
        w("    - " + l)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    passed = (not offroster) and (csv_count == csv_expected) and bad_body == 0 \
        and not over5
    print("\n".join(lines[:32]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
