# campaign_finance/ — Murray City municipal campaign-finance disclosures

**ACQUISITION-ONLY layer** (built 2026-07-13 by the expand-city-sources skill, source
type 6): every campaign-finance statement Murray City publishes for its municipal
candidates, as raw originals + a §9-contract index. **No dollar amounts are extracted
yet** — the structured contributions/expenditures pass (cf-vision-transcribe →
`build_finance.py`) is a later step. 92 of 131 filings are scanned.

```
raw/                131 originals (129 PDF + 1 xlsx + 1 docx), never modified
raw/_fetch_log.jsonl  bytes-level provenance (url, status, sha256, final_url) per attempt
index.csv           one row per filing — SCHEMA_SPEC §9 campaign_finance contract header
AVAILABILITY.md     what exists / what doesn't / discrepancy FLAGS (read before quoting)
```

## Coverage — 131 filings, 5 cycles

| Cycle | Filings | Candidates | Source |
|---|---|---|---|
| 2017 | 16 | 7 (Mayor + D2 + D4) | Wayback-recovered index (retired /1460 page), bytes live from city |
| 2019 | 21 | 7 (D1 + D3 + D5) | city /1903 page (below the repo's 2020 floor; kept — trivially available) |
| 2021 | 21 | 8 (Mayor + D2 + D4) | city /1903 page |
| 2023 | 34 | 11 (D1 + D3 + D5) | city /1903 page |
| 2025 | 39 | 13 (Mayor + D2 + D3-special + D4) | city /1903 page |

Authoritative source: `https://www.murray.utah.gov/1903/Campaign-Finance-Statements`.
The state (`disclosures.utah.gov`) and county pages carry nothing for Murray (verified
2026-07-13 — see AVAILABILITY.md).

## index.csv — the §9 contract + extras

Contract columns first (`date, candidate, office, election_year, filing_type,
reporting_period, title, source_url, retrieved_date, format, extraction_method, path`),
then city extras: `district, source` (`city_cf_page` | `wayback_recovered_index`),
`in_election_results` (`yes`/`no`/`below_floor`), `matched_election_candidate` (the
UPPER-CASE name in `../election_results/murray_results_by_candidate.csv`),
`join_confidence`, `date_precision` (`page_stated` | `archived_page_stated`), `docid`
(CivicPlus DocumentCenter id), `note` (amendments, mislabel flags, recovery provenance).

- `date` is the **city-stated upload date** (the page's own label), not a statutory
  deadline; 2017 dates come from an archived capture of the same page.
- `filing_type`: `interim` = pre-primary/pre-general periodic statements; `summary` =
  finals (year-end, post-primary-eliminated, or withdrawal finals). One row (Jim Brass
  2023 withdrawal *affidavit*) has a blank filing_type — it is not a finance statement.
- `format`: `text` = born-digital (39), `scanned` = image-only (92, incl. the one
  image-based docx). The one xlsx (Holbrook 2025) is `text`.

## THE DOUBLE-COUNT TRAP (do not sum filings)

Candidates file **several statements per cycle** (pre-primary, pre-general 28-day +
7-day, year-end final) and **amended statements restate the originals** (Hales 2025
pre-primary, Bullen 2021 pre-general, Pickett/Hock 2023 pre-general, Dominguez 2019 ×2).
Any per-candidate cycle total must use the repo's dedup rules
(`scripts/campaign_finance/cycle_totals.py`) once amounts are transcribed — never sum
rows of this index or the future filing_totals blindly.

## Flags worth knowing before analysis (details in AVAILABILITY.md)

- **The 2021 filings prove a 2021 MAYOR primary — and, it turns out, a D4 primary that was
  scheduled but never conducted. Flag CLOSED 2026-08-01.** The Mayor race is now in
  `../election_results/murray_races.csv`, certified against Murray's Board of Canvassers'
  Report (city docid 12340, retained at `../election_results/raw/`), which covers the
  mayoralty **alone** — so there is **no D4 primary result to carry**. This layer's
  Pre-Primary filings were the decisive evidence: Rasmussen + Turner filed on **2021-08-03**
  (Murray posts "Disclosure not required" for that slot when a race has no primary — 2021 D2,
  2023 D5, 2025 D4 are all empty), so D4 was still a primary race a week out and collapsed
  after that deadline; Galt filed nothing, not even a post-primary "eliminated" final.
  See `AVAILABILITY.md` §DISCREPANCY FLAGS and `../election_results/CLAUDE.md` §2026-08-01.
- 7 `in_election_results=no` rows are all explained: Fitzgerald/Teemsma (2021 Mayor primary —
  eliminated there, so absent from the general-only by-candidate file), Lambrinos 2025 +
  Brass 2023 (withdrew pre-ballot).
- Dominguez 2019 filings are the city's 2023 **redacted re-uploads** (originals
  withdrawn); two are mislabeled on the page — see `note` column.
- Holbrook 2025: the "Aug 5" xlsx and the Sept 11 PDF appear to be one September
  statement in two forms.
- No filings exist for Joe Christensen (2025, withdrew) or Skylar L. Galt (2021 D4) —
  honest empties. Galt's total silence is itself evidence: he filed neither a Pre-Primary
  (which both his D4 rivals did) nor a "Post-Primary final (eliminated in primary)" (which
  both losing 2021 mayoral candidates did), consistent with a candidacy that ended before
  election day. He appears on no ballot in `../election_results/` — correctly so.

## Rebuild / extend

Index built by a session script from the parsed /1903 page + Wayback captures; the raw
bytes and `_fetch_log.jsonl` are the ground truth. To refresh after a future election:
re-parse /1903 (or its successor), fetch new `DocumentCenter/View/<id>` docs via
`scripts/polite_fetch.py` with `YYYYMM_<Candidate>_<docid>` names, append contract rows.
Validate with
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py <this dir>`.

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed the **2025-cycle scanned C&E filings** via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API** — Claude Code allotment). **26 of 27** scanned 2025 filings
cached in `vision/*.json` (223 contributions + 175 expenditures itemized). **NOT done:** John
Jeffrey Evans summary `raw/202509_John-Jeffrey-Evans_17148.docx` — image-based .docx, not
renderable by `pdftoppm`; needs docx→image conversion (remaining, later tranche).

- **Cache contract (provisional-standard, no build yet):** filenames use the repo-standard
  West Jordan `_did8` convention — `sha1(index_path)[:8].json` (trailing-8-hex-of-filename
  shortcut where present); body is the WJ vision schema (`contributions[]`/`expenditures[]` +
  verbatim cover totals `total_contributions`/`total_expenditures`/`contributions_50_or_less`/
  `beginning_balance`/`ending_balance`; `reports[]` for bundled multi-period PDFs — 1 filing).
  Each cache carries a `_meta` block (index_path, candidate, office, filing_type,
  election_year, source_pdf, pages) so a future build can re-key losslessly.
- **STRUCTURING PENDING:** Murray has **no `build_finance.py`** — these caches are additive raw
  transcriptions; the per-city structuring build (contributions/expenditures/filing_totals CSVs
  + `cycle_totals`) is **owner-gated later-tranche work**, not scaffolded here. No CSVs
  regenerated; nothing federated (cf_* refresh at the orchestrator boundary).
- **Murray form quirks captured verbatim:** not-itemized threshold is **$500** (not $50 — left
  `contributions_50_or_less` null unless the $50 line was printed); separate **in-kind
  Schedule C** recorded as `in_kind:true` contributions. Preserved source defects (invalid date
  "06/61/2025", donor typo "Sat Lake Board of Reatlors", scribbled/illegible ending balances →
  null on a couple of filings). Parker-Reed itemized ~933.61 vs printed 933.71 — printed
  retained (no reconciliation).
- Backup: `_backups/2026-07-17-cf-vision-t1/murray/` (greenfield — nothing pre-existed to back up).

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 2, 2023 + 2021 cycles + Evans .docx) — vision/ caches written

Transcribed the remaining scanned filings via `/cf-vision-transcribe` (Read-tool vision,
**$0 Anthropic API**), fanned out over chunked `general-purpose` agents (≤~15 page-images each).
**37 new caches**, taking the scanned in-scope layer to complete:

- **2023 cycle — 16 caches** (all scanned 2023 filings EXCEPT `raw/202308_Jim-Brass_14399.pdf`,
  which is a **Candidacy Withdrawal Affidavit, not a C&E statement** — correctly not transcribed).
  Candidates: Rodgers ×4, Pickett ×5, Strobell, Brass (14400 final), Parker-Reed ×2, Dominguez
  (the 2019-origin redacted re-upload — 101 contribs / 69 expends), Goodman ×2.
- **2021 cycle — 20 caches** (every scanned 2021 filing): Silverzweig ×2, Cotter ×2, Rasmussen ×3,
  Turner ×3, Fitzgerald ×2, Teemsma ×2, Hales ×3, Bullen ×3. Proves the 2021 Mayor + D4 primary
  (Fitzgerald/Teemsma pre- then post-primary "eliminated" finals; Bullen amended pre-general).
- **2025 John Jeffrey Evans `.docx` (hash `577872d2`)** — the tranche-1 hold-out (image-based
  `.docx`, un-renderable by `pdftoppm`). LibreOffice is unavailable here, so the 4 embedded PNGs
  were extracted from the docx zip (`word/media/image1-4.png`) and Read directly. Post-primary
  final: contribs 500.00 + 20.00 + Personal Loans 508.15 = printed 1,028.15; expends 5 lines =
  printed 1,377.42; begin 349.27, end 0.00. **Its index.csv row was updated** honestly
  (`extraction_method=claude_vision (docx-embedded images)` + a `note`) — the ONE index row this
  tranche touched.

- **Cache count now: 63** `vision/*.json` (2025 ×27, 2023 ×16, 2021 ×20). Same WJ `_did8` =
  `sha1(index_path)[:8].json` convention + WJ vision schema (`contributions[]`/`expenditures[]`
  + verbatim cover totals + `_meta`). Expenditure rows use `recipient`/`purpose`.
- **Index `extraction_method` unchanged for the 2021/2023/2025 raw rows** (still
  "none (raw acquisition…)") — matching the tranche-1 convention (caches are additive; no
  `build_finance.py` consumes them yet; structuring stays owner-gated). Evans is the deliberate
  exception (its format story — docx→images — changed). No CSVs regenerated; nothing federated.
- **Verbatim source defects preserved** (anti-fabrication): candidate arithmetic that doesn't foot
  to printed cover totals (printed totals retained, never reconciled), donor typos, dates with no
  year, struck/illegible entries → null/omitted. Per-filing reconcile notes live in each cache's
  `_meta` where an agent flagged one.
- **Honest remaining gaps (out of THIS scope):** the **2017 (16) + 2019 (12) below-floor scanned
  filings** are NOT transcribed (future candidates). Backup: `_backups/2026-07-17-wave2/murray/`.

## 2026-07-18 — STRUCTURED LAYER BUILT (vision-cache wave; born-digital text captured)
`build_finance.py` (family **`vision_cache`**, shared `scripts/campaign_finance/vision_lib.py`)
+ the city helper **`murray_text.py`** now write the four derived CSVs — `contributions.csv`
(1,446) / `expenditures.csv` (1,046) / `filing_totals.csv` (**130** rows = the full in-scope
inventory) / `cycle_totals.csv` (46 candidate-cycles) — all regenerable, never hand-edited.
`validate_finance.py` PASS (0 FAIL, 1 WARN = the excluded Jim Brass affidavit);
`scripts/validate_city.py murray_city_council/` 26 PASS / 0 FAIL.

- **TWO transcription paths, consumed uniformly:** (1) **scanned** filings → the 63 `vision/`
  caches (`build_result`, extract_method `vision_cache/vision`, OCR→medium conf); (2)
  **born-digital `format=text`** filings → **30 new `text_cache/` caches** in the SAME WJ schema,
  consumed by `murray_text.build_text_result` (extract_method `vision_cache/**text**`,
  born-digital→high conf). **UNLIKE midvale, Murray's text layer carries REAL money** — e.g.
  Ben Peck 2025 Pre-Primary **$5,700.00 contributions / $4,002.81 expenditures** (both reconcile,
  high) — so the born-digital filings were transcribed from the authoritative pdftotext/openpyxl
  text layer (fan-out subagents), NOT left out. 93 filings transcribed; **74 both-sides
  reconcile**; the rest carry verbatim filer/transcription mismatches (flagged `needs_review`,
  never adjusted — e.g. Clark Bullen 2021 Mayor $100 page-subtotal error, Dominguez 14940 $0.02
  ActBlue rounding).
- **`reconcile_cash_only=True`** — the form's "Total Contributions Received (Schedule A)" cover
  EXCLUDES Schedule C in-kind (a separate schedule/total); 105 in-kind rows carry `in_kind=True`
  and are excluded from the cash reconciliation (verified on Bullen/Hrechkosy in-kind filings).
- **SINGLE regime — no annual/election split.** Every Murray filing is an ELECTION-CYCLE C&E
  report (interim / summary; report types Pre-Primary / Pre-General 28-&-7-day / Year-end /
  Post-Primary). Murray publishes NO mandatory annual financial statement in this dataset (its
  Utah-Code conflict-of-interest statements live on the separate `/2123` page, out of scope), so
  `filing_regime=""` for all rows.
- **PER-PERIOD form ⇒ 23 `cycle_overrides.csv` rows.** Murray's form Covers a DISJOINT date range
  per report, so a candidate's "Year-end final" / "Post-Primary final" is itself a **period
  report**, not a cumulative summary. `cycle_totals.py`'s summary-vs-interims `max()` therefore
  DROPS the final period and undercounts. For the 23 multi-filing per-period filers whose final
  period is non-zero, the documented override sets cycle = **sum of all live period covers**
  (reason cites the per-filing breakdown). 4 per-period filers whose final period was ~$0
  (Aaron Thompson 2023, Daren Rasmussen 2021, Diane Turner 2025, Pamela J. Cotter 2021) need no
  override. **3 candidates are genuinely CUMULATIVE** and correctly latest-wins with NO override:
  Janice Strobell 2023 + Scott Goodman 2023 (their post-primary "final" RESTATES the pre-primary
  verbatim — identical totals + donor lists) and Aaron Lee Holbrook 2025 (the xlsx + signed PDF
  are duplicates of one September statement). **Always read `cycle_totals.csv`; never sum
  `filing_totals` naively.**
- **Jim Brass 2023 docid 14399** (Candidacy Withdrawal Affidavit) is excluded by `in_scope_fn`
  (NOT a C&E statement; his Final 14400 IS in scope). **Rosalba Dominguez 2023 (14463)** was
  confirmed a genuine **2023** filing (form header "2023 Murray City Elections", D3, received
  8.29.2023; transaction dates Apr–Aug 2023) despite the tranche-2 cache `_meta` calling it a
  "2019 re-upload" — the landmine is a false alarm; the ~$9.7k belongs to the 2023 D3 race.
- **Below-floor:** the 16 (2017) + 21 (2019) filings stay as honest **inventory-only** rows
  (empty, low conf, dated reason) — acquired ≠ transcribed (midvale convention). Backups (docs
  I appended to): `_backups/2026-07-17-cf-structuring/murray/`; derived CSVs + `text_cache/` are
  greenfield.
