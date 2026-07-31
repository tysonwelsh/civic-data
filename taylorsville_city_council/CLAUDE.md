# Taylorsville City Council — data repository

Canonical datasets about the Taylorsville City Council, Planning Commission, and
Redevelopment Agency (RDA), modeled on the Salt Lake City reference repo and conforming to
the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with
`scripts/validate_city.py`). Built by the `build-city-data-repo` skill. Data floor: **2020**
(Taylorsville incorporated **1996** — full modern history exists; 2020 is a normal floor,
not an incorporation edge like Millcreek).

```
meeting_minutes/      City Council + RDA minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + fetch_new.py refresh
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only; no published
                      written-comment archive) — no all_comments_clean.csv by design
election_results/     Salt Lake County results filtered to Taylorsville council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
db/                   relational SQLite (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday = 2)
fetch_new.py          incremental refresh driver (CivicEngage Central + PMN cross-check;
                      probes BOTH datasets — see "Keeping it current")
recon.md              map of this city's data sources (provenance) — written BEFORE
                      acquisition; portal vendor, URL patterns, and the honest-gap record.
                      ⚠ its Minutes folder ids were off by one column — corrected in
                      fetch_new.py + meeting_minutes/CLAUDE.md
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extended
                      with dated addenda whenever the data is repaired or re-audited)
```

## The structural facts that make Taylorsville different
1. **The MAYOR does NOT vote.** Taylorsville uses Utah's **council–mayor (executive-mayor)
   form**: five district members (D1–D5) legislate, and a separately-elected **Mayor is the
   executive** (appoints the City Administrator, gives updates) who **presides over the city
   but not the council and casts no vote**. The council **elects its own Chair/Vice-Chair**
   to conduct meetings, so the presiding "Chair" is always **one of the five councilmembers**
   — a `Chair <Name>` in a roll call maps to that member, never to a separate person. A full
   council roll call therefore tops out at **5** (never 6). Mayor **Kristie Overson** appears
   in **0** vote rows and is absent from the db `person` table. This differs from Millcreek
   (mayor votes, tally 5 incl. mayor) and matches South Jordan's mayor-uncounted practice.
   See `meeting_minutes/CLAUDE.md`.
2. **Roster of 7, not 5.** The five current members — **Burgess (D1), Cochran (D2), Barbieri
   (D3), Harker (D4), Knudsen (D5)** — plus two former members who really vote in the early
   record: **Brad Christopherson (D3, 2020 only)** and **Dan Armstrong (D5, 2020–2021)**.
   Barbieri succeeded Christopherson mid/late 2020 (then won the 2021 D3 special); Knudsen
   succeeded Armstrong from 2022. **Anna Barbieri also sits on the Planning Commission early
   on** — she is a single `person` with two `role` rows, so a person-level join spans both
   bodies by design. Join carefully across years.
3. **RDA is an in-record body, not a separate portal.** The Council convenes as the
   **Taylorsville Redevelopment Agency** board (in-meeting recess). Its open votes are tagged
   `body=RDA` (**8 motions**, `stage=rda_vote`) in the council CSV; "Board Member <Name>" =
   the councilmembers. There are no separate RDA portal files to acquire.
