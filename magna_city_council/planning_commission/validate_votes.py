#!/usr/bin/env python3
"""validate_votes.py — sanity-check extracted Magna Planning Commission vote JSONs.
Writes votes/_validation_report.txt: motion totals, per-year observed commissioners,
non-roster names, outcome consistency, and the contested-vote list (named dissent/abstain).
PC outcomes are TALLY-ONLY unanimous on most motions (majority unnamed by source).

Also runs the DOCUMENT-DATE GUARD (added 2026-07-31): every indexed minutes document must
carry the meeting date it is filed under. See check_dates() — this is the check that catches
the PMN draft-copy trap that manufactured four phantom PC meetings before 2026-07-31.
`--check-dates` makes a month/day mismatch a non-zero exit."""
import json, os, re, sys, csv
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
INDEX = os.path.join(REPO, "minutes_index.csv")
ROSTER = {"Richards", "Weight", "Cripps", "Elieson", "VanRoosendaal", "Lockwood", "Collard",
          "Taylor", "Larson", "White", "Alder", "Shaw", "Everett", "Sudbury"}


MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
HDR_RE = re.compile(
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),?\s+(\d{4})")


def check_dates():
    """DOCUMENT-DATE GUARD.

    Utah PMN body 1559 attaches minutes to a notice TWO different ways:
      * `YYMMDD_MagnaPC_MinutesApproved.pdf` — the APPROVED minutes of that notice's OWN
        meeting.  The notice date is correct.
      * `<Month> minutes.pdf` — the DRAFT minutes of the PREVIOUS meeting, posted with this
        meeting's agenda packet because this meeting is the one that will approve them.
        The notice date is WRONG for this file by one meeting.

    Ingesting the second kind under the notice date manufactures a PHANTOM meeting that
    double-counts the previous meeting's motions.  That is exactly what happened on the four
    notices where MSD never posted an approved copy (2023-08-10, 2023-10-12, 2024-08-08,
    2025-10-16 — de-ingested 2026-07-31, see raw/_duplicate_drafts/README.md and
    minutes_unrecovered.csv).

    The guard: the MSD 'MEETING MINUTE SUMMARY' header names the meeting date in-body.  Its
    MONTH+DAY must equal the index date.  The YEAR is only WARNed on — the MSD clerk typo'd
    the year on several 2023 documents ('Thursday, April 13, 2022'), which is a source typo,
    not a misdate.

    Returns (fails, warns) as lists of human-readable strings.
    """
    fails, warns = [], []
    if not os.path.exists(INDEX):
        return fails, warns
    for r in csv.DictReader(open(INDEX, encoding="utf-8")):
        p = os.path.join(REPO, r["path"])
        if not os.path.exists(p):
            fails.append(f"{r['date']}: indexed file missing on disk -> {r['path']}")
            continue
        txt = open(p, encoding="utf-8").read()
        body = txt.split("---", 1)[-1]          # skip the provenance header block
        m = HDR_RE.search(body)
        if not m:
            warns.append(f"{r['date']}: no in-body meeting-date header found ({r['path']})")
            continue
        mon, day, yr = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3))
        iy, im, idd = (int(x) for x in r["date"].split("-"))
        if (mon, day) != (im, idd):
            fails.append(f"{r['date']}: in-body header says {m.group(0)} -> filed under the "
                         f"WRONG date (PMN draft-copy trap?) [{r['path']}]")
        elif yr != iy:
            warns.append(f"{r['date']}: in-body year {yr} != index year {iy} "
                         f"(known MSD clerk year-typo era) [{r['path']}]")
    return fails, warns


def main():
    enforce = "--check-dates" in sys.argv
    meetings = motions = mtgs_with = 0
    type_counts = Counter(); per_year = defaultdict(Counter); unknown = Counter()
    contested = []; land_use = 0
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if not fn.endswith(".json") or fn.startswith("_"):
                continue
            mtg = json.load(open(os.path.join(dp, fn), encoding="utf-8"))
            meetings += 1
            if mtg["votes"]:
                mtgs_with += 1
            year = mtg["date"][:4]
            for v in mtg["votes"]:
                motions += 1
                type_counts[v["motion_type"]] += 1
                if v["motion_type"] == "Land-Use/Zoning":
                    land_use += 1
                for nm in v["nay"] + v["abstain"] + v["recuse"] + v["aye"] + v["absent"]:
                    per_year[year][nm] += 1
                    if nm not in ROSTER:
                        unknown[nm] += 1
                if v["nay"] or v["abstain"] or v["recuse"]:
                    contested.append(f"{mtg['date']} m{v['motion_no']} {v['result']} | "
                                     f"NAY={v['nay']} ABSTAIN={v['abstain']} :: {v['motion'][:75]}")
    L = []; w = L.append
    w("Magna Planning Commission — vote extraction validation report")
    w("=" * 74)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >= 1 motion : {mtgs_with}")
    w(f"Motions extracted         : {motions}   (Land-Use/Zoning: {land_use})")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("\n" + "-" * 74)
    w("PER-YEAR OBSERVED COMMISSIONERS (appear only on named dissent/abstain — most")
    w("motions are tally-only 'unanimous in favor', majority unnamed by source).")
    w("-" * 74)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            w(f"   {nm:18s} {c}{'  <-- NON-ROSTER' if nm not in ROSTER else ''}")
    if unknown:
        w("\nNON-ROSTER NAMES receiving a vote row:")
        for nm, c in unknown.most_common():
            w(f"   {nm} ({c})")
    w("\n" + "-" * 74)
    w(f"CONTESTED VOTES (named Nay/Abstain) — the signal: {len(contested)}")
    w("-" * 74)
    for ln in contested or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)

    fails, warns = check_dates()
    w("\n" + "-" * 74)
    w("DOCUMENT-DATE GUARD (in-body MSD header date vs index date; catches the PMN")
    w("'<Month> minutes.pdf' draft-copy trap that manufactures phantom meetings)")
    w("-" * 74)
    w(f"   FAIL: {len(fails)}    WARN: {len(warns)}")
    for ln in fails:
        w("   FAIL " + ln)
    for ln in warns:
        w("   WARN " + ln)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} contested={len(contested)} "
          f"non_roster={len(unknown)} land_use={land_use}")
    print(f"date_guard: fails={len(fails)} warns={len(warns)}")
    for ln in fails:
        print("  FAIL " + ln)
    if fails and enforce:
        sys.exit(1)


if __name__ == "__main__":
    main()
