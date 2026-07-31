# expand-city-sources — Taylorsville expansion report

**Date:** 2026-07-06 · **City:** Taylorsville (Salt Lake County, ~60k, inc. 1996) · **Skill:**
`.claude/skills/expand-city-sources/`

Six additive source datasets built on top of the standard minutes/votes/comments/elections
layer. Each has its own `CLAUDE.md` + `AVAILABILITY.md` and **individually passes
`validate_dataset.py`**; **no existing dataset was modified**; parent docs (`README.md` +
`CLAUDE.md`) written once by the orchestrator. Portal family exercised: **CivicPlus /
CivicEngage Central (Akamai edge, 403s bare bots) + Utah PMN + jobs.utah.gov HCD + YouTube**.
The distinctive Taylorsville facts driving this run: **the city CMS 403s bare bots**
(`scripts/polite_fetch.py` browser UA used for every city fetch), **packets are
current-cycle-only with no archive**, **Utah PMN body 720 is the sole independent ordinance
source** (American Legal 403 + consolidated-only; not a municipalcodeonline client), and the
city is **audio-only with a PR-only YouTube channel**.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Method | Key caveats |
|---|---|---|---|---|
| 1 | Packets → `packets/` | **7 current-cycle docs** (June–July 2026, ~11.6 MB) | CivicEngage "Document Folder Box" widgets on 3 dedicated packet pages (council / PC / RDA); `polite_fetch.py` browser UA (Akamai 403s bots); `/home/showpublisheddocument/<docId>/<token>`. | **HONEST PUBLISHING GAP — current-cycle-only, no archive.** Staff overwrite the widget each cycle (verified live: 1/2/4 docs). The Agendas-&-Minutes year folders (2008→2026) carry **Agendas | Minutes | Audio**, and the archived *agendas* are **thin 1–2-page outlines, not staff-report bundles** (2026-06-09: 0.66 MB agenda vs a separate 8.09 MB/45 pp staff report). 2020–2026 packets **unrecoverable** from the portal (`unrecovered.csv`). Snapshot joins by date to just **1** existing meeting (2026-06-03 Council). |
| 2 | Housing → `housing_plans/` | **14 docs** (~172 MB): 2025 General Plan (9 chapters), MIH element (GP Ch.8 + Ord 23-03), state 2023/24/25 MIH compilations + SB 34 summary | City `taylorsvilleut.gov` (sitemap-page-1 → `/government/general-plan` + `/moderate-income-housing-plan`; `polite_fetch.py`). State `jobs.utah.gov` HCD `/reporting/documents/{23,24,25}reports.pdf` + `sb34.pdf`. `pdftotext -layout`; state reports sliced to per-city page ranges. | **General Plan has NO printed adoption date** (dated 2025 by Ch.3 wording + Oct/Nov 2025 export). **Published only as 9 chapter PDFs** (no consolidated file; ids non-sequential — harvest by anchor text). **MIH element = GP Chapter 8**; the formally-adopted artifact is standalone **Ordinance 23-03, PASSED 2023-02-01** (PC 6-0 on 2023-01-24) — **joins the vote layer**. State compilations sliced by the HCD **form first-field marker** (never an "isolated header"), grep-verified zero Syracuse/Tooele bleed. **SB 34 p165–166 = source-side mojibake** (strategy matrix; p158–164 clean). |
| 3 | Ordinances → `ordinances/` | **90 ordinances (2020+)** linked to motions; 84 with a retained independent PDF (588 MB); **71% land-use** (64/90) | **Utah PMN council body 720** (`utah.gov/pmn/list/notices.html?id=720&page=<big>`, one cumulative GET) — `adopted` (signed final) + `meeting_material` (2020 Agenda-Summary bundles); `polite_fetch.py`. Join = ordinance no. cited in `all_votes.csv` motion text ∩ the PMN PDF. | Confidence **75 high / 9 medium / 6 within_source** (`within_source` = motion-derived, `high` **by construction, NOT** an independent cross-match). **⚠ Parallel ordinance/resolution number series** — `Ordinance NN-NN` ≠ `Resolution NN-NN`; keyed on **instrument word + number** (6 ord-cited numbers exist on PMN only as a resolution → `within_source`). **9 medium** = signed adopted PDF but number absent from the motion text (vote-citation gap; all 9 adopted). 81 text / 3 scanned (RICOH→tesseract) / 6 na. **American Legal 403 + consolidated-only; not a municipalcodeonline client** — PMN body 720 is the sole independent source. ~129-doc **2012–2019 back-catalog** on the same body, out of scope below the 2020 floor. |
| 4 | PMN backfill → `pmn_backfill/` | **2 genuinely-missing council meetings recovered** + **15 OCR-upgrade candidates flagged** | Utah PMN entity 284 → bodies **council 720 / PC 722 / RDA 721** / CDRA 2770. Cumulative single-GET history (`page=300`), keyed on each attachment's **internal meeting date** (posting dates lag; PMN often carries the *previous* meeting's minutes), set-difference vs the repo indices (±1 day). | **2 recovered** = the **2020-01-29** and **2024-01-31** *Let's Talk Taylorsville* 5th-Wednesday town halls (non-standard, **no roll-call votes** — do not feed to the vote extractor). **PC = 0 genuine gaps; RDA = no separate documents** (in-recess with council, matching `body=RDA` modeling); CDRA 0 attachments; 4 false positives (mislabeled filenames) resolved. **15 OCR-upgrade candidates** (`ocr_upgrade_candidates.csv`): the repo holds these only as RICOH scans (`format=ocr`); PMN posts a born-digital text PDF of the same meeting (7 of 10 PC candidates are DRAFT vs the repo's APPROVED scan). **Flagged, NOT merged.** Repo is otherwise a PMN superset. |
| 5 | Transcripts → `transcripts/` | **141-video channel mapped; 1 ASR caption sampled** | `youtube.com/taylorsvillecity` via `yt-dlp --flat-playlist` → `channel_map.csv` (upload_date 102/141 resolved; the 41 blanks all promotional). Single meeting video's ASR pulled to VTT → cleaned text. | **HONEST GAP: AUDIO-ONLY city / PR-ONLY YouTube channel** — Taylorsville streams meetings live but does **not** archive them as video. `category` = `meeting_planning_commission` 1 / `event_livestream` 4 / `promotional` 136; no Streams tab, no meeting playlist. Exactly **1** genuine meeting video (`0ui3x38KRRo`, 2024-05-15 PC livestream) → the sample (`caption_type=asr`, joins PC by date). **Whisper NOT run** (owner's call). ASR never authoritative. Future routes: **OpenUtah** (`taylorsville.openutah.org`, ~8 transcribed, robots-limited — metadata lead only) or **Whisper over the city "Audio Recordings"** archive. **SAMPLE-ONLY by owner policy.** |
| 6 | Campaign finance → `campaign_finance/` | **71 filings** / Mayor + 5 district seats (2017–2026); **100%** join to `election_results` | City **self-hosts** (Utah Code 10-3-208 → city recorder): `/government/elections/financial-disclosures` + `<YYYY>-financial-disclosures` subpages, `showpublisheddocument/<docId>`; `polite_fetch.py` (site 403s bots). Section headers supply the candidate. | **ACQUISITION LAYER ONLY** — no dollar extraction yet (`extraction_method=none`; **28 born-digital text + 43 scanned**). **TWO regimes** (`filing_regime`): **`annual`** (**50** — the March-1 statement **every sitting official files yearly**, even off-cycle 2017–2026, why the record is dense off-year) + **`election_cycle`** (**21**: Primary/Pre-General/Final, present **2021** (12) & **2023** (9)). **100% candidate-join** (71/71; **Overson→Mayor** hard-map — she was D2 in 2011/2015); 18 winner-filings + 3 by Larry Johnson (lost 2021 D5). **DOUBLE-COUNT TRAP: do NOT sum filings** (per-PDF `filing_type`/`filing_phase`; run `cycle_totals.py`). `date` **inferred** from phase+year (read the PDF "Received" stamp at structuring). **Gaps: 2019 & 2025 election-cycle filings never/not-yet posted** — not Wayback-recoverable. Not EasyVote / not `disclosures.utah.gov`. |

