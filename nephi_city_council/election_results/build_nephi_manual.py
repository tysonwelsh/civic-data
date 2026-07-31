"""Manually-entered Nephi races that are NOT in the Enhanced Voting portal JSON.

  2019 & 2021 GENERAL — pre-date the Juab County Enhanced Voting portal (2023+), so
  figures come from archived secondary sources in election_results/raw/ (UNOFFICIAL
  canvass tallies):
    2019: raw/deseret-2019-utah-municipal-general-results.html
          ("Nephi CITY COUNCIL (3 elected): Justin D. Seely (inc.) 501, Larry O.
           Ostler (inc.) 500, Nathan H. Memmott (inc.) 495, Sarah Goode 139")
    2021: raw/midutahradio-2021-municipal-election-results.html
          ("Nephi: Mayor Justin D. Seely 965, Glade R. Nielson 673; City Council
           Skip F. Worwood 1,162, Jeramie L. Callaway 834, J.D. Parady 708,
           L. Nyle Robinson 388")

  2023 PRIMARY (Sept 5, 2023) — a REAL council primary WAS held (9 candidates for 3
  seats => field 9 > 2N=6 triggers a primary; top 2N=6 advance to the Nov general).
  The Enhanced Voting portal only carries an EMPTY `primary09052023_Demo` slug (0
  votes) for this cycle, so the numbers are hand-keyed from the OFFICIAL Juab County
  Clerk canvass PDF stored in raw/ (verified 2026-07-20):
    raw/juabcounty-2023-primary-official-results.pdf
    (https://juabcounty.gov/wp-content/uploads/2023/09/Official-Results-Prim-23.pdf)
    Header: "Juab County, UT Summary Results — OFFICIAL RESULTS — Municipal Primary
    Election — September 5, 2023". Contest "Nephi City Council / Vote For 3".
  The six advancers (Worwood, Parady, Cowan, Ostler, Bradley, Miller) are exactly the
  six candidates who then appear on the 2023 Nov general — the primary eliminated
  Andersen, Ford, and Goates. (The CF layer's unresolved 2023 filers "Vanessa Goode"
  and "Carolyn Louise …" are VANESSA GOATES and CAROLYN L. FORD, now confirmed.)

No per-precinct data exists for 2019/2021 (city-total only) or the 2023 primary (the
county summary PDF prints contest totals only) -> no precinct rows for these.
Names kept UPPER-CASE to match the Enhanced Voting convention used for 2023/2025.
"""

def _pct(v, tot):
    return round(v / tot * 100, 2) if tot else 0.0

# Each entry: n_seats, vm, contest, opts=[(NAME, votes)]; optional etype (default
# "municipal general"), advance (primary advancement cutoff), note, source_file.
DATA = {
    (2019, "Council", "municipal general"): dict(
        n_seats=3, vm="plurality at-large (vote-for-3)", contest="Nephi City Council",
        opts=[("JUSTIN D. SEELY", 501), ("LARRY O. OSTLER", 500),
              ("NATHAN H. MEMMOTT", 495), ("SARAH GOODE", 139)]),
    (2021, "Mayor", "municipal general"): dict(
        n_seats=1, vm="plurality", contest="Nephi City Mayor",
        opts=[("JUSTIN D. SEELY", 965), ("GLADE R. NIELSON", 673)]),
    (2021, "Council", "municipal general"): dict(
        n_seats=2, vm="plurality at-large (vote-for-2)", contest="Nephi City Council",
        opts=[("SKIP F. WORWOOD", 1162), ("JERAMIE L. CALLAWAY", 834),
              ("J.D. PARADY", 708), ("L. NYLE ROBINSON", 388)]),
    (2023, "Council", "municipal primary"): dict(
        n_seats=3, advance=6, vm="plurality at-large (vote-for-3)",
        contest="Nephi City Council",
        opts=[("J.D. PARADY", 672), ("BART STANLEY MILLER", 449),
              ("LARRY OSTLER", 583), ("TRAVIS L. WORWOOD", 733),
              ("CAROLYN L. FORD", 200), ("VANESSA GOATES", 160),
              ("SHARI COWAN", 652), ("KOLYER K. ANDERSEN", 281),
              ("JOHN BRADLEY", 484)],
        note=("OFFICIAL Juab County canvass (Municipal Primary, Sept 5 2023); top "
              "2N=6 advanced. Official printed Contest Totals=4,608 vs named-candidate "
              "sum=4,214: the 394-vote difference is write-in/unallocated votes not "
              "itemized in the county summary. registered/ballots/turnout omitted "
              "(the PDF reports COUNTY-wide, not Nephi-only, figures)."),
        source_file="raw/juabcounty-2023-primary-official-results.pdf"),
}

races = []
cands = []
precs = []  # none for 2019/2021 or the 2023 primary (contest-total-only sources)

for (year, office, etype), c in DATA.items():
    district = "At-Large" if office == "Council" else ""
    ranked = sorted(c["opts"], key=lambda o: -o[1])
    total = sum(v for _, v in ranked)
    n_seats = c["n_seats"]
    n_cand = len(ranked)
    vm = c["vm"]
    # boundary = advancement cutoff for a primary, else the seat count
    boundary = c.get("advance", n_seats) if etype == "municipal primary" else n_seats
    for i, (name, v) in enumerate(ranked):
        cands.append(dict(
            year=year, election_type=etype, office=office, district=district,
            contest=c["contest"], candidate=name, voting_method=vm,
            round1_votes=v, round1_pct=_pct(v, total), final_votes=v,
            rank=i + 1, is_winner="True" if i < boundary else "False"))
    winner = ranked[0]
    if n_cand > boundary:
        ru = ranked[boundary]          # first loser / non-advancer
        edge = ranked[boundary - 1]    # last winner / last advancer
        margin_v = edge[1] - ru[1]
        runner_up, runner_up_votes = ru[0], ru[1]
    else:
        runner_up, runner_up_votes, margin_v = "", "", ""
    races.append(dict(
        year=year, election_type=etype, office=office, district=district,
        contest=c["contest"], n_seats=n_seats, n_candidates=n_cand, voting_method=vm,
        total_first_choice_votes=total,
        winner=winner[0], winner_votes=winner[1], winner_pct=_pct(winner[1], total),
        runner_up=runner_up, runner_up_votes=runner_up_votes,
        margin_votes=margin_v,
        margin_pct=_pct(margin_v, total) if margin_v != "" else "",
        note=c.get("note", ""), source_file=c.get("source_file", "")))
