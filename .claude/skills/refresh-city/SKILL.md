---
name: refresh-city
description: Refresh one, several, or all city repos — probe every portal for new documents, fetch and ingest them with full provenance, rebuild the derived layers, verify source health (moved portals, rotted URLs), and refresh any expansion datasets the city has. Use when the user wants to "refresh", "update", "pull the latest", or "check for new meetings/comments/data" for cities.
---

# Refresh city data

Refreshes `<city>_city_council/` repos under /Users/tysonwelsh/civic-data. Default
scope: every city in `scripts/cities.py` (the `level=='city'` shim over the real registry
`registry/entities.csv` since 2026-07-11; 31 cities as of 2026-07-16); the
user may name cities or datasets. The per-city machinery
already exists — this skill orchestrates it and handles what the scripts can't:
judgment about changed portals, verification, and the derived-layer chain.

**Entity list = `registry/entities.csv`** (loaded by `scripts/entities.py`). `scripts/cities.py`
is a back-compat `level=='city'` SHIM — never hand-edit it, and note it does NOT list the
non-city entities (8 counties, 2 MPOs, ut_state). The generated tier tree is
`registry/HIERARCHY.md` (regenerate via `scripts/build_hierarchy.py`, never edit). The
repo-root federated database is **gov.db (formerly cities.db)** — the Phase-6 rename is in
progress; both names refer to the same file, so this doc writes "gov.db (formerly cities.db)"
to stay correct across the cutover. **Sections §1–§6 below are the CITY refresh; the
non-city-entity refresh is its own section further down.**

## Procedure

### 1. Probe (read-only, always first)

For each city in scope: `python3 <city>_city_council/fetch_new.py --probe`
(writes `<city>/refresh_probe.json`). Then `python3 scripts/refresh_status.py` and
read the regenerated `refresh_status.md`. Report to the user: which cities have new
documents, which are current, and which probes FAILED. Distinguish honestly between
repo staleness and **city-side publishing lag** (portals post approved minutes 2–6
weeks late; a "0 new" with recent unposted meetings is current, not stale — see the
notes column). Watch items live in TODO.md (e.g. the Lehi minutes-publishing lapse).

### 1b. PMN cross-check (MANDATORY post-probe step — owner-approved 2026-07-13, built 2026-07-17)

For each city in scope: `python3 scripts/pmn_crosscheck.py <slug>` (or `--all`; add
`--cached` only when re-analyzing without refetching). The engine is city-agnostic and
report-only: it diffs PMN's notice history (one-directional — PMN-has / repo-lacks;
PMN purges history, so PMN absence means nothing) against the city's minutes indexes,
using the per-city configs `pmn_backfill/pmn_bodies.csv` (body map — ALL 31 cities
seeded 2026-07-17) and `pmn_backfill/pmn_exceptions.csv` (the verified-false-positive
ledger). Output: `pmn_backfill/crosscheck_report.md` + `crosscheck_flags.csv` (+ a
dated copy under `_crosscheck/history/` — successive runs measure each city's real
PMN attachment lag; revisit the 60-day pending-adoption window per city after 2–3
cycles).

**The review gate is non-negotiable: NEVER auto-ingest a flag.** Surface
`crosscheck_report.md` in the refresh output; a human/Claude review decides per flag:
genuine recovery lead (→ TODO / a recovery pass) or a new `pmn_exceptions.csv` row
(kind + one-line reason + verified_date). `new_body` flags mean the city's PMN body
list changed (bodies re-register — draper 379→5555) — inventory the new id into
`pmn_bodies.csv` (crawl=yes only if it maps to a repo dataset). Systemic false-flag
patterns are ENGINE findings — record them in `scripts/pmn_crosscheck_HARDENING.md`
and harden the shared script, never per-city forks (per-city facts stay in the
config CSVs). Verified 2026-07-17 across all 31 cities: 640 first-run flags triaged
to a small genuine-leads ledger + exception ledgers; the flag classes and their
review semantics are documented in the engine docstring.

### 2. Source-health triage (the judgment step)

- **Probe failure** = the portal changed. Investigate: vendor migration, moved URL
  scheme, new auth wall. Fix the adapter functions in that city's `fetch_new.py`,
  add a dated note to the city's `recon.md`, and re-probe. If the portal is truly
  gone, check Utah PMN (utah.gov public notice) as the fallback source and say so.
