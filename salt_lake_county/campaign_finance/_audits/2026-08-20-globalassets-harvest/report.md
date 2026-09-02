# SLCo campaign finance — the 2015–2021 paper slice, ACQUIRED (2026-08-20)

Harvest of the **130 paper-filed county-office PDFs** that sit on the Salt Lake County Clerk's
"Salt Lake County Offices" financial-disclosures page under the `saltlakecounty.gov/globalassets/…`
URL family. This closes the *acquirable* half of the 2015–2021 gap documented in `RECON.md`
channel (b). **Acquisition only — no donor data was transcribed.**

- Files: `raw/globalassets/` (130 PDFs + `_fetch_log.jsonl`)
- Index: 130 rows appended to `index.csv` with `source='globalassets'`
- Per-file characterisation (one row per PDF, with the basis of every derived field):
  `characterisation.csv` beside this report. **Extended 2026-08-20 (index-rebuild pass) with four
  columns** — `index_candidate` / `candidate_basis` and `index_filing_type` / `filing_type_basis`
  — so that EVERY document-derived index.csv field has an explicit, recorded source here. See
  the addendum at the foot of this report.

## 1. The inventory was re-verified against the live listing before fetching

The `_recon/2026-08-20-portal-probe/globalassets_inventory.csv` inventory is a prior agent's work
product, so it was re-derived from the live page rather than trusted.

Re-fetched `https://www.saltlakecounty.gov/clerk/elections/financial-disclosures/salt-lake-county-offices/`
(HTTP 200, 264,083 bytes) and re-parsed every anchor:

| measured on the live page, 2026-08-20 | count |
|---|---:|
| PDF anchors on the page | **690** |
| … `globalassets` anchors | **135** (→ **130** unique URLs) |
| … `slco.org/clerk/financialDisclosurePDF/` anchors | 555 (→ 547 unique) |
| any `globalassets` reference of any extension (JS/CSS/img included) | 133 → **130 PDFs** + 3 images |

**The inventory is exact: the live set and the inventory's 130 URLs are identical — zero
additions, zero omissions** (set difference empty in both directions). The 547 legacy URLs on the
same page all already appear in `raw/clerk_legacy/_fetch_log.jsonl`; overlap between the
globalassets set and the legacy set is **0**.

Nothing was missed and nothing was added. The probe agent's inventory stands.

## 2. Fetch

Sequential plain HTTPS GET, browser UA, same-site `Referer`, 1.0 s delay between requests,
one retry after 3 s on any non-200/zero-byte response.

| | |
|---|---:|
| URLs attempted | **130** |
| HTTP 200 with a non-empty body | **130** |
| failures / retries needed / zero-byte bodies | **0 / 0 / 0** |
| sha256 recomputed from disk and matched to the log | **130 / 130** |
| total bytes | 230,829,706 (~220 MB) |
| total pages | **717** |

`raw/globalassets/_fetch_log.jsonl` carries, per file: `url`, `http_status`, `bytes`, `sha256`,
`content_type`, `retrieved_utc`, `path`, the inventory's `candidate` / `office` / `listing_label` /
`folder_year` / `folder_period` / `filename`, `n_anchors`, and `additional_listing_labels`
(the second listing label where one URL is anchored twice).

**On-disk naming.** 130 unique URLs collapse to only **102 unique basenames** — 12 basenames are
reused across different folders for *different documents* (e.g. `sim-gill_redacted.pdf` exists at
five distinct URLs). Files are therefore stored under the URL path below `financial_disclosure/`
with `/` → `__` (e.g. `2016_disclosures__september__sim-gill_redacted.pdf`), which is unique by
construction. No file was overwritten. sha256 comparison confirms all 130 are **distinct
documents** — there are no byte-identical duplicates among them, and none duplicates anything
already in `index.csv` (0 sha256 collisions against the 989 existing rows).

## 3. Characterisation (not transcription)

