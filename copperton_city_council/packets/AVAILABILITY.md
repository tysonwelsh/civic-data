# Agenda packets / supporting documents — availability (Town of Copperton)

**Source type 1** of the `expand-city-sources` skill. Purely additive — does **not** modify any
existing Copperton dataset. **As-of: 2026-07-14.**

Copperton is a ~800-person town (Salt Lake County; metro township 2017 → Town 2024-05-01), so it
holds **~11–12 council meetings/yr** and a Planning Commission that **cancels most of its meetings**.
A thin, sparse packet record is the correct, honest result — see the counts below.

## What "packet" means here + the two portals

Copperton posts the **Supporting Documents / packet** behind each meeting on two portals. This
dataset draws each meeting from exactly **one** of them (a clean, non-overlapping split), keyed by
`date` + `body` so a packet joins `meeting_minutes/all_votes.csv` and
`planning_commission/all_votes.csv`:

| Body | Dates | Source | What it is |
|---|---|---|---|
| **Council** | **≤ 2023-12-31** (metro-township era) | **Utah PMN body 5831** | per-meeting `[Public Information Handout]`/`[Other]` attachments — agendas, staff reports, ordinance/resolution drafts, budgets, studies, contracts |
| **Council** | **≥ 2024-01-01** (town era) | **GoDaddy town site** (`copperton.utah.gov/<YEAR>-agendas...`; docs on `img1.wsimg.com`) | the town's combined **"Agenda with Supporting Documents"** / **"Meeting Packet"** / **"Agenda Packet"** bundles + item-level staff reports |
| **Planning Commission** | **all dates** | **Utah PMN body 1560** | `*_Packet.pdf` / `*_Agenda.pdf` + staff reports + public-hearing notices |

**Why the split (documented decision):** PMN body 5831 mirrors the town's GoDaddy 2023 page but
with cleaner, per-meeting date labels, so **2023 and earlier council packets are taken from PMN**;
the GoDaddy site is where the town packages its own combined-packet PDFs for the **town era
(2024+)**, so those years are taken from GoDaddy. **No meeting is sourced from both**, so there is
no cross-portal double-counting. The PC has no packets on the GoDaddy site — its record lives
entirely on PMN body 1560.

The GoDaddy listing pages are JS-rendered and served under a **TLS cert mismatch**
(`copperton.utah.gov` presents a `secureserversites.net` cert), so the *listings* were harvested
with `curl -k` + a browser UA and the document anchors read from the rendered DOM (opaque
`img1.wsimg.com/.../downloads/<guid>/<file>.pdf?ver=<n>` GUIDs — harvested, never guessed). The
*documents* themselves (`img1.wsimg.com`, `www.utah.gov/pmn/files/<id>.pdf`) have valid certs and
were downloaded through `scripts/polite_fetch.py`.

## Coverage retrieved — STORED (400.3 MB, under budget)

**305 packet documents stored, 400.3 MB** (well under the ~1.5 GB budget — tiny town, so STORED,
not index-only). All raw originals retained under `raw/<date>/`; per-file provenance (URL, HTTP
status, bytes, **sha256**, retrieved_utc) in each `raw/<date>/_fetch_log.jsonl` and consolidated in
`raw/_fetch_log.jsonl`.

| Body | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Total docs | Meeting dates |
|---|---|---|---|---|---|---|---|---|---|---|
| **Council** | 20 | 45 | 33 | 41 | 55 | 4 | 19 | 12 | **229** | 83 |
| **Planning Commission** | 15 | 14 | 1 | 10 | 11 | 10 | 10 | 5 | **76** | 45 |

- **Council:** 194 docs from PMN 5831 (2019–2023) + 35 from GoDaddy (2024–2026), across **83
  meeting dates, 2019-02-20 → 2026-07-15.** (2024 is low because the town era's GoDaddy page
  packages a meeting's whole packet as a single "Agenda Packet" PDF, whereas PMN posted many small
  handout files per township meeting — fewer *files*, not less content.)
- **Planning Commission:** 76 docs across **45 dates, 2019-01-15 → 2026-07-01.** Sparse because the
  PC cancels most meetings (see below).
- **`packet_kind`:** 200 `supporting_docs`, 52 `agenda_packet`, 43 `full_packet`, 10 `staff_report`.
- **`doc_class`** (primary-doc layer, 2026-07-16): **6 `staff_report`** (all born-digital `ok`), and
  **0 each** for `member_memo` / `plan_amendment` / `development_agreement` — see "Primary-document
  classification layer" below.
- **Format:** 298 born-digital `text` (240 got a `text/<stem>.txt` sidecar via
  `scripts/extract_packet_text.py`; 48 are `.docx`/`.doc`, retained raw, no PDF sidecar) + **7
  `scanned`** image-only PDFs (listed in `index.csv` with `extraction_method` noting vision/OCR is
  needed to read them).

## Primary-document classification layer (doc_class, 2026-07-16 — PRIMARY_DOCS_ROLLOUT)

A `doc_class` label was added over the in-scope rows (`supporting_docs` + `staff_report` = 210 of
305; the `full_packet`/`agenda_packet` containers are skipped — their whole-meeting text already
feeds `fts_packet`). This is **classify-in-place**: the binaries are already STORED with `text/`
sidecars, so no fetching — just a class label + a link to the existing text. Built by
`classify_attachments.py` (deterministic, rerunnable). **Tiny land-use town → 6 classified is the
correct honest count.**

