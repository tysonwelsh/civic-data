# expand-city-sources — West Jordan expansion report

**Date:** 2026-07-03 · **City:** West Jordan (Salt Lake County) · **Skill:** `.claude/skills/expand-city-sources/`
**Third city** (after Lehi/Granicus and St. George/Revize). Purpose: exercise the **PrimeGov JSON-API**
portal family. All six datasets built; every one passes `validate_dataset.py`; no existing dataset
modified; parent docs written once by the orchestrator (fan-out doc-ownership fix — worked, zero agent
collisions). Concurrency pre-flight clean (repo quiet; last remediation write ~6 h prior).

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**LINK INDEX**) | **222 packets indexed** (Council 122, PC 70, RDA 21, MBA 9; 2022–2026), 7.36 GB catalogued, 0 stored | PrimeGov API confirms **bundled one-PDF-per-meeting** (like Revize) → index-only. 2023/24 = 100% vote-date coverage. Gap: mid-2025 switch to non-downloadable HTML Interactive Agenda |
| 2 | Housing → `housing_plans/` | **11 PDFs (~75 MB)**: 2023 GP + FLUM + adoption ord, MIH element (2020+2026), 2020 annual report, state 23/24/25 + SB 34 | City GP nav link is a 403 amlegal host; real PDF on `wp-content`; MIH on a Wix asset host |
| 3 | Ordinances → `ordinances/` | **285 rows; 61 signed zoning PDFs**; 58 `high` / 224 `within_source` / 3 `none` | Municode SPA (current-only) + PrimeGov exposes no ordinance type → recorder "Adopted Ordinances" page. **3 adopted ords not in `all_votes.csv`** flagged |
| 4 | PMN backfill → `pmn_backfill/` | **33 recovered** (5 council + **28-meeting 2021–22 PC run**) | Bodies 395/396. Contradicts the "no standalone PC 2020–21" doc claim; 0 still-missing |
| 5 | Transcripts → `transcripts/` | **10 ASR** + 647-video map | **YouTube ends 2025-02-04** → Swagit/OpenUtah after; `en-orig`; two tabs (/streams+/videos) |
| 6 | Campaign finance → `campaign_finance/` | **135 filings (~208 MB)** | New vendor: **EasyVote portal** (2023+) + city WP (2021+annual/COI); 2019 GRAMA-only; joins to elections |

**Existing layer untouched:** `all_votes.csv` 6,706 rows, 321 council + 84 PC minutes, db unchanged.
**New footprint on disk:** ~390 MB (packets index-only; campaign-finance OCR packets are the bulk).

## Timing
Six agents in parallel; end-to-end ≈ slowest (~25 min) + verification/docs. Per-source: PMN ~12,
housing ~12, ordinances ~14, packets ~10, transcripts ~20, campaign finance ~20 min.

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **PMN vs docs:** the parent CLAUDE.md said 2020–21 had no standalone PC meetings; PMN shows a full
   16-meeting 2021 + 12-meeting early-2022 PC run. The audited PC layer is missing them.
2. **Ordinances vs votes:** 3 recorder-signed adopted ordinances (22-08, 23-08, 24-18) have no motion
   in `all_votes.csv` — a likely minutes/vote-extraction gap.
3. **Finance vs elections:** 7 primary-only candidates appear in filings but not `election_results`
   (which documents generals only) — consistent, but worth noting for completeness.
These are good candidates for a future `remediate-city-data` pass on West Jordan's core layer.

## Vendor learnings (PrimeGov — new this run)
- **PrimeGov packets are bundled** one-PDF-per-meeting (not per-item), so they take the **index-only**
  branch like Revize — an API portal does NOT imply separable documents.
- Doc model: `ListArchivedMeetings?year=YYYY` → per-meeting `documentList`; packet = `templateName ∈
  {Complete Packet, Meeting Materials, Packet}` → `/Public/CompiledDocument?meetingTemplateId=<id>` →
  302 → Azure blob (SAS ~2 days, re-minted per call).
- **Format drift:** cities migrate from compiled-packet PDFs to in-portal HTML Interactive Agendas
  (SPA) with no fetchable packet URL — record as a documented gap.
- **EasyVote** (`*.easyvotecampaignfinance.com`) is a common Utah campaign-finance vendor; public
  download endpoint is `/documents/{id}/viewfinalredactedpdf`; city and county run separate instances.

## Skill revisions surfaced (for later — applied ones noted)
1. **[applying now] `polite_fetch.py --size-only`** — `--probe` does a full-body GET, so sizing
   hundreds of large bundled PDFs pulls GBs. Expose the existing HEAD `content_length()` as a flag.
2. **Add PrimeGov API doc-model + "bundled ⇒ index-only" to Source 1**; add the HTML-Interactive-Agenda
   format-drift gap type.
3. **Add EasyVote as a first-class Source 6 vendor** (recipe above); warn to assign cycle/office by
   document year, not the portal's current-seat field.
4. **Transcripts:** `--js-runtimes node` is now mandatory for YouTube; bundle a shared `clean_vtt.py`
   in the skill's `scripts/` (every city re-implements the rolling-window de-dup); record the
   "meetings moved off YouTube to Swagit/OpenUtah at a hard date" pattern; enumerate BOTH /streams
   and /videos tabs.
5. **Source 3:** Municode is a current-text-only SPA (like Sterling/American Legal); the real
   per-ordinance source is the recorder page + `wp-content/uploads/.../Ordinance-No.-*-signed.pdf`
   (WP media REST API usually locked → find by keyword search). Add "signed-PDF-not-in-votes" as a
   standard audit output.
6. **OCR sandbox gotcha:** `tesseract` can't read temp images written to `/tmp` (per-process
   namespace) — use the session scratchpad dir.

## Recommendation
West Jordan is the cleanest expansion yet (PrimeGov API made packets + coverage trivial). Next up in
this autonomous run: **Provo**, then **Park City**. I'll apply revision #1 now; the rest are queued
for your review.
