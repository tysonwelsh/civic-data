#!/usr/bin/env python3
"""
Build Logan (Cache County, Utah) municipal election CSVs from raw sources.

Logan elects its Mayor (single-winner) and a 5-member Municipal Council ENTIRELY
AT-LARGE (no districts, plurality / vote-for-N, NO ranked-choice). Council seats
are staggered: 3 seats elected 2019 & 2023, 2 seats elected 2021 & 2025.

Sources (immutable, in raw/):
  2019 primary/general (council)      -> City of Logan official PDFs (city-run election)
  2021 primary (mayor) / general      -> City of Logan official PDFs (city-run election)
  2023 primary (council)              -> Cache County Clerk OFFICIAL summary PDF
  2023 general (council, CERTIFIED)   -> Cache County Clerk OFFICIAL canvass PDFs
                                         (race/candidate from results summary;
                                          precinct from the 12/01/2023 details canvass)
  2025 primary/general (mayor+council)-> Utah Enhanced Voting JSON API (electionresults.utah.gov)

2023 NOTE: Cache County's 2023 election had an integrity investigation (clerk + staff
on administrative leave) and a recount (Logan council margins within 0.25%). The
recount did NOT change the winners. This repo uses the CERTIFIED county canvass
figures for 2023, not the (higher) unofficial election-night portal numbers.

Multi-winner (vote-for-N) model: winner = top vote-getter; runner_up = first loser
(rank N+1); margin = rank-N minus rank-(N+1) = the seat-deciding margin. In
by_candidate, is_winner=Y for rank<=N (general) or rank<=2N (primary advancement).
Mayor is conventional single-winner.
"""
import csv, json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

def pdftext(name):
    return subprocess.check_output(
        ["pdftotext", "-layout", os.path.join(RAW, name), "-"]).decode("utf-8", "replace")

# ---------------------------------------------------------------------------
# race records accumulate here.
# each = dict(year, election_type, office, district, contest, n_seats,
#             voting_method, candidates=[(name, votes)], source)
# candidate vote order need not be sorted; we sort by votes desc.
# ---------------------------------------------------------------------------
RACES = []
# precinct rows: (year, election_type, office, contest, precinct_code, precinct_name, candidate, votes)
PRECINCTS = []

PLURALITY = "plurality"
PLURALITY_N = "plurality (vote-for-N at-large)"

# ===========================================================================
# 1-2 & 3-5: City of Logan official transposed-crosstab PDFs (2019, 2021)
# Layout: candidate rows x precinct columns, in 3 column-blocks separated by
# "VOTING PRECINCTS" headers, plus a right-hand per-candidate Total summary.
# ===========================================================================
def parse_city_pdf(name, candidates):
    """Return {cand: {precinct_label: votes}} and {cand: total} from a Logan city PDF.
    `candidates` is the ordered list of exact candidate names as they appear."""
    txt = pdftext(name)
    lines = txt.splitlines()
    # Split into the 3 precinct column-blocks on the "VOTING PRECINCTS" marker.
    blocks, cur = [], []
    started = False
    for ln in lines:
        if "VOTING PRECINCTS" in ln:
            if started:
                blocks.append(cur)
            cur = []
            started = True
            continue
        if started:
            cur.append(ln)
    if started:
        blocks.append(cur)

    # Precinct labels per block come from the "CANDIDATES <labels...>" header row
    # which is the first non-empty line of each block.
    per_cand = {c: {} for c in candidates}
    block_labels = []
    for bi, blk in enumerate(blocks):
        # header: first line containing "CANDIDATES"
        hdr = next((l for l in blk if "CANDIDATES" in l), None)
        if hdr is None:
            block_labels.append([])
            continue
        raw_labels = hdr.split("CANDIDATES", 1)[1].split()
        # The final block merges the right-hand summary table ("CANDIDATES Total %
        # Voter Turnout") onto the same row. Keep ONLY real precinct labels:
        # bare precinct numbers, split precincts like "33:5", or "Provisional".
        labels = [l for l in raw_labels
                  if re.match(r"^\d+(:\d+)?$", l) or l == "Provisional"]
        block_labels.append(labels)
        nlab = len(labels)
        for c in candidates:
            # candidate's data row in this block: the line that STARTS with the name.
            row = next((l for l in blk if l.strip().startswith(c)), None)
            if row is None:
                continue
            after = row.strip()[len(c):]
            nums = re.findall(r"-?\d+", after)
            vals = nums[:nlab]  # the first nlab ints are the precinct columns
            for lab, v in zip(labels, vals):
                per_cand[c][f"b{bi}:{lab}"] = int(v)

    # Per-candidate Total from the summary table (right of final block):
    # lines like "Mark A. Anderson   3837   25%". Use the LAST occurrence with a
    # bare integer (the summary), matched globally across the text.
    # Per-candidate certified Total from the right-hand summary table. That row is
    # the candidate line containing a "<int>  <int>%" pair (e.g. "3,283   65%").
    totals = {}
    for c in candidates:
        printed = None
        for ln in lines:
            s = ln.strip()
            if s.startswith(c) and "%" in s:
                m = re.findall(r"([\d,]+)\s+\d{1,3}%", s)
                if m:
                    printed = int(m[-1].replace(",", ""))
        totals[c] = printed
    # Build clean precinct labels (strip the b#: prefix -> human label, keep block uniqueness)
    return per_cand, totals, block_labels

