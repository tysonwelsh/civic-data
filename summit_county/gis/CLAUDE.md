# summit_county / gis — a CATALOG of growth/development GIS layers (link, don't mirror)

**This module is a catalog + live-endpoint index, NOT mirrored bulk geodata.** Parcels,
zoning, and address points are tens of thousands of features each. We store their
**metadata + a queryable ArcGIS REST endpoint + vintage + license** in `index.csv` and let
an app query them live. Never download a full layer into this repo.

## Files

- `index.csv` — **the catalog.** 15 verified growth/housing/development GIS layers/sources
  for Summit County. Columns: `layer, description, publisher, url, api_endpoint, format,
  vintage, license, growth_relevance, notes`. `api_endpoint` is the live ArcGIS REST layer
  URL — queryable directly (blank only for MAG, which is download-only).
- `SOURCES.md` — the three publishers, access method, licenses, honest gaps.
- `derived/` — reserved for tiny already-summarized tables (empty at build; add with a
  reproduce query if needed).

## Three publishers

1. **Summit County ArcGIS Server** (`maps.summitcounty.org/arcgis`) — authoritative
   parcels (`ParcelQuery`, 43,966) + cartographic base (`OnlineMap`). MapServer layers.
2. **Summit County ArcGIS Online** (org `gyfpgFh2Wj2gglYD`, `services2.arcgis.com`) — the
   county-distinct **zoning** layers (Basin district, Eastern district, Ag Protection,
   Ridgelines, Lower Silver Creek overlay) + county address points.
3. **UGRC / Utah SGID** (`services1.arcgis.com/99lidPhWCzftIe9K`, CC BY 4.0) — the
   `Parcels_Summit_LIR` housing/assessor base (37,294), `HousingUnitInventory`, statewide
   address/municipal/county boundaries filterable to Summit.
   Plus **MAG** (Mountainland AOG) regional GIS **downloads** (TAZ/projections) — file
   downloads, no REST endpoint.

## Growth relevance (what to reach for)

- **Zoning, by district** -> Summit County `Zoning_Service/2` (Basin) + `/3` (Eastern) —
  pair with `plans/` (the two General Plans) + `ordinances/` (Title 10 / Title 11).
- **Housing supply / type / density** -> UGRC `HousingUnitInventory` (Summit subset) +
  `Parcels_Summit_LIR` (per-parcel value/built-year/units).
- **Land value / who owns what / build-out** -> `Parcels_Summit_LIR` (UGRC, richest) or
  the county `ParcelQuery` layer.
- **Development constraints** -> Ag Protection, Ridgelines, Lower Silver Creek overlay.
- **City vs unincorporated (what the COUNTY plans)** -> `UtahMunicipalBoundaries`
  (Park City / Coalville / Kamas / Oakley / Henefer / Francis vs unincorporated).
- **Regional growth / TAZ projections** -> MAG downloads (see SOURCES.md; download-only).

## How to use the endpoints

Standard ArcGIS REST. Query narrowly (see SOURCES.md for the full recipe):
`<api_endpoint>?f=json` (metadata) · `.../query?where=1=1&returnCountOnly=true&f=json`
(count) · `.../query?where=<sql>&outFields=*&returnGeometry=false&f=json` (attributes).
Filter SGID statewide layers to Summit by `COUNTY='SUMMIT'` or a bbox.

## Cardinal rules here

- **Catalog, don't mirror.** Never commit bulk layer downloads. Only tiny `derived/`
  summaries, each with provenance + a reproduce query.
- **Verify before quoting.** Re-check `?f=json` before relying on an endpoint; ArcGIS
  hosted-item ids migrate. `maps.summitcounty.org/arcgis` is the most stable host; the
  county attaches an accuracy DISCLAIMER — verify.
- **Don't fabricate coverage.** MAG is honestly recorded as download-only (no
  `api_endpoint`); there is no county-wide future-land-use GIS layer (that lives in
  `plans/`).
