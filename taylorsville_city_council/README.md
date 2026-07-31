# Taylorsville City Council — data repository

A Salt Lake City-style civic-data repository for the **Taylorsville City Council**, **Planning
Commission**, and **Redevelopment Agency (RDA)** (Salt Lake County, Utah; ~60k pop.; incorporated
1996), built 2026-07-06 by the `build-city-data-repo` skill. Council + RDA + PC minutes (as
markdown), extracted roll-call votes, a relational cross-body db, public-comment availability,
municipal election results, and an address→district tool — all as markdown/CSV. See `CLAUDE.md`
for analysis guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in
`VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + RDA minutes | 2020-01-08 → 2026-06-03 | **150 md** (== 150 index) | CivicEngage Central (agendas-minutes landing) | ✅ complete; 126 `pdf-text` + 24 `ocr` (mid-2025 RICOH scans); 2 honestly unrecovered (2026-06-17 not-yet-posted, 2026-07-01 CANCELLED) |
| Council + RDA votes | 2020–2026 | **613 motions** (605 Council + 8 RDA) · **2,457 vote rows** (2,315 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; **mayor NON-voting** (max tally 5); narrative-tally — unanimous majorities honestly unnamed, contested/RDA rolls named |
| PC minutes | 2020-01-14 → 2026-04-28 | **91 md** (== 91 index) | CivicEngage Central (PC minutes landing) | ✅ complete; 60 `pdf-text` + 31 `ocr`; 0 unrecovered |
| PC votes | 2020–2026 | **324 motions** (58 recommendations · 81 final actions · 185 procedural) · **961 vote rows** (761 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; **three vote formats** (narrative-tally → named-inline → tabular) all parse; 5 "No recorded vote" honest |
| Relational db (`db/taylorsville.db`) | 2020–2026 | **937 motions** · **3,076 votes** · **28 PC→Council referrals** (7 high / 15 med / 6 low) | standard cross-city schema | ✅ reconciles exactly (3,076 named CSV rows == 3,076 db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md only** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive; comment is in-person/livestream. `all_comments_clean.csv` deliberately not built |
| Election results | 2007 → 2025 | **39 races** (32 general + 7 primary) · candidate + precinct tables | Salt Lake County canonical SOVC (`salt_lake_county/elections/` + raw 2019/2021 re-parse) | ✅ verified; 2019 general RECOVERED; 2019 D1 primary ADOPTED 2026-07-19; all races match outside sources |
| Geo (address→district) | current / post-2020 | **44 precincts → Districts 1–5**; derived district polygons | precinct-derived (no official layer; UGRC CountyID 18) | ✅ tool + geojson present; **PRECINCT-DERIVED, current/post-2020-census vintage** |
| Weekly bundles | 2020–2026 | **144 week bundles** | derived (`build_weeks.py`, Monday grid) | ✅ regenerable; weekly vote sum 2,457 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 613 / PC 324 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor does NOT vote
**Council–mayor (executive-mayor) form:** five district councilmembers (D1–D5) legislate; a
separately-elected **Mayor is the executive** who appoints the City Administrator and presides
over the city but **casts no council vote**. The council **elects its own Chair/Vice-Chair** to
run meetings, so the presiding "Chair" is always one of the five members (a `Chair <Name>` roll
entry maps to that councilmember). **Max council roll-call tally = 5**; Mayor **Kristie Overson**
appears in **0** vote rows.

**Roster of 7 (join carefully):** current — **Ernest Burgess** (D1), **Curt Cochran** (D2),
**Anna Barbieri** (D3), **Meredith Harker** (D4), **Bob Knudsen** (D5). Former members who vote
in the early record — **Brad Christopherson** (D3, 2020 only) and **Dan Armstrong** (D5,
2020–2021). Barbieri succeeded Christopherson mid/late 2020 (then won the 2021 D3 special);
Knudsen succeeded Armstrong from 2022. **Barbieri also sits on the Planning Commission early on**
(one `person`, two `role` rows). Terms are 4-year staggered, non-partisan: **D4/D5/Mayor** on
2017/2021/2025; **D1/D2/D3** on 2019/2023.

### RDA — an in-record body
The Council convenes as the **Taylorsville Redevelopment Agency** board (in-meeting recess). RDA
open votes live in `meeting_minutes/` tagged `body=RDA` (**8 motions**, `stage=rda_vote`); the
same councilmembers appear as "Board Member <Name>". No separate RDA portal files exist.

## Distinctive Taylorsville facts (read before quantitative claims)
- **Narrative-tally minutes — unanimous majorities are honestly UNNAMED.** Motions record
  mover + seconder + a narrative outcome ("passed unanimously on a roll call vote"); a genuine
  roll call is taken but the printed minutes give the tally, not each Aye. The parser leaves
  ayes unnamed (`names_recorded:false`) rather than guessing — **it does NOT Present-fill**.
  Named per-member rows appear on **contested** motions and on the **RDA / PC named-roll**
  formats. A blank member list on a unanimous motion is a source style, not an extraction miss.
- **Three PC vote formats.** The Planning Commission's grammar evolved **narrative-tally
  (2020–21) → named-inline (2023) → tabular (2024-12+)**, all handled by the PC extractor.
- **Mid-2025 RICOH-OCR switch.** Taylorsville moved minutes production to scanned RICOH output
  mid-2025 → recent minutes are image-only PDFs (**24 council + 31 PC** files `format=ocr`).
  OCR is clean; the corpus screener found **0 fabricated names** (incl. all OCR files).
- **Case-number bridge is one-sided.** PC files land-use cases as `<SEQ><LETTER><YY>` (e.g.
  `15Z19`, `29C20`); Council/RDA are ordinance/resolution-keyed and cite **0** PC case numbers.
  So the strongest key can't link PC→Council — every cross-body referral falls to
  address + subject + temporal (28 links; only 7 high-confidence).
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **2 unrecovered council meetings** (both 2026, past the current data max): 2026-06-17 (minutes
  not yet approved/posted — only the agenda exists) and 2026-07-01 (meeting CANCELLED; the portal
  doc is a 1-page cancellation notice). Logged in `meeting_minutes/minutes_unrecovered.csv`,
  never stubbed. PC has **0** unrecovered.
- **Elections:** county-administered; only Taylorsville council + mayor races included. Built
  directly from the **county canonical** (`salt_lake_county/elections/`, re-pointed 2026-07-19);
  **2019 & 2021 generals re-parsed from the retained raw SOVC** (the canonical carries the 2019
  general only under the sheet code `TAY Council N`, and privacy-suppresses the 2021 method split).
  **A 2019 District 1 primary WAS held (Burgess/Gehrke/Quigley) — ADOPTED 2026-07-19**, correcting
  the prior "no 2019 primary" claim. **2021 District 3 is a special/unexpired-term** race, flagged
  in `note`.
- **Geo is precinct-derived, current/post-2020-census vintage** — no official city district
  layer exists; pre-2022 addresses near a moved boundary may mis-assign. See `geo/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Taylorsville-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each layer