- **URL-rot spot-check**: for each refreshed city, sample ~5 rows from its
  `sources.csv` with polite HEAD/GET; update `verified_date` on live sampled rows via
  `python3 scripts/build_sources_index.py --verify-sample`. A newly dead host goes in
  TODO.md and sources_summary.md immediately.
- Known portal quirks are documented in each fetch_new.py header (ogden needs a
  browser UA; SLC PrimeGov doesn't list PC; sandy PC stages API rows). Read before
  debugging.

### 3. Fetch + ingest (per city with new documents)

`python3 <city>_city_council/fetch_new.py --fetch` — it retains raw originals under
`<dataset>/raw/`, converts per the city's conventions, appends `minutes_index.csv`
rows with source_url, logs `retrieved_date` in `fetch_log.csv`, and runs the city's
`extract_votes.py` + `validate_votes.py`. After the fetch:
`python3 scripts/add_minutes_headers.py <slug>` (embeds the provenance header in any
new minutes markdown — idempotent) and, if packets were fetched,
`python3 scripts/extract_packet_text.py <slug>` (text sidecars → fts_packet).
Then run the quality gate on the NEW files:
`python3 .claude/skills/audit-city-data/scripts/screen_corpus.py` on the affected
year dir(s) — investigate any flag before proceeding (new documents mean new
extraction risk: wrong-doc uploads, format changes, new OCR pathologies).

### 4. Rebuild the derived chain (order matters)

Per refreshed city: `python3 scripts/rebuild_derived.py <slug> [<slug> ...]` — one
command runs the whole chain in order (db → referrals → weeks → motions_std →
sources → validate_city, then repo-level coverage.json + cities.db incl. the FTS
search layer), fail-loud at the first broken step. Validation must stay 0 FAIL;
new WARNs must be explained or fixed.

### 5. Expansion datasets (where present)

If the city has expansion datasets (`packets/`, `housing_plans/`, `ordinances/`,
`pmn_backfill/`, `transcripts/`, `campaign_finance/` — all 31 cities have `packets/`
+ `housing_plans/` since the 2026-07 expansion waves; the per-city `CLAUDE.md`
enumerates what exists), refresh each: probe its source for items newer than the max
date in its `index.csv`, fetch with raw retention + source_url/retrieved_date
provenance per the expand-city-sources contract, and note coverage changes. Sources
for these are slower-moving (housing plans are annual; ordinances follow council
action) — quarterly is the right cadence.

**5a. Primary-document doc_class chain (Source 7 — rolled out to all 31 cities
2026-07-16).** After ANY packet refresh that adds `packets/index.csv` rows, the
doc_class layer must be brought current or the new rows sit honestly-blank forever.
The per-city `packets/CLAUDE.md` is authoritative for which scripts exist and their
order; the generic chain is:

1. `python3 scripts/extract_packet_text.py <slug>` — text sidecars for newly STORED
   raws (no-op for index-only cities).
2. `python3 <city>_city_council/packets/classify_attachments.py` — every yielding
   city has one; deterministic + idempotent (safe to re-run over the whole index;
   existing pipeline columns are preserved). Blank doc_class on a new row after this
   = honestly out of scope, correct.
3. The city's pipeline step, where one exists:
   - **logan**: `packets/fetch_extract_text.py` — fetches ONLY classified rows with
     blank `fetch_status` (incremental by design), extracts, sha256s, DISCARDS the
     binary (the sanctioned §9 exception).
   - **draper**: `packets/link_text_sidecars.py` — links existing sidecars into the
     §9 columns (no fetch).
   - **cottonwood_heights / magna**: `packets/split_sections.py --write` — idempotent
     section-cutter (drops + re-cuts `packet_section` rows deterministically). CH cuts
     only appendix-TOC-era council packets; magna cuts MSD-template sections — a new
     packet with neither structure yields 0 new sections, which is correct, not a bug.
   - Everywhere else the classifier alone is the whole chain (classify-in-place).
4. Spot-check any NEWLY classified rows against their source (the precision gates
   were sampled at build time; a refresh adds unseen title patterns — if a new
   title family looks systematically misclassified, STOP and treat it as a
   classifier-boundary change, not a per-row fix).
5. B-no / honest-zero cities (see each `packets/AVAILABILITY.md` "Primary-document
   classes" section, 2026-07-16): nothing to run — but if a PORTAL CHANGES shape
   (e.g. a city starts publishing per-item attachments, or west_jordan's SPA era
   starts serving packets again), that invalidates the bucket ruling: flag it in
   TODO.md for a re-triage rather than improvising a classifier mid-refresh.
6. Class 3: new/updated General Plans or MIH elements found during a housing_plans
   refresh get text sidecars per that dataset's convention (raws RETAINED there —
   the discard-binary exception is packets-only).

The federation step in §4 (`rebuild_derived.py` → `build_cities_db.py`) already
carries `doc_class` into `document` + `fts_packet` — no extra step needed beyond
running the chain BEFORE the rebuild.

### 6. Report

Summarize per city: documents ingested (dates, datasets), validation results,
source-health findings, anything deferred. Update TODO.md if new watch-items
appeared. Multiple cities → parallel agents (one per city; never two agents on one
city).

## Non-city entities (counties · MPOs · state) — refresh per tier

The repo now federates 8 counties, 2 MPOs, and `ut_state` alongside the 31 cities. They do
NOT flow through `fetch_new.py --probe`; each is refreshed on its own terms, and **each
entity's own `CLAUDE.md` (and per-module `CLAUDE.md`/`SOURCES.md`/`recon.md`) is
authoritative** — read it before probing. Honor every honest ceiling (a tally-only body, a
suppressed precinct, a dead-on-all-channels cycle) — never fabricate names, votes, or rows
to fill one. The registry (`registry/entities.csv`) records each entity's `portal`,
`db_rel_path`, and tier notes; `registry/HIERARCHY.md` shows the tree.

### Counties (`legislative/` + `land_use/` [+ `agencies/`, `development/`] · `elections/` · `projections/` · `gis/` · `ordinances/` · `plans/`)

- **Legislative (council/commission) + land-use (PC) minutes.** Probe each county's own
  per-module fetch scripts for dates newer than the module's `minutes_index.csv` max — e.g.
  `db/fetch_minutes.py` / `db/fetch_legislative.py` (utah/weber/SLCo pattern),
  `land_use/enumerate_pmn.py` (PMN-sourced PC), `salt_lake_county/db/harvest_legistar.py`
  (Legistar). Prefer the **append-only ingest path** where a county exposes one (the CH/
  herriman `--ingest` discipline — full-build/`--fetch` paths are destructive). Every built
  county db carries the standard (possibly empty) `referral` table; the federator hard-fails
  without it, so don't drop it on a rebuild.
- **Respect the named-roll vs tally ceiling, which varies by county AND era** — weber (99.6%
  named 2015+, depth to 2000) and cache (named 2021+, tally-only scanned 2015–20) print FULL
  roll calls; utah is INVERTED (named 2015–16, then tally-only OCR 2017+); SLCo and summit are
  tally-only. A tally-only stretch is a source limit, not a gap to backfill with names. County
  motions currently carry **NULL disposition** (classifier not yet extended to counties) —
  don't infer one on refresh.
- **Elections canvass — new-cycle checks.** Each county's `elections/build_elections.py`
  draws from up to three OFFICIAL channels, in this precedence: (A) county Clerk canvass PDFs;
  (B) the Lt. Governor per-county certifications at **vote.utah.gov** (2024+); (C) the
  **Enhanced Voting JSON API** (`electionresults.utah.gov`, dataset key `<county>-county-ut`,
  precinct-level `ev_*.json` — often the PRIMARY, richest source). After a new election,
  check all three for the new cycle. **Suppression is preserved, never filled**: suppressed
  precinct rows stay marked and still reconcile to the certified canvass total. Cycles dead on
  ALL official channels are honest gaps (juab 2019/2021 municipal floors at 2023) — the caveat
  is the *city's*, never the canvass's.
- **PMN fallback (JSON-POST mechanism).** For PMN-sourced counties, the browser search is
  captcha/erroring; the working path is a **JSON POST to `/pmn/searchresult.html` with an
  `X-CSRF-TOKEN` header** (params JSON-stringified; paginate via `startingRow`;
  `publicBodyName` exact-match does NOT match "Planning Commission", so filter client-side).
  Proven in the washington build. PMN purges history, so PMN absence proves nothing.
- **Structured modules** (`projections/`, `gis/`, `ordinances/`, `plans/`, `development/`) are
  slower-moving — re-pull on the source's own cadence (Gardner projections annually; ordinance
  registers follow board action). Keep code-codification catalogs OUT of `ordinances/index.csv`
  (Weber keeps them in `code_sources.csv`) or they federate as junk ordinance rows.

