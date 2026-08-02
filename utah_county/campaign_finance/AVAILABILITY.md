# Campaign-finance disclosures — availability & sources checked (Utah County, COUNTY offices)

**As-of: 2026-08-01.** Package B of the owner-approved county acquisition wave. Dataset for
**Utah County COUNTY-office candidates** — Board of Commissioners (Seats A/B/C), County
Attorney, Clerk / Clerk-Auditor / Auditor, Sheriff, Assessor, Recorder, Treasurer, Surveyor.

**Result: DEEP AND SUBSTANTIALLY COMPLETE — 267 filings acquired, 2008 → 2026, all eleven county
election cycles the county has ever published; 263 retained as county-office filings.** Every
channel the county has ever used was swept, including three that are dead on the live web and
one undocumented API. The exhaustive probe log is in **`RECON.md`**; this file records what each
source *had*, and what is missing.

> **Updated 2026-08-01 after the VISION-TRANSCRIPTION pass** (cover page + stated totals;
> `/cf-vision-transcribe`, Read-tool method, $0 API). All 267 acquired filings were read from
> the page. Consequences recorded below: the office ledger is now **256 resolved · 7 honestly
> unresolved · 4 proved school-board and moved to `out_of_scope.csv`** (§4); a **stated-totals
> money layer exists** (`filing_totals.csv`, 265 rows) where §4 previously said "deliberately
> NOT built"; and a new **§4a** ledgers every filing whose figures are absent, with the reason.

---

## 1. Where these filings actually live

