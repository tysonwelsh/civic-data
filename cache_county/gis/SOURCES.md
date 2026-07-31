# cache_county / gis — SOURCES & provenance

## Portals (2 publishers, verified live 2026-07-20)

1. **Cache County GIS**
   - ArcGIS Server REST: `https://gis.cachecounty.gov/arcgis/rest/services` (v10.91).
     Growth-relevant folders: `Planning` (zoning, future land use, subdivisions,
     annexations, rezones, floodplain, sensitive areas, airport overlays, buildings,
     sand & gravel), `PZ_New` (LU project polygons, year-built), `Assessor` (parcels +
     assessor analysis), `Cadastral`, `Voting`.
   - Open-data portal (ArcGIS Hub): `https://gis-cacheut.opendata.arcgis.com` — browse /
     download / export the county layers (csv/geojson/shp).
   - Parcel & Zoning Viewer + GIS home: `https://gis.cachecounty.gov`,
     `https://www.cachecounty.gov/gis/`.
   - **License:** no explicit open-data license is posted on the county services; treat as
     public records and verify reuse terms with Cache County before redistribution.
2. **UGRC / Utah SGID** — `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services`
   (hosted) and `https://gis.utah.gov/products/`. **License: CC BY 4.0.** Cache-relevant:
   `Parcels_Cache_LIR` (~73,655, assessor attributes), `Parcels_Cache` (~60,227 geometry),
   `UtahAddressPoints` (~1.49M statewide, filter to Cache), `UtahMunicipalBoundaries`.

## Method

Enumerated the county ArcGIS server folder tree, verified endpoint counts for the key
growth layers (Subdivisions 2,794; Annexation_History 611; Buildings 69,306; Future Land
Use 20; LUProjectsPolys 1,367), and confirmed the UGRC Cache parcel/address/municipal
layers. Built `index.csv` (24 layers) and one `derived/` zoning-composition summary.
Nothing bulk was downloaded — only counts and one small aggregate.

## Honest gaps / notes

- **UGRC `HousingUnitInventory` has no Cache data** (`COUNTY='CACHE'` → 0 features on
  2026-07-20) — **not catalogued** (would be a false coverage claim). The per-parcel
  housing-type inventory SLCo has is absent for Cache; use `Parcels_Cache_LIR` +
  `PZ_New/YearBuilt` + `Planning/Buildings` for housing/growth analysis instead.
- The base-zoning layer (`Planning/Zoning` MapServer/1) **500s on `outStatistics`
  groupBy**; the derived zoning summary was built with per-value `returnCountOnly` queries
  (see `derived/PROVENANCE.md`).
- `Assessor/Parcels_Current_Assessor_Parcel_Analysis_Solution` MapServer/0 rejected a bare
  count query (needs a valid sublayer/param); catalogued as the service (enumerate
  sublayers via `?f=json`) — for a clean queryable parcel-attribute layer prefer the UGRC
  `Parcels_Cache_LIR` row.
- County layers carry **no explicit open license** — flagged in every county row's
  `license` field.
- This is a **catalog**, not a mirror; endpoints are live and may change. Re-verify
  `?f=json` before quoting.
