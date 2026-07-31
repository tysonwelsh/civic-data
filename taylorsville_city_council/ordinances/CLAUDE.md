# ordinances/ — Taylorsville adopted ordinances (2020–2026) + vote linkage

Additive dataset built by the `expand-city-sources` skill (source #3, zoning/land-use
ordinances). **Purely additive** — it does not modify `meeting_minutes/` or any other
existing dataset. It catalogs the city's adopted ordinances and links each to the council
motion that adopted it in `meeting_minutes/all_votes.csv`.

As-of: **2026-07-06**. Scope: **2020–2026** (the repo's 2020 data floor). A larger
**2012–2019 back-catalog** exists on the same PMN source but is out of scope (no matching
votes below the floor) — see `AVAILABILITY.md`.

## Where the ordinances come from — Utah Public Notice (PMN), NOT the code host

Taylorsville publishes **no online adopted-ordinance archive** and **no per-ordinance
"Notice of Adoption and Summary" page.** The dead ends checked (2026-07-06):
- **municipalcodeonline.com** S3 recipe — Taylorsville is **not a client** (bucket
  `municipalcodeonline.com-new`, us-west-2, has zero `taylorsville/` keys).
- **Code host = American Legal** (`codelibrary.amlegal.com/codes/taylorsvilleut`) — **403
  bot-protected and current-consolidated-text only** (no per-ordinance adoption dates).
- City site `our-city/city-code-ordinances` + `i-want-to/review-a-city-ordinance` — both
  just **iframe amlegal**; no ordinance list.
- City `elected-officials/public-notices` — meeting/budget/quorum notices only; **no
  ordinance-adoption notices**.

The **real independent archive is the Utah Public Notice Website**, council **body id 720**
(`utah.gov/pmn/list/notices.html?id=720&page=<big>` returns the full cumulative history in
one GET). Body 720 attaches the actual ordinance PDFs to its notices in two flavors, both
harvested here:
- **`meeting_material`** — the ordinance as presented on a "City Council Meeting" agenda
  (for 2020 these are large *Agenda Summary Form* bundles: staff report + ordinance text,
  ~3.4 MB each).
- **`adopted`** — the **signed/executed final** ordinance, posted a day or two later under a
  "Newly Adopted Ordinance(s)" notice.

Per ordinance number we keep **one canonical PDF** in `raw/` (preferring the signed/adopted
version, else the meeting-material one). `raw/_fetch_log.jsonl` is the byte-level provenance
(url, status, sha256, bytes) written by `scripts/polite_fetch.py`. Raw is **588 MB / 84
PDFs** (the 2020 agenda-summary bundles dominate; retained verbatim per the non-negotiable
rule). PMN was fetched with the browser UA in `polite_fetch.py` (the city CMS 403s bare
bots, but PMN itself does not).

## ⚠ Taylorsville runs PARALLEL ordinance & resolution number sequences

`Ordinance No. 20-09` and `Resolution No. 20-09` are **different documents with the same
number** (an ordinance amending code §13.19.010 vs a resolution adopting the CDBG plan). The
linkage is therefore keyed on the **instrument word + number** (`Ordinance NN-NN`), never the
number alone. When a number appears in votes as an ordinance but PMN only has a *resolution*
of that number, the ordinance PDF was simply never posted → it stays `within_source` (see
below). This bit the first pass; the parser now excludes `resolution`-labeled attachments.

## index.csv columns

Required six (`date, title, source_url, retrieved_date, format, extraction_method`) plus:
- `ordinance_no` — `YY-NN` (2-digit adoption year + sequence; `20-01` = 2020 ord #1).
- `date` / `adoption_date` — the **council adoption date** (the vote date for matched rows;
  the PMN meeting-agenda date for `medium`; the vote date for `within_source`).
- `path` — dataset-relative (`raw/ord_<YY-NN>__<pmnFileId>.pdf`); empty for `within_source`
  rows (no independent doc on disk).
- `format` — `text` (born-digital, 81), `scanned` (3: 24-01/24-02/24-04, RICOH JPEG scans →
  `tesseract-ocr`; TIFF rasterization — the anaconda leptonica cannot read PNG here), `na`
  (6 within_source).
- `land_use` — `yes`/`no` keyword classifier over title+motion (zoning/general-plan/land-
  development/rezone/subdivision/vacation/height/flood/etc.). **64/90 = 71 % are land-use.**
- `result` — (§9 contract column; blank where not recorded)
- `matched_motion_date`, `matched_motion_no`, `match_confidence` — the vote linkage.
- `pmn_notice_type` — `adopted` (signed final) / `meeting_material` / `none` (within_source).

## Linkage method + confidence (the join to all_votes.csv)

Join key = the **ordinance number cited in the council motion text** in
`meeting_minutes/all_votes.csv`, corroborated by the independent PMN ordinance PDF.

- **`high` (75)** — number cited in an adopted council motion **and** an independent PMN
  ordinance PDF exists. `matched_motion_no` = the motion, `matched_motion_date` = vote date.
- **`medium` (9)** — the ordinance is on a PMN council-meeting agenda **and** has a signed
  PMN adopted doc, but the number is **absent from the `all_votes.csv` motion text** (the
  clerk's motion said "approve the ordinance as presented" without the number, or the number
  OCR-garbled). Date + subject agree; the specific motion isn't number-cited.
  (22-08, 24-05, 24-07, 25-01, 25-02, 25-03, 25-07, 25-08, 25-15.)
- **`within_source` (6)** — cited in an adopted council motion but **no independent ordinance
  PDF exists on PMN** (only a same-numbered *resolution*, or the ordinance was never posted).
  `source_url` points at the **minutes doc**, not an ordinance PDF; this linkage is `high` *by
  construction* (it comes from the motion itself) and is **NOT independently corroborated** —
  do not read it as cross-matched. (20-09, 20-10, 20-11, 22-27, 22-28, 25-25.)
- **`none`** — deliberately **unused**. No ordinance was force-matched, and every PMN
  ordinance in scope reconciled to a council action. Pre-2020 PMN ordinances are not indexed
  (below the floor) rather than carried as `none`.

**Ordinances in PMN but missing a number-citation in votes** are the 9 `medium` rows — a
gap in the *vote layer's* motion text, not missing ordinances (all 9 have signed adopted
PDFs). **Ordinances in votes but missing an independent PMN doc** are the 6 `within_source`.

## Rebuild

Not a generated layer — this is a retrieved dataset. To refresh: re-crawl
`utah.gov/pmn/list/notices.html?id=720&page=400`, diff new ordinance attachments against
`index.csv`, fetch via `scripts/polite_fetch.py` into `raw/`, extract text sidecars
(`pdftotext -layout`; scans → `pdftoppm -tiff` + `/opt/homebrew/bin/tesseract`), and re-run
the linkage against `meeting_minutes/all_votes.csv`. Validate with
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
taylorsville_city_council/ordinances` (PASS as of 2026-07-06).
