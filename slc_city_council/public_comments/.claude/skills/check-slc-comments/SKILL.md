---
name: check-slc-comments
description: Check slcdocs.com for newly published Salt Lake City Council public-comment PDFs, download any new weekly files, extract them with Claude Vision, and fold them into the cleaned dataset. Use when the user wants to refresh/update the SLC public comments data, check for new comment files, or "get the latest comments".
---

# Check for new SLC public comment files

Refreshes the SLC public-comments dataset with any weekly PDFs published since the
last run. Work in `/Users/tysonwelsh/civic-data/slc_city_council/public_comments`.

## Steps

1. **Probe + download.** Run:
   ```
   python3 check_new_comments.py
   ```
   It finds the latest file we have, probes the city site forward (handling
   multi-week bundles and recess gaps), downloads any new PDFs into the right year
   folder, and appends them to `download_comments.sh`. It prints each new file and
   an `AFFECTED_YEARS=...` line.

2. **If it prints "Up to date":** report that and stop — nothing more to do.

3. **Extract the new pages.** For each affected year from `AFFECTED_YEARS`, run:
   ```
   python3 vision_extract.py --year <year>
   ```
   This calls the Anthropic Vision Batch API (incurs cost). `progress/progress.json`
   marks already-done pages, so only the new pages are processed. The API key loads
   automatically from `.env` (via `config.py`) — do not ask the user for it.
   The script submits a batch and polls until it ends; this can take several minutes.

4. **Fold into the cleaned dataset.** Run:
   ```
   python3 clean_comments.py --report
   ```
   This regenerates `all_comments_clean.csv`, `comments_clean.json`, `by_year/`, and
   the dropped-rows audit from the raw JSON.

5. **Report** to the user: how many new files, the new per-year comment counts, and
   the new clean total.

## Notes
- `progress/raw/*.json` is the immutable source of truth; never edit it by hand.
- See `CLAUDE.md` in the project for the full pipeline, schema, and cleaning rules.
- If extraction fails on a key error, confirm `.env` exists and contains
  `ANTHROPIC_API_KEY=...` (it is gitignored).
