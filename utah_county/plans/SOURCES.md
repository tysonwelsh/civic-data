# Utah County — Plans module: SOURCES & provenance

The governing **General Plan** for unincorporated Utah County, as a searchable
plain-text corpus for growth / housing / development research. Built 2026-07-20.
Utah County is a **3-member Board of Commissioners** county (FIPS 49049); its
Community Development Department plans/permits only the **unincorporated** areas
(incorporated cities run their own codes).

## Where these come from

Two publishers hold the authoritative unincorporated-county General Plan:

1. **municipalcodeonline.com** (`utahcounty.municipalcodeonline.com`) — the county's
   codified online code host (product: "Municipal Code Online" / phoenix-based book
   viewer). It carries four books: `plan` (the General Plan), `landordinances` (the
   Land Use Ordinance — see the ordinances module), `ordinances` (the Code of
   Ordinances), and `policies` (county administrative policies).
   - The **General Plan** is the current living plan: it was *revised and adopted in
     its entirety* on **2020-12-30 by Ordinance 2020-1110** (effective 2021-02-05),
     re-numbered and re-formatted for Municode, and has been amended continuously since
     (most recent captured: Ord. 2025-1064, Water Use & Preservation Element,
     2025-12-31). This is the authoritative in-force plan.
   - Landing: https://utahcounty.municipalcodeonline.com/book?type=plan

2. **Utah County Community Development — Laserfiche WebLink** (`utahcounty.gov`) — hosts
   a PDF snapshot of the **2006** General Plan (adopted 2006-10-17 by Ord. 2006-33,
   amended 2007-03-20 by Ord. 2007-08). This predates the 2020 codified re-adoption and
   is retained as the historical adopted-record snapshot.
   - PDF: https://www.utahcounty.gov/apps/WebLink/Dept/COMDEV/Binder2.pdf (3.2 MB)
   - Community Development landing: https://codev.utahcounty.gov/

## Retrieval method

- **Codified plan (current):** the municipalcodeonline book viewer is an AngularJS SPA
  whose section AJAX (`/book/content`, `/book/expand`) is gated ("Unauthorized Access")
  behind a runtime `bookDataId`. The full plan text is instead retrievable from the
  **print view**: `GET /book/print?type=plan` returns the entire book as one HTML
  document (section headers in `<div class='phx-name'>`, body in `phx-docs`). Parsed to
  plain text with a section-splitter (each `===== <section> =====` header preserved).
  85 nodes / ~430k chars extracted.
- **2006 PDF:** fetched with curl; text extracted with pypdf (`PdfReader`, per-page
  `extract_text()`). 36 pp, born-digital, clean (no OCR floor).

## Moderate-Income Housing (MIH)

Utah County's MIH element is **Chapter 4 of the General Plan** (`4.02 Adoption`,
`4.04 Moderate Income Housing Element And Its Implementation`, `4.06 Programs`,
`4.10 ... preservation ... development ... regulatory barriers`) — it is NOT a
standalone plan. Grep the codified plan text for "Moderate Income". The 2006 PDF also
carries an MIH chapter (Chapter 2). This matches the scouted finding: **MIH lives
INSIDE the GP.**

## Size policy (link vs. store, >~50MB rule)

Both documents are small. The 2006 PDF (3.2 MB) is stored in `raw/`. The current
codified plan is a **web book, not a downloadable PDF**, so `path` is blank and
`source_url` is the live Municode book; its text sidecar is the searchable artifact.

## Inventory (2 documents, both with extracted text)

| doc_type | title | adopted | source | raw? |
|---|---|---|---|---|
| general_plan | General Plan (current codified) | 2020-12-30 (Ord 2020-1110) | municipalcodeonline | link (web book) |
| general_plan | General Plan (2006 snapshot) | 2006-10-17 (Ord 2006-33) | Laserfiche WebLink | raw PDF |

## Honest gaps / not-retrieved

- **No standalone Utah County Moderate-Income-Housing plan PDF exists.** MIH is a
  chapter inside the General Plan (Ch. 4 codified / Ch. 2 in the 2006 PDF), consistent
  with the scouted source. Not a fabricated zero — the MIH strategy content is in the
  plan text. The state Dept. of Workforce Services publishes a compiled *Moderate Income
  Housing Program Annual Report* (jobs.utah.gov/housing/affordable/moderate/reporting)
  that includes all jurisdictions' self-reported progress; that is a STATE compilation,
  not a county-authored plan, and was not ingested here.
- **Area / community / small-area plans:** none were located as separate published
  documents on the county Community Development site as of this build. If the county
  later publishes sub-area plans they should be added as additional rows. Logged as a
  follow-up, not claimed as retrieved.
- **The codified plan's raw pixel-faithful form:** the current plan is only published as
  a codified web book (Municode), not as a single official PDF. If a signed/pixel-exact
  copy is later needed it must come from the county Clerk's adopted-ordinance record for
  Ord. 2020-1110 and its amending ordinances.

## Regenerate a text file

- 2006 PDF:

      python3 -c "from pypdf import PdfReader; \
      open('text/utah_county_general_plan.txt','w').write('\n'.join((p.extract_text() or '') \
      for p in PdfReader('raw/utah_county_general_plan.pdf').pages))"

- Codified plan: re-fetch `https://utahcounty.municipalcodeonline.com/book/print?type=plan`
  and re-run the phx-name/phx-docs section splitter (see the ordinances module SOURCES.md
  for the identical parser used on the code books).

## Verify a link

    curl -sSI -A Mozilla/5.0 -L "<source_url>" | grep -i "http/\|content-type"

Expect `200` (`application/pdf` for the PDF; `text/html` for the Municode book).