Every one of the 130 PDFs was rendered and **its cover page read by vision**; 717 of 717 pages were
rendered, and for 99 filings at least one schedule page was read as well. Nothing beyond form
metadata was recorded — no donor names, no amounts, no addresses.

### Text layer

| | count |
|---|---:|
| **image-only** (`pdffonts` empty, `pdftotext` returns 0 characters) | **127** |
| carries a font layer | **3** |

The three: `2020_disclosures__june__staggs-mayor_redacted.pdf` (15,529 chars, Producer
`www.ilovepdf.com` — a genuinely born-digital typed contributor list), `julie-dole_redacted.pdf`
(1,451 chars) and `2018_disclosures__april__steve-debry.pdf` (1,164 chars); the latter two are
**Canon iR-ADV scanner OCR over a handwritten form** — the pre-printed labels extract, the filer's
figures do not. The `riverton` precedent applies: `format=text` in these rows means "has a font
layer", **not born-digital**. Only the Staggs file has machine-readable money.

### Form families present (from the printed title, not the folder)

| family | filings |
|---|---:|
| `<YEAR> Financial Disclosure Report For a Candidate` — 2016 | 28 |
| … 2018 | 29 |
| … 2020 | 18 |
| … 2017 | 14 |
| … 2015 | 11 |
| … 2019 | 8 |
| … 2021 | 4 |
| … 2014 | 1 |
| **`Financial Disclosure Report For a Candidate` — NO YEAR in the title** (older template; two header sub-variants: a plain clerk header, and a `SHERRIE SWENSEN` header with the footer `k://election/candidateinfo/financialdisclosures/04pccfindisc.doc`) | **13** |
| `2014 Financial Disclosure Report For County and Local School Board Candidates` (a different 2014 form: Column B is "Year to Date", interim boxes are dated April 7 / June 17 / Sept 15 / Oct 28) | 1 |
| `Dissolution of a Candidate Campaign Committee` / `Statement of Campaign Dissolution` notice | 2 |
| a bare `Schedule A/B` page with no cover | 1 |

**It is the same form the repo already transcribes.** Page 1 cover (candidate / Office / Office
Sought / District / Party / Type-of-Report checkboxes / amendment yes-no / signature + date / clerk
RECEIVED stamp), a `Summary Page` with Column A "Total this Period" and Column B "Aggregate Total"
lines 1–7, `Schedule A — Itemized Contributions Received`, `Schedule B — Itemized Expenditures
Made`, each with `SUBTOTAL FOR THIS PAGE` and a schedule grand total. The 2019–2021 vintages add
three trailing pages — `Summary Page Other Campaign Accounts` (Column B is "Year to Date" there,
a **different table**, per the existing `bf8a4533`/`ee4789b4` precedent) plus its two itemized
pages. The existing vision pipeline applies unchanged.

### Occupation/Employer — the new Schedule-A column

**The `Occupation/Employer` column is pre-printed on the county Schedule A of EVERY form vintage
in this corpus** — untitled-year, 2014 (both variants), 2015, 2016, 2017, 2018, 2019, 2020, 2021.
It is not an era-limited field; wherever a county Schedule A page exists in this slice, the column
exists.

| Schedule-A situation | filings |
|---|---:|
| county Schedule A grid **observed** (column present) | **86** |
| Schedule A page present but **not among the pages inspected** (column present by form design) | 31 |
| itemization is a **filer attachment**, and the attachment carries an occupation/employer-equivalent column | 3 |
| itemization is a **filer attachment with NO occupation/employer column** | 1 (`r.-fred-ross_redacted.pdf`) |
| **no Schedule A page exists** in the document | 9 |

So a transcription wave should expect the column on **117 of 130** filings (86 observed + 31
by form design), on 3 more in attachment form, absent on 1 attachment, and non-existent on 9.
Values are short free text ("RETIRED", "PAC", "BUSINESS OWNER", "LEGISLATOR", "realtors",
"self-employed", "unknown"). `scripts/campaign_finance/SCHEMA.md` has no home for it today —
capturing it is the owner-approved schema change, **not implemented here**.

