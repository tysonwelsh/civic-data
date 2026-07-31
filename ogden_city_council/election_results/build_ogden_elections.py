#!/usr/bin/env python3
"""
Build Ogden City municipal election CSVs from raw/ sources.

Ogden Municipal Council = 4 district seats (1-4) + 3 at-large seats (A/B/C),
all single-winner, plus a separately-elected Mayor (strong-mayor form).
Odd-year cycles, staggered:
  A-cycle (Mayor + At-Large C + Districts 2 & 4): 2019, 2023
  B-cycle (At-Large A & B + Districts 1 & 3):     2021, 2025
We capture the GENERAL (Nov) result as the race outcome.

Sources (all in raw/), per cycle:
  2019 general  -> 2019_general_results.pdf  (Ogden summary page; summary-only, no precinct)
  2021 general  -> 2021_general_b.pdf        (Weber canvass summary; summary-only, no precinct)
  2023 general  -> raw/state_api/items/2023-Nov-General__*.json
                   (Weber County publishes NO 2023 general municipal PDF -- the county
                    results index says "For municipal results visit the municipality's
                    website" -- so the state Enhanced Voting portal export is the source.
                    It carries full per-precinct breakdown.)
  2025 general  -> 2025_general_precinct.pdf  (Weber born-digital per-precinct canvass)
                   cross-checked against raw/state_api/items/general11042025__*.json

Output: ogden_races.csv, ogden_results_by_candidate.csv, ogden_results_by_precinct.csv
Reproducible: python3 build_ogden_elections.py   (needs pdftotext on PATH)
"""
import csv, json, os, re, subprocess, sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
ITEMS = os.path.join(RAW, "state_api", "items")

ELECTION_TYPE = "municipal general"


def canon_contest(office, district):
    if office == "Mayor":
        return "Ogden City Mayor"
    if str(district).startswith("At-Large"):
        seat = district.split()[-1]
        return f"Ogden City Council At-Large Seat {seat}"
    return f"Ogden City Council District {district}"


def norm_precinct(p):
    """Normalize precinct labels to the 29OG## canonical form used by UGRC.
    2025 PDF/state already use 29OG##; 2023 state uses OGD##."""
    p = p.strip()
    m = re.match(r"^OGD0*?(\d+)(:.*)?$", p)
    if m:
        return f"29OG{int(m.group(1)):02d}{m.group(2) or ''}"
    m = re.match(r"^29OG0*?(\d+)(:.*)?$", p)
    if m:
        return f"29OG{int(m.group(1)):02d}{m.group(2) or ''}"
    return p


# ---------------------------------------------------------------------------
# Generic record assembly
# ---------------------------------------------------------------------------
def build_records(year, contests):
    """contests: list of dicts with keys:
        office, district,
        candidates:[(name,votes)]          -> authoritative race/candidate totals
        precincts:{pname:{name:votes}}     -> per-precinct rows (optional)
        suppressed:[pname,...]             -> precincts present but vote-withheld (optional)
    Returns (race_row, candidate_rows, precinct_rows)."""
    races, cand_rows, prec_rows = [], [], []
    for c in contests:
        office, district = c["office"], c["district"]
        contest = canon_contest(office, district)
        cands = sorted(c["candidates"], key=lambda x: -x[1])
        total = sum(v for _, v in cands)
        ranked = []
        for rank, (name, votes) in enumerate(cands, 1):
            pct = round(100.0 * votes / total, 2) if total else 0.0
            is_win = rank == 1
            ranked.append((name, votes, pct, rank, is_win))
            cand_rows.append(dict(year=year, election_type=ELECTION_TYPE, office=office,
                                  district=district, contest=contest, candidate=name,
                                  votes=votes, pct=pct, rank=rank, is_winner=is_win))
        winner = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else None
        margin_v = (winner[1] - runner[1]) if runner else winner[1]
        margin_p = round(winner[2] - runner[2], 2) if runner else 100.0
        races.append(dict(year=year, election_type=ELECTION_TYPE, office=office,
                          district=district, contest=contest, n_seats=1,
                          n_candidates=len(cands), total_votes=total,
                          winner=winner[0], winner_votes=winner[1], winner_pct=winner[2],
                          runner_up=(runner[0] if runner else ""),
                          runner_up_votes=(runner[1] if runner else ""),
                          margin_votes=margin_v, margin_pct=margin_p))
        for pname, votemap in c.get("precincts", {}).items():
            for cand, votes in votemap.items():
                prec_rows.append(dict(year=year, election_type=ELECTION_TYPE, office=office,
                                      district=district, contest=contest,
                                      precinct=norm_precinct(pname), candidate=cand,
                                      votes=votes, suppressed=False))
        # suppressed precincts: appeared in the canvass but votes withheld (voter
        # privacy in very small precincts). Emit one placeholder row per candidate
        # with blank votes so the precinct↔canvass reconciliation is auditable.
        for pname in c.get("suppressed", []):
            for name, _ in cands:
                prec_rows.append(dict(year=year, election_type=ELECTION_TYPE, office=office,
                                      district=district, contest=contest,
                                      precinct=norm_precinct(pname), candidate=name,
                                      votes="", suppressed=True))
    return races, cand_rows, prec_rows


