#!/usr/bin/env python3
"""
Build Ogden City municipal election CSVs from raw/ sources.

Ogden Municipal Council = 4 district seats (1-4) + 3 at-large seats (A/B/C),
all single-winner, plus a separately-elected Mayor (strong-mayor form).
Odd-year cycles, staggered:
  A-cycle (Mayor + At-Large C + Districts 2 & 4): 2019, 2023
  B-cycle (At-Large A & B + Districts 1 & 3):     2021, 2025
We capture BOTH the August PRIMARY and the November GENERAL as separate races
(`election_type` = "municipal primary" / "municipal general").

Sources (all in raw/), per cycle:
  2019 general  -> 2019_general_results.pdf  (Ogden summary page; summary-only, no precinct)
  2019 primary  -> NO RAW HELD. Weber County administers Ogden's elections and no 2019
                   primary canvass was ever fetched into raw/; whether a 2019 Ogden
                   primary was even required is UNVERIFIED (the general carried 2 mayoral
                   candidates and 3 unopposed council seats). Ledgered as an honest gap in
                   CLAUDE.md -- never synthesized.
  2021 general  -> 2021_general_b.pdf        (Weber canvass summary; summary-only, no precinct)
  2021 primary  -> 2021_general_results.pdf  (MISNAMED in raw/: this file is the Weber
                   County "2021 Primary" summary, Aug 10 2021 -- see CLAUDE.md GOTCHA 3).
                   Summary-only; its STATISTICS block is county-wide, not Ogden-scoped,
                   so registered_voters/ballots_cast/turnout are left blank.
  2023 general  -> raw/state_api/items/2023-Nov-General__*.json
                   (Weber County publishes NO 2023 general municipal PDF -- the county
                    results index says "For municipal results visit the municipality's
                    website" -- so the state Enhanced Voting portal export is the source.
                    It carries full per-precinct breakdown.)
  2023 primary  -> 2023_primary_ogden_results.pdf (ALSO misnamed: it is the OGDEN CITY
                   *precinct-level* Official Canvass for the Sep 5 2023 primary, 41 pages /
                   41 precincts. The sibling 2023_primary_ogden_precinct.pdf is NORTH Ogden
                   and is NOT used.) Ogden has no citywide summary page in that PDF, so the
                   race/candidate totals are SUMMED over its 41 precinct pages and
                   cross-checked against the printed per-page "Total Votes Cast" lines
                   (must agree exactly, else the build aborts).
  2025 general  -> 2025_general_precinct.pdf  (Weber born-digital per-precinct canvass)
                   cross-checked against raw/state_api/items/general11042025__*.json
  2025 primary  -> raw/state_api/items/primary08122025__OGDEN_CITY_*.json (summary +
                   42-precinct breakdown; the same two voter-privacy-suppressed precincts
                   as the 2025 general -- 29OG31, 29OG41:U -- return null counts).
  The 2025_primary_ogvalley_* PDFs are OGDEN VALLEY, a different city -- not used.

Output: ogden_races.csv, ogden_results_by_candidate.csv, ogden_results_by_precinct.csv
Reproducible: python3 build_ogden_elections.py   (needs pdftotext on PATH)
"""
import csv, json, os, re, subprocess, sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
ITEMS = os.path.join(RAW, "state_api", "items")

