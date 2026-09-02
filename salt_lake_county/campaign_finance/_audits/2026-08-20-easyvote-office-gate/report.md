# EasyVote office-gate repair — Salt Lake County campaign finance

**Date:** 2026-08-20 · **Scope:** `salt_lake_county/campaign_finance/build_finance.py` +
the three derived CSVs · **Backups:** `_backups/2026-08-20-slco-gate/` (pre-change
`contributions.csv`, `expenditures.csv`, `filing_totals.csv`, `build_finance.py`, SHA256s
in `SHA256.txt`).

Federation was NOT run (standing GOTCHAS rule — gov.db is federated once at wave close).

---

## 1. Root cause, verified at the source

`build()` gated every itemized row on

```python
def county_office(guid):
    return BL.is_county_officename(offices.get((guid or "").upper(), ""))
```

`offices` comes from `raw/easyvote_api/offices.json` (64 entries), which is a snapshot of
**currently-active** offices, not a complete historical GUID table. **12 distinct
`OfficeGuid` values that appear on itemized rows are absent from it.** For those rows the
lookup returned `""`, `is_county_officename("")` was False, and the row was dropped with no
log line.

The 12 unresolved GUIDs, and the office each one actually belongs to (from the filing's own
metadata — `documentsearch.json`'s filer-level `officename`, mirrored verbatim in
`raw/easyvote/_fetch_log.jsonl`; the two agree on **every** row):

| OfficeGuid | resolves to | rows | in county scope |
|---|---|---:|---|
| `DAB06B7E-…` | Salt Lake County Clerk | 1,139 | yes |
| `8954E6B2-…` | Salt Lake County Sheriff | 252 | yes |
| `796E1406-…` | Salt Lake County Council District 1/3/5 + "County Council District" | 195 | yes |
| `3CD50A8D-…` | Salt Lake County Auditor | 74 | yes |
| `5CFC9EFB-…` | Salt Lake County Council At-Large B | 43 | yes |
| `C4977E85-…` | Salt Lake County Recorder | 4 | yes |
| `D3275791-…` | Salt Lake County Surveyor | 1 | yes |
| `61F0F6A9-…` | Canyons School Board (+ its districts) | 273 | no |
| `EF4E5F8B-…` | Granite School District / Board | 168 | no |
| `EFD90CCF-…` | Salt Lake City School Board / District | 51 | no |
| `BFDEDC58-…` | Jordan School District / Board | 34 | no |
| `EC3B6E6C-…` | Murray School District / Board | 25 | no |

Each missing GUID maps to exactly ONE office family across every filing it appears on —
the resolution is unambiguous, not a majority vote.

Reproduction of the old gate outside the build returned **4,957 / 3,279** kept rows
(4,956 / 3,278 published, the difference being the one `Training Candidate` record with no
downloaded PDF) — i.e. the reproduction is faithful.

## 2. The fix

`build_finance.py` only. `scripts/campaign_finance/*` untouched; `build_lib.py` (which is
**Salt Lake County-LOCAL**, not shared — see §8) untouched.

Office resolution is now two-step, **row-level GUID first, filing metadata only as a
fallback**:

```python
def officename_for(r):
    return (offices.get((r.get("OfficeGuid") or "").upper())
            or doc_meta.get(base_fid(r), {}).get("officename")
            or filer_officename.get(base_fid(r), ""))

def county_office(r):
    return BL.is_county_officename(officename_for(r))
```

The county-scope test is applied to the RESOLVED name, so school-board and municipal filers
stay excluded.

**Why GUID-first, not metadata-first — this is load-bearing.** The filer-level `officename`
is the filer's CURRENT registration, and it lies about older documents. Charlotte
Fife-Jepperson's filer record reads "Salt Lake County Council District 2", but her 2024-cycle
filings' own covers read **"Office Sought: Salt Lake School Board, District 2"** (verified at
the page, `raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__7DB60678.pdf` and `__1BFB7187.pdf`), and
their rows' `OfficeGuid` correctly resolves to `Salt Lake School Board`. Her 2026 filing
(`__B5AB014E.pdf`) settles it completely: its cover prints **Office = Salt Lake City School
Board District 2** (the seat she holds) and **Office Sought = Salt Lake County Council
District 2** (the seat she is running for). Metadata-first would have pulled 73 school-board
contributions and 40 expenditures into a county dataset. GOTCHAS' "portal labels lie" applies
to this portal too.

