# HANDOFF — resume point (2026-09-01: SLCo WAVE W2 CLOSED — THE COUNTY ITEMIZATION PROGRAMME IS COMPLETE)

> **Read in order: root `CLAUDE.md` → this file → `TODO.md` → `GOTCHAS.md`. Options menu:
> `LEADS.md`. Publish criteria: `SHIP_GATE.md`. One session banner, overwritten per handoff
> (prior banner: TODO_ARCHIVE.md anchor 2026-08-24-CACHE-WASHINGTON-BANNER).**

## What landed 2026-09-01 — SLCo's EasyVote residue, and the repo's first external transcription

The last un-itemized corpus in the county programme is closed. **Every campaign-finance
document any of the 8 counties holds is now itemized.** What remains anywhere in the county
tier is ACQUISITION — SLCo's 251 GRAMA-only online-filed 2015–2021 reports — not transcription.

Wave W2 was **transcribed 2026-08-24 by an EXTERNAL agent (Kimi K3)** under
`salt_lake_county/campaign_finance/W2_HANDOFF.md`, which deliberately stopped at the handoff's
"minimum bar" (module gates green, no federation, no docs). **This session ran the
deterministic tail: verify → federate → reconcile the docs.** Nothing was committed.

| | |
|---|---:|
| derived queue (EasyVote filings with no advanced-search API rows) | **240** |
| transcribed / out of scope (school board) / remaining | **238 / 2 / 0** |
| rows published | **18,240** (11,852 C + 6,388 E) |
| `pct:` geometry | **100%** |
| new covers read (`cf_filing` 971 → **1,112**) | **141** |
| sides: exact / delta-with-cause / `none` / unknown / out-of-scope / **withheld** | 359 / 33 / 82 / 2 / 4 / **0** |
| amounts blank | **78, all redacted or absent AT SOURCE** (77 = the Wilson bar over the Amount column) |

`cf_contribution` for the county **24,352 → 36,204**; `cf_expenditure` **14,488 → 20,876**.

## Trust was verified, not assumed — this is the part that mattered

W2 is the **first non-Claude transcription federated into `gov.db`**, so the wave was checked
before anything reached the db, not after:

* **Gates re-run independently** — `validate_finance.py` **PASS** (7 by-design warns),
  `screen_records.py` **240 records, 0 fails, queue filings missing a record: 0**,
  `checkpoint.py` **OK (append-only held)**, `vision_coverage.py` **remaining 0** in all three
  cycles. Full CF sweep: **38 modules PASS + the 2 known non-regressions**; 93 family tests and
  the 31-case county-reducer suite green.
* **Deterministic rebuild** — `build_finance.py` reproduced all four CSVs **byte-for-byte**.
* **Frozen blocks proved field-for-field** against `_backups/2026-08-24-slco-w2/pre-mod/`:
  `contributions.csv` rows 1–24,352 and `expenditures.csv` rows 1–14,488 **identical**; in
  `filing_totals.csv` rows 1–971 **exactly 97 rows changed and all 97 are the 2022 residue
  cohort gaining an itemized half — ZERO `stated_*` values moved**.
* **Four filings re-read at the page**, chosen across the ledger tiers — `Conder-Phil__12F26E7B`
  (exact county grid), `Bradshaw-Arlyn__927411EB` (2026 cover-only), `Wilson-Jennifer__B5D1F91C`
  (the redaction case), `Gettel-Dustin__E61DBCB5` (a +$120.00 delta). **Every published row
  matched the document**, including two column-clipped donor strings correctly kept as visible
  glyphs at `needs_review=1` rather than completed, and the delta traced to exactly the one
  in-kind row the filer left out of his own Summary line 1.
* **The out-of-scope ruling re-proved at the cover** — `FIFE-JEPPERSON__AE07FEF8` prints
  Office Sought = "Salt Lake School Board" (correctly excluded), while her 2026 `B5AB014E`
  prints Office = school board but **Office Sought = "Salt Lake County Council District 2"**
  and is correctly INCLUDED. ⚠ **Classify by Office Sought, never by the top-row Office.**

