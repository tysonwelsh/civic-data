# campaign_finance/ — AVAILABILITY (Cache County, county offices)

Acquired **2026-08-01**; **vision transcription pass 2026-08-01/02** (office lines + stated
totals). Source-by-source log of what was checked, what each channel held, what was
retained, and what is honestly missing. Method + channel detail: `RECON.md`. Reading guide:
`CLAUDE.md`.

---

## 1. What was acquired

**495 filing PDFs retained** (198 MB), each with a text sidecar in `text/` and a provenance
row in `raw/_fetch_log.jsonl` (URL, HTTP status, byte count, **sha256**, fetch timestamp).
**171 of them additionally carry a vision transcription** in `vision/` — one per distinct
document, covering **213 ledger rows**.

| ledger | rows | meaning |
|---|---|---|
| `index.csv` | **239** | county-office filings (see the scope-status split below) |
| `excluded.csv` | **256** | acquired, then classified OUT of scope (school board 237 + water district 14 + municipal 2 + special district 2 + state legislature 1) |
| `unrecovered.csv` | **2** | listed on a county page, bytes not retrievable anywhere |

Cross-channel duplicates are **kept, not deleted** (the same filing served by the county
site, the state site and Wayback is three independent publications of one document) —
**42 index rows carry a `byte-identical duplicate of …` note** in `notes`; 82 index rows sit
in a duplicate group, and the 239 rows are **197 distinct documents**. De-duplicate at query
time with `GROUP BY sha256`.

### Coverage matrix — `index.csv` filings by office × election cycle

| office | 2008 | 2010 | 2012 | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| County Executive | · | 1 | · | 4 | · | 3 | · | 6 | · | 9 | **23** |
| County Council | 11 | 4 | 19 | 9 | 6 | 21 | 20 | 13 | 9 | 18 | **130** |
| Sheriff | · | 1 | · | 3 | · | 3 | · | 4 | · | 2 | **13** |
| County Attorney | · | 1 | · | 4 | · | 4 | · | 3 | 1 | 8 | **21** |
| Clerk/Auditor | · | 2 | · | 3 | · | 3 | · | 4 | 2 | 6 | **20** |
| Assessor | · | 1 | · | 2 | · | · | 3 | · | · | · | **6** |
| Recorder | · | 1 | · | 3 | · | · | 4 | · | 1 | · | **9** |
| Treasurer | · | 1 | · | 7 | · | · | 3 | · | 1 | · | **12** |
| *(office not established)* | · | · | · | · | · | · | 1 | · | 3 | 1 | **5** |
| **total** | **11** | **12** | **19** | **35** | **6** | **34** | **31** | **30** | **17** | **44** | **239** |

**The matrix cells are PUBLICATION facts, not fundraising facts** — a cell counts filings
published, and the same filing can appear twice via two channels. Group on `sha256` first.

**The handwriting floor is CLOSED.** Before the vision pass, 160 of 249 rows (64%) had no
readable office because Cache's pre-2022 form was completed in pen and OCR cannot read
handwriting. Rendering every page and reading it natively resolved all of them: the
`county_office_illegible` bucket is now **empty**, and only **5 rows (2%)** lack an office —
in every one of those the *filer* left the Office box blank.

`scope_status` (in `index.csv`) says exactly how much is known per row:

| `scope_status` | rows | means |
|---|---:|---|
| `county_confirmed` | **234** | an office is established by evidence (see the `office_basis` table in `CLAUDE.md`) |
| `undetermined` | **5** | the page image WAS read and the office line is genuinely blank on the document |

By source channel: county site 155 · state disclosures 46 · Wayback 38.
By text quality: 89 born-digital (`format=text`), 150 OCR'd scans (`format=scanned`).
**142 distinct named filers.**

### The money layer

**Each filing's own printed STATED TOTALS are transcribed; the 2022+ BORN-DIGITAL subset is
now ITEMIZED as well (2026-08-02).**

