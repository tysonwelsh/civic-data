# ordinances/ — Herriman adopted ordinances (build notes)

Additive dataset (`expand-city-sources` Source 3), built **2026-07-13**. Maps adopted
**Ordinance YYYY-NN → adoption date → subject → the council motion that passed it**, so a
vote in `../meeting_minutes/all_votes.csv` links to what the ordinance did. **274 distinct
ordinances** (2014→2026 back-catalog; the repo's analytical window is **2020+ = 194
ordinances, 130 land-use**). Regenerate: `python3 extract_text.py && python3 build_index.py`
(idempotent, no network in build_index).

## Three sources, three evidence roles (READ THIS)

1. **Municipal Code Online public S3 archive** (independent, FULL signed text) —
   `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/herriman/ordinances/documents/`
   (anonymous ListObjectsV2 works; every key in `archive_backcatalog.csv`). 111 distinct
   signed PDFs 2018–2026, stored as `raw/archive/<num>.pdf` (latest upload per number;
   re-uploaded numbers keep all keys in the backcatalog). Filenames embed the zoning case
   (`case_no` column, e.g. Z2021-45). ~91% wet-signature scans → **tesseract OCR @300dpi**
   sidecars (`text/<num>.txt`, labeled per stem in `text/_extraction_log.csv`); 10
   born-digital (`pdftotext -layout`). OCR ordinal noise (`8"` for `8th`) preserved.
