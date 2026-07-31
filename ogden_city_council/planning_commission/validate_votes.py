#!/usr/bin/env python3
"""
validate_votes.py - QA for the Ogden Planning Commission vote extraction.

Checks (writes planning_commission/votes/_validation_report.txt):
  1. 0 off-roster members (every member in all_votes.csv must be in roster.csv).
  2. JSON <-> CSV reconciliation (motion + member-vote-row counts agree).
  3. Per-year observed voters (sanity on the rosters).
  4. Tally mismatches: motions with both a named roll-call and an explicit "passed N-M"
     tally where the counted names disagree with the stated tally.
  5. OCR vs born-digital coverage note.
  6. Appointment cross-check against meeting_minutes/all_votes.csv (council appoints PC).
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
CSV_PATH = ROOT / "all_votes.csv"
ROSTER_PATH = ROOT / "roster.csv"
REPORT = VOTES_DIR / "_validation_report.txt"
COUNCIL_CSV = REPO / "meeting_minutes" / "all_votes.csv"

def main():
    lines = []
    def out(s=""):
        lines.append(s)

    idx = [{k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
           for r in csv.DictReader(open(INDEX))]
    fmt = {r["date"]: r.get("format", "") for r in idx}

    roster = {r["commissioner"] for r in csv.DictReader(open(ROSTER_PATH))}
    csv_rows = list(csv.DictReader(open(CSV_PATH)))

    out("=" * 70)
    out("OGDEN PLANNING COMMISSION - vote extraction validation")
    out("=" * 70)

    # ---- JSON inventory
    jsons = sorted(VOTES_DIR.rglob("*.json"))
    n_meetings = len(jsons)
    json_motions = 0
    json_rows = 0
    tally_mismatches = []
    per_year_voters = defaultdict(Counter)
    recs = finals = procedural = contested = tally_only = 0
    ocr_meetings = born_meetings = 0
    for jp in jsons:
        obj = json.loads(jp.read_text())
        if obj.get("format") == "ocr":
            ocr_meetings += 1
        else:
            born_meetings += 1
        year = obj["year"]
        for mo in obj["votes"]:
            json_motions += 1
            res = mo["result"]
            if res.startswith("Positive recommendation") or res.startswith("Negative recommendation"):
                recs += 1
            elif "(Final Action)" in res:
                finals += 1
            else:
                procedural += 1
            members = (mo["aye"] + mo["nay"] + mo["abstain"] + mo["absent"] + mo["recuse"])
            if members:
                json_rows += len(members)
            else:
                json_rows += 1  # one empty placeholder row
            if mo["nay"] or mo["abstain"] or mo["recuse"]:
                contested += 1
            if not mo["names_recorded"]:
                tally_only += 1
            for m in members:
                per_year_voters[year][m] += 1
            # integrity: no member counted in two lists; <=10 voters/motion
            lists = {"aye": mo["aye"], "nay": mo["nay"], "abstain": mo["abstain"],
                     "absent": mo["absent"], "recuse": mo["recuse"]}
            allmem = mo["aye"] + mo["nay"] + mo["abstain"] + mo["absent"] + mo["recuse"]
            if len(allmem) != len(set(allmem)):
                tally_mismatches.append((obj["date"], mo["motion_no"], "member in two lists"))
            if len(allmem) > 10:
                tally_mismatches.append((obj["date"], mo["motion_no"],
                                         f"{len(allmem)} voters (>10 seats)"))
            # named roll-call vs the clerk's explicit 'passed N-M' tally in the source
            if mo["names_recorded"] and mo.get("explicit_tally"):
                ea, en = mo["explicit_tally"]
                if (len(mo["aye"]), len(mo["nay"])) != (ea, en):
                    tally_mismatches.append(
                        (obj["date"], mo["motion_no"],
                         f"named {len(mo['aye'])}:{len(mo['nay'])} vs stated {ea}:{en}"))

    # ---- off-roster check
    off = Counter()
    for r in csv_rows:
        if r["member"] and r["member"] not in roster:
            off[r["member"]] += 1

    # ---- CSV reconcile
    csv_motions = len(set((r["source"], r["motion_no"]) for r in csv_rows))
    csv_member_rows = sum(1 for r in csv_rows if r["member"])

    out("")
    out(f"meetings parsed           : {n_meetings}  (born-digital {born_meetings}, OCR {ocr_meetings})")
    out(f"motions (JSON)            : {json_motions}")
    out(f"motions (CSV distinct)    : {csv_motions}")
    out(f"all_votes.csv rows        : {len(csv_rows)}")
    out(f"member-vote rows (CSV)    : {csv_member_rows}")
    out(f"member-vote rows (JSON)   : {sum(1 for jp in jsons for mo in json.loads(jp.read_text())['votes'] for _ in (mo['aye']+mo['nay']+mo['abstain']+mo['absent']+mo['recuse']))}")
    out(f"recommendations           : {recs}")
    out(f"final actions             : {finals}")
    out(f"procedural                : {procedural}")
    out(f"contested motions         : {contested}")
    out(f"tally-only motions        : {tally_only}")
    out("")
    out(f"JSON motions == CSV motions : {'OK' if json_motions == csv_motions else 'MISMATCH'}")
    out(f"JSON rows   == CSV rows     : {'OK' if json_rows == len(csv_rows) else 'MISMATCH %d/%d' % (json_rows, len(csv_rows))}")
    out("")

    # ---- off-roster
    if not off:
        out("off-roster members        : 0  (PASS - every voter is on the reconstructed roster)")
    else:
        out(f"off-roster members        : {sum(off.values())} rows  (FAIL)")
        for m, c in off.most_common():
            out(f"   {m!r}: {c}")
    out("")

    # ---- vote distribution
    vd = Counter(r["vote"] for r in csv_rows if r["vote"])
    out("vote distribution         : " + ", ".join(f"{k} {v}" for k, v in vd.most_common()))
    out("")

    # ---- tally mismatches
    if not tally_mismatches:
        out("tally mismatches          : 0  (named counts agree with stated tallies; "
            "no member double-listed; <=10 voters/motion)")
    else:
        out(f"tally mismatches          : {len(tally_mismatches)}")
        for d, mn, why in tally_mismatches:
            out(f"   {d} motion {mn}: {why}")
    out("")

    # ---- per-year observed voters
    out("per-year observed voters (named roll-calls only):")
    for y in sorted(per_year_voters):
        names = ", ".join(sorted(per_year_voters[y]))
        out(f"  {y}: {len(per_year_voters[y])} voters - {names}")
    out("")

    # ---- appointment cross-check against the council minutes
    out("appointment cross-check (council all_votes.csv -> PC appointments):")
    appt_names = set()
    if COUNCIL_CSV.exists():
        for r in csv.DictReader(open(COUNCIL_CSV)):
            m = r.get("motion", "") or ""
            if "PLANNING COMMISSION" in m.upper() and re.search(r"APPOINT|RATIF", m.upper()):
                for sn in roster:
                    last = sn.split()[-1].upper()
                    if re.search(r"\b" + re.escape(last) + r"\b", m.upper()):
                        appt_names.add(sn)
        out(f"  roster names confirmed by a council appointment vote: {len(appt_names)}")
        out("  " + ", ".join(sorted(appt_names)))
        unconfirmed = sorted(roster - appt_names)
        out(f"  roster names NOT found in a council appointment motion: {len(unconfirmed)}")
        out("  " + ", ".join(unconfirmed))
    else:
        out("  council all_votes.csv not found - skipped")
    out("")

    # ---- coverage by year/format
    out("coverage by year (index):")
    yc = Counter((r["year"], r.get("format", "")) for r in idx)
    for (y, f), c in sorted(yc.items()):
        out(f"  {y} {f}: {c}")
    out("")
    out("note: 2020-2023 (+4 of 2024) are born-digital mixed-case prose; 2024-2026 are")
    out("OCR'd uppercase roll-calls. OCR files have noisier names (folded fuzzily over the")
    out("reconstructed surname list); born-digital named tallies parse from the")
    out("'with Commissioners ... voting aye [and ... voting no]' clause.")

    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n-> {REPORT}")

if __name__ == "__main__":
    main()
