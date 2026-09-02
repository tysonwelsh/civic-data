# COUNTY CYCLE REDUCER — build specification

**Status:** DESIGN COMPLETE, ready to execute. Written 2026-08-23 (design stage, owner-approved).
**Audience:** the implementation agent. This document is self-contained; you need no memory of
the design session. Every number in it was measured read-only against `gov.db` on 2026-08-23
and is reproducible with the prototypes in `_backups/2026-08-23-cycle-reducer-design/`.

**What you are building:** a sanctioned, evidence-honest **per-candidate per-election-year**
campaign-finance total for all 8 counties, so that "who raised the most for county mayor" is one
query — without repeating the failure modes that caused the 2026-08-02 deferral.

**Cardinal rule 1 governs everything here.** A total that cannot be established from the filings'
own printed arithmetic is a **gap row**, never an estimate. Honest gaps are the deliverable too.

---

## 0. READ THIS FIRST — a live landmine you must disarm in step 1

`scripts/campaign_finance/cycle_totals.py` (the CITY reducer) resolves its target list through
`all_cities()`, which returns **every registry entity that has a `campaign_finance/filing_totals.csv`
— including all 8 counties**. `scripts/build_search_layer.py::load_cf` then federates
`campaign_finance/cycle_totals.csv` from **every** entity into `cf_cycle`. Nothing today stops a
county file from landing in the city-only table.

Running `python3 scripts/campaign_finance/cycle_totals.py --all` right now would (verified
2026-08-23, read-only, by calling `cycle_totals(slug)` without `write_city`):

| county | what the CITY reducer produces | why it is wrong |
|---|---|---|
| weber, utah, wasatch | **0 rows, silently** | the REGIME FILTER drops every filing whose `filing_regime` is non-empty and `!= 'election_cycle'`; these counties store `per-period` / `cumulative` / `period` there |
| summit | **74 rows, `basis='sum-interim'`** | summit's corpus is documented CUMULATIVE — this SUMS cumulative snapshots. `David R. Brickey 2014` → **32,400.00** where the truth is **16,800.00** (a 93% overstatement: his two filings state 15,600.00 and 16,800.00 cumulative, and 16,800 − 15,540.12 = 1,259.88 = the printed ending balance) |
| cache, juab, washington, salt_lake | rows, unaudited basis | same class of error |

### 0.1 The `filing_regime` vocabulary collision (root cause)

`filing_regime` carries **two incompatible vocabularies** at the county tier:

| meaning | vocabulary | who uses it |
|---|---|---|
| **statutory stream** (which legal filing obligation) — the CITY meaning | `election_cycle`, `annual` | cities (taylorsville), `juab_county` (27 `election_cycle`), `washington_county` (178 `election_cycle` / 28 `annual`) |
| **arithmetic basis** (period vs cycle-to-date) — a COUNTY-only meaning | `per-period`, `cumulative`, `period` | `utah_county` (265 `per-period`), `weber_county` (98 `cumulative`), `wasatch_county` (62 `cumulative` / 49 `period`) |
| unset | `''` | `cache_county`, `summit_county`, `salt_lake_county` (regime lives in module docs) |

**Do not read `filing_regime` as the arithmetic basis.** This reducer derives the basis from each
candidate-cycle's own printed arithmetic (§3). `filing_regime` is used for exactly one thing —
the non-cycle stream filter (§3.1) — via an explicit allow-list, never the city's
`!= 'election_cycle'` rule.

**Step 1 of implementation (do this before anything else):** add a hard guard to
`cycle_totals.py::all_cities()` restricting it to `e.level == 'city'`, and a guard in
`write_city()` that refuses a non-city slug. Note it in the module docstring citing this file.
File a LEADS.md line proposing that `filing_regime` be split into `statutory_stream` +
`stated_basis` so the collision cannot recur.

---

## 1. Evidence base — the eight county regimes

Read each county's `campaign_finance/AVAILABILITY.md` + `CLAUDE.md` and its `cf-*` `caveat` row
before touching its numbers. Condensed here (all quotes are from the `caveat` table in `gov.db`):

| county | filings | documented regime | BB populated | notes |
|---|---:|---|---:|---|
| `salt_lake_county` | 841 | **per-period** (3 eras: clerk-legacy 2006–2015, unacquired 2015–2021, EasyVote 2022–2026) | 609/841 | "at least two filers (DeBry 2022, Gill 2007) put CUMULATIVE figures in the per-period column"; 143 EasyVote filings have no `cf_filing` row at all |
| `utah_county` | 265 | **per-period**, INVERTED vs summit/weber | 250/265 | "an AMENDMENT RESTATES ITS ORIGINAL'S PERIOD rather than adding one"; `notes` carry `ytd_contrib=` / `ytd_expend=` — a free cross-check anchor (§5.4) |
| `weber_county` | 98 | **cumulative** — "cycle figure = latest non-superseded report, never a sum"; "officeholder carryover inflates cumulative totals — Harvey 2024 opens from his 2020 closing" | 69/98 | every row's `notes` carry the literal marker `REGIME: this form is CUMULATIVE …` |
| `summit_county` | 131 | **cumulative** — "Reports are CUMULATIVE snapshots — never sum a candidate's filings"; Current\|Last\|Cumulative column order REVERSED vs the parsed cities | **0/131** | no beginning balance anywhere → no chain is constructible |
| `wasatch_county` | 111 | **MIXED, per CANDIDATE** — "the two older sheets are CUMULATIVE …, the 2024+ sheet is period-scoped — but three filers restate cumulatively on it anyway (flagged in notes; regime is per CANDIDATE, not per form)" | **0/111** | clean 2022→2024 form seam |
| `washington_county` | 206 | **MIXED** — "THE COUNTY'S TEMPLATE IS PER-PERIOD, BUT A MINORITY OF FILERS FILL IT CUMULATIVELY" (Kevin Brooks 2010, Chris White 2012 close only on the cumulative reading) | 112/206 | 28 `annual` officeholder filings with **blank `election_year`** — a non-cycle stream |
| `cache_county` | 239 | **MIXED** — "`is_incremental` varies PER FILING (`filing_regime` is NULL in db — regime lives in the module docs)" | 83/239 | 42 cross-channel byte-duplicate rows — group on sha256 before counting filings |
| `juab_county` | 27 | **cumulative** — "Never sum filing_totals across a candidate's filings; these forms are cumulative" | **0/27** | 2010/2014/2020 only |

### 1.1 The itemized substrate (what a cross-check can reach)

Itemized rows exist and are **COMPLETE** for `utah` (245/245 scanned + 2 born-digital),
`weber` (98/98), `summit` (131/131), `wasatch` (111/111), `juab` (27/27), and `salt_lake`'s
**clerk-legacy era only** (496/496). They are **partial** for `washington` (machine-readable era
closed 2026-08-23; 100 handwritten filings outstanding), `cache` (born-digital slice only), and
`salt_lake`'s EasyVote era (197 of 442; 245 filings carry no rows and that is a **gap**, not zero).

