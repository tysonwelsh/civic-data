# packets/ — Emigration Canyon agenda packets & supporting documents

Additive `expand-city-sources` dataset (source type 1). The **Supporting-Documents / packet behind
each Council and Planning Commission meeting** — resolution/ordinance drafts, staff & liaison
reports (UPD/UFA), interlocal agreements, budgets, exhibits, hearing notices — keyed by `date` +
`body` so it joins the minutes/votes layers. **Read `AVAILABILITY.md` first** for coverage, the PMN
mechanics, and the honest 2017–2018 purge floor. Canonical schema: `SCHEMA_SPEC.md` §9.

## What's here

```
raw/<date>/…            originals verbatim, one folder per meeting date
  _fetch_log.jsonl      per-date polite_fetch provenance (url, status, bytes, sha256, retrieved_utc)
raw/_pages/             cached PMN notice-list HTML the harvest parsed (bodies 5809 + 1562)
text/<stem>.txt         pdftotext -layout sidecars for born-digital PDFs (feeds cities.db fts_packet)
text/_extraction_log.csv  per-file extraction outcome (extracted / image_only / too_big / skipped)
index.csv               the dataset index — §9 packets contract + city-extra columns
AVAILABILITY.md         coverage, single-portal mechanics, gaps, as-of date
build_packets_index_ec.py   the (idempotent) harvest→fetch→index builder
```

