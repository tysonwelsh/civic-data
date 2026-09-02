# Salt Lake County COUNTY-office campaign finance — channel reconnaissance

**Recon + acquisition date: 2026-08-01. Corrected + re-probed 2026-08-20** (channel (b)
re-diagnosed, channel (c) office gate repaired — both marked ⚠️ CORRECTED below).
Scope: Salt Lake County COUNTY offices only —
Mayor, County Council (Districts 1–6 + At-Large A/B/C), Sheriff, District Attorney, Clerk,
Assessor, Recorder, Treasurer, Auditor, Surveyor. (School boards + metro-township councils are
OUT of scope — inventoried as leads in `AVAILABILITY.md`.)

This is the county whose absence made the owner's "largest donor in a county race" query fail.

Utah county-candidate campaign finance is filed with the **County Clerk** (not the Lieutenant
Governor's `disclosures.utah.gov`, which carries STATE candidates/PACs). Salt Lake County has run
its disclosure through **three successive systems**; each is a distinct era with distinct data:

## Channel (a) — LEGACY per-candidate PDFs (~2006–2015)

- **Listing:** `https://www.saltlakecounty.gov/clerk/elections/financial-disclosures/salt-lake-county-offices/`
  — an alphabetical roster of officials/candidates; each has an `<h4>Name (Office)</h4>` header
  followed by year-grouped links to report PDFs on `https://slco.org/clerk/financialDisclosurePDF/…`.
- **Coverage:** 173 candidate headers, **547 unique county-office PDFs**, folders
  `candidate/` + `2008County` + `2009Disclosures` + `2010Disclosures` + `2010_Year_end` +
  `2011YearEnd` + `2012Disclosures` + `2013_Disclosures` + `2014Disclosures` + `2015Disclosures`
  + `Archives`. Report periods (April / June / September / October interims, Summary, Dissolution).
  All 10 county offices present. Earliest dated files are 2006 (e.g. `jallen_apr52006.pdf`).
- **Access:** plain HTTPS GET works (browser UA). **DOWNLOADED: all 547** to
  `raw/clerk_legacy/` (provenance in `_fetch_log.jsonl`: url, sha256, bytes, candidate, office,
  period).
- **Format:** RAW PDF only — no itemized/structured data. ⚠️ **CORRECTED 2026-08-01:** this
  section previously read "~30% born-digital (typed forms)". It is **not** — the 123 PDFs that
  `index.csv` marks `format=text` carry a **scanner-embedded OCR layer over HANDWRITTEN**
  2006-era forms. The pre-printed labels extract cleanly; the filers' figures are garbage. So
  `format=text` here means "has a font layer", not born-digital (the riverton precedent), and
  **there is no text path to the money in this era at all**.
- **Amounts:** transcribed by Read-tool VISION, not by parsing. Caches in `vision/`, contract
  + coverage in `CLAUDE.md` / `AVAILABILITY.md`. ⚠️ **CORRECTED 2026-08-20** (the fact it
  restates landed 2026-08-03): this bullet previously read "the 2026-08-01 tranche covered stated totals only … itemized Schedule A/B
  lines remain untranscribed for this era". **Stated totals are now complete for all 547** (496
  with a printed Summary Page; 51 documents have none) and the **ITEMIZED Schedule A/B layer is
  CLOSED for this era** — 496 of 496 filings with a Summary Page, **14,746 contribution + 8,125
  expenditure rows** (wave B2, 2026-08-02/03). The residual gaps inside it are 8 sides across 5
  filings that state a non-zero total but contain no schedule page; see `CLAUDE.md`.

## Channel (b) — County-run disclosure portal (state-software clone, ~2015–2021) — **THE APPLICATION IS DEAD; GRAMA IS THE ONLY ROUTE TO THE ONLINE SLICE**

⚠️ **CORRECTED 2026-08-20.** This section previously read **"WAF-BLOCKED … a real browser
TLS/JS session may pass the WAF"** and gave the report URL as **`/Report/{id}`**. Both were
wrong, and together they made a browser pass look turnkey when no browser route exists. Full
probe record + evidence: `_recon/2026-08-20-portal-probe/NOTES.md`. What is true:

