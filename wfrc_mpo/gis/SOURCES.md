# wfrc_mpo / gis — sources & provenance (CATALOG, don't mirror)

**This module CATALOGS WFRC GIS layers — it does NOT mirror bulk geodata.** Per the repo's
GIS discipline (cf. `salt_lake_county/gis/`), we record each layer's metadata + a live
queryable **ArcGIS REST endpoint** + vintage + license in `index.csv`, and let an app query
them on demand. Nothing is downloaded whole.

Everything in `index.csv` was verified live (service exists, feature count sampled,
fields inspected) on **2026-07-20**. No layer was catalogued unseen.

## Publisher / portal

**Wasatch Front Regional Council**, ArcGIS Online org **`taguadKoI1XFwivx`**
(`https://services1.arcgis.com/taguadKoI1XFwivx/arcgis/rest/services`, 470 services).
Human portal: <https://wfrc.org/maps-data/>. WFRC publishes these publicly with **no
explicit license stated** — treat as open public data, attribute "Wasatch Front Regional
Council." Access is standard ArcGIS REST: `?f=json` for metadata,
`/<id>/query?where=...&f=geojson` for data, `outStatistics`/`groupByFieldsForStatistics`
for server-side summaries.

## What is catalogued (18 layers, growth-focused)

- **Wasatch Choice vision / centers / land use** — `WCV_All_Centers_2023` (density targets),
  `Wasatch_Choice_2050_Centers`, `Regionally_Significant_Land_Use`,
  `Generalized_Future_Land_Use_(2025)` (cross-jurisdiction future land use w/ MaxDUA),
  `BIG5_Housing_Jobs_Within_Centers` (homes/jobs-in-centers time series). The region's
  growth-shaping vision — the highest-value WFRC-distinct layers.
- **Equity / access** — `Equity_Focus_Areas_2023` (poverty/minority focus areas),
  `AccessToOpportunities` (TAZ jobs-accessibility).
- **Public engagement** — `TIP_Public_Comments`.
- **Projection & project geometry** — the RTP2023 City_Area / TAZ projection FeatureServers
  and the RTP2023 roadway/transit/AT project layers. Their **attributes are federated** in
  `../projections/` and `../projects/`; catalogued here as the spatial (geometry) endpoints.
- **Refresh seam — DRAFT RTP2027** — `CITYAREA_RTP27_gdb`, `COUNTY_RTP27_gdb`,
  `RTP2027_PreferredScenario_*`. Catalogued as the NEXT plan cycle; **do NOT blend into the
  adopted RTP2023 data** (projects/projections). Marked `[DRAFT RTP2027]` with a
  do-not-merge note in the row.

## How to use the endpoints

- Metadata / fields: `<api_endpoint>?f=json`
- Count: `<api_endpoint>/query?where=1=1&returnCountOnly=true&f=json`
- Attributes (cheap): `<api_endpoint>/query?where=<sql>&outFields=*&returnGeometry=false&f=json`
- GeoJSON: `<api_endpoint>/query?where=<sql>&outFields=*&f=geojson`
- Group-by summary: `&outStatistics=[...]&groupByFieldsForStatistics=<field>`
- Page with `resultOffset`/`resultRecordCount` (max ~2000).

## Cardinal rules here

- **Catalog, don't mirror.** Never commit bulk layer downloads.
- **Verify before quoting.** Re-check `?f=json`; ArcGIS orgs migrate.
- **Don't fabricate coverage.** Only layers actually seen live are listed.
- **Vintages are not blended.** RTP2027 draft layers are flagged and kept separate from the
  adopted RTP2023 layers.

## Honest gaps / not catalogued here

- **Parcels, zoning, address points, building footprints** are statewide UGRC/SGID or
  county products, already catalogued in `salt_lake_county/gis/` — not re-listed here.
- The parallel **MAG** project/forecast layers (`MAG_Roadway_lines_gdb`, `MAG_*`,
  `CITYAREA_RTP27` for Utah County) live in this same WFRC org but belong to the sibling
  **MAG** module.
- Many of the 470 org services are ad-hoc/analysis/mask/basemap layers; only durable,
  growth-relevant ones are catalogued.
- **Layer rename (note 2026-07-22): "Equity Focus Areas" → "Community Focus Areas."** WFRC
  renamed the equity overlay; the catalogued 2023 service's layer is already named
  `CommunityFocusAreas2023` (the FeatureServer keeps the `Equity_Focus_Areas_2023` service
  name — `index.csv` catalogs by service name, unchanged). A next-cycle service
  `Community_Focus_Areas_2027_RTP` exists in the org (verified live 2026-07-22) — catalog
  refresh QUEUED with the RTP2027 seam; do not blend into the adopted RTP2023 layers.
