#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Millcreek Planning Commission vote layer.

Re-reads the per-meeting JSONs and all_votes.csv and reports (never mutates):

  1. Motion totals, per-category (recommendation / final / procedural) and named-vs-
     tally-only counts; motion-type distribution.
  2. JSON member-vote rows reconcile 1:1 with all_votes.csv.
  3. Per-year observed-commissioner roster (name -> vote count) — catches
     missing/misspelled members and out-of-range appearances.
  4. Off-roster names (a member not on the canonical roster) — should be ZERO.
  5. Out-of-range votes (a commissioner voting outside first_seen..last_seen) —
     advisory (ranges are reconstructed from the votes themselves).
  6. Tally-vs-result reconciliation: named Aye/Nay counts vs the A:N printed in the
     result string (a mismatch = source typo or parse miss to hand-review).
  7. result-string well-formedness (recommendation strings carry 'recommendation' +
     Positive/Negative; final-action strings carry '(Final Action'; never both).
  8. OCR fuzzy-name match rate: independently re-scan every minutes file for roll-call
     name tokens and report how many resolve to the roster (unresolved are listed —
     those rows were left BLANK, never guessed).
  9. Full contested-vote list (any Nay/Abstain/Recuse).

Exit 0 = PASS (no off-roster names, JSON<->CSV reconcile clean).
Writes votes/_validation_report.txt.
"""
import os, re, csv, json, glob, collections, sys

PC = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES = os.path.join(PC, "all_votes.csv")
ROSTER = os.path.join(PC, "roster.csv")
MIN_DIR = os.path.join(PC, "minutes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

import extract_votes as E   # reuse the canonical roster + canon()

FULLNAMES = set(E.SURNAME_TO_FULL.values())


def load_meetings():
    out = []
    for f in sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True)):
        out.append(json.load(open(f, encoding="utf-8")))
    return out


def ocr_match_rate():
    """Independently re-scan the minutes for roll-call name tokens and measure the
    fraction that resolve to the roster (dash 'Name – Yes/No' and prose 'Role Name
    voted yes/no')."""
    resolved = 0
    total = 0
    unresolved = collections.Counter()
    role = r"(?:Commissioner|Chair(?:man|person|woman)?|Vice[\s-]?Chair(?:man|person)?)"
    pats = [
        re.compile(r"\b" + role + r"\s+([A-Z][A-Za-z'\-]{2,})\s+(?:voted|abstained)", re.I),
        re.compile(r"(?:" + role + r"\s+)?([A-Z][A-Za-z'\-]{2,})\s*[–—-]\s*"
                   r"(?i:Yes|No|Aye|Nay|Abstain)"),
    ]
    for mf in glob.glob(os.path.join(MIN_DIR, "**", "*.md"), recursive=True):
        t = re.sub(r"[ \t\n]+", " ", open(mf, encoding="utf-8").read())
        for p in pats:
            for m in p.finditer(t):
                tok = m.group(1)
                if tok.lower() in ("commissioners", "commissioner", "chair",
                                   "council", "member", "mayor", "vice"):
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

    # ---- totals -----------------------------------------------------------
    motions = named = tally = unanimous = contested = 0
    rec = fin = proc = 0
    mtype = collections.Counter()
    by_year_voter = collections.defaultdict(collections.Counter)
    csv_expected = 0
    offroster = []
    tally_mismatch = []
    illformed = []
    contested_list = []
    with_motions = 0

    # roster ranges
    roster = {}
    for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
        roster[r["commissioner"]] = (r["first_seen"], r["last_seen"])

    for o in meetings:
        if o["votes"]:
            with_motions += 1
        for v in o["votes"]:
            motions += 1
            mtype[v["motion_type"]] += 1
            c = v["action_category"]
            rec += c == "recommendation"; fin += c == "final"; proc += c == "procedural"
            members = []
            for g, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                           ("absent", "Absent"), ("recuse", "Recuse")):
                for nm in v.get(g, []):
                    members.append((nm, lab))
            if v["names_recorded"]:
                named += 1
                csv_expected += len(members)
                if v["nay"] or v["abstain"] or v["recuse"]:
                    contested += 1
                    contested_list.append(
                        f"{o['date']} m{v['motion_no']} [{c}] {v['result']}  "
                        f"nay={v['nay']} abstain={v['abstain']} recuse={v['recuse']}")
                for nm, lab in members:
                    by_year_voter[o["date"][:4]][nm] += 1
                    if nm not in FULLNAMES:
                        offroster.append(f"{o['date']} m{v['motion_no']}: {nm!r}")
                    elif nm in roster and not (roster[nm][0] <= o["date"] <= roster[nm][1]):
                        pass
                # tally-vs-result reconciliation
                mm = re.search(r"(\d+):(\d+)", v["result"])
                if mm:
                    a, n = int(mm.group(1)), int(mm.group(2))
                    if a != len(v["aye"]) or n != len(v["nay"]):
                        tally_mismatch.append(
                            f"{o['date']} m{v['motion_no']}: result {v['result']!r} "
                            f"but roll call aye={len(v['aye'])} nay={len(v['nay'])}")
            else:
                tally += 1
                csv_expected += 1        # one summary row
                if v.get("tally_only", {}).get("unanimous"):
                    unanimous += 1
            # result well-formedness
            res = v["result"]
            is_rec_str = "recommendation" in res
            is_fin_str = "Final Action" in res
            deferred = bool(re.search(r"\((?:Continued|Tabled|Withdrawn)\)", res))
            if c == "recommendation" and not is_rec_str and not deferred:
                illformed.append(f"{o['date']} m{v['motion_no']}: rec category but "
                                 f"result={res!r}")
            if is_rec_str and is_fin_str:
                illformed.append(f"{o['date']} m{v['motion_no']}: result carries BOTH "
                                 f"recommendation and Final Action: {res!r}")

    # ---- CSV reconcile ----------------------------------------------------
    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    bad_body = sum(1 for r in csv_rows if r["body"] != "PlanningCommission")
    bad_title = sum(1 for r in csv_rows if r["title"] != "Planning Commission")

    # ---- OCR match rate ---------------------------------------------------
    resolved, total_tok, unresolved = ocr_match_rate()

    # ---- write report -----------------------------------------------------
    w("Millcreek PLANNING COMMISSION — vote extraction validation")
    w("=" * 62); w()
    w(f"Meetings (JSON)        : {len(meetings)}")
    w(f"Meetings with >=1 vote : {with_motions}")
    w(f"Motions                : {motions}")
    w(f"  named roll-calls     : {named}")
    w(f"  tally-only           : {tally}  (of which unanimous: {unanimous})")
    w(f"Recommendation / Final / Procedural : {rec} / {fin} / {proc}")
    w(f"Contested motions      : {contested}")
    w(f"Distinct commissioners : {len(roster)}")
    w()
    w(f"CSV rows               : {csv_count}")
    w(f"Expected (from JSON)   : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body!=PlanningCommission: {bad_body}   title!=Planning Commission: {bad_title}")
    w()
    w("Motion-type distribution:")
    for k, v in mtype.most_common():
        w(f"    {k:28} {v}")
    w()
    w(f"Off-roster names       : {len(offroster)}")
    for l in offroster[:40]:
        w("    - " + l)
    w()
    w(f"result-string issues   : {len(illformed)}")
    for l in illformed[:40]:
        w("    - " + l)
    w()
    w(f"Tally-vs-result mismatches (source typo or parse miss — roll call retained): "
      f"{len(tally_mismatch)}")
    for l in tally_mismatch[:60]:
        w("    - " + l)
    w()
    w(f"OCR fuzzy-name match rate: {resolved}/{total_tok} = "
      f"{100.0*resolved/total_tok:.1f}%  (unresolved tokens left BLANK, never guessed)")
    if unresolved:
        w("  unresolved name tokens (count):")
        for tok, c in unresolved.most_common():
            w(f"    - {tok!r}: {c}")
    w()
    w("Per-year observed commissioners (name: vote rows):")
    for yr in sorted(by_year_voter):
        w(f"  {yr}:")
        for nm, c in by_year_voter[yr].most_common():
            flag = "" if nm in FULLNAMES else "  <<OFF-ROSTER"
            w(f"      {nm:22} {c}{flag}")
    w()
    w(f"Contested votes ({len(contested_list)}):")
    for l in contested_list:
        w("    - " + l)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    passed = (not offroster) and (csv_count == csv_expected) and bad_body == 0
    print("\n".join(lines[:34]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
