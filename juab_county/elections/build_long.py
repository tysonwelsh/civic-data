#!/usr/bin/env python3
"""build_long.py — assemble the canonical Juab County canvass long file from the
retained raws (Channel C Enhanced Voting JSON in raw/ev/ + the hand-keyed 2023
Sept-5 municipal primary from the Channel A Clerk PDF).

Output: juab_results_long.csv — tidy long. Two row kinds per contest x candidate,
distinguished by vote_method:
  * 'Certified Total' (precinct='') — the EV portal's certified contest total for
    that candidate (== the Clerk/Lt-Gov canvass PDF). AUTHORITATIVE; this is what
    build_elections.py sums, so the derived layer reconciles to the canvass even
    when precinct detail is privacy-suppressed.
  * 'Precinct' — the per-precinct breakdown. EV publishes precinct TOTALS only (no
    per-method split — the honest ceiling). Low-count precincts are PRIVACY-
    SUPPRESSED by the portal (voteCount=null): those rows carry votes='' and
    suppressed='True', so Certified Total >= sum(attributed precincts). Municipal
    contests have zero suppression and reconcile exactly; a handful of 2024/2026
    county/state contests hide 1-2 low-population split precincts (e.g. Eureka #6,
    Nephi #5:U2). See VERIFICATION.md.
The 2023 Sept-5 primary is 'Certified Total' only (Clerk summary PDF, no precinct).

Verbatim analysis layer — never hand-edit; rerun after harvest_ev.py. Every row's
source_file traces to a file in raw/. Names/precincts are recorded verbatim.
"""
import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_EV = os.path.join(HERE, "raw", "ev")
OUT = os.path.join(HERE, "juab_results_long.csv")

# (slug, year, election_type) — must mirror harvest_ev.ELECTIONS
ELECTIONS = [
    ("2023-Nov-General", 2023, "municipal general"),
    ("primary06252024",  2024, "primary"),
    ("general11052024",  2024, "general"),
    ("primary08122025",  2025, "municipal primary"),
    ("general11042025",  2025, "municipal general"),
    ("Primary06232026",  2026, "primary"),
]

COLS = ["year", "election_type", "source_file", "contest_id", "contest",
        "vote_for", "precinct", "candidate", "party", "votes", "suppressed",
        "vote_method"]


def nm(x):
    if isinstance(x, list):
        for e in x:
            if e.get("languageId") == "en":
                return e["text"]
        return x[0]["text"] if x else ""
    return x or ""


def vote_for_int(vf):
    s = nm(vf)
    for tok in s.replace("Vote for", "").split():
        if tok.isdigit():
            return tok
    return ""


def party_abbr(o):
    p = o.get("party")
    if not p:
        return ""
    ab = (p.get("abbreviation") or "").strip()
    # nonpartisan municipal/school offices carry no meaningful party token
    if ab.upper() in ("", "NON", "NP", "NONPARTISAN", "UNA"):
        return ""
    return ab


def rows_from_ev():
    rows = []
    for slug, year, etype in ELECTIONS:
        for path in sorted(glob.glob(os.path.join(RAW_EV, f"ev-juab-{slug}-item-*.json"))):
            d = json.load(open(path))
            src = os.path.relpath(path, HERE)
            cid = d.get("id", "")
            contest = nm(d.get("name")).strip()
            vf = vote_for_int(d.get("voteFor"))
            # 1) certified contest total per candidate (authoritative)
            for o in d["summaryResults"]["ballotOptions"]:
                vc = o.get("voteCount")
                rows.append(dict(
                    year=year, election_type=etype, source_file=src,
                    contest_id=cid, contest=contest, vote_for=vf, precinct="",
                    candidate=nm(o.get("name")).strip(), party=party_abbr(o),
                    votes=(0 if vc is None else vc),
                    suppressed="False", vote_method="Certified Total"))
            # 2) per-precinct detail (null = privacy-suppressed low-count precinct)
            for b in (d.get("breakdownResults") or []):
                pname = nm(b["precinct"]["name"]).strip()
                for o in b.get("ballotOptions", []):
                    vc = o.get("voteCount")
                    rows.append(dict(
                        year=year, election_type=etype, source_file=src,
                        contest_id=cid, contest=contest, vote_for=vf,
                        precinct=pname, candidate=nm(o.get("name")).strip(),
                        party=party_abbr(o),
                        votes=("" if vc is None else vc),
                        suppressed=("True" if vc is None else "False"),
                        vote_method="Precinct"))
    return rows


