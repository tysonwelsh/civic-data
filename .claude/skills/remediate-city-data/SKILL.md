---
name: remediate-city-data
description: Execute repairs on civic-data city repos from an audit report or defect list — verify each defect at source, fix at the right layer with backup discipline, regenerate the derived chain, and prove every change (expected-rows-only diffs, validators, doc reconciliation). The action counterpart to audit-city-data (which only reports). Use when the user wants to fix/repair/remediate data defects in one or more cities.
---

# Remediate city data

Executes repairs in `<city>_city_council/` repos under /Users/tysonwelsh/civic-data.
Input: an `_audits/<date>/report.md`, a defect list, or TODO.md items. This skill
encodes the discipline proven in the 2026-07-02 remediation (`REMEDIATION_PLAN.md` —
read it as the worked example; every pattern below has a receipt there).

## Setup

Create `_audits/<YYYY-MM-DD>/remediation.md` (or extend the audit's plan) listing the
defects ranked: data loss > garbling > wrong/duplicate documents > derived-layer
integrity > doc drift. Independent city workstreams run as parallel agents — **never
two agents on one city**; if another session may be editing a city's README/CLAUDE,
use targeted Edits only and put detail in VERIFICATION.md.

## Per-defect discipline (all seven steps, every time)

1. **Back up before touching**: copy each file you'll modify to
   `_backups/<date>/<relative path>` (no-clobber; add `.pre-<phase>` suffixes if a
   backup already exists there).
2. **Verify the defect at source before changing anything.** Re-fetch the source
   document via `minutes_index.csv`/`sources.csv` URLs; md5-compare; visually Read
   scanned pages. Audits are sometimes subtly wrong (the "St George 110 dup rows"
   were 70 dups + 40 legitimate rows from a real second meeting; the "16 Sandy
   page-break drops" were voice votes never named in source).
3. **Fix at the right layer.** Extraction bugs → fix the extractor and regenerate
   (never hand-edit a generated CSV). Wrong/stub/duplicate documents → re-fetch the
   real document (portal, then Utah PMN); if unrecoverable at every source, REMOVE
   and log in `minutes_unrecovered.csv` — an honest gap beats a wrong document.
   Garbled text → recover deterministically where possible (PUA −0xF000; contextual
   ligature restoration with judgment calls flagged in the file header); vision
   re-reads can't see through fonts that render tofu. Hand-edits to minutes markdown
   are allowed only to restore verbatim source text, noted in the provenance header.
4. **Faithful source contradictions are kept, not fixed.** A clerk listing a member
   in both AYES and NAYS stays verbatim in `all_votes.csv`; the db resolves it via a
   documented `db/vote_overrides.csv` row (value, resolution, reasoning). db builds
   must be FAIL-LOUD: any conflict not covered by an override kills the build. Never
   silently drop; never reassign a vote to a different person without source proof.
5. **Regenerate the full derived chain**: rerun the extractor → `all_votes.csv`, then
   `python3 scripts/rebuild_derived.py <slug>` (one command: db → referrals → weeks →
   motions_std → sources → validate, then coverage.json + cities.db incl. the search
   layer; fail-loud). TRAP: `db/referral_overrides.csv` pins application_ids
   that SHIFT when applications appear/disappear — remap via stable
   (source_file, motion_no) keys and verify the referral layer reproduces link-for-link.
6. **Prove the change.** The diff must be exactly the expected rows — state "all other
   rows byte-identical" only after checking (multiset compare). Re-run
   `screen_corpus.py` on touched corpora, the city's `validate_votes.py`, and
   `scripts/validate_city.py` (0 FAIL; new WARNs explained). For recovered text,
   verify against the source (token diff or visual page read); preserved source typos
   are evidence of fidelity.
7. **Document.** Dated addendum in the city's `VERIFICATION.md` (cause, action,
   before/after counts, evidence); fix every count in README/CLAUDE the repair
   changed; check the item off in the remediation plan; deferred or newly discovered
   issues go to TODO.md — never leave them only in an agent report.

## Boundaries

- `raw/` is never modified. City-faithful values are never overwritten — corrections
  flow through override files or extractor regeneration. Never fabricate: no invented
  votes, names, tallies, URLs, or text; unparseable → unknown/flagged.
- If a fix requires a judgment call the source can't settle (ambiguous clerk error,
  unrecoverable ambiguity), document the options and pick only if one is clearly
  defensible — otherwise exclude with a documented reason and flag for the owner.
- After all workstreams land: run a final validator sweep across affected cities and
  append a remediation summary to the driving audit report.