- **`staff_report` = 6** (all `ok`): the MSD land-use staff reports — 2023-04-19 (Title 18/19
  repeal-replace, a `.docx` given a `textutil` sidecar), 2023-07-19 (REZ2023-000840 rezone), 2024-09-10
  (OAM2024-001253 SB174/HB476 subdivision), 2025-07-02 (OAM2025-001422 parking), 2025-12-03
  (OAM2025-001540 HB368 bonding), 2026-06-03 (OAM2026-001628 landscaping).
- **`member_memo` / `plan_amendment` / `development_agreement` = 0 each** — honest empties. The
  councilmember/memo title hits are administrative resolutions/redlines; the ~15 "agreement"/annex
  hits are interlocal/franchise/annexation (no private land-development agreement exists); and the
  DRAFT **Annexation Policy Plan** is a distinct statutory land-use plan (Utah Code 10-2-401.5), not
  a GP/land-use-map amendment exhibit, so it is left blank (its text is still FTS-searchable).
- **Boundary calls:** the 2025-08-20 `packet_kind=staff_report` rows (UFA Q2 / EOC training / Hazard
  Mitigation annex) are operational reports, not land-use staff reports → blank; draft Title 18/19
  code-text amendments and the "Phase 1 Package" staff cover memo → blank (code drafts / non-"staff
  report" memo). Full detail + the quality-gate metrics are in `CLAUDE.md`.

## Genuine gaps (not fabricated, not scraper misses)

1. **2017–2018 packet/handout attachments are 404-PURGED (retention).** PMN keeps a notice's
   *minutes* attachment far longer than its bulkier *handout/packet* attachments. Every meeting
   notice for 2017–2018 still lists a packet/handout file-ID, but **18 of those attachments return
   HTTP 404** — verified this run, logged as failed fetches in `raw/_fetch_log.jsonl`:
   - **PC:** 2017-12-06 through 2018-11-13 (11 notices) — packets/agendas all 404.
   - **Council:** 2018-11-21 (3) and 2018-12-19 (4) handouts — all 404.
   This is the same retention purge documented for the minutes layer (`../meeting_minutes/README.md`
   §Gap: attachments older than ~mid-2018 are gone). Effective packet floor is therefore **2019**
   (earliest surviving: Council 2019-02-20, PC 2019-01-15), even though the town's data floor is
   2017. The pre-2019 meetings themselves are real (their notices exist) — only the packet PDFs are
   purged.

2. **Planning Commission cancels most meetings.** On PMN body 1560, **~83 notices (2017+) are
   cancellation / "no-meeting" agendas** vs **~45 dates that carry a real agenda/packet/staff
   report** (some of the latter are **General Plan Steering Committee (GPSC)** work sessions, not
   regular PC business). The cancellation notices are **deliberately excluded** from this packet
   dataset (a ~150-word "meeting cancelled" PDF is the opposite of a packet); their pattern is
   quantified here instead. This matches the repo-wide note that Copperton's PC "cancels most
   meetings" and its land-use volume is tiny.

3. **Undated GoDaddy loose docs (town era) — out of scope.** The 2024–2026 GoDaddy pages also carry
   loose supporting materials with **no meeting date** (annual budgets, adopted ordinance/resolution
   texts, logos, a fee schedule). These are excluded because (a) the §9 contract requires a real
   `date` per row and assigning one would be fabrication, and (b) adopted ordinance/resolution texts
   and general-plan/budget documents belong to the future `ordinances/` and `housing_plans/`
   datasets, not `packets/`. They remain live on the GoDaddy site.

## What was intentionally excluded (kept out of the packet dataset)

- **Minutes & minute-attachments** — already the `meeting_minutes/` and `planning_commission/`
  datasets; classified out by filename.
- **Audio recordings** (`.mp3/.wav/.m4a`) — out of scope for packets.
- **PC cancellation / no-meeting / annual-schedule notices** — quantified above, not stored as
  non-packets.
- **Re-posted PRIOR-meeting minutes** attached to a later council notice for approval (a bare
  `MM-DD-YY.pdf` whose date precedes the notice) — duplicates of the minutes layer.
- **Branding/images** (logos, `IMG_*`, ballots).

## How this was checked

`build_packets_index_copperton.py --harvest` fetched the four GoDaddy year pages (`curl -k`) and
the cumulative PMN notice lists for bodies 5831 and 1560 (`.../list/notices.html?id=<body>&page=N`,
pages 1/20/48 unioned to reach the oldest rows), classified every anchor/attachment by
filename/label, applied the exclusions above, then `--fetch` downloaded the survivors through
`polite_fetch.py` and `--index` built `index.csv` (reading `text/_extraction_log.csv` to mark the 7
scanned PDFs). Text corpus screened with `audit-city-data/scripts/screen_corpus.py` — flags were
all benign (budget/finance tables → high symbol ratios; the same budget re-attached to multiple
meetings → duplicate bodies; multi-page packet headers → repeated lines), no extraction failures.
Passes `expand-city-sources/scripts/validate_dataset.py`.
