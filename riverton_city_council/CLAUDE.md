# Riverton City Council — data repository

Canonical datasets about the Riverton City Council and Planning Commission, modeled on the Salt
Lake City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by
the `build-city-data-repo` skill. Data floor: **2020** (Riverton incorporated **1997** — full
modern history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).

```
meeting_minutes/      City Council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + votes/ JSON intermediate
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md + header-only all_comments_clean.csv — comments are
                      HONEST-EMPTY (submit-only: in-person / Granicus eComment / emailed to
                      the City Recorder; none archived by the city)
election_results/     Salt Lake County SOVC results filtered to Riverton council+mayor races
geo/                  official district FeatureServer + pre-2022 layer + address->district tool
db/                   relational SQLite civic.db (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together (Tuesday grid)
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday = 1)
fetch_new.py          incremental refresh driver (PMN mirror primary / Granicus fallback)
recon.md              map of this city's data sources (provenance) — portal vendor, URL
                      patterns, and the honest-gap record; written BEFORE acquisition
SOURCES.md/sources.csv  per-document provenance index (regenerate: build_sources_index.py)
VERIFICATION.md       independent QA + external election cross-check (23 PASS / 0 FAIL)
```

## The structural facts that make Riverton different
1. **The MAYOR does NOT vote — EXCEPT to break a tie (the Park City model).** Riverton uses
   Utah's **six-member council form**: five district members (**D1–D5**) legislate, and a
   separately-elected **Mayor** chairs the council and is chief executive. The Mayor "casts a vote
   as a member of the city council [only] when necessary to break a tie … when voting on the
   appointment or dismissal of a city manager … and when amending the powers of the mayor"
   (city's own language). So a full council roll call tops out at **5**, and the Mayor appears as
   presiding officer + tie-breaker only. This differs from **Millcreek** (mayor votes routinely,
   tally 5 incl. mayor) and **Taylorsville / South Jordan** (mayor never votes at all) — Riverton
   matches **Park City** (mayor votes only to break ties).
   **The single tie-break in the corpus: 2025-12-16, Resolution No. 25-62** (skate-facility
   removal). Council split **2–2** (McDougal + Pierucci Aye, Buroker + McCay Nay); **Mayor Trent
   Staggs broke the tie voting yes → passed.** Captured verbatim in `all_votes.csv` as
   `result = "Passed (Mayor tie-break)"` + row `Trent Staggs | Aye (Mayor tie-break)` — the one
   `Aye (Mayor tie-break)` vocabulary extension (the sole non-FAIL vote-value WARN). In
   `db/civic.db` it is **normalized to a plain `Aye`** (verbatim is preserved only in the flat
   CSV, per the cardinal rules). Staggs has exactly 1 vote row and 1 role entry.
2. **Two-portal acquisition — Granicus mirrored on Utah PMN.** The city hosts a **Granicus**
   meeting archive (`rivertoncity.granicus.com/ViewPublisher.php?view_id=1`, all bodies), and
   every meeting is cross-posted to **Utah Public Notice** (`utah.gov/pmn`, PC/council body
   **5473**). All minutes here were acquired from **PMN** (`source=pmn`) because the PMN PDFs are
   clean **born-digital text — no OCR anywhere in the corpus.** The city's own **Revize** CMS
   lists meeting dates only (no downloadable archive); Granicus is the fallback enumeration route.
3. **The PC names members ONLY on divided votes.** Riverton's Planning Commission (2nd & 4th
   Thursday) prints a **full named roll call on divided votes** (127 motions, fully attributed)
   and "unanimous consent" — **no names** — on unanimous ones (548 placeholder motions). The
   parser leaves the majority unnamed rather than guessing. **7 PC motions died for lack of a
   second** (recorded with no members). A blank member list on a unanimous PC motion is source
   style, not an extraction miss. (Council is denser: 751 of 885 motions carry named roll calls;
   134 are tally-only.)
4. **D3 ↔ D4 were renumbered at the 2022 redistricting (Ordinance 22-07).** The **election
   record** labels **McCay = D3** and **Buroker = D4** (2017 & 2021) — the **opposite** of
   `recon.md` and current GIS/roster (which have McCay = D4, Buroker = D3 → seat to Johnson D3 /
   Smith D4 in 2025). The retained **pre-2022** GIS layer corroborates the election record.
   **Person↔district joins that cross 2022 must join on person identity, not the bare district
   number** (D1/D2/D5 unaffected). Full write-up in `election_results/CLAUDE.md`.
