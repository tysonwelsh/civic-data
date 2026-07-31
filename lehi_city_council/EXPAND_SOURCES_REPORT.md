# expand-city-sources — Lehi pilot report

**Date:** 2026-07-02 · **City:** Lehi (Utah County) · **Skill:** `.claude/skills/expand-city-sources/`
**Outcome:** all six new source types built; every dataset passes `validate_dataset.py`; existing
datasets not modified by this skill. One operational issue (concurrent session) documented below.

---

## ⚠️ Operational issue — concurrent session writing the same repo

During this pilot a **separate top-level Claude session** (scratchpad `0ee36bc8…`) was actively
executing the repo-wide `REMEDIATION_PLAN.md`. Evidence: `_backups/2026-07-02/` created 16:35;
Lehi `all_votes.csv`/`minutes_index.csv`/`db/lehi.db` regenerated 16:32–16:33; `README.md` (16:42)
and `CLAUDE.md` (16:43) rewritten; that session's scratchpad shows `weeks_final.md5` (16:37) and
stgeorge/vineyard/nephi/orem work.

Consequences:
- **No data lost.** The remediation backs up before editing. `_backups/2026-07-02/lehi_city_council/`
  holds the pre-remediation `all_votes.csv` (**6413 rows**) and `minutes_index.csv` (**181 rows**).
  A safety snapshot of the current working copy is also in this session's scratchpad.
- Lehi's existing vote layer currently shows **6148 rows / 175 minutes** — the remediation session's
  in-progress edit, **not** a change made by this skill. Left untouched (backed up; belongs to that run).
- **Live doc collision:** the six new-dataset sections my agents appended to Lehi `README.md`/`CLAUDE.md`
  may be overwritten by the remediation session's rewrite of those files. **Therefore the parent-doc
  consolidation was intentionally deferred.** Each new dataset carries its own self-contained
  `CLAUDE.md` + `AVAILABILITY.md` + `index.csv`, so the datasets are fully documented regardless.
  A ready-to-paste parent-doc snippet is at the end of this report.

