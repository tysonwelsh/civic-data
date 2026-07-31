#!/usr/bin/env python3
"""
validate_votes.py — integrity checks for the Logan Planning Commission vote dataset.

Checks (all must pass except the advisory tally cross-check, which only lists
source/OCR discrepancies — it never rewrites the data):
  1. JSON <-> all_votes.csv reconciliation (row counts match).
  2. Every member in a vote row is a known roster commissioner (0 off-roster).
  3. Every per-year observed commissioner falls within their roster first/last-seen
     year range (0 out-of-range).
  4. Tally cross-check: named yea/nay counts vs the numeric "Approved/Denied: a-b"
     tally (orientation in the source is inconsistent, so we compare as a multiset
     and also allow yea+nay == a+b). Mismatches are LISTED, never fixed.
  5. OCR-affected meetings/motions reported separately.
Outputs a PASS/FAIL summary.
"""
import csv, json, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES = ROOT / "votes"
CSV = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"
INDEX = ROOT / "minutes_index.csv"


def load_jsons():
    return [json.load(open(f)) for f in sorted(glob.glob(str(VOTES / "*/*/*.json")))]


def load_roster():
    r = {}
    for row in csv.DictReader(open(ROSTER)):
        r[row["commissioner"]] = (int(row["first_seen"][:4]), int(row["last_seen"][:4]))
    return r


def load_formats():
    fmt = {}
    for row in csv.DictReader(open(INDEX)):
        fmt[row["date"].strip()] = row["format"].strip()
    return fmt


def main():
    objs = load_jsons()
    roster = load_roster()
    fmt = load_formats()
    fails, advis = [], []

    # ---- counts
    n_meet = len(objs)
    motions = [(o, mo) for o in objs for mo in o["votes"]]
    n_mot = len(motions)
    rec = sum(1 for _, m in motions if "recommend" in m["result"].lower())
    fin = sum(1 for _, m in motions if "Final Action" in m["result"])
    proc = n_mot - rec - fin
    contested = sum(1 for _, m in motions if len(m["nay"]) > 0)
    tally_only = sum(1 for _, m in motions if not m["names_recorded"])
    member_rows = sum(len(m["aye"]) + len(m["nay"]) + len(m["abstain"]) +
                      len(m["absent"]) + len(m.get("recuse", [])) for _, m in motions)

    # ---- 1. JSON <-> CSV reconcile
    csv_rows = list(csv.DictReader(open(CSV)))
    csv_member_rows = sum(1 for r in csv_rows if r["member"])
    csv_motions = len({(r["date"], r["motion_no"]) for r in csv_rows})
    if csv_member_rows != member_rows:
        fails.append(f"CSV member rows {csv_member_rows} != JSON {member_rows}")
    if csv_motions != n_mot:
        fails.append(f"CSV motions {csv_motions} != JSON {n_mot}")
    if any(r["body"] != "PlanningCommission" for r in csv_rows):
        fails.append("non-PlanningCommission body value in CSV")
    if any(r["title"] != "Planning Commission" for r in csv_rows):
        fails.append("non-'Planning Commission' title in CSV")

    # ---- 2. off-roster members
    off = set()
    for o, m in motions:
        for k in ("aye", "nay", "abstain", "absent", "recuse"):
            for nm in m.get(k, []):
                if nm not in roster:
                    off.add(nm)
    if off:
        fails.append(f"off-roster members: {sorted(off)}")

    # ---- 3. per-year observed within roster range
    oor = []
    for o, m in motions:
        yr = o["year"]
        for k in ("aye", "nay", "abstain", "absent", "recuse"):
            for nm in m.get(k, []):
                if nm in roster:
                    lo, hi = roster[nm]
                    if not (lo <= yr <= hi):
                        oor.append((nm, yr, o["date"]))
    if oor:
        fails.append(f"out-of-range commissioner-years: {sorted(set((n,y) for n,y,_ in oor))}")

    # ---- 4. tally cross-check (advisory)
    for o, m in motions:
        if not m["names_recorded"] or not m["tally_text"]:
            continue
        try:
            a, b = [int(x) for x in m["tally_text"].split("-")]
        except ValueError:
            continue
        yea, nay = len(m["aye"]), len(m["nay"])
        if sorted([yea, nay]) != sorted([a, b]) and (yea + nay) != (a + b):
            advis.append(f"{o['date']} m{m['motion_no']}: named {yea}-{nay} "
                         f"(abs {len(m['abstain'])}) vs tally {a}-{b} [{fmt.get(o['date'],'?')}]")

    # ---- 5. OCR breakdown
    ocr_meet = sum(1 for o in objs if fmt.get(o["date"]) == "ocr")
    ocr_mot = sum(1 for o, m in motions if fmt.get(o["date"]) == "ocr")

    status = "PASS" if not fails else "FAIL"
    print(f"=== Logan PC vote validation: {status} ===")
    print(f"meetings={n_meet}  motions={n_mot}  member_rows={member_rows}")
    print(f"recommendations={rec}  final_actions={fin}  procedural={proc}")
    print(f"contested={contested}  tally_only={tally_only}")
    print(f"distinct_commissioners={len(roster)}")
    print(f"OCR meetings={ocr_meet}  OCR motions={ocr_mot}  (text meetings={n_meet-ocr_meet})")
    print(f"tally cross-check discrepancies (advisory): {len(advis)}")
    for a in advis:
        print("   ", a)
    if fails:
        print("FAILURES:")
        for f in fails:
            print("   ", f)
    return status, advis


if __name__ == "__main__":
    main()
