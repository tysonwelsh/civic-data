"""build_elections.py — Summit County canonical election canvass layer.

Reads the verbatim Summit County Clerk canvass PDFs in raw/ and writes:

  summit_results_long.csv         canonical PRECINCT-grain tidy long
                                  (contest x candidate x precinct [x method]),
                                  mirror of the SLCo long schema:
                                  year, election_type, source_file, sheet,
                                  contest, vote_for, precinct, candidate,
                                  votes, suppressed, vote_method, times_cast,
                                  registered_voters
  election_results_by_contest.csv contest x candidate CERTIFIED totals for the
                                  governance contests (municipal council/mayor
                                  + Summit County offices), the gov.db
                                  `election_result` loader shape:
                                  year, election_type, contest,
                                  jurisdiction_slug, office, district, seats,
                                  candidate, party, votes, rank_in_contest,
                                  n_precincts, suppressed, source_file

DESIGN NOTE (differs from salt_lake_county deliberately): by-contest vote
totals come from each election's CERTIFIED summary layer (Summary Results
Report / GEMS jurisdiction 'Total' rows), NOT from summing the precinct rows —
Summit's 2024-25 precinct tables SUPPRESS low-turnout precincts, so precinct
sums honestly undercount. n_precincts/suppressed are measured from the
precinct layer. Suppressed cells are never imputed (suppressed rows carry
votes='').

DERIVED + idempotent: rerun after any raw refresh; never hand-edit outputs.
Every parse is gated: candidate sums must equal printed Total-Votes-Cast /
jurisdiction totals; precinct sums must reconcile to certified totals up to
documented suppression. Failures raise. Verification detail -> VERIFICATION.md.
"""
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
sys.path.insert(0, HERE)

from canvass_parsers import (parse_ew_summary, parse_ew_precinct,
                             parse_table_precinct, parse_gems_sovc,
                             parse_gems_summary, PRECINCT_LABEL_RE)

P21_RE = re.compile(r"^(\S+ )?\d+[A-Za-z]*:[0-9A-Za-z]+$|^[0-9A-Za-z]+:[0-9A-Za-z]+$")

LONG_COLS = ["year", "election_type", "source_file", "sheet", "contest",
             "vote_for", "precinct", "candidate", "votes", "suppressed",
             "vote_method", "times_cast", "registered_voters"]
BYC_COLS = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes",
            "rank_in_contest", "n_precincts", "suppressed", "source_file"]

