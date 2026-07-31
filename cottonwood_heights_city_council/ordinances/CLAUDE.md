# cottonwood_heights ordinances/ — adopted ordinances (build notes)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 3). Additive dataset;
it NEVER touches the audited `meeting_minutes/` layer — it only READS `all_votes.csv`,
`motions_std.csv`, and `minutes_index.csv` to enumerate ordinances and compute the motion
linkage.

## What this dataset is

A per-ordinance index of every **adopted ordinance 2020→present** for Cottonwood Heights,
each linked to the enacting council motion in `meeting_minutes/all_votes.csv`, with the
signed ordinance PDF retained where one is published. Cottonwood Heights council motions
cite the ordinance number richly ("moved to approve Ordinance 407"), so the number →
adoption-date → subject → motion map is derivable straight from the vote layer; the PDFs
corroborate it and provide the ordinance body text for FTS.

## Counts (2026-07-13 build)

- **128 adopted ordinances**, window **2020-01-07 → 2026-05-19** (Ord 336 → 467, plus one
  year-based `Ordinance 2024-58`; sequential gaps 392/455/456/457 and the failed 464 are
  logged in `unrecovered.csv`).
- **match_confidence:** high 86 · within_source 36 · none 5 · low 1. All 86 `high` rows were
  verified to genuinely cite the ordinance number in the matched motion (0 mismatches).
- **doc-backed:** 92 rows carry a retained PDF (pmn 57 · s3 35); 36 rows are
  `within_source` (motion-only, `format=na`).
- **format:** scanned 81 · text 11 · na 36. **land_use=yes:** 40.
- **raw/:** 121 PDFs retained (39 S3 + 82 PMN). One PMN attachment titled "Ordinance
  2024-09" is actually **Resolution No. 2024-09** (a bank-account resolution) — retained in
  `raw/` for provenance but **excluded from the index** (it is not an ordinance; the drop
  is by document-body inspection, printed by `ch_ord_build.py`). Ordinances with both a PMN
  and an S3 PDF index one as `path` (the ordinance body over any posting-notice PDF) and
  retain the other.

## Where the documents come from

