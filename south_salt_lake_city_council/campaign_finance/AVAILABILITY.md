# South Salt Lake — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained with full
provenance; **no OCR/vision extraction and no dollar totals** — deferred;
`extraction_method='none (acquisition-only; …)'` on every row). **Cycles in scope:**
2021 (Mayor + D2/D3 + At-Large), 2023 (D1/D4/D5 + At-Large), 2025 (Mayor + D2/D3 +
At-Large + **At-Large 2-yr special**). **Bonus (on the same city pages):** a 2026
council-vacancy appointment filing set (7) + the 2026 elected-officer conflict-of-interest
disclosures (8).

**68 filings, ~102 MB, all under `raw/`** (each with sha256 + HTTP status in
`raw/_fetch_log.jsonl`), fetched GET-only via `scripts/polite_fetch.py`. **Two document
classes:**
- **60 campaign-finance filings** — Utah campaign financial disclosure reports
  (contributions/expenditures), the campaign-finance dataset proper: 2021 (9), 2023 (20),
  2025 (24), **2026 council-vacancy appointment (7)**.
- **8 Conflict-of-Interest (COI) disclosures** — "Elected Officer Annual Conflict of Interest
  Disclosure Statement" (Utah Code 10-3-1313 / 20A-11-1604(6)), FY2026, one per seated
  official. These are **officeholder ethics disclosures, NOT campaign contribution/expenditure
  reports** — `filing_type='coi_disclosure'`; **exclude them from any cycle/money total.**
  Captured because they sit on the same city disclosure page and document each seated member's
  financial interests (elections→members→votes chain), but they are not campaign filings.

**Format split: 14 born-digital `text` / 54 `scanned`** (image-only; OCR/vision deferred).
The scanned files are the hand-filled / image-scanned state-form declarations (all 9 of the
2021 state-tree files are scanned); the born-digital ones are typed 2023/2025 reports
(Mitchell, Pinkney, Sanchez, Karzen, Williams, Campos, Wood post-general) plus the COI forms.

## What was checked (search order)

1. **City recorder / elections pages (PRIMARY host for 2023 + 2025 + 2026).** From
   `https://sslc.gov/212/Elections-Voting` two dedicated pages carry the filings, both built on
   CivicPlus **Archive Center** (documents are `Archive.aspx?ADID=<n>` → redirect to
   `/ArchiveCenter/ViewFile/Item/<n>`, `application/pdf`):
   - **`/469/Campaign-Finance-Statements`** → three archive modules:
     `AMID=61` **2025 Elections** (24 docs), `AMID=62` **2023 Elections** (20 docs),
     `AMID=64` **2026 Council Vacancies** (7 docs).
   - **`/559/Conflict-of-Interest-Disclosures`** → `AMID=60` **Current Elected Official
     Disclosures** (8 COI forms). (`DocumentCenter/View/3504` on the elections page is the
     **blank COI form template**, not a filing — not captured.)
   `source=city_archive_center`. The Archive-Center document rows render server-side but the
   file links use `Archive.aspx?ADID=<n>`, NOT `DocumentCenter/View` — a bare href/pdf grep
   misses them; parse the `ADID=…<span>title</span>` pairs.
2. **State — `disclosures.utah.gov/Municipal`** (GET-navigable folder tree; the
   `/Municipal/salt lake` → `salt lake_<year>` → `salt lake_<year>_South Salt Lake City`
   chain). Present with files: **`salt lake_2021_South Salt Lake City`** (9 PDFs — the ONLY
   host for the 2021 cycle; the city Archive Center starts at 2023). The **`salt lake_2023`
   SSL folder redirects to the city page** `sslc.gov/212/Elections-Voting`, and the **2025 year
   folder has NO SSL subfolder** (also city-hosted) — same "recent cycles live on the city
   site" pattern as Cottonwood Heights / Riverton / Holladay. `source=state_lg_municipal_disclosures`.
   Dir listings 403 but individual files GET fine; state links use Windows **backslash** paths
   rewritten to https + forward-slash + `%20`.
3. **SLCo Clerk financial-disclosures** (`saltlakecounty.gov/clerk/elections`) — the city
   elections page links out to the county for county/state contests, not municipal
   city-council/mayor candidates. Not a source for SSL municipal filings.
4. **Wayback** — **not needed for 2021/2023/2025**: the city Archive Center + the state
   `_2021_` folder together cover every in-scope ballot candidate, and all 68 files fetched
   live (200). (Wayback IS the only remaining path for a 2019 recovery — see flag 3 below.)

## Coverage vs the election roster (`election_results/south_salt_lake_races.csv` + `_by_candidate.csv`)

**Every candidate who appeared on a ballot in an in-scope cycle (2021/2023/2025) has
campaign-finance filings — coverage is COMPLETE.**

