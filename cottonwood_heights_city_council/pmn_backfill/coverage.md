# PMN backfill — coverage (Cottonwood Heights City)

> **✅ PROMOTED 2026-07-16:** all 16 recovered docs below were merged into
> `planning_commission/` (vote rows `provenance=pmn_minutes`; +6 motions / +12 rows from the
> 2022-07-06 PC doc; the 15 admin hearings are legit 0-motion). See `AVAILABILITY.md` §PROMOTED
> and `../VERIFICATION.md` (2026-07-16 addendum). The tables below describe the pre-promotion
> diff and remain the recovery record.

**As of 2026-07-13.** Utah Public Notice (`utah.gov/pmn`) sweep of **every** Cottonwood Heights
public body, cross-checked by **meeting DATE** (±4-day tolerance) and **document count** against
the repo's audited `meeting_minutes/minutes_index.csv` (Council session) and
`planning_commission/minutes_index.csv` (PC + admin-hearing). Minutes were detected by scanning
attachment **FILENAMES** (from each anchor's `aria-label`, so untruncated), **not** the PMN type
labels (labels mislabel/undercount), and each doc was classified by its filename tokens so a
cross-filed doc is diffed against the correct body.

**Key result: Cottonwood Heights' core minutes are ALREADY a portal∪PMN union** (the original
build resolved council body **2147** and PC body **2148** and backfilled 2020–2024 from PMN).
This sweep therefore finds only what that union *missed*. It is a near-empty result **by
design**: the **Council session is a complete superset (0 genuine gaps 2020+)**; the only genuine
recoveries are on the **Planning-Commission side** — one PC work meeting and a run of 2020–2023
**Administrative-Hearing-Officer** sessions (which the repo's PC dataset scope already includes,
but had only picked up for 2024+).

## PMN entity + body ids (Cottonwood Heights entity id = 111)

| body id | body | minutes-like filenames | role vs repo |
|---|---|---|---|
| 2147 | City Council | 396 | **primary — Council session** (+ in-session CDRA) |
| 2148 | Planning Commission | 127 | **primary — PC** |
| 3287 | Administrative Hearings | 53 | PC-scope admin-hearing-officer sessions (repo files these under `body=PlanningCommission`) |
| 2150 | Architectural Review Commission | 31 | **separate body — NOT in repo** (inventory only) |
| 3085 | Board of Adjustments | 20 | separate body — NOT in repo (all pre-2018, below floor) |
| 7091 | Appeals Hearing Officer | 9 | separate body — NOT in repo (inventory only) |
| 3287/others | (agenda/notice-only bodies) | 0 | Parks/Trails, Historic, Arts Council, Health Coalition, Citizen Budget — no minutes |

