# West Valley City — adopted ordinances (zoning/land-use focus)

Additive dataset built by `expand-city-sources`. Coverage window **2020–2026** (plus one
2019 straggler, Ord 19-49, adopted at the 2020-01-07 meeting). As-of **2026-07-06**;
**26-26..30 backfilled 2026-07-19** (2026-06-23 meeting — see the update note at the bottom).

## What this is

An index of West Valley City adopted ordinances (`YY-NN` numbering), each linked — where
possible — to the City Council roll-call motion that adopted it in
`../meeting_minutes/all_votes.csv`. WVC is a **case-number city**: land-use items are keyed
`GPZ-`/`Z-`/`PUD-`/`SMI-` (general-plan+zone / zone change / planned-unit / subdivision), so
the land-use **case number** is captured in `case_no` where present, feeding the repo's
existing case-number referral layer.

## Sources & whether an independent archive exists

- **Independent signed-ordinance archive: YES, but only 2024–2026.** The city's CivicPlus
  Archive Center (`www.wvc-ut.gov/Archive.aspx`) publishes signed ordinance PDFs under
  per-year modules **"City Ordinances 2024" (AMID 171), "2025" (172), "2026" (182)**. Each
  PDF carries an authoritative `Date Adopted:` and full title. **106 signed PDFs** were
  harvested to `raw/` (covers 2023-35 & 2023-36, adopted in Feb-2024, through 26-30 — the
  2026-07-19 backfill added the signed PDFs for 26-28 / 26-29 / 26-30, ADID 3731/3732/3733).
  There is **no** Archive Center module for **2020–2023** ordinances.
- **Codified code (American Legal / Sterling `westvalleycity.municipal.codes`):** both are
  bot-blocked (American Legal 403 current-only; municipal.codes returns 403 to non-browser
  clients). No machine-readable ordinance-adoption table was retrievable there.
- **Minutes:** WVC council minutes cite ordinance numbers verbatim (`to approve Ordinance
  26-03`). **316 distinct ordinance numbers** appear in `all_votes.csv` motions — this is the
  spine of the index for the years the signed-PDF archive does not cover.

## Counts (329 ordinance rows total, 258 land-use)

Confidence tiers (see `CLAUDE.md` for definitions):

| tier | all | land-use | meaning |
|------|-----|----------|---------|
| `high` | 97 | 68 | number in an independent signed PDF **and** a council motion |
| `within_source` | 223 | 189 | council motion only (no independent PDF — mostly 2020–2023) |
| `none` | 9 | 1 | adopted (signed PDF) but **no** motion cites the number — audit signal |

- **106 signed PDFs** retained in `raw/` (all `high` + all 9 `none`).
- **164 rows carry a land-use `case_no`**: GPZ 96 · Z 53 · SMI 7 · PUD 6 · ZT 1 · SA 1.
- Adoption dates: PDF `Date Adopted:` is authoritative where a PDF exists; otherwise the
  council vote date is used.

## Audit signal — adopted ordinances missing from `all_votes.csv`

9 ordinances have a signed, dated city PDF but **no motion in `all_votes.csv` cites that
ordinance number** (`match_confidence=none`, empty match fields — never forced). All 9 fall
inside the minutes-coverage window (their meeting dates have carved minutes), so these are
genuine link gaps, not post-coverage seams — most likely **consent-calendar adoptions** or
motions that referenced the application/resolution number rather than the ordinance number:

- `25-02` (2025-02-25, fire-dept fees), `25-04` (2025-04-08, code §16-5-101),
  `26-01` (2026-01-27, Fairbourne CRA amendment), `26-02` (2026-01-27, code §1-2-107),
  `26-22` (2026-06-09, **zone change A-2→…, land-use**), `26-23` (2026-06-09, budget),
  `26-24` (2026-06-09, code ch. 5-3), `26-25` (2026-06-09, code §1-2-107),
  `26-30` (2026-06-23, International Building Codes — a **Consent Agenda item A** adopted in
  the bundled "approve all items on the Consent Agenda" motion, which cites no number).

Only `26-22` is land-use. Recommend the parent repo reconcile these against the consent
agenda of each meeting.

## Backfill note — 2026-07-19 (26-26 … 26-30, the 2026-06-23 Regular Meeting)

Five ordinance numbers from the **2026-06-23** Council Regular Meeting were owed and are now
indexed:

- **26-26** (GP change, 6290 W Parkway) and **26-27** (zone-map change, same site,
  application GPZ-2-2026) were **DENIED** — Councilmember Harmon's *motion to deny* passed
  4-1 (mno 2 and 3). No signed PDF exists (correctly — nothing was adopted). Indexed as
  `within_source` land-use rows exactly like the 30+ other denied-motion ordinance numbers
  already in the index (20-09 … 26-08); **the row is a number↔motion cross-reference, not a
  claim of adoption** — the denial is recorded in the linked `all_votes.csv` motion
  (`to deny Ordinance 26-26 … 4-1 Pass`).
- **26-28** (Title-7 zone-text SB-284 compliance, ZT-1-2026, mno 5) and **26-29** (public-
  utility-easement vacation, SA-4-2026, mno 6) were **approved 5-0**; signed PDFs harvested
  (ADID 3731 / 3732) → `high`.
- **26-30** (International Building Codes, Title 16) was **approved in the Consent Agenda
  bundle**; signed PDF harvested (ADID 3733) but no motion cites the number → `none`
  (building code, `land_use=0`).

## Gaps / caveats

- **2020–2023 has no independent signed-PDF archive** — those 221 rows are `within_source`
  (minutes-derived). Their titles come from the minutes agenda-item header, which is reliable
  for standalone land-use items but was **misattributed for ~9 consent-calendar ordinances**
  (nearest header was "CITY COUNCIL COMMENTS" etc.); those titles were **blanked** rather
  than left wrong (10 rows have empty `title`).
- The Archive Center 2024/2025 modules are themselves **incomplete**: 2024 skips 24-04, -12,
  -27, -32/-33, -42/-43, and everything above 24-49 (24-50…24-57 exist in minutes but not in
  the archive); 2025 skips 25-17, -25, -36/-37. Those un-archived-but-adopted ords are carried
  as `within_source`.
- No separate extracted-text corpus is stored — the raw PDFs are the retained originals and
  the only derived text is the short `title`/`case_no` metadata in `index.csv` (spot-verified
  against source PDFs; nothing to anomaly-screen at corpus scale).
- Nothing here overwrites city-faithful values; `result`/`motion_type` remain verbatim in
  `all_votes.csv`. This dataset is a read-only cross-reference.
