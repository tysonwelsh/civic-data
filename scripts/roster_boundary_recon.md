# Prior-plan (pre-2022) council-district geometry — recoverability recon

**Date:** 2026-07-11 · **Scope:** READ-ONLY assessment. No fetches, no edits to roster/geo/db.
**Question:** For each district city, is the *prior-plan* (`plan_pre2022` / `plan_2012` /
`plan_2016`) council-district GEOMETRY — currently a blank `geometry_ref` + `low`
confidence acquisition gap in `roster/district_versions.csv` — recoverable, and how?

## Method (the Path-A test)

The CURRENT district polygons in every one of these cities were **derived, not fetched**:
`geo/precincts.geojson` (UGRC VistaBallotAreas, one polygon per precinct) **dissolved by**
a precinct→district assignment taken from the **district-contest precinct rows** in
`election_results/<city>_results_by_precinct.csv` (each council-DISTRICT contest lists
exactly the precincts that voted in it, so contest-precincts == district-precincts for that
election's lines). Five cities even ship the tool: `geo/build_precinct_district_map.py
--years YYYY,YYYY`.

**Path A therefore reconstructs the PRIOR map the same way, from repo data alone, IF**
(a) pre-2022 council-DISTRICT contest rows exist (they give the *old* assignment), AND
(b) the *old* precinct codes still have geometry in the current `precincts.geojson`.
I measured both, per city, plus assignment nesting (does each old precinct map to ONE old
district?) and how much the old assignment differs from the current one (is the prior map
genuinely distinct and worth recovering?).

**Vintage caveat that caps confidence at `medium`:** every `precincts.geojson` on disk is
the *current* UGRC layer (SLCo cities carry `EffectiveDate = 2025-12-17`). So a Path-A
prior map = *old assignment applied to current precinct shapes*. Where the county left
precinct boundaries stable and only moved DISTRICT lines along them (the common Utah case),
this is faithful; where precincts themselves were reshaped in 2022, shared-code precincts
differ slightly and retired codes leave holes. This is exactly how the CURRENT tay/wjd/wvc/
slc maps were already built (precinct-dissolved, not official layers), so a `medium`-
confidence prior map is a real upgrade from the present blank/`low`, kept honestly distinct
from the fetched-authoritative current plan.

## Per-city results

| City | Prior cycle | Pre-2022 district data (years) | Old precinct codes vs current geo | Nesting (conflicts) | Old≠current assign | Verdict |
|---|---|---|---|---|---|---|
| **west_jordan** | 2012 (`plan_pre2022`) | 2019 = all 4 districts, 68 precincts | **68/68 present** (WJD###) | 0 conflicts | 28/68 moved | **REPO-RECONSTRUCTABLE** |
| **taylorsville** | 2012 (`plan_pre2022`) | 2017+2021 (or 2019+2021) = D1–5, 39 precincts | **38/39 present** (TAY###; TAY045 missing) | 1 (TAY013) | 25/38 moved | **REPO-RECONSTRUCTABLE** |
| **south_jordan** | 2012 (`plan_pre2022`) | 2019+2021 = D1–5, 49 precincts | **49/49 present** (SJD###) | 0 conflicts | 34/49 moved | **REPO-RECONSTRUCTABLE** |
| **sandy** | 2012 (`plan_pre2022`) | 2019+2021 = all 4 districts, 76 precincts | **76/76 present** (SAN###) | 1 (SAN024) | n/a* | **REPO-RECONSTRUCTABLE** |
| **millcreek** | 2016 incorporation (`plan_2016`) | 2017+2019 = all 4 districts, 46 precincts | **46/46 present** (MIL###) | 0 conflicts | 39/46 moved | **REPO-RECONSTRUCTABLE** |
| **west_valley** | 2012 (`plan_pre2022`) | 2019+2021 = all 4 districts, 74 precincts | **64/74 present** (10 missing: WVC068,070–074,076,077…) | 1 (WVC038) | 44/63 moved | **REPO-RECONSTRUCTABLE (partial — 13% holes)** |
| **slc** | 2012 (`plan_2012`) | 2019+2021 = all 7 districts, 124 precincts | **107/124 present** (17 missing: SLC135,146–152…) | 2 (SLC055,062) | 65/105 moved | **REPO-RECONSTRUCTABLE (partial — 14% holes; county renumbered)** |
| **provo** | 2012 (`plan_2012`) | 2021 = D2/D5 only, 45 precincts (PR##); D1/3/4 never had precinct CSVs | **0/45 present** — old PR## vs current 25PR## (renumbered) | — | — | **EXTERNAL-FETCH** |
| **ogden** | 2012 (`plan_2012`) | **none** — only 2023/2025 exist (29OG##), no pre-2022 rows | 0 — 29OG## ≠ current OGD## anyway | — | — | **EXTERNAL-FETCH** |

\* sandy's precinct→district lives in `roster/`, not a `geo/precinct_to_district.csv`, so the
old-vs-current field wasn't machine-diffable here; the 76/76 geometry match is the load-bearing result.

Ogden (4 districts) and provo (5 districts) also carry At-Large + Mayor **citywide** rows —
those are `N/A` (whole-city extent, unchanged by redistricting, already `high`). Only their
DISTRICT prior geometry is the gap, and it is the hard case below.

## The dissolve recipe (Path A cities)

For each REPO-RECONSTRUCTABLE city, produce `geo/council_districts_pre2022.geojson`:

1. Build the **old** precinct→district map from the pre-2022 district-contest rows of
   `<city>_results_by_precinct.csv` (years in the table; combine the staggered odd-year
   cycles so all districts appear). Resolve the 0–2 conflict precincts by hand (a precinct
   that appears under two district contests across years = a precinct that was reassigned or
   split; pick the year matching the plan window, or drop to the edge it borders).
2. Filter `precincts.geojson` to those codes and **dissolve (union) by old district**.
3. Write the polygons; set `district_versions.csv` `geometry_ref =
   geo/council_districts_pre2022.geojson`, `confidence = medium`, and a note:
   "approximate — old assignment dissolved over current-vintage precinct shapes; N missing
   precincts left as edge gaps."

**taylorsville** and **west_jordan** already have `build_precinct_district_map.py` with a
documented prior-map invocation (`--years 2017,2021` and `--years 2019` respectively) — run
it, no new code. **sandy, south_jordan, millcreek** have no such script; either generalize
the shared tayl/wjd script to read the in-repo `<city>_results_by_precinct.csv` (the tay/wjd
scripts currently read an external `~/Desktop/slco-election-archive` copy, but the in-repo
by_precinct CSV carries identical year/district/precinct fields), or hand-dissolve in
geopandas. Note taylorsville's own `geo/CLAUDE.md` and `recon.md §5` already point at this
exact rebuild — the polygons simply were never generated and committed.

## The hard cases (Path B — external fetch)

- **provo (`plan_2012`)** — old assignment exists for **D2/D5** only (2021 PR## rows); D1/3/4
  had **no precinct SOVC published**. And PR## precinct codes were renumbered to 25PR## in
  2022 (0 geometry overlap; `geo/CLAUDE.md` confirms ~45→~65 precincts), so even D2/D5 can't
  dissolve from repo geometry. **Fetch target:** Utah County 2020-cycle precinct/VTD layer
  keyed to PR## (Utah County GIS historical precincts, or Census TIGER 2020 VTDs for Utah
  County), then dissolve the 2021 D2/D5 assignment; D1/3/4 remain unrecoverable without a
  pre-2022 precinct SOVC. Alternatively the 2012 redistricting ordinance map (Provo City
  Code §2.01.050) — a PDF image needing georeferencing (lossy). **Partly permanently
  unrecoverable (D1/3/4).**
- **ogden (`plan_2012`)** — **no pre-2022 by-precinct data on disk at all** (note: "no pre-2022
  Ogden precinct SOVC"); the only precinct rows are 2023/2025 in 29OG## codes that don't even
  match the current OGD## geometry. Path A has nothing to stand on. **Fetch target:** Weber
  County GIS historical precinct layer + a 2019/2021 precinct-level SOVC to derive the old
  assignment, then dissolve; OR the 2012-cycle redistricting map exhibit under Ogden Municipal
  Code Sec 1-7-2 (georeferencing required, lossy).

## Path C (prior redistricting ordinance exhibit) — in-repo check

No pre-2022 redistricting ordinance with a district-map exhibit is present in any city's
`ordinances/` or `pmn_backfill/` (only current-era/unrelated ordinance text + index files).
A recovered PDF map exhibit would in any case require georeferencing to become usable
geometry, so Path C is a distant fallback behind Paths A and B everywhere.

## Prioritized recommendation

1. **Quick repo-only wins — do now, no fetch (low → medium confidence):**
   - **west_jordan** — single year (2019), all 4 districts, 0 conflicts, 0 holes. Cleanest.
     Script already supports it (`--years 2019`).
   - **taylorsville** — script + prior-map recipe already documented (`--years 2017,2021`);
     1 conflict, 1 missing precinct. Its own docs already ask for this.
   - **south_jordan, sandy, millcreek** — equally clean data (0–1 conflict, **0 holes**) but
     need a small dissolve script (or a generalization of the tay/wjd tool). millcreek and
     sandy are the highest-value corrections because their `district_versions.csv` notes
     currently assert the prior map is "not reconstructable" / "no composition available" —
     **that is demonstrably wrong**: 46/46 and 76/76 old precinct codes carry geometry, and
     the old assignment differs from the current one on 39/46 (millcreek) precincts, i.e. a
     genuinely distinct prior map is recoverable.

2. **Partial repo now, optional fetch to firm up:**
   - **west_valley** (10-precinct / 13% holes) and **slc** (17-precinct / 14% holes, plus a
     real county precinct renumber). Reconstruct the approximate prior map from repo now
     (`medium`-`low`), leaving the missing precincts as honest edge gaps; optionally fetch the
     Salt Lake County 2020-vintage VistaBallotAreas layer to fill holes and validate the
     shared-code polygons before promoting confidence.

3. **External fetch, lowest certainty — schedule or close:**
   - **provo** (Utah County 2020 precinct layer + PR##→assignment for D2/D5; D1/3/4
     permanently unrecoverable) and **ogden** (Weber County historical precincts + a pre-2022
     SOVC, none on disk). Highest effort, partial ceilings. If not prioritized, keep the
     `low`/blank gap but correct the notes to "external-fetch required" rather than the
     current phrasing.

**Bottom line:** 5 of 9 cities (west_jordan, taylorsville, south_jordan, sandy, millcreek)
are repo-only reconstructable today with no fetch; 2 (west_valley, slc) are repo-
reconstructable but approximate with edge holes; 2 (provo, ogden) genuinely need a county
fetch and have partial ceilings. Several `district_versions.csv` notes overstate the gap and
should be revised alongside the reconstruction.

---
## STATUS UPDATE 2026-07-11 — 5 REPO-ONLY RECONSTRUCTIONS DONE (owner-approved scope)
Reconstructed the prior-plan district geometry + composition for the 5 clean cities via
`scripts/build_prior_district_map.py` (dissolve current precinct shapes by the pre-2022 assignment):
- **west_jordan** (D1–4, 68/68), **taylorsville** (D1–5, 38/39; TAY045 edge hole), **south_jordan**
  (D1–5, 49/49), **sandy** (D1–4, 76/76; SAN024 conflict→D3), **millcreek** (D1–4, 46/46; 2016 map).
- Each `<city>/geo/council_districts_pre2022.geojson` + `precinct_to_district_pre2022.csv` committed;
  wired into the driver via `roster_lib` `Redistrict.prior_geom_ref/prior_confidence` +
  `RosterConfig.prior_precinct_map_path` (a backward-compatible lib add). district_versions prior rows
  now `medium`+geometry; district_precincts prior rows POPULATED (medium). Federated: district_precinct
  733→988, district_version 22 medium / 20 low. council_terms BYTE-IDENTICAL (term still 370). All
  validate, 0 DISCREPANCY. **millcreek + sandy's factually-wrong "unrecoverable" notes corrected.**
- **STILL OPEN (documented gaps, per approved scope):** west_valley + slc (repo-partial, ~13–14% holes);
  provo + ogden (need a county/Census fetch — provo D1/3/4 likely permanently unrecoverable). Notes on
  those 4 cities' prior rows remain `low`/blank, honestly flagged.

## STATUS UPDATE 2026-07-19 — west_valley + slc REPO-PARTIAL RECONSTRUCTIONS DONE (7 of 9)
Reconstructed the two repo-partial cities via the same `scripts/build_prior_district_map.py` dissolve
(current precinct shapes × the pre-2022 assignment), accepting the renumbered-precinct holes as HONEST gaps:
- **west_valley** (`--years 2019,2021`): D1–D4, **64/74** old WVC codes present, **10 holes**
  (WVC068/070–074/076–079, mostly D2 SW corner — 6 of D2's 20), 1 conflict (WVC038 2019-D1/2021-D2→D2).
  All 4 `plan_pre2022` district_versions rows `medium`; 64 `district_precincts` rows populated `medium`.
- **slc** (`--years 2019,2021 --precincts geo/slco_precincts_current.geojson`): D1–D7, **107/124** codes
  present, **17 holes**, 2 conflicts (SLC055/SLC062 2019-D4/2021-D5→D5). **Holes highly UNEVEN:** D1–D5 = 0,
  D6 = 1 (SLC135), **D7 = 16/22** (renumbered SLC146–167 band) → D7's dissolved polygon is a 6-precinct
  FRAGMENT → **D7 `district_versions` row `confidence=low`** (D1–D6 `medium`); 107 `district_precincts`
  rows `medium` (D7 only 6). This drove a small BACKWARD-COMPATIBLE `roster_lib` add: `Redistrict.
  prior_confidence` now accepts a `{district_label: confidence}` dict (+ `prior_confidence_default` +
  `prior_note_by_district`) so per-district fidelity can be marked; verified the 5 scalar-string cities
  (wjd/tay/sjd/sandy/millcreek) emit **byte-identical** `district_versions`/`district_precincts`.
- **Better-source probe:** attempted the SL County **2020-vintage VistaBallotAreas** layer to firm up the
  holes (esp. slc D7). UGRC/SLCo publish only the CURRENT vintage of VistaBallotAreas as an open layer
  (already on disk); no simple open FeatureServer exposes a 2020 snapshot with the retired precinct codes.
  → used the sanctioned current-shape fallback; holes left as honest gaps, the 2020-layer firm-up still open.
- Both: build+validate PASS, idempotent (geo + roster outputs byte-identical on re-run), `validate_city.py`
  **0 FAIL**. Stale "NOT reconstructable" notes corrected in both cities' `roster/CLAUDE.md` + `geo/CLAUDE.md`.
- **STILL OPEN:** provo + ogden (external county/Census fetch; provo D1/3/4 likely permanently unrecoverable);
  slc D7 + the ~10–17 holes per city could be firmed up with the SL County 2020 VistaBallotAreas layer.

## STATUS UPDATE 2026-07-19 — MILLCREEK plan_2016 PROMOTED medium→HIGH (AUTHORITATIVE fetch)
The one OPEN half of the millcreek geo TODO — the AUTHORITATIVE (exact) 2016-incorporation
boundary vintage — is now **SOURCED and acquired**. It was NOT a dead external gap: Millcreek's
own city GIS org (`services9.arcgis.com/XRrSFvEwSsReIxuA`, the SAME org that serves the current
2022-2032 layer) publishes **`CityCouncilDistricts` FeatureServer layer 0**, explicitly named
**"City Council District Boundaries 2017-2022"** — 4 exact district polygons, `DIST`=District 1..4,
`DistrictRep` carrying the pre-2022 members (incl. **Dwight Marchant D2**, who left office Jan 2022 →
vintage confirmed). Fetched with `outSR=4326` (native SR was 3566 Utah State Plane) into
`millcreek_city_council/geo/council_districts_pre2022.geojson` (repo convention, property
`district`="1".."4" + `DIST`/`Representative`/`source_url`/`fetched` provenance).
- **`district_versions.plan_2016` D1–D4 → `confidence=high`** with the layer as `source_url`
  (via a new backward-compatible `Redistrict.prior_source_url`; every other city defaults to "" →
  byte-identical, verified across tayl/sandy/sjd/wjd/slc/wvc, incl. slc's per-district dict path).
- **The 2026-07-11 precinct-dissolve reconstruction was MATERIALLY WRONG**, not merely approximate:
  per-district IoU vs this authoritative layer ≈ **0.00–0.25** (D1 = 0.000; no clean label permutation),
  because the `MIL###` precinct CODES were **renumbered/reshaped** between 2019 and the current 2025 UGRC
  precinct vintage — a centroid-in-authoritative-polygon test disagrees with the 2019 SOVC assignment on
  **36/44** codes. So dissolving current precinct shapes by the old SOVC labels painted the wrong geography.
  This is the general risk the vintage caveat flagged, here realized at full severity — a caution for the
  other cities' repo-dissolve prior maps (esp. where precincts were renumbered).
- Authoritative layer vs the CURRENT 2022-2032 plan: per-district IoU **0.58–0.92** (2022 redistricting most
  reshaped D3/D4), city-extent IoU 0.983 → genuinely the distinct prior vintage.
- The `plan_2016` **precinct-CODE composition** (`district_precincts`, 46 rows) stays **medium** — it is the
  honest SOVC record of which OLD code voted in which district contest, NOT geographically joinable to current
  precinct shapes; kept separate from the now-authoritative boundary geometry. NOT degraded.
- ⚠ **Do NOT rerun `scripts/build_prior_district_map.py --city millcreek_city_council`** — it would overwrite
  the authoritative fetch with the discredited reconstruction. Raw fetch + layer metadata archived under
  `_backups/2026-07-19-lm-wave/geo/millcreek/`.
- Validation: `roster/build_roster.py --check` clean; `scripts/validate_city.py millcreek_city_council/`
  **26 PASS / 0 FAIL**; roster + geojson rebuilds byte-identical (idempotent). (west_valley + slc holes and
  provo/ogden external fetches remain the OPEN items for the OTHER cities.)

## STATUS UPDATE 2026-07-19 — 6 SLCo CITIES' pre-2022 RECONSTRUCTIONS VALIDATED → ALL DOWNGRADED medium→low (LM-wave follow-up)
Applied the millcreek validation method (find the city's OWN authoritative GIS; IoU / fragmentation /
centroid tests) to the six repo-dissolve reconstructions: **west_jordan, taylorsville, south_jordan,
sandy, west_valley, slc**. Backups `_backups/2026-07-19-lm-wave-followups/geo/` (incl. the authoritative
fetches under `_authoritative_fetches/`).

**Authoritative-layer probe — NONE of the six publishes a true pre-2022 boundary layer** (unlike
millcreek's "City Council District Boundaries 2017-2022"). Every layer found is the CURRENT 2022 plan:
- **south_jordan**: `gis2.southjordanutah.gov` Voting/CouncilDistricts **"FinalApproved"** (desc "established
  2012") **== Voting/Voting "Council Districts 2020"** (IoU 1.000, both carry 2020-census FIPS) — both are the
  CURRENT plan: centroid-agree 68/68 (100%) with the current assignment, 15/49 (31%) with pre-2022. The
  "established 2012" text is stale metadata, not a 2012-vintage layer.
- **sandy**: `gis.sandy.utah.gov` Common/City_Council_Districts — CURRENT (current members Christensen/Stroud/
  Nicholl/Houseman); 110/110 (100%) current vs 21/76 (28%) pre-2022. Common + Historic folders have no prior.
- **west_jordan**: org `yznraL2FyB2Sm732` has Council_Districts / Council_Districts_22 / WJC_Council_2025 — all
  CURRENT 2022+ (87-99% current vs 59-69% pre-2022).
- **slc**: org `mMBpeYj0vPFotzbe` Salt_Lake_City_Council_Districts + legacy City_Council_Boundries — both the
  CURRENT 2022 plan (IoU 0.995, 2022-era members Puy/Petro).
- **west_valley**: AGOL org `VuwCBhloG26S6mpc` = City Boundary only; SLCo-hosted WVC D1/D3/At_Large services =
  CURRENT only. **taylorsville**: publishes NO council-district GIS at all (confirmed — recon §6).

**Renumbering PROVEN via a fragmentation control** (the decisive test, needs no prior layer): dissolving
CURRENT precinct shapes by the CURRENT precinct→district assignment (known-good, ~100% vs authoritative)
yields CLEAN **1-2-piece** districts for every city; the pre-2022 dissolve (old codes on current shapes)
yields **3-15-piece FRAGMENTS**:

| City | current-dissolve pieces (control) | pre-2022 recon pieces | current-vs-pre2022 centroid agree | recon-vs-current IoU |
|---|---|---|---|---|
| west_jordan | 1,1,2,1 | 4,4,3,5 | 59-69% | 0.360 |
| taylorsville | 1,1,1,1,1 | 3,1,4,1,4 | (no city layer) | — |
| south_jordan | 1,1,1,1,1 | 2,2,7,5,5 | 31% | 0.155 |
| sandy | 1,2,1,2 | 9,8,10,13 | 28% | 0.114 |
| west_valley | 2,1,1,1 | 4,8,2,5 | (partial layer) | — |
| slc | 1×7 | 2,6,3,7,9,15,4 | 38% | 0.175 |

The current dissolve is clean everywhere → 3-15-piece pre-2022 fragments can ONLY come from old precinct
CODES having been renumbered to different geography between the SOVC vintage and the current UGRC precinct
layer — the SAME defect that made millcreek's dissolve materially wrong (IoU 0.00-0.25). Severity: SEVERE
in sandy/south_jordan/slc/west_valley, moderate in west_jordan (codes partially stable), mild in
taylorsville (D2/D4 clean). The centroid agreements (28-38% ≈ random for 4-7 districts) corroborate.

**ACTION — all six pre-2022 GEOMETRY rows DOWNGRADED medium→low** in each driver (`prior_confidence`,
slc's per-district dict → all low), with the finding cited in the `district_versions` note. **The
`district_precincts` precinct-CODE composition stays `medium`** (following the millcreek principle: which
OLD code voted in which district contest is a faithful SOVC record, geometry-independent, NOT degraded).
No REPLACE was possible (no authoritative prior layer exists); the reconstructed geojson is KEPT as the
best-available approximate artifact, now honestly labeled `low`. NB: `representatives_for_address` already
returns an honest GAP for pre-2022 dates regardless of this geometry, so the downgrade has no query impact.

**Gates:** all 6 regenerate + `--check` PASS + idempotent (byte-identical re-run); `council_terms`
BYTE-IDENTICAL (no tenure impact); `district_precincts` composition unchanged (still medium);
`scripts/validate_city.py` **0 FAIL** for all 6 (23/25/23/21/26/24 PASS). **STILL OPEN:** the true pre-2022
geometry for these six is genuinely unrecovered (would need a 2019/2020-vintage SLCo VistaBallotAreas
snapshot with the retired codes, or a georeferenced 2012 ordinance map exhibit) — same as provo/ogden.

## STATUS UPDATE 2026-07-19 — CONFIDENCE-GATED prior-plan address→rep resolution (query-path, roster_lib)
`roster_lib.representatives_for_address` now RESOLVES a prior-plan-dated query by point-in-polygon
against the prior plan's own geojson — but **only when the plan_old `district_versions` row for the
HIT district carries a non-blank `geometry_ref` AND `confidence` high/medium**. The gate is
**data-driven from the written `district_versions.csv`** (never config prose), and **per-district**:
a `low` district NEVER resolves even when its neighbors could (exercised by test — a forced-low hit
district returns the gap while its high neighbors would have resolved). This supersedes the NB in the
previous section ("the downgrade has no query impact"): the downgrade now IS the query gate.
- **Resolution provenance:** a resolved prior-plan hit carries `plan_provenance` = {plan_id,
  district_id, geometry_confidence, geometry_ref, source_url, adopted_by} from the district_versions
  row, so downstream output can cite the geometry honestly.
- **Gap behavior:** blank-geometry plans (provo/ogden) keep the ORIGINAL "boundaries not acquired"
  message verbatim; low-confidence geometry (the six downgraded SLCo reconstructions) returns a new
  explanatory gap — "…prior-plan geometry is low-confidence (approximate reconstruction — see
  district_versions note) — not resolved (honest gap)" — never a resolution.
- **Today exactly ONE city qualifies: millcreek** (plan_2016 = `high`, the authoritative city-GIS
  "City Council District Boundaries 2017-2022" layer). Verified: 3330 S 1300 E (City Hall) on
  2021-06-01 → plan_2016 D2 → **Dwight Marchant + Mayor Silvestrini** (cross-checked three ways:
  the authoritative layer's own `Representative` field = Dwight Marchant on the hit polygon;
  `council_terms` D2 [2018-01-08, 2022-01-10) = Marchant; and a prior≠current divergence point
  (40.668, -111.86: plan_2016 D1 / plan_2022 D2) resolves to a DIFFERENT district per date,
  proving the prior map itself is read). The plan_2016 `district_precincts` composition is NOT used
  (not geographically joinable — see the millcreek promotion note above); resolution is pure PiP
  against the authoritative polygons.
- **Mechanics:** pure-python even-odd ray-cast PiP (no geopandas dependency); coordinates from the
  city geo tool's Census geocoder, else the caller's stated latlon. Implementation + docstring in
  `scripts/roster_lib.py` (`_point_in_geojson_geom`, `_latlon_for_address`, `_prior_plan_district`).
- **Back-compat proven:** current-plan behavior byte-identical (unchanged code path); at-large
  (nephi) unchanged; blank-geometry gap string asserted equal to the original formula output.
  Build path untouched — sandy/nephi/slc rosters regenerate BYTE-IDENTICAL under the new lib, and a
  control rebuild of millcreek with the BACKED-UP old lib produced bytes identical to the new lib's.
  (millcreek's `council_terms.csv` did change on regeneration, from BOTH libs equally — input-data
  currency only: the 2026-07-19 recovered 2017 en-dash roll calls moved the founders' `first_vote`
  to 2017-02-27, and the same-day q3 refresh advanced serving rows' `last_vote` to 2026-06-22;
  re-federation into cities.db `term` is queued with the roster-refresh flow.)
