# ordinances/ — Midvale adopted ordinances (build notes)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 3). **Additive** — this
dataset only READS `../meeting_minutes/all_votes.csv` + `minutes_index.csv` to compute the
motion linkage; it never modifies the audited minutes/votes layer.

Maps each adopted **Ordinance No. YYYY-O-NN → adoption date → subject → the council motion
that enacted it**, so a vote in `../meeting_minutes/all_votes.csv` links to the ordinance
text. **263 rows**: 261 retained documents (256 signed ordinances + 5 publication-notice
gap-fillers) + 2 `within_source` motion-only rows. Window **2012-O-01 → 2026-O-22**
(the 2020→present mandate is 142 documents; 2012–2019 is a cheap complete back-catalog).
Regenerate: `python3 build_index.py` (idempotent, no network).

## Where the documents come from — the city posts its OWN full ordinance archive

Unlike most cities (where only the current-year Recorder notices are online and the
back-catalog lives on PMN), **Midvale publishes every signed ordinance on its own Revize
Document Center**, listed by number on the Recorder's Office page:

- **Signed ordinances (primary):** `recorder_s_office/midvale_city_ordinances.php` links
  257 PDFs under `Document Center/Government/Departments/Recorders Office/Midvale City
  Ordinances/<YEAR>/…` (year folders **2012–2026**). These are the **Recorder-certified,
  signed instruments** (the actual ordinance text + WHEREAS clauses + adoption clause).
  Harvested by `mv_harvest_links.py` → `_sources.csv` → `_fetch_batch.txt`.
- **Publication notices (gap-fillers only):** `recorder_s_office/public_notices.php` posts
  "Ordinance Publications" (the newspaper/website publication proofs, 2022–2026). Most
  duplicate a signed ordinance, so **only the 5 whose number has NO signed PDF were
  retained** (`kind=publication`, name `<num>_pub.*`): 2023-O-15, 2024-O-02, 2024-R-06,
  2024-R-08, 2024-R-20.
- **Codified municipal code host (NOT mirrored):** **`midvale.municipal.codes`**
  (General Code / "Municipal Codes" platform) — current consolidated text only, no
  per-ordinance adopted PDFs. Recorded here; the signed-ordinance PDFs + council minutes are
  the backbone, so the code host is a manual reference for current text, per the skill's
  standing rule.
- **PMN:** Midvale entity **201**; the Recorder's adopted-ordinance record is the city
  portal above, so PMN was not needed as an ordinance source (a sibling `pmn_backfill/`
  dataset independently sweeps PMN for missing *minutes*). Midvale PMN bodies: 753 Council,
  754 PC, 756 RDA, 757 MBA.

## Files

- `raw/` — 261 documents verbatim (~1.0 GB; the signed ordinances are large scanned
  wet-signature PDFs) + `_fetch_log.jsonl` (url/status/bytes/sha256/retrieved per fetch).
  Filenames are the canonical ordinance number (`2024-O-16.pdf`); the 2022-O-03 a/b pair are
  two source files for one number.
- `text/` — 261 sidecars + `_extraction_log.csv` (per-file `format` + `extraction_method`).
  **151 born-digital** (`pdftotext -layout`) + **110 OCR** (`tesseract 5 @300 dpi`, capped
  at the first 15 pages — a signed ordinance's operative text is at the front; later pages
  are image-only map/plat exhibits with no text). OCR noise (garbled ordinals, `'`→`th`) is
  preserved, never "cleaned". `screen_corpus.py` (2026-07-13): clean — no cid/mojibake/stub;
  the 2 `duplicate_bodies` are the intentional 2022-O-03 a/b pair; outliers are benign scan
  artifacts. Two corrupt-xref source PDFs (2018-O-06, 2018-O-08) were `gs`-repaired before
  OCR; 2025-O-01 was force-OCR'd (its only text layer was a DocuSign envelope stamp).
- `index.csv` — SCHEMA_SPEC §9 ordinances contract header + city extras
  (`kind, adoption_date_source, sha256, linkage_note`). One row per document + 2
  within_source. **Never hand-edit** — regenerate.
