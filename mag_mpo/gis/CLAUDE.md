# mag_mpo / gis — CATALOG of MAG growth/development GIS layers (link, don't mirror)

Catalog + live-endpoint index of **20 MAG-region GIS layers** (Utah/Summit/Wasatch), NOT
mirrored geodata. Same discipline as `salt_lake_county/gis/`: store metadata + queryable
ArcGIS REST endpoint + vintage + license; query live. All byte-verified 2026-07-20.

## Files

- `index.csv` — the catalog. Columns: `layer, description, publisher, url, api_endpoint,
  format, vintage, license, growth_relevance, notes`. `api_endpoint` is the live ArcGIS
  layer URL. `growth_relevance`: 7 high / 6 medium / 7 low.
- `SOURCES.md` — portal, per-county-service convention, label-verification note, gaps.
- `derived/` — reserved for tiny summarized tables only (none yet).

## What to reach for

- **Housing supply / density** → `MAG Housing Unit Inventory` (195k units, per-unit type +
  DUA) · `General Plan Land Use 2025` (future land use + MaxDUA) · `Station Area Planning
  HB 462 Status` (TOD housing mandate) · `MAG Wasatch Choice Vision Centers and Land Use`.
- **Socioeconomic forecast (fine grain)** → `MAG TAZ Population/Employment/Household
  Forecast` (`TAZ_SE_RTP23`, annual 2019–2050) — the TAZ grain behind the city projections
  in `../projections/`. `MAG Traffic Analysis Zones` = join geography.
- **Project geometry** → `MAG 2023 Unified Plan Data (lines)` — geometry twin of
  `../projects/projects.csv`.
- **Boundaries** → MAG MPO / MAG AOG (3-county) / Wasatch Back RPO.

## Notes

- **Per-county services:** TAZ forecasts, TAZ geography, and traffic projections publish one
  service per county; `index.csv` lists the Utah-County endpoint + names the Summit/Wasatch
  analogs in `notes`.
- **Verify labels from the body.** `General Plan Land Use 2025` is served under the legacy
  `General_Plan_Land_Use_2023` service path (kept as the working `api_endpoint`); the 2025
  label is confirmed from the layer name + `PlanYear` field.
- **Catalog, don't mirror.** No bulk downloads; re-check `?f=json` before quoting.
