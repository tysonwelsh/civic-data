# mag_mpo / projects — sources & provenance

Attribute-only federation of the **Mountainland Association of Governments (MAG)**
transportation project lists into the repo's shared cross-MPO `projects.csv` schema
(shared with the `wfrc_mpo` agent). **No geometry is mirrored** — each row is the
project's attributes; the geometry stays live at the ArcGIS endpoint. Raw JSON snapshots
of every source layer are in `raw/`. Nothing here is modeled or fabricated; blanks are
honest source blanks (never 0).

## Source portal

MAG ArcGIS Hub — **`data.magutah.gov`** (formerly `data.mountainland.org`), hosted org
`services2.arcgis.com/EiGeaCDLpVDPqdJ5`. DCAT catalog:
<https://data.magutah.gov/api/feed/dcat-us/1.1.json>. Public, no auth. Every layer was
byte-verified live 2026-07-20 (feature counts confirmed via `?returnCountOnly=true`).

## The three plans (`plan_kind`)

| plan_kind | source layers | `plan_vintage` | rows |
|---|---|---|---|
| `tip` | `MAG_TIP_Projects` (FeatureServer/0) | `MAG TIP (UDOT ePM snapshot 2026-07-01)` | 225 |
| `rtp` | 2023 RTP Highway / Transit / Active-Transportation, points **and** lines | see below | 262 |
| `rpo` | `Wasatch_Back_RPO_2023_Projects` points + lines | `Wasatch Back RPO 2023 Plan` | 84 |

**TIP.** Item snippet: *"a snapshot of Transportation Improvement Program (TIP) projects
obtained from UDOT's ePM database on 7/1/2026."* Project type (`PROJ_TYP_NM`) → `improvement_type`;
`mode` left blank (the source does not cleanly separate mode from project category).
`STIP_SPONSOR_CD` (UDOT / MAG) → `jurisdiction`; `FORECAST_ST_YR` → `phase_or_year`
(range 2012–2031, concentrated 2024–2029); `PROJECT_VALUE` → `cost`;
`PIN_STATUS_PHASE_DESC` (Design/Construction/STIP/Advertising/Awarded) → `status`. TIP has
no county field → `county` blank.

**RTP** = adopted **2023 Regional Transportation Plan** (adopted May 2023). Vintage is
recorded **per mode** because the amendments differ — vintages are never blended:
- Highway → `MAG 2023 RTP (Amendment 3, 2025-12-11)`
- Transit → `MAG 2023 RTP (Amendment 1, 2025-01-16)`
- Active Transportation → `MAG 2023 RTP (Amendment 1, 2025-01-16)`

`unique_id` → `project_id`; native `mode` / `improvement_type` / `jurisdiction` / `county` /
`phase` (1 | 2 | 3 | Unfunded → `phase_or_year`) / `cost` / `description` carried verbatim.

**Wasatch Back RPO** (Summit + Wasatch rural RPO). `ProjNum` → `project_id`
(scoped by `mode`=`ProjType`, so Highway-1 / Transit-1 / Active-1 are distinct rows);
`ProjName`→`name`, `ProjType`→`mode`, `ProjFacOwn`→`jurisdiction`, `Phase`→`phase_or_year`,
`ProjDesc`→`description`. No cost or county fields published → both blank.

## De-duplication (IMPORTANT — cost is never summed)

Points and lines are two GEOMETRY representations of the **same** project (a corridor line
plus its grade-separated crossing points, or alternative alignments). Since only attributes
are stored, rows are **de-duplicated to one per `project_id`** (RTP `unique_id`; RPO
`(ProjType,ProjNum)`), **lines taken as primary** (the line row carries the corridor name +
full description). Verified: `cost` is a **project-level total stated identically on every
geometry variant** of a `unique_id` (e.g. RTP `M-U-2023-A-69` shows cost 4,960,000 on the
line and on all five crossing points) — so collapsing to one row is required to avoid a
massive cost double-count. 19 RTP ids had geometry variants with a differing `name`/
`improvement_type`; the line (corridor) value was kept. Final key
`(plan_kind, mode, project_id)` is unique (0 collisions). RTP by mode: Highway 113,
Transit 16, Active 133. RPO by mode: Highway 61, Transit 4, Active 19.

## Files

- `projects.csv` — 571 rows (tip 225 / rtp 262 / rpo 84), shared 15-col schema.
- `raw/*.json` — verbatim ArcGIS `query` responses (attributes, `returnGeometry=false`) for
  all 9 source layers, retrieved 2026-07-20. Small (<110 KB each) so retained in-repo.

## Honest gaps

- TIP carries no county attribute (blank, not inferred).
- Wasatch Back RPO publishes no cost or county (blank).
- `cost` blank on 105 rows = source blank (unfunded/未priced), never 0.
- The RTP `points`/`lines` split is geometry only; no attribute-unique project is lost in
  de-dup (each `unique_id` retained once).
