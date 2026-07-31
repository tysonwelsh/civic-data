# ordinances/ — West Valley City adopted ordinances (zoning/land-use)

Additive, read-only cross-reference dataset. **Never edit `../meeting_minutes/all_votes.csv`
from here** — this layer points *at* the vote record, it does not change it. Regenerating is
not automated; `index.csv` was built from the CivicPlus Archive Center signed PDFs (`raw/`)
plus the minutes/votes. See `AVAILABILITY.md` for coverage, counts, and gaps.

## Files
- `raw/` — 106 signed ordinance PDFs from the city Archive Center (2024–2026 modules), named
  `Ord-YY-NN-ADID<n>.pdf`. Authoritative `Date Adopted:` + full title live inside each PDF.
  `raw/_fetch_log.jsonl` is the machine-readable fetch provenance (url, sha256, bytes, status).
- `index.csv` — one row per distinct adopted ordinance number (329 rows, 2019 straggler +
  2020–2026; 26-26..30 backfilled 2026-07-19).

## index.csv columns
Required six: `date` (= adoption date), `title`, `source_url`, `retrieved_date`, `format`
(`text` for archived PDFs, `na` for minutes-derived rows), `extraction_method`
(`pdf-pdftotext` | `minutes-derived` | `minutes-derived-consent`). Plus:
- `ordinance_no` — `YY-NN` (verbatim city numbering).
- `adoption_date` — PDF `Date Adopted:` where a signed PDF exists, else the council vote date.
- `path` — repo-relative path to the signed PDF in `raw/` (empty for minutes-derived rows).
- `land_use` — 1 if a zoning/land-use ordinance (rezone, general-plan, subdivision/plat,
  street vacation, PUD, zone-text, land-use code title), else 0. 254 of 324 are land-use.
- `result` — (§9 contract column; blank where not recorded)
- `matched_motion_date`, `matched_motion_no` — the adopting Council motion in
  `../meeting_minutes/all_votes.csv` (join on `date`+`motion_no`). Empty when unmatched.
- `match_confidence` — see below.
- `case_no` — WVC land-use case number (`GPZ-`/`Z-`/`PUD-`/`SMI-` …) where present (164 rows).
  This is the join key into the repo's case-number referral layer (`db/`).

## Confidence honesty
- `high` — ordinance number appears in **both** an independent signed city PDF **and** a
  council motion. Quote freely. (97 rows)
- `within_source` — number is in a council **motion only**; no independent PDF exists for that
  year (chiefly 2020–2023, plus un-archived later ords). Trustworthy as a vote record but
  **not independently corroborated**. (223 rows) — NB this tier also carries 30+ ordinance
  numbers whose only motion was a *motion to deny* (e.g. 26-26/26-27); the index is an
  ordinance-number↔motion cross-reference, so **disposition (approve/deny/pass/fail) lives in
  the linked `all_votes.csv` motion, not here** — never read a `within_source` row as proof of
  adoption without checking its motion.
- `none` — an independent signed PDF exists but **no motion cites the number** → adopted
  ordinance missing from `all_votes.csv` (consent-bundle adoptions, or motions citing the
  application number); match fields left **empty, never forced**. Audit signal — see
  `AVAILABILITY.md`. (9 rows)
- (`medium`/`low` tiers are defined by the skill but did not occur here — matching is on
  exact verbatim ordinance number, so a match is either exact or absent.)

## Cardinal rules honored
Never fabricated a match; empty match fields mean genuinely unmatched. Raw PDFs retained.
City-faithful `result`/`motion_type` untouched (they stay in `all_votes.csv`).
Misattributed consent-calendar subjects were blanked, not guessed.
