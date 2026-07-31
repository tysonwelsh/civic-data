# weber_county / gis — catalog only

Catalog of authoritative geospatial layers for Weber County growth/housing analysis.
**Catalog only — no bulk data is mirrored here.** Query the live ArcGIS FeatureServers
by bounding box / `where` clause; do not bulk-download the parcel layers. All endpoints
verified live 2026-07-20.

## `index.csv` (8 layers)

Key layers:

- **Weber County Parcels (LIR)** — the authoritative growth/housing base layer. UGRC/SGID
  `Parcels_Weber_LIR` FeatureServer, **203,008 records**, 29 fields (owner, acreage,
  market value, year built, building sqft, property class). CC BY 4.0.
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_Weber_LIR/FeatureServer/0`
- **Weber County Parcels (geometry)** — `Parcels_Weber`, **115,212 polygons**, geometry
  only (prefer the LIR variant).
- **Utah Address Points**, **Utah Municipal Boundaries** (incorporated vs unincorporated —
  the jurisdictional frame for the county PC), **Utah County Boundaries** (Weber FIPS
  49057) — statewide SGID layers, filter to Weber.
- **SGID Generalized Zoning** — statewide WIP layer, sparse; for authoritative Weber
  zoning use the county's own ArcGIS org (below) + the Land Use Code (`../ordinances/`).
- **Weber County ArcGIS Online org** — https://weber.maps.arcgis.com/ — the county's own
  authoritative zoning / future-land-use / addressing layers (enumerate its FeatureServers
  when doing parcel-level land-use work; not mirrored here).
- **Weber County Geo-Gizmo viewer** — https://www.webercountyutah.gov/GIS/gizmo2/ —
  public interactive parcel/zoning/aerial map viewer for one-off lookups.

## Notes

- The LIR parcel layer is the base for every housing/growth question in **unincorporated**
  Weber. With **Ogden Valley City** incorporating (2024/2025), use **Utah Municipal
  Boundaries** to distinguish newly-incorporated land from remaining unincorporated county
  jurisdiction when analyzing over time.
- No `derived/` summaries are produced in this catalog-only pass (unlike the reference
  county, which precomputed a zoning-polygon count). Add them if/when a parcel analysis is
  undertaken.
