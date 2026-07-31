# packets/ — Town of Alta agenda packets & staff reports (build + linkage)

Additive dataset built by the `/expand-city-sources` skill (source type 1). **Purely
additive** — no existing Alta dataset was modified. Canonical truth is `raw/` + `index.csv`;
`text/` sidecars are derived (regenerate with `scripts/extract_packet_text.py alta`).

## What this is
The staff analysis and supporting materials behind each Town Council (body **1601**) and
Planning Commission (body **1602**) agenda item — draft resolutions/ordinances, budget
worksheets, staff reports, memos, zoning redlines, studies, exhibits, and (from mid-2025) the
single bundled meeting packet. Joins to `../meeting_minutes/all_votes.csv` and
`../planning_commission/all_votes.csv` (and the minutes) by **`date` + `body`**.

## Source & enumeration
- Portal `/meetings/` is a JS-only Juniper app (no static links) → enumerated from **Utah PMN**.
- Cumulative one-GET list per body: `https://www.utah.gov/pmn/list/notices.html?id=<1601|1602>&page=200`
  (returns the body's entire notice history — 425 council, 134 PC notices).
- Each notice's attachments are `https://www.utah.gov/pmn/files/<fileId>.pdf`. Records were
  parsed by slicing the list HTML at each `/pmn/sitemap/notice/<id>.html` anchor, taking the
  Event Date and every `.pdf` attachment.
- All raws fetched with `scripts/polite_fetch.py` into `raw/<date>/<fileId>_<slug>.pdf`;
  `raw/_fetch_log.jsonl` is the per-byte provenance (url, status, bytes, sha256, retrieved_utc).

## ⚠ Two Alta-specific gotchas encoded in the build
1. **Classify by FILENAME, not the PMN type label.** Alta's clerk mislabels attachment types
   (the 2026-03-11 council Agenda *and* Meeting Packet are both tagged "(Meeting Minutes)" on
   PMN). The build ignores type labels: it keeps agenda/packet/staff/supporting PDFs and
   **excludes** any PDF whose filename contains "minutes" (approved/draft council/PC minutes and
   budget-committee minutes attached as exhibits — the audited minutes are owned by
   `meeting_minutes/` and `planning_commission/`). Audio (`.mp3`) is never captured.
   **A refresh MUST keep this filename-based rule** — a type-label filter silently drops
   mislabeled agendas/packets.
2. **Alta unbundled its packet until mid-2025.** 2020–mid-2025 meetings posted an Agenda plus
   individual per-item handouts (no single packet PDF); mid-2025+ meetings post one bundled
   "Meeting Packet". `packet_kind` distinguishes them — see below. This is why the earlier years
   have *more* files, not fewer.

## index.csv schema (SCHEMA_SPEC §9 packets contract + Alta extras)
Contract columns (exact order): `date, title, body, meeting_type, packet_kind, source_url,
retrieved_date, format, extraction_method, path`. Alta extras after the contract:
`pmn_notice_url, pmn_file_id, bytes`. **Primary-document §9 trailing columns (2026-07-16):
`doc_class, fetch_status, sha256, text_path, text_chars`** — see the Primary-document text
layer section below.

- `date` — the PMN notice Event Date (`YYYY-MM-DD`); the meeting date. Join key.
- `title` — the source PDF filename (verbatim, minus `.pdf`).
- `body` — `TownCouncil` | `PlanningCommission`.
- `meeting_type` — `regular` | `work_session` | `special` (derived from the notice title).
- `packet_kind`:
  - `full_packet` — the bundled "… Meeting Packet.pdf" (council 2023-06-07+, standard ~2025-08;
    PC 2024-12-18+). Large, often image-only/map-heavy.
  - `agenda_packet` — the meeting Agenda outline (item list; consent-agenda docs land here too).
  - `staff_report` — filename indicates memo / report / staff / presentation / slides.
  - `supporting_doc` — the remaining unbundled per-item materials (draft ordinances/resolutions,
    budgets, exhibits, studies, letters).
- `format` — `text` (born-digital, has a `text/` sidecar) | `scanned` (image-only, no sidecar).
- `extraction_method` — `pdftotext -layout` where a sidecar was produced; otherwise
  `none (image-only; vision/OCR required)`.
- `path` — dataset-relative **including** `raw/` (e.g. `raw/2026-03-11/1401481_...pdf`).
- `pmn_notice_url` — the source notice page; `pmn_file_id` — the PMN file id; `bytes` — HEAD size.

Keyed by (`date`, `body`, `pmn_file_id`) — a meeting can have many rows (agenda + packet +
handouts, plus any "Amended" re-posts, which are kept as distinct rows).

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16 — classify-in-place)

The stored, born-digital packet attachments were classified into the four content-bearing
primary-document classes (SKILL.md Source 7 / `PRIMARY_DOCS_PILOT_SPEC.md`). Alta's packets
are already on disk with `text/` sidecars, so this is **classify-in-place**: no fetching —
`classify_attachments.py` assigns `doc_class`, links the existing sidecar as `text_path`,
computes `sha256` from the retained raw PDF, and records `text_chars` / `fetch_status`.

