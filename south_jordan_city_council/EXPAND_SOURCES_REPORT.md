# expand-city-sources — South Jordan expansion report

**Date:** 2026-07-06 · **City:** South Jordan (Salt Lake County) · **Skill:**
`.claude/skills/expand-city-sources/`

Six additive source datasets built on top of the standard minutes/votes/comments/elections
layer. Each has its own `CLAUDE.md` + `AVAILABILITY.md` and **individually passes
`validate_dataset.py`**; **no existing dataset was modified**; parent docs (`README.md` +
`CLAUDE.md`) written once by the orchestrator. Portal family exercised here: **CivicPlus +
Municode Meetings + municipalcodeonline.com S3 + Utah PMN + YouTube + CivicPlus/Wayback** —
notably the **HTTP/2-only Municode Meetings** portal and a **publicly-listable S3 ordinance
bucket**, both new to the playbook.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Method | Key caveats |
|---|---|---|---|---|
| 1 | Packets → `packets/` (**INDEX-ONLY**) | **169 whole-meeting packets** — Council 87, PC 82 (2022–2026); 5.32 GB catalogued | Municode Meetings (`southjordan-ut.municodemeetings.com`), meeting-group filter 27 (Council) / 481 (PC). **Host is HTTP/2-only** (curl `--http2`; Python requests disconnects). Date-range GET params, paged + unioned by UID (filter is cache-flaky). | One PDF per meeting (agenda + all staff reports + exhibits), median 19.8 MB / max 195 MB → **too large to store**; each row is a live `source_url` + exact byte size + `packet_uid`. **2020–2021 predate Municode publication** (zero-result filter, not a miss). CivicPlus AgendaCenter `?packet=true` links are empty stubs (not used). |
| 2 | Housing → `housing_plans/` | **6 docs**: 2020 General Plan, 2025 MIH element (GP Appendix A), state 2023/24/25 MIH compilations, SB 34 summary | City: `sjc.utah.gov` DocumentCenter (`View/812` GP, `View/8116` MIH). State: `jobs.utah.gov` HCD generic year URLs. `pdftotext -layout`; state reports sliced to per-city page ranges. | General Plan has **no printed adoption date** (dated by PDF CreationDate 2020-01-31). MIH element and GP are **one plan** (Appendix A). State reports are one statewide PDF/year — SJ block derived via the `Who is filling out this report?` form marker (the isolated-header heuristic **over-brackets 2024**; corrected + contamination-checked). |
| 3 | Ordinances → `ordinances/` | **129 ordinances (2020+)** linked to motions; **213-doc back-catalog 1997–2026** indexed; 52 general-series PDFs stored | `southjordan.municipalcodeonline.com` **public S3 bucket** (`?list-type=2&prefix=…/ordinances/documents/`, paginated). Join = ordinance no. cited in `all_votes.csv` motion text ∩ S3 archive. | Confidence **39 high / 78 within_source / 7 low / 5 none** (`within_source` = motion-derived, `high` by construction — **not** an independent cross-match). **Two parallel series** (general `YYYY-NN` + zoning `YYYY-NN-Z`) — the S3 bucket carries **only general** (zero `-Z`). **45% land-use** (58/129). 47/52 stored PDFs are signed scans (OCR deferred); `low`/`none` adoption dates read by **vision** from handwritten signature blocks. |
| 4 | PMN backfill → `pmn_backfill/` | **13 council-minutes docs across 8 dates recovered** | Utah PMN (`utah.gov/pmn`): entity 269; bodies Council 1031 / PC 1032 / RDA 3901 / MBA 5015 / BoA 1033. Cumulative single-GET history (`page=300`), set-difference vs `minutes_index.csv` (±4-day), fetch only missing. | **All 13 are City Council**, filling the previously-unrecoverable **2020 Jan–Jul** gap plus a 2023-01-24 budget meeting. RDA/MBA 2020+ and 2 "PC-body" docs are **Combined** meetings already on disk (no standalone gap). **The 6-month PMN list view the base build used is why it missed these.** **Contradicts 2 rows of `minutes_unrecovered.csv`** — left in place; merge is the user's call. |
| 5 | Transcripts → `transcripts/` | **125 videos mapped, 10 ASR caption tracks sampled** | Official channel "City of South Jordan" via `yt-dlp --flat-playlist` + per-video `--dump-json` caption detection; 10 governance-adjacent ASR tracks pulled to VTT → cleaned text. | **HONEST GAP: SJ does not post meeting *video*** — the YouTube channel is PR/promotional; council/PC meetings live as **audio + minutes** elsewhere (OpenUtah has 60 transcribed). `caption_type` manual 19 / asr 65 / none 41; 9 removed/private in `unrecovered.csv`. **No join to votes** (these are not meetings). ASR never authoritative. **Sample-only by owner policy.** |
| 6 | Campaign finance → `campaign_finance/` | **46 filings / 14 candidates** (2019–2025; Mayor + 5 district seats) | CivicPlus `/230/Elections` finance column (2025 live; 2021/2023 id-maps via **Wayback**, PDFs still live; **2019 bytes from the Internet Archive** — live URLs 404). All via `polite_fetch.py`. | **ACQUISITION LAYER ONLY** — no dollar extraction yet. **100% of filers join `election_results`** (normalize UPPER-CASE names). 42 scanned / 4 text. **Double-count trap:** candidates file several reports/cycle (cumulative-vs-incremental unknown) — **do NOT sum** until the structured step; **3 superseded 2023 uploads** (5135/5148/5149) are re-uploads, never extra filings. |

