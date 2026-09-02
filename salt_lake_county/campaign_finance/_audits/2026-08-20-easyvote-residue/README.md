# SLCo EasyVote row-less filings — HONEST or GAP? (audit, 2026-08-20)

**Question.** Salt Lake County's EasyVote era (2022–2026) holds 442 downloaded filings. 240 of
them carry no itemized donor/vendor rows in `contributions.csv` / `expenditures.csv`. The repo
could not say whether that was HONEST (no itemizable activity) or a GAP (detail sits in the
document, untranscribed). This audit settles it filing by filing and sizes the recoverable
remainder.

**Method.** Every page of all 240 filings was rendered (`pdftoppm -r 100 -gray`, 1,719 pages)
and READ — 276 contact sheets at ~500 px/page, plus ~180 single-page re-renders at 130–200 dpi
where a row count or a Column-A cell could not be judged from the montage. Nothing was
transcribed: the only figures read off the documents are the two Summary-Page Column-A totals,
which are the reconciliation gate. Classification was per SIDE (contributions and expenditures
separately), then rolled up per filing. Raw per-filing results: `classification.csv`.

**Headline: the row-less-ness is overwhelmingly a GAP, not an honest zero.**
**197 of 240 filings (82%) carry itemized detail in the document — ~18,433 lines over 980 pages.**

## Per-class counts

| cycle | filings | `has-attachment-detail` | `empty-schedule` | `no-schedule-page` | `withheld` | `undetermined` |
|---|---|---|---|---|---|---|
| 2022 | 97 | **89** | 4 | 4 | 0 | 0 |
| 2024 | 91 | **76** | 2 | 13 | 0 | 0 |
| 2026 | 52 | **32** | 2 | 18 | 0 | 0 |
| **all** | **240** | **197** | **8** | **35** | **0** | **0** |

Per SIDE (480 sides): contributions `has-detail` 170 / `empty-schedule` 26 / `no-schedule-page` 44;
expenditures `has-detail` 192 / `empty-schedule` 10 / `no-schedule-page` 38.
**Nothing is `withheld` and nothing is `undetermined`** — every side resolved at the document.

`doc_kind`: 237 `standard-report`, 3 `small-budget-certificate` (the one-page SLCo Ord.
2.72A.204.5 under-threshold certification, no figures exist). **There are NO one-page
dissolution notices in this cohort** — every document titled "Dissolution"/"Final" is the full
standard form with the Final/Dissolution box checked. That differs from the clerk-legacy era,
where the standalone notice is the bulk of the no-Summary-Page class.

## The recoverable class — what a wave would transcribe

| cycle | filings | contribution rows | expenditure rows | total |
|---|---|---|---|---|
| 2022 | 89 | 6,538 | 2,282 | 8,820 |
| 2024 | 76 | 4,574 | 3,568 | 8,142 |
| 2026 | 32 | 860 | 611 | 1,471 |
| **all** | **197** | **11,972** | **6,461** | **18,433** |

Spread over **980 pages** that carry itemized lines (`pages_with_detail` in the CSV names them
per filing). Count basis: **14,397 rows `counted`** line by line, **1,489 `numbered`** (the
filer's own spreadsheet numbers its rows), **2,547 `approx`** (dense uniform grids measured on
sampled pages and extrapolated at a fixed row pitch). ~86% of the estimate is a real count.

Concentration is extreme: the largest 10 filings hold roughly a third of the rows
(Olson 287617F3 = 138 C + 268 E; Harrison BDCA235C = 425 C; Wilson, Chapman, Rivera, Frost,
Gettel and Morris each carry 150–450). A wave that took only the 60 largest filings would
recover well over half the total.

## Layouts — one county grid plus a long tail of filer-specific exports

Detail sits in one of three structural places, and this matters for a wave's page-finding logic:
1. **on the county's own Schedule A/B grid** — 224 of the 362 has-detail sides (62%). One
   geometry, stable 2022→2026, ~15 ruled rows per page with a printed `SUBTOTAL FOR THIS PAGE`
   and a `TOTAL … RECEIVED/MADE` line.
2. **on a filer attachment behind a blank county stub** reading "See Schedule A attached" /
   "See attached" / "See Worksheets" — the shape the coordinator's brief describes.
3. **with NO county schedule page in the document at all** — the filer's own sheet simply *is*
   the schedule (Hobbs, Wilson ×4, Morris, Chapman 2026, Robinson, Srivastava, Pinkney,
   Gehrke …). **A wave keyed on finding a "See Attached" stub would silently miss these** —
   agents counted well over a thousand rows in this shape.