- `unrecovered.csv` — ordinance numbers a council motion ADOPTED but for which the city
  posts no signed PDF (the 2 within_source rows).
- `mv_harvest_links.py` (portal HTML → `_sources.csv`; needs the scratchpad HTML captures),
  `extract_text.py` (sidecars; idempotent, resumable, page-capped OCR), `build_index.py`
  (the index; no network).

## Motion linkage (`matched_motion_date`, `matched_motion_no`, `match_confidence`)

Midvale council motions **cite the ordinance number richly** (`MOVED to Approve Ordinance
No. 2024-O-16 …`), so the number itself is the join key. `ORD_RE` tolerates the OCR variants
seen in the minutes: `O`→`0`, `O`→`00`, and the second hyphen rendered as `.` (`2022-0.05`).
Both separators are mandatory and the letter slot is O/0 only, so a bare date (`2020-01-07`)
can never match — **verified zero date false-positives** on `all_votes.csv`.

**REPAIRED 2026-07-29 — two coupled defects.**
1. `ORD_RE` tolerated the OCR `O`↔`0` swap only in the LETTER slot, not in the **year** or
   the serial's leading zero. The scans print `2O23-O-O1`, `2O22-O-13`, `2024-O-10`, so the
   real enacting motions were invisible: **14 rows moved `none`/`low` → `high`** (all
   verified — each matched motion cites its own number under an adopting verb), and
   2023-O-04 `medium` → `high`.
2. A citation only counts as an **ENACTMENT** when an adopting verb governs it
   (`cited_nums(..., adopting_only=True)`, preferred by `choose_adopting`). Midvale's
   consent-agenda motion text bleeds into the NEXT agenda heading, so it "cites" the
   number of an item it never enacted: **2023-O-01** was linked to the consent agenda by
   that bleed (`… VII. ACTION ITEMS A. CONSIDER RESOLUTION NO. 2023-0-01 …`) and now links
   to the true motion "MOVED to Approve Ordinance No. 2O23-O-O1 Amending Section 5.08 …
   regarding Business Licenses".

