# cache_county / gis — a CATALOG of growth/development GIS layers (link, don't mirror)

**This module is a catalog + live-endpoint index, NOT mirrored bulk geodata.** Parcels,
zoning, subdivisions, and footprints are tens of thousands of features each. By repo
policy we store their **metadata + queryable ArcGIS REST endpoint + relevance** in
`index.csv` and let an app query them live. The only stored data are tiny derived
summaries in `derived/`. Never download a full layer into this repo.

## Files

- `index.csv` — **the catalog**, 24 growth/housing/development GIS layers for Cache
  County. Columns: `layer, description, publisher, url, api_endpoint, format, vintage,
  license, growth_relevance, notes`. `api_endpoint` is the live ArcGIS layer URL.
- `SOURCES.md` — the portals, how to query, licenses, and honest gaps.
- `derived/` — small already-summarized tables only
  (`cache_county_base_zoning_counts.csv`); see `derived/PROVENANCE.md`.

## Two publishers

1. **Cache County** (`gis.cachecounty.gov/arcgis/rest/services`, ArcGIS Server v10.91;
   open-data portal `gis-cacheut.opendata.arcgis.com`; Parcel & Zoning Viewer at
   `gis.cachecounty.gov`) — the county-distinct layers: **County Zoning** (base +
   overlay), **Future Land Use**, **Subdivisions** (2,794), **Annexation History** (611),
   **Historical Zoning / Rezones**, **Land-Use Project Polygons** (1,367), building
   footprints (69,306), floodplain / sensitive-area / airport overlays, sand-and-gravel,
   assessor parcels, voting districts. **No explicit open license is posted** — verify
   reuse terms with the county.
2. **UGRC / Utah SGID** (`services1.arcgis.com/99lidPhWCzftIe9K`, CC BY 4.0) — statewide
   authoritative: **Cache parcels (LIR, ~73,655** with assessor value/year-built/acreage —
   the housing base layer), parcel geometry (~60,227), address points, municipal
   boundaries.

## How to use the endpoints

Every `api_endpoint` is a standard ArcGIS REST layer. Do NOT bulk-fetch — query narrowly:

- Metadata / fields: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (cheap): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- Geometry as GeoJSON: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson` (FeatureServer)
- Spatial filter: `&geometry=<xmin>,<ymin>,<xmax>,<ymax>&geometryType=esriGeometryEnvelope&inSR=4326`
- Distinct values: `&outFields=<f>&returnDistinctValues=true&returnGeometry=false`

Note: **MapServer** layers (most county layers) support draw/query but not always
`outStatistics` groupBy (the base-zoning layer 500s on groupBy — page or per-value count
instead, as `derived/PROVENANCE.md` does). **FeatureServer** layers (Subdivisions,
Annexation_History, Buildings, UGRC parcels, Voting) support geojson/csv export by query.

## Growth relevance (what to reach for)

- **Zoning composition / where you can build what** → county `Planning/Zoning` sublayer 1
  (Base Districts) + sublayer 0 (Overlays); `Future_Land_Use` for the plan vision. Cache's
  8 base districts (A10, FR40, RU2, RU5, RR, C, I, CITY) are in
  `derived/cache_county_base_zoning_counts.csv` — unincorporated land is mostly A10
  (Agricultural 10-acre) + FR40 (Forest Recreation).
- **Development / subdivision growth record** → `Subdivisions`, `LUProjectsPolys` (the
  spatial development-application proxy — the county has no tabular dev-app log),
  `Rezones_Historical`, `Zoning_Historical`.
- **Jurisdiction / annexation** → `Annexation_History`, UGRC `UtahMunicipalBoundaries`
  (city vs unincorporated = the land the COUNTY plans).
- **Land value / who owns what / built year** → UGRC `Parcels_Cache_LIR` (assessor
  attributes) or the county `Assessor` parcel service; `PZ_New/YearBuilt`.
- **Development constraints** → `Floodplain`, `Sensitive_Area_Planning`,
  `Airport_Overlays`, `Sand_and_Gravel` (recurring PC contested topics).
- **Representation ↔ geography** → county `Voting/Voting_Information`.

## Cardinal rules here

- **Catalog, don't mirror.** Never commit bulk layer downloads. Only tiny `derived/`
  summaries, each with provenance and a reproduce query.
- **Verify before quoting.** Re-check `?f=json` before relying on an endpoint; ArcGIS orgs
  migrate. `gis.cachecounty.gov/arcgis` is the stable county host.
- **Don't fabricate coverage.** UGRC `HousingUnitInventory` has **no Cache rows**
  (`COUNTY='CACHE'` → 0 on 2026-07-20) so it is NOT catalogued — see `SOURCES.md` gaps.
