#!/usr/bin/env python3
"""
validate_votes.py — integrity/sanity report for the Taylorsville Planning Commission
vote dataset.  Reads the per-meeting JSONs + all_votes.csv + roster.csv (+ the
minutes_index.csv format column and votes/_extract_stats.json), prints a PASS/FAIL
summary, and PERSISTS the full report to votes/_validation_report.txt.

Checks:
 1. JSON <-> all_votes.csv reconciliation (member-row + motion counts; body/title).
 2. Off-roster members (0 expected — canon only maps roster surnames).
 3. Per-year observed-commissioner roster (name -> vote count).
 4. Named-count vs printed-tally cross-check (LISTED, never auto-corrected).
 5. Result-vs-count consistency (a named 'Approved'/'Positive' whose ayes don't beat nays).
 6. Roster-size per named motion (seated voters vs the 7-member PC — flags vacancies/quorum).
 7. Per-format counts (narrative-tally / named-inline / tabular) + OCR fuzzy-match rate.
 8. Recommendation vs final-action vs procedural; unanimous vs contested.
 9. 'No recorded vote' motions (moved but not voted) + case-number capture.
Full contested-vote list is written to the report.
"""
import csv
import json
import glob
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES = ROOT / "votes"
CSV = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"
INDEX = ROOT / "minutes_index.csv"
REPORT = VOTES / "_validation_report.txt"

LINES = []


def out(s=""):
    LINES.append(str(s))


def load_objs():
    return [json.load(open(f)) for f in sorted(glob.glob(str(VOTES / "*/*/*.json")))]


