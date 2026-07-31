#!/usr/bin/env python3
"""Trim trailing EXHIBIT pages (attached resolutions, staff reports, maps) from the minutes
markdown. When SSL bundles minutes after an agenda packet, the tail of the PDF is exhibits
whose forms/rotated labels pdftotext renders as vertical single characters — harmless to the
vote extractor (which keys on the roll-call grammar, all above) but noise in the corpus.

We cut a few lines after the LAST real minutes signal (a member-vote line, a 'vote was …'
narrative, an adjournment, or 'consent of the Commission'). Idempotent; only trims when it
removes a substantial tail. Preserves the provenance header + all attendance/discussion/votes.
"""
import re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DS = [REPO/"meeting_minutes", REPO/"planning_commission"]

VOTE = re.compile(r"^\s*(?:Commissioner|Council\s*Member|Board\s*Member|Chair|Vice[- ]?Chair|"
                  r"Director|Mr\.|Ms\.|Mrs\.)?\.?\s*[A-Za-z][A-Za-z'’.\-]{1,30}?\s*(?::|[–\-—])\s*"
                  r"(Yes|No|Not\s+Present|Absent|Abstain|Recuse|Aye|Nay|Excused)\b", re.I)
END = re.compile(r"adjourn|the vote was|consent of the commission|roll call vote|voice vote|"
                 r"motion (?:passed|carried|failed|denied)", re.I)

def cut_index(lines):
    last = -1
    for i, ln in enumerate(lines):
        if VOTE.match(ln) or END.search(ln):
            last = i
    return last

def main():
    n_trim = 0
    for ds in DS:
        for md in sorted((ds/"minutes").rglob("*.md")):
            text = md.read_text(encoding="utf-8", errors="replace")
            m = re.match(r"(<!--.*?-->\n\n)(.*)$", text, re.S)
            header, body = (m.group(1), m.group(2)) if m else ("", text)
            lines = body.split("\n")
            L = cut_index(lines)
            if L < 0:
                continue
            keep = min(L + 6, len(lines))
            if len(lines) - keep >= 25:          # only trim a substantial exhibit tail
                new = header + "\n".join(lines[:keep]).rstrip() + "\n"
                md.write_text(new, encoding="utf-8")
                n_trim += 1
    print(f"Trimmed exhibit tails from {n_trim} files")

if __name__ == "__main__":
    main()
