# RECON — Washington County COUNTY-OFFICE campaign finance

**Recon date: 2026-08-01.** Scope: campaign Contribution & Expenditure (C&E) filings by
candidates for and holders of **Washington County county offices** — Commission Seats A/B/C,
Attorney, Clerk/Auditor, Sheriff, Assessor, Recorder, Treasurer. **Local School Board is OUT
of scope** (it shares every channel below; see `AVAILABILITY.md` for the excluded ledger).

Entity context: `washington_county` is a **db-less LIGHT+** entity (root `CLAUDE.md`). This
dataset is a document + text corpus with an `index.csv`; it federates without a per-entity db.

---

## 1. Who holds the record, and why it is the county

County-office C&E reports are filed with the **County Clerk/Auditor** and posted by the county
under **Utah Code 17-16-6.5** (county officers / county-office candidates) — the online-posting
duty was created by **HB 29 (2008 General Session, effective 2008-05-05)**, which the county's
own 2008 page cites verbatim:

> "House Bill 29 … requires any Financial Campaign Reports filed in Washington County to be
> posted on the internet. Washington County will post the candidate's financial disclosure on
> our county website, within seven (7) days after the report is filed."
> — `washco.utah.gov/clerk/campaignReporting.php`, Wayback `20080822000949`

**HB 29 (2008) is therefore the true origin of the online record.** Anything printed for an
earlier year exists only as a later-scanned "historic annual report" re-posted by the county
(the deepest is a **2006** report — see §2A).

### The state site is NOT empty for county offices — checked under the FORM-HEADER rule

The **Lieutenant Governor's** site (`disclosures.utah.gov` → files on `municipal.utah.gov`)
looks municipal-only from its folder names. **It is not.** Acting on the coordinator's
residence-town-folder warning (from the Juab build, where a county sheriff filing sat inside
`juab_2014_Mona`), the whole `/Municipal/washington*` tree was walked recursively — **83
folders, 673 links, 570 state-hosted PDFs** — and every PDF was classified by the **form
header printed inside it**, not by its folder label. Image-only files (most of them) were
rendered and OCR'd for the header.

**The discriminator actually used:**

| Marker in the form header | Means |
|---|---|
| `FINANCIAL CAMPAIGN REPORT` + `Utah Code reference 17-16-6.5` + `To … County Clerk` | filed with the **County Clerk** |
| `CAMPAIGN FINANCIAL REPORT` + `(City Recorder / Town Clerk)` + `(Municipality)` / 10-3-208 | filed with a **city/town** — out of scope |

⚠ **The header rule CUTS BOTH WAYS — it is supporting evidence, never a classification.**
The county-clerk form is handed to more people than county-office candidates:

- **Local School Board** candidates file on it (they also file under 17-16-6.5) — so the
  header **false-positives** on school board, which this scope excludes;
- so do **special districts** — this county's clearest instance is
  `/Municipal/washington_**2021**_Northwestern Special Service District`, **6 filings whose
  header reads "WASHINGTON COUNTY CANDIDATE FINANCIAL CAMPAIGN REPORT / The financial
  campaign law for Washington County…"** while the candidates are NWSSD board candidates in
  an **odd** year. Exactly the false-positive class the Summit build reported (29 such files
  there).

**The rule this dataset actually applies** (header = evidence, office line = decision,
parity = check):

1. **Decide on the stated office.** `office` is read from the form's own
   **"Name of Office" / "Candidate for Office Of"** line, or the born-digital
   summary/ledger table's `Office` column. The header only tells you *which clerk* took
   the filing.
2. **Fall back explicitly, never silently.** If the document's office line is unreadable
   (the 2006–2025 forms are handwritten), fall back to the archived listing page's office
   heading, then to the filename — and record which was used in
   `office_source` / `office_confidence` (`document` = high, `portal_listing` = medium,
   `filename` = low). A row whose office cannot be established **at all** is held OUT of
   `index.csv` and ledgered in `unrecovered.csv` — never guessed.
3. **Check cycle parity.** Washington County offices are elected in **even years only**.
   `index.csv` therefore carries `cycle_year` (from the form's printed "Election Year", or
   derived for a January year-end close, else blank) and `cycle_parity_flag`. **Every
   county-office row in this dataset resolves to an EVEN cycle year; zero parity flags.**
   Odd-year folders are treated as municipal-suspect and none contributed a row.
4. An **odd _reporting_ year is normal** and is not flagged: the county's **annual**
   officeholder report is filed every January, so 2011 / 2015 / 2025 reporting years are
   expected for `filing_type=annual` and carry a blank `cycle_year` rather than a guess.

**What the sweep found — two folders whose labels lie:**