**Recommendation for scaling:** never run this skill on a city while the remediation (or any other
session) is writing that city. Add a pre-flight check to the skill (see revision #10).

---

## Per-source results

All datasets: `raw/` retained + `_fetch_log.jsonl` provenance; `index.csv` with the required
columns; `AVAILABILITY.md`; `CLAUDE.md`. `retrieved_date = 2026-07-02`.

### 1. Agenda packets / staff reports → `packets/` — PASS
- **564 files, 327 MB**, 112 meetings (Council 56, PC 56) across the pilot window **2024–2025**.
  452 staff reports + 112 agendas; 555 born-digital, 9 scanned. 0 dead links.
- **Portal finding:** Lehi has no single packet doc. The agenda PDF (`AgendaViewer.php`) embeds
  `/URI` hyperlinks to per-item Legistar staff reports/exhibits (hosts `lehi.granicus.com/services/
  legistar/download/…` and `legistarweb-production.s3.amazonaws.com/…`). Packet = agenda + linked
  attachments.
- **Gaps (logged):** only **5/56 council** meetings hyperlink staff reports vs **45/56 PC** — a city
  publishing gap (council moved onto the linked pipeline at the 2025→2026 boundary), not a scraper
  miss. 163 oversize exhibits (~3.05 GB — plats, traffic/engineering studies) dropped by a 4 MB cap
  and logged in `dropped_oversize.csv` (re-fetchable). Years 2020–2023, 2026, RDA/LBA deferred.
- **Join:** by `date`+`body`; 52/53 council packet dates match `meeting_minutes` exactly.

### 2. Moderate income housing + General Plan → `housing_plans/` — PASS
- **9 PDFs, ~42 MB.** City: General Plan (2022, 136 pp) + Land-Use & Max-Density maps + **MIH element**
  (adopted 2017-12-12, updated 2024-05-28) + its adopting ordinance. State (DWS/HCD): **MIH annual
  reports 2023/2024/2025** (statewide compilations — Lehi page-ranges extracted to `text/`) + **SB 34**
  municipal progress summary.
- **Gaps (verified):** HCD publishes only statewide compilation PDFs, no standalone per-city report
  or compliance letter; pre-2023 compilations superseded/deferred.
- **Reusable state URLs** (stable across all Utah cities): index `jobs.utah.gov/housing/affordable/
  moderate/reporting/`; compilations `.../documents/{23,24,25}reports.pdf`; `.../documents/sb34.pdf`.

### 3. Zoning / land-use ordinances → `ordinances/` — PASS
- **313 unique ordinances** indexed 2020–2026 (**284 = 91% land-use**: Dev-Code text amendments 115,
  zone changes 91, general-plan 45, area-plan 22, …). Two 2026 born-digital "Notice of Ordinance
  Adoption & Summary" PDFs retrieved to `raw/`.
- **Sourcing reality:** no online full-text ordinance archive. American Legal
  (`codelibrary.amlegal.com/codes/lehiut/`) is **403 bot-protected** and current-consolidated-text
  only; the city posts only the **current year's** adoption-notice PDFs; back-catalog lives on PMN
  (opaque ids). So the index was **reconstructed from ordinance numbers cited in the audited council
  minutes** and linked to their motions.
- **Linkage confidence:** high 295 / medium 17 / none 1 (2026-04 Noise — no matching motion, not
  forced). **Caveat:** because the index derives from the motions, `high` is *within-source by
  construction*, not an independent cross-match — documented in the dataset `CLAUDE.md`. See skill
  revision #6.

### 4. Utah PMN backfill → `pmn_backfill/` — PASS
- Full per-year coverage cross-check (Council body **2512**, PC **2651**). **The Granicus-built repo
  is a superset of PMN every in-scope year** (PMN attaches minutes to ~26% of council / ~5% of PC
  notices), so **per-year counts are misleading** — a per-**date** set-difference found the real gaps.
- **6 genuine gaps recovered** (born-digital, screener-clean): Council 2020-02-04, 2020-08-04,
  **2021-07-13 (a missing regular meeting with full roll-call votes — highest value)**; PC 2025-03-06,
  2025-08-07, 2025-09-04. **0 in-scope minutes remain unrecovered.** Kept in `pmn_backfill/` (separate
  from the audited `minutes/` layer) for deliberate review, not merged.
- **Crawl finding:** PMN search is POST/CSRF (disallowed); the escape hatch is that
  `/pmn/list/notices.html?id=<body>&page=N` is **cumulative** — one high page returns a body's entire
  history via GET. Body ids are global, not per-city-sequential.

### 5. Meeting video transcripts → `transcripts/` — PASS (honest map)
- **0 transcripts pulled; 12 meetings mapped** to video (YouTube "Lehi City Public Meetings" +
  `lehi.granicus.com`; mirror `lehi.openutah.org` has 87 AI transcripts Jan 2025→present).
- **Why 0:** `yt-dlp` **not installed** here (the skill's expected fallback path). The OpenUtah mirror's
  verbatim transcript text is served client-side behind `robots.txt Disallow: /api/`, so under the
  polite-scraper rule it was **not** scraped (one summary page retained as evidence).
- **Whisper candidates listed, not run** (housing/high-density hearings, contested votes).

### 6. Campaign finance → `campaign_finance/` — PASS
- **134 filings, 59 MB** (2019: 27, 2021: 20, 2023: 36, 2025: 51), Mayor + Council. **124/134 join to
  `election_results` by person+year; all 12 general-election winners covered.**
- **Where they live (the finding):** the **city recorder's elections page**, NOT `disclosures.utah.gov`
  (which redirects to the city) nor the county. Legacy 2019/21/23 PDFs 404 on the migrated CMS and were
  recovered from the **Wayback Machine**.
- **Gaps (verified):** 12 specific 2023 report PDFs never captured by Wayback and 404 live — logged in
  `unrecovered.csv`; no candidate fully missing. **Surfaced a real discrepancy:** the filings prove Lehi
  held a **2019 primary**, contradicting `election_results/CLAUDE.md` ("no 2019 primary"). Flagged in
  the dataset docs; **not fixed** (additive-only).

---

## Timing (wall-clock, parallel agents)

| Source | Approx |
|---|---|
| Housing | ~12 min |
| Transcripts | ~15 min |
| Ordinances | ~15 min |
| PMN backfill | ~15 min |
| Campaign finance | ~55 min (Wayback throttled downloads) |
| Packets | ~42 min (566-file throttled download) |

Six agents ran concurrently, so end-to-end ≈ the slowest (~55 min) plus verification.

---

## Skill revisions before scaling to the other 12 cities

1. **`polite_fetch.py` — S3 underscore-bucket rewrite.** Granicus attachment buckets like
   `granicus_production_attachments.s3.amazonaws.com` fail Python `requests` TLS (cert/hostname
   mismatch on the underscore); `curl` tolerates it. Auto-rewrite virtual-host → path-style
   (`s3.amazonaws.com/<bucket>/<key>`) when the bucket contains `_`. **Will bite every Granicus city.**
2. **`polite_fetch.py` — add `--max-bytes`.** Check `Content-Length`, skip+log oversize files. Packets
   are multi-GB; this makes "sample and log what you dropped" a one-liner instead of a custom pass.
3. **`polite_fetch.py` — `--batch` per-row subdir** (`url,name,subdir`) so one call fills
   `raw/<date>/` folders.
4. **Transcripts — install yt-dlp first.** `python3 -m pip install yt-dlp` as step 0 (Python is
   present), fall back to the map-only path only if install is blocked. Would have yielded real ASR
   captions here.
5. **Packets — fix the Granicus packet model in the skill.** Not `DocumentViewer.php?file=<hash>`; it's
   agenda PDF → extract embedded `/URI` links → Legistar attachments. Add that as the canonical step,
   and have recon flag agenda→staff-report linkage per body (the council-vs-PC asymmetry).
6. **Ordinances — name the "minutes are the backbone" path.** When no online ordinance archive exists
   (common: American Legal 403 + city keeps only current-year notices), derive number→date→subject
   from motion text in `all_votes.csv`. **State the honest caveat** that this join is within-source
   (`high` by construction) — consider a distinct confidence label (e.g. `within_source`) so it isn't
   read as an independent match. Add "Notice of Ordinance Adoption & Summary" PDFs as a named target,
   and run ordinances + PMN together (PMN holds the notice back-catalog).
7. **PMN — document the mechanics.** GET-only cumulative `notices.html?id=<body>&page=N`; per-**date**
   (±3–4 day tolerance) set-difference, not per-year counts; attachment-type labels parse from list
   HTML; body-id discovery chain `entities.html?id=3` → `publicBodies.html?id=<entityId>`; ids are
   global, not per-city-sequential.
8. **Campaign finance — encode the hosting reality + Wayback.** Check the **city recorder elections
   page** first (`/elections/financial-disclosures/` and `/campaign-finance-disclosures/`), not the
   state/county. Make **Wayback a first-class tool** for CMS-migrated pages: CDX
   (`web.archive.org/cdx/search/cdx?url=<page>&output=json`) → archived HTML `…/web/<ts>id_/<url>` →
   original PDF links → fetch each `…/<ts>id_/<pdf>`. `WebFetch` cannot reach web.archive.org — use
   `polite_fetch.py`/urllib. Prefix saved names with upload `YYYYMM`/hash (basenames collide across
   filing periods). Note finance data can surface election-record gaps worth cross-checking.
9. **General — crawl the city sitemap before trusting search-cached PDF URLs.** Lehi migrated CMS;
   `wp-content/uploads/...` URLs from web search 404; live docs are `/media/<hash>/<slug>.pdf` found via
   `sitemap.xml`. Add sitemap-first discovery to the recon step.
10. **General — concurrency pre-flight (NEW, from this run).** Before starting, check that no backup is
    being written and no other session is mutating the target city (`_backups/<today>/` freshly created,
    or `meeting_minutes/*.csv`/`db` modified in the last few minutes). If so, **abort and warn** — do
    not run alongside a remediation/other session. Prefer writing new-dataset docs to each dataset's own
    `CLAUDE.md` and defer parent `README.md`/`CLAUDE.md` edits to a single final reconciliation step
    (reduces the shared-file collision surface even in the solo case).
11. **`validate_dataset.py` gotcha to document:** `index.csv` `path` values must be dataset-relative
    including `raw/` (e.g. `raw/foo.pdf`) to resolve. Worth one line in the skill.

---

## Parent-doc snippet to reconcile later (apply once the remediation session settles)

The six new-dataset sections currently in `lehi_city_council/README.md`/`CLAUDE.md` (added by the
pilot agents) may be overwritten by the concurrent remediation. After it finishes, re-append a
coverage block. Source of truth for each = that dataset's own `index.csv` + `CLAUDE.md`:

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Agenda packets | 2024–2025 (pilot) | 564 files · 327 MB · 112 mtgs · 452 staff reports | Granicus/Legistar | ✅ raw retained; 2020–23 deferred |
| Housing plans | GP 2022; MIH 2024; reports 2023–25 | 9 PDFs · 42 MB | city + DWS/HCD | ✅ state = statewide compilations |
| Ordinances | 2020–2026 | 313 ordinances (91% land-use) | reconstructed from minutes + city notices | ✅ within-source linkage, caveated |
| PMN backfill | 2020–2026 | 6 recovered mtgs; full coverage table | utah.gov/pmn (2512/2651) | ✅ repo is PMN superset |
| Transcripts | 2025+ (map only) | 12 mapped · 0 pulled | YouTube / OpenUtah | ⚠️ yt-dlp absent; ASR; Whisper deferred |
| Campaign finance | 2019/21/23/25 | 134 filings · 59 MB | city recorder + Wayback | ✅ 124/134 join to elections |