Attachment layouts: **63 distinct filer slugs**, collapsing to **19 field-set families** once
column ORDER and synonyms are normalized. Four families cover 110 of the 138 attachment sides:
`date+recipient+purpose+amount` (52 E), `date+name+address+geo+occupation+amount` (30 C),
`date+name+address+occupation+amount` (21 C), and the in-kind-flagged expenditure variant (7 E).
Layouts are **filer-stable across cycles** (Gill uses one pair 2022/2024/2026; Wilson one pair
across four filings), so per-filer calibration transfers.

## Geometry anchoring outlook — good

- **185 of 197** has-detail filings have printed table gridlines (`ruled=1`); 10 are unruled
  text tables and 2 are mixed (one side ruled, the other not). `pct:` boxes are anchorable on
  the overwhelming majority, and the county-grid half of the corpus has a fixed template.
- **178 of 197** print their own SUBTOTAL/TOTAL line — a real page- or side-level reconciliation
  gate on top of the Summary Page figure.
- **19 filings have no printed gate at all** (~4,290 rows) — the Summary-Page total is the only
  check. Named in the CSV (`subtotals=0`); Olson 2024, Wilson B5D1F91C, Harrison ×2 and Gettel
  are the large ones. For these, a row-count gate (rule-detection banding, as wave B2 used on
  the McAdams landscape export) is the second independent check.
- **28 of 197 are handwritten**; the rest are typed or printed — far easier than the
  clerk-legacy handwriting.
- Two mechanical traps: **rotated attachments** (Harrison E5C37303 pp.8–14, Morris) are stored
  90° inside the PDF and must be rotated before rendering; and one attachment
  (Liewer, p9, a bank export) **runs off the bottom of the page mid-row** — 26 visible debits
  sum to $8,142.97 against a stated $8,316.61, so $173.64 of lines never printed. That is a
  real ceiling, not a zero.

## Redaction — donor geography does NOT survive

The county's black bar covers the itemized rows' address column on 157 of 197 filings; it never
obscures a donor name, date or amount, so **nothing is `withheld`**. But the repo keeps
`donor_city`/`donor_state`, and those are lost almost everywhere:
- On the **county grid** the bar covers the single "Complete Mailing Address" cell — city, state
  and ZIP live inside that cell, so they go with it.
- On **attachments with separate Address/City/State/Zip columns**, one wide bar routinely spans
  all four.
- **Exactly three filings preserve any geography**: `Robinson-Zach__7022E201` (ZIP legible),
  `Robinson-Zach__C4162BAF` (street address only redacted), `Pinkney-Natalie__07C097D5`
  (state, ZIP and country survive).
A wave should expect `donor_city`/`donor_state` to be honestly blank as a **county redaction**,
and the row note must say *redacted*, not *left empty by the filer* — different facts.
Occupation/Employer almost always survives; on a handful of filings the bar clips its left edge
and on `Anderson-Kathleen__3E1F074A` it covers the occupation cell on most rows.

## Contradictions against stated totals — 3, all verified at the document

A side classified `empty-schedule`/`no-schedule-page` whose Summary Page states a NON-ZERO total
for that side. Every one was re-rendered and read again by the auditor:

| filing | side | stated (Column A) | what the document shows | verdict |
|---|---|---|---|---|
| `Snelgrove-Richard__CE0A4B74` (2024, Recorder, Final/Dissolution) | expenditures | **$3,261.09** | 2-page filing, cover + Summary only. Lines 3/5/6 all read 3,261.09 and line 7 closes at 0. **No Schedule B page exists.** | **GENUINE GAP** — $3,261.09 spent, no detail ever filed. It is the final report, so no sibling can cover it. |
| `Ahn-Danielle__23F2E34E` (2022, District Attorney) | expenditures | **$11,868.21** | Schedule A is typed on the county grid (11 rows). Schedule B page is present and wholly blank; line 6 also reads 11,868.21. | **GENUINE GAP at this filing**, but the sibling `Ahn-Danielle__43FA92A0` (final/amended, overlapping period) itemizes ~30 expenditure rows totalling $11,008.96 — partial sibling cover, the clerk-legacy `Romero` pattern. |
| `Creno-Tracey__E28B702C` (2026, Sheriff, Final/Dissolution) | contributions | **$5,046.08** | Schedule A present and wholly blank. BUT the same Summary's line 4 ("From Line 1 Column A") reads **0** and line 6 reads **1,500**, and Schedule B itemizes exactly one $1,500 row. | **NOT a gap — a basis inversion.** The filer put the CYCLE-CUMULATIVE figure in lines 1/2 and the period figure in lines 4/6. Same per-filer semantic already documented for DeBry 2022 and Gill 2007 (CLAUDE.md finding 12). Period activity is $0 in / $1,500 out and is fully itemized. |

