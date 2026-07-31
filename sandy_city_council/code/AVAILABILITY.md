# `code/` — Sandy codified zoning/land-use snapshot: HONEST GAP (side-probe, 2026-07-16)

**Outcome: NOT ACQUIRED.** The consolidated codified **Land Development Code (Title 21)**
text for Sandy is **not publicly extractable** by polite GET-only means. This file is the
evidence record. It is the ONLY artifact in `code/` — no snapshot was fabricated.

Context: this is the class-6 (`code_snapshot`) **side-probe** of the primary-documents
pilot (`PRIMARY_DOCS_PILOT_SPEC.md` §7). Per that spec the pilot succeeds without this
class; the job was to land it cleanly or document the gap with evidence. It is a gap.

## What Sandy's code is, and where it lives

- Sandy's codified ordinances are hosted by **CivicPlus / MunicipalCodeOnline** at
  `https://sandy.municipalcodeonline.com/book?type=ordinances` (book code `O`,
  "Municipal Code"). The land-use/zoning body is **Title 21 (Land Development Code)** —
  identified from adopted ordinance titles (e.g. Ord 25-25, "Ordinance Amendment — Title
  21 Chapters 3, 30 & 37 boundary adjustments"). The full Title 21 chapter TOC could not
  be enumerated (the TOC endpoint is gated — see below).
- Municode (`library.municode.com/ut/sandy`) is only a **redirect stub** to the above; it
  hosts no Sandy code content of its own (evidence table, row B).
- `sandy.municipal.codes` was **NOT contacted** — it is a documented 403 bot-block and was
  off-limits for this probe.

## Probe order and results (spec §7)

### (a) Municode public JSON backend — reachable, but Sandy has NO content there
`api.municode.com` is publicly GET-reachable and returned Sandy's client/product metadata,
but Sandy publishes **no codified content on Municode's own backend** — the product carries
`HasPdf=false`, no publication job exists, and it points OUT to MunicipalCodeOnline via
`ExternalCodeLink`. So the Municode content API (`codesToc`/`CodesContent`) has nothing to
serve for Sandy. PATH YIELDS NO CODE.

### (b) Public MunicipalCodeOnline site — content/TOC/print endpoints are auth-gated
The MCO SPA loads its table of contents and chapter text from `book/expand`, `book/content`,
and `book/print`. Every anonymous polite GET to these returned **HTTP 500 "Unauthorized
Access"** — they require an authenticated/editor session that was **not** attempted (forging
it would violate the pilot's cardinal no-auth-evasion rule). The publicly-listable **S3
bucket** behind MCO holds only (1) adopted-**ordinance** PDFs — the amendment/diff record,
already captured in Sandy's `ordinances/` Legistar dataset — (2) two **design-standard**
manuals, and (3) a single **Chapter 1-1** fragment; it does **not** hold the consolidated
Title 21 title text. PATH YIELDS NO CONSOLIDATED CODE (only partials; see below).

### (c) Conclusion — honest gap
The consolidated codified Land Development Code text is behind an auth gate on the only host
that has it. Recorded as a documented honest gap for Sandy, per spec §7(c).

## Evidence table (all 2026-07-16; GET-only; browser or polite UA; ≥1.5s throttle)

| # | URL | Method | Status | Meaning |
|---|-----|--------|--------|---------|
| A | `https://api.municode.com/Clients/name?clientName=sandy&stateAbbr=ut` | GET | 200 | Sandy = Municode ClientID **4222** |
| B | `https://api.municode.com/ClientContent/4222` | GET | 200 | one product **41373** "City Code"; `hasPdf=false`, `hasPdfDownloadEnabled=false`, `publicationId=null` |
| C | `https://api.municode.com/Jobs/latest/41373` | GET | **204** | no Municode-hosted publication exists (contrast: a Municode-native city e.g. Orlando product 13349 returns 200 + a real supplement job) |
| D | `https://api.municode.com/Products/41373` | GET | 200 | `HasPdf=false`; **`ExternalCodeLink="https://sandy.municipalcodeonline.com/book?type=ordinances"`** — code is off-platform |
| E | `https://api.municode.com/codesToc?productId=41373` | GET | 404 | no Municode TOC for Sandy |
| F | `https://library.municode.com/ut/sandy` | GET | 200 | SPA shell only (6 KB); code loads client-side from the external host |
| G | `https://sandy.municipalcodeonline.com/book?type=ordinances` | GET | 200 | MCO SPA shell; TOC loads via AJAX `book/expand` |
| H | `https://sandy.municipalcodeonline.com/book/expand?type=ordinances` | GET | **500** | body: `Unauthorized Access` (TOC gated) |
| I | `https://sandy.municipalcodeonline.com/book/content?type=ordinances&name=&...` | GET | **500** | body: `Unauthorized Access` (chapter text gated) |
| J | `https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/?list-type=2&prefix=sandy/` | GET | 200 | public S3 listing; prefixes `sandy/ADC/`, `sandy/ordinances/`, `sandy/site/` |
| K | `...&prefix=sandy/ordinances/documents/` | GET | 200 | **123** adopted-ordinance PDFs (amendment/diff record; = the `ordinances/` layer, NOT consolidated titles) |
| L | `...&prefix=sandy/ADC/files/` | GET | 200 | 5 objects: `Sandy City Architectural Standards.pdf`, `Cairns Design Standards.pdf`, and `Sandy City_Municipal Code_20260112.pdf` |
| M | `.../sandy/ADC/files/ordinance/1768240412_Sandy%20City_Municipal%20Code_20260112.pdf` | GET | 200 (79 KB) | fetched + `pdftotext`: **only Chapter 1-1** (Code Established; Definitions), ~18 KB text — a fragment, NOT Title 21 |

`sandy.municipal.codes`: intentionally never contacted (off-limits 403 bot-block).

## What IS publicly available (partials — deliberately NOT captured here)

These are on the public S3 bucket and are plainly fetchable, but none is the consolidated
zoning code, so none was pulled into a `code/` snapshot (capturing them would misrepresent a
fragment/manual as "the code"):

- **Adopted-ordinance PDFs** (`sandy/ordinances/documents/`, 123 files) — these are the
  amendment/diff record and are already represented in Sandy's `ordinances/` dataset (built
  from Legistar). Not re-captured; `ordinances/` is canonical for them.
