# ordinances/ — Vineyard adopted ordinances index + linkage (as-of 2026-07-05)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on every
existing dataset; nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`,
`weeks/`, etc.

## What this is
An index of **adopted Vineyard City ordinances** (84 rows, ordinance numbers 2020-02 → 2025-16),
each mapped to the council/PC **motion** that adopted or acted on it in the vote layers, with an
honest confidence score. Emphasis is **zoning / land-use** ordinances (zone-map + zoning/subdivision
text amendments, general-plan amendments): **18 of 84 (21%)** are land-use.

## Code host + independence caveat (READ THIS)
Vineyard's codified-code host is **`https://vineyard.municipalcodeonline.com/`** (the city's
online municipal code). It carries an **"Ordinances — an index of Ordinances adopted by the
Municipality"** book, i.e. an independent adopted-ordinance archive **does exist**. BUT it is a
JavaScript single-page app: the tree/`/book/expand?type=ordinances` endpoint returns **HTTP 500**
to a plain GET (it needs a `data-databookid` set client-side), so the number→date→subject list is
**not politely GET-retrievable**. It gives current consolidated text, not a downloadable per-ordinance
history. (American Legal `codelibrary.amlegal.com` returns **403** to the fetcher; Vineyard also has a
Municode vendor client record `ClientID 17397`, but the public code host is municipalcodeonline.)

Because no online full-text ordinance archive is politely retrievable, **the backbone of this index
is reconstructed from Vineyard's own minutes**: Vineyard's minutes **do cite `Ordinance YYYY-NN`**
richly (unlike Orem; like Lehi/Logan). 84 ordinance numbers are cited in council/PC motion text in
`meeting_minutes/all_votes.csv` + `planning_commission/all_votes.csv`, carrying number + adoption
date + subject. This is therefore a **derived (within-source) index**, honestly labeled — NOT an
independent cross-match — except for the 5 ordinances independently corroborated by signed PDFs on
Utah Public Notice (see below).

## raw/
The only independently-published full ordinance texts retrievable by a polite GET were **5 signed
ordinance PDFs on the Utah Public Notice website (PMN body 530)** — ordinances **2021-07, 2021-09,
2021-10, 2021-11, 2021-12** (each a Recorder "Ordinance Passage" notice attachment). Retained
verbatim in `raw/` with `_fetch_log.jsonl` (url, status, bytes, sha256, retrieved_utc) from
`polite_fetch.py`. Extracted text (born-digital, `pdftotext -layout`) is in `text/`. All 5 are clean
under `screen_corpus.py` (0 real anomalies; `ends_mid`/`repeated_line` flags are advisory — legal
signature blocks + campaign-finance boilerplate).

## index.csv columns
Minimum provenance cols (`date`,`title`,`source_url`,`retrieved_date`,`format`,`extraction_method`)
plus source-specific cols:
- `ordinance_no` — canonical `YYYY-NN` (zero-padded; a space-tolerant matcher normalizes the minutes'
  occasional `2021- 08` spacing).
