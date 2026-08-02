# Juab County campaign finance — RECON (exhaustive-channel determination)

**As-of 2026-08-01.** Task: determine whether Juab **COUNTY-OFFICE** campaign financial
disclosures (Commission ×3, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer)
exist anywhere public, and if so acquire them. A prior recon (also 2026-08-01) concluded "no
public posting — juabcounty.gov links no disclosures; the state system's juab folders are sparse
and city-labeled." **That conclusion was a FALSE NEGATIVE.**

**Determination: DATASET — 27 county-office filings acquired**, 2010 / 2014 / 2020, plus a
defensible negative for every other cycle. Details in `AVAILABILITY.md`.

## The finding that overturned the prior recon

`disclosures.utah.gov/Municipal/juab` is labelled **Municipal** and its subfolders are labelled
with **town names** (Nephi, Mona, Levan, Callao, Eureka, Rocky Ridge). That labelling is what the
prior recon read as "city-labeled" — but it is the candidate's **town of residence**, not the
office's jurisdiction. Opening the files shows the **even-year** folders hold filings on the
**county** form:

> **FINANCIAL CAMPAIGN REPORT** — "The financial campaign law is in the **Utah Code reference
> 17-16-6.5**" — filed **TO … County Clerk** — form 5-5-PG, Carr Printing Company

Utah Code **17-16-6.5** is *Campaign financial disclosure in county elections*. Municipal
disclosure is 10-3-208; school board is 20A-11-1301..1305. The form header is the only reliable
discriminator, and it is only visible **inside** the PDF (every file is an image scan —
`pdftotext` returns 0 characters on all 82). This is the Weber County pattern the task warned
about, in a sharper form: not aggregate PDFs, but **individually-named county filings shelved
under a municipal tree and sub-foldered by residence town.**

Even-year folders are the county-office suspects; odd-year folders (2009, 2013, 2017, 2019,
2021, 2023, 2025) are genuine municipal cycles and were confirmed municipal-only.

## Channel-by-channel

### 1. juabcounty.gov (current CMS) and co.juab.ut.us (legacy)

| URL | Result |
|---|---|
| `juabcounty.gov/departments/clerk-auditor/` | 200. No filings. Links to `/disclosures/`. |
| `juabcounty.gov/residents/election-information/` | 200. No filings. |
| `juabcounty.gov/residents/election-information/election-results/` | 200. Results only. |
| `juabcounty.gov/residents/election-information/election-forms/` | 200. Voter-registration forms only. |
| **`juabcounty.gov/disclosures/`** | 200. **The county's entire CF surface is one link, "Campaign Finance Reports", pointing at a SharePoint workbook — see below.** |
| **`juabcounty.gov/residents/election-information/financial-disclosures-2024/`** | 200. Page titled "Financial Disclosures – 2024". Contains a deadlines PDF and a button reading **"Submit Financial Disclosure Online (Coming Soon)"**. **No filings.** |
| `juabcounty.gov/.../running-for-office-2024/` | 200. Links the 2024 page above + the state candidate guide. |
| `juabcounty.gov/wp-content/uploads/2023/12/Financial-Disclosure-Deadlines.pdf` | 200. Deadlines only, no filings. |
| WP REST search (`campaign finance`, `financial disclosure`, `disclosure`) | 200. Returns exactly the 3 pages above — nothing else on the site mentions campaign finance. |
| WP REST media library (`search=financ`) | 200. **Exactly 1 asset repo-wide**: the deadlines PDF. No candidate-named PDFs exist in the media library. |
| `co.juab.ut.us` (legacy host) | **Connection timed out** — host is dead. Wayback only (see §3). |

**The SharePoint register — AUTH-WALLED.** The "Campaign Finance Reports" link on
`/disclosures/` resolves to
`https://juabcounty-my.sharepoint.com/:x:/g/personal/carlaw_juabcounty_gov/EaDx-3j6IphHuXUIgl7p1LcBrhlZaGOzLbjCatGWnVRDdQ?e=AFVzJw`
— a personal-OneDrive share of an Excel workbook. Fetched plain and with `&download=1`: both
return Microsoft's **"Sign in to your account"** page (HTTP 200, `text/html`). It is **not
publicly readable**. Recorded as a live-but-walled channel, never as a gap that was "filled".
This is the single highest-value GRAMA target (see `AVAILABILITY.md`).

### 2. disclosures.utah.gov / municipal.utah.gov — THE PRODUCTIVE CHANNEL

Every folder under `/Municipal/juab` was opened (13 year folders, 26 subfolders, recursively).
Files are served from `http://municipal.utah.gov/juab\<folder>\<file>.pdf` (backslash separators
in the published href; URL-encode as `/`).

| Folder | Subfolders | Files | County-office content |
|---|---|---|---|
| `juab_2008` | School Board | 34 | none (school board only) |
| `juab_2009 Primary` | — | 8 | none (municipal) |
| **`juab_2010 primary`** | — | **29** | **12 county-office filings** + 17 school board, interleaved |
| `juab_2013 Municipal` | Mona | 3 | none (municipal) |
| **`juab_2014`** | Callao, Eureka, Levan, Mona, Nephi | **17** | **12 county-office filings** + 5 school board |
| `juab_2017` | Eureka, Levan, Mona, Rocky Ridge, Santaquin | 12 | none (municipal) |
| `juab_2019` | Levan Town, Rocky Ridge Town | 5 | none (municipal) |
| **`juab_2020`** | Primary | **2** | **3 county-office filings** (2 multi-filing bundles) + 1 school board |
| `juab_2021` | Eureka/Levan/Mona/Nephi/Santaquin/Rocky Ridge | 26 | none (municipal) |
| `juab_2023` | Levan, Mona, Nephi, Rocky Ridge | 26 | none (municipal) |
| `juab_2025` | — | **0 files** | empty folder |
| `juab_2026` | — | **0 files** | empty folder |