4. **Three PC vote formats + a mid-2025 OCR seam.** The Planning Commission's vote grammar
   evolved **narrative-tally → named-inline → tabular** across 2020→2026, all handled by its
   extractor. And Taylorsville switched minutes production to **RICOH scans mid-2025**, so
   recent minutes are OCR (**21 council + 28 PC** files, `format=ocr`, after the 2026-07-12
   PMN born-digital promotion of 3 council + 3 PC meetings — see `pmn_backfill/CLAUDE.md`).

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` = `civicplus` (council) / `civicengage` (PC) — same
  CivicEngage Central CMS, two labels the two extractors emit. `format` ∈ `pdf-text`/`ocr`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Wednesday** — 1st & 3rd Wednesday, a 6:00
PM Briefing + a 6:30 PM Regular meeting captured in **one combined minutes doc** per
meeting-day). The **PC meets Tuesday** (2nd & 4th); its records join on their own date.
`build_weeks.py` buckets every record onto the Monday grid (`MEETING_WEEKDAY = 2`). Elections
are point-in-time (Nov, odd years) and are NOT in the weekly bundles — they join by
**person + year + district** (normalize names first; election names are UPPER-CASE, some
non-partisan suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. Remember these are
  **narrative-tally** minutes: on a unanimous council motion the majority is honestly
  **unnamed** (mover + seconder are named; a genuine roll call is taken but the printed
  minutes give the tally, not each Aye). Named per-member rolls appear on contested motions
  and on the RDA/PC named-roll formats. Do NOT read a blank member list on a unanimous
  motion as missing extraction.
- **Relational / cross-body** (PC recommendation → council outcome; RDA co-actions; member
  records): `db/taylorsville.db` — read `db/SCHEMA.md` first; start from views
  `v_referral_chain`, `v_project_timeline`, `v_member_record`, `v_contested`. The `referral`
  layer is reconstructed + scored (**28 links: 7 high / 15 medium / 6 low**) — respect the
  confidence column. **The case-number bridge is one-sided** (PC land-use cases key
  `<SEQ><LETTER><YY>`; Council/RDA are ordinance/resolution-keyed and cite 0 PC case numbers),
  so every cross-body link falls to address + subject + temporal.
- **Meeting-level / contextual**: the `weeks/<Wednesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind the roster drift —
  **Christopherson → Barbieri (D3, 2020)** and **Armstrong → Knudsen (D5, 2022)**.
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–5 (the
  Mayor is citywide, never returned).

## Elections — recovered gap + adopted primary + one special
- **39 races, 2007–2025** (32 general + 7 primary). Built **directly from the Salt Lake
  County canonical** (`salt_lake_county/elections/slco_municipal_results_long.csv`) —
  re-pointed 2026-07-19, per-city archive slice retired (re-point proven byte-identical bar
  the adopted primary below). The **2019 general (D1/D2/D3)** and **2021 general** are still
  re-parsed from the retained `election_results/raw/sovc/*.xlsx` (the canonical carries the
  2019 general only under the sheet code `TAY Council N`, and privacy-suppresses the 2021
  method split); all match the city's certified results.
- **A 2019 District 1 primary WAS held (adopted 2026-07-19).** D1 drew 3 candidates
  (Burgess 728 / Gehrke 371 / Quigley 229) → primary; the county canonical carries it,
  cell-verified vs the raw workbook, top-2 = the D1 general's two candidates. Corrects the
  prior "no 2019 primary" claim (the retired archive slice had dropped the whole 2019
  Taylorsville set). See `election_results/CLAUDE.md`.
- **2021 District 3 is a SPECIAL/unexpired-term race** (Barbieri, uncontested), running off
  its normal 2019/2023 cycle — flagged in the `note` column so member-term logic doesn't read
  it as a cycle shift. Winners cross-checked against outside sources (City Journal, Tribune,
  certified results) in `VERIFICATION.md`.

## public_comments — HONEST-EMPTY (submit-only)
Taylorsville publishes **no** standalone written-comment archive / eComment / correspondence
page. Public comment is taken in-person at meetings and via livestream; minutes carry an
`Others Present:` attendee list and paraphrased hearing-speaker notes (meeting-record speaker
notes, **not** genuine written comments). `all_comments_clean.csv` was **deliberately not
built** — the SUBMIT-ONLY verdict is documented in `public_comments/AVAILABILITY.md`. Treat
this as a legitimate honest zero, not a gap.

## Geo — PRECINCT-DERIVED, no official layer (vintage caveat)
No standalone Taylorsville council-district FeatureServer exists. The **44 precinct → District
1–5** map and district polygons were **derived** from the 2023/2025 SOVC precinct rows over
Salt Lake County precinct geometry (UGRC CountyID 18) — see `geo/CLAUDE.md`. These are the
**current / post-2020-census** boundaries (5 districts, "0% deviation" redistricting); an
address near a moved boundary may mis-assign for **pre-2022** questions. `--latlon`
point-in-polygon works offline; address-geocode mode needs network.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists CivicEngage Central Minutes-folder
items newer than the index max for each dataset — council + RDA (agendas-minutes landing) and
PC (planning-commission-meeting-minutes landing) — excluding dates already indexed or logged
in `minutes_unrecovered.csv`, plus a read-only PMN (council body 720) cross-check.
`--fetch [--dataset meeting_minutes|planning_commission]` downloads each new date's candidate
doc(s) → `raw/`, resolves the genuine minutes doc (a council date lists BOTH its agenda and
its minutes under the same label — the fetch keeps the one with recorded motion prose, drops
agendas/cancellations), converts OCR-aware → markdown → `minutes_index.csv`, then runs the
dataset's `extract_votes.py` + `validate_votes.py`. Rebuild db + motions_std + weeks
afterward (the CLI prints the reminder). Idempotent + resumable. **The site sits behind an
Akamai edge that 403s bare bots — `fetch_new.py` uses a browser+archive UA (verified live).**

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**
  (db `v_contested` = 73 motions); `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see each `CLAUDE.md`); standardized
  categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md`
  — read those before quantitative claims (especially the narrative-tally unnamed-majority
  style, the mid-2025 OCR seam, and the precinct-derived / post-2020 geo vintage).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers, each with its own `CLAUDE.md` + `AVAILABILITY.md` and each passing
