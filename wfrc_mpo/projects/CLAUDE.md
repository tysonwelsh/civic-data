# wfrc_mpo / projects — WFRC transportation project pipeline (TIP + RTP)

One normalized attribute table of **Wasatch Front Regional Council** capital transportation
projects: the short-range **TIP** (Transportation Improvement Program, 8 vintages
2020-2025 … 2027-2032) and the long-range adopted **2023-2050 RTP** (Regional
Transportation Plan) roadway + transit + active-transportation projects. Built for
growth/development research: where the region is investing, how much, and when.

## Files

- `projects.csv` — **canonical.** 5,146 rows, the shared 15-column schema (identical column
  set to the MAG module so the two federate cleanly):
  `entity, plan_kind, plan_vintage, project_id, name, mode, improvement_type, jurisdiction,
  county, phase_or_year, cost, status, description, source_layer, source_url`.
  `entity` is always `wfrc_mpo`; `plan_kind` is `tip` or `rtp`.
- `SOURCES.md` — full provenance, per-vintage field mapping, the field-name drift across
  TIP vintages, and honest gaps. **Read before quoting a field.**
- `raw/` — per-layer attribute JSON snapshots (returnGeometry=false), the byte-level source.
- `derived/` — the **TIP project-lifecycle layer** (2026-07-22, WFRC-native Phase 1;
  DERIVED — regenerate with `python3 build_project_history.py`, never hand-edit):
  `project_vintage.csv` (one row per pin × vintage, 3,453) + `project_history.csv` (one row
  per pin, 1,884: entry/exit/slip/cost-drift across the 8 vintages) + `BUILD_REPORT.md`
  (gates) + its own `SOURCES.md` (column semantics — read it before quoting `exited_tip`
  or `cost_drift_pct`; the statewide-2020 scope guard and left-censoring rules live there).
  Federated into `gov.db` as `project_vintage`/`project_history` with 4 caveat rows.
- `vintage_overrides.csv` — documented adjudications of (pin,vintage) attribute conflicts
  (cardinal-rule-2 override file; 2 rows: pin 19561 merge_dup, pin 21213 keep_both).
  Unadjudicated conflicts HARD-FAIL the derived build — new ones on refresh surface loudly.

## Row counts

- **TIP: 3,699** — 995 / 362 / 261 / 298 / 342 / 387 / 340 / 714 across vintages
  2020-2025 … 2027-2032.
- **RTP2023-2050: 1,447** — roadway 485 (394 lines + 91 points), transit 102 (69+33),
  active transportation 860 (731+129).

## Read-me-first caveats

1. **`plan_kind` changes what columns mean.** TIP `phase_or_year` = a **calendar year**
   (programmed forecast start); RTP `phase_or_year` = a **phase band** (1-4, time bands to
   2050). RTP `cost` = base-2019 $ (unphased); TIP `cost` = the programmed project value.
2. **RTP `status` is `status19vs23`** — how the project changed vs the 2019 RTP
   (New/Existing/Updated), NOT a construction status. TIP `status` IS a delivery status
   (Scoping/Awarded/Under Construction/Close Out).
3. **The 2020-2025 TIP is statewide-inclusive** (Utah/Washington/Cache counties present),
   unlike the WFRC-region-focused later vintages. Filter by `county` for WFRC-only.
4. **Vintages are never blended.** Only the adopted RTP2023-2050 is here. The DRAFT RTP2027
   next cycle is the refresh seam — catalogued in `../gis/index.csv`, not ingested.
5. **cost is blank, never 0** where the source was empty/non-numeric.
6. Geometry is NOT stored — `source_url` is a live per-record ArcGIS query; spatial
   endpoints are in `../gis/index.csv`.

## Rebuild

Re-query each WFRC ArcGIS service (org `taguadKoI1XFwivx`) layer with
`?where=1=1&outFields=*&returnGeometry=false&f=json` (page at 2000), map fields per
`SOURCES.md`, and rewrite `projects.csv` + `raw/`. Add new TIP vintages / the adopted
RTP2027 as NEW `plan_vintage` values.
