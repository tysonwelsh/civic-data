#!/usr/bin/env python3
"""
Cottonwood Heights PLANNING COMMISSION vote extractor (PURE deterministic; no LLM/net).
Named inline roll call (Commissioners; the Chair is a voting Commissioner). No Mayor.
Admin-hearing files are tagged body=AdministrativeHearing. Emits votes/*.json +
all_votes.csv. Run:  python3 extract_votes.py [--force]

Roster OBSERVED from the 2020-2026 PC corpus (surname-keyed; a person appears as
Commissioner or Chair in different terms — both map to the same voter).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ch_vote_lib import Parser, run  # noqa: E402

ROSTER = {
    "mills": "Dan Mills", "shelton": "Mike Shelton", "smith": "Mike Smith",
    "ebbeler": "Jonathan Ebbeler", "anderson": "Lucy Anderson", "andersen": "Lucy Anderson",
    "poulson": "Dan Poulson", "chappell": "Jessica Chappell", "chappel": "Jessica Chappell",
    "steinman": "Sean Steinman", "wilde": "Bob Wilde", "allen": "Jesse Allen",
    "bevan": "Craig Bevan", "coutts": "Chris Coutts", "rhodes": "Douglas Rhodes",
    "ryser": "Sue Ryser", "barnes": "Garry Barnes", "lugo": "Rusty Lugo",
    "griffin": "Graig Griffin",
}


def body_for(slug):
    return "AdministrativeHearing" if "administrative-hearing" in slug else "PlanningCommission"


PARSER = Parser(ROSTER, set(), default_body="PlanningCommission", body_for_path=body_for)

# Docs promoted 2026-07-16 from ../pmn_backfill/ (PMN Administrative Hearings body 3287
# + one missed PC work meeting, PC body 2148). They live in minutes/ like every audited
# doc but their vote rows carry provenance=pmn_minutes (documented trailing 14th column;
# audited-primary rows = 'minutes') — filter provenance='minutes' for an audited-only cut.
PROMOTED_PMN_BACKFILL = {
    "2020-03-11_administrative-hearing", "2020-06-17_administrative-hearing",
    "2020-07-01_administrative-hearing", "2020-09-02_administrative-hearing",
    "2021-03-17_administrative-hearing", "2021-04-07_administrative-hearing",
    "2021-05-26_administrative-hearing", "2021-09-29_administrative-hearing",
    "2021-12-15_administrative-hearing", "2022-02-09_administrative-hearing",
    "2022-03-30_administrative-hearing", "2022-05-18_administrative-hearing",
    "2022-06-08_administrative-hearing", "2022-07-06_planning-commission",
    "2022-10-12_administrative-hearing", "2023-03-01_administrative-hearing",
    # Added 2026-07-17 (PMN-crosscheck missing_minutes recovery leads):
    "2021-01-27_administrative-hearing", "2021-03-03_planning-commission",
    "2022-12-07_administrative-hearing", "2023-03-08_planning-commission",
}


def provenance_for(index_row):
    stem = Path(index_row["path"]).stem
    return "pmn_minutes" if stem in PROMOTED_PMN_BACKFILL else "minutes"


if __name__ == "__main__":
    run(Path(__file__).resolve().parent, PARSER, force="--force" in sys.argv,
        provenance_for=provenance_for)
