# South Salt Lake City Council — data repository

Canonical datasets about the South Salt Lake City Council, Redevelopment Agency (RDA), and
Planning Commission (Salt Lake County, Utah; ~26k pop.; incorporated 1938), modeled on the
Salt Lake City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built
by the `build-city-data-repo` skill. Data floor: **2020** (SSL is old; 2020 is a normal floor,
not an incorporation edge like Millcreek).

```
meeting_minutes/      City Council + RDA minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only; no published
                      written-comment archive) — all_comments_clean.csv is header-only by design
election_results/     Salt Lake County SOVC filtered to SSL council+mayor races (2011/2019/2021
                      recovered from raw sheets)
geo/                  SSL's OWN official 5-district ArcGIS polygons + address/point → district
db/                   relational SQLite (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday)
fetch_new.py          incremental refresh driver — probes PMN bodies 1295/1296/1297,
                      content-detecting recorded minutes vs agenda packets
.harvest/             the bulk PMN harvester (harvest_minutes.py + build_index.py) + logs
recon.md              provenance map written BEFORE acquisition (portal, URL patterns, gaps)
COVERAGE.md           the coverage story — READ FIRST for any quantitative claim
VERIFICATION.md       independent QA + external election cross-check
```

## ⚠ The one structural fact that governs this city — the coverage cliff (REVISED 2026-07-16)
SSL's PMN **"Meeting Minutes" slot very often serves the AGENDA PACKET** (no roll call) *even
when the file is labelled `… RC Minutes.pdf`* — that part of the original story is verified and
permanent. But the city's CivicPlus AgendaCenter hides genuine recorded roll-call minutes in a
**hidden `ArchivedMinutes` previous-version slot** (the visible *Minutes* slot serves the
packet). The 2026-07-13 `pmn_backfill/` sweep recovered them and on **2026-07-16 119 verified
docs (2022–2026) were PROMOTED into the audited layer** (Council 75 / RDA 29 / PC 15; 11 of the
130 recovered were rejected — 2 agenda packets, 9 duplicates of audited meetings).
**Content-detection is still the whole ballgame — portal labels lie** (most recovered files
labelled "work meeting" are REGULAR-meeting minutes; one "RDA"-slot file is council minutes).

**Net effect now:** the audited layer holds **95 council + 43 RDA + 60 PC** minutes; council
regulars are well covered 2020–early-2021 and **2022-09 → 2026-06**; **PC minutes begin
2022-01-20** (2020–2021 PC genuinely unpublished — the AgendaCenter PC listing starts 2022).
The honest residual is **221** agenda-only meetings (dominated by **council WORK meetings,
117** — those genuinely go unpublished — plus mid-2021→mid-2022 council regulars, 19 RDA
dates, and **24 PC** — incl. 8 genuine 2022 PC agenda-only dates logged 2026-07-17 after a
ledger cross-check), in each dataset's `minutes_unrecovered.csv`. That residual is data, not a
scraper miss.
Vote rows carry a **`provenance`** column (`minutes` = PMN-harvested, `agendacenter_minutes` =
promoted recoveries). Read `COVERAGE.md` before any quantitative claim.

## The structural facts that make South Salt Lake different
1. **Strong-mayor form — the MAYOR does NOT vote.** A **7-member council = 5 districts (1–5) +
   2 At-Large**, plus a separately-elected **executive Mayor** (runs the administration, casts
   no council vote). The council **elects its own Chair** (currently **Sharla Bynum, D3**) to
   preside — a `Council Chair <Name>` in a roll maps to that councilmember, never a separate
   person. A full council/RDA roll tops out at **7** (never 8). **Mayor Cherie Wood** appears
   in **0** vote rows (she only *presents* items) and is absent from the db `person` table —
   verified against a real 2026-06-10 roll call. Matches South Jordan/Taylorsville's
   mayor-uncounted practice.
2. **Roster evolves 2020 → 2026 (observed, nothing hard-coded).** The 2020 seven (Bynum,
   deWolfe, Thomas, Huff, Mila, Pinkney, Siwik) is a different body from the 2026 seven (Glad,
   Thomas, Bynum, Mitchell, Jones, Williams, deWolfe). ⚠ **D1/D5 are mid-term appointees in
   2026** — *elected* 2023 winners were **Huff (D1)** and **Sanchez (D5)**; *serving* 2026
   members are **Glad (D1)** and **Jones (D5)**. Join by person carefully across years.
