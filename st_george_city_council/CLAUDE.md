# St. George City Council — data repository

Canonical datasets about the **St. George, Utah City Council** (Washington County — NOT
St. George, Louisiana), modeled on the Salt Lake City reference repo, plus a derived weekly
view unifying minutes + votes + comments. Built by the `build-city-data-repo` skill. Data
floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 305 files 2020–2026) + roll-call votes (all_votes.csv)
public_comments/      all_comments_clean.csv (136 GENUINE written comments 2023+) +
                      minutes_speaker_log.csv (in-person speaker notes, NOT comments) + AVAILABILITY.md
election_results/      Washington County results filtered to St. George council+mayor races
geo/                  city-limits polygon -> in/out-of-city check (council is at-large, no districts)
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Thursday)
recon.md              map of this city's data sources (provenance)
VERIFICATION.md       independent QA + external election cross-check (PASS)
```

## The join key
Everything keys to the **council meeting weekday (Thursday — 1st & 3rd Thu)**. Votes +
minutes carry the meeting date; genuine written comments carry their submission/meeting date.
`build_weeks.py` buckets every record onto that weekly grid. Elections are point-in-time
(Nov, odd years), NOT in the weekly bundles.

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (8,312 member-vote rows) and
  `public_comments/all_comments_clean.csv` (**136 genuine written comments**, 2023–2026).
  Do NOT use `minutes_speaker_log.csv` (132 in-person speaker pointers) as comments.
- **Meeting-level / contextual**: the `weeks/<thursday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/st_george_races.csv`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` returns whether an address is inside city
  limits (council is at-large — there are no districts).

