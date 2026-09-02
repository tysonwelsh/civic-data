# Salt Lake County COUNTY-office campaign finance — availability & sources

**As-of: 2026-09-01** (**EasyVote residue itemization CLOSED — wave W2**, verified + federated
2026-09-01; 2015–2021 paper slice closed 2026-08-23 by wave W1; EasyVote office gate repaired
2026-08-20; vision totals tranche COMPLETE 2026-08-02 + **clerk-legacy itemization
COMPLETE — queue closed 2026-08-03**; acquisition recon 2026-08-01). Entity: **Salt Lake County**
(county tier). Scope: the 10 elected
**county offices** — Mayor, County Council (Districts 1–6 + At-Large A/B/C), Sheriff, District
Attorney, Clerk, Assessor, Recorder, Treasurer, Auditor, Surveyor. Utah county candidates file
their Contribution & Expenditure reports with the **County Clerk** (not `disclosures.utah.gov`,
which is the STATE candidate/PAC system).

**Result, stated plainly (2026-09-01).** ✅ **CLOSED:** 2006–2015 — stated totals for all 547
filings and a COMPLETE itemized donor/vendor layer (496 of 496 filings with a Summary Page).
✅ **CLOSED:** the 2015–2021 PAPER slice — 130/130 filings, 6,028 rows (wave W1, 2026-08-23).
✅ **CLOSED:** the whole EasyVote 2022–2026 era — 197 of 442 documents itemized by the API
(2022 26 · 2024 104 · 2026 67) plus **238/238 of the row-less residue transcribed by wave W2**
(18,240 rows + 141 previously-missing covers, closed 2026-09-01; 2 school-board filings ledgered
out of scope). ❌ **UNACQUIRED — the county's ONLY remaining gap:** the **251 online-filed
2015–2021 reports, GRAMA-only** (the portal application is dead, not WAF-blocked — corrected
2026-08-20).

This is the county whose absence made the owner's "largest donor in a county race" query fail —
that query is now answerable from `contributions.csv` for **every document the county holds**,
and is unanswerable only for the 251 GRAMA-only online reports of 2015–2021.

**Update 2026-08-02 (vision totals tranche — COMPLETE):** the two non-structured eras (legacy
PDFs, 2022 EasyVote) now have **stated-totals** rows in `filing_totals.csv` for **all 670 of
their filings** — cover-page identity plus the Summary Page's printed totals and balances, read
by Read-tool vision (114 filings on 2026-08-01, the remaining **556 on 2026-08-02**). **618
carry printed totals; 52 documents have no Summary Page at all** (dissolution notices, Small
Budget Campaign Certificates, letters/emails, cover-only scans, six damaged/blank PDFs).
**Update 2026-08-03 (ITEMIZATION — the clerk-legacy queue is CLOSED):** the Schedule A/B donor and
vendor lines of the CLERK-LEGACY era are transcribed into the same caches.
**All 496 clerk-legacy filings that have a Summary Page are itemized** (214 wave-B2 + 24 promoted
from the calibration pilot + 256 residue + 2 residue-close), yielding **14,746 contribution +
8,125 expenditure rows**; **0 filings remain queued**, and the queue is DERIVED from the caches so
it is exact at any moment (`python3 vision_coverage.py`). Per side: 427/428 exact, 39/41
delta-with-cause (every delta traced to the filing itself), 204/201 unknown, **0 withheld**.
"Unknown" = the form states no total for that side, or the side is `none`.
The honest gaps INSIDE this layer are **8 sides across 5 filings** that state a non-zero total but
contain no schedule page at all ($121,789.32 contributions + $120,455.49 expenditures; 4 of the 8
are exactly reproduced by an itemized sibling filing — table in `CLAUDE.md`).
See "Stated-totals coverage" below; method and cache contract in `CLAUDE.md`.

⚠️ **CORRECTED 2026-08-20.** The two sentences that used to close this paragraph — *"The 2022
EasyVote cycle and the 2016–2021 WAF gap still have no itemized layer. Itemized donor lines for
the 2022 cycle remain untranscribed in these two eras."* — were **false for 2022**. Joining the
API's `advancedsearch_{contributions,distributions}.json` on `DocumentFilingId` → `documentid`
shows **26 of the 123 2022-cycle documents carry keyed itemized rows** (e.g.
`Chapman-Lannie__FC001F57`, 556 contributions). They had been dropped by an office-gate bug in
`build_finance.py`, repaired 2026-08-20 —
`_audits/2026-08-20-easyvote-office-gate/report.md`. The 2016–2021 era genuinely has no itemized
layer, but it is **not** WAF-blocked; see the corrected channel-(b) rows below.

## Where county campaign-finance filings live — three eras, four channels

| Channel | System | Years | Result |
|---|---|---|---|
| **(a) Legacy PDFs** | `slco.org/clerk/financialDisclosurePDF/…` (listed on the county clerk "Salt Lake County Offices" page) | ~2006–2015 | ✅ **547 PDFs** downloaded. RAW only — **all effectively image-only for values** (see the corrected finding below); no itemized data. |
| **(b1) Clerk page, `globalassets` path** ✅ CLOSED 2026-08-23 | `saltlakecounty.gov/globalassets/…/financial_disclosure/…` (linked from the SAME county-offices page as (a)) | 2015–2021 | ✅ **130 PDFs harvested 2026-08-20 and FULLY TRANSCRIBED 2026-08-23 (wave W1): 717 pages, 6,028 itemized rows + stated totals for all 125 filings that have a Summary Page.** Zero overlap with the 547 in `raw/clerk_legacy/`. Inventory: `_recon/2026-08-20-portal-probe/globalassets_inventory.csv`; per-file characterisation: `_audits/2026-08-20-globalassets-harvest/characterisation.csv`. |
| **(b2) Disclosure portal** | `disclosure.saltlakecounty.gov` (state-software MVC clone; `disclosure.slco.org` 301s in) | 2015–2021 | ❌ **THE APPLICATION IS DEAD** (⚠️ corrected 2026-08-20 — previously recorded as "WAF-blocked … browser lead"). Report route is `/Search/PublicSearch/Report/{id}`, never crawled by Wayback. **251 online-filed reports, GRAMA only.** |
| **(c) EasyVote** ✅ CLOSED 2026-09-01 | `saltlakecountyut.easyvotecampaignfinance.com` → `ecf-api.easyvoteapp.com` | 2022–2026 | ✅ **442 redacted PDFs + ITEMIZED JSON** (structured layer built). **197 of the 442 documents are itemized by the API**; the other 245 were row-less and **wave W2 transcribed them from the documents — 238/238 of the derived queue, 18,240 rows + 141 new covers, 0 withheld** (2 school-board filings out of scope). See the W2 verification record at the foot of this file. |