# ---------------------------------------------------------------------------
# 2019 & 2021 -- parse summary PDFs (Ogden City contests, summary-only)
# ---------------------------------------------------------------------------
def pdftext(fname):
    out = subprocess.run(["pdftotext", "-layout", os.path.join(RAW, fname), "-"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"pdftotext failed on {fname}: {out.stderr}")
    return out.stdout


# matches both the "DISTRICT N" (2019/2021) and "SEAT N" (2025) district labels,
# and "AT-LARGE [SEAT] X" / "MAYOR".
CONTEST_HEADER = re.compile(
    r"OGDEN CITY (?:COUNCIL[ -]+)?(MAYOR|AT[ -]?LARGE (?:SEAT )?([ABC])|DISTRICT (\d)|SEAT (\d))",
    re.IGNORECASE)
CAND_LINE = re.compile(r"^(.+?)\s{2,}([\d,]+)\s+\d+\.\d+%\s*$")


def parse_summary_contests(fname):
    """Return the Ogden City contests from a SUMMARY-style PDF as
    [{office, district, candidates:[(name,votes)], precincts:{}}], excluding
    North/South Ogden and Ogden Valley look-alikes."""
    text = pdftext(fname)
    lines = text.splitlines()

    def next_nonblank(i):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        return lines[j].strip().upper() if j < len(lines) else ""

    contests, cur = [], None
    for i, ln in enumerate(lines):
        # a contest header is any line immediately followed by "Vote For N".
        # Every header closes the previous contest so a non-Ogden contest can't
        # leak candidate rows into the last Ogden contest (the 2025 summary has
        # no "Total Votes Cast" closer; 2019/2021 do).
        if next_nonblank(i).startswith("VOTE FOR"):
            cur = None
            u = ln.upper()
            if "OGDEN CITY" in u and "NORTH OGDEN" not in u and "SOUTH OGDEN" not in u \
                    and "OGDEN VALLEY" not in u:
                m = CONTEST_HEADER.search(ln)
                if m:
                    if m.group(1).upper() == "MAYOR":
                        office, district = "Mayor", ""
                    elif m.group(2):
                        office, district = "Council", f"At-Large {m.group(2).upper()}"
                    else:
                        office, district = "Council", (m.group(3) or m.group(4))
                    cur = dict(office=office, district=district, candidates=[], precincts={})
                    contests.append(cur)
            continue
        if ln.strip().upper().startswith("VOTE FOR"):
            continue
        if cur is not None:
            cm = CAND_LINE.match(ln)
            if cm:
                name = cm.group(1).strip()
                if name.upper().startswith("TOTAL VOTES"):
                    cur = None
                    continue
                votes = int(cm.group(2).replace(",", ""))
                cur["candidates"].append((name, votes))
    return [c for c in contests if c["candidates"]]


def parse_summary_pdf(fname, year, expect):
    """Build records from a summary PDF; assert `expect` (canonical contest labels)."""
    contests = parse_summary_contests(fname)
    found = {canon_contest(c["office"], c["district"]) for c in contests}
    missing = expect - found
    if missing:
        sys.exit(f"{fname}: expected contests not found: {missing}; found {found}")
    return build_records(year, contests)


# ---------------------------------------------------------------------------
# 2023 -- parse state_api item JSONs (summary + per-precinct breakdown)
# ---------------------------------------------------------------------------
def parse_state_items(prefix, year):
    contests = []
    for fn in sorted(os.listdir(ITEMS)):
        if not fn.startswith(prefix) or not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(ITEMS, fn)))
        name = d["name"][0]["text"].strip().upper()
        m = CONTEST_HEADER.search(name)
        if not m:
            sys.exit(f"unrecognized state contest: {name}")
        if m.group(1).upper() == "MAYOR":
            office, district = "Mayor", ""
        elif m.group(2):
            office, district = "Council", f"At-Large {m.group(2).upper()}"
        else:
            # group(3) = "DISTRICT N" (2023), group(4) = "SEAT N" (2025)
            office, district = "Council", (m.group(3) or m.group(4))
        cands = [(b["name"][0]["text"].strip(), b["voteCount"])
                 for b in d["summaryResults"]["ballotOptions"]]
        prec = {}
        for br in d.get("breakdownResults", []) or []:
            pname = br["precinct"]["name"][0]["text"]
            prec[pname] = {b["name"][0]["text"].strip(): b["voteCount"]
                           for b in br["ballotOptions"]}
        contests.append(dict(office=office, district=district, candidates=cands, precincts=prec))
    if not contests:
        sys.exit(f"no state items for prefix {prefix}")
    return build_records(year, contests)


