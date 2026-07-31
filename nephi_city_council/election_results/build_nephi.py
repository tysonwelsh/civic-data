#!/usr/bin/env python3
"""Build Nephi (Juab County, UT) election_results CSVs from Enhanced Voting raw JSON
plus manually-entered externally-confirmed pre-portal years (2019/2021).
Every number traces to a file in election_results/raw/ or a cited URL in CLAUDE.md."""
import json, csv, os

RAW = "/Users/tysonwelsh/civic-data/nephi_city_council/election_results/raw"
OUT = "/Users/tysonwelsh/civic-data/nephi_city_council/election_results"

def nm(x):
    if isinstance(x, list):
        for e in x:
            if e.get("languageId") == "en":
                return e["text"]
        return x[0]["text"] if x else ""
    return x

def load(f):
    return json.load(open(os.path.join(RAW, f)))

def find_item(items, needle):
    for it in items:
        if needle in nm(it.get("name")).strip():
            return it
    return None

# ---- Contest spec: (year, etype, office, contest, n_seats, voting_method, raw_file, item_needle, detail_file) ----
# voting_method: plurality (single seat) or "plurality at-large (vote-for-N)"
EV_CONTESTS = [
    # 2025 general
    dict(year=2025, etype="municipal general", office="Mayor", contest="Nephi City Mayor",
         n_seats=1, vm="plurality",
         bi="ev-juab-general11042025-ballot-items.json", needle="Nephi City Mayor",
         detail="ev-juab-general11042025-nephi-mayor-detail.json"),
    dict(year=2025, etype="municipal general", office="Council", contest="Nephi City Council",
         n_seats=2, vm="plurality at-large (vote-for-2)",
         bi="ev-juab-general11042025-ballot-items.json", needle="Nephi City Council",
         detail="ev-juab-general11042025-nephi-council-detail.json"),
    # 2025 primary (council; top 2N=4 advance)
    dict(year=2025, etype="municipal primary", office="Council", contest="Nephi City Council",
         n_seats=2, vm="plurality at-large (vote-for-2)",
         bi="ev-juab-primary08122025-ballot-items.json", needle="Nephi City Council",
         detail="ev-juab-primary08122025-nephi-council-detail.json", advance=4),
    # 2023 general (council only; 3 seats - externally confirmed)
    dict(year=2023, etype="municipal general", office="Council", contest="Nephi City Council",
         n_seats=3, vm="plurality at-large (vote-for-3)",
         bi="ev-juab-2023-Nov-General-ballot-items.json", needle="Nephi City Council",
         detail="ev-juab-2023-Nov-General-nephi-council-detail.json"),
]

races_rows = []
cand_rows = []
prec_rows = []

def pct(v, tot):
    return round(v / tot * 100, 2) if tot else 0.0