## Sources checked (each URL / query, and the result)

| Source | URL | Result |
|---|---|---|
| Clerk — County Offices disclosure listing | `saltlakecounty.gov/clerk/elections/financial-disclosures/salt-lake-county-offices/` | ✅ 173 candidate headers → **547 unique county PDFs** on `slco.org/clerk/financialDisclosurePDF/`. Downloaded all. |
| Clerk — legacy PDF host | `slco.org/clerk/financialDisclosurePDF/{candidate,2008County,…,2015Disclosures,Archives}/*.pdf` | ✅ plain GET (browser UA) works; 547 fetched, 0 errors (as of build). |
| Clerk — County Offices page, `globalassets` PDFs (re-checked 2026-08-20) | `saltlakecounty.gov/globalassets/…/financial_disclosure/…` | ✅ **HIT — 690 PDF links on that page, 135 anchors / 130 unique are `globalassets`, 2015–2021, county offices.** Plain GET (browser UA) returns `200 application/pdf`; image-only scans of the same form. **Zero overlap** with the 547 in `raw/clerk_legacy/`. ⚠️ Missed on 2026-08-01 because this URL family was only ever inspected on the METRO-TOWNSHIP page (see the corrected Metro Township Councils section below). |
| County disclosure portal (live, re-probed 2026-08-20) | `disclosure.saltlakecounty.gov/Search/PublicSearch`, `/Search/PublicSearch/Report/{id}`, `/Registration/EntityDetails/{id}` | ❌ **THE APPLICATION IS DEAD, not defended.** ⚠️ CORRECTED — the 2026-08-01 entry read "BigIP WAF … no scripted access with any UA/TLS/cookie/delay combination", implying a browser might pass. It cannot: the LB discriminates by PATH, resetting every app-pool path at a flat ~0.23 s while every other path gets a clean catch-all 302. Real Chrome over CDP → `ERR_CONNECTION_RESET`; an unrelated source IP → `read ECONNRESET`. Wayback's last HTTP-200 capture is **2026-01-15**. |
| County disclosure portal (Wayback) | `web.archive.org/…/disclosure.saltlakecounty.gov/Search/PublicSearch/FolderDetails/{id}` and `…/Category/PCC` | ⚠️ **folder/registration metadata archived COMPLETELY** — the archived `Category/PCC` listing enumerates all **54** County/Metro-Township folders and Wayback holds all 54 (131 folder pages incl. school boards + 1 PAC), so the online-report inventory is exhaustive. But **CDX for `…/Report*` is EMPTY** — the dollar figures were never crawled. ⚠️ The 2026-08-01 entry cited a 404 on `/Report/{id}`; that was **the wrong URL** (the real route is `/Search/PublicSearch/Report/{id}`), so that 404 was never evidence about the reports. |
| EasyVote SPA + API | `ecf-api.easyvoteapp.com/advancedsearch/{contributions,distributions}/{customerId}` | ✅ **HIT — full itemized JSON** (no auth; browser UA required; the flagship structured source). |
| `disclosures.utah.gov` | LG state search | State candidates/PACs only — county municipal filings are NOT here (filed with the County Clerk). |
| `disclosures.utah.gov/Municipal/salt lake` | LG state municipal tree (checked per coordinator tip re: county filings hiding under a town-of-residence folder) | ❌ **NEGATIVE for county offices.** Even-year folders (2010/2018/2020/2022/2024/2026) are EMPTY; no 2016 folder. Only ODD-year folders are populated, with **CITY** municipal candidates (16 SLCo cities) — a lead for city CF, not county. SLCo county filings are not in the state system (unlike Juab's). |

## Coverage by cycle (county offices)

Counts as of **2026-08-20** (after the office-gate repair). "Itemized filings" = documents
with at least one row in `contributions.csv` / `expenditures.csv`.

| Cycle | Channel | Documents | Itemized filings | C rows | E rows | State |
|---|---|---:|---:|---:|---:|---|
| 2006–2015 (each even-year county election + interims) | (a) legacy PDFs | 547 | **496** | 14,746 | 8,125 | ✅ stated totals for ALL 547 (496 with a Summary Page, 51 without) + **ITEMIZED CLOSED 2026-08-03** |
| **2015–2021 — paper slice** | (b1) clerk `globalassets` | **130** | **125** | **3,422** | **2,606** | ✅ **CLOSED 2026-08-23** — 130/130 read, 244 sides transcribed, 16 `none`, **0 withheld**; 5 filings have no Summary Page |
| **2015–2021 — online slice** | (b2) dead portal | **251 reports** | 0 | 0 | 0 | ❌ **GRAMA ONLY** (application dead; never archived) |
| 2022 | (c) EasyVote | 123 (87 dated 2022 + 36 dated 2023) | **26** | 1,152 | 332 | ✅ stated totals for ALL 123 (122 printed, 1 no Summary Page); ⚠️ **97 filings row-less — 89 of them hold detail in the document** |
| **2024** (incl. reports filed in 2025) | (c) EasyVote | 199 | **104** | 4,148 | 2,572 | ⚠️ **95 filings row-less — 76 of the 91 audited hold detail; 91 have no `filing_totals` row at all** |
| **2026** | (c) EasyVote | 119 | **67** | 884 | 853 | ⚠️ **52 filings row-less — 32 hold detail; all 52 have no `filing_totals` row at all** |

⚠️ **CORRECTED 2026-08-20.** The rows above replace: *"2016/2018/2020 … NOT ACQUIRED — WAF
gap"*; *"2024 … 98 itemized filings, 4,121 contrib rows"*; *"2026 … 66 itemized filings, 835
contrib rows"*; and *"2022 … no keyed itemized data in the API for 2022"*. The 2022 line was
false (26 documents do carry API rows, suppressed by an office-gate bug), the 2024/2026 counts
were low for the same reason, and the 2016–2021 line understated what is recoverable and
misnamed why the rest is not. The Fife-Jepperson filings indexed `office=County Council` whose
covers read *Salt Lake School Board* are counted here as documents but are out of county scope —
flagged in `index.csv`, not relabelled.

## Stated-totals coverage — the vision tranche (2026-08-01/02)

The two non-structured eras were given **stated-totals** coverage (cover-page identity +
Summary Page Column-A totals and balances), read off each filing by Read-tool vision into
`vision/*.json` and appended to `filing_totals.csv`. **Itemized donor/expenditure lines were
NOT transcribed in this tranche.** Method and cache contract: `CLAUDE.md`.

As-of **2026-08-02**; regenerate these counts from the files with
`python3 vision_coverage.py` (never quote them from memory).

| era | filings | stated totals transcribed | text-parsed | no Summary Page in the doc | not yet transcribed |
|---|---|---|---|---|---|
| (a) clerk_legacy ~2006–2015 | 547 | **496** | **0** | 51 | **0** |
| (c) EasyVote 2022 cycle | 123 | **122** | **0** | 1 | **0** |
| **total** | **670** | **618** | **0** | **52** | **0** |

**Why text-parsed is zero — a corrected finding.** RECON.md estimated "~30% born-digital
(typed forms)" for the legacy channel. Measured 2026-08-01: the 123 legacy PDFs that
`index.csv` marks `format=text` carry a **scanner-embedded OCR layer over HANDWRITTEN**
2006-era forms — the pre-printed labels extract cleanly, the filers' figures do not. And all
**123** 2022 EasyVote PDFs return **zero characters** from `pdftotext`. The EasyVote
`documentsearch` JSON was also checked and carries no total fields. So there was no text path
for either era; every figure in this tranche is vision-read.

**Unreadable / honest-blank counts** (across all 670 caches): **216 illegible-or-absent stated
fields**, of which **208 are fields that do not exist** on the 52 documents that carry no
Summary Page, and **exactly 8 are genuine illegibility** on a real Summary Page
(`jhatch_sept152006.pdf` all four, `sharmsen_10_FinalDis_CntyCncl1.pdf` two,
`ltopham_jan3107report.pdf` one, `Sherrie-Swensen__56E26BA7.pdf` one — each re-rendered up to
600 dpi and cell-cropped before being left null). **2,440** fields carry a printed value;
**24** were left blank by the filer. Filing-level confidence: **610 `medium`, 8 `low`**,
52 ungraded — vision is **capped at `medium`** per SCHEMA §6.

**The 52 no-Summary-Page documents are a real taxonomy, not a failure mode:** the single-page
"Dissolution of a Candidate Campaign" notice (the bulk), the one-page **"Small Budget Campaign
Certificate"** (SLCo Ord. 2.72A.204.5 — an under-threshold filer certifies instead of
reporting; no figures exist), printed **email threads** asking the Clerk to close an account,
plain letters, cover-sheet-only scans, and six damaged/blank PDFs.