| | rows |
|---|---:|
| `filing_totals.csv` rows | 239 |
| …carrying a stated **contributions** figure | **210** |
| …carrying a stated **expenditures** figure | **212** |
| …carrying a stated ending balance | 202 |
| …carrying a stated beginning balance | 83 |
| …with **no** stated totals at all | **1** (the orphan Form-B page) |
| `contributions.csv` rows | **32** (born-digital only) |
| `expenditures.csv` rows | **111** (born-digital only) |
| …filings carrying itemized rows | **21 of 239** |

Totals source: vision transcription 202 · born-digital text parse 37.
Extraction confidence: high 135 · medium 103 · low 1.
Form shape: `carr_three_column` 147 · `cfd_period_ytd` 91 · none 1.

#### The born-digital itemized layer (TRANCHE 3 Phase A, 2026-08-02)

| | count |
|---|---:|
| filings entering the born-digital pass (`parse_summary_text` finds a real text layer) | **38** |
| contribution sides **reconciling exactly** to the stated total → shipped | **7** |
| expenditure sides **reconciling exactly** → shipped | **19** |
| distinct filings carrying at least one itemized row | **21** |
| rows emitted | **32 contributions · 111 expenditures** |
| rows carrying `geometry` | **143 of 143 (100%)** |

Parsed by the registered `cache_cfd` family (`scripts/campaign_finance/families/`), keyed on
`sha256` so a cross-channel byte-duplicate is parsed once. **Every side is
reconciliation-gated**: rows ship only when they sum to the cent against the total this
module already published, and a side that does not reconcile emits **nothing** plus a reason
in `notes` (both `filing_totals.csv` and `filing_stated_detail.csv` carry it). No stated
total was recomputed or moved by this pass — 0 of 239 `stated_*` values changed.

Rows carry `donor_city` / `donor_state` only; the street portion of the free-typed address is
discarded and never stored (`common.split_city_state`). The handwritten Carr era is untouched
and stays Phase-B (vision) work.

---

## 2. Channel-by-channel log

| # | channel | checked | result |
|---|---|---|---|
| 1 | **`cachecounty.gov/elections/financial-disclosures/`** + its 9 per-year pages | ✅ | **291 PDFs** (2012:28 · 2014:81 · 2016:14 · 2018:39 · 2020:17 · 2022:37 · 2024:31 · 2025:7 · 2026:37) — the primary channel |
| 2 | `disclosures.utah.gov` → Municipal → COUNTIES → **CACHE** (87 folders walked) | ✅ partial | **63 hosted PDFs** in county-cycle folders (`2012 General` 21 · `2012 Primary` 9 · `2020_General` 31 · `2020_Primary` 2) **+ 32** in the 2018 residence-town folders (below). Every other year folder is a link stub or municipal |
| 3 | **Wayback** — `cachecounty.org/elections/disclosures.php` (2008 capture) | ✅ | **33 of 35** 2008-cycle filings recovered (2 never captured) |
| 4 | **Wayback** — `cachecounty.org/elections/disclosures/2010.php` | ✅ | **all 37** 2010-cycle filings recovered |
| 5 | **Wayback** — `cachecounty.org/elections/campaign-finance.html` (the 2022-era page) | ✅ | **39 individual PDFs + 1 combined primary PDF**; this list is **not identical** to the current 2022 page (see below) |
| 6 | `disclosures.utah.gov` **public/advanced search** | ✅ | state/legislative filers only; county candidates route to the Municipal tree |
| 7 | `disclosures.utah.gov/Municipal/cache_2024` (re-opened explicitly) | ✅ | **0 hosted files** — one outbound link to the county's own 2024 page. Same for `cache_2014`, `cache_2016` (both entirely empty), `cache_2022`, `cache_2025`, `cache_2026` |
| 8 | blank **form templates** in the archive (`Form - Finance Campaign Report.pdf`, `Form - School Bd …`, `Finance Campaign Report Dates.pdf`) | ✅ | deliberately **not acquired** — empty instruments, not filings |

### The residence-town folder trap — checked, and it is real here

