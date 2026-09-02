# W2 HANDOFF — Salt Lake County EasyVote residue itemization

**Prepared 2026-08-23 for an external agent (Kimi K3 or any capable vision-equipped agent).**
This document is the complete context package for running wave W2. It assumes no memory of
any prior session. Where this document and a primary source disagree, **the source document
governs** — every number here is a hypothesis to verify, not a fact to assert. That rule is
load-bearing: in the last four waves, coordinator briefs were wrong about queue sizes, office
resolution order, and document shapes, and in every case the agent that read the page caught it.

---

## 1. The mission

Salt Lake County's 2022/2024/2026 campaign-finance filings live in the county's EasyVote
system. Machine-readable itemized data (individual donations and payments) was recovered for
197 filings via the county's API. But **245 filings carry no itemized rows**, and a page-by-page
audit (`_audits/2026-08-20-easyvote-residue/` — read it in full) established:

- **197 of them contain real itemized detail inside the PDF documents** — an estimated
  **~18,433 lines over ~980 pages** (~86% of that figure is line-by-line counts; the rest is
  dense grids extrapolated at fixed row pitch — expect the true count to differ).
- 8 have genuinely empty schedules; 35 have no schedule page at all.
- **143 filings (all 2024 + all 2026) have no `filing_totals.csv` row at all** — their cover
  stated-totals were never read. Reading those covers is part of W2.

Your job: transcribe every itemized line and every missing cover from those documents into the
repo's campaign-finance layer, under the verification contract below. When you finish, every
document Salt Lake County holds is itemized, and recent county races (mayor, sheriff, council,
DA, row offices) have complete, searchable donor records.

## 2. Repository orientation — read these files before any work

Repo root: `/Users/tysonwelsh/civic-data`. Reading order:

1. **Root `CLAUDE.md`** — the whole campaign-finance block, plus the three cardinal rules.
2. **`GOTCHAS.md`** — standing operational rules. All apply. Pay particular attention to:
   the zero-glyph ruling; the escalation rules (§ Sources & portals); "vision renders FULL
   pages, never cropped"; the sqlite `mode=ro` habit; absolute paths.
3. **`salt_lake_county/campaign_finance/CLAUDE.md` + `AVAILABILITY.md`** — the module's own
   documentation: eras, channels, form families, caveats. The raw PDFs are under
   `salt_lake_county/campaign_finance/raw/` (EasyVote era under `raw/easyvote/`).
4. **`_audits/2026-08-20-easyvote-residue/`** — the audit that sized this corpus, including
   its per-filing findings. This is your queue's primary source.
5. **`_backups/2026-08-23-slco-w1p2/CLOSEOUT.md`** — the most recent closed SLCo wave
   (the 2015–2021 paper era). Match its conventions, ledger formats, and verification style.
6. **`_audits/cf-calibration-suite/`** — the calibration specimens and pass protocol (§4).
7. **`scripts/campaign_finance/`** — shared tooling: `validate_finance.py` (the conformance
   validator), `make_snippet.py` (renders a crop from stored geometry to verify it),
   `rowbands.py`/`fitgrid.py` (printed-rule row detection and row-count gating),
   `normalize_donors`, `common.py` (column contracts, including the trailing-optional
   `donor_occupation` column), and `tests/`.
8. **`PRIVACY.md`** — what ships verbatim vs redacted. CF documents ship verbatim. Also read
   the SLCo `cf-*` caveat rows in `gov.db` (`sqlite3 "file:gov.db?mode=ro"`, table `caveat`)
   including the EasyVote donor-geography note.

## 3. Non-negotiable ground rules (cardinal rules, applied to this wave)

1. **Never fabricate.** A cell you cannot read is ledgered illegible, never guessed. A side
   whose arithmetic cannot be closed against any printed figure is **withheld with the reason
   stated**, never estimated. Honest gaps are data.
2. **Documents are transcribed verbatim.** Filer errors (bad arithmetic, misspellings) are
   preserved exactly, with the discrepancy *traced and noted* — never corrected.