**Six source files are damaged or blank at the file level** — `jauger_61906amendment.pdf`,
`20_june_cannon_russ06.pdf`, `nhendricks_sept152006.pdf`, `jhatch_sept152006.pdf`,
`lreberg_sept152006.pdf` (broken xrefs, missing or overprinted Summary Pages) and
**`dwilde_apr52006.pdf`, a wholly blank 4-page scan** (pixel range 251–255 on every page).
All 989 raw PDFs were re-verified byte-intact against `index.csv` sha256 on 2026-08-02, and the
two xref-broken 2006 files were **re-fetched from `slco.org` and returned byte-identical** — so
the defect is upstream in the Clerk's own copies and re-acquisition by URL is exhausted. A GRAMA
request is the only remaining route. Recorded, not worked around.

**Itemization status for these two eras (updated 2026-08-20):** the Schedule A/B donor and vendor
lines for **2006–2015 are COMPLETE** — all 496 filings with a Summary Page, 22,871 rows — so
"who gave to whom" is answerable for that era. The vision caches carry those rows in the
`contributions`/`expenditures` lists the totals tranche shipped empty — no schema change was
needed, exactly as designed. ⚠️ **CORRECTED 2026-08-20:** this paragraph used to end *"2022
remains untranscribed (its EasyVote PDFs are flattened redacted images with the schedules
redacted), and 2016–2021 remains the WAF gap."* **26 of the 123 2022 documents are itemized from
the API** (office-gate repair), and the 2022 PDFs' schedules are **not** redacted — the county's
black bar covers the donor ADDRESS column, never a donor name, date or amount, which is why the
2026-08-20 residue audit classified **zero** sides as withheld. The 97 remaining 2022 filings are
untranscribed, not empty: **89 of them carry itemized detail in the document.**

**Structured totals (EasyVote API, county offices, rebuilt 2026-08-20):** **6,184 itemized
contributions ($2,176,360.58) + 3,757 expenditures ($2,009,188.50) across 197 filings** spanning
the **2022, 2024 and 2026** cycles. ⚠️ **CORRECTED 2026-08-20** — this paragraph previously read
"4,956 itemized contributions ($1,905,741) + 3,278 expenditures ($1,633,769) across 164 filings"
and scoped them to 2024 + 2026 only; both the counts and the scope were wrong, for the
office-gate reason above. Largest single contribution: a $70,000 self-loan (Christopher Stavros,
Assessor 2024); largest external donor to one candidate: Shawn Robinson (District Attorney 2026,
$34,000 in one gift) — both still hold.

**Whole-file totals (all eras, all methods):** `contributions.csv` **20,930 rows /
$9,003,802.56**, `expenditures.csv` **11,882 rows / $6,828,672.55**, `filing_totals.csv`
**841 rows** (rows 1–171 structured EasyVote, rows 172–841 the vision tranche). **Never sum
`filing_totals` dollar columns** — interims, year-ends, finals and amendments overlap by design.

## Honest gaps

⚠️ Gaps 1, 2 and 4 below were **rewritten 2026-08-20**; the superseded wording is quoted inside
each so the record of what was previously believed survives.