for c in EV_CONTESTS:
    items = load(c["bi"])["data"]
    it = find_item(items, c["needle"])
    assert it, c["needle"]
    total = it["voteTotal"]
    opts = it["summaryResults"]["ballotOptions"]
    # rank by voteCount desc
    ranked = sorted(opts, key=lambda o: -o["voteCount"])
    n_seats = c["n_seats"]
    n_cand = len(ranked)
    etype, office, contest, year = c["etype"], c["office"], c["contest"], c["year"]
    district = "At-Large" if office == "Council" else ""
    vm = c["vm"]

    if etype == "municipal primary":
        # primary: winners = advancers (top `advance`); flag advancers is_winner
        adv = c.get("advance", 2 * n_seats)
        winners_idx = set(range(min(adv, n_cand)))
    else:
        winners_idx = set(range(min(n_seats, n_cand)))

    # by_candidate rows
    for i, o in enumerate(ranked):
        name = nm(o["name"])
        v = o["voteCount"]
        cand_rows.append(dict(
            year=year, election_type=etype, office=office, district=district,
            contest=contest, candidate=name, voting_method=vm,
            round1_votes=v, round1_pct=pct(v, total), final_votes=v,
            rank=i + 1, is_winner="True" if i in winners_idx else "False",
        ))

    # race-level: winner = top vote-getter; runner_up = first loser (rank n_seats+1);
    # margin = seat-deciding boundary (rank n_seats vs rank n_seats+1) -- mirrors St George schema
    winner = ranked[0]
    if etype == "municipal primary":
        # for primary, treat seat boundary as advancement boundary
        boundary = c.get("advance", 2 * n_seats)
    else:
        boundary = n_seats
    if n_cand > boundary:
        ru = ranked[boundary]            # first loser
        edge_win = ranked[boundary - 1]  # last winner / last advancer
        margin_v = edge_win["voteCount"] - ru["voteCount"]
        runner_up = nm(ru["name"]); runner_up_votes = ru["voteCount"]
    else:
        runner_up = ""; runner_up_votes = ""; margin_v = ""
    races_rows.append(dict(
        year=year, election_type=etype, office=office, district=district, contest=contest,
        n_seats=n_seats, n_candidates=n_cand, voting_method=vm,
        total_first_choice_votes=total,
        winner=nm(winner["name"]), winner_votes=winner["voteCount"],
        winner_pct=pct(winner["voteCount"], total),
        runner_up=runner_up, runner_up_votes=runner_up_votes,
        margin_votes=margin_v,
        margin_pct=pct(margin_v, total) if margin_v != "" else "",
    ))

    # precinct rows from detail
    det = load(c["detail"])
    for b in (det.get("breakdownResults") or []):
        pname = nm(b["precinct"]["name"])
        for o in b["ballotOptions"]:
            prec_rows.append(dict(
                year=year, election_type=etype, office=office, district=district,
                contest=contest, precinct=pname, candidate=nm(o["name"]),
                votes=o["voteCount"],
            ))

# expose for append of manual rows
if __name__ == "__main__":
    import build_nephi_manual as M  # noqa
    races_rows.extend(M.races)
    cand_rows.extend(M.cands)
    prec_rows.extend(M.precs)

    # sort
    et_order = {"municipal primary": 0, "municipal general": 1}
    races_rows.sort(key=lambda r: (r["year"], et_order.get(r["election_type"],9), r["office"]))
    cand_rows.sort(key=lambda r: (r["year"], et_order.get(r["election_type"],9), r["office"], r["rank"]))
    prec_rows.sort(key=lambda r: (r["year"], et_order.get(r["election_type"],9), r["office"], r["precinct"], -r["votes"]))

    # races.csv is the SCHEMA_SPEC §9 25-col federated superset (validator m.elections).
    # Nephi populates the core fields; contest_verbatim/total_votes/registered_voters/
    # ballots_cast/turnout_pct/uncontested/suppressed_precincts stay blank (unknown /
    # not-Nephi-specific); note/source_file carry per-race provenance where available.
    rf = ["year","election_type","office","district","contest","contest_verbatim",
          "n_seats","n_candidates","voting_method","total_votes",
          "total_first_choice_votes","winner","winner_votes","winner_pct",
          "runner_up","runner_up_votes","margin_votes","margin_pct",
          "registered_voters","ballots_cast","turnout_pct","uncontested",
          "suppressed_precincts","note","source_file"]
    cf = ["year","election_type","office","district","contest","candidate","voting_method",
          "round1_votes","round1_pct","final_votes","rank","is_winner"]
    pf = ["year","election_type","office","district","contest","precinct","candidate","votes"]

    def write(path, rows, fields):
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows: w.writerow(r)

    write(os.path.join(OUT, "nephi_races.csv"), races_rows, rf)
    write(os.path.join(OUT, "nephi_results_by_candidate.csv"), cand_rows, cf)
    write(os.path.join(OUT, "nephi_results_by_precinct.csv"), prec_rows, pf)
    print(f"races={len(races_rows)} candidates={len(cand_rows)} precinct_rows={len(prec_rows)}")
