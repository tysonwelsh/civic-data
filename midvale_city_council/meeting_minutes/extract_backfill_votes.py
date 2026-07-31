#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the PMN-recovered Midvale council-session
minutes (Council + standalone RDA/MBA companion docs) from ../pmn_backfill/ into
meeting_minutes/all_votes.csv.

WHY
    Midvale's audited minutes came from the city's own Revize portal, which had
    GENUINE coverage holes (a whole 2024 cluster, recurring 3rd-Tuesday January
    meetings). Utah Public Notice (PMN) held 25 minutes docs for 14 missing
    council-session dates (pmn_backfill/, built 2026-07-13). They use the same
    "MOTION: ... The voting was as follows:" grammar the audited parser reads, so
    this REUSES extract_votes.parse_motions(...) over the text sidecars and
    merges, tagged with provenance (the ogden/vineyard/orem/south_jordan/herriman
    promotion pattern).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

BODY
    - Council docs: per-motion ev.detect_body(...) — the audited convention (a
      CC-doc motion whose text names the RDA is tagged body=RDA, exactly as in
      the audited in-session captures).
    - Standalone RDA / MBA docs: body FORCED from the pmn index — the whole doc
      is that board's meeting. These print "Board Member <Name>" / "Chair
      <Name>" roles the audited council roles regex does not cover, so an
      AGENCY_ROLES variant is swapped in for those docs only (names are still
      captured as printed; ev's NAME_ALIASES/canon map applies unchanged).

DATE OVERRIDE (verified 2026-07-16 — "PMN labels lie")
    - The PMN doc labeled "RDA Minutes 1-17-2023" contains the 2023-01-17 RDA
      AGENDA plus the minutes OF THE 2022-12-06 RDA MEETING (the minutes being
      considered/approved that night; every page header reads "December 6,
      2022", approval line "Approved this 17th day of January, 2023"). Its
      motions are merged under date=2022-12-06. The 2023-01-17 RDA session's own
      minutes are NOT held anywhere found -> meeting_minutes/
      minutes_unrecovered.csv.

MBA is a NEW body value for Midvale (1 doc, 2024-05-07 — FY2025 tentative
budget). Its page running header prints a stale "May 2, 2023" template date;
the meeting is verified 2024-05-07 (title header, FY2025 content, roster incl.
Billings, "Approved this 3rd day of December 2024").

RUN (after extract_votes.py — REQUIRED after any extract_votes.py re-run, or
the pmn_minutes rows drop out of all_votes.csv):
    python3 extract_votes.py
    python3 extract_backfill_votes.py
Idempotent. Also refreshes roster.csv from the merged rows so recovered voters
are roster-resolvable.
"""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
ROSTER = HERE / "roster.csv"
INDEX = HERE / "minutes_index.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
import extract_votes as ev

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]
VOTE_KEYS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
             ("absent", "Absent"), ("recuse", "Recuse"))

# (pmn-index date, body) -> (true meeting date, note). See DATE OVERRIDE above.
DATE_OVERRIDES = {
    ("2023-01-17", "RDA"): "2022-12-06",
}

# Standalone board docs print "Board Member <Name>" rolls (+ presiding
# "Chair <Name>"); one 2021 doc says "Trustee". Kept alongside Mayor so a
# genuine presiding-officer vote line would still be captured (none observed).
AGENCY_ROLES = (r"(?:[BE]oard\s*Member|Trustee|Vice[-\s]?Chair|"
                r"Chair(?:man|person)?|Mayor)")
COUNCIL_ROLES = ev.CFG["roles"]


def rx_for(roles):
    ev.CFG["roles"] = roles
    return ev.make_rx()


RX_COUNCIL = rx_for(COUNCIL_ROLES)          # identical to the audited RX
RX_AGENCY = rx_for(AGENCY_ROLES)
ev.CFG["roles"] = COUNCIL_ROLES             # restore


def parse_with(rx, text):
    ev.RX = rx
    try:
        return ev.parse_motions(text)
    finally:
        ev.RX = RX_COUNCIL


def text_path_for(row):
    """pmn index path raw/<stem>.pdf -> text/<stem>.txt sidecar."""
    stem = Path(row["path"]).stem
    return PMN / "text" / f"{stem}.txt"


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

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] not in ("Council", "RDA", "MBA"):
                continue
            recovered.append(r)

    # ---- pass 1: canonical-name map over the audited corpus + recovered docs
    all_names, parsed = [], []
    for r in csv.DictReader(open(INDEX, encoding="utf-8")):
        md = HERE / r["path"]
        if not md.exists():
            continue
        for m in parse_with(RX_COUNCIL, ev.load_body_text(md)):
            all_names += [m["mover"], m["seconder"]]
            for b in m["buckets"].values():
                all_names += [x["name"] for x in b]
    for r in sorted(recovered, key=lambda x: (x["date"], x["body"])):
        tp = text_path_for(r)
        if not tp.exists():
            print(f"MISSING sidecar: {tp}", file=sys.stderr)
            continue
        rx = RX_COUNCIL if r["body"] == "Council" else RX_AGENCY
        ms = parse_with(rx, tp.read_text(encoding="utf-8", errors="replace"))
        date = DATE_OVERRIDES.get((r["date"], r["body"]), r["date"])
        if (date, r["body"]) in structured:
            # a recovered doc must never re-ingest a meeting the audited layer
            # already structured — verify content by hand before whitelisting
            sys.exit(f"UNEXPECTED (date, body) collision ({date}, {r['body']}) "
                     f"for {tp.name} — verify before merging")
        parsed.append((r, date, ms))
        for m in ms:
            all_names += [m["mover"], m["seconder"]]
            for b in m["buckets"].values():
                all_names += [x["name"] for x in b]
    canon = ev.build_canon(all_names)

    # ---- pass 2: emit recovered rows
    back_rows = []
    n_docs = n_motions = 0
    novote = []
    for r, date, ms in parsed:
        rel_source = f"pmn_backfill/text/{text_path_for(r).name}"
        if not ms:
            novote.append(rel_source)
            continue
        n_docs += 1
        for k, m in enumerate(ms, start=1):
            n_motions += 1

            def cbucket(key):
                seen, out = set(), []
                for x in m["buckets"][key]:
                    nm = canon(x["name"])
                    if nm and nm not in seen:
                        seen.add(nm)
                        out.append(nm)
                return out

            body = (ev.detect_body(m["desc"]) if r["body"] == "Council"
                    else r["body"])
            base = {
                "date": date, "year": date[:4], "title": r["title"],
                "body": body, "motion_no": k, "motion": m["desc"][:600],
                "motion_type": ev.classify_motion(m["desc"]),
                "result": ev.result_string(m),
                "mover": canon(m["mover"]) or "",
                "seconder": canon(m["seconder"]) or "",
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            emitted = False
            for key, vote in VOTE_KEYS:
                for member in cbucket(key):
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

    # ---- roster refresh from the merged rows (same semantics as
    # ev.build_roster: one count per member-vote row; dataset label Council)
    seen = {}
    for r in out:
        m = (r.get("member") or "").strip()
        if not m or not r.get("vote"):
            continue
        d = seen.setdefault(m, {"n": 0, "first": r["date"], "last": r["date"],
                                "votes": {v: 0 for _, v in VOTE_KEYS}})
        d["n"] += 1
        d["first"] = min(d["first"], r["date"])
        d["last"] = max(d["last"], r["date"])
        d["votes"][r["vote"]] = d["votes"].get(r["vote"], 0) + 1
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["body", "member", "n_vote_rows", "first_date", "last_date",
                    "aye", "nay", "abstain", "absent", "recuse"])
        for m in sorted(seen, key=lambda x: -seen[x]["n"]):
            s = seen[m]
            w.writerow(["Council", m, s["n"], s["first"], s["last"],
                        s["votes"]["Aye"], s["votes"]["Nay"],
                        s["votes"]["Abstain"], s["votes"]["Absent"],
                        s["votes"]["Recuse"]])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Midvale council-session backfill "
                "(pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered docs with motions : {n_docs}\n")
        f.write(f"recovered motions           : {n_motions}\n")
        f.write(f"recovered rows              : {len(back_rows)}\n")
        f.write(f"canonical rows              : {len(canon_rows)}\n")
        f.write(f"merged total rows           : {len(out)}\n")
        f.write(f"zero-motion recovered docs  : {len(novote)}\n")
        for s in novote:
            f.write(f"    novote: {s}\n")
        f.write("DATE OVERRIDE applied: pmn 2023-01-17 RDA doc -> 2022-12-06 "
                "(the attached minutes ARE the 2022-12-06 RDA meeting; the "
                "2023-01-17 RDA session's own minutes stay in "
                "minutes_unrecovered.csv).\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + "
          f"{len(back_rows)} recovered ({BACKFILL_PROVENANCE}) rows; "
          f"{n_docs} docs / {n_motions} motions; {len(novote)} zero-motion docs")


if __name__ == "__main__":
    main()