| Cycle | Ballot candidates (office) | Finance filers held | Status |
|---|---|---|---|
| **2021** (Mayor/D2/D3/At-Large) | Mayor ×3 (Wood\*, Christensen, Siwik); D2 ×2 (Thomas\*, Garfield); D3 ×2 (Bynum\*, Hampton); At-Large ×2 (Williams\*, Spencer) | all **9** | **COMPLETE** |
| **2023** (At-Large/D1/D4/D5) | At-Large ×2 (Pinkney\*, Campos); D1 ×2 (Huff\*, Potter); D4 ×2 (Mitchell\*, Mila); D5 ×1 (Sanchez\*, unopposed) | all **7** | **COMPLETE** |
| **2025** (Mayor/D2/D3/At-Large/At-Large-2yr) | Mayor ×2 (Wood\*, Karzen); D2 ×1 (Thomas\*, unopposed); D3 ×2 (Bynum\*, Hampton); At-Large ×1 (Williams\*, unopposed); **At-Large-2yr ×2 (deWolfe\*, Campos)** | all **8** | **COMPLETE** |

`*` = seat winner. **Per-candidate filing counts** (excludes the 8 COI forms):
- **2021** — 1 file per candidate (9 total), from the state tree; each a single per-candidate
  cycle filing.
- **2023** — 3 filings per candidate (a pre-general "Final", an election-period "Electionl"
  report, and a year-end "Final") EXCEPT **Jeanette Potter** (D1 runner-up, lost) who filed 2
  (no year-end final). 6×3 + 2 = 20.
- **2025** — 3 filings per candidate (two pre-general interims + a Dec-4 post-general final),
  8×3 = 24.

**Bonus 2026 council-vacancy appointment** (`AMID=64`, 7 applicants): Joy Glad, Irvin Jones,
Laurie Robinson, Leo Shivers, Charles Connelley, Robert Tate, Darlene McDonald. These filed
campaign financial disclosures for the **appointive** filling of the D1 + D5 vacancies (the
`serving` D1 **Glad** and D5 **Jones** appointees per the city `CLAUDE.md`), NOT for an
election — `election_year` blank, `filing_type=summary`, `join_confidence` none/person_only.

**Bonus 2026 COI** (`AMID=60`, 8): Wood (Mayor), Thomas (D2), Bynum (D3), Mitchell (D4),
Williams + deWolfe (At-Large), Glad (D1), Jones (D5) — the current seated body.

## Discrepancy FLAGS (recorded here only — `election_results/` was NOT edited)

1. **⚠ The 2021 Mayor race was 3-way, implying an August 2021 municipal PRIMARY that
   `election_results` does not list.** `south_salt_lake_races.csv` stores only winner+runner-up
   for the 2021 Mayor row, but `_by_candidate.csv` DOES carry all three (Wood 1,777 / Christensen
   678 / **L. SHANE SIWIK 596, rank 3**), and **all three filed campaign-finance reports** in the
   2021 state folder. Utah holds a municipal primary when a single-seat field exceeds two
   candidates, so a **2021 primary (≈Aug) is implied but absent from `election_results`** (no 2021
   `municipal primary` rows exist for SSL). Finance corroborates the 3-way field; the missing
   primary rows are an election-record gap to verify, NOT a finance-coverage miss. (This mirrors
   the recon note that the 2011/2019 SSL primaries/generals needed raw-SOVC recovery.)
2. **Siwik is fully accounted for — NOT an unlisted candidate.** He was the 3rd 2021 mayoral
   candidate (`_by_candidate.csv` rank 3), matched `office=Mayor`, `join_confidence=exact`. His
   presence in the 2021 folder (while D5 was not on the 2021 ballot) is because he ran for **Mayor**
   in 2021, not District 5.
3. **2019 cycle — no filings surfaced; the state folder is a shell that redirects to a dead
   legacy page.** A `salt lake_2019_South Salt Lake City` folder is **registered but holds ZERO
   files**; it redirects to the legacy `https://sslc.com/city-government/election-2019` page,
   which is **unreachable** (connection timed out, 2026-07-13). This aligns with the **known 2019
   election-record gap** (`recon.md` / `election_results/CLAUDE.md`: 2019 D-rows were dropped from
   the SLCo archive and recovered by raw-SOVC re-parse). **No 2019 finance filings surfaced to
   corroborate the recovered 2019 contests** — the finance channel is legacy-only/silent for 2019.
   Recovery would require a Wayback crawl of `sslc.com/city-government/election-2019` — documented
   future work, out of the 2021/2023/2025 scope. **A `salt lake_2011` SSL subfolder does not exist
   at all** (2011 is the other known election-record gap; the finance channel is likewise silent).
4. **2025 At-Large 2-Year special (deWolfe) is captured as its own contest.** deWolfe + Campos
   both filed under the off-cycle `district='At-Large-2yr'` seat — matching the
   `election_results` special (Pinkney → county council, deWolfe appointed Jan-2025 then won the
   special). Not a discrepancy; flagged so member-term logic doesn't read it as a cycle shift.
