# nephi_city_council/pmn_backfill — Utah Public Notice (PMN) minutes backfill

**Additive** gap-filler dataset. It does **not** replace or edit the audited minutes
layer (`meeting_minutes/`, `planning_commission/`). It records which meeting **dates**
Utah's Public Notice site (PMN) carries that the repo lacked, and holds the recovered
minutes for those dates only.

## What this is

- Built by expand-city-sources **Source 4 (PMN cross-check)** on **2026-07-05**.
- Scope: **City Council (PMN body 1788)** + **Planning Commission (PMN body 1869)** for
  the repo's **2020–2026** window. Nephi entity id on PMN = **216** (govType 3, Municipality).
- Result: **9 recovered born-digital minutes PDFs** (8 council, 1 PC) that fill real
  holes in the audited layer. **0 purged (404), 0 still-missing** in scope.

## How to use it

- **These are recovered SOURCE minutes, not yet promoted** into `meeting_minutes/` or
  `planning_commission/` and **not** vote-extracted, not in `db/`, not in `weeks/`. Treat
  `index.csv` as the authority for "what PMN added and where the file is."
- For aggregates/timelines/votes, the audited layers remain canonical. If these 9 dates
  are ever promoted, run the normal extraction + `db/build_db.py` + `build_weeks.py` chain
  (see parent `CLAUDE.md`) — do it there, never here.

## Layout

- `index.csv` — one row per recovered meeting. Columns extend `minutes_index.csv`:
  `date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
  `retrieved_date,format,extraction_method,meeting_type,raw_path,status`.
  `date` = meeting date read **inside** the PDF (not the notice date). `path` → `text/`,
  `raw_path` → `raw/`. All rows `status=recovered`, `format=text`.
- `raw/` — verbatim PMN PDFs (`<pmn_file_id>.pdf`) + `_fetch_log.jsonl` (provenance:
  url, HTTP status, bytes, sha256, retrieved_utc — written by `scripts/polite_fetch.py`).
- `text/` — `pdftotext -layout` extraction, one `.txt` per recovered PDF.
- `council.json` / `pc.json` — every PMN notice parsed for that body (id, title, date,
  attachments). `recoverable.json` — the set-difference output.
- `parse_notices.py` — the notice-HTML parser (from the lehi pilot).
- `AVAILABILITY.md` — confirmed ids + what was/wasn't checked. `coverage.md` — per-year
  per-body gap tables.

## Cardinal rules honored

- **Additive only** — no existing row edited; no file outside this dir written.
- **Never fabricate** — a listed-but-404 attachment would be `status=source-unavailable`
  (none occurred here); duplicates would be `status=duplicate-not-promoted` (none needed
  downloading). Every recovered date's true meeting date was read from the PDF.
- **Raw retained** — every byte kept under `raw/` with a fetch log.

## 2026-07-19 — CRA body 5737 harvested in full (TODO "Nephi expansion (a)")

The Community Reinvestment Agency (PMN body **5737**) — flagged out-of-scope by Source 4 — was
enumerated in full and its attachments fetched. Result: **10 notices 2016–2023** (`cra.json`), only
**2 downloadable attachments** ever posted, and **nothing new recovered within the 2020 floor**.

- **`cra.json`** — every body-5737 notice parsed (notice_id, title, notice_type, meeting_date,
  description, attachments). Meeting dates read from each notice's Event Start Date.
- **Attachments (fetched, `raw/` + `_fetch_log.jsonl`):** `465713.docx` = *2019 Annual CRA Meeting
  Schedule* (pre-floor, type "Other" — retained); `359223.docx` = *CRA 12-19-17* minutes (pre-floor,
  now **HTTP 404 / purged** — logged, not recoverable). Every other notice carries no file.
- **Within-floor picture (2020+):** two CRA meeting dates evidenced — **2021-07-27** (interlocal
  agreement; minutes already in `meeting_minutes/` body=CRA via AgendaCenter) and **2023-12-19**
  (agenda-only: AgendaCenter Minutes slot 404, no PMN attachment → `meeting_minutes/minutes_unrecovered.csv`).
  So PMN 5737 recovers **0 new minutes**; the CRA layer is complete within floor.
- **Modeling:** CRA stays a `body=CRA` value inside `meeting_minutes/` (slc/holladay/millcreek pattern),
  not a separate dataset — the audited crosswalk row lives in `scripts/normalize_motions.py`
  `BODY_CROSSWALK` (regenerated into `crosswalks/body_crosswalk.csv`). `pmn_bodies.csv` row 5737 updated
  `crawl=yes`.

## Rebuild / re-check

Re-fetch the two notice histories with `scripts/polite_fetch.py` (GET only) →
`parse_notices.py` → set-difference against the two `minutes_index.csv` files (tolerance
±4 days, comparing the date *inside* each PDF). Validate:
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py nephi_city_council/pmn_backfill`.

