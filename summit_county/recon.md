# Summit County — source reconnaissance (2026-07-20)

The MID-tier county build. Summit County (FIPS 49043; **Council–Manager form** — a
**6-member elected County Council** [legislative] + an **appointed County Manager**
[executive]; meets **Wednesdays**, weekly). Seat: Coalville. Contains one repo city,
**park_city** (do not touch — separately owned). Federated into repo-root `gov.db`
(`cities.db`) as `gov_level='county'`, fed_index **105**. Counties are modeled as
**modules**, not big cities. This file maps the county's own growth/development records;
`legislative/` (County Council) is the built module here, `agencies/` is a deferral ledger,
and land_use / elections / plans / etc. are owned by other agents.

## Legislative — County Council ✅ primary source found (Granicus, NOT Legistar)

- **Platform: Granicus** MinutesViewer, `view_id=1`. The Council's minutes are **born-digital
  HTML text** (not scanned) with timestamped agenda sections and attached staff
  reports/ordinances. Per-meeting URL:
  `https://summitcounty.granicus.com/MinutesViewer.php?view_id=1&clip_id={N}`. The archive
  index is `ViewPublisher.php?view_id=1` (456 clips across all bodies; the Council rows are
  labeled **"SCC …"** / "Summit County Council" — 205 clips).
- **Summit has NO Legistar** — there is no structured API. Votes must come from the minutes
  prose, and the minutes are **TALLY-PRIMARY** (see the ceiling below).
- **Granicus coverage: 2023-01-04 → present** (2026-07-07 at build). Enumerated
  systematically from ViewPublisher; **198 HTML meetings** extracted + **7 uploaded-PDF
  special sessions** (Jan–Feb 2023, behind Granicus DocumentViewer — logged unrecovered).
  The Granicus era is contiguous weekly with a single normal summer-recess gap
  (2026-06-10 → 2026-07-07); **no missing regular meetings**.

### THE RECORDING CEILING — tally-primary (honest, final)

Every motion names the **mover + seconder** and prints a **tally**, but names individual
members' votes **only when a division is called**. Verbatim example (clip 1185, 2025-12-17):

> "Roger Armstrong made a motion to approve the new precinct maps. (6:20 PM). Christopher
> Robinson seconded, and **all voted in favor, (5-0)**."

vs. a divided vote the same night:

> "Canice Harte made a motion to deny the PID. (9:01 PM). Roger Armstrong seconded, and **the
> motion carried, (3-2)**. Roger Armstrong voted AYE / Canice Harte voted AYE / Megan McKenna
> voted AYE / Christopher Robinson voted NAY / Tonja B Hanson voted NAY."

So unanimous motions are **tally-only** (`names_recorded=0`, blank member/vote — the majority),
and **named `vote` rows exist only for the 23 divided motions**. Because Summit has no
Legistar, this ceiling **cannot be lifted** — it is a true recording limit, not a gap (cf.
nephi / west_jordan PC; contrast salt_lake_county, whose Legistar API is richer than its
tally-only minutes). Mover/seconder are recorded on every motion. Never fabricated.

Extraction note: the born-digital minutes frequently run the motion action and the seconder
clause together **without a sentence period** ("…Board of Equalization Malena Stevens
seconded"). Mover/seconder are therefore attributed by **surname → the known 6-member roster**
(`extract_votes.py`), which also unifies the printed variants (Chris/Christopher Robinson;
Tonja/Tonja B Hanson). Verbatim prose is preserved in the motion text + the minutes markdown.
The Council convenes **in-session** as the Board of Equalization, the SBSRD/rec-district
governing board, etc.; those convening motions stay `body='County Council'` (verbatim in the
motion text) — the legislative module is the Council.

### Pre-Granicus backfill — CivicPlus AgendaCenter + PMN 1330 (OCR-gated, honest ledger)

- **CivicPlus AgendaCenter** (`summitcountyutah.gov/AgendaCenter`, County Council **catID=1**;
  fetch a year with `UpdateCategoryList?catID=1&year=<YYYY>`) holds County Council minutes
  **2015–2024**. AgendaCenter was frozen for new postings after **2024-05-15** (a new
  "Meetings and Minutes" page took over — which is the Granicus front-end).
- **Decisive finding:** the pre-2023 AgendaCenter minutes are **image-only scanned PDFs** (files
  up to ~180 MB, ~zero extractable text layer) — a **different, OCR-gated era** from the clean
  Granicus HTML. **2015 is a partial exception** (a rough OCR text layer;
  "…made a motion … passed unanimously, 5 to 0"). Extracting votes from these requires an OCR
  pass with per-year-varying prose, so it is **deferred as a documented backfill** rather than
  guessed at.
- **Honest ledger (`legislative/minutes_unrecovered.csv`, 460 rows):** every pre-Granicus
  Council meeting date + its AgendaCenter minutes URL is captured — **453 dates 2015-03-25 →
  2022-12-30** (`status=scanned-image`, OCR-pending) plus the **7 Granicus uploaded-PDF**
  special sessions (`status=granicus-pdf`). By year: 2015=40, 2016=17*, 2017=52, 2018=57,
  2019=41, 2020=110, 2021=63, 2022=73. (*2016 posts minutes for only 17 meetings — agendas
  exist for the rest; a genuine posting gap, PMN-recoverable.) **Jan–Mar 2015** and **pre-2015**
  Council minutes are **not posted** on AgendaCenter (earliest is 2015-03-25) — a genuine
  availability floor, not a build omission.
- **Utah PMN body 1330** (Summit County Council, `pmn.utah.gov`) is the born-digital
  reconciliation/backfill channel for OCR-upgrading the 2015–2022 scans — queued follow-on.
  The Granicus era needs no PMN reconciliation (verified contiguous-weekly, no gaps).

## Agencies — RDA + Housing Authority ⏸ DEFERRED (honest ledger only)

Both are documented in `agencies/README.md` and **not built** (per scope):
- **Redevelopment Agency** — PMN body **1277**; thin (a single Silver Creek project area),
  minimal minutes history.
- **Summit County Housing Authority** — **formed 2025** (Granicus body "Summit County Housing
  Authority", first minutes 2025-06; PMN presence just beginning) — essentially **no history**
  to harvest yet.

## Modules owned by OTHER agents (not built here)

`land_use/` (Snyderville Basin PC = SBPC + Eastern Summit County PC = ESCPC, both on Granicus
`view_id=1` and PMN), `elections/` (county Clerk canvass), `plans/`, `projections/`, `gis/`,
`ordinances/`, `packets/`, `development/`. Not touched by this build.

## Module status

| module | source | status |
|---|---|---|
| `legislative/` | Granicus MinutesViewer (SCC, view_id=1), 2023-01→present | ✅ built (198 mtgs, 1,831 motions — counts refreshed 2026-07-25) |
| pre-2023 backfill | CivicPlus AgendaCenter (scanned) + PMN 1330 | ⏸ ledger only — OCR-gated follow-on |
| `agencies/` | RDA (PMN 1277) + Housing Authority (formed 2025) | ⏸ deferral ledger (README.md) |
| `db/` | prose staging → summit_county.db (standard 8-table) | ✅ built (FK ok, integrity ok) |