3. **RDA is a separate PMN body (1296), same board.** The Council convenes as the SSL RDA the
   same Wednesday (6:15 p.m.); the board is the seven councilmembers, Mayor = non-voting
   Executive Director. RDA open votes are tagged `body=RDA` (**125 motions** since the
   2026-07-16 promotion) in the council CSV. The 2023–24 RDA clerk prints colon-less rolls
   ("Bynum   Yes") and January officer elections are often by acclamation (no vote — honestly
   uncaptured).
4. **`result` is SYNTHESIZED.** SSL prints **no** "motion passed" string, only a per-member
   roll call, so `result` = the computed **`<aye>-<nay> Pass|Fail`** from the roll
   (abstains/absents excluded from the count; e.g. 5-Aye/1-Abstain → `"5-0 Pass"`). It is
   *derived from* the recorded votes, honest, not invented — `validate_city.py`'s `f.tally`
   confirms 100% of synthesized tallies equal the counted member rows.
5. **Named per-member roll calls throughout** (`names_recorded` almost always true) — SSL is
   NOT a narrative-tally city. Council formats: **Roll Call Vote** / **Voice Vote**, both
   listing all 7 members `Name: Yes/No/Not Present`. PC grammar differs:
   `Commissioner <Name> – Aye;` under a `Vote:` header (its own commissioner roster, up to 8);
   a few procedural PC motions are tally-only, captured with one placeholder row (no fabricated
   members). A faithful clerk typo — `Oliva`/`Olivia Spencer` — is retained as a PC-roster
   near-duplicate, not merged.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` **+ documented
  extension cols `body,meeting_kind,pmn_file`** (this city stores Council + RDA in one dataset,
  so `body` walks them; `meeting_kind` ∈ RC/WM/SM/BoC/TT; `pmn_file` = the PMN attachment id,
  blank for AgendaCenter recoveries). One row per document on disk; unrecoverable meetings live
  in `minutes_unrecovered.csv` (`date,body,meeting_kind,reason`), never as stub/wrong-doc rows.
  `source ∈ pmn | agendacenter` (the 2026-07-16 promoted recoveries), `format=pdf-text`
  (born-digital, no OCR).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ the documented trailing `provenance` column** (`minutes` = PMN-harvested audited primary;
  `agendacenter_minutes` = the 2026-07-16 promoted ArchivedMinutes recoveries — fully audited,
  same parser/validators);
  `result` (synthesized) and `motion_type` are city-native — **cross-city comparison goes
  through `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- Raw minutes-bearing originals are retained under each dataset's `raw/` and never deleted
  (pure-agenda packets are NOT retained — a future `packets/` layer).