## index.csv columns

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path`
(the exact §9 packets contract, in order) **+ city extras** `source,pmn_body,notice_url,bytes,sha256`
**+ the 2026-07-16 primary-document text-layer columns** `doc_class,fetch_status,text_path,text_chars`
(see "Primary-document text layer" below).

- **`path`** is dataset-relative including `raw/` (e.g. `raw/2026-05-19/…pdf`) — the convention the
  validator + sources index expect.
- **`body`** ∈ `Council` | `PlanningCommission` (matches the vote/minutes layers).
- **`packet_kind`** ∈ `supporting_docs` (the standard per-meeting Supporting-Documents bundle or an
  item handout — resolution/ordinance draft, liaison report, budget, exhibit, hearing notice) ·
  `full_packet` (a combined "Agenda with Supporting Documents" / "Meeting Packet" bundle) ·
  `staff_report` (an individual staff report).
- **`meeting_type`** — `Workshop` / `Special` / `Emergency` when the source filename says so, else
  blank. Same-day **Workshop (6 PM) + Regular (7 PM)** council meetings are separate notices; where
  both carry docs they disambiguate by date + body (+ meeting_type).
- **`format`** — `text` (born-digital: a `.pdf` with a `text/` sidecar, or a `.docx`/`.xlsx`/oversize
  PDF retained raw with no sidecar) or `scanned` (25 image-only PDFs — `extraction_method` says
  vision/OCR is needed to read them).
- **`source`** = `pmn` for every row; **`pmn_body`** = `5809` (Council) / `1562` (PC);
  **`notice_url`** = the PMN notice page.
- **`sha256`** (city extra, present for EVERY row) = a 16-char prefix of the full SHA-256
  digest of the STORED raw file (verified `sha256(raw).hexdigest().startswith(col)`). Because
  EC **retains** every raw original, this doubles as the §9 doc_class `sha256` provenance — the
  classifier does not re-fetch or discard binaries, so it leaves this column untouched.
- **`doc_class`** (in-scope rows only) — `staff_report` | `plan_amendment` | blank =
  **honestly unclassified**. `member_memo` and `development_agreement` are both **empty for EC**
  (honest zero — see below). Assigned by `classify_attachments.py`.
- **`fetch_status`** (classified rows only) — `ok` (born-digital `text/` sidecar exists) |
  `needs_ocr` (classified but the raw is image-only/office-doc with no sidecar — a recorded OCR
  floor, not a silent skip) | blank (unclassified).
- **`text_path`** / **`text_chars`** (classified `ok` rows) — the dataset-relative sidecar
  (`text/<fileid>_<stem>.txt`) and its character count. The federated search layer prefers this
  explicit `text_path` over the stem convention. Unclassified rows keep these blank — their
  sidecars are still federated into `fts_packet` via the stem convention, unaffected.

## Primary-document text layer (doc_class classifier, 2026-07-16)

`classify_attachments.py` (deterministic, rerunnable, **no network / no db / no LLM** — reads
`index.csv` + the on-disk `text/` sidecar heads) labels the two content classes that actually
exist in EC's packet corpus and links their extracted text. **Scope:** `supporting_docs` +
`staff_report` rows (362); `full_packet` container rows (13) are skipped. **17 classified** — a
small count is the CORRECT result for a ~1,600-pop MSD-staffed town.

| doc_class | rows | ok | needs_ocr | what it is |
|---|---|---|---|---|
| staff_report | 15 | 15 | 0 | MSD land-use / code staff reports — Dark Sky / Night Lighting (19.73.110), the Comprehensive Code Update, stream-setback overlay (OAM2022-000601), rezone (REZ Camp K), slope waiver (WVR), APA designation (OAM2025-001470), conditional use (CUP2025-001542) |
| plan_amendment | 2 | 1 | 1 | GP-amendment ordinance draft (2022-03-01 "AN ORDINANCE ADOPTING A NEW GENERAL PLAN") + the 2025-O-09 zoning-**map**-change ordinance (image-only → `needs_ocr`) |
| member_memo | 0 | — | — | **EMPTY** — EC council is narrative-tally (mayor votes); members file no proposal memos. The 3 packet "memo" titles are MSD staff/legal/agency memos (ADU legislative update by MSD counsel; Night-Sky discussion memo by MSD planners; a URC utility-program memo), NOT member proposals |
| development_agreement | 0 | — | — | **EMPTY** — the "agreement" titles are interlocal/utility-program agreements (C-REP, UPD, MSD ILA, URC); "EC DA Ordinance" is a DA-**enabling** ordinance (zoning text), not a DA/MDA instrument (instrument-only rule) |

- **Classifier logic** (first match wins): `staff_report` = title matches `staff report` **OR**
  the sidecar head carries the **MSD staff-report template** (`Meeting Body:` / `Meeting Date:` /
  `File Number & Project Type` — ≥3 markers) **AND** the phrase "staff report" (the in-TEXT
  detector that catches the opaque case-key title `CUP2025-001542 Fixed.pdf`). `plan_amendment` =
  title is a `(zoning|land use) map change/amend` **OR** a `general plan` + `ordinance` draft.
  `member_memo` = an EC council-member surname + memo/proposal token (→ 0). `development_agreement`
  = a `development agreement`/`MDA` **instrument** title, not an enabling ordinance/interlocal/memo
  (→ 0).
- **Quality gates (2026-07-16, whole-class ground-truthed against the sidecars):** precision
  `staff_report` 100% (n=15, all verified genuine MSD staff reports), `plan_amendment` 100%
  (n=2). Recall — a full sweep of all 345 unclassified in-scope rows for staff-report /
  MSD-template / general-plan / map-change / development-agreement / member-memo signals found
  **0 genuine misses** (2 documented boundary blanks, below).
- **Boundary decisions (documented, not misses):**
  - `2022-03-22 "6.3 - 2022 General Plan - Staff Recommendation.pdf"` — left **blank**:
    it is a staff *Summary and Recommendation* of the GP amendment, neither a formal "Staff
    Report" nor the amendment instrument. `plan_amendment` is kept tight to the amendment
    instrument/exhibit (the GP ordinance itself); this staff summary's sidecar is still in
    `fts_packet` via the stem convention.
  - `2025-11-17 "…Leick Property Documents and Public Comments.pdf"` (Council) — left **blank**:
    a mixed Council-stage bundle whose head carries the OAM2025-001470 APA analysis but is
    titled/assembled as a documents+comments bundle, not a staff report. The clean
    `2025-10-09 OAM2025-001470 Staff Report` IS classified.
  - EC's full draft General Plan documents (2019 GP/TPC + 2020 draft-GP packets) are class-3
    `general_plan` (→ a future `housing_plans/` build), **out of this packets classifier's scope**.
- **Sidecars are pre-existing** (from `scripts/extract_packet_text.py`); the classifier only
  labels rows and links their text — it never fetches, extracts, or discards. Rerun idempotently:
  `python3 classify_attachments.py` (`--dry-run` to preview).
- **`classify_attachments.py` is now §9-discard-row-safe (hardened 2026-07-19).** The script
  RESETS `doc_class`/`fetch_status`/`text_path`/`text_chars` on every row each run and re-derives
  them from the on-disk `text/<stem>.txt` sidecar keyed off `path`. That is safe only while EC
  RETAINS every raw binary (true today — **0 discard rows**). A future §9 discard row (`stored=no`,
  blank `path`, binary fetched/hashed/extracted then DISCARDED, its §9 columns maintained IN-FILE)
  would otherwise be **blanked on every rerun** (reset clears the columns; with `path` blank the
  re-derive finds no sidecar → `text_path`/`text_chars` lost, `fetch_status` mis-set). The fix adds
  the draper-pattern guard: a `stored=no` row with a populated `text_path` is preserved VERBATIM
  (no reset, no reclassification), reported as `§9 discard rows preserved verbatim: N`. This is the
  same defect CLASS that blanked draper's 243 §9 discard rows (see draper
  `packets/link_text_sidecars.py` "DISCARD-ROW SAFETY"). Proven: current-state rerun is a clean
  byte-identical no-op (0 discard rows, index.csv sha256 unchanged); a synthetic discard row in a
  sandbox survives verbatim while normal rows still classify. Pre-fix backup:
  `_backups/2026-07-19-lm-wave-followups/ec-classifier/`. Safe to rerun.
- **Spot-check (date + file-number join to the vote layers):** staff reports join their acting
  motions — `OAM2025-001470`, `CUP2025-001542`, `WVR2024-001086`, `OAM2022-000601` are exact
  file-number matches to PC motions; the Night-Lighting staff report (2023-06-27) → Council
  "adopt Ordinance No. 2023-06-01" (Pass, unanimous); the GP-ordinance draft (2022-03-22) →
  Council "adopt Ordinance No. 2022-03-01" (Pass, unanimous).

## The single-portal design (why + how) — the load-bearing fact

Emigration Canyon has **no city document CMS**. Both bodies publish entirely on **Utah Public
Notice**: **Council = body 5809**, **Planning Commission = body 1562** (MSD-staffed). There is no
second portal to reconcile (contrast the sibling township Copperton, which splits Council between
PMN and a GoDaddy site). Every notice's attachments are labeled `Public Information Handout` (a few
`Other` / `Audio Recording` mislabels), so **classification is by FILENAME, not by PMN label** — the
handout label wraps agendas, packets, and item PDFs indiscriminately.

**Fetch mechanics.** Notice lists are enumerated with the cumulative GET
`https://www.utah.gov/pmn/list/notices.html?id=<body>&page=N` — the **`&page=N` form is REQUIRED**
(the bare `?id=` endpoint 500s "Technical Difficulties"); paging is cumulative, so `--harvest` walks
page 0,1,2,… until the notice-id set stops growing and caches each page under `raw/_pages/`. Each
`<tr>` gives the meeting date + `<li>` file links (`aria-label` filename + label). Documents live at
`https://www.utah.gov/pmn/files/<fileId>.pdf` (**⚠ NOT pmn.utah.gov**; opaque non-sequential ids —
harvested, never synthesized) and download through `scripts/polite_fetch.py` (GET-only, ≥1s/host,
browser UA, logged).