5. **Roster additions the recon missed (added by the corrected extractor).** Two 2020–2023
   voting members: **Sheldon Stewart** (D1, 2020→2022, → Pierucci) and **Claude Wells** (D5,
   2020→2023, → Haymond). Both verified voting at source (`VERIFICATION.md` §4). Join carefully
   across the 2022–2026 turnover.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings would live in `minutes_unrecovered.csv` (**0 here**),
  never as stub/wrong-doc rows. `source = pmn` for every file; `format = text` (born-digital, no
  OCR).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **plus a documented trailing `provenance` column** (2026-07-16): `minutes` = audited series,
  `pmn_minutes` = the 7 meetings promoted from `pmn_backfill/` (their `source` points at
  `pmn_backfill/text/…`, not `minutes/`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Tuesday** — 1st & 3rd Tuesday; each meeting-day
is **one combined minutes doc**: an Informal Meeting → Work Session → Regular Meeting). The **PC
meets Thursday** (2nd & 4th); its records join on their own date. `build_weeks.py` buckets every
record onto the weekly grid (`MEETING_WEEKDAY = 1`). Elections are point-in-time (Nov, odd years)
and are NOT in the weekly bundles — they join by **person + year + district** (normalize names
first; election names are UPPER-CASE — **and mind the D3↔D4 renumber across 2022**).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. Remember the PC unnamed-majority
  style: on a unanimous PC motion the members are honestly **unnamed** (one placeholder row);
  named per-member rolls appear on **divided** PC votes and on Council roll calls. Do NOT read a
  blank member list on a unanimous motion as missing extraction.
- **Relational / cross-body** (PC recommendation → council outcome; member records):
  `db/civic.db` — read `db/SCHEMA.md` first; start from views `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is reconstructed +
  scored (**60 links: 24 high / 22 medium / 14 low** as-of the 2026-07-19 rebuild — the
  IDF-scored subject links are corpus-dependent, so borderline links can move a notch when
  motions are added; the 2026-07-19 four-motion recovery nudged the count +1) — respect the
  confidence column.
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind the roster drift
  (Stewart→Pierucci D1, Wells→Haymond D5, Buroker→Mayor, and the 2025-elected Johnson D3 /
  Smith D4) **and the D3↔D4 renumber**.
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–5 (the Mayor
  is citywide, never returned); an **official** current district layer plus a **pre-2022** layer
  are both retained — use the right vintage for cross-2022 questions.

## Elections — two recovered gaps + the D3/D4 hazard
- **39 races, 2007–2025** (30 general + 9 primary). The **2019 general + primary** (Cycle B:
  D1/D2/D5) and the **2021 general** (Cycle A: D3/D4/Mayor) were **recovered from the raw SOVC** —
  2019 was absent from the canonical county slice (sheet named `RIV Council N`, no `RIVERTON`
  string) and 2021 was **privacy-suppressed** at the In-Person/Vote-By-Mail method split (McCay D3
  read 0 → recovered to **863**). All winners cross-checked against outside sources
  (`VERIFICATION.md` §7): 2023 (McDougal/Haymond/Pierucci), 2025 (Buroker mayor / Johnson / Smith),
  and the 2021 recovery vs the official certified Riverton results.
- **⚠ D3↔D4 renumber (Ordinance 22-07)** is the single most important join hazard — see
  `election_results/CLAUDE.md` before joining any person to a district across 2022.

## public_comments — HONEST-EMPTY (submit-only)
Riverton publishes **no** written-comment archive. Comment is taken (1) in-person at the
meeting, (2) via **Granicus eComment** (a live per-agenda submission button — a submission
channel, not an archive), or (3) emailed in advance to the City Recorder
(`recorder@rivertonutah.gov`). None are published back. The **only** public record of a comment
is the recorder's third-person paraphrase of in-person / public-hearing speakers inside the
minutes — a **speaker log** (meeting-record notes), explicitly **not** genuine written comments,
so it does not populate `all_comments_clean.csv` (which is **header-only by design**). Treat this
as a legitimate honest zero, not a gap. See `public_comments/AVAILABILITY.md`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py` probes for meetings newer than `max(date)` in each dataset's
`minutes_index.csv` (council 1st & 3rd Tuesday; PC 2nd & 4th Thursday), fetches the born-digital
PDF from the **Utah PMN mirror** (body 5473; Granicus fallback) into `raw/`, converts →
markdown → `minutes_index.csv`, then runs the dataset's `extract_votes.py` + `validate_votes.py`.
Rebuild db + motions_std + weeks afterward. Uses a browser UA.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**
  (db `v_contested` = 136 motions, incl. 4 recovered `pmn_minutes` ones); `summary.md`
  surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see each subfolder `CLAUDE.md`);
  standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md` —
  read those before quantitative claims (especially the mayor-tie-break vote value, the PC
  unnamed-majority style, and the D3↔D4 renumber).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`).
