# Nephi City Council — packets (agenda documents / staff reports)

Additive dataset built by the `expand-city-sources` skill. **328 meeting agenda documents**
harvested from Nephi's CivicPlus CivicEngage **AgendaCenter** (`https://www.nephi.utah.gov/AgendaCenter`),
window **2020–2026**. Additive only — this dataset never touches `meeting_minutes/`,
`planning_commission/`, `public_comments/`, `election_results/`, `db/`, or `weeks/`.

> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **C** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) are **HONEST ZEROS**
> (AgendaCenter exposes only Agenda + Minutes types; no packet layer). See `AVAILABILITY.md`
> § "Primary-document classes".

## What this is (and is NOT)
- **IS**: the *agenda* posted before each meeting (order of business; on this portal often
  carrying a short staff/agenda narrative). This is the closest thing Nephi publishes to an
  "agenda packet" — the portal exposes **only two document types, `Agenda` and `Minutes`**;
  there is **no `AgendaPacket` / staff-report attachment type** and no separate bundled packet.
- **IS NOT**: minutes. Minutes are excluded here — they already live in `meeting_minutes/`
  (Council) and `planning_commission/` (PC). This dataset carries the pre-meeting agenda only.

## Layout
```
index.csv           328 rows — one per agenda document (the join surface)
raw/<date>/         the raw originals, verbatim (council_<id>_agenda.pdf, pc_<id>_agenda.pdf, cra_<id>_agenda.*)
_fetch_log.jsonl    provenance: one JSONL line per fetch (url, status, bytes, sha256, content_type)
AVAILABILITY.md     coverage, size math, storage decision, gaps
```
`raw/` also contains per-directory `_fetch_log.jsonl` copies (polite_fetch writes one per outdir);
the dataset-root `_fetch_log.jsonl` is the consolidated log.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, size_mb, stored_locally`
- **date** — meeting date (`YYYY-MM-DD`), parsed from the AgendaCenter file id `_MMDDYYYY-<id>`.
- **title** — verbatim listing label ("City Council Meeting", "Work Session Agenda",
  "Planning Commission Agenda", …). City-faithful; not normalized.
- **body** — `Council` (254) / `PlanningCommission` (72) / `CRA` (2, Community Reinvestment
  Agency — matches the single CRA meeting the minutes repo records under `body=CRA`).
- **meeting_type** — normalized guess from the title: `regular` (217), `work_session` (103),
  `public_hearing` (5), `public_hearing+work_session` (2), `special` (1). Convenience only —
  `title` is authoritative.
- **packet_kind** — always `agenda` (portal has no packet/staff-report type; see above).
- **format** — `text` (324) or `scanned` (4). All stored locally.
- **extraction_method** — `none (raw retained)`. No text layer is committed; extract on demand
  from `raw/` (pdftotext works on the 324 text PDFs; 3 rows are `.docx`, see below).
- **path** — dataset-relative, e.g. `raw/2020-01-07/council_94_agenda.pdf`.

## How to join
By **date (+ body)** to the votes/minutes flat CSVs. Coverage is strong: **every one of the 194
council-vote meeting dates has an agenda here**, and 61 of 63 PC-vote dates match. Agenda dates
*exceed* vote dates because agendas also cover work sessions and meetings with no recorded motion.

## Quirks / caveats
- **`<id>` suffix is non-derivable** — it is a CivicPlus per-post serial, harvested from the
  AgendaCenter Search listing, not computable from the date. To refresh, re-enumerate the Search
  endpoint (see AVAILABILITY.md) and diff on the id.
- **3 documents are Word `.docx`, not PDF** (`council_232` 2022-06-21, `pc_267` 2023-01-11,
  `pc_382` 2025-05-14) — the city uploaded `.docx` to the Agenda slot. Kept verbatim; `format=text`.
- **4 PC agendas are scanned** (no text layer): 2020-01-08, 2022-02-16, 2022-04-27, 2022-06-22.
- **Council vs PC asymmetry** — Council files ~2× more agendas (254 vs 72). PC meets roughly
  monthly and posts fewer/short agendas; the 4 scanned + short-text files are all PC. Not a gap
  in *this* harvest — it mirrors what the city posts.
- **DO NOT** treat these as minutes or as recorded votes; they are pre-meeting agendas only.
