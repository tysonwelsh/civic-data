# Housing Authority (Housing Connect / HACSL) — how to answer questions here

Sub-body of `salt_lake_county/agencies/`. The **Board of Commissioners of the Housing
Authority of the County of Salt Lake** (dba **"Housing Connect"**; legacy **HACSL/HASLC**) —
a **separately-incorporated** county public entity (NOT the County Council's Legistar, NOT the
RDA/MBA). Develops and manages affordable housing county-wide, so its record is squarely
growth/housing/development. **`SOURCES.md` is authoritative for provenance** — read it first.

## What's here

```
raw/            69 board-minutes PDFs, named <date>_<wpid>_minutes.pdf (incl. 1 image-only).
minutes/<year>/ 68 converted markdown files <date>_housing_authority.md (front-matter + pypdf
                text) — the SEARCHABLE MINUTES CORPUS. 2020-01-15 → 2025-11-19.
minutes_index.csv  date,body,md_path,source_url,minutes_status,note  (69 rows incl. the
                image-only gap row with blank md_path).
all_votes.csv   Standard 13-col vote table, body=HousingAuthority. 327 motions / 1,692 named
                member votes. See "Votes" below.
build.py        Fetch (housingconnect.org WP media API) → minutes md + index. Idempotent.
extract_votes.py Minutes prose → all_votes.csv. Idempotent.
```

## Which artifact for which question

- **What did the Housing Authority discuss / decide** (keyword, project, RAD/MTW/voucher,
  acquisition): the **minutes markdown** (`minutes/<year>/*.md`). Full text; feeds `fts_minutes`
  once federated. Start from `minutes_index.csv` to pick a meeting; open the md for context.
- **Who moved/seconded/voted on a motion**: `all_votes.csv`. One row per motion × named member.
- **What source exists / provenance / gaps**: `minutes_index.csv` (`minutes_status`,
  `source_url`) + `SOURCES.md`.

## Cardinal rules in play (repo-wide — do not break)

1. **Never fabricate.** Blank `member`/`vote` in `all_votes.csv` = **tally-only motion** (the
   minutes stated the outcome without re-listing names, 27 motions) — not a missing vote. The
   `2021-12-15` index row with blank `md_path` + `minutes_status=image-only` = the PDF is
   scanned/unextractable, minutes exist but text doesn't — an **honest gap**, never filled.
2. **Meeting date is the in-document date, not the filename.** Some 2025 filenames carry the
   finalized/approval date; `build.py` parses the header date. Don't "correct" a date from a
   filename.
3. **`Johnston` is left surname-only on 2 vote rows on purpose** — Mark Johnston and Jennifer
   Johnston both served; the source gave no first name there. Do not guess which one.
4. Derived files are **regenerated** (rerun the two scripts), never hand-edited.

## Vote recording ceiling — **NAMED**, high-consensus

The minutes name mover, seconder, and the in-favor roster on nearly every motion (see
SOURCES.md for the exact form and caveats). It is **not** tally-only like Nephi or the County
Council's own prose. Signal to know:
- **327 / 327 motions Passed**; across six years **0 named Nay, 3 Abstain** (all in the file).
  This is a real consensus board — treat "contested" as rare-by-nature, not under-captured.
- `result` = normalized `Passed`; `motion_type` = a keyword label (not a city-native string —
  don't aggregate it across bodies as if verbatim).

## Not yet wired (honest scope boundary)

This module is **standalone flat files only**. It is **not yet** loaded into
`salt_lake_county.db` / `gov.db` / `cities.db`, `weeks/`, or the referral/roster layers, and
the parent `salt_lake_county/CLAUDE.md` still lists Housing Authority as a TODO. Federating it
(a `body`/`meeting`/`motion`/`vote` load + `fts_minutes` rows, `gov_level='county'`) is the
next step. Until then, query the flat CSVs and markdown directly.

## Rebuild

```
python3 build.py           # re-download + rebuild minutes/ + minutes_index.csv
python3 extract_votes.py   # rebuild all_votes.csv from minutes/
```
