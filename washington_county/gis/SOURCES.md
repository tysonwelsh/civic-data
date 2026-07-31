# gis/ — sources

**Catalog only — link, never mirror.** Cataloged 2026-07-20.

- **County ArcGIS Server:** `https://agisprodvm.washco.utah.gov/arcgis/rest/services` — live,
  no key, **91 services**. Full reference: `derived/washco_arcgis_full_service_list.csv`.
  `index.csv` curates the ~24 growth/development-relevant ones (Parcels, ParcelOwners,
  Assessor, Developed_Parcels, Zoning, GeneralPlan, Subdivisions, Boundaries, Greenbelt,
  Hazards/WUI/WildfireHazardPotential, hillside slope, Elections precincts, RMP, and the
  1953–2026 aerial/Pictometry/NAIP imagery time-series).
- **Interactive front-ends:** `outpost.washco.utah.gov/apps/community-development/interactive-map/`;
  zoning-info map PDFs at `outpost.washco.utah.gov/apps/gis/assets/maps/gis/mi/*.pdf`.
- **UGRC / Utah SGID (statewide):** Washington County Parcels LIR, Municipal Boundaries,
  ACS demographic/housing — `opendata.gis.utah.gov` / `gis.utah.gov`.

Query the REST endpoints by bbox/where (export json/geojson/csv); do NOT bulk-download rasters
or parcel fabrics.
