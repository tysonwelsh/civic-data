# Geo — Millcreek address/point → council district

Maps a Millcreek, Utah address (or lat/long) to its City Council **district (1–4)** by
point-in-polygon against **Millcreek's own city GIS district polygons** ("Millcreek City
Council Districts 2022-2032") — the authoritative, whole-city boundary layer. Ported from
`south_jordan_city_council/geo/` (same county, same UGRC precinct source; Salt Lake
County, **UGRC CountyID = 18**). **As-of: 2026-07-06.**

## Millcreek council structure (important for interpretation)
Millcreek uses a **council-mayor form: 4 district seats (Districts 1–4)** plus a
separately-elected, city-wide **Mayor** (Cheri Jackson). There are **no at-large council
seats** — the Mayor is the only city-wide elected official. Every resident is represented
by **two** officials: their District councilmember and the city-wide Mayor.

Unlike South Jordan, **the Millcreek mayor is a full VOTING member of the council**
(max council tally = 5). That nuance concerns *vote extraction* (see the city `recon.md`),
**not geography** — this tool resolves only the **District seat (1–4)**. The Mayor is
city-wide (no district) and is not returned (the CLI prints a reminder).

Current district members (mirrors the city layer's `COUNCILMEMBER` field / 2026-05-11
council-minutes header; embedded in `address_to_district.py::COUNCIL_MEMBERS`, update after
each election):
District 1 = Silvia Catten · District 2 = Thom DeSirant · District 3 = Nicole Handy ·
District 4 = Bev Uipi. (Mayor, city-wide, voting: Cheri Jackson.)

## Files
```
council_districts.geojson   Millcreek's 4 council-district polygons, true EPSG:4326
                            (field "DIST" = "District 1".."District 4"; also carries
                            "COUNCILMEMBER", "CITY", "Pop"; from the city
                            "Millcreek City Council Districts 2022-2032" layer)
precincts.geojson           51 Millcreek (MIL-prefixed) SLCo precincts, true EPSG:4326
precinct_to_district.csv    precinct -> district (1–4), centroid-in-district; 51 rows, 0 splits
address_to_district.py      CLI + importable module: address/point -> district 1-4
council_districts_pre2022.geojson  AUTHORITATIVE 2016-incorporation (2017-2022) district
                            polygons (field "district"="1".."4" + "DIST","Representative",
                            provenance) — Millcreek City GIS CityCouncilDistricts/0; see
                            "District-boundary vintage" below
precinct_to_district_pre2022.csv   plan_2016 precinct-CODE -> district from the 2017+2019 SOVC
                            (a record of which OLD code voted in which district contest; medium,
                            NOT geographically joinable to the current precinct shapes)
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `council_districts.geojson`
   (`DIST` → "1".."4"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Millcreek →
district None. The address tool does **not** use `precinct_to_district.csv` — the city
district layer is authoritative and whole-city, so the lookup is a direct point-in-polygon
against the **district** outlines. The precinct table is a join aid for future by-precinct
election data.

## ⚠ District-boundary vintage (2016 vs 2022)
The `address_to_district.py` tool assigns every address on the **2022–2032 redistricting**
boundary (`council_districts.geojson`; ArcGIS Online item `5bf2141feb434742918a1c7b20f4b7e1`).
Millcreek incorporated Dec 2016 and elected its first council on the **original 2016
incorporation lines**; those lines were redrawn for the 2022–2032 cycle by Ordinance 22-23
(2022-05-09). Post-2022 data (the bulk of the analytic window and all current members) is exact.

**The pre-2022 (2016) boundary is now SOURCED — AUTHORITATIVE, 2026-07-19.**
`council_districts_pre2022.geojson` holds the exact 2016-incorporation district polygons,
fetched from **Millcreek's own city GIS** — the SAME ArcGIS org that publishes the current
layer (`services9.arcgis.com/XRrSFvEwSsReIxuA`), **`CityCouncilDistricts` FeatureServer layer 0**,
a layer the city explicitly named **"City Council District Boundaries 2017-2022"**
(`…/CityCouncilDistricts/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`).
4 polygons, field `DIST`=District 1..4, with a `DistrictRep` field carrying the **pre-2022**
members (incl. **Dwight Marchant, D2**, who left office Jan 2022 — confirming the vintage).
The roster's `district_versions` `plan_2016` rows are therefore **`confidence=high`** with this
`source_url`. Genuinely distinct from the 2022 plan (per-district IoU 0.58–0.92; the 2022
redistricting most reshaped D3/D4). ⚠ `address_to_district.py` itself still resolves against the
**2022** layer only; to answer a **pre-2022** address→district question, point-in-polygon
against `council_districts_pre2022.geojson` (property `district` = "1".."4").

**This authoritative layer REPLACED a 2026-07-11 precinct-dissolve reconstruction** (the old
`medium` `council_districts_pre2022.geojson`), which was found materially wrong (IoU ≈ 0 vs
this authoritative layer) because the `MIL###` precinct **codes were renumbered/reshaped**
between 2019 and the current 2025 UGRC precinct vintage — so dissolving current precinct
shapes by the 2019 SOVC assignment painted the wrong geography. **⚠ Do NOT regenerate this
file with `scripts/build_prior_district_map.py`** — that would overwrite the authoritative
fetch with the discredited reconstruction. The prior raw fetch + layer metadata are archived
under `_backups/2026-07-19-lm-wave/geo/millcreek/`.

