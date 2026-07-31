#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered Herriman Planning Commission
minutes from ../pmn_backfill/ into planning_commission/all_votes.csv.

WHY
    Utah Public Notice held 13 PC minutes absent from the repo (2026-07-13
    pmn_backfill build), incl. the 2020-12-03 meeting behind the "COVID
    cancellation" belief and the 2022-23 dates the portal never served. Same
    minutes format the audited parser reads, so this REUSES
    extract_votes.extract_meeting(...) and merges, tagged with provenance
    (the ogden/vineyard/orem/south_jordan promotion pattern).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

REJECTS (verified 2026-07-16, never merged — stay pmn_backfill sidecars)
    - 2023-11-01 PC: the recovered doc is stamped "Pending Formal Approval /
      Draft" (drafts are never promoted).
    - 2022-04-21 PC: the PMN file named "2022_04_21_PC_Minutes.pdf" is actually
      a zoning use-table / agenda attachment (PDF title "Planning Commission
      Agenda", no minutes narrative) — a source mislabel; the 2022-04-21 PC
      minutes remain genuinely unrecovered.

RUN (after extract_votes.py):
    python3 planning_commission/extract_votes.py
    python3 planning_commission/extract_backfill_votes.py
Idempotent. Also refreshes roster.csv from the merged rows.
"""
import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
ROSTER = HERE / "roster.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
import extract_votes as ev

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
REJECTS = {"2023-11-01": "draft (Pending Formal Approval)",
           "2022-04-21": "not minutes (mislabeled zoning use-table attachment)"}
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]
VOTE_KEYS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
             ("absent", "Absent"), ("recuse", "Recuse"), ("excused", "Excused"))


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first")
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
            if r["body"] != "PlanningCommission" or not r.get("text_path", "").strip():
                continue
            if r["date"] in REJECTS:
                continue
            recovered.append(r)

    idx_rows = list(csv.DictReader(open(HERE / "minutes_index.csv", encoding="utf-8")))
    files = [str(HERE / r["path"]) for r in idx_rows]
    files += [str(PMN / r["text_path"]) for r in recovered]
    ev.NAME_MAP, ev.FULLS, ev.SURNAMES = ev.build_name_map(files)

    back_rows = []
    parsed = motions = 0
    novote = []
    for r in sorted(recovered, key=lambda x: x["date"]):
        path = PMN / r["text_path"]
        if not path.exists():
            print("MISSING", r["text_path"], file=sys.stderr)
            continue
        if r["date"] in structured_dates:
            sys.exit(f"UNEXPECTED PC date collision {r['date']} for "
                     f"{r['text_path']} — verify before merging")
        rel_source = f"pmn_backfill/{r['text_path']}"
        meeting = ev.extract_meeting(str(path), rel_source, r["date"],
                                     r["date"][:4], r["title"])
        if not meeting["votes"]:
            novote.append(r["text_path"])
            continue
        parsed += 1
        for v in meeting["votes"]:
            motions += 1
            base = {
                "date": r["date"], "year": r["date"][:4], "title": r["title"],
                "body": "PlanningCommission",
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover", ""), "seconder": v.get("seconder", ""),
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

    seen = {}
    for r in out:
        m = (r.get("member") or "").strip()
        if not m:
            continue
        d = seen.setdefault(m, {"first": r["date"], "last": r["date"], "n": 0})
        d["first"] = min(d["first"], r["date"])
        d["last"] = max(d["last"], r["date"])
        d["n"] += 1
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_votes"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, "", d["first"], d["last"], d["n"]])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Herriman PC backfill "
                "(pmn_backfill -> planning_commission/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")
        f.write(f"zero-vote recovered docs  : {len(novote)}\n")
        for s in novote:
            f.write(f"    novote: {s}\n")
        f.write("REJECTS (never merged): " +
                "; ".join(f"{d} ({why})" for d, why in sorted(REJECTS.items())) + "\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} "
          f"recovered ({BACKFILL_PROVENANCE}) rows; {parsed} PC meetings / "
          f"{motions} motions; {len(novote)} zero-vote docs")


if __name__ == "__main__":
    main()
