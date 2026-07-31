# salt_lake_county / gis — sources & provenance (CATALOG, don't mirror)

**Policy (owner decision): this module CATALOGS GIS layers — it does NOT mirror bulk
geodata.** Parcels, zoning, address points, building footprints are hundreds of
thousands of features and are GB-scale as shapefiles. We record, per layer, the
metadata + a live queryable **ArcGIS REST endpoint** + vintage + license (`index.csv`)
so an LLM app can query them on demand. We do NOT download the full layers into the repo.
The only files stored are tiny already-summarized tables under `derived/` (see its
`PROVENANCE.md`).

Everything in `index.csv` was verified live against the endpoint on **2026-07-11**
(service exists, returns metadata, feature counts sampled). No layer was catalogued
unseen.

## Portals

### 1. UGRC / Utah SGID — statewide authoritative
- Human portal: <https://opendata.gis.utah.gov/> and <https://gis.utah.gov/> (product
  pages under `/products/sgid/`).
- REST org: `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services`
  (872 services; we curated the SLCo-relevant growth/housing/development ones).
- Access: open ArcGIS FeatureServers. `?f=json` for metadata; `/<id>/query?where=...&f=geojson`
  for data; `supportedExportFormats` include csv, shapefile, geoPackage, geojson, kml, excel.
- License: **CC BY 4.0** for SGID datasets (verified on the parcels item); Census-derived
  layers are US Census public domain.
- Salt Lake County parcels are maintained by UGRC **in coordination with the SLCo
  Assessor**, updated **monthly** (LIR layer last-edited 2026-03-27 at cataloguing).

### 2. Salt Lake County — its own GIS (distinct layers)
- Human portal / ArcGIS Hub: <https://salt-lake-county-maps-slco.hub.arcgis.com/> and
  the open-data site <https://gisdata-slco.opendata.arcgis.com/>.
- **Authoritative published server:**
  `https://apps.saltlakecounty.gov/slcogis/rest/services` — folders incl. `Land`
  (Zones/Parcels), `Administration` (Subdivisions, Municipalities, Annexations, County
  Council, Tax/Service Districts, Census), `Reference` (Address Points, PLSS),
  `Transportation` (RoadCenterline), `Assessor`, `Recorder`, `RegionalDev`, `Surveyor`.
  These are ArcGIS **MapServer** layers (query the same way as FeatureServers).
- **Hosted feature layers (ArcGIS Online org `slco`, id `DJP723NX3ukQ2LtF`):**
  `https://services1.arcgis.com/DJP723NX3ukQ2LtF/arcgis/rest/services` — 900+ items, most
  are ad-hoc/analysis/survey layers. We catalogued only the authoritative, durable,
  growth-relevant ones (HTRZ zones, building footprints, current municipal boundaries,
  council districts, unincorporated parcels, affordable-housing / missing-middle products).
- License: Salt Lake County publishes these publicly with **no explicit license stated**;
  treat as open public data and attribute "Salt Lake County GIS."
- The standout SLCo-distinct layer is **Land/MapServer/7 "Zones"** — a single harmonized
  countywide zoning layer (28,614 polygons) spanning every municipality + unincorporated,
  which SGID does not provide. It is the reason the county portal is catalogued separately
  rather than deferring entirely to SGID.

## Honest gaps

- **No statewide/countywide parcel-level ZONING in SGID.** SGID's `planning_generalized_zoning`
  is a work-in-progress with only 297 polygons statewide — sparse for SLCo. Authoritative
  per-parcel zoning lives with each **municipality**, and the best cross-jurisdiction
  substitute is the county's own `Zones` layer (catalogued). Individual city zoning
  ordinances are handled in the per-city repos, not here.
- **TAZ / travel-demand & long-range land-use projections** are published by **WFRC**
  (Wasatch Front Regional Council), a separate portal not catalogued here — noted as a
  future add if projection questions arise.
- **General Plan future-land-use** layers are municipal (each city adopts its own);
  there is no single county-wide general-plan-land-use GIS layer. The county's `Zones`
  layer is current zoning, not future land use.
- **`housing_unit_inventory_by_county`** (SGID) exists but its attribute columns were
  found **empty/null** on 2026-07-11 — NOT catalogued (would be a fabricated-value trap).
  The per-parcel `HousingUnitInventory` (populated) is catalogued instead.
- Bulk downloads are deliberately **absent** — this is the catalog policy, not a gap.
- Endpoints can move (ArcGIS org migrations); re-verify `?f=json` before relying on any
  URL. `apps.saltlakecounty.gov/slcogis` (authoritative) is more stable than individual
  hosted-org item URLs.