GUID-first also makes the change a **strict superset by construction**: every row the old
gate admitted resolves on exactly the same string and is admitted again.

**Second half of the fix — one row per filing.** 26 of the 33 newly-admitted filings are
EasyVote-2022 filings that the vision totals tranche ALSO emits a `filing_totals` row for
(their printed totals live only on an image-only PDF). Emitting a second, structured row
would have double-counted the filing. So `build()` now routes those filings' raw API rows
into `build_totals_tranche(api_itemized)`, which attaches them to the existing vision row via
a new `apply_api_itemized()`: `stated_*` is never recomputed, the itemized half is filled
from the API, and the delta between the two independent readings is published. A filing that
already carries a VISION itemization keeps it (the two are not merged) — today no
EasyVote-2022 filing does, so the branch is a documented guard, not live behaviour.
`tranche_document_ids()` mirrors the tranche's era test so the two cannot drift.

## 3. Before / after

| | before | after | delta |
|---|---:|---:|---:|
| contributions rows | 19,702 | 20,930 | **+1,228** |
| contributions $ | 8,733,183.27 | 9,003,802.56 | **+270,619.29** |
| expenditures rows | 11,403 | 11,882 | **+479** |
| expenditures $ | 6,453,253.40 | 6,828,672.55 | **+375,419.15** |
| filing_totals rows | 834 | 841 | **+7** |
| EasyVote-API itemized contributions | 4,956 | 6,184 (5,032 structured + 1,152 attached to vision rows) | +1,228 |
| EasyVote-API itemized expenditures | 3,278 | 3,757 (3,425 + 332) | +479 |

## 4. Proof obligations

**(1) Superset property — PASS.** Multiset diff of every data row against the backups:
contributions 0 lost / 1,228 added; expenditures 0 lost / 479 added; headers byte-identical.
`filing_totals`: 0 rows removed, 7 added, 26 pre-existing rows changed — and the columns that
moved are **only** `itemized_contrib_sum`, `itemized_expend_sum`, `reconciles_contrib`,
`reconciles_expend`, `recon_delta_contrib`, `recon_delta_expend`, `self_funded_amount` (10),
`n_contrib_rows` (22), `n_expend_rows` (25), `notes`. **Zero** identity or `stated_*` columns
moved. (Row ORDER inside the CSVs shifts where new rows interleave; row CONTENT does not.)

**(2) Every added row is provably a county office — PASS.** Office × seat histogram of the
added rows:

| office / seat | contributions | expenditures |
|---|---:|---:|
| Clerk | 1,006 | 133 |
| Sheriff | 115 | 137 |
| Auditor | 37 | 37 |
| County Council District 5 | 34 | 83 |
| County Council District 1 | 20 | 12 |
| County Council At-Large B | 4 | 39 |
| County Council District 3 | 4 | 30 |
| County Council (seat blank) | 5 | 6 |
| Recorder | 2 | 2 |
| Surveyor | 1 | 0 |

All ten labels are Salt Lake County COUNTY offices. **No school-board or municipal row
entered**; the whole output file contains only the ten county-office labels. All added rows
carry `extract_method=easyvote_api/json`, `extraction_confidence=high`, `in_kind=False`.

The 5+6 `County Council` rows with a blank seat come from four filings whose filer label is
the generic string "County Council District". Verified at the primary source — each filing's
own cover, transcribed in its `vision/` cache — as Salt Lake County C&E forms with
`Office Sought = "_Council - District"`: Soelberg **District 3**, Barnes ×2 **District 1**,
Cox **District 2**. They are county offices. (The coordinator's brief excluded these 11 rows
from its estimate as unadjudicated; **the source governs and they are admitted.** Their `seat`
is blank because `index.csv` carries no seat for them — a legible, fixable gap, flagged in §7.)

