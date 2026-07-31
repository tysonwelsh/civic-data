# public_comments/ — Herriman City (HONEST-EMPTY)

**Verdict: HONEST-EMPTY — no published written-comment archive.** Herriman offers only
**submit-only** public-comment channels; nothing is published as a retrievable
written-comment dataset. `all_comments_clean.csv` is therefore **header-only** (the 14-col
collection schema, zero rows) — this is *data*, not a gap. **Do not fabricate rows.**

## What's here
```
all_comments_clean.csv   14-col schema, HEADER-ONLY (0 rows) — by design
AVAILABILITY.md          the completed 2026-07-11 audit (browser UA) documenting the verdict
raw/                     empty — nothing to retain
```

## Why empty (from AVAILABILITY.md)
Herriman's only public-comment mechanisms are **submission**, tied to a live or upcoming
meeting, not an archive:
- the PrimeGov portal **"Add a new comment"** (eComment) form, and
- the **"Request To Speak"** form.

There is **no** standalone written-comment / correspondence / eComment **archive** page to
harvest. Public comment is taken in-person at meetings and via the eComment submission window
that closes with the meeting. This is the same honest-zero pattern as Taylorsville / South
Jordan (submit-only), and it supersedes the recon's "UNCONFIRMED" placeholder with a
completed audit.

## Consequences for analysis
- Treat comment volume for Herriman as a **legitimate honest zero**, never a missing dataset.
- The weekly bundles (`../weeks/`) carry **no** comments files, consistent with this verdict
  (`validate_city.py` check `i.weeks` confirms).
- Speaker names paraphrased in the meeting minutes (`Public Comment` agenda items) are
  **meeting-record notes, not genuine written comments** — do not promote them into a comment
  corpus.

## If Herriman ever publishes an archive
Rebuild the flat table with the collection's comment cleaner and drop the header-only stub;
update `AVAILABILITY.md` with a dated addendum recording the new source.