**Core layer untouched:** council+RDA 613 motions / 2,457 vote rows (150 minutes), PC 324
motions / 961 rows (91 minutes), `db/taylorsville.db`, election results — all unchanged.

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)

1. **15 born-digital PMN copies of the repo's RICOH-scan minutes (highest-value signal).** The
   mid-2025 RICOH-OCR production switch left **24 council + 31 PC** minutes as image-only scans
   (`format=ocr`). For **15** of those meetings, PMN posts a **born-digital text PDF of the same
   meeting** — enumerated in `pmn_backfill/ocr_upgrade_candidates.csv`. Swapping the born-digital
   text in would retire the OCR noise. **NOT done here** (do not replace `meeting_minutes/` /
   `planning_commission/` files in place); 7 of the 10 PC candidates are DRAFT minutes (repo has
   the APPROVED scan) — better as a searchable text sidecar than a like-for-like swap. A
   deliberate, human-reviewed merge is the follow-up.
2. **Campaign-finance is a two-regime structure, not one filing stream.** Taylorsville City Code
   2.36.040 mandates an **annual March-1 statement from every sitting official (50 filings, even
   off-cycle)** *and* **election-cycle candidate reports (21)**. The dense off-year record is the
   annual regime, not extra election filings — reading it as one stream would badly overcount
   activity. `filing_regime` separates them; the double-count trap (multiple per-PDF reports per
   race) still applies within `election_cycle`.
