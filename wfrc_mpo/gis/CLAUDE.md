# wfrc_mpo / gis — a CATALOG of WFRC growth/vision GIS layers (link, don't mirror)

**This module is a catalog + live-endpoint index, NOT mirrored geodata.** It records, per
layer, metadata + a queryable ArcGIS REST endpoint + vintage + license, and lets an app
query them live. Only tiny derived summaries (none yet) would ever be stored.

## Files

- `index.csv` — **the catalog.** 18 verified WFRC growth/vision/equity/land-use layers.
  Columns: `layer, description, publisher, url, api_endpoint, format, vintage, license,
  growth_relevance, notes` (same schema as `salt_lake_county/gis/index.csv`). `api_endpoint`
  is the live ArcGIS FeatureServer URL.
- `SOURCES.md` — the WFRC org/portal, access recipes, the refresh seam, and honest gaps.

## What's here (highest value first)

- **Where growth is planned to concentrate** → `WCV_All_Centers_2023` (center density
  targets: dwelling/acre, non-res FAR), `Regionally_Significant_Land_Use`,
  `BIG5_Housing_Jobs_Within_Centers` (is growth landing in centers?).
- **Cross-jurisdiction future land use** → `Generalized_Future_Land_Use_(2025)` (stitched
  from city general plans; City/County/GenLUType/MaxDUA).
- **Equity & access overlays** → `Equity_Focus_Areas_2023`, `AccessToOpportunities`.
- **Spatial twin of the federated data** → the RTP2023 projection (City_Area/TAZ) and
  project (roadway/transit/AT) geometry endpoints; attributes live in `../projections/` and
  `../projects/`.
- **Refresh seam** → `[DRAFT RTP2027]` layers (`CITYAREA_RTP27_gdb`, `COUNTY_RTP27_gdb`,
  `RTP2027_PreferredScenario_*`) — the next cycle; **do not blend** into RTP2023 data.

## Cardinal rules

- **Catalog, don't mirror.** No bulk downloads.
- **Verify before quoting** (`?f=json`); orgs migrate.
- **Vintages not blended** — RTP2027 draft is flagged separate from adopted RTP2023.
- Publisher is WFRC (org `taguadKoI1XFwivx`); no explicit license — attribute "Wasatch
  Front Regional Council." Statewide parcels/zoning/address layers stay in
  `salt_lake_county/gis/`; MAG/Utah-County layers belong to the MAG module.
