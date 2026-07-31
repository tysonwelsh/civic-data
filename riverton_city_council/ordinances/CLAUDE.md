# ordinances/ — Riverton adopted zoning/land-use ordinances

Additive dataset (`expand-city-sources` Source 3), built 2026-07-13. Maps each adopted
**Ordinance No. YY-NN → adoption date → subject → the council motion that passed it**, so a
vote in `../meeting_minutes/all_votes.csv` links to what the ordinance actually did.
**155 ordinances** (2020 floor → 2026-06; 111 land-use). Regenerate:
`python3 build_index.py` (idempotent).

## Code host (NOT mirrored)

Riverton's codified municipal code is on **Code Publishing → eCode360**
(`https://www.codepublishing.com/UT/Riverton`, book `RI4763`). That is
current-consolidated text only (no per-ordinance adopted PDFs) and the eCode360 dashboard
403s to a bot UA — so it is **recorded here but deliberately not mirrored**. The
adopted-ordinance record comes from the two witnesses below.

## Two witnesses, two confidence semantics (READ THIS)

1. **Council minutes backbone (primary).** Every council motion in `all_votes.csv` that
   cites an `Ordinance No. YY-NN` (regex tolerant of `No.`/`Number`/`#`/no-space) yields a
   number → adoption-date → subject → motion row **derived from the motion itself**. These
   are **`within_source`** — high *by construction*, **NOT an independent cross-match** (the
   minutes are the only witness). Their `source_url` points at the minutes doc (the
   within-source pointer); `path` is blank, `format=na` (no separate PDF on disk).
2. **Utah Public Notice signed-adoption PDFs (independent corroboration).** The Riverton
   **City Council** PMN body (**id 889**, entity 251) posts the Recorder-certified signed
   ordinance as a born-digital "NOTICE OF ADOPTION" PDF (enumerated in
   `pmn_adoption_notices.csv`; stored `raw/<num>.pdf` + a `text/<num>.txt` sidecar that
   feeds `cities.db` `fts_ordinance`). A motion-cited number that ALSO has a PMN PDF is
   upgraded to **`high`**, and its `adoption_date` is taken from the signed PDF's
   "PASSED AND ADOPTED … this Nth day of Month YYYY" (authoritative over the motion date).

A PMN PDF whose number is **not** cited in any motion is left **`none`** (unmatched — date
source-verified from the PDF, `matched_motion_date` blank) unless a same-date subject-
matching motion exists. **Never force a match.**

## Counts (as-of 2026-07-13)

- **155 ordinances**: `high` 58 · `within_source` 93 · `none` 4.
- **Land-use: 111** (`land_use=yes`): keyword classifier over the motion + PDF title, keyed
  on **Title 18** (the zoning code — the regex tolerates OCR spacing/punctuation like
  `18. 195`, `18.(20,25`, `18(65`), rezones, general-plan-map amendments, plats/subdivisions,
  right-of-way vacations, accessory structures, with a non-land-use guard for
  budget/fee/compensation/franchise/police-chief/city-seal/appointment items.
- **62 independent PDFs** (all born-digital `text`; PMN posting starts 2023 → 4·2023,
  23·2024, 22·2025, 13·2026). The 93 `within_source` rows are 2020–2022-heavy (pre-PMN) +
  the CRA-plan and amend/repeal cases.

## The 4 `none` (unmatched) rows — dates source-verified, not motion-linked

Real adopted ordinances whose number no motion cites (all adopted on a consent agenda);
adoption date read from the signed PMN PDF:
- **23-14** Office of Police Chief (Title 2 Ch 55) — 2023-08-15.
- **25-09** compensation of elected officials (Title 2 Ch 105) — 2025-04-01.
- **25-19** electric utility franchise + easement, Rocky Mountain Power — 2025-06-03.
- **26-07** gas franchise, Questar/Enbridge — 2026-04-21 (PMN notice quotes the adopting
  consent-agenda motion; all_votes captured it only as "approve the Consent Agenda").

For `none` rows `matched_motion_date` is blank so they are never read as corroborated.

## Six-member council (linkage note)

Riverton is a six-member council: **5 districts + a Mayor who votes only to break a tie**
(max ordinary roll = 5; one tie-break exists, 2025-12-16, Res. 25-62 — a resolution, not in
this dataset). The linkage never assumes the Mayor is a normal voter. `build_index.py`
`choose()` picks the **adopting** motion, excluding later repeal/reconsider/table motions on
the same number (e.g. 24-14, adopted 2024-07-16, later reconsidered 2024-08-06 and repealed
2024-08-20 — the row links the 2024-07-16 adoption).

## Schema

`index.csv` — §9 ordinances contract header (`ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`) + city extras
`linkage_note, minutes_source, pmn_notice_url, pmn_file_id`. **Never hand-edit** — regenerate
from source. Inputs: `pmn_adoption_notices.csv` (the PMN body-889 enumeration) +
`../meeting_minutes/all_votes.csv` + the `text/` sidecars.

## Caveats

- **`within_source` ≠ corroborated.** 93 of 155 rows are motion-derived only — treat as
  suggestive, not independently confirmed. Only the 58 `high` rows have a second source.
- **2020–2022 has no independent PDFs** (PMN Notice-of-Adoption posting began 2023) — an
  honest source limit, not a scraper miss.
- **Resolutions are a separate instrument sequence** — out of scope; the join keys on the
  word "Ordinance" + number in the motion text.