| doc_class | rows | ok | needs_ocr | what it is |
|---|---|---|---|---|
| staff_report | 11 | 10 | 1 | land-use staff reports/memos — CUP (RACS/Conex), slope variance, zoning-map ratification, zoning-amendment memo, subdivision-ordinance updates, Sugarplum Meadows site-plan/PUD |
| member_memo | 0 | — | — | **HONEST EMPTY** — Alta council memos are staff-authored; the one surname hit ("UFA memo to Mayor Sondak") is a fire-authority memo TO the mayor, not a member proposal |
| plan_amendment | 0 | — | — | **HONEST EMPTY** — the General Plan lives in `housing_plans/`; no GP/land-use-map amendment EXHIBIT rides the packet corpus |
| development_agreement | 0 | — | — | **HONEST EMPTY** — no DA/MDA instruments 2020–2026 (verified) |

- **Only `staff_report` is populated** — the correct result for a ~380-person town whose
  land-use docket is a handful of ski-area CUPs/variances + a subdivision-ordinance rewrite.
- **`fetch_status`**: `ok` (sidecar text linked) | `needs_ocr` (classified but the raw is
  an image-only scan with no sidecar — 1 row: 2024-05-22 "Memorandum Re Proposed Subdivision
  Ordinance", PC; an honest OCR floor, not a skip). No `404`s (nothing fetched — all on disk).
- **`sha256`** is the hash of the retained raw PDF (cross-checked against `raw/_fetch_log.jsonl`);
  `text_path` is dataset-relative (`text/<pmn_file_id>_<slug>.txt`); `text_chars` is the sidecar
  length. Only classified rows carry these five columns; blank = honestly unclassified (out of
  scope, never force-bucketed).

### Classifier method + gates (`classify_attachments.py`)
Deterministic + rerunnable (idempotent — resets the five columns each run). **No matter table
exists** (unlike the Sandy Legistar reference), so classification is **title tokens + the text
SIDECAR HEAD** (first 1500 chars — the script reads `text/` to disambiguate opaque titles like
`2023-7-Conex-CUP-Materials` and `JG memo to TC last issue`). A `staff_report` requires a
**STRONG land-use phrase** (title OR sidecar head) AND an **analysis signal** (title token
`staff report`/`memo`/`report`/`review`, OR a body-level `Staff Report`/`Memo to the … Council`
header). Land-use scoping is narrow: single ambiguous tokens (`subdivision`, `hillside`, `annex`,
bare `zone`/`plan`) are excluded — only multi-word phrases (`conditional use permit`, `variance
request`, `site plan agreement`, `planned unit development`, `subdivision ordinance`, `zoning
map`, `zoning amendment`, `appeal authority`, `slopes over 30`) qualify.

- **Gates (2026-07-16):** precision **11/11 = 100%** (whole-class, each ground-truthed against
  its on-disk sidecar/raw). Recall: exhaustive sweeps — all 98 `staff_report`-kind titles, all
  analysis-token `supporting_doc` rows, and all sidecar heads carrying a body `Staff Report`
  header + a strong land-use phrase; the last sweep recovered 3 opaque-title staff reports
  (`…-Materials` / `…Update`) that the title gate alone missed. Every land-use doc left
  unclassified is a non-staff-report type (draft ordinance, code redline, agenda, signed
  approval, presentation) — est. miss <5%.
- **Boundary decisions (documented, not bugs):**
  - **Land-use scoping (Sandy convention):** business-license/STR (incl. "Staff report peruvian
    estates" — an STR business-license amendment), parking/traffic (Title 6), noise, budget/
    capital-projects, fire, water/sewer rates, audit, town-manager, EIS-response, and
    PC-governance (member appointment/term) staff reports are NOT land-use → unclassified even
    when titled "Staff Report".
  - **Presentations/slide decks excluded** (not staff reports) — this drops the **Shallow Shaft
    rezone PRESENTATIONS** (2025–2026 PC), which are image/slide decks; no separate Shallow
    Shaft staff report was posted, so that contested matter has no `staff_report` row here.
  - **"Peruvian Estates West Line Memo"** (2022-08-10 ×2) is a WATERLINE budget-amendment memo
    (the pipe runs through the subdivision) → correctly NOT a land-use staff report; the naive
    place-name token was dropped for this reason.
  - **"Appeal Authority"** is treated as land-use because Alta's Appeal Authority IS the Land
    Use Appeal Authority (body 1603); both appeal-authority staff reports are ski-area variances.

Rerun: `python3 classify_attachments.py` (rewrites the five columns only);
`--dry-run` prints counts without writing.

## Linkage to votes/minutes
Join `packets.date + packets.body` to `../meeting_minutes/all_votes.csv` (Council) or
`../planning_commission/all_votes.csv` (PC) and to the minutes by meeting date. 83/84 council
minutes dates and 15/17 PC minutes dates have a packet indexed here (gaps in `AVAILABILITY.md`).
Ordinance/resolution numbers appear richly in the `supporting_doc`/`staff_report` filenames
(e.g. `2021-O-6`, `2020-R-15`) — a strong secondary key to the enacting motion.

## Rebuild
1. Re-fetch the two PMN cumulative lists; re-parse anchors; classify by filename (rules above).
2. `polite_fetch.py` each new `.pdf` into `raw/<date>/`; consolidate `raw/_fetch_log.jsonl`.
3. `python3 scripts/extract_packet_text.py alta` → `text/` sidecars (idempotent).
4. Rebuild `index.csv` (contract header first; format/extraction_method from the extraction log).
5. `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
   alta_city_council/packets` must PASS.
The dataset feeds `cities.db` `fts_packet` / `document` on the next `build_cities_db.py` run
(run separately — not part of this build).
