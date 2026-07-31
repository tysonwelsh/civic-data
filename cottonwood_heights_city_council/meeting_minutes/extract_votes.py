#!/usr/bin/env python3
"""
Cottonwood Heights CITY COUNCIL vote extractor (PURE deterministic; no LLM, no network).
Named inline roll call; THE MAYOR VOTES (max roll = 5 = 4 districts + voting Mayor).
Emits votes/<year>/<week>/<slug>.json (resumable) + all_votes.csv (13-col standard).
Run:  python3 extract_votes.py [--force]

Roster is OBSERVED from the 2020-2026 corpus. Mayor turnover: Michael Peterson
(2020-2021) -> Mike Weichers (2022-2025) -> Gay Lynn Bennion (2026+). District seats:
Bracken/Petersen/Mikell/Bruce (2020-2023 era) -> Holton/Hyland/Newell/Birrell (2024+;
Newell & Birrell continuous from 2022). NOTE the near-collision Council Member *Petersen*
(Douglas, district) vs Mayor *Peterson* (Michael) — distinct people, distinct tokens.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ch_vote_lib import Parser, run  # noqa: E402

# Docs promoted 2026-07-17 from ../pmn_backfill/ PMN-crosscheck recovery leads. They
# live in minutes/ like every audited doc but their vote rows carry
# provenance=pmn_minutes (documented trailing 14th column; audited-primary rows =
# 'minutes') — filter provenance='minutes' for an audited-only cut. The council file
# gains the trailing provenance column the first time a council doc is PMN-promoted.
PROMOTED_PMN_BACKFILL = {"2022-01-25_retreat"}

# Wayback-recovered doc (2026-07-17 agenda-grade recovery): the 2020-10-06 council
# minutes were delisted from the live portal; the DOCUMENT bytes come from the
# Internet Archive capture of the city's own showpublisheddocument URL (holladay
# precedent) — provenance=wayback_minutes, index source=wayback.
WAYBACK_RECOVERED = {"2020-10-06_work-session-and-business-meeting"}


def provenance_for(index_row):
    stem = Path(index_row["path"]).stem
    if stem in WAYBACK_RECOVERED:
        return "wayback_minutes"
    return "pmn_minutes" if stem in PROMOTED_PMN_BACKFILL else "minutes"

ROSTER = {
    "weichers": "Mike Weichers",        # Mayor 2022-2025 (VOTES)
    "peterson": "Michael Peterson",     # Mayor 2020-2021 (VOTES)
    "bennion": "Gay Lynn Bennion",      # Mayor 2026+ (VOTES)
    "birrell": "Ellen Birrell",         # District (D4)
    "newell": "Shawn E. Newell",        # District (D3)
    "hyland": "Suzanne Hyland",         # District (D2, 2024+)
    "highland": "Suzanne Hyland",       # OCR/typo variant
    "holton": "Matt Holton",            # District (D1, 2024+)
    "bracken": "Scott Bracken",         # District (2020-2023 era)
    "petersen": "Douglas Petersen",     # District (2020-2023 era) — NOT the Mayor
    "mikell": "Christine Mikell",       # District (2020-2023 era)
    "bruce": "Tali Bruce",              # District (2020-2023 era)
}
MAYOR_TOKENS = {"weichers", "peterson", "bennion"}

PARSER = Parser(ROSTER, MAYOR_TOKENS, default_body="Council",
                body_for_path=lambda slug: "Council")

if __name__ == "__main__":
    run(Path(__file__).resolve().parent, PARSER, force="--force" in sys.argv,
        provenance_for=provenance_for)