The state system files a county-office disclosure under the folder for the **candidate's
town of residence**, not the jurisdiction of the office. `disclosures.utah.gov` has **no
`cache_2018` file list at all**; its 2018 children are nine *municipal* folders (Avon,
Hyde Park, Lewiston, Logan, Newton, North Logan, Paradise, Providence, River Heights)
holding **32 PDFs** — and those 32 are the **county's own 2018 filers**, not municipal
candidates. All 32 were opened and classified. Odd-year Cache folders (2009/2011/2013/2015/
2017/2019/2021/2023) are municipal by the **election calendar** — county offices in Utah
are elected only in even years — and are out of scope for this package.

### The 2022 page changed under the county's feet

The **live** 2022 page and the **archived** 2022 page list different filers:
live-only **Roger R. Marce**; archive-only **Bethany Nielson** and **Bret Randall**, plus a
combined `2022 Primary Financial Disclosures .pdf` covering **Chris Booth** and **Ladd
Kennington**, neither of whom has an individual file on either page. Both lists were
acquired. Two of these are now resolved by the vision pass: **Bethany Nielson's two filings
are SPECIAL-DISTRICT filings** (re-classified out), and the **combined primary PDF is a
County Council document** — both of its cover pages name County Council, so it is
`county_confirmed`, with Booth's Summary figures in `stated` and Kennington's recorded
verbatim in the cache's `notes` (a two-candidate document does not fit the one-row-one-filer
model, and is flagged as such).

---

## 3. Honest gaps

1. **Itemized rows exist only for the 2022+ BORN-DIGITAL subset** — 21 of 239 filings
   (32 contribution / 111 expenditure rows, each side reconciled to the cent). For the other
   218 filings, "who gave to X" still requires opening the raw PDF: the handwritten Carr era
   is not parseable by any text pipeline, and its stated totals are all that exists. An empty
   side there means **NOT TRANSCRIBED**, never "no donors" — which is why those
   `reconciles_*` stay blank (unknown) and never `False`. This remains the biggest limit on
   the dataset, now measured rather than total.
2. **Stated totals are not a cycle ledger.** Filings within a cycle overlap (interim +
   final), the Carr and CFD families count differently, and `is_incremental` varies **per
   filing**. Summing the deduped stated figures gives ≈$346,104 contributions / $476,620
   expenditures across 181 filings — a magnitude, **not** a sanctioned per-candidate total.
   There is no `cf_cycle` equivalent here.
3. **5 filings have no office** (2% of the ledger), and in every case the *filer* left the
   Office box blank: `2020_st_Scan_3` (an orphan, detached Form-B expenditure page carrying
   no name, office, signature or stamp — nothing on it identifies the filer), Allison
   Goulais 2024, Frank C. Stewart 2024, Jeff Ostermiller 2024, Jeffrey Wallentine 2026.
   These are `undetermined` + `needs_review=1`; the county canvass could not disambiguate
   them either.
4. **4 offices rest on an adjacent-cycle canvass match** (`election_canvass_join (other
   cycle)`) because the page's own office line is blank — David Erickson 2024 ×2 (County
   Council) and D. Chad Jensen 2026 ×2 (Sheriff). Sound, but weaker than a read office
   line, and the `office_basis` string says so on every row.
5. **2 filings never archived** (`unrecovered.csv`): Craig **Butters** 2008-10-27 and
   2008-12-03 — listed on the 2008 page, but the Wayback CDX index has **no capture of
   either PDF**, and `cachecounty.org` is gone. Every other 2008/2010 filing was recovered.
6. **The 2022 posting dates are a migration artefact.** Every file on the live 2022 page
   carries a CMS date of **2025-07-29** — the county re-uploaded the set during a site
   migration, three years after the cycle. Those rows carry a cycle-year `date` with the
   posting date parked in `listing_posted_date`; the archived 2022 page (channel 5) is the
   better provenance for that cycle.
7. **Pre-2008 is a paper-era gap.** The earliest capture of the county's disclosure page is
   2008-12-07, and the 2010-era navigation exposes only `2008.php` and `2010.php`. Cache
   County has never published a pre-2008 county C&E report online.
