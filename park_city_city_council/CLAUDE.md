# Park City Council — data repository

Canonical datasets about the **Park City Council** (Summit County, Utah), modeled on the SLC
reference repo, plus a derived weekly view. Built by `build-city-data-repo`. Data floor: **2020**.
Independent QA: `VERIFICATION.md` (**PASS**).

```
meeting_minutes/   238 minutes (CivicClerk) + roll-call votes (all_votes.csv; Council/RDA/HA)
planning_commission/  162 PC minutes + votes (all_votes.csv, body=PlanningCommission) + project_timeline.csv
                   (PILOT: the Planning Commission — technical land-use body; appointed, no elections)
db/                NORMALIZED RELATIONAL DATABASE (db/parkcity.db SQLite + table CSVs) — the canonical,
                   queryable form joining ALL bodies' votes by real keys. Start here: db/SCHEMA.md
public_comments/   all_comments_clean.csv (459 GENUINE published written comments!) +
                   minutes_speaker_log.csv (644 in-person, NOT comments) + AVAILABILITY.md
election_results/   Park City self-administered results, mayor + at-large council
geo/                city boundary (Summit + Wasatch straddle) + 13 precincts + in-city-limits tool
weeks/              DERIVED weekly bundles (build_weeks.py: CITY="Park City", MEETING_WEEKDAY=Thursday)
recon.md / VERIFICATION.md
```

## How to analyze
- **Votes**: `meeting_minutes/all_votes.csv` — 1,592 motions / 7,927 rows / 101 contested
  (council figures current as of the Q3-2026 refresh). Filter `body` for Council
  (1,525) vs **RDA (49)** vs **HA / Housing Authority (18)**. `AYES:/NAYS:` roll-calls; tally-only
  "unanimous" → `names_recorded:false`. **Planning Commission** votes live separately in
  `planning_commission/all_votes.csv` — **873 motions / 1,086 rows / 52 contested** after the
  2026-07-19 folded-outcome parser fix + the 2026-07-19 post-audit token-strip repair (see below).
- **Public comments (rare — genuinely published)**: `public_comments/all_comments_clean.csv` (459
  comments = 433 verbatim eComment/email quoted in minutes + 26 agenda-packet correspondence). A
  *real* public-sentiment dataset, unusual for Utah. Do NOT use `minutes_speaker_log.csv` (1,055
  in-person paraphrases) as comments.
- **Mayor** does not vote except tie-breaks (**2 in the record**: Beerman 2020-06-25 Ord 2020-31,
  Worel 2024-08-22 Res 16-2024 — both "Nay (Mayor tie-break)", both 2-3 Fail; in `db/parkcity.db`
  they are `vote_value='Nay'` with `note='Mayor tie-break'`); councilmembers-turned-mayor (Worel,
  Dickey) vote only in their council years. **By person**: join `election_results/park_city_races.csv`
  winners ↔ votes. **By geography**: `geo/address_to_district.py` → inside/outside city limits.

## Council structure
**Mayor + 5 all-at-large (0 districts), council-manager form.** Mayor votes only to break ties.
Meets Thursdays. RDA (Main St + Lower Park Ave project areas) + Housing Authority run as in-council
recesses → `body=RDA`/`HA`.

