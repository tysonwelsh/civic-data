# CF transcription calibration suite (standing regression instrument)

Created 2026-08-02 (owner-directed, tranche 3 Phase A; the [GATED] TODO note is the
companion decision about retroactively rerunning tranches 1–2 under it). Pattern: the
"select sample pages" human-in-the-loop stage of the Library-of-Congress-lineage
"enriched pipeline" (Green Book digitization) — but run as a **regression suite of
known-hard pages**, not a representative sample.

## What this is

`manifest.csv` — 13 specimens, each a documented transcription trap from the 2026-08
county campaign-finance waves, with the expected output and the evidence citation.
**Any model / resolution / prompt / parser configuration must pass every applicable
specimen BEFORE it earns bulk-transcription rights** over a corpus. That includes:
a new model tier (e.g. a Sonnet pilot for tranche 3), a changed render recipe, a new
form family, or a rerun of a prior tranche.

## Protocol

1. For each specimen applicable to the target corpus/configuration: render the cited
   page **FULL-PAGE** (never cropped — GOTCHAS rule) at the configuration's standard
   resolution, transcribe with the configuration under test, and compare to
   `expected_json`.
2. **Negative controls are load-bearing.** Several specimens' correct answer is a
   BLANK or a WITHHELD sum (`summit-genuine-blank`, `wasatch-na-blank`,
   `weber-dash-nil`, `washco-wrapped-ledger`, `utah-malformed-decimal`). A
   configuration that "recovers" a value on these FAILS — eagerness is the failure
   mode being screened.
3. **Escalation means TIGHT CROPS at high dpi, never full-page dpi** (the Read tool downsamples ~2000px). **But escalation resolves LEGIBILITY, never TRUTH** — the Rhodes specimen's answer was CORRECTED 2026-08-02 after a 600dpi sibling 'settlement' validated the WRONG digit: the glyph is bistable at any resolution, and only the document's own arithmetic (Form A sum + cover closure) decides it. A configuration passes Rhodes by reaching '1' via arithmetic closure; reaching either digit by re-reading alone — even 'confirmed' across copies — is a FAIL (correlated error, the suite's founding lesson, now proven twice).
4. Zero-glyph specimens apply the owner ruling 2026-08-02 (GOTCHAS.md): Ø / -0- /
   written "zero" → 0 with verbatim preserved; bare dash / N/A / empty → blank.
5. Record results as a dated table appended to `runs.md` in this directory:
   configuration, specimen results, pass/fail, and what was changed before retry.
   A configuration change after a failure restarts the suite.

## Growing the set

Add a specimen whenever a wave documents a new trap class (one row, expected values
ground-truthed at the page, evidence citation to the module doc that records it).
Candidates should come from each county's CLAUDE.md/AVAILABILITY.md "traps"/"cardinal
rule" sections — if a trap was worth documenting, it is worth regression-testing.

## Current coverage by failure mode

**21 specimens** (13 original + 7 added 2026-08-18 by the utah_county Phase B pre-flight, per
the wave brief's instruction to grow the suite with the candidates the weber/summit waves
produced).

| failure mode | specimens |
|---|---|
| correlated misread / resolution | rhodes-4v1-fax |
| column transposition | summit-reversed-columns, utah-colAB-regime |
| zero-vs-blank discrimination | summit-zero-glyph, summit-genuine-blank, wasatch-word-zero, wasatch-na-blank, weber-dash-nil |
| currency conventions | slco-decimal-comma, slco-superscript-cents, utah-malformed-decimal |
| page selection / decoys | utah-checklist-decoy, **summit-swapped-pages** |
| completeness gating | washco-wrapped-ledger |
| field/column shift (reconciliation-proof errors) | wasatch-field-shift |
| **non-transaction rows on the page** | **summit-specimen-row** |
| **GEOMETRY correctness (pointer errors no sum can see)** | **utah-underline-band-offset, weber-wrong-column-pointer, weber-rtl-rows** |
| **cross-filing / cross-document errors** | **weber-swapped-cover-pair** |
| **provenance-token traps** | **utah-template-vintage-year** |

### The three failure classes the 2026-08-18 additions open up

The original thirteen almost all ask *"is this cell's VALUE right?"*. The seven added on
2026-08-18 ask three questions the suite could not previously pose:

1. **Is the POINTER right?** `utah-underline-band-offset`, `weber-wrong-column-pointer` and
   `weber-rtl-rows` are all cases where every amount is correct, every side reconciles to the
   cent, and the stored `pct:` geometry still aims at the wrong cell — one row early, the
   donor-name column, or the ledger in reverse. **No arithmetic gate can see any of them**;
   only a render-back of the stored box can. They are why the two-crop proof is mandatory.
2. **Is the ROW a transaction at all?** `summit-specimen-row` — the blank form's own printed
   example, left in place by the filer. The proof it must be dropped is arithmetic (the
   printed total closes only without it), never the highlighting.
3. **Is the error even ON this page?** `weber-swapped-cover-pair` is two internally-consistent
   covers filed under swapped keys, and `utah-template-vintage-year` is a year token that
   belongs to the blank form's vintage rather than the report. Both are invisible to any
   single-page check.

The `wasatch-field-shift` specimen carries the suite's sharpest lesson: its amounts
reconciled EXACTLY while the name/date columns were systematically wrong — sum-level
gates cannot see mis-columned rows. Field-level screens (or geometry) are mandatory,
and "withhold the side" is a passing answer.
