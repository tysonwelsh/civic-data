# campaign_finance/ — Draper municipal campaign-finance disclosures (ACQUISITION layer)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 6). **Acquisition-only:
no dollar amounts extracted** — raw filings + provenance index. In-scope cycles **2021,
2023, 2025**; cycles **2011–2019 came along free** because the city's GRAMA records
portal holds them (see below). Read `AVAILABILITY.md` for per-cycle coverage, the honest
empties, and four flagged election-record findings (incl. CF corroboration of the
canceled 2025 4-year council race).

## What's here

- `raw/` — 148 PDFs (~156 MB): 23 live city-page filings (`<mediahash>_<name>.pdf`),
  117+1 GRAMA-portal attachments (`tyler_<node>_<att>_<label>.pdf`), 7 intact Wayback
  duplicates (`wb<docid>_<name>.pdf`), 8 Wayback truncated partials
  (`wb….pdf.truncated` — do not read; provenance only), plus `raw/_fetch_log.jsonl`
  (url, status, sha256, bytes, retrieved_utc for every fetch, including the truncated
  ones and the skipped/duplicate probes).
- `index.csv` — **125 rows, one per acquired CF filing document** (116 distinct by
  sha256 — 9 rows carry `duplicate_of`). SCHEMA_SPEC §9 contract header
  (`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,
  retrieved_date,format,extraction_method,path`) + extras
  (`seat,source,original_url,tyler_node,tyler_attachment_id,date_precision,
  duplicate_of,matched_election_candidate,join_confidence`).
- `AVAILABILITY.md` — coverage, gaps, flags.

## The three sources and when each is authoritative

1. **`source=city_website`** (2025 only): the live CF page
   `draperutah.gov/city-government/elections/campaign-finance-disclosures/`,
   PDFs at `/media/<hash>/…`. Rewritten every cycle — **harvest the 2027 cycle before
   the page turns over.** Browser UA (Azure edge).
2. **`source=tyler_cm_grama_portal`** (2011–2023): Tyler EagleWeb at
   `drapercityut.contentmanager.tylerapp.com`. **Session-bound**: `source_url`s under
   `/tylercm/eagleweb/downloads/…` need a guest session first — GET
   `/tylercm/web/loginPOST.jsp?guest=true&submit=I+Acknowledge` (cookie jar), then the
   download URL works. Discovery path: Elections search (`docSearchPOST.jsp?__search_
   select=Elections&YearID=<yr>` — also accepts GET), result nodes at
   `viewDoc.jsp?node=DOC…` list all attachments. The portal is the **only** source for
   2023 (never Wayback-crawled, dead on the live CMS).
3. **`source_url` on `wb…` duplicates / `original_url` on 2021 rows**: the old
   CivicPlus `/DocumentCenter/View/<id>` addresses (dead since the ~2024 Umbraco-style
   CMS migration), captured 2022-08. web.archive.org truncated 8 of 15 at exactly
   1 MiB even with 28 s trickle — if you re-pull from Wayback, verify `%%EOF` and
   prefer the Tyler copies.

## Semantics / gotchas

- **`filing_type`**: `interim` = pre-primary, 7-day pre-primary, 28-day pre-general,
  7-day pre-general (incl. Walker 2021 AMENDED); `summary` = the 30-days-after final
  (post-general, or post-primary for eliminated candidates: Herrera Schuster/Sorensen
  2025-09-11, Clegg 2019-08-29, North 2019-09-04). Blank = class unknown (all 2011–2017
  single undated "financials" scans + Rouzer's 2023 compilation) — never guessed.
  **Never sum dollars across a candidate's filings** (repo-wide double-count trap;
  Walker 2021 amendment is an extra double-count risk).
- **`date`** = statutory due date or document date as best known; `date_precision` ∈
  `exact_received` (read off the form: Farley 2021, Rouzer 2023 compilation),
  `from_filename` (city/portal filename carries the date), `est_report_class`
  (statutory due date), `cycle_anchor` (undated 2011–2017 scans — `date` is that
  year's general-election day, NOT a filing date).
- **`seat`** (2025 only): `mayor` / `council-4yr` (the canceled-race pair Green+Lowery)
  / `council-2yr` (the Dahlin/Byington short-term seat). Elsewhere blank — Draper is
  all at-large, so there is no district key; join to elections on
  `matched_election_candidate` + `election_year`.
- **`duplicate_of`** (9 rows): the city double-catalogued all seven 2017 filings (a
  copy in the candidate's DECLARATION node and a byte-identical copy in a FINANCIALS
  node), plus Roberts' 2019-10-28 and Rouzer's 2021 final twice each.
  **Filter `duplicate_of=""` for a distinct-document cut (116 docs)** — critical once
  dollars are extracted.
- **Election join**: `matched_election_candidate` is the UPPER-CASE name in
  `../election_results/draper_results_by_candidate.csv` (year-scoped token match,
  full-name — remember `T. Lowery` ≠ `F. Lowry`). `join_confidence=none` on exactly 12
  rows, all real: 2019 declared-but-withdrawn (Clegg, DeYoung, Mason, North) and 2025
  Green/Lowery (canceled race — flagged, see AVAILABILITY §FLAG 1).
- **Not indexed but in `raw/`**: 3 Oaths of Office (`tyler_DOC362S26?_A?_*` for
  Lowry/Roberts/Johnson — the 2023 nodes mix them in), 1 Cal Roberts email re the
  12.5.2019 deadline, the Recorder’s 2019-07-19 notice letter to Clegg (which dates
  the 2019 first-report deadline: 2019-08-08), and 11 "22-month-retention" declaration bundles (2023) — kept as
  fetched, excluded from the CF index by content inspection. The 2021 declaration
  bundles and 2025 declaration/certificate packets were deliberately not downloaded.
- **The DOC288 nodes** (2021) duplicate the DOC290 catalog rows attachment-for-
  attachment — skipped at acquisition (same files, same labels).
- 2021 was the **RCV pilot**: no primary, so the cycle has only 7-day-pre-general +
  post-general classes. 2023's general was **Nov 21** (CD2-special consolidation), so
  its class dates (10-24 / 11-14 / 12-21) are offset from a normal year.

## Rebuild / extend

Scratch build scripts (session artifacts, not shipped): the index was generated from a
per-attachment classification table + `polite_fetch`-style logs; regenerating means
re-running the acquisition (city page + portal harvest) — everything needed is
documented above and in `raw/_fetch_log.jsonl`. Next cycle (2027): harvest the live CF
page during/right after the cycle, then sweep the GRAMA portal's `YearID=2027` for the
archival copies + any candidates the page dropped. The dollar-extraction step
(contributions/expenditures/cycle_totals, Lehi/Logan pattern) is future work — the
corpus is 92% scanned, so `/cf-vision-transcribe` is the intended method.