# ---------------------------------------------------------------------------
# 2025 -- parse the per-precinct canvass PDF
# ---------------------------------------------------------------------------
def parse_precinct_pdf(fname, year, summary_totals):
    """Parse per-precinct Ogden contests. `summary_totals` is
    {contest_key:[(name,votes),...]} from the official SUMMARY PDF, used as the
    authoritative race/candidate totals (the precinct sum is short by any
    'Suppressed' precinct whose votes are withheld for voter privacy)."""
    text = pdftext(fname)
    lines = text.splitlines()
    # accumulate per contest: summary candidates + per-precinct votes
    summ = OrderedDict()   # contest_key -> {office,district,candidates:{name:votes}}
    prec = {}              # contest_key -> {precinct -> {name:votes}}
    suppressed = {}        # contest_key -> set(precinct) withheld
    cur_prec = None
    cur_prec_suppressed = False
    cur_contest = None
    # a precinct header is its own line: 29OG##  (optionally with a trailing
    # "Suppressed" or sub-precinct ":U" tag)
    PREC_RE = re.compile(r"^(29OG\d+(?::\w+)?)(\s+Suppressed)?\s*$")
    # Every contest header line is immediately followed by a "Vote For N" line.
    # We use that lookahead to detect a contest BOUNDARY: any header (Ogden or
    # not) closes the previous contest, so a non-Ogden contest cannot leak its
    # candidate rows into the last Ogden contest on the page.
    def next_nonblank(i):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        return lines[j].strip().upper() if j < len(lines) else ""

    for i, ln in enumerate(lines):
        s = ln.strip()
        pm = PREC_RE.match(s)
        if pm:
            cur_prec = pm.group(1)
            cur_prec_suppressed = bool(pm.group(2))
            cur_contest = None
            continue
        is_header = next_nonblank(i).startswith("VOTE FOR")
        if is_header:
            cur_contest = None  # close prior contest at every header boundary
            m = re.search(r"OGDEN CITY COUNCIL (?:AT-LARGE SEAT ([ABC])|SEAT (\d))", s.upper())
            if m and "OGDEN CITY" in s.upper():
                if m.group(1):
                    office, district = "Council", f"At-Large {m.group(1)}"
                else:
                    office, district = "Council", m.group(2)
                key = (office, district)
                cur_contest = key
                summ.setdefault(key, dict(office=office, district=district, candidates=OrderedDict()))
                if cur_prec_suppressed and cur_prec is not None:
                    suppressed.setdefault(key, set()).add(cur_prec)
            continue
        if s.upper().startswith("VOTE FOR"):
            continue  # the marker line itself; keep cur_contest as set by its header
        if cur_contest is not None and not cur_prec_suppressed:
            cm = CAND_LINE.match(ln)
            if cm and not cm.group(1).strip().upper().startswith("TOTAL"):
                name = cm.group(1).strip()
                votes = int(cm.group(2).replace(",", ""))
                if cur_prec is not None:
                    prec.setdefault(cur_contest, {}).setdefault(cur_prec, {})[name] = votes
    contests = []
    for key, info in summ.items():
        # authoritative candidate totals come from the official summary PDF
        cands = summary_totals.get(key)
        if cands is None:
            sys.exit(f"2025: contest {key} in precinct PDF missing from summary PDF")
        contests.append(dict(office=info["office"], district=info["district"],
                             candidates=cands, precincts=prec.get(key, {}),
                             suppressed=sorted(suppressed.get(key, set()))))
    return build_records(year, contests)