3. **Derived layers are regenerated, never hand-edited.** You write vision caches
   (`vision/<sha1(index path)[:8]>.json` — the repo-standard key; see
   `scripts/campaign_finance/vision_lib.py::cache_key`, which also defines the `sub`
   discriminator for multi-report PDFs) and, where the documented path requires, index/module
   inputs; `build_finance.py` derives `contributions.csv` / `expenditures.csv` /
   `filing_totals.csv` from them. Never hand-edit a derived CSV.
4. **Do not git commit anything.** The owner commits. Never run destructive git commands.
5. **Back up before modifying.** Workdir + pre-modification copies of every repo file you
   change go in `_backups/<date>-slco-w2/`. Checkpoint after every batch so a kill at any
   point is resumable.
6. **Redactions are honored as printed.** If a "redacted" PDF has black bars over an intact
   text layer, you transcribe only what is *visibly* printed. Never extract text from beneath
   a redaction bar; flag the file in your report instead (a known case exists — see
   `_backups/2026-08-23-slco-w1p2/OWNER_DECISION_PRIVACY.md`).
7. **School-board filings are out of scope** (owner ruling 2026-08-01). Classify by the
   **office line inside the form**, not the filer's label or folder: e.g. Charlotte
   Fife-Jepperson's 2024 covers read "Office Sought: Salt Lake School Board" although her
   filer label says County Council. Ledger exclusions; never transcribe under a wrong label.

## 4. Calibration pre-flight — required before bulk work

Before transcribing at volume, pass the calibration suite at `_audits/cf-calibration-suite/`
(read its README + pass protocol; ~21 specimens including negative controls whose correct
answer is BLANK or DROP). Record your pass results in your workdir. If you cannot pass the
suite, stop and report — do not bulk-transcribe on a failing configuration.

## 5. The transcription contract (the "B2 production contract")

These rules were hardened over six closed county waves. Each exists because its absence
corrupted data at scale.