- **Host:** `https://disclosure.saltlakecounty.gov` (`disclosure.slco.org` 301s to it);
  `Server: BigIP`, DNS `204.99.179.232`. An ASP.NET-MVC app of the `disclosures.utah.gov`
  family: `/Search/PublicSearch`, `/Search/PublicSearch/FolderDetails/{id}` (per-candidate
  folder), `/Registration/EntityDetails/{id}`, `/Registration/Dissolution/{id}`.
- **The itemized report route is `/Search/PublicSearch/Report/{id}`, ids 1069–2104** — NOT
  `/Report/{id}`. The archived folder pages call `openReport('/Search/PublicSearch/Report/{id}')`.
  The 2026-08-01 session probed `/Report/1069`, **which is not an application route at all**;
  its bare redirect and its Wayback 404 were therefore never evidence about the reports.
- **Why it is DEAD, not defended (measured 2026-08-20).** The load balancer discriminates by
  PATH, not by client. Every path forwarded to the application pool RSTs deterministically at a
  flat ~0.23 s — LB-local, no backend latency (`/Search/PublicSearch`,
  `/Search/PublicSearch/FolderDetails/1`, `/Search/PublicSearch/Report/1069`,
  `/Registration/EntityDetails/196`, `/Content/Site.css`) — while every other path gets a clean
  catch-all `302 → /Search/PublicSearch` (`/`, `/foobarbaz`, `/favicon.ico`, `/Home/Index`).
  An anti-bot control discriminates by *client*; this discriminates by *path*. Real Chrome
  (local binary, headless=new, full TLS + JS, Chrome UA, driven over CDP) returns
  `ERR_CONNECTION_RESET`; a request from unrelated infrastructure returns `read ECONNRESET`.
  The TLS cert is current (Sectigo, valid to 2026-11-18) — the VIP is maintained, the pool
  behind it is not. Wayback's last HTTP-200 capture of `/Search/PublicSearch` is **2026-01-15**,
  with no successful capture after; the portal went dark between then and the 2026-08-01 recon.
  **There is nothing listening, so there is nothing to defeat.** A browser route does not exist.
- **Wayback holds the folder metadata COMPLETELY and ZERO report pages.** The archived
  `Search/PublicSearch/Category/PCC` listing enumerates **54** County/Metro-Township filer
  folders (ids 129–263) and Wayback holds all 54 (131 folder pages in total, incl. 76 Local
  School Board + 1 PAC) — so the online-filed inventory below is **exhaustive, not a sample**.
  CDX for `…/Report*` is empty: the dollar figures were never crawled. A folder page yields
  filer name, cycle-year + office label, the per-year paper/online report lists, and each online
  report's numeric id. That is the whole of what survives of the online slice.

### STATUS — the era splits into TWO slices, and only one of them is blocked

| slice | count | route | status |
|---|---:|---|---|
| **paper-filed 2015–2021**, on the county CMS `globalassets` path | **130 unique PDFs** (135 anchors) | plain HTTPS GET, works today | **FREELY ACQUIRABLE — NOT YET IN THE REPO** |
| **online-filed 2015–2021**, rendered only by the dead portal | **251 reports** (249 county-office across 46 filer folders; 2 belong to a Canyons school-board folder) | `/Search/PublicSearch/Report/{id}` | **GRAMA ONLY** — never archived, host dead |

