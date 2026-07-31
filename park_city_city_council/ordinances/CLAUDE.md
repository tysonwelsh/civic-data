# ordinances/ — Park City adopted ordinances index + linkage (as-of 2026-07-05)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on every
existing dataset; nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`, etc.
Coverage, counts, and gaps: **`AVAILABILITY.md`**. Rebuild: `python3 build_index.py`.

## What this is
An index of **adopted Park City ordinances 2020–2026** (262 rows; refreshed 2026-07-19), each
mapped to the council motion that adopted it in `meeting_minutes/all_votes.csv`, with a
confidence tier. Land-use (zoning/subdivision/LMC/general-plan/annexation) is 160/262. One row
per ordinance number (`YYYY-NN`), union of two independent sources below.

## Code host & independent archive (this is unusual — Park City HAS one)
- **Codified current code** — Municode: `parkcity.municipalcodeonline.com` (Land Management
  Code / Municipal Code, current consolidated text) and the Municode Library mirror
  `library.municode.com/ut/park_city`. Current text only — no number→date→subject history.
- **Signed adopted-ordinance archive (INDEPENDENT)** — the MunicipalCodeOnline document store,
  a **publicly list-able S3 bucket**: `https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/parkcity/ordinances/documents/`
  (list with `?list-type=2&prefix=parkcity/ordinances/documents/`). 371 signed ordinance PDFs
  total; the 98 in-window numbers (104 files) are cached in `raw/`. Each PDF is born-digital
  and states its number, full title, and a *"PASSED AND ADOPTED this <day> day of <Month>,
  <Year>"* clause. **This is a genuine independent adoption record** — the source of every
  `high` confidence link. (The Municode drafting API `bookadmin/ordinance` requires sign-in
  and was NOT used; only the public S3 objects and the public bucket listing were fetched.)
- Park City also deep-links individual ordinances as `parkcity.gov/home/showpublisheddocument/<id>/<ver>`
  (CivicClerk); the S3 bucket is the complete set, so those were not separately harvested.
- All fetching via `polite_fetch.py` (GET-only, browser UA, ≥1 s throttle);
  `raw/_fetch_log.jsonl` is the provenance (url/status/bytes/sha256/retrieved_utc).

## Linkage method + the independence caveat
Each ordinance number is joined to the council motion that adopted it. The **adopted number is
the FIRST `Ordinance (No.) YYYY-NN` cited in a motion** ("moved to approve Ordinance No. X, an
ordinance …"); any later numbers in the same motion are references to *prior* ordinances being
amended/extended and are deliberately not attributed. Citations are restricted to the
2020–2026 window (out-of-window tokens like `2019-60` are cross-references, not adoptions).

`match_confidence`:
- **high (96)** — the number appears in BOTH a signed S3 PDF (independent) AND a council
  motion. This is a true **cross-source** confirmation. `source_url` is the S3 PDF; `path`
  points at `raw/`. (Was 93; the 2026-07-19 votes refresh linked `2026-14/16/17` to their
  2026-06-25 motions.)
- **within_source (164)** — the number is known ONLY from council motion text; no signed PDF
  exists in the archive for it. The number, date, and subject all come from the **same**
  audited `all_votes.csv` row, so the join is strong **but not independently corroborated** —
  treat it as a within-source derivation, not a cross-match. `source_url` is the minutes
  markdown; `path` is empty.
- **medium / low** — reserved for the date+subject fallback (signed PDF matched to a motion
  that does not restate the number): medium ≥0.34 subject overlap on the adoption date, low
  ≥0.20. **0 rows** currently (every signed ordinance matched by number or fell to none).
- **none (2)** — signed ordinance with no linkable vote row. Match fields **empty, never
  forced**. Both are in-coverage audit signals (adopted on the consent agenda, not itemized:
  2024-08, 2026-08). See `linkage_note` and AVAILABILITY.md. **Owed the other way:** two 2026
  ordinances have the motion captured but no signed PDF yet — `2026-15` (FY26/FY27 budget) and
  `2026-18` (elected-official compensation), both adopted 2026-06-25, sit at `within_source`
  because Municode's S3 archive does not carry these non-codified administrative ordinances
  (honest gap logged 2026-07-19 — see AVAILABILITY.md "Signed PDFs still owed").

To go from an ordinance to its full vote: filter `meeting_minutes/all_votes.csv` on
`matched_motion_date` + `matched_motion_no`, or open `minutes_source`.

## index.csv columns
Required provenance (`date`,`title`,`source_url`,`retrieved_date`,`format`,`extraction_method`)
plus: `ordinance_no` (canonical `YYYY-NN`), `adoption_date` (= `date`; council motion date for
matched rows, PDF PASSED-AND-ADOPTED date for `none`), `path` (the `raw/` PDF; empty for
minutes-only rows), `land_use` (informational regex on subject), `result` (verbatim motion
result), `matched_motion_date`, `matched_motion_no`, `match_confidence`,
`land_use_category` (informational regex on subject), `n_motion_events` (distinct motions
citing the number), `has_signed_pdf`, `linkage_note`, `minutes_source`. `format` is `text` for all
(born-digital PDFs and born-digital minutes; nothing scanned).

## Known limitations
- **within_source is a floor, not a cross-check** — 164 rows rest on the minutes alone. To
  upgrade, obtain the signed PDF (only ~half the in-window numbers are in the S3 archive).
- **5 within_source rows link to a continue/deny motion** (2022-05, 2023-06, 2023-17, 2024-04,
  2025-19) — the number was cited but that motion wasn't the final adoption; `result` shows it.
- **Land-use classification is regex on the subject** (informational); verify before citing a
  category. Subdivision/plat dominates (107) because Park City adopts many plat ordinances.