`validate_dataset.py`. **None modify the core minutes/votes/comments/elections layer.** Join
to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **7 documents, CURRENT-CYCLE-ONLY snapshot** (June–July 2026). The three
  packet pages (`/council-packet`, `/planning-commission-packet`, `/rda-board-packet`) are
  CivicEngage "Document Folder Box" widgets holding **only the current cycle** — staff
  overwrite them each cycle, so **no historical packet archive exists** (verified live: 1/2/4
  docs on 2026-07-06). The Agendas-&-Minutes year folders (2008→2026) carry **Agendas | Minutes
  | Audio** only — the archived agendas are **thin 1–2-page outlines, not staff-report bundles**
  (on 2026-06-09 the PC agenda is 0.66 MB/2 pp vs a separate 8.09 MB/45 pp staff report that
  lives only on the rotating page). So 2020–2026 packets are an **honest publishing gap**, not a
  scraper miss (`unrecovered.csv`, with a Wayback lead). The snapshot joins by `date`(+`body`,
  `meeting_type`) to just the 2026-06-03 Council meeting.
- **`housing_plans/`** — **14 docs**. City (`taylorsvilleut.gov`, behind an Akamai edge that
  403s bare bots — `polite_fetch.py` browser UA): the **2025 General Plan** as **9 chapter
  PDFs** (no consolidated file; chapter ids non-sequential — harvest by anchor text) + the
  **standalone adopted MIH plan, Ordinance 23-03** (`ShowDocument?id=3679`, PASSED **2023-02-01**,
  PC 6-0 on 2023-01-24). The **MIH element = General Plan Chapter 8** (`mih_element` records
  both the 2025 GP Ch.8 and the 2023 ordinance). State (`jobs.utah.gov` HCD): the **2023/24/25**
  statewide MIH compilations + the **SB 34** summary, sliced to Taylorsville's per-city page
  ranges via the HCD form's first-field marker (never an "isolated header" heuristic) and
  grep-verified for zero Syracuse/Tooele bleed. **Ordinance 23-03 joins `all_votes.csv` by
  2023-02-01** (council) and `planning_commission/all_votes.csv` ~2023-01-24 (PC recommendation)
  — a concrete cross-body MIH referral. Document dataset; not joined to `db/`. **SB 34 p165–166
  is source-side mojibake** (not an extraction defect). No printed General Plan adoption date
  (dated 2025 by Ch.3 wording + Oct/Nov 2025 export).
- **`ordinances/`** — **90 adopted ordinances (2020+)**, one row each, linked to the council
  motion that adopted it. Confidence **75 high** (number cited in an adopted motion **and** an
  independent PMN PDF) / **9 medium** (signed PMN adopted PDF but the number is absent from the
  `all_votes.csv` motion text — a vote-citation gap, all 9 adopted) / **6 within_source**
  (motion-cited, no independent PDF — `high` **by construction, NOT** an independent
  cross-match; `source_url` points at the minutes doc). **71% land-use** (64/90). Source is
  **Utah PMN council body 720** (`utah.gov/pmn`) — the city has no online adopted-ordinance
  archive, American Legal is 403-protected + consolidated-text-only, and municipalcodeonline
  has no Taylorsville client; PMN body 720 attaches the signed/executed "Newly Adopted
  Ordinance" PDFs (and 2020 Agenda-Summary-Form bundles). **⚠ Parallel ordinance/resolution
  number sequences** — `Ordinance NN-NN` ≠ `Resolution NN-NN`; the join is keyed on the
  **instrument word + number**, and 6 numbers cited as ordinances but present on PMN only as a
  resolution are the `within_source` rows. 81 `text` / 3 `scanned` (RICOH OCR) / 6 `na`. A
  ~129-doc **2012–2019 back-catalog** exists on body 720, out of scope below the 2020 floor.
