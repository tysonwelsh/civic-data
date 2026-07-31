# Ogden City Council — data repository

Canonical datasets about the **Ogden City Council** (Weber County, Utah), modeled on the Salt
Lake City reference repo, plus a derived weekly view unifying minutes + votes. Built by the
`build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 504 files 2020–2026; 2022 OCR'd — re-OCR'd 2026-07-02) + votes (all_votes.csv)
                      incl. separate RDA (111) + MBA (18) meeting votes via the `body` column
planning_commission/  140 PC minutes + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                      (the appointed technical land-use body; recommendations vs final actions; 51 OCR'd;
                      the 2020-23 gap CLOSED 2026-07-19 — 63 recovered born-digital drafts)
db/                   NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL bodies'
                      votes by real keys + reconstructed cross-body referrals. Start here: db/SCHEMA.md
public_comments/      all_comments_clean.csv (EMPTY — submit-only city) + minutes_speaker_log.csv
                      (635 in-person speaker notes, NOT comments) + AVAILABILITY.md (the audit)
election_results/     Weber County results filtered to Ogden council + mayor races
geo/                  precinct boundaries + address/point -> council district tool (Districts 1–4)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (CITY="Ogden", MEETING_WEEKDAY = Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. Votes + minutes carry the
meeting date; `build_weeks.py` buckets every record onto that weekly grid. Elections are
point-in-time (Nov, odd years), NOT in the weekly bundles — they join by **person + year +
district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (4,992 member-vote rows across
  1,506 motions). Filter `body` to separate Council (1,377) from RDA (111) / MBA (18). There
  are **no** genuine public comments to aggregate (submit-only city); do NOT use
  `minutes_speaker_log.csv` (635 in-person paraphrases) as a comments dataset.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/ogden_races.csv`) ↔ votes.
- **By geography**: `geo/address_to_district.py` resolves an address to Districts 1–4.

## Council structure
**Council–Mayor (strong-mayor) form. 4 District + 3 At-Large = 7 council members.** The
**Mayor does NOT vote.** Caldwell = Mayor 2020–2023; Nadolski = voting council chair 2020–2023,
then Mayor from 2024-01-02. The extractor excludes the mayor **per-year via the roster** (never
by name globally), so Nadolski correctly votes 2020–23 and is excluded 2024+. At-large + mayor
are city-wide; geo maps addresses to Districts 1–4.

## Data notes / caveats
- **Votes**: 1,506 motions / 4,992 member-vote rows / 87 contested. Many motions pass on a tally
  / "ALL VOTING AYE" with **no per-member names** → `names_recorded:false` (no guessed members).
  Named roll-calls (`VOTING AYE - COUNCIL MEMBERS … VOTING NO - …`) are parsed member-by-member;
  the NO list is captured across line wraps and terminates at the sentence period. Treat the
  contested *rate* as "among recorded roll-calls." See `meeting_minutes/CLAUDE.md`.