# --- 2023 Sept-5 municipal PRIMARY: EV portal carries only an empty _Demo slug
# (all voteTotal=0). The ONLY source is the official Juab County Clerk canvass PDF
# raw/clerk/2023-09-05-primary-official.pdf ("OFFICIAL RESULTS - Municipal Primary
# Election - September 5, 2023"). Contest-grain (TOTAL column only; no precinct).
# Hand-keyed verbatim below; sums cross-checked to the printed Contest Totals.
CLERK_2023_PRIMARY_SRC = "raw/clerk/2023-09-05-primary-official.pdf"
CLERK_2023_PRIMARY = [
    # (contest, vote_for, [(candidate, votes)...])
    ("Republican for U. S. House District 2", "1", [
        ("CELESTE MALOY", 26), ("BECKY EDWARDS", 33), ("BRUCE R HOUGH", 28)]),
    ("Nephi City Council", "3", [
        ("J.D. PARADY", 672), ("BART STANLEY MILLER", 449), ("LARRY OSTLER", 583),
        ("TRAVIS L. WORWOOD", 733), ("CAROLYN L. FORD", 200), ("VANESSA GOATES", 160),
        ("SHARI COWAN", 652), ("KOLYER K. ANDERSEN", 281), ("JOHN BRADLEY", 484)]),
    ("Rocky Ridge Town Council", "2", [
        ("NEPHI LAUB", 26), ("JOANNA COVINGTON", 48), ("WENDY ALLRED", 26),
        ("SHANNON ALLRED", 45), ("ANDREW AAGARD", 69)]),
    ("Mona City Council", "3", [
        ("TIFFINIE MCAFEE", 50), ("KRIS KAY", 244), ("JUSTIN WEAVER", 60),
        ("FRANK RIDING", 179), ("RUSSELL A. FORSYTH", 95), ("JANA CRAWFORD", 101),
        ("JACK BOYD", 56), ("KEVIN L. SQUIRE", 211), ("AMY STANLEY", 303)]),
    ("Levan Town Council - 4 yr", "2", [
        ("ALAN M. KENDALL", 106), ("NATHAN JAMES WASHER", 84), ("RACHEL GOATES", 94),
        ("CHRISTOPHER J. CHIPPING", 106), ("CLAYTON SPERRY", 62),
        ("TYRA JACKMAN-WANKIER", 77)]),
]


def rows_from_clerk_2023_primary():
    rows = []
    for i, (contest, vf, cands) in enumerate(CLERK_2023_PRIMARY):
        cid = f"clerk-2023p-{i}"
        # US House is a partisan primary contest; municipal councils are nonpartisan
        party = "REP" if contest.startswith("Republican") else ""
        for cand, votes in cands:
            rows.append(dict(
                year=2023, election_type="municipal primary",
                source_file=CLERK_2023_PRIMARY_SRC, contest_id=cid, contest=contest,
                vote_for=vf, precinct="", candidate=cand, party=party,
                votes=votes, suppressed="False", vote_method="Certified Total"))
    return rows


def main():
    rows = rows_from_ev() + rows_from_clerk_2023_primary()
    rows.sort(key=lambda r: (r["year"], r["election_type"], r["contest"],
                             str(r["contest_id"]), r["precinct"], r["candidate"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT}: {len(rows)} rows")


if __name__ == "__main__":
    main()