Row counts in `gov.db` at design time: `cf_contribution` — slco 20,930 · utah 2,956 · washington
1,518 · weber 1,360 · summit 1,298 · wasatch 346 · juab 46 · cache 32. `cf_expenditure` — slco
11,882 · utah 3,710 · summit 1,793 · washington 1,738 · weber 1,256 · wasatch 505 · juab 141 ·
cache 111.

**Empty itemized anywhere in the county tier means NOT TRANSCRIBED, never "no donors."**

---

## 2. SCHEMA DECISION — a new table, `cf_cycle_county`

### Recommendation: **NEW TABLE. Do not put county rows in `cf_cycle`.** Confidence: high.

Rationale:

1. **The two quantities are not the same measurement.** A city `cf_cycle.raised` is
   `max(latest summary, summed interims)` of stated totals with no carryover concept and no
   provenance of which filings governed. A county row must carry regime, carryover, chain proof,
   governing-filing provenance, floor flags and gap reasons. Unioning them would let a consumer
   rank a city figure against a county figure that was built on a different basis — precisely the
   error the 2026-08-02 deferral was protecting against.
2. **`cf_cycle`'s 11 columns cannot carry the required evidence** (§2.2). Widening it stamps
   ~10 permanent NULL columns onto all 805 existing city rows and changes a table that
   `SCHEMA.md` §6, `gov_db_SCHEMA.md`, root `CLAUDE.md` and `build_search_layer.py`'s docstring
   all describe with fixed semantics.
3. **Repo precedent — "incorporate entities on their own terms."** The MPO tier got
   `regional_project` rather than being forced into the city vote-shape; the state tier's
   mis-fit into `application` is a standing TODO precisely because it was NOT given its own
   table. This is the same call.
4. **The naive-UNION risk is answered by a view, not by a shared table** (§2.3), so the
   cross-tier question stays one query while the warning rides every row.

### 2.1 On-disk artifact

Each county emits `<county>/campaign_finance/**cycle_totals_county.csv**`.

> ⚠ **The filename matters.** `build_search_layer.py::load_cf` unconditionally reads
> `campaign_finance/cycle_totals.csv` for **every** entity into `cf_cycle`. Naming the county
> artifact `cycle_totals.csv` would silently federate it into the city-only table. Use
> `cycle_totals_county.csv` and add a **new** loader block for it.

### 2.2 Column contract

`cycle_totals_county.csv` header (exact order; the federated table prepends nothing — `city`
is column 1 on disk as in the city file, and the loader overrides it with `e.slug`):

| # | column | type | meaning |
|---:|---|---|---|
| 1 | `city` | text | entity slug (`weber_county`). Kept for symmetry with the city file; the loader authoritatively uses the registry slug. |
| 2 | `candidate` | text | **VERBATIM** as it appears in `cf_filing.candidate`. Never folded, never re-ordered. (SLCo prints `Sim Gill` in the legacy era and `Gill, Sim` in EasyVote — those are two rows, in two non-overlapping cycles. Person-folding is `cf_candidate_person`'s job, not this layer's.) |
| 3 | `election_year` | text | verbatim |
| 4 | `office` | text | from the governing filing's `cf_filing.office` (present for every county) |
| 5 | `seat` | text | from `index.csv` **only where that county's index has a `seat`/`council_seat` column** (summit, wasatch, salt_lake, cache). Blank elsewhere — utah/weber/washington/juab index schemas have no seat column. Blank means "the county does not publish it," not unknown-by-omission. |
| 6 | `regime` | enum | `per-period` \| `cumulative` \| `per-period-single` \| `cumulative-single` \| `mixed` \| `undetermined` |
| 7 | `regime_basis` | enum | how #6 was decided: `chain-closure` \| `filing-arithmetic` \| `county-prior` \| `single-filing` \| `none` |
| 8 | `raised_gross` | decimal / **blank** | the cycle's contributions total **in the regime's own terms** (§4). Blank on a gap row. |
| 9 | `spent_gross` | decimal / blank | same for expenditures |
| 10 | `carryover_opening` | decimal / blank | the printed **beginning balance of the first governing filing**. **Reported as its own column and NEVER silently folded into #8.** |
| 11 | `carryover_basis` | enum | `chain-first-bb` \| `governing-report-bb` \| `` (blank = the form prints no opening balance — summit / wasatch / juab) |
| 12 | `raised_net_of_carryover` | decimal / blank | see §4.3 and **⚠ BLOCKING B1** |
| 13 | `ending_balance` | decimal / blank | printed ending balance of the last governing filing |
| 14 | `chain_closes` | `True`/`False`/blank | the **CHAIN-CLOSURE PROOF**: `BB_first + ΣC − ΣE == EB_last` within $0.51 (§3.4). Blank = untestable (a required figure is not printed). |
| 15 | `n_filings` | int | filings in the candidate-cycle group, pre-filter |
| 16 | `n_live` | int | after the supersede pre-filter |
| 17 | `n_governing` | int | filings that actually produced #8/#9 |
| 18 | `chain_len` | int | length of the maximal balance chain (0 where no chain is constructible) |
| 19 | `is_floor` | `1`/`` | **1 = the published figure is a LOWER BOUND, not a total** (§4.4) |
| 20 | `in_kind_basis` | enum | `unknown` (default) \| `included` \| `excluded` — settled per filing from its own arithmetic where `build_finance.py` recorded it; **never from form family or county** (owner-ratified 2026-08-17 per-filer in-kind finding) |
| 21 | `confidence` | enum | `A` \| `A-superseded` \| `B` \| `C` \| `` (blank on gap rows) — §5 |
| 22 | `governing_filings` | text | `;`-joined `source_filing` values of the filings that produced #8/#9, in chain order. **This is the reproducibility contract** — gate G1 re-derives the figure from these and nothing else. |
| 23 | `excluded_filings` | text | `;`-joined `source_filing=reason` for every filing dropped (`superseded-note`, `orphan-not-chained`, `duplicate-restatement`, `non-cycle-stream`) |
| 24 | `gap_reason` | text | populated **only** where #8 is blank; one of the §5.5 codes plus a human clause. Blank on published rows. |
| 25 | `itemized_check_raised` | decimal / blank | ADVISORY cross-check (§5.4). Never gates. |
| 26 | `itemized_check_spent` | decimal / blank | ADVISORY |
| 27 | `itemized_check_note` | text | e.g. `agrees`, `differs +1,000.00 (filer arithmetic, see filing notes)`, `not-comparable: mixed is_incremental within cycle`, `no itemized layer` |
| 28 | `review_flag` | text | free text; a human follow-up marker, never a substitute for `gap_reason` |

