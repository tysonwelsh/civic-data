#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the PMN-recovered Magna minutes (5 Council +
7 approved standalone CRA docs) from ../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Magna's audited council layer came from CivicPlus (2022+) + PMN body 5803
    (township era), which together still missed 5 council dates; and the standalone
    Community Reinvestment Agency meetings (PMN body 6925, discovered 2026-07-14)
    were never harvested at all — the audited layer held only 5 CRA dates (all from
    in-recess captures / CivicPlus one-offs). pmn_backfill/ recovered 13 docs
    (5 Council + 8 CRA). They use the same narrative-tally grammar the audited
    parser reads, so this REUSES extract_votes.parse_meeting(...) over the text
    sidecars and merges, tagged with provenance (the ogden/vineyard/orem/
    south_jordan/midvale/herriman promotion pattern).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

BODY
    - Council docs: parse_meeting's own in-doc CRA recess detection applies (the
      audited convention).
    - Standalone CRA docs: doc_body forced to CRA from the pmn index — the whole
      doc is that board's meeting ("Board Member <Name>" roles, already covered by
      the audited ROLE regex).

DRAFT EXCLUSION (verified 2026-07-16)
    The 2025-11-18 CRA doc is stamped "**DRAFT MINUTES – UNAPPROVED**" — it stays a
    pmn_backfill sidecar and is NOT promoted (noted in pmn_backfill/CLAUDE.md).
    The other 12 docs carry approval attestations / "APPROVED" filenames, and each
    CRA attest chain was content-verified (e.g. the 2025-01-14 doc's OCR page
    header misprints "JANUARY 14, 2024"; its adjourn motion + attest block + the
    2025-02-11 approval motion all confirm the true date 2025-01-14).

THE SEAM (inherited from extract_votes.py, keyed off meeting date)
    2024-25 docs: the elected Chair titled "Mayor" (Eric Barney) is one of the five
    and VOTES. 2026+ docs: Mayor Sudbury presides but does NOT vote (parse_meeting
    flags any recorded Sudbury vote as mayor_voted).

RUN (after extract_votes.py — REQUIRED after any extract_votes.py re-run, or the
pmn_minutes rows drop out of all_votes.csv):
    python3 extract_votes.py
    python3 extract_backfill_votes.py
Idempotent. roster.csv is hand-curated (roles/districts) and NOT touched here.
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
import extract_votes as ev

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]
VOTE_KEYS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
             ("absent", "Absent"), ("recuse", "Recuse"))

# (date, body) recovered docs that are NOT promoted, with the reason.
EXCLUDED = {
    ("2025-11-18", "CRA"): "DRAFT MINUTES - UNAPPROVED (stays a pmn_backfill sidecar)",
}


def load_sidecar_lines(path):
    """ev.load_lines + OCR pipe-noise cleanup specific to these tesseract sidecars.

    The 2026 scans carry a right-margin border that tesseract renders as a
    TRAILING "|" on most lines (and some pipe-only lines). Joined into a scan
    window that yields "The motion passed | unanimously; 5-0" — the result
    regexes miss it, the window overruns into the NEXT motion, and a motion is
    silently swallowed (observed on 2026-06-09). Trailing pipes and pipe-only
    lines are pure margin noise, so strip them; LEADING pipes are left alone
    (in this corpus a line-initial "|" is usually an OCR'd "I").
    """
    out = []
    for ln in ev.load_lines(path):
        ln = re.sub(r"\s*\|\s*$", "", ln)
        out.append(ln)
    return out


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first")

    canon_rows, structured = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue                                    # idempotent
            canon_rows.append(r)
            structured.add((r["date"], r["body"]))

    recovered, excluded = [], []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] not in ("Council", "CRA"):
                continue
            if (r["date"], r["body"]) in EXCLUDED:
                excluded.append((r["date"], r["body"],
                                 EXCLUDED[(r["date"], r["body"])]))
                continue
            recovered.append(r)

    back_rows = []
    n_docs = n_motions = 0
    novote = []
    for r in sorted(recovered, key=lambda x: (x["date"], x["body"])):
        tp = PMN / r["text_path"]
        if not tp.exists():
            sys.exit(f"MISSING sidecar: {tp}")
        if (r["date"], r["body"]) in structured:
            # a recovered doc must never re-ingest a meeting the audited layer
            # already structured — verify content by hand before whitelisting
            sys.exit(f"UNEXPECTED (date, body) collision ({r['date']}, {r['body']}) "
                     f"for {tp.name} — verify before merging")
        votes = ev.parse_meeting(load_sidecar_lines(tp), r["date"], r["body"])
        rel_source = f"pmn_backfill/{r['text_path']}"
        if not votes:
            novote.append(rel_source)
            continue
        n_docs += 1
        for k, v in enumerate(votes, start=1):
            n_motions += 1
            base = {
                "date": r["date"], "year": r["year"], "title": r["title"],
                "body": v["body"], "motion_no": k, "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            emitted = False
            for key, vote in VOTE_KEYS:
                for member in v.get(key, []):
                    back_rows.append(dict(base, member=member, vote=vote))
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
    out.sort(key=lambda r: (r["date"], r["body"], r["source"],
                            int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Magna Council+CRA backfill "
                "(pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered docs with motions : {n_docs}\n")
        f.write(f"recovered motions           : {n_motions}\n")
        f.write(f"recovered rows              : {len(back_rows)}\n")
        f.write(f"canonical rows              : {len(canon_rows)}\n")
        f.write(f"merged total rows           : {len(out)}\n")
        f.write(f"zero-motion recovered docs  : {len(novote)}\n")
        for s in novote:
            f.write(f"    novote: {s}\n")
        for d, b, why in excluded:
            f.write(f"excluded (not promoted): {d} {b} — {why}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + "
          f"{len(back_rows)} recovered ({BACKFILL_PROVENANCE}) rows; "
          f"{n_docs} docs / {n_motions} motions; {len(novote)} zero-motion docs; "
          f"{len(excluded)} excluded (draft)")


if __name__ == "__main__":
    main()