def add_city_race(year, etype, office, contest, n_seats, pdf, candidates, district="At-Large"):
    per_cand, printed, _ = parse_city_pdf(pdf, candidates)
    cand_votes = []
    for c in candidates:
        psum = sum(per_cand[c].values())
        pr = printed.get(c)
        if pr is None:
            raise RuntimeError(f"{pdf}: no certified total parsed for {c!r}")
        # certified printed total is authoritative; precinct sum is a cross-check
        if pr != psum:
            print(f"  WARN {year} {etype} {office} {c}: precinct-sum {psum} != certified {pr}")
        cand_votes.append((c, pr))
    RACES.append(dict(year=year, election_type=etype, office=office, district=district,
                      contest=contest, n_seats=n_seats,
                      voting_method=(PLURALITY if office == "Mayor" else PLURALITY_N),
                      candidates=cand_votes, source=pdf))
    # precinct rows
    for c in candidates:
        for lab, v in per_cand[c].items():
            human = lab.split(":", 1)[1]  # drop b# prefix
            PRECINCTS.append((year, etype, office, contest, human, human, c, v))

# 2019 council (3 seats) - city-run
add_city_race(2019, "municipal primary", "Council", "Logan City Council", 3,
              "logan-2019-primary-official.pdf",
              ["Mark A. Anderson", "Jeannie F. Simmonds", "Abraham E. Verdoes",
               "Ken Heare", "Keegan Garrity", "Gary Poore", "Tom Jensen"])
add_city_race(2019, "municipal general", "Council", "Logan City Council", 3,
              "logan-2019-general-official.pdf",
              ["Mark A. Anderson", "Jeannie F. Simmonds", "Abraham E. Verdoes",
               "Ken Heare", "Keegan Garrity", "Tom Jensen"])

# 2021 mayor primary - city-run (single contest)
add_city_race(2021, "municipal primary", "Mayor", "Logan Mayor", 1,
              "logan-2021-primary-official.pdf",
              ["Holly H. Daines", "Dee Jones", "R. Lowell Huber"], district="")

# 2021 general - city-run PDF holds BOTH mayor and council. Parse each separately.
# Mayor candidates and council candidates share the file; restrict name lists.
add_city_race(2021, "municipal general", "Mayor", "Logan Mayor", 1,
              "logan-2021-general-official.pdf",
              ["Holly H. Daines", "Dee Jones"], district="")
add_city_race(2021, "municipal general", "Council", "Logan City Council", 2,
              "logan-2021-general-official.pdf",
              ["Amy Z. Anderson", "Keegan Garrity", "Ernesto Lopez"])

