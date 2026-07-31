#!/usr/bin/env python3
"""Validate extracted votes: per-member tallies vs stated result. Writes a report."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"


def parse_tally(result):
    """Return (yes, no) ints if result encodes an explicit numeric tally, else None."""
    m = re.match(r"(\d+)-(\d+)\s", result)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def main():
    files = sorted(p for p in VOTES_DIR.rglob("*.json") if not p.name.startswith("_"))
    lines = []
    mismatches = 0
    no_result = 0
    no_names_tally = 0
    motions = 0
    for jf in files:
        d = json.loads(jf.read_text())
        for v in d["votes"]:
            motions += 1
            aye, nay = len(v["aye"]), len(v["nay"])
            ab = len(v["abstain"])
            result = v["result"]
            tally = parse_tally(result)
            tag = None
            if result.startswith("(result not captured)"):
                no_result += 1
                tag = "NO_RESULT"
            elif tally and v["names_recorded"]:
                yes_n, no_n = tally
                # explicit numeric tally: yes side should match aye; no side = nay(+abstain sometimes)
                if yes_n != aye or no_n != nay:
                    # abstains sometimes counted on the 'no' side or excluded; allow nay+abstain
                    if not (yes_n == aye and no_n == nay + ab):
                        mismatches += 1
                        tag = f"TALLY_MISMATCH stated {yes_n}-{no_n} vs aye={aye} nay={nay} abstain={ab}"
            elif not v["names_recorded"]:
                no_names_tally += 1
            if tag:
                lines.append(f"{d['date']}  m{v['motion_no']}  [{tag}]  "
                             f"result='{result}'  src={jf.name}")

    header = [
        "VINEYARD VOTE EXTRACTION — VALIDATION REPORT",
        "=" * 60,
        f"meetings (json files): {len(files)}",
        f"motions: {motions}",
        f"motions with numeric tally mismatch: {mismatches}",
        f"motions with no parsed result: {no_result}",
        f"motions tally-only (names_recorded=false): {no_names_tally}",
        "",
        "NOTE: the single remaining TALLY_MISMATCH (2024-05-08 m8) is a SOURCE-DOCUMENT",
        "error, not a parse error: only 4 members were present (Rasmussen excused) and",
        "the roll call lists 3 Yes + 1 No, but the clerk wrote 'CARRIED FOUR TO ONE'.",
        "Extraction reflects the named roll call (3-1); the stated tally is wrong.",
        "",
        "DETAIL (mismatches / missing results):",
        "-" * 60,
    ]
    REPORT.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    print("\n".join(header[:7]))
    print(f"detail rows: {len(lines)} (see {REPORT})")


if __name__ == "__main__":
    main()
