# utah_county / gis — sources & provenance (CATALOG, don't mirror)

**Policy (owner decision): this module CATALOGS GIS layers — it does NOT mirror bulk
geodata.** Parcels, address points, housing inventory, and building footprints are
190k-330k features and are GB-scale as shapefiles. We record, per layer, the metadata +
a live queryable **ArcGIS REST endpoint** + vintage + license (`index.csv`) so an LLM app
can query them on demand. We do NOT download the full layers into the repo. The only
files stored are tiny already-summarized tables under `derived/` (see its `PROVENANCE.md`).

Everything in `index.csv` was verified live against the endpoint on **2026-07-20**
(service exists, returns metadata, feature counts sampled). No layer was catalogued
unseen. 23 layers: 13 from UGRC/SGID (filtered to Utah County FIPS 49049), 10 from the
Utah County GIS hosted org.

## Portals

### 1. UGRC / Utah SGID — statewide authoritative
- Human portal: <https://opendata.gis.utah.gov/> and <https://gis.utah.gov/> (product
  pages under `/products/sgid/`).
- REST org: `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services`
  (~870 services; we curated the Utah-County-relevant growth/housing/development ones).
- Access: open ArcGIS FeatureServers. `?f=json` for metadata; `/<id>/query?where=...&f=geojson`
  for data; `supportedExportFormats` include csv, shapefile, geoPackage, geojson, kml, excel.
- License: **CC BY 4.0** for SGID datasets; Census-derived layers are US Census public domain.
- **Utah County parcels** are the county-specific `Parcels_Utah` / `Parcels_Utah_LIR`
  services (COUNTY_NAME='Utah County', 327,655 LIR records, CURRENT_ASOF 2025-10-30,
  updated monthly). Building footprints, housing unit inventory, address points, municipal
  boundaries, census geographies, and opportunity/enterprise zones are statewide services
  filtered to Utah County by their county field.

### 2. Utah County GIS — its own hosted org
- Human portal / ArcGIS Hub: <https://utah-county-gis-maps-and-data-utahcounty.hub.arcgis.com/>.
- **Hosted feature layers (ArcGIS Online org `utahcounty`, id `9DapJHuwsEakbYuW`):**
  `https://services1.arcgis.com/9DapJHuwsEakbYuW/arcgis/rest/services` — 249 services,
  **most are elections/redistricting, mosquito-abatement, parks/trails, geologic-hazard,
  survey123, or test/analysis layers.** We catalogued only the durable, populated,
  growth-relevant ones: municipal boundaries, city points, plat blocks/lots, RDA/CDA
  project areas, county roads, PLSS townships/sections, and the 2050 Travel Demand Model.
- License: Utah County publishes these publicly with **no explicit license stated**;
  treat as open public data and attribute "Utah County GIS."
- **The authoritative published server `https://maps.utahcounty.gov/arcgis/rest/services`
  is 401-locked** to the public (it backs the ParcelMap / ParcelViewer apps at
  `maps.utahcounty.gov/ParcelMap/`). Bulk data is offered only through a separate
  downloads portal, <https://is.utahcounty.gov/gis/downloads>. Because the REST root does
  not resolve unauthenticated, **it is not catalogued as a live endpoint** — the public
  parcel/LIR data is instead reached via UGRC's `Parcels_Utah_LIR` (catalogued).

## Structural facts (not gaps)

- **No county-commission-district GIS layer** because Utah County is governed by a
  **3-member County Commission elected AT-LARGE** (contrast SLCo's 9-member Council with
  district boundaries). The hosted-org layers named "West/Central/South District
  Boundary" are **school-district** boundaries (`SCHLDSCRP` = "West"/"Central"/
  "Timpanogos") — NOT commission districts — and are deliberately NOT catalogued as such.
- **Unincorporated land** (the County Planning Commission's jurisdiction) has no dedicated
  parcels layer; derive it by differencing `UtahMunicipalBoundaries` from the county
  boundary, or filter parcels by `PARCEL_CITY`.

## Honest gaps (layer types not found for Utah County)

- **No county-wide ZONING layer.** SGID's `planning_generalized_zoning` returns **0
  polygons in Utah County** (301 statewide; `county` field never = UTAH), and Utah County
  publishes no harmonized countywide zoning feature service (unlike SLCo's `Zones` layer).
  Authoritative zoning lives with each **municipality** and (for unincorporated land) in
  the county's own ordinances (handled in `utah_county/ordinances/` and the per-city
  repos), not here.
- **No GENERAL PLAN / FUTURE-LAND-USE GIS layer.** The Utah County General Plan is
  published as an ArcGIS **StoryMap**, not a queryable feature service — so it is not
  catalogued (a StoryMap is narrative, not data). The county's `Redevelopment_new` is
  current RDA/CDA project areas, not future land use.
- **No harmonized SUBDIVISION-boundary layer** and **no live subdivision/development-
  application feature service.** The closest county-hosted proxies are the recorded plat
  `City_Lots` (7,852) and `City_Blocks` (1,240) — recorded-plat geometry, catalogued as
  such. A legacy web form (`utahcounty.gov/LandRecords/DevelopmentSearchForm.asp`) and an
  "Annexation Plat Search" web app exist but expose no REST layer.
- **No ANNEXATIONS feature service** in the open org (only a web-app search tool).
- **No county BUILDING-FOOTPRINTS layer** in the Utah County org — UGRC's statewide
  `Buildings` (191,853 in Utah County) is catalogued in its place.
- **TAZ / travel-demand & long-range land-use projections:** the county's own 2050
  `Travel_Demand_Model_Results` is catalogued; broader WFRC/MAG regional projection
  portals are separate and not catalogued here (future add if projection questions arise).
- Bulk downloads are deliberately **absent** — this is the catalog policy, not a gap.
- Endpoints can move (ArcGIS org migrations); re-verify `?f=json` before relying on any
  URL. UGRC `services1.arcgis.com/99lidPhWCzftIe9K` is the most stable host.
