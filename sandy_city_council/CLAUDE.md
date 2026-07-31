# Sandy City Council — data repository

Canonical datasets about the **Sandy City Council** (Salt Lake County, Utah), modeled on the
Salt Lake City reference repo, plus a derived weekly view unifying minutes + votes. Built by
the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 274 files 2020–2026, Legistar) + roll-call votes (all_votes.csv)
planning_commission/  PC votes (all_votes.csv, body=PlanningCommission) — EXACT Legistar
                      EventItemVote records (no PC minutes exist on disk) + roster.csv
db/                   NORMALIZED RELATIONAL DATABASE (db/sandy.db) — the standard cross-city
                      schema (body/person/meeting/application/motion/vote/role + referral +
                      views) PLUS the full Legistar harvest in legistar_* extension tables.
                      Start: db/SCHEMA.md (incl. the minutes-vs-Legistar sourcing decision)
public_comments/      all_comments_clean.csv (EMPTY — submit-only city) + minutes_speaker_log.csv
                      (362 in-person speaker notes, NOT comments) + AVAILABILITY.md (the audit)
election_results/     Salt Lake County results filtered to Sandy council + mayor races
geo/                  precinct boundaries + address/point -> council district tool (Districts 1–4)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (CITY="Sandy", MEETING_WEEKDAY = Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. Votes + minutes carry the
meeting date; `build_weeks.py` buckets every record onto that weekly grid. Elections are
point-in-time (Nov, odd years), NOT in the weekly bundles — they join by **person + year +
district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (3,975 member-vote rows across
  833 motions; re-extracted 2026-07-02 after the PUA decode). There are **no** genuine public comments to aggregate (see below); do NOT use
  `minutes_speaker_log.csv` (362 in-person paraphrases) as a comments dataset.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/sandy_races.csv`) ↔ votes.
- **By geography**: `geo/address_to_district.py` resolves an address to Districts 1–4.
- **Cross-body / project-level**: `db/sandy.db` (standard schema since 2026-07-02, plan
  item 2.6 — read `db/SCHEMA.md` first). Council/RDA votes come from the minutes CSV
  (minutes-primary: 240 vote dates & 292 Nays vs Legistar's 214 & 173); PC votes from
  Legistar (their only source). The 116-link PC→Council `referral` layer and the
  `v_referral_chain`/`v_project_timeline`/`v_member_record`/`v_contested` views behave
  exactly like every other city's. Legistar extras (matters, agenda numbers, action
  names, `Nonvoting`, Board of Adjustment) live in `legistar_*` extension tables.
  Rebuild: `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent; the
  build prints CSV↔db reconciliation, exact to 0 with the 11 documented
  `db/vote_overrides.csv` duplicate-pair merges).

## Council structure
**Council–Mayor (strong-mayor) form. 4 District + 3 At-Large = 7 council members.** The
**sitting Mayor does NOT vote** on council motions (max tally is 7). **Monica Zoltanski was the
District 4 councilmember in 2020–2021** (170 vote rows) before being elected **Mayor (took
office Jan 2022)** — so she legitimately appears in 2020–21 tallies but not in council votes
afterward (her 4 Mayor-era rows are Board of Municipal Canvassers canvass actions —
2023-12-06 ×2 Excused, 2025-08-26, 2025-11-18 — listed in the minutes themselves). **Scott
Earl** held District 4 by appointment 2022–2023 until Houseman won the seat. The Council
elects its own Chair (Cyndi Sharkey), who presides — not the Mayor. At-large + mayor are
city-wide; geo maps addresses to Districts 1–4. The 3 at-large seats are staggered **2+1**: two
elect together (2019, 2023), one alone (2021, 2025).

## Data notes / caveats
- **Votes**: 833 motions / 3,975 member-vote rows / 131 contested (re-extracted 2026-07-02:
  63 minutes from 2021-08 → 2023-11 were PUA-garbled by a broken source-PDF font cmap and had
  yielded zero votes; they were decoded and verified against the retained raw PDFs — see
  `meeting_minutes/CLAUDE.md`). Sandy records named
  roll-calls mainly for substantive items — routine/consent business often passes without an
  individually recorded motion — so the recorded set skews toward contested items (~16% draw a
  Nay/Abstain/Recuse). Treat the contested *rate* as "among recorded roll-calls." Two formats:
  a labeled `Yes: N- <names>` / `No: N- <names>` roll-call, and a **narrative inline tally**
  (*"failed by a vote of 5-2 with X, Y opposed"*) that names only dissenters — for the latter
  the parser captures all named dissenters, orients the tally by pass/fail outcome, and leaves
  the majority **unnamed** (`names_recorded:false`, no guessing). See `meeting_minutes/CLAUDE.md`.
