# HANDOFF — resume point (2026-08-02: COUNTY ACQUISITION + VISION-TOTALS both COMPLETE)

> **2026-08-02 addendum — the vision-totals tranche is DONE on top of the state below.**
> Every county CF cover was vision-read (7-agent owner-approved wave; survived a
> session-limit kill and a network outage via cache-checkpoint discipline). gov.db (built
> 2026-08-02T12:13) now carries **cf_filing 3,802** (1,891 city + 1,911 county stated-totals
> rows), caveat **104** (county rows rewritten to totals-tier truth), all gates green
> (44/44 · doc checks 13/13 · marquee 5/5 · city cf rows byte-identical to the pre-package
> baseline). cf_cycle remains CITY-ONLY by design (county rollup = design lead in
> LEADS.md). The ZERO-GLYPH RULING is decided and executed (owner 2026-08-02: Ø/-0-/"zero"
> = the digit 0, verbatim preserved; dash/N-A/empty stay blank — GOTCHAS.md carries it
> repo-wide; 7 summit cells + wasatch Kahler promoted, re-federated, gates green). Owner
> decisions open: COMMIT (all work uncommitted) and Phase B of tranche 3 (vision
> itemization of the scanned majority — per-wave approval). TRANCHE 3 PHASE A is DONE
> (2026-08-02 evening): calibration suite (14 specimens), 6 shared families + driver
> capabilities (city byte-identity proven), born-digital sweep (1,311 itemized rows, 6
> counties, geometry-anchored), federated + gated (cf_contribution 25,147 /
> cf_expenditure 19,987; 44/44; doc checks PASS). Everything below this banner describes
> the 2026-08-01 state it built on.

> **Read in order: root `CLAUDE.md` → this file → `TODO.md` → `GOTCHAS.md`. Options menu:
> `LEADS.md`. Publish criteria: `SHIP_GATE.md`. One session banner, overwritten per handoff
> (prior banner: TODO_ARCHIVE.md anchor 2026-08-01-COUNTY-ACQUISITION).**

## Where the repo stands (verified 2026-08-01T16:07 build)

The COUNTY DATA ACQUISITION package (both halves) is **DONE and federated** — one
federation, all gates green: auto-gate **44/44**, integrity ok, FK 0, reconciliation
exact, `check_doc_numbers.py` **13/13**, marquee examples **5/5**, `v_council_current`
193/31. [DEBT] is EMPTY (the st_george Larkin item was filed, verified at source, FIXED,
and closed within this session). gov.db headline: motion 78,561 · vote 247,459 ·
**election_race 810** · **election_result 5,820** · caveat **104** · cf_contribution
**24,741** · cf_filing 2,082 · fts_minutes 14,696. G9 (public flip) still parked.

## What this session landed (detail: TODO.md changelog + TODO_ARCHIVE anchor)

- **Package A** — SLCo even-year canvasses 2002–2026 in-repo + parsed (3 never-parsed
  eras cracked; dual reconciliation gates), 122 audited county-office races federated
  into election_race, 338 county-office tally rows into election_result (new columns
  `election_date`/`certified_votes`/`votes_basis` — use certified_votes under 2024/2026
  suppression). Loader changes in `build_cities_db.py` (backed up).
- **Package B** — 8 county `campaign_finance/` datasets, ~2,270 county-office filings
  2006–2026 (all row offices). STRUCTURED so far: salt_lake (EasyVote 2024/2026
  itemized; **the owner's "largest county-race donor" question now answers from
  cf_contribution**) + juab (3 transcribed 2020 filings). The other six are
  document-tier awaiting the vision pass. `load_cf` now iterates ALL entities; city rows
  proven byte-identical (baselines in `_backups/2026-08-01-county-acquisition/`).
- **st_george DEBT fix** — two state-channel AMENDED 2023 filings ingested +
  vision-transcribed (itemized = stated exactly); Larkin 2023 cycle corrected to
  **$33,610 / $31,491.92**; originals superseded-marked; validate_finance PASS.
- **Caveats 92→104** (8 county-CF ceilings, 4 SLCo county-election rows, cf-coverage
  rewritten two-tier). GOTCHAS.md +7 portal rules (PMN keyword no-op; state-folder
  labels lie BOTH ways — classify by in-form office line + cycle parity; Wayback
  200-with-zero-bytes; EasyVote API recipe; BigIP-dead SLCo portal; Wix headers;
  backslash URLs). LEADS.md: full wave consolidation + 3 WATCHES + the owner's
  school-board ruling (ledgered, out of scope). wasatch_county → `built_dbless`
  (first dataset); hierarchy regenerated; coverage.json + DATA_DICTIONARY.md rebuilt.
- **`.gitignore`**: `slco_county_results_long.csv` (78 MB, derived) kept local-only —
  reversible owner call.

## NOT yet done (owner decisions / follow-ups — all in LEADS.md or [GATED])

1. **Vision-transcription pass scope** (owner): cheap first tranche = office-line-only on
   ~195 unresolved filings (cache 128 / utah 19 / washington 48); full-dollar tranches
   county-by-county after. `cf-vision-transcribe` needs a county-tier entry point.
2. **Metro-township CF** (297+57 plain-GET filings) — likely closes kearns
   `cf-blocked-cycles`.
3. SLCo 2016–2021 CF portal era (browser automation or GRAMA); juab + weber + washington
   GRAMA asks drafted in their AVAILABILITY files.
4. election_race promotion for the OTHER counties' county-office tallies (Package-A
   pattern is the reference).
5. Shared CF family candidates (6 specs) + driver per-filing/per-sheet `is_incremental`
   capability; `validate_finance.py` document-only conformance mode.
6. The session's work is **UNCOMMITTED** — commit needs the owner's go
   (`_backups/2026-08-01-county-acquisition/` holds every pre-edit original + the
   byte-identity baselines).

## Discipline reminders (unchanged)

Cardinal rules (CLAUDE.md); GOTCHAS.md before touching portals or builders; ONE
federation per work package (this package's is done — the next change re-federates);
after any federation run `check_doc_numbers.py` and reconcile; leads → LEADS.md; [DEBT]
needs primary-source evidence; agent waves need owner approval (count/model/effort).
