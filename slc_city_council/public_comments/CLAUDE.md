# SLC Public Comments — project notes

Dataset + pipeline for Salt Lake City Council public-comment PDFs (2020–2026),
extracted, cleaned, and prepared for analysis (notably **weekly time-binning**).

## Pipeline (one direction, raw JSON is the source of truth)

```
download_comments.sh        scrape weekly PDFs -> 2020/ … 2026/  (one folder per year)
vision_extract.py + config.py   Claude Vision per page -> progress/raw/{year}/*.json   <-- SOURCE OF TRUTH
clean_comments.py           -> all_comments_clean.csv      (canonical flat table)
                            -> comments_clean.json         (same data, typed: arrays + booleans)
                            -> by_year/comments_YYYY.csv   (split by date_normalized year)
                            -> all_comments_dropped.csv    (audit trail of every removed row)
```

Regenerate everything (fast, no API calls): `python3 clean_comments.py` (add `--report`).

## Extraction (`vision_extract.py`) — how it works & gotchas

- **Technique:** each PDF page is rendered to a JPEG image (`pypdfium2`, scale 2.0)
  and sent to Claude via the **Batch API**; the model returns the page's data as
  **JSON text** which is parsed into `progress/raw/{year}/*.json`. One image per page.
- **API key:** read from `ANTHROPIC_API_KEY`, auto-loaded from a gitignored `.env`
  by `config.py`. Don't ask the user for it; don't print it.
- **Model:** set once as `MODEL` in `config.py` (currently `claude-sonnet-4-6`).
  The original `claude-sonnet-4-20250514` was **retired** — if every request errors
  with `not_found`, the model id needs updating to the current Sonnet. Check the
  `claude-api` skill for current model ids.
- **Known failure + fix:** long verbatim comments often contain literal quotes
  (e.g. `the "rule of law"`), which the model emits **unescaped**, breaking JSON.
  `fix_unescaped_quotes()` (first repair strategy in `process_batch_results`)
  re-escapes interior quotes and recovers these. This was the cause of ~70 early
  error pages, since recovered.
- **Do NOT use forced tool-use / structured output here.** It was tried and
  reverted: on long-text pages the model degenerates and dumps a giant string
  into the tool instead of filling the schema. The text-JSON + quote-repair path
  is the proven approach.
- Re-running is safe and cheap: pages already done are skipped (`progress.json`),
  and pages saved as `page_type: "error"` are retried until they succeed. Run a
  single year with `--year 2026` or all not-done pages with no flag.
- **Oversized pages:** the API rejects images > 8000px and downscales > 1568px,
  so `render_page_to_base64` caps the long edge at `MAX_IMAGE_DIM` (1568).

### Residual unrecoverable pages (~8, don't keep retrying)
After recovering ~62 of the original ~70 error pages, 8 remain and are expected:
- **5 content-filter blocks** — the API returns `invalid_request_error: Output
  blocked by content filtering policy` for these page images (mostly 2020 protest-
  era pages). No retry fixes this; they stay not-done and re-fail each run.
- **3 JSON edge cases** — comments containing a mid-sentence quoted phrase like
  `"neighborhood",` defeat the quote heuristic (ambiguous with a real string end).
  2 of the 3 are the same resubmitted comment, so it's ~a handful of comments.
  Left as `page_type: "error"`; not worth more repair logic (regression risk).

### Do NOT
- **Do not edit `progress/raw/*.json`** — it's the immutable source of truth. All
  cleaning happens in memory in `clean_comments.py`.
- **Do not rename the PDF/JSON files** — `source_file` links the raw JSON,
  `progress/progress.json`, and every output. Filename typos are handled by an
  override map (`PERIOD_OVERRIDES`), not renaming.
- There is no longer an `all_comments_vision.csv` / `merge_vision_output.py` /
  emotion-classification branch — those were retired. `all_comments_clean.csv`
  is the single canonical table.

## Canonical output schema (`all_comments_clean.csv` / `comments_clean.json`)

`date, contact_name, subject, topic, comment, district, source, has_attachment,
source_file, page_numbers, period_start, period_end, date_normalized, quality_flag`

