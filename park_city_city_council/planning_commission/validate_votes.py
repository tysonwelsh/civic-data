#!/usr/bin/env python3
"""
validate_votes.py — sanity checks for the Park City Planning Commission vote data.

Reads the per-meeting JSON under planning_commission/votes/ (and all_votes.csv) and
writes planning_commission/votes/_validation_report.txt:
  * motion / row / meeting counts
  * per-YEAR observed-commissioner roster vs the known 14 appointees + date ranges
    (flags any commissioner appearing OUTSIDE their seated range, and any name in the
    data that is NOT on the roster — there should be none, names are dropped not invented)
  * contested motions (any Nay/Abstain/Recuse) listed with date + tally
  * Recommendation-to-Council vs PC-final-action counts
  * tally-only (names_recorded:false) count
  * roll-call integrity: per-name tally in `result` must equal the number of names

No mayor / no elections checks (appointed body); the Chair votes like any member.
"""
import csv
import json
import os
import re
from collections import defaultdict

PC = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

# Roster surname -> (full name, first-seated YYYY-MM, last-seated YYYY-MM).
ROSTER_RANGES = {
    "John Phillips":      ("2020-01", "2022-07"),
    "Mark Sletten":       ("2020-01", "2020-10"),
    "Doug Thimm":         ("2020-01", "2022-05"),
    "John Kenworthy":     ("2020-01", "2023-06"),
    "Sarah Hall":         ("2020-01", "2025-04"),
    "Laura Suesser":      ("2020-01", "2025-06"),
    "Christin Van Dine":  ("2020-01", "2026-01"),
    "Bill Johnson":       ("2021-05", "2025-11"),  # served through 2025-11-12 (present,
                                                   # voted Nay) per primary minutes
    "John Frontero":      ("2022-08", "2026-05"),
    "Henry Sigg":         ("2022-10", "2026-05"),
    "Rick Shand":         ("2023-07", "2026-05"),
    "Grant Tilson":       ("2025-05", "2026-05"),
    "Seth Beal":          ("2025-07", "2026-05"),
    "Adam Strachan":      ("2026-04", "2026-05"),
}


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = tally_only = contested = recs = finals = others = 0
    by_year_members = defaultdict(set)        # year -> set(full names seen voting)
    member_total = defaultdict(int)
    out_of_range = []
    unknown_names = set()
    integrity_issues = []
    partial_named = 0
    contested_rows = []
    motion_type_ct = defaultdict(int)

    roster_full = set(ROSTER_RANGES)

    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        date = mtg["date"]
        ym = date[:7]
        year = date[:4]
        for v in mtg["votes"]:
            motions += 1
            motion_type_ct[v["motion_type"]] += 1
            at = v.get("action_type")
            if at == "Recommendation":
                recs += 1
            elif at == "Final Action":
                finals += 1
            else:
                others += 1
            if not v["names_recorded"]:
                tally_only += 1
            voters = []
            for b in ("aye", "nay", "abstain", "absent", "recuse"):
                for nm in v.get(b, []):
                    voters.append(nm)
                    if b != "absent":
                        by_year_members[year].add(nm)
                        member_total[nm] += 1
                    if nm not in roster_full:
                        unknown_names.add(nm)
                    else:
                        lo, hi = ROSTER_RANGES[nm]
                        if not (lo <= ym <= hi):
                            out_of_range.append((date, nm, f"seated {lo}..{hi}"))
            # roll-call integrity: a FULL per-name roll call's numeric tally must equal
            # the number of names. The folded / name-only-dissenters grammar
            # (names_mode="partial") legitimately names just the dissenters/abstainers
            # beside a printed tally, so it is NOT held to tally==names — but a partial
            # naming must never CONTRADICT the tally (more nays named than the tally).
            names_mode = v.get("names_mode",
                               "rollcall" if v["names_recorded"] else "tally")
            if names_mode == "rollcall":
                m = re.search(r"(\d+)\s*-\s*(\d+)", v["result"])
                if m:
                    want = int(m.group(1)) + int(m.group(2))
                    got = len(v["aye"]) + len(v["nay"])
                    if want != got:
                        integrity_issues.append(
                            (date, v["motion_no"], v["result"], f"names={got}"))
            elif names_mode == "partial":
                partial_named += 1
                m = re.search(r"(\d+)\s*-\s*(\d+)", v["result"])
                if m and len(v["nay"]) > int(m.group(2)):
                    integrity_issues.append(
                        (date, v["motion_no"], v["result"],
                         f"named nays={len(v['nay'])} > tally nays"))
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested_rows.append((
                    date, v["motion_no"], v["result"],
                    f"aye={len(v['aye'])} nay={len(v['nay'])} "
                    f"abstain={len(v['abstain'])} recuse={len(v['recuse'])}",
                    v["motion"][:70]))
                contested += 1

    # CSV row count
    csv_rows = 0
    if os.path.exists(ALL_VOTES_CSV):
        with open(ALL_VOTES_CSV, newline="", encoding="utf-8") as f:
            csv_rows = sum(1 for _ in csv.reader(f)) - 1

    L = []
    L.append("Park City PLANNING COMMISSION — vote extraction validation report")
    L.append("=" * 70)
    L.append(f"meetings (JSON files) : {meetings}")
    L.append(f"motions extracted     : {motions}")
    L.append(f"all_votes.csv rows    : {csv_rows}")
    L.append(f"tally-only (no names) : {tally_only}")
    L.append(f"names recorded        : {motions - tally_only}")
    L.append(f"  of which partial     : {partial_named}  (folded / name-only-dissenters "
             f"grammar: dissenters/abstainers named beside a printed tally)")
    L.append(f"contested (Nay/Abst.) : {contested}")
    L.append("")
    L.append("action_type breakdown (recommendation-to-Council vs PC-final action):")
    L.append(f"  Recommendation : {recs}")
    L.append(f"  Final Action   : {finals}")
    L.append(f"  Procedural     : {others}")
    L.append("")
    L.append("motion_type taxonomy:")
    for k, c in sorted(motion_type_ct.items(), key=lambda x: -x[1]):
        L.append(f"  {k:28s} {c}")
    L.append("")
    L.append("Per-year observed-commissioner roster (voting appearances):")
    for year in sorted(by_year_members):
        names = sorted(by_year_members[year])
        L.append(f"  {year}: " + ", ".join(names))
    L.append("")
    L.append("Commissioner total voting appearances (vs roster of 14):")
    for nm in sorted(member_total, key=lambda n: -member_total[n]):
        rng = ROSTER_RANGES.get(nm)
        rs = f"  [{rng[0]}..{rng[1]}]" if rng else "  [NOT ON ROSTER]"
        L.append(f"  {nm:20s} {member_total[nm]:4d}{rs}")
    seen = set(member_total)
    missing = roster_full - seen
    if missing:
        L.append("")
        L.append("Roster members with NO recorded per-name vote (tally-only era / "
                 "short tenure): " + ", ".join(sorted(missing)))
    L.append("")
    L.append(f"Names in data NOT on roster (should be 0): {len(unknown_names)}")
    for nm in sorted(unknown_names):
        L.append(f"  ! {nm}")
    L.append("")
    L.append(f"Out-of-range commissioner appearances (should be 0): {len(out_of_range)}")
    for d, nm, info in out_of_range:
        L.append(f"  ! {d}  {nm}  ({info})")
    L.append("")
    L.append(f"Roll-call tally integrity issues (should be 0): {len(integrity_issues)}")
    for d, mno, res, info in integrity_issues:
        L.append(f"  ! {d}  motion {mno}  result={res}  {info}")
    L.append("")
    L.append(f"Contested motions ({contested}):")
    for d, mno, res, tally, mtext in contested_rows:
        L.append(f"  {d}  #{mno}  {res:28s} {tally}  {mtext}")
    L.append("")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {REPORT}")


if __name__ == "__main__":
    main()
