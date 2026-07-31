# cache_county/gis/derived — provenance

Small pre-summarized tables only (repo rule: catalog GIS, never mirror bulk layers).

## cache_county_base_zoning_counts.csv

Parcel counts per primary zoning district for the county base-zoning layer.

- **Source layer:** `Planning/Zoning` MapServer, sublayer **1 (County Zoning Base
  Districts)** on `https://gis.cachecounty.gov/arcgis/rest/services`.
- **Field:** `zone_primary`.
- **Reproduce** (per category, because the layer's `outStatistics` groupBy returns a
  server 500):
  `…/Planning/Zoning/MapServer/1/query?where=zone_primary='A10'&returnCountOnly=true&f=json`
  for each of the 8 districts (A10, FR40, RU2, RU5, RR, C, I, CITY).
- **Retrieved:** 2026-07-20. Total parcels ≈ 60,103. Note ~49.5k are `CITY` (parcels
  inside incorporated municipalities); the county's own unincorporated land is dominated
  by `A10` (Agricultural 10-acre) and `FR40` (Forest Recreation 40-acre) — the
  thin-agricultural land-use profile.
- Counts are a live-service snapshot; re-query for current values.
