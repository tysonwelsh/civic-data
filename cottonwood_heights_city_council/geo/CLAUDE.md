# Geo — Cottonwood Heights address/point → council district

Maps a Cottonwood Heights, Utah address (or lat/long) to its City Council
**district (1–4)** by point-in-polygon against **Cottonwood Heights' own city GIS
district polygons** ("Council Districts", authoritative, whole-city, current
post-2020-census map). Salt Lake County; UGRC CountyID = 18. **As-of: 2026-07-12.**

## Cottonwood Heights council structure (important for interpretation)
CH uses a **4-district council + a separately-elected Mayor who VOTES** as a full
member of the council (max roll-call tally = 5). There are **no at-large council
seats**; the Mayor is the only city-wide elected official. Every resident is
represented by **two** officials: their District councilmember and the city-wide
Mayor. This is the OPPOSITE of Taylorsville / South Jordan (non-voting mayor) — but
for *geography* it makes no difference: the tool resolves the **District seat
(1–4)** only, and the Mayor (city-wide, no district) is never returned.

Current members (baked into `districts.geojson`'s `Member`/`Term` fields, from the
city's own layer): **D1 Matt Holton (2024–2027) · D2 Suzanne Hyland (2024–2027) ·
D3 Shawn Newell (2022–2029) · D4 Ellen Birrell (2022–2029)**. Mayor, city-wide:
**Gay Lynn Bennion (2026–2029)**.

## Files
```
districts.geojson          CH's 4 council-district polygons, true EPSG:4326
                           (field DistrictID = 1..4; Member/Term/email inline)
precincts.geojson          44 COT-prefixed SLCo precincts, true EPSG:4326
precinct_to_district.csv   precinct -> district (1–4), point-in-polygon; 44 rows,
                           cross-checked vs current-map elections (0 disagreements)
address_to_district.py     CLI + importable module: address/point -> district 1-4
build_geo.py               refetch sources + rebuild all three artifacts (idempotent)
raw/                       the untouched source fetches (provenance)
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`DistrictID` = 1..4); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside CH →
district None. The address tool does **not** use `precinct_to_district.csv` — the
city district layer is authoritative and whole-city, so the lookup is a direct
point-in-polygon against the **district** outlines. The precinct table is a join
aid for by-precinct election data.

## Data sources

### City council-district polygons — OFFICIAL layer used (not derived)
CH's own "Council Districts" layer. The city runs two GIS hosts:
- **`gis.chcity.org`** — the catalogued `CityData/CityCouncilDistricts_SD`
  service, but it is **FIREWALLED** from outside the city network (connection
  times out — confirmed in `recon.md` and re-confirmed this build).
- **`gis.cwh.utah.gov`** — a **PUBLIC mirror that IS reachable**, exposing the
  same districts as **layer 15 "Council Districts"** of
  `PublicData/City_Base_Data/MapServer`. **This is the layer used** (fetched via
  `…/MapServer/15/query?where=1=1&outFields=*&outSR=4326&f=geojson`). 4 polygons,
  fields incl. **`DistrictID`** (1..4), `Label`, **`Member`**, **`Term`**, `email`.
  So the geo layer is the **official city boundary**, NOT a precinct-derived
  fallback — despite `gis.chcity.org` being unreachable, the mirror gave the real
  thing.

### CRS note
Fetched with **`outSR=4326`**; verified true Utah lon/lat (bounds ≈
`[-111.866, 40.575, -111.777, 40.638]`; CH sits ~ −111.82, 40.61). geopandas reads
it as EPSG:4326 and point-in-polygon against Census lat/long works directly. If you
refetch, keep `outSR=4326` and re-verify coords look like Utah lon/lat.

### Precincts (informational + join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — CH
elections are county-run), filtered to the **44 `COT`-prefixed** precincts
(`COT001–041` + mail/special `COT901/902/903`), fetched with `outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18 AND PrecinctID LIKE 'COT%'&outSR=4326&f=geojson`

**Precinct→district method:** each precinct's representative interior point tested
for containment in a district polygon (`method=point_in_polygon`), then
**cross-checked against the current-map elections** (2023 D1/D2 + 2025 D3/D4): all
**43** precincts that appear in those contests **agree** with polygon containment
(`agrees_with_current_election=yes`; 0 disagreements). The 44th precinct
(`COT041`, no votes in those contests) is polygon-only (`n/a`). Counts: D1=8, D2=11,
D3=8, D4=17 (44 total). `COT901/902/903` resolve cleanly to D4.

### ⚠ Redistricting seam (documented, not applied to the current crosswalk)
CH redrew districts after the 2020 census. The **2021** (old-map) SOVC assigns
several COT precincts to a *different* district than the current layer
(e.g. COT007/016 old-D3 → now D1; COT017/018 old-D3 → now D2; COT021/023/037
straddle old D1/D4 vs current). `precinct_to_district.csv` reflects the **current**
map only (the official layer + 2023/2025 elections). The pre-2022 assignment is
recoverable from the 2021 rows in
`../election_results/cottonwood_heights_results_by_precinct.csv` if a historical
crosswalk is ever needed (mirrors South Jordan's `*_pre2022` split).

## Usage
```
python3 address_to_district.py "2277 E Bengal Blvd, Cottonwood Heights, UT 84121"
python3 address_to_district.py --latlon "40.6197 -111.8113"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
python3 build_geo.py                                           # refetch + rebuild
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 2277 E Bengal Blvd (City Hall), geocoded | **District 3 (Shawn Newell)** |
| 451 S State St, Salt Lake City (control) | outside CH → None |
| D1 / D2 / D3 / D4 interior points (offline) | resolve to 1 / 2 / 3 / 4 respectively |

## Caveats
- **The Mayor is city-wide** — no district mapping; never returned. There are **no
  at-large council seats**. (Mayor VOTES on the council — a vote-extraction fact,
  not a geography one; it does not affect this tool.)
- **Boundaries are Cottonwood Heights only** — points outside the city return None.
- **`--latlon` quoting:** longitude is negative; pass the pair as one quoted token
  (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** always refetch with `outSR=4326` (see note above).
- **Member names** come from the layer's `Member` field (primary) with a hand
  fallback in `COUNCIL_MEMBERS`; update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are
  offline.
- The official `gis.chcity.org` host is firewalled from outside the city; the
  reachable `gis.cwh.utah.gov` mirror is the working endpoint (see build_geo.py).
