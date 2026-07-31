# nephi_city_council/ordinances/ — adopted ordinances index

Additive dataset: **adopted zoning / land-use (and other) ordinances of the Nephi City
Council, 2020–2026**, linked to the vote layer. Built by `expand-city-sources`
(Source 3). Coverage, gaps, and confidence tiers are in **`AVAILABILITY.md`** — read it first.

```
index.csv        103 ordinance numbers (2020–2026), one row each, linked to all_votes.csv
raw/             6 PMN ordinance PDFs (+ _fetch_log.jsonl provenance); 5 corroborate index,
                 1 (1253943.pdf) is a North Salt Lake reference doc — retained, NOT indexed
text/            extracted text of the 5 corroborating PMN PDFs (screened, clean)
build_index.py   regenerates index.csv from meeting_minutes/ (idempotent; DERIVED — never hand-edit)
```

## The number = the date (Nephi's numbering)
Nephi ordinance numbers **are the adoption date**: `Ordinance MM-DD-YYYY`, uppercase
suffix (`-A`…`-Z`) for multiple ordinances the same meeting. So `ordinance_no`,
`adoption_date`, and `date` are all the same date, and `matched_motion_date` equals it for
a clean match. (Unlike Lehi/Logan `YYYY-NN`; unlike Orem which prints no numbers.)

## How the index was built (linkage method)
1. Scan every `meeting_minutes/minutes/**/*.md` (+ `all_votes.csv` motion text) for the
   `Ordinance MM-DD-YYYY[-X]` pattern → the set of ordinance numbers Nephi assigned.
2. For each number, take the **subject** from the minutes section header and link it to the
   **adopting council motion** on that date in `all_votes.csv` (`matched_motion_no`),
   assigning same-day suffix siblings uniquely (exact-number carry → distinctive-keyword →
   positional; a motion is eligible only if it is an *ordinance*-adoption motion, never a
   plat/CUP/consent-agenda row).
   ⚠ **REPAIRED 2026-07-29** — that eligibility rule was documented but **not applied in
   pass 1** (exact-number carry), which scanned every motion on the date. Because a Nephi
   ordinance number IS a date, the consent-agenda row ("…claims dated 9-2-2025", "…Claims
   dated 1-20- 2026") carries the digits of an ordinance number without enacting anything,
   and it out-ran the real motion simply by coming first. 9 rows moved: **09-02-2025**
   (consent agenda → #2 "adopt Ordinance 09-02-0205 – Nuisance Code Update", the source's
   own year typo) and **01-20-2026** (consent agenda → #3 Jacobson Annexation) were the
   flagged pair; the other 7 had been pointing at a same-day **Resolution** motion of the
   same number (Nephi numbers ordinances AND resolutions by date) and now point at the
   Ordinance motion. **07-02-2024-A dropped to `none`** — its old link was the 07-02-2024-A
   *fireworks resolution*; the base number claims the only ordinance motion that day, so the
   suffixed ordinance has no discrete vote row. An honest gap, per cardinal rule 1.
3. Corroborate against the 5 independent **PMN Notice-of-Ordinance PDFs** in `raw/`.

## Independence caveat — read before trusting `match_confidence`
Because the number **is** the meeting date, a number recovered from the minutes is **not
independent** of the council vote — both live in the same minutes document. Therefore:
- `high` (5 rows) = the number is **also** in an independent **PMN signed-ordinance PDF**
  *and* a council motion — the only genuinely corroborated tier.
- `within_source` (91) = number + motion both from the **minutes only**; internally
  consistent but **not** independently verified. 9 of these are same-day siblings linked
  **positionally** (suffix truncated in the source `all_votes.csv`) — flagged in
  `extraction_method`; do not quote their exact `matched_motion_no` as certain.
- `none` (7, down from 11 at the 2026-07-20 extractor recovery) = genuinely adopted (per
  minutes) but **no discrete vote row** exists, or the number's date is not a meeting date.
  Match fields are **empty** — an **audit signal**, not a defect to fill. See `AVAILABILITY.md`
  for the list + the 2026-07-20 resolution of the 4 flagged land-use rows (2 recovered/linked,
  2 honest gaps).

## Columns
`ordinance_no, adoption_date, date, title, source_url, retrieved_date, format,
extraction_method, path, land_use, result, matched_motion_date, matched_motion_no,
match_confidence, land_use_type, status, minutes_files`.
- `format` ∈ text / scanned / na (one PMN PDF, `02-07-2023-A`, was scanned → OCR'd).
- `land_use` yes/no; `land_use_type` ∈ zone_change / land_use_code / subdivision /
  annexation / short_term_rental / adu / overlay / street_vacation / general_plan / plat / parking.
- `result` / `status` are city-faithful (`result` = the vote tally string from `all_votes.csv`;
  `status` = ADOPTED/APPROVED/TABLED/FAILED etc. from the minutes header). **4 rows are
  non-adopted** (1 FAILED, 3 TABLED) — exclude them when counting *adopted* ordinances.
- `path` is dataset-relative and points into `raw/` for the 5 `high` rows only.

## Analysis notes
- Cross-check a rezone/annexation/subdivision timeline: join `index.csv.matched_motion_no`
  + `matched_motion_date` → `meeting_minutes/all_votes.csv` (and `db/civic.db`).
- Nephi's ordinance stream is **land-use-heavy** (69 of 99 adopted): near-every rezone,
  annexation, plat and Title 10/11 amendment gets its own dated ordinance.
- Regenerate: `python3 ordinances/build_index.py` (idempotent; reads minutes + all_votes).