5. **2026 council-vacancy filings have no matching election.** Seven applicants filed CF forms
   for the appointive D1/D5 vacancy fill; there is no 2026 SSL election. `in_election_results=no`
   for the six non-winning applicants (and Glad, appointed D1) is expected; only **Irvin Jones**
   matches the election roster at all (2011 D5 winner; `join_confidence=person_only`).
6. **Name-normalization** (election names are UPPER-CASE, stored in `matched_election_candidate`):
   filing **"Nicholas Mitchell"** = election **NICK MITCHELL** (`normalized`); **"LeAnne Huff"** =
   **LEANNE HUFF**; filing **"Ray deWolfe"** = **G. RAY DEWOLFE** (`normalized`); 2021 **"Aileen
   Hampton"** = **AILEEN E. HAMPTON**; **"Clarissa Williams"** = **CLARISSA J. WILLIAMS**.

## The double-count trap (per SKILL §6) — READ BEFORE ANY DOLLAR TOTAL

SSL candidates file **multiple reports per cycle** (2023 = pre-general + election-period +
year-end; 2025 = two pre-general interims + a post-general final). The Utah form carries a
**"Year to Date" cumulative column** alongside per-period transaction detail, so the LAST report's
YTD (not a sum of every filing) is the cycle total. `is_incremental='no'` on every campaign-finance
row reflects that a cumulative YTD figure exists; the per-period transaction *detail*, however, is
non-overlapping across a candidate's reports (verified from born-digital dates: Mitchell 2023 =
≤Oct 22 / Oct 23–Nov 8 / Nov 15+). **NEVER sum a candidate's filings blindly** — verify per
candidate via `scripts/campaign_finance/cycle_totals.py` at the (deferred) extraction stage before
quoting any total. COI rows carry blank `is_incremental` (n/a).

## Dates are ACQUISITION-layer inferences (see `CLAUDE.md`)

Every `date` is anchored to the filing's report LABEL / statutory deadline (`date_precision`
column: `label_inferred` / `label_year`), NOT read as a signature date from the (mostly scanned)
PDF. Verified anchors: 2025 "Post Election Filing" = the Dec-4 post-general form (confirmed from
Wood's born-digital form checkbox); 2023 period order confirmed from born-digital transaction-date
windows. Exact filing dates and dollar figures require the deferred OCR/vision extraction pass.

## Not captured / out of scope (deliberate)

- **Dollar amounts / contribution + expenditure tables** — not extracted (acquisition layer).
  Extraction to `filing_totals.csv` / `cycle_totals.csv` is future work; the 54 scanned forms will
  need OCR or the `cf-vision-transcribe` skill.
- **2019 / 2011 cycles** — no filings surfaced (state shells empty / redirect to a dead legacy
  page; see flag 3). Wayback recovery of `sslc.com` is future work, below scope.
- **Pre-2021 state folders** (`salt lake_2017`, `_2015`, …) exist but are below the 2021/2023/2025
  scope — not fetched.

## 2026-07-17 — Dollar amounts NOW EXTRACTED (structured layer built)

The "no dollar figures" caveat above is **SUPERSEDED for the 53 in-scope 2021/2023/2025 C&E
filings.** `build_finance.py` (family `vision_cache`) writes `contributions.csv` (839) /
`expenditures.csv` (510) / `filing_totals.csv` (53) / `cycle_totals.csv` (24). Read
`cycle_totals.csv` for a per-candidate total (it encodes the dedup); the on-disk `raw/` PDFs +
`vision/*.json` caches remain canonical. `validate_finance.py` PASS.
- All 40 scanned + **13 born-digital `format=text`** filings are transcribed (the 13 text ones
  were Read-tool vision-transcribed 2026-07-17 because their text layers are handwritten /
  `SEE ATTACHED` scanned / AcroForm / custom-spreadsheet — not deterministically parseable).
- The **double-count trap** is now handled: the SSL form is INCREMENTAL (Column A this-period /
  Column B YTD); a cycle total = Σ Column A = the final report's printed YTD. Ten
  `cycle_overrides.csv` rows apply the YTD-not-sum discipline where the Dec year-end
  `summary`-typed report is itself a per-period ($0) filing. Cumulative-restatement filers
  (Sanchez 2023, deWolfe 2025) take the latest report.
- **Coverage / notable cycle totals (from `cycle_totals.csv`, deduped):** 2021 Mayor —
  Wood $16,495 / Christensen $7,209 / Siwik $8,531; 2023 At-Large — Pinkney **$29,666** vs
  Campos $6,023; 2025 Mayor — Wood **$35,915** vs Karzen $14,969.
- Nine filings carry verbatim, unadjusted filer inconsistencies (2021 struck-through covers;
  Campos 2025 `adid311` stale carryover; Pinkney `adid336` ±$750; Mitchell `adid340` +$0.75).
- The 8 FY2026 COI + 7 2026 council-vacancy filings remain OUT of scope (excluded from the
  money layer).