**Gap rows are ROWS.** A candidate-cycle whose total cannot be established still emits a row, with
`raised_gross`/`spent_gross` blank and `gap_reason` set. The gap is the data (cardinal rule 1). At
design-time measurement that is **268 of 900** candidate-cycles.

### 2.3 Federation

In `scripts/build_search_layer.py`:

```sql
CREATE TABLE cf_cycle_county (
    city TEXT NOT NULL, candidate TEXT, election_year TEXT, office TEXT, seat TEXT,
    regime TEXT, regime_basis TEXT,
    raised_gross REAL, spent_gross REAL,
    carryover_opening REAL, carryover_basis TEXT, raised_net_of_carryover REAL,
    ending_balance REAL, chain_closes TEXT,
    n_filings INTEGER, n_live INTEGER, n_governing INTEGER, chain_len INTEGER,
    is_floor TEXT, in_kind_basis TEXT, confidence TEXT,
    governing_filings TEXT, excluded_filings TEXT, gap_reason TEXT,
    itemized_check_raised REAL, itemized_check_spent REAL, itemized_check_note TEXT,
    review_flag TEXT
);
CREATE INDEX idx_cfcc_cand ON cf_cycle_county(city, candidate, election_year);
```

Load it in `load_cf()` from `cycle_totals_county.csv`, iterating **only** entities with
`e.level != 'city'` — a county file must never reach the `cf_cycle` insert and a city file must
never reach this one. Add both counts to the function's `counts` dict and the build banner.

And the deliberate cross-tier door:

```sql
CREATE VIEW v_cf_cycle_all AS
  SELECT c.city, e.level AS gov_level, c.candidate, c.election_year, c.office, c.seat,
         c.raised AS raised, c.spent AS spent,
         NULL AS carryover_opening, c.basis AS basis, NULL AS regime,
         NULL AS confidence, '' AS is_floor, c.review_flag,
         (SELECT caveat FROM caveat WHERE city='*' AND code='cf-coverage') AS coverage_caveat
    FROM cf_cycle c JOIN entity e ON e.slug = c.city
  UNION ALL
  SELECT q.city, e.level, q.candidate, q.election_year, q.office, q.seat,
         q.raised_gross, q.spent_gross,
         q.carryover_opening, q.regime_basis, q.regime,
         q.confidence, COALESCE(q.is_floor,''), q.review_flag,
         (SELECT caveat FROM caveat WHERE city='*' AND code='cf-cycle-tiers')
    FROM cf_cycle_county q JOIN entity e ON e.slug = q.city
   WHERE q.raised_gross IS NOT NULL;
```

Gap rows are deliberately excluded from the view (a gap is not a total) but remain in the base
table, which is where a coverage question is asked. (`entity`'s primary key is `slug`, verified
2026-08-23; `cf_cycle.city` / `cf_cycle_county.city` hold entity slugs.)

---

## 3. DERIVATION BASIS AND THE DECISION PROCEDURE

### Recommendation: **stated totals from `cf_filing` are PRIMARY. The balance chain is the
resolver. Itemized sums are an ADVISORY cross-check that never gates.** Confidence: high.

Why stated totals: they are complete for all 8 counties back to 2006 (2,918 `cf_filing` rows),
they are the filer's own printed figures (cardinal rule 2 — city-faithful values), and they are
the only substrate that spans every county. Itemized sums cannot be primary — the itemized layer
is absent for `cache` pre-2022, for `washington`'s handwritten era, and for 245 of `salt_lake`'s
442 EasyVote filings; and where present it is deliberately period-scoped or cycle-restating in a
way that makes a naive cycle sum wrong (washington: 1,518 rows = 676 distinct donations).

### 3.1 Step 1 — scope filter (non-cycle statutory streams)

Drop a filing when **either**:
* `filing_regime` (lowercased, trimmed) ∈ `{'annual'}` — washington's 28 mandatory officeholder
  annual reports; **or**
* `election_year` is blank.

Do **not** use the city rule (`regime != 'election_cycle'`): it would drop all of utah, weber and
wasatch (§0.1). Record the counts. Measured at design time: washington 28 `annual` + 2 blank-year,
salt_lake 8 blank-year. Every dropped filing appears in some cycle's `excluded_filings` where a
cycle exists, and in the run report otherwise.

### 3.2 Step 2 — supersede pre-filter (conservative, marker-driven)

Drop a filing when its `cf_filing.notes` carries an explicit supersede marker:
* a `;`-separated note **entry that begins with** `superseded` (the existing structural convention
  — reuse `cycle_totals.py::is_superseded` verbatim, do not re-invent the substring test that
  once dropped a bluffdale filing for merely mentioning the word); **or**
* the literal substrings `SUPERSEDED by` / `is SUPERSEDED` (weber's wave-B2 wording, e.g. Froerer
  2022-06-21: *"this June amended report is SUPERSEDED by the 2022-11-01 report"*).

If the filter empties the group, keep the original set (a group cannot be all-superseded).

**This filter is deliberately incomplete, and that is fine** — SLCo's overlapping April-5 trio
carries no supersede marker at all. Step 4's chain resolves those. Marker hits at design time:
weber 105, utah 8, salt_lake 5, cache 3 (most weber hits are the `REGIME:` sentence, which the
`startswith` test correctly ignores).

### 3.3 Step 3 — per-filing arithmetic signature

Parse `stated_beginning_balance` (BB), `stated_total_contributions` (C),
`stated_total_expenditures` (E), `stated_ending_balance` (EB) with a money parser that returns
`None` for `''`, `-`, `N/A`, `None` and any unparseable token. **A blank is never `0`**
(washington's standing rule).

For each filing compute two booleans at $0.51 tolerance (chosen so the corpus's documented
whole-dollar and rounding variance does not manufacture failures; every documented filer-arithmetic
delta in these corpora is ≥ $1):

```
period_sig = BB is not None and C,E,EB not None and |BB + C − E − EB| ≤ 0.51
cumul_sig  =                    C,E,EB not None and |C − E − EB|      ≤ 0.51
```

**This is the discriminator, and it matches every county's documented regime** (measured
2026-08-23 over 1,718 filings with parseable C/E/EB):

| county | period-only | cumulative-only | both | neither | documented regime | agrees? |
|---|---:|---:|---:|---:|---|---|
| salt_lake | 415 | 10 | 147 | 28 | per-period | ✓ |
| utah | 87 | 7 | 137 | 13 | per-period | ✓ |
| weber | 1 | 61 | 17 | 9 | cumulative | ✓ |
| summit | 0 | 98 | 0 | 29 | cumulative | ✓ |
| wasatch | 0 | 82 | 0 | 19 | cumulative (older) | ✓ |
| juab | 0 | 11 | 0 | 7 | cumulative | ✓ |
| washington | 53 | 70 | 21 | 28 | **mixed** | ✓ (mixed) |
| cache | 16 | 64 | 51 | 58 | **mixed** | ✓ (mixed) |

