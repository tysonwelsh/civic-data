"""parse_canvass.py — normalize the Cache County Clerk canvass into the canonical
long files (SLCo model: one row per precinct x candidate x vote-method).

Inputs (raw/, verbatim originals — see sources.csv):
  Electionware PDFs (pdftotext -layout at parse time; text never stored in raw/).
  Two report families, three precinct-header dialects:
    - precinct grain: "Precinct Summary Report" (2021P, 2022P), precinct-block
      "Summary Results Report" (2020, 2023 details), "Precinct Results Report"
      (2026). Precinct ids are colon-style (LOG24:CSD1, 3AMA:I) in 2021+ or
      BARE tokens (AMA, LOG01) in 2020; both appear only as the first content
      line of a page — continuation pages repeat them (2020/2022/2023) —
      captured positionally so wrapped candidate-name fragments (2020:
      "...KAMALA D." / "HARRIS") can never be mistaken for precincts.
    - electionwide grain: "Election Summary Report" / summary "Summary Results
      Report": countywide totals only; rows carry precinct='Electionwide' (the
      tabulator's own rollup notion; excluded from n_precincts downstream,
      consistent with the SLCo 'Cumulative' discipline).
  Enhanced Voting state-portal JSON (raw/ev/): 2025 municipal primary + general
    — the channel Cache County itself linked as its official 2025 results.
    Portal summary totals emit precinct='Electionwide'; breakdownResults emit
    real precinct rows. The portal flags isOfficialResults:false (no certified
    county PDF was published for 2025) — a recorded ceiling; see VERIFICATION.md.

Outputs (canonical — never hand-edit; rerun this):
  cache_municipal_results_long.csv      municipal odd-year canvass (2021-2025)
  cache_county_office_results_long.csv  even-year county canvass (2020, 2022,
                                        2026 primary), every contest verbatim
                                        (federal/state/county/school/props)

Row filter (documented; verbatim otherwise): candidate-like vote rows only —
named candidates, FOR/AGAINST/YES/NO, 'Write-In: <name>', 'Write-In Totals',
'Not Assigned', and the printed 'CANDIDATE DISQUALIFIED' rows (2021 primary
Lewiston — the source's own text, kept verbatim). Excluded: Overvotes,
Undervotes, Contest Totals, Total Votes Cast (per-contest statistics, not votes
for anyone; recoverable from raw/ and used in VERIFICATION reconciliation).
Only the TOTAL column is parsed where a source also prints vote-method columns
(2022: Election Day / Absentee) — vote_method='Total' throughout; the method
split is a recorded ceiling, not a loss of totals. Wrapped candidate names
(2020 layout) are re-joined ("DEM JOSEPH R. BIDEN, KAMALA D. HARRIS"); party
prefixes are the source's own text, kept in place.

times_cast / registered_voters carry the precinct block's own statistics and
are therefore filled ONLY on precinct-grain PDF rows; electionwide PDF rows
and portal rows leave them blank (the report-level statistics belong to the
whole canvass, not one contest — recorded in VERIFICATION.md instead).

Never fabricates: every row traces to (source_file, sheet = pNN page / portal
ballot-item uuid).
"""
import csv
import json
import os
import re
import subprocess
from glob import glob

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

COLS = ["year", "election_type", "source_file", "sheet", "contest", "vote_for",
        "precinct", "candidate", "votes", "suppressed", "vote_method",
        "times_cast", "registered_voters"]

# ---------------------------------------------------------------- Electionware

ID_COLON_RE = re.compile(r"^[0-9A-Z]{2,7}:[A-Z0-9]{1,4}$")
ID_BARE_RE = re.compile(r"^[A-Z]{2,6}[0-9]{0,2}$")
VOTE_FOR_RE = re.compile(r"^\s*Vote For (\d+)\s*$")
# candidate-ish line: text, >=2 spaces, integer; optional pct; optional trailing
# method-column integers (2022) — only the first integer (TOTAL) is taken.
CAND_RE = re.compile(
    r"^(\s*)(.+?)\s{2,}([\d,]+)(?:\s+\d{1,3}\.\d{2}%)?(?:\s+[\d,]+)*\s*$")