### Partial filings that need pairing with a sibling — 3, and 2 of them have no sibling

1. **`2020_disclosures__september__burdick-fin-report-3.pdf` — a bare Schedule B page.** One page,
   no cover, no Summary Page; the page header names only "Burdick" and "Date of Report 9-15-20".
   Its sibling is `2020_disclosures__september__amendment-burdick-fin-report-9-15-20_redacted.pdf`
   (cover + Summary + Schedule A, also dated 9-15-20) — **pair on the 9-15-20 report date, not on
   the filename**, and note that the clerk lists the sibling as "Amendment to Sept 2020" while the
   form's amendment box is *not* checked.
2. **`2020_disclosures__april__alvord-financial-disclosures_redacted.pdf` — 3 of 4 pages.** The
   filer numbers his own report `Pg 1 of 4` (cover), `2 of 4` (Schedule A), `3 of 4` (Schedule B);
   the PDF holds exactly those three. **The Summary Page is missing from the county's scan.**
   Alvord has no other file in this corpus — an honest gap, not recoverable by pairing.
3. **`forms__staggs-dissolution_redacted.pdf` — a dissolution notice whose attachment is absent.**
   The one-page notice states "Attached is a final summary financial report"; no such report is in
   the PDF and no Staggs final report exists in this corpus (his only other file is the June-2020
   pre-primary). Honest gap.

Three further PDFs are the **opposite** case — extra documents bundled *in front of* the report, so
page 1 is not a cover (a real trap for any "page 1 = cover" wave):

- `2018_disclosures__september__guyman-adam-council-at-large-c1.pdf` — p1 is a **Statement of
  Organization for a Candidate** (9-12-18); the FDR cover is p2, its Summary p3.
- `jennywilson_dissolution_redacted.pdf` — p1 is a **Dissolution of a Candidate Campaign
  Committee** notice; the FDR cover is p2.
- `forms__jim-bradley_redacted_1.pdf` — p1 dissolution notice, **p2 is a near-blank ghost page**,
  the FDR cover is p3, Summary p4.

### Illegible or damaged

**None.** All 130 PDFs open cleanly (`pdfinfo` reports no xref or syntax errors on any file), and
every cover was legible enough to read the candidate and the checked report type. The two weakest
scans are `jensen-michael-2021ye.pdf` and `forms__snelgrove_redacted.pdf` — **photographed** pages
rather than scans, low contrast, but legible. This is a materially healthier corpus than
`raw/clerk_legacy/`, which holds six damaged/blank files.

Fields that are genuinely `undetermined` (recorded as such, never guessed):

| filing | undetermined | reason |
|---|---|---|
| `lisa-gehrke-redacted.pdf` | office, office sought, district, party | all four cells are **covered by the county redaction bar** |
| `2020_disclosures__september__burdick-fin-report-3.pdf` | office, report type, candidate first name | no cover page exists in the PDF |
| `2018_disclosures__september__guyman-adam-council-at-large-c1.pdf` | signature date | the filer left it blank; no clerk stamp on the FDR cover |
| `2016_disclosures__september__bradley-september-amendment-2018.pdf` | type of report | **no Type-of-Report box is checked at all** (only the amendment "Yes") |

## 4. index.csv

**130 rows appended**; `index.csv` goes 989 → **1,119** rows. The existing 989 rows are
**byte-identical** (asserted at write time: the new file's first N bytes equal the old file
exactly). Columns match the existing contract exactly, in order, with no additions.

How each column was derived, document-first:

- **`candidate`** — the form's own "Name of Candidate or Officeholder", verbatim (including the
  filer's own spelling and capitalisation: `GUYMAN` on the covers vs `Guymon` on the dissolution
  notice; `Samuel F.` / `Samuel Frank` / `Sam F.` Granato across four filings by one person).
  For the cover-less Schedule-B page it is the page-header last name, `Burdick`.
