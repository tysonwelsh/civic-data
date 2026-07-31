#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered Herriman council-family
minutes (Council + standalone CDRA/HCSEA/HCFSA + Joint CC/PC) from
../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Utah Public Notice held 57 council-family minutes absent from the repo
    (2026-07-13 pmn_backfill build + one 2021-01-13 RCCM recovered 2026-07-16):
    12 real 2020 meetings behind the "COVID cancellation" belief, 2021-22 special
    meetings, an entire 2022-05-11 meeting day, the 2023-12-05 Board of
    Canvassers, and the standalone CDRA/HCSEA/HCFSA minutes whose content is
    ABSENT from the combined council docs (systemically so from ~2024 on).
    They are the same minutes format the audited parser reads, so this REUSES
    extract_votes.extract_meeting(...) over them and merges, tagged with
    provenance (the ogden/vineyard/orem/south_jordan promotion pattern).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

BODY
    Taken from each doc's front-matter/pmn index body (Council / CDRA / HCSEA /
    HCFSA — the same body vocabulary the audited layer already uses).
    JointCC-PC docs are merged as body=Council, matching how the audited layer
    models joint CC/PC minutes (e.g. 2020-09-30, 2022-03-30: Body: Council).
    AppealAuthority docs are NOT merged (no appeals body in the city model —
    catalogued in pmn_backfill/ only).

REJECTS (verified 2026-07-16, never merged)
    - 2021-01-13 CDRA: duplicate — the audited 2021-01-13 doc IS those CDRA
      minutes (portal-mistitled; front matter corrected Council→CDRA).

(body,date) COLLISION WHITELIST (verified distinct same-day sessions)
    - Council 2020-09-30: audited joint doc + 2 recovered special sessions.
    - Council 2022-06-29: audited special council meeting + recovered joint doc.
    - Council 2021-01-13: recovered RCCM minutes; the audited doc that date is
      the CDRA minutes (re-tagged), so no Council overlap remains.

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent. Also refreshes roster.csv from the merged rows so recovered voters
are roster-resolvable.
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
BODIES = {"Council": "Council", "CDRA": "CDRA", "HCSEA": "HCSEA",
          "HCFSA": "HCFSA", "JointCC-PC": "Council"}
REJECTS = {("2021-01-13", "CDRA")}   # duplicate of the audited (re-tagged) doc
COLLISION_WHITELIST = {("Council", "2020-09-30"), ("Council", "2022-06-29")}
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]
VOTE_KEYS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
             ("absent", "Absent"), ("recuse", "Recuse"), ("excused", "Excused"))


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first")
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
            if r["body"] not in BODIES or not r.get("text_path", "").strip():
                continue
            if (r["date"], r["body"]) in REJECTS:
                continue
            recovered.append(r)

    # global name map over the audited corpus + the recovered docs, so
    # surname-only movers/rolls in recovered files resolve to full names
    idx_rows = list(csv.DictReader(open(HERE / "minutes_index.csv", encoding="utf-8")))
    files = [str(HERE / r["path"]) for r in idx_rows]
    files += [str(PMN / r["text_path"]) for r in recovered]
    ev.NAME_MAP, ev.FULLS, ev.SURNAMES = ev.build_name_map(files)

    back_rows = []
    parsed = motions = 0
    novote, collisions = [], []
    for r in sorted(recovered, key=lambda x: (x["date"], x["body"])):
        path = PMN / r["text_path"]
        if not path.exists():
            print("MISSING", r["text_path"], file=sys.stderr)
            continue
        body = BODIES[r["body"]]
        if (body, r["date"]) in structured:
            key = (body, r["date"])
            if key not in COLLISION_WHITELIST:
                sys.exit(f"UNEXPECTED (body,date) collision {key} for "
                         f"{r['text_path']} — verify before merging")
            collisions.append(f"{key} :: {r['text_path']} (whitelisted, "
                              f"verified distinct session)")
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
                "body": body,                       # forced (JointCC-PC→Council)
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

    # roster refresh from the merged rows (same semantics as ev.build_roster:
    # one count per motion-person occurrence) so recovered voters resolve
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
        f.write("Herriman council-family backfill "
                "(pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")
        f.write(f"zero-vote recovered docs  : {len(novote)}\n")
        for s in novote:
            f.write(f"    novote: {s}\n")
        f.write(f"whitelisted (body,date) collisions: {len(collisions)}\n")
        for s in collisions:
            f.write(f"    {s}\n")
        f.write("REJECTS (never merged): 2021-01-13 CDRA (duplicate of the "
                "audited re-tagged doc); AppealAuthority docs (no appeals body "
                "in the model).\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} "
          f"recovered ({BACKFILL_PROVENANCE}) rows; {parsed} meetings / "
          f"{motions} motions; {len(novote)} zero-vote docs")


if __name__ == "__main__":
    main()