# ===========================================================================
# 6: 2023 primary (council) - Cache County OFFICIAL summary PDF (no precinct detail)
# ===========================================================================
def parse_county_summary(name, contest_header, vote_for):
    """Parse a 'Vote For N' contest block from a Cache County summary PDF.
    Returns list of (candidate, votes)."""
    txt = pdftext(name)
    lines = txt.splitlines()
    out = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == contest_header:
            j = i + 1
            # skip until first candidate (after the TOTAL VOTE % header)
            while j < len(lines) and "TOTAL" not in lines[j]:
                j += 1
            j += 1
            while j < len(lines):
                s = lines[j].strip()
                if not s:
                    j += 1; continue
                if s.startswith("Total Votes Cast") or s.startswith("Overvotes") \
                        or s.startswith("Undervotes") or s.startswith("Contest Total"):
                    break
                m = re.match(r"^(.*?)\s+([\d,]+)\s+[\d.]+%$", s)
                if m:
                    out.append((m.group(1).strip(), int(m.group(2).replace(",", ""))))
                j += 1
            return out
        i += 1
    raise RuntimeError(f"contest {contest_header!r} not found in {name}")

c23p = parse_county_summary("cache-2023-primary-results.pdf", "Logan City Council", 3)
RACES.append(dict(year=2023, election_type="municipal primary", office="Council",
                  district="At-Large", contest="Logan City Council", n_seats=3,
                  voting_method=PLURALITY_N, candidates=c23p,
                  source="cache-2023-primary-results.pdf"))

# ===========================================================================
# 7: 2023 general (council) - CERTIFIED. Race/candidate from results summary PDF;
#     precinct from the 12/01/2023 details canvass PDF.
# ===========================================================================
c23g = parse_county_summary("cache-2023-nov-general-results.pdf", "Logan City Council", 3)
RACES.append(dict(year=2023, election_type="municipal general", office="Council",
                  district="At-Large", contest="Logan City Council", n_seats=3,
                  voting_method=PLURALITY_N, candidates=c23g,
                  source="cache-2023-nov-general-results.pdf (certified canvass)"))

# precinct detail for 2023 general from the details canvass (LOG## precincts only)
def parse_2023_details():
    txt = pdftext("cache-2023-nov-general-details.pdf")
    lines = txt.splitlines()
    cur_prec = None
    i = 0
    prec_re = re.compile(r"^(LOG\d+:[A-Za-z0-9]+)\s*$")
    while i < len(lines):
        s = lines[i].strip()
        m = prec_re.match(s)
        if m:
            cur_prec = m.group(1)
            i += 1; continue
        if s == "Logan City Council" and cur_prec:
            j = i + 1
            while j < len(lines) and "TOTAL" not in lines[j]:
                j += 1
            j += 1
            while j < len(lines):
                t = lines[j].strip()
                if not t:
                    j += 1; continue
                if t.startswith("Overvotes") or t.startswith("Undervotes") \
                        or t.startswith("Contest Total"):
                    break
                mm = re.match(r"^(.*?)\s+([\d,]+)\s+[\d.]+%$", t)
                if mm:
                    PRECINCTS.append((2023, "municipal general", "Council",
                                      "Logan City Council", cur_prec, cur_prec,
                                      mm.group(1).strip(), int(mm.group(2).replace(",", ""))))
                j += 1
            i = j; continue
        i += 1
parse_2023_details()

# ===========================================================================
# 8-11: 2025 primary + general (mayor + council) - Enhanced Voting JSON
# ===========================================================================
def parse_ev(fname, year, etype, office, contest, n_seats, district):
    d = json.load(open(os.path.join(RAW, fname)))
    opts = d["summaryResults"]["ballotOptions"]
    cands = [(o["name"][0]["text"].strip(), o["voteCount"]) for o in opts]
    RACES.append(dict(year=year, election_type=etype, office=office, district=district,
                      contest=contest, n_seats=n_seats,
                      voting_method=(PLURALITY if office == "Mayor" else PLURALITY_N),
                      candidates=cands, source=fname))
    for b in d.get("breakdownResults", []) or []:
        pname = b["precinct"]["name"][0]["text"]
        for o in b["ballotOptions"]:
            PRECINCTS.append((year, etype, office, contest, pname, pname,
                              o["name"][0]["text"].strip(), o.get("voteCount") or 0))

