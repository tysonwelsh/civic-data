#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered standalone Ogden RDA / MBA
minutes from ../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Ogden's structured RDA has a 2022-2023 hole and MBA starts only 2024. Utah
    Public Notice held standalone RDA (2023) + MBA (2020) special-meeting minutes,
    recovered (born-digital) into ../pmn_backfill/. Same minutes format the audited
    parser reads, so this REUSES extract_votes.find_motions(...) over them and merges,
    tagged with provenance. body is forced from the pmn index (standalone RDA/MBA file).

    2026-07-17 — also integrates Council "reverse-combined" siblings: on many nights
    Ogden filed CC + Joint Work Session (+ special / closed) as SEPARATE per-body
    minutes and the audited layer kept only one, dropping the others. Those recovered
    siblings (body=Council in the pmn index) are merged too. Because they share
    (body,date) with the audited per-night doc, Council dedup keys on the recovered
    SLUG (skip only if that same kind of council meeting is already audited that date),
    not on (body,date) — RDA/MBA keep the exact (body,date) dedup. Work/closed sessions
    parse to zero motions and drop out (documentary-only recoveries in the index).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent.
"""
import os
import re
import csv
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


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first")
    canon_rows, structured = [], set()
    structured_slugs = {}   # (body, date) -> {slug, ...} derived from audited source paths
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue
            canon_rows.append(r)
            structured.add((r["body"], r["date"]))
            base = os.path.basename(r.get("source", ""))
            m = re.match(r"\d{4}-\d{2}-\d{2}_(.+)\.md$", base)
            if m:
                structured_slugs.setdefault((r["body"], r["date"]), set()).add(m.group(1))

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            b = r["body"]
            if r.get("status") != "recovered":
                continue
            if b in ("RDA", "MBA"):
                # RDA/MBA are held as separate meetings — coarse (body,date) dedup
                # is exact for them (they never collide with a Council doc same night).
                if (b, r["date"]) in structured:             # already have that meeting
                    continue
            elif b == "Council":
                # Council "reverse-combined" siblings (JWS / special / regular / CS)
                # SHARE (body,date) with the audited per-night doc, so dedup on the
                # recovered slug: skip only if THAT kind of council meeting is already
                # in the audited layer for that date. Work/closed sessions parse to
                # zero motions and drop out below regardless.
                if r["slug"] in structured_slugs.get((b, r["date"]), set()):
                    continue
            else:
                continue
            recovered.append(r)

    back_rows = []
    parsed = motions = 0
    for r in sorted(recovered, key=lambda x: (x["date"], x["body"])):
        rel = r.get("path", "")
        path = PMN / rel if rel else None
        if not path or not path.exists():
            continue
        text = path.read_text(errors="replace")
        year = r["date"][:4]
        mos = ev.find_motions(text, int(year), default_body=r["body"])
        if not mos:
            continue
        parsed += 1
        rel_source = f"pmn_backfill/{rel}"
        for mo in mos:
            motions += 1
            base = {
                "date": r["date"], "year": year, "title": r["title"],
                "body": mo["body"], "motion_no": mo["motion_no"], "motion": mo["motion"],
                "motion_type": mo["motion_type"], "result": mo["result"],
                "mover": mo.get("mover") or "", "seconder": mo.get("seconder") or "",
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            emitted = False
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in mo.get(key, []):
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
    out.sort(key=lambda r: (r["date"], r["body"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Ogden RDA/MBA backfill (pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} RDA/MBA meetings / {motions} motions")


if __name__ == "__main__":
    main()