**The paper slice (130 PDFs) — a source that was here all along.** They sit on the SAME clerk
"Salt Lake County Offices" page channel (a) was harvested from, under a URL family
(`saltlakecounty.gov/globalassets/…/financial_disclosure/…`) the 2026-08-01 harvest never
matched: that page carries 690 PDF links, of which **135 anchors / 130 unique files** are
`globalassets`, while all 547 already in `raw/clerk_legacy/` are
`slco.org/clerk/financialDisclosurePDF/…`. **Verified zero overlap** — by URL and by filename —
against `raw/clerk_legacy/_fetch_log.jsonl`. By year: 2015 15 · 2016 29 · 2017 16 · 2018 34 ·
2019 10 · 2020 23 · 2021 5, plus 2 filed under 2014 and 1 unlabelled. Inventory (candidate,
office, listing label, folder year/period, direct URL):
`_recon/2026-08-20-portal-probe/globalassets_inventory.csv`. Sampled files fetch live
(`200 application/pdf`) and are **image-only scans of the SAME form this repo already
transcribes** (cover + Summary Page Column A/B lines 1–7 + Schedule A/B with printed page
subtotals) — so vision is the channel, exactly as for `raw/clerk_legacy/`, and the existing
pipeline applies unchanged. Three shape warnings taken off the sample pages: Schedule A in this
era adds an **Occupation/Employer** column the row schema has no home for; **a filing can be
split across several PDFs** (page 1 is not always a cover); and **folder-year labels lie**
(2018 documents parked in a `2016_disclosures/` folder) — the form governs, per GOTCHAS.

**The online slice (251 reports) — GRAMA.** Enumerated from the archived folder pages:
2015 14 · 2016 27 · 2017 6 · 2018 75 · 2019 12 · 2020 98 · 2021 19. **249 of the 251 are
county offices**; the other 2 (both 2015) sit in a Canyons school-board folder and are out of
scope. Inventory — folder id,
filer label, reporting year, report id, the dead URL, and the Wayback folder URL that PROVES
each filing exists: `_recon/2026-08-20-portal-probe/portal_online_reports_inventory.csv`
(251 rows across 47 distinct filer folders; NOTES.md's headline "54 filers" is the count of
archived County/Metro-Township folders, 7 of which list no online reports). Because the
county's own system rendered these, ask GRAMA for the export, not for 251 printouts.

**The two slices are COMPLEMENTARY, not duplicative.** 34 of the 54 portal filers have no
clerk-page PDF at all — they filed electronically only (Bradshaw 8 online / 0 PDFs; Swensen,
Rivera, Newton and Winder likewise) — while the filers with rich clerk-page PDF sets have zero
online reports (Bradley 0 online / 12 PDFs, Evershed 0/8, Dekeyzer 0/4). By year the mismatch
is starkest where the portal was busiest (2020: 98 online vs 23 PDFs; 2018: 75 vs 34).
**Harvesting the 130 PDFs closes a real and distinct part of the hole; it does NOT make the
GRAMA unnecessary.**

## Channel (c) — EasyVote portal (2022+) — STRUCTURED, the flagship

- **Public UI:** `https://saltlakecountyut.easyvotecampaignfinance.com/home/publicfilings`
  (Angular SPA — empty to a plain fetch). **API base** (from the SPA `main.5cb5b76dc155dd14.js`):
  `https://ecf-api.easyvoteapp.com`. **Customer id** (`/customer/current`, Origin-scoped):
  `D2EEAA9C-E9BF-4B77-AC5E-2A6F379D1775` = "Salt Lake County".
- **Working access recipe (no auth):**
  - Public token: `GET /authentication/getwebsiteuser/saltlakecountyut` → `{UserId, CustomerId,
    ZumoToken:null}`.
  - **Itemized structured data (the prize):** `GET /advancedsearch/contributions/{customerId}`
    and `GET /advancedsearch/distributions/{customerId}` — return **every itemized contribution /
    expenditure** across all filers as JSON (recipient/candidate, contributor/payee name+org,
    date, amount, office GUID, filing id). Header `Easy-Vote-Authenticated-User:
    UserId:{u}|CustomerId:{c}|ZumoToken:null` + `ZUMO-API-VERSION: 2.0.0` + Origin =
    the public site. **This is the same channel `disclosures.utah.gov`-style itemized data — it
    feeds `cf_contribution` directly.**
  - Filer/document list: `GET /filer/documentsearch/{customerId}`; office map:
    `GET /filer/offices/{customerId}`.
  - Redacted PDF (image-only): `GET /documents/{documentId}/viewfinalredactedpdf`.
  - **GOTCHA:** the API returns **403 to `Python-urllib`** — send a browser `User-Agent`.
- **Coverage (county offices only):** 107 county filers, **442 documents 2022–2026** indexed.
  DOWNLOADED: all 442 redacted PDFs to `raw/easyvote/` + the four API JSON responses to
  `raw/easyvote_api/` (the authoritative structured source).