## The join key
Everything keys to the **council/RDA meeting weekday (Wednesday** — 2nd & 4th; a 6:30 p.m. Work
Meeting + a 7:00 p.m. Regular Meeting, plus the 6:15 p.m. RDA, each a separate PMN attachment).
The **PC meets Thursday** (~1st & 3rd); its records join on their own date. `build_weeks.py`
buckets every council/RDA record onto the Monday grid. Elections are point-in-time (Nov, odd
years) and are NOT in the weekly bundles — they join by **person + year + district** (normalize
names; election names are UPPER-CASE with `(NP)` suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. **Mind the (smaller) residual
  cliff**: council vote volume still dips mid-2021→mid-2022 and work-meeting minutes are mostly
  unpublished. Weight per-year council counts by `minutes_index.csv` coverage; the `provenance`
  column separates the PMN-era corpus from the 2026-07-16 recoveries.
- **Relational / cross-body** (member records; PC→Council referrals): `db/civic.db` —
  read `db/SCHEMA.md` first; start from `v_member_record`, `v_contested`, `v_project_timeline`.
  The **`referral` layer holds 43 links since the promotion** (40 Council←RDA, 3
  Council←PlanningCommission, all `medium` subject-matches) — still thin on the PC side because
  2020–2021 PC minutes don't exist; don't infer "PC never influenced Council" from a missing link.
- **Meeting-level / contextual**: the `weeks/<Wednesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind the roster drift and
  the D1/D5 elected-vs-serving appointment nuance (above).
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–5; the 2
  At-Large seats and the Mayor are city-wide (returned as context, not point-resolved).

## Elections — recoveries + one special
**52 races, 2007–2025.** **2011 & 2019** generals+primaries were **re-parsed from the raw SOVC**
(the archive normalizer keyed the contest off sheet names that omitted "South Salt Lake", so a
city-string filter missed them — same failure mode as Taylorsville/South Jordan/Millcreek 2019).
**2021** was re-parsed to undo privacy-suppression, and **⭐ 2021 is an RCV-PILOT year** —
SSL joined Utah's 2021 Municipal Alternate Voting Methods pilot, proved by the Clerk's
*Official Final Ranked Choice Results* (`election_results/raw/2021-general-election-ranked-
choice-summary-report.pdf`, p.20 = `CITY OF SOUTH SALT LAKE MAYOR`). All four 2021 rows carry
`voting_method='RCV'` (**corrected from `plurality` on 2026-07-31**; no tally changed). Round 1
was decisive in every SSL contest — Wood cleared the 1,526 majority threshold outright, the
three council contests had 2 candidates each — so unlike Draper/Millcreek 2021 the stored
winners/pcts/margins **are** the RCV finals and can be quoted directly. **Corollary: there was
no Aug-2021 SSL primary and none is missing** — the pilot replaces the municipal primary (the
county's 2021 primary publication holds 6 contests, all non-pilot cities).
**2025 ran an off-cycle "At-Large (2-Year
Term)" special** (`district='At-Large-2yr'`) — Pinkney (At-Large) left for the county council,
deWolfe was appointed Jan-2025 then won the special — kept as its own contest so member-term
logic doesn't misread it as a cycle shift. Winners cross-checked against outside sources in
`VERIFICATION.md`.

## public_comments — HONEST-EMPTY (submit-only)
SSL publishes **no** standalone written-comment archive / eComment / correspondence page.
Comment is taken in-person, over Zoom, and via the connect line `connect@sslc.gov` /
801-464-6757; minutes carry a `Public Comments/Questions` item + an `OTHERS PRESENT` list
(meeting-record speaker notes, **not** written comments). `all_comments_clean.csv` is
header-only by design — see `public_comments/AVAILABILITY.md`. A legitimate honest zero, not a
gap.

## Geo — SSL's OWN official layer (better than the precinct-derived cities)
The 5 council-district polygons come from **South Salt Lake's own official ArcGIS
FeatureServer** ("South Salt Lake City Council Districts") — the authoritative whole-city
boundary layer, no precinct-derivation needed. Current / post-2020-census vintage; pre-2022
addresses near a moved boundary may mis-assign. At-Large (2) + Mayor are city-wide (no polygon).
See `geo/CLAUDE.md`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default, read-only) lists PMN meeting dates newer than the
per-dataset index max for council (body 1295), rda (1296) and pc (1297), excluding dates
already indexed or logged unrecovered; writes `refresh_probe.json`. `--fetch [--stream
council|rda|pc]` downloads each new date's candidate PDF(s) → `raw/`, **content-detects**
minutes vs an agenda packet (the whole SSL ballgame — a labeled "Minutes" file is often an
agenda), writes markdown → `minutes_index.csv` (or logs the gap), then extracts + validates.
Rebuild db + motions_std + weeks + `cities.db` afterward (the CLI prints the reminder).
Idempotent + resumable. `.harvest/harvest_minutes.py` remains the full-re-harvest tool.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**
  (db `v_contested` = **68**: Council/RDA 56, PC 12 — recounted 2026-07-16 after the
  ArchivedMinutes promotion quintupled the corpus; before it the count was 12);
  `summary.md` surfaces them per week. Residual quirks: a few ADJOURN vote blocks are
  physically cut mid-roll by appended STAFF REPORT attachments (honest 2-0/3-0 tallies);
  two clerk-typo vote values ("Huff: Ye" 2024-02-28 RDA m2, "Huff: Y/es" 2026-01-14
  Council m3) leave that member honestly unrecorded in the flat CSVs — the db carries the
  corrected `Aye` via documented add-member `db/vote_overrides.csv` rows (2026-07-17);
  2022-10-26 advice-and-consent items
  print "VOTE: All present in favor" with a blank YES/NO table → captured tally-only.
- Motion types: city-native taxonomy in `all_votes.csv`; standardized categories in
  `motions_std.csv`; never aggregate raw `result`/`motion_type` across cities.
- Coverage seams + known gaps are documented in `README.md`, `COVERAGE.md`, `recon.md`, and
  `VERIFICATION.md` — read those before quantitative claims (especially the coverage cliff, the
  synthesized `result`, and the D1/D5 elected-vs-serving nuance).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`).

