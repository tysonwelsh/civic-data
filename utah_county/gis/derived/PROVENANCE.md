# gis/derived — small derived summaries (provenance)

Per the module's **catalog, don't mirror** policy, this folder holds ONLY tiny
already-summarized tables extracted live from a catalogued endpoint — never bulk geodata.

## `utahco_housing_unit_inventory_by_type.csv`

- **What:** Housing units in Utah County from the statewide **Housing Unit Inventory**,
  grouped two ways: by `TYPE` (2 rows: single_family / multi_family) and by `SUBTYPE`
  (7 rows: single_family, apartment, townhome, condo, duplex, mobile_home_park, mixed
  th/single_family). One long table; the `grouping` column distinguishes the two cuts.
  `n_records` = inventory records; `housing_units` = SUM of the `UNIT_COUNT` field.
- **Why this instead of a zoning summary:** Salt Lake County's derived file counts
  polygons in its harmonized countywide **Zones** layer. Utah County publishes **no**
  county-wide zoning / general-plan-land-use GIS layer (see `../SOURCES.md`), so the
  closest growth-composition summary is the housing supply mix from the Housing Unit
  Inventory (populated for Utah County — 195,204 records ≈ 231,597 units).
- **Source layer:** Utah Housing Unit Inventory —
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/HousingUnitInventory/FeatureServer/0`
  (UGRC + WFRC + MAG; see `../index.csv`).
- **How derived:** ArcGIS `outStatistics` group-by (count of OBJECTID + sum of
  UNIT_COUNT) against the live layer filtered to Utah County (no geometry downloaded),
  2026-07-20. Reproduce (POST or urlencoded GET):
  `.../HousingUnitInventory/FeatureServer/0/query?where=COUNTY='UTAH'&groupByFieldsForStatistics=TYPE&outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"n_records"},{"statisticType":"sum","onStatisticField":"UNIT_COUNT","outStatisticFieldName":"units"}]&f=json`
  (and again with `groupByFieldsForStatistics=SUBTYPE`).
- **Totals:** Single-family dominates (147,357 units), then apartments (28,041),
  townhomes (22,616), condos (15,120), duplexes (14,498), mobile-home-park pads (2,465).
  Single-family + multi-family = ~231,597 units countywide.
- **Caveat:** counts are inventory-record / unit-count figures from a best-effort
  parcel-derived model, not a permit or census count. Treat as relative composition.
  Regenerate anytime — it is a live-query snapshot, not authoritative canon.