- `adoption_date` (= `date`) — the meeting date the adopting motion passed (or the PDF's "PASSED AND
  ADOPTED" date for the PMN-only row).
- `title` — subject: the PMN PDF caption for corroborated rows; otherwise the richest motion text
  citing the number.
- `source_url` — the PMN PDF URL for the 5 corroborated rows; otherwise the repo-relative **minutes
  file** that recorded the adoption (Vineyard publishes no per-ordinance URL).
- `format` — `text` for all (born-digital minutes / born-digital PDFs; nothing scanned).
- `extraction_method` — `pdftotext -layout (…PDF)` for PMN rows; `reconstructed from … motion text`
  otherwise.
- `path` — the `raw/` PDF for the 5 PMN rows; empty for minutes-derived rows.
- `land_use` — classification (regex on subject; `yes` for zone change / zoning
  or subdivision text amendment / general-plan amendment / plat / annexation / development agreement).
- `result` — the chosen motion's verbatim result string.
- `matched_motion_date`, `matched_motion_no`, `match_confidence` — the linkage.
- `land_use_category` — classification (regex on subject; see `land_use`).
- `n_motion_events` — how many distinct (date, motion_no) motions cite the number (0 = PMN-only).
- `linkage_note` — multi-date ambiguity, corroboration, or "not confirmed adopted" flags.
- `minutes_source` — the repo minutes markdown recording the adopting vote (the join target).

## Linkage method + confidence
Join = adoption date + ordinance number cited in the motion text (the skill's rule).
- **high (5)** — `2021-07, 2021-09, 2021-10, 2021-11, 2021-12`: the number appears BOTH in an
  independent signed ordinance PDF on Utah Public Notice AND in a passing council motion. Genuine
  cross-source. (`2021-12` joined this tier 2026-07-19 — see the source-typo note below.)
- **within_source (79)** — the number is cited in council/PC motion text only, with no independent
  archive retrieved. The number/date/subject are present **by construction** (the index is derived
  *from* the motions), so this is a strong within-source join, NOT independent corroboration — hence
  the distinct `within_source` value so it is never misread as cross-checked. `medium`/`low`/`fuzzy`
  are not used: every within-source row cites its number exactly.
- **none (0)** — the dataset's former lone audit signal (`2021-12`) is **RESOLVED** as of 2026-07-19.

### 2021-12 source-typo resolution (2026-07-19)
`2021-12` (Committees & Commissions, Chapter 2.30) is a genuinely **adopted** ordinance (signed PDF,
"PASSED AND ADOPTED … SEPTEMBER 08, 2021"). It was originally scored `none` on the theory that the
2021-09-08 council meeting had no motion restating the number. That theory was **wrong**: the
2021-09-08 minutes DO record the adopting motion at business item **9.3** — whose agenda header reads
"(Ordinance 2021-12)" — but the clerk **mistyped the number in the motion sentence** as
"APPROVE ORDINANCE **2021-02**". The vote was therefore never missing from `all_votes.csv`
(2021-09-08 #4, "Carried unanimously": Fullmer, Earnest, Flake, Judd, Welsh all Aye); it was
mis-numbered at the source, which also caused the reconstructor to falsely attach 2021-09-08 #4 to
the **real, distinct** Ord 2021-02 (2021-02-10 item 9.1, ZTA 15.34.100 Parking). A documented
`MOTION_ORD_OVERRIDE` in `build_index.py` re-keys that one motion event to `2021-12` **for linkage
only** — the verbatim `all_votes.csv` motion text is untouched (cardinal rule 2). Net effect:
`2021-12` → `high` matched to 2021-09-08 #4; `2021-02` → its correct sole match 2021-02-10 #4.

To go from an ordinance to its full vote: read `minutes_source`, or filter the vote CSV on
`matched_motion_date` + `matched_motion_no`.

## Known limitations
- **This is a floor, not a census.** 33 further `YYYY-NN` numbers appear in the minutes *prose*
  (agenda/staff references) but are cited by **no** passing motion, so they are not indexed
  (adopting motion didn't restate the number, or the reference was to a staff report). See
  AVAILABILITY.md.
- **Data floor = 2020** (Vineyard's minutes floor). Ordinances adopted 2014–2019 (the town-to-city
  years) are not covered — no minutes and no politely-retrievable independent list.
- A handful of within-source rows are cited only in a non-adopting motion (e.g. `2022-16`, a PC
  negative recommendation) — flagged "NOT confirmed adopted" in `linkage_note`; spot-check before
  quoting as adopted.
- 18 rows cite the number on >1 date (continued item / PC-rec + council-adoption pairs) — the last
  passing council motion is chosen; alternates are listed in `linkage_note`.

Rebuild: re-run the Source-3 builder against the two `all_votes.csv` vote layers plus any newly
downloaded PMN signed-ordinance PDFs.