**Core layer untouched:** council 1,029 motions / 1,448 vote rows, PC 730 motions, 243
council + 125 PC minutes, `db/south_jordan.db`, election results — all unchanged.

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)

1. **2020 minutes recovery (PMN) contradicts the audited minutes layer.** `pmn_backfill/`
   recovered **13 council-minutes docs (8 dates)** for the **2020 Jan–Jul** span that the base
   build had logged **unrecoverable** in `meeting_minutes/minutes_unrecovered.csv`. These
   recoveries **contradict 2 rows** of that file. They are kept in the separate `pmn_backfill/`
   layer by design; **a deliberate merge into the audited minutes layer** (move the true
   minutes onto disk, drop the 2 now-superseded `minutes_unrecovered.csv` rows, re-extract
   votes, rebuild db + weeks) is the single highest-value follow-up. See
   `pmn_backfill/coverage.md` §Reconciliation.
2. **Campaign-finance ↔ elections 100% corroboration.** Every one of the 14 candidates across
   the 46 filings **joins to `election_results/south_jordan_races.csv`** on candidate + year +
   district — a clean two-way corroboration of the elected roster (unlike Sandy, which surfaced
   an unmatched primary candidate). No election-record gap detected from the CF side.
3. **Ordinance two-series split is a structural, not a coverage, fact.** SJ runs **general
   `YYYY-NN` and zoning `YYYY-NN-Z` as independent series**, and the code host's S3 bucket
   publishes **only the general series** — so the 35 `-Z` rezones are `within_source` (motion-
   derived) with **no independently archived PDF to corroborate**. This is a publication limit
   of the source, not an extraction miss; a `-Z` PDF backfill (if the city ever exposes signed
   rezone ordinances) would upgrade those rows to `high`.
4. **Transcripts audio-only gap.** SJ publishes meeting **audio + minutes**, never meeting
   *video*, so there is no native deliberation-transcript corpus. The honest deliverable is a
   YouTube map + 10-track ASR sample; a real transcript layer requires **Whisper over the city
   audio** (or reusing **OpenUtah's 60 transcribed meetings**) — logged as the future route.

## TODO follow-ups worth queuing

- **[high] Merge the 2020 PMN minutes recovery into the audited minutes layer** — reconcile
  the 13 `pmn_backfill/` docs against `meeting_minutes/`, drop the 2 superseded
  `minutes_unrecovered.csv` rows, re-run `extract_votes.py` + validators, rebuild db + weeks.
- **[med] Structure the campaign-finance layer** — run `/cf-vision-transcribe` on the 42
  scanned filings, build `contributions.csv` / `expenditures.csv` / `filing_totals.csv` /
  `cycle_totals.csv` via a `build_finance.py`, classify incremental-vs-cumulative, reconcile
  (mind the 3 superseded 2023 uploads).
- **[med] Real meeting transcripts via OpenUtah/Whisper** — evaluate OpenUtah's 60 transcribed
  SJ meetings and/or Whisper over the city's published meeting **audio**; if adopted, join to
  minutes/votes on the Tuesday weekly grid.
- **[low] Ordinance body OCR + `-Z` backfill** — OCR the 47 signed-scan general-series PDFs;
  watch for a signed-rezone (`-Z`) source to upgrade the 35 `within_source` zoning rows.
- **[low] Refresh cadence** — packets: re-enumerate both Municode meeting groups for new dates
  (HTTP/2); ordinances: re-list the S3 prefix; PMN: re-crawl `page=300` for the four bodies.

## Note on the source index
Per the orchestrator's scope, this run did **not** rebuild `sources.csv` /
`sources_summary.md` — the sources-index tooling is owned by a separate agent and should be
re-run to fold in all six new datasets.