- **`office` / `seat`** — from the form's "Office Sought" (falling back to the "Office" cell where
  Office Sought is blank), normalised to the repo's 10 county offices. **126 of 130 are
  document-derived**; 4 fall back to the clerk listing and each says so in
  `characterisation.csv → office_basis`: Gehrke (redacted), Bradley 2019 YE (all office cells
  blank), the cover-less Burdick Schedule B, and Goodfellow (whose form names a **non-existent
  office, "COUNTY COMMISSION 2"** — Salt Lake County has had a Council since 2001).
- **`date`** — the form's signature/report date in ISO (**118 of 130**). Where that is blank,
  illegible or contradicted by the clerk's own RECEIVED stamp by more than ~60 days, the
  **RECEIVED stamp** is used (9) — the stamp is also printed on the document. One date comes from
  the **Summary Page** (Theodore Oct-2020: the cover's signature+date block is under the redaction
  bar) and one from a **Schedule B page header** (the cover-less Burdick). One is honestly blank
  (Guymon Sept-2018: unsigned, unstamped). `date_basis` in `characterisation.csv` names the source
  for every row.
- **`election_year`** — the repo's documented even-year proxy (`build_lib.election_year_from_date`)
  applied to that date. It is a proxy, not a cycle.
- **`reporting_period`** — the **form's own checked Type-of-Report label**, verbatim
  (`April 5`, `Seven days before a primary election`, `September 15`, `Seven days before a general
  election`, `Year-End (Jan 31)`, `Final / Dissolution Report`, and the co-checked combinations).
  The clerk's listing label is preserved in `title`, so the two are visible side by side in
  `index.csv` itself.
- **`filing_type`** — derived class from that box: `interim` 54 · `year-end` 55 · `final` 17 ·
  `''` 4 (2 dissolution notices, 1 no-box-checked amendment, 1 cover-less schedule page).
  The class is the form's OWN printed section heading above the checked box (`INTERIM REPORTS` /
  `YEAR-END REPORT` / `FINAL / DISSOLUTION REPORT`), not an inferred label; it is now executable
  as `build_lib.filing_type_from_report_boxes` and recorded per filing in
  `characterisation.csv → index_filing_type` / `filing_type_basis`.
- **`format` / `extraction_method`** — measured with `pdffonts`, exactly as `build_index.py` does.
- **`source='globalassets'`**, `document_id` blank (this channel has no id; a vision cache key will
  become the stable id when a transcription wave runs), `has_text='no'` (no `text/` sidecars
  written), `has_itemized='no'` (acquisition-time flag, per the existing caveat).

⚠ **CLOSED 2026-08-20.** This section originally read *"`build_index.py` does not know about
this channel … re-running it as written would delete these 130 rows"*. It does now:
`python3 build_index.py` regenerates all **1,119** rows with no manual step, reproducing every one
of these 130 rows byte-for-byte from `characterisation.csv` + `raw/globalassets/_fetch_log.jsonl`.
See the addendum.

## 5. What the documents say that the folder and the filename do not

`RECON.md`'s three shape warnings are all confirmed, and there are more.

**Folder years lie — confirmed, twice, exactly as warned.** Two 2018 documents are parked in
`2016_disclosures/september/`:
`bradley-september-amendment-2018.pdf` (RECEIVED OCT 05 2018) and
`evershed-amendment-09-2018.pdf` (RECEIVED OCT 05 2018).
A third case is a **filename**, not a folder, lie: `2014_disclosures/2014_year_end/mike_fife2014ye.pdf`
is signed **2016-02-12** and checks Year-End **and** Final/Dissolution — it is the 2015 year-end,
on a 2014-titled form, in a 2014 folder. (Two other folder/date offsets are legitimate: a year-end
report signed in January or an amendment received in March properly belongs to the prior year's
folder.)