## Data notes
- **`body`**: `Council` / `RDA` / `HA` (in-council recess detection, mirroring Provo's convene/reconvene).
- **Elections**: Park City **self-administers** (Summit County defers); at-large vote-for-N, no RCV;
  the 2025 mayoral race went to a 7-vote recount (Dickey > Rubin). See `election_results/CLAUDE.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit. (Rebuilt 2026-07-02; weekly
  summaries now carry the 459 public comments.)
- **PC folded-outcome parser fix 2026-07-19** (HIGH-priority Q3 refresh): from 2024-10-09 the PC
  minutes dropped the separate `VOTE:` marker and fold the outcome into the `MOTION:` block, so the
  old `parse_meeting()` silently dropped **every PC motion since then** (34 meetings). Fixed in
  `planning_commission/extract_votes.py` (emit on folded outcomes + `Vote on Motion:` roll calls +
  prose named dissent, `names_mode` field; never fabricate an outcome-less motion). **Recovered 264
  PC motions / 289 rows** post-2024-10-09 (40 meetings) plus 6 source-verified pre-2024 folded cases;
  pre-2024-10-09 otherwise byte-identical. Derived layers (+12 PC→Council referrals, weeks,
  motions_std) rebuilt; `validate_city` 0 FAIL. Backups: `_backups/2026-07-19-parkcity-pc-parser/`.
  Details in `planning_commission/CLAUDE.md`.
- **PC post-audit token-strip repair 2026-07-19** (audit `_audits/2026-07-19-postingest-park_city/`,
  fixes #1+#2): the folded fix's reconciliation sample was 11 folded meetings and **excluded
  2024-11-13**, so its "0 mismatches / all folded meetings reconcile" claim missed a single un-fixed
  root cause — a lone page-number/watermark token stamped WITH a trailing period (`1.`, `3.`, `D.`)
  that `clean_lines` kept (it stripped only the period-less shapes), wedged between "The motion" and
  its outcome verb. It silently dropped **1** motion (the 2024-11-13 Johnson/Sigg unanimous-consent
  continuance-and-amend-Conditions #13/#16 motion) and garbled **6** result strings to a bare
  `Approved` (2024-11-13 m5, 2025-06-25 m3, 2025-08-13 m4, 2026-01-14 m4, 2026-05-27 m6, 2025-04-02
  m6). Fixed in `folded_vote_window()` (drops the trailing-period furniture on the outcome window
  ONLY — stored motion text stays byte-identical — plus a guarded reunification for the scrambled
  2025-04-02 "D" layout). **PC 872→873 motions / 1,085→1,086 rows**; the 6 results healed to their
  true "passed with the unanimous consent of the Commission" forms (outcome/disposition unchanged);
  contested still 52; pre-2024-11-13 byte-identical; db (9 vote-overrides + 2 mayoral tie-breaks
  intact) / +12 referrals / weeks / motions_std rebuilt; `validate_city` 0 FAIL. Backups:
  `_backups/2026-07-19-audit-fixes/park_city/`.
- **Repairs 2026-07-02** (post-audit, Phase 1.6 — details in `README.md` § Repairs): extraction
  regexes made case-sensitive (10 spurious motions removed), db build made fail-loud with
  `db/vote_overrides.csv` for the 9 source clerk errors (member in both AYES and NAYS/ABSTAIN),
  both mayoral tie-breaks preserved in the db. Originals: `_backups/2026-07-02/`.

## Planning Commission + the relational database (cross-body analysis)
`planning_commission/` is a parallel dataset for the **second governing body** (same schema as
`meeting_minutes/`; every row `body=PlanningCommission`). For any cross-body or project-level question,
**prefer `db/parkcity.db`** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers,
never conflated:
- *Within-body core is EXACT*; project keys are **resolved from prose** and **body-scoped** — a Council
  "Founder's Place" and a PC "Founder's Place" are **distinct** applications; `0 applications span >1
  body` by design. `motion.app_match_method` ∈ `singleton`(high) / `name`(medium, heuristic) /
  `override`(high) tells you how solid each grouping is. **Stages**: PC `pc_recommendation`
  (positive/negative → forwarded to Council; 156), PC `pc_final_action` (CUP/design-review/steep-slope
  — never reaches Council; 446), then `council_vote`, plus `rda_vote`/`ha_vote`.
- *Cross-body `referral` is RECONSTRUCTED + scored + GENERALIZED* — 100 links keyed
  `(primary_body←related_body)`: **Council←PlanningCommission 95**, plus **Council←HA 3 / Council←RDA 1
  / PC←HA 1** (47 high / 30 medium / 23 low). **`high`≈exact (address+subject or override); `medium`
  spot-check; `low` flagged.** Use **`v_referral_chain`** (this **supersedes** the old heuristic
  `planning_commission/project_timeline.csv` crosswalk) and **`v_project_timeline`**.
- **Agency links are signal-limited** (boilerplate RDA/HA titles vs terse ordinance titles), so the
  marquee development links — **Founder's Place, Sommet Blanc, Studio Crossing, Argent** — are carried
  explicitly by `db/referral_overrides.csv` (4 forced overrides). Correct mistakes in
  `db/overrides.csv` / `db/referral_overrides.csv` and rebuild.
- **Analytical value**: the PC is the technical land-use filter, the council the political body — they
  diverge (e.g. Founders Place: PC unanimous YES → Council fail; 446 PC-final actions invisible to the
  council). Profile commissioners with `v_member_record`; **12 people served on >1 body** (unified by
  name in `person`/`role`). NOTE: the DB was **retrofitted** from an older alias-merge model — the
  legacy `project_timeline.csv` and `pl_number`/`alias` tiers are superseded. PC is still not in `weeks/`.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) reports CivicClerk meetings newer than each
  dataset's `minutes_index.csv` max date; `--fetch [--dataset <name>]` downloads new minutes PDFs
  (raw retained under `<dataset>/raw/`), converts to markdown, appends index rows, and runs
  extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- After any fetch, rebuild derived layers: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers (**CivicClerk OData** minutes/packets/video + Revize static `/Documents/` tree +
Municode S3 ordinance bucket + PMN); each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none
modify existing data. Join to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **942 rows HYBRID**: 474 agendas STORED (52 MB, born-digital) + 468 agenda packets
  INDEX-ONLY (~30 GB, resort image-heavy). Council/PC/HPB. 100% vote-date join; PC agenda PDFs reliable only ~2023+.
- **`housing_plans/`** — **standalone Five-Year MIHP** (2022 + amended + 2025, w/ signed resolutions) AND a
  GP housing chapter (2025 GP). Deed-restricted affordable/workforce program.
- **`ordinances/`** — **262** (160 land-use), refreshed 2026-07-19. **Strong independent archive** (Municode
  public S3 signed-PDF bucket) → **96 high** / 164 within_source / 2 none. 2 consent-agenda adoptions missing
  from votes (2024-08, 2026-08). **2 signed PDFs still owed** — `2026-15` (budget) + `2026-18` (compensation),
  adopted 2026-06-25, motion captured but not in Municode's S3 (non-codified admin ordinances); honest gap in
  `ordinances/AVAILABILITY.md`.
- **`pmn_backfill/`** — Entity 233; Council 653 / PC 1860 / **RDA 654**. **2 net-new Council** (June 2026);
  RDA is an **honest zero** (it convenes in-council; PMN "RDA minutes" = the combined council doc, verified 14/14).
- **`transcripts/`** — **194 videos mapped, 0 captions**: Park City publishes meeting VIDEO (CivicClerk MP4
  feed) but NO captions (no ASR/YouTube). The map is the deliverable; video 2023-09+. Whisper proposed for 3 un-minuted meetings.
- **`campaign_finance/`** — **126 filings** (2017–2025; 91 text / 45 scanned), self-hosted on the Revize
  `/Documents/.../Campaign Disclosures/` tree. **89% election join.** Flags Betsy Wallace (2023 primary filer
  absent from roster). Line-items live only in `text/` sidecars — structured `contributions.csv` is the separate planned layer.