- **`packets/`** — **3,015 rows, STORED (1.80 GB)**: 295 agenda outlines + 561 staff reports +
  1,757 exhibits on disk (2,490 text sidecars) + 402 index-only (301 oversize-capped in
  `dropped_oversize.csv`, 83 permanently-403 legistarweb 2020 exhibits, 18 duplicate bundles).
  Granicus, THREE agenda-delivery eras (S3 /URI-outline 2020-05+, GeneratedAgendaViewer early
  2020, DocumentViewer). Council 139 / PC 127 / RDA 29; 2020→2026.
  - **doc_class layer** (2026-07-16): 530 classified (staff_report 522 / development_agreement 8),
    gates 100%; staff_report-vs-exhibit kind is a filename heuristic, so the classifier scanned
    both — see packets/CLAUDE.md.
- **`housing_plans/`** — **8 rows**: General Plan (published as a single-page LAND-USE MAP, a
  small-city pattern), 2020–2024 MIH Implementation Plan, city-filed 2020/2021 forms + state
  compilation excerpts 2023/24/25 + SB34. The Oct-2019 MIH element is honestly unrecovered
  (only Wayback copy is a 1-MiB Common-Crawl truncation).
- **`ordinances/`** — **155 ordinances (2020-03→2026-06, 111 land-use)** from PMN council body
  889 "Notice of Adoption" PDFs (62 signed; code host Code Publishing eCode360, bot-gated).
  Linkage **58 high** / 93 within_source / 4 none — the within_source concentration is real:
  Riverton's PMN adoption-PDF practice only starts in 2023, so 2020–2022 adoptions are
  motion-attested but uncorroborated. Six-member-council handled (adopting motion over repeals;
  mayor tie-break-only).
- **`pmn_backfill/`** — PMN entity **251** (council 889, PC 5473, + RDA 1101, service-area
  boards, HPC, etc.). Riverton's minutes came FROM PMN, so **Granicus was the independent diff
  source** — it surfaced **3 meetings PMN never carried minutes for** (2023 council + PC) that
  the repo's PMN-derived harvest could never see, plus **3** early-2020 council (Word-format)
  + a recent PC date = **7 recovered**. Both core bodies now complete-superset.
  **PROMOTED 2026-07-16** into the audited vote layer (`provenance=pmn_minutes`; 34 council +
  10 PC motions via each dataset's `extract_backfill_votes.py`). Granicus
  MinutesViewer wraps the PDF in a gview HTML shell (needs a second hop to DocumentViewer);
  2015–early-2020 era serves Word `.doc/.docx`.
- **`transcripts/`** — Granicus video-complete (**652 clips catalogued**, back to 2015-09;
  Council 263 / PC 214) but caption-less (empty 40-byte stubs). Riverton is the FIRST city the
  "Utah Record" mirror does NOT carry — the only sanctioned caption is one 2018 council meeting
  (below floor, kept as a bonus). In-scope window is Whisper-only (candidates proposed; MP4
  URLs in `granicus_clips.csv`).
- **`campaign_finance/`** — **60 filings, 2021/2023/2025 — complete per ballot candidate**.
  Methodological note: the city page and `disclosures.utah.gov/municipal` were each INCOMPLETE
  alone (the state folder tree uniquely held the 2023 interims) — merging the two publishers
  gave full coverage. 30 text / 30 scanned; acquisition only. 3 declared-then-withdrew
  candidates flagged (absent from SOVC — election-record notes, not edits). Mind the D3↔D4
  renumber + council→mayor moves when joining (person-key, not district number).