# ---------------------------------------------------------------------------
# Election registry. totals_from: 'summary' (EW/table Summary Results Report),
# 'sovc' (GEMS jurisdiction 'Total' rows), 'precinct_sum' (no machine-readable
# certified summary exists - scanned; totals derived by summing the complete
# unsuppressed precinct report, spot-verified by vision reads - see
# VERIFICATION.md), 'gems_summary' (GEMS two-column summary).
# ---------------------------------------------------------------------------
ELECTIONS = [
    # year, etype, family, precinct_file, summary_file, totals_from, note
    (2006, "general", "gems", "2006_general_precinct.pdf", "2006_general_summary.pdf", "sovc", ""),
    (2008, "western states presidential primary", "gems", "2008_western_primary_precinct.pdf", "2008_western_primary_summary.pdf", "sovc", ""),
    (2008, "primary", "gems", "2008_primary_precinct.pdf", "2008_primary_summary.pdf", "sovc", ""),
    (2008, "general", "gems", "2008_general_precinct.pdf", "2008_general_summary.pdf", "sovc", ""),
    (2010, "primary", "gems", "2010_primary_precinct.pdf", "2010_primary_summary.pdf", "sovc", ""),
    (2010, "general", "gems", "2010_general_precinct.pdf", "2010_general_summary.pdf", "sovc", ""),
    (2011, "municipal general", "gems_summary_only", None, "2011_special_summary.pdf", "gems_summary",
     "SOVC precinct groups are UNNAMED in the source (labels not printed); "
     "precinct grain not loadable - contest grain only"),
    (2012, "primary", "gems", "2012_primary_precinct.pdf", "2012_primary_summary.pdf", "sovc", ""),
    (2012, "general", "gems", "2012_general_precinct.pdf", "2012_general_summary.pdf", "sovc", ""),
    (2014, "primary", "gems", "2014_primary_precinct_parkcity5.pdf", "2014_primary_summary.pdf", "sovc",
     "school-board-only primary; second SOVC merged below"),
    (2014, "primary", "gems_extra", "2014_primary_precinct_ssummit4.pdf", None, "sovc", ""),
    (2014, "general", "gems", "2014_general_precinct.pdf", "2014_general_summary.pdf", "gems_summary",
     "SOVC covers Early Voting + Election Day only (paper ballots excluded "
     "by the report itself); certified totals from the summary"),
    (2015, "municipal general", "gems", "2015_general_precinct.pdf", None, "sovc",
     "summary is a garbled scan; certified totals = the SOVC's own "
     "jurisdiction-wide Total rows"),
    (2016, "primary", "gems", "2016_primary_precinct.pdf", None, "sovc", "summary is a garbled scan"),
    (2016, "general", "gems", "2016_general_precinct.pdf", None, "sovc", "summary is a garbled scan"),
    (2018, "primary", "ew", "2018_primary_precinct.pdf", "2018_primary_summary.pdf", "summary", ""),
    (2018, "general", "ew", "2018_general_precinct.pdf", None, "precinct_sum",
     "summary is a scan; no suppression in this era - precinct report is complete"),
    (2019, "municipal general", "ew", "2019_general_precinct.pdf", "2019_general_summary.pdf", "summary", ""),
    (2020, "presidential primary", "ew", "2020_pres_primary_precinct.pdf", None, "precinct_sum",
     "summary is a scan; no suppression in this era"),
    (2020, "primary", "ew", "2020_primary_precinct.pdf", "2020_primary_summary.pdf", "summary", ""),
    (2020, "general", "ew", "2020_general_precinct.pdf", "2020_general_summary.pdf", "summary", ""),
    (2021, "municipal primary", "ew", "2021_municipal_primary_precinct.pdf", "2021_municipal_primary_summary.pdf", "summary", ""),
    (2021, "municipal general", "table", "2021_general_precinct.pdf", "2021_general_summary.pdf", "summary",
     "per-city Municipal Report crosstabs incl. Park City + county Open Space "
     "bond; standalone GO-bond report pair is a duplicate of the bond section"),
    (2022, "general", "table", "2022_general_precinct.pdf", "2022_general_summary.pdf", "summary", ""),
    (2023, "municipal primary", "table", "2023_municipal_primary_precinct.pdf", "2023_municipal_primary_summary.pdf", "summary", ""),
    (2023, "municipal general", "table", "2023_general_precinct.pdf", "2023_general_summary.pdf", "summary", ""),
    (2024, "presidential primary", "table", "2024_pres_primary_precinct.pdf", "2024_pres_primary_summary.pdf", "summary", ""),
    (2024, "general", "table", "2024_general_precinct.pdf", "2024_general_summary.pdf", "summary", ""),
    (2025, "municipal primary", "table", "2025_primary_precinct.pdf", "2025_primary_summary.pdf", "summary", ""),
    (2025, "municipal general", "table", "2025_general_precinct.pdf", "2025_general_summary.pdf", "summary", ""),
    (2026, "primary", "table", "2026_primary_precinct.pdf", "2026_primary_summary.pdf", "summary", ""),
]

# ---------------------------------------------------------------------------
# by-contest governance filter + jurisdiction tagging
# ---------------------------------------------------------------------------
DISTRICT_BODY_RE = re.compile(
    r"SCHOOL|BOND|SERVICE AREA|FIRE|WATER|SEWER|CEMETERY|\bSSD\b|SBWRD|"
    r"TRUSTEE|PROPOSITION|\bPROP\b|JUDICIAL|RETENTION|STRAIGHT PARTY|"
    r"AMENDMENT|TURN OUT|RECLAMATION|MOSQUITO|\bSSA\b|COURT|"
    r"PARK CITY DIST")   # 'PARK CITY DIST N' = PCSD school-board seats (2016)