| Folder | Label says | Actually contains |
|---|---|---|
| `washington_2008_**Local School Board**` | school board | **County Commission** filings — Alan Dean Gardner (Sept, Oct 2008) and Linden Haner Alder (= "Lin Alder"; Sept, Oct 2008). Header-verified `17-16-6.5`; one prints "County Commission Seat". |
| `washington_**2010 Elections**` (flat, no town subfolders) | an election-year folder | **the entire 2010 county-office field**, header-verified: Brock Belnap (**County Attorney**), Cory Pulsipher (**County Sheriff**), David Whitehead (**Treasurer**), Russell Shirts, Kim Hafen, Denny Drake, James Eardley, Arlin Hughes, Slade Hughes, Greg Aldred, Kevin Brooks (×2), Rob Tersigni, Steven Despain, **Cyril Noble** — plus 4 school-board filers on the same county form. |

These are **April/May 2010 and Sept/Oct 2008 filings that the county's own site does not
hold** (the county channel's 2010 folder starts at 6-15-2010, and its 2008 page links only the
June/Aug/Oct/Dec set). **Cyril Noble** appears in no county-site channel at all. So the state
site is a genuine **gap-filler for the county tier**, not a redirect — the opposite of the
finding recorded for Lehi and St. George, where the state merely pointed back at the city.

**Where the state site IS a redirect** (verified, no documents):

| Probe | Result |
|---|---|
| `…/washington_2012` | **link-only** → `washco.utah.gov/clerk/electFinancialReport.php` |
| `…/washington_2020_General` and `…_Primary` | **link-only** → `…/forms/clerk-auditor/elections/campaign-financial-reports.php` |
| `…/washington_2022` | **link-only** → the same county page |
| `…/washington_2024` | one `St. George` subfolder (municipal), 2 PDFs |
| `…/washington_2025`, `…_2026` | link lists to city/town and district pages; the only county link is the **Conflict-of-Interest** page (out of scope) |

The odd-year folders (2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023) are municipal-election
folders sub-divided by city/town; every PDF in them that was header-checked came back
municipal. **Residual risk is stated honestly in `AVAILABILITY.md`** rather than assumed away.

> **PMN was not used as a channel here.** Campaign-finance filings are not public-meeting
> notices and PMN publishes none for this county. (Recorded for the next agent: the PMN JSON
> POST **silently ignores a `keyword` param** and returns an unfiltered entity browse that
> looks like a hit — a keyword-based negative from PMN is not a real negative. Honored fields
> are entityName / publicBodyName / title / agenda / tags / startDate / endDate, dates
> `YYYY-MM-DD`, paginated by `startingRow` at 25/page.)

---

## 2. Channels found (five URL generations of one dataset)

The county has migrated its CMS repeatedly. The same logical dataset lives under **five**
different URL shapes; only the newest two are reachable live, the rest survive only in the
Internet Archive.

### A. LIVE — the current WordPress page (PRIMARY)
`https://www.washco.utah.gov/departments/clerk/elections/campaign-financial-reports/`
→ HTTP 200 (needs a browser `User-Agent` **and** `Referer: https://www.washco.utah.gov/`;
the county host 403s plain fetchers — the same gotcha the minutes corpus records).

Two tables, and the page states its own semantics:

> "† Annual Reports are submitted each January for prior year funds – **year is reporting
> period**."

- **Annual reports table** — one row per *current* elected official, linking that official's
  most recent January filing (the "2025" label = **calendar-2025 activity, filed Jan 2026**;
  files under `/wp-content/uploads/2026/01/`).
- **Historic Reports table** — the same officials' earlier filings, re-uploaded under
  `/wp-content/uploads/2026/05/` with `<year>-<Name>.pdf` names, **plus** live
  `outpost.washco.utah.gov/apps/clerk/elections/2024/reports/<…>.pdf` links for the 2024 cycle.
  Depth reaches **2006** (Treasurer Whitehead).

**Structural limit of this page (important):** it is organised by **CURRENT OFFICE HOLDER**,
not by election. Defeated candidates, retired officials and prior-cycle filers are **not
listed** — e.g. the entire 2020 Recorder field (five challengers) and the 2018 Attorney and
Sheriff races are absent. The live page alone therefore under-represents every contested race.
Recovering those is what §2C–E are for.

### B. LIVE — `outpost.washco.utah.gov` (the file host behind the 2024 links)
`https://outpost.washco.utah.gov/apps/clerk/elections/<year>/reports/<file>.pdf`
Directory listing is **disabled**: `/2018/`, `/2020/`, `/2022/`, `/2024/` return **403**
(they exist), `/2016/` and `/2026/` return **404** (they do not). So outpost is fetch-by-known-URL
only — it can be *read* but not *enumerated*. Enumeration must come from the county page or the
Archive. **Wayback has zero captures of the `outpost.` host** (CDX: 0 rows), so a link that has
fallen off the county page and lives only on outpost is recoverable *only* while the county
keeps linking it.

