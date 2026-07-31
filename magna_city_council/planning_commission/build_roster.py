#!/usr/bin/env python3
"""build_roster.py — regenerate planning_commission/roster.csv from the minutes ATTENDANCE
tables.  DERIVED: run it after any change to minutes_index.csv / minutes/.

WHY THIS SCRIPT EXISTS (2026-07-31)
-----------------------------------
roster.csv was originally written by hand at build time with no recorded rule, so it could
not be regenerated — and two of its `last_seen` values pointed at 2023-08-10 / 2024-08-08,
dates that turned out to be PHANTOM meetings (PMN draft copies of 2023-07-13 / 2024-07-11,
de-ingested 2026-07-31; see raw/_duplicate_drafts/README.md).  Rather than hand-patch
un-reproducible numbers, the file is now computed by this documented rule:

  * The MSD 'MEETING MINUTE SUMMARY' opens with an ATTENDANCE block: a `Commissioners`
    column, then `Public Mtg` / `Business Mtg` / `Absent` marker columns, with the Planning
    Staff / DA table repeating the same marker columns further right on the SAME text lines.
    The `Absent` header's own column position is read per-document, so the staff half of the
    line is never mistaken for a commissioner marker.
  * seated       — the commissioner's name is printed in that meeting's attendance block,
                   OR they moved / seconded / cast a named vote in it (all_votes.csv).  The
                   narrative half matters: Commissioner Alder appears ONLY as a seconder,
                   never in an attendance block, so an attendance-only rule would erase a
                   real commissioner.
  * present      — an `x` sits left of the `Absent` column on their row, OR they moved /
                   seconded / cast a named vote (acting in a motion proves presence).
  * first_seen / last_seen = first / last indexed meeting where they were SEATED.
  * meetings_present       = number of indexed meetings where they were PRESENT.

Names are the published surnames (PC minutes print surnames in the narrative; the attendance
block prints full names).  `role` is 'Commissioner' for everyone — the block's parenthetical
(Chair) / (Vice Chair) / (Alternate) rotates and is not a distinct seat.
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
OUT = ROOT / "roster.csv"

# published surname -> regex matching the attendance-block full name
COMMISSIONERS = {
    "Cripps": r"Dan\s+Cripps",
    "Lockwood": r"Ammon\s+Lockwood",
    "Weight": r"Aaron\s+Weight",
    "Elieson": r"Mark\s+Elieson",
    "Richards": r"Todd\s+Richards",
    "VanRoosendaal": r"Sara\s+Van\s?Roosendaal",
    "Taylor": r"Jed\s+Taylor",
    "Collard": r"\w+\s+Collard",
    "Sudbury": r"\w+\s+Sudbury",
    "Alder": r"\w+\s+Alder",
    "Everett": r"\w+\s+Everett",
    "White": r"\w+\s+White",
    "Larson": r"\w+\s+Larson",
    "Shaw": r"\w+\s+Shaw",
}


def attendance_block(text):
    """(lines, absent_col) for the ATTENDANCE table, or (None, None)."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if "ATTENDANCE" in l), None)
    if start is None:
        return None, None
    window = lines[start:start + 30]
    ab = next((l for l in window if re.search(r"\bAbsent\b", l)), None)
    if ab is None:
        return None, None
    return window, ab.index("Absent")


def main():
    seated, present = {}, {}
    rows = list(csv.DictReader(INDEX.open(encoding="utf-8")))
    for r in rows:
        block, absent_col = attendance_block((ROOT / r["path"]).read_text(encoding="utf-8"))
        if block is None:
            print(f"  ! no attendance block: {r['path']}", file=sys.stderr)
            continue
        for line in block:
            for name, pat in COMMISSIONERS.items():
                m = re.search(pat, line)
                if not m:
                    continue
                seated.setdefault(name, set()).add(r["date"])
                # markers strictly left of the Absent column = Public Mtg / Business Mtg
                if "x" in line[m.end():absent_col].lower():
                    present.setdefault(name, set()).add(r["date"])

    # narrative participation the extractor does not emit — procedural hearing gavels
    # ("Alder seconded that motion") and "Commissioner <Surname>" mentions.  Deliberately
    # narrow: a bare surname anywhere in the text would collect public speakers.
    for r in rows:
        text = (ROOT / r["path"]).read_text(encoding="utf-8")
        for name in COMMISSIONERS:
            if re.search(rf"Commissioner\s+{name}\b|{name}\s+(?:seconded|motioned|moved)\b",
                         text):
                seated.setdefault(name, set()).add(r["date"])
                present.setdefault(name, set()).add(r["date"])

    # named/attributed motion action in the extracted vote table
    av = ROOT / "all_votes.csv"
    if av.exists():
        for r in csv.DictReader(av.open(encoding="utf-8")):
            for col in ("mover", "seconder", "member"):
                nm = r.get(col) or ""
                if nm in COMMISSIONERS:
                    seated.setdefault(nm, set()).add(r["date"])
                    present.setdefault(nm, set()).add(r["date"])

    out = []
    for name, dates in seated.items():
        out.append({"name": name, "role": "Commissioner",
                    "first_seen": min(dates), "last_seen": max(dates),
                    "meetings_present": len(present.get(name, ()))})
    out.sort(key=lambda r: (-r["meetings_present"], r["name"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "role", "first_seen", "last_seen",
                                          "meetings_present"])
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {OUT} with {len(out)} commissioners from {len(rows)} indexed meetings")


if __name__ == "__main__":
    main()