**Form-title years lie too, and more often — 8 filings** print a title year that is not the report's
own period year, including a 2018-titled form used for an April-**2020** report (Alvord) and a
June-**2020** report (Preston), and a 2017-titled form used for the April-**2018** report (Gill).
The clerk simply reused stock. `cover.form_year` must never be read as the cycle.

**Clerk listing labels lie — 26 of 130 filings carry a listing/form disagreement**, always in the
same direction already documented for the clerk-legacy era: the listing calls a filing "Summary
Report", "October", "Dissolution" or "Amendment" where the form checks something else. Examples:
- eight filings listed "June …" whose form checks **Seven days before a primary election**;
- `2018_disclosures__2018_year_end__jim-bradley_redacted.pdf`, listed **both** as "October" and as
  "2018 Summary Report", is a **Year-End** report signed 1-29-2019 (same for the Sim Gill 2018 file);
- three listed "2015/2016 Summary Report" whose form checks **Final / Dissolution**;
- `2020_disclosures__september__amendment-burdick-…` is listed "Amendment to Sept 2020" and the
  form's amendment box is **not checked**.

**One listing anchor is simply wrong.** `steve-debry---redacted.pdf` is anchored twice, once under
"2019 Year End Report" and once under "2020 Year End Report". The form is signed **Jan. 26, 2020**
and stamped **RECEIVED JAN 28 2020** — it is the 2019 year-end. The 2020 anchor points at the wrong
document; DeBry's real 2020 year-end is not on this page. Four other URLs are also double-anchored
(Bradley, Snelgrove, Gill, Staggs) — **135 anchors are 130 documents**, so an anchor-driven wave
would double-count five filings.

**Other source properties worth carrying into a transcription wave:**

- **`_redacted` in the filename is unreliable in both directions.** 40 of 130 files lack the
  suffix, but several *with* it are unredacted and several *without* it are redacted. Two filings
  print **contributor mailing addresses in the clear** on Schedule A
  (`2016_disclosures__april__ben-mcadams_april.pdf`, `2015_…__jim_bradley2015ye.pdf`), and
  `kenneth-hansen_redacted.pdf` prints an organization's street address. Candidate phone numbers
  and campaign emails also survive on several covers. **The wave's "discard the address at read
  time" rule is load-bearing here** — unlike the EasyVote era, the county's black bar cannot be
  relied on to do the work. Where a bar *is* present it covers only the address column, never a
  name, date, occupation or amount.
- **Two report-type boxes are frequently checked together** — Year-End **and** Final/Dissolution on
  the same form (Dole, Hansen, Hughes, Fife, Recanzone, Evershed 2018, Bradley 2020, Amann). Both
  are recorded verbatim in `reporting_period`; `filing_type` resolves to `final`.
- **Filer year-typos in the signature date, contradicted by the clerk stamp** — Bradley 2017 YE
  signed "1-27-17" but RECEIVED JAN 29 2018; Hansen signed "01-29-2017" but RECEIVED JAN 30 2018.
  Kept verbatim in `characterisation.csv → doc_signature_date_verbatim`, with `date` taken from
  the stamp.
- **A received-before-signed pair**: Bradley's April 2018 report is stamped RECEIVED APR 02 2018 and
  signed 4-3-18.
- **One filing is signed by someone other than the candidate**: `2018_…__sam-granato_redacted.pdf`
  has "N/A" on the signature line and, handwritten on the cover, *"DECEASED — Leslie Reberg,
  Committee Secretary on His Behalf."*
- **Struck-through and rewritten figures on Summary Pages** (Bradley Sept-2018 amendment; Bradley
  April-2018 Column B) — the clerk-legacy "retain both, never reconcile" rule applies unchanged.
- **A district number that is not a district**: `scott-miller---redacted.pdf` writes "52" in the
  District Number cell for a Recorder filing.