# ---------------------------------------------------------------------------
def main():
    all_races, all_cands, all_prec = [], [], []

    # 2019 -- A-cycle: Mayor, At-Large C, District 2, District 4
    r, c, p = parse_summary_pdf("2019_general_results.pdf", 2019, {
        "Ogden City Mayor", "Ogden City Council At-Large Seat C",
        "Ogden City Council District 2", "Ogden City Council District 4"})
    all_races += r; all_cands += c; all_prec += p

    # 2021 -- B-cycle: At-Large A, At-Large B, District 1, District 3
    r, c, p = parse_summary_pdf("2021_general_b.pdf", 2021, {
        "Ogden City Council At-Large Seat A", "Ogden City Council At-Large Seat B",
        "Ogden City Council District 1", "Ogden City Council District 3"})
    all_races += r; all_cands += c; all_prec += p

    # 2023 -- A-cycle from state_api (no county PDF exists)
    r, c, p = parse_state_items("2023-Nov-General__", 2023)
    all_races += r; all_cands += c; all_prec += p

    # 2025 -- B-cycle. Per-candidate/race totals from the official SUMMARY PDF
    # (authoritative; includes the suppressed precinct's withheld votes); the
    # per-precinct rows come from the precinct canvass PDF.
    summary_totals = {(c2["office"], c2["district"]): c2["candidates"]
                      for c2 in parse_summary_contests("2025_general_summary.pdf")
                      if c2["office"] == "Council"}  # 2025 has no Ogden mayor race
    r, c, p = parse_precinct_pdf("2025_general_precinct.pdf", 2025, summary_totals)
    all_races += r; all_cands += c; all_prec += p

    # ---- cross-check 2025 race totals (from summary PDF) vs state_api portal ----
    state_r, _, _ = parse_state_items("general11042025__", 2025)
    st = {x["contest"]: x["total_votes"] for x in state_r}
    for x in r:
        s = st.get(x["contest"])
        ok = "OK" if s == x["total_votes"] else f"DIFF (state={s})"
        print(f"  [2025 xcheck] {x['contest']}: summaryPDF={x['total_votes']} vs state -> {ok}")

    # ---- write CSVs ----
    races_cols = ["year", "election_type", "office", "district", "contest", "n_seats",
                  "n_candidates", "total_votes", "winner", "winner_votes", "winner_pct",
                  "runner_up", "runner_up_votes", "margin_votes", "margin_pct"]
    cand_cols = ["year", "election_type", "office", "district", "contest", "candidate",
                 "votes", "pct", "rank", "is_winner"]
    prec_cols = ["year", "election_type", "office", "district", "contest", "precinct",
                 "candidate", "votes", "suppressed"]

    order = {2019: 0, 2021: 1, 2023: 2, 2025: 3}
    dist_order = {"": 0, "1": 1, "2": 2, "3": 3, "4": 4,
                  "At-Large A": 5, "At-Large B": 6, "At-Large C": 7}
    keyf = lambda x: (order[x["year"]], 0 if x["office"] == "Mayor" else 1,
                      dist_order.get(str(x["district"]), 9))
    all_races.sort(key=keyf)
    all_cands.sort(key=lambda x: (order[x["year"]], 0 if x["office"] == "Mayor" else 1,
                                  dist_order.get(str(x["district"]), 9), x["rank"]))
    all_prec.sort(key=lambda x: (order[x["year"]], 0 if x["office"] == "Mayor" else 1,
                                 dist_order.get(str(x["district"]), 9), x["precinct"], x["candidate"]))

    def write(fn, cols, rows):
        with open(os.path.join(HERE, fn), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    write("ogden_races.csv", races_cols, all_races)
    write("ogden_results_by_candidate.csv", cand_cols, all_cands)
    write("ogden_results_by_precinct.csv", prec_cols, all_prec)

    print(f"\nWrote {len(all_races)} races, {len(all_cands)} candidate rows, "
          f"{len(all_prec)} precinct rows.")
    by_year = {}
    for x in all_races:
        by_year[x["year"]] = by_year.get(x["year"], 0) + 1
    print("races by year:", by_year)
    print("\nWinners:")
    for x in all_races:
        print(f"  {x['year']} {x['contest']:42s} {x['winner']:22s} "
              f"{x['winner_votes']:>6} ({x['winner_pct']}%)  margin {x['margin_votes']}")


if __name__ == "__main__":
    main()