**Unlinked-folder probe.** `juab_2011/2012/2015/2016/2018/2022/2024`, `juab_2012 primary`,
`juab_2016 Primary`, `juab_2018 Primary`, `juab_2022 Primary`, `juab_2024 Primary`,
`juab_2020_General`, `juab_2014_Primary`, `juab_2025_Primary`, `juab_2026_Primary` — all return
HTTP 200 with **zero items**. The system creates an empty page for any folder name; **no hidden
county-election-year folder exists.** So the county-office record on the state system is
**2010, 2014, 2020 only** — 2012, 2016, 2018, 2022, 2024 and 2026 are genuinely absent.

**Rocky Ridge 2017** is a real empty folder (listed, 0 files) — a municipal gap, noted only
because it shows empty folders are published as such.

### 3. Wayback Machine

| Target | Rows | CF-relevant |
|---|---|---|
| `juabcounty.gov*` | 5,013 archived URLs | 2: `/disclosures/` (2025-02-23) and the deadlines PDF. **No filings ever captured.** |
| `co.juab.ut.us*` | 3,917 archived URLs | **ZERO** matches for `financ|disclos|campaign`. The legacy county site never published disclosures. |
| `disclosures.utah.gov/Municipal/juab*` | 37 folder captures 2015–2025 | Folder set identical to live — **no folder was ever removed.** |
| `municipal.utah.gov/juab*` | 154 distinct archived PDFs | Diffed against the 162 live-listed PDFs: **2 archive-only URLs**, both apostrophe-encoding variants of Mona-City-2021 files that ARE live under their canonical names. **Zero real losses.** |

Wayback therefore adds **nothing** — and, more usefully, confirms the live state is complete
rather than decayed.

### 4. Utah Public Notice (PMN)

Browsed the **complete Juab County notice history**: entity `Juab County`, 2008→2026, paginated
via `startingRow` (page size 25), **802 notices** retrieved. (Note for future work: the PMN
search form fields are `entityName / publicBodyName / title / agenda / tags / startDate /
endDate` — a `keyword` param is silently IGNORED and returns an unfiltered entity browse, which
looks like a successful keyword search. Dates are `YYYY-MM-DD`.)

**No disclosure filings ride PMN attachments.** Two notices matched `campaign|disclos|financ`,
and they are the legal-framework finding of this recon:

- **2024-10-21 — "Notice of Adoption of Ordinance Establishing Campaign Financial Reporting
  Requirements"** (notice `948361`): *"The Juab County Commission hereby gives notice of its
  intent to adopt an ordinance establishing campaign financial disclosure requirements. The
  ordinance mandates separate campaign financial institution accounts, sets campaign financial
  reporting deadlines, states required campaign financial statement contents, states penalties
  for failure to timely file … **A complete copy of the ordinance is available at the county
  clerk's office for public review.** Commissioners Marty Palmer, Clint Painter, and Marvin
  Kenison voted for the adoption."*
- **2025-02-03 — "Notice of Ordinance Renumbering Campaign Financial Reporting Ordinance"**
  (notice `971141`): renumbers **Chapter 2-11 → Chapter 2-12** (Campaign Financial Reporting),
  *"No changes will be made to the wording."*

So Juab County adopted its own campaign-finance ordinance only in **October 2024** — after every
filing in this dataset. Both notices carry contact **Tanielle Callaway, taniellec@juabcounty.gov,
160 N Main, Nephi**.

**Ordinance text not machine-retrievable.** The County Code lives on CivicLinq
(`hosting.civiclinq.com/juabcounty/books/county-code/preface`), a JavaScript SPA whose content
API is not discoverable from the served bundle (`/assets/index-B8Aac4Hi.js`; `/api/*` paths all
return the SPA shell). Chapter 2-12 could not be read. The two PMN notices above are the
primary-source record; per the county's own notice, the full text is available **only at the
clerk's office**. Queued as a GRAMA item, not asserted from a secondary source.

### 5. General web search

Searches for Juab County commissioner campaign financial disclosures / the Chapter 2-12
ordinance surfaced no independent posting location, no news coverage naming one, and no
third-party mirror. Results pointed back to `juabcounty.gov`, the county directory, and
`disclosures.utah.gov/Municipal/juab_2023_Nephi` — i.e. the channels already exhausted.

## What was acquired

82 PDFs (every file in the four even-year folders), byte-verified, each with source URL, fetch
timestamp and sha256 in `index.csv`:

- **26 files carrying 27 COUNTY-OFFICE filings** — the dataset.
- **56 school-board files** — Juab and Tintic School District candidates. Out of scope for county
  government (separate taxing entities) but acquired and indexed, because the state folders
  interleave them with county filings and only the in-document form header separates the two.
  Not transcribed. The 2008 folder's 34 files are classified from the folder label plus one
  sampled form header — recorded honestly as such in `index.csv.classification_basis`.

Odd-year (municipal) folders were **not** downloaded: they are Nephi/Mona/Levan/Eureka/
Rocky Ridge/Santaquin city candidates, out of scope here, and belong to the city modules.
