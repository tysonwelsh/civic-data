# SLC City Council — data repository

Three canonical datasets about Salt Lake City Council, plus a derived weekly view that
unifies the first two for meeting-level / cross-dataset analysis.

```
public_comments/            public-comment PDFs -> cleaned dataset (~13k comments, 2020–2026)
meeting_minutes/            council meeting minutes (text) + extracted vote tables (2020/2021–2026)
election_results/           county CANONICAL canvass -> SLC council+mayor races (2007–2025;
                            re-pointed 2026-07-19 to salt_lake_county/elections/, raw copies retired)
geo/                        precinct boundaries + address/point -> council district tool
weeks/                      DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py              regenerates weeks/ from comments + minutes + votes
```

`geo/address_to_district.py` resolves any SLC address (or lat/long) to a council
district (geocode → precinct point-in-polygon → district). It ties an address/comment
to a district, and thus to that district's member, votes, and election margin.

Each subproject has its own `CLAUDE.md` with the details of how it's built.

## Three ways the datasets connect
- **By week** (comments ↔ minutes ↔ votes): the `weeks/` bundles, keyed on the Tuesday
  meeting (see below). Best for "what happened around this meeting."
- **By councilmember** (elections ↔ votes ↔ comments): a race winner in
  `election_results/slc_races.csv` is a member whose roll-call votes are in
  `meeting_minutes/all_votes.csv` and whose constituents' comments are in
  `public_comments/`. Join on person+year+district (normalize names — election names
  are upper-case with `(NP)` suffixes; see that folder's CLAUDE.md). Best for "did a
  member's record/sentiment track their election margin?"
- Elections are point-in-time (Nov, odd years) and are NOT in the weekly bundles.

## The join key

Everything keys to the **council week ending on the Tuesday meeting** (the cadence is
Wed → the following Tue). Public comments carry `period_end` (that Tuesday); minutes and
votes carry the meeting date (≈90% Tuesdays). `build_weeks.py` maps every record to its
week-ending Tuesday so the three sources line up on one grid.

## How to analyze (which artifact for which question)

- **Aggregate / time-series** (comment volume or emotion over years, voting patterns by
  member or motion type, topic trends): use the **canonical flat tables** —
  `public_comments/all_comments_clean.csv` and `meeting_minutes/all_votes.csv`.
- **Meeting-level / contextual** (what did the public say the week of a given vote? how
  did members vote the week of a comment surge? full context for one meeting): use the
  **`weeks/<tuesday>/` bundle**. Start with its `summary.md`, then `comments.csv` and
  `votes.csv`; the week's minutes are **linked from `summary.md`** (canonical files live in
  `meeting_minutes/minutes/`, not copied into the bundle). `weeks/index.md` lists every week
  with counts.

So: comment → open its week bundle for the meeting + votes; vote → read that week's
comments. Both directions are one folder away.

## weeks/ is derived — regenerate, don't hand-edit

`weeks/` is generated from the canonical datasets and is safe to delete. After re-running
any scraper/cleaner, rebuild it:

```
python3 build_weeks.py
```

Canonical sources of truth are the two subproject datasets; never edit files under `weeks/`.

## Planning Commission + the relational database (cross-body analysis)

