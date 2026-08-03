# Salt Lake County COUNTY-office campaign finance — availability & sources

**As-of: 2026-08-03** (vision totals tranche COMPLETE + **clerk-legacy itemization COMPLETE — queue closed**; acquisition recon 2026-08-01). Entity: **Salt Lake County** (county tier). Scope: the 10 elected
**county offices** — Mayor, County Council (Districts 1–6 + At-Large A/B/C), Sheriff, District
Attorney, Clerk, Assessor, Recorder, Treasurer, Auditor, Surveyor. Utah county candidates file
their Contribution & Expenditure reports with the **County Clerk** (not `disclosures.utah.gov`,
which is the STATE candidate/PAC system).

**Result: SUBSTANTIALLY COMPLETE for 2006–2015 (PDF) and 2022–2026 (STRUCTURED); a genuine
2016–2021 gap** blocked by a WAF (documented, recoverable only via browser or GRAMA). This is the
county whose absence made the owner's "largest donor in a county race" query fail — that query is
now answerable from `contributions.csv` for the 2024 + 2026 cycles.

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
are exactly reproduced by an itemized sibling filing — table in `CLAUDE.md`). The 2022 EasyVote
cycle and the 2016–2021 WAF gap still have **no** itemized layer.
Itemized donor lines for the 2022 cycle remain untranscribed
in these two eras. See "Stated-totals coverage" below; method and cache contract in `CLAUDE.md`.

## Where county campaign-finance filings live — three eras

| Channel | System | Years | Result |
|---|---|---|---|
| **(a) Legacy PDFs** | `slco.org/clerk/financialDisclosurePDF/…` (listed on the county clerk "Salt Lake County Offices" page) | ~2006–2015 | ✅ **547 PDFs** downloaded. RAW only — **all effectively image-only for values** (see the corrected finding below); no itemized data. |
| **(b) Disclosure portal** | `disclosure.saltlakecounty.gov` (state-software MVC clone; `disclosure.slco.org` 301s in) | ~2015–2021 | ❌ **WAF-blocked** to all scripted access; Wayback has folder metadata but NOT the itemized `/Report/{id}` pages. Browser/GRAMA lead. |
| **(c) EasyVote** | `saltlakecountyut.easyvotecampaignfinance.com` → `ecf-api.easyvoteapp.com` | 2022–2026 | ✅ **442 redacted PDFs + full ITEMIZED JSON** (structured layer built). |

## Sources checked (each URL / query, and the result)

