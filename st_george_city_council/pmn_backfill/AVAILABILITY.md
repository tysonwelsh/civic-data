# PMN backfill — availability & what was checked

**As-of:** 2026-07-02

## What was checked
- Utah Public Notice (PMN, `utah.gov/pmn`) full notice history for **both** St. George
  public bodies whose minutes this repo tracks:
  - **City Council — body id 241** (cumulative `notices.html?id=241&page=300`; 1,602 notices,
    2015-02 → 2026-07).
  - **Planning Commission — body id 242** (cumulative `notices.html?id=242&page=300`; 931
    notices, 2014-03 → 2026-07).
- Filtered to attachments PMN labels `(Meeting Minutes)`; per-date set-difference against the
  audited `meeting_minutes/minutes_index.csv` and `planning_commission/minutes_index.csv`
  (±3-day tolerance), 2020+.

## What exists and was recovered
- **20 documents / 17 meeting dates** added to `index.csv` + `raw/`. See `coverage.md` for the
  per-year table. All born-digital text (`pdftotext -layout`; one `.docx` via `textutil`).
  Corpus screener (`screen_corpus.py`) ran clean — no garbling, mojibake, or dict-ratio
  outliers; `repeated_line` flags are benign page headers.

## What does NOT exist / remains unavailable
- **Planning Commission 2023-05-23 minutes** — never posted to PMN. The only 2023-05-23
  attachment PMN labels "Meeting Minutes" is a 178-page **agenda packet** (`980505`), which
  embeds the *prior* meeting's (2023-05-09) minutes — already in the repo. The 05-23 minutes
  themselves are genuinely unpublished on PMN. The agenda packet is retained
  (`doc_type=agenda_packet`) so a reader can see what was on the agenda, but this is NOT the
  minutes.

## What was deliberately excluded (not gaps)
- **2020-08-27 (council)** — PMN date is a false positive; its attached file is
  `09.03.2020 minutes.pdf` and 2020-09-03 is already in the repo.
- **2025-07-31 (under council body 241)** — the file is **St. George Arts Commission**
  minutes, mis-posted under the Council body. Out of scope for the council minutes layer;
  the Arts Commission has its own PMN body (id 248) and is not tracked in this repo.
- **One byte-identical duplicate** of the 2023-11-09 council minutes (two PMN notices carried
  the same file; sha256 verified identical). Kept one.

## Provenance
- Every byte fetched via `scripts/polite_fetch.py` (≥1s/host throttle, retry, sha256) →
  `raw/_fetch_log.jsonl`. Frozen clock `--now 2026-07-02T00:00:00Z`.
- `index.csv` carries `notice_url`, `pmn_file_id`, `pmn_body_id` for every row so each
  document is traceable back to its PMN notice page.
