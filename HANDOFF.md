# HANDOFF — resume point (2026-08-18: PHASE B — 4 COUNTIES CLOSED, FEDERATED & COMMITTED)

> **Read in order: root `CLAUDE.md` → this file → `TODO.md` → `GOTCHAS.md`. Options menu:
> `LEADS.md`. Publish criteria: `SHIP_GATE.md`. One session banner, overwritten per handoff
> (prior banner: TODO_ARCHIVE.md anchor 2026-08-17-PHASEB-RESUME).**

## CONSOLIDATION DONE 2026-08-18 — the tree is banked

Federation rebuilt 2026-08-18T01:12 (FK 0, integrity ok, reconciliation exact);
`check_doc_numbers.py` 13/13 PASS; `validate_entity.py --federation` **44/44 in step**.
slc CF no longer stale (248C/176E in db = disk). All four wave caveats federated.
County itemized rows now in `gov.db`: slco 19,702 · weber 1,360 · summit 1,298 ·
wasatch 346 · washington 181 · utah 72 · juab 46 · cache 32.

## Wave state — Phase B county itemization

- **juab — CLOSED & VERIFIED** (2026-08-14). 27/27 filings, 187 rows.
- **wasatch — CLOSED & VERIFIED** (2026-08-14). 111/111 filings, 851 rows.
- **summit — CLOSED & VERIFIED** (2026-08-17). Queue closed **116/116 scans; 131/131
  filings itemized**; 2,600 vision rows (1,193C+1,407E), 100% geometry. 181 sides exact,
  29 filer deltas verbatim, 15 no-schedule, **5 withheld** (1250 amount column off the
  scan; 1268 contrib + 4278 expend where neither printed figure closes; 12943/12944 blank
  pages, no gate). `validate_entity` 12 PASS / 3 WARN / 0 FAIL.
- **weber — CLOSED & VERIFIED** (2026-08-18). **98/98 filings itemized** (93 vision +
  5 born-digital); **1,360C + 1,256E = 2,616 rows, 100% geometry-anchored**; 186 sides =
  149 transcribed / 26 empty-schedule / 11 no-schedule-page / **0 withheld**; 134 of 149
  close exactly on a printed figure (62 exact + 72 period-exact), 15 filer deltas verbatim.
  The 18 geometry re-measures came back **18/18 measured, zero unmeasurable**.
  `validate_entity` 13 PASS / 1 WARN / 0 FAIL (== baseline).

The weber audit WITHDREW 70 already-published rows and replaced 16 more — its killed-leg
output had reached the canonical CSVs (summit's had not). Nothing survived because it was
already published.

## OWNER RULING RATIFIED 2026-08-17 — reconciliation basis

> Reconcile each itemized side against the printed cover figure that MATCHES ITS OWN SCOPE
> — Current Report for a period ledger, Cumulative for a cumulative one. Tag rows with
> `is_incremental`. NEVER synthesize a figure by differencing covers. Withhold only where
> NEITHER printed figure closes.

Applied to summit: **16 sides / 81 rows promoted**, 5 correctly still withheld; no
`stated_*` cell changed, CSV diffs additions-only, rebuild byte-identical. Weber had
ALREADY implemented the rule (`period-exact`); one divergence corrected (verified period
sides were leaving `reconciles_*` blank). Full record: LEADS.md 2026-08-17 blocks.

⚠ **Shared-script change to review:** `scripts/campaign_finance/validate_finance.py` check 6
now admits ONE declared exception (every row `is_incremental=True` AND a literal
`ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)` marker in notes). All 38 CF modules
re-run, all PASS, none newly relaxed. **SCHEMA.md §4 was NOT updated to record it — owed.**

## New [DEBT] (queue was empty since 2026-08-01) — both are TOOLING, both repo-wide

- ~~`make_snippet.py` rotation bug~~ **FIXED 2026-08-18** (page size now returned as
  poppler renders it; one fix covers the pct/px/span paths; `/Rotate 0` control 80/80
  byte-identical; the oversized-mediabox blank-crop defect fixed too, with a dpi clamp).
  **STILL OPEN: the repo-wide RE-PROOF of geometry previously "validated" with the broken
  tool on rotated pages** (closed SLCo B2 + summit work) — that re-audit was out of scope.
- **`rowbands.py`** registers text baselines as rules on typed sheets, returns
  header/spacer bands, and measures on a DESKEWED copy while cropping from the RAW render.
  **Fix BEFORE the LEADS-proposed promotion to `scripts/campaign_finance/`.**

## Owner decisions open

- Next wave go: **utah 245** · cache pre-2022 Carr era · washington scans.
- **SLC GRAMA send** (drafted, not sent — `slc_city_council/campaign_finance/GRAMA_PREP_2026-08-14.md`).
- **4278 Adair summit expend** — 10 rows held out over **+$0.30** after full escalation;
  extend the delta-verbatim contract to withheld-then-promoted sides?
- G9 (public flip) parked; [GATED] retro-anchor/blind-reverify program unchanged.

## Highest-value leads from this wave (full text: LEADS.md 2026-08-17)

- **Cross-county cover-chain sweep** — the swapped Gibson pair proves the 2026-08-01 totals
  tranche can file a CORRECT reading under the WRONG key; no arithmetic gate sees it. Cheap
  detector, no vision cost: chain each filing's Last-Report vs the prior Cumulative across
  all 8 counties' 1,911 cover rows. **Run before the utah wave.**
- **In-kind treatment is PER-FILER, not a form property** — test both conventions per filing.
- **Ogden Valley City** appears in weber's 2026 filings (incorporated off the 2024 ballot) —
  not in `registry/entities.csv`.
- Cross-channel corroboration record: weber Harvey 2016 transcribed twice, independently,
  hours apart — **all 60 donor + 101 vendor rows agree** on name and amount.

## Discipline reminders (unchanged)

Cardinal rules (CLAUDE.md); GOTCHAS.md before touching portals or builders; ONE federation
per work package; after any federation run `check_doc_numbers.py` and reconcile; leads →
LEADS.md; [DEBT] needs primary-source evidence; agent waves need owner approval
(count/model/effort); wave agents never run `build_cities_db.py` and never edit root docs.