REG_RE = re.compile(
    r"^\s*Registered Voters - Total\s{2,}([\d,]+)(?:\s+[\d,]+)*\s*$")
CAST_RE = re.compile(
    r"^\s*Ballots Cast - Total\s{2,}([\d,]+)(?:\s+[\d,]+)*\s*$")
# 2020 presidential-primary dialect: precinct headers are full mixed-case
# place names ("Amalga", "River Heights") — accepted only at page top.
ID_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .']{1,28}(?: \d{1,2})?$")
# a votes line with no name on it (the 2020 summary's sandwich name-wrap:
# fragment line / numbers line / trailing fragment line)
NUMBERS_ONLY_RE = re.compile(
    r"^\s*([\d,]+)(?:\s+\d{1,3}\.\d{2}%)?(?:\s+[\d,]+)*\s*$")

STAT_ROWS = {"overvotes", "undervotes", "contest totals", "total votes cast"}

SKIP_RES = [re.compile(p) for p in (
    r"OFFICIAL RESULTS", r"UNOFFICIAL RESULTS", r"OFFICIAL CANVASS",
    r"^UT Cache \d+", r"^\d{2}/\d{2}/\d{4}\b", r"Cache County$",
    r"Election Summary Report", r"Precinct Summary Report",
    r"Summary Results Report", r"Precinct Results Report",
    r"Report generated with Electionware", r"Page \d+ of \d+",
    r"^\s*STATISTICS\s*$", r"^\s*Statistics\b",
    r"^\s*TOTAL(\s+VOTE ?%)?\s*$",
    r"^\s*TOTAL\s+VOTE ?%",  # method-column header (2022: '... Absentee')
    r"^\s*TOTAL\s+Election Day\s+Absentee\s*$",
    r"^\s*Election\s*$", r"^\s*Day\s*$", r"^\s*Absentee\s*$",
    r"^\s*Mail\s*$", r"^\s*Provisional\s*$",
    r"^\s*TOTAL\s+Mail\s+Provisional\s*$",
    r"^\s*PRESIDENTIAL PRIMARY ELECTION\s*$",
    r"^\s*VOTE ?%\s*$", r"^\s*[\d.,]+%\s*$",
    r"Cache County, U", r"^\s*[A-Z][a-z]+ \d{1,2}, \d{4}\s*$",
    r"Voter Turnout", r"Ballots Cast - Blank",
    r"Ballots Cast - (?!Total)",  # partisan ballots-cast lines (2020 primary)
    r"Precincts Reporting",
    r"Registered Voters - (?!Total)",  # partisan registration lines (2022)
    r"Registered Voters - Total\s*$",  # value printed on a neighboring line
    r"Ballots Cast - Total\s*$",
    r"^\s*(Municipal General Election|Municipal Primary|General Election|"
    r"Primary Election|Presidential Primary( Election)?|"
    r"\d{4} (Republican |Municipal )?(Primary|General)( Election)?)\s*$",
)]


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True, check=True).stdout


