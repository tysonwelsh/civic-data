# planning_commission/ — Riverton Planning Commission subtree

Parallel dataset for Riverton's **Planning Commission**, sibling of `meeting_minutes/`, built to
the same schemas (SCHEMA_SPEC.md applies in full). Every `all_votes.csv` row is
`body=PlanningCommission`. Data floor **2020**.

## What's here
- `minutes/<year>/<week>/<date>_planning-commission.md` — **119** PC minutes, 2020-01-23 →
  2026-06-11. The PC meets **2nd & 4th Thursday**; the folder is keyed on that week's Monday.
  Indexed in `minutes_index.csv` (13-col standard; `source=pmn`, `format=text` — all born-digital,
  no OCR). **0 unrecovered meetings.**
- `raw/<date>_*.pdf` — retained source PDFs (never modified).
- `all_votes.csv` — long format, one row per member-vote (or one placeholder row per tally-only
  motion), the standard 13 columns **+ a documented trailing `provenance` column** (14th):
  `minutes` = audited series, `pmn_minutes` = recovered. **682 motions (672 audited + 10
  `pmn_minutes`) across 120 vote-carrying meetings; 1,308 vote rows.**
- `extract_backfill_votes.py` — merges the **2 recovered PC meetings** in `../pmn_backfill/`
  (2023-11-09 — Granicus-only, PMN never carried its minutes; 2026-06-25 — posted after the
  last PC harvest) into `all_votes.csv`, reusing this dataset's own parser and tagging
  `provenance=pmn_minutes` (promoted 2026-07-16). All 10 recovered motions passed by
  unanimous consent → tally-only placeholder rows (the majority is never guessed — the
  source ceiling holds). Their `source` points at `pmn_backfill/text/…`; they are NOT in
  `minutes_index.csv`/`minutes/` and do not feed `roster.csv` presence counts.
- `votes/<year>/<week>/<date>_*.json` — the resumable per-meeting intermediate; `all_votes.csv` is
  rebuilt from these.
- `roster.csv` — 17 commissioners observed: `commissioner, first_seen, last_seen,
  meetings_present, vote_rows`.
- `extract_votes.py` — the deterministic parser (no network; resumable).
- `validate_votes.py` — the sanity report (totals, per-year roster, tally-vs-named consistency,
  plausibility, contested list).

Run: `python3 extract_votes.py`, then `python3 extract_backfill_votes.py` (re-merges the 2
pmn_backfill meetings), then `python3 validate_votes.py` (audited-JSON subset only; the
backfill merge is reported in `votes/_backfill_extract_report.txt`).

## Vote grammar — NAMED ROLL CALL ONLY ON DIVIDED VOTES
Riverton's PC clerk prints a **full named roll call on DIVIDED votes** and "unanimous consent"
(**no names**) on unanimous ones — the honest tally-only convention. So:
- **Divided votes** (127 motions) → **fully attributed** per-member `Aye`/`Nay`/`Abstain`/`Recuse`
  rows (751 rows).
- **Unanimous** (538 motions) → tally captured, **no individual names** → one placeholder row
  (`member`/`vote` blank). The X ayes are never guessed. A blank member list on a unanimous PC
  motion is source style, **not** a parse loss.
- **Died for lack of a second** (7 motions) → recorded with no members.

548 unanimous (538 audited + 10 recovered) + 7 died = **555 tally-only** motions; + 127
named-divided = **682** total. Mover +
seconder are captured on nearly every motion; application numbers (`PLZ ##-####`) are pulled into
the JSON where cited (they feed the referral layer). `result`/`motion_type` are **verbatim**;
normalized fields live **alongside** in `motions_std.csv`.

`motion_type` distribution: Land-Use/Zoning 434, Procedural/Administrative 160, Other 77,
Ordinance 11 — a land-use-dominated body, as expected. Most PC actions are **final actions**
(site plans / CUPs / plats); rezones / general-plan / text amendments are **recommendations to the
City Council** (the cross-body referral signal in `db/civic.db`).

## One index meeting has no motions (truthful)
`minutes_index.csv` has **119** meetings but only **118** carry votes: **2020-06-09** is a
**discussion/study meeting with no motions taken** (verified at source — no "moved"/"seconded"/
"vote" language). This is a truthful no-action meeting, not a dropped meeting (`../VERIFICATION.md`
§2). With the 2 pmn_backfill meetings merged, `validate_city.py` prints **120** distinct PC
source refs (118 audited + 2 `pmn_backfill/text/…`).

## Commissioners (roster.csv — top by tenure)
Gary Cannon (2020→2026), Troy Rushton (2020→2025), Shelly Cluff (2021→2026, acting chair in some
2023 meetings), Evan Matheson, Darren Park, Monique Beck, Keith Breinholt, Brian Russell, Crystal
Keele, Grant Lefgren, Jon Gilchrist (chair, 2022→2024), plus earlier members (Hartley, Brown,
James, Hansen) and recent adds (Chris Knudsen, Joe Marzo). Note **Darren Park** the commissioner is
distinct from **Darren J. Park** the 2017/2025 council candidate — join on full context.

## Acquisition — Granicus mirrored on Utah PMN (body 5473)
Same two-portal setup as the Council: minutes from the **Utah PMN mirror** (`utah.gov/pmn`, body
5473) of the city's **Granicus** archive — clean born-digital text. See `../recon.md`.
