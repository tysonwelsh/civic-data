# expand-city-sources — Nephi expansion report

**Date:** 2026-07-05 · **City:** Nephi (Juab County) · **Skill:** `.claude/skills/expand-city-sources/`
**Ninth city** (after Lehi, St. George, West Jordan, Provo, Sandy, Orem, Logan, Vineyard). Purpose:
a **small rural CivicPlus `/AgendaCenter` city** (~6,500 pop.) — the smallest yet. All six datasets
built; every one passes `validate_dataset.py`; no existing dataset modified; parent docs written once
by the orchestrator. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**STORED**) | **328 agendas** (Council 254, PC 72, **CRA 2**), 12 MB — all stored locally | CivicPlus AgendaCenter exposes only **Agenda/Minutes** doc types (no separate packet) → "packet" = the agenda doc. Tiny total (10.8 MB) → stored, not index-only. 3 `.docx` + 4 scanned detected by magic bytes. **A CRA body exists** (recon said none) |
| 2 | Housing → `housing_plans/` | **6 docs (~31 MB)** | MIH = **General Plan Element 6 (chapter)**, not standalone. **Nephi is EXEMPT** from §10-9a-408 annual reporting (under the >10k / >5k-in-40k-county threshold) → genuinely absent from all state compilations (verified negative; retained as evidence-of-absence) |
| 3 | Ordinances → `ordinances/` | **103 numbers** (99 adopted, **71 land-use**) | **Date-as-number city** (`Ordinance MM-DD-YYYY`) → the number carries no independent signal → **within_source 87 / high 5 (PMN-corroborated) / none 11**. 4 land-use adoptions missing from votes (tally-only/consent-folded). Caught + excluded a mis-posted North Salt Lake model ordinance |
| 4 | PMN backfill → `pmn_backfill/` | **9 recovered** (8 Council + 1 PC; 2.3 MB) | Entity 216; Council 1788 / PC 1869 (CRA 5737, LBA 6527). Fills real late-2025/early-2026 holes (council 2025-10-14 → 11-18 gap). **No purge here** — all files live (the "PMN purges old blobs" pattern is era/city-specific) |
| 5 | Transcripts → `transcripts/` | **4 ASR captions / 13-video map** (~4 MB) | A **brand-new @NephiCity YouTube channel began streaming May 2026** (~6 weeks pre-build) — so a small *populated* set, not the expected empty. Everything pre-2026 has no video. Caught + ignored ~130 stray non-Nephi VTTs left in the shared scratchpad by another task |
| 6 | Campaign finance → `campaign_finance/` | **27 filings / 43 index rows** (~19 MB; all 4 cycles) | Handwritten scans, self-hosted on the city **DocumentCenter**. **92% election join.** Flags a likely **Aug-2023 primary** the election dataset omits (7+ filers for a vote-for-3 seat). Worwood name ambiguity resolved (Skip vs Travis L.), not merged |

**Existing layer untouched:** `all_votes.csv` (5 at-large council; Mayor tie-breaker; **mostly tally-only** — ~58 motions name voters), 243 council + 70 PC minutes, `db/civic.db` unchanged.
**New footprint on disk:** ~75 MB raw (all stored — the city is small enough that even packets fit locally).

## Timing
Six agents in parallel; end-to-end ≈ slowest (ordinances ~32 min — motion-linkage disambiguation). The
packets agent finished cleanly with **no stall** (inline size-probe, no background monitor — the fix held).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **A CRA (Community Reinvestment Agency) body exists** (2 agenda docs; PMN body 5737) — the core repo has
   no CRA layer. Minor, but recon's "no RDA/CRA" was wrong.
2. **Likely Aug-2023 municipal primary missing from `election_results`** (campaign-finance filer count implies it).
3. **4 adopted land-use ordinances missing from `all_votes.csv`** (05-18-2021, 05-20-2025, 06-20-2023,
   07-12-2022) — consent-folded / narrated without a discrete roll-call; vote-extraction leads.

## Skill changes worth folding in
- **CivicPlus AgendaCenter:** only Agenda/Minutes doc types (no packet type — "packet" = the agenda);
  `<id>` suffix is a non-derivable serial (harvest from the per-year Search listing); cities upload `.docx`
  and scans into the Agenda slot (detect true type by magic bytes).
- **Date-as-number ordinance cities** need an explicit confidence branch — the number equals the meeting
  date, so it's `within_source` (not independent) unless a PMN/recorder PDF corroborates.
- **Small-city MIH exemption test** (>10k pop, or >5k in a ≥40k county) predicts absence from state
  compilations — treat the download as a negative-check artifact.
- **Shared scratchpad is cross-task** — write only newly-downloaded, provenance-verified files; never trust
  pre-existing scratchpad artifacts (another task's Nephi-looking VTTs nearly contaminated this run).
- **Wayback CDX as a *discovery* index** for de-linked-but-live DocumentCenter View ids (cheaper + truncation-free than fetching the archived capture).

## Source index
`nephi_city_council/sources.csv` regenerated: **818 documents indexed, 99% with recorded URLs** (up from
324). Repo-root `sources_summary.md` refreshed.
