# mag_mpo / gis — a CATALOG of growth/development GIS layers (link, don't mirror)

**Catalog + live-endpoint index, NOT mirrored geodata** (same discipline as
`salt_lake_county/gis/`). Housing inventory (195k units), parcels (281k), land use, and TAZ
forecasts are large; we store their metadata + queryable ArcGIS REST endpoint + vintage +
license in `index.csv` and query them live. Only tiny `derived/` summaries would ever be
stored. **20 layers, all byte-verified live 2026-07-20** (feature counts confirmed).

## Publisher

Almost all layers are **Mountainland Association of Governments (MAG)**, ArcGIS Hub
`data.magutah.gov`, hosted org `services2.arcgis.com/EiGeaCDLpVDPqdJ5`. Exception: **UDOT
Road Functional Classification** is served from UDOT's own roads server
(`roads.udot.utah.gov`) and catalogued by MAG. No explicit license is stated on the hub
(public open data) — recorded as such per row.

## What's catalogued (by growth relevance)

- **Housing supply / type / density (high):** `MAG Housing Unit Inventory` (per-unit type,
  DUA, value, year built — 195,203 units); `General Plan Land Use 2025` (future land use +
  MaxDUA density ceiling from adopted municipal general plans); `MAG Wasatch Choice Vision
  Centers and Land Use` (the regional growth-vision centers); `Station Area Planning HB 462
  Status` (transit-oriented housing-density mandate tracking); `Utah County Parcels for
  Modeling` (build-out modeling base).
- **Socioeconomic forecast (high/medium):** `MAG TAZ Population / Employment / Household
  Forecast` (`TAZ_SE_RTP23`, annual 2019–2050 by traffic-analysis zone) — the fine grain
  behind the city projections federated in `../projections/`. `MAG Traffic Analysis Zones`
  is the join geography.
- **Network / traffic (medium):** `MAG Traffic Projections`, `UDOT Road Functional
  Classification`, `Transportation Master Plans (Utah County)`, `MAG 2023 Unified Plan Data
  (lines)` (geometry twin of `../projects/projects.csv`).
- **Active transport & safety (low):** bike lanes, paved trails, High Injury Network, trail
  counters.
- **Boundaries (low, context):** MAG MPO, MAG AOG (3-county), Wasatch Back RPO extents.

## Per-county services

Several MAG products are published as **one service per county** (Utah / Summit / Wasatch),
all sharing a schema. `index.csv` lists the **Utah-County** service as the primary
`api_endpoint` and names the Summit/Wasatch analog services in `notes` (TAZ SE forecasts,
TAZ geography, traffic projections). Query the analogs by swapping the county in the service
name.

## How to use the endpoints

Every `api_endpoint` is a standard ArcGIS REST layer. Query narrowly — do NOT bulk-fetch:

- Metadata / fields: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (cheap, no geometry): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- GeoJSON: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson`
- Filter by place: most MAG layers carry `City` / `County` (or `CITY`/`COUNTY`) fields.
- Paging: `maxRecordCount` ~2000; page with `resultOffset` / `resultRecordCount`.

## Label-verification note (cardinal rule)

`General Plan Land Use 2025` is served under the **legacy service name
`General_Plan_Land_Use_2023`**, but the layer's own `name` is "General Plan Land Use 2025"
and it carries a `PlanYear` field — the **body-verified label (2025)** is used in `index.csv`
while the working `api_endpoint` keeps the `_2023` service path (that is the URL that
resolves). Verify `?f=json` before quoting; ArcGIS services get renamed.

## Cardinal rules here

- **Catalog, don't mirror.** No bulk layer downloads committed.
- **Verify before quoting.** Re-check `?f=json`; counts in `notes` are the 2026-07-20 live
  values.
- **Don't fabricate coverage.** Empty/placeholder-attribute layers are not catalogued.