MUNI_PATTERNS = [
    ("park_city", [r"PARK CITY"]),
    ("coalville", [r"COALVILLE"]),
    ("kamas",     [r"\bKAMAS\b"]),
    ("oakley",    [r"\bOAKLEY\b"]),
    ("francis",   [r"\bFRANCIS\b"]),
    ("henefer",   [r"\bHENEFER\b"]),
]
COUNTY_OFFICE_RE = re.compile(
    r"(SUMMIT )?COUNTY (COUNCIL|COMM\b|COMMISSION|ASSESSOR|ATTORNEY|AUDITOR|"
    r"CLERK|RECORDER|SHERIFF|SURVEYOR|TREASURER)|^COUNCIL SEAT [A-E]$|"
    r"^SEAT [A-E]$|"      # 2008 SOVC bare county-council seat titles
    r"^(ASSESSOR|ATTORNEY|AUDITOR|CLERK|RECORDER|SHERIFF|SURVEYOR|TREASURER)$|"
    r"CANDIDATE FOR SUMMIT COUNTY (COUNCIL|.*)")


def classify_contest(contest):
    """(jurisdiction_slug, office, district) for governance contests;
    ('', '', '') to exclude from by-contest."""
    up = " ".join(contest.upper().split())
    if DISTRICT_BODY_RE.search(up):
        return "", "", ""
    for slug, pats in MUNI_PATTERNS:
        if any(re.search(p, up) for p in pats):
            office = "Mayor" if "MAYOR" in up else "Council"
            district = ""
            if re.search(r"4\s*Y(EA)?R", up):
                district = "4 Year"
            elif re.search(r"2\s*Y(EA)?R", up):
                district = "2 Year"
            return slug, office, district
    if COUNTY_OFFICE_RE.search(up):
        m = re.search(r"COUNCIL SEAT ([A-E])|^SEAT ([A-E])$", up)
        if m:
            return ("summit_county", "County Council",
                    f"Seat {m.group(1) or m.group(2)}")
        m = re.search(r"COUNTY COMM(?:ISSION(?:ER)?)? ([A-E])", up)
        if m:
            return "summit_county", "County Commission", f"Seat {m.group(1)}"
        m = re.search(r"COUNCIL DISTRICT (\d)", up)
        if m:
            return "summit_county", "County Council", f"District {m.group(1)}"
        if "COUNCIL" in up:
            return "summit_county", "County Council", ""
        for off in ("ASSESSOR", "ATTORNEY", "AUDITOR", "CLERK", "RECORDER",
                    "SHERIFF", "SURVEYOR", "TREASURER"):
            if off in up:
                return "summit_county", "County " + off.title(), ""
    return "", "", ""


def party_of(candidate):
    m = re.search(r"\(([A-Z]{2,4})\)", candidate)
    if m and m.group(1) not in ("NP",):
        return m.group(1)
    m = re.search(r"\b(DEM|REP|LIB|CON|IAP|IAM|GRN|UUP)\b\s*$", candidate)
    if m:
        return m.group(1)
    m = re.match(r"^(DEM|REP|LIB|CON|IAP|IAM|GRN|UUP)\b", candidate)
    return m.group(1) if m else ""


