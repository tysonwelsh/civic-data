# ordinances/ — Ogden adopted ordinances index + linkage (as-of 2026-07-05)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on every existing
dataset; nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`, etc.

## What this is
An index of **adopted Ogden City ordinances** (308 rows, 2020-01-07 → 2026-06-16), each mapped to the
council **motion** that adopted it in `meeting_minutes/all_votes.csv`, with a confidence score. The
emphasis is **zoning / land-use**: **107 of 308 (35%)** are land-use (`land_use=yes`) — zoning-map
reclassifications, General Plan / community-plan amendments, Title 15 (Land Use Code) text amendments,
street/alley vacations, overlay/subdivision changes.

## Code host + independent archive (see AVAILABILITY.md for the full account)
- **Codified code host = American Legal Publishing** — `codelibrary.amlegal.com/codes/ogdencityut/`
  (current consolidated text incl. the Land Use Code). **HTTP 403** to the fetcher; current text only,
  not a number→date→subject history. Not the join backbone.
- **Independent adopted-ordinance archive = Recorder "Synopsis of Ordinance" affidavits**, posted to
  the city **DocumentCenter** (discrete PDFs, late-2023+) and **Utah Public Notice** (`utah.gov/pmn`,
  back to 2022). Each certifies a meeting date + the ordinance numbers adopted + full titles. **20
  signed PDFs retained in `raw/`** (1 South-Ogden false hit excluded), corroborating 32 numbers. The
  CivicEngage search returns only a fixed top-10 and cannot be paged, so this independent set is a
  partial cross-check, not exhaustive — the **council minutes are the backbone**.

## raw/ and text/
- `raw/` — the 20 signed synopsis / full-text ordinance PDFs, fetched verbatim via `polite_fetch.py`
  with `_fetch_log.jsonl` (url, status, bytes, sha256, retrieved_utc) as provenance. Browser UA; the
  `.com`→`.gov` DocumentCenter redirects are followed.
- `text/` — `pdftotext -layout` extracts of the 19 Ogden synopsis PDFs (labeled by ordinance number).
  `screen_corpus.py` = clean (0 PUA/mojibake/replacement anomalies; 4 advisory flags on the long
  full-text 2026 budget/salary PDFs are expected).

## index.csv columns
Minimum provenance cols (`date`,`title`,`source_url`,`retrieved_date`,`format`,`extraction_method`)
plus source-specific cols:
- `ordinance_no` — canonical `YYYY-NN` (zero-padded). Ogden uses one native spelling, `Ordinance YYYY-NN`.
- `adoption_date` (= `date`) — the council meeting date the adopting motion passed (for none rows, the
  Recorder synopsis's certified adoption date).
- `title` — ordinance subject, verbatim from the motion's `[ENTITLED:"…"]` / `[AGENDA ITEM:"…"]` bracket
  (or the synopsis PDF for none rows; or, for 4 bracket-less motions, the verbatim adoption sentence —
  noted in `linkage_note`).
- `source_url` — the independent synopsis PDF URL for high/none rows; otherwise the repo-relative
  **minutes file** that recorded the adoption (Ogden publishes no per-ordinance URL for most).
- `format` — `text` for all (born-digital synopsis PDFs; minutes are text — 2022 minutes are OCR'd but
  clean per meeting_minutes/CLAUDE.md).
- `extraction_method` — states minutes-derived vs. corroborated-by-synopsis vs. synopsis-only.
- `path` — the `raw/` synopsis PDF for high/none rows; empty for within_source (minutes-derived) rows.
- `land_use` — `yes`/`no`, regex on the title (informational).
- `result` — the adopting motion's verbatim tally (all indexed = a Pass form; empty for none rows).
- `matched_motion_date`, `matched_motion_no`, `match_confidence` — the linkage (below).
- `n_motion_events` — distinct (date, motion_no) motions that cite this number (0 = synopsis-only).
- `independent_source` — the corroborating synopsis PDF URL, if any.
- `minutes_source` — the repo minutes markdown that recorded the adoption vote (the join target).
- `linkage_note` — multi-date ambiguity, date conflicts, sibling-title borrowing, none-row reasoning.

## Linkage method + confidence — and the independence caveat
Each ordinance is joined to the council motion that adopted it (skill rule: join by adoption date +
ordinance number cited in the motion text). Adoption motions are detected across Ogden's wording
generations — "…ADOPTED AS OGDEN CITY ORDINANCE N" (2020–23), "ORDINANCE N … WAS ADOPTED [ENTITLED:…]"
(2024+), "ORDINANCE N BE ADOPTED", and amend-and-adopt — all OCR-tolerant (2022 minutes are scanned;
"WAS PASSED" OCR-garbles to "WASP ASSED" etc.). Ordinance numbers that appear only in an
`EXTEND/CONTINUE ORDINANCE N` reference are **not** treated as adoptions.

- **high (27)** — the ordinance number appears in BOTH the council adoption motion AND an independent
  Recorder Synopsis PDF (`raw/`). A genuine cross-source match.
- **within_source (276)** — derived from the council adoption motion text only. Because the number,
  date, and subject come *from* the motion, this linkage is strong **by construction** — but it is a
  **within-source** join, NOT independently corroborated. Labeled distinctly so it is never read as a
  cross-check. (No synopsis PDF was located for these numbers.)
- **none (5)** — adopted per a Recorder Synopsis PDF but with **no adoption motion in `all_votes.csv`**
  (2025-01 = a missing first-of-year meeting; 2026-09/10/13/14 = adopted 2026-06-16, beyond current
  minutes coverage which ends 2026-05-19). Match fields empty. **No match was forced.** See
  AVAILABILITY.md "Adopted ordinances missing from the vote layer."

To go from an ordinance to its full vote: read `minutes_source` (the exact minutes markdown), or filter
`meeting_minutes/all_votes.csv` on `matched_motion_date` + `matched_motion_no`.

## Caveats to respect
- **within_source ≠ verified.** 276 of 308 rows are minutes-derived only; treat the linkage as
  self-consistent, not corroborated.
- **4 multi-date rows** (2019-54, 2020-26, 2025-07, 2025-23) and the **2022-39 date conflict** (minutes
  Aug 9 vs Recorder Oct 4) are flagged in `linkage_note` — spot-check before quoting a single date.
- The index is a **floor**: an ordinance adopted via a motion that did not restate its `YYYY-NN` number
  (OCR loss, or a non-standard motion) is captured only if a synopsis PDF surfaced it.

Rebuild: re-run the Source-3 builder against `meeting_minutes/all_votes.csv` + `raw/` synopsis PDFs,
then `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py ogden_city_council/ordinances`.
