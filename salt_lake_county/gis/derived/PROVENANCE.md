# gis/derived — small derived summaries (provenance)

Per the module's **catalog, don't mirror** policy, this folder holds ONLY tiny
already-summarized tables extracted live from a catalogued endpoint — never bulk geodata.

## `slco_zoning_polygon_counts.csv`

- **What:** Count of zoning polygons in the Salt Lake County countywide **Zones** layer,
  grouped two ways: by normalized `regional_category` (23 rows) and by `municipality`
  (24 rows). One long table, `grouping` column distinguishes the two cuts.
- **Source layer:** SLCo Countywide Zoning (Zones) —
  `https://apps.saltlakecounty.gov/slcogis/rest/services/Land/MapServer/7`
  (Salt Lake County Surveyor's Office; see `../index.csv`).
- **How derived:** ArcGIS `outStatistics` group-by `count(OBJECTID)` query against the
  live layer (no geometry downloaded), 2026-07-11. Reproduce:
  `.../Land/MapServer/7/query?where=1=1&groupByFieldsForStatistics=regional_c&outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"n"}]&f=json`
  (and again with `groupByFieldsForStatistics=municipali`).
- **Total:** 28,614 zone polygons countywide. Single Family dominates (18,984),
  then Multifamily (3,700), Commercial (1,705), Parks/Open Space (1,233), Mixed Use (835).
- **Caveat:** counts are POLYGON counts, not acreage (the service rejected an area
  statistic). Treat as relative composition, not land-area shares. Regenerate anytime —
  it is a live-query snapshot, not authoritative canon.