- **`body` column**: `body ∈ {Council, RDA}`. Council coverage is complete (3,974 rows). RDA has
  just 1 row, and that is essentially complete — Sandy publishes **no separate RDA minutes**
  (verified 2026: Legistar exposes only 5 bodies, none RDA; all 391 minutes are City Council). The
  RDA Board convenes **inside** council meetings (recess → "convene a meeting of the Redevelopment
  Agency" → usually **closed session** → reconvene); the extractor tags any open RDA vote
  `body=RDA`, but Sandy's RDA almost always acts in closed session. Not an acquisition gap.
- **Comments**: Sandy is **submit-only** — no public archive of genuine written/online
  comments. Public emails `CitizenComment@sandy.utah.gov` (read into record, not published); a
  Granicus eComment portal was briefly active 2020–21 but retains no exportable public
  submissions. `all_comments_clean.csv` is intentionally empty. In-person speakers are in
  `minutes_speaker_log.csv` (record notes, not public-submitted comments). Full audit:
  `public_comments/AVAILABILITY.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) lists Legistar API events newer than the indexes
  (+ Draft/Final minutes status); `--fetch --dataset meeting_minutes` downloads new `View.ashx?M=M`
  minutes PDFs (Calendar.aspx year postback) → raw/ → markdown → `minutes_index.csv`, then runs
  extract_votes.py + validate_votes.py; `--fetch --dataset planning_commission` appends new body-140
  events/items/votes to `db/staging/` and re-runs `planning_commission/build_from_legistar.py`.
- After a fetch, rebuild: `python3 db/build_db.py` + `db/build_referrals.py`, `python3 build_weeks.py`,
  `python3 ../scripts/normalize_motions.py --all`. fetch_new.py never mutates sandy.db directly.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal**; `weeks/<tue>/summary.md`
  surfaces them. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
- Cross-check election winners against `geo/` districts and the votes roster for member-level
  analysis.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers built from the **Granicus Legistar Web API** (`webapi.legistar.com/v1/sandyutah`);
each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing data. Join to
`all_votes.csv`/minutes by `date` (+ `body`); `matter_id` joins the `legistar_*` tables in `db/sandy.db`.
Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — Legistar 3-hop API (events→eventitems→matter attachments). **462 agenda PDFs stored**
  (Council 296, PC 157, BoA 9; born-digital text) + **6,446 matter attachments INDEX-ONLY** (`format=na`,
  `stored_locally=no`, live `source_url` + `size_mb` + `matter_id`; ~14.9 GB catalogued, 10× over the
  disk ceiling). 2020–2026, both bodies symmetric. To read an attachment: fetch its `source_url`.
- **`housing_plans/`** — 8 docs: MIH element (2022 Ch.10 + Ord 23-01 amendment), 2017 biennial report,
  state 2023/24/25 compilations + SB 34. **The current General Plan (adopted 2025-01-07) is a web/ArcGIS
  product with no PDF** (landing-page HTML retained); the last PDF-form MIH element is the Sept-2022 Ch.10.
- **`ordinances/`** — **170 ordinance matters** (`MatterTypeId=53`), 87 adopted (65 land-use), 83 signed
  PDFs. Vote-linkage confidence **73 high / 7 medium / 6 low / 1 none** (the `none` is post-vote-cutoff).
  `adopted` derived from Legistar `histories` (null flag=adopted, only `Fail`=failed), NOT `MatterStatusName`.
  **5 Legistar-vs-minutes ordinance-number discrepancies flagged** (signed-PDF number vs minutes motion —
  a minutes-layer audit signal, not fixed here).
- **`pmn_backfill/`** — **separate** from the audited minutes. Sandy PMN entity 260; bodies Council 464 /
  PC 466 / RDA 465 / BoA 467. **8 recovered** (6 Council + 2 RDA minutes). **PC & BoA carry zero PMN
  minutes** (honest coverage zero, verified).
- **`transcripts/`** — **ASR** captions (79) from the third-party **Utah Record** YouTube channel via the
  OpenUtah meeting index; NEVER authoritative. 88-video map. **Hard 2025-01 cutoff** — all 215 pre-2025
  council meetings have no video. (Owner decision 2026-07-05: transcripts are sample-only going forward;
  Sandy's fuller pull predates that and is retained.)
- **`campaign_finance/`** — **83 filings** (7 filers; 2021/23/25) from the **EasyVote portal**
  (`sandycityut.easyvotecampaignfinance.com`); scanned → OCR. 67/83 join elections. **2019 proven absent.**
  Flags a real election-record gap: **Parry Harrison** filed a 2025 D3 *primary* set but is absent from
  `election_results` (general-only). **Structured layer built 2026-07-05:** `contributions.csv` (1,261) /
  `expenditures.csv` (813) / `filing_totals.csv` (83) via `build_finance.py` (F2 EasyVote OCR mode; 81/83
  reconcile clean; 34 filings used a gated Claude-vision pass, ~$3). See the "## Structured layer" section
  in `campaign_finance/CLAUDE.md`.