- **`pmn_backfill/`** — Utah PMN cross-check (entity 284; **council 720 / PC 722 / RDA 721** /
  CDRA 2770). Keyed on each attachment's **internal meeting date** (PMN posting dates lag and
  often carry the *previous* meeting's minutes). **2 genuinely-missing meetings recovered** —
  the **2020-01-29** and **2024-01-31** *Let's Talk Taylorsville* town halls (non-standard,
  no roll-call votes — do NOT feed to the vote extractor). **PC = 0 genuine gaps; RDA = no
  separate documents** (convenes in-recess with council, matching the repo's `body=RDA`
  modeling); 4 false positives (mislabeled filenames) resolved. The **15 OCR-upgrade
  candidates were RESOLVED 2026-07-12**: 6 promoted into the audited layer (born-digital md,
  vote diff clean, one genuine recovery — Cochran's Aye on 2025-01-22 council m5), 2 no-ops
  (PMN's file is the already-born-digital council doc; the OCR doc those dates is the separate
  RDA Board minutes PMN doesn't carry), 7 PC DRAFTs kept as sidecars (repo's APPROVED scans
  stay canonical). Detail: `pmn_backfill/CLAUDE.md` + `ocr_upgrade_candidates.csv`. The repo
  is otherwise a PMN superset.
- **`transcripts/`** — **SAMPLE-ONLY (owner policy); AUDIO-ONLY honest gap.** Taylorsville
  streams Council/PC meetings live but does **not** archive them as YouTube video —
  `youtube.com/taylorsvillecity` is a **PR channel of 141 videos** (festivals, recaps, PSAs),
  fully mapped in `channel_map.csv` (`meeting_planning_commission` 1 / `event_livestream` 4 /
  `promotional` 136). Exactly **1** genuine meeting video exists (`0ui3x38KRRo`, a 2024-05-15
  PC livestream); its YouTube **ASR** caption is the sole sample (`index.csv`, `caption_type=asr`,
  joins PC by 2024-05-15). **Whisper was NOT run.** ASR is never authoritative (proper nouns /
  case numbers misrecognized, no speaker labels) — the clerk's minutes remain the record.
  Future routes: **OpenUtah** (`taylorsville.openutah.org`, ~8 transcribed, robots-limited —
  metadata lead only) or **Whisper over the city "Audio Recordings"** archive.
- **`campaign_finance/`** — raw filings + provenance `index.csv` **plus the structured money
  layer** (`build_finance.py`, family `taylorsville_form`; **36 of 71 filings structured,
  35/36 both-sides reconcile as-of 2026-07-12** — the other 35 await sidecars/vision; see
  `campaign_finance/CLAUDE.md`). **71 filings**, Mayor + 5 district seats, self-hosted on the city CivicEngage
  site (Utah Code 10-3-208 → city recorder; not EasyVote, not `disclosures.utah.gov`). **TWO
  regimes** (`filing_regime`): **`annual`** (**50** — the March-1 statement **every sitting
  official files yearly**, even off-cycle, 2017–2026 — why the record is dense in off-years)
  and **`election_cycle`** (**21**, Primary/Pre-General/Final during a race, present **2021**
  (12) & **2023** (9)). **100% candidate-join** (71/71) to `election_results/taylorsville_races.csv`
  (normalize UPPER-CASE names; **Overson→Mayor** hard-mapped — she was D2 in 2011/2015);
  18 winner-filings + 3 by Larry Johnson (lost 2021 D5). **DOUBLE-COUNT TRAP: do NOT sum
  filings** — `filing_type`/`filing_phase` are per-PDF; run `cycle_totals.py` at the structuring
  step. **Honest gaps: 2019 & 2025 election-cycle filings never/not-yet posted** (annual
  statements only), not Wayback-recoverable. `date` is **inferred** from phase+year (read the
  PDF "Received" stamp during structuring).