parse_ev("ev-2025p-logan-mayor.json", 2025, "municipal primary", "Mayor", "Logan Mayor", 1, "")
parse_ev("ev-2025p-logan-council.json", 2025, "municipal primary", "Council", "Logan City Council", 2, "At-Large")
parse_ev("ev-2025g-logan-mayor.json", 2025, "municipal general", "Mayor", "Logan Mayor", 1, "")
parse_ev("ev-2025g-logan-council.json", 2025, "municipal general", "Council", "Logan City Council", 2, "At-Large")

# ===========================================================================
# DERIVE races / by_candidate
# ===========================================================================
def is_writein(name):
    return name.lower() in ("write-in", "write in", "writein") or name.lower().startswith("write-in")

races_rows = []
cand_rows = []
for r in sorted(RACES, key=lambda x: (x["year"], 0 if x["election_type"].endswith("primary") else 1,
                                      x["office"])):
    cands = [(n, v) for n, v in r["candidates"] if v is not None]
    cands.sort(key=lambda x: -x[1])
    n_cand = len(cands)
    n_seats = r["n_seats"]
    total = sum(v for _, v in cands)
    is_primary = r["election_type"].endswith("primary")
    # winners / advancers cutoff
    if is_primary:
        cutoff = min(2 * n_seats, n_cand)   # top 2N advance
    else:
        cutoff = min(n_seats, n_cand)       # top N win seats
    winner_name, winner_votes = cands[0]
    winner_pct = round(100 * winner_votes / total, 2) if total else 0
    # runner_up = first one past the cutoff (rank cutoff+1); margin = rank cutoff - rank cutoff+1
    if n_cand > cutoff:
        last_in = cands[cutoff - 1]
        first_out = cands[cutoff]
        runner_up, runner_up_votes = first_out
        margin_votes = last_in[1] - first_out[1]
        margin_pct = round(100 * margin_votes / total, 2) if total else 0
    else:
        # uncontested-for-the-cutoff: report 2nd place as runner_up if exists
        if n_cand >= 2:
            runner_up, runner_up_votes = cands[1]
            margin_votes = cands[0][1] - cands[1][1]
            margin_pct = round(100 * margin_votes / total, 2) if total else 0
        else:
            runner_up, runner_up_votes, margin_votes, margin_pct = "", "", "", ""
    races_rows.append([
        r["year"], r["election_type"], r["office"], r["district"], r["contest"],
        n_seats, n_cand, r["voting_method"], total,
        winner_name, winner_votes, winner_pct,
        runner_up, runner_up_votes, margin_votes, margin_pct,
    ])
    for rank, (n, v) in enumerate(cands, 1):
        pct = round(100 * v / total, 2) if total else 0
        is_win = "Y" if rank <= cutoff else "N"
        cand_rows.append([r["year"], r["election_type"], r["office"], r["contest"],
                          n, v, pct, rank, is_win])

# ===========================================================================
# WRITE
# ===========================================================================
with open(os.path.join(HERE, "logan_races.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "election_type", "office", "district", "contest", "n_seats",
                "n_candidates", "voting_method", "total_first_choice_votes",
                "winner", "winner_votes", "winner_pct", "runner_up", "runner_up_votes",
                "margin_votes", "margin_pct"])
    w.writerows(races_rows)

with open(os.path.join(HERE, "logan_results_by_candidate.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "election_type", "office", "contest", "candidate", "votes",
                "pct", "rank", "is_winner"])
    w.writerows(cand_rows)

PRECINCTS.sort(key=lambda x: (x[0], x[1], x[2], x[4], x[6]))
with open(os.path.join(HERE, "logan_results_by_precinct.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "election_type", "office", "contest", "precinct_code",
                "precinct_name", "candidate", "votes"])
    w.writerows(PRECINCTS)

print(f"races={len(races_rows)} candidates={len(cand_rows)} precinct_rows={len(PRECINCTS)}")