**(3) The cover tranche did not move — PASS.** `stated_total_contributions`,
`stated_total_expenditures`, `stated_beginning_balance`, `stated_ending_balance`,
`extraction_confidence`, `candidate`, `office`, `election_year`, `filing_date`,
`reporting_period`, `filing_type`, `source_filing`, `document_id`, `filing_regime` are
byte-identical on all 834 pre-existing rows.

The itemized-derived movement, reported in full: 26 filings went from
`n_*_rows=0`, blank `itemized_*_sum`, blank `reconciles_*` to a filled itemized half.
**Every one of the 52 sides reconciles EXACTLY** (|delta| ≤ $0.01): 26 contribution sides
True, 26 expenditure sides True, every `recon_delta_* = 0.00`. Nothing was nudged; the
figures simply agree. This is a genuine independent cross-validation — the vision transcriber
read the printed Summary Page off a page image, the API returns born-digital schedule rows,
and the two match to the cent on filings as large as Chapman's $102,508.83 / 556 rows and
$96,608.99 / 10 rows.

Ten of the 26 also gained a `self_funded_amount`. The 7 new filing rows (2024/2026) carry
blank `stated_*` — the API publishes no printed totals — so their `reconciles_*` stay blank
(honest unknown), the existing structured-path convention.

`apply_api_itemized` carries one guard the vision path does not need: zero API rows on a side
is read as a real zero **only** when the form itself states $0.00 for that side; otherwise the
side is left blank with a note. All five zero-row sides here have a stated $0.00, so the guard
does not fire today.

**(4) The 2000 and 2030 oddities — adjudicated at the source.**

*2000 — EXCLUDED, with a stated reason.* The filing is
`raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__1BFB7187.pdf` (5 contributions / 11 expenditures).
Two separate facts:
 * the `2000` is an artifact — EasyVote carries the placeholder `datesubmitted "01/01/01"`
   for this document, which `build_index.py` rendered as `date=2001-01-01` and the even-year
   proxy floored to `election_year=2000`. The form itself is signed **11/26/24** and is an
   amendment of the 2024-11-16 report.
 * it is **out of county scope regardless of the date**: the cover reads
   **Office Sought = Salt Lake School Board, District 2**. It is a school-board filing.
   It is excluded for THAT reason, not for the date artifact.

