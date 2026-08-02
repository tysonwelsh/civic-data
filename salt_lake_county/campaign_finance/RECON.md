# Salt Lake County COUNTY-office campaign finance — channel reconnaissance

**Recon + acquisition date: 2026-08-01.** Scope: Salt Lake County COUNTY offices only —
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
- **Amounts:** transcribed by Read-tool VISION, not by parsing. The 2026-08-01 tranche covered
  **stated totals only** (cover page + Summary Page) for 61 of the 547; caches in `vision/`,
  contract + coverage in `CLAUDE.md` / `AVAILABILITY.md`. Itemized Schedule A/B lines remain
  untranscribed for this era.

## Channel (b) — County-run disclosure portal (state-software clone, ~2015–2021) — WAF-BLOCKED

- **Live host:** `https://disclosure.saltlakecounty.gov/Search/PublicSearch`
  (`https://disclosure.slco.org` 301s to it). An ASP.NET-MVC app (the same "state software"
  family as `disclosures.utah.gov`): `/Search/PublicSearch`, `/Search/PublicSearch/FolderDetails/{id}`
  (per-candidate folder, reporting years 2015–2025), `/Registration/EntityDetails/{id}`,
  `/Registration/Dissolution/{id}`, and **itemized report pages at `/Report/{id}`**.
- **WAF finding (BigIP):** the root `/` returns `HTTP/1.0 302 → /Search/PublicSearch`; **every**
  deeper path a plain fetcher requests either **302-redirects back to `/Search/PublicSearch`**
  (e.g. `/Report/1069`, `/Home/Contact`) or **resets the connection** (`curl (56) Recv failure`,
  e.g. `/Registration/EntityDetails/196`, and `/Search/PublicSearch` itself). Tried: IPv4 +
  HTTP/1.1 + browser UA + full navigation headers + cookie flow from root + delays — **all reset**.
  The portal is effectively **inaccessible to any non-browser client** (`Server: BigIP` catch-all).
- **Wayback:** the Internet Archive captured the **registration/folder metadata**
  (`FolderDetails`, `EntityDetails`, `Dissolution` — 135 FolderDetails captures) BUT **NOT** the
  itemized `/Report/{id}` pages (a live `/Report/1069` playback = 404; the reports were never
  crawled). So Wayback recovers *who filed which years* but **not the dollar figures**.
- **Data shape (from an archived FolderDetails page):** the portal is itemized like
  `disclosures.utah.gov` — each folder lists paper + online-filed reports, and each online report
  is a `/Report/{id}` itemized contribution/expenditure page. This era covers the **2016 / 2018 /
  2020 county cycles** — the gap between channel (a) (≤2015) and channel (c) (2022+).
- **STATUS: NOT ACQUIRED.** The itemized 2016–2021 data is reachable ONLY via (i) the
  `claude-in-chrome` browser skill against the live portal (a real browser TLS/JS session may
  pass the WAF), or (ii) a GRAMA request to the County Clerk. Handed to the coordinator as a
  lead; the `/Report/{id}` URL pattern makes a browser pass turnkey.

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
- **Coverage (county offices only):** 107 county filers, **442 documents 2022–2026**; of those,
  **164 filings carry itemized data** (2024 + 2026 cycles — the 2022 county docs store only the
  redacted PDF, no keyed itemized rows). **4,956 itemized contributions + 3,278 expenditures**
  (**$1,905,741 raised / $1,633,769 spent**). DOWNLOADED: all 442 redacted PDFs to `raw/easyvote/`
  + the four API JSON responses to `raw/easyvote_api/` (the authoritative structured source).
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

## Summary of what each era yields

| Era | Channel | Years | Filings | Structured? | Status |
|---|---|---|---|---|---|
| Legacy | (a) slco.org clerk PDFs | ~2006–2015 | 547 PDFs | No (PDF only) | ✅ acquired; **stated totals vision-transcribed for 61** (2026-08-01/02) |
| Portal | (b) disclosure.slco.org | ~2016–2021 | itemized | Yes (like Utah) | ❌ WAF-blocked (browser/GRAMA lead) |
| EasyVote | (c) easyvoteapp API | 2022–2026 | 442 PDFs / 164 itemized | **Yes (JSON)** | ✅ acquired + structured; 2022 cycle (123 docs) has no itemized data — **stated totals vision-transcribed for 41** |