GENERAL = "municipal general"
PRIMARY = "municipal primary"


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
def build_records(year, contests, election_type=GENERAL, keep_verbatim=None):
    """contests: list of dicts with keys:
        office, district,
        candidates:[(name,votes)]          -> authoritative race/candidate totals
        precincts:{pname:{name:votes}}     -> per-precinct rows (optional)
        suppressed:[pname,...]             -> precincts present but vote-withheld (optional)
      optional 25-col-superset extras (blank unless the SOURCE supports them; the 2019-2025
      GENERAL rows predate the superset upgrade and deliberately carry blanks):
        verbatim, voting_method, registered_voters, ballots_cast, note, source_file
    Returns (race_row, candidate_rows, precinct_rows).

    NOTE on primaries: `winner` / `runner_up` are the top-two vote-getters, i.e. the two
    who ADVANCE to the general -- not an office-winner. Where the general's field does not
    equal the primary's top two (a withdrawal), the race row carries an explicit `note`;
    the advancement is never inferred, only observed against the general we already hold.

    keep_verbatim defaults to PRIMARY-only ON PURPOSE. The 2019-2025 GENERAL rows were
    audited into the 25-col superset with the ten extra columns blank; this build leaves
    them byte-identical rather than back-filling them as a side effect of adding the
    primaries. Flip keep_verbatim=True on the general calls to backfill contest_verbatim
    (the parsers already carry it) as a separate, reviewable change."""
    if keep_verbatim is None:
        keep_verbatim = election_type == PRIMARY
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
            cand_rows.append(dict(year=year, election_type=election_type, office=office,
                                  district=district, contest=contest, candidate=name,
                                  votes=votes, pct=pct, rank=rank, is_winner=is_win))
        winner = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else None
        margin_v = (winner[1] - runner[1]) if runner else winner[1]
        margin_p = round(winner[2] - runner[2], 2) if runner else 100.0
        reg, bal = c.get("registered_voters", ""), c.get("ballots_cast", "")
        turnout = round(100.0 * bal / reg, 2) if (reg and bal) else ""
        sup = c.get("suppressed", [])
        races.append(dict(year=year, election_type=election_type, office=office,
                          district=district, contest=contest,
                          contest_verbatim=(c.get("verbatim", "") if keep_verbatim else ""),
                          n_seats=1,
                          n_candidates=len(cands),
                          voting_method=c.get("voting_method", ""), total_votes=total,
                          total_first_choice_votes="",
                          winner=winner[0], winner_votes=winner[1], winner_pct=winner[2],
                          runner_up=(runner[0] if runner else ""),
                          runner_up_votes=(runner[1] if runner else ""),
                          margin_votes=margin_v, margin_pct=margin_p,
                          registered_voters=reg, ballots_cast=bal, turnout_pct=turnout,
                          uncontested=c.get("uncontested", ""),
                          suppressed_precincts=c.get("suppressed_flag", ""),
                          note=c.get("note", ""), source_file=c.get("source_file", "")))
        for pname, votemap in c.get("precincts", {}).items():
            for cand, votes in votemap.items():
                prec_rows.append(dict(year=year, election_type=election_type, office=office,
                                      district=district, contest=contest,
                                      precinct=norm_precinct(pname), candidate=cand,
                                      votes=votes, suppressed=False))
        # suppressed precincts: appeared in the canvass but votes withheld (voter
        # privacy in very small precincts). Emit one placeholder row per candidate
        # with blank votes so the precinct↔canvass reconciliation is auditable.
        for pname in sup:
            for name, _ in cands:
                prec_rows.append(dict(year=year, election_type=election_type, office=office,
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
                    cur = dict(office=office, district=district, candidates=[],
                               precincts={}, verbatim=ln.strip())
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
def parse_state_items(prefix, year, election_type=GENERAL, extras=None):
    contests = []
    for fn in sorted(os.listdir(ITEMS)):
        if not fn.startswith(prefix) or not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(ITEMS, fn)))
        name = d["name"][0]["text"].strip().upper()
        # look-alike guard: OGDEN VALLEY / NORTH OGDEN items live in the same export
        if "OGDEN CITY" not in name or "NORTH OGDEN" in name or "OGDEN VALLEY" in name:
            continue
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
        prec, suppressed = {}, []
        for br in d.get("breakdownResults", []) or []:
            pname = br["precinct"]["name"][0]["text"]
            opts = {b["name"][0]["text"].strip(): b["voteCount"] for b in br["ballotOptions"]}
            # voter-privacy suppression: the portal returns null counts for very small
            # precincts. Their votes ARE in the summary total, so keep the summary as
            # authoritative and emit blank/suppressed=True placeholder precinct rows.
            if any(v is None for v in opts.values()):
                suppressed.append(pname)
            else:
                prec[pname] = opts
        c = dict(office=office, district=district, candidates=cands, precincts=prec,
                 suppressed=suppressed, verbatim=d["name"][0]["text"].strip())
        c.update((extras or {}))
        if suppressed:
            c["suppressed_flag"] = True
        contests.append(c)
    if not contests:
        sys.exit(f"no state items for prefix {prefix}")
    return build_records(year, contests, election_type)


