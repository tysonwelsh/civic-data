# ordinances/ — Draper adopted ordinances (build notes)

Additive dataset (`expand-city-sources` Source 3), built **2026-07-13**. Maps adopted
**Ordinance #NNNN → adoption date → subject → the council motion that passed it**, so a
vote in `../meeting_minutes/all_votes.csv` links to what the ordinance did. **276
distinct ordinances, #1344 (2018) → #1726 (2026-07-07); 272 in the 2020+ window, 168
land-use.** Draper numbers ordinances **sequentially across years** (no YYYY-NN form).
Regenerate: `python3 extract_text.py && python3 build_index.py` (offline, idempotent).

## Two sources, two evidence roles

1. **PMN Recorder adoption notices** (independent witness; **1-page adoption-summary
   PDFs, NOT full ordinance text**) — PMN entity **114**, City Council body **5555**
   (not the "City Recorder" body 9205 — that one holds only election notices). 219
   adoption notices (+7 hearing notices, catalogued but excluded) in
   `raw/pmn/notice_<id>.html`; 202 attachment PDFs `raw/pmn/ord<num>_n<nid>_f<fid>.pdf`
   (195 born-digital → `pdftotext -layout`; 7 scanned → tesseract OCR @300dpi, labeled
   in `text/_extraction_log.csv`). **Notice posting resumed regularly only in May 2021**
   — calendar 2020 has ZERO adoption notices.
2. **Council minutes backbone** (`../meeting_minutes/all_votes.csv`, READ-ONLY) —
   motions cite numbers richly, singular and plural ("Ordinances #1709, #1710, and
   #1711"). Motion classification uses the **operative verb after "moved/motioned to"**
   — naive keyword matching false-positives on subjects like "Use **Tables** Text
   Amendment" and "Notice of **Continued** Item".

## Linkage rubric (`match_confidence`)

- **high** (182) — notice exists AND a council motion cites the number AND the dates
  agree (incl. 7 POSTED_DATE_RULE rows where the notice printed its own Wednesday
  posting date; the citing Tuesday motion fixes the date — both dates in `linkage_note`).
- **medium** (2) — independent doc + agreement but imperfect number linkage: **#1520**
  (motion printed the erroneous #1514 the Recorder later corrected) and **#1625** (the
  notice/attachment body was mis-copied from the #1624 notice; headline + the
  2024-10-15 3-2 tie-break motion establish it).
- **low** (18) — minutes exist for the stated adoption date but no extracted motion
  cites the number (consent/unattributed item); `matched_motion_date` set,
  `matched_motion_no` blank.
- **within_source** (69) — witnessed ONLY by the citing council motion (no PMN notice;
  concentrated 2020→mid-2021, the no-notice era). High by construction, **NOT
  independently corroborated**. `source_url` = the minutes markdown; `path` blank,
  `format=na`.
- **none** (5) — notice-backed, no matching motion: 4 pre-2020 rows (below the vote
  floor) + **#1726** (2026-07-07 recap-only meeting, minutes pending). **Never
  forced.** *(#1494/#1496/#1497 moved none→high 2026-07-16 when the PMN-recovered
  2021-07-20 minutes were promoted — their enacting motions (m3/m4/m5, each 5-0
  Pass) now match on number + date.)*

Adopting-motion selection: the FINAL passing approve/adopt-verb motion citing the
number (continuations and the double-moved #1438 resolve to the last); deny-verb
citations never create rows (**20 denied proposals** listed in `unrecovered.csv`).

## Documented city-error overrides (sources verbatim; tables in build_index.py)

- `NOTICE_NUM_OVERRIDES` — 723375 (#1514 "erroneously numbered" → **#1520**; a REAL
  #1514 exists, adopted 2021-11-16); 947383 (body says #1624/Sept 17, headline +
  attachment + motion say **#1625**, 2024-10-15).
- `CITE_REMAPS` — the minutes' 2021-12-14 m5 "approve Ordinance 1514" enacted what the
  Recorder renumbered #1520 (without the remap 1514 double-counts).
- `ATTACHMENT_MISMATCH` — notices 785825 (#1556) and 1007201 (#1661) carry the WRONG
  PDF (byte-identical to the sibling notice's); rows use the notice HTML, wrong raws
  retained. Local filenames `ord1520_n723375…`/`ord1625_n947383…` were renamed to the
  corrected numbers (our naming, not source content; `_fetch_log.jsonl` keeps the
  fetch-time names).

## Schema

`index.csv` — SCHEMA_SPEC §9 ordinances contract header
(`ordinance_no,adoption_date,date,title,source_url,retrieved_date,format,
extraction_method,path,land_use,result,matched_motion_date,matched_motion_no,
match_confidence`) + extras `pmn_notice_id,pmn_notice_url,adoption_date_source,
linkage_note`. `date` = `adoption_date`. `format` ∈ `text` (born-digital PDF, 182) /
`scanned` (OCR, 7) / `html` (notice-HTML-witnessed, 18: 16 attachment-less + 2
mismatched-attachment) / `na` (within_source, 69). `result` is the matched motion's
verbatim result string. `adoption_date_source` ∈ `pmn-notice` / `pmn-notice+posted-year`
(year inferred from the posting date on year-less 2021–22 notices) / `motion` /
`motion (notice stated posting date)`. `land_use` is a keyword classifier over
title+notice-body+motion with a non-land-use guard — a convenience filter, not a legal
category.

## Codified-code host (recorded, NOT mirrored)

**American Legal** — `https://codelibrary.amlegal.com/codes/draperut/latest/overview`
(the city's "City Code" link). 403 bot-protected, current-consolidated-text only — use
manually. Full signed ordinances are "on file at the City Recorder"; the city's Tyler
Content Manager portal (`drapercityut.contentmanager.tylerapp.com/tylercm/web/`) has a
Document Search but **no anonymous GET API** (JS/POST — manual-browser lead only).

## Files

```
raw/pmn/notice_<id>.html         226 PMN notices verbatim (+ _fetch_log.jsonl)
raw/pmn/ord<num>_n<nid>_f<fid>.pdf  202 attachment PDFs (38 MB; 1 of 203 purged on PMN)
text/<stem>.txt                  222 sidecars (195 pdftotext / 7 tesseract / 20 html-strip)
text/_extraction_log.csv         per-stem format + extraction_method (build input)
pmn_notices.csv                  the crawl catalog (226 notices, kind=adoption/hearing)
index.csv                        the §9 contract index (276 rows)
unrecovered.csv                  44 rows: 22 series holes + 2 cited-only + 20 denied
extract_text.py                  sidecar extractor (OCR-aware, idempotent)
build_index.py                   index builder (offline, idempotent)
```

## Caveats

- **The PDFs are adoption-SUMMARY notices, not ordinance texts** (a few multi-page
  scans excepted) — `fts_ordinance` search hits Draper's subjects/summaries, not full
  body text. Full text requires the Recorder/AmLegal (see above).
- **within_source ≠ corroborated** (69 rows); the 2020 PMN silence means most 2020
  ordinances have no independent witness.
- **Mayor is NON-voting** (max roll 5); the single mayoral tie-break in the corpus is
  this dataset's **#1625** (3-2 Pass, 2024-10-15) — consistent with the city CLAUDE.md.
- Duplicate notices (13 ordinances noticed twice) are single rows; secondary notice
  ids in `linkage_note`.
- Ground-truth spot-check 2026-07-13: #1495, #1536, #1707 — notice PDF, stated date,
  and motion agree on number/date/subject exactly.