- **Render full pages first** (~150–200 dpi) for field coverage. For any disputed or
  low-contrast cell, escalate with a **tight crop of that cell at ≥600 dpi** (up to 1200).
  Beware tool-side image downsampling: a high-dpi *full page* may be silently downscaled by
  your image pipeline — only a tight crop actually delivers resolution. And:
  **arithmetic closure outranks glyph reading at any resolution.** If the schedule's own sum,
  page subtotal, or balance chain says the digit is a 1, it is a 1, no matter how the glyph
  looks. (History: the "Rhodes reversal" — a 600 dpi re-read validated the wrong digit; the
  form's own sum decided it. `cache_county/campaign_finance/CLAUDE.md` § "Render resolution
  matters".)
- **Reconciliation-basis rule (owner-ratified, final per-page form):** reconcile each
  transcribed side against the printed cover figure that **matches its own scope** — the
  Current-Report column for a period-scoped ledger, the Cumulative column for a cumulative
  ledger — and run the scope test **per page**, because one filer can flip convention between
  an original and his amendment. Tag rows `is_incremental` accordingly. **Never synthesize a
  figure by differencing two covers.** Withhold only where *neither* printed figure closes.
- **Zero-glyph ruling:** a glyph that denotes zero (slashed Ø, `-0-`, the word "zero")
  transcribes as `0` with the verbatim glyph preserved in the cache notes; a bare dash,
  `N/A`, or an empty cell stays BLANK — a nil mark is not a numeral.
- **Completeness, not agreement, gates publication:** maintain found-vs-emitted row counters
  per side. A side publishes when every found row is emitted, even if the sum disagrees with
  the cover — a disagreement is then provably the *filer's* arithmetic, published verbatim
  with `reconciles_*=False` and the delta traced to a named page.
- **Geometry on every row:** store `pct:`-form bounding boxes (page, percentage coordinates)
  for each transcribed row; verify a sample per filing by rendering the crop back with
  `make_snippet.py` and confirming it reproduces donor + amount. Use `rowbands.py`/`fitgrid.py`
  as a row-count gate on ruled forms — and score against the ink centroid, not the ruled band
  (filers write *above* the rule).
- **Ghost-row screen:** blank county forms print example rows (Jon/Jane Doe). Correct answer:
  DROP, proven by the total closing only without them.
- **Transcribe once per sha256** and apply to every filing that shares the document
  (`applies_to`); filings can be split across PDFs and one PDF can bind multiple reports —
  verify document boundaries from content, never from filename or folder (folder years lie).
- **Amendments:** keep both documents; publish from the governing one; note the pair. Run the
  chain check (this filing's Last-Report figure vs the prior filing's Cumulative) across each
  candidate's filings — a break can mean a swapped or mis-keyed cover.
- **Known trap #1 — schedule-total vs summary gap:** on roughly a quarter of has-detail
  filings, the schedule's printed grand total sits *below* the Summary's line 1/2, uniformly
  because page subtotals exclude In-Kind rows the schedule does list. Settle in-kind treatment
  per filing from its own arithmetic; reconciling against the wrong total manufactures false
  deltas.
- **Known trap #2 — three structural shapes:** ~62% of has-detail sides are typed onto the
  county's own Schedule A/B grid; others attach the filer's spreadsheet; a third group has
  **no county schedule page at all** — the filer's own sheet IS the schedule. Classify each
  side's shape explicitly. Keying on a "See Attached" stub misses >1,000 rows.
- **`donor_occupation`:** the schema has a trailing-optional occupation/employer column.
  Capture it **only where the form actually prints such a field**; NULL means the form has no
  such field. Never infer it.

## 6. Verification gates — what "done" must prove

Minimum bar (transcription complete):
1. Queue closure measured, not counted: a coverage check derived from the audit's own
   per-filing ledger shows **remaining = 0** — never "N files processed".
2. Ledger per side: exact / filer-delta (traced) / withheld (reason) / empty — every one of
   the ~197 detail filings and 143 missing covers accounted for.
3. `python3 scripts/campaign_finance/validate_finance.py` (or the module's documented
   invocation) **PASS** for salt_lake_county after rebuilding via `build_finance.py`.
4. **Frozen blocks byte-identical:** the pre-existing itemized rows (clerk-legacy 22,871;
   the EasyVote API rows; the 2015–2021 paper-era 6,028) and every pre-existing `stated_*`
   cover figure must be unchanged by your work — prove it by diff, and explain any exception.
5. Everything backed up + checkpointed in `_backups/<date>-slco-w2/`, with a
   `CLOSEOUT.md` reporting all of the above.

Full bar (only if no other agent is working in the repo — coordinate with the owner):
6. One federation at the very end: `python3 scripts/build_cities_db.py` (absolute path) —
   its auto-gate must print 44/44 in step, `PRAGMA integrity_check` ok, foreign keys 0.
7. Regenerate the county cycle layer (`scripts/campaign_finance/cycle_totals_county.py`,
   see its `--report`/`--validate` flags) — published totals must be unchanged by
   itemization for the 197 detail filings (it derives from stated totals); the **143 new
   cover reads will legitimately change it** (they fill current gap rows) — report exactly
   which rows moved and why.
8. `python3 scripts/check_doc_numbers.py` — all checks PASS; any headline number your rows
   move must be updated in the docs in the same session.
9. Doc updates: SLCo `AVAILABILITY.md` dated verification section; the `cf-county-eras`
   caveat row rewritten; module + root `CLAUDE.md`; `TODO.md` changelog line.

If you cannot safely run the full bar, stop after the minimum bar and say so plainly —
a Claude session will run federation + docs afterward. **Never run the federation while any
other agent is working in the repo.**

## 7. Reporting conventions

- New observations that are out of scope → one-line bullets in `LEADS.md` (date + what was
  observed + evidence pointer). Never file work items there.
- A wrong or missing **published** value, verified at the primary source → `TODO.md` under
  `[DEBT]`, with the citation. Nothing else goes in TODO.md.
- Candidate calibration specimens (pages that would fool a naive transcriber) → note them in
  your closeout for promotion into the suite.
- Your final report: queue derivation arithmetic, per-tier ledger counts, dollar totals in/out,
  gate results one by one, docs touched, leads/DEBT filed, and anything that blocked you.

## 8. Sizing honesty

Expect ~18,433 lines to be wrong in the details — it is an estimate. Prior waves at this
scale (utah: 6,513 rows; SLCo clerk-legacy: 22,871 rows) survived session kills only through
checkpoint discipline. Chunk the queue, checkpoint each chunk, verify chunk completion against
the derived queue (a launched chunk is not a run chunk; a partial save is not a finished
chunk), and generate mechanical values from generators rather than typing them by hand.
