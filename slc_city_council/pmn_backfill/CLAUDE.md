# slc_city_council/pmn_backfill — how to use this dataset

**Additive** Utah Public Notice (PMN) backfill for Salt Lake City, built 2026-07-05 by the
`expand-city-sources` Source-4 pass. It does two things and **never touches the audited
minutes layer** (`meeting_minutes/`, `planning_commission/`):

1. **Gap-fill** — council minutes that exist on PMN but are absent from the repo's audited
   `minutes_index.csv`. 7 recovered docs. See `index.csv`.
2. **2020 source-URL recovery** (the high-value secondary goal) — a citable PMN URL for each
   of the repo's 68 un-URL'd 2020 Laserfiche council minutes. See `url_recovery_2020.csv`.

## Files
- **`index.csv`** — the 7 recovered minutes. Schema (§9 pmn_backfill contract + extras):
  `date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
  `retrieved_date,format,extraction_method,status,raw_path`. `path` → the extracted `text/` file (repo-relative); `raw_path` → the
  retained PDF under `raw/`. `source_url` = the citable `/pmn/files/<id>.pdf`.
  `status` ∈ {recovered}. `format` = text (all born-digital).
- **`url_recovery_2020.csv`** — 68 rows, one per repo 2020 council minutes file:
  `date,body,meeting_type,pmn_url,pmn_file_id,matches_repo_file,match_confidence`. 65 rows
  carry a recovered `pmn_url`; 3 are honest `no-pmn-source` (blank url). **PROMOTED
  2026-07-19** — these 65 verified PMN URLs were written into the `source_url` column of
  `meeting_minutes/minutes_index.csv` (and thus `sources.csv`/`SOURCES.md` after
  `scripts/build_sources_index.py slc`), closing the TODO "SLC 2020 Laserfiche minutes: no
  per-document URLs". This CSV remains the standalone match ledger. The `source` column
  stays `laserfiche` (the stored TEXT is still Laserfiche OCR — the PMN URL is a citation to
  the *same meeting's* minutes record, not the text's origin); each URL was re-verified
  in-body 2026-07-19 (retained `raw/2020/<id>.pdf` → pdftotext: meeting date 65/65, "MINUTES
  OF THE SALT LAKE CITY COUNCIL …" title line present, session agrees, word-overlap ≥0.84 for
  64/65 + 3/3 live-URL liveness checks byte-identical to the retained raws). **One honest
  scope note:** 2020-07-07 Formal (file 645597) — the repo stored a narrow *"Delegating Bond
  Resolution Minutes"* excerpt for that slug; the cited PMN file is the *comprehensive* formal
  minutes of the same July 7, 2020 formal session (its item #1 IS that bond resolution), so
  word-overlap is 0.51 but it is the same meeting's fuller adopted minutes. The 3
  `no-pmn-source` rows (2020-01-07/01-17/01-21 Formal — PMN posted only the Work Session
  minutes for those dates) stay honestly URL-less.
- **`text/`** — the 7 recovered minutes as text.
- **`raw/`** — retained originals + crawl provenance: `slc_entities.html`, `slc_bodies.html`,
  `notices_<bodyId>.{html,json}`, the 5 non-2020 recovered PDFs, `_fetch_log.jsonl`.
- **`raw/2020/`** — all 68 downloaded 2020 council minutes PDFs (the URL-recovery corpus,
  incl. the 2 recovered 06-09/06-16 formals) + its own `_fetch_log.jsonl`.
- **`AVAILABILITY.md`** — confirmed entity/body IDs + everything checked and excluded.
- **`coverage.md`** — per-year × per-body tables.
- Code: `parse_notices.py` (PMN listing → JSON), `crosscheck.py` (date set-difference vs
  repo), `verify_2020_minutes.py` (reads meeting date/session from each 2020 PDF),
  `build_url_recovery.py` (the match). `recoverable.json`, `verify2020.json`,
  `final_meta.json` are their intermediate outputs.

## Confirmed PMN IDs (see AVAILABILITY.md for full history/counts)
SLC entity **259**. Bodies: Council **1360**, Planning Commission **1274**, RDA **1277**,
CRA **9033**, LBA **3475**.

## Cardinal rules honored
- **Never fabricate.** The 3 missing 2020 Formal URLs are recorded blank, not guessed. The
  one agenda-mislabelled-as-minutes PMN file (593695) was caught by reading the PDF and
  excluded.
- **Additive only** (as-built). The recovered TEXT never touches the audited minutes layer.
  The 2020 URLs originally lived *alongside* in `url_recovery_2020.csv`; on 2026-07-19 the 65
  verified ones were promoted into `minutes_index.csv`'s `source_url` column as a
  citation-provenance fix (text unchanged; `source` still `laserfiche`).
- **Raw retained.** Every PDF/HTML kept under `raw/`; every fetch logged with SHA-256.

## Cross-check flag verification — 2026-07-17 (pmn_crosscheck.py)
The mandatory-refresh `scripts/pmn_crosscheck.py slc` run emitted **40 flags**
(21 count_mismatch + 8 missing_minutes + 11 agenda_only_gap). Verified → **36 suppressed to
`pmn_exceptions.csv`, 5 remain as live recovery leads** (3 missing_minutes + 2 agenda_only).

**count_mismatch (all 21) = engine-semantics false positives — combined-doc
architecture.** SLC posts each session's minutes SEPARATELY on PMN (Formal + Work Session,
plus multi-stage "Approved"/"Signed" duplicates, all-bodies "Trifecta" versions, and
adjacent-board files — Airport LOC, Board of Canvassers), while the repo stores ONE combined
all-bodies doc per date. Verified a sample (repo holds 1–3 docs on every flagged date; no
content missing). Family suppressed kind=other. **HARDENING CANDIDATE** (see below).

**Systemic SLC-specific finding: Historic Landmark Commission notices ride PMN body 1274
(Planning Commission).** All 5 PC agenda_only_gaps (2020-05-07/06-04/07-16/08-06/09-03) and
1 missing_minutes (2025-07-10 "HLC07.10.2025minutes.pdf") are HLC, out of the repo's PC
scope. Confirmed the HLC notice IDs are in the crawled `notices_1274.html`. Suppressed
kind=other. **HARDENING CANDIDATE** (the config assumed 1266=HLC only).

**3 missing_minutes recovery leads (real minutes, repo lacks entirely):** 2021-05-13
Special Limited Formal, 2021-06-10 Work-Session-only, 2023-05-25 Work-Session-only.
**2 agenda_only recovery leads:** 2022-08-02 (verified genuine Special Work Session; no
minutes on PMN) and 2023-07-26 Work Session — agenda-grade (SLC does not always publish
special/WS minutes).

**Other exceptions:** 2022-09-12 RDA (wrong_date — minutes are 2022-09-13, in repo),
2025-08-15 (mislabel — only the 2025-08-19 Truth-in-Taxation file attached, already in repo),
2023-01-11 Legislative Breakfast + 2023-01-16 legislator Open House (other — real but
non-governing adjacent-series; recoverable if scope expands), and 4 hearing/comment-period
notices (2022-10-27, 2022-11-02, 2024-04-23, 2026-04-28). Re-run: **40 → 5 flags,
36 suppressed.**

### Promotion of the 3 missing_minutes leads — ✅ MINUTES PROMOTED 2026-07-17 (votes EXTRACTED same day — see below)
All fetched from PMN (polite, ≥2s), content-verified, and promoted into the audited
`meeting_minutes/` layer (`source=pmn`, `format=text`, `> Source:` header via
`scripts/add_minutes_headers.py slc`). Raws retained in `pmn_backfill/raw/<file_id>.pdf` with
fetch provenance in `raw/_fetch_log.jsonl`. **4 minutes docs across the 3 dates** (the 2021-05-13
notice carried BOTH a Formal and a Work Session minutes file; the short-name "…Special F/…WS"
attachments were verified to be AGENDAS and excluded):
- **2021-05-13 Special Limited Formal Meeting** (file 741853) — `special-limited-formal-meeting`.
- **2021-05-13 Council Work Session** (file 888883) — `council-work-session`.
- **2021-06-10 Council Work Session** (file 913083) — `council-work-session`.
- **2023-05-25 Council Work Session Meeting** (file 1011945) — `council-work-session-meeting`.

All 4 are genuine SLC Council minutes (verified body/date/weekday — these are COVID-era
electronic meetings held **Thursday**; no draft markers). ✅ **VOTE EXTRACTION DONE 2026-07-17
(evening wave):** the 4 `.votes.json` were written by direct read of the promoted markdown
(same schema as the LLM pipeline; no API batch), `all_votes.csv` rebuilt via
`extract_votes.py::rebuild_csv()` — which now emits the repo-standard trailing
**`provenance` column** (`pmn_minutes` for these, `minutes` for portal rows, keyed off
`minutes_index.csv` `source`) — and `db/build_db.py` stores `motion.provenance`. Yield:
**3 motions / 20 member-vote rows** (Special Formal: Res 17 of 2021 Faris D2 appointment 6-0;
2021-06-10 WS: enter/exit Closed Session, both 7-0); the **2021-05-13 WS and 2023-05-25 WS
have honestly ZERO formal votes** (candidate straw polls only / closed session "Item not
held") — empty `votes` arrays, no fabrication. validate_votes 0 hard failures; validate_city
**24 PASS / 2 WARN (documented extensions) / 0 FAIL**. Backups:
`_backups/2026-07-17-pmn-leads-recovery/slc/` (minutes) + `_backups/2026-07-17-wave2/slc/`
(pre-extraction CSV/scripts). **The 2 agenda_only leads (2022-08-02,
2023-07-26) remain genuine no-minutes gaps — SLC does not always publish special/WS minutes.**

## Gotchas for whoever uses this next
- **PMN notice date == SLC council meeting date** for minutes attachments (verified 68/68 in
  2020), but this is an SLC coincidence — for other cities the notice date is a *posting*
  date and you must read the meeting date from inside the PDF (`verify_2020_minutes.py` shows
  how). Do not assume it elsewhere.
- SLC **filename convention** is load-bearing for session type: `…ws.pdf` = Work Session,
  `…r.pdf` = Formal/regular; retreats are named `…Retreat…` and the repo files them as Work
  Session.
- RDA/CRA/LBA are **separate PMN bodies** but their minutes ride inside the combined Council
  minutes doc — do not double-count them against the council series.
- Re-running the crawl: `page=400` returns each body's full history in one GET; PMN's
  arbitrary-date search is POST/CSRF-gated and off-limits to the polite fetcher.