def main():
    objs = load_objs()
    roster = {r["commissioner"]: (r["first_seen"], r["last_seen"])
              for r in csv.DictReader(open(ROSTER))}
    fmt = {r["date"].strip(): r["format"].strip() for r in csv.DictReader(open(INDEX))}
    stats = json.load(open(VOTES / "_extract_stats.json")) if (VOTES / "_extract_stats.json").exists() else {}

    motions = [(o, m) for o in objs for m in o["votes"]]
    n_meet, n_mot = len(objs), len(motions)
    member_rows = sum(len(m["aye"]) + len(m["nay"]) + len(m["abstain"]) +
                      len(m["absent"]) + len(m["recuse"]) for _, m in motions)

    fails = []

    # ---- 1. reconcile with CSV
    csv_rows = list(csv.DictReader(open(CSV)))
    csv_member_rows = sum(1 for r in csv_rows if r["member"])
    csv_motions = len({(r["date"], r["source"], r["motion_no"]) for r in csv_rows})
    if csv_member_rows != member_rows:
        fails.append(f"CSV member rows {csv_member_rows} != JSON {member_rows}")
    if csv_motions != n_mot:
        fails.append(f"CSV motions {csv_motions} != JSON {n_mot}")
    if any(r["body"] != "PlanningCommission" for r in csv_rows):
        fails.append("non-PlanningCommission body in CSV")
    if any(r["title"] != "Planning Commission" for r in csv_rows):
        fails.append("non-'Planning Commission' title in CSV")

    # ---- 2. off-roster
    off = sorted({nm for _, m in motions for k in
                  ("aye", "nay", "abstain", "absent", "recuse") for nm in m[k]
                  if nm not in roster})
    if off:
        fails.append(f"off-roster members: {off}")

    # ---- 3. per-year roster
    per_year = defaultdict(Counter)
    for o, m in motions:
        for k in ("aye", "nay", "abstain", "absent", "recuse"):
            for nm in m[k]:
                per_year[o["year"]][nm] += 1

    # ---- 4. named vs printed tally, 5. result-vs-count, 6. roster size
    tally_mismatch, result_incons, size_flags = [], [], []
    for o, m in motions:
        if not m["names_recorded"]:
            continue
        aye, nay = len(m["aye"]), len(m["nay"])
        seated = aye + nay + len(m["abstain"]) + len(m["recuse"])
        if m["tally_text"]:
            try:
                a, b = (int(x) for x in m["tally_text"].split("-"))
                if sorted([aye, nay]) != sorted([a, b]) and (aye + nay) != (a + b):
                    tally_mismatch.append(
                        f"{o['date']} m{m['motion_no']}: named {aye}-{nay} "
                        f"(abs {len(m['abstain'])}, rec {len(m['recuse'])}) vs tally "
                        f"{a}-{b} [{fmt.get(o['date'],'?')}]")
            except ValueError:
                pass
        # Check MOTION pass/fail vs the named tally ONLY where the result maps directly to
        # it: procedural "Pass"/"Fail" and recommendation carried/"— motion failed".
        # (final-action Approved/Denied is XOR-derived from the motion verb — a *passed*
        # deny motion is "7-0 Denied", ayes>nays — so it is NOT checked here.)
        r = m["result"]
        if m["kind"] == "procedural":
            carried_label = r.endswith("Pass") or "Pass (" in r
            failed_label = r.endswith("Fail")
        elif m["kind"] == "recommendation":
            failed_label = "motion failed" in r
            carried_label = not failed_label
        else:
            carried_label = failed_label = False
        if carried_label and aye <= nay:
            result_incons.append(f"{o['date']} m{m['motion_no']}: '{r}' "
                                 f"but ayes {aye} !> nays {nay}")
        if failed_label and aye > nay:
            result_incons.append(f"{o['date']} m{m['motion_no']}: '{r}' "
                                 f"but ayes {aye} > nays {nay}")
        if seated and seated not in (5, 6, 7):
            size_flags.append(f"{o['date']} m{m['motion_no']}: {seated} seated "
                              f"[{fmt.get(o['date'],'?')}] — {m['result']}")

    # ---- 7. formats + fuzzy rate
    vf = Counter(m["vote_format"] for _, m in motions)
    ocr_meet = sum(1 for o in objs if fmt.get(o["date"]) == "ocr")
    ocr_mot = sum(1 for o, m in motions if fmt.get(o["date"]) == "ocr")
    res = stats.get("resolutions", 0)
    fuzzy = stats.get("fuzzy", 0) + stats.get("variant", 0)
    fuzzy_rate = (100.0 * fuzzy / res) if res else 0.0

    # ---- 8/9 taxonomy
    rec = sum(1 for _, m in motions if m["kind"] == "recommendation")
    fin = sum(1 for _, m in motions if m["kind"] == "final_action")
    proc = sum(1 for _, m in motions if m["kind"] == "procedural")
    pos_rec = sum(1 for _, m in motions if "Positive recommendation" in m["result"])
    neg_rec = sum(1 for _, m in motions if "Negative recommendation" in m["result"])
    tally_only = sum(1 for _, m in motions if not m["names_recorded"])
    contested = [(o, m) for o, m in motions if m["nay"] or m["abstain"] or m["recuse"]]
    no_vote = [(o["date"], m["motion_no"], m["motion"][:70]) for o, m in motions
               if m["result"] == "No recorded vote"]
    with_case = sum(1 for _, m in motions if m["case_no"])
    named_aye = sum(len(m["aye"]) for _, m in motions)
    named_nay = sum(len(m["nay"]) for _, m in motions)
    named_abs = sum(len(m["abstain"]) for _, m in motions)
    named_absent = sum(len(m["absent"]) for _, m in motions)
    named_rec = sum(len(m["recuse"]) for _, m in motions)

    status = "PASS" if not fails else "FAIL"

    out(f"=== Taylorsville PC vote validation: {status} ===")
    out(f"meetings={n_meet}  motions={n_mot}  member_rows={member_rows}")
    out(f"formats: {dict(fmt_counts(objs, fmt))}   OCR meetings={ocr_meet} "
        f"(motions={ocr_mot})  text meetings={n_meet-ocr_meet}")
    out(f"vote_format: narrative-tally={vf['narrative-tally']}  "
        f"named-inline={vf['named-inline']}  tabular={vf['tabular']}")
    out(f"names_recorded={n_mot-tally_only}  tally_only={tally_only}")
    out(f"kind: recommendation={rec} (pos {pos_rec}/neg {neg_rec})  "
        f"final_action={fin}  procedural={proc}")
    out(f"named votes: Aye={named_aye} Nay={named_nay} Abstain={named_abs} "
        f"Absent={named_absent} Recuse={named_rec}")
    out(f"contested (any Nay/Abstain/Recuse)={len(contested)}  "
        f"unanimous/uncontested={n_mot-len(contested)}")
    out(f"case numbers captured on {with_case}/{n_mot} motions")
    out(f"'No recorded vote' motions (moved, not voted)={len(no_vote)}")
    out(f"OCR name-resolution fuzzy/variant rate: {fuzzy}/{res} = {fuzzy_rate:.2f}%")
    out(f"distinct commissioners (roster.csv)={len(roster)}")

    out("\n--- per-year observed commissioners (name: vote rows) ---")
    for yr in sorted(per_year):
        items = ", ".join(f"{n}:{c}" for n, c in per_year[yr].most_common())
        out(f"  {yr}: {items}")

    out(f"\n--- named vs printed-tally mismatches (advisory, verbatim): {len(tally_mismatch)} ---")
    for x in tally_mismatch:
        out("   " + x)
    out(f"\n--- result-vs-count inconsistencies: {len(result_incons)} ---")
    for x in result_incons:
        out("   " + x)
    out(f"\n--- roster-size flags (seated not in 5/6/7): {len(size_flags)} ---")
    for x in size_flags:
        out("   " + x)
    out(f"\n--- 'No recorded vote' motions: {len(no_vote)} ---")
    for d, mno, mt in no_vote:
        out(f"   {d} m{mno} | {mt}")

    out(f"\n--- contested votes ({len(contested)}) ---")
    for o, m in contested:
        out(f"   {o['date']} m{m['motion_no']} [{m['kind']}] {m['result']} | "
            f"Aye={m['aye']} Nay={m['nay']} Abstain={m['abstain']} Recuse={m['recuse']}")

    if fails:
        out("\nFAILURES:")
        for f in fails:
            out("   " + f)

    report = "\n".join(LINES) + "\n"
    REPORT.write_text(report)
    print(report)
    return status


def fmt_counts(objs, fmt):
    return Counter(fmt.get(o["date"], "?") for o in objs)


if __name__ == "__main__":
    main()
