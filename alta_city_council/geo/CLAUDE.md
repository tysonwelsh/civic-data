# Geo — Town of Alta boundary / precincts (AT-LARGE — no council districts)

Resolves a Town of Alta, Utah address (or lat/long) to its **representation**. Unlike the
district cities (South Jordan, Taylorsville, Sandy…), **Alta has NO council districts**, so
there is nothing to map an address *to* except **town membership** + the single at-large seat
basis. The standard "address → district" question degenerates to a **point-in-polygon
membership test**: *is this point inside the Town of Alta?* **As-of: 2026-07-11/12.**

## Alta council structure (important for interpretation)

Alta uses Utah's **Town** form of government: a town-wide (VOTING) **Mayor** plus a **4-member
Town Council, ALL elected AT-LARGE**. There are **no single-member districts** and **no at-large
vs district split** — every council seat is filled town-wide, and **every resident is
represented by the entire council + the Mayor** on an **At-Large** basis. The **Mayor is a full
voting member** (see the repo `CLAUDE.md` / `meeting_minutes/CLAUDE.md`); that concerns vote
extraction, not geography.

Because there are no districts, this layer carries **no per-district polygons** and there is no
real address→district resolution — `precinct_to_district.csv` maps **all** precincts →
`At-Large`.

## Files
```
city_boundary.geojson       Town of Alta boundary — single Polygon, true EPSG:4326
                            (Little Cottonwood Canyon; UGRC Municipal Boundaries NAME='Alta')
precincts.geojson           the 2 Alta SLCo precincts (ALT001, ALT002), true EPSG:4326
precinct_to_district.csv    precinct -> "At-Large" (both ALT001 & ALT002); there are no districts
address_to_district.py      CLI + importable module: address/point -> town membership + "At-Large"
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → in_alta** by point-in-polygon against `city_boundary.geojson` (fully offline).
3. If inside, optionally report which of the 2 precincts (`ALT001`/`ALT002`) the point falls in
   — **both map to At-Large** (`precinct_to_district.csv`), so the precinct is informational only.

`district_for_point(lon, lat)` returns
`{in_alta, seat_basis ("At-Large"|None), district ("At-Large"|None, a sibling-key alias),
precinct, representation ("Mayor + 4 at-large Town Council members"), mayor, council_at_large,
lat, lon}`; `district_for_address(address)` adds `matched_address`. Points **outside** the Town
return `in_alta=False`, `seat_basis=None`. The current Mayor + 4 at-large members are hand-kept
in `address_to_district.py` (`MAYOR` / `COUNCIL_AT_LARGE`); update after each election — the
GIS layer has no member field.

## Data sources

### Town boundary (authoritative membership polygon)
**UGRC Utah Municipal Boundaries**, `NAME='Alta'` (queried `NAME='ALTA'`), **COUNTYNBR / CountyID
= 18** (Salt Lake County) — a single Polygon covering the town at the top of Little Cottonwood
Canyon (`ENTITYNBR` 3010; `POPLASTCENSUS` 228). Fetched as true EPSG:4326.

### Precincts (informational)
**UGRC VistaBallotAreas**, `CountyID=18` (Salt Lake County — Alta elections are county-run),
filtered to the **2** Alta precincts (`ALT001`, `ALT002`), fetched with `outSR=4326`. These are
a join aid for by-precinct election data (`../election_results/`), not a district source — both
resolve to **At-Large**.

## Usage
```
python3 address_to_district.py "10230 E State Highway 210, Alta, UT 84092"
python3 address_to_district.py --latlon "40.5884 -111.6386"   # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt          # one address per line
```
As a module: `from address_to_district import district_for_address, district_for_point`.

## Caveats
- **No council districts** — Alta is at-large; the tool answers *town membership* + `At-Large`,
  never a district number. A `district` key == `"At-Large"` is included only for callers that
  expect the sibling-city key.
- **The Mayor votes** (Town form) but is city-wide like the whole at-large council — no separate
  mapping. Member names are hand-maintained (GIS layer has no member field); update after each
  election.
- **Boundaries are Alta only** — points outside the Town return `in_alta=False`.
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`; comma also accepted).
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline. The
  Census geocoder may fail to match some canyon addresses — supply `--latlon` directly then.
</content>