def parse_electionware(pdf_name, year, election_type, grain):
    """grain: 'precinct' (per-precinct blocks) or 'electionwide' (summary)."""
    text = pdf_text(os.path.join(RAW, pdf_name))
    rows = []
    precinct = "Electionwide" if grain == "electionwide" else None
    contest = vote_for = None
    reg = cast = ""
    for page_no, page in enumerate(text.split("\f"), start=1):
        pending_title = None
        at_page_top = True
        prev_was_candidate = False
        lines = page.splitlines()

        def next_content(i):
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return lines[j]
            return ""

        for line_no, line in enumerate(lines):
            if not line.strip():
                prev_was_candidate = False
                continue
            if any(r.search(line) for r in SKIP_RES):
                prev_was_candidate = False
                continue
            tok = line.strip()
            # precinct id: only as the first content line of a page (all three
            # dialects print it there; continuation pages repeat it).
            if grain == "precinct" and at_page_top and (
                    ID_COLON_RE.match(tok) or ID_BARE_RE.match(tok)
                    or ID_NAME_RE.match(tok)):
                if tok != precinct:
                    contest = vote_for = None
                    reg = cast = ""
                precinct = tok
                at_page_top = False
                prev_was_candidate = False
                continue
            at_page_top = False
            m = REG_RE.match(line)
            if m:
                reg = m.group(1).replace(",", "")
                prev_was_candidate = False
                continue
            m = CAST_RE.match(line)
            if m:
                cast = m.group(1).replace(",", "")
                prev_was_candidate = False
                continue
            m = VOTE_FOR_RE.match(line)
            if m:
                contest, vote_for = pending_title or contest, m.group(1)
                pending_title = None
                prev_was_candidate = False
                continue
            m = CAND_RE.match(line)
            if m and contest:
                name = m.group(2).strip()
                if name.lower() in STAT_ROWS or name.lower().startswith(
                        ("overvotes", "undervotes")):
                    prev_was_candidate = False
                    pending_title = None
                    continue
                # leading name-wrap (2020 summary layout): the name's first
                # line carries no numbers ("LIB DANIEL RHEAD COTTAM, BARRY
                # EVAN"), the votes ride the final fragment ("SHORT  1,948").
                # A real contest title is always consumed by its "Vote For N"
                # line before any candidate row, so a pending title here is a
                # name fragment.
                if pending_title is not None:
                    name = pending_title + " " + name
                    pending_title = None
                name = " ".join(name.split())
                rows.append({
                    "year": year, "election_type": election_type,
                    "source_file": pdf_name, "sheet": f"p{page_no}",
                    "contest": contest, "vote_for": vote_for,
                    "precinct": precinct, "candidate": name,
                    "votes": m.group(3).replace(",", ""),
                    "suppressed": "False", "vote_method": "Total",
                    "times_cast": cast if grain == "precinct" else "",
                    "registered_voters": reg if grain == "precinct" else "",
                })
                prev_was_candidate = True
                continue
            # numbers-only line: the middle of a sandwich name-wrap (2020
            # summary: fragment / numbers / trailing fragment) — emit for the
            # pending fragment; otherwise an orphan statistic value, ignored.
            m = NUMBERS_ONLY_RE.match(line)
            if m and contest and pending_title is not None:
                rows.append({
                    "year": year, "election_type": election_type,
                    "source_file": pdf_name, "sheet": f"p{page_no}",
                    "contest": contest, "vote_for": vote_for,
                    "precinct": precinct,
                    "candidate": " ".join(pending_title.split()),
                    "votes": m.group(1).replace(",", ""),
                    "suppressed": "False", "vote_method": "Total",
                    "times_cast": cast if grain == "precinct" else "",
                    "registered_voters": reg if grain == "precinct" else "",
                })
                pending_title = None
                prev_was_candidate = True
                continue
            if m:
                prev_was_candidate = False
                continue
            # plain text line: a wrapped candidate-name fragment or a contest
            # title awaiting its "Vote For N". If the next content line is a
            # numbers-only line this is a LEADING name fragment (its votes
            # follow); if it directly follows a candidate row it is a TRAILING
            # fragment (2020 precinct: "...KAMALA D." / "HARRIS").
            if tok and not tok.endswith("%"):
                if prev_was_candidate and rows and \
                        not NUMBERS_ONLY_RE.match(next_content(line_no)):
                    rows[-1]["candidate"] = " ".join(
                        (rows[-1]["candidate"] + " " + tok).split())
                    continue
                pending_title = tok
            prev_was_candidate = False
    return rows


# ------------------------------------------------------- Enhanced Voting JSON

def _txt(x):
    if isinstance(x, list):
        for e in x:
            if e.get("languageId") == "en":
                return e.get("text", "")
        return x[0].get("text", "") if x else ""
    return x or ""


