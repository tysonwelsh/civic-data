# PRIMARY_DOCS_PILOT_SPEC — primary-document text corpus (Sandy pilot)

Drafted 2026-07-16 from the TODO High-priority item "Evaluate which additional primary
documents should be stored as on-disk markdown text" (surfaced 2026-07-14). Companion
record: the deferred-classes watch list in Appendix A.

**STATUS: ✅ PILOT EXECUTED + ACCEPTED 2026-07-16** (owner-approved scope: classes 1–5,
class 6 as side-probe). Results:
- Classifier gates: staff_report 100% (n=50) / member_memo 98.1% (n=52) / plan_amendment
  100% precision; recall iterated to 0 misses in a 100-row unclassified sample.
  **889 classified** (staff_report 739 / member_memo 131 / plan_amendment 19 /
  development_agreement 0 — an honest EMPTY class: Sandy's 2020–26 Legistar corpus holds
  no DA instruments).
- Fetch/extract: 767 text sidecars (24.0M chars), 96 needs_ocr (2020–22 scan era), 26
  404s (link rot already — validates the rot-proofing rationale). Disk: **25.2 MB text
  vs the 2.26 GB classified-binary counterfactual (~1.1%)**.
- GP corpus (class 3): pre-2025 GP fully recovered (11 chapters via a Wayback
  widget-JSON resurrection), 2025 Pace-of-Progress draft-of-record captured from
  Legistar (Ord 25-01 adopts the 10/21/2024 draft), all 5 station-area plans, T19–T41
  located (Section 7). Honest gap: Section 8 (consultant host NXDOMAIN'd).
- Class 6: honest gap (§7 probe outcome above); rollout list re-scoped (§10).
- Federation: `document.doc_class` + `fts_packet.doc_class` added to
  `scripts/build_search_layer.py` (the city loop now honors explicit `text_path`
  columns); fts_packet 11,893 → 12,660.
- **§2 Sharkey acceptance test: PASSED** — `fts_packet MATCH` with
  `doc_class='member_memo'` returns ">>Eliminate<< the establishment of a minimum
  density…" as a snippet; the chain joins to the 2024-12-17 amendment vote (3–4 FAIL,
  full roll) and the enacting Ord 25-01 motion via matter 6140 (5–2 Pass, Sharkey +
  D'Sousa Nay). One documented join caveat: the memo's own matter (6126, a
  "presenting potential amendments" discussion matter) carries no `application_id` —
  the motion join runs through the action matter 6140; the memo joins by date +
  matter-family (recorded in packets/CLAUDE.md).
Rollout decisions (§10/§11) remain open for the owner.

## 1. Motivation

Analysis currently leans on the minutes' *paraphrase* of what a document did, and
paraphrases can invert meaning. Live case (Sandy, 2026-07-14): a clerk's one-line minute —
"the establishment of a minimum density in all land use designations" — dropped the
governing verb from Sharkey's actual GP-amendment memo ("**Eliminate** the establishment
of a minimum density…"), fully reversing the reading until the primary PDF was fetched
live (write-up: `~/Desktop/sharkey-amendment-misread-incident.md`).

The original blocker was disk: Sandy's packet binaries ≈14.9 GB. The reframing that
unblocks it: **extracted text is ~1–5% of PDF size**, so a fetch → extract text → discard
binary pipeline is cheap, and it is rot-proof where index-only `source_url`s will 404 over
time. Selection principle: a document class earns text storage when analysis cites its
**content** (not just its existence) and the minutes' paraphrase is the current fallback.

## 2. Goal + acceptance test

Make the PRIMARY text the default hit for "what does it say" questions: searchable in the
FTS layer, one join from the vote that acted on it.

**Acceptance test (the Sharkey test):** an FTS query for the minimum-density amendment
returns the memo's own text with the verb "Eliminate" in the snippet, and the row joins to
the enacting motion + roll call via `matter_id`. Cost target: answering "what did the
amendment say" costs a `snippet()` (~100 tokens), not a live PDF render (~2,000).

## 3. Measured Sandy baseline (recon 2026-07-16, read-only)

- `packets/index.csv`: 6,908 rows = 462 agendas (`stored_locally=yes`) + **6,446
  `staff_report_or_exhibit` attachments, ALL `stored_locally=no`, ALL with `matter_id`**,
  `format=na`. Titles are heterogeneous ("PC Staff Report", "2_Memo", "Exhibit A",
  "Ord 26-15", photos) → the existing `packet_kind` column CANNOT select classes;
  a classifier is required (§5).
- `db/sandy.db` `legistar_matter` (matter_id, matter_file, title, matter_type, status,
  enactment_number, application_id, …) — the join that gives each attachment its matter
  TYPE and its link into `application`/`motion` (Sandy's `app_match_method='matter_id'`
  extension). `ordinances/index.csv` already carries matter_id + match_confidence.
- `housing_plans/`: 2022-era GP chapter PDFs partially captured (ch. 10 MIH); **the
  Jan-2025 adopted GP (incl. five station-area plans + new MIH element) is an ArcGIS
  web-only product — no PDF exists** (documented in `AVAILABILITY.md`); a 2017 MIH
  biennial report is already captured (the class partially exists).
- Codified zoning text: **Municode `library.municode.com/ut/sandy` (browser-only; NOT
  mirrored); `sandy.municipal.codes` is a 403 bot-block** (per `ordinances/CLAUDE.md`).

## 4. In-scope document classes (pilot = Sandy only)

| # | Class | doc_class value | Why | Home |
|---|-------|-----------------|-----|------|
| 1 | Land-use staff reports | `staff_report` | The "why" behind every rezone/CUP/plat; richest per-token class | `packets/` |
| 2 | Council-member proposal memos + amendment text | `member_memo` | The Sharkey class; motions say "as distributed", text lives only here | `packets/` |
| 3 | General-plan text: draft-era chapters, section tables (T19–T41), small/station-area plans | `general_plan` | What the council actually debated; referral layer already admits these plans as applications | `housing_plans/` |
| 4 | GP / land-use-map amendment exhibits | `plan_amendment` | The adopting ordinance says "as shown in Exhibit A"; the exhibit is the substance | `packets/` |
| 5 | Development agreements + MDAs and their amendments | `development_agreement` | Negotiated density/phasing/vesting exists nowhere else | `packets/` |
| 6 | Zoning / land-use titles of the codified municipal code, dated snapshot | `code_snapshot` | The state of the law the ordinance layer only diffs; "what does the code allow" baseline | new `code/` dataset |

Classes 1–5 are attachment-borne and ride the existing `packets/` dataset. Class 6 is a
new small dataset (§7).

## 5. Classifier (the real design problem)

Selection mechanics, not the class list, are the risk: the 6 classes are maybe 10–20% of
6,446 attachments, and bulk-fetching everything re-creates the disk problem and buries the
signal.

- **Inputs per attachment row:** title/filename tokens + the `matter_id` →
  `legistar_matter.matter_type`/`title` join (e.g. attachments of rezone/ordinance-type
  matters titled "Staff Report" → `staff_report`; matter title containing "Development
  Agreement" → `development_agreement`).
- **Output:** a `doc_class` column added to `packets/index.csv` (blank = unclassified —
  honestly out of pilot scope, NOT force-bucketed).
- **Quality gates before any fetch:** ground-truth a random sample of ≥50 classified rows
  per class against the live PDFs — require ≥95% precision per class; estimate recall by
  sampling ~100 unclassified rows and counting missed in-scope docs (report the estimated
  miss rate honestly; iterate tokens until <10% or documented why not).
- Classifier is a script in `packets/` (rerunnable, deterministic, config visible), never
  hand-edits.

## 6. Pipeline (classes 1–5)

1. Fetch classified rows via `scripts/polite_fetch.py` — **note the known `--batch`
   comma-filename mangling bug; fix or route around it before the run** (it silently drops
   files; see the magna incident).
2. Extract text: `pdftotext -layout`; `.docx` via `textutil`; scanned/no-text-layer pages
   → flag `extraction_method=ocr` or `needs_ocr` honestly (OCR floor is a recorded limit,
   not silently skipped). Record `sha256` of the binary, then **discard the binary**;
   retain `source_url` + sha256 as provenance. Keep text under `packets/text/` (the
   existing sidecar convention; `text_path` column).
3. Index columns added: `doc_class`, `text_path`, `sha256`, `text_chars` (keep
   `stored_locally=no` — it describes the binary). Conform to the SCHEMA_SPEC §9
   expansion contract; `validate_dataset.py` must PASS.
4. Oversize/404 rows: record outcome per row (`fetch_status`); a 404 is a dated honest
   gap, not a retry loop.

## 7. Zoning-code snapshot (class 6)

- New dataset `sandy_city_council/code/` with dated snapshot dirs (`code/2026-07/`), one
  markdown/text file per land-use title/chapter + `index.csv` (title_no, chapter, heading,
  source_url, retrieved_date, sha256). Land-use titles only (zoning, subdivision, and the
  development-code chapters) — not the whole municipal code.
- **Acquisition risk is the open question:** Municode is browser-only and the mirror is
  bot-blocked. Probe order: (a) Municode's public JSON backend endpoints if reachable
  politely, (b) a manual browser-assisted export session, (c) if neither works — record
  the whole class as a documented honest gap for Sandy and note that MunicipalCodeOnline
  S3 cities (the township wave) are cheaper first targets for this class at rollout.
- **⛔ PROBE OUTCOME (2026-07-16): HONEST GAP for Sandy** — evidence in
  `sandy_city_council/code/AVAILABILITY.md`. Municode's API is a redirect stub for Sandy
  (product `hasPdf=false`, `Jobs/latest` 204, `codesToc` 404; `ExternalCodeLink` →
  MunicipalCodeOnline); MCO's `book/expand`/`book/content` endpoints return HTTP 500
  "Unauthorized Access" to anonymous GETs (treated as a no — no auth games); the public
  MCO S3 bucket holds only adopted-ordinance PDFs (= the `ordinances/` diff layer, NOT
  consolidated Title 21 text). Re-probe only if MCO exposes an unauthenticated read path
  or Sandy migrates codifiers.
- Versioning convention: snapshots are dated states; the `ordinances/` layer remains the
  diff record. A snapshot is refreshed (new dated dir, old one kept) only on refresh
  cycles where the ordinance layer shows land-use code changes. Never backdate; never
  synthesize historical code text.

## 8. DB / FTS integration

- Text sidecars flow through the existing `document` catalog → `fts_packet` at the next
  federation (the plumbing already exists; the county's 358-doc fts_packet is precedent).
- Add `doc_class` to the federated document/packet rows so queries can filter
  ("staff_report only"). `code/` snapshots federate as documents with their own doc_class.
- Motion linkage: via `matter_id` through Sandy's existing extension tables — same rules
  as ordinances: quote only unique/high-confidence links; ambiguous stays flagged.
- Federation discipline: no `build_cities_db.py` run while any other agent is live; one
  federation at a work-package boundary.

## 9. Verification & acceptance (all must pass before calling the pilot done)

1. Classifier precision/recall gates (§5) met and reported with sample sizes.
2. Fetch/extract ledger: every classified row has fetch_status; text_chars>0 for ≥95% of
   born-digital rows; OCR-floor rows flagged, counted, honest.
3. `validate_dataset.py` PASS for packets/ + code/; `validate_city.py sandy_city_council/`
   0 FAIL; sources.csv regenerated.
4. The Sharkey acceptance test (§2) passes end-to-end via FTS after federation.
5. Spot-check: 10 random staff reports read against their motion + application rows —
   the text is the right document for the matter (no cross-matter contamination).
6. Disk report: total text bytes vs the ~14.9 GB binary counterfactual (expect ≤ ~300 MB).
7. Honest-gap ledger: ArcGIS-only GP content scraped at reduced fidelity is flagged as
   such; unclassified attachments counted; Municode outcome documented either way.

## 10. Rollout after the pilot (not in pilot scope)

- Fold classes 1–5 into `/expand-city-sources` (extend Source 1/packets with the
  doc_class+text pipeline) and class 6 as a new source type; per-city value gates (a
  township with 40 attachments doesn't need a classifier).
- ~~Cheapest first targets for `code/` at rollout: the MunicipalCodeOnline S3 cities.~~
  **CORRECTED by the 2026-07-16 probe:** MCO cities (Park City, South Jordan, Cottonwood
  Heights, Herriman, Millcreek all verified MCO-external) share the same auth-gated
  `book/*` endpoints — their S3 buckets feed `ordinances/`, not a class-6 snapshot.
  Re-scope the class-6 rollout list around **"codifier serves consolidated title text
  over public GET"**: Municode-NATIVE-hosted cities (where `Jobs/latest`/`CodesContent`
  return real content) or American Legal / Sterling platforms with printable HTML.
- County parallel: `salt_lake_county/` already stores staff-report text (fts_packet) —
  reconcile conventions rather than inventing a second one.
- Overlaps to reconcile at rollout: the deferred raw-PDF backfill (§Deferred in TODO) and
  the county "General Plan… (text corpus)" menu item.

## 11. Open questions for the owner

1. Go/no-go on pilot execution, and whether `code/` (class 6) is in the first cut given
   the Municode acquisition risk.
2. Does `doc_class` belong in SCHEMA_SPEC §9 as a standard optional column (my
   recommendation: yes, at rollout time)?
3. Snapshot cadence for `code/` (proposed: only when the ordinance layer shows land-use
   changes, checked at refresh).

---

## Appendix A — Watch list: deferred document classes (assess cost/benefit before admitting)

**Standing reminder: none of these are approved for acquisition. Before admitting any,
write down (a) the question pattern it answers that we have actually hit, (b) source +
fetch cost, (c) text-extraction fidelity, (d) expected corpus size. A class without a
demonstrated question pattern stays on this list.**

| Class | Value hypothesis | Cost/feasibility notes |
|-------|------------------|------------------------|
| Subdivision ordinances + design standards / form-based code manuals | De-facto density constraints (street widths, open-space ratios, design-review triggers) | Often inside the code host → mostly falls out of `code/` if class 6 lands |
| Consolidated fee schedules + impact-fee analyses (IFFP/IFA) | "What does it cost to build a unit here"; statutorily required, small corpus | City sites/packets; small and citable — likely first promotion off this list |
| Annexation policy plans + boundary/annexation agreements | Where growth CAN go | Lt. Governor's certified boundary actions = centralized source (cheap) |
| MIH **annual** reports (state compliance filings) | Year-over-year housing-policy compliance | State report page centralizes links; Sandy already holds a 2017 biennial — partially exists |
| Transportation / water / sewer master plans | Capacity constraints cited in denials ("insufficient sewer capacity") | Big PDFs, situational — fetch per-city when the question pattern appears |
| RDA/CRA project-area plans + tax-increment budgets | Core growth mechanism | Already queued on the county content menu; city RDAs (SLC, Ogden, WVC, Midvale) substantial |
| Hearing-officer / Board of Adjustment / appeal decisions | Quasi-judicial land-use outcomes invisible to council votes | Requires modeling new bodies (Orem BoA, CH Appeals Officer already flagged as unmodeled) |
| Land-use litigation settlements / consent decrees | Rare but can bind zoning for years | Watch-for, not sweep; no enumerable source |
| Adopted budgets + ACFRs | Revenue reliance on growth; impact-fee fund balances | Low density of load-bearing text; summary/ordinance sections only, if ever |
| Applicant rezone narratives / annexation petitions | Applicant's own framing | Staff reports usually restate operative facts — low marginal value |
| Building permits / housing starts | Hardest growth signal | STRUCTURED data, not document text — stays on the county menu; Ivory-Boyer (Gardner) compiles Utah permits centrally |
| Site plans, plats, traffic studies, engagement summaries | — | Skip: graphical or paraphrase-of-paraphrase; text extraction yields little |