2. **PMN Recorder adoption notices** (independent, number + adoption-meeting date +
   subject; **summary only, NO full text**) — PMN entity 155, bodies 1287 ("Public
   Hearings and Notices") + 1155 ("City Council"); 190 notices 2014–2026 in
   `raw/pmn/notice_<id>.html` + `text/notice_<id>.txt` sidecars; catalog
   `pmn_notices.csv`. Herriman's PMN notices carry no PDF attachments (unlike Murray).
3. **Council minutes backbone** (`../meeting_minutes/all_votes.csv`, READ-ONLY) — motions
   citing an ordinance number. **Number grammar has three eras**: `01-2020` (NN-YYYY,
   early 2020, resurfacing occasionally, e.g. "18-2025"), `2020-07`+ (YYYY-NN), and the
   notices' `14-25` (YY-NN, 2014). All normalized to `YYYY-NN`; source strings verbatim.

## Linkage rubric (`match_confidence`)

- **high** — an independent document (archive PDF or PMN notice) exists AND a council
  motion cites the number AND the motion date agrees with the stated adoption date
  (or no independent date exists to conflict). 125 rows (2020+).
- **medium** — independent doc + date-and-subject agreement but the number linkage is
  imperfect: the motion prints a typo'd number (CITE_REMAPS), the motion date conflicts
  with the notice-stated date (the 2021-17/18/20 cluster), subject-scored match with
  no number in the motion, or (2026-07-29) a **consent-agenda match**.
  - **Consent-agenda matching (2026-07-29).** A council genuinely ADOPTS ordinances inside
    a consent agenda, but the motion text ("approve the consent agenda as written") carries
    no subject, so the subject scorer can never see it. `consent_match()` reads the
    ENUMERATED consent items out of the minutes markdown instead and links only when
    exactly ONE item matches the notice subject — by shared code citation (Title/Chapter/
    Section N) or ≥2 shared subject tokens. The matched item is quoted in `linkage_note`.
  - **`PROCEDURAL_RE` guard (2026-07-29).** A motion that only adjourns / recesses /
    convenes a closed session (or approves the agenda) is no longer a subject-match
    candidate. Generic words in such a motion used to out-score the real one: **2022-36**
    (amending Title 2, boards and commissions) was linked to the 2022-08-24 **closed-session
    recess** on a score of 2 vs 1, carried entirely by "council" + "utah". It now links to
    that meeting's consent-agenda motion (#2), whose enumerated item 9.3 is "Update to
    Title 2 of Herriman City Code". Net effect on the index: this one row.
- **low** — stated adoption date has minutes but no attributable motion (consent-agenda
  or unextracted item); `matched_motion_date` set, `matched_motion_no` blank. 9 rows.
- **within_source** — witnessed ONLY by the citing motion (no independent doc): high by
  construction, **NOT corroborated**. `source_url` points at the minutes PDF; `path`
  blank, `format=na`. 42 rows.
- **none** — independent doc, no match. All 80 pre-2020 rows (below the vote floor) +
  12 rows on dates with no extracted motions (several are the missing-minutes dates —
  see AVAILABILITY.md "Leads"). **Never forced.**

## adoption_date provenance (`adoption_date_source`)

`pmn-notice` (the Recorder states the meeting date — strongest) → `motion` (high /
within_source / remapped rows) → `pdf-clause` ("PASSED AND APPROVED this Nth day of …",
OCR-fragile, fallback only) → `pdf-recital`/`pdf-cover` (3 pre-2020 archive-only rows
hand-read via `MANUAL_DATES`; **2019-20 is month-granular `2019-07`** — its PDF is the
rate-study exhibit with an unexecuted signature block) → blank (within_source rows cited
outside their series year stay blank rather than guess).

## Documented city-error overrides (sources kept verbatim; see build_index.py tables)

- `NOTICE_NUM_OVERRIDES` — Recorder printed the wrong/missing number: 675239
  (2021-10 → the fireworks ordinance is **2021-11**), 819153 (2022-06 → the annexation
  is **2023-06**), 796087 (prints only zoning case Z2022-116 = **2022-40**).
- `NOTICE_DATE_OVERRIDES` — Recorder printed the wrong meeting date: 846044/846052/
  846056 ("July 12, 2022" → **2023-07-12**; posted 2023-07-14, 2023-series numbers,
  identical-subject motions that day), 1080729 ("May 14, 2026" → **2026-05-13**).
- `CITE_REMAPS` — the MINUTES printed the wrong number (rows held at medium):
  2025-08-13 #14 prints 2025-18 for the wireless ordinance signed as **2025-17**;
  2023-04-12 #3 prints 2023-05 for the cemetery amendment signed as **2023-08**.
- Genuine same-number collisions with no independent tiebreaker keep the
  date-corroborated motion and list the rejected co-citation in `linkage_note`
  (2021-16: transportation plan vs a budget motion; 2022-01: mayor salary 2022 vs a
  Title 2 motion in 2023).

## Schema

`index.csv` — SCHEMA_SPEC §9 ordinances contract header
(`ordinance_no,adoption_date,date,title,source_url,retrieved_date,format,
extraction_method,path,land_use,result,matched_motion_date,matched_motion_no,
match_confidence`) + extras `pmn_notice_id,pmn_notice_url,adoption_date_source,case_no,
linkage_note,minutes_source`. `format` ∈ `text` (born-digital PDF) / `scanned` (OCR) /
`html` (notice-only) / `na` (within_source). `result` is the matched motion's verbatim
result string. `land_use` is a keyword classifier over title+filename+motion+first 1.5KB
of text with a non-land-use guard — a convenience filter, not a legal category.

## Codified-code host (recorded, NOT mirrored)

**Municipal Code Online** — `https://herriman.municipalcodeonline.com/book?type=ordinances`
(the city's "City Code" link). SPA; its XHR endpoints return "Unauthorized Access" to
non-browser clients — current-consolidated-text only, use manually. The public S3 bucket
behind it (source 1 above) is the sanctioned bulk path and is what this dataset mirrors.

## Files

```
raw/archive/<num>.pdf        111 signed ordinance PDFs (+ _fetch_log.jsonl)
raw/pmn/notice_<id>.html     190 PMN adoption notices verbatim (+ _fetch_log.jsonl)
text/<num>.txt               PDF sidecars (101 tesseract OCR, 10 pdftotext)
text/notice_<id>.txt         notice sidecars (headed "summary only")
text/_extraction_log.csv     per-stem format + extraction_method (build input)
archive_backcatalog.csv      every S3 key verbatim (incl. superseded uploads)
pmn_notices.csv              the PMN crawl catalog (notice_id, body, title, listed dt)
index.csv                    the §9 contract index (274 rows)
unrecovered.csv              12 series holes 2020+ (numbers witnessed nowhere)
extract_text.py              sidecar extractor (OCR-aware, idempotent)
build_index.py               index builder (offline, idempotent)
```

## Caveats

- **within_source ≠ corroborated** (42 rows); only high/medium rows have an independent
  witness. `html`-format rows have a one-sentence summary, not the ordinance text.
- **Do not treat the archive or the notices as complete** — both are selective (see
  AVAILABILITY.md); the series holes in `unrecovered.csv` are honest unknowns.
- The Mayor VOTES in Herriman (max roll 5) — any tally analysis joined through
  `matched_motion_*` must count the Mayor as a normal voter (see the city CLAUDE.md).
- Spot-checked ground truth 2026-07-13: 2021-31 (shipping containers, Z2021-45),
  2022-14 (internal ADUs, Z2022-025), 2024-08 (heliports) — signed PDF, PMN notice,
  and motion all agree on number/date/subject; 2021-31's signed clause ("8th day of
  December 2021") matches the motion date exactly.
