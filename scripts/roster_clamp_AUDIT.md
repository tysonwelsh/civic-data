# Roster vote-bound CLAMP — adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build the change)
**Scope:** roster-hardening item #2 — `roster_lib.load_vote_dates()` + `clamp_vote_bounds()`
replacing the old person-level `first_vote`/`last_vote` min/max. Read-only; ground truth
queried directly from `cities.db` (`vote → motion → meeting`, `body='Council'`).
**Verdict up front:** the clamp is **CORRECT and SAFE fleet-wide** on the DATA. **1 confirmed
defect, documentation-only** (provo `roster/CLAUDE.md` still defines the field as person-level).

---

## Method

Independent recompute harness (`scratchpad/verify.py`): for every one of the **370** tenure
rows in all 16 `council_terms.csv`, I re-derived the correct in-window first/last Council vote
straight from `cities.db` — `SELECT p.name_key, m.meeting_date FROM vote v JOIN motion mo JOIN
meeting m JOIN body b JOIN person p WHERE v.city=? AND b.name='Council'` — mapped through each
driver's `db_key`, then applied the half-open window `start_date <= d < (end_date or 9999)`
**reimplemented from scratch**, and compared to the CSV cell.

Corroborating checks: `db_key` omission sweep, blank-truthfulness proof, crossover enumeration,
orphaned-vote sweep, mayor-regime split, prose sweep. `meeting.body_id` and `motion.body_id`
never disagree fleet-wide, so the body filter is unambiguous.

---

## (A) CONFIRMED DEFECTS

### D1 — provo `roster/CLAUDE.md` misdefines `first_vote`/`last_vote` as person-level (prose contradicts data). Severity: MEDIUM (doc-only; data is correct)

`provo_city_council/roster/CLAUDE.md:52-54` (a LIVE current-state doc, not a dated audit) still
reads:

> **`first_vote` / `last_vote`** — the person's first/last observed council member-vote in
> `cities.db` (`role`, `city='provo'`, `body='Council'`). **Person-level** bounds (span all
> of a person's terms).

This is the exact stale claim item #5 targets. The clamp makes the cells **per-tenure**, and the
provo CSV proves it — four multi-term holders carry a first-row `last_vote` strictly earlier than
their person-level max:

| person | first-row window | CSV `last_vote` | person-level max (cities.db) |
|---|---|---|---|
| george_handley (D2) | `[2018-01-01, 2022-01-04)` | **2021-12-14** | 2025-11-18 (801 votes, 2020-01-07..2025-11-18) |
| travis_hoban (D4) | `[2020-01-07, 2024-01-09)` | **2023-12-12** | 2026-05-12 |
| rachel_whipple (D5) | `[2022-01-04, 2026-01-13)` | **2025-11-18** | 2026-05-12 |
| katrice_mackay (CW-I) | `[2022-01-04, 2026-01-13)` | **2025-11-18** | 2026-05-12 |

cities.db ground truth for handley: person-level `MAX(meeting_date)=2025-11-18`, but the last vote
inside `[2018-01-01, 2022-01-04)` is `2021-12-14` — exactly the clamped cell. The doc says the cell
"span[s] all of a person's terms"; it demonstrably does not.

This is the **only** city whose CLAUDE.md was not reworded: the other 15 reference "person-level"
solely to describe the OLD/replaced behavior (qualified with "old", "former smear", "would have
smeared", "LANDED 2026-07-11", "no longer one shared span").

**Fix:** reword provo `roster/CLAUDE.md:52-54` to match the fleet, e.g. "clamped to each tenure's
own half-open `[start_date, end_date)` window (LANDED 2026-07-11 — `roster_lib.clamp_vote_bounds`,
replacing the old person-level min/max); blank if the window holds no observed vote. The
authoritative service interval is always `start_date`/`end_date`." Also correct the source
reference `(role, …)` → the clamp reads the `vote → motion → meeting` join (`load_vote_dates`), not
the `role` table.

**No data defect** — the four cells above are the *correct* clamped values.

---

## (B) Calibration notes (not defects)

1. **370/370 rows reproduce exactly.** `verify.py` found **0 mismatches** — every CSV
   `first_vote`/`last_vote` equals the independently recomputed min/max of that person's
   council-vote dates intersected with `[start_date, end_date)`, including all VACANT rows (bounds
   blank) and all `non_voting_mayor` Mayor rows (bounds blank).

2. **Blanks are truthful.** All 47 blank Council-body rows have **0** in-window council votes.
   Several have real council votes that all fall *outside* the shown pre-floor window (e.g.
   taylorsville `ernest_burgess` 125 votes, millcreek `bev_uipi` 100, south_jordan
   `patrick_harris` 34, `tamara_zander` 47) — the clamp correctly places them in other tenures /
   excludes them; none is lost (the orphan sweep confirms every such vote lands in another tenure
   of the same person or is a documented tie-break/attribution stray).

3. **`db_key` omission sweep is clean.** Only 4 council `name_key`s fleet-wide are absent from any
   `db_key`, all correctly: `park_city/andybeerman` (documented non-voting-mayor tie-break),
   `lehi/markjohnson` (4 mayoral tie-breaks on 3:2/2:3 splits — non-voting mayor),
   `south_jordan/dawnrramsey` and `st_george/jonpike` (mayors, 1 stray vote each). None has a
   council tenure, so no real in-window council vote is excluded.

4. **All 12 crossover people de-smeared correctly** (logan Anderson, millcreek Jackson, nephi
   Seely, ogden Nadolski, park_city Worel + Dickey, sandy Zoltanski + Robinson + Houseman, slc
   Mendenhall, st_george Hughes + Randall, taylorsville Overson + L. Johnson, west_valley Lang,
   west_jordan Lamb). Verified from cities.db that the clamp cut real later votes:
   - **Worel** person-level council `MAX=2024-08-22` (mayoral tie-break, Res 16-2024); AL-A1 tenure
     `[2020-01-09, 2022-01-06)` → `last_vote=2021-12-16`. Reproduces the RETIRED override target.
   - **Randall** has council-body votes on 2021-02-25 and 2025-02-20 (post-mayor); AL-B1
     `[2018-01-01, 2021-01-21)` → `last_vote=2021-01-19`. Reproduces the RETIRED override target.
   - **Lang** (voting mayor) — half-open boundary works: her 2022-01-04 votes land on the MAYOR row
     (`first_vote=2022-01-04`), excluded from D3 `[…, 2022-01-04)` whose `last_vote=2021-12-14`.

5. **Both retired overrides are header-only and reproduced by the clamp alone.**
   `park_city/roster/roster_overrides.csv` and `st_george/roster/roster_overrides.csv` have 0 data
   rows (header + `# RETIRED 2026-07-11` comment only); the clamp alone yields Worel 2021-12-16 and
   Randall 2021-01-19.

6. **Mayor regime split is clean:** the 4 voting-mayor cities (millcreek, orem, vineyard,
   west_valley) carry mayor-era bounds on every Mayor row; the 12 non-voting-mayor cities have
   every Mayor row blank. Consistent with each city's CLAUDE.md.

7. **No query regressed.** `roster_as_of` / `representatives_for_address` read only
   `start_date`/`end_date` (code inspected — they never reference `first_vote`/`last_vote`);
   `clamp_vote_bounds` writes only the two vote-bound cells and runs after `chain_end_dates`, so no
   seat chain, VACANT interval, or date moved. Counts confirmed **370 rows / 255 high · 114 medium
   · 1 low**. Change magnitude corroborated: **14 clamp-induced blank rows × 2 cells = 28 blanks**,
   matching the stated "28 went blank".

8. **Half-open boundary edge (documented convention, not a defect):** a departing member whose
   final vote falls exactly on the end/vacate date (= successor start) has that vote assigned to the
   successor, so their `last_vote` shows the prior meeting — slc `eva_lopez_chavez` (window ends
   2026-05-05, `last_vote=2026-04-21`), slc `amy_fowler` (ends 2023-06-13, `last_vote=2023-06-06`),
   vineyard `sara_cameron`. One-meeting effect on an informational field; the authoritative interval
   is `start_date`/`end_date`.

9. **cities.db attribution noise is correctly quarantined (surfaces a separate, non-roster TODO):**
   several departed members have stray council-body votes in cities.db dated months after their
   documented final meeting — ogden `angela_choberka` & `bart_blair` (2026-05-19, both left council
   2026-01-06), slc `darin_mano` (2026-03-24, did-not-run, succeeded 2026-01-13). The clamp
   correctly excludes these rather than smearing them as `last_vote`. Worth a cities.db
   person-resolution follow-up, but it does **not** affect the roster.

10. **park_city `AUDIT.md` #2 and orem `AUDIT.md` #1** retain present-tense pre-clamp finding
    bodies, but each file carries a **RESOLUTION ADDENDUM — 2026-07-11** ("the dated findings above
    are unchanged") — the whitelisted dated-audit + addendum convention. Acceptable; a reader must
    reach the addendum. (Contrast provo D1, which has no addendum and states person-level as the
    live definition.)

---

## (C) Verdict

**The clamp is correct and safe to ship fleet-wide.** All 370 tenure rows exactly reproduce an
independent from-scratch recompute against `cities.db` (0 data defects); the 47 blank council rows
are all truthfully empty; every crossover person is de-smeared correctly; both retired overrides
are reproduced structurally with header-only files; the voting/non-voting mayor split is clean; and
the authoritative query surface (`start_date`/`end_date`, seat chains, VACANT intervals,
`roster_as_of`) is untouched, with row counts and the 28-blank/209-cell magnitude corroborated.

**The single confirmed finding (D1) is documentation-only:** provo `roster/CLAUDE.md` was never
reworded and still defines `first_vote`/`last_vote` as person-level, contradicting its own clamped
CSV. Fix the four lines; no data change required.