## 2026-07-17 — crosscheck flag verification (22 → 18)

Verified all 22 `crosscheck_flags.csv` flags. 4 exceptions appended (`pmn_exceptions.csv`);
re-run: **18 flags** (agenda_only_gap 9, missing_minutes 9; 4 suppressed, 4 pending-adoption).

**Exceptions (false positives):**
- `2024-04-16 / 1869` **duplicate** — file `CM 4-16-24.docx` is COUNCIL minutes already in
  `meeting_minutes` (2024-04-16); PMN cross-filed council minutes under the PC body.
- `2022-03-09 / 1788` **duplicate** — "Planning Commission Meeting"; PC minutes for that date
  already in `planning_commission`; PMN cross-filed the PC notice under the council body.
- `2023-02-14 / 1788` **other** — "NO WORK SESSION 2-14-23" cancellation notice.
- `2024-01-24 / 1788` **other** — "Nephi Airport Advisory Committee Meeting" (foreign body).

**Recovery leads (18, reported to review gate — NOT ingested):**
- 9 missing_minutes with real minutes attachments: council WORK SESSIONS the repo lacks
  (WS 11-24-20, WS 10-12-21, WS 2-22-22, WS 4-26-22, WS 7-26-22, WS 6-25-24), council
  meeting CM 3-7-23; plus `2025-11-04` whose attachment is `CM 10-21-25.pdf` (true meeting
  date **2025-10-21** — repo lacks it; recover under 2025-10-21, not the notice date); and
  `2026-05-13` PC (known_unrecovered — live lead).
- 9 agenda_only_gap (agenda-grade, lower confidence): PC meeting agendas the repo has no
  record of (2020-04-08, 2021-02-10, 2022-02-23, 2024-07-10, 2025-07-09, 2025-09-23,
  2026-03-11) + two PC agendas cross-filed under the council body (2020-12-09, 2021-10-13).

**Hardening candidate (config, not engine):** Nephi cross-files PC notices under council
body 1788 (confirmed 2022-03-09, 2020-12-09, 2021-10-13). Setting body 1788
`repo_datasets=meeting_minutes;planning_commission` (herriman multi-dataset pattern) would
auto-absorb the in-repo cross-filings — but would also let a genuinely-missing council date
be cleared by a PC date. Left as review-gate material; resolved here via exceptions instead.


## 2026-07-17 — 8 council minutes PROMOTED into the audited layer (crosscheck leads)

The 7 `missing_minutes` council leads + the mis-dated 2025-10-21 doc were fetched,
content-verified, and PROMOTED into `meeting_minutes/` (source=pmn, format=text). Raw
originals retained in `raw/` (docx served at `/pmn/files/<id>.docx`, not `.pdf`) with text
sidecars in `text/`; `index.csv` rows appended (status=promoted). Promoted dates → file id:
2020-11-24 (671045, WS), 2021-10-12 (789517, WS), 2022-02-22 (837353, WS), 2022-04-26
(856255, WS), 2022-07-26 (876545, WS), 2023-03-07 (963179, CM), 2024-06-25 (1152995, WS),
2025-10-21 (1346003, CM — the doc PMN filed under the 2025-11-04 notice; recovered under its
TRUE internal date). Extraction added +14 vote rows (all_votes 1090→1104, motions 918→932);
2020-11-24 and 2021-10-12 are discussion/tour-only work sessions that record NO motion
(0 rows — honest, not an extraction miss). validate_votes 0 HARD FAILURES. NOTE: `weeks/` is
stale (i.weeks FAIL = the +14 delta) — will clear on the orchestrator's build_weeks.py rebuild.
