# planning_commission/ — Herriman Planning Commission vote pipeline

Same schemas and pipeline as `../meeting_minutes/`, for the **Planning Commission**
(`body=PlanningCommission`). Read that folder's `CLAUDE.md` for the shared mechanics; this
file records only what differs.

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **130** PC minutes, 2020-01-02 →
  2026-05-20. The PC meets **Wednesday** (1st & 3rd). Indexed in `minutes_index.csv`.
  `source` ∈ `primegov` (111) / **`s3-legacy` (19, the 2020 backfill** from the legacy
  `herriman-agendas` AWS S3 bucket — PrimeGov only serves 2021-01+).
- `raw/`, `extract_votes.py`, `votes/*.json`, `votes/_validation_report.txt`,
  `all_votes.csv`, `motions_std.csv` — as in `meeting_minutes/`.
- **+11 PMN-promoted PC docs** (2026-07-16) living in `../pmn_backfill/text/`, merged into
  `all_votes.csv` by **`extract_backfill_votes.py`** with **`provenance=pmn_minutes`**
  (audited rows = `minutes`); incl. the 2020-12-03 meeting behind the old "COVID
  cancellation" belief, 2021-22 dates the portal never served, and the 3 tesseract-OCR
  scans (2022-06-16, 2023-01-04, 2023-01-18 — the 2023-01-04 scan's header-year misprint
  is preserved). NOT promoted (sidecars in `pmn_backfill/`): 2023-11-01 (stamped DRAFT)
  and 2022-04-21 (the PMN "Minutes" file is a mislabeled zoning use-table) — both now in
  `minutes_unrecovered.csv`.

## Run
```
python3 extract_votes.py
python3 extract_backfill_votes.py   # REQUIRED — merges the promoted PMN docs + provenance
python3 validate_votes.py
```

## Validation summary (2026-07-19)
141 meetings (130 audited + 11 promoted) · **926 motions** · **3,661 vote rows** (provenance
`minutes` 3,389 / `pmn_minutes` 272). The PC is a 5–7-member commission (no mayor); a full roll names the seated
commissioners; alternates print "Not Voting" rows on some 2023+ rolls (non-votes, honestly
not captured). The promoted 2023-01-04 roll carries Herriman's first **Recuse** row
(Commissioner Fenn, conflict of interest, item 4.1). **2026-07-16 extraction repair:** the
audited 2023-08-02 doc's item-4.1 motion printed "Commissioner Jacobson to approve …"
(verb "moved" omitted — a documented dropped-verb clerk typo healed in the extractor);
its 6-Yes roll had been mis-attributed to the preceding close-hearing motion and is now
correctly attached (close-hearing is tally-only per source).

