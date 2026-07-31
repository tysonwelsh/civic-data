# ordinances/ — availability & gaps (as-of 2026-07-05)

Adopted zoning / land-use (and other) ordinances of the **Nephi City Council**, 2020–2026.
What was checked for an independent ordinance archive, what exists, and what does not.

## How Nephi numbers ordinances (the join key)
Nephi does **not** use a `YYYY-NN` sequence. Every ordinance number **is its adoption
date**: `Ordinance MM-DD-YYYY`, with an uppercase suffix (`-A`, `-B`, `-C`, `-S`, `-Z`)
when more than one ordinance is adopted at the same meeting (e.g. `11-16-2021-A`
Mangelson rezone, `-B` Powell Yards rezone, `-C` addressing). Because the number encodes
the meeting date, the number is **intrinsic to the council motion text** — so a
number recovered from the minutes is *not* independent of the vote layer (see confidence
note in `CLAUDE.md`).

## Code host (current codified text)
- **CivicLinQ** — `https://hosting.civiclinq.com/nephicity/books/city-code/preface`
  (linked from `nephi.utah.gov/168/City-Code-Planning-Documents` as "Online City Code").
  Holds **Title 10 (Land Use & Zoning)** and **Title 11 (Subdivision, Site Plan &
  Land Development)** as current consolidated text — **not** a number→date→subject
  adoption history, so it is not the join backbone. No Municode / American Legal /
  Sterling code exists for Nephi (Municode `library.municode.com/ut/nephi` = 403 / none).

## Independent adopted-ordinance archive — YES (partial): Utah Public Notice (PMN)
- **Utah Public Notice, public body 1788** (`utah.gov/pmn/sitemap/publicbody/1788.html`)
  posts Nephi City **"Notice of Ordinance"** PDFs — signed/certified ordinance texts that
  carry the **same `MM-DD-YYYY` number**. These are the one source **independent of the
  council minutes**, so they are what lifts a row to `match_confidence=high`.
- PMN's per-body page shows only recent notices and its search is JS/opaque, so this pass
  **did not exhaustively crawl** it. **5 ordinance PDFs** were discovered (via web search),
  retrieved to `raw/`, text-extracted to `text/`, and used to corroborate 5 index rows:
  `07-11-2023` (Title 10 zoning), `02-07-2023-A` (§10.15.5 RV parks, scanned→OCR),
  `12-02-2025` (ID4 data-center zone), `12-02-2025-A` (modular data center in ID1),
  `01-20-2026` (Jacobson/400 W annexation). PMN holds **more** Nephi ordinance notices
  than these 5 — harvesting the rest is the obvious backfill (see Deferred).
- The city website (`nephi.utah.gov`, CivicPlus DocumentCenter) publishes the General
  Plan, zoning maps and annexation plans but **no per-adoption ordinance PDF list**; the
  Recorder does not post signed ordinances online. So no city-hosted archive backs the index.

## What this dataset therefore is
Because no complete online full-text archive exists, the index is **primarily
reconstructed from the council minutes** (`meeting_minutes/`, 2020–2026): every ordinance
number that appears in a minutes section header or a motion, linked to its adopting
council motion in `meeting_minutes/all_votes.csv`. The 5 PMN PDFs cross-validate 5 rows.

## Coverage (103 ordinance numbers, 2020–2026)
| adoption year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| ordinances | 19 | 23 | 15 | 16 | 18 | 9 | 3 |

- **99 adopted**, **4 non-adopted** (kept for the record, flagged in `status`): `03-03-2020`
  **FAILED** 2–3 (Title 10 ch.15 amendment), `07-07-2020` / `06-06-2023` / `10-15-2024`
  **TABLED** (nuisance-abatement, a trail resolution/ordinance, short-term-rental draft).
- **71 land-use** ordinances (69 of them adopted): 41 zone changes, 10 land-use-code
  (Title 10) amendments, 8 subdivision (Title 11), 5 annexations, 2 short-term-rental,
  + ADU / overlay / street-vacation / general-plan / plat / parking.

## Confidence tiers (`match_confidence`)
| tier | n | meaning |
|---|---|---|
| `high` | 5 | number in an **independent PMN Notice-of-Ordinance PDF** *and* a council motion |
| `within_source` | 91 | number recovered from the **minutes/motions only** (not independently corroborated) |
| `none` | 7 | **unmatched** — a genuinely adopted ordinance with **no discrete vote row**, or a number whose date is not a council meeting date (match fields left empty — audit signals, below) |