## Federation + reducer

`build_cities_db.py` — auto-gate **44/44**, integrity ok, FK **0**, caveat **108**. The build
also correctly REMOVED 2 school-board `cf_filing` rows the live db had been carrying.

`cycle_totals_county.py` regenerated (gates **G1/G5/G6 PASS**, all 8 counties). Every change
explained: **37 salt_lake candidate-cycles moved GAP → PUBLISH** on the strength of the new
covers; **0 moved back, 0 published figure changed value**; 39 stayed GAP with a *more specific*
`gap_reason`; 17 changed only their advisory itemized cross-check; 1 row removed (the
out-of-scope ruling). **The other seven counties changed by zero rows.** Repo totals
1,009 → **1,008** cycles, 620 → **657** publishing, 389 → **351** gaps, 201 → **222** floors.

`check_doc_numbers.py` **all checks PASS** after 6 headline numbers were corrected in
README.md / CLAUDE.md / gov_db_SCHEMA.md in the same session.

## Two module-wide reading rules this wave CHANGED — carry them

1. **`donor_occupation` is no longer paper-slice-only.** The EasyVote grid and most filer
   attachments print Occupation/Employer too, so **10,225 W2 rows populate it** (repo total
   **12,517**). The claim "the 2015–2021 paper slice is the only source" was true until
   2026-09-01 and is now corrected in root CLAUDE.md, the module CLAUDE.md and AVAILABILITY.md.
2. **Some SLCo expenditure amounts are NEGATIVE as printed** — Morris's five bank/ledger
   exports and Liewer `585D94D0`; the sign is verbatim, reconciliation is on MAGNITUDE, and
   `itemized_expend_sum` publishes positive. **Take `abs()` before summing
   `cf_expenditure.amount` for this county** (892 negative rows module-wide, including
   pre-existing clerk-legacy McAdams/Winder rows).

Also corrected in passing: `vision_coverage.py`'s legacy TOTAL row was double-counting the new
W2 caches and printing `remaining -141`; the total now sums only the three stated-totals eras.

**NOT COMMITTED** — this sits in the working tree with the prior utah, washington-parser, SLCo
W1 and cache+washington waves.

## Next

* **[DEBT] +1, filed this session:** 9 malformed `geometry` pointers in the SLCo CF CSVs (one
  negative height, eight off-page). Provenance pointers only — **no money value is wrong** —
  but they should be re-measured or withdrawn, and `validate_finance.py` should gate box
  validity. **[DEBT] open: 4.**
* **W3 — the only county CF work left is a RECORDS REQUEST, not a wave**: the owner sends the
  GRAMA draft at
  `salt_lake_county/campaign_finance/_recon/2026-08-20-portal-probe/GRAMA_EMAIL_2026-08-20.txt`
  for the 251 online-filed 2015–2021 reports. 34 of the 54 portal filers have no clerk-page PDF
  at all, so this is complementary to everything already transcribed.
* **Calibration specimens still unpromoted**: ~20 candidates from the cache+washington wave, 5
  from SLCo W1, and now the W2 candidates recorded in
  `_backups/2026-08-24-slco-w2/RESUME_2026-08-24_claude.md` §5 — the Wilson Amount-column
  redaction, the occupation cell clipped on both sides by a bar and a rule, and the
  spreadsheet row physically shorter than its own text (900 dpi recovers nothing).
* **LEADS filed 2026-09-01**: the `cycle_totals_county.py --help` footgun (a bare run
  regenerates all 8 counties), the Wilson redaction floor, the side-by-side attachment shape
  that hides 51 expenditure rows on the right half of a page, the `work/chunkNN` vs
  `work/chunk_NN` scratch-dir fork, and the Office-Sought-flips-scope finding.

Working set + close-out evidence: `_backups/2026-08-24-slco-w2/` (queue, 76 chunks, 240
records, FINDINGS.md, the wave's own CLOSEOUT.md) and `_backups/2026-09-01-w2-closeout/`
(this session's verification record, hashes, and page renders).