def main():
    long_rows = []
    byc = []
    verif = []          # (year, etype, check, status, detail)

    for year, etype, family, pfile, sfile, totals_from, note in ELECTIONS:
        src = pfile or sfile
        ppath = os.path.join(RAW, pfile) if pfile else None
        spath = os.path.join(RAW, sfile) if sfile else None
        summary = None
        if spath and family in ("ew", "table"):
            summary = parse_ew_summary(spath, per_section=(pfile == "2021_general_precinct.pdf"))
        elif spath and family in ("gems", "gems_summary_only"):
            summary = parse_gems_summary(spath)

        contest_meta = {}         # contest -> dict(vote_for)
        pre_rows = []             # precinct rows for this election
        certified = {}            # (contest, candidate) -> certified votes
        n_prec = defaultdict(set)
        suppressed_c = set()

        if family in ("gems", "gems_extra"):
            rows, totals, turnout = parse_gems_sovc(ppath)
            sums = defaultdict(int)
            for r in rows:
                sums[(r["contest"], r["candidate"])] += r["votes"]
                n_prec[r["contest"]].add(r["precinct"])
                pre_rows.append(dict(
                    contest=r["contest"], vote_for="", precinct=r["precinct"],
                    candidate=r["candidate"], votes=r["votes"],
                    suppressed=False, vote_method=r["vote_method"],
                    times_cast=r["times_counted"], registered=r["registered"]))
            bad = sum(1 for k, v in totals.items() if sums.get(k, 0) != v)
            verif.append((year, etype, f"SOVC precinct-sum == jurisdiction Total rows ({pfile})",
                          "PASS" if bad == 0 else "FAIL", f"{len(totals)} contest x candidate totals, {bad} mismatches"))
            if bad and totals_from == "sovc":
                raise SystemExit(f"{pfile}: SOVC internal reconciliation failed")
            if totals_from == "sovc":
                certified = dict(totals)
            elif totals_from == "gems_summary":
                for c in summary:
                    for cand, v in c["candidates"]:
                        certified[(c["name"], cand)] = v
                # cross-check: sovc totals <= summary totals (2014 general:
                # sovc excludes paper ballots)
                verif.append((year, etype, "GEMS summary parsed (certified layer)",
                              "PASS", f"{len(summary)} contests"))
        elif family == "gems_summary_only":
            for c in summary:
                for cand, v in c["candidates"]:
                    certified[(c["name"], cand)] = v
                bad = sum(1 for c2 in summary if c2["total_votes"] is not None and
                          sum(v for _, v in c2["candidates"]) != c2["total_votes"])
            verif.append((year, etype, f"GEMS summary candidate sums == printed Total Votes ({sfile})",
                          "PASS" if bad == 0 else "FAIL", f"{len(summary)} contests"))
        elif family == "ew":
            rows, stats = parse_ew_precinct(ppath)
            sums = defaultdict(int)
            for r in rows:
                sums[(r["contest"], r["candidate"])] += r["votes"]
                n_prec[r["contest"]].add(r["precinct"])
                st = stats.get(r["precinct"], (None, None))
                pre_rows.append(dict(
                    contest=r["contest"], vote_for=r["vote_for"],
                    precinct=r["precinct"], candidate=r["candidate"],
                    votes=r["votes"], suppressed=False, vote_method="Total",
                    times_cast=st[1], registered=st[0]))
            if totals_from == "summary":
                bad = []
                for c in summary:
                    named_wi = [x for x in c["candidates"]
                                if x[0].startswith(("Write-In:", "Write-in:",
                                                    "Not Assigned"))]
                    for cand, v in c["candidates"]:
                        got = sums.get((c["name"], cand))
                        if got is None and (cand.startswith(("Write-In:", "Write-in:"))
                                            or cand == "Not Assigned"):
                            # precinct report prints only 'Write-In Totals';
                            # compare the aggregate instead
                            continue
                        if got != v:
                            bad.append((c["name"], cand, v, got))
                    if named_wi:
                        agg = sum(v for _, v in named_wi)
                        gotwi = sums.get((c["name"], "Write-In Totals"), 0)
                        if gotwi and agg != gotwi:
                            bad.append((c["name"], "write-in aggregate", agg, gotwi))
                    for cand, v in c["candidates"]:
                        certified[(c["name"], cand)] = v
                        contest_meta[c["name"]] = dict(vote_for=c["vote_for"])
                verif.append((year, etype, f"precinct sums == certified summary ({sfile})",
                              "PASS" if not bad else "FAIL",
                              f"{sum(len(c['candidates']) for c in summary)} candidates, {len(bad)} mismatches"))
                if bad:
                    raise SystemExit(f"{pfile}: precinct-vs-summary reconciliation failed: {bad[:4]}")
            else:   # precinct_sum
                for (cst, cand), v in sums.items():
                    certified[(cst, cand)] = v
                for r in rows:
                    contest_meta.setdefault(r["contest"], dict(vote_for=r["vote_for"]))
                verif.append((year, etype, f"totals derived by summing the complete precinct report ({pfile})",
                              "DERIVED", f"{len({c for c, _ in sums})} contests; certified summary is a scan - "
                              "spot-verified by vision reads (see VERIFICATION.md)"))
        elif family == "table":
            rows, stats, checks = parse_table_precinct(
                ppath, summary, precinct_re=P21_RE)
            for r in rows:
                st = stats.get(r["precinct"], (None, None))
                if r.get("suppressed"):
                    suppressed_c.add(r["contest"])
                    pre_rows.append(dict(
                        contest=r["contest"], vote_for=r["vote_for"],
                        precinct=r["precinct"], candidate=r["candidate"],
                        votes=None, suppressed=True, vote_method="Total",
                        times_cast=None, registered=None))
                else:
                    n_prec[r["contest"]].add(r["precinct"])
                    pre_rows.append(dict(
                        contest=r["contest"], vote_for=r["vote_for"],
                        precinct=r["precinct"], candidate=r["candidate"],
                        votes=r["votes"], suppressed=False, vote_method="Total",
                        times_cast=st[1], registered=st[0]))
            bad = [c for c in checks if not c[-1]]
            verif.append((year, etype, f"precinct table == own Totals row == certified summary "
                          f"(suppression-aware) ({pfile})",
                          "PASS" if not bad else "FAIL",
                          f"{len(checks)} candidates, {len(bad)} failures"))
            if bad:
                raise SystemExit(f"{pfile}: table reconciliation failed: {bad[:4]}")
            for c in summary:
                for cand, v in c["candidates"]:
                    certified[(c["name"], cand)] = v
                    contest_meta[c["name"]] = dict(vote_for=c["vote_for"])

        # ---- emit long rows
        for r in pre_rows:
            long_rows.append([
                year, etype, "raw/" + (pfile or ""), r["contest"], r["contest"],
                r["vote_for"], r["precinct"], r["candidate"],
                ("" if r["votes"] is None else r["votes"]),
                str(bool(r["suppressed"])), r["vote_method"],
                ("" if r.get("times_cast") is None else r["times_cast"]),
                ("" if r.get("registered") is None else r["registered"])])

        # ---- emit by-contest rows (governance contests only)
        bycontests = defaultdict(list)
        for (cst, cand), v in certified.items():
            bycontests[cst].append((cand, v))
        for cst, cands in bycontests.items():
            juris, office, district = classify_contest(cst)
            if not office:
                continue
            cands.sort(key=lambda cv: cv[1], reverse=True)
            vf = contest_meta.get(cst, {}).get("vote_for", "")
            for rank, (cand, v) in enumerate(cands, start=1):
                byc.append([year, etype, cst, juris, office, district,
                            vf, cand, party_of(cand), v, rank,
                            len(n_prec.get(cst, ())),
                            "true" if cst in suppressed_c else "false",
                            "raw/" + (sfile if totals_from in ("summary", "gems_summary") and sfile else (pfile or ""))])

    # merge the two 2014 primary registry entries happens naturally (separate
    # source files, separate contests)

    long_rows.sort(key=lambda r: (r[0], r[1], r[4], r[6], r[7], r[10]))
    with open(os.path.join(HERE, "summit_results_long.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(LONG_COLS)
        w.writerows(long_rows)

    byc.sort(key=lambda r: (r[0], r[1], r[3], r[4], r[5], r[10]))
    with open(os.path.join(HERE, "election_results_by_contest.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(BYC_COLS)
        w.writerows(byc)

    print(f"Wrote summit_results_long.csv: {len(long_rows)} precinct-grain rows")
    print(f"Wrote election_results_by_contest.csv: {len(byc)} contest x candidate rows")
    juris_n = defaultdict(int)
    for r in byc:
        juris_n[r[3]] += 1
    print("  per jurisdiction:", dict(sorted(juris_n.items())))
    print("\nVerification gates:")
    for year, etype, check, status, detail in verif:
        print(f"  [{status}] {year} {etype}: {check} - {detail}")
    return verif


if __name__ == "__main__":
    main()