def parse_ev(election_slug, year, election_type):
    rows = []
    for path in sorted(glob(os.path.join(RAW, "ev", election_slug + "__*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        contest = _txt(d.get("name")).strip()
        uuid = d.get("id", "")
        m = re.search(r"Vote for (\d+)", _txt(d.get("voteFor")))
        vote_for = m.group(1) if m else ""
        src = "ev/" + os.path.basename(path)

        def emit(precinct, opts):
            for o in opts:
                nm = _txt(o.get("name")).strip()
                if o.get("isWriteIn") and not nm.lower().startswith("write-in"):
                    nm = f"Write-In: {nm}"
                vc = o.get("voteCount")
                rows.append({
                    "year": year, "election_type": election_type,
                    "source_file": src, "sheet": uuid,
                    "contest": contest, "vote_for": vote_for,
                    "precinct": precinct, "candidate": nm,
                    "votes": "" if vc is None else vc,
                    "suppressed": "False", "vote_method": "Total",
                    "times_cast": "", "registered_voters": "",
                })

        sr = d.get("summaryResults") or {}
        emit("Electionwide", sr.get("ballotOptions") or [])
        for b in d.get("breakdownResults") or []:
            emit(_txt((b.get("precinct") or {}).get("name")).strip(),
                 b.get("ballotOptions") or [])
    return rows


# ------------------------------------------------------------------- assembly

MUNICIPAL = [
    ("cache-2021-primary-precinct-summary.pdf", 2021, "municipal primary", "precinct"),
    ("cache-2021-general-summary.pdf", 2021, "municipal general", "electionwide"),
    ("cache-2023-primary-results.pdf", 2023, "municipal primary", "electionwide"),
    ("cache-2023-general-details.pdf", 2023, "municipal general", "precinct"),
]
MUNICIPAL_EV = [
    ("primary08122025", 2025, "municipal primary"),
    ("general11042025", 2025, "municipal general"),
]
# Each county-race election carries BOTH grains where published: the summary's
# Electionwide rows are the authoritative totals (the 2026 "Precinct Public"
# report withholds 36 of 126 precincts outright — small-precinct privacy — so
# precinct sums legitimately undercount there; see VERIFICATION.md), and the
# precinct rows are the geographic layer. Downstream aggregation must prefer
# Electionwide rows, exactly as build_elections.py does for the municipal file.
# 2020 presidential primary: precinct grain only — the county published no
# summary report for it (honest ceiling).
COUNTY = [
    ("cache-2020-primary-official-precinct.pdf", 2020, "primary", "precinct"),
    ("cache-2020-primary-official-summary.pdf", 2020, "primary", "electionwide"),
    ("cache-2020-general-canvass-precinct.pdf", 2020, "general", "precinct"),
    ("cache-2020-general-canvass-summary.pdf", 2020, "general", "electionwide"),
    ("cache-2020-presidential-primary-canvass-precinct.pdf", 2020,
     "presidential primary", "precinct"),
    ("cache-2022-primary-precinct.pdf", 2022, "primary", "precinct"),
    ("cache-2022-primary-summary.pdf", 2022, "primary", "electionwide"),
    ("cache-2022-general-summary.pdf", 2022, "general", "electionwide"),
    ("cache-2026-primary-precinct-public.pdf", 2026, "primary", "precinct"),
    ("cache-2026-primary-results-summary.pdf", 2026, "primary", "electionwide"),
]


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {os.path.basename(path)}: {len(rows)} rows")


def main():
    muni = []
    for pdf, year, etype, grain in MUNICIPAL:
        r = parse_electionware(pdf, year, etype, grain)
        print(f"  {pdf}: {len(r)} rows")
        muni.extend(r)
    for slug, year, etype in MUNICIPAL_EV:
        r = parse_ev(slug, year, etype)
        print(f"  ev/{slug}: {len(r)} rows")
        muni.extend(r)
    write_csv(os.path.join(HERE, "cache_municipal_results_long.csv"), muni)

    county = []
    for pdf, year, etype, grain in COUNTY:
        r = parse_electionware(pdf, year, etype, grain)
        print(f"  {pdf}: {len(r)} rows")
        county.extend(r)
    write_csv(os.path.join(HERE, "cache_county_office_results_long.csv"), county)


if __name__ == "__main__":
    main()