- **Council + RDA votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Geo:** `cd geo && python3 build_precinct_district_map.py` (derives the precinct→district map
  + polygons from the SOVC precinct rows).
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`CITY="Taylorsville"`, `MEETING_WEEKDAY=2` →
  Wednesday). `weeks/` and `db/` are **derived** — regenerate, never hand-edit; rebuild weeks/
  after any change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists CivicEngage Central Minutes-folder items newer than the
index max for each dataset (council agendas-minutes landing; PC minutes landing), excluding
dates already indexed or in `minutes_unrecovered.csv`, plus a read-only PMN (council body 720)
cross-check; `--fetch [--dataset …]` downloads new docs → `raw/` → markdown (OCR-aware) →
`minutes_index.csv`, then extracts + validates. Rebuild db + motions_std + weeks afterward (the
CLI prints the reminder). Idempotent + resumable. The site 403s bare bots — the script uses a
browser+archive UA (verified live).

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.

## Expansion datasets (additive, 2026-07-06)
Six additional source layers built by `expand-city-sources`, each documented in its own
folder (`CLAUDE.md` + `AVAILABILITY.md`) and each individually passing `validate_dataset.py`.
**None modify the core minutes/votes/comments/elections layer.** Join to
`all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **7 current-cycle documents** (June–July 2026). **Honest publishing gap:**
  Taylorsville posts staff-report packets on three dedicated **current-cycle-only** widget
  pages (council-packet / planning-commission-packet / rda-board-packet) that staff overwrite
  each cycle — **there is no historical packet archive** (the Agendas-&-Minutes year folders
  hold thin agenda outlines, not staff-report bundles). 2020–2026 packets are unrecoverable
  from the portal; only the live snapshot was captured (joins by date to just the 2026-06-03
  Council meeting). Wayback is the sole possible partial-recovery lead (logged).
- **`housing_plans/`** — **14 docs**: the **2025 General Plan** (9 per-chapter PDFs — no single
  consolidated file), the **MIH element** (General Plan **Chapter 8** + the standalone adopted
  **Ordinance 23-03**, PASSED **Feb 1 2023**, PC recommended 6-0 Jan 24 2023 — linkage confirmed
  to the vote layer), and the state DWS/HCD MIH compilations (**2023/24/25** + the **SB 34**
  summary, sliced to Taylorsville's per-city page ranges, grep-verified for zero adjacent-city
  bleed). City docs from `taylorsvilleut.gov`; state from `jobs.utah.gov` HCD. Document dataset;
  not joined to `db/`.
- **`ordinances/`** — **90 adopted ordinances (2020+)** linked to the council motion that passed
  each. Confidence **75 high** (number cited in an adopted motion **and** an independent PMN PDF
  exists) / **9 medium** (signed PMN adopted PDF but the number is absent from the motion text) /
  **6 within_source** (motion-cited but no independent PDF — `high` by construction, NOT a
  cross-match). **71% land-use** (64/90). Source is **Utah PMN council body 720** signed "Newly
  Adopted Ordinance" PDFs (American Legal 403s + is consolidated-text only; municipalcodeonline
  has no Taylorsville client). **Parallel ordinance/resolution number sequences** —
  `Ordinance NN-NN` ≠ `Resolution NN-NN`; keyed on instrument word + number. A ~129-doc
  **2012–2019 back-catalog** exists on the same PMN body, out of scope (below the 2020 floor).
- **`pmn_backfill/`** — Utah PMN cross-check (council 720 / PC 722 / RDA 721). **2 genuinely-
  missing meetings recovered** — the **2020-01-29** and **2024-01-31** *Let's Talk Taylorsville*
  5th-Wednesday town halls (non-standard, no roll-call votes). **PC = 0 gaps, RDA = no separate
  docs** (in-recess with council), 4 false positives resolved. Plus **15 OCR-upgrade candidates**
  (`ocr_upgrade_candidates.csv`): meetings the repo holds only as RICOH scans for which PMN has a
  born-digital text PDF — **flagged, NOT merged** (do not replace `meeting_minutes/` files in
  place; a deliberate human follow-up).
- **`transcripts/`** — **audio-only honest gap.** Taylorsville streams meetings live but does
  **not** archive them as video; `youtube.com/taylorsvillecity` is **141 PR/event videos**
  (mapped in `channel_map.csv`), with exactly **1** genuine meeting video (a 2024-05-15 PC
  livestream) whose ASR caption is the single sample retrieved. **Whisper was NOT run.** No
  deliberation-transcript corpus; not an official record. OpenUtah (`taylorsville.openutah.org`,
  ~8 transcribed, robots-limited) and Whisper-over-city-audio are the future routes.
- **`campaign_finance/`** — **71 filings** / Mayor + 5 district seats, 2017–2026,
  100% joined to `election_results`. **TWO regimes:** mandatory **annual** March-1 statements
  (**50** — every sitting official files yearly, even off-cycle) + **election-cycle** filings
  (**21**, 2021 & 2023). **ACQUISITION LAYER ONLY** — 43 scanned / 28 born-digital,
  `extraction_method=none`; **do NOT sum filings** (candidates file multiple reports/cycle;
  dollar structuring deferred). Honest gaps: **2019 and 2025 election-cycle filings unposted**
  (not Wayback-recoverable).