Two independent public sources are unioned (there is no single complete online
ordinance-PDF archive; the codifier's full metadata list is behind auth):

1. **MunicipalCodeOnline (the city's codifier) public S3 bucket** —
   `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/cottonwoodheights/ordinances/documents/`.
   The bucket allows anonymous `ListBucket` (verified 2026-07-13), so every "proposed
   action document" PDF the codifier tracks is enumerable and downloadable. 39 keys (one
   Ord 454 is a 58-second re-upload duplicate). Filenames carry a Unix-timestamp UPLOAD
   prefix (NOT the adoption date). This set reaches the most recent ordinances (through
   **Ord 454**, Dec 2025). Catalog: `s3_documents.csv`.
2. **Utah Public Notice (PMN) — Cottonwood Heights City Council body 2147.** There is NO
   dedicated PMN "ordinances" body for CH (unlike Murray's 7321); the signed ordinance
   PDFs are posted as **attachments on the council meeting notices** (mostly labeled
   "Public Information Handout"). The full notice history is one GET:
   `https://www.utah.gov/pmn/list/notices.html?id=2147&page=300` (the cumulative view;
   the 6-month list and the historical search are POST/CSRF and off-limits to the polite
   GET rule). 82 ordinance PDFs recovered (one file id, Ord 304 2018, 404'd — pre-floor,
   logged in `unrecovered.csv`). This set is dense **2020→2024 (Ord 336–422)**. Catalog:
   `pmn_documents.csv`; parsed attachment table: `pmn_attachments.csv`.

**Codified-code host (recorded, not mirrored):** MunicipalCodeOnline —
`https://cottonwoodheights.municipalcodeonline.com/` (book view
`?type=ordinances`; Municode Library mirror at
`library.municode.com/ut/cottonwood_heights`). The public book UI is an AngularJS SPA whose
list endpoint (`bookadmin/ordinance`) requires auth; the current **consolidated code text**
is browse-only there. We mirror only the individual adopted-ordinance PDFs from the public
S3 bucket, not the codified code. Older/other ordinances: GRAMA to `recorder@ch.utah.gov`.

## Files

- `raw/` — every fetched PDF verbatim (39 S3 + 82 PMN = 121) + `_fetch_log.jsonl`
  (url, http status, bytes, sha256, retrieved_utc per fetch). Names:
  `s3_<uploadTs>_Ord<n>.pdf`, `pmn_f<fileId>_Ord<n>.pdf`.
- `text/` — one `.txt` sidecar per raw PDF. **Most CH ordinance PDFs are Recorder-certified
  signed SCANS with no text layer**, so those sidecars are **tesseract 5 OCR @300 dpi**
  (rendered via pymupdf); the born-digital minority use `pdftotext -layout`. Method +
  char-count per file in `text/_extraction_log.csv`; the same value is written to each
  index row's `extraction_method`/`format`. OCR noise (mangled ordinals like `3"` for
  `3rd`, `!` for `I`) is preserved, never "cleaned". These sidecars feed `cities.db`
  `fts_ordinance` on the next `build_cities_db.py`.
- `index.csv` — SCHEMA_SPEC §9 contract header + CH extras
  (`doc_source, variant_adopted, pmn_notice_id, pmn_notice_url, adoption_date_source,
  n_docs, linkage_note`). One row per adopted ordinance.
- `citations_map.csv` — every ordinance-number citation found in a council motion (date,
  motion_no, body, action verb, outcome, is_adoption), the transparency trail behind the
  linkage.
- `s3_documents.csv` / `pmn_documents.csv` / `pmn_attachments.csv` — the raw discovery
  catalogs (build inputs).
- `unrecovered.csv` — honest gap log (see AVAILABILITY.md).
- Helper scripts (idempotent, no network unless noted):
  `ch_ord_parse_pmn.py` (PMN notices HTML → attachment table),
  `ch_ord_extract_text.py` (text/OCR sidecars),
  `ch_ord_build.py` (rebuilds `index.csv` + `citations_map.csv` from the vote layer +
  the two doc catalogs + `text/`).

## Adoption date (`adoption_date` / `date`), provenance in `adoption_date_source`

1. `motion` — the date of the passed council approve/adopt motion that cites the number,
   from `all_votes.csv`. **Authoritative** (the council vote is the enactment). Used for
   every row with a motion match.
2. `pdf` — for doc-only ordinances (no number-citing motion), parsed from the signed
   document's adoption clause ("PASSED AND APPROVED this Nth day of Month, YYYY").
3. `pmn_event` — fallback: the PMN notice "Event Start Date & Time" (the meeting).

## Motion linkage (`match_confidence`) — the honest distinction

Confidence describes the tie between the ordinance and a row in `all_votes.csv`:

- **high** — an independent ordinance PDF exists AND a passed council motion on the
  adoption date cites that ordinance NUMBER (date + number both corroborated). CH's
  number-citing motion style makes this the common case for the 2020–2024 documented set.
- **medium** — a PDF exists, matched to a motion by date + subject (number not literally
  in the motion).
- **low** — a PDF exists, matched by date only.
- **none** — a PDF exists but no motion match (adopted at a meeting outside the vote
  layer, or a consent-agenda ordinance not itemized in the minutes' motion list).
- **within_source** — **NO independent PDF**; the row is derived from the motion citation
  itself. Number/date/subject are self-consistent *by construction*, NOT independently
  corroborated — do not read `within_source` as a cross-verified match. `source_url` for
  these points at the enacting meeting's minutes PDF (the actual source of the fact);
  `format=na`, no `path`.

## Cottonwood Heights specifics baked into the build

- **`variant_adopted` (‑A / ‑D drafts).** CH prepares alternative draft ordinances under
  one number — a `‑A` (approve/adopt) and a `‑D` (deny) version — and the council adopts
  whichever fits ("moved to APPROVE Ordinance 379‑D **denying** a General Plan
  Amendment"). `ordinance_no` is the bare number; `variant_adopted` records which draft
  passed. An adopted `‑D` is still an adopted ordinance (it enacts a denial).
- **Two numbering schemes.** The main sequential series (336…467) plus a small year-based
  administrative series (`Ordinance 2024-NN` — surplus-property / bank-account consent
  items). Both are enumerated where cited in a passed motion.
- **Mayor votes (max roll 5).** Land-use/rezone ordinances are `body=Council` (or `CDRA`
  for redevelopment project-area ordinances, e.g. Ord 391). No mayor-tie-break assumption
  is used anywhere here.
- **Adoption requires a PASSED approve/adopt motion.** `result` is copied verbatim from the
  motion row; this layer never re-derives tallies. The two retained clerk-error tallies from
  the core build do NOT mislead it: **Ord 405** (2023-11-21, "passed 4-to-1") is a real
  adoption → indexed; **Ord 464** (2026-05-19, "failed 4-to-2", the phantom-"Highland"
  case) — the motion to APPROVE it **FAILED**, so 464 was **not adopted** and is correctly
  **excluded** from the index (logged in `unrecovered.csv`).
- **Resolutions mislabeled as ordinances are dropped.** One PMN attachment titled
  "Ordinance 2024-09" has a **RESOLUTION** body (bank account); `ch_ord_build.py` inspects
  each document's preamble ("AN ORDINANCE" vs "A RESOLUTION", OCR-punctuation-tolerant) and
  excludes resolutions while keeping the raw.

## Rebuild

```
python3 ch_ord_parse_pmn.py <saved pmn notices html> pmn_attachments.csv   # only to refresh PMN
python3 ch_ord_extract_text.py                                             # sidecars (OCR)
python3 ch_ord_build.py                                                    # index.csv + citations_map.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
The dataset loads into `cities.db` `ordinance` + `fts_ordinance` on the next
`scripts/build_cities_db.py` (run by the orchestrator, not here).