- `date_normalized` — **ISO `YYYY-MM-DD`; 100% populated. USE THIS FOR TIME ANALYSIS.**
- `page_numbers` — every source page a (possibly multi-part) comment spans.
  JSON: array `[5,6]`. CSV: `;`-joined `5;6`.
- `period_start` / `period_end` — the council "week" window from the filename
  (Wed → following Tue), with 4 filename typos corrected.
- `quality_flag` — `|`-joined (JSON: `quality_flags` array). Values:
  `date_from_filename`, `no_name`, `orphan_continuation`, `short_comment`.

## What `clean_comments.py` does (and decisions made)

1. **Routes out non-comment tables** (petition/sign-on sheets) — detected
   structurally (page has no comment/description/message column).
2. **Re-stitches multi-part comments** ("1/2"+"2/2", "*Continued Below*", "N of M")
   into one row by adjacency + part-number continuity, tolerating empty names
   (later parts are often unnamed) and name typos. Embedded markers are scrubbed.
3. **Drops non-substantive rows** (not the commenter's own analyzable written text):
   empty/placeholder, "Live Public Comment", bare attachment pointers, staff
   third-person phone summaries, and **all voicemail content** (voicemail files +
   `source=Voicemail`).
4. **Normalizes dates** -> `date_normalized`. Falls back to the filename's meeting
   date when a row has no per-row date (flagged `date_from_filename`).
5. **Dedups** exact same-date duplicates (`name`+`comment`+`date`) — these come
   from overlapping file periods. Same person resubmitting on a *different* date is
   kept; mass form-letters (different names) are untouched.

All removed rows go to `all_comments_dropped.csv` with a `_drop_reason` — nothing
is silently deleted.

## Current counts (regenerate to refresh)

Clean total **13,334**. Per year (by `date_normalized`):
2020: 6583 · 2021: 1236 · 2022: 900 · 2023: 1307 · 2024: 2151 · 2025: 646 · 2026: 511

Dropped **1,654**: non_comment_table 851 · voicemail 515 · empty_or_placeholder 114
· duplicate 73 · staff_summary 62 · live_public_comment 37 · attachment_pointer 2.

## File cadence (important for binning)

- Files are **weekly, Wednesday → Tuesday** (the Tuesday = council meeting night).
- Coverage over the weekly era (2020-07-18 → 2026-04-07) is **97.0% contiguous**.
  ~59% of files are exactly 7 days; the rest are **single files that bundle 2–5
  weeks** at holidays/recess (still contiguous coverage, just a larger bucket).
- **Before ~2020-07-18**: comments were posted per *meeting date* (single-date
  files, all Tuesdays), often with multiple `_Part`/`_File` PDFs per meeting
  (June 2020 = George Floyd / police-budget surge). These rely on
  `date_from_filename`.

### Coverage gaps (intentionally unfilled — mostly the annual summer break)
~56 uncovered days across these windows; leave them empty when binning:
- 2021-05-12→05-18, 2021-06-02→06-08
- 2022-06-03→06-14 (~2 weeks)
- 2023-05-03→05-09, 2023-06-07→06-13
- 2024-06-05→06-11
- 2026-02-04→02-10

If asked to fill gaps: check slcdocs.com `…/Public_Comments/{year}/` for files in
those windows and add them to `download_comments.sh`.

## Weekly binning guidance

- **Bin on `date_normalized`** (each comment's real date), not on file/period.
  Same-date duplicates are already removed, so counts won't be inflated.
- Gap weeks will legitimately show **0** — that's expected, don't fill them.
- Caveat: `date_from_filename` rows (1,735, almost all 2020) carry the meeting/
  period *start* date, not an exact submission date. For **yearly** bins this is
  fine; for **weekly** bins they land on the period-start week. A small number
  (~19) sit inside multi-week bundle files, so they cluster on the bundle's first
  week. Filter on `quality_flag` containing `date_from_filename` to isolate them.

---
*Doc corrections 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): counts
refreshed from the current `all_comments_clean.csv` / `all_comments_dropped.csv` —
clean total 12,887 → 13,334 (per-year updated), dropped 1,638 → 1,654, weekly-era end
2026-03-10 → 2026-04-07 (97.3% → 97.0% contiguous), `date_from_filename` 1,717 → 1,735.*