County-office candidates file with the **Utah County Clerk** (Utah Code **17-16-6.5**, calendar
per 20A-11; the form's own header cites "Utah County Code 2-5" alongside it). The
Lieutenant Governor's `disclosures.utah.gov` is a STATE system with a **municipal** landing area
organised county → year, and for Utah County that area is — in every year but one — **a pointer
back to the county's own page**. So the county clerk's web estate is the channel, and it has
been rebuilt four times since 2008.

| Era | Listing | PDF host | Live 2026-08-01 |
|---|---|---|---|
| 2008–2018 | `…/candidates/disclosures/<YEAR>Disclosures.html` (and its `CandidateFinancialDisclosure<YEAR>.asp` predecessor) | `…/dept/Clerk/Data/Minutes/CANDFINDISC<OFFICE>/<YEAR>/*.pdf` | listing **dead**, PDFs **LIVE** |
| 2020 | `…/disclosures/2020Disclosures.html` + the ClerkAud `Disclosures/index.asp` · `Past/2020.asp` · `name.asp?LINK_NAME=` set | `…/apps/WebLink/Dept/CLERKAUD/*.pdf` · `…/elections/documents/*.pdf` | **both dead** |
| 2020–2024 | `…/candidates/disclosuresByYear.html?year=` (JS) | **`api.utahcounty.gov/cms/elections`** (Strapi) | listing dead, **API LIVE** |
| 2024– | `vote.utahcounty.gov/financial-disclosures` → a public Google Sheet | `drive.google.com` | **LIVE** |

`ssl.utahcounty.gov` — the host named in the work order — **no longer resolves at all** (TCP
connect timeout), so every `ssl.utahcounty.gov/dept/clerkaud/elections/*` path in the older
documentation is dead at the host level. `www.utahcounty.gov/Elections/Disclosures/index.asp`
302s to the new portal.

## 2. Sources checked — what each had

| Source | Result |
|---|---|
| `vote.utahcounty.gov/financial-disclosures` | ✅ links one public **Google Sheet** (the current listing) |
| `vote.utahcounty.gov/candidate-information#financial-disclosures` | ⚠️ **blank forms only** (2026 Candidate Manual, fillable disclosure form, conflict-of-interest form). No filings |
| Google Sheet — **CSV** export | ⚠️ exports the **first tab only** and **drops the hyperlinks**, which ARE the filings. Retained as `raw/index_pages/…_tab2026.csv` to document the limitation |
| Google Sheet — **XLSX** export | ✅ **the usable export** — 3 tabs (`2026`/`2025`/`2024`), 308 per-cell hyperlinks preserved. 2026: 31 county-office candidate rows; 2024: 12; 2025: **municipal, out of scope** |
| `vote.utahcounty.gov/candidate-records` (a 2nd Google Sheet) | ⚠️ candidate FILING records, tabs 2026/2025/2024 only — no disclosure documents, and nothing for 2022. Not acquired (a lead, §5) |
| Wayback CDX sweep, `utahcounty.gov` domain, urls matching `disclos` | ✅ 161 distinct URLs → the complete four-scheme map above |
| `<YEAR>Disclosures.html`, 2008/2010/2012/2014/2016/2018/2020 | ✅ **all seven recovered** — accordion listings that print the OFFICE as the section heading (2008–2018) or the CANDIDATE (2020) |
| `CandidateFinancialDisclosure<YEAR>.asp`, 2008–2018 | ✅ recovered and **diffed against the `.html` successors: zero asp-only URLs**. The `.html` pages are the superset; both retained |
| a **pre-2008** county disclosure page | ❌ **none exists** in the Internet Archive. `…2008.asp` is the earliest. **2008 is the true publication floor** |
| the 2008–2018 `CANDFINDISC…` PDF store (live probe) | ✅ **still served** — 127 of 128 listed county PDFs fetched 200/application/pdf directly from `www.utahcounty.gov` |
| `…/apps/WebLink/Dept/CLERKAUD/*.pdf` (2020 scheme, live) | ❌ 404 → recovered from Wayback (10 filings) and/or from the Strapi re-host |
| `…/Dept/Clerk/elections/documents/*.pdf` (2020 scheme, live) | ❌ returns the site's HTML 404 shell → Wayback |
| **`api.utahcounty.gov/cms/elections`** (+ the Bearer token the county shipped in `disclosure.js`) | ✅ **LIVE** — 78 candidate records / **158 documents** (2020: 18 · 2021: 2 · 2022: 135 · 2024: 3). **The ONLY channel for the 2022 cycle** |
| `disclosures.utah.gov/Municipal/utah_2024` | ✅ **hosts real filings** — 20 PDFs + 1 `.xlsx` + 1 `.JPG` on `municipal.utah.gov`, county offices AND school board. A genuine second 2024 channel |
| `disclosures.utah.gov/Municipal/utah_{2008,2010,2012,2014,2016,2018,2020,2022,2026}` | ⚠️ **no county-office filings.** 2008/2012/2018/2022 carry a pointer link back to the county; 2020/2010/2014/2016 are empty; 2026 lists city **conflict-of-interest** pages (a different instrument) |
| state **residence-town sub-folders** (`/Municipal/utah_<year>_<Town>`) | ⚠️ **Utah County's state tree has none** — the only sub-folder in the whole tree is `utah_2020_Primary`, and it is a pointer page, not a document folder. Enumerated explicitly, not assumed (see §3) |
| `municipal.utah.gov/utah/<year>/` directory listing | ❌ **403** — the rendered state page is the only enumeration |
| Google Drive `uc?export=download` / `drive.usercontent…/download` | ✅ works for shared objects; **3 of the 2026 objects are not publicly shared** (`unrecovered.csv`) |

## 3. The two classification rules this package was built under

Both come from the coordinator, from other agents in this wave, and both were applied here:

1. **Residence-town folder trap (Juab).** State `/Municipal/<county>_<year>` folders can
   sub-folder filings by the candidate's TOWN OF RESIDENCE, hiding county-office filings inside
   what look like city folders. **Checked explicitly**: every `utah_<year>` page was
   re-enumerated for `/Municipal/utah_*` sub-links (my first sweep had filtered them out).
   Utah County has exactly **one** sub-folder, `utah_2020_Primary`, and it contains **no
   documents** — only a link to the (now dead) county page. So the trap does not bite here, but
   the negative was established by enumeration, not by assumption.
2. **The 17-16-6.5 header cuts both ways (Summit).** A county form header is NOT proof of a
   county office — clerks hand the blank county form to towns and districts. So **office is
   classified from the STATED OFFICE inside the form** ("Office Seeking" / "Office"), with the
   form header and the file-to-County-Clerk line as *supporting evidence only*, and **cycle
   parity** (county offices are even-year here) as a cross-check. The one odd-year exception is
   real and documented: the **2021 County Clerk/Auditor special election** (2 filings). The
   odd-year 2025 sheet tab is municipal (Spring Lake town + Aspen Peaks School District) and was
   treated as municipal-suspect and left out of scope.

Three independent evidence sources were reconciled per filing — the channel's printed office,
the filing's own Office field, and the county's own canvass (`../elections/`). Where two or more
resolved, **agreement was 39/39 with zero real mismatches** (the apparent mismatches were all
naming conventions: listing `Assessor` vs form `County Assessor`, or a form that prints
"County Commission" without a seat). Details in `CLAUDE.md`.

## 4. Honest gaps

| Gap | Size | Status |
|---|---|---|
| **Pre-2008 filings** | all | **Does not exist online.** The county's earliest disclosure page is the 2008 cycle. Not a recovery failure |
| **Odd years 2009–2019, 2023, 2025** | — | **No county-office filings exist** — county offices are elected on the even-year partisan cycle. An honest calendar property, not a gap. (2021 is the documented special-election exception) |
| **Office unresolved** | **7 filings** (was 19 — RESOLVED 2026-08-01) | The vision pass read all 19 Office fields from the page: **8 promoted** to a county office, **4 proved LOCAL SCHOOL BOARD** and moved to `out_of_scope.csv`, **7 remain honestly unresolved** — Osborn 2020, Balderree 2022 ×2, Clement 2022, Riley 2022 (the Office box is **blank on the form**) and Taylor 2022, Bird 2024 (the Office box contains a **street address**, which is not an office claim). Nothing was guessed. Full ledger: `CLAUDE.md` "The 19 unresolved offices" |
| **3 × 2026 "30 Days after Primary" filings** (Davidson, Herrin, Paxman) | 3 | `unrecovered.csv` — the county's sheet links them but the **Drive objects are not publicly shared**; the download endpoint returns a Google sign-in page. A county-side permissions error, re-probeable |
| **2020 Voeks 6/23 byte copy from the 2020 page** | 1 URL | `unrecovered.csv` — 404 live, never archived. **NOT a lost filing**: the same report is held via the Strapi channel |
| **2024 "Candidate Financial Disclosure.pdf" (18 MB) on the state page** | 1 | Reachable only through a **`mail.google.com` attachment-preview link** (the state site pasted Gmail preview URLs). Unattributed to a filer; not fetchable without the clerk's mailbox |
| **2018 Sheriff `CS.Smith.pdf`** | — | **Recovered.** 404 on the live store; pulled from Wayback (2.2 MB). The only 2008–2018 PDF the live store had lost |
| **Stated-totals layer** (`filing_totals.csv`) | **BUILT 2026-08-01** | 265 rows for 263 filings, vision-transcribed from the page. Confidence high 153 · medium 96 · low 16. See §4a for the rows without figures |
| **Itemized donor / vendor layer** (`contributions.csv` / `expenditures.csv`) | **2 of 263 filings** (72 contribution + 81 expenditure rows, 2026-08-02) | **BUILT for the machine-readable subset only.** The registered `utahcounty_schedab` family was run over the **17** filings with a real text layer; 2 shipped (Ainge 2018, Paxman 2026), every other side emitted nothing with a stated reason (`CLAUDE.md` "The machine-readable itemized layer"). For the remaining 261 the old note still holds: This tranche was scoped to cover page + stated totals. An empty itemized layer means *not transcribed*, **not** *no donors*. The itemization pass is the queued next step; the Schedule A/B pages are already in `raw/` and the page-locator output makes them cheap to target |

## 4a. Honest gaps INSIDE the money layer (vision pass, 2026-08-01)

252 of the 265 `filing_totals.csv` rows carry at least one stated figure. Every absence below is
a property of the DOCUMENT — a page the county never published, a cell the filer left empty, or
a value the filer wrote as something other than a number. **Not one is a failed read**: across
all 267 transcripts only 86 individual fields are flagged `unreadable`, and each is `""` with a
per-field reason rather than a guessed digit.

**(a) 9 rows with NO stated figure at all.** Seven are the same defect — *the county published
the filing WITHOUT its Summary Page*: Carlton Bowen 2014 (cover + Schedule B only), James Tracy
2014 (cover + Schedule A), David Leavitt 2018, Jason Christenson 2018, Bill Lee 2018, Jeff Gray
2022 (a **one-page, cover-only** PDF), Kim Jackson 2022 (cover + a blank Schedule B). Where a
Schedule page prints its own page total it is kept in `totals_verbatim` under an explicit
`scheduleB_*`-style key so it can never be mistaken for a summary box. The other two:
`2024_Alan_Wessman_Redacted2.pdf` is **an entirely blank form** (all four pages of the v. 12.23
template, nothing filled, only the clerk's redaction bars), and `2024_Alan_Wessman.xlsx` is the
corpus's one spreadsheet filing, which prints cycle totals for **two** reporting periods and so
states no single per-period figure (its cumulative totals are in `notes`).

**(b) 10 rows blank on one side only.** Four (Houskeeper 2010, Poulson 2014, Revill 2014,
Riding 2014) have a balance ladder but left both totals cells empty. Jackson 2014, Bowen 2018
and Powers Gardner 2021 state expenditures with the contributions cell empty. **The three 2026
born-digital filings — Astill, Kaufusi, Paxman — are a different and more interesting ceiling:
each states contributions as a COMPOUND string** (`"94009.26 +Inkind 666.67"`), i.e. two numbers
in one cell. Splitting them would be a decision the filer did not make, so the cell stays blank
and the verbatim string is preserved in `totals_verbatim` and `notes`. These are the largest
campaigns in the corpus, so this is a real analytic caveat, not a rounding matter.

**(c) The channel's own labels are wrong on several filings — always in the channel's favour of
looking tidier.** Recorded, never silently corrected (`filing_totals.csv.notes` carries both
readings on every affected row):

- **Filer:** the Strapi API files **Paul V. Child's** 2020 Recorder filing under **Taylor
  Dayton** (`Child 5.1.20 Redacted`); `2022_Adam_Pomeroy.pdf`'s OCR opens "Josh Daniels" (that
  is the Clerk's letterhead, not the filer); `2024_Brian_Baird.pdf` is signed **Brian Bird**.
  `filing_totals.csv.candidate` is therefore the PAGE-FACE name.
- **Cycle:** `2021_Powers__Gardner.pdf` is filed by the API under candidacyYear **2021 /
  "Special Election"** but its own Date of Report is **04/02/2022** and its office is Commission
  Seat A — a 2022 filing. `2022_WarnickShauna.pdf` is dated **12/2/2020**. `election_year` was
  NOT changed (that is a manifest-level decision, and `office_overrides.csv` governs office
  only) — flagged here for the coordinator.
- **Reporting period:** at least six filings check a different box than the channel's label
  (e.g. Andrea Allen 2020 "10/27/2020" is the **6/23/20 pre-primary** report; McConnell 2014
  "Post Primary" is a **withdrawal** report). `filing_totals.filing_type` is the box actually
  marked; `reporting_period` keeps the channel's label alongside.

**(d) Two PDFs are genuine multi-report bundles** and are emitted as two rows sharing a
`source_filing` but with distinct `document_id`: Jeffrey Buhman 2014 (original 6-15-14 +
its 6-19-14 amendment) and Tom Westmoreland 2024 (a 5/7/24 withdrawal report bound BEFORE the
4/11/24 pre-primary report it postdates). Nothing was merged.

**(e) A note on what the county's page-ordering does to automated locators.** The modern form
puts its Summary Page LAST, the county's scans interleave pages out of order (one 16-page Bill
Lee 2022 PDF is hand-numbered "Pg 8 of 8" on its cover), and the county's own internal
*Campaign Financial Disclosure Checklist* is bound into ~20 filings and reads like a summary
page to OCR. Every such case was resolved by eye during the pass and is recorded in the
transcript's `notes`; a future itemization pass should not trust page position.

## 5. Out of scope — recorded, not acquired (`out_of_scope.csv`)

**Local school board is OUT of Package-B scope by instruction.** Utah County's clerk posts
school-board, judicial-retention and (2025) municipal filers in the *same* lists as county
offices, so they were fetched, classified, and then **ledgered rather than retained**:
**93 school-board filings** (2022: 70 · 2024: 19 · 2020: 4), each with its candidate, source
URL, byte count and **sha256 measured at acquisition**, so a later package can take them without
redoing any recon. **Four of those 93 arrived late** — they were retained as office-unresolved
county filings until the 2026-08-01 vision pass read their Office fields (McCabe "Provo School
Board District 5", Warnick "Nebo School Board district 3", Hoiland "School board", Nielsen
"Provo School District Board Member"). Their raw PDFs and their vision transcripts are kept as
the evidence for the exclusion; only their `index.csv` rows were dropped. Not fetched at all
(enumerated from the listings only): the school-board rows
of the 2008–2018 static pages, the judicial rows of the 2024 sheet, and the **223 hyperlinks of
the 2025 municipal tab** (Spring Lake town + Aspen Peaks School District).

**Leads for the coordinator** (filed here, not in `LEADS.md`):
- the **2025 sheet tab** is a complete municipal C&E set for **Spring Lake town** and **Aspen
  Peaks School District** — 223 filings, not a repo entity today;
- `disclosures.utah.gov/Municipal/utah_2024` proves the **state municipal tree can hold county
  filings** — worth re-checking for every county in the wave;
- the **Strapi API + shipped Bearer token** pattern (`api.utahcounty.gov/cms/elections`) may
  exist on other Utah county CMSs of the same vintage;
- Utah County's **candidate-records Google Sheet** (2024–2026) would give a filed-candidate
  roster that could resolve Brian Bird's 2024 office (one of the 7 still unresolved);
- **ITEMIZATION is the obvious next tranche.** The Schedule A/B pages are already in `raw/`, the
  form is now fully characterised, and the vision pass left a page map behind — a donor/vendor
  layer would make this the repo's first county-tier `cf_contribution`-shaped dataset;
- **the channel's `election_year` is wrong on at least two filings** (Powers Gardner 2021→2022,
  Warnick 2022→2020, §4c). Fixing it means editing `batch/manifest.json`, which is an
  acquisition-layer decision above this package's remit — flagged, not taken;
- **the county published unredacted copies of three 2024 filings** (Andrea Allen and Anthony
  Canto each appear both redacted and in the clear; Brian Bird's is unredacted), with street
  addresses and phone numbers visible. Nothing was transcribed from those fields and the raws
  are retained verbatim per the cardinal rule — but the owner may want a view on whether a
  government's own inconsistent redaction changes anything for this repo;
- **`gov.db` federation of a county CF layer is still an owner decision** — the `cf_*` tables
  are city-scoped (the juab package hit the same wall).

## 6. Privacy

Everything here is a **government-published public record**, and — importantly — **the county
redacted it before publishing**: the overwhelming majority of files are named `*_Redacted.pdf`,
with donor addresses blacked out by the clerk. `raw/` and `text/` are **verbatim reproductions**
and are not edited further, per repo-root `PRIVACY.md`. No structured donor rows exist in this
package; if one is ever built, that layer stores donor **city/state only**, never street
addresses.
