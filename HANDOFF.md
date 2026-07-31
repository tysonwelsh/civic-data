# HANDOFF — resume point (as of 2026-07-31: publication review → restructure → caveat fix)

> **Read in order: root `CLAUDE.md` → `TODO.md` (queue = PUBLISH GATE + [DEBT] + [GATED]) →
> `SHIP_GATE.md`. Standing operational rules: `GOTCHAS.md`. Options/leads/watches: `LEADS.md`.
> This file is ONE session banner, overwritten each handoff (prior banner → TODO_ARCHIVE.md).**

## What this session did

1. **13-agent publication-readiness review** (owner-requested; 8 Opus triage agents verified
   every open TODO item against the repo — 245 rows — + 5 review agents). Deliverables:
   `_audits/2026-07-31-publication-review/report.md` (synthesis) + `triage_full.md` (all rows,
   evidence-cited). Headline: data publishable now, packaging not; only 10 of 245 rows were
   fix-before-publish; 86 were already-done or not-an-issue; the backlog was wrong in BOTH
   directions (3 filed defect sections falsified at source — holladay's "10 duplicate Layton
   rows" are TWO real people; executing the filed fix would have deleted 10 genuine votes —
   while the worst real defects were filed nowhere).
2. **TODO restructure (owner-approved).** TODO.md 3,786→~165 lines ([DEBT]+[GATED]+PUBLISH
   GATE only); new `LEADS.md` (options/tails + WATCHES table, no checkboxes); new `GOTCHAS.md`
   (standing rules out of HANDOFF); new `SHIP_GATE.md` (3 runnable predicates + the policy:
   open DEBT blocks publish only if a published value is WRONG); NEXT_SESSION_PLAN.md retired;
   CLAUDE.md work-tracking rules rewritten (leads→LEADS.md; DEBT needs primary-source
   evidence; same-session archiving; ≤3 promotions/session; no umbrellas). Everything
   pre-restructure preserved VERBATIM in `TODO_ARCHIVE.md` anchor
   `2026-07-31-RESTRUCTURE` (+ `_backups/2026-07-31-todo-restructure/`, local only).
3. **PUBLISH GATE G2 — caveat refresh — DONE.** Caveat table **63→88 rows**; the two
   FALSIFIED rows rewritten (utah_county "blind after 2018" — repaired 07-25, now states the
   42-of-63 honest residual; weber "21 scans never OCR'd" — OCR'd 07-26); south_jordan PC
   `dissent-only` added (its 100%-nay PC rows were uncaveated); millcreek comments caveat now
   matches the built 27-letter harvest; **16 previously zero-caveat entities back-filled**
   (SLCo wave + lehi: tally-only/dissent-only/mayor-vote/OCR/coverage ceilings from their own
   CLAUDE.md); NEW disposition-coverage rows (cities+cache+mag only) + campaign-finance
   coverage rows (cf-coverage 29-of-31; slc honest-zero portal-blocked; draper unstructured;
   kearns blocked cycles); summit disposition caveat reworded (blanket "counties" claim was
   false).

## LIVE DB STATE (verified post-federation)

Built **2026-07-31T14:30:48-04:00** · `validate_entity.py --federation` → **44/44 in step** ·
integrity ok · FK 0 · reconciliation exact · caveat **88** · motion 78,608 (city 49,172 /
county 27,269 / regional 959 / state 1,208) · vote 181,119/38,597/0/27,887 · motion_std
77,400 · election_race 680 · comment 14,202 (millcreek 27 now enumerated) · fts_minutes
13,886 · **0 built entities without a caveat row**. Verified surfacing: south_jordan PC and
magna rows in v_member_record_all carry `dissent-only`.

## NEXT (the PUBLISH GATE, in TODO.md — owner-approved 2026-07-31)

**G1 DONE 2026-07-31 — the repo is under git with a private remote:
`github.com/tysonwelsh/civic-data` (main, initial commit `e9872b9`, 59,468 files).**
Owner residue: rotate the ANTHROPIC_API_KEY; enable secret scanning at public-flip.
Commits are now the change record — wave-record prose in TODO.md is retired for good.
Next: G3 (LICENSE/CITATION/METHODS/PRIVACY + the owner's two privacy decisions), G4 (doc-
consistency pass — README county counts 24,346→27,269 etc.; CLAUDE.md 27,376→27,269;
regenerate cities_db_SCHEMA.md), G5 (FTS: 935 excluded pmn_minutes), G6 (quickstart +
gov.db.gz release asset), G7 (atomic build + lockfile + auto-gate), G8 (three wrong-value
data fixes: mag_mpo inverted outcome, mis-dated-meetings class, weber 2019-07-30), G9
(declare against SHIP_GATE.md → publish).

## Session rules that changed today

- Agent launches (count, per-agent model, effort) are presented for OWNER APPROVAL first;
  Opus by default, Fable only where judgment-heavy (memory: approve-agent-launches).
- Leads → LEADS.md, never TODO.md; TODO admission requires primary-source evidence; closures
  archive in the same session; a closure that falsifies a doc claim fixes the doc in the
  same session (full rules: CLAUDE.md "Work tracking").
