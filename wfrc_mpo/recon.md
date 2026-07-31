# WFRC (wfrc_mpo) — recon / source map

**Wasatch Front Regional Council** — the repo's first **REGIONAL-tier** entity
(`gov_level='regional'`, `level='regional'`, fed_index **201**, dir `wfrc_mpo/`). WFRC is
the federally-designated **Metropolitan Planning Organization (MPO)** for the greater
Salt Lake / Ogden urbanized area: Salt Lake, Davis, Weber, and Morgan counties plus the
southern (Willard/urbanized) part of Box Elder County. It is NOT a general-purpose
government — no land use, no ordinances, no elections, no taxes. Its Council adopts the
**Regional Transportation Plan (RTP)**, the **Transportation Improvement Program (TIP)**,
the **Wasatch Choice Vision**, certifies member-city **Station Area Plans**, and runs the
WFRC budget. Registry row already exists (do NOT edit registry files); 26 repo cities +
salt_lake_county + weber_county carry `member_of wfrc_mpo` edges in
`registry/relationships.csv`.

## Governance form

A **27-member Council, 21 voting**. Seats are held **ex officio** by elected
mayors/commissioners of member jurisdictions (allocated by county), plus the **UDOT
Executive Director** and **UTA trustees**. Six **non-voting** appointments come from the
Utah League of Cities and Towns, Utah Association of Counties, Envision Utah, the
Legislature (one Senator, one Representative), and GOPB. The Council elects a **Chair**
(2025-26: South Jordan Mayor **Dawn Ramsey**) and **Vice Chair** (Davis County
Commissioner Bob Stevenson). Its standing committees — **Regional Growth Committee (RGC)**,
**Transportation Coordinating Committee (Trans Com)**, and the **WFRC Budget Committee** —
meet separately but their recommended actions are **taken by the full Council** and recorded
IN the Council minutes under numbered agenda sections. See `roster/` for the seat table.

Non-repo jurisdictions (Davis / Morgan / Box Elder / Tooele counties and their cities,
UDOT, UTA, the Legislature) sit on the Council too; they are flagged **external** and are
NEVER invented as repo entities.

## Source portal

- Site: **wfrc.org → wfrc.utah.gov** (301). Current WordPress rebuilt **Dec 2025** (Events
  Manager plugin). The Council portal is
  **https://wfrc.utah.gov/committees/wfrc-council/** — per-meeting Agenda / Full Packet /
  Minutes + a YouTube recording, plus the current-year member roster.
- Minutes live at stable file paths: **`/Committees/Council/<year>/<NN_MonDD>/<file>.pdf`**
  (2026 pattern e.g. `/Committees/Council/2026/01_Jan22/2026Jan22_Council_MinutesFINAL.pdf`;
  early-year meetings are sometimes flat, `/Committees/Council/<year>/<file>.pdf`; folder +
  filename naming **drifts year to year**). The **live host serves the full historical file
  tree** — every 2016-2024 path still resolves `200` on wfrc.utah.gov even after the Dec-2025
  rebuild — so minutes are fetched from the LIVE site (Wayback used only for path discovery).
- Documents are **born-digital Google-Docs → Skia PDFs**. `pdftotext` extracts them cleanly;
  **WebFetch mis-renders them** — extract locally. 2024+ exports lace every word with Unicode
  directional/zero-width chars (U+200B, U+202C/D) and occasionally break a word across a
  line; the extractor strips these (→ space) and unwraps.
- **PMN body 2262** exists but is shallow (notices roll off). **Wayback** archived the old
  wfrc.org site including the `/Committees/Council/` PDF paths — used to DISCOVER the archive.

## Archive depth found (probed back to floor)

**Council meets ~5×/year** (modal Jan / Mar / May / Aug / Oct, 4th-week weekday). Discovered
via the old-site Wayback CDX index + the live Events-Manager event pages. **FLOOR = 2016**:
the earliest Council minutes online is **2016-01-28** (2015 and earlier: no capture on the
live host or Wayback — honest floor). Full continuous coverage **2016 → 2026**:

