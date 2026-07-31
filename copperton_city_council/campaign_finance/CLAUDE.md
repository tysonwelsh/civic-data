# campaign_finance — Copperton candidate campaign-finance & COI disclosures

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained verbatim
under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs every retrieved
artifact against the SCHEMA_SPEC.md §9 contract. **No OCR/vision extraction and no dollar totals are
computed here** — `extraction_method` is `none (raw acquisition; text/OCR/vision deferred)` on every
row (year-attribution OCR of form title lines is metadata, not the deferred dollar pass). Read
`AVAILABILITY.md` for the full coverage/threshold/discrepancy record and `unrecovered.csv` for the
two blocked/absent cycles (2023, 2025 CF).

## Scope & the jurisdiction split (this is the whole story)

Copperton (~800 pop., Salt Lake County) is a **metro township (2017–2024) → TOWN (2024-05-01, HB35;
first town election 2025-11-04)**, elections administered by the **Salt Lake County Clerk**. Filing
jurisdiction — and retrievability — split by era:

- **Township campaign-finance filings 2016–2021** were filed with the **county** and posted on the
  SLCo Clerk's **static** metro-township-councils page → **19 PDFs** (`source=slco_clerk_static`).
- **2023 (still a township)** moved to the county's **EasyVote** SPA (2022+), which is
  **HTTP-500/auth-gated** → **not retrievable** under polite GET (honest gap; `unrecovered.csv`).
- **2025 (now a town)** files with the **town recorder**; `copperton.utah.gov` IS reachable
  (`curl -k` — TLS cert-mismatch host) but posts **only Conflict-of-Interest forms**, no
  campaign-finance report — both 2025 candidates ran **unopposed** (threshold-exempt).

Per the metro-township cluster lesson (White City / Kearns / Magna): these entities are **absent
from `disclosures.utah.gov/Municipal`** (and the host was HTTP-500 at check time). Do NOT expect
Copperton there.

## What's in `raw/` (25 indexed PDFs + context files)

- **19 township campaign-finance `*.pdf`** — SLCo Clerk candidate disclosures, all **scanned**:
  2016 (5, founding) / 2017 (3, @LRG) / 2019 (5, A/B/C) / 2021 (6, D/E).
