# summit_county / ordinances — sources & provenance

**Adopted Summit County land-use ordinances + the two Development Codes** as a searchable
plain-text corpus. Self-contained: raw PDFs, extracted text, a manifest. Nothing here
writes to the db. Built 2026-07-20; every row verified live against its `source_url`.

## Where these come from

Summit County publishes its ordinances/codes across three hosts:
1. **Municode** — the LIVE, authoritative codified text:
   <https://library.municode.com/ut/summit_county/codes/code>. Two land-use codes:
   **Title 10 — Snyderville Basin Development Code** (`nodeId=TIT10SNBADECO`) and
   **Title 11 — Eastern Summit County Development Code** (`nodeId=TIT11EASUCODECO`).
   Municode blocks automated fetch (HTTP 403) and its OrdBank "recently adopted" list is
   not exposed via a usable public API (client id 17622) — so Municode is catalogued as a
   **link** (the code is not mirrored), and individual amending ordinances are catalogued
   from their signed PDFs below.
2. **County DocumentCenter** (`summitcountyutah.gov/DocumentCenter/View/<id>`) — signed
   ordinance / staff-report PDFs and the consolidated Eastern (Title 11) code PDF.
3. **Utah Public Notice** (`utah.gov/pmn/files/<id>.pdf`) — noticed ordinance drafts
   (e.g. Ord 912), and **water.utah.gov** for the recent Basin water ordinance (1003).

## Retrieval & text method

- PDFs fetched with `curl -L`; all born-digital and <50 MB, so all retained. Text via
  `pypdf`. Regenerate:

      python3 -c "from pypdf import PdfReader; \
      open('text/<stem>.txt','w').write('\n'.join((p.extract_text() or '') \
      for p in PdfReader('raw/<stem>.pdf').pages))"

## What is catalogued

- **2 Development Codes** — Title 10 (Basin; Municode link-only) + Title 11 (Eastern;
  county consolidated PDF retained + Municode link).
- **3 discrete land-use ordinances with local text** — Ord **912** (NMU-1 mixed-use zone
  in Title 10), Ord **936** (landscaping regulations), Ord **1003** (Basin GP Chapter 8:
  Sustainable Development / Water Use / Agriculture).
- **6 plan-adopting ordinances cross-referenced** — Ord **839** (Basin GP), **950/951**
  (Basin/Eastern MIH), **962/968/980** (MIH amendments). Their full text lives in the
  `plans/` module; here they carry a catalog row with **blank `path`** and a pointer, so
  the adopted-ordinance catalog is complete without byte duplication.

## HONEST GAPS

### 1. Enacting-vote linkage is intentionally BLANK (out of scope for this pass)
`matter_id`, `motion_id`, `match_confidence` are **left blank** for every row. Summit
County is **not** in the repo's Legistar/vote pipeline for this module, and linking each
ordinance to its enacting Council roll call is out of scope. Never forced/fabricated —
a closing pass can populate these from the county's minutes/agenda system.

### 2. Two ordinances are pre-signature drafts → adoption_date blank
Ord **912** and **936** were captured as the **noticed/pre-signature draft** whose
signature block reads `Enacted this ___ day of ___` (blank). Per the no-fabrication rule,
`adoption_date` is left blank; the Council/PC action dates found in the body are recorded
in `notes` (912: PC 2020-06-05, Council 2020-08-19; 936: PC 2021-11-09, Council 2022-05-25).

### 3. The full adopted-ordinance register is NOT enumerated here
This is a **targeted land-use/housing catalog**, not the complete Summit County ordinance
book. Municode's OrdBank (recently-adopted-but-not-yet-codified list) was not scrapable
via API on 2026-07-20 — enumerating every adopted ordinance number is a logged follow-up.
The codified corpus lives on Municode (linked).

### 4. Title 10 (Basin Development Code) is link-only
Municode is the authoritative consolidated Basin code; the county serves it as individual
chapter PDFs on DocumentCenter rather than one file. Not mirrored (link-only) — the code
itself is huge and continuously amended; discrete amending ordinances are catalogued
instead.

## Verify a source link

    curl -sSI "<source_url>" | grep -i "http/\|content-type\|content-length"

Expect `200` and `application/pdf` (DocumentCenter/PMN rows).