1. **2015–2021 (channel b) — NOT ACQUIRED, and it is TWO gaps with two different routes.**
   ⚠️ CORRECTED — this item used to read *"The county disclosure portal is WAF-blocked to every
   non-browser client … Recoverable ONLY via the `claude-in-chrome` browser skill against the live
   portal or a GRAMA request to the Clerk. The `/Report/{id}` URL pattern + the archived folder
   inventory make a browser pass turnkey."* **A browser pass is not turnkey; it is impossible.**
   The application behind the load balancer is dead (evidence in the sources table above and in
   `_recon/2026-08-20-portal-probe/NOTES.md`), and the report route was mis-recorded — it is
   `/Search/PublicSearch/Report/{id}` (ids 1069–2104), so the old `/Report/{id}` 404 was never
   evidence about the reports. The era now splits:
   - **130 paper-filed county-office PDFs, 2015–2021, are FREELY DOWNLOADABLE TODAY** from the
     clerk page's `globalassets` URL family — zero overlap with the 547 in `raw/clerk_legacy/`.
     Image-only scans of the same form; the existing vision pipeline applies unchanged. Inventory:
     `_recon/2026-08-20-portal-probe/globalassets_inventory.csv`. **This is an acquisition that
     needs no permission and has not been done.**
   - **251 online-filed reports exist only in the dead portal and were never archived — GRAMA is
     the only route.** Inventory (with the Wayback folder URL proving each filing exists):
     `portal_online_reports_inventory.csv`. The two slices are complementary — 34 of the 54
     portal filers have no clerk-page PDF at all — so harvesting the 130 does not make the GRAMA
     unnecessary.
2. **2022 EasyVote cycle — 26 of 123 documents ARE itemized; the other 97 are a GAP.**
   ⚠️ CORRECTED — this item used to read *"The 123 county documents in the 2022 cycle are stored
   as redacted PDFs (in `raw/easyvote/`) but return no itemized rows from the API — so the
   itemized layer starts at 2024."* **False.** 26 documents carry keyed API rows (1,152 C + 332 E);
   they were being dropped by the `build_finance.py` office gate, repaired 2026-08-20. Stated
   totals for all 123 are vision-transcribed. Of the 97 still row-less, the residue audit found
   **89 carry itemized detail in the document** — untranscribed, not empty.
3. **Image-only text sidecars deferred.** Every filing in both non-structured eras is
   image-only for VALUES (see the correction above — `format=text` here means "has a font
   layer", not born-digital). Full text sidecars for the scans remain deferred; the vision
   tranche transcribed **stated totals only**, not page text and not itemized lines.
   The EasyVote API money data is unaffected — it comes from the structured API, not OCR.
4. ~~**THE LARGEST OPEN GAP: 245 EasyVote filings carry no itemized rows**~~ — **CLOSED
   2026-09-01 by wave W2** (238/238 transcribed + 2 out of scope; 18,240 rows + 141 covers;
   verification record at the foot of this file). ⚠️ CORRECTED TWICE: this item once read
   *"ITEMIZATION for 2006–2015 and 2022 — NOT TRANSCRIBED …"* (2006–2015 closed 2026-08-03),
   then declared the EasyVote residue the largest open gap (closed 2026-09-01). **The largest
   open gap is now item 1 — the 251 GRAMA-only online reports of 2015–2021.** The audit's
   findings below are RETAINED as the record of the corpus and as the sizing the wave worked
   from; where the audit's per-filing priors disagree with what W2 read at the page, **the page
   governs** and the wave's records carry the correction (e.g. Hobbs `0F64E921` 77/17 rows, not
   81/18; the estimate of ~18,433 lines came in at **18,240 actual rows**, 1.0% high).
   Audit 2026-08-20 (`_audits/2026-08-20-easyvote-residue/`) rendered and read **all 1,719 pages
   of 240 row-less filings** and classified every side:
   - **197 filings (82%) `has-attachment-detail`** — an estimated **~18,433 lines** (11,972 C +
     6,461 E) over **980 pages**. **That total is an ESTIMATE**: 14,397 rows were counted line by
     line and 1,489 are numbered by the filer (~86% real counts); the remaining 2,547 are dense
     uniform grids measured on sampled pages and extrapolated at a fixed row pitch.
   - **8 `empty-schedule`** (a schedule page that is genuinely blank) and **35 `no-schedule-page`**.
   - **0 `withheld`, 0 `undetermined`** — every one of the 480 sides resolved at the document.
   - **143 of the 240 have NO `filing_totals` row at all** (all 91 audited 2024 filings + all 52
     from 2026): no itemized rows, no stated totals, no vision cache. They exist only as a PDF
     plus an `index.csv` row. A wave here owes stated totals for those 143 as well as
     itemization. → **W2 read 141 of them** (the other 2 are the school-board filings);
     `filing_totals` went 971 → 1,112.
   - **Two genuine stated-total-without-detail gaps** were verified at the page:
     `Snelgrove-Richard__CE0A4B74` ($3,261.09 expenditures stated, no Schedule B page exists —
     a final report, so no sibling can cover it) and `Ahn-Danielle__23F2E34E` ($11,868.21 stated,
     Schedule B blank; partially covered by an itemizing sibling). A third apparent contradiction
     (`Creno-Tracey__E28B702C`) is a per-filer **basis inversion**, not a gap.
   - **Donor geography will NOT survive this era.** The county's black bar covers the itemized
     rows' address column on 157 of the 197; on the county grid one cell holds address, city,
     state and ZIP together, so all of it goes. **Exactly 3 filings preserve any geography.**
     A wave must record `donor_city`/`donor_state` as *redacted at source*, not *left blank by
     the filer* — different facts. Occupation/Employer usually survives.
5. **Six legacy/2022 source PDFs are damaged or blank upstream** (listed under Stated-totals
   coverage above); re-fetching by URL is exhausted, GRAMA is the only remaining route.

## OUT OF SCOPE (inventoried, NOT acquired) — leads for the coordinator

- **Local School Boards** — the clerk's `…/financial-disclosures/local-school-board/` page + the
  EasyVote portal carry school-board candidate filings (Canyons, Granite, Jordan, Murray, Salt
  Lake City/District school boards). Present in the EasyVote `documentsearch` (excluded from this
  county-office build). Not a county office → out of scope; a future school-board CF entity could
  reuse the same EasyVote API recipe.
- **Metro Township Councils (lead — see below; its `globalassets` host turned out to hold 130
  IN-SCOPE county-office PDFs too).**

## Metro Township Councils historical disclosures (report-only, NOT acquired)