**2026-07-17 T3.1(j) extractor sync (divergence closed).** The council's 2026-07-12
T3.1(j) repairs had never been copied to this PC `extract_votes.py` (the "one file, both
datasets" copies had drifted): (1) `OUTCOME_RE` now heals an outcome sentence that WRAPS
across a single line break; (2) an inline narrative-roll block ("`<Role Name>, <Role
Name> voted aye, and <Role Name> voted nay`") is now recognized; (3) the result string is
cut of trailing prose/page-numbers that leak into a period-less outcome sentence. **Net
effect on the PC corpus: ZERO row/text changes** — the PC exhibits none of these forms
(no mayor-narrative inline rolls; the commission uses tables; no wrap-truncated results;
no colon-tally page-number leaks). The one exception: the council's trailing-page-number
strip `\s+\d{1,3}$` is calibrated to the council's COLON tally ("3:2", no space before
the last digit) and would have CORRUPTED the PC's WORD-form tally ("a vote of 4 to 3" →
"4 to", the 2023-10-18 m2 tie-break roll). A PC-grammar guard `(?<!to )` was added so the
strip removes only a genuine leaked page number ("... 4 to 3 11" → "4 to 3"), never a
tally digit. Post-guard the sync is a verified no-op: 3,642 rows unchanged (provenance
`minutes` 3,370 / `pmn_minutes` 272 — the backfill rows intact), `motions_std.csv`
byte-identical, validate_votes 0 hard failures, validate_city 24 PASS / 2 WARN / 0 FAIL.
Run order after any re-extract stays: `extract_votes.py` → `extract_backfill_votes.py`
→ `validate_votes.py`.

**2026-07-19 extractor idempotency repair (shared file; council + PC).** A `--force` /
backfill re-extract was NOT reproducing the canonical `all_votes.csv` — three latent bugs,
now fixed in BOTH copies:
1. **`DROPPED_VERB_RE` mis-fire (mover-blanking).** `NAME` matches uppercase tokens, so on
   the COMMON all-caps line "Commissioner Jackson Ferguson **MOVED** to approve …" the healer
   swallowed "MOVED" as a name token and double-inserted "moved", making the mover capture
   "Jackson Ferguson MOVED" → `resolve_person()` blanked it. A **negative-lookahead guard**
   now fires the healer ONLY when the verb is genuinely omitted (rejects any
   "`<Role> <Name> moved/motioned`" line). Corrupted 58 movers on re-extract (1 mm-audited,
   51 pc-audited, **6 pmn-recovered** — the pmn layer, always re-parsed, already carried
   blank movers). **Net PC change: 6 pmn movers RECOVERED** (2021-06-17 m1–m5 Rypien/Palmer/
   Rypien/Palmer/Ferguson, 2021-10-07 m2 Jacobson — all source-verified); audited movers were
   already correct (JSON-resumable) and now reproduce byte-identically.
2. **Wrap-crossing OUTCOME_RE swallowed a page header** across a form-feed (`\x0c`) page
   break ("The motion passed unanimously \x0c August 2, 2023 Planning Commission Meeting
   Minutes Page 6 of 9"; 2023-08-02 m7). The result is now cut at the form-feed FIRST — a
   result sentence never spans a page break.
3. **Role-strip ate a word-form tally clause** ("…five votes in favor and **one Commissioner
   abstaining**" → "…and one"; 2021-03-04 m3). The new-speaker strip now requires a
   CAPITALIZED name after the role, so "one Commissioner abstaining" is kept and a real
   trailing narrator ("3:2 Councilmember Smith explained") is still cut.
Fixes 2–3 RESTORE the canonical result strings (pre-existing non-idempotency, present in the
backup extractor too). After the fixes the pipeline is byte-idempotent on both datasets;
mm `all_votes.csv` is byte-identical to its pre-fix state; PC differs only by the 6 recovered
movers; `motions_std.csv` byte-identical (mover is not a std field); validate_city
24 PASS / 2 WARN / 0 FAIL. The two extractor copies still differ by exactly the one
documented `(?<!to )` PC-grammar guard line.

## The vote grammar
Same forms as the council extractor: a full named roll under `"The vote was recorded as
follows:"` (`Commissioner <Name> Aye|Nay`), tally-only `"all voted aye"` (placeholder row,
member blank), named-absence unanimous, and contested `"passed with a vote of 5 to 1"` with
the named dissenter. `result`/`motion_type` verbatim; normalized values in `motions_std.csv`.

## ⚠ Documented source typo — "Commissioner Lorin Powell" (retained verbatim)
Exactly **5 PC rows in 2020** (2020-08-20 m2, 2020-09-17 m2, 2020-11-19 m1 & m2, and the
promoted 2020-12-03 m4) print `Lorin Powell` — a clerk conflation of **two real
seat-holders**: Commissioner **Andy Powell** and Commissioner **Lorin Palmer** (who sat on
the PC 2020–2021 before becoming Mayor). It is **kept exactly as the source prints it**,
never guess-merged into either person. **Flag it on any person-level 2020 PC join** — a
`Lorin Powell` row cannot be confidently attributed to either individual. (Contrast:
`Darryl Finn`, one 2021-06-17 roll row, IS folded to Darryl Fenn — the same doc prints
Fenn in 9 other rolls, an unambiguous same-person typo in `CANON_FULL`.)

## Roster (14 people across 2020–2026)
Current core: Jacobson, Bradford, Andy Powell, Rypien, Garcia, Ferguson, Fenn (2021+),
Sickles (2022+), Oberg (2023+). Earlier/short: **Lorin Palmer** (2020–2021, → Mayor), Chris
Berbert, Joy Kaseke, **Terrah Anderson** (2023–2025, → Council D4), and the typo `Lorin
Powell` (5 rows). Palmer and Anderson are each a single `person` spanning PC + Council — a
person-level join spans both bodies by design.

## Cross-body role
PC recommendations flow to the Council; the reconstructed `../db/civic.db` `referral` layer
links them (51 Council←PlanningCommission links post-promotion: 23 high / 22 medium /
6 low — respect the confidence column). Herriman's PrimeGov minutes carry no structured
planning file-number key in the vote prose, so cross-body linkage falls to subject +
address + temporal.

## Coverage floor (2020) — the S3 backfill
Coverage begins **2020-01-02**. The 19 2020 PC docs were recovered from the legacy S3 bucket
(18 carry votes). ⚠ Not every 2020 interior gap was a COVID cancellation: 3 PC dates are
proven cancellations (proof pages in `../pmn_backfill/`), and 2020-12-03 was a real meeting
(promoted 2026-07-16). The remaining true gaps live in `minutes_unrecovered.csv`
(2022-04-21, 2023-11-01).