## Rebuild (idempotent)

```
python3 build_packets_index_ec.py --harvest   # walk PMN lists (cache raw/_pages/) -> _candidates.csv
python3 build_packets_index_ec.py --fetch      # download survivors -> raw/<date>/ (skips existing)
python3 build_packets_index_ec.py --index      # -> index.csv (first pass: born-digital assumption)
python3 /Users/tysonwelsh/civic-data/scripts/extract_packet_text.py emigration_canyon   # text/ sidecars
python3 build_packets_index_ec.py --index      # re-run to finalize format/extraction_method from log
```

`--harvest` re-fetches list pages only if `raw/_pages/` is empty (delete it to force a fresh pull on
a refresh). `--fetch` attempts **all** candidates including known-purged ones, so the 404s are
recorded as evidence. Classification/exclusion rules live at the top of the script. Do NOT hand-edit
`index.csv` or files under `raw/`/`text/` — regenerate.

## Exclusions (recorded so they're not mistaken for scraper misses)

minutes & minute-attachments (they're the minutes datasets) · agenda-only PDFs · audio (`.MP3`) ·
meeting-cancellation / no-meeting / annual-schedule notices — **but substantive resolutions that say
"cancel" are KEPT** (2021 "Resolution to Cancel Election", 2025 "R2025-10 Canceling the 2025 Mayoral
Race") · re-posted prior-meeting docs (bare `MM-DD-YY.ext` whose date ≠ the notice date) ·
branding/images.

## Known limits

- **Packet floor is effectively 2019, LATER than the 2017 data floor / 2018-10 minutes floor.**
  2017–2018 handout/packet attachments are **404-purged** on PMN (17 logged failed fetches; 2017: 9,
  2018: 8) — PMN retains minutes longer than bulky handouts. Council 2019–2020 is especially thin (1
  doc each year) for the same reason. Not a harvest miss; the notices exist, the packet PDFs are gone.
- **25 scanned PDFs** need vision/OCR (no text sidecar); **24 `.docx`/`.xlsx`** are retained raw with
  no PDF sidecar (`format=text`, `extraction_method="none (docx raw retained)"`); **2 oversize PDFs**
  (>120 MB — the split 2019-01-17 GP packet halves) are retained raw with no sidecar.
- **A few oversized general-plan PDFs dominate the 1.65 GB total** (472 MB + 137 MB 2019 PC
  GP/TPC packet; 107 MB + 81 MB 2020 draft GP + appendices). These are genuine meeting-attached
  packet items; the General Plan itself also belongs to a future `housing_plans/` build.
- **Mayor VOTES (Millcreek pattern, max tally 5)** — when joining a packet to its vote, the
  presiding mayor is a full voting member of the 5, not a tie-break-only executive.
- Text corpus screener flags are all benign (Spanish/sample ballots; columnar slides & notices;
  packets with maps/plats & signed ordinances) — no extraction failures.
