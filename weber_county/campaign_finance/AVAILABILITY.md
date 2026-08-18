# Campaign finance — availability, coverage & gaps (Weber County offices)

**As-of 2026-08-01.** Companion to `RECON.md` (which channels were checked and how).
This file answers: **what exists, what was retrieved, and what is honestly missing.**

**Result: GOOD for a Utah county — every even-year cycle 2012–2026 is represented, with
one cycle (2014) recoverable ONLY from the Internet Archive and two cycles (2018, 2020)
where the county's own archive holds far fewer filings than the county's own former
website once listed.**

- **89 documents retained** (117.4 MB) across 4 channels.
- **197 index rows** = **196 filings** (114 of them page-ranged inside a consolidated PDF)
  + 1 document-grain row.
- **98 county-office filings**, **32 distinct county-office candidates**, cycles
  **2012 · 2014 · 2016 · 2018 · 2020 · 2022 · 2024 · 2026**.
- **STATED-TOTALS LAYER BUILT 2026-08-01** — `filing_totals.csv`, one row per
  county-office filing, **98/98 with a stated cumulative contribution total** (see §7).
- **ITEMIZED LAYER COMPLETE — QUEUE CLOSED 2026-08-18.** All **98 of 98** county-office
  filings carry donor/vendor rows (**1,360 contributions + 1,256 expenditures**, 100%
  `pct:`-geometry-anchored, zero sides withheld). Read the **"QUEUE CLOSED 2026-08-18"**
  section at the end of this file before quoting any itemized figure.

---

## 1. Coverage matrix — county-office filings by office × cycle

| office (as stated on the form) | 2012 | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---|---|---|---|---|---|---|---|---|
| **Commission Seat A** | — | 2 | — | 1 | — | 2 | — | 17 | **22** |
| **Commission Seat B** | — | 2 | — | 1 | — | 2 | — | 4 | **9** |
| **Commission Seat C** | — | — | 2 | — | 1 | — | 11 | — | **14** |
| **Commission (seat not stated)** | 3 | — | 3 | — | — | — | — | 1 | **7** |
| **Clerk/Auditor** | — | 4 | — | 1 | — | 1 | — | 1 | **7** |
| **Sheriff** | — | 2 | — | 1 | — | 1 | — | 1 | **5** |
| **Attorney** | — | 2 | — | — | — | 1 | — | 1 | **4** |
| **Assessor** | — | 2 | — | — | 1 | — | 4 | 1 | **8** |
| **Recorder/Surveyor** | — | 5 | — | — | 1 | — | 4 | — | **10** |
| **Treasurer** | — | 4 | — | — | 1 | — | 4 | — | **9** |
| **(office field blank on the form)** | — | — | — | — | — | — | — | 3 | **3** |
| **total** | **3** | **23** | **5** | **4** | **4** | **7** | **23** | **29** | **98** |

The 2026 column is **in-cycle and lopsided by design**: Commission Seat A drew a
seven-candidate convention field, and convention/pre-primary/primary reports are all filed
before the general — so 17 of 29 rows are Seat A. It is not a coverage bias.

### 1b. Coverage matrix WITH DOLLARS (2026-08-01 stated-totals tranche)

Every figure below is a **stated cumulative total printed on a filing's own cover
page** — nothing is computed from itemized rows (there are none) and nothing is
inferred. **The forms are CUMULATIVE**, so a cycle figure is Σ over candidates of each
candidate's **latest non-superseded** report, **never** a sum of that candidate's
filings.

| cycle | filings | candidates | Σ latest cumulative RAISED | Σ latest cumulative SPENT | what the cycle figure actually is |
|---|---|---|---|---|---|
| 2012 | 3 | 2 | $69,221.41 | $59,483.83 | 1 final + 1 pre-general (Combe filed no final) |
| 2014 | 23 | 11 | $200,749.54 | $166,564.39 | finals for all 11 — the richest cycle |
| 2016 | 5 | 2 | $94,301.70 | $90,741.10 | last-filed report per candidate (no January final exists for either) |
| **2018** | **4** | **4** | **$109,232.04** | **$100,014.77** | ⚠ **FINALS ONLY** — every interim is lost (§3) |
| **2020** | **4** | **4** | **$34,469.72** | **$26,232.46** | ⚠ **FINALS ONLY** — every interim is lost (§3) |
| 2022 | 7 | 6 | $85,886.71 | $78,158.54 | Oct-25/Nov-1 pre-general per candidate |
| 2024 | 23 | 6 | $153,927.05 | $126,163.69 | Dec-5 finals for all 6 |
| 2026 | 29 | 14 | $353,158.66 | $318,676.57 | **in-cycle**, latest report as of the 2026-08-01 harvest |
| **all** | **98** | | **$1,100,946.83** | **$966,035.35** | not a time series — see the caveats below |

**⚠ THE FINALS-ONLY BIAS (the comparability ceiling worth stating on every chart).**
2018 and 2020 are the only cycles whose figures rest on **a single report per
candidate with no interim behind it**, because the county's own interim filings for
those two cycles are gone (§3: 24 lost in 2018, 9 in 2020). Their cycle dollars are
therefore **not less complete in amount** — a cumulative final restates the whole
cycle — but they are **not comparable in shape**: there is no way to see *when* the
money moved, no pre-convention or post-primary snapshot, and no way to detect a
candidate who raised and spent entirely before the final. Every other cycle can be
read as a trajectory; 2018 and 2020 can only be read as an endpoint.

**Proposed caveat sentence for the coordinator** (drop-in for a `caveat`-table row or
a chart footnote):

> *Weber County campaign-finance cycle figures for **2018 and 2020** are
> **FINAL-report figures only**: the county's interim (pre-convention / post-primary /
> pre-general) filings for those two cycles were published on its former website and
> no longer exist on any channel (33 filings, ledgered in `unrecovered.csv`). The
> amounts are whole-cycle cumulative totals and are not understated, but no
> within-cycle timing exists for 2018/2020 and they must not be compared
> trajectory-to-trajectory against 2014, 2022, 2024 or 2026.*

Other things a dollar comparison must respect:

- **Officeholder accounts carry across cycles, and the cumulative column carries them
  with it.** James H. "Jim" Harvey's 2024 final states **$77,060.05** cumulative, but
  its own opening column is **$28,610.05 / $21,218.46 / $7,391.59** — exactly his 2020
  final figures. Ricky D. Hatch (2018, 2026) and Gage Froerer (2022 opening = his 2018
  closing balance) do the same. A "raised in cycle N" question must subtract the
  opening column, which `stated_beginning_balance` carries for the balance line only.
- **2016's James H. Harvey 2016-10-31 filing exists on TWO channels** (inside the 2016
  archive PDF and as a standalone Wayback PDF). Both were transcribed independently
  and agree exactly; the rollup above counts it **once**.