- **6 town Conflict-of-Interest `*coi*.pdf`** (`filing_type=coi_disclosure`): the 2025 candidate COI
  packet (`2025_coi_election-candidates_packet.pdf`, born-digital) + five 2026 annual sitting-official
  COIs (Clayton/Stitzer/Bailey/McCalmon/Pratt; born-digital except Bailey's scan).
- **Context (NOT indexed):** `_context_2025_certified_candidate_list.pdf` (town clerk's certified
  2025 candidate list — used to verify the roster + surface flag #3), and the harvested source-page
  HTML (`_slco_metro_township_archive.html`, `_copperton_election_info.html`,
  `_copperton_disclosures.html`). The 2025 Official-Notice + UOCAVA election-admin PDFs were seen on
  the page but not fetched (out of finance scope).
- **`_fetch_log.jsonl`** — every fetch (url, status, bytes, sha256, retrieved_utc); the build script
  reads each row's `source_url` from here (never hard-coded).

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method`
then Copperton extras (mirrors the Kearns/Magna CF schema):
`path,source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- **`filing_type`** ∈ `interim` (13, Oct/Nov period reports) · `summary` (6, Dec year-end totals) ·
  `coi_disclosure` (6 — the town COI forms).
- **`office`** = cycle-level for the county filings (`Metro Township Council (founding, at-large)` /
  `… At-Large (2017 @LRG / D-E cycle)` / `… At-Large (2019 A/B/C cycle)` / `… At-Large Seat D|E`).
  Seat letters on the scanned county forms are a **handwritten "Council # __ at large"** field, not
  reliably OCR-legible — so seats are asserted only where the election layer confirms them (2021
  D/E) and are `inferred` in `notes` for 2019 (A/B/C).
- **`format`** = `scanned` (20) / `text` (5). `extraction_method` is uniform
  `none (raw acquisition; text/OCR/vision deferred)` regardless.
- **`date` / `date_precision`** — `county_folder_ym` (2016, year+month from the
  `/2016_disclosures/november/` path) · `county_month_label_year_ocr` (2017/2019/2021 root files —
  the page shows only a month; the **year was OCR-read from each form's "&lt;YYYY&gt; Financial
  Disclosure Report" title line**, which surfaced the 2019 cohort) · `city_page_label` (town COI).
- **`is_incremental`** = BLANK (deferred) — the Dec `summary` is expected cumulative; do NOT sum a
  candidate's filings before the extraction pass. Any dollar total → `cycle_totals.py`, never a row sum.
- **`matched_election_candidate`** = UPPER-CASE `copperton_races.csv` name where the person is a
  certified winner/runner-up; **`join_confidence`**: `high` (2017 @LRG + 2021 D/E — real election
  rows) · `medium` (2016 founding cohort + the 2019 A/B/C cohort — real people of record but no
  matching election row exists in the layer). BLANK on the 2025 packet (multi-candidate) and the
  McCalmon/Pratt annual COIs (not in the election layer). **No `low` rows** — every county filing
  maps to a candidate of record.
- **`sha256`** recomputed from disk by the build script.

## The three discrepancy FLAGS (see AVAILABILITY.md — recorded, never edited into election_results/roster)

1. **Founding year label:** finance dates the founding cycle **2016** (folder path + OCR'd form
   titles); `election_results` labels it **2017** (@LRG contest). Founding metro-township elections
   were Nov 2016 (terms Jan 2017). The 2016 finance cohort (Patrick/Stitzer/Bailey/Baxter/Clayton)
   is broader than the single @LRG contest the SOVC preserved.
2. **2019 A/B/C cycle:** Bailey/Stitzer/Clayton each filed **2019** disclosures — a cycle **ABSENT
   from the election layer** (the documented 2019 SLCo drop). Finance **confirms** the 2019 contest;
   seat letters are inferred from their certified 2023 seats (`join_confidence=medium`).
3. **2025 Pratt appointed, not elected:** the certified list shows only Clayton (Mayor) + McCalmon
   (Seat D), both unopposed, with **Seat C "No Candidate Declarations."** Jonathan Pratt (on the 2026
   council) was therefore **appointed**, not elected — a roster nuance the COI record surfaces.

## COI rows — retained per the SKILL's COI→coi_disclosure note

The 6 `coi_disclosure` rows are **conflict-of-interest statements** (Utah Code 10-3-1301, posted
under HB80-2024), **not** contribution/expenditure reports — they carry no dollar figures. They are
retained because the town publishes essentially no campaign-finance dollar reports for the town era
(unopposed candidates), so these are the substantive town-era candidate/official disclosure record.
Do NOT treat a COI row as a campaign-finance total. The 2025 packet is multi-candidate (Clayton +
McCalmon).

## Counts (as-of 2026-07-14)

**25 rows** — by election_year: **2016** 5 · **2017** 3 · **2019** 5 · **2021** 6 · **2025** 1 (COI
packet) · **(annual 2026 COI)** 5. By source: **slco_clerk_static** 19 · **copperton_town_site** 6.
By filing_type: **interim** 13 · **summary** 6 · **coi_disclosure** 6. Format: **scanned** 20 ·
**text** 5. **2023** (Seat A/B/C) and **2025 campaign finance** (Mayor + Seat D) are the honest gaps
(`unrecovered.csv`).

## vision/ — Read-tool transcription caches (2026-07-17 wave2; structured build still owner-gated)

The 19 **scanned** township campaign-finance filings (2016/2017/2019/2021) were transcribed via
`/cf-vision-transcribe` (Read-tool method, **$0 API — Claude Code allotment**) into
`vision/<sha1(index-path)[:8]>.json` — the tranche-1 midvale cache-key + schema convention
(`contributions[]` `{date,name,amount,in_kind}`, `expenditures[]` `{date,recipient,purpose,amount,in_kind}`,
printed cover `total_contributions`/`total_expenditures`/`contributions_50_or_less`/`beginning_balance`/
`ending_balance` verbatim-or-null, plus `_meta`). One cache per scanned CF filing; the 6 COI rows and
the 5 born-digital `text` filings are NOT vision targets (COIs carry no dollars). **19/19 written, all
pages legible.** Transcription is verbatim — printed totals copied never computed, illegible digits →
`null`, nothing inferred (see per-filing notes: Baxter-2016 struck-through ending balance = null;
Severson-2021 Dec blank this-period totals = null; Column-B YTD figures deliberately not captured).

Findings: this is a tiny ~800-pop town — **most filings are filing-fee-only ($50)** or $0-activity
summary pages. The only substantive itemizations are **Ron Patrick 2016** (4 contrib / 2 expend,
$381.97 incl. a Vista Print sign order) and **Kathleen Bailey 2019 Oct** (1 contrib / 7 expend,
$428.40). The caches are verbatim (printed totals copied never computed, illegible digits → `null`,
nothing inferred). Do NOT sum a candidate's filings — use `cycle_totals.csv` (built below).
`index.csv` `extraction_method` stays `none (…deferred)` (the index is the acquisition catalog; the
structured dollar layer lives in the derived CSVs).

## 2026-07-17 — STRUCTURED LAYER BUILT (vision-cache reference implementation)

`build_finance.py` (family **`vision_cache`**, shared helpers `scripts/campaign_finance/vision_lib.py`)
now writes the derived CSVs — `contributions.csv` (10) / `expenditures.csv` (15) / `filing_totals.csv`
(**19** = the 19 scanned township C&E filings; the 6 COI rows are OUT OF SCOPE, excluded by
`in_scope_fn`) / `cycle_totals.csv` (14 candidate-cycles) — all regenerable, never hand-edited.
`validate_finance.py` PASS (0 fails; 6 WARNs = the excluded COI rows have no filing_totals row, by
design). `scripts/validate_city.py copperton_city_council/` unchanged (0 FAIL).

- **Scope:** the 19 scanned SLCo-Clerk candidate disclosures 2016–2021, every one consumed from its
  `vision/*.json` cache. The 5 born-digital `format=text` rows are all COIs (no campaign-finance text
  filing exists), so no text sidecar is parsed; the 6 COI rows carry no dollars and are excluded.
- **Reconciliation:** 11/19 filings reconcile BOTH sides against printed covers; 8 are honest
  totals-only/blank (fee-only or $0 pages that print a cover total over an itemized-nothing schedule —
  reconcile UNKNOWN, never a fabricated mismatch). Verbatim quirks preserved: Baxter-2016
  struck-through ending balance = null; Severson-2021 Dec blank this-period totals = null; Column-B
  YTD figures deliberately not captured.
- **Regime (per candidate-cycle, printed + eyeballed):** ALL cycles resolve to `incremental` — no
  cumulative restatement chains. The two multi-filing 2019 candidates (Bailey, Stitzer) file disjoint
  per-period reports; every 2021 pair is a $50/$50 interim + a $0/null Dec summary.
- **One `cycle_overrides.csv` row — Kathleen Bailey 2019:** her Dec "summary"-typed filing is itself a
  disjoint period report (a single $71.60 loan-repayment-to-self, disjoint from the Oct interim's
  $428.40), so the generic summary-vs-interim `max()` rule undercounts spent by $71.60. Override sums
  both filings → raised $450 / spent $500 (basis=override; the reason is carried as the row's
  review_flag). Every other multi-filing cycle needs no override (max()=sum there).
- **`donor_aliases.csv` (3 curated, evidence-cited):** "Sean Clayton (self)" + "Tessa Stitzer (filing
  fee)" → `candidate-self` (the parentheticals defeated the deterministic surname+firstname matcher →
  `unknown`); "Reagan Outdoor Advertising" → `business` (Utah billboard company; the 3-token name read
  as person-shaped → `individual`). Raw-PDF spot-check (Ron Patrick 2016) confirms every amount/name.
- **`finance_overrides.csv`:** none needed (no row-level corrections vs the raw PDFs).
- Backup of the pre-build docs: `_backups/2026-07-17-cf-structuring/copperton/`.

## Join to other layers

Join finance ↔ council votes/elections on **person + year** (Copperton seats are **at-large** — no
district key) — normalize the UPPER-CASE election names first (e.g. `KATHLEEN RAY BAILEY`, `SEAN
CLAYTON`, `KEVIN SEVERSON`). Mind the **township→town seam** (2024-05-01) and the presiding-officer
rule (the Chair/Mayor VOTES in both eras — max roll 5). Sean Clayton spans the whole record (2016
founding cohort → 2023 Seat B → first Town Mayor 2025). Kevin Severson appears in 2017 (@LRG winner)
AND 2021 (Seat E write-in winner). Kathleen Bailey / Tessa Stitzer span 2016 → 2019 → (2023).

## Rebuild / refresh

`index.csv` is generated from the retained `raw/` PDFs + `raw/_fetch_log.jsonl`:
```
python3 build_copperton_cf_index.py   # idempotent; recomputes sha256 + format from disk, reads source_url from the fetch log
```
The SPEC table (year/seat/candidate/period/filing_type/match) is hard-coded from the SLCo Clerk
page's per-candidate Copperton grouping + the OCR-verified form years + the Copperton town
`/disclosures` + `/election-information` pages. To refresh:
- **2016–2021 (static county page):** re-harvest anchors from
  `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (#copperton).
- **2023 (EasyVote):** requires reaching `ecf-api.easyvoteapp.com` past its HTTP-500/auth-gate — a
  browser/session fetch, not polite GET.
- **2025+ (town site):** re-harvest `copperton.utah.gov/disclosures` + `/election-information`
  (`curl -k` for the TLS cert mismatch; docs at `img1.wsimg.com/blobby/go/07a53a68-…/downloads/…`).
Fetch new PDFs through `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py` (GET-only,
logged) into `raw/`, extend the SPEC table, and re-run. A later dollar-extraction pass
(`/cf-vision-transcribe` → `cycle_totals.py`) is deferred and OUT OF SCOPE here.
