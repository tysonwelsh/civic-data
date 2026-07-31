# Logan ordinances/resolutions — availability & coverage

*As-of 2026-07-05. Additive dataset; regenerate stats from `index.csv`.*

## What this is

An index of **adopted City ordinances and resolutions, 2020–2026**, built from Logan's
**independent City Recorder archive** (the Recorder's `ordinances.php` / `resolutions.php`
document-center pages on loganutah.gov, files served from the Revize CDN), cross-linked to
the council vote layer (`../meeting_minutes/all_votes.csv`). Land-use / zoning ordinances
are the focus: their signed adopting PDFs are retained verbatim in `raw/`.

The Recorder archive is a **genuinely independent, number-bearing source** (not derived
from the minutes), so a number that appears in BOTH the archive and a council motion is
corroborated on two independent records. See `CLAUDE.md` for the linkage method and its
independence caveat.

## Counts

| Metric | Count |
|---|---|
| Total index rows (ordinances + resolutions) | **496** |
| Ordinances | 167 |
| Resolutions | 329 |
| **Land-use / zoning items** (`land_use=yes`) | **143** (122 ord + 21 res) |
| Raw signed PDFs retained in `raw/` | **162** (143 land-use + 19 un-voted for dating) |
| Date range (`date`) | 2020-01-21 → 2026-07-01 |

### Confidence tiers (`match_confidence`)

| Tier | Rows | Meaning |
|---|---|---|
| **high** | 461 | Independent Recorder PDF **and** a council motion cite the same number — two-source agreement. |
| **within_source** | 11 | Number cited in a council motion, but **no PDF in the Recorder archive** (minutes-derived only; not independently corroborated). |
| **none** | 24 | In the Recorder archive but **no matching council vote row** — audit signal (see below). Match fields left empty. |

There are **no `medium`/`low` rows**: Logan's linkage is either an exact number match on
two sources (`high`), an exact number match on one source (`within_source`), or unmatched
(`none`). Fuzzy date/subject matching was not needed because both sources carry the literal
ordinance/resolution number.

## Land-use raw corpus quality

Of the 143 land-use PDFs retained: **55 born-digital text**, **88 scanned (image-only,
`format=scanned`)**. The scanned share is high because older signed ordinances were
filmed/scanned for the archive. Raw bytes are kept verbatim; no OCR text corpus is
published (so no extracted-text screening applies), and signature dates on the scans are
handwritten — this is why an independent `adoption_date` is not asserted for un-voted items
(see below).

## Audit signals — adopted/listed items with NO council vote row (24)

`audit_flag=adopted_no_vote_row`. These carry an ordinance/resolution number in the
Recorder archive but no motion in `all_votes.csv` cites that number. Breakdown:

- **Genuinely adopted land-use ordinances missing from the vote layer** (flag for a
  vote-extraction audit): **Ord 22-13** LDC Amendment Annexations (2022), **Ord 23-15**
  Tempki Subdivision Easement (2023), **Ord 26-12** Data-Center Moratorium (2026, may
  post-date the 2026-06-02 minutes floor). None of these appear in `all_votes.csv` by
  number *or* subject.
- **Not actually adopted** (archive lists the assigned number anyway): **Ord 24-01** Little
  Bloomsbury Rezone — *DENIED*; **Ord 21-06** 1200 W 1400 N Rezone — *WITHDREW*. A denied/
  withdrawn item has no adopting motion by design.
- **Non-land-use** (salary schedules, budget adjustments, tax-rate & tentative-budget
  resolutions): 18 rows, several of them FY2026-2027 items (**Res 26-16/17/18/21/23**)
  adopted in mid-June 2026, **after the current minutes floor (2026-06-02)** — an honest
  timing gap, not missing data.

For these 24 rows `adoption_date` is intentionally **empty** (no reliable source: signed
PDFs carry handwritten/scanned dates, and body-text date parsing proved unreliable). Their
`date` falls back to the Recorder's document-post timestamp (`date_basis=recorder_posted`),
a sourced document date — not a verified adoption date.

## Gaps & scope boundaries

- **Window:** 2020–2026 only. The Recorder archive reaches back to 1866/2000; earlier
  numbers were not indexed here.
- **11 `within_source` numbers** (e.g. Ord 20-25, 20-26, 23-33, 24-14, 24-20; Res 20-45,
  21-51, 23-44, 26-02) are cited in council motions but have **no PDF** on the Recorder
  pages as of the retrieval date — indexed for completeness, `path` empty, not
  independently corroborated. Res 26-02 is recent (Feb 2026); the archive may simply lag.
- **Codified code** (current text of Logan's Land Development Code / Municipal Code) lives
  on **American Legal Publishing** (`codelibrary.amlegal.com/codes/loganut`), which serves
  *current* consolidated text only — not the point-in-time adopting ordinances this dataset
  needs. Municode (`library.municode.com/ut/logan`) returns only a SPA shell. Neither was
  used as a source; the Recorder's per-ordinance PDF archive is authoritative for adopted
  instruments.
- **No ordinance API** (Revize CMS); all discovery was via the two Recorder listing pages.

## Provenance

Every raw fetch is logged in `raw/_fetch_log.jsonl` (url, status, sha256, bytes,
content_type, retrieved_utc) — all 162 fetches returned HTTP 200. Fetched GET-only through
`scripts/.../polite_fetch.py` with a browser UA and ≥1s throttle.
