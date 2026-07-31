# cache_county/ordinances — how to use this module

**Cache County's adopted ordinances**, as (a) the full **codified County Code** text and
(b) a **catalog of every ordinance cited in that code**, with the land-use ordinances
flagged and the enacting-vote linkage left blank for a later closing pass. Self-contained:
the code PDF, its text, and two manifests. Nothing here writes to the db.

## Layout

- `raw/cache_county_code_amlegal.pdf` — the compiled **County Code of Cache County, Utah**
  (American Legal Publishing), **current through Ord. 2023-18 (passed 2023-05-09)**,
  260 pp. Born-digital.
- `text/cache_county_code_amlegal.txt` — pypdf-extracted full text. **The searchable
  code layer — grep this** for what any provision says.
- `index.csv` — the **ordinance catalog**, one row per distinct ordinance number cited in
  the code's section source-notes. Columns: `ordinance_no, adoption_date, land_use_type,
  code_titles, code_title_names, motion_id, match_confidence, source_url, notes`.
- `code_structure.csv` — the code's skeleton: the 17 Titles + every **Title 15/16/17**
  (Buildings / Subdivision / Zoning) chapter, with a `land_use_flag`. The "what's in the
  land-use code" index.
- `SOURCES.md` — the three codification portals, method, and the honest scope limits.

## The land-use code (what to reach for)

Land use / growth / housing lives in three Titles (flagged `land_use` throughout):
- **Title 17 — Zoning Regulations** (24 chapters: 17.06 Uses, 17.08 Zoning Districts,
  17.09 Schedule of Zoning Uses, 17.10 Development Standards, 17.13 Mineral Extraction,
  17.16 Group Living, 17.18 Sensitive Areas, …). See `code_structure.csv`.
- **Title 16 — Subdivision Regulations** (16.01–16.04).
- **Title 15 — Buildings and Construction**.
39 of the 169 cataloged ordinances amended these three titles.

## The vote linkage — DERIVED, regenerate it (`db/link_ordinances.py`)

`motion_id` / `match_confidence` are **computed, never hand-written**. Run
`python3 db/link_ordinances.py` **after every `db/build_db.py`** — the script re-derives
the whole linkage and rewrites only `motion_id`, `match_confidence`, and the trailing
linkage clause of `notes`. It is idempotent and self-documenting (read its docstring for
the seven guards).

**17 of 169 ordinances are uniquely linked**, all `match_confidence=high`, all 2021–2022
(the named-roll era; the 2015–2020 tally-only era has no roll call to link and the
pre-2015 code-cited ordinances predate the data floor). Join `motion_id` → `vote` in
`db/cache_county.db` (or gov.db `motion`/`vote` WHERE `city='cache_county'`, remapped by
the federation offset).

**Ordinances 2022-06, 07, 08, 09 and 10 all carry the SAME `motion_id`** — the Council
enacted them in one printed roll call ("approve Ordinance 2022-06, 07, 08, 09 and 10",
2022-02-22). That is the source, not a matching error; `motion_resolution='unique'` still
holds (the enacting motion is unambiguous), it is simply shared.

**8 ordinances are named on the floor but left BLANK** (`match_confidence=unlinked`, each
with a `notes` reason): 2020-12, 2021-09, 2021-14, 2022-01, 2022-26, 2022-34, 2022-35,
2023-02. Reasons include a *failed* adoption motion (2022-01 — the code source-notes it as
adopted 1-25-2022 while the minutes read "Motion Fails"; both are retained, neither is
arbitrated), set-public-hearing-only motions (2022-35, 2023-02), two competing adoption
motions (2022-26, 2022-34), and a Resolution-not-Ordinance number collision (2021-14).

### Why hand-written ids failed (audit 2026-07-25 F8 + F16 follow-through, 2026-07-29)

Two independent failures, both fixed by making the linkage derived:

1. **A clerk typo shipped as `high` confidence.** ORD 2021-22 pointed at a 2021-10-12
   motion. The primary document says otherwise: at 2021-10-12 item **(b)** reads
   "Ordinance 2021-22 … **TABLED FOR NEXT MEETING**", while the motion the matcher grabbed
   sits under item **(c)** "Ordinance **2021-23** … APPROVED" and reads "approve Ordinance
   2021-22" — the clerk typed the wrong number. The true enactment is **2021-12-14**
   ("Ordinance 2021-22 Adopting the Cache County Consolidated Fee Schedule APPROVED";
   Erickson moved, Borup seconded, Aye 6 / Absent 1 Ward), which matches the code's own
   source note **`(Ord. 2021-22, 12-14-2021, eff. 1-1-2022)`** printed at 15 places in
   `text/`. The register's `adoption_date` was right all along; the *link* was wrong.
2. **Every stored id went stale.** The 2026-07-26 OCR backfill inserted 1,505 motions from
   the 2015–2020 era *ahead* of the born-digital era, renumbering `motion_id`. All 10
   surviving links then pointed at unrelated 2015–2017 motions ("approve the agenda as
   written", "adjourn from the Council meeting at …"). **A hand-written motion id cannot
   survive a db rebuild** — which is why this is now a script.

## Cardinal rules & honest scope (read before quoting)

- **This catalog = CODE-AMENDING ordinances only.** It is built from the codified
  source-notes, so it lists ordinances that changed **code text**. **Map-amending
  ordinances — rezones — are NOT here** (a rezone changes the zoning *map*, not the code,
  so American Legal never source-notes it). The rezone record lives in the **`land_use/`
  PC motions** and the County Council legislative record — not this module. A land-use
  researcher wanting "every rezone" must use those, not `index.csv`.
- **Never fabricate — especially ordinance numbers/dates.** `adoption_date` is populated
  **only where the code printed a date**; blank otherwise. Ordinance numbers are copied
  **verbatim** as cited (including old 2-digit-year forms like `65-03`, `91-02`); no
  calendar year is inferred onto them.
- **Text is derived; the PDF + `source_url` are canonical.** Regenerate the text by
  re-running pypdf on the raw PDF.
- Coverage is the codified era through **Ord. 2023-18 (2023-05-09)**; ordinances adopted
  after that supersede the code and are not yet in this snapshot — an honest, dated floor.

## Linkage rules (2026-07-26 after audit F8; enforced in code 2026-07-29)

An ordinance-number match is **not sufficient** to link an enacting motion. Every guard
below is now implemented in `db/link_ordinances.py`, so the rules run instead of being
remembered:

1. **Canonical document.** The motion's `source_file` must be listed in
   `legislative/minutes_index.csv`. 12 un-indexed byte-identical duplicate markdown files
   sit on disk and the vote extractor walks the directory, so a motion from one of them
   would make an otherwise-unique match look like two.
2. **Ordinance context, not Resolution.** Cache reuses the same serial number for an
   ordinance and a resolution in the same year (2021-14, 2021-22, 2022-19 all have both).
3. **Adoption verb** — approve/adopt/enact, excluding set-a-public-hearing, deny, table,
   postpone, and minutes-correction motions.
4. **The motion carried** — `outcome='Pass'` *and* the verbatim result does not say the
   motion died/failed (2022-06-28's "Motion dies" for ORD 2022-19 is stored `Pass`; an
   upstream extractor defect, guarded here too).
5. **Read the agenda item the motion sits under.** These minutes number their items, and
   the clerk types the wrong ordinance number in the Action line often enough to matter —
   at 2021-10-12, item (b) says "Ordinance 2021-22 … **TABLED FOR NEXT MEETING**" while
   the motion sits under item (c) "Ordinance **2021-23** … APPROVED". **The item heading
   outranks the number inside the motion text.** (Skipped for bundled roll calls, which
   sit under the last item of the bundle by construction.)
6. **Date consistency.** If the register printed an `adoption_date`, the motion's meeting
   date must equal it.
7. **Year consistency** where no date was printed — the ordinance's own year prefix must
   equal the meeting year. This is what keeps ORD 2021-09 honest: its only surviving
   candidate is the 2021-03-09 roll call **re-printed inside the 2022-11-22 packet** as
   ATTACHMENT 2 (the Council amended the March 2021 minutes to include the omitted
   approval), and the extractor dates attachment motions to the host meeting.

When the guards do not leave **exactly one** survivor, `motion_id` stays blank with
`match_confidence=unlinked` and a `notes` reason — an honest gap beats a confident wrong
link, and `motion_resolution='unique'` must never be quoted for an ambiguous one.
