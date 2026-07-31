# meeting_minutes/ — Town of Alta Council vote pipeline

## What's here
- `raw/<date>_<slug>.pdf` — **85** retained source minutes (Utah PMN body **1601**,
  `utah.gov/pmn/files/<file_id>.pdf`), 2020-02 → 2026-06. Never modified.
- `raw_text/<slug>.txt` — OCR text cache for the **36 image-only (scanned) PDFs**
  (pdftoppm 300dpi + tesseract); the other 49 are born-digital.
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — cleaned markdown + YAML provenance
  header (`source: pmn`, `source_url`, `pmn_file_id`, `format: ocr|pdf-text`). Council
  meets **2nd Wednesday** monthly; folder keyed on that week's Monday.
- `minutes_index.csv` — 8-col standard (`source=pmn`; `format` = `pdf-text` 49 / `ocr` 36).
- `minutes_unrecovered.csv` — header-only: **every PMN-enumerated council doc was
  recovered** (no gaps; 2020 is the floor, minutes exist earlier but out of scope).
- **+3 PMN-promoted council docs** (2026-07-16) living in `../pmn_backfill/text/`
  (2020-05-06, 2020-06-17 born-digital; 2024-08-14 tesseract-OCR — a COUNCIL meeting
  PMN mis-filed under PC body 1602), merged into `all_votes.csv` by
  **`extract_backfill_votes.py`** with a documented trailing 14th **`provenance`**
  column (`minutes` = audited docs, `pmn_minutes` = promoted PMN recoveries). All
  three are in-body-verified APPROVED minutes; they were invisible to the original
  label-based harvest (posted as "Public Information Handout" / wrong body).
- `extract_votes.py` — PURE deterministic parser (no LLM/network; resumable). Run:
  `python3 extract_votes.py council [--force]` → `votes/<year>/<week>/<slug>.json` +
  `all_votes.csv` (13-col standard + `provenance` after the backfill merge).
- `validate_votes.py` — `python3 validate_votes.py council` → `votes/_validation_report.txt`
  + `roster.csv` (observed voters). Since 2026-07-16 it covers the MERGED record
  (audited JSONs + the `pmn_minutes` rows read back from `all_votes.csv`).
- **Run order:** `extract_votes.py council` → `validate_votes.py council` →
  `extract_backfill_votes.py` (LAST — the first two rebuild `all_votes.csv`/roster
  without the pmn rows; the backfill merge restores them idempotently).
- `screen_corpus.py` (repo root) — corpus-screen gate: flags image-only PDFs for OCR.

## THE MAYOR VOTES (max tally = 5)
Utah **Town** form: the Mayor is an ordinary voting member. A full roll call = **5**
(Mayor + 4 at-large councilmembers). No tie-break special-casing. Mayor turnover in-span:
**Harris Sondak** was Mayor **2020–2021**; **Roger Bourke** Mayor **2022→present**. The
2020–21 councilmember Bourke is **MARGARET Bourke** (Roger was a Planning Commissioner
then). Names resolve **PER FILE** (the meeting's own PRESENT-block/role-prefixed full
names beat the corpus-modal roster), so "Mayor Sondak" / 2021 "Council Member Bourke"
never misattribute to Roger Bourke (T3.1(a) fix, 2026-07-12).

## The BUDGET COMMITTEE is a SEPARATE body in the same PDF (`body=BudgetCommittee`, 2026-07-29)
An Alta "council minutes" document frequently minutes **more than one meeting**: the town's
**Budget Committee** — **Mayor + 2 councilmembers + the staff TREASURER** — meets immediately
before the Town Council and its minutes are printed in the same file, opened by
`CALL THE BUDGET COMMITTEE MEETING TO ORDER` and closed by the next `CALL THE …TO ORDER` /
`TOWN COUNCIL MEETING` banner. It is **not** the Town Council (the other two councilmembers
neither sit nor vote on it). `extract_votes.py` used to hard-code `body=Council` for every
motion in the file, so BC actions were recorded as **council votes** — which put Treasurer
**Craig Heimark** (staff 2022-05→2025; certified to the Council only for the 2026 term) in the
**2022 council roll**: `2022-04-13` m1 `VOTE: In favor: Bourke, Morgan, Byrne and Heimark`
is the *budget committee* approving *budget committee* minutes. Fixed by a **sub-meeting body
walk** (`body_walk()`); **7 motions** now carry `body=BudgetCommittee` — 2022-04-13 m1,
2022-12-14 m1, 2023-02-08 m1, 2023-04-12 m1, 2023-05-10 m1+m2, 2023-06-07 m1 (that last file
is a BC meeting end-to-end) — 5 adjournments + 2 BC-minutes approvals, one of them the only
named roll (4 rows: R. Bourke / Morgan / Byrne / Heimark). **No row was added, removed, or
otherwise altered** (1,159 rows before and after; 88 meetings / 505 motions / 181 named / 324
tally-only / 28 contested unchanged). Heimark's db `role` on **Council** now starts
**2026-01-14**, matching `roster/council_terms.csv`. The `PUBLIC HEARING` sub-sections are
left as `Council` — the source never says which body adjourns them, and guessing would
fabricate. ⚠ `scripts/db_build_lib.kind_of()` classifies the name as `kind='council'`
(it only mints `committee` for names containing "board"), so the db's coarse `kind`/`stage`
still read council for these 7 — the `body.name` is the authoritative discriminator.

