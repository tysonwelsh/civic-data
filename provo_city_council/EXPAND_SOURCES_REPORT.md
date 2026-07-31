# expand-city-sources — Provo expansion report

**Date:** 2026-07-03 · **City:** Provo (Utah County) · **Skill:** `.claude/skills/expand-city-sources/`
**Fourth city** (after Lehi/Granicus, St. George/Revize, West Jordan/PrimeGov). Purpose: exercise the
**Hyland OnBase "Agenda Online"** portal family. All six datasets built; every one passes
`validate_dataset.py`; no existing dataset modified; parent docs written once by the orchestrator
(fan-out doc-ownership — zero agent collisions). Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**LINK INDEX**) | **391 packets** (Council 306, PC 85), ~16 GB catalogued, 0 stored | **Two portals:** Council = OnBase (CSRF+cookie, chunked/no-Content-Length), PC = CivicPlus AgendaCenter. 100% vote-date coverage |
| 2 | Housing → `housing_plans/` | **6 PDFs (~33 MB)**: 2023 GP, MIH element (GP App. B), state 23/24/25 + SB 34 | MIH element unlinked on GP page (found by search); `provo.org` bot-gated |
| 3 | Ordinances → `ordinances/` | **213 rows (135 zoning)**; 34 `high`/20 `medium`/126 `within_source`/33 `none` | **PMN "Notice of Ordinances Approved" (.docx)** is an independent corroborator; 3 genuine adopted-not-in-votes; 2023 number gap |
| 4 | PMN backfill → `pmn_backfill/` | **390 docs / 100 dates (118 MB)** — biggest recovery in the repo | Recovered the **entire empty 2020–2024 PC record** (per-item ROA) + 8 council special meetings; 0 still-missing |
| 5 | Transcripts → `transcripts/` | **10 ASR** + 740-video map | Continuous 2014+, no off-YouTube cutoff; PC not on YouTube |
| 6 | Campaign finance → `campaign_finance/` | **41 filings (~50 MB)**, 38/41 join | City Recorder CivicPlus DocumentCenter (`provo.gov/1001`); no EasyVote; 2019 gap |

**Existing layer untouched:** `all_votes.csv` 6,373 rows, 311 council + 26 PC minutes, db unchanged.
**New footprint on disk:** ~215 MB (packets index-only; PMN ROA backlog 118 MB + finance 51 MB are the bulk).

## Timing
Six agents in parallel; end-to-end ≈ slowest (~30 min, campaign-finance OCR) + verification/docs.

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **PC record was essentially empty 2020–2024** in the audited layer; PMN backfill recovered 70
   PC meeting-dates (ROA docs). The strongest "core layer is incomplete" signal of the four cities.
2. **Ordinances vs votes:** 3 genuine adopted ordinances not in `all_votes.csv` (2025-8, 2025-10,
   2026-6 — bundled/amended items); the other 30 "missing" are just minutes published after the
   vote-layer's cutoff (the agent split these correctly in `adopted_not_in_votes.csv`).
3. **Finance vs elections:** 3 candidates filed disclosures but withdrew before the ballot (not an
   elections defect — the county file lists only ballot-qualified candidates).
These are good candidates for a future `remediate-city-data` pass (especially the PC backlog).

## Vendor learnings (OnBase — new this run)
- **OnBase "Agenda Online"** (`agendas.provo.gov`): GET `/Meetings` for a CSRF token + cookie → POST
  search → `DownloadFileBytes/<file>.pdf?documentType=5&meetingId=<id>` with cookie + Referer.
  Packets are **bundled** whole-meeting PDFs → index-only.
- **OnBase serves `Transfer-Encoding: chunked` with NO Content-Length** — `--size-only`/HEAD/streaming
  all return null. This is the one portal where size-probing fails; characterize from packets already
  on disk and record `size_source=unknown_chunked_no_content_length`.
- **Bodies can split across portals:** Provo Council is on OnBase but Planning Commission is on a
  separate CivicPlus AgendaCenter — always confirm the live body set, don't trust recon's "shared".
- **PMN is a first-class ordinance source** (not just minutes backfill): Provo's Recorder posts
  "Notice of Ordinances Approved" `.docx` to PMN, giving an independent number→date→summary list.

## Skill revisions surfaced (queued for your review — none applied mid-run except `--size-only` earlier)
1. **Source 1 / OnBase:** document the CSRF+cookie+`DownloadFileBytes` flow; the no-Content-Length
   exception (size-probe fails → index-only w/ `size_source` column); and that bodies may split across
   OnBase + CivicPlus AgendaCenter.
2. **Source 3:** promote **PMN "Notice of Ordinances Approved"** to a first-class independent source
   *before* defaulting to `within_source`; PMN notices are often **`.docx`** (`unzip word/document.xml`,
   not pdftotext); use the **application code** (`PLRZ…/PLGPA…`) as the `medium` join key; split
   adopted-not-in-votes into coverage-boundary vs genuine; normalize ordinance # as `(year, int(seq))`.
2. **Source 4:** PMN attachment labels are **city-specific filenames**, not a fixed `(Meeting Minutes)`
   vocab — categorize by filename keyword (`minute`/`summary`/`roa`/`agenda`/`packet`); PC minutes may
   be **per-item ROA** (one row per file + `doc_kind`, classify out duplicates/exhibits); PMN can be
   *thinner* than the repo for regular meetings (value = special meetings + whole-body backlogs);
   RDA = council-as-RDA (expect duplicates).
3. **Source 5:** `--js-runtimes node` mandatory + `--sub-lang en-orig`; **bundle a shared `clean_vtt.py`
   in `scripts/`** (every YouTube city re-implements the rolling-window de-dup); enumerate BOTH
   `/videos` and `/streams`; OpenUtah robots block names ClaudeBot on `/transcripts`,`/meetings`,etc.
4. **Source 6:** CivicPlus DocumentCenter recorder page is a common pattern (View-id is the stable
   key; assign cycle by section+roster, IDs are non-monotonic); add OCR **rotation** handling
   (`tesseract --psm 0` OSD) and treat **fontless/ToUnicode-less** born-digital PDFs as scanned.

## Status
**Paused here per your instruction** — West Jordan and Provo are complete; Park City and the remaining
cities are shelved for later. The skill + `polite_fetch.py --size-only` fix are in place. The queued
revisions above (especially bundling `clean_vtt.py` and the OnBase/PMN-ordinance notes) are ready to
fold in whenever you want to resume.