- **Page-numbering is filer-relative and inconsistent** — some filers number the cover as page 1,
  others start at the Summary Page, and many leave the `Page __ of __` box blank entirely. Where
  it *is* filled it is a genuine completeness gate (that is how the Alvord missing page was found),
  but it cannot be assumed present.
- **Schedule order varies**: Schedule B precedes Schedule A on at least one filing
  (`2020_disclosures__april__dekeyzer-…`), and page 2 is Schedule A rather than the Summary Page on
  `kenneth-hansen_redacted.pdf`.

## 6. Distribution as ACQUIRED (from the documents, not the folders)

Document-stated date year (the year of the form's own report/signature date, or the clerk stamp
where that is the basis):

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | blank |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 33 | 10 | 38 | 10 | 24 | 7 | 5 | 1 |

This differs materially from the probe's folder-derived spread (2015 15 · 2016 29 · 2017 16 ·
2018 34 · 2019 10 · 2020 23 · 2021 5 · 2014 2 · 1 unlabelled) — chiefly because **year-end reports
are signed in January or February of the following year**, so a "2015 folder" filing is dated 2016.
Under the repo's even-year `election_year` proxy the corpus is: **2014 ×2 · 2016 ×43 · 2018 ×48 ·
2020 ×31 · 2022 ×5 · blank ×1**.

Office, as read from the forms:

| office | filings |
|---|---:|
| County Council — District 6 | 25 |
| District Attorney | 19 |
| County Council — District 4 | 15 |
| County Council — At-Large C | 14 |
| Mayor | 13 |
| County Council — District 5 | 11 |
| County Council — At-Large B | 9 |
| Auditor | 5 |
| Recorder | 4 |
| County Council — At-Large A | 4 |
| County Council — District 2 | 3 |
| Sheriff | 3 |
| Clerk | 2 |
| Assessor | 1 |
| County Council — District 3 | 1 |
| Treasurer | 1 |

County Council 82 · the nine row offices 48. All ten county offices are represented except
Surveyor, which has no paper filing in this slice.

## 7. What is still owed

- **Stated totals and itemization for these 130** — none was transcribed here. They are the same
  form as the closed clerk-legacy tranche, image-only, with printed page subtotals and schedule
  grand totals, so the wave-B2 per-row contract
  (`_backups/2026-08-02-tranche3/slco-b2/AGENT_BRIEF.md`) applies unchanged. 717 pages total, a
  little over one-eighth of the wave-B2 page volume.
- ~~**`build_index.py` must learn the `globalassets` channel**~~ — DONE 2026-08-20 (addendum below).
- **The 251 online-filed reports remain GRAMA-only.** Acquiring this paper slice does **not**
  substitute: 34 of the 54 portal filers have no clerk-page PDF at all.
- **Two unrecoverable in-slice gaps**: Alvord's missing April-2020 Summary Page and the Staggs
  final summary report attached to his dissolution notice. Neither has a sibling in this corpus.


---

## Addendum — `build_index.py` learns the channel (2026-08-20, index-rebuild pass)

`python3 build_index.py` now regenerates **all 1,119 rows with no manual step**, and the 130
globalassets rows come out **byte-identical** to the harvest's own output
(`_backups/2026-08-20-slco-gate/index.csv.post-harvest`): same row order, zero differing cells.
Two consecutive runs produce identical bytes.

**What was missing, and where it now lives.** The harvest's derivations had to be recoverable from
the artifacts on disk, not from a finished agent's memory. Measured against
`characterisation.csv` as originally written:

