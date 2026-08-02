# Cache County campaign finance — source reconnaissance (2026-08-01)

> **Acquisition recon only.** The channel findings below are unchanged, but the
> *classification* counts they end with were superseded by the **vision transcription pass
> (2026-08-01/02)**, which read every page image and moved 11 rows out of scope. Current
> ledger sizes: **index 239 · excluded 256 · unrecovered 2**. See `AVAILABILITY.md` §1 and
> `CLAUDE.md` for the live numbers.

Scope of this package: **COUNTY-office** candidate campaign-finance filings for Cache County
(FIPS 49005) — County Council (7 seats), County Executive, and the elected constitutional
officers (Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor), across
**both governance eras** (Board of Commissioners → the Council–Executive form adopted at the
2016 vote / seated **January 2019**). **School-board candidates are OUT of scope** (they file
with the same county clerk and appear interleaved on every listing page — see AVAILABILITY.md
for the ledger of what was excluded and why). Municipal (city/town) filings inside Cache County
are likewise out of scope; Utah municipalities file with their own recorders.

Statutory basis: county candidates file **Contribution & Expenditure (C&E) reports** with the
**county clerk** under Utah Code **17-16-6.5** / Title 20A Ch. 11 Pt. 5 (county candidates and
officeholders). Cache County publishes them itself; the Lt. Governor's `disclosures.utah.gov`
**"Municipal Disclosures"** tree carries a Cache County node that is a *mix* of hosted PDFs
(older cycles) and outbound links back to the county/municipal sites.

---

## Channels checked

### 1. PRIMARY — county elections site, per-year disclosure pages ✅

`https://www.cachecounty.gov/elections/financial-disclosures/` is the landing page. It links a
per-year page for **2012, 2014, 2016, 2018, 2020, 2022, 2024, 2025, 2026** (URL pattern
`.../financial-disclosures/<year>-candidate-financial-disclosures.html`; **2016 is the
exception** — `2016-financials.html`).

- Each year page renders an HTML **table** — `File | Type | Date` — where `Date` is the
  **posting/upload date** recorded by the CMS, not necessarily the statutory due date printed
  inside the filing. Treated as a *posting-date proxy*, kept in a separate index column.
- PDFs live under `.../assets/department/clerk/elections/financialDisclosures/<year>/…`.
  Directory listings 403; files fetch by exact (URL-encoded, space-bearing) filename.
- **Filenames are irregular and are NOT authority for office or filing type** — they are
  clerk-typed labels ("A Geary finance campaign.pdf", "2024 General Allen Grunig.pdf",
  "2025 Mark Hurd Financial Docusign.pdf"). Every acquired file's office/candidate/form family
  is verified from the **document body**.
- Two years carry an internal folder taxonomy that *is* meaningful and was preserved as a hint
  (still verified from content): **2012** splits by filing month (`June/ August/ October/
  December/`) and **2014** splits `CountyOffices/` vs `SchoolBoardCandidates/` vs a
  `2014-01-12/` year-end-summary folder.
- **Link inventory: 291 PDFs** (2012:28 · 2014:81 · 2016:14 · 2018:39 · 2020:17 · 2022:37 ·
  2024:31 · 2025:7 · 2026:37).

**Broken link found:** the landing page's **"2013 Financial Disclosures"** anchor points at
`trails/calendar.html` (a parks page), and the expected
`2013-candidate-financial-disclosures.html` **404s**. 2013 is an odd year = municipal-only, so
this is not a county-office gap; recorded as a site defect.

### 2. `disclosures.utah.gov` (Lt. Governor) — Municipal Disclosures → COUNTIES → CACHE ✅ partial

`https://disclosures.utah.gov/Municipal/cache` is a folder tree with **87 sub-folders**
(2008 → 2026) holding **482 file links** overall. Most sub-folders are **per-municipality**
(`cache_2021_Providence City`, `cache_2023_Smithfield`, …) and are out of scope. The tree
mixes two behaviours:

- **Hosted PDFs** (served from `municipal.utah.gov/cache\<folder>\<file>.pdf` — note the
  literal **backslashes**, which must be rewritten to `/` and percent-encoded to fetch).
- **Outbound link stubs** — e.g. `cache_2024` is nothing but a link back to the county's own
  2024 page; `cache_2008`/`cache_2010` link to the long-dead `cachecounty.org` pages.

County-office-relevant folders **with hosted PDFs**: `cache_2012 General` (21),
`cache_2012 Primary` (9), `cache_2020_General` (31), `cache_2020_Primary` (2) = **63 files**.
This is a **real gap-filler**: the county's own 2020 page lists only **17** files while the
state holds **33** for the same cycle. Fetched and deduped by content hash against the county
copies.

### 3. Wayback Machine — the legacy `cachecounty.org` era ✅ (three distinct recoveries)

The county moved `cachecounty.org` → `cachecounty.gov` and rebuilt its CMS at least twice; two
whole pre-2012 disclosure eras and one 2022-era page exist **only** in the archive.

| archived page | capture | what it holds |
|---|---|---|
| `cachecounty.org/elections/disclosures.php` | `20081207055606` | **2008** cycle — 34 filing links under `docs/elections/disclosures/`, each labelled `Surname, First (MM.DD.YY)` — the archive page supplies **exact filing dates** the live site never did |
| `cachecounty.org/elections/disclosures/2010.php` | `20101108181727` | **2010** cycle — 37 filing links under `docs/elections/disclosures/2010/`, same dated-label form |
| `cachecounty.org/elections/campaign-finance.html` | `20230528172133` | the **2022** page as the county then published it — 39 per-candidate PDFs under `assets/department/clerk/` (20 pre-primary + 19 `…22G` general) **plus** a combined `2022 Primary Financial Disclosures .pdf` covering two candidates who have no individual file |