- **Subject enrichment (2026-07-02, plan 3.5)**: 500 bare adoption motions ("ORDINANCE WAS
  PASSED AND ADOPTED AS OGDEN CITY ORDINANCE 20xx-N…") carry the item's **verbatim** long-title /
  agenda heading appended to `motion` inside `[ENTITLED: "…"]` / `[AGENDA ITEM: "…"]` delimiters
  (matched by instrument number; never a summary). This is what makes them classifiable in
  `motions_std.csv` (Land-Use/Budget/…). The bare clerk sentence is always the prefix before
  the bracket. See VERIFICATION.md "Remediation 3".
- **`body` column**: `body ∈ {Council, RDA, MBA}`. Ogden runs RDA and MBA as **separate
  meetings** (own minutes files / slugs), tagged from the slug (+ rare in-meeting transitions).
  **2022–2023 RDA/MBA are undercounted (0 motions those years)** — the separate 2022 and 2023
  RDA/MBA meeting sets were not acquired (2023: DocCenter 29548/29549; a 2022 set is referenced
  in the council minutes but was likewise never harvested; ~20–25 RDA + ~5–8 MBA meetings
  missing per year). RDA coverage = 2021 in-meeting transitions + 2024–26 separate meetings.
- **2022 minutes are OCR'd** (the 2022 compilation is a scan; other years are born-digital or
  cleanly re-OCR'd). Repaired 2026-07-02: re-OCR'd with tesseract + re-carved into 73 files /
  38 dates (the earlier carve used the scan's garbled embedded OCR, dropped 8+ meeting dates,
  undercaptured 47% of 2022 roll calls, and mis-tagged ~33 Council motions as RDA — an earlier
  version of these docs wrongly blamed 2023 and claimed council coverage was complete). OCR'd
  names can still carry stray spaces / merged words; the parser matches space-insensitively +
  fuzzily over a known-surname list. Two preserved 2022 clerk typos: the 2022-03-01 regular
  meeting opening prints "March 1, 2021", the 2022-06-07 work session prints "June 2, 2022"
  (both dated per running header + weekday); the Jan 2022 chair-election roll calls print
  departed member STEPHENS (kept verbatim → 2 flagged rows in the validation report).
- **Comments**: Ogden is **submit-only** — no public archive of genuine written/online comments
  (`all_comments_clean.csv` empty). In-person speakers are in `minutes_speaker_log.csv` (record
  notes, not public-submitted comments). Full audit: `public_comments/AVAILABILITY.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **140 meetings · 988 motions · 4,764 member-vote rows · 150
  contested** (2026-07-19; 140 = 138 + 2 sibling work-session docs on 2021-08-18/2021-12-15,
  both 0-motion so vote counts are unchanged). Roster (19 appointed commissioners incl. the recovered early-2020
  cohort Wright/Herman/Castillo) in `planning_commission/roster.csv` (built from attendee
  headers — no election; cross-checked vs Council appointment votes). `result` encodes the
  **recommendation-vs-final-action taxonomy** (`Positive/Negative recommendation N:N` forwarded to
  Council vs `N:N Approved/Denied (Final Action)` for PC-delegated CUP/design/site-plan). **Caveats:**
  **51 of 138 minutes are OCR'd** (UPPERCASE roll-calls, stray-space names normalized). The old
  "2020–2023 PC coverage is sparse" gap was **CLOSED 2026-07-19**: 63 meetings recovered from
  standalone DocumentCenter draft-minutes PDFs (+2 packet carves, 1 .docx), every one with
  following-meeting approval verified; a documented-corrections hook
  (`planning_commission/vote_corrections.csv`) fixes a recurring failed-motion both-lists-say-aye
  clerk typo. These draft-sourced recoveries are now tagged in the `provenance` column
  (added 2026-07-19) so they filter apart from audited primary: **`doccenter_draft`** (525
  motions, the DocumentCenter drafts) and **`packet_carve`** (34 motions, 2020-04-15 +
  2021-11-03 packet carves); audited portal minutes stay `minutes` (429). See
  `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no reliable file number in
    Ogden's recorded motions) and **body-scoped** — `0 applications span >1 body` by design.
    `motion.app_match_method` ∈ `name`(medium, heuristic — 58) / `singleton`(high, 610) /
    `override`(high) tells you how solid each grouping is (counts grew again 2026-07-19 when
    the PC gap recovery added 543 PC motions; 656 applications total).
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — scored links across Council←PlanningCommission
    and Council←agency (RDA/MBA). **6 links as of 2026-07-19** (2 override-high + 4
    subject-medium: moderate-income housing element, Airport CRA, Union Station Framework
    Plan, Adams CRA) after the **surname-token guard** landed (2026-07-19, PV Tier-B wave)
    — `medium` = spot-check before quoting. The guard (OGDEN-LOCAL, in `db/build_referrals.py`
    — see its header) dropped **7 boilerplate/surname false positives** the raw matcher had
    been emitting (e.g. Ord 2024-12 code-amendments vs RDA Ogden Bend Master Plan; Ord 2026-7
    clean-energy vs an RDA ADJOURN motion matched on the lone surname `lundell`; two different
    Gibson-Avenue parcels; Continental-vs-Airport CRA): a subject link must now share genuine
    CONTENT (not just motion/plan boilerplate + a member surname), and a name-anchored link
    needs >=2 distinctive non-name tokens. The
    **Ogden Bend PC↔RDA** link is now FORCE-LINKED with stable name-based app_keys (its
    organic subject link detached when the PC recovery regrouped applications).
    The **171 Franklin Street override** row (the second override-high link) was RE-KEYED
    2026-07-19: it had drifted through successive re-binds and was mis-bound to two
    unrelated 2024/2026 RDA motions; it is now bound (verified in both primary docs) to the
    correct pair — PC 2022-02-02 street-vacation recommendation (m7) → Council 2022-08-09
    special-meeting 171 Franklin rezone/vacation (Ord 2022-39/40). The "high" referral it
    emits is now safe to quote. Tuning is in
    `db/referral_overrides.csv` (5 documented suppress rows — 4 of them the surname-token
    false-positive class the matcher used to count shared mover/seconder surnames as subject
    signal). **As of the 2026-07-19 surname-token guard those suppress rows are REDUNDANT**
    (rebuilding with them removed yields the identical 6 links — the guard, not the
    suppression, now rejects the class), but they are KEPT as documentation; the build
    handles now-redundant suppress rows gracefully. Overrides key by content-derived
    `app_key`, which survives rebuilds — but VERIFY each row still binds to the intended
    motions after any re-extraction, which is exactly how the Franklin row went stale;
    correct mistakes there / in `db/overrides.csv` and rebuild (idempotent). NOTE: the guard was
    PORTED into the shared `scripts/referrals_lib.py` template 2026-07-20 as four opt-in params
    (`member_names`/`template_stopwords`/`content_veto`/`name_anchor_min`, all defaulting to a
    no-op); `db/build_referrals.py` is now a thin stub that ENABLES them via `main(..., content_veto=True,
    name_anchor_min=2)` — no more monkeypatches. Ogden is the ONLY city that turns the guard on;
    the port left all 30 other cities' referral tables byte-identical. Enabling it elsewhere is a
    logged TODO follow-up (needs per-city evidence review).
  - **Ogden address nuance:** a "shared address" is an approximate **grid intersection / street
    crossing**, not a parcel, so address-alone is co-location (low). Use `v_referral_chain` /
    `v_project_timeline`. Build: `python3 db/build_db.py` then `python3 db/build_referrals.py`.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal** (80 council, 149 PC, 7 RDA);
  `weeks/<tue>/summary.md` surfaces council ones. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
- The **RDA subset** (`body=RDA`) is the highest-value slice for development/subsidy analysis.
- Validation: `meeting_minutes/votes/_validation_report.txt` (per-year rosters confirm no mayor
  leak; remaining flags = 2 year-boundary tally artifacts + the 2 Jan-2022 STEPHENS clerk typos
  preserved from source).

## Refreshing (incremental updates — Phase 3.3)

- `python3 fetch_new.py --probe` (default; read-only) reports new minutes vs the indexes — council/
  RDA/MBA from the DocumentCenter "Approved Minutes" hub, PC from the AgendaCenter; `--fetch
  [--dataset <name>]` downloads them (raw PDFs retained in `<dataset>/raw/`), converts, appends index
  rows, and runs extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
  CAVEAT: PC minutes are scanned — fetch refuses to ingest text-less PDFs and tells you to OCR
  (300 dpi + tesseract, per VERIFICATION.md "Remediation 2").
- After any fetch, rebuild derived layers: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers (**CivicPlus CivicEngage** DocumentCenter/AgendaCenter + PMN + YouTube); each has its
own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing data. Join to `all_votes.csv`/minutes
by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **166 agendas STORED** (PC 162, Council 4). Ogden's AgendaCenter has **no packet type** —
  only thin agendas. Council publishes ~nothing there; **PC agendas are a superset (71 PC dates whose minutes
  the repo lacks)**.
- **`housing_plans/`** — MIH = **General Plan Chapter 7** (amended 2022); 2020 GP update; state 23/24/25 + SB 34.
- **`ordinances/`** — **308 adopted** (107 land-use). **27 high** (Recorder "Synopsis of Ordinance" affidavits) /
  276 within_source / 5 none. **Ord 2025-01 (2025-01-07) has no matching meeting — first 2025 council meeting
  appears un-ingested.**
- **`pmn_backfill/`** — Entity 225; historical CC/RDA/MBA under **combined body 6587** (individual RDA 321/MBA
  322 pages are 6-month-capped). **Recovered 7 of the 2023 RDA minutes** (the "2022–23 RDA/MBA never acquired"
  gap — partially closed) + 1 2024 RDA + 2 2020 MBA. 2022 RDA/MBA + 2023 MBA confirmed **not on PMN** (honest zeros).
- **`transcripts/`** — **ASR** captions, 10 sampled / 683 videos mapped (Ogden City Council YouTube, 2018–2026).
  Recipe: default yt-dlp client (the `android` override returns zero subs here).
- **`campaign_finance/`** — **38 filings** (2019/21/23) self-hosted on per-cycle `/<id>/<YYYY>-Elections` pages.
  **100% election join 2019–2023** (all 12 winners); primaries implied (flagged); **2025 not yet published**.
  Structured dollar layer BUILT (`contributions.csv`/`expenditures.csv`/`filing_totals.csv`/`cycle_totals.csv`;
  25/38 filings both-sides reconcile as-of 2026-07-12) — see `campaign_finance/CLAUDE.md`.