| index.csv column | recoverable as written? |
|---|---|
| `date` / `office` / `seat` | yes — `index_date` / `index_office` / `index_seat` (130/130) |
| `candidate` | yes — `doc_candidate` matches **130/130** (`listing_candidate` matches only 68/130; that is the listing lying, not a missing derivation) |
| `reporting_period` | yes — `doc_report_type_boxes` verbatim (130/130) |
| `title` | yes — composed from the clerk listing's own `candidate` / `office` / `listing_label`, which the fetch log carries (130/130) |
| `election_year` | yes — `build_lib.election_year_from_date(index_date)` (130/130) |
| **`filing_type`** | **NO source column** — this was the one genuine hole |

**Four columns were added** so the DOCUMENT → INDEX ROW mapping is explicit and recorded rather
than implicit in a column-name coincidence:

- **`index_candidate`** — the exact string index.csv carries (equals `doc_candidate` on all 130;
  stated rather than inferred).
- **`candidate_basis`** — where that name was read: the FDR cover's *Name of Candidate or
  Officeholder* (127, three of them on a cover that is **not page 1**), the *Name of County Office
  Candidate* line of a Statement of Campaign Dissolution (2), or the *Candidate or Officeholder's
  Last Name* box in a schedule-page header (1 — the cover-less Burdick Schedule B).
- **`index_filing_type`** — the controlled-vocabulary class.
- **`filing_type_basis`** — the form heading(s) the class was read from, or the recorded reason it
  is blank.

**`filing_type` is derived, not stored-and-copied.** `build_lib.REPORT_TYPE_BOXES` encodes the
form's actual Type-of-Report block — four INTERIM boxes (April 5 / seven days before a primary /
September 15 / seven days before a general), one YEAR-END box, one FINAL / DISSOLUTION box, plus
the separate amendment question — and `filing_type_from_report_boxes()` maps each verbatim checked
label to its own printed section heading, with final/dissolution governing when two are ticked.
`build_index.py` derives the value and then **hard-fails** if it disagrees with the recorded
`index_filing_type`; an unrecognised box label raises rather than being silently classed. Rule and
record cannot drift apart, and the rule is the form's taxonomy rather than a string pattern that
happens to fit.

**Verified at the documents, not just against the strings** (the classes that a substring rule
would get wrong):

| document | page read | what the cover shows | class |
|---|---|---|---|
| `2020_…__dekeyzer-…-interim-4.5.20_redacted.pdf` | p1 | **April 5** ticked, signed 4/1/2020 | `interim` |
| `julie-dole_redacted.pdf` | p1 | **Year-End** ✗ **and** **Final / Dissolution** ✗, "amendment? No" ✗ | `final` |
| `2016_…__bradley-september-amendment-2018.pdf` | p1 | **no Type-of-Report box ticked at all**; only "amendment? Yes — 10-5-2018" | `''` |
| `2018_…__adam-guyman_redacted.pdf` | p1 | a **Statement of Campaign Dissolution** — the form has no Type-of-Report block | `''` |
| `2020_…__burdick-fin-report-3.pdf` | p1 | a bare **Schedule B** page; header names "Burdick", "Date of Report 9-15-20" | `''` |

Those five also confirm the two `''` mechanisms are genuinely different facts — *no box ticked on a
report form* versus *no such block exists on this document* — which is why the basis string records
which one applies, and why a keyword rule keying on "dissolution" would have mislabelled the
Guymon notice `final`.

**Unread documents.** A `raw/globalassets/` PDF with no `characterisation.csv` row is never indexed
off its filename: the build prints a `WARN … NO characterisation row — document unread, SKIPPED`
line, counts it, and leaves the row out. A missing `characterisation.csv` altogether is a FATAL,
not a silent drop of the channel. (Both paths exercised; the current corpus warns 0 times.)

**One fetch-log subtlety.** Four records carry `fetch_error: "HTTP Error 525"` from their FIRST
attempt yet completed on the retry (`http_status` 200, non-empty body, sha256 matched). The build
gates on the OUTCOME (status + bytes + the file on disk), not on that note; gating on `fetch_error`
would have dropped Dekeyzer's June-2020, both Ann Granato filings and DeBry's 2015 year-end.
