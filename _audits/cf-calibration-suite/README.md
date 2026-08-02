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
3. **The Rhodes specimen tests the escalation rule, not the first read.** A first read
   at 150–200 dpi that yields "1," is expected; the configuration passes only if its
   disagreement/low-contrast path escalates to ≥600 dpi or a sibling copy and lands on
   "4". Two same-resolution passes agreeing is NOT a pass (correlated error — the whole
   reason this suite exists).
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

| failure mode | specimens |
|---|---|
| correlated misread / resolution | rhodes-4v1-fax |
| column transposition | summit-reversed-columns, utah-colAB-regime |
| zero-vs-blank discrimination | summit-zero-glyph, summit-genuine-blank, wasatch-word-zero, wasatch-na-blank, weber-dash-nil |
| currency conventions | slco-decimal-comma, slco-superscript-cents, utah-malformed-decimal |
| page selection / decoys | utah-checklist-decoy |
| completeness gating | washco-wrapped-ledger |
| field/column shift (reconciliation-proof errors) | wasatch-field-shift |

The `wasatch-field-shift` specimen carries the suite's sharpest lesson: its amounts
reconciled EXACTLY while the name/date columns were systematically wrong — sum-level
gates cannot see mis-columned rows. Field-level screens (or geometry) are mandatory,
and "withhold the side" is a passing answer.
