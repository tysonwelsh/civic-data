# Utah County — Ordinances module: SOURCES & provenance

The **codified ordinances of Utah County** (Land Use Ordinance + Code of Ordinances +
County Policies) as a searchable plain-text corpus, plus an **adopted-ordinance
catalog** (numbers / dates / titles) assembled from the code's own amendment histories.
Built 2026-07-20. Utah County is a **3-member Board of Commissioners** county
(FIPS 49049); the Land Use Ordinance governs only the **unincorporated** areas.

## Where these come from

Utah County publishes its code on **municipalcodeonline.com**
(`utahcounty.municipalcodeonline.com`; product = "Municipal Code Online", an AngularJS
book viewer). Four books exist; three are catalogued in THIS module, the fourth (`plan`
= the General Plan) is in the **plans/** module:

| book type | catalogued as | this module? |
|---|---|---|
| `landordinances` | Land Use Ordinance (UCLUO) | yes |
| `ordinances` | Code of Ordinances | yes |
| `policies` | County Policies (administrative) | yes |
| `plan` | General Plan | no — see `../plans/` |

## Retrieval method (the SPA workaround)

The book viewer is an AngularJS SPA whose section-content AJAX routes (`/book/content`,
`/book/expand`) return **"Unauthorized Access"** without a runtime `bookDataId` pulled
from the page's Angular scope — they are not directly fetchable. The full text of each
book is instead retrievable from the **print view**:

    GET https://utahcounty.municipalcodeonline.com/book/print?type=<landordinances|ordinances|policies>

which returns the entire book as one HTML document. Section headers are
`<div class='phx-name'><a>…SECTION NUMBER + TITLE…</a></div>`; body text follows in a
`phx-docs` block. Parsed to plain text with a section splitter (each section written as
`===== <number> <title> =====` + body). No auth, no rate limit hit; one request per book.

- `book/search?type=<t>&searchText=<q>` also works (returns server-rendered result
  links) and is handy for locating a section by keyword.
- All three books are **born-digital HTML** (clean text, no OCR floor). None exceeds
  ~1 MB of text; the codified code is a **web book, not a downloadable PDF**, so `path`
  is blank in `index.csv` and `source_url` (the live Municode book) is canonical.

## Files

- `text/<stem>.txt` — extracted text of each book. **The searchable layer — read/grep.**
  `land_use_ordinance.txt` (132 sections, ~955k chars), `code_of_ordinances.txt` (915
  sections, ~965k chars), `county_policies.txt` (74 sections, ~349k chars).
- `index.csv` — the **code-book manifest** (3 rows). Columns include SCHEMA_SPEC §9
  primary-document fields (`doc_class=code_snapshot`, `fetch_status`, `sha256`,
  `text_chars`) from day one.
- `code_sections.csv` — the **navigable section catalog**: one row per codified section
  (`book, section_no, section_title, char_count`), 1,121 rows across the three books.
- `adopted_ordinances.csv` — the **adopted-ordinance catalog** (below).
- `raw/` — empty (the code is a web book; nothing stored locally).

## The adopted-ordinance catalog (`adopted_ordinances.csv`)

Utah County adopts ordinances by number (`YYYY-NNN`, e.g. `2025-341`). The county
publishes **no standalone adopted-ordinance index/register** that we could locate
(honest gap, below). The catalog is instead **assembled from the amendment-history
citations embedded in the codified text** — every section records the ordinances that
created/amended it, e.g. *"Amended by Ord. 2025-341 Updated Parking on 4/24/2025."*
A regex (`Ord. YYYY-NNN <description> on M/D/YYYY`) over the Land Use Ordinance + Code
of Ordinances text yields:

- **322 distinct adopted ordinances**, **1997-04-22 → 2026-06-09**, every one with an
  **adoption date** and a description.
- **303 land-use** (from the Land Use Ordinance) + 19 non-land-use (Code of Ordinances).
- Columns: `ordinance_no, adoption_date, title, land_use, source_book, n_amendments,
  source_url, matched_motion_date, matched_motion_no, match_confidence, notes`.
  `title` concatenates the distinct amendment descriptions for that ordinance;
  `n_amendments` = how many sections it touched.

**Enacting-vote linkage is intentionally BLANK** (`matched_motion_date`,
`matched_motion_no`, `match_confidence` empty on all rows). Utah County is NOT a
Legistar county and its Commission votes are not yet in the legislative db; a downstream
**closing pass** links these ordinance numbers/dates to the enacting Commission motion.
Never force a link.

## Recodification note (honest correction)

The scouting note said the Land Use Ordinance was "recodified 2022-02-23." That exact
date does **not** appear in the code text. What the amendment history actually records
is: amended in its entirety with new numbering/formatting by **Ord. 2020-1109**, then
"Revise and adopt, in its entirety, numbering and new format for Municode" by
**Ord. 2021-258 on 2021-04-09**. `index.csv` records the **verified** 2021-04-09
Municode recodification, not the unconfirmed 2022 date.

## HONEST GAPS

- **No published adopted-ordinance register.** The county does not publish a machine-
  readable list of adopted ordinances (numbers/dates/titles) that we could find; the
  catalog is reconstructed from the code's amendment histories. This means: (a)
  ordinances that were adopted but **never amended a codified section** (e.g. one-off
  resolutions, project-specific rezones that only touch the zoning MAP, budget
  ordinances) are **not captured** — the catalog is a floor, not a complete register;
  (b) an ordinance's `title` here is its *amendment description*, not its formal caption.
- **Enacting votes not linked** (see above) — deferred to the closing pass.
- **Zoning map ordinances** (rezones of specific parcels) are adopted as ordinances but
  change the Land Use *Map*, not the ordinance text, so most do not surface in the
  amendment-history catalog. The map itself is a GIS layer (see the gis/ module).
- **Code of Ordinances recodification date** is not printed in the section text (blank).

## Regenerate a text file

    curl -sS -A Mozilla/5.0 "https://utahcounty.municipalcodeonline.com/book/print?type=landordinances" -o print.html
    # then run the phx-name/phx-docs section splitter (see the build note above)

## Verify a source link

    curl -sSI "https://utahcounty.municipalcodeonline.com/book?type=landordinances" | grep -i "http/"

Expect `200`.