- **`planning_commission/all_votes.csv`** — the appointed technical land-use body; same long vote schema
  as council, every row `body=PlanningCommission`. **145 meetings (minutes files) · 776 motions · 5,376
  member-vote rows · 30 rostered commissioners** (`planning_commission/roster.csv`; 290 motions
  non-unanimous, i.e. with a recorded Nay/Abstain/Recuse — counts re-measured 2026-07-12 after the
  T3.1(b) missed-aye-block repair: first-name roll lists, verbless quoted votes, chair tie-break
  rows, "all other Commissioners voted yes", a phantom mid-roll split merged, one scrivener
  double-nay roll honestly demoted to tally-only). The
  `result` string encodes the **recommendation-vs-final-action taxonomy**: PC *recommendations forwarded
  to Council* (261 — 218 Positive / 43 Negative) vs *final actions* (308 — conditional use / design
  review / planned development that never reach Council); the remaining 207 motions are procedural. Votes here are **pure-regex** extracted
  (`planning_commission/extract_votes.py`, deterministic) — distinct from the **LLM-batch-extracted**
  council votes in the prior build. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two idempotent build stages:
  `python3 db/build_db.py` then `python3 db/build_referrals.py`. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no usable file number) and
    **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping is.
    SLC is **singleton-dominated** (titles are address-keyed, e.g. *"Rezone at approximately 536 South
    200 West"*), so one matter can appear as several council singletons.
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — **31 scored links (11 high / 15 medium / 5
    low)**: 28 Council←PlanningCommission + 3 Council←agency (the HTRZ / Sugar House Streetcar interlocal
    agreements the RDA/CRA and Council both acted on). **`high`≈exact (address+subject); `medium`
    spot-check before quoting; `low` flagged.** 11% of council land-use items linked; the rest are
    honestly unlinked (PC origin pre-2020, council-initiated, or duplicate singletons of a linked
    matter). 6 reviewed false positives are suppressed in `db/referral_overrides.csv`. The payoff is the
    **technical-vs-political divergence** (PC negative rec → Council acts anyway). Use
    `v_referral_chain` / `v_project_timeline`.
- **The five bodies & how they're separated.** SLC's Council adjourns/reconvenes *in-session* as the
  **LBA, RDA, and CRA**, so one minutes document interleaves up to four bodies' motions. Since the
  2026-07-02 retrofit the council `all_votes.csv` carries a per-row **`body` column** (clone-standard
  short codes `Council`/`RDA`/`CRA`/`LBA`, placed after `title` — standard 13-col schema), derived by
  **walking the markdown minutes' section headers** (`SALT LAKE CITY COUNCIL MEETING`, `LBA OPENING
  CEREMONY`, etc.). That walk lives in the DB build (`db/build_db.py`, an SLC-local adaptation — the
  shared skill template is left pristine), which now reads the CSV's `body` column (mapping the short
  codes to the db's full body names, `RDA` ↔ `Redevelopment Agency` etc.) and keeps the walk as the
  derivation of record. It also recognizes SLC's rich land-use `motion_type` taxonomy. Both are
  read-time only; no other source content was modified. **SLC address nuance:** a "shared address" is an
  approximate **grid intersection**, not a parcel, so address-alone is co-location (low), not exact.

## Refreshing (incremental updates — Phase 3.3)

- `python3 fetch_new.py --probe` (default; read-only) reports what's new on the portals vs the
  indexes for all three datasets; `--fetch [--dataset <name>]` downloads it (minutes delegate to
  `meeting_minutes/scrape_primegov.py`; comments delegate to `public_comments/check_new_comments.py`
  + then `vision_extract.py --year <y>` / `clean_comments.py`), appends index rows, and runs
  extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- After any fetch, rebuild derived layers: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Notable analysis guidance

- The council is **high-consensus**: only ~4% of motions are contested. The **contested
  votes are the signal** for where members stand — `summary.md` surfaces them per week.
- Motion types are a fixed 12-category taxonomy (see `meeting_minutes/CLAUDE.md`).
  Substantive policy = Ordinance / Resolution / Budget Amendment / Grant-Funding /
  Interlocal / Appointment; Procedural-Administrative, Public Hearing Action, and
  Ceremonial are mostly low-signal housekeeping.
- Coverage seams to remember: comments are weekly from ~2020-07; minutes are clean
  Markdown (PrimeGov) for 2021+ but OCR text (Laserfiche) for 2020; votes exist for
  2021+ only. Some summer-recess weeks legitimately have 0 comments.

---
*Phase 2.5 retrofit 2026-07-02 (`REMEDIATION_PLAN.md`): directories renamed to the clone
standard (`slc_public_comments/` → `public_comments/`, `municipal_election_results/` →
`election_results/`); `body` column added to `meeting_minutes/all_votes.csv` (13-col
standard schema); `meeting_minutes/minutes_index.csv` regenerated in the standard schema
(`date,year,title,slug,path,source,source_url,format`) — the legacy extras
(`week_start`/`chars`/`ref_id`) are frozen in `meeting_minutes/minutes_index_legacy.csv`.
Verification: `VERIFICATION.md`.*

*Doc corrections 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): PC
recommendation/final-action split corrected to the current extraction (252 rec = 211
Positive / 41 Negative; 290 final actions; 198 procedural — was 314/269/45/426); the
stale "274 contested" replaced with the measured 277 non-unanimous motions. All other
quoted totals (145 PC meetings / 740 motions / 5,333 rows / 30 commissioners; db 5
bodies / 70 persons / 494 meetings / 893 applications / 2,582 motions / 18,169 votes /
31 referrals 11-15-5) re-verified against the data unchanged.*

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers (**PrimeGov** + slcdocs.com + PMN + YouTube); each has its own `CLAUDE.md`.
All built datasets pass `validate_dataset.py`; none modify existing data. Join to `all_votes.csv`/minutes
by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **582 rows HYBRID**: Council 530 INDEX-ONLY (~15–30 GB, `Meeting Materials` bundles) +
  PC 52 (39 stored). SLC PrimeGov holds **only the Council family**; PC lives on slcdocs.com (2026 machine-discoverable only).
  - **doc_class layer** (2026-07-16): 11 PC-2026 staff reports classified (whole-class verified);
    Council packets ruled not separable (monolithic, index-only) — see packets/AVAILABILITY.md.
- **`housing_plans/`** — **Growing SLC (2018–22)** + **Housing SLC (2023–27)** five-year plans + Thriving in Place + Plan Salt Lake.
- **`ordinances/`** — **464 adopted, all Council** (RDA/CRA/LBA pass resolutions; 2026 = 1–40 complete
  after the 2026-07-19 backfill of 19–25 + 27–40). 9 high / 49 medium / 352
  within_source / 54 none. Signed archive JS-gated; corroborated via SLC Planning list + PMN synopsis.
- **`pmn_backfill/`** — Entity 259; Council 1360 / PC 1274 / RDA 1277 / CRA 9033 / LBA 3475. 7 recovered +
  **`url_recovery_2020.csv`: citable PMN URLs for 65 of the 68 un-URL'd 2020 Laserfiche minutes —
  PROMOTED 2026-07-19 into `meeting_minutes/minutes_index.csv` `source_url` (re-verified in-body;
  `source` stays `laserfiche`, text unchanged). The 3 Jan Formal dates PMN never posted stay
  honestly URL-less.**
- **`transcripts/`** — **ASR**, 10 sampled / **1,142 videos mapped** (SLC Live Meetings YouTube, 2011+; the repo's largest map).
- **`campaign_finance/`** — **0 filings, PORTAL-BLOCKED.** SLC's JSON WebAPI (`dotnet.slcgov.com/Attorneys/
  CampaignFinance_Public/`) returned 503 "scheduled maintenance" throughout the run. API reverse-engineered +
  harvester scaffolded (honest-empty, validates PASS) — **re-run when the portal is up** (see TODO).
