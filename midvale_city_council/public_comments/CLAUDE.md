# public_comments/ — Midvale (HONEST-EMPTY, submit-only)

## Status: no published written-comment archive
Midvale City publishes **no** standalone written-public-comment corpus — no eComment portal,
no correspondence/letters page, no packet-embedded comment compilation. Public comment is taken
**in person** at Council and Planning & Zoning meetings (and via submit-only channels); the
minutes carry an inline **"Public Comments"** section that paraphrases who spoke, which is a
**meeting-record speaker note, not a genuine written comment**. Reading those paraphrases into a
comments table would fabricate structure the city never published.

So `all_comments_clean.csv` is **header-only by design** (the 14-column standard header, zero
data rows). This is a **legitimate honest zero**, not missing data — do not treat the empty file
as an extraction gap, and never backfill it from minutes speaker notes. The full verdict and the
sources checked are in `AVAILABILITY.md`.

## Files
- `all_comments_clean.csv` — the standard header only (0 rows).
- `AVAILABILITY.md` — the availability audit (why this city is submit-only).
- `raw/` — retained originals if any snapshot was captured (empty by default).

## If Midvale ever starts publishing comments
Add the acquisition + cleaning here and populate `all_comments_clean.csv` to the collection
schema
(`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`),
then rebuild the weekly bundles (`python3 ../build_weeks.py`) so comments join votes on the
Tuesday grid. Until then, this folder documents the honest gap.

## Cross-city note
Substantive published comments exist only in **SLC + Park City** across the collection; Midvale
is one of the honest-zero cities. See the root `CLAUDE.md` coverage-asymmetry notes before any
cross-city comment aggregation.