`both` is the **first-report case**: when BB = 0 the two signatures are algebraically identical.
That is exactly `utah_county`'s documented `cumulative-exact` first-report state — *"this is the
cycle's first report for this filer, so period IS year-to-date."* It is not ambiguity to be
resolved at the filing level; it resolves at the cycle level in step 4.

`neither` means the filer's own arithmetic does not close, or a needed figure is blank. It is
never repaired.

### 3.4 Step 4 — the BALANCE CHAIN and the CHAIN-CLOSURE PROOF

Order the live filings by `(filing_date, source_filing)`. Build the **longest chain** by linking
filing *n* to filing *n+1* when `|BB(n+1) − EB(n)| ≤ 0.51`. Try every start; prefer the
later-dated candidate on ties; each filing is used at most once. (Reference implementation:
`_backups/2026-08-23-cycle-reducer-design/proto2.py::longest_chain`. It is O(n²) over group sizes
that never exceed ~15 — no optimization is warranted.)

Then compute the proof:

```
chain_closes  ⇔  | BB(first) + Σ C(chain) − Σ E(chain) − EB(last) | ≤ 0.51
```

**This is the reducer's spine.** It simultaneously (a) resolves amendments and supersessions with
no marker required, (b) confirms the per-period regime, and (c) surfaces the carryover as
`BB(first)` — all from figures the documents themselves print, differencing nothing across covers.