The 2022 archived list and the *current* 2022 page **are not the same set** (the archive has
Bethany Nielson and Bret Randall; the current page has Roger R. Marce) — so both were fetched
and reconciled.

Archived PDF bytes fetch via `web.archive.org/web/<ts>id_/<original-url>` (follow redirects).
`original_url` (the county URL as published) is what the index records as `source_url`; the
Wayback wrapper is recorded separately.

Also confirmed present in the archive and **deliberately not acquired**: blank **form
templates** (`Form - Finance Campaign Report.pdf`, `Form - School Bd Finance Campaign
Report.pdf`, `Finance Campaign Report Dates.pdf`) — these are empty instruments, not filings.

### 4. Depth floor probe

`disclosures.php` captures reach back to **2008-12-07**, and the 2010-era navigation exposes
only `disclosures/2008.php` and `disclosures/2010.php` — i.e. **2008 is the earliest cycle the
county ever published online.** Pre-2008 county C&E reports are a paper-era gap at the Clerk's
office, not a retrievable channel.

### 5. Channels checked and found to hold nothing in scope

- **`disclosures.utah.gov` public/advanced search** — indexes state/legislative filers; county
  candidates route to the Municipal tree above.
- **`cache_2018` on the state site** — exists but its only children are municipal
  (Avon/Hyde Park/Lewiston/Logan/Newton/North Logan/Paradise/Providence/River Heights). The
  county's 2018 candidates are on the county site only.
- **`cache_2022` on the state site** — a link stub to the (now dead) county
  `campaign-finance.html`, recovered via channel 3 instead.

---

## What the year pages actually contain (the label-vs-content problem)

`Financial Disclosure` on this site names **two different instruments**, and the filename never
distinguishes them:

1. **Campaign C&E report** — the county's "Financial Campaign Report" form (contributions,
   expenditures, balances). **In scope.**
2. **Annual conflict-of-interest / financial disclosure statement** filed by *sitting*
   officeholders (Utah Code 17-16a). **Out of scope** by the money-layer contract
   (`scripts/campaign_finance/SCHEMA.md` §"Scope of the money layer"). The **odd-year** pages
   (2025) and the site's separate `<year>-conflict-of-interest-disclosures.html` pages are
   where these live.

Every acquired file is therefore classified **from its own text**, and the classification is
recorded in `index.csv`; nothing is trusted from the portal label. Odd-year pages were fetched
precisely so the distinction could be *proved* rather than assumed.

## The classification rule that was actually applied

Recorded here because both halves of it were needed, and each alone would have been wrong.

1. **The printed statutory citation is the primary discriminator**, because it is *printed*
   and therefore survives OCR, while every value the candidate supplied is handwritten.
   The county instrument cites **Utah Code 17-16-6.5** (later, **Cache County Code 2.21**)
   and carries a "Name of Office" line; the school-board instrument is a physically
   different form citing **20A-11-1301..1305**. Validated against the county's own 2014
   folder split (`CountyOffices/` vs `SchoolBoardCandidates/`): 27/36 and 30/33 agreement,
   the residual being files whose header did not survive OCR at all — no disagreement in
   the other direction except one file, which is flagged in its `notes`.
2. **But the county header can FALSE-POSITIVE**, because a county clerk sometimes hands the
   blank county form to a municipal or special-district candidate. So the header **never
   asserts an office by itself.** Scope is decided by the **stated office** (typed field, or
   the county election canvass, or the filer's own sibling filing in the same cycle), and a
   filing on the county instrument with an unreadable office is parked at
   `scope_status='county_office_illegible'` + `needs_review=1` — *not* counted as a
   confirmed county office. Two known-suspect rows (Kevin Rhodes 2016, Shannon Rhodes 2018)
   sit there deliberately.
   > **SUPERSEDED 2026-08-02.** The vision pass read every one of those pages, so
   > `county_office_illegible` is now an EMPTY bucket and no longer a value in `index.csv`.
   > Rule 2 was vindicated — 11 filings on the county instrument turned out to name
   > school-board, municipal, special-district or state-legislative offices — and **both
   > Rhodes rows resolved to "Cache County Council" on their own Name-of-Office lines.**
3. **Cycle parity is a cross-check, never a source.** County offices in Utah are elected in
   even years only, so odd-year *pages* are municipal-suspect — but the 2025 page proved the
   page label lies in the other direction too: its seven filings are 2026-cycle **County
   Executive** C&E reports. Parity is recorded per row in `cycle_parity`; odd-year filings
   are indexed to the following even cycle.
4. **Every state-site folder in scope was opened and read under this rule**, including
   `cache_2024` (re-checked explicitly: 0 hosted files, one outbound link) and the nine
   **2018 residence-town** folders, whose 32 PDFs turned out to be county filers filed under
   their home towns.

PMN was not used for this package — the county publishes its own disclosure pages and the
state mirrors them, so no notice-body search was needed.

## Acquisition universe

**497 distinct PDF URLs** across the three channels (county_site 291 · state_disclosures 95 ·
wayback 111), before content classification and cross-channel de-duplication by sha256.
**495 retained**; 2 are `unrecovered.csv`.

**Post-vision classification (2026-08-02):** of the 495 retained, **239** are county-office
filings (`index.csv`) and **256** are out of scope (`excluded.csv`). The pass also settled
the recon's open question about the classification rule — see §"The classification rule that
was actually applied" below: rule 2 (the county header can false-positive) proved correct
**11 times**, and rule 1's printed-citation discriminator was necessary but never sufficient
on its own. Every office is now established from the page image, a typed field, a canvass
join, or a sibling filing; 5 rows remain `undetermined` because the filer left the Office box
blank.