### C. WAYBACK — `washco.utah.gov/forms/clerk-auditor/elections/<year>/reports/` (2016–2024)
The previous CMS generation. The **listing page** for it
(`…/elections/campaign-financial-reports.php`) was **never archived with content** (every CDX
row is 404/403/301/302 — the county's `robots.txt`/error behaviour blocked it), but the
Archive did crawl the **files**: 2016 (29), 2018 (31), 2020 (36), 2024 (25). This is the
channel that restores the **defeated candidates** the live page drops.

### D. WAYBACK — `washco.utah.gov/clerk/pdf/financialreports/` (2011–2015) and
`washco.utah.gov/clerk/electAdmin/pdf/` (2011)
The pre-WordPress clerk site. **454 archived files.** Two eras inside it:
- **2011–2012 = PDF**, split three ways per filing: `Contributions - <Name>_<date>.pdf`,
  `Expenditures - <Name>_<date>.pdf`, `County Candidate Summary - <Name>_<date>.pdf`.
- **2014–2015 = `.xls`** (real Excel workbooks, **machine-readable — the only born-structured
  material in the whole county record**), same three-file split.
The `electAdmin/pdf/` variant is the same 2011 files at their original path; **Wayback returns
401 for every one of them**, while the identical files under `clerk/pdf/financialreports/`
return 200 — so the `financialreports` path is the one to use.
Listing pages **were** archived here: `clerk/electFinancialReport.php` (13 distinct captures
2012–2016) and `clerk/2008campaignReporting.php` (6 captures) — these are the enumeration keys.

### E. WAYBACK — `washco.utah.gov/clerk/pdf/` + `clerk/pdf/2010elections/` (2008–2010)
The original HB-29 implementation.
- `clerk/campaignReporting.php` (38 captures, 2008-08 → 2010-11) is a **rendered HTML report**:
  it prints each candidate's office, submission date and **inline dollar totals**
  (contributions / expenditures / balance, split "Beginning Balance" vs "Party Convention"),
  then links `Detailed Contribution Report` / `Detailed Expenditure Report` PDFs. The totals in
  the HTML are a **second, independent statement of the same numbers** in the linked PDFs —
  a built-in reconciliation anchor.
- `clerk/pdf/2010elections/` — **144 archived files** for the 2010 cycle (`6-15-2010
  Contributions - <Name>.pdf` etc.).

### Channels checked that yielded NOTHING for county offices
| Channel | Result |
|---|---|
| `disclosures.utah.gov` (LG municipal) | Municipal only; `washington_2022` is a link back to the county (§1) |
| `outpost` directory listings | 403 (exists, not listable) / 404 (absent) |
| `…/elections/campaign-financial-reports.php` in Wayback | 14 captures, **all** 404/403/301/302 — never archived with content |
| Wayback on the `outpost.` host | **0 captures** |

---

## 3. Aggregate shape of the record

Enumerated candidate URLs before scope filtering — **803** (72 live page links + 731 unique
Wayback 200-captures), spanning **2006, 2008, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2018,
2020, 2022, 2024, 2025**. Roughly a third are Local School Board (out of scope, ledgered).

**Format reality — the county's PDFs are scans.** Every PDF sampled across every era
(2006 historic, 2024 outpost, 2025 annual) yields **zero characters** from
`pdftotext -layout`: they are image-only. Only the **2014–2015 `.xls`** generation is
born-structured. This sets the extraction plan: OCR sidecars for the PDF eras, direct cell
reads for the `.xls` era, and the 2008-era HTML totals as an independent cross-check.

## 4. Filing vocabulary observed in filenames (to be verified from document content)

`FCR` = Financial Campaign Report (the periodic pre-primary / pre-general report) ·
`Final` / `FINAL` = the closing report · a bare `<Month> <day> <year>` = that statutory
deadline's report · the January `<Name>-Financial-0126.pdf` files = the **annual** officeholder
report. The 2008 page prints the statutory calendar directly: **May 15** (state school board),
**Jun 17** (7 days pre-primary), **Aug 31**, **Oct 28** (7 days pre-general), **Jan 10** (year-end).

**Portal labels lie — every office/candidate/date in this dataset is verified from the document
itself**, never from the link text. Two label defects were already visible during recon:
- the live page's Assessor row links `2020-Tom-Durrant.pdf` under the label **`12-07-2024`**
  (the same file also appears, correctly, as `2020`);
- the Treasurer row labels `2011-David-Whitehead.pdf` as **`2012`**;
- one Recorder link (`Gary L_01-08-2025. Christensen_Recorder_Final`) carries **no file
  extension** (it serves a PDF anyway).

## 5. Excluded by scope
Local School Board districts 1–7 (all channels) · judicial retention filings seen in the 2024
folder (5th District Court, 5th District Juvenile Court, Justice Court) · officeholder
**Conflict-of-Interest** annual disclosures (`/wp-content/uploads/2026/01/<Name>-Conflict-of-
Interest-012026.pdf`, one per official) — a different document class, excluded by
`scripts/campaign_finance/SCHEMA.md` ("Annual financial / conflict-of-interest statements are
out of scope") · municipal (city) candidate filings, which belong to the cities.