**Worked specimen — the SLCo amendment trio, resolved.** `Rivera, Rosie`, Sheriff, 2022, nine
filings, five of them labelled reporting period `April 5` with mutually inconsistent totals
(the deferral's `$68,605 / $38,236 / $31,019` case):

| filed | period | BB | C | E | EB |
|---|---|---:|---:|---:|---:|
| 2022-04-25 | April 5 | 0.00 | 38,236.42 | 8,787.48 | 29,448.94 |
| 2022-06-20 | April 5 | 0.00 | **68,605.79** | 29,202.92 | 39,402.87 |
| 2022-06-28 | April 5 | 0.00 | 38,236.42 | 8,752.10 | 29,484.32 |
| 2022-09-14 | September 15 | 0.00 | 88,170.87 | 16,928.16 | 71,242.71 |
| **2022-09-24** | April 5 | **1,341.42** | 38,236.42 | 8,752.10 | **30,825.74** |
| **2022-09-24** | April 5 | **30,825.74** | 31,019.37 | 21,011.74 | **40,833.37** |
| **2022-09-24** | September 15 | **40,833.37** | 48,768.00 | 16,928.16 | **72,673.21** |
| **2022-10-31** | 7 days before general | **72,673.21** | 22,607.00 | 55,143.11 | **40,137.10** |
| **2023-01-30** | year-end | **40,137.10** | 1,710.00 | 13,910.37 | **27,936.73** |

The bolded five chain end-to-end. The other four are earlier versions that all open from `0.00`
and link to nothing. Result: `raised_gross = 142,340.79`, `spent_gross = 115,745.48`,
`carryover_opening = 1,341.42`, `ending_balance = 27,936.73`, and the proof closes exactly:
`1,341.42 + 142,340.79 − 115,745.48 = 27,936.73`. **No marker, no heuristic, no guess.**

**When the chain BREAKS** (the weber swapped-cover class — two internally consistent covers filed
under each other's key, *"detectable ONLY by chaining Last-Report to Cumulative"*): `chain_len`
falls below `n_live`, the proof fails or is untestable, and the cycle drops out of tier A. It does
**not** silently fall back to a sum. It classifies per §4/§5 and, where nothing settles it, emits a
gap row with `gap_reason='chain-broken'` naming the unlinked filings in `excluded_filings`. A
broken chain is a finding to report, not an obstacle to route around.

### 3.5 Step 5 — regime classification

Per candidate-cycle, in order (first match wins). `nper` / `ncum` = counts of period-only /
cumulative-only filings among the live set.

| # | condition | `regime` | `regime_basis` |
|---:|---|---|---|
| 1 | `n_live == 1` and (county prior is cumulative **or** the filing is cumulative-only) | `cumulative-single` | `single-filing` |
| 2 | `n_live == 1` and the filing is period-only | `per-period-single` | `single-filing` |
| 3 | `n_live == 1`, otherwise | `undetermined` | `none` |
| 4 | `chain_closes` and `chain_len ≥ 2` and `nper ≥ ncum` | `per-period` | `chain-closure` |
| 5 | `ncum > 0` and `nper == 0` | `cumulative` | `filing-arithmetic` |
| 6 | county prior is `cumulative` and every live filing has a parseable C | `cumulative` | `county-prior` |
| 7 | otherwise | `undetermined` | `none` |

**The county prior is a TIE-BREAK ONLY and is never allowed to overrule a filing's own
arithmetic.** It exists for `summit` / `wasatch` / `juab`, which print **no beginning balance at
all** (0 of 131, 0 of 111, 0 of 27) so no chain is constructible, and whose own caveat rows assert
the cumulative regime. Hard-code it from the caveat rows, with the citation inline:

```python
COUNTY_PRIOR = {  # from each county's cf-* caveat row; TIE-BREAK ONLY (rule 6)
    "utah_county":       "per-period",   # caveat: "regime PER-PERIOD"
    "salt_lake_county":  "per-period",   # caveat: per-period column; 2 filers deviate
    "weber_county":      "cumulative",   # caveat: "regime CUMULATIVE … never a sum"
    "summit_county":     "cumulative",   # caveat: "CUMULATIVE snapshots — never sum"
    "juab_county":       "cumulative",   # caveat: "these forms are cumulative"
    "wasatch_county":    "mixed",        # caveat: "regime is per CANDIDATE, not per form"
    "cache_county":      "mixed",        # caveat: "is_incremental varies PER FILING"
    "washington_county": "mixed",        # CLAUDE.md: template per-period, minority cumulative
}
```

A `mixed` prior never fires rule 6 — those three counties must settle every cycle on its own
arithmetic or emit a gap. That is the design's answer to *"regimes vary per CANDIDATE, not per
form"*: **the prior can only ever confirm, never decide.**

---

## 4. TOTALS BY REGIME

### 4.1 `per-period` (rule 4)

```
raised_gross = Σ C over the chain          spent_gross = Σ E over the chain
carryover_opening = BB(first)              carryover_basis = 'chain-first-bb'
ending_balance = EB(last)                  chain_closes = True
raised_net_of_carryover = raised_gross     # carryover is a BALANCE, not a contribution —
                                           # nothing is subtracted; the two are equal BY CONSTRUCTION
```

Periods on a chain are disjoint by the owner-ratified reconciliation-basis reasoning
(*"period rows are DISJOINT from the prior filing's rows … so publishing both does not
double-count"*), and the closure proof confirms it arithmetically on this very cycle.

### 4.2 `cumulative` (rules 5, 6) and `cumulative-single` (rule 1)

```
governing = the latest-dated live filing with a parseable C (tie-break: larger C)
raised_gross = C(governing)                spent_gross = E(governing)
carryover_opening = BB(earliest live filing) or blank
carryover_basis = 'governing-report-bb' (single) | 'chain-first-bb' (multi) | ''
ending_balance = EB(governing)
raised_net_of_carryover = BLANK            # see §4.3 / ⚠ B1
n_governing = 1
```

**Never sum.** `summit David R. Brickey 2014` is the regression specimen: two filings stating
15,600.00 and 16,800.00 cumulative; the answer is **16,800.00**, and the existing city reducer
produces 32,400.00.

### 4.3 Carryover — separated, never silently subtracted

`carryover_opening` is **always** its own column. Measured at design time: **125 of 632 publishable
cycles open with a non-zero balance, totalling $1,099,586.15.** The largest cases are exactly the
distortion the deferral described:

| county | candidate | year | carryover | raised in cycle |
|---|---|---|---:|---:|
| salt_lake | Winder Newton, Aimee | 2022 | **215,160.87** | 61,084.62 |
| salt_lake | Gill, Sim | 2022 | 102,201.23 | 302,822.72 |
| salt_lake | Sim Gill | 2010 | 65,715.86 | 190,306.67 |
| utah | Brent Bowles | 2026 | 51,667.96 | 51,667.96 *(cumulative — see below)* |
| salt_lake | DeBry, Steve | 2022 | 46,616.34 | **0.00** |
| salt_lake | Ben McAdams | 2012 | 39,431.50 | 906,913.53 |

Winder Newton 2022 alone: a cumulative reading would report ~$276k where she raised $61k in the
cycle. `DeBry, Steve 2022` is the documented "put CUMULATIVE figures in the per-period column"
filer, and the classifier catches him as `cumulative` from his own arithmetic rather than from
SLCo's per-period prior — the per-candidate detection working as intended.

For **per-period** cycles the net figure needs no subtraction (§4.1). For **cumulative** cycles a
net figure would require subtracting the governing report's opening-balance column from its own
cumulative total. **Recommendation: leave `raised_net_of_carryover` BLANK for cumulative cycles**
(and say so in the caveat), because weber proves the opening-balance column's semantics is not
stable: on Froerer 2022 the cumulative contributions cell demonstrably equals `BB + this-period`
(31,415.05 = 7,815.05 + 23,600.00), but on his 2018 final the same column carries a last-report
*contributions* figure (73,234) beside a *balance* BB of 9,976.05. A blanket subtraction would be
wrong on one of those two. See **⚠ BLOCKING B1**.

### 4.4 `is_floor` — the published figure as a lower bound

Set `is_floor=1` when:
* `regime = 'per-period-single'` — one period was filed or survives; the cycle total is at least
  this, and more may exist (measured: ~50 cycles); **or**
* `regime = 'per-period'` and `chain_len < n_live` **and** an unchained filing carries a non-zero
  C — money exists in a filing the chain could not place.

`is_floor` rows publish a number. They must never be described as a total. Every consumer surface
(`v_cf_cycle_all`, the caveat, `gov_db_SCHEMA.md`) says so. See **⚠ BLOCKING B2**.

### 4.5 In-kind

`in_kind_basis` defaults to `unknown`. Populate `included`/`excluded` **only** where the county's
`build_finance.py` already settled it per filing from that filing's own arithmetic and recorded it
in `notes` (weber's Gochnour 2016 is the documented exclusion; summit's 4020/4278/8191/1268/11110/
20758/24234/24708 are documented inclusions). **Never infer it from cycle, form family or county**
— that is the owner-ratified 2026-08-17 finding, and it applies beyond summit. The stated totals
this layer sums are the filer's own printed figures, so whatever the filer did with in-kind is
already inside them; `in_kind_basis` documents which convention that was, it does not adjust
anything.

---

## 5. CONFIDENCE TIERS AND THE PUBLICATION RULE

| tier | meaning | publishes | measured n |
|---|---|---|---:|
| **A** | `regime='per-period'`, chain closes, `chain_len == n_live` — every filing accounted for and the arithmetic proves it | number, no caveat tag beyond the layer caveat | **90** |
| **A-superseded** | as A, but the chain excluded orphan filings (amendments/re-files resolved by the chain). `excluded_filings` names each. | number + `excluded_filings` | **54** |
| **B** | `regime='cumulative'` — the latest non-superseded report, per each county's own documented rule. No chain proof available (or none needed). | number, tagged `regime='cumulative'` | **281** |
| **C** | single-filing or otherwise unproved but arithmetically coherent; typically `is_floor=1` | number, tagged `is_floor` where applicable | **207** |
| **GAP** | nothing can be established | **row with blank figures + `gap_reason`** | **268** |

Total **900** candidate-cycles across the 8 counties; **632 publish a figure, 268 are honest
gaps** (measured 2026-08-23, `proto2.py`). Per county:

| county | A | A-sup | B | C | GAP | total | publishes |
|---|---:|---:|---:|---:|---:|---:|---:|
| salt_lake | 36 | 44 | 2 | 59 | 141 | 282 | 141 |
| utah | 43 | 4 | 6 | 70 | 35 | 158 | 123 |
| cache | 8 | 3 | 50 | 60 | 43 | 164 | 121 |
| summit | 0 | 0 | 72 | 0 | 2 | 74 | 72 |
| wasatch | 0 | 0 | 50 | 6 | 5 | 61 | 56 |
| weber | 2 | 1 | 50 | 0 | 0 | 53 | 53 |
| washington | 1 | 2 | 28 | 12 | 38 | 81 | 43 |
| juab | 0 | 0 | 23 | 0 | 4 | 27 | 23 |

These are **expected-outcome targets, not acceptance thresholds.** If your run differs materially,
find out why before shipping — but do not tune the classifier to hit them.

### 5.5 `gap_reason` vocabulary (closed enum + free clause)

| code | when |
|---|---|
| `no-stated-total` | no live filing prints a parseable contributions total (dominant in salt_lake: 141 cycles, mostly the 143 EasyVote filings that carry no `cf_filing` row) |
| `chain-broken` | multi-filing cycle, no closing chain, signatures do not agree |
| `regime-conflict` | period-only and cumulative-only filings coexist and no chain resolves them |
| `mixed-county-no-evidence` | a `mixed`-prior county where the cycle's own arithmetic is silent |
| `neither-basis` | the filer's arithmetic closes on neither reading (washington's `delta` class; weber's `neither` filings) |
| `superseded-only` | every live filing was superseded and the fallback set still cannot be settled |

Publication rule, stated plainly for the caveat: **a candidate-cycle publishes a number only when
that number is reproducible from named filings' own printed figures. Otherwise it publishes a gap
row naming why.** No estimate, no interpolation, no differenced cover.

### 5.4 Itemized cross-check (ADVISORY — never gates)

Where an itemized layer exists, compute per cycle:
* rows with `is_incremental='True'` → **sum** (periods are disjoint);
* rows with `is_incremental='False'` → **take the latest filing's ledger only** (the ledger
  restates the cycle — washington's 1,518 rows are 676 distinct donations);
* **mixed within one cycle → emit `itemized_check_note='not-comparable: mixed is_incremental'`
  and leave the figures blank.** Measured mixed cycles: weber 10, summit 8, utah 2, cache 1.

Free extra anchor for `utah_county`: its `cf_filing.notes` carry `ytd_contrib=` / `ytd_expend=`.
For a per-period cycle, `raised_gross` should equal the **last** governing filing's `ytd_contrib`.
Report agreement; do not gate. (`Jeffrey R. Buhman 2014`: chain sum 15,209.58 + 500 + 0 =
**15,709.58** = the last filing's `ytd_contrib`. Naive sum of all four stated totals = 30,919.16.)

Disagreement here is **usually the filer's arithmetic**, which every county's caveat says is
retained verbatim and never adjusted. Record it; never correct a stated total from an itemized sum.

### 5.6 Override mechanism

`<county>/campaign_finance/**cycle_overrides_county.csv**` — columns
`candidate,election_year,raised_gross,spent_gross,carryover_opening,regime,reason,evidence,added`.
Values REPLACE the computed ones; `regime_basis` becomes `override` and `review_flag` carries the
reason. Mirrors the city `cycle_overrides.csv` convention and satisfies cardinal rule 2
(corrections go through documented override files, never in-place edits). Ship with these files
absent — an override is a human verification, not a build step.

---

## 6. VALIDATION GATES — what the implementation must PROVE

Ship a `--validate` mode on the reducer plus these checks. G1–G6 run against the emitted CSVs;
G7–G9 are repo-level.

| # | gate | pass condition |
|---:|---|---|
| **G1** | **Reproducibility.** For every published row, re-read only the `cf_filing` rows named in `governing_filings` and re-derive `raised_gross`/`spent_gross` by the row's own `regime` rule. | 100% exact match. Any miss is a hard FAIL. |
| **G2** | **Chain-closure proof.** Every `confidence` ∈ {`A`,`A-superseded`} row has `chain_closes='True'`. Report the per-county closure rate over all multi-filing cycles. | invariant holds; rates reported in the run banner and in the caveat |
| **G3** | **Zero change to existing cf_\* rows.** Snapshot `SELECT COUNT(*)` and a `md5` of an ordered dump of `cf_filing`, `cf_contribution`, `cf_expenditure`, `cf_cycle` before and after the whole change. | byte-identical |
| **G4** | **No county leakage into `cf_cycle`.** `SELECT COUNT(*) FROM cf_cycle` = **805**; `SELECT COUNT(DISTINCT city) FROM cf_cycle` = **29**; `SELECT COUNT(*) FROM cf_cycle WHERE city LIKE '%_county'` = **0**. | exact |
| **G5** | **No fabrication.** Every row with a non-blank `raised_gross` names ≥1 governing filing whose `stated_total_contributions` parses. Every row with a blank `raised_gross` has a non-blank `gap_reason` from the §5.5 enum, and vice versa. | 100% |
| **G6** | **Carryover never silently folded.** `raised_net_of_carryover` is blank, **or** (`regime` starts with `per-period` **and** it equals `raised_gross`), **or** an override set it. | 100% |
| **G7** | **Itemized cross-check, reported not gated.** Per county: cycles with a comparable itemized figure, % agreeing within $0.51, and the top 10 disagreements with their filing notes. | report exists and is filed in the run record; **no threshold** |
| **G8** | **Federation + repo gates.** `python3 scripts/build_cities_db.py` → auto-gate 44/44; `PRAGMA integrity_check` ok; `PRAGMA foreign_key_check` no rows; `python3 scripts/check_doc_numbers.py` exit 0; `python3 scripts/validate_entity.py <county>` for all 8 unchanged from its pre-change result. | all pass (SHIP_GATE.md predicates 1 and 3) |
| **G9** | **Specimen regression suite** (§7.2). | all pass |

**Do not run `scripts/build_cities_db.py` until the reducer's own output is validated** and the
`cycle_totals.py` guard from §0 is in place.

---

## 7. IMPLEMENTATION PLAN

### 7.1 Files

| action | path | note |
|---|---|---|
| **GUARD** | `scripts/campaign_finance/cycle_totals.py` | `all_cities()` → `e.level == 'city'` only; `write_city()` refuses non-city slugs; docstring cites §0 of this file. **Step 1, before anything else.** |
| **NEW** | `scripts/campaign_finance/cycle_totals_county.py` | the reducer. Stdlib only; reads `filing_totals.csv` + `index.csv` + `contributions.csv`/`expenditures.csv` (advisory) per county; writes `cycle_totals_county.csv`. CLI: `<slug>` \| `--all` \| `--validate` \| `--report`. Resolve dirs through `scripts/entities.py::by_slug` exactly as `cycle_totals.py::_cf_dir` does. |
| **NEW** | `scripts/campaign_finance/tests/test_cycle_totals_county.py` | §7.2 specimens |
| **EDIT** | `scripts/build_search_layer.py` | `CREATE TABLE cf_cycle_county` + `CREATE VIEW v_cf_cycle_all`; new loader block in `load_cf()` gated on `e.level != 'city'`; counts in the banner |
| **EDIT** | `scripts/build_cities_db.py` | 3 caveat rows (§8) |
| **EDIT** | `scripts/campaign_finance/SCHEMA.md` | new §4a documenting `cycle_totals_county.csv`; and — **owed since 2026-08-17, close it in this session** — record `validate_finance.py` check 6's declared period-scope exception in §6 |
| **EDIT** | `gov_db_SCHEMA.md`, root `CLAUDE.md` (CF block), `README.md` | §8 |
| **NEW (optional)** | `<county>/campaign_finance/cycle_overrides_county.csv` | only if a human verifies a correction |

### Shared script vs compute-at-federation

**Recommendation: the shared script writing a per-county CSV.** Confidence: high.

`compute_motion_std_noncity` exists in `build_cities_db.py` because counties publish **no**
`motions_std.csv` — there was no on-disk artifact to read, and no uniform flat-motion shape to
read it from. That condition does not hold here: every county already has a
`filing_totals.csv` with an identical 24-column header, so the city path works unchanged. Emitting
a CSV also (a) makes the layer diffable in git, so a regime reclassification is visible in review,
(b) gives `cycle_overrides_county.csv` a natural sibling, (c) lets `validate_finance.py` and the
per-county validators read it, and (d) keeps the derivation runnable without a full federation.

The anti-drift concern (a county rebuild leaving a stale CSV) is real and is handled the same way
the city tier handles it: the reducer is idempotent, `SCHEMA.md` records "regenerate after any
`build_finance.py`", and add a **staleness check** — the reducer refuses to validate if any
county's `filing_totals.csv` mtime is newer than its `cycle_totals_county.csv`.

**Keep exactly one classifier.** Put the money parser, the signature test, the chain builder and
the closure proof in `cycle_totals_county.py` as importable functions; if a future federation-time
path is ever wanted, it imports them the way `build_cities_db.py` imports
`normalize_motions.py` — so the tiers cannot drift.

### 7.2 Test plan — unit cases drawn from documented specimens

Each is a fixture of `cf_filing`-shaped dicts (copy the real values out of `gov.db`; do not
depend on the live db in tests).

| # | specimen | asserts |
|---:|---|---|
| **T1** | **SLCo `Rivera, Rosie` 2022** (9 filings, §3.4 table) | chain picks the bolded 5; `raised_gross=142,340.79`; `spent_gross=115,745.48`; `carryover_opening=1,341.42`; `ending_balance=27,936.73`; `chain_closes=True`; `confidence='A-superseded'`; the 4 orphans appear in `excluded_filings` with `orphan-not-chained`. **The amendment trio never sums.** |
| **T2** | **weber `Gage Froerer` 2022** (2 live filings: 2022-06-21 amended C 31,415.05 BB 7,815.05; 2022-11-01 C 13,895.18 BB 8,895.18) | supersede marker drops the June report; `regime='cumulative'`; `raised_gross=13,895.18` (**not** 45,310.23); `carryover_opening` is reported, not folded; `raised_net_of_carryover` blank. |
| **T3** | **weber officeholder carryover** — `Gage Froerer` 2022 opening 7,815.05 = his own 2018 final ending balance; `Harvey 2024 opens from his 2020 closing` | `carryover_opening` non-zero and reported in its own column on both; no cross-cycle subtraction is ever attempted |
| **T4** | **summit `David R. Brickey` 2014** (15,600.00 then 16,800.00 cumulative) | `raised_gross=16,800.00`; **never 32,400.00**; `regime='cumulative'`, `regime_basis='filing-arithmetic'`; `carryover_basis=''` (summit prints no BB) |
| **T5** | **utah `Jeffrey R. Buhman` 2014** (4 filings, two from ONE PDF both stating 15,209.58) | `raised_gross=15,709.58`; **never 30,919.16**; the duplicate restatement is excluded once; `itemized_check` agrees with the last filing's `ytd_contrib=15709.58` |
| **T6** | **utah clean per-period cycle** (pick any tier-A utah cycle with ≥3 chained filings) | `regime='per-period'`, `chain_closes=True`, `raised_net_of_carryover == raised_gross` |
| **T7** | **washington restating ledger** (a 2010/2012/2014 born-digital cycle, `is_incremental=False` on every row) | the itemized cross-check takes the **latest ledger**, never the sum; the stated-total derivation is unaffected by the itemized layer |
| **T8** | **washington cumulative-filling filer** — `Kevin Brooks` 2010 or `Chris White` 2012 (close only on the cumulative reading) | classified `cumulative` from its own arithmetic despite washington's per-period template; the template never decides |
| **T9** | **wasatch 2024 period-sheet restater** (one of the three named in `notes`) | classified `cumulative` from its own arithmetic despite `filing_regime='period'`; **proves `filing_regime` is not consulted for the basis** |
| **T10** | **SLCo `DeBry, Steve` 2022** (cumulative figures in the per-period column; carry 46,616.34, in-cycle C 0.00) | `regime='cumulative'`; not summed as periods |
| **T11** | **NEGATIVE CONTROL — a `neither`-basis cycle** (washington `delta` class or a weber `neither` filing) | emits a **gap row**: figures blank, `gap_reason='neither-basis'`, `confidence=''`. Producing any number here is a test failure. |
| **T12** | **NEGATIVE CONTROL — broken chain** (synthesize from the weber swapped-cover pair: two internally consistent covers that do not link) | `chain_len < n_live`, no tier-A, gap or floor as §4.4/§5.5 dictate — **never a silent sum** |
| **T13** | **GUARD** — `cycle_totals.all_cities()` returns zero `*_county` slugs; `write_city('weber_county')` raises | §0 landmine cannot recur |

### 7.3 Rollout order

1. **Guard** `cycle_totals.py` (§0). Prove: `all_cities()` has no county; `cf_cycle` still 805/29.
2. Build `cycle_totals_county.py` + tests. Iterate to green on T1–T13 with **no federation run**.
3. Run `--all --report`. Compare the tier/regime distribution to §5's table; investigate every
   material divergence and write the findings into the run record.
4. **Hand-verify a stratified sample against the source documents** — 3 cycles per county
   (one A, one B, one GAP), reading the filing PDFs/caches, not the CSVs. This is the
   verify-substance-against-primary-docs rule and it is not optional for a new sanctioned total.
5. Emit the 8 CSVs. Diff-review them.
6. Extend `build_search_layer.py` (table + view + loader). Re-federate.
7. G3/G4/G8: prove `cf_filing`/`cf_contribution`/`cf_expenditure`/`cf_cycle` are byte-identical and
   the repo gates pass.
8. Caveats (§8) + docs (§8) + `check_doc_numbers.py` additions in the **same session**.
9. `TODO_ARCHIVE.md`: move the LEADS.md deferral block verbatim under a dated anchor, leaving one
   changelog line. Update the LEADS entry to CLOSED.

### 7.4 Designed for the incoming salt_lake wave

A transcription wave (W1p2, ~130 newly-harvestable 2015–2021 paper filings) is live in
`salt_lake_county/campaign_finance/` as this spec is written, and SLCo has 245 EasyVote filings
still un-itemized behind it. **Nothing in this design needs revisiting when they land**:

* the reducer reads `filing_totals.csv` fresh on every run and derives regime per candidate-cycle
  from that run's filings — a new filing simply joins its group;
* new filings that fill a chain move cycles **from GAP → A** and from `is_floor` → total,
  monotonically improving coverage without a schema change;
* `gap_reason='no-stated-total'` (SLCo's 141 cycles) is precisely the state new acquisitions
  resolve;
* the itemized cross-check is advisory, so a growing itemized layer never destabilizes a
  published figure.

Re-run the reducer after each wave closes and record the tier deltas. Do **not** hard-code any
SLCo count into the reducer.

---

## 8. CAVEATS AND DOCS

### 8.1 New `caveat` rows in `scripts/build_cities_db.py`

1. `('*', 'campaign_finance', 'cf-cycle-tiers', …)` — **the row that prevents the naive union.**
   Must state: `cf_cycle` is CITY-ONLY and is `max(latest summary, summed interims)` of stated
   totals with no carryover concept; `cf_cycle_county` is the COUNTY tier, derived per
   candidate-cycle from each cycle's own printed arithmetic, carrying `regime`, a separated
   `carryover_opening`, `is_floor`, and gap rows; **the two are different measurements and must not
   be ranked against each other without reading both `basis`/`regime`**; `v_cf_cycle_all` unions
   them deliberately and carries this caveat on every row.
2. `('*', 'campaign_finance', 'cf-cycle-county-method', …)` — the method and its honest ceilings:
   stated totals primary; the balance-chain closure proof; the per-candidate regime rule and the
   fact that a county form prior can only confirm, never decide; the tier counts (A/A-sup/B/C/GAP
   and the 632-of-900 publication rate); `is_floor` semantics; `raised_net_of_carryover` blank for
   cumulative cycles and why; itemized cross-check advisory only; **empty itemized ≠ no donors**.
3. **REWRITE** `('*', 'campaign_finance', 'cf-coverage', …)` — the sentence *"cf_cycle is
   CITY-ONLY: county cycle rollups are deliberately NOT derived (regimes vary per candidate and
   officeholder carryover contaminates naive sums — design lead in LEADS.md)"* is falsified by this
   layer and must be replaced in the same session, pointing at `cf_cycle_county`. Keep
   **"NEVER sum `cf_filing` dollar columns"** — it is still true and now has a sanctioned
   alternative for both tiers.

Per-county `cf-*` rows need no rewrite; they already document each regime and this layer consumes
them. Add one clause to any county whose classifier outcome contradicts its row (none expected —
all eight agreed in the design measurement).

### 8.2 Doc updates (same session — SHIP_GATE predicate 3)

* **root `CLAUDE.md`**, campaign-finance bullet: `cf_cycle` is city-only **and `cf_cycle_county` is
  the county-tier equivalent**; one sentence on regime + separated carryover + gap rows; keep the
  never-sum-`cf_filing` rule.
* **`gov_db_SCHEMA.md`**: `cf_cycle_county` table + `v_cf_cycle_all` view + updated caveat count.
* **`README.md`**: one line in the campaign-finance sentence.
* **`scripts/campaign_finance/SCHEMA.md`**: new §4a (the CSV contract); §6 gains the owed
  check-6 exception record.
* **`scripts/check_doc_numbers.py`**: add assertions for the `cf_cycle_county` row count and the
  caveat count, so the new headline numbers are gated like every other.
* **`TODO_ARCHIVE.md` / `LEADS.md`**: §7.3 step 9.

**State explicitly, in every doc that mentions it:** `cf_cycle_county` is a **DERIVED** layer,
regenerated by `python3 scripts/campaign_finance/cycle_totals_county.py --all` after any county
`build_finance.py` run, and it is never hand-edited — corrections go through
`cycle_overrides_county.csv` (cardinal rules 2 and 3).

---

## 9. ⚠ BLOCKING QUESTIONS FOR THE OWNER

Everything not listed here is delegated to the recommended default. These two are genuinely
low-confidence and the implementation agent should get a ruling before shipping the affected
behavior. **Neither blocks starting** — build to the recommended default, flag the rows, ask.

### ⚠ B1 — Should `raised_net_of_carryover` be computed for CUMULATIVE cycles?

**Recommended default: NO — leave it blank for cumulative cycles.**

The subtraction (`cumulative total − the same report's own printed opening balance`) is arithmetic
inside one document, so it does not violate the never-difference-covers rule. But weber shows the
opening-balance column's semantics is **not stable across filings**: Froerer 2022's cumulative
contributions cell demonstrably equals `BB + this-period` (31,415.05 = 7,815.05 + 23,600.00), while
his 2018 final carries a last-report *contributions* figure (73,234) next to a *balance* BB of
9,976.05. One blanket rule is wrong on one of them.

This matters: **281 of 632 published cycles are tier B (cumulative)**, and several open with large
officeholder balances. Leaving the column blank means those cycles publish only a gross cumulative
figure that may include carried money — honest, tagged, but less useful.

**The question:** accept blank (honest, less useful), or authorize the subtraction gated on a proof
that the cumulative figure includes the carry (`|C − BB − this_period| ≤ tol` where the form prints
a this-report column), publishing net only where that proof holds and blank otherwise?

### ⚠ B2 — Should tier C (`is_floor`) rows publish a number at all?

**Recommended default: YES, publish with `is_floor=1`.**

**207 of 632 published cycles (33%) are tier C**, most of them single-filing per-period cycles where
the figure is a lower bound, not a cycle total. Publishing them makes the layer far more useful and
is honest as long as `is_floor` is respected — but it means a third of a *sanctioned totals* table
holds bounds, and a consumer who ignores one column will misread them.

**The question:** publish floors inside `cf_cycle_county` (recommended), or move them to gap rows
with `gap_reason='floor-only'` and the figure carried in `review_flag`, so that every non-blank
`raised_gross` in the table is a true cycle total?

### Non-blocking, recorded for the owner

* **`filing_regime` vocabulary collision** (§0.1) — this layer works around it; the durable fix is
  splitting the column into `statutory_stream` + `stated_basis`. File as a LEADS lead.
* **Cross-era name variance** (SLCo `Sim Gill` 2010 vs `Gill, Sim` 2022) — this layer groups
  verbatim and does not fold. Correct here; person-level folding belongs to `cf_candidate_person`.
* **cache's 42 cross-channel byte-duplicate rows** — group on sha256 before counting filings, per
  its caveat. Verify this does not inflate `n_filings` for cache cycles.

---

## 10. REFERENCE MATERIAL

Working notes and runnable prototypes: `_backups/2026-08-23-cycle-reducer-design/`
* `proto.py` — first-pass chain classifier (tier sizing)
* `proto2.py` — the full decision procedure of §3–§5; **the reference implementation** for the
  chain builder, the signature test and the closure proof. Read-only against `gov.db`; writes
  nothing to the repo.

Primary sources every implementer should read before changing a number:
`LEADS.md` (the 2026-08-02 deferral block; the 2026-08-17 RECONCILIATION-BASIS RULE blocks),
`scripts/campaign_finance/SCHEMA.md` §4/§6, `scripts/campaign_finance/validate_finance.py` check 6,
each `<county>/campaign_finance/AVAILABILITY.md` + `CLAUDE.md`, and the `cf-*` rows of the `caveat`
table in `gov.db`.