So the honest count is **2 genuine stated-total-without-detail gaps ($15,129.30) and 1
basis-inversion false positive**. Nothing else in 480 sides disagreed.

**Independent validation of the 2026-08-02 vision tranche.** The 2022-cycle stated totals were
re-read from the documents without reference to the caches, then compared: **191 comparable
sides, ZERO disagreements.** That tranche's Column-A figures hold.

## Things this audit found that the repo's own docs get wrong

1. **"The 2022 EasyVote cycle has NO itemized rows in the API" is FALSE.**
   `RECON.md`, `AVAILABILITY.md` and `campaign_finance/CLAUDE.md` all assert it. Joining
   `advancedsearch_{contributions,distributions}.json` on `DocumentFilingId` (strip `_Redacted`)
   → `documentid` shows **26 of the 123 2022-cycle documents carry keyed itemized rows**, e.g.
   `Chapman-Lannie__FC001F57` ("November 1 Amendment", submitted 01/31/23) with **556
   contributions** whose dates are 2022. Verified directly against the JSON. The claim is most
   likely a downstream artifact of the office gate the coordinator is separately repairing; the
   docs still need correcting.
2. **143 of the 240 row-less filings are absent from `filing_totals.csv` entirely** — all 91
   from 2024 and all 52 from 2026. They have no itemized rows AND no stated totals AND no vision
   cache: they exist only as a PDF plus an `index.csv` row. The 2022 cohort, by contrast, has
   complete stated totals from the 2026-08-02 tranche. Any wave here should ship stated totals
   for those 143 as well, not just itemization.
   *(`filing_totals.csv` was read once for this cross-check while another agent was rewriting
   it; it stood at 841 rows at 2026-08-20T17:2x.)*
3. **School-board filings have leaked into the county-office index.** Both
   `FIFE-JEPPERSON-CHARLOTTE` filings (`AE07FEF8`, `D20522DA`) are indexed `office=County
   Council`; the cover's Office Sought reads **Salt Lake School Board District 2**. Flagged, not
   relabelled (riverton-Pierucci precedent). A third filing of hers carries
   `index.csv election_year=2000` from an EasyVote `datesubmitted` of `01/01/01`.
4. **`index.csv` form-year is not the cycle, at scale.** ~25 filings across 2022/2024/2026 print
   a "2020 Financial Disclosure Report" cover; one 2026 filing uses the 2019 form. Already
   documented for 2022; it runs through 2024 and 2026 too.
5. **The 2026 form family is not one form.** "Financial Disclosure Report **For an Open Campaign
   Account**" and "…**For a Candidate**" are both live in the 2026 cycle, with different
   Type-of-Report option sets and different Column-B semantics.

## Things in the coordinator's brief the documents contradicted

- The brief's illustration — a blank county stub pointing at a filer attachment — is **one of
  three** structural shapes, and only the second-commonest. **62% of has-detail sides are typed
  or handwritten directly onto the county's Schedule A/B grid**, and a further group has no
  county schedule page at all. Stated as the brief instructed: the documents govern.
- "Donor addresses redacted with black bars" understates it: on the county grid and on most
  attachments the bar takes **city, state and ZIP with the address**. Only 3 of 197 filings
  leave any donor geography legible.
- The brief anticipated one-page dissolution notices; there are none. It anticipated a
  `withheld` class; there is none.
- Beyond the brief's four states, one further class recurs and should be named for a wave:
  **`schedule-total-vs-summary-gap`** — the detail IS all present, but the schedule's printed
  grand total sits below Summary line 1/2. It appears on roughly a quarter of has-detail
  filings and the cause is uniform and benign: **the page subtotals exclude In-Kind rows that
  the schedule nonetheless lists**. A wave that reconciles against the SCHEDULE total instead of
  the SUMMARY figure will manufacture false deltas on dozens of filings.

## Scope note

Read-only audit. Nothing outside this directory was modified; no build script, CSV, doc or
`gov.db` was touched, and nothing was federated. The classification is of DOCUMENTS — no donor
name, address or individual amount was transcribed anywhere.