## Council structure
**Mayor + 5 council members, ALL AT-LARGE (0 districts)**, 4-yr staggered terms,
council-manager form. Elections are "vote-for-N" multi-winner (top N win N open seats).

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **132 meetings · 1,006 motions · 6,250 rows · 88 contested**, **16
  appointed commissioners** (`planning_commission/roster.csv`, reconstructed from attendee headers —
  no elections; cross-checked vs Council appointment votes). The `result` string encodes the
  **recommendation-vs-final-action taxonomy**: `Positive/Negative recommendation N:N` (forwarded to
  Council — 674 of them) vs `N:N Approved (Final Action)` (CUP/site-plan/hillside — never reach
  Council). Two source vintages (Revize 2024+ born-digital vs PMN 2020–23, with 2020–21 layout
  fragmentation). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    St. George) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping
    is (St. George leans on `singleton` — PC motions cite only "Item 2A", so the project string lives
    in the Council twin and in `application.rep_title`).
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — **117 scored links (15 high / 92 medium /
    10 low)**, all Council←PlanningCommission here (the table also models Council←agency / PC←agency for
    cities with one; St. George's RDA carries none). Keyed `(primary_application_id, primary_body,
    related_application_id, related_body, match_method, confidence, …)`. **`high`≈exact;
    `medium` spot-check before quoting; `low` flagged.** 108 of 836 council land-use items (13%) linked;
    the rest are honestly unlinked (PC final-action, PC origin pre-2020, or council-initiated). Tune in
    `db/overrides.csv` / `db/referral_overrides.csv` (30 suppress + 3 link applied) + rebuild.
  - **St. George address nuance:** Council minutes are richly addressed (198/836 apps) but PC motions
    rarely cite an address (29/713), so the join leans on **subject** (IDF title agreement) and reserves
    address+subject for `high`. The payoff = the technical-vs-political relationship; use
    `v_referral_chain` / `v_project_timeline`. **4 people served on both Council and PC** — profile a
    career across both bodies with `v_member_record`. Build (idempotent): `python3 db/build_db.py` then
    `python3 db/build_referrals.py`.

## Data notes / caveats
- **Minutes** span 2020–2026: 2022–26 from Revize; **2020–21 backfilled from Utah PMN's live
  search API**. 2020–21 PDFs needed inline vote-header normalization; their member names are
  bare surnames (verified real). See `meeting_minutes/CLAUDE.md`.
- **Genuine written comments** (the public's own submissions via the city's JotForm/email
  comment page) exist **2023+ only** — no pre-2023 written archive (`AVAILABILITY.md`). The
  minutes only *point* to in-person speakers (name + video timestamp, no text); those are in
  `minutes_speaker_log.csv` (record notes, NOT public-submitted comments). Spoken-comment
  video transcription is a deferred future option.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal**; `weeks/<thu>/summary.md`
  surfaces them. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).

## Refreshing (incremental updates — Phase 3.3)

- `python3 fetch_new.py --probe` (default; read-only) reports minutes newer than each index's max
  date on the two Revize listing pages (council `agendas_and_minutes.php`, PC
  `planning_commission.php`); `--fetch [--dataset <name>]` downloads into `<dataset>/raw/`,
  converts (pdftotext; docx via textutil), appends index rows, runs extract_votes.py +
  validate_votes.py. Probe results land in `refresh_probe.json`.
- After any fetch, rebuild: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Agenda packets / staff reports (`packets/`) — additive LINK INDEX, as-of 2026-07-02
Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning analysis,
recommendation) behind each agenda item — use it to explain *why* a motion in `all_votes.csv`
passed. **Join key:** `(date, body [, meeting_type])`. Packet dates cover **150/163 council** and
**39/46 PC** vote dates (non-matches are work/special/canvass meetings with no roll call).
- **INDEX-ONLY (no PDFs stored).** Revize bundles each meeting into one **10–150 MB image/map-heavy
  PDF** (full 224-set = 7.5 GB), not text-convertible. By owner decision the PDFs are not retained;
  `index.csv` (224 rows) is a pointer table — `source_url`, `size_mb`, `packet_kind`
  (`full_packet`/`agenda_packet`/`packet`), `format=na`, `stored_locally=no`.
- **To read a packet:** fetch its `source_url` (public GET) and use **vision/OCR** (not pdftotext).
  Prefer `packet_kind=full_packet`. To re-hydrate all: `polite_fetch.py --batch` **uncapped** (7.5 GB).
- URLs were **scraped, never guessed** (Revize filename encodings vary wildly); all 224 verified 200
  on 2026-07-02 (`raw/_fetch_log.jsonl`). `validate_dataset.py` PASS. See `packets/CLAUDE.md`.

## Moderate-income housing + General Plan (`housing_plans/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 2). The policy/statutory layer behind land-use votes
(Utah Code 10-9a-403/408; SB 34 2019 / HB 462 2022). **7 index rows, born-digital, PASS
`validate_dataset.py`.** Two source families:
- **City site (Revize):** the **St. George General Plan** (interactive web plan — no PDF; 8
  HTML pages in `raw/general_plan_web/`), the **2040 Downtown Area Plan** PDF, and the **2022
  MIH Plan** (general-plan MIH element, 29 pp; file slug `2025-GPA-005 … Clean`). Revize
  gotcha: doc-center links render as `Documents/<f>.pdf` (404); real files live at
  `cms3.revize.com/revize/stgeorge/Documents/<f>.pdf` (= `sgcityutah.gov/Documents/<f>.pdf`).
- **State HCD (`jobs.utah.gov/housing/affordable/moderate/reporting/`):** annual MIH reports
  are **statewide compilation PDFs**, not per-city — St. George's block bracketed out of each
  (FY2023 pp.820–833, FY2024 pp.782–794, FY2025 pp.953–971; SB 34 pp.151–152) into
  `text/stgeorge-*.txt`. "St. George" sorts before "Summit County" — sidecars verified free of
  Summit/Snyderville bleed. St. George present in all four (contact: Brenda Hatch, Planner II).
- Joins to `meeting_minutes/all_votes.csv` / `ordinances/` by date+subject (report narratives
  cite Switchpoint, form-based code, Downtown Area Plan implementation). See
  `housing_plans/CLAUDE.md` + `AVAILABILITY.md` for the full gap log.
- **doc text layer** (2026-07-16): 8 text sidecars extracted from the stored GP HTML web-plan
  (was html-only, unsearchable) — see `housing_plans/CLAUDE.md`.