- **Design-standard manuals** (`sandy/ADC/files/ordinance/`): "Sandy City Architectural
  Standards" (~1.2 MB) and "Cairns Design Standards" (~24 MB) — genuine development-design
  regulatory documents, adopted as exhibits, but NOT the Title 21 zoning/subdivision text.
  If the owner later wants these as a partial, they are one polite GET each (URLs in the S3
  listing); flag as reduced-scope (design manuals, not zoning titles) if captured.
- **A Chapter 1-1 fragment** (the 79 KB PDF, row M) — only the definitions/construction
  chapter; not land-use.

## Rollout recommendation (corrects spec §10 for this class)

Spec §10 proposed "MunicipalCodeOnline S3 cities (the township wave)" as the cheapest
first targets for class 6. **This probe shows that assumption needs revising for codified
_title text_:**

- Every Utah "Municode" client in the repo's orbit is actually **MunicipalCodeOnline-external**.
  Verified 2026-07-16 via `ExternalCodeLink`: Park City (`parkcity.municipalcodeonline.com`),
  South Jordan, Cottonwood Heights, Herriman, Millcreek — all redirect to MCO, all `hasPdf=false`,
  all `Jobs/latest`→204. Their code text sits behind the **same gated `book/*` endpoints** as
  Sandy's.
- The MCO public **S3** buckets expose only **adopted-instrument PDFs** (what White City's
  `ordinances/` dataset already harvests) — NOT consolidated codified titles. So "S3 cities"
  are cheap for the **ordinances/** layer but **not** for a class-6 `code_snapshot` of the
  zoning titles.
- **Cheaper genuine class-6 targets are cities whose codifier serves consolidated title text
  over public GET**: Municode-*native*-hosted cities (where `Jobs/latest` and `CodesContent`
  return real content, e.g. the Orlando pattern), or American Legal / Sterling Codifiers
  platforms that expose printable HTML. Recommend re-scoping the class-6 rollout list around
  "codifier exposes printable/JSON content publicly," not around the MCO S3 buckets.

## Refresh / re-probe convention

Re-probe only when (a) MunicipalCodeOnline exposes an unauthenticated read path for
`book/content` (it does not today), or (b) Sandy migrates its code to a codifier with public
title-text GET access. Until then this class stays a documented gap. Never synthesize
historical code text; `ordinances/` remains the diff record and `db/sandy.db` the enacting-
motion linkage.
