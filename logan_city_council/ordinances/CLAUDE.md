# Logan `ordinances/` — adopted ordinances & resolutions (2020–2026)

Additive dataset (built by `expand-city-sources`). Do not hand-edit `index.csv` values that
come from source; regenerate. Start with `AVAILABILITY.md` for coverage & audit signals.

## Source / code host

- **Adopting-ordinance archive (the source used):** Logan **City Recorder** document-center
  pages on the Revize CMS —
  `https://www.loganutah.gov/government/mayor_s_office/city_recorder/ordinances.php` and
  `.../resolutions.php`. Each lists signed adopting PDFs whose **filename carries the
  ordinance/resolution number and subject** (e.g. `26-01 Future Bookshop Rezone 404 Park
  Avenue.pdf`). Files serve from the Revize CDN via `www.loganutah.gov/departments/admin/…`.
  This is an **independent, number-bearing** record, separate from the meeting minutes.
- **Codified code (NOT used as a source):** the current consolidated **Land Development Code
  / Municipal Code** is hosted on **American Legal Publishing**
  (`codelibrary.amlegal.com/codes/loganut`). It gives *current text only* — no point-in-time
  adopting ordinances — so it cannot support adoption dating/linkage. Municode
  (`library.municode.com/ut/logan`) is only a SPA shell. No ordinance API exists (Revize).
- Note Logan's code naming: **LDC = Land Development Code** (the zoning/land-use code;
  "LDC Amendments…" are land-use). **LMC = Logan Municipal Code** (general — alcohol, noise,
  parking, camping; usually NOT land-use). The `land_use` classifier keys on this.

## Linkage method + independence caveat

`index.csv` unions two record sets, keyed on `(kind, ordinance_no)`:

1. **Recorder archive** (`origin=archive`, 485 rows) — every adopted/assigned number 2020–26.
2. **Council motions** — numbers extracted from `../meeting_minutes/all_votes.csv` motion
   text via `\b(Ordinance|Resolution)\s*(?:No\.?\s*)?(\d{2}-\d{1,3})\b`.

`match_confidence`:

- **`high`** (461) — the number appears in **both** the independent Recorder PDF **and** a
  council motion. Two independent sources agree; `matched_motion_date/_no` point to the
  adopting motion (the highest-scoring "adopt/carried/passed" motion for that number).
- **`within_source`** (11) — number cited in a council motion but **absent from the Recorder
  archive**. This is **minutes-derived only**: high *within the minutes by construction*, but
  **NOT independently corroborated**. `origin=votes`, `path` empty, `source_url` = the
  minutes file.
- **`none`** (24) — in the Recorder archive but **no council motion cites the number**
  (`audit_flag=adopted_no_vote_row`). Match fields empty — never forced. Some are genuinely
  adopted land-use ordinances missing from the vote layer (a vote-extraction audit lead);
  some are denied/withdrawn items the archive still numbered; some are post-minutes-floor
  FY26-27 budget items. See AVAILABILITY.md.

**Caveat:** `high` here means *two independent records carry the same literal number*. It
does **not** verify that the PDF's text and the motion describe the same substance beyond the
number — though the archive filename subject and motion context agree on every land-use row
spot-checked. No fuzzy (date/subject) matching was used or needed; Logan numbers both sources
explicitly, so linkage is exact-number or nothing.

## `date` / `adoption_date`

- `adoption_date` = council adoption date, taken from the matched motion (`date_basis=
  council_motion`) — populated for the 472 matched rows.
- For the 24 un-voted rows `adoption_date` is **empty** (signed PDFs carry handwritten/scanned
  dates; body-text date parsing was unreliable and dropped). Their `date` falls back to the
  Recorder's document-post timestamp (`t=` in the CDN URL, `date_basis=recorder_posted`) — a
  sourced document date, explicitly not a verified adoption date.

## Columns (`index.csv`)

Contract (§9): `ordinance_no, adoption_date, date, title, source_url, retrieved_date, format,
extraction_method, path, land_use, result, matched_motion_date, matched_motion_no,
match_confidence`. City extras: `kind, date_basis, lu_basis, n_motions, origin, audit_flag`. `format` ∈ text/scanned/na (`na` = PDF exists at `source_url` but not
retrieved to `raw/` — the non-land-use bulk). `land_use` from a keyword+address classifier
(`lu_basis` = keyword / address / motion_text); it is best-effort and inclusive for
zoning/annex/subdivision/vacation/LDC/overlay/plan items.

## Regenerate / refresh

Re-fetch the two Recorder listing pages, re-parse `<a … .pdf>` links (number = leading
`\d{2}-\d{1,3}`; strip an OCR-bled trailing capital that runs into a lowercase subject word,
e.g. `25-15Honey` → `25-15`), filter to years 20–26, download land-use PDFs via
`polite_fetch.py` (browser UA, ≥1s, GET-only), then re-run the number↔motion match. Keep raw
bytes verbatim; log every fetch to `raw/_fetch_log.jsonl`.