- **Itemized rows, as rebuilt 2026-08-20:** **197 of the 442 documents carry keyed itemized API
  rows** (2022 **26** · 2024 104 · 2026 67) — **6,184 contributions ($2,176,360.58) + 3,757
  expenditures ($2,009,188.50)**.
  ⚠️ **CORRECTED 2026-08-20.** This bullet previously read **"164 filings carry itemized data
  (2024 + 2026 cycles — the 2022 county docs store only the redacted PDF, no keyed itemized
  rows) … 4,956 itemized contributions + 3,278 expenditures ($1,905,741 raised / $1,633,769
  spent)"**. **The 2022 claim was FALSE and the counts were low.** `build_finance.py` resolved
  office names only through `raw/easyvote_api/offices.json` — a snapshot of CURRENTLY-ACTIVE
  offices, missing 12 historical `OfficeGuid` values — so every row keyed to one of those GUIDs
  failed the county-scope test and was dropped with no log line (Clerk, Sheriff, Auditor,
  Recorder, Surveyor and four Council seats). Repaired the same day: GUID-first resolution with
  the filing's own metadata as fallback and the county-scope test applied to the RESOLVED name
  (so school-board and municipal filers stay excluded). Record, proof obligations and the
  before/after diff: `_audits/2026-08-20-easyvote-office-gate/report.md`. **Zero rows were lost,
  every `stated_*` value is byte-identical, and every added row is a Salt Lake County county
  office.** `raw/easyvote_api/offices.json` must never again be treated as a complete historical
  office table.
- **An independent cross-validation fell out of the repair.** The 26 newly-admitted 2022-cycle
  filings already carried vision-transcribed cover totals and gained an itemized half from the
  API. **All 52 sides reconcile EXACTLY** (`recon_delta = 0.00`) — a page image read by vision
  and a born-digital API feed agreeing to the cent, on filings as large as $102,508.83 over 556
  rows. Nothing was nudged; the figures simply agree.
- **The remaining 245 EasyVote filings carry NO itemized rows, and that is a GAP, not an honest
  zero.** Audited 2026-08-20 — all 1,719 pages of 240 of them read and classified per side
  (`_audits/2026-08-20-easyvote-residue/README.md` + `classification.csv`; the 5 unaudited are
  Fife-Jepperson filings whose covers read *Salt Lake School Board* while `index.csv` labels them
  County Council — flagged, not relabelled, per the riverton-Pierucci precedent). Of the 240:
  **197 filings (82%) carry real itemized detail in the document** — coincidentally the same
  number as the API-itemized filings above, but a DIFFERENT set — spread over **980 pages** and
  estimated at **~18,433 lines** (11,972 C + 6,461 E). **That row figure is an estimate**: ~86%
  of it is a line-by-line count (14,397 rows counted + 1,489 numbered by the filer), the
  remaining 2,547 are dense uniform grids measured on sampled pages and extrapolated at a fixed
  row pitch. The other 43: **8 `empty-schedule`** (a schedule page that is genuinely blank) and
  **35 `no-schedule-page`**. **Nothing is `withheld` and nothing is `undetermined`** — every one
  of the 480 sides resolved at the document.
- **143 of those 240 filings have NO `filing_totals` row at all** — all 91 audited 2024 filings
  and all 52 from 2026. No itemized rows, no stated totals, no vision cache: they exist only as
  a PDF plus an `index.csv` row. The 2022 cohort by contrast has complete stated totals from the
  2026-08-02 vision tranche. Any wave here owes stated totals for those 143 as well as
  itemization.
- **Two stated-total-without-detail gaps were found and verified at the page**:
  `Snelgrove-Richard__CE0A4B74` (2024 Recorder final, $3,261.09 expenditures stated, no
  Schedule B page exists) and `Ahn-Danielle__23F2E34E` (2022 District Attorney, $11,868.21
  stated, Schedule B present and blank — partially covered by an itemizing sibling filing).
  A third apparent contradiction (`Creno-Tracey__E28B702C`) is a **basis inversion**, not a gap.
  The same audit re-read the 2022 stated totals blind and found **191 comparable sides, ZERO
  disagreements** with the 2026-08-02 vision tranche.