- **Two superseding re-files exist and are marked in `filing_totals.notes`:** Gage
  Froerer's 2022-06-21 report is hand-labelled *"Amended"*, and Katrina C. Gibson filed
  a **second June-16-Primary report on 2026-07-23** correcting the 2026-06-16 one
  (whose "Last Report" column repeats the prior report's *This Report* figures).
- **Expenditures are sometimes printed in parentheses** (Steven Van Wagoner 2024,
  Sharon Arrington Bolos 2026 negative balances). `filing_totals.csv` stores the
  parsed **signed** value verbatim; the table above takes absolute values for the
  spend column and says so here.
- **A dash is not a zero.** Ten filings leave the cumulative ending-balance cell as the
  filer's `-` nil marker; `stated_ending_balance` is **blank** on those rows, never 0.

Read the zeros as **"no filing exists in any channel"**, not "not looked for". A county
office only appears in the cycle its four-year term is on the ballot (Commission Seats A/B
and Clerk/Auditor, Sheriff, Attorney in one pair of cycles; Seat C, Assessor,
Recorder/Surveyor, Treasurer in the other), so the checkerboard is the real election
calendar — except where §3 records a genuine loss.

### Per-cycle source of record

| cycle | filings | where they came from |
|---|---|---|
| 2012 | 3 | Wayback per-candidate (Bell ×2, Combe). **The county's own "2012 Reports" archive PDF contains ZERO county-office filings** — all 12 filings in it are school board (verified page by page). |
| 2014 | 23 | **Wayback ONLY.** No 2014 archive PDF exists on the county page and the state site has no 2014 folder. The single richest cycle in the dataset. |
| 2016 | 5 | 1 in the county archive PDF (Harvey) + 4 Wayback per-candidate (Gochnour ×2, Harvey ×2). |
| 2018 | 4 | county archive PDF only — see §3, the portal once listed 24 more. |
| 2020 | 4 | county archive PDF only — see §3, the portal once listed 9 more. |
| 2022 | 7 | county archive PDF (also published, re-saved, on the state site — §4). |
| 2024 | 23 | county archive PDF (167 pages, 50 filings, 23 of them county office). |
| 2026 | 29 | per-candidate PDFs on the live page, in-cycle (convention / pre-primary / primary / final). |

---

## 2. School board — OUT OF SCOPE (and why 91 school-board rows exist anyway)

Weber County's elections office is the filing officer for **county offices AND local
school board** (Ogden City and Weber County school boards) — they share one form, one web
page, and one archive PDF per cycle. **School board is out of scope for this dataset.**

But the consolidated archive PDFs cannot be split by scope without lying about what the
retained document is: the 2024 archive is one 167-page PDF holding 50 filings, 23 county
and 27 school board. So `index.csv` inventories **every** filing inside each retained
document and marks it `office_scope` ∈ `county` | `school_board` | `unclear`. The 91
`school_board` rows are **inventory of a county document**, not a school-board dataset —
no attempt was made to complete school-board coverage (2010 and 2012-primary school-board
singles were acquired only as the verification evidence for §5's negative).

If a school-board dataset is ever wanted, the leads are: the same six archive PDFs, the
state site's `weber_2010 Elections` (7) and `weber_2012 Primary` (14) folders, and the
Wayback per-candidate sets (138 school-board documents enumerated in recon, not fetched).

**Officeholder Conflict-of-Interest forms are also out of scope** — the live page carries
9 of them (2026, one per sitting county officer). `scripts/campaign_finance/SCHEMA.md`
scopes the money layer to **campaign contribution & expenditure reports only**; annual
financial/conflict-of-interest statements are excluded. Their URLs are in
`batch/portal_manifest.json` if that decision is ever revisited.

---

## 3. The real gap: 33 county-office filings the county itself once published, now lost

The predecessor site (`weberelections.com`) published a **sortable table** of every filing
— name, office, date filed, election year — with a link to each per-candidate PDF under
`/documents/reports/`. Wayback captured the **table** (2018-12-12, 2020-10-16, 2021-06-24)
but **never captured a single file under `/documents/reports/`** (CDX over that prefix
returns zero rows). The live site is a different CMS and no longer serves those paths.

So for 2018 and 2020 we know **exactly what existed and can prove it is gone**:

| cycle | county-office filings the portal listed | recovered | **listed but lost** |
|---|---|---|---|
| 2012 | 3 | 3 | 0 |
| 2014 | 23 | 23 | 0 |
| 2016 | 4 | 4 | 0 |
| **2018** | **24** | **0 (per-candidate)** | **24** |
| **2020** | **9** | **0 (per-candidate)** | **9** |

The 2018/2020 **archive PDFs** on the live page do hold 4 filings each — but those are the
year-end/final reports only. The **interim** reports (June pre-convention, July
post-primary, October pre-general) are the lost ones, and they are the reports that show
money moving *during* a campaign. Named losses:

- **2018 (24):** Chris Allred (Attorney) ×2 · John Holloway Thompson (Clerk/Auditor) ×2 ·
  Ricky D. Hatch (Clerk/Auditor) ×2 · Gage Froerer (Commission A) ×3 · James Ebert
  (Commission A) ×2 · James J. Couts (Commission A) ×2 · Neil Hansen (Commission B) ×2 ·
  Scott K Jenkins (Commission B) ×2 · David Allen MacInnes (Sheriff) ×2 · Kevin Burns
  (Sheriff) ×2 · Ryan Arbon (Sheriff) ×2. *Three 2018 sheriff candidates' entire primary
  campaigns are unrecoverable.*
- **2020 (9):** John Ulibarri (Assessor) · Alex McDonald (Commission) · James Harvey
  (Commission) · LeAnn Kilts (Recorder) ×2 · Samuel Leake (Recorder) · John Bond
  (Treasurer) · James Couts (Recorder) ×2.

**Ten county-office candidates have ZERO retained filings for the cycle in question** —
2018: Chris Allred (Attorney), James Ebert (Commission A), James J. Couts (Commission A),
Neil Hansen (Commission B), John Holloway Thompson (Clerk/Auditor), David Allen MacInnes
(Sheriff), Kevin Burns (Sheriff); 2020: Alex McDonald (Commission), Samuel Leake
(Recorder), James Couts (Recorder). Their existence and their filing dates are recorded in
`unrecovered.csv` and `batch/portal_manifest.json` (the captured portal table), so the gap
is a citable fact rather than a silence. `unrecovered.csv` marks each row
`also_in_archive_pdf = yes/NO` so a query can tell "this candidate is thinly covered" from
"this candidate is entirely absent."

The complete listed-but-lost ledger is `unrecovered.csv`.

---

## 4. The 2022 duplicate — two channels, two files, one compilation

| | bytes | pages | cover pages detected | sha256 (first 16) |
|---|---|---|---|---|
| county `raw/archives/2022_combined_7e3a53_78d55edd.pdf` | 6,204,461 | 52 | 1,3,4,7,8,11,14,17,20,30,34,37,40,43,47,50 | `18b09b39c5a1b3b1` |
| state `raw/state/st2022_Weber_County_Candidates_General_Election_22_Financial_Disclosures.pdf` | 6,176,720 | 52 | same, plus a 17th false positive at p27 (OCR artifact) | `d2cb92dd65bded90` |

Identical page count and identical filing boundaries ⇒ **the same compilation, re-saved**,
not two document sets. **Both files are retained** (each is what its own channel
published) but the filings are attributed **once**, against the county copy; the state
copy carries the single `filing_grain=document` row in `index.csv`. **Do not count the
state 2022 file's filings again** — that would double 2022.

---

## 5. Verified negatives (things checked that turned out to hold nothing)

- **State site, `weber_2010 Elections` (7 files):** all seven are **school board**
  (Brad C Smith, Cheryl Ferrin, Dean L. Oborn, J H Thompson, Sharilyn Gerber, Stan
  Bassett, Steven Prisbrey) — read from the rendered forms, since they are handwritten
  and return no `pdftotext` characters. **Zero county-office filings**, so the dataset's
  depth floor is **2012**, not 2010.
- **State site, `weber_2012 Primary` (14 files):** all fourteen are **school board**. The
  county-office 2012 filings (Bell, Combe) came from Wayback instead.
- **State site, odd-year town subfolders (606 files):** all municipal. See RECON.md §2 for
  the residence-town-trap check and the form-header rule actually applied.
- **`weber_2014` / `weber_2024` state folders:** do not exist (server says so).
- **`weberelections.gov` in Wayback:** zero captures.

---

## 6. Cross-entity leads (recorded, not acted on — this dataset changes nothing elsewhere)

- **45 odd-year municipal filings on the state site are by people who also hold or seek
  Weber COUNTY office** — Sharon Arrington Bolos (West Haven city 2013/2017/2021 → County
  Commission Seat B 2022, 2026), Michael N. Thomas (Washington Terrace 2023 → Commission
  Seat B 2026), Jon Beesley (Plain City 2017/2021 → Commission Seat B 2026), Kevin Burns
  (North Ogden 2019; Sheriff candidate 2018), Michelle Tait (Harrisville 2011/2021 →
  Commission Seat A 2026). Those are **city** filings belonging to each city's own
  campaign-finance layer, not here — but they are a real career-path join for a future
  cross-entity person layer.
- **Ogden City municipal filings sit in this same state tree** (`weber_2013
  Municipal_Ogden`, and the Wayback `documents/2016/*_ogden.pdf` set) — a direct
  acquisition lead for `ogden_city_council/campaign_finance/`, which currently has no
  county-channel material.
- **John Holloway Thompson** filed in 2018 for **Clerk/Auditor** and again in **2022**
  with the office line filled in as *"HOME OFFICE"* (`office_scope=unclear`). The
  `elections/` module shows a **JOHN H THOMPSON (DEM)** running for **County Commission
  Seat A in 2022** — consistent, but the FORM does not say so, so `office_stated` stays
  verbatim and the row stays `unclear`. Resolving it needs the ballot record, not a guess.

---

## 7. Structured layer — STATED TOTALS (2026-08-01) + the BORN-DIGITAL ITEMIZED LAYER (2026-08-02)

**What changed on 2026-08-01.** The `cf-vision-transcribe` pass predicted here was run
as a **cover-page office + stated-totals tranche**. OCR was never trusted for a number:
each filing's **summary page was rendered inside its own PDF** (`pdftoppm` at 200 dpi,
page selected from `filing_attribution.csv`) and **read visually**, except the five
born-digital Polimorphic e-filings whose totals were parsed straight from their
machine-readable text sidecars. Result:

```
vision/<key>.json    CURATED — 98 caches, one per county-office filing, per-field
                     confidence, verbatim last/this/cumulative cells, transcription
                     stamp "vision-transcribed(claude-opus-5; 2026-08-01 totals tranche)"
filing_totals.csv    DERIVED — 98 rows (SCHEMA.md §4 column contract, + filing_regime)
contributions.csv    DERIVED — HEADER ONLY (§2 contract)
expenditures.csv     DERIVED — HEADER ONLY (§3 contract)
build_finance.py     the module-local builder (idempotent; re-verifies every sha256)
```

- **93 of 98 filings were vision-read; 5 were text-read** (born-digital).
- **98/98 carry a stated cumulative contribution total; 97/98 a stated expenditure
  total; 88/98 a stated cumulative ending balance.** The gaps are honest, not missing
  work — see "blanks" below.
- `python3 scripts/campaign_finance/validate_finance.py weber_county/campaign_finance`
  → **PASS (0 fails, 25 warns)**; every warn is an index row with no filing_totals row,
  i.e. a school-board / `unclear` / state-duplicate document — all out of scope.

**Three printed form variants, plus a fourth born-digital one** (the cache records
which, in `form_variant`):

| variant | cycles | summary lines |
|---|---|---|
| **4-line** | 2012, 2014 | contributions >$50 · aggregate ≤$50 (+ number of contributors) · expenditures · ending balance |
| **3-line** | 2016 – 2024 | contributions from ALL donors · expenditures · ending balance |
| **2026 redesign** | 2026 | same three lines in a boxed "Campaign Financial Summary", plus a **seven**-item Filing Schedule (Convention / May 26 / June 16 / Oct 6 / Oct 27 / Dec 3 / 30-days-after) |
| **Polimorphic e-filing** | 2026 (5 filings) | labelled fields, fully machine-readable |

The cache's `form_variant` records the **summary SHAPE**, so it takes only two values —
`4line` (26 filings: 2012 + 2014) and `3line` (72: 2016-2024, the 2026 redesign and the
five Polimorphic e-filings, which all print the same three summary lines). The printed
layout/report-type differences between those three later forms are described per row in
`filing_totals.notes`.

`stated_total_contributions` is the **cumulative** column: on the 4-line form it is
line 1 + line 2 summed over **only the cells the filer printed**; on every later form it
is the single all-donors line.

**The blanks, and why each one is honest:**

- **10 filings: `stated_ending_balance` blank** — the filer wrote the nil marker `-`.
  A dash is not a transcribed zero (cardinal rule 1). The verbatim `-` is in the cache.
- **1 filing: `stated_total_expenditures` blank** — Sharon Arrington Bolos'
  2026-03-31 report prints the cumulative expenditure as **`13.742.18`**, a period
  where the thousands comma belongs. Not repaired; the verbatim string is in the cache.
- **1 filing: `stated_ending_balance` blank at LOW confidence** — Corey Combe (2012)
  wrote a balance that reads as either **4,287.87 or 4,957.87** and did not resolve at
  900 dpi (the scan is bilevel). Left blank rather than guessed; the note records both
  readings and that the form's own arithmetic would give 4,957.87.
- **11 filings: `reporting_period` blank** — no report-type box is marked on the form.
  On four 2026 Bolos filings the checkbox column itself was dropped by the scan/flatten,
  which is why the honest reading is "no box marked".
- **1 filing: `filing_date` blank** — James Ebert's 2026 post-elimination report has a
  genuinely empty date box (it is signed).
- **1 filing: `office` blank** — Richard Hyer's 2026 convention report has its
  *Name of Office* line **inside the county's own redaction bar**. That is an
  over-redaction by the publisher, preserved (PRIVACY.md), not an unread value.
  (`index.csv` shows **3** county rows with a blank `office_stated`; the tranche read
  the office off the form for two of them — both Sharon Arrington Bolos 2026 filings,
  where the office IS written on the page — leaving this one genuinely blank.)
- **29 filings: `stated_beginning_balance` blank** — the "Totals from Last Report"
  column is empty or `-` on a candidate's FIRST report of a cycle. Expected, not a gap.

Confidence over the 98 rows: **92 high · 5 medium · 1 low.**

### 7a. The BORN-DIGITAL itemized layer — 3 of 98 filings (built 2026-08-02)

The `weber_polimorphic` family predicted below was registered in the shared library
(TRANCHE 3 Phase A) and is now wired into `build_finance.py`. **Measured coverage:**

| | filings | contribution rows | expenditure rows |
|---|---|---|---|
| **born-digital, itemized + reconciled** | **3 of 98** | **16** | **11** |
| born-digital, totals-only (nothing emitted) | 2 | 0 | 0 |
| handwritten scans — NOT transcribed | 93 | 0 | 0 |

- The three that ship are exactly the three this section predicted would reconcile:
  **Gary C New** 13.72 + 931.39 + 55.08 = **1,000.19** (3 rows each side), **Jon Beesley**
  7 rows = **1,120.00** / 2 rows = **867.92**, **Michelle Tait** 6 + 6 rows = **1,973.10**
  each side. Every side reconciles to the cent against the total already published in
  `filing_totals.csv`; **no stated total moved.**
- **100% geometry coverage** — every emitted row carries `geometry`
  (`p<page>:l<line>:c<col0>-<col1>`, SCHEMA.md §2a) pointing at the amount cell it was
  read from, so a mis-columned read is auditable without reopening the PDF.
- **Parsed from the RAW PDF** (`pdftotext -layout`), never from `text/` — those sidecars
  are `format=mixed` (part native text, part tesseract OCR) and a dollar figure must
  never come off an OCR layer. Born-digital detection is by DOCUMENT CONTENT (the
  Polimorphic footer + the "Total Contributions on This Report" summary line), never by
  filename or portal label.
- **Privacy:** the form prints `Donor's City` / `Recipient's Location` only, so rows carry
  `donor_city` / `donor_state` and nothing finer. No street address exists to discard.
- **Two born-digital filings emit NOTHING, each for a stated reason** (both recorded in
  `filing_totals.notes`):
  - **Ryan Arbon** (`39510beb`) — the filer answered **"No"** to both *do you have
    contributions/expenditures to disclose*, yet the summary states **879.97** on both
    sides. The document itemizes nothing, so reconciliation is **UNKNOWN**; the internal
    inconsistency is recorded verbatim, never resolved.
  - **Chris Allred** (`443f5c0e`) — a **FAMILY LIMITATION, documented not patched.**
    The filing prints one contribution and one expenditure (both **1,147.66**, matching
    the stated totals exactly), but Polimorphic **omits the `Itemized Contribution
    Report (#n)` block header when a filing has a single entry**, and `weber_polimorphic`
    slices records on that header only — so the family returns no row. The shared engine
    is frozen this phase, so the rows are **gated out** rather than hand-built. Queued
    for Phase B along with a one-line family fix.
- **The other 93 filings are unchanged**, byte for byte, in every column: their itemized
  layer is still **not transcribed** (handwritten Form A/B schedules behind a
  vision-read cover), which is why their `reconciles_*` stay **blank (unknown)** and
  never `False`. An empty itemized layer here has never meant *no donors*.
- `python3 scripts/campaign_finance/validate_finance.py weber_county/campaign_finance`
  → **PASS (0 fails, 25 warns)** — the same 25 out-of-scope warns as before.
- One schema note: the shared validator keys itemized rows on an index `election_year`,
  while this module's own column is `election_cycle`. `build_index.py` now writes a
  **trailing derived alias `election_year`** carrying the identical value; `election_cycle`
  remains the authoritative name here.

**Filing dates the tranche RECOVERED but did not write back.** All **24 `needs_review=1`
county rows** (every one of them 2026) carry a blank `date` in `index.csv` /
`filing_attribution.csv`, because `build_index.py` could not read a handwritten or
boxed date. The vision pass **read a date off the form face for 23 of the 24** — the
24th (James Ebert's post-elimination report) has a genuinely empty date box. Examples:
Thurgood 3/25/26, Kearsley 5/26/2026, Gibson 4/3/2026, Hyer 5-22-2026, Bolos
"31 March 2026". Those values are recorded in each `vision/<key>.json`
(`filing_date_stated`) and flow into `filing_totals.filing_date` with a note; the
CURATED `filing_attribution.csv` was **deliberately left untouched** — promoting them
is an attribution-layer decision for the coordinator, not this tranche's to make.

---

## 8. Refresh notes

- The 2026 cycle is **live** — the page showed 5 candidates *"Awaiting final report"* on
  2026-08-01, and the **2026 consolidated archive PDF does not exist yet** (the pattern is
  that the county posts a `<year> Reports` combo after the cycle closes). Re-probe
  `https://www.weberelections.gov/financialdisclosures` after the November 2026 general.
- Re-fetch: `python3 fetch_cf.py --batch batch/<name>.tsv --out raw/<channel>
  --referer https://www.weberelections.gov/financialdisclosures [--use-curl]`;
  then `python3 backfill_text.py` and `python3 build_index.py`.
- **New filings need attribution added to `filing_attribution.csv`** (read from the
  document, never from the portal label) — `build_index.py` will otherwise emit a
  `filing_grain=document` row with `needs_review=1`, which is the intended loud default.

---

## 9. The itemization wave — RESUMED AND AUDITED 2026-08-17 (Tranche 3 Phase B, weber wave B2)

> **SUPERSEDED 2026-08-18 — the queue is now CLOSED (93 of 93 scans; 98 of 98 filings) and
> the 18 withdrawn geometry frames have been RE-MEASURED and proved (100% coverage).** This
> dated section is left VERBATIM as the record of the resume leg; where it and the close-out
> disagree, the close-out governs. Read
> **"The SCAN itemization wave — QUEUE CLOSED 2026-08-18"** at the end of this file.

**Status: SUBSTANTIALLY COMPLETE, NOT CLOSED.** **83 of the 93** scanned county-office
filings now carry a real donor/vendor layer or a reasoned statement of why no schedule
exists — **1,155 contribution + 1,153 expenditure rows**, $946,796.20 and $816,787.73
itemized. **10 filings remain untranscribed** and are named below. Together with the
born-digital slice (now 4 filings after the `weber_polimorphic` single-entry family fix)
the module publishes **1,172 contribution and 1,165 expenditure rows over 87 of 98 filings**.

This section records the RESUME leg. The wave was authorized on 2026-08-14 (calibration
pre-flight **13/13 PASS**, `_audits/cf-calibration-suite/runs.md`), killed three times that
day, and resumed on 2026-08-17 under the same configuration — which was therefore **not
re-run**, the configuration being unchanged.

### 9a. The state audit came first, and it pulled work back out

The 2026-08-14 legs had already **published** 345 contribution rows into `contributions.csv`.
Nothing survived because it was already published. Every staged record was re-screened:

| gate | result |
|---|---|
| `checkrec.py` (key ↔ index, side states, amounts parse, geometry resolves) | **67 of 67 records OK** |
| reconciliation verdict **independently re-derived** from the rows + the 2026-08-01 stated cells | **132 of 134 sides agreed**; the 2 disagreements were both one filing, and the filing was right — see 9b |
| blind render-back: resolve a stored row's `pct:` box to a fresh crop and READ it | **18 records failed** — see 9c |

**Two filings were re-read independently and agreed exactly.** James H. Harvey's 2016-10-31
report exists on two channels (`raw/wayback/wb20190828041319_harvey_commission.pdf` and pages
14–21 of the 2016 archive). Two agents transcribed them separately, hours apart, without
knowledge of each other: **all 60 donor rows and all 101 vendor rows agree on name and
amount**, differing only in internal whitespace. That is the strongest evidence in this module
that the transcription tier is sound.

### 9b. Two cover-tranche corrections the itemization forced

Both went through `apply_totals_corrections.py`, which is the only sanctioned path to a
published figure, and both are decided by primary evidence, never by a glyph preference.

- **Corey Combe 2012 (`6803c289`)** — `stated_total_contributions` 24,792.52 → **24,292.52**
  and the blank `stated_ending_balance` → **4,287.87**. Schedule A page 2's own printed
  *TOTAL CONTRIBUTIONS RECEIVED* line reads **24,122.52** (verified at the page on
  2026-08-17), the filer's summary adds the 170.00 sub-$50 aggregate to reach 24,292.52, and
  the cover's own balance line closes exactly at 4,287.87. Under the 2026-08-01 reading
  (24,622.52) none of the three identities closes.
- **Katrina C. Gibson 2026 — a SWAPPED PAIR (`76c91f61` ⇄ `8a163a02`).** The 2026-08-01
  totals tranche transcribed these two filings' covers **into each other's cache**. Page 1 of
  each retained PDF was re-rendered on 2026-08-17 (sha256 of both re-verified against
  `index.csv` first — both MATCH, so the bytes never moved): `…fd9d0787.pdf` prints the
  **June 16 – Primary Election** box with 66,670.65 / 21,550.00 / 88,220.65, while
  `…d8532285.pdf` prints the **30-days-after-elimination** box with 88,220.65 / 4,168.61 /
  92,389.26. Each cover closes internally and the pair chains (the later report's Last-Report
  column IS the earlier one's Cumulative), so both readings were correct figures filed under
  each other's key. The verbatim cells were exchanged; nothing was recomputed. Gibson's third
  2026 primary-window filing (`32f407e4`, signed 6/16/2026) was read correctly in 2026-08-01
  and is untouched.

**Nothing else in the cover tranche moved.** `checkpoint_weber.py` asserts that on every run:
ten frozen columns, the pre-existing born-digital block, and the rule that the set of
`filing_totals` rows which changed is exactly (filings with an itemized layer) ∪ (the three
declared corrections) ∪ (the one declared born-digital addition).

### 9c. GEOMETRY: what the render-back audit found, and what was withheld

The B2 contract stores a `pct:x,y,w,h@p<page>` box per row, pointing at the **amount cell**
the figure was read from. The resume leg tested that claim instead of trusting it: for a
sample row of every itemized filing, the stored box was cropped out of the retained PDF and
read. A tesseract sweep of the amount-column band on the machine-readable pages ran the same
test at zero vision cost across 470 rows.

**On 18 filings the box did not reproduce the recorded amount.** The frame's Amount-column
band had been set to a middle column (the donor name, the street address, the city), or the
row band list still contained the header/shaded spacer band so every row pointed one row
early, or both. The values on those filings are not in question — every side still closes on
a figure the filing itself prints — but a measurement that is wrong is not published in a
weaker form. **`geometry` is BLANK on those 18 filings' 291/275 rows**, each carrying a
`geometry_provenance` that says the measurement was withdrawn and why, and the reason travels
into `filing_totals.notes`. Re-measurement is a cheap follow-up pass that re-reads no values.

**881 contribution and 890 expenditure rows across the other 65 filings keep a measured
pointer that was verified by rendering it back.**

**Four filings failed the first render-back and were CLEARED on re-test — the audit tool was
wrong, not the record.** `scripts/campaign_finance/make_snippet.py` resolves a `pct:` box
against the **unrotated MediaBox** that `pdfinfo` reports, while `pdftoppm` renders the page
**with `/Rotate` applied**; on a `/Rotate 90|270` page its crop therefore lands somewhere else
entirely. Two chunk agents found this independently on 2026-08-17 and neither patched the
shared frozen script. Re-cropped against the RENDERED raster — which is the frame the B2
contract stores geometry in — all eight sampled boxes on `14230ff0`, `4dedb81d`, `8b392841`
and `1b428642` reproduce their recorded amounts exactly. Every withdrawal that stands is on a
`/Rotate 0` page, where the tool is sound and the crop returned real content from the WRONG
column. **Any stored geometry elsewhere in the repo that was "proved" with `make_snippet` on a
rotated page is unproved** — that is a filed lead, not a weber finding.

Two mechanical facts that caused the defect, recorded so the re-measure pass does not repeat
them: `rowbands.py` on a TYPED Weber sheet registers each row's text baseline as well as the
printed rule, so the real grid is every other detected rule; and it returns the header band
and the hatched spacer band the form prints beneath it, which must be trimmed before the row
list is index-aligned. A third fact bit the AUDIT rather than the wave: the 2026
per-candidate scans hold a page-size image, so a `make_snippet --dpi 900` crop is a ~12×
upsample and returns **blank** — crops on those filings must be taken at ~200 dpi, and a
blank crop there is an artefact, not a defect.

### 9d. Reconciliation — per SIDE (166 sides across 83 filings)

| state | contributions | expenditures |
|---|---|---|
| **exact** — rows close on the schedule's printed total AND the cover's CUMULATIVE cell | **27** | **29** |
| **period-exact** — rows close on the cover's *Totals For This Report* cell | **33** | **31** |
| **delta** — rows and the printed anchor disagree, cause traced on the page | 6 | 8 |
| **empty-schedule** — the page exists and the filer entered nothing | 13 | 10 |
| **no-schedule-page** — the retained document has no such page at all | 4 | 5 |

**120 of 134 transcribed sides reconcile EXACTLY** to a figure the document itself prints.
Not one figure was nudged. `empty-schedule` and `no-schedule-page` remain different facts and
are stored differently.

### 9e. The reconciliation-basis rule (owner-ratified 2026-08-17) and what changed here

> Reconcile each itemized side against the printed cover figure that MATCHES ITS OWN SCOPE —
> the *This Report* column for a period-scoped ledger, the *Cumulative* column for a
> cumulative one. **Never synthesize a figure by differencing covers.** Withhold only where
> neither printed figure closes.

Weber's module already worked this way — `period-exact` is exactly that rule, and the build
verifies the claim mechanically against the cache's own *This Report* cell. **One thing
diverged and was corrected:** a verified period-scoped side used to leave
`reconciles_*`/`recon_delta_*` BLANK, which under-reported a real reconciliation as an
unknown. Those sides now publish `reconciles_*=True` with `recon_delta_*` stated **against
the period anchor**, every row carries `is_incremental=True`, and the note carries the
literal marker `ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)` that
`scripts/campaign_finance/validate_finance.py` check 6 requires as its declared exception.
`stated_*` remains the CUMULATIVE column, is never recomputed, and is never differenced.
32 contribution and 31 expenditure sides carry that declaration.

Where the build CANNOT verify a period claim it still publishes nothing: one filing (James H.
"Jim" Harvey 2024) closes on Form A's own printed 24,300.00 while the cover's line-1
This-Report cell was left blank by the 2026-08-01 tranche as unresolvable between 24,300 and
24,000 — the rows ship, the verdict stays an honest unknown, and the note says so.

**In-kind is per FILER, not a form property.** Tested both conventions on every side that did
not close first time. Sharon Arrington Bolos 2026 closes only WITH in-kind (10,500.00 fails,
11,120.00 closes); Katrina Gibson books one in-kind item on both schedules and both printed
totals require it. Nothing was assumed from cycle or form family.

**Accounting parentheses are a filer's presentation, not a sign.** Steven Van Wagoner writes
every expenditure cell as `(32,960.17)` across all four of his filings, and his Form B prints
a leading minus on every row. `stated_*` keeps the parsed **signed** value verbatim; the
period check closes the rows against the cell's **magnitude** and the note says so.

### 9f. The 10 filings that remain

Not started — the wave was stopped by wall-clock, not by anything the documents did. No
partial record exists for any of them; each has its cover-page stated totals as before and an
honestly empty itemized layer.

| key | candidate | cycle | source |
|---|---|---|---|
| `1cb41e87` | James Ebert | 2026 | `raw/y2026/2026_ugd_92078f_f7ac73e5.pdf` |
| `1f6d253e` | Caitlin K. Gochnour | 2016 | `raw/wayback/wb20160824043243_16June_Gochnour_Commission.pdf` (11 pp) |
| `44a69eb1` | John E. Ulibarri II | 2014 | `raw/wayback/wb20160824043328_Ulibarri_financials.pdf` |
| `48dde135` | Brian Rowley | 2024 | 2024 archive pp125–127 |
| `611f381e` | James Ebert | 2014 | `raw/wayback/wb20160824055040_Ebert_financials.pdf` |
| `7a142d87` | James H. "Jim" Harvey | 2024 | 2024 archive pp141–143 |
| `965feb98` | John Ulibarri | 2024 | 2024 archive pp147–149 |
| `a4ef7bda` | Leann Kilts | 2014 | `raw/wayback/wb20160824031533_Kilts_financials.pdf` |
| `aaf819ad` | John B. Bond | 2020 | 2020 archive p18 (single page) |
| `bc70d022` | Caitlin K. Gochnour | 2016 | `raw/wayback/wb20160824045455_16July_Gochnour_Commission.pdf` |

Three of these (`44a69eb1`, `611f381e`, `a4ef7bda`) had a 2026-08-14 record that was
**WITHDRAWN** on 2026-08-17 for the geometry defects in §9c and requeued for an independent
re-read that did not get reached. (The fourth withdrawn record, Chris Allred 2014
`b687614d`, WAS re-read: the fresh read found Form B on p2 and Form A on p3 and both sides
exact at 4,067.20, and its rows are published.) Their withdrawn records are retained, unused,
at `_backups/2026-08-14-weber-cf/quarantine-2026-08-17/` — they are evidence for the
re-read to diff against, **not** a data source.

### 9g. Provenance and rebuild

Every itemized row is stamped
`vision-itemized / itemized-vision(claude-opus-5; 2026-08-14 wave B2 weber)` and capped at
**`medium`** confidence (SCHEMA.md §6 reserves `high` for a born-digital source). Rows live
in each filing's `vision/<key>.json` under `_meta.itemized`, written **only** by
`make_itemized_caches.py` from the durable records in `_itemized_records/`. The chain is
idempotent — re-materializing and rebuilding twice reproduces `contributions.csv`,
`expenditures.csv` and `filing_totals.csv` byte for byte.

```
python3 apply_totals_corrections.py      # curated, evidence-cited cover corrections
python3 withdraw_geometry.py             # the 18 filings whose pointer failed render-back
python3 make_itemized_caches.py _itemized_records
python3 build_finance.py
python3 ../../scripts/campaign_finance/validate_finance.py .        # PASS (0 fails, 25 warns)
python3 ../../_backups/2026-08-14-weber-cf/workdir/checkpoint_weber.py
```

`python3 scripts/validate_entity.py weber_county` → **13 PASS / 1 WARN / 0 FAIL**, the WARN
being the pre-existing land_use duplicate-date note, unchanged by this wave.

---

## The SCAN itemization wave — QUEUE CLOSED 2026-08-18 (Tranche 3 Phase B, weber wave B2)

The wave authorized on 2026-08-14 and resumed on 2026-08-17 was **finished on 2026-08-18**.
**All 93 scanned county-office filings now carry an itemized layer**, so with the 5
born-digital filings **98 of 98 Weber county-office filings are itemized**. Nothing remains
in the queue: the ten filings §9f named are transcribed, and the eighteen filings whose
measured pointer §9c withdrew have been **re-measured and proved**, so the module's
`geometry` column is now **100% populated with no withdrawals**.

**Configuration:** unchanged from the 2026-08-14 pre-flight (`claude-opus-5`, Read-tool
vision at 200 dpi full page, tight-crop escalation, `$0` API). The calibration suite was
therefore **NOT re-run** — the recorded pre-flight for this configuration is
`_audits/cf-calibration-suite/runs.md` §2026-08-14, **13/13 PASS**, and re-running an
unchanged configuration would measure nothing. Fan-out: **3 concurrent chunk agents** per
lane (transcription, then geometry), plus the coordinator's own build, audit and invariant
passes.

### The shared crop tool was repaired FIRST, because both lanes depend on it

`scripts/campaign_finance/make_snippet.py` sized its crop from the page size `pdfinfo`
reports — the **UNROTATED MediaBox** — while `pdftoppm` renders the page **with `/Rotate`
applied**. On a `/Rotate 90|270` page the axes are swapped and the crop lands somewhere
else entirely. That defect nearly cost four good weber records on 2026-08-17 (§9c) and it
made every rotated-page geometry claim in the repo unproved. It is now **FIXED**:
`page_size_pts()` returns the page **as poppler renders it**.

The fix is one change serving three call paths, because `pdftotext -bbox` — which the
`p<page>:l<line>:c<c0>-<c1>` span vocabulary resolves against — also emits WORD coordinates
in the rotated frame while keeping an unrotated `<page>` header. Measured on a `/Rotate 90`
specimen: a word at unrotated y-top 74.77–96.97 pts on a 612×792 page reports xMin/xMax
**695.03/717.23** — i.e. `792 − y_top`, a value that exceeds the page width pdfinfo reports.

| proof | before | after |
|---|---|---|
| rotated specimen `2026_ugd_92078f_741f163c.pdf` p2 (`/Rotate 270`), row "James Ebert", recorded **53,000.00**, geometry `pct:85.23,16.62,10.66,3.17@p2` | crop rendered the **address column** ("Ogden … 84403") | crop renders **`$53,000.00`** |
| all **65** published rows sitting on a rotated page, OCR render-back | **0 of 65** reproduced the recorded amount | **54 of 65** (the residual are OCR failures on a tight cell — the 53,000.00 row is one of them and was confirmed by eye) |
| span vocabulary on a synthetic `/Rotate 90` page | region `pct:113.57,…` — **off the page**, x > 100% | `pct:87.76,8.17,2.80,12.86`, matching the hand-computed rendered-frame box exactly |
| **`/Rotate 0` regression control** — 40 published rows × value+row modes | — | **80 of 80 renders byte-identical**, region strings identical |

A **second, independent defect** in the same tool was also fixed. `pdftoppm` crops a window
out of a page it still rasterizes WHOLE, so the ceiling is set by the page: poppler's splash
bitmap allocates `3 × width × height` bytes and guards that against int32. Past it, poppler
prints *"Bogus memory allocation size"* to stderr, **exits 0, and writes an all-white PNG** —
a silent blank that reads as evidence of absence. It bites oversized-MediaBox pages, where a
scan is placed at roughly one point per source pixel: weber's `2026_ugd_92078f_f36d6ca9.pdf`
is **2310 × 3012 pts**, so `--dpi 900` asks for a 28875 × 37650 raster and returned blank
(§9c recorded the symptom without the cause). The tool now clamps the dpi to what poppler can
render and **says so** (`dpi clamped 900 -> 693: … the region is unchanged, only its
resolution`); a letter page at 900 dpi is untouched. Same specimen, same region: **before —
blank (extrema 255,255); after — real content.** A stderr guard also refuses rather than
returning a blank if the condition ever arises another way.

The tool's interface and output format are unchanged, and no other county's stored geometry
was re-audited here — that remains separately filed work.

### Lane T — the ten filings §9f named

Each was a clean transcription (no partial record existed). Three of them —`44a69eb1`,
`611f381e`, `a4ef7bda` — had a WITHDRAWN 2026-08-14 record quarantined at
`_backups/2026-08-14-weber-cf/quarantine-2026-08-17/`; that material was treated as **diff
evidence only and never opened by the transcribing agents**. The pages were read fresh.

| key | candidate | cycle | sides | rows C/E | verdict and the printed figure that gated it |
|---|---|---|---|---|---|
| `1f6d253e` | Caitlin K. Gochnour | 2016 | both transcribed | 147 / 35 | expenditures **exact** on Form B's printed 32,769.16; contributions **delta +2,065.00**, traced to the filer's own two SUM ranges (see below) |
| `bc70d022` | Caitlin K. Gochnour | 2016 | both transcribed | 9 / 3 | both **period-exact** — 3,500.00 and 1,551.00, the cover's This-Report cells |
| `1cb41e87` | James Ebert | 2026 | both transcribed | 5 / 13 | both **period-exact** — 12,904.63 and 16,004.52 |
| `611f381e` | James Ebert | 2014 | both transcribed | 6 / 18 | both **exact** — 6,230.00 and 6,948.22 |
| `44a69eb1` | John E. Ulibarri II | 2014 | both transcribed | 6 / 6 | both **exact** at 1,892.08 (This-Report == Cumulative) |
| `a4ef7bda` | Leann Kilts | 2014 | both transcribed | 5 / 13 | both **period-exact** — 2,100.00 and 787.72 |
| `7a142d87` | James H. "Jim" Harvey | 2024 | both transcribed | 9 / 3 | both **period-exact** — 8,350.00 and 6,741.67 |
| `48dde135` | Brian Rowley | 2024 | contrib transcribed, expend **empty-schedule** | 1 / 0 | **exact** on Form A's printed 15.00 == the cover's Cumulative |
| `965feb98` | John Ulibarri | 2024 | both **empty-schedule** | 0 / 0 | both **exact at 0.00** on the schedules' own printed zero totals |
| `aaf819ad` | John B. Bond | 2020 | both **no-schedule-page** | 0 / 0 | no sum claimed — the filing is genuinely one page |

**188 contribution and 91 expenditure rows added. Nothing withheld.**

`aaf819ad` is the distinction §9d insists on, decided at the source rather than from its
0.00 cover: p18 is a cover only, and the page-range boundary was verified by reading its
neighbours — **p17 is the preceding filer's Form A** and **p19 is the next filer's cover**.
So the document contains no schedule page: `no-schedule-page` (non-existence), not
`empty-schedule` (a page the filer left blank). `965feb98` is the other case — both schedule
pages physically exist, are blank, and print their own zero totals.

**The Gochnour 2016 delta is the filer's SUM RANGE, and it is a new shape.** The precedents
in this corpus (§9d) are single-row omissions. Here p6's printed subtotal 4,450.00 falls
exactly 300.00 short of its 25 rows, and p7's printed 7,955.00 falls exactly 1,765.00 short
of its 26 — and 1,765.00 is precisely the sum of that sheet's **first thirteen rows**, which
are the ones the filer typed with the figure inline (`$100.00`) instead of in the split
cells. Rows 14–26 alone sum to 7,955.00. The grand total 32,162.25 is the sum of the filer's
seven subtotals, not of his rows. Retained verbatim; nothing nudged.

**Two source properties this corpus had not shown before.** Harvey's 2024 schedules print
**every date without a year** (12 of 12 rows: "10/30", "30 Oct."); kept verbatim and blanked
by the build with `needs_review=1` — **a year is never inferred from the report date**.
And Gochnour's `bc70d022` carries a **typed** malformed decimal, `In-Kind $1,327,00`,
confirmed at 900 dpi: the §6 whitelist covers only the HANDWRITTEN decimal comma, so the
amount is **blank with `needs_review=1`** and the glyph is preserved verbatim.

### IN-KIND IS PER FILER — confirmed on weber, and the builder now tests both conventions

`CHUNK_BRIEF.md` §6 states that weber's form counts in-kind toward the schedule total, and
the form does instruct that. **Gochnour's 2016 Form A does the opposite**, and the page
proves it: the seven monetary rows sum to **3,500.00**, exactly the schedule's printed total
and the cover's This-Report cell, while including the two in-kind rows gives 8,153.00, which
matches nothing printed anywhere on the document. That is the owner-ratified rule
(2026-08-17) confirmed on this county: **in-kind treatment is a property of the FILER, not
of the form.**

`build_finance.py` could only test one convention, so a correctly-transcribed filer using
the other one produced an unverifiable verdict. It now computes the monetary-only subtotal
as well and accepts it **as a fallback, only where the all-rows sum fails, and only on an
exact close**, naming the convention and both figures in `filing_totals.notes`. It admits
nothing that does not land on a printed figure. Effect, measured by running the old and new
builders over identical records: **one row of `filing_totals.csv` changed** — Gochnour
`bc70d022` gains `reconciles_contrib=True` / `recon_delta_contrib=0.00` — and
`contributions.csv` / `expenditures.csv` are byte-identical. `itemized_contrib_sum` still
reports **every row that shipped** (6,826.00), so a rollup that ignores the per-filer
convention will mis-add this filing, and the note says so in those words.

### Lane G — the 18 withdrawn geometry frames, re-measured and proved

Values were never in doubt and **were not re-read**: this pass re-measured a pointer. Each
agent wrote a patch to `_remeasure/<key>.json` and the coordinator applied them centrally
with `remeasure_geometry.py`, which by construction copies **only** the `frames` block onto
the record — it cannot touch an amount, a name, a date, a row index or a verdict.

**Result: 18 of 18 filings, 43 of 43 pages measured. Zero pages left unmeasurable, zero
withdrawals standing.** Every page was gated by the two-crop proof the contract requires —
the first and the last transcribed row cropped from the geometry about to be stored, at 900
dpi, each rendering the amount already recorded. Over 70 proof crops were read and every one
matched.

**What was actually wrong** — the withdrawn frames' failures were dominated by the
Amount-column band, not by row indexing:

- **A wrong `cell` column on nearly every page.** It held the donor *Address* or *Mailing
  Address* band, the *Name* / *Person or Organization* band, the *City* band, the *Date*
  band, or — on two pages — a 2.5-pct sliver between two text baselines that is not a column
  at all. ⚠ **This has a privacy dimension, not only an accuracy one:** on at least a dozen
  pages the published pointer aimed at the **donor street-address column**, which the
  transcription rules deliberately never carry (PRIVACY.md: city/state only). Withdrawing
  those pointers in §9c was the right call for a second reason nobody had named.
- **Leading-band trims that are per PAGE, not per filing, and not constant.** This corpus
  contains 2-band, 3-band and 4-band trims; a merged header+spacer band needing an
  interpolated rule; a page that prints a **wholly blank table row** below the grey spacer;
  and — on Kilts — a trim at the **high**-pct end, because that filing's printed rows run
  DESCENDING while its siblings run ascending. Deriving one page's frame from another's
  failed wherever it was tried.
- **Printed-line ordinal is not row ordinal.** Combe's p3 has a filer-skipped ruled line
  between rows 23 and 24; the blank band is omitted so `rows[N-1]` remains record row N.
  Proved with a third crop at row 26 rendering the distinctive 9,826.83.

**The `rowbands.py` defects the pass had to work around** are the ones already on the [DEBT]
queue, plus two new flavours worth the record: on the pre-2013 portrait forms the black
**"PLEASE NOTE" instruction box** is detected as a horizontal rule and heads the band list
(that, not a header row, mis-seated three of Combe's four pages); and at ~0.4° skew it can
fail to return the row grid **at all** (Kilts p3: one rule for a 26-row table). The method
that recovered every such page — worth folding into the tool — is to scan the rendered
raster for dark runs **restricted to the Amount column's own band on the other axis**, where
the printed grid survives even when text has destroyed it elsewhere; on Kilts p3 a deskew
sweep was needed first. One more caution the pass earned: **a `cell` band bounded on a
detected rule can still CLIP the value**, because a right-aligned figure overhangs the
interior rule — the band must run to the printed border, and only a render proves it.

### The coordinator's independent check on the re-measured frames

The agents' proofs are on the FIRST and LAST transcribed row of each page, which is exactly
where an off-by-one shows up. To test the middle of the band lists as well, the coordinator
took a **MIDDLE row from every one of the 18 re-measured filings**, cropped it from the newly
stored geometry at 500 dpi and read all eighteen: **18 of 18 rendered the recorded amount**
(326.21 · 39.50 · 809.76 · 1,000.00 · 552.22 · 9.63 · 250.00 · 723 · 1000 · 1,205.27 ·
585.00 · 500 · 500.00 · 1359.81 · 25.00 · 270 · 1000.00 · 300.00).

⚠ **A methodological warning for the next wave.** A zero-vision-cost tesseract sweep was run
over the same rows first and scored them almost entirely as "did not reproduce". It is
WRONG, and the 18 visual crops above are the control that proves it: these are handwritten
2012/2014 sheets, and tesseract on a tight handwritten cell returns noise, not a verdict.
The same tool scored the machine-printed corpus usefully (999 of 1,124 legible crops
reproduced across the rest of the module) and it scored the confirmed-good rotated-page
specimen `$53,000.00` as a failure. **An OCR render-back is a screen for TYPED sheets only;
on handwriting it must never be read as a negative** — the 2026-08-17 audit's own "87 of 133
unverifiable" line already said as much, and this leg confirms it quantitatively.

### Measured — the closed state

| | |
|---|---:|
| county-office filings | **98** |
| filings itemized | **98 of 98 — QUEUE CLOSED** (93 vision + 5 born-digital) |
| scanned filings itemized | **93 of 93** |
| still queued | **0** |
| rows published | **1,360 contributions · 1,256 expenditures = 2,616** |
| of which vision tier | 1,343 · 1,244 |
| rows carrying `geometry` | **2,616 of 2,616 (100%)** — 2,587 vision rows rule-measured, 29 born-digital span-anchored |
| geometry withdrawals standing | **0** (was 18 filings / 566 rows on 2026-08-17) |
| money in the vision rows | **$955,399.58 monetary contributions + $63,941.58 in-kind · $849,942.81 spent + $33,539.29 in-kind** |
| sides, all states | **186** across 93 filings |
| sides `transcribed` | **149** (74 contributions · 75 expenditures) |
| sides `empty-schedule` (page exists, filer entered nothing) | **26** |
| sides `no-schedule-page` (document has no such page) | **11** |
| sides **WITHHELD** | **0** |
| verdict `exact` (closes on the CUMULATIVE column) | **62** |
| verdict `period-exact` (closes on the This-Report column) | **72** |
| verdict `delta` (filer arithmetic, traced on the page) | **15** |
| **transcribed sides closing EXACTLY on a printed figure** | **134 of 149** |
| tight-crop escalations used | **416** |
| per-row confidence | **2,578 `medium` · 9 `low`** (SCHEMA.md §6 caps a page image at medium) |

**134 of 149 transcribed sides reconcile EXACTLY to a figure the document itself prints, and
not one figure was nudged.** `empty-schedule` and `no-schedule-page` remain different facts
and are stored differently. **Zero sides are withheld** — weber is the only county in this
tranche that finished with none.

### The period basis, and the one honest unknown

**71 sides publish on the PERIOD basis** — `reconciles_*=True` with `recon_delta_*` stated
against the cover's *Totals For This Report* cell, every row `is_incremental=True` (601
contribution + 432 expenditure rows), and the literal marker
`ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)` in `filing_totals.notes` that
`validate_finance.py` check 6 requires as its declared exception. On those rows
`itemized_*_sum` is ONE REPORTING PERIOD and sits far below `stated_total_*` **by design**;
comparing the two is a basis error, and the note names both figures. **No figure anywhere in
this module is derived by differencing two covers.**

The 72nd period claim stays an honest unknown and always has: James H. "Jim" Harvey's 2024
filing (`03f2e863`) closes on Form A's own printed 24,300.00, but the cover's line-1
This-Report cell was left blank by the 2026-08-01 tranche as unresolvable between 24,300 and
24,000. The rows ship; the build says it **could not verify** the claim; `reconciles_contrib`
stays blank rather than asserting either way. The build prints that disagreement as a WARN on
every run, which is the intended behaviour — it is a standing, visible unknown, not a defect.
One other standing WARN is the same kind of honesty: `eae67827` expenditures carry a
**$0.67** filer-arithmetic gap against the schedule anchor.

### Invariants proved on this leg

- **No `stated_*` cell moved.** The frozen half of all **98** `vision/<key>.json` caches
  (`stated`, `confidence`, `candidate_stated`, `office_stated`, `report_type_stated`,
  `filing_date_stated`, `notes`, `form_variant`, …) is **byte-identical, 98 of 98**, to the
  snapshot taken before this leg began. The three declared 2026-08-17 cover corrections
  (Combe 2012; the Gibson swapped pair) are unchanged and remain the only ones.
- **`checkpoint_weber.py` passes** — 93 filings itemized, 3 declared totals corrections, 1
  declared born-digital addition, the prior born-digital block intact, 10 frozen columns held,
  no filing shrinking against the high-water mark.
- **The geometry pass changed geometry and nothing else.** A digest over every published
  column EXCEPT `geometry`, taken before and after the re-measure, is **unchanged on both
  CSVs** (1,360 and 1,256 rows).
- **The rebuild is idempotent** — running `apply_totals_corrections.py` →
  `remeasure_geometry.py` → `make_itemized_caches.py` → `build_finance.py` twice reproduces
  `contributions.csv`, `expenditures.csv`, `filing_totals.csv` **and every `vision/` cache**
  byte for byte.
- `python3 scripts/campaign_finance/validate_finance.py .` → **PASS (0 fails, 25 warns)**,
  the same 25 out-of-scope school-board / `unclear` / state-duplicate index rows as before.
- `python3 scripts/validate_entity.py weber_county` → **13 PASS / 1 WARN / 0 FAIL**, equal to
  the pre-leg baseline; the WARN is the pre-existing land_use duplicate-date note and is
  untouched by this wave.

### Rebuild

```
python3 apply_totals_corrections.py      # curated, evidence-cited cover corrections
python3 remeasure_geometry.py            # the 2026-08-18 proved re-measurements
python3 make_itemized_caches.py _itemized_records
python3 build_finance.py
python3 ../../scripts/campaign_finance/validate_finance.py .        # PASS (0 fails, 25 warns)
python3 ../../_backups/2026-08-14-weber-cf/workdir/checkpoint_weber.py
```

`withdraw_geometry.py` is retained as the audit trail of the 2026-08-17 withdrawal and is
**no longer part of the chain**; each re-measured record keeps its superseded frame under
`frames_withdrawn` and a `geometry_remeasured` block carrying the date, the pages and the
agent's proof line.