**No CDRA body exists on PMN.** Cottonwood Heights' Community Development & Renewal Agency is an
**in-session** board — its votes ride inside the Council minutes doc (`body=CDRA` in the council
CSV), so there is nothing separate to sweep (confirmed: no "Development"/"Renewal" body in the
entity's public-body list). Every body was swept via the cumulative
`notices.html?id=<body>&page=200` GET (council history reaches back to 2009).

## Council session (body 2147, in-session CDRA) — per year

`repo` = distinct dates in `meeting_minutes/minutes_index.csv`; `PMN` = distinct meeting-dates
PMN holds minutes for under body 2147; `recovered` = new council dates fetched here;
`still-missing` = genuine council dates PMN has that the repo lacks, after recovery.

| year | repo | PMN | recovered | still-missing |
|---|---|---|---|---|
| 2020 | 27 | 27 | 0 | 0 |
| 2021 | 31 | 31 | 0 | 0 |
| 2022 | 28 | 27 | 0 | 0 |
| 2023 | 29 | 27 | 0 | 0 |
| 2024 | 28 | 23 | 0 | 0 |
| 2025 | 22 | 0 | 0 | 0 (PMN posts no 2025 council minutes on this body) |
| 2026 | 14 | 0 | 0 | 0 |

**Council is a complete superset — 0 recoveries.** (PMN's per-year council count runs *below* the
repo's from 2022 on because the repo also pulls the born-digital CivicEngage portal, which PMN
doesn't mirror; the union already holds every PMN council date.)

## Planning Commission + Administrative Hearings — per year

`pcRepo` = repo PC dates; `pcPMN`/`admPMN` = distinct PMN dates under body 2148 / body 3287
(class=admin); `recovered` = PC-scope dates fetched here.

| year | pcRepo | pcPMN (2148) | admPMN (3287) | recovered | still-missing |
|---|---|---|---|---|---|
| 2020 | 10 | 10 | 7 | 4 (admin) | 0 |
| 2021 | 7 | 7 | 6 | 5 (admin) | 0 |
| 2022 | 11 | 12 | 8 | 6 (5 admin + **1 PC**) | 0 |
| 2023 | 13 | 13 | 6 | 1 (admin) | 0 |
| 2024 | 4 | 4 | 2 | 0 | 0 |
| 2025 | 10 | 0 | 1 | 0 | 0 |
| 2026 | 3 | 0 | 0 | 0 | 0 |

**Recovered — 16 docs / 16 dates:**
- **1 genuine PC work meeting:** **2022-07-06** (`070622 CHPC Mtg - Approved Minutes.pdf`, body
  2148) — a real Planning Commission Work Meeting (Wed Jul 6, 2022, Chair Jesse Allen presiding)
  the original union missed entirely.
- **15 Administrative-Hearing-Officer sessions, 2020–2023** (body 3287): 2020-03-11, 2020-06-17,
  2020-07-01, 2020-09-02, 2021-03-17, 2021-04-07, 2021-05-26, 2021-09-29, 2021-12-15, 2022-02-09,
  2022-03-30, 2022-05-18, 2022-06-08, 2022-10-12, 2023-03-01. The repo's PC dataset already treats
  admin-hearing minutes as `body=PlanningCommission, slug=administrative-hearing` (it had them for
  2024+ from the CivicEngage portal + one 2021-10-06 from PMN); these fill the 2020–2023 hole.
  Admin hearings are staff-level land-use approvals and **carry no roll-call votes** — legitimate
  0-motion minutes files (see `../planning_commission/CLAUDE.md`).

The **2024-10-29** joint PC/CC work session appears on PMN under the Council body
(`102924 CHCC PC Meeting Minutes Approved.pdf`) but is **already in the repo** (council index,
`2024-10-29`, from CivicEngage) — *not* a gap, excluded.

## Separate-body inventory (NOT recovered — out of council/PC scope)

These are distinct CH public bodies with their own minutes on PMN that the repo does **not** model
(there is no ARC/BOA/appeals dataset). Documented here so a future targeted build could pick them
up; they are **not** council or PC minutes, so recovering them is out of this dataset's scope.

- **Architectural Review Commission (body 2150)** — 30 distinct minutes dates 2013–2023;
  **in-window (2020+): 2020×5, 2021×4, 2022×1, 2023×3 = 13 dates**. A live land-use body
  (design review) with named minutes on PMN. **The most consequential inventory finding** — a
  candidate future dataset.
- **Appeals Hearing Officer (body 7091)** — 11 minutes dates; in-window 2021×2, 2022×3, 2023×3,
  2025×1 = 9 dates. Quasi-judicial appeals body.
- **Board of Adjustments (body 3085)** — 19 minutes dates, **all 2013–2017 (below the 2020
  floor)** — nothing in-window.

## Reproduce
`python3 chpmn_parse.py` (notices HTML → `_work/attachments_all.csv`) → `python3 chpmn_diff.py`
(classify + per-date diff vs repo) → `python3 chpmn_build.py` (select recover set →
`_work/recover_manifest.csv`) → fetch via `polite_fetch.py --batch _work/fetch_batch.txt` →
`pdftotext -layout` sidecars → `python3 chpmn_index.py` (→ `index.csv`).
