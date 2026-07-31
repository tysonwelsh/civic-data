# PMN backfill — availability (Cottonwood Heights City)

**Checked 2026-07-13** against Utah Public Notice (`utah.gov/pmn`), entity **111**
(Cottonwood Heights). GET-only, throttled (`polite_fetch.py`); PMN files download with the plain
browser UA (only the *city* CivicEngage portal needs the full header set).

## What this dataset is
A **cross-check** of the repo's already-unioned minutes against a **full-history, all-body** PMN
sweep, plus the recovered files for the dates the union missed. Cottonwood Heights' core minutes
were built as a **portal (CivicEngage) ∪ PMN** union from the start — council body **2147**, PC
body **2148** were already harvested and 2020–2024 already backfilled from PMN. So this sweep's
job was to find what that union *missed*, by diffing on **meeting date** (not per-year counts) and
by classifying each PMN attachment on its **filename** (catching docs cross-filed under another
body).

## What was checked
- **Every** Cottonwood Heights public body was swept via the cumulative
  `notices.html?id=<body>&page=200` GET: **2147** City Council, **2148** Planning Commission,
  **2150** Architectural Review Commission, **3085** Board of Adjustments, **3287** Administrative
  Hearings, **7091** Appeals Hearing Officer, plus **6511** Parks/Trails/Open Spaces, **9027**
  Historic, **9035** Arts Council, **8699** Health-in-the-Heights, **9491** Citizen Budget
  (the last five carry agendas/notices only — **0 minutes**).
- Minutes detected by **filename** (via anchor `aria-label`, untruncated), then classified
  council / pc / admin / arc / boa / aho and date-parsed from the filename (authoritative;
  `event_date` fallback). Diff tolerance ±4 days. **0 filenames were unparseable.**
- Text corpus screened with `screen_corpus.py`: **0** dict-ratio / split-word / weird-char
  outliers / read errors across all 16 files (born-digital, clean). The only flag is advisory
  "ends_mid" on short admin-hearing minutes — normal for these brief 0-motion documents.

## What exists / was recovered
- **Council session (body 2147): a complete superset — 0 genuine gaps 2020+.** Every PMN council
  date is already in `meeting_minutes/minutes_index.csv`. Nothing to recover.
- **Planning Commission (body 2148): 1 genuine missing meeting — 2022-07-06** (a real PC Work
  Meeting) — recovered.
- **Administrative-Hearing-Officer sessions (body 3287): 15 missing dates, 2020–2023** — recovered
  (the repo's PC dataset scope includes admin hearings; it only had 2024+ before). These carry
  **no roll-call votes** — legitimate 0-motion land-use hearing minutes.
- **Total recovered: 16 docs / 16 dates** (all born-digital `text`). Files in `raw/`, sidecars in
  `text/`, catalogued in `index.csv` (§9 pmn_backfill contract header). Provenance in
  `raw/_fetch_log.jsonl` (url, status, bytes, sha256, retrieved_utc).

## What was NOT recovered, and why (honest scope boundary)
- **Architectural Review Commission (body 2150)** — a live design-review body with **13 in-window
  (2020+) minutes dates** on PMN. The repo has **no ARC dataset**, so these are out of the
  council/PC scope of this backfill. **Inventoried** in `coverage.md` as a candidate future
  dataset — a real, deliberate gap, not a scraper miss.
- **Appeals Hearing Officer (body 7091)** — 9 in-window minutes dates; separate quasi-judicial
  body, not modeled in the repo. Inventoried, not recovered.
- **Board of Adjustments (body 3085)** — minutes exist only 2013–2017, **all below the 2020
  floor**. Nothing in-window.
- **CDRA** — no separate PMN body; it is an **in-session** board whose votes already live inside
  the Council minutes (`body=CDRA`). Nothing separate to acquire.
- **2025–2026 council/PC minutes** are on the CivicEngage portal (already in the repo) but **not**
  posted to PMN under these bodies yet — the repo, not PMN, is authoritative for the recent window.

## Do NOT
- Modify any existing dataset. This is a **separate, review-then-merge** dataset. Merging the
  admin-hearing + 2022-07-06 PC docs into `planning_commission/` is a deliberate human/Claude step
  (re-slug into `minutes/<year>/<week>/`, append to `minutes_index.csv`, rerun `extract_votes.py`
  → `db/` → `weeks/`), not done here.

## ✅ PROMOTED 2026-07-16
All **16 recovered docs were merged into `planning_commission/`** (the deliberate merge step
above): 15 admin-hearing sessions (`slug=administrative-hearing`, extending the audited 2024+/
2021-10-06 convention backward — all legit 0-motion officer-decision minutes) + the 2022-07-06
PC doc (ONE combined PDF: 5:00 pm Work Meeting + 6:00 pm Business Meeting; **+6 motions /
+12 vote rows**, tagged **`provenance=pmn_minutes`** in `planning_commission/all_votes.csv`).
Verification notes: every doc's date/body verified in-body; none stamped draft (9 carry explicit
"Approved" stamps/filenames; the rest are the city's official PMN-published record with no draft
markings); the 2023-03-01 doc's in-body header misprints "March 1, 2022" (footer "APPROVED …
03/01/23" + CUP-23-xxx case numbers + Wednesday check prove 2023-03-01). Raw PDFs copied
(sha256-verified) to `planning_commission/raw/pmn_<date>_<slug>.pdf`; the originals here are
retained unchanged. Details: `../VERIFICATION.md` (2026-07-16 addendum).