| Years | Meetings | Notes |
|------|---------|-------|
| 2016-2019 | 20 | "…minutes APPROVED" PDFs; 2016-03-24 is a **.docx** (only format published; textutil-converted); 2016 also has .WMA audio (not ingested) |
| 2020-2024 | 25 | MinutesFINAL PDFs; a few own-minutes only as DRAFT recovered from the following packet |
| 2025 | 5 | Jan flat, rest `NN_MonDD/` |
| 2026 | 3 | Jan/Mar FINAL; **2026-05-28 DRAFT** (latest posted); Aug 27 & Oct 22 2026 scheduled, no minutes yet |

**53 meetings total, all fetched + converted.** Two are **draft-sourced** (no FINAL
published): **2023-01-26** (only `…MinutesDRAFT_wPublicAttendanceLists`) and **2026-05-28**
— tagged `provenance='minutes_draft'` (filterable apart from audited FINAL/APPROVED).

## THE VOTE RECORDING CEILING (verified across 2016-2026)

WFRC minutes name the **MOVER** and the **SECONDER** of every action and print a **narrative
tally** result. **Dissent is COUNT-ONLY — dissenters are NEVER named, and there is NO roll
call.** Mover/seconder are procedural attributions, **not votes**. So individual `vote` rows
are **absent by construction** (`vote` table empty; every motion `names_recorded=0`) — an
honest recording ceiling, the same shape as nephi / west_jordan PC. Verbatim example
(2025-10-23, RGC section, a *divided* vote — still no names):

> "[01:26:23] ACTION: Legacy Parkway - I-15 / US-89 to I-215 (Davis County) **Commissioner
> Jim Harvey made a motion** to approve the Level 3 amendment for this project as presented.
> The motion was **seconded by Mayor Brandon Stanger**. **There were two dissenting votes;
> however, the affirmative vote was the majority and the amendment was approved.**"

Unanimous example: "…the affirmative vote was unanimous." / "…passed unanimously."

## What was built (all modules — finalized 2026-07-20)

- `legislative/` — 53 Council minutes (markdown + provenance front-matter) +
  `minutes_index.csv` (with `md_path`) + `all_motions.csv` (**323 motions**: mover/seconder
  person-linked by full name, verbatim `result_raw`, `outcome`, `body` walking the RGC /
  Trans Com / Budget section headers). `meetings_source.tsv` = the curated URL manifest.
- `roster/council_seats.csv` — the WFRC Council seat table (office → person → repo entity →
  voting). The current member table enumerates **28 seats (22 voting + 6 non-voting)** against
  WFRC's nominal 27-member/21-voting charter (the extra voting row is a second UTA trustee the
  2026-01-22 table lists); UDOT/UTA carried from the clean 2025-10-23 table (`confidence=medium`).
- `db/wfrc_mpo.db` — the STANDARD 8-table schema (federates unchanged; 53 meetings, 86 persons,
  323 motions, `vote`=0). Scripts: `fetch_minutes.py` → `extract_motions.py` → `build_db.py`
  (rerun in that order).
- **`projects/`** — TIP+RTP pipeline, `projects.csv` **5,146 rows** (TIP 3,699 / RTP2023-2050
  1,447). **`projections/`** — WFRC RTP-2023 small-area forecast, `wfrc_mpo_projections.csv`
  **9,504 rows** (98 city-areas + region × pop/HH/jobs × annual 2019-2050). **`gis/`** — catalog
  of **18** Wasatch Choice growth/vision ArcGIS layers (`services1.arcgis.com/taguadKoI1XFwivx`,
  link-only). All BUILT; each carries its own SOURCES.md. Federated: `regional_project` (5,146),
  `projection` (9,504), `motion` (323).