- **9 of the 91** `within_source` rows are **same-day suffix siblings** whose motion could
  only be linked **positionally** (the source `all_votes.csv` truncates the suffix letter,
  e.g. `"adopt Ordinance 11-16-2021-"`); these say so in `extraction_method`.

## Audit signals — adopted ordinances with NO matching vote row (7 `none` rows)
Nephi votes are **mostly tally-only / narrative** (many ordinance adoptions are folded
into a consent agenda or narrated without a discrete roll-call). These ordinances are
recorded as adopted in the minutes but have **no discrete motion in `all_votes.csv`**:
- **Land-use** (2): `05-18-2021` (R1-H→CU rezone, McPherson) and `07-12-2022` (§10.3.6
  sign-permit authority) — see the 2026-07-20 note below; both are honest gaps, NOT
  extraction misses.
- **Other** (5): `05-05-2020` (cemetery §7-5-7, adopted in a bundled motion), `07-07-2020`
  (nuisance/abatement, tabled), `10-02-2021` & `01-18-2025` (impact-fee / adopt — number-date
  not a meeting date), `12-19-2023` (appointed-employees code). Match fields are left
  **empty** — never forced.

### 2026-07-20 — the 4 flagged land-use ordinances, resolved
The vote-extractor recovery this date (see `../meeting_minutes/CLAUDE.md`) plus source review
resolves the four land-use `none` rows two-and-two:
- **`06-20-2023`** (rescission of a temporary R-3 land-use ordinance) — **RECOVERED → linked**
  (`within_source`, motion #3). It was a real `Councilor Wowood moved to adopt Ordinance
  06-20-2023 …` motion that the extractor dropped because the mover surname was OCR-mangled
  ("Wowood"); the `Wowood→Worwood` alias fixed it.
- **`05-20-2025`** (R1-H→R1-½ac rezone, 300 W) — **RECOVERED → linked** (`within_source`,
  motion #2, **4-0 named roll call**). Dropped because the 2025 recorder wrote "made **the**
  motion to approve the zone change ordinance …"; the widened motion anchor fixed it.
- **`05-18-2021`** (R1-H→CU rezone, McPherson) — **HONEST GAP (correctly `none`).** The minutes
  print no motion: "The council agreed to **table** the zone change until they receive more
  information." The ordinance was **tabled by verbal consensus** (no mover/seconder/vote) — there
  is no separable action to extract.
- **`07-12-2022`** (§10.3.6 sign-permit authority) — **the adopting vote EXISTS in
  `all_votes.csv`** (2022-07-19 motion #7: "Councilor Parady moved to adopt Ordinance 07-12-2022
  … amending section 10.3.6 c(3) … sign permits"). The ordinance NUMBER-date (07-12, a 2nd-Tuesday
  work session) simply **differs from its adoption date** (07-19); the number-keyed index looks on
  07-12 and finds nothing, so the row stays `none`. This is an index-linkage artifact, **not** a
  missing vote — the roll-call is present and correctly extracted on 2022-07-19.

## Retained but NOT indexed
- `raw/1253943.pdf` — a PMN file titled "Nephi City ORDINANCE No. 2025-06 … Title 10 land
  use," but its text reads **"APPROVED AND ADOPTED by the City of North Salt Lake"** — it is
  a **North Salt Lake model/reference ordinance** Nephi posted, **not a Nephi adoption**.
  Kept in `raw/` (never discard a fetched original) but deliberately excluded from `index.csv`.

## Deferred / not obtained (how to get it later)
- **Full PMN harvest of body 1788** — crawl every "Notice of Ordinance" page for its
  `/pmn/files/NNNN.pdf` attachment; would add official signed texts and lift many
  `within_source` rows to `high`. Overlaps the PMN-backfill source type.
- **Recovering the remaining `none` ordinance vote rows** (now 7, down from 11 after the
  2026-07-20 extractor recovery) — re-carve the specific minutes (bundled/consent-folded
  adoptions) so any that carry a real motion gain a discrete row. Note 05-18-2021 (tabled by
  consensus) and 07-12-2022 (adopted 2022-07-19, a number-date≠meeting-date quirk) are NOT
  recoverable this way — they are honest/linkage gaps, documented above.
- **CivicLinQ current Title 10 / Title 11 text** — readable in-browser; not an adoption history.
