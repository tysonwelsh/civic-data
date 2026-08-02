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
  county-office filing, **98/98 with a stated cumulative contribution total**
  (see §7). Itemized donor/vendor rows remain deliberately untranscribed.

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
