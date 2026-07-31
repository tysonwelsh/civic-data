#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered Riverton COUNCIL minutes from
../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Riverton's audited council series starts 2020-02-18 (PMN-derived harvest). The
    pmn_backfill diff (2026-07-13) recovered 5 council meetings the audited layer
    was missing:
      - 2020-01-07, 2020-01-21, 2020-02-04 — PMN Word-era files (.docx/.doc,
        converted with `textutil -convert txt` into ../pmn_backfill/text/), all
        predating the audited series' first meeting.
      - 2023-09-05, 2023-11-07 — Granicus-only (PMN never carried their minutes;
        fetched from rivertoncity.granicus.com DocumentViewer, pdftotext -layout).
    Same clerk grammar the audited parser reads, so this REUSES
    extract_votes.parse_meeting(...) over the text sidecars and merges the result,
    tagged with provenance.

PARSE TOLERANCE (bounded, source text NEVER modified)
    Two early-2020 clerk-era quirks, both handed to the parser as normalized text
    while the stored sidecar/raw files stay verbatim (mirroring the T3.1
    page-header-split roll tolerance precedent):
    1. A few roll-call tokens print with the name-vote hyphen genuinely absent in
       the source document ("McDougalYes", "StewartYes", "WellsYes" — verified
       against the raw .docx XML: no <w:noBreakHyphen/>, the run boundary simply
       carries no hyphen). The voter and vote are both printed and unambiguous, so
       `<RosterSurname>Yes/No` is bridged to `<Surname>-Yes/No`.
    2. ONE site (2020-02-04, council-compensation amendment, a named 3-2 divided
       vote) introduces its full roll call with the standalone phrase
       "Roll Call vote." instead of the corpus-standard "The vote was as
       follows:" — the variant appears nowhere in the audited corpus. It is
       rewritten to the standard introducer (only when immediately followed by a
       roster-surname vote token) so the printed roll call is captured.
    3. ONE site (2020-02-04, Ordinance 20-05 short-term rentals): the clerk wrote
       "Council Member Buroker made a SUBSTITUTE motion to ..." WITHOUT the word
       MOVED (later clerks write "MOVED for a substitute motion", which anchors).
       The 3-2 roll call that follows belongs to the SUBSTITUTE (150 nights), not
       to Stewart's superseded original (185 nights); without an anchor the
       parser would misattribute the substitute's roll call to the original's
       text. Bridged to "... MOVED a SUBSTITUTE motion to ..." so the substitute
       anchors its own motion; the never-voted original window is then skipped by
       the parser's no-vote/no-outcome rule (faithful — it was superseded).

PROVENANCE (trailing 14th all_votes.csv column, flows into the db)
    minutes      — audited council minutes (extract_votes.py)
    pmn_minutes  — recovered meetings (this script)

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent: rebuilds the merged all_votes.csv from canonical rows + a fresh parse.
"""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
import extract_votes as ev  # reuse the audited Riverton council parser

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
BODY = "Council"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]

# roster surnames only; bridges the source's missing name-vote hyphen (see docstring)
ROSTER_ALT = r"(?:Buroker|Haymond|McCay|McDougal|Pierucci|Johnson|Smith|Stewart|Wells)"
MERGED_TOKEN = re.compile(r"\b(" + ROSTER_ALT + r")(Yes|No)\b")
# the single 2020-02-04 nonstandard roll-call introducer (see docstring, tolerance 2)
RC_VARIANT = re.compile(
    r"Roll Call vote\.\s*(?=" + ROSTER_ALT + r"\s*[-–—]\s*(?:Yes|No))")
# the single 2020-02-04 un-anchored substitute motion (see docstring, tolerance 3)
SUBSTITUTE = re.compile(
    r"\b((?:Council\s*Member|Councilmember)\s+" + ROSTER_ALT + r")\s+"
    r"made a SUBSTITUTE motion\b")


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first — canonical all_votes.csv is missing")
    canon_rows, structured = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue                                    # idempotent
            canon_rows.append(r)
            structured.add((r["body"], r["date"]))

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] != BODY:
                continue
            if (BODY, r["date"]) in structured:             # already audited
                continue
            recovered.append(r)

    back_rows = []
    parsed = motions = 0
    for r in sorted(recovered, key=lambda x: x["date"]):
        stem = Path(r["path"]).stem
        path = PMN / "text" / f"{stem}.txt"
        if not path.exists():
            print(f"MISSING text sidecar: {path}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        text = MERGED_TOKEN.sub(r"\1-\2", text)             # parse tolerance only
        text = RC_VARIANT.sub("The vote was as follows: ", text)
        text = SUBSTITUTE.sub(r"\1 MOVED a SUBSTITUTE motion", text)
        votes = ev.parse_meeting(text)
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        if not votes:
            continue
        parsed += 1
        rel_source = f"pmn_backfill/text/{stem}.txt"
        for v in votes:
            motions += 1
            base = {
                "date": r["date"], "year": r["date"][:4], "title": r["title"],
                "body": v["body"], "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            emitted = False
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v.get(key, []):
                    back_rows.append(dict(base, member=member, vote=vote))
                    emitted = True
            for tb in v.get("mayor_tiebreak", []):
                label = "Aye (Mayor tie-break)" if tb["vote"] == "aye" \
                    else "Nay (Mayor tie-break)"
                back_rows.append(dict(base, member=tb["member"], vote=label))
                emitted = True
            if not emitted:
                back_rows.append(dict(base, member="", vote=""))

    out = []
    for r in canon_rows:
        r = dict(r)
        if not r.get("provenance"):
            r["provenance"] = CANON_PROVENANCE
        out.append(r)
    out += back_rows
    out.sort(key=lambda r: (r["date"], r["body"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Riverton council backfill (pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} council meetings / {motions} motions")


if __name__ == "__main__":
    main()
