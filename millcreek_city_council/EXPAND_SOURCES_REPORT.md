# expand-city-sources — Millcreek expansion report

**Date:** 2026-07-06 · **City:** Millcreek (Salt Lake County, ~62k; **incorporated Dec 28
2016** — the short record is the city's entire life, not a 2020-floor gap) · **Skill:**
`.claude/skills/expand-city-sources/`

Six additive source datasets built on top of the standard minutes/votes/comments/elections
layer. Each has its own `CLAUDE.md` + `AVAILABILITY.md` and **individually passes
`validate_dataset.py`**; **no existing dataset was modified** (the sole edit outside the new
folders is a documented bug fix to `fetch_new.py` — the stale PMN council body id `1031 →
5741`, see below). Parent docs (`README.md` + `CLAUDE.md`) carry the compact per-dataset
summaries. Portal family exercised: **CivicPlus AgendaCenter + municipalcodeonline.com S3 +
jobs.utah.gov HCD + Utah PMN + YouTube/@UtahRecord (OpenUtah mirror) + CivicPlus/Wayback**.
The distinctive Millcreek facts driving this run: the **combined Agenda+Packet PDF is already
on disk** (packets go INDEX-ONLY with `path`), the **ordinance code host exposes a
publicly-listable S3 back-catalog** (550 ordinances, independent of the minutes), the city has
**genuine in-packet resident comments** (Provo pattern) and **genuine meeting video via a
third-party mirror** (not the city's own PR-only channel), and the base refresh script carried
a **stale PMN council body id**.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Method | Key caveats |
|---|---|---|---|---|
| 1 | Packets → `packets/` (**INDEX-ONLY**) | **552 docs** — 340 `full_packet` (Council 186 / CRA 54 / PC 100, 2018–2026) + 212 thin `agenda_packet` | `POST /AgendaCenter/UpdateCategoryList` (catID **3** Council / **7** CRA / **2** PC), years 2016→2026; classify each row's agenda title. Sizes from HEAD / retained siblings. | **The combined Agenda+Packet PDF is served at the same `docId` as the Minutes view — those exact PDFs are already retained** in `meeting_minutes/raw/` (979 MB) + `planning_commission/raw/` (499 MB). Re-storing would duplicate ~1.2 GB, so each `full_packet` row carries **`path`** into the sibling raw dir (`stored_locally=yes`, 335/340) — the retention rule is met because the bytes ARE in the repo. **PC `full_packet` rows bundle verbatim resident-comment letters = the IN-PACKETS comment corpus** (flagged, not extracted). 5 items had no combined PDF → `unrecovered.csv`. Join `(date, body[, meeting_type])`. |
| 2 | Housing → `housing_plans/` | **7 docs**: General Plan (MIH embedded) + Ord 22-44 (MIH element of record) + city Aug-2024 Housing Report + state 2023/24/25 MIH compilations + SB 34 summary | City `millcreekut.gov/DocumentCenter/View/<id>` (sitemap + P&Z page `/151`); Ord 22-44 from **Utah PMN** (`utah.gov/pmn/files/893155.pdf`). State `jobs.utah.gov` HCD `NNreports.pdf`/`sb34.pdf`. `polite_fetch.py`; `pdftotext -layout`; state sliced to Millcreek page ranges. | **No standalone MIH-element PDF** — it is **embedded in the General Plan** (Ch. 4 + appendix); the self-contained artifact is **Ordinance 22-44** (2022-09-26), which **joins the vote layer** (council adopted it Sept 26 2022 + upstream PC recommendation). **GP cover date anomaly** — `View/3193` reads "Amended December 12 2026" (future-dated placeholder); cite in-text content, not the cover. **State "annual report" = statewide compilation** (cite the page range: 2023 pp.413–429 / 2024 pp.399–413 / 2025 pp.507–521 / SB34 pp.81–82). **2023 & 2024 compilations bleed adjacent Murray text** into Millcreek's range (2025 + SB 34 clean). Born-digital → no minutes-corpus OCR garble. Not joined to `db/`. |
| 3 | Ordinances → `ordinances/` | **550 adopted ordinances 2016-01→2026** (`ORD YY-NN`) linked to council votes; 525 PDFs stored (857 MB); **~39% land-use** (213) | **municipalcodeonline.com S3 back-catalog** — bucket `municipalcodeonline.com-new` (region **us-west-2, path-style only** — the dotted virtual-host name fails TLS), `?list-type=2&prefix=millcreek/<sub>/`; 812 objects → 550 distinct ordinances. `polite_fetch.py`; date via pdftotext→tesseract→vision ladder. Join = `Ordinance YY-NN` cited in `all_votes.csv` motion text ∩ the S3 archive. | `match_confidence` **346 high** (cited in a council motion AND the PDF's own month+year match → cross-source corroborated) / **84 medium** (cited but PDF date not independently extractable, or cited on >1 date) / **120 none** (no motion cites it — mostly 2016–18 procedural, pre-named-vote seam). **25 oversize exhibit bundles index-only** (documented exception; live `source_url`, re-fetchable). **13 cited-but-no-document numbers** → `citations_without_document.csv` (a real host-catalog gap, not an extraction miss). **⚠ Ordinance 17-99 is an INAUTHENTIC test/template doc** (John Doe / Jane Doe / Betsy Ross voters, a "(joke)" clause, fictitious `U.C.A. 3.4.5`) — flagged in `note`, kept for provenance, **exclude from analysis**. |
| 4 | PMN backfill → `pmn_backfill/` | **1 council meeting recovered** + **1 verified-dead file**; **3 PMN bodies discovered** | Utah PMN GET-only entity chain (**do not hardcode ids**): `entities.html?id=3` → Millcreek **id=1279** → `publicBodies.html?id=1279` → **Council 5741 · PC 5815 · CRA 6367**; one cumulative `notices.html?id=<body>&page=300` per body; per-date set-difference (±4-day) vs the repo indices. | **Repo is a near-total superset** — the city **double-posts to AgendaCenter**, so PMN is thin. **Recovered:** 2017-11-21 Board of Canvassers general-election canvass (seated D2 Marchant / D4 Uipi; tally-only, pre-2022 seam; tesseract OCR sidecar). **Unrecovered:** 2018-03-20 CC Budget Work Meeting (PMN attachment 404, also budget-spreadsheet-only on AgendaCenter — already in `minutes_unrecovered.csv`). **This run surfaced the stale council body id** the base `fetch_new.py` carried (`1031`) and corrected it to the live **5741**. |
| 5 | Transcripts → `transcripts/` | **92 meeting videos mapped** (58 Council + 34 PC, 2025-01-06→2026-06-22); **10 ASR captions sampled** | Playlist "Millcreek City Meetings" on **`@UtahRecord`** ("Utah Record — Public Meetings") via `yt_dlp --flat-playlist` → `index.csv`; 10 auto-caption VTTs pulled + cleaned to `text/` with the ASR disclaimer. | **Real meeting video EXISTS** (unlike the audio-only South Jordan / Taylorsville siblings) — but on the **third-party `@UtahRecord` mirror** (same operator as the searchable `millcreek.openutah.org` transcript front-end), **not** the city's own `@millcreekutah3408` channel, which is **PR-only** with no meeting video. **2025+ only** — the pre-2025 record is minutes-PDF only. **SAMPLE-ONLY by owner policy** (10 stored, 82 link-only rows, all re-fetchable). **Whisper NOT run.** ASR is contextual/color only — **never extract votes/tallies/quotes**; the `body` label is the mirror's title (**unverified** — e.g. the 2026-06-01 "CityCouncil" video is actually a URCA board meeting). Join by meeting date. |
| 6 | Campaign finance → `campaign_finance/` | **41 filings / 4 cycles** (2019/2021/2023/2025), Mayor + Council D1–D4; **39/41 join `election_results`** | Live CivicPlus `/547/Disclosures` + `/161/Elections` (2021/2023/2025); **2019 from Wayback CDX** on the legacy `millcreek.us` + `millcreekut.gov` domains (404 on live). `polite_fetch.py` (⚠ live DocumentCenter needs the `/<slug>` suffix — bare `/View/<id>` 404s). | **ACQUISITION LAYER ONLY** — no dollar extraction yet (`extraction_method=none`; 31 born-digital + 10 scanned). **39/41 filings (20/22 candidate-cycles) join** on person + year + district (normalize UPPER-CASE `(NON)`/`(NP)`). **2 non-joins are appointment artifacts** (`in_election_results=no`): **Jackson 2025 Mayor** + **Handy 2025 D3**, both appointed **Nov 2025**, neither elected to that seat. Inverse: **2023 Mayor (Silvestrini) + D1 (Catten)** were cancelled-uncontested → no campaign → correctly no filing. **DOUBLE-COUNT TRAP — do NOT sum filings** (**2021 = one combined bundle per candidate**; 2019/2023/2025 = interim + summary). Some 2025 filings are **city-redacted** (donor PII removed). **2016/17 unpublished** (pre-online paper era, `unrecovered.csv`). |

**Core layer untouched:** council+CRA 2,257 motions / 5,580 vote rows (372 minutes), PC 759
motions / 2,840 rows (149 minutes), `db/millcreek.db` (3,016 motions / 6,721 votes / 34
referrals), election results (22 races) — all unchanged.

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)

1. **The IN-PACKETS resident-comment corpus is now acquirable (highest-value signal).**
   Millcreek publishes **genuine verbatim resident comments**, but only inside the PC
   `full_packet` PDFs as appendices to land-use staff reports (the Provo pattern) — there is
   no standalone comments page. `public_comments/AVAILABILITY.md` correctly marks the folder
   **IN-PACKETS**, not honest-empty. The `packets/` index now **pins exactly where those
   letters live** (PC full-packet rows, `path` into `planning_commission/raw/`),
   so a Provo-style page-walk harvest → `all_comments_clean.csv` is a well-scoped follow-up,
   not a discovery problem.
2. **The ordinance layer is a genuine independent second source.** The
   **municipalcodeonline.com S3 back-catalog** (550 ordinances 2016–2026) corroborates each
   ordinance NUMBER independently of the council minutes — which is why **346 rows reach
   `high` confidence** (motion citation ∩ the PDF's own printed month+year). It also surfaced a
   **data-quality defect on the code host itself**: **Ordinance 17-99 is an inauthentic
   test/template document** (fictitious voters, a "(joke)" clause) — a source defect to exclude,
   flagged in `note`, never silently dropped. **13 cited numbers have no document** on the host
   (`citations_without_document.csv`) — a real catalog gap.
3. **Millcreek has real meeting video — on a third-party mirror, not its own channel.**
   Unlike the audio-only siblings, Millcreek's deliberations are on YouTube via **`@UtahRecord`
   / `millcreek.openutah.org`** (2025+). The city's own channel is PR-only. This makes a **real
   Whisper/ASR deliberation-transcript layer genuinely reachable** for 2025+ (the 92-video map
   is the index; only 10 ASR samples stored by owner policy) — a stronger future position than
   cities with no meeting video at all.
4. **Campaign-finance ↔ elections corroboration exposes the appointment regime.** 39/41 filings
   join `election_results`; the **2 non-joins are the Nov-2025 council appointments** (Jackson
   D3→Mayor, Handy→D3) — the CF side independently corroborates that the 2025 mayoral/D3 seats
   were **appointed, not elected** (matching the elections dataset's "no 2025 mayoral race row").
   No election-record gap surfaced from the CF side. The **2021 single-combined-bundle filing
   style** (vs interim+summary elsewhere) is the key double-count trap for the structuring step.
5. **The base refresh script carried a stale PMN body id.** `fetch_new.py` probed the council on
   PMN "body **1031**"; the live 2026-07-06 entity chain resolves Millcreek's council to **5741**
   (1031 is absent from the current publicBodies list). **Fixed this run** (id + docstring in
   `fetch_new.py`, plus the `README.md`/`CLAUDE.md` one-liners; PC 5815 / CRA 6367 recorded for
   completeness). `python3 fetch_new.py --probe` re-verified: parses, 0 new items, note now reads
   "PMN body 5741".

## TODO follow-ups worth queuing

- **[high] Harvest the IN-PACKETS resident comments (Provo-style).** Page-walk the PC
  `full_packet` PDFs enumerated in `packets/index.csv` (`path` → the retained raw
  files already on disk), classify + extract the verbatim resident-comment appendices to
  `public_comments/all_comments_clean.csv`, and retire the "pending harvest" note in
  `public_comments/AVAILABILITY.md`. Mind the corpus-wide OCR garble.
- **[med] Structure the campaign-finance layer.** Run `/cf-vision-transcribe` on the 10 scanned
  filings (2019 + Uipi-2021), build `contributions.csv`/`expenditures.csv`/`cycle_totals.csv`
  via `build_finance.py`, and honor the double-count trap (2021 = one combined bundle/candidate;
  interim+summary elsewhere) + the 2025 city-redacted PII limit before quoting any totals.
- **[med] Real meeting transcripts via @UtahRecord / OpenUtah / Whisper.** Millcreek genuinely
  has 2025+ meeting video — retrieve the remaining 82 mapped ASR tracks and/or run Whisper over
  the mirror audio for higher-quality transcripts; join to minutes/votes on the Monday (Council)
  / Wednesday (PC) grids, **verifying each `body` label against the matching minutes** (URCA
  mislabels). High-value candidates = contested rezone / budget hearings.
- **[low] Merge the recovered 2017-11-21 Board of Canvassers minutes.** The pmn_backfill
  recovery is a real council-body meeting the audited layer lacks; if merged, add to
  `meeting_minutes/minutes_index.csv` (tally-only canvass, pre-2022 seam) and rebuild db + weeks.
- **[low] Ordinance refresh + the 13 missing-document numbers.** Re-list the S3 prefix for new
  ordinances; re-check `citations_without_document.csv` (mostly recent 2025–26 not-yet-uploaded)
  as the host backfills. Keep `17-99` excluded.
- **[low] F-1 2017 en-dash re-extract** (already noted upstream) — the previously-flagged 2017
  minutes en-dash re-extraction item remains queued; fold into the next minutes re-run.

## Note on the source index

Per the orchestrator's scope, this run rebuilt **only** `millcreek_city_council/sources.csv` +
`SOURCES.md` (`python3 scripts/build_sources_index.py millcreek`, all six new datasets folded
in). The shared `sources_summary.md` was **not** regenerated (the orchestrator's serialized
final step, run once after all concurrent city expansions finish).
