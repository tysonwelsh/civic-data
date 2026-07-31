# salt_lake_county / gis — a CATALOG of growth/development GIS layers (link, don't mirror)

**This module is a catalog + live-endpoint index, NOT mirrored bulk geodata.** Parcels,
zoning, address points, and footprints are 100k-700k features each (GB-scale as files).
By owner decision we store their **metadata + queryable ArcGIS REST endpoint + vintage +
license** in `index.csv` and let an app query them live. The only stored data are tiny
derived summaries in `derived/`. Never download a full layer into this repo.

## Files

- `index.csv` — **the catalog.** 34 verified growth/housing/development GIS layers for
  Salt Lake County. Columns: `layer, description, publisher, url, api_endpoint, format,
  vintage, license, growth_relevance, notes`. `api_endpoint` is the live ArcGIS
  FeatureServer/MapServer layer URL — queryable directly.
- `SOURCES.md` — the two portals, how to access them, licenses, and honest gaps.
- `derived/` — small already-summarized tables only (`slco_zoning_polygon_counts.csv`);
  see `derived/PROVENANCE.md`.

## Two publishers

1. **UGRC / Utah SGID** (`services1.arcgis.com/99lidPhWCzftIe9K`, CC BY 4.0) — statewide
   authoritative: SLCo parcels (LIR, with assessor value/built-year/units — the housing
   base layer), address points, municipal/county boundaries, housing unit inventory,
   census geographies, opportunity/enterprise zones.
2. **Salt Lake County** (authoritative `apps.saltlakecounty.gov/slcogis`; hosted org
   `services1.arcgis.com/DJP723NX3ukQ2LtF`) — county-distinct: the **countywide Zones
   (zoning)** layer, subdivisions, annexations, HTRZ (housing+transit) zones, building
   footprints, unincorporated-lands parcels, affordable/missing-middle housing products,
   county-council districts.

## How to use the endpoints

Every `api_endpoint` is a standard ArcGIS REST layer. Do NOT bulk-fetch — query narrowly:

- Metadata / fields: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (no geometry, cheap): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- Geometry as GeoJSON: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson`
- Spatial filter: add `&geometry=<xmin>,<ymin>,<xmax>,<ymax>&geometryType=esriGeometryEnvelope&inSR=4326`
- Group-by summary (like the derived file): `&outStatistics=[...]&groupByFieldsForStatistics=<field>`
- Paging: `maxRecordCount` is ~2000; page with `resultOffset` / `resultRecordCount`.

Filter statewide SGID layers to Salt Lake County by the county field or a SLCo bbox.

## Growth relevance (what to reach for)

- **Housing supply / type / density** -> UGRC `HousingUnitInventory` (per-parcel unit
  type) + SLCo `MissingMiddleHousingAnalysis` + `AffordableHousing_Data` + `HTRZ_Zones`.
- **Land value / build-out / who owns what** -> UGRC `Parcels_SaltLake_LIR` (assessor
  attributes) or SLCo `Land/MapServer/1` Parcels (Recorder).
- **Zoning composition, cross-municipal** -> SLCo `Land/MapServer/7` **Zones** (the one
  harmonized countywide zoning layer; SGID has no good statewide zoning). See
  `derived/slco_zoning_polygon_counts.csv` for the category/municipality breakdown.
- **Jurisdiction / boundary / annexation questions** -> `UtahMunicipalBoundaries` or SLCo
  `Municipalities` + `Annexations`; `Parcels_Within_UnincorporatedLands` scopes exactly
  the land the COUNTY (not a city) plans and permits.
- **Historical growth footprint** -> `Residential_Growth_in_the_Salt_Lake_Valley`.
- **Representation <-> geography** -> SLCo County Council district layers (pair with the
  legislative + roster modules).

## Cardinal rules here

- **Catalog, don't mirror.** Never commit bulk layer downloads. Only tiny `derived/`
  summaries, each with provenance and a reproduce query.
- **Verify before quoting.** Re-check `?f=json` before relying on an endpoint; ArcGIS
  orgs migrate. `apps.saltlakecounty.gov/slcogis` is more stable than hosted-org item URLs.
- **Don't fabricate coverage.** If a layer's attributes are empty (e.g. SGID's
  `housing_unit_inventory_by_county` was all-null on 2026-07-11), it is NOT catalogued —
  see the gaps list in `SOURCES.md`.