*2030 — NOT garbage, NOT mine to fix.* `index.csv` row
`raw/clerk_legacy/snelgrove_R_Mayor_2031_YearEnd.pdf`, `election_year=2030`,
`date=2031-01-01`. Already adjudicated at the page by the wave-B2 transcriber and recorded
verbatim in the filing's own `notes`: the form is a **Year-End (January 31) report signed
1-28-14 and clerk-stamped JAN 28 2014**, printed on the 2012 template — i.e. the January-2014
year-end filing for the **2012 county-mayor cycle**. `2030`/`2031-01-01` are a mis-parse of
the `_2031_` token in the filename. It is a real, in-scope, transcribed county filing whose
manifest LABEL is wrong. The defect lives in `index.csv`, which is outside this task's write
set — and the tranche deliberately never overwrites a non-blank acquisition-time
`election_year` (doing so would break `validate_finance`'s row↔manifest referential check).
**Flagged for the coordinator**, unchanged here. This row was not touched by this rebuild.

**(5) Privacy — PASS.** Verified over the full key space of both API payloads: the
contributions file exposes 29 keys, the distributions file 22, and **not one is an address,
street, city, state, zip or postal field**. (`CustomSearchResultFields` is `null` on all
7,130 contribution rows.) There is no street address in the source to leak.
`donor_city`/`donor_state`/`donor_district` are blank on all 1,228 added contribution rows —
an honest absence in the structured feed, not a redaction, and the same state the pre-existing
API rows were already in.

**(6) Determinism — PASS.** Two consecutive `python3 build_finance.py` runs produce
byte-identical files:
```
bf3814d732957276124438ed0cd201c806bd0ec691eced32baf1a1a94cd2838d  contributions.csv
122a99482ea2e59c40201a2020a2fa97d3072f53259bdc68765de56d89c6395c  expenditures.csv
1896b01372acf4403b00a5900f05a6a0cde793d292e5b1dea6df9d90c38774bb  filing_totals.csv
```

## 5. Validator

`python3 scripts/campaign_finance/validate_finance.py salt_lake_county/campaign_finance`
→ **PASS (0 fails, 148 warns)**. Before the change the same validator run against the backup
CSVs gave **PASS (0 fails, 155 warns)** — 7 fewer warnings, exactly the 7
`index filing … has no filing_totals row` warnings the new filing rows close.

The 7 build-time "RECONCILIATION VERDICT DISAGREEMENT" lines the build prints are
**pre-existing** clerk-legacy vision filings (`jwinder_oct312006`, `Horiuchi` ×2, `Ott_G`,
`Burdick_M`, `Recanzone_P`, `Romero_R`). `apply_itemized` and every vision-itemized row are
untouched by this change (0 lost rows in the diff proves it); they are not introduced here
and are not in this task's scope.

## 6. What the gate correctly still excludes

877 contributions / 767 expenditures remain excluded. All are school-board or municipal
filers (Canyons, Granite, Jordan, Murray, Salt Lake City school boards; metro-township
filers) — the intended scope per `RECON.md` §scope — plus three itemized-only records with no
`documentsearch` entry and no downloaded PDF, which were already excluded by the existing
"no downloaded PDF" guard and remain so:
 * `DF1C2D9E-…` "Cleo Patra" with donors "john doe" / "mary doe" and a "kinkos" expenditure —
   an EasyVote **test record**;
 * `6D868938-…` Terry Bawden and `A7F47401-…` Trish Hull — no filer record, no PDF, so no
   office can be established and no `index.csv` path exists to key them to.

## 7. Findings flagged for the coordinator (NOT fixed here — outside the write set)

1. **`index.csv` mislabels 5 Charlotte Fife-Jepperson filings** as
   `office=County Council, seat=District 2` when the forms' own covers read
   `Office Sought = Salt Lake School Board, District 2` (docs `1BFB7187`, `7DB60678`,
   `C7936B62`, `F2EC7ADF`, `F46B5B5A`). They are school-board filings sitting in a
   county-office manifest. Her 2026 filing `B5AB014E` IS county (Office Sought = Salt Lake
   County Council District 2) and is correctly labelled.
2. **`index.csv` election_year/date for `snelgrove_R_Mayor_2031_YearEnd.pdf`** — `2030` /
   `2031-01-01` should be the 2012 cycle / a Jan-2014 year-end (see §4).
3. **`index.csv` `election_year=2000` + `date=2001-01-01` for `1BFB7187`** is an
   EasyVote `datesubmitted "01/01/01"` placeholder, not a filing date.
4. **Four filings could gain a `seat`**: Soelberg `15DD60FD` → District 3, Barnes `A1E63503`
   and `D23F4002` → District 1, Cox `A4DE0204` → District 2, each legible on the form cover
   and already captured in the `vision/` cache's `cover.district_number`.
5. **`AVAILABILITY.md` / `RECON.md` / `CLAUDE.md` counts move**: SLCo itemized contributions
   19,702 → 20,930 and expenditures 11,403 → 11,882; SLCo filing_totals 834 → 841 (the
   repo-wide "salt_lake 834" cover-tranche figure is a FILING count and now needs re-stating,
   though the cover tranche itself — the 834 vision-read stated totals — is unchanged).

## 8. Contradiction with the brief

The brief warns that `scripts/campaign_finance/build_lib.py` is shared with every other
county. **That file does not exist.** `build_lib.py` lives only at
`salt_lake_county/campaign_finance/build_lib.py` (plus two frozen copies under
`_backups/2026-08-01-county-acquisition/`) and is Salt Lake County-local; `build_finance.py`
imports it from its own directory even though it puts `scripts/campaign_finance` first on
`sys.path`, because that directory has no `build_lib`. The shared modules it does import are
`common.py`, `vision_lib.py` and `normalize_donors.py`. Per the brief's own rule, the source
governs — and in any case **no file outside `build_finance.py` was modified**, so no other
county's output can move.