✅ **The ArchivedMinutes recovery was PROMOTED into the audited layer 2026-07-16** (see the ⚠
section at the top and `COVERAGE.md`): of the 130 recovered minutes, **119 verified docs were
promoted** (Council 75 / RDA 29 / PC 15 — content-verified body/kind, several portal labels
corrected) and **11 rejected** (2 agenda packets, 9 duplicates of audited meetings) via
`pmn_backfill/promote_to_audited.py`. The recovery **refuted "PC minutes begin 2023-01-19"**
(PC now starts 2022-01-20). Honest residual: **221** agenda-only meetings (mostly council work
meetings; 2020–2021 PC genuinely absent). `pmn_backfill/` remains the recovery-provenance
dataset; the promoted copies live in the audited `minutes/` layers with
`source=agendacenter` / `provenance=agendacenter_minutes`.

- **`packets/`** — **429 packets INDEX-ONLY (3.37 GB)** from the AgendaCenter (Council 197 / PC
  116 / RDA 50 [reaches 2020] / CRB 66; 2020/2022→2026). This is the layer the core deferred
  (the AgendaCenter "Minutes" slot serves these packets). Use the **`?packet=true`** endpoint —
  the plain `/ViewFile/Agenda/` link is sometimes a thin outline; `?packet=true` assembles the
  full packet and is always ≥ the plain slot.
- **`housing_plans/`** — **8 rows**: 2021 "General Plan 2040" + Market Analysis appendix, 2016
  standalone MIH element, 2023 MIH Plan & Needs Assessment (the current MIHP — city page
  mislabels it), + 4 state excerpts (SSL present all years).
- **`ordinances/`** — **114 rows (100 Municode-enumerated 2020–2026; 39 land-use)** via the
  **Municode NEXT API** (`api.municode.com`, GET-only) COCOTADILI disposition table — an
  authoritative minutes-INDEPENDENT number→date→subject map. Linkage 0 high (SSL motions cite
  ordinances by SUBJECT, never by number) / 1 medium (cited code-section match) / 96 none (the
  coverage cliff — no recorded adopting motion) / 14 within_source (2026 budget ordinances). PMN
  1295 is minutes-only, NOT an ordinance archive.
- **`pmn_backfill/`** — PMN entity **271** (all bodies swept; 1295 council / 1296 RDA / 1297 PC).
  **130 recorded minutes recovered from the AgendaCenter `ArchivedMinutes` slot** (119 promoted
  into the audited layer 2026-07-16 — see the ✅ above) — `source=agendacenter`,
  `recovery_source` column. PMN cliff-confirmation: the core
  missed no in-scope PMN minutes (the >22 MB skipped council files are all agenda packets).
  CRB (27) + Arts Council minutes are non-governance (out of scope).
- **`transcripts/`** — YouTube `@SouthSaltLakeCity` (`UCnIf0PqrH3cERoBB-vyhrbA`): **269 meeting
  videos 2022-12→2026-07** (Council 134 / PC 60 / RDA 29 / CRB 46), **100% ASR captions** (all
  269 ground-truthed), 10 samples fetched. Lands squarely on the cliff — for the 160 gap-year
  (2023–25) Council+PC videos, the ASR caption is often the only substantive record (caveat: not
  a roll-call/tally). yt-dlp trap: default/web clients hit the PO-token wall and FALSELY report
  no captions — use `--js-runtimes node --extractor-args youtube:player_client=android`.
- **`campaign_finance/`** — **68 filings, 2021/2023/2025 complete per ballot roster** (+ bonus
  2026 council-vacancy applicant filings + 8 COI). 14 text / 54 scanned; acquisition only. ~~FLAG:
  the filings prove a **3-way 2021 mayoral primary** (Wood/Christensen/Siwik) that
  `election_results` doesn't list.~~ **RESOLVED 2026-07-17 (SOVC re-parse):** the filings
  prove a 3-way RACE, not a primary — SSL was in the 2021 RCV pilot, so all three advanced
  directly to the ranked general (audited); no primary was held or is missing. **Re-verified
  at the primary source 2026-07-31** — the 2026-07-17 note asserted the pilot without citing a
  document; the Clerk's Ranked Choice Results report (now retained in `election_results/raw/`)
  names SSL Mayor on p.20, and the 2021 rows are relabelled `RCV` accordingly. CF lives on
  the CivicPlus Archive Center (`Archive.aspx?ADID=`
  → `/ArchiveCenter/ViewFile/Item/`, not DocumentCenter).
