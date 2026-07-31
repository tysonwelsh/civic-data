# summit_county / gis — sources & provenance (CATALOG, don't mirror)

**Policy (per the SLCo reference): this module CATALOGS GIS layers — it does NOT mirror
bulk geodata.** Parcels, zoning, address points are tens of thousands of features. We
record, per layer, the metadata + a live queryable **ArcGIS REST endpoint** + vintage +
license (`index.csv`) so an app can query them on demand. No full layer is downloaded.

Every `index.csv` row was verified live against its endpoint on **2026-07-20** (service
exists, `?f=json` returns metadata, feature counts sampled). No layer was catalogued
unseen. 15 layers / sources.

## Three publishers

### 1. Summit County — its own ArcGIS Server (`maps.summitcounty.org/arcgis`)
- Landing: <https://www.summitcountyutah.gov/234/Summit-County-GIS>; portal
  <https://maps.summitcounty.org/>.
- Authoritative published server:
  `https://maps.summitcounty.org/arcgis/rest/services` — folder **`Maps`** holds
  `OnlineMap` (cartographic base: parcels/roads/cities/subdivisions/communities/PLSS) and
  `ParcelQuery` (the **Parcel Information** layer, 43,966 parcels with county attributes).
  These are ArcGIS **MapServer** layers.
- License: county publishes publicly with a **completeness/accuracy DISCLAIMER** (users
  verify); treat as open, attribute "Summit County GIS."

### 2. Summit County — ArcGIS Online hosted org (`summitcounty.maps.arcgis.com`, org id `gyfpgFh2Wj2gglYD`, `services2.arcgis.com`)
- The **zoning** layers behind the county's Interactive Zoning Map
  (`webappviewer id=8fa54cade4d64da8b8a6869ba9b38f82`): `Zoning_Service/FeatureServer`
  layers **2 = Snyderville Basin zoning**, **3 = Eastern zoning**, **1 = Ag Protection**,
  **0 = Ridgelines**; plus `LowerSilverCreekOverlayZone` and `AddressPoints_24_12`
  (county address points, 2024-12 vintage). These are the county-distinct, growth-relevant
  layers and the reason the hosted org is catalogued alongside SGID.

### 3. UGRC / Utah SGID — statewide authoritative (`services1.arcgis.com/99lidPhWCzftIe9K`)
- Human portal: <https://opendata.gis.utah.gov/> and <https://gis.utah.gov/>.
- `Parcels_Summit_LIR` (37,294 — the **housing/assessor base**: value, built year, units
  per parcel), `Parcels_Summit` (geometry), `HousingUnitInventory` (per-parcel unit
  type/density; ~601 Summit records), plus statewide `UtahAddressPoints` /
  `UtahMunicipalBoundaries` / `UtahCountyBoundaries` filterable to Summit.
- License: **CC BY 4.0**.

## Regional (download portal, not REST)

- **Mountainland Association of Governments (MAG)** — Summit is one of MAG's 3 member
  counties (with Utah + Wasatch). GIS **downloads** at
  <https://magutah.gov/gis-data-downloads/> (TAZ/socioeconomic projections, transportation
  network, aerials, base data). Catalogued with **no `api_endpoint`** — it is file
  downloads, not a queryable service (honest limitation). Relevant if a future
  `projections/` module needs TAZ / travel-demand data.

## How to use the endpoints

Every `api_endpoint` is a standard ArcGIS REST layer. Do NOT bulk-fetch — query narrowly:
- Metadata: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (cheap): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- Geometry: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson`
- Filter statewide SGID layers to Summit by the county field (e.g. `COUNTY='SUMMIT'`) or bbox.

## Honest gaps

- **No county-wide FUTURE-land-use GIS layer** — the catalogued zoning layers are CURRENT
  zoning; General-Plan future land use is in the `plans/` documents, not a GIS layer.
- **MAG is download-only** (no per-layer REST endpoint) — recorded as such, not faked.
- **County server has an accuracy disclaimer** — re-verify `?f=json` before quoting; ArcGIS
  orgs/hosted-item ids migrate (the `maps.summitcounty.org` server is the most stable).
- Bulk downloads are deliberately **absent** — catalog policy, not a gap.