⚠ **Side effects worth knowing.** (a) 2023-O-01 and 2020-O-01 now link to the **correctly
dated copy** of their meeting (2023-01-17 / 2020-01-21, `provenance=pmn_minutes`) instead of
a mis-dated duplicate — see the duplicate-meeting note below; 2023-O-01's new adoption_date
matches its signed PDF's own clause ("this 17th day of January, 2023"). (b) The
**2022-O-03 number collision** (two unrelated documents share the number) now resolves to
the EARLIEST adopting motion (2022-01-18 #2, electronic meetings) for BOTH rows, per the
documented `choose_adopting` rule; linkage keys on the number, so one of the two rows is
necessarily wrong — a standing limitation, not a new one. (c) **2022-O-18** links correctly
but is held at `low`: its motion text contains "**Table** 17-7-1.2" (a zoning table), which
trips the `NONADOPT` table/deny/continue guard. Honest under-confidence, left as found.

## ⚠ Mis-dated duplicate meetings in the vote layer (found 2026-07-29, NOT fixed here)

Chasing 2023-O-01 surfaced a defect in `../meeting_minutes/`, not in this dataset: Revize
minutes filenames of the form `M DD YY` are being read as `MM D YY`, so some meetings are
indexed under a **wrong date** — and the PMN backfill later promoted the SAME meeting again
under its correct date, leaving duplicates:

| indexed (wrong) | true meeting | evidence |
|---|---|---|
| 2023-11-07 | **2023-01-17** | `CC Minutes 11723001.pdf`; the doc's own header reads "JANUARY 17, 2023"; identical motions 1-4 exist under 2023-01-17 (`pmn_minutes`) |
| 2020-12-01 | **2020-01-21** | identical motions 2-4 exist under 2020-01-21 (`pmn_minutes`) |
| 2022-11-08 | **2022-01-18** | identical "Ordinance No. 2022-0- 03 … Electronic Meetings" motion |

Note the repo currently records **2023-01-17 council minutes as recovered-via-PMN** while
also holding the same meeting as an audited Revize doc dated 2023-11-07. Fixing this means
re-dating documents + `minutes_index.csv` + `all_votes.csv` rows and dropping duplicates —
it CHANGES motion/vote counts, so it was deliberately left alone here and logged instead.

- **`high`** (107) — the ordinance number is cited in a **passing adopting** council motion
  (adopt/approve/enact, not table/deny/continue). The signed PDF independently corroborates
  the motion → the strongest tier. All 107 audited: the matched motion genuinely cites the
  number (0 false).
- **`medium`** (2) — number not cited, but a same-date adopting motion's subject clearly
  matches (keyword overlap ≥2, unambiguous). The matcher **skips** any motion citing a
  *different* ordinance number (so an O-12 document can't steal the O-11 motion on a shared
  day).
- **`low`** (8) — date-only (adoption date parsed from the PDF matches a meeting date but no
  unique subject match), OR a signed ordinance whose only citing motion is a
  table/deny/continue action (adoption motion not separately identifiable — see
  `linkage_note`).
- **`none`** (144) — no adopting motion found. **119 are pre-2020 back-catalog** (no minutes
  exist before the 2020 data floor — linkage is structurally impossible, not a miss). The
  other 25 are 2020+ ordinances adopted on a consent agenda whose motion never prints the
  number AND whose OCR'd adoption clause didn't parse. Match fields left empty; never forced.
- **`within_source`** (2) — 2023-O-12, 2023-O-13: a council motion adopted the number but the
  city posts **no signed PDF**; the row is derived ONLY from the motion (`format=na`,
  `path` blank, `source_url` = the minutes doc) — high *by construction*, NOT an independent
  cross-match. Resolutions (R) with no PDF are **out of scope** (ordinances only).

**Six-member council:** 5 districts + a Mayor who votes only to break a tie (max ordinary
roll 5). The linkage never assumes the mayor is a routine voter. `choose_adopting()` excludes
table/deny/continue/repeal/reconsider motions and picks the earliest genuine adoption.

## Dates (`adoption_date` / `date` / `adoption_date_source`)

- **`adoption_date`** (authoritative; 155 rows populated) — parsed from the signed PDF's
  "PASSED AND APPROVED this Nth day of Month, YYYY" clause (`pdf`, 90; OCR-junk-tolerant
  between the day digits and "day of"), or the month+year read + resolved to the unique
  council meeting that month (`pdf-monthyear+calendar`, 1), or the linked motion's date
  (`minutes-motion`, 64). **Blank when genuinely unknown** — never inferred.
- **`date`** (§9 index date, always populated) — the adoption date when known; otherwise a
  **`year-only`** placeholder `YYYY-01-01` (106 rows). The YEAR is certain (it's in the
  ordinance number); the **month/day are a placeholder and `adoption_date` stays BLANK**.
  Most year-only rows are pre-2020 back-catalog OR 2016–2017 signed ordinances that are
  fill-in-the-blank templates with the day/month left blank in the posted copy
  (genuinely undateable to the day — honest, not a parse failure).

## land_use

Keyword classifier over title + first ~2 KB of text (zoning/rezone, general plan,
subdivision/plat, annexation, vacation, setback/overlay, Title 17, ADU/dwelling,
mixed-use, development agreement; budget/fee/franchise/salary guard). **182 rows** flagged
(106 in 2020+). A convenience filter, not a legal category — check the document before
quoting.

## `result` (verbatim)

The matched motion's city-verbatim result string (`5-0 Pass`, `4-1 Pass`, `1-4 Fail`, …).
Blank where unmatched. Cross-city comparison goes through the minutes' `motions_std.csv`.

## Regeneration

```
python3 build_index.py          # index.csv + unrecovered.csv (no network)
```
Re-harvesting the portal (new adoptions): re-fetch the two Recorder pages to the scratchpad,
rerun `mv_harvest_links.py <scratchpad>` → fetch new `_fetch_batch.txt` rows into `raw/` via
`scripts/polite_fetch.py`, `python3 extract_text.py`, then `build_index.py`. The `text/`
sidecars feed `cities.db` `fts_ordinance` on the next `scripts/build_cities_db.py` run.
