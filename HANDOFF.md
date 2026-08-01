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

Built **2026-08-01T00:28:03-04:00** · auto-gate → **44/44 in step** · integrity ok · FK 0 ·
reconciliation exact · caveat **91** · motion 78,561 (city 49,105 / county 27,271 /
regional 977 / state 1,208) · vote 180,980/38,592/0/27,887 · motion_std 77,353 ·
election_race **688** · comment 14,202 (redacted) · fts_minutes 14,696 · **0 built
entities without a caveat row** · check_doc_numbers 13/13 · marquee examples 5/5.

## NEXT (the PUBLISH GATE, in TODO.md — owner-approved 2026-07-31)

**G1 DONE 2026-07-31 — the repo is under git with a private remote:
`github.com/tysonwelsh/civic-data` (main, initial commit `e9872b9`, 59,468 files).**
Owner residue: rotate the ANTHROPIC_API_KEY; enable secret scanning at public-flip.
Commits are now the change record — wave-record prose in TODO.md is retired for good.
G3 DONE 2026-07-31 (MIT code / CC-BY-4.0 data / comment emails+phones redacted — 635+248
across 87 files, `scripts/redact_comments.py`, GOTCHAS re-run rule / CF text ships
verbatim per PRIVACY.md). ⚠ Next federation must precede any G9 release asset so
comment/fts_comment carry the redacted text.
**G4–G8 ALL DONE 2026-07-31 — the PUBLISH GATE is complete through G8 and SHIP_GATE
shows P1/P2/P3 ALL PASS at build 17:00:54.** G4 doc pass + check_doc_numbers (13
assertions); G5 FTS fixes (823 recovered-PMN texts indexed; statute floor); G6 packaging
(quickstart, examples 5/5, DATA_DICTIONARY, gov-sample.db, build_status registry column);
G7 hardening (lockfile + atomic build + auto-gate, proven live); G8 data fixes — mag_mpo
grammar (+14 motions, the inverted 2015-11-05 strike recovered), the date-collision class
(17 verified pairs across 10 entities fixed by an owner-approved 10-agent wave; ~70
phantom motions removed; ~10 vacated real meetings ledgered; detector now clean), weber
loop-skip (+15 motions corpus-wide). Headline counts moved to 49,105/27,262/973/1,208
motions · 180,979/38,589/0/27,887 votes · motion_std 77,340 · fts 14,696 — all docs
reconciled.
**2026-08-01 DEBT-CLEARANCE WAVE (owner-approved, 10 Opus agents + coordinator solo): the
post-restructure [DEBT] queue went 14 → 4.** Fixed: weber died-motions ×4 + an ORPHANED
contested roll recovered; ogden died ×2 + 7 primary races; midvale died ×1 + Erikson merge
+ weeks 13→0; EC parse_present + VERIFICATION rewrite; SSL 2021 rows plurality→RCV (the
"missing primary" premise failed — RCV has no primaries); draper 2025 canceled race added
(Res #25-49); murray 2021 Mayor primary certified-canvass corrections; wfrc +4 appositive
motions; washington premises failed (290/290 byte-identical; 82%→78% OCR doc fix);
bluffdale referrals ground-truthed 269→62 (-207 false links). Solo: logan RCV claim, riverton
auth-wall relabel, SLCo HA premise-failed, weeks_lib fixes (Meetings:0 class → 0 repo-wide),
kind_of committee fix. Five backlog premises failed at source — the evidence-not-fact rule
keeps proving itself. Closing federation 2026-08-01T00:28:03, all gates green
(check_doc_numbers 13/13 after reconciliation; election_race 680→688). SURVIVING [DEBT]:
the 56-row recommendation-oracle adjudication, the NEW 2021 RCV mislabel class (CH×3 —
incl. misleading first-choice margins on a 4-round mayor race — magna×1, slc×5), the NEW
bluffdale motion-text-window item, and the murray-PC audit routine.

**REMAINING = G9 (owner's move) + 4 [DEBT] + 6 [GATED]:** declare against SHIP_GATE.md, cut the GitHub
release (gzip gov.db → ~400 MiB asset + sha256), mint the Zenodo DOI, flip the repo
public, link from municipalsky.com. Also owner residue: rotate the ANTHROPIC_API_KEY;
enable secret scanning at public-flip. Run `check_doc_numbers.py` + the federation gate
after ANY future rebuild (both are one command each; the build auto-runs the gate).

## Session rules that changed today

- Agent launches (count, per-agent model, effort) are presented for OWNER APPROVAL first;
  Opus by default, Fable only where judgment-heavy (memory: approve-agent-launches).
- Leads → LEADS.md, never TODO.md; TODO admission requires primary-source evidence; closures
  archive in the same session; a closure that falsifies a doc claim fixes the doc in the
  same session (full rules: CLAUDE.md "Work tracking").
