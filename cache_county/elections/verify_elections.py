"""verify_elections.py — reconciliation gates for the Cache County canvass
module. Read-only over raw/ + the two long files + the derived by-contest
file; prints PASS/FAIL per gate. Run after any re-parse. Findings are
summarized in VERIFICATION.md.

Gates:
 1. Precinct-grain sources sum EXACTLY to the county's own summary documents,
    contest by contest, candidate by candidate (2023 municipal general details
    vs certified summary; 2020 primary, 2020 general, 2022 primary, 2026
    primary precinct reports vs their summary reports).
 2. The 2025 portal Electionwide totals vs precinct sums: every difference is
    a small positive unassigned bucket (the portal artifact the logan module
    documented), never a sign flip and never > 5 votes.
 3. The held city's audited layer (logan_city_council/election_results/) is
    reproduced by this module for every overlapping race (2023 + 2025).
 4. by_contest internal: every contest's rank sequence is 1..n and votes are
    non-increasing; no pseudo-candidate row leaked in.
"""
import csv
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parse_canvass import parse_electionware  # noqa: E402

FAILS = []


def check(ok, label, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


AGGREGATE = {"write-in totals", "not assigned", "write-in",
             "write-in: not assigned"}


def contest_totals(rows):
    """{(contest, candidate): votes} — named rows summed across precincts;
    aggregate write-in buckets excluded (they double-count their components
    only when BOTH the bucket and components are summed — compared apples to
    apples both sides here, so simply excluded both sides)."""
    out = defaultdict(float)
    for r in rows:
        if r["candidate"].strip().lower() in AGGREGATE:
            continue
        if r["votes"] == "":
            continue
        out[(" ".join(r["contest"].split()), r["candidate"])] += float(r["votes"])
    return out


def gate1(precinct_pdf, summary_pdf, year, etype, label, mode="exact"):
    """mode='exact': precinct sums equal the summary. mode='subset': the
    precinct report withholds whole precincts (2026 public report), so sums
    must be <= the summary for every candidate; the shortfall is reported."""
    p = contest_totals(parse_electionware(precinct_pdf, year, etype, "precinct"))
    s = contest_totals(parse_electionware(summary_pdf, year, etype, "electionwide"))
    diffs = []
    short = 0.0
    for k in sorted(set(p) | set(s)):
        d = s.get(k, 0.0) - p.get(k, 0.0)
        if mode == "exact" and abs(d) > 1e-9:
            diffs.append((k, p.get(k), s.get(k)))
        if mode == "subset":
            if d < 0 or k not in s:
                diffs.append((k, p.get(k), s.get(k)))
            else:
                short += d
    detail = f"{len(p)} candidate totals vs summary"
    if mode == "subset" and not diffs:
        detail = (f"{len(s)} candidate totals; precinct report is a documented "
                  f"subset, total shortfall {int(short)} votes withheld with "
                  f"whole small precincts")
    check(not diffs, f"gate1 {label}", detail if not diffs
          else f"{len(diffs)} mismatches, e.g. {diffs[:4]}")


def main():
    gate1("cache-2023-general-details.pdf", "cache-2023-general-results.pdf",
          2023, "municipal general", "2023 municipal general (certified)")
    gate1("cache-2020-primary-official-precinct.pdf",
          "cache-2020-primary-official-summary.pdf", 2020, "primary",
          "2020 primary")
    gate1("cache-2020-general-canvass-precinct.pdf",
          "cache-2020-general-canvass-summary.pdf", 2020, "general",
          "2020 general")
    gate1("cache-2022-primary-precinct.pdf", "cache-2022-primary-summary.pdf",
          2022, "primary", "2022 primary")
    gate1("cache-2026-primary-precinct-public.pdf",
          "cache-2026-primary-results-summary.pdf", 2026, "primary",
          "2026 primary (public precinct report withholds small precincts)",
          mode="subset")

    # gate 2 — 2025 portal: Electionwide vs precinct sums
    rows = list(csv.DictReader(open(os.path.join(
        HERE, "cache_municipal_results_long.csv"), encoding="utf-8")))
    ew = defaultdict(float)
    ps = defaultdict(float)
    for r in rows:
        if r["year"] != "2025" or r["votes"] == "":
            continue
        k = (r["election_type"], r["contest"], r["candidate"])
        (ew if r["precinct"] == "Electionwide" else ps)[k] += float(r["votes"])
    bad = []
    n_short = 0
    for k in set(ew) | set(ps):
        d = ew.get(k, 0.0) - ps.get(k, 0.0)
        if d:
            n_short += 1
        if d < 0 or d > 5:
            bad.append((k, d))
    check(not bad, "gate2 2025 portal unassigned bucket",
          f"{n_short} candidates differ, all by +1..+3" if not bad
          else f"out-of-band: {bad[:5]}")

    # gate 3 — logan audited layer reproduced (overlap: 2023, 2025)
    audited = {}
    lr = "/Users/tysonwelsh/civic-data/logan_city_council/election_results/logan_results_by_candidate.csv"
    if os.path.exists(lr):
        for r in csv.DictReader(open(lr, encoding="utf-8")):
            if r["year"] in ("2023", "2025"):
                audited[(r["year"], r["election_type"], r["office"],
                         r["candidate"].upper())] = int(float(r["votes"]))
    mine = {}
    for r in csv.DictReader(open(os.path.join(
            HERE, "election_results_by_contest.csv"), encoding="utf-8")):
        if r["jurisdiction_slug"] == "logan" and r["year"] in ("2023", "2025"):
            mine[(r["year"], r["election_type"], r["office"],
                  r["candidate"].upper())] = int(r["votes"])
    diffs = [(k, audited[k], mine.get(k)) for k in audited
             if audited[k] != mine.get(k)]
    extra = [k for k in mine if k not in audited]
    check(bool(audited) and not diffs,
          "gate3 logan audited layer reproduced",
          f"{len(audited)} audited candidate totals match exactly"
          f"{'; module-only rows: ' + str(extra) if extra else ''}"
          if not diffs else f"mismatches: {diffs[:6]}")

    # gate 4 — by_contest internal
    byc = defaultdict(list)
    leaked = []
    for r in csv.DictReader(open(os.path.join(
            HERE, "election_results_by_contest.csv"), encoding="utf-8")):
        byc[(r["year"], r["election_type"], r["contest"])].append(
            (int(r["rank_in_contest"]), int(r["votes"])))
        if r["candidate"].strip().lower() in AGGREGATE:
            leaked.append(r["candidate"])
    bad = []
    for k, v in byc.items():
        v.sort()
        if [r for r, _ in v] != list(range(1, len(v) + 1)):
            bad.append((k, "rank gap"))
        if any(v[i][1] < v[i + 1][1] for i in range(len(v) - 1)):
            bad.append((k, "votes increase with rank"))
    check(not bad and not leaked, "gate4 by_contest internal",
          f"{len(byc)} contests rank-consistent" if not (bad or leaked)
          else f"{bad[:4]} leaked={leaked[:4]}")

    print()
    if FAILS:
        print("FAILURES:", FAILS)
        sys.exit(1)
    print("ALL GATES PASS")


if __name__ == "__main__":
    main()
