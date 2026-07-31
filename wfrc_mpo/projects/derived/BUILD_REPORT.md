# wfrc_mpo / projects / derived — BUILD REPORT

Derived TIP project-lifecycle layer from `raw/TIP*.json` (8 vintages, 14 layers).
Run `python3 build_project_history.py` to regenerate. DERIVED — never hand-edit.

## Result: **ALL GATES PASSED**

| gate | check | status |
|---|---|---|
| 1 | reconciliation (nothing lost vs projects.csv) | PASS |
| 2 | (pin,vintage) uniqueness after identical-collapse | PASS |
| 4 | idempotency (derive twice, byte-identical) | PASS |

## Gate 1 — reconciliation vs projects.csv

Full accounting per vintage: **kept (project_vintage rows) + collapsed-duplicates + excluded(null/empty/0 pin) == raw rows == projects.csv TIP rows**. When that closes, nothing is lost. The `literal_delta` column is the requested `csv_numeric_id - (kept + excluded)` figure; it is non-zero by construction wherever (a) identical-attribute duplicate pins were collapsed here but sit as separate numeric rows in projects.csv, or (b) null pins land as OID fallback (non-numeric) in projects.csv while pin=0 rows land as numeric "0" — both explained, neither a data loss.

| vintage | kept | collapsed_dups | conflict_quar | ovr_merged | excl(0) | excl(null) | raw_rows | csv_rows | csv_numeric | csv_oid | full_ok | literal_delta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-2025 | 965 | 0 | 0 | 0 | 30 | 0 | 995 | 995 | 995 | 0 | yes | +0 |
| 2021-2026 | 254 | 108 | 0 | 0 | 0 | 0 | 362 | 362 | 362 | 0 | yes | +108 |
| 2022-2027 | 261 | 0 | 0 | 0 | 0 | 0 | 261 | 261 | 261 | 0 | yes | +0 |
| 2023-2028 | 298 | 0 | 0 | 0 | 0 | 0 | 298 | 298 | 298 | 0 | yes | +0 |
| 2024-2029 | 307 | 0 | 0 | 0 | 0 | 35 | 342 | 342 | 307 | 35 | yes | -35 |
| 2025-2030 | 327 | 0 | 0 | 0 | 0 | 60 | 387 | 387 | 327 | 60 | yes | -60 |
| 2026-2031 | 339 | 0 | 0 | 0 | 0 | 1 | 340 | 340 | 339 | 1 | yes | -1 |
| 2027-2032 | 702 | 0 | 0 | 1 | 0 | 11 | 714 | 714 | 703 | 11 | yes | -10 |

Reconciliation reason notes (do-not-force policy — deltas explained, not massaged):
- **2020-2025**: 30 rows carry `PIN=0`; excluded here (rule: drop null/empty/0), but projects.csv stored them as numeric project_id `"0"` — they sit in `csv_numeric` AND in excl(0), so the literal_delta nets to 0 for this vintage.
- **2021-2026 / 2027-2032**: identical-attribute duplicate pins (108 / 2 rows) collapse to one row here; projects.csv keeps every raw feature as its own numeric row — hence literal_delta reflects them.
- **2024-2029 / 2025-2030 / 2026-2031 / 2027-2032**: null pins → OID fallback (non-numeric) in projects.csv; counted here under excl(null); they are NOT in csv_numeric, so literal_delta goes negative.
- **conflict_quar** = raw feature rows held out of a (pin,vintage) group that has CONFLICTING attributes (see Gate 2). They are accounted here (never silently dropped) but excluded from `project_vintage.csv` pending the upstream semantic decision; `full_ok` includes them so the accounting still closes exactly.
- Every vintage's `full_ok=yes` proves the full accounting closes exactly — no raw row is dropped.

## Gate 2 — (pin,vintage) uniqueness (hard-fail on UNADJUDICATED conflicts)

Adjudicated via `vintage_overrides.csv` (documented decisions, 2026-07-22):
- 2027-2032 pin=19561 : `merge_dup` (see the override row's reason)
- 2027-2032 pin=21213 : `keep_both` (see the override row's reason)

Zero UNADJUDICATED conflicting attribute tuples within any (pin,vintage). PASS.

## Gate 3 — pin coverage

- raw TIP feature rows (all layers): **3699**
- excluded (null/empty/0 pin): **137**
- project_vintage rows (distinct pins after collapse): **3453**
- % of raw rows carrying a usable pin: **96.30%**

Excluded pins per vintage (zero / null-empty):

| vintage | pin=0 | null/empty |
|---|---|---|
| 2020-2025 | 30 | 0 |
| 2021-2026 | 0 | 0 |
| 2022-2027 | 0 | 0 |
| 2023-2028 | 0 | 0 |
| 2024-2029 | 0 | 35 |
| 2025-2030 | 0 | 60 |
| 2026-2031 | 0 | 1 |
| 2027-2032 | 0 | 11 |

## Gate 4 — idempotency

Derivation run twice in-process; both CSV renderings byte-identical: **PASS**.
Outputs overwrite on every run (safe to re-run).

## Gate 5 — sanity counts (project_history)

- pins total: **1884**
- present in newest vintage (2027-2032): **701**
- exited (non-blank exited_tip): **574**
- left-censored (first_vintage == 2020-2025): **965**
- slip_years != 0: **118**
- RTP exact-name matches: **5**