| Source | URL | Result |
|---|---|---|
| Clerk — County Offices disclosure listing | `saltlakecounty.gov/clerk/elections/financial-disclosures/salt-lake-county-offices/` | ✅ 173 candidate headers → **547 unique county PDFs** on `slco.org/clerk/financialDisclosurePDF/`. Downloaded all. |
| Clerk — legacy PDF host | `slco.org/clerk/financialDisclosurePDF/{candidate,2008County,…,2015Disclosures,Archives}/*.pdf` | ✅ plain GET (browser UA) works; 547 fetched, 0 errors (as of build). |
| County disclosure portal (live) | `disclosure.saltlakecounty.gov/Search/PublicSearch`, `/Report/{id}`, `/Registration/EntityDetails/{id}` | ❌ BigIP WAF: root 302→/Search; deeper paths 302-loop or **reset the connection** (curl 56). No scripted access with any UA/TLS/cookie/delay combination. |
| County disclosure portal (Wayback) | `web.archive.org/…/disclosure.saltlakecounty.gov/Search/PublicSearch/FolderDetails/{id}` | ⚠️ **folder/registration metadata archived** (135 FolderDetails, EntityDetails, Dissolution captures) but the itemized **`/Report/{id}` pages were NOT crawled** (playback = 404). Recovers *who filed which years*, not dollar figures. |
| EasyVote SPA + API | `ecf-api.easyvoteapp.com/advancedsearch/{contributions,distributions}/{customerId}` | ✅ **HIT — full itemized JSON** (no auth; browser UA required; the flagship structured source). |
| `disclosures.utah.gov` | LG state search | State candidates/PACs only — county municipal filings are NOT here (filed with the County Clerk). |
| `disclosures.utah.gov/Municipal/salt lake` | LG state municipal tree (checked per coordinator tip re: county filings hiding under a town-of-residence folder) | ❌ **NEGATIVE for county offices.** Even-year folders (2010/2018/2020/2022/2024/2026) are EMPTY; no 2016 folder. Only ODD-year folders are populated, with **CITY** municipal candidates (16 SLCo cities) — a lead for city CF, not county. SLCo county filings are not in the state system (unlike Juab's). |

## Coverage by cycle (county offices)

| Cycle | Channel | Filings | Structured itemized? |
|---|---|---|---|
| 2006–2015 (each even-year county election + interims) | (a) legacy PDFs | 547 | No itemized layer — **stated totals vision-transcribed for ALL 547** (496 with printed totals, 51 no Summary Page) |
| **2016 / 2018 / 2020** | (b) portal | itemized (exists) | **NOT ACQUIRED — WAF gap** |
| **2024** (incl. reports filed in 2025) | (c) EasyVote | 98 itemized filings | ✅ 4,121 contrib rows |
| **2026** | (c) EasyVote | 66 itemized filings | ✅ 835 contrib rows |
| 2022 | (c) EasyVote | PDFs only (123 docs in the cycle; 87 dated 2022 + 36 dated 2023) | ⚠️ redacted PDFs stored; **no keyed itemized data** in the API for 2022 — **stated totals now vision-transcribed for ALL 123** (122 with printed totals, 1 no Summary Page) |

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

**Itemization status for these two eras (updated 2026-08-03):** the Schedule A/B donor and vendor
lines for **2006–2015 are now COMPLETE** — all 496 filings with a Summary Page, 22,871 rows — so
"who gave to whom" is answerable for that era as well as 2024/2026. **2022 remains
untranscribed** (its EasyVote PDFs are flattened redacted images with the schedules redacted), and
2016–2021 remains the WAF gap. The vision caches carry the rows in the
`contributions`/`expenditures` lists the totals tranche shipped empty — no schema change was
needed, exactly as designed.

**Structured totals (2024 + 2026, county offices):** 4,956 itemized contributions
(**$1,905,741**) + 3,278 expenditures (**$1,633,769**) across 164 filings. Largest single
contribution: a $70,000 self-loan (Christopher Stavros, Assessor 2024); largest external donor
to one candidate: Shawn Robinson (District Attorney 2026, $34,000 in one gift).

## Honest gaps

1. **2016–2021 itemized data (channel b) — NOT ACQUIRED.** The county disclosure portal is
   WAF-blocked to every non-browser client and Wayback never crawled its `/Report/{id}` itemized
   pages. This is a genuine ~3-cycle gap (2016, 2018, 2020 county elections). Recoverable ONLY via
   the `claude-in-chrome` browser skill against the live portal or a GRAMA request to the Clerk.
   The `/Report/{id}` URL pattern + the archived folder inventory make a browser pass turnkey.
2. **2022 EasyVote cycle — PDFs but no ITEMIZED rows.** The 123 county documents in the 2022
   cycle are stored as redacted PDFs (in `raw/easyvote/`) but return no itemized rows from the
   API — so the itemized layer starts at 2024. **Stated totals for all 123 are now
   vision-transcribed** (table above), but every filing's DONOR DETAIL is still only in the
   image-only PDFs.
3. **Image-only text sidecars deferred.** Every filing in both non-structured eras is
   image-only for VALUES (see the correction above — `format=text` here means "has a font
   layer", not born-digital). Full text sidecars for the scans remain deferred; the vision
   tranche transcribed **stated totals only**, not page text and not itemized lines.
   The 2024/2026 EasyVote money data is unaffected — it comes from the structured API, not OCR.
4. **ITEMIZATION for 2006–2015 and 2022 — NOT TRANSCRIBED.** Stated-totals coverage is complete
   (670 of 670), so "how much did this filing report" is answerable for every filing in both
   eras; "who gave it" is not. The Schedule A/B lines remain image-only. The vision caches carry
   empty `contributions`/`expenditures` lists sized for exactly that follow-on tranche.
5. **Six legacy/2022 source PDFs are damaged or blank upstream** (listed under Stated-totals
   coverage above); re-fetching by URL is exhausted, GRAMA is the only remaining route.

## OUT OF SCOPE (inventoried, NOT acquired) — leads for the coordinator

- **Local School Boards** — the clerk's `…/financial-disclosures/local-school-board/` page + the
  EasyVote portal carry school-board candidate filings (Canyons, Granite, Jordan, Murray, Salt
  Lake City/District school boards). Present in the EasyVote `documentsearch` (excluded from this
  county-office build). Not a county office → out of scope; a future school-board CF entity could
  reuse the same EasyVote API recipe.
- **Metro Township Councils (BONUS lead — see below).**

## BONUS — Metro Township Councils historical disclosures (report-only, NOT acquired)

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