### MPOs (`wfrc_mpo`, `mag_mpo`) — DATA-FORWARD, never vote-shaped

- **Board minutes are tally-only by source** — mover/seconder named, dissent COUNT-only,
  dissenters never named; the vote table is **EMPTY by source** and caveat rows encode this.
  Do NOT synthesize named rolls. Probe **magutah.gov's static tree** (MAG Board + TAC 2014+)
  and **wfrc.utah.gov's year folders** (WFRC Council/TransCom/Budget/RGC 2016+), plus the PMN
  bodies, for minutes newer than `legislative/minutes_index.csv`. MAG's MPO Board is
  **Utah-County-only** — the summit/park_city member edges are AOG/RPO and never imply MPO votes.
- **The crown jewels are the structured layers — re-pull, don't scrape.** TIP/RTP project
  layers (`projects/` → `regional_project`), the city-area projections, and Wasatch Choice GIS
  live on **ArcGIS Hub / FeatureServers** (WFRC org `taguadKoI1XFwivx` on
  `services1.arcgis.com`; MAG's ArcGIS Hub datasets). Re-pull the dataset when a new vintage
  publishes; geometry stays live at the endpoint (the repo mirrors attributes only, raw JSON
  per layer under `projects/raw/`). `SOURCES.md` is authoritative on per-vintage field drift.
- **The RTP2027 refresh seam — APPEND, never blend.** New TIP/RTP vintages land as a NEW
  vintage alongside the existing 8 TIP vintages + RTP-2050; vintages are **never blended or
  overwritten**. RTP2027 drafts are catalogued but NEVER adopted or blended into the numbers
  until final.

### `ut_state` (`legislation/` · `advisory_opinions/` · `statutes/` · `projections/`)

- **New-session sweep.** After each General or Special Session, refresh the land-use bill
  subset (floor 2015 GS) via the **PUBLIC le.utah.gov channel** — `legislation/harvest_bills.py`
  for bills/status, then named roll calls from le.utah.gov's public vote pages
  (`svotes.jsp` voteids); `harvest_shell_recovery.py` recovers sessions served as JS shells.
  **No account is created** — LegiScan bulk is the documented OWNER-GATED alternative. Watch
  the **HTML-comment shell trap** (stale placeholder rows inside comments would fabricate
  ~2,200 fake votes — `harvest_bills.py` strips them; verify none leaked). Legislators are a
  **DISJOINT person population** — never surname-merge them with municipal people.
- **New advisory opinions.** OPRO / Property-Rights-Ombudsman opinions are year-sequential;
  the state hosts are Cloudflare-walled, so fetch via **Wayback CDX**. Image-only opinions are
  an OCR/vision follow-up, not a skip.
- **Statute recodification watch.** LUDMA was **recodified effective 2025** (10-9a→10-20,
  17-27a→17-79; the old chapters are repealed stubs); `le.utah.gov` chapter XML is the only
  current source. Re-pull the tracked LUDMA sections each session and watch for further
  renumbering/amendments.

### Federation (one run, at the very end)

Non-city refreshes rebuild each entity's own derived layer (its `db/`, module CSVs), then the
repo re-federates into **gov.db (formerly cities.db)** with a SINGLE run of
`scripts/build_cities_db.py` at the END of the work package — **never during agent waves, and
never while any entity agent is live** (one federation per package is the standing protocol).
Confirm success by `integrity_check: ok` + `Search layer done (reconciliation exact)`. The
non-city loaders read `gov_level` from the registry; db-less thin counties still federate
their `projections`/`gis`/`development`/`election_result` modules.

## Rules

- Never fabricate; unrecoverable/unposted documents are honest gaps, logged, not
  filled. Raw originals are always retained. Polite scraping (the shared
  refresh_lib.py throttles and identifies itself).
- If minutes for a probed meeting exist but extraction yields something anomalous
  (0 motions from a regular meeting, duplicate body hash with an existing file),
  STOP and investigate at source before ingesting — cities upload wrong files
  (see the audit-city-data pathology catalog).
- Derived layers are never hand-edited — everything flows through regeneration.
