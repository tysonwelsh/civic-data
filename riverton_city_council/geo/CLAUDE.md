# Geo — Riverton address/point → council district

Maps a Riverton, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **Riverton's own city GIS district polygons** — the authoritative,
whole-city boundary layer. Salt Lake County, **UGRC CountyID = 18**. **As-of: 2026-07-11.**

## Riverton council structure (important for interpretation)
Riverton uses a **six-member council form: 5 district seats (Districts 1–5)** plus a
separately-elected **Mayor** (city-wide). There are **no at-large council seats** — the Mayor
is the only city-wide elected official, chairs the council, and **votes only to break a tie**
(see the city `recon.md`). Every resident is represented by **two** elected officials: their
District councilmember and the city-wide Mayor.

This tool resolves only the **District seat (1–5)**. The Mayor is city-wide (no district) and
is not returned (the CLI prints a reminder). The mayor-vote nuance concerns vote extraction,
not geography, and does not affect this tool.

## ⚠ D3 ↔ D4 renumbering across the 2022 redistricting
Ordinance No. 22-07 (2022) redrew the districts AND **renumbered D3 ↔ D4**. The two retained
GIS vintages make this explicit:
- **Pre-2022** (`districts_pre2022.geojson`, the 2019 lines): **D3 = Tawnee McCay, D4 = Tish
  Buroker** — which matches the authoritative *election* record (McCay won "District 3" 2017 &
  2021; Buroker won "District 4").
- **Current 2022** (`districts.geojson`): **D3 = Alexander Johnson, D4 = Shannon Smith** (the
  successors), with the numbers **swapped** relative to the pre-2022 layer.

So the D3/D4 seat number is **not stable across 2022**. This tool returns the **current
(2022)** number by default; pass `--pre2022` for pre-redistricting questions. Any
person↔district join crossing 2022 must key on person identity, not the bare number. See
`../election_results/CLAUDE.md` for the full caveat. (D1/D2/D5 are unaffected.)

## Files
```
districts.geojson           Riverton's 5 CURRENT council-district polygons (post-Ord 22-07,
                            EPSG:4326; field DIST_NAME = "D1".."D5", NAME = sitting member)
districts_pre2022.geojson   the pre-2022 (2019) district lines/numbers — vintage layer for
                            pre-redistricting address→district (dist_name/name, EPSG:4326)
precincts.geojson           35 Riverton (RIV-prefixed) SLCo precincts, EPSG:4326
precinct_to_district.csv    precinct → district (1–5), 35 rows, 0 splits, election-cross-checked
address_to_district.py      CLI + importable module: address/point → district 1–5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`DIST_NAME` = "D1".."D5", stripped to "1".."5"); fully offline. Member name comes from
   the layer's `NAME` field (no hand-maintained map needed — the city layer carries it).

`district_for_point(lon, lat, pre2022=False)` returns `{district, council_member, lat, lon,
vintage}`; `district_for_address(address)` adds `matched_address`. Points outside Riverton →
district None. The address tool does **not** use `precinct_to_district.csv` — the city
district layer is authoritative and whole-city, so the lookup is a direct point-in-polygon
against the **district** outlines. The precinct table is a join aid for by-precinct election
data.

## Data sources

### City council-district polygons (authoritative, PRIMARY source used)
Riverton's **own city ArcGIS Server** (`https://gis.rivertoncity.com/arcgis/rest/services`):
- **Current (2022):** the `districts.geojson` on disk is the post-Ordinance-22-07
  `Riverton_City_Council_Districts_2022` layer (combined FeatureServer
  `Council_Districts/FeatureServer/0` / per-district `Hosted/Council_Districts_2022/…`). 5
  polygons; fields `DIST_NAME` ("D1".."D5"), `LABEL`, **`NAME`** (sitting member), plus
  contact fields. Already delivered in EPSG:4326 (bounds ≈ `[-112.024, 40.493, -111.914,
  40.541]`, Riverton is around −111.94, 40.52).
- **Pre-2022 vintage:** fetched this build from
  `https://gis.rivertoncity.com/arcgis/rest/services/Hosted/City_Council_Voting_District_20191231/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`
  → `districts_pre2022.geojson` (5 polygons, lowercased fields `dist_name`/`name`; the
  `address_to_district.py` resolver handles both field-name cases). The host serves
  **gzip** — fetch with `curl --compressed`.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — Riverton
elections are county-run), filtered to the **35 `RIV`-prefixed** precincts, fetched with
`outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18+AND+PrecinctID+LIKE+'RIV%'&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
(1008 SLCo features county-wide → 35 `RIV###`). The precinct identifier is `PrecinctID` /
`VistaID` (the `AliasName` field is null for SLCo, unlike some other counties).

**Precinct→district method:** each precinct's representative interior point was tested for
containment in a current district polygon (`method=centroid_in_district`), cross-checked two
ways: (a) majority-area overlap (every precinct's largest-district area fraction is **> 0.98**,
min 0.980 → **no split precincts**), and (b) the district **election-contest membership** from
the post-2022 cycles (2023 D1/D2/D5 + 2025 D3/D4). **All three methods agree on all 35
precincts (0 disagreements).** Counts: **D1=5, D2=7, D3=7, D4=8, D5=8** (35 total). The CSV
carries `district` (geometry), `district_election` (contest membership), `area_frac`,
`agree_election`, and `split` columns so the cross-check is auditable.

## Usage
```
python3 address_to_district.py "12830 S 1700 W, Riverton, UT 84065"
python3 address_to_district.py --latlon "40.5219 -111.9391"    # quote the pair (negative LON)
python3 address_to_district.py --pre2022 "12830 S 1700 W, Riverton, UT 84065"
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-11)
| Input | Result |
|---|---|
| 12830 S 1700 W (Riverton City Hall), by address | District 5 (Spencer Haymond) |
| City Hall by `--latlon "40.5219 -111.9391"` (offline) | District 5 (Spencer Haymond) |
| 451 S State St, Salt Lake City (control) | outside Riverton → None |
| `--latlon "40.7608 -111.8910"` (SLC, control) | outside Riverton → None |
| all 5 district interior points (`representative_point()`) | each resolves to its own D1–D5 |
| City Hall `--pre2022` | District 5 (Claude Wells) — 2019-vintage member |

## Caveats
- **D3 ↔ D4 renumbered at 2022** — see above; use `--pre2022` for pre-redistricting
  questions and never assume the number is the same seat across 2022.
- **The Mayor is city-wide** — no district mapping; never returned. There are **no at-large
  council seats**.
- **Boundaries are Riverton only** — points outside the city return district None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** both district layers and the precinct layer are stored true EPSG:4326; if you
  refetch, keep `outSR=4326`, use `curl --compressed` for the `gis.rivertoncity.com` host
  (gzip), and re-verify coords look like Utah lon/lat.
- **Member names** ride on the city layer's `NAME` field (no hand-maintained map); they
  refresh whenever `districts.geojson` is refetched after an election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
