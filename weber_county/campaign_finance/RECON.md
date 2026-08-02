# RECON — Weber County COUNTY-OFFICE campaign finance

**As-of 2026-08-01.** Source reconnaissance for `weber_county/campaign_finance/`
(Package B of the 2026-08-01 county acquisition wave). Scope: **county offices only** —
Commission (Seats A/B/C), Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder/Surveyor,
Treasurer. **School board is OUT of scope** (see `AVAILABILITY.md`); the county elections
office publishes county and local-school-board filings on the same page, so school-board
rows are enumerated in recon but not acquired.

Municipal (city) candidates are **not** Weber County's to publish — Utah Code 10-3-208
puts odd-year municipal disclosure with each **city recorder**. County and school-board
candidates file with the **County Clerk** under **Utah Code 17-16-6.5** and Weber County's
own campaign-finance ordinance. That statutory split is what makes "county office" a
clean scope line, and it is the discriminator used below.

---

## 1. Channels checked

| # | Channel | URL | Result |
|---|---|---|---|
| 1 | **Weber County Elections — Financial Disclosures** (PRIMARY, live) | `https://www.weberelections.gov/financialdisclosures` | ✅ **The authoritative channel.** 2026 per-candidate report PDFs + consolidated per-cycle archive PDFs for **2024, 2022, 2020, 2018, 2016, 2012**. **No 2014 archive link.** Also 9 officeholder Conflict-of-Interest PDFs (out of scope), a blank report form (`.xlsx`), and the Weber County Financial Ordinance PDF. |
| 2 | **Predecessor host — `weberelections.com/financials.php`** (Wayback) | `web.archive.org/web/20151107042924/http://www.weberelections.com/financials.php` (21 captures 2015-11→2018-11) | ✅ **The only channel for the 2014 cycle.** A tabbed page (2014 / 2012) grouped by **office → candidate → report period**, linking per-candidate PDFs under `/documents/`. |
| 3 | **Predecessor host — `weberelections.com/candidate_ballot_info/financial_disclosures.php`** (Wayback) | 26 captures 2017-07→2021-06 | ✅ A sortable **table**: `Name | Office | Date Filed | Election Year | File`. Gives a **per-filing manifest** (candidate, office, exact date filed, cycle) for 2014/2016/2018/2020 — used as the ground truth for splitting the consolidated PDFs. |
| 4 | **Wayback CDX over the predecessor host's document tree** | `cdx/search/cdx?url=weberelections.com/documents*` | ⚠️ 219 archived PDFs, but **`documents/reports/*` was NEVER captured** (`url=weberelections.com/documents/reports/*` → 0 rows). So the **2018 and 2020 per-candidate PDFs do not exist anywhere** — only inside the consolidated 2018/2020 archive PDFs on channel 1. |
| 5 | **State — LG municipal disclosure tree, Weber** (SUPPLEMENTARY) | `disclosures.utah.gov/Municipal/weber` → 16 year folders, crawled recursively (83 folders / 628 file links) | ⚠️ Mostly **odd-year municipal** filings in **town subfolders** (606 files). County-relevant: `weber_2010 Elections` (7 flat), `weber_2012 Primary` (14 flat), `weber_2022` (1 aggregate PDF). `weber_2016/2018/2020/2026` are **link-only redirects** back to the county site. `weber_2014` and `weber_2024` **do not exist** (server prints `Path: \\172.16.120.206\Municipal\weber\2014 does not exist.`). |
| 5b | **State — `weber_2024` and `weber_2014` specifically** | `disclosures.utah.gov/Municipal/weber_2024`, `/weber_2014` | ❌ **Server-level negative, checked two ways** (not inferred from the other years' pattern): the `/Municipal/weber` index enumerates its own subfolders and lists **no 2014 and no 2024 folder**, and a direct request returns the server's own message `Path: \\172.16.120.206\Municipal\weber\2024 does not exist.` (same for 2014). Checked because some counties' `_2024` folder IS a real second channel even when every other year is a pointer. Note `municipal.utah.gov` directory listings are 403 while direct file URLs serve fine — but with no folder there is nothing to list or guess at, and URLs are never fabricated. |
| 6 | **Wayback — `weberelections.gov`** (the current Wix site) | CDX | ❌ **Zero captures.** The live Wix site is the only copy; nothing to recover from an earlier version of it. |
| 7 | **Wayback — `webercountyutah.gov/elections/`** | CDX | ❌ One 2025 capture, HTTP 404. No county-website-era disclosure page distinct from channels 2–3. |
| 8 | **Utah Public Notice (PMN)** | — | **Not a campaign-finance channel** (PMN carries meeting notices/agendas/minutes). Not swept. Recorded so a later session does not re-litigate it. |

---

## 2. The residence-town folder trap — checked, does not bite here

The state system files a disclosure under the **candidate's town of residence**, not the
jurisdiction of the office, so a county-office filing can sit inside what looks like a
city folder (the Juab precedent: a county sheriff filing inside `juab_2014_Mona`). Folder
labels cannot clear a folder — **only the form header inside the PDF can.**

What was actually done for Weber:

1. **Recursive crawl** of the whole `/Municipal/weber*` tree (not just the year folders):
   83 folders, 628 file links enumerated. Weber's **even-year** folders — the only ones
   where county offices are on the ballot — are **flat**: `weber_2010 Elections`,
   `weber_2012 Primary`, `weber_2022`. **No town subfolders exist under any even year**,
   so the trap has no structure to hide in.
2. **Keyword screen** over all 606 odd-year files for county-office words
   (`commission|sheriff|assessor|attorney|clerk|auditor|recorder|surveyor|treasurer|county`)
   in both the label and the URL → **0 hits**.
3. **Name screen**: 45 odd-year files whose filer surname collides with a known
   county-office filer (Bolos, Thomas, Beesley, Jenkins, Burns, Gibson, Hansen, Tait,
   Erickson, Thompson, Bell, Jensen).
4. **Form-header verification** on a sample of those collisions (rendered at 250 dpi and
   read, because these are **handwritten** forms that return zero characters from
   `pdftotext`): e.g. `weber_2021_West Haven City / Sharon Arrington Bolos Final.pdf`
   carries the header **"CAMPAIGN FINANCIAL REPORT: 2021 / WEST HAVEN CITY CANDIDATES /
   City Council and Mayor"**, Office written in as *Mayor*. It is a **municipal** filing
   by a person who later held county office — a real cross-entity people link, **not** a
   misfiled county document.

**Conclusion:** every odd-year state-folder filing screened is a municipal filing. No
county-office filing was found hiding in a town subfolder. The surname collisions are
recorded in `AVAILABILITY.md` as a cross-entity lead (same people, different office,
different jurisdiction's channel), not as in-scope documents.

### The classification rule actually applied (both failure modes)

The form header alone is **not** a sufficient discriminator, in either direction:

- **False negative** (the residence-town trap): a county-office filing can sit in a
  town-labelled folder — the folder label never clears it.
- **False positive** (the Summit precedent): county clerks hand the **blank county form**
  to small cities, towns and special districts, so a document can carry the county
  header — "CAMPAIGN FINANCIAL REPORT … WEBER COUNTY & LOCAL SCHOOL BOARD CANDIDATES … TO
  BE FILED WITH THE WEBER COUNTY CLERK", Utah Code 17-16-6.5 — and still be a **city**
  candidate's filing.

So the rule used here is: **classify on the stated office written INSIDE the form**
(`Office:` on the pre-2016 form, `Name of Office:` on the 2016+ form), cross-checked
against **cycle parity** — Utah county offices are elected in **even** years only, so an
odd-year filing is municipal-suspect until its stated office says otherwise. The header
is supporting evidence, never the decision. Weber's own combined form is explicitly
shared between county offices **and local school boards** (its subtitle names both), which
is exactly why the stated office — not the form — is what separates in-scope from
out-of-scope inside a single archive PDF.

---

## 3. What the primary channel actually publishes (verified from the page, 2026-08-01)

The 2026 table lists **29 candidates** in master-ballot order with a `County Office`
column: **14 county-office** filers —

| Office | Candidates listed |
|---|---|
| Commission Seat A | Katrina C. Gibson, James Ebert, Gary C. New, Michelle Tait, Alvin Thurgood, Richard Hyer, Duane D Kearsley |
| Commission Seat B | Michael N. Thomas, Jon D. Beesley, Sharon Arrington Bolos |
| Attorney | Chris F Allred |
| Clerk/Auditor | Ricky Hatch |
| Sheriff | Ryan Arbon |
| Assessor | Jared L. Preisler |

— plus **15 school-board** filers (Ogden School Board 2/4/6/7, Weber School Board 1/2/3/6),
out of scope.

⚠️ **The report links are laid out COLUMN-WISE, not row-wise** in the page markup: the
"Report Name" column renders as a flat run of links (`Convention`, `Pre-Primary`,
`Primary`, `Final`, `Primary - Amended`) interleaved with `Awaiting final report`
placeholders, so **a link cannot be attributed to a candidate by DOM position**. The
candidate↔office pairing is reliable (two parallel 29-entry columns); the candidate↔PDF
pairing is **not**. Every 2026 PDF is therefore attributed from **its own content**
(the "Candidate" / "Office" fields printed on the form), never from the portal label.
The portal label is retained in `_fetch_log.jsonl` `note` as `portal label: <text>` so
label-vs-content disagreements stay visible.

## 4. Fetch mechanics (recorded so a refresh does not rediscover them)

- **Wix `_files/ugd/` hotlink protection**: a plain `urllib` GET returns **HTTP 429** even
  at one request per 8 s. The same URL returns **200** with `Accept:` +
  a same-site `Referer: https://www.weberelections.gov/financialdisclosures`. Two objects
  (the 2018 and 2024 archives) 429 for `urllib` regardless and needed the **curl**
  fallback — `fetch_cf.py --use-curl`. Both paths log identical provenance.
- **State-site URLs contain literal backslashes** as published
  (`http://municipal.utah.gov/weber\2022\Weber County Candidates ... .pdf`). Percent-encode
  the backslash (`%5C`) and upgrade to `https` — `.../weber%5C2022%5C...` returns 200
  (the forward-slash form works too; the backslash form is kept because it is what the
  state page publishes).
- **Wayback**: `web/<ts>id_/<original>` only works at a timestamp where **that object**
  was captured — the listing page's timestamp is usually wrong for its PDFs. Resolve each
  PDF's own capture through the **CDX API** first.

## 5. Cross-check between channels

The **2022** cycle is published on both channels and the two files are **not identical**:

| | bytes | pages | sha256 (first 16) |
|---|---|---|---|
| county combo `2022_combined_7e3a53_78d55edd.pdf` | 6,204,461 | 52 | `18b09b39c5a1b3b1` |
| state aggregate `st2022_Weber_County_Candidates_General_Election_22_Financial_Disclosures.pdf` | 6,176,720 | 52 | `d2cb92dd65bded90` |

Same page count, different bytes — a re-save, not a different document set. **Both are
retained** (each is what its own channel published); the content comparison is reported in
`AVAILABILITY.md`. Never treat the two as one document and never merge their index rows.

## 6. Format floor (the reason a vision pass is planned)

These are **handwritten fill-ins on printed forms**, then scanned. `pdftotext` returns
**0 characters** on most documents; `tesseract` recovers the **printed** form scaffolding
(headers, "Total Campaign Contributions", office labels) reliably but renders the
**handwritten amounts and donor names as garbage**. That is a real property of the source,
not an extraction failure. Consequences, applied throughout this dataset:

- `text/` sidecars are built anyway (they carry the printed scaffolding, which is what
  identifies candidate/office/report-type and makes the corpus searchable).
- **No structured layer** (`contributions.csv` / `expenditures.csv` / `filing_totals.csv`)
  is built. None of the shared families in `scripts/campaign_finance/families/` parses this
  family from OCR of handwriting without library modification, and the binding rule for
  this package is *structured layers only where the shared lib parses the family WITHOUT
  lib modification*. Rows would be fabricated amounts. See `AVAILABILITY.md` §
  "Structured layer — deliberately not built".
- Filings whose candidate/office could not be read from content are marked
  `needs_review=1` in `index.csv` and are the queue for the `cf-vision-transcribe` pass.
