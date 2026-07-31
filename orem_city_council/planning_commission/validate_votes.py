#!/usr/bin/env python3
"""
Validate the Orem Planning Commission vote extraction (PURE PYTHON, no network/LLM).

Checks:
  1. JSON <-> all_votes.csv reconciliation (member-vote row counts match).
  2. 0 off-roster members (every member in all_votes.csv is a known commissioner in roster.csv).
  3. Per-motion consistency: outcome vs aye/nay; no member in both aye & nay; <=7 voters
     (7 PC seats); non-empty member lists when names_recorded.
  4. OCR vs born-digital coverage note.
  5. Every index row produced a JSON.

Writes planning_commission/votes/_validation_report.txt and prints a summary.
Run: python3 planning_commission/validate_votes.py
"""
import csv
import glob
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
VOTES_DIR = os.path.join(SCRIPT_DIR, "votes")
ALL_VOTES_CSV = os.path.join(SCRIPT_DIR, "all_votes.csv")
ROSTER_CSV = os.path.join(SCRIPT_DIR, "roster.csv")
INDEX_CSV = os.path.join(SCRIPT_DIR, "minutes_index.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
MAX_SEATS = 7


def main():
    lines = []
    def out(s=""):
        lines.append(s)

    out("OREM PLANNING COMMISSION — VOTE EXTRACTION VALIDATION REPORT")
    out("=" * 62)
    out("")

    # roster
    roster = set()
    with open(ROSTER_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            roster.add(r["member"])

    # JSONs
    json_files = sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True))
    json_member_rows = 0
    json_motions = 0
    tally_mismatches = []
    for jf in json_files:
        d = json.load(open(jf, encoding="utf-8"))
        for v in d["votes"]:
            json_motions += 1
            aye, nay = v["aye"], v["nay"]
            abstain, recuse = v.get("abstain", []), v.get("recuse", [])
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                json_member_rows += len(v.get(k, []))
            if not v["names_recorded"]:
                if aye or nay or abstain or recuse:
                    tally_mismatches.append((d["date"], v["motion_no"],
                                             "names_recorded=false but member lists non-empty"))
                continue
            probs = []
            overlap = set(aye) & set(nay)
            if overlap:
                probs.append(f"member in aye&nay: {sorted(overlap)}")
            total = len(aye) + len(nay) + len(abstain) + len(recuse)
            if total > MAX_SEATS:
                probs.append(f"{total} voters > {MAX_SEATS} seats")
            if total == 0:
                probs.append("names_recorded but all lists empty")
            # outcome vs tally (only when no supermajority note in result)
            oc = v.get("outcome", "")
            if "Final Action" not in v["result"] and "recommendation" not in v["result"].lower():
                pass
            if oc == "Passed" and len(aye) < len(nay):
                probs.append(f"Passed but aye({len(aye)})<nay({len(nay)})")
            if probs:
                tally_mismatches.append((d["date"], v["motion_no"], "; ".join(probs)))

    # CSV
    csv_rows = list(csv.DictReader(open(ALL_VOTES_CSV, newline="", encoding="utf-8")))
    off_roster = sorted({r["member"] for r in csv_rows if r["member"] not in roster})
    bad_body = sorted({r["body"] for r in csv_rows if r["body"] != "PlanningCommission"})
    bad_title = sorted({r["title"] for r in csv_rows if r["title"] != "Planning Commission"})

    # index reconcile
    index_rows = list(csv.DictReader(open(INDEX_CSV, newline="", encoding="utf-8")))
    json_dates = {json.load(open(jf, encoding="utf-8"))["date"] for jf in json_files}
    index_dates = {r["date"] for r in index_rows}
    missing_json = sorted(index_dates - json_dates)
    fmt = {}
    for r in index_rows:
        fmt[r["format"]] = fmt.get(r["format"], 0) + 1

    out(f"Index rows                 : {len(index_rows)}")
    out(f"Per-meeting JSON files     : {len(json_files)}")
    out(f"Meetings missing a JSON    : {len(missing_json)} {missing_json}")
    out(f"Motions (JSON)             : {json_motions}")
    out(f"Member-vote rows (JSON)    : {json_member_rows}")
    out(f"Member-vote rows (CSV)     : {len(csv_rows)}")
    out(f"JSON<->CSV row match       : {'OK' if json_member_rows == len(csv_rows) else 'MISMATCH'}")
    out(f"Distinct commissioners     : {len(roster)}")
    out(f"Off-roster members in CSV  : {len(off_roster)} {off_roster}")
    out(f"Rows with body != Planning : {bad_body}")
    out(f"Rows with bad title        : {bad_title}")
    out(f"Tally/consistency issues   : {len(tally_mismatches)}")
    out(f"Source format breakdown    : {fmt}  (OCR = lower fidelity, born-digital text/docx preferred)")
    out("")
    if tally_mismatches:
        out("--- tally / consistency issues ---")
        for d, mn, p in tally_mismatches:
            out(f"  {d} motion #{mn}: {p}")
        out("")

    # per-year roster
    out("--- roster by year (members appearing in recorded votes or attendance) ---")
    by_year = {}
    with open(ROSTER_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for y in r["years_active"].split(";"):
                if y:
                    by_year.setdefault(y, []).append(r["member"])
    for y in sorted(by_year):
        out(f"  {y}: {len(by_year[y])}  {', '.join(sorted(by_year[y]))}")
    out("")

    ok = (json_member_rows == len(csv_rows) and not off_roster and not bad_body
          and not bad_title and not missing_json and not tally_mismatches)
    out("RESULT: " + ("ALL CHECKS PASS" if ok else "SEE ISSUES ABOVE"))

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return {
        "json_member_rows": json_member_rows, "csv_rows": len(csv_rows),
        "off_roster": off_roster, "tally_mismatches": tally_mismatches,
        "missing_json": missing_json, "reconcile_ok": json_member_rows == len(csv_rows),
        "all_pass": ok, "distinct": len(roster), "fmt": fmt,
    }


if __name__ == "__main__":
    main()