# ---------------------------------------------------------------------------
# Ogden City per-precinct Official Canvass PDF with NO citywide summary page
# (the 2023 PRIMARY). Citywide race/candidate totals are SUMMED over the precinct
# pages and cross-checked against each page's printed "Total Votes Cast" line.
# ---------------------------------------------------------------------------
def parse_ogden_precinct_canvass(fname, year, election_type, expect, source_file):
    text = pdftext(fname)
    lines = text.splitlines()
    PREC_RE = re.compile(r"^(OGD\d+(?::\w+)?)\s*$")
    STAT_RE = re.compile(r"^(Registered Voters - Total|Ballots Cast - Total)\s+([\d,]+)\s*$")
    TOTAL_RE = re.compile(r"^Total Votes Cast\s+([\d,]+)\s+100\.00%\s*$")

    contests = OrderedDict()          # header -> {office,district,cands:Counter,prec:{}}
    printed_totals = OrderedDict()    # header -> summed printed "Total Votes Cast"
    stats = OrderedDict()             # precinct -> {stat: n}
    seen = OrderedDict()              # header -> set(precincts carrying the contest)
    cur_prec = cur = None
    in_stats = False

    # every contest header is immediately followed by a "Vote For N" line -- the same
    # boundary test the summary/precinct parsers use. Without it the page FOOTER
    # ("Ogden City Precinct Level Results - ... Page 1 of 41") reads as a contest header.
    def next_nonblank(i):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        return lines[j].strip().upper() if j < len(lines) else ""

    for i, ln in enumerate(lines):
        s = ln.strip()
        pm = PREC_RE.match(s)
        if pm:
            cur_prec, cur, in_stats = pm.group(1), None, True
            stats.setdefault(cur_prec, {})
            continue
        u = s.upper()
        if next_nonblank(i).startswith("VOTE FOR"):
            cur = None                      # any header closes the previous contest
            if not (u.startswith("OGDEN CITY") and "NORTH OGDEN" not in u
                    and "OGDEN VALLEY" not in u):
                continue
            m = CONTEST_HEADER.search(s)
            if not m:
                sys.exit(f"{fname}: unrecognized Ogden contest header: {s}")
            if m.group(1).upper() == "MAYOR":
                office, district = "Mayor", ""
            elif m.group(2):
                office, district = "Council", f"At-Large {m.group(2).upper()}"
            else:
                office, district = "Council", (m.group(3) or m.group(4))
            cur, in_stats = s, False
            contests.setdefault(cur, dict(office=office, district=district,
                                          cands=OrderedDict(), prec={}))
            seen.setdefault(cur, set()).add(cur_prec)
            continue
        if in_stats and cur_prec:
            sm = STAT_RE.match(s)
            if sm:
                stats[cur_prec][sm.group(1)] = int(sm.group(2).replace(",", ""))
            continue
        if cur:
            tm = TOTAL_RE.match(s)
            if tm:
                printed_totals[cur] = printed_totals.get(cur, 0) + int(tm.group(1).replace(",", ""))
                cur = None
                continue
            cm = CAND_LINE.match(ln)
            if cm:
                nm, v = cm.group(1).strip(), int(cm.group(2).replace(",", ""))
                contests[cur]["cands"][nm] = contests[cur]["cands"].get(nm, 0) + v
                contests[cur]["prec"].setdefault(cur_prec, {})[nm] = v

    out = []
    for header, info in contests.items():
        summed = sum(info["cands"].values())
        if summed != printed_totals.get(header):
            sys.exit(f"{fname}: {header}: precinct-summed {summed} != printed "
                     f"Total-Votes-Cast sum {printed_totals.get(header)}")
        ps = seen[header]
        out.append(dict(office=info["office"], district=info["district"],
                        candidates=list(info["cands"].items()), precincts=info["prec"],
                        verbatim=header, voting_method="plurality", uncontested=False,
                        suppressed_flag=False, source_file=source_file,
                        registered_voters=sum(stats[p].get("Registered Voters - Total", 0)
                                              for p in ps),
                        ballots_cast=sum(stats[p].get("Ballots Cast - Total", 0) for p in ps)))
    found = {canon_contest(c["office"], c["district"]) for c in out}
    if expect - found:
        sys.exit(f"{fname}: expected contests not found: {expect - found}; found {found}")
    return build_records(year, out, election_type)


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

    # ---- PRIMARIES (August; the seat-narrowing round) -------------------------------
    # 2019: no primary canvass held in raw/ -> honest gap (see module docstring).
    #
    # 2021 primary -- raw/2021_general_results.pdf is MISNAMED; it is the Weber County
    # "2021 Primary" (Aug 10, 2021) summary. Only the >2-candidate Ogden fields appear:
    # At-Large A and District 3 (At-Large B and District 1 drew 2 candidates each, so no
    # primary was held for them -- confirmed against the 2021 general's n_candidates).
    p21 = parse_summary_contests("2021_general_results.pdf")
    for c in p21:
        c.update(voting_method="plurality", uncontested=False, suppressed_flag=False,
                 source_file="raw/2021_general_results.pdf",
                 note="File name says 'general'; the PDF is the Aug 10 2021 Weber County "
                      "PRIMARY. Its STATISTICS block is county-wide, not Ogden-scoped, so "
                      "registered_voters/ballots_cast/turnout_pct are left blank.")
    exp21 = {"Ogden City Council At-Large Seat A", "Ogden City Council District 3"}
    got21 = {canon_contest(c["office"], c["district"]) for c in p21}
    if got21 != exp21:
        sys.exit(f"2021 primary: expected {exp21}, found {got21}")
    r, c, p = build_records(2021, p21, PRIMARY)
    all_races += r; all_cands += c; all_prec += p

    # 2023 primary -- Ogden City per-precinct Official Canvass, no citywide summary page;
    # totals summed over 41 precinct pages and reconciled to the printed page totals.
    r, c, p = parse_ogden_precinct_canvass(
        "2023_primary_ogden_results.pdf", 2023, PRIMARY,
        {"Ogden City Mayor", "Ogden City Council At-Large Seat C",
         "Ogden City Council District 4"},
        "raw/2023_primary_ogden_results.pdf")
    all_races += r; all_cands += c; all_prec += p

    # 2025 primary -- state portal export (Weber published only an Ogden VALLEY primary PDF).
    r, c, p = parse_state_items(
        "primary08122025__", 2025, PRIMARY,
        extras=dict(voting_method="plurality", uncontested=False,
                    source_file="raw/state_api/items/primary08122025__OGDEN_CITY_*.json"))
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

    # ---- primary -> general advancement cross-check (OBSERVED, never inferred) -------
    # A primary's top two are the two who should appear on the November ballot. Where the
    # general's field differs, the primary row is annotated with the discrepancy verbatim;
    # no cause (withdrawal, disqualification, ...) is asserted -- no held source states one.
    gen = {(x["year"], x["contest"]): x for x in all_races if x["election_type"] == GENERAL}
    for x in all_races:
        if x["election_type"] != PRIMARY:
            continue
        g = gen.get((x["year"], x["contest"]))
        if not g:
            print(f"  [{x['year']} primary->general] {x['contest']}: no general row to check")
            continue
        adv, field = {x["winner"], x["runner_up"]}, {g["winner"], g["runner_up"]}
        if adv != field:
            x["note"] = ((x["note"] + " ") if x["note"] else "") + (
                f"Primary top two ({', '.join(sorted(adv))}) are NOT the general's field "
                f"({', '.join(sorted(field))}): {', '.join(sorted(adv - field))} did not "
                f"appear on the November ballot. Both rows are as canvassed; no held source "
                f"states the reason and none is inferred here.")
        print(f"  [{x['year']} primary->general] {x['contest']}: "
              f"{'OK' if adv == field else 'DIFFERS -> annotated'}")

    # ---- write CSVs ----
    # the repo-wide audited 25-column race superset (SCHEMA_SPEC; peers murray/holladay).
    # Columns the SOURCE does not support stay blank -- never filled by inference. The
    # 2019-2025 GENERAL rows predate the superset and carry blanks in the ten extras.
    races_cols = ["year", "election_type", "office", "district", "contest",
                  "contest_verbatim", "n_seats", "n_candidates", "voting_method",
                  "total_votes", "total_first_choice_votes", "winner", "winner_votes",
                  "winner_pct", "runner_up", "runner_up_votes", "margin_votes",
                  "margin_pct", "registered_voters", "ballots_cast", "turnout_pct",
                  "uncontested", "suppressed_precincts", "note", "source_file"]
    cand_cols = ["year", "election_type", "office", "district", "contest", "candidate",
                 "votes", "pct", "rank", "is_winner"]
    prec_cols = ["year", "election_type", "office", "district", "contest", "precinct",
                 "candidate", "votes", "suppressed"]

    order = {2019: 0, 2021: 1, 2023: 2, 2025: 3}
    # within a year the GENERAL block comes first, then the PRIMARY block -- this keeps
    # every pre-existing general row in exactly its previous relative position.
    type_order = {GENERAL: 0, PRIMARY: 1}
    dist_order = {"": 0, "1": 1, "2": 2, "3": 3, "4": 4,
                  "At-Large A": 5, "At-Large B": 6, "At-Large C": 7}
    base = lambda x: (order[x["year"]], type_order[x["election_type"]],
                      0 if x["office"] == "Mayor" else 1,
                      dist_order.get(str(x["district"]), 9))
    all_races.sort(key=base)
    all_cands.sort(key=lambda x: base(x) + (x["rank"],))
    all_prec.sort(key=lambda x: base(x) + (x["precinct"], x["candidate"]))

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