⚠️ **CORRECTED 2026-08-20 — the "BONUS … out of scope" framing this section used to carry cost
the county-office package 130 in-scope filings.** The `globalassets` host below was recorded on
2026-08-01 as a metro-township curiosity, so **nobody checked whether the county-offices page
served the same URL family. It does** — 130 unique county-office PDFs, 2015–2021, plain-GET, in
the very era recorded as an unrecoverable gap (see Honest gaps §1). A URL family found on one
page of a site is a reason to re-check every sibling page, not a bonus to file away.

The clerk's **`…/financial-disclosures/metro-township-councils/`** page carries **297 unique
redacted disclosure PDFs** (on `saltlakecounty.gov/globalassets/…/financial_disclosure/`),
covering **seven metro townships**: Millcreek 75, Magna 64, Kearns 47, Copperton 32, Brighton 30,
Emigration Canyon 26, White City 23. Predominantly the **2016 cycle** (194 in `2016_disclosures/`
folders incl. `november/`, `2016_year_end/`, `dissolutions/`) plus ~102 undated (2016/2017 era)
and a 2019 straggler. Additionally the **EasyVote portal** holds **57 metro-township filings**
(18 filers, 2023 + 2026) for Copperton, Emigration Canyon, Kearns, Magna, White City.

**Why this matters (hand to coordinator):** these directly bear on repo city entities born from
metro townships — it may **close the kearns `cf-blocked-cycles` caveat** (47 Kearns PDFs, 2016–)
and **enrich the campaign-finance layers of magna / white_city / copperton / emigration_canyon**
(and millcreek's). Recovery is a plain-GET job (globalassets host) + the EasyVote API recipe
already documented here. Not acquired under this county-office package's scope.

## The 2015–2021 PAPER slice — QUEUE CLOSED 2026-08-23 (wave W1 phase 2)

Phase 1 (2026-08-20) harvested and characterised the 130 paper-filed county-office PDFs the
county CMS serves at its `globalassets` path. **Phase 2 transcribed them, and unlike every
earlier SLCo tranche it transcribed BOTH halves in one pass** — stated totals AND itemized
Schedule A/B lines — because this era had no `filing_totals` row at all.

**Configuration:** `claude-opus-5` via the Read tool (Claude Code allotment, **$0 API**),
`pdftoppm -jpeg -r 200` full-page first read of every page, tight-crop escalation at 600–1200 dpi
only, the document's own arithmetic outranking any glyph re-read. Calibration pre-flight
**21/21 PASS** — the first run of the full 21-specimen suite, mandatory because the tooling
changed on 2026-08-20 (`_audits/cf-calibration-suite/runs.md` §2026-08-23). Fan-out: 31 disjoint
chunks; at most 20 concurrent agents.

### Measured coverage (regenerate with `python3 vision_coverage.py` — never quote from memory)

| | |
|---|---:|
| documents in the queue (index.csv `source='globalassets'`) | **130** |
| pages rendered and read | **717** |
| filings with a Summary Page → stated totals transcribed | **125** |
| filings with **no** Summary Page (honest non-existence) | **5** |
| **still queued** | **0** |
| contribution rows | **3,422** |
| expenditure rows | **2,606** |
| **rows total** | **6,028** |

**Sides: 244 `transcribed` · 16 `none` · 0 `withheld` · 0 `out-of-scope`.** Nothing was abandoned
mid-read and nothing was guessed: **0 amounts blank for illegibility** across all 6,028 rows.
196 rows carry `needs_review=1`, overwhelmingly dates the filer printed **without a year** (never
completed from the report date) plus a handful of impossible days (`3/72/20`, `11-31-17`,
`2/3/3015`) left blank with the verbatim in the note.

**Reconciliation, as shipped:** contributions 106 `True` / 6 `False` / 18 blank; expenditures
106 `True` / 8 `False` / 16 blank. As READ by the transcribers: **226 sides exact · 13 delta ·
21 unknown**. Every delta is traced to a named page of the filer's own arithmetic — a page
subtotal that disagrees with its own rows, a grand total that misadds the filer's own subtotals,
a gross-vs-net basis mix (Fresques' $5.33 FundHero fees), an $0.09 misadd, a 2¢ spreadsheet slip.
**Nothing was ever recomputed or nudged.**

**Money observed** (period Column-A figures — **NEVER sum these across filings**; interims,
year-ends, finals and amendments overlap by design): **$2,163,611.66** contributions /
**$1,726,036.30** expenditures. Filing-level confidence: 124 `medium`, 1 `low`, 5 blank (no
Summary Page to grade) — vision is capped at `medium` per SCHEMA §6.
`filing_type` from the form's own checked box: interim 54 · year-end 55 · final 17 · `''` 4.

### `donor_occupation` — the new column, and the only slice that populates it

This era's Schedule A pre-prints an **Occupation/Employer** column that no other SLCo era has.
The owner ruled on 2026-08-20 that it be captured; it is now a trailing-optional column on
`contributions.csv` and `gov.db.cf_contribution` (SCHEMA §2c). **2,292 of 3,422 contribution rows
carry a value**, verbatim as the filer wrote it (`RETIRED` 45 + `Retired` 313 — capitalisation is
NOT normalized, `Attorney` 107, `Business` 75, `Attorney/SLCo DA` 48, `Homemaker` 39, …).

The 1,130 blanks are **three different facts**, and each row's note says which: the form has no
such column (the filer-attachment filings), the column exists and the filer left it empty, or the
county's redaction bar covers it. **Blank is never "no occupation".**

⚠ **Three filings attach a spreadsheet that SPLITS the county's single cell into two columns**
(one filer spells its headers `Employeer` / `Professon`). Both halves are preserved in the vision
cache and composed into the one published field with `" / "` — the same separator the handwritten
county cells already use. 484 rows are composed this way.

### Geometry — 5,744 of 6,028 rows carry a `pct:` pointer, and 284 were WITHDRAWN on purpose

`2016_..._ben-mcadams-mayor_redacted.pdf` pp.4–9 is a rotated landscape attachment whose
transcriber honestly disclosed that its converted pointers drift. Measured at the source: on p9
the true row grid runs 18.53–83.30 pct (43 rules / 42 bands for 42 rows) while the stored boxes
run 17.08–78.89 — row 1 lands BEFORE the first printed rule and row 42 is ~2.1 bands short — and
`rowbands.py` returns `geometry_status: gaps` with ONE FEWER band than ink rows on five of the six
pages, so the grid cannot be independently confirmed there. Per the calibration suite's geometry
specimens (**"frame corrected OR geometry withheld"**), the 284 contribution pointers are blanked
with the reason on every row; **the values are untouched and both sides still reconcile EXACTLY**
($114,752.45 / $256,152.35). That filing's 65 expenditure rows were measured directly in portrait
and keep their geometry.

### Source properties this slice established (each measured, none assumed)

1. **The reconciliation SCOPE TEST must be run PER PAGE — not per filer, and not per filing.**
   A schedule's `TOTAL (Sum of subtotals from all pages)` cell can hold the CYCLE-CUMULATIVE
   figure while `SUBTOTAL FOR THIS PAGE` on the same sheet holds the PERIOD figure; on some
   filings Summary line 1/2 **Column A is ALSO cumulative**, with the true period figure only at
   lines 4/6. Found on six filings, in **both directions**, and **the same filer flips convention
   between his original and his amendment.** Gating on the wrong anchor would have manufactured
   false deltas of $57,703.50, $53,203.50, $46,352.17, $39,353.50, $19,975.92, $2,660.00 and
   $0.32 — well over $180,000 in total. 5 filings ship with `reconciles_*` deliberately BLANK
   under the `SCHEDULE-SCOPE SPLIT` marker in `notes`.
2. **Rotation sign is per PAGE-BLOCK, not per file.** One PDF stores its Schedule A attachment
   rotated clockwise and its Schedule B attachment upright, with `pdfinfo` reporting `rot: 0` on
   both; another has pp.4–9 rotated and pp.11–12 upright. A document-wide rotation silently
   mis-reads half such a filing.
3. **`sha256`-distinct is NOT document-distinct.** `2020_…_burdick-fin-report-3.pdf` is a SECOND
   SCAN of the Schedule B sheet inside its "sibling" — identical rows, identical printed grand
   total, identical stray pencil line, differing only by one pixel row in the embedded raster.
   The 2026-08-20 harvest report calls them a split filing needing pairing; **that is wrong**,
   and summing the pair double-counts $9,533.28.
4. **A page-1 cover cannot be assumed.** Three documents bundle another document in front (a
   Statement of Organization; a Dissolution notice; a Dissolution notice **plus a near-blank ghost
   page**, with the FDR cover only on p3). One filing binds TWO covers — an amendment cover on p1
   and the ORIGINAL September report's cover on p7. Another's pp.5–8 are a page-for-page photocopy
   of a *different* filing in the same queue (transcribed once, the duplicate named and excluded).
5. **The county's black bar UNDER-COVERS**, in every year of the slice (2016/2018/2020): address
   fragments — street numbers, street-type abbreviations, whole glyphs — escape past its edge into
   the neighbouring Occupation column, and one filer wrote a street address *into the Name of
   Contributor cell*, outside the bar entirely. **Every instance was discarded at read time.** The
   `_redacted` filename means nothing: 40 of 130 files lack it, several that have it are
   unredacted, and two print contributor addresses fully in the clear.
6. ⚠ **One filing's redaction is COSMETIC** — see `OWNER_DECISION_PRIVACY.md` in the wave
   workdir. `2020_…_staggs-mayor_redacted.pdf` is the corpus's one born-digital document and its
   black bars are a drawn rectangle over an intact text layer: 40,598 extractable characters and
   **156 ZIP-shaped tokens against exactly 156 contribution rows**. Nothing was extracted (the
   transcriber recorded city/state only; the coordinator's verification counted regex shapes and
   printed no values), and **no address, ZIP or street token from that filing exists anywhere in
   this repo**. It is a defect in the COUNTY'S publication and is raised for owner decision.
7. **Filer arithmetic breaks often enough to be a property.** A grand total that misadds the
   filer's own two page subtotals by $0.09; a balance chain off by $1 carried through both an
   original and its amendment; a Summary line 5 that disagrees with lines 3+4 while line 7 is
   consistent with the *un*-printed value; a $0.32 chain failure. All retained verbatim.
8. **Arithmetic overrode a glyph read more than a dozen times**, per GOTCHAS — a `$/500.00` that
   is 500 because the page subtotal closes only there (confirmed on a second page and the schedule
   total); `247.13` not `249.13` from a $2.00 subtotal miss; `18,941` not `18,441` settled by the
   filer's own struck-through line 5; a `1599.00` whose ink reads `15.99,` with a raised no-cents
   dash. **And once in the opposite direction**, refusing the convenient answer: a Granato page
   will not gate by $2 and the 1200 dpi read (`2,877.61`) was KEPT over the 200 dpi read
   (`2,879.61`) that *would have closed the page exactly*.
9. **A printed figure its own page disproves.** Goodfellow's Balance at Close is written `173634`
   with no decimal point. Published as **1,736.34** with the verbatim retained in
   `cache["totals_verbatim"]`: the form's own instruction for line 7 is "Subtract Line 6 from
   Line 5", line 5 prints the identical six glyphs WITH the point, line 6 is `0`, and line 3 is
   1736.34 with zero activity all period. Same class as the utah Smith-2014 `$3446` adjudication;
   applied through an evidence-carrying `adjudications.csv` that **hard-fails if the recorded
   reading no longer matches the cache**.
10. **Two `index.csv` seat labels are WRONG**, both found at the form by agents not looking for
    them: Cundick is indexed `At-Large A` where his form says **District 4** (which hides that he
    and Ann Granato were 2018 general-election opponents in the same district), and Guymon is
    indexed `At-Large C` where his form has **no letter at all**. `characterisation.csv` carries an
    `office_basis` per row proving the office came from the document but has **no equivalent basis
    column for `seat`** — which is how both slipped through. A seat sweep of all 130 is warranted;
    filed against the open `index.csv` [DEBT].

### Reproducing this slice

The wave's working set is preserved at `_backups/2026-08-23-slco-w1p2/`: `queue.csv`,
`chunks/chunk_NN.csv` (31 disjoint assignments), `prompts/` (the generated launch prompts),
`records/chunk_NN.json` (one record per filing, each declaring its own `wave`),
`records/adjudications.csv` + `records/geometry_withdrawals.csv` (the two evidence-carrying
coordinator interventions), **`AGENT_BRIEF.md`** (the per-row contract verbatim — hand this to any
agent continuing the work), `screen_records.py`, `checkpoint.py`, **`prove_additive.py`**,
`CLOSEOUT.md`, `LEADS_STAGING.md`, `SPECIMEN_CANDIDATES.md`, `OWNER_DECISION_PRIVACY.md`, and
`pre-mod/` (byte-for-byte copies of every repo file the wave touched, taken before its first edit).

```
python3 _backups/2026-08-23-slco-w1p2/screen_records.py <records>   # must PASS first
python3 make_vision_caches.py <records> --transcribed-by "…" --transcribed-date 2026-08-23
python3 make_itemized_caches.py <records> --wave "…" --date 2026-08-23
python3 build_finance.py
python3 _backups/2026-08-23-slco-w1p2/checkpoint.py                 # append-only held?
python3 _backups/2026-08-23-slco-w1p2/prove_additive.py             # pre-wave rows unchanged?
python3 ../../scripts/campaign_finance/validate_finance.py .
python3 vision_coverage.py                                          # 0 remaining = closed
```
⚠ Order matters: `make_vision_caches.py` CREATES each cache and `make_itemized_caches.py` merges
INTO it, so the itemizer silently reports `NO STATED-TOTALS CACHE` for any record the first step
has not yet seen.

## The EasyVote residue — QUEUE CLOSED 2026-09-01 (wave W2), verification record

**Transcribed 2026-08-24 by an external agent (Kimi K3) under the W2 handoff contract
(`W2_HANDOFF.md`); verified independently, federated and documented 2026-09-01 by a Claude
Opus 5 session.** This is the FIRST non-Claude transcription in the repo, so the verification
below is deliberately fuller than a Claude wave's would be. Working set:
`_backups/2026-08-24-slco-w2/` (queue, 76 chunks, 240 records, `screen_records.py`,
`checkpoint.py`, `FINDINGS.md`, `CLOSEOUT.md`, `pre-mod/`). Close-out + verification evidence:
`_backups/2026-09-01-w2-closeout/`.

### Queue derivation (derived, never hand-kept)

Every EasyVote filing whose `document_id` has **no rows in the advanced-search API** — ungated,
so a school-board filing whose rows exist but fail the county-office gate is excluded here too.

| | |
|---|---:|
| derived queue | **240** filings (2022 97 · 2024 89 · 2026 52 after out-of-scope removal: 97/89/52) |
| transcribed | **238** |
| ledgered OUT OF SCOPE (school board, owner ruling) | **2** |
| remaining | **0** |

The two out-of-scope filings are `FIFE-JEPPERSON-CHARLOTTE__AE07FEF8.pdf` and `__D20522DA.pdf`.
Re-verified at the cover 2026-09-01: `AE07FEF8` prints **Office Sought = "Salt Lake School
Board", District Number 2**. ⚠ **Classify by OFFICE SOUGHT, never by the top-row "Office"**,
which carries the filer's *current* seat: her 2026 filing `__B5AB014E` prints Office = "Salt
Lake City School Board District 2" but Office Sought = "**Salt Lake County Council District
2**", and its 2 API contribution rows + `filing_totals` row + `cf_cycle_county` 2026 row are
correctly IN scope. The distinction is a two-box form pattern already documented for the
2008-era form.

### What the wave delivered (measured; regenerate with `python3 vision_coverage.py`)

| | |
|---|---:|
| pages read | **1,719** (every page of all 240 documents) |
| rows published | **18,240** — 11,852 contributions + 6,388 expenditures |
| `pct:` geometry | **18,240 / 18,240 = 100%** |
| rows re-read in a tighter band and identical (`verified=1`) | **11,736** (64.3%) |
| tight-crop escalations | **1,368** |
| new covers read (`filing_totals` 971 → **1,112**) | **141** |
| 2022 filings whose existing cover gained an itemized half | **97** (their `stated_*` did not move) |
| filings with a Summary Page / without | **234 / 4** |
| `extraction_confidence` | medium 18,002 · low 238 · **high 0** (vision is capped at medium) |
| `needs_review=1` | 975 |
| `donor_occupation` populated | **10,225** of 11,852 contribution rows |

**Per SIDE (240 filings × 2 = 480 sides).**

| verdict | sides | meaning |
|---|---:|---|
| exact | **359** | rows sum to the printed figure that matches their own scope |
| delta-with-cause | **33** | the FILER's arithmetic; both figures retained verbatim, cause traced to a named page |
| `none` | **82** | the document has no such schedule page — non-existence, never a zero |
| unknown | **2** | the document prints no anchor for that side |
| out-of-scope | **4** | the 2 school-board filings |
| **withheld** | **0** | no side was abandoned mid-read |

**Dollars.** W2 rows total **$4,330,753.87 contributions / $3,305,602.19 expenditures**
(measured from the published CSVs 2026-09-01). ⚠ The wave's own `CLOSEOUT.md` quotes
$3,583,562.53 / $1,999,268.65; those are a **mid-wave snapshot and are superseded** — the
figures above are what `build_finance.py` emits and they reconcile exactly to the module total
it prints, **$15,498,168.09 contributions / $11,860,311.04 expenditures**. Never sum
`filing_totals` across filings; use `cycle_totals_county.py`.

### The honest gaps this wave leaves, named

* **78 contribution amounts are blank BY SOURCE.** 77 of them on
  `Wilson-Jennifer__B5D1F91C.pdf`: the county's redaction bar spans **Address → Amount
  inclusive** on pp.3 and 6 while Date, Name, Employer and Occupation survive (re-rendered and
  confirmed at the page 2026-09-01; 37 rows on p3, 40 on p6). That C side is a documented
  **FLOOR** — $114,980.00 readable against a stated $161,699.85, so ≈29% of the side is
  unrecoverable from the public record. **This is the only place in the SLCo corpus where the
  county's bar takes a MONEY column**; everywhere else it takes only the address.
  The 78th is `Wilson-Jennifer__CE8EF5B5.pdf`, where the filer printed no amount at all for one
  row (Loralee Rees).
* **4 documents have no Summary Page** — a Small Budget Campaign Certificate, a dissolution
  notice and two cover-only documents. Honest non-existence, `null`, never zero.
* **82 sides are `none`** — the document has no such schedule page.

### Verification performed before federation (2026-09-01)

1. **Module gates re-run independently.** `validate_finance.py` **PASS** (0 fails; the 7
   Fife-Jepperson "no filing_totals row" warns are by design). `screen_records.py` **PASS**
   (240 records, 0 fails, 124 warns, **queue filings still missing a record: 0**).
   `checkpoint.py` **OK — append-only invariant held**. `vision_coverage.py` **remaining 0** in
   every cycle (2022 97/97 · 2024 89/89 · 2026 52/52).
2. **Deterministic rebuild.** `build_finance.py` re-run off the caches reproduced
   `contributions.csv`, `expenditures.csv`, `filing_totals.csv` and `index.csv`
   **byte-for-byte** (sha256 identical).
3. **Frozen blocks proved, not asserted.** Against the pre-wave copies in
   `_backups/2026-08-24-slco-w2/pre-mod/slco_cf/`: `contributions.csv` rows 1–24,352 and
   `expenditures.csv` rows 1–14,488 are **field-for-field identical**. In `filing_totals.csv`
   rows 1–971, **exactly 97 rows changed and all 97 are the 2022 residue cohort gaining an
   itemized half** — the changed columns are only `itemized_*`, `reconciles_*`, `recon_delta_*`,
   `n_*_rows`, `self_funded_amount` and `notes`, and **ZERO `stated_*` values moved**.
   Re-hashing all 388 paths in `all_cf_csv_sha256.baseline.txt` found 13 differences: the 3 SLCo
   money CSVs (this wave) and 10 cache/washington/cycle files timestamped 2026-08-24 00:00–00:22,
   i.e. other entities' work that predates any W2 write.
4. **Spot-check at the page — 4 filings across the ledger tiers, all reproduced exactly.**
   `Conder-Phil__12F26E7B` (exact, county grid): 6 contribution rows and 13 expenditure rows
   match the page line for line, including two column-clipped donor strings kept as visible
   glyphs at `needs_review=1` ("er, Phil (2015 State Trea", "alt Lake County Treasur") rather
   than completed, and stated totals $2,817.22 / $2,816.64 / $0.00 / $0.58.
   `Bradshaw-Arlyn__927411EB` (2026 cover-only): $0.00 / $0.00 / $22.61 / $22.61, year-end box,
   2-page filing with no schedule — `reconciles_*` correctly BLANK.
   `Wilson-Jennifer__B5D1F91C` (redaction): the bar and the surviving columns are exactly as
   published, 37 + 40 blank-amount rows on pp.3/6.
   `Gettel-Dustin__E61DBCB5` (delta +$120.00): p14's 15 rows match one-for-one including
   verbatim casing and the two `(In Kind)` flags, the 218 rows sum to $23,166.09, and the delta
   is exactly the one in-kind row (Silverzweig, 3/24/2024, $120.00) the filer left out of his
   own Summary line 1.
5. **Full CF sweep:** 38 modules PASS + the 2 known non-regressions (draper is
   documents-only; `scripts/campaign_finance` is not a dataset dir). 93 family tests green,
   31-case county-reducer regression suite green.
6. **Federation:** `build_cities_db.py` auto-gate **44/44**, `PRAGMA integrity_check` ok,
   `foreign_key_check` **0**. `cf_contribution` for the county 24,352 → **36,204**,
   `cf_expenditure` 14,488 → **20,876**, `cf_filing` 971 → **1,112** (the live pre-wave db also
   carried 2 school-board `cf_filing` rows that this build correctly REMOVES). `cf_cycle`
   (city tier) and `cf_candidate_person` are byte-identical.
7. **County cycle reducer regenerated** (`cycle_totals_county.py`), gates **G1/G5/G6 PASS** on
   all 8 counties. Changes, all explained: **37 salt_lake candidate-cycles moved GAP →
   PUBLISH** on the strength of the 141 new covers; **0 moved the other way and 0 published
   figure changed value**; 39 rows stayed GAP with a *more specific* `gap_reason` (the reducer
   now has a stated total and can advance past the no-stated-total test to `chain-broken` /
   `neither-basis`); 17 rows changed only their advisory `itemized_check_*`; and 1 row was
   removed (`FIFE-JEPPERSON, CHARLOTTE` 2024, the out-of-scope ruling). **The other seven
   counties changed by zero rows.** Repo totals 1,009 → **1,008** cycles, 620 → **657**
   publishing, 389 → **351** gaps, 201 → **222** flagged floors; SLCo chain closure 113/225
   (50.2%) of its multi-filing cycles.
8. `check_doc_numbers.py` **all checks PASS** after 6 headline numbers were updated in
   `README.md` / `CLAUDE.md` / `gov_db_SCHEMA.md` in the same session.

### Two things this wave changed about how the module must be read

* ⚠ **`donor_occupation` is no longer paper-slice-only.** The EasyVote county grid prints an
  Occupation/Employer column and most filer attachments carry Organization + Title, so 10,225
  W2 rows populate it and the module total is **12,517**. Composed `occupation / employer`.
* ⚠ **Some expenditure amounts are NEGATIVE as printed** — Morris-Rachelle's five bank/ledger
  exports and `Liewer-Ashley__585D94D0` print every debit with a minus sign, and the sign is
  kept **verbatim** under the never-correct-the-filer rule. Reconciliation is on **MAGNITUDE**
  and `filing_totals.itemized_expend_sum` is published POSITIVE, so **a consumer summing
  `expenditures.amount` must take `abs()`**. The convention already existed in the
  clerk-legacy McAdams/Winder rows (892 negative expenditure rows module-wide).

### Reproducing this wave

```
python3 _backups/2026-08-24-slco-w2/screen_records.py _backups/2026-08-24-slco-w2/records
python3 make_vision_caches.py _backups/2026-08-24-slco-w2/records     # covers; skips the 99
                                # itemization-only records (their caches already exist)
python3 make_itemized_caches.py _backups/2026-08-24-slco-w2/records
python3 build_finance.py                                              # deterministic
python3 _backups/2026-08-24-slco-w2/checkpoint.py
python3 ../../scripts/campaign_finance/validate_finance.py .
python3 vision_coverage.py                                            # 0 remaining = closed
python3 ../../scripts/campaign_finance/cycle_totals_county.py salt_lake_county
python3 ../../scripts/build_cities_db.py
```
Each record declares its own `wave`, so the provenance stamp is reproducible from the records
and not from a CLI flag. Calibration pre-flight for this wave: **21/21**, recorded in
`_audits/cf-calibration-suite/runs.md` under 2026-08-24.