## Data sources

### City council-district polygons (authoritative, PRIMARY source used)
Millcreek's **own city GIS** (ArcGIS Online org services9 / `XRrSFvEwSsReIxuA`), layer
**2** of the `Millcreek_City_Council_Dist_2022` FeatureServer
("Millcreek City Council Districts 2022-2032 Polygons"):
`https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/Millcreek_City_Council_Dist_2022/FeatureServer/2`
- Fetched via Query → geojson with `outSR=4326`:
  `…/FeatureServer/2/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- **4 polygons**; fields incl. `OBJECTID`, **`DIST`** (= "District 1".."District 4"),
  **`COUNCILMEMBER`**, `CITY` (= "Millcreek CITY"), `Pop`, `Shape__Area`. The layer's
  member field is mirrored into the resolver's `COUNCIL_MEMBERS` map so member names
  resolve even for `--latlon` lookups.
- ⚠ Layers **0 and 1 on this FeatureServer return "layer not found"** — the district
  polygons are on **layer 2** (enumerate via the `?f=json` service root). Layer's native
  extent SR is Web Mercator (wkid 102100 / 3857); the query was issued with `outSR=4326`
  and verified to be true Utah lon/lat (bounds ≈ `[-111.921, 40.659, -111.777, 40.714]`,
  Millcreek sits SE of downtown SLC). If you refetch, keep `outSR=4326` and re-verify.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — Millcreek
elections are county-run), filtered to the **51 `MIL`-prefixed** Millcreek precincts,
fetched with `outSR=4326`. Service (canonical, per gis.utah.gov):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
(1008 SLCo features statewide-county → filtered to the 51 whose **representative interior
point falls inside a Millcreek district polygon**; all 51 are `MIL`-prefixed).

**Precinct→district method:** each precinct's representative interior point was tested for
containment in a district polygon (`method=centroid_in_district`). Cross-checked against
majority-area overlap — **the two methods agree on all 51 precincts**, and every precinct's
largest-district area fraction is **> 0.98** (min 0.982), so there are **no split
precincts** (`split=no` for all rows). Precinct→district counts:
**D1 = 11, D2 = 14, D3 = 13, D4 = 13** (51 total). `MIL901` (a mail/special precinct)
resolves cleanly to D3. (Precinct `MIL048` and any `MUR`-prefixed edge precincts have
centroids outside Millcreek and are correctly excluded.)

## Usage
```
python3 address_to_district.py "3330 S 1300 E, Millcreek, UT 84106"
python3 address_to_district.py --latlon "40.6899 -111.8571"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-06)
| Input | Result |
|---|---|
| 3330 S 1300 E (City Hall area) | District 2 (Thom DeSirant) |
| 2760 E 3300 S | District 4 (Bev Uipi) |
| 1550 E 3900 S | District 2 (Thom DeSirant) |
| all 4 district interior rep-points (offline) | each resolves to its own district D1–D4 |
| 451 S State St, Salt Lake City (control) | outside Millcreek → None |

All four district interior points (`geometry.representative_point()`) resolve to their own
district, confirming point-in-polygon for D1–D4.

## Caveats
- **The Mayor is city-wide** — no district mapping; never returned. There are **no
  at-large council seats**. (The Millcreek mayor *votes* on the council — a vote-extraction
  nuance, not a geographic one.)
- **2016-vs-2022 vintage** — see the boundary-vintage section above; only the 2022–2032
  layer is published.
- **Boundaries are Millcreek only** — points outside the city (incl. the unincorporated
  Salt Lake County pockets that interleave with Millcreek) return district None. Example:
  `4188 S 2700 E` geocodes but lies outside the city → None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** the layer's native SR is Web Mercator; always refetch with `outSR=4326` and
  re-verify coords look like Utah lon/lat.
- **Member names are mirrored** from the layer's `COUNCILMEMBER` field into
  `COUNCIL_MEMBERS`; update after each election (and note the Nov 2025 seat change —
  Cheri Jackson moved from District 3 council to Mayor, Nicole Handy now holds District 3).
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
  The Census geocoder fails to match some valid Millcreek addresses (e.g. "1330 E Chambers
  Ave", the City Hall street) — supply `--latlon` directly when that happens.