- **Structured layer built** from the API JSON (`build_finance.py` → `contributions.csv` /
  `expenditures.csv` / `filing_totals.csv`, per `scripts/campaign_finance/SCHEMA.md`). See CLAUDE.md
  for the honest caveats (no in-kind flag; no stated totals in API ⇒ reconciliation unknown;
  even-year `election_year` proxy).

## Channel (d) — State system `disclosures.utah.gov/Municipal/salt lake` — NEGATIVE (checked per coordinator tip)

Checked 2026-08-01 after the Juab agent flagged that county-office filings sometimes hide in the
LG state system, sub-foldered by the candidate's **town of residence**, discriminable by the form
header "FINANCIAL CAMPAIGN REPORT — Utah Code **17-16-6.5**". **Result for Salt Lake: NEGATIVE.**
- The state `/Municipal/salt lake` tree has year folders 2009–2026 but the **EVEN-year folders
  (2010, 2018, 2020, 2022, 2024, 2026) are EMPTY** ("SALT LAKE » 2010 » Financial Disclosure
  Reports" with no entries; town subfolders like `salt lake_2020_Sandy City` return 74-byte empty
  responses). **No 2016 folder exists at all.**
- Only **ODD-year** folders are populated, and they hold **CITY municipal candidates** (Alta,
  Bluffdale, Midvale, Cottonwood Heights, Draper, Herriman, Holladay, Millcreek, Murray, Riverton,
  Sandy, South Jordan, South Salt Lake, Taylorsville, West Jordan, West Valley) — **not county
  offices.** So unlike Juab, Salt Lake COUNTY filings are NOT in the state system; they live only
  in channels (a)/(b)/(c). The odd-year CITY folders are a **lead for city CF datasets**, not this
  county-office package.
- The coordinator's refinement (the `17-16-6.5` county form header FALSE-POSITIVES because clerks
  hand the blank county form to small municipalities too — classify by the in-form "Office Filed
  For" line + even-year parity, not the header) was **moot here**: the even-year Salt Lake folders
  returned empty (74-byte) responses, so there were **zero PDFs to classify** — the negative is a
  genuinely empty tree, not a mis-classification.

## Summary of what each era yields (as of 2026-08-20)

| Era | Channel | Years | Filings | Structured? | Status |
|---|---|---|---|---|---|
| Legacy | (a) slco.org clerk PDFs | ~2006–2015 | 547 PDFs | No (image-only) | ✅ acquired; **stated totals for all 547** (496 with a Summary Page) + **ITEMIZED CLOSED** — 496/496, 14,746 C + 8,125 E rows (wave B2, 2026-08-02/03) |
| Portal — paper slice | (b) `saltlakecounty.gov/globalassets/…` | 2015–2021 | **130 unique PDFs** | No (image-only) | ⬜ **NOT ACQUIRED — but freely downloadable today**; inventory in `_recon/2026-08-20-portal-probe/globalassets_inventory.csv` |
| Portal — online slice | (b) `disclosure.saltlakecounty.gov` | 2015–2021 | **251 reports** | was (like Utah) | ❌ **application DEAD** (not WAF-blocked — corrected 2026-08-20); never archived. **GRAMA only**; inventory in `portal_online_reports_inventory.csv` |
| EasyVote | (c) easyvoteapp API | 2022–2026 | 442 PDFs / **197 itemized** | **Yes (JSON)** | ✅ acquired + structured (2022 26 · 2024 104 · 2026 67 — office gate repaired 2026-08-20); **stated totals for all 123 of the 2022 cycle**; ⚠ **245 filings still row-less — 197 of the 240 audited hold ~18,433 untranscribed lines (estimate), and 143 have no `filing_totals` row at all** |

**The itemized layer is NOT complete for this entity.** Closed: 2006–2015 (vision) and the
197 API-itemized EasyVote filings. Sized known gap: the 197 has-detail EasyVote filings,
~18,433 estimated lines. Unacquired: 130 paper PDFs (free) + 251 online reports (GRAMA),
2015–2021.