## Zoning / land-use ordinances (`ordinances/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 3). Maps **Ordinance #YYYY-NN → adoption date → the
council motion that passed it**, so a vote in `all_votes.csv` links to what the ordinance did.
**252 rows / 35 raw PDFs**; `validate_dataset.py` PASS.
- Code host `stgeorge.municipal.codes` (Sterling) is **403 bot-protected** (like American Legal);
  the full **Title 10 zoning text** was instead recovered from a PMN attachment.
- Confidence semantics (in `match_confidence`): **`high` (118)** = number confirmed by BOTH a
  Recorder "Notice of Ordinance Adoption" PDF (independent source) AND a motion — a genuine
  cross-match; **`within_source` (91)** = motion cites the number but no notice exists — high *by
  construction*, NOT corroborated (mostly pre-Oct-2024); **`medium` (39)** = notice+date only
  (consent-calendar, no number in any motion); **`none` (4)**. Treat `within_source` as
  suggestive, not proof. 2020–2022 actions have no numbers (scheme began 2023). See
  `ordinances/CLAUDE.md`.

## Utah Public Notice backfill (`pmn_backfill/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 4). A **coverage cross-check + recovery** dataset, kept
**separate** from the audited `meeting_minutes/`/`planning_commission/` layers — do not treat it
as canonical minutes without review. PMN bodies **241 = Council, 242 = Planning Commission**.
**20 recovered docs / 17 dates** (mostly 2022–2025 work/joint council meetings absent from the
city site). Per-year repo-vs-PMN table in `pmn_backfill/coverage.md`; provenance columns
`notice_url`, `pmn_file_id`, `pmn_body_id`. **Verify body-name header + internal date before
trusting any recovered file** — PMN's own `(Meeting Minutes)` label was wrong 3 ways this run
(an Arts-Commission file under the council body, wrong-year filenames, an agenda packet labeled
minutes). Remaining gap: PC 2023-05-23 minutes (never posted).

## Meeting video transcripts (`transcripts/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 5). **Automatic (ASR) YouTube captions** — use for the
*discussion* the minutes compress, NEVER as an authoritative record (word errors; every sidecar
is headed with the caveat). **10 transcripts / ~106k words; 37 uncaptioned** (`unrecovered.csv`,
`format=na`). Join by `date` to minutes/votes. Caveats: council spans **two YouTube channels**
(Community Education → City of St. George), captions are a per-video lottery with a **near-total
2023–2024 gap**, PC is not on video. `caption_type=asr` throughout (no manual tracks exist).
2024 council is the top **Whisper** candidate (proposed, not run). See `transcripts/CLAUDE.md`.

## Campaign finance (`campaign_finance/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 6). Completes **elections → members → votes**: who
funded the candidates. **104 rows / 14 scanned packet PDFs**, cycles **2021, 2023, 2025**;
`validate_dataset.py` PASS.
- Municipal campaign-finance reports are filed with the **City Recorder** (Utah Code
  10-3-208), NOT `disclosures.utah.gov` (state-only) or the county (verified empty). The
  city posts **combined per-deadline packets** (all candidates in one scanned PDF); each is
  split into one `index.csv` row per candidate.
- **2023 + 2025 live** on `sgcityutah.gov` (Revize root-relative quirk: 2025 files resolve
  at `sgcityutah.gov/<name>.pdf`; 2023 under `Documents/Government/Mayor And Council/Election
  Information/`). **2021 recovered from Wayback** (`www.sgcity.org/pdf/administration/general/
  campaignfinancialreports/`). **2019 unrecoverable** (never archived — exhaustive CDX in
  `campaign_finance/AVAILABILITY.md`).
- **All scanned** → `format=scanned`, `extraction_method=ocr:tesseract`. Text sidecars in
  `text/` are OCR (error-prone); **no dollar amounts in `index.csv`** — read raw PDFs.
- **Join key:** `index.csv.candidate` = `election_results/st_george_results_by_candidate.csv`
  `.candidate` (both UPPER-CASE, exact) for the same year — **40/40 pairs join, 0 unmatched**.
  `candidate_match=inferred` marks 14 rows whose OCR name was assigned by set-elimination.
- Regenerate: `python3 campaign_finance/build_index.py`. Full detail in
  `campaign_finance/CLAUDE.md`.
