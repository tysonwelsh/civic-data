# utah_county / gis — a CATALOG of growth/development GIS layers (link, don't mirror)

**This module is a catalog + live-endpoint index, NOT mirrored bulk geodata.** Parcels,
address points, housing inventory, and building footprints are 190k-330k features each
(GB-scale as files). By owner decision we store their **metadata + queryable ArcGIS REST
endpoint + vintage + license** in `index.csv` and let an app query them live. The only
stored data are tiny derived summaries in `derived/`. Never download a full layer into
this repo.

Modeled on `salt_lake_county/gis/` — same schema and conventions — but Utah County's own
open GIS org publishes far fewer growth layers than SLCo's, so the catalog leans harder on
UGRC/SGID statewide layers filtered to Utah County (FIPS 49049). See `SOURCES.md` for the
honest gaps (no county-wide zoning, general-plan, subdivision, or annexation feature
service is published open).

## Files

- `index.csv` — **the catalog.** 23 verified growth/housing/development GIS layers for
  Utah County. Columns: `layer, description, publisher, url, api_endpoint, format,
  vintage, license, growth_relevance, notes`. `api_endpoint` is the live ArcGIS
  FeatureServer layer URL — queryable directly. All verified live 2026-07-20.
- `SOURCES.md` — the portals, how to access them, licenses, and honest gaps.
- `derived/` — small already-summarized tables only
  (`utahco_housing_unit_inventory_by_type.csv`); see `derived/PROVENANCE.md`.

## Two publishers

1. **UGRC / Utah SGID** (`services1.arcgis.com/99lidPhWCzftIe9K`, CC BY 4.0) — statewide
   authoritative, filtered to Utah County: the **Utah County parcels (LIR, with
   assessor value/built-year/units — the housing base layer)** and geometry variant,
   address points, municipal/county boundaries, **housing unit inventory**, **building
   footprints**, census geographies, opportunity/enterprise zones, water-related land
   use. These carry a county field (`COUNTY`/`COUNTYNBR`/`CountyID='49049'`/`GEOID20`
   prefix `49049`) — filter, never bulk-fetch.
2. **Utah County GIS** (ArcGIS Online org `9DapJHuwsEakbYuW`, hosted at
   `services1.arcgis.com/9DapJHuwsEakbYuW`) — county-published: municipal boundaries,
   city points, plat **city blocks / city lots**, **Redevelopment / CDA project areas**,
   county roads, PLSS townships/sections, and the **2050 Travel Demand Model** roadway
   results. Public open data, no explicit license — attribute "Utah County GIS."

> The authoritative county server `maps.utahcounty.gov/arcgis` (behind the ParcelMap /
> ParcelViewer apps) is **401-locked** to the public — its bulk data is offered only via
> `https://is.utahcounty.gov/gis/downloads`. It is NOT catalogued as a live REST endpoint
> because it does not resolve unauthenticated. Everything in `index.csv` is a public,
> unauthenticated, live endpoint.

## How to use the endpoints

Every `api_endpoint` is a standard ArcGIS REST layer. Do NOT bulk-fetch — query narrowly:

- Metadata / fields: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (no geometry, cheap): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- Geometry as GeoJSON: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson`
- Spatial filter: add `&geometry=<xmin>,<ymin>,<xmax>,<ymax>&geometryType=esriGeometryEnvelope&inSR=4326`
- Group-by summary (like the derived file): `&outStatistics=[...]&groupByFieldsForStatistics=<field>`
- Paging: `maxRecordCount` is ~2000; page with `resultOffset` / `resultRecordCount`.

Filter statewide SGID layers to Utah County by the county field: parcels are already
Utah-County-only; `HousingUnitInventory`/`Buildings`/`WaterRelatedLandUse` use
`COUNTY='UTAH'`; `UtahMunicipalBoundaries` uses `COUNTYNBR='25'`; `UtahAddressPoints` uses
`CountyID='49049'`; census/OZ layers use a `49049`/`049` FIPS prefix.

## Growth relevance (what to reach for)

- **Housing supply / type / density** -> UGRC `HousingUnitInventory` (per-development unit
  type/count/density; see `derived/`) + `Buildings` (footprints) + `Redevelopment_new`
  (CDA/tax-increment project areas).
- **Land value / build-out / who owns what** -> UGRC `Parcels_Utah_LIR` (assessor
  attributes: TOTAL_MKT_VALUE, BUILT_YR, HOUSE_CNT, PROP_CLASS, SUBDIV_NAME).
- **Platted / subdivided land** -> Utah County `City_Lots` + `City_Blocks` (recorded plat
  fabric). NOTE: this is recorded-plat geometry, NOT a live subdivision-application layer
  and NOT a harmonized subdivision-boundary layer (the county publishes neither openly).
- **Jurisdiction / boundary questions** -> UGRC `UtahMunicipalBoundaries` (carries
  population) or Utah County `City_Boundaries`. Unincorporated land = the county
  Planning Commission's jurisdiction; derive it by differencing municipal boundaries from
  the county boundary (no dedicated unincorporated-parcels layer is published — see
  `SOURCES.md`).
- **Development-incentive geography** -> `Redevelopment_new` (RDA/CDA project areas) +
  `Eligible_Opportunity_Zones` + `EnterpriseZones`.
- **Future roadway loading / growth pressure** -> `Travel_Demand_Model_Results` (2050
  build vs no-build volumes/LOS) — the closest county-published growth-projection layer.
- **Representation <-> geography** -> NONE published. Utah County is governed by a
  **3-member County Commission elected AT-LARGE**, so there is no commission-district GIS
  layer (an honest structural fact, not a gap). See `SOURCES.md`.

## Cardinal rules here

- **Catalog, don't mirror.** Never commit bulk layer downloads. Only tiny `derived/`
  summaries, each with provenance and a reproduce query.
- **Verify before quoting.** Re-check `?f=json` before relying on an endpoint; ArcGIS
  orgs migrate. UGRC `services1.arcgis.com/99lidPhWCzftIe9K` is the most stable; the Utah
  County hosted org (`9DapJHuwsEakbYuW`) mixes durable layers with survey/test/mosquito
  layers — only the growth-relevant, populated, durable ones are catalogued.
- **Don't fabricate coverage.** SGID's `planning_generalized_zoning` has **0 polygons in
  Utah County** (301 statewide) — NOT catalogued. Layer types Utah County does not
  publish openly (zoning, general-plan/future-land-use, subdivision boundaries,
  annexations, unincorporated-parcels) are recorded as honest gaps in `SOURCES.md`, never
  invented.