8. **No 2013 page.** The landing page's "2013 Financial Disclosures" anchor points at
   `trails/calendar.html` (a parks page) and `2013-candidate-financial-disclosures.html`
   404s. 2013 is an odd year — municipal only — so this is a **site defect, not a
   county-office gap**.
9. **The 2026 cycle is in progress.** Filings run to 2026-06-17 (the pre-primary deadline);
   the post-general and year-end reports for 2026 do not exist yet.
   ⚠ **The earlier suspicion that 2026's unresolved rows were school-board filings is
   FALSIFIED** — reading the pages shows Chris Daines wrote "County Attorney", David Gillie
   wrote "Cache County Clerk" (twice), and N. George Daines wrote "Cache County Executive".
   The 2026 column still shows **zero** school-board filers, and that remains unexplained:
   if 2026 school-board filings exist, they were not on the channels probed.
10. **Cross-channel duplicates are deliberate.** 42 of the 239 index rows are byte-identical
    to another row. Counting rows without grouping on `sha256` overstates filing volume by
    roughly a sixth.
11. **Filer arithmetic is retained, never corrected.** 17 lines across the Carr set fail the
    form's own `last + this = cumulative` identity — every one is the filer's own error or
    restatement, transcribed verbatim with the disagreement stated in the cache's `notes`.
    A screen of all 125 Carr transcriptions found **no transcription defect**.

---

## 4. Out of scope (recorded, not acquired into `index.csv`)

- **School-board candidates — 237 filings.** Cache County's clerk publishes school-board and
  county filings on the *same* pages, and the pre-2022 school-board instrument is a
  **separate printed form** citing **Utah Code 20A-11-1301..1305** (versus **17-16-6.5** for
  county offices). Six of these were caught only by the vision pass — they were filed on the
  *county* form, and only the office the filer wrote gives them away. They are fully retained
  in `raw/` + `text/` with complete provenance (`excluded.csv`), consistent with the owner's
  2026-08-01 ruling that county school-board CF is ledgered and out of scope.
  **Cache County School District is not a registered entity in this repo**, so nothing
  downstream consumes them today.
- **Cache Water District Board — 14 filings**, plus **2 more special-district filings**
  (Bethany Nielson 2022) found by the vision pass. Special districts, not county offices.
- **Municipal — 2 filings** (Matt Funk 2012, office line "Justice Court Judge") and
  **state legislature — 1** (Greg Merrill 2018), both filed on the county instrument and
  both caught only by reading the page.
- **Municipal (city/town) filings inside Cache County** generally. Utah municipal candidates
  file with their own city recorder; the state's odd-year `cache_<year>_<City>` folders hold
  them. Logan's belong to `logan_city_council`.
- **Annual conflict-of-interest / financial-disclosure statements** (Utah Code 17-16a) —
  out of scope by the money-layer contract (`scripts/campaign_finance/SCHEMA.md`). The
  county publishes these on separate `<year>-conflict-of-interest-disclosures.html` pages,
  which were **not** harvested. ⚠ **The odd-year page label is misleading and was verified,
  not assumed:** the seven filings on the **2025** page are *not* conflict-of-interest
  statements — every one is a **County Executive campaign C&E report** for the **2026**
  cycle (Craig Anhder, Dirk Anderson, N. George Daines, Mark Hurd, Micah Safsten, Rhyan
  Dockter, Stephanie Miller). They are indexed with `election_year=2026`.

---

## 5. Privacy

Repo policy (`PRIVACY.md`, 2026-07-31): `raw/` and `text/` are **verbatim reproductions of
government-published documents** and are not edited — including donor street addresses
printed on the face of a filing. The donor-city/state-only rule applies to the *structured*
donor tables, which this package produces only for the born-digital subset.
The `vision/` transcriptions record cover-page and totals fields only — no donor rows — so
no donor address is transcribed anywhere in this module. Nothing here is redacted, and
nothing here should be redacted.
