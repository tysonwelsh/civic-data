#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered Alta Planning Commission
minutes from ../pmn_backfill/ into planning_commission/all_votes.csv.

WHY
    The audited harvest filtered on PMN's "(Meeting Minutes)" attachment LABEL;
    the PC minutes below were posted under a "Public Information Handout" label
    and were invisible to it. Recovered 2026-07-13 into ../pmn_backfill/ and
    verified against their internal headers; promoted 2026-07-16. Same clerk
    format the audited parser reads, so this REUSES
    extract_votes.parse_meeting(...) and merges, tagged with provenance
    (the ogden/vineyard/orem/south_jordan/herriman promotion pattern).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

PROMOTED
    2024-04-24  fid 1124533, born-digital. No draft marking; posted under the
                2024-05-22 PC notice; the audited 2024-05-22 PC minutes record
                these minutes approved UNAMENDED with unanimous consent (item 2),
                so the posted as-presented copy equals the approved record.
                (In-body header prints "Tuesday, April 24th, 2024" — 2024-04-24
                was a WEDNESDAY; a clerk day-name typo, date kept as printed
                four times in-body and confirmed by the 2024-05-22 approval item.)

REJECTED (verified 2026-07-16, never merged — stays a pmn_backfill sidecar)
    2023-11-28  fid 1089283: stamped with a DRAFT watermark on every page, and
                its PDF was authored 2024-02-23 — four days BEFORE the
                "Minutes Approved on February 27, 2024" line pre-printed in it
                (the line names the scheduled approval meeting; it cannot attest
                approval). Drafts are never promoted. The meeting is real and its
                minutes WERE approved (audited 2024-02-27 PC minutes, item 2,
                unamended) but the approved version was never posted to PMN —
                logged in minutes_unrecovered.csv as the honest gap.

RUN ORDER (this script must run LAST — extract_votes.py rebuilds all_votes.csv
without the pmn rows, and validate_votes.py rebuilds roster.csv from the
audited JSONs only):
    python3 extract_votes.py pc [--force]
    python3 validate_votes.py pc
    python3 extract_backfill_votes.py
Idempotent. Refreshes roster.csv from the merged rows and writes
votes/_backfill_extract_report.txt.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
ROSTER = HERE / "roster.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0], "pc"]               # extract_votes reads argv at import
import extract_votes as ev                   # reuse the audited Alta parser

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
REJECTS = {"2023-11-28": "DRAFT watermark; PDF authored 2024-02-23, before its "
                         "pre-printed 2024-02-27 approval date — drafts are "
                         "never promoted"}
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]
VOTE_KEYS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
             ("absent", "Absent"), ("recuse", "Recuse"))


def text_sidecar(row):
    return PMN / "text" / (Path(row["path"]).stem + ".txt")


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py pc first")
    canon_rows, structured_dates = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue                                    # idempotent
            canon_rows.append(r)
            structured_dates.add(r["date"])

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] != "PlanningCommission" or r["date"] in REJECTS:
                continue
            if not text_sidecar(r).exists():
                sys.exit(f"missing text sidecar for {r['path']}")
            recovered.append(r)

    md_files = sorted((HERE / "minutes").rglob("*.md"))
    ev.build_roster(md_files + [text_sidecar(r) for r in recovered])

    back_rows = []
    parsed = motions = 0
    novote = []
    for r in sorted(recovered, key=lambda x: x["date"]):
        if r["date"] in structured_dates:
            sys.exit(f"UNEXPECTED PC date collision {r['date']} — verify "
                     "before merging (never double-ingest)")
        path = text_sidecar(r)
        ev.set_local_roster(path.read_text(encoding="utf-8", errors="replace"))
        votes = ev.parse_meeting(ev.load_lines(path))
        if not votes:
            novote.append(path.name)
            continue
        parsed += 1
        rel_source = f"pmn_backfill/text/{path.name}"
        title = f"Alta Planning Commission — Regular Meeting {r['date']}"
        for v in votes:
            motions += 1
            base = {
                "date": r["date"], "year": r["date"][:4], "title": title,
                "body": v["body"], "motion_no": v["motion_no"],
                "motion": v["motion"], "motion_type": v["motion_type"],
                "result": v["result"],
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
    out.sort(key=lambda r: (r["date"], r["body"], int(r["motion_no"]),
                            r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    # refresh roster.csv from merged rows (PC is 100% tally-only — stays empty
    # unless a future doc ever prints a named PC roll)
    seen = {}
    for r in out:
        m = (r.get("member") or "").strip()
        if not m:
            continue
        d = seen.setdefault(m, {"n": 0, "years": set()})
        d["n"] += 1
        d["years"].add(r["year"])
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "recorded_votes", "years_active"])
        for nm in sorted(seen, key=lambda n: (-seen[n]["n"], n)):
            w.writerow([nm, seen[nm]["n"], ",".join(sorted(seen[nm]["years"]))])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Alta PC backfill (pmn_backfill -> planning_commission/all_votes.csv)\n")
        f.write(f"recovered PC meetings parsed : {parsed}\n")
        f.write(f"recovered motions            : {motions}\n")
        f.write(f"recovered rows               : {len(back_rows)}\n")
        f.write(f"canonical rows (minutes)     : {len(canon_rows)}\n")
        f.write(f"merged total rows            : {len(out)}\n")
        f.write(f"zero-vote recovered docs     : {len(novote)}\n")
        for s in novote:
            f.write(f"    novote: {s}\n")
        f.write("REJECTS (never merged): " +
                "; ".join(f"{d} ({why})" for d, why in sorted(REJECTS.items())) + "\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} "
          f"recovered ({BACKFILL_PROVENANCE}) rows; {parsed} PC meetings / "
          f"{motions} motions; {len(novote)} zero-vote docs; "
          f"REJECTED (draft, sidecar): 2023-11-28")


if __name__ == "__main__":
    main()