## Vote grammar (all handled; `result`/tallies verbatim-ish, normalize via motions_std)
- **Named per-member roll call:** `ROLL CALL VOTE [BY JEN CLANCY]: Councilmember Byrne –
  yes, ... Mayor Bourke – yes`. Clerk Jen Clancy's token **`I` = Aye** (a checkmark;
  confirmed by trailing "All in favor"/"Against: no votes").
- **Named in-favor / against lists:** `VOTE: In favor: Bourke, Davis, Byrne, Morgan and
  Anctil. None opposed.` and narrative `The Mayor, John Byrne, ... voted I in favor of the
  ordinance. Carolyn Anctil voted nay.` (+ narrative abstain/absent).
- **Tally-only unanimous (majority UNNAMED):** `VOTE: All in favor.` / `unanimous consent`
  → one placeholder row, `member`/`vote` blank (no member ever guessed).
- **Amendment-then-main double votes** under one agenda item: the parser reads the **main**
  (last) `VOTE:`, not the `AMENDMENT VOTE:` sub-vote.
- **`RESULT:` line** (newer docs) taken verbatim, normalized to a keyword.

## Known SOURCE defect, retained verbatim: the 2024-02-14 "Councilmember Davis" roll call
`2024-02-14` m4 (approve **Ordinance 2024-O-3**) prints
`ROLL CALL VOTE: Councilmember Byrne — yes, Councilmember Davis — yes, Mayor Bourke — yes,
Councilmember Morgan — yes, Councilmember Anctil — yes` in the **APPROVED** minutes (verified
against the source PDF page 10, not just the OCR sidecar). **Sheridan Davis lost the 2023
election and left the council at the 2024-01-10 seating of Dan Schilling**; he is *not* in this
meeting's PRESENT block, and the roll call three paragraphs earlier (Res 2024-R-4, same page)
names **Schilling** in exactly that slot. It is a **clerk transposition in the primary
document**, not an extraction artifact — so the row stays **verbatim** (cardinal rule 2:
city-faithful values are never overwritten). It is the sole reason `role.last_seen` for Davis
is 2024-02-14 rather than 2023-12-13. Do **not** "repair" it in `all_votes.csv`; the shared
`db/vote_overrides.csv` mechanism cannot express a wrong-*person* correction (it resolves
contradictory values and adds missing members only), and substituting Schilling would be
inference, not record.

## Coverage (measured, post-promotion 2026-07-16; tally-recovery 2026-07-19)
**88 meetings (85 audited + 3 PMN-promoted)** · **505 motions** · 1,159 rows · **184
named** / **321 tally-only** · **28 contested** · **0** roster-ceiling breaches (>5) ·
**0** outcome-vs-count inconsistencies · 10 distinct voters. The 3 promoted 2020/2024
docs added 22 motions incl. **4 contested Sondak-era/2024 votes** (2020-05-06 R-10
resort-tax increase FAILED 1-2 with Morgan+Sondak abstaining; 2020-06-17 R-11 UFSA
boundary 3-1 Davis dissenting + M. Bourke abstaining; 2020-06-17 R-15 final budget 3-1
M. Bourke dissenting; plus a Bourke abstention on the 2020-05-06 tentative budget).
Two 2026-07-16 extractor fixes (both zero-regression on the audited corpus, proven by
byte-identical re-extract): narrative name-lists now allow role prefixes per element
("Mayor Sondak and Council Members Elise Morgan and Cliff Curry voted “Aye”" no longer
drops the leading Mayor), and "advice and consent of the council" / "written consent
of the other party" boilerplate no longer counts as a vote event (the superseded
2020-06-17 R-12 original motion is honestly `RECORDED (no vote line)`). A 2026-07-19
fix (audit 2026-07-12 WARN) made `MEMBER_TOKEN_RE` tolerate a stray OCR/table glyph
(`. | !`) between the dash and a LINE-WRAPPED vote token — the clerk's roll wraps a
member mid-token (`Councilmember Byrne — .\nyes`, `Mayor Bourke — |\nyes`, `Morgan
— !\nyes`), which silently DROPPED that member and understated the derived N-0 tally.
Recovered **9 named Aye rows** on **9 unanimous motions** (each N-0 → (N+1)-0, all
source-verified; no outcome flip, no fabrication): 2023-12-13 m3 (R. Bourke), 2024-01-10
m7 (Byrne), 2024-04-10 m3 (Byrne) + m4 (Morgan), 2024-06-20 m13 (Morgan), 2024-11-13 m3
(Byrne), 2025-01-08 m1 (Byrne → true 5-0), 2025-03-12 m3 (Schilling) + m5 (R. Bourke).
Fail/RECORDED classes byte-identical across the re-extract. 24 motions are `RECORDED (no vote line)` — deferred/restated
parliamentary main-motions whose vote is cast later via a "called the question"/restated
sequence; their db `outcome` is **NULL (honestly unknown)**, never a default Pass. The
2021 narrative grammar (quoted "voted “Aye.”" lists, "A vote … was taken" events, CAPS
"CALLED the Question on …" motions, the 2021-07-14 Ayes/Nays column grid) is parsed; 13
true motion failures are recorded (the pre-fix data fabricated APPROVED on 6 of them).
6 meetings (retreats / strategic-planning / agenda-only work sessions) record **no
formal motions** — honest, verified against source.