3. **Campaign-finance ↔ elections 100% corroboration.** All 71 filings across Mayor + 5 district
   seats **join to `election_results/taylorsville_races.csv`** on candidate + office/district +
   year — a clean two-way corroboration of the elected roster (incl. the Overson D2→Mayor drift,
   hard-mapped). No election-record gap surfaced from the CF side; no filing proved a race the
   election dataset lacks.
4. **Packets are current-cycle-only — a publishing gap, not a scraper miss.** The staff-report
   bundles behind each agenda item exist **only on a rotating widget** and are never archived;
   the year-folder "agendas" are thin outlines. For a 2020→present research window this is a
   **hard, honest gap** (the June-9 PC case shows the 8.09 MB/45 pp staff report living only on
   the rotating page while its 0.66 MB agenda is the only archivable artifact). Wayback captures
   of the three packet pages at different past dates are the only — heavy, low-yield — partial
   recovery lead.
5. **Ordinances rest entirely on Utah PMN body 720.** With American Legal 403-protected +
   consolidated-text-only, the city hosting no adopted-ordinance archive, and Taylorsville not a
   municipalcodeonline client, **PMN body 720 is the single independent ordinance-document
   source** — and a good one (signed finals + 2020 agenda-summary bundles). The **parallel
   ordinance/resolution number sequences** are a structural fact (6 ord-cited numbers exist on
   PMN only as a same-numbered *resolution* → `within_source`, uncorroborated); never collapse
   the two series.

## TODO follow-ups worth queuing

- **[high] Promote the 15 PMN born-digital minutes over the repo's RICOH scans** — reconcile
  `pmn_backfill/ocr_upgrade_candidates.csv` against `meeting_minutes/`/`planning_commission/`,
  swap the born-digital text in for the 15 OCR meetings (mind the 7 DRAFT-vs-APPROVED PC cases —
  sidecar, not swap), re-run `extract_votes.py` + validators, rebuild db + weeks.
- **[med] Consider merging the 2 recovered town-hall meetings** — the 2020-01-29 / 2024-01-31
  *Let's Talk Taylorsville* sessions are real council-body meetings but non-standard (no votes);
  if merged, add to `minutes_index.csv` marked town-hall/no-vote and rebuild db + weeks.
- **[med] Structure the campaign-finance layer** — run `/cf-vision-transcribe` on the 43 scanned
  filings, build `contributions.csv`/`expenditures.csv`/`filing_totals.csv`/`cycle_totals.csv`
  via `build_finance.py`, replace the inferred `date`s with the PDF "Received" stamps, and honor
  the two-regime split + the per-PDF double-count trap. **Re-probe the 2025 page** for the
  not-yet-posted election-cycle filings.
- **[med] Real meeting transcripts via OpenUtah / Whisper** — evaluate OpenUtah's ~8 transcribed
  Taylorsville meetings and/or run Whisper over the city's published meeting **audio** (portal
  "Audio Recordings" column); if adopted, join to minutes/votes on the Wednesday (Council) /
  Tuesday (PC) grids. High-value candidates = contested rezone / budget hearings.
- **[low] Packets — Wayback reconstruction** — Wayback captures of the three current-cycle packet
  pages at different past dates may each hold a different cycle's `showpublisheddocument` links,
  allowing partial historical-packet recovery. Heavy, low-yield (large PDFs rarely captured).
- **[low] Ordinance refresh + back-catalog** — re-crawl PMN body 720 (`page=400`), diff new
  attachments against `index.csv`; the 2012–2019 back-catalog (~129 numbers) is retrievable from
  the same body if the 2020 floor is ever lowered.

## Note on the source index

Per the orchestrator's scope, this run rebuilt **only** `taylorsville_city_council/sources.csv`
+ `SOURCES.md` (`python3 scripts/build_sources_index.py taylorsville` — **429 documents, 99.3%
with recorded URLs**, all six new datasets folded in). The shared `sources_summary.md` was
**not** regenerated (the orchestrator's serialized final step, run once after all concurrent
city expansions finish).
