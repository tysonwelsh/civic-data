# Geo — address/point → council district

Maps a Salt Lake City address (or lat/long) to its City Council district, using the
precinct boundaries here plus the precinct→district lookup derived from election data.

## Files
```
slco_precincts_current.{geojson,gpkg}        Salt Lake County precinct boundaries (PrecinctID)
shapefile/slco_precincts_current/*.shp ...   same, shapefile format
build_precinct_district_map.py               -> precinct_to_district.csv   (regenerable lookup)
precinct_to_district.csv                      precinct, district, source_year (144 SLC precincts)
address_to_district.py                        CLI + importable module: address/point -> district
```

## How it works (no council-boundary file needed)
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → precinct** by point-in-polygon against `slco_precincts_current.geojson`
   (`PrecinctID`); fully offline.
3. **precinct → district** via `precinct_to_district.csv`.

The election `precinct` column == the shapefile `PrecinctID` (e.g. `SLC014`), which is
what makes the join work. The district map is built from election data: each SLC council
contest lists its precincts, so contest→precincts == district→precincts.

## Usage
```
python3 build_precinct_district_map.py          # (re)build the lookup; default = current map
python3 address_to_district.py "675 N F St, Salt Lake City, UT"
python3 address_to_district.py --latlon 40.76 -111.89        # offline
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

## Caveats
- **Redistricting:** `precinct_to_district.csv` is the CURRENT map, built from the two
  most recent generals (2023 even + 2025 odd districts). For a historical question,
  rebuild with `--years YYYY` from that era's election data.
- **PRIOR (pre-2022 / plan_2012) map — RECONSTRUCTED 2026-07-19** at
  `geo/council_districts_pre2022.geojson` + `geo/precinct_to_district_pre2022.csv` (via
  `scripts/build_prior_district_map.py --city slc_city_council --years 2019,2021 --precincts
  geo/slco_precincts_current.geojson` — 2019 D2/D4/D6 + 2021 D1/D2/D3/D5/D7 district-contest
  precincts dissolved over current precinct shapes). **APPROXIMATE + UNRELIABLE:** old assignment over
  current-vintage shapes; 107/124 old codes carry geometry. **GEOMETRY confidence DOWNGRADED to `low`
  for ALL 7 districts 2026-07-19** (was D1–D6 `medium`/D7 `low`): a VALIDATION probe found SLC publishes
  NO 2012-vintage council layer (both SLC-org layers are the current 2022 plan), and a fragmentation
  control proved the renumbering is city-wide — the current-assignment dissolve makes clean 1-piece
  districts but this pre-2022 dissolve makes 2–15-piece fragments (D6=15, D5=9, D4=7, D2=6) even for D1–D6
  whose codes are all "present". SLC055/SLC062 are resolved 2019-D4/2021-D5 conflicts (→D5). The
  `roster/district_precincts` precinct-CODE composition stays `medium` (a faithful SOVC record). See
  `scripts/roster_boundary_recon.md`.
- Geocoding requires internet (Census API, free, no key); lat/long lookups don't.
- `SLC903` (mail/provisional) has no polygon — addresses won't resolve to it.
- Comment addresses are frequently `[REDACTED]`, so auto-extraction from comments yields
  little; the tool is most useful when an address is supplied directly.
- Boundaries are county-wide; non-SLC points return district None.
