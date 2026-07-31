#!/usr/bin/env python3
"""
Resolve a Logan, Utah address (or lat/long) to its City Council representation.

  *** Logan City Council is ENTIRELY AT-LARGE — there are ZERO districts. ***

Logan (Cache County seat) is governed by a Mayor + a 5-member Municipal Council.
All five council seats are elected CITYWIDE (at-large); they are NOT geographic
districts. Because there is no ward / district map, the classic
"address -> council district" lookup is DEGENERATE: every address inside the city
is represented by the same six officials (Mayor + all 5 at-large councilmembers),
and an address outside the city has no Logan representation.

This tool therefore answers the only meaningful geographic question:
  "Is this address (or point) INSIDE the Logan city limits?"

Pipeline:
  address --[Census geocoder, free, needs internet]--> lat/long
  lat/long --[point-in-polygon vs geo/city_boundary.geojson]--> in-city True/False

For context it also reports which voter precinct the point falls in
(geo/precincts.geojson, the Cache County / UGRC VistaBallotAreas subset for Logan
city — precincts 3LG01..3LG25) — but precinct does NOT map to a district here; it
is purely informational / useful for joining the by-precinct election data.

CLI:
    python3 address_to_district.py "290 N 100 W, Logan, UT 84321"
    python3 address_to_district.py --latlon 41.7370 -111.8338
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("290 N 100 W, Logan, UT 84321")
    # -> {"in_city": True, "council": "at-large (Mayor + 5 citywide)",
    #     "precinct": "3LG..", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API). lat/long lookups are fully offline.
  - CRS: geo/*.geojson are stored in EPSG:4326 (lon/lat). The UGRC source was
    requested with outSR=4326 and the coords were VERIFIED as Utah lon/lat
    (~ -111.84, 41.74), NOT UTM 26912 meters — so no reprojection was needed.
    (UGRC VistaBallotAreas has shipped 26912 mislabeled as 4326 elsewhere; this
    Cache County fetch checked out as true 4326.)
  - The city polygon was fetched from UGRC Utah Municipal Boundaries by
    NAME='LOGAN' (COUNTYNBR='03' = Cache County, FIPS=45860). Precincts are the
    VistaBallotAreas CountyID=3 features whose PrecinctID starts with '3LG'
    (Logan city), dissolved to one polygon per precinct.
  - "district" keys are kept in the return dict for API parity with the SLC /
    St. George / Lehi tools, but they are always None / "at-large" for Logan
    (no districts).
"""

import argparse
import functools
import json
import subprocess
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent
CITY_LIMITS_GEOJSON = BASE / "city_boundary.geojson"
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

COUNCIL = "at-large (Mayor + 5 citywide councilmembers — no districts)"


@functools.lru_cache(maxsize=1)
def _city_limits():
    import geopandas as gpd
    gdf = gpd.read_file(CITY_LIMITS_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    return gdf.to_crs("EPSG:4326")


@functools.lru_cache(maxsize=1)
def _precincts():
    import geopandas as gpd
    if not PRECINCTS_GEOJSON.exists():
        return None
    gdf = gpd.read_file(PRECINCTS_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    return gdf.to_crs("EPSG:4326")


def geocode(address):
    """Address -> (lon, lat, matched_address) via the free Census geocoder, or None."""
    url = (CENSUS + "?address=" + urllib.parse.quote(address)
           + "&benchmark=Public_AR_Current&format=json")
    out = subprocess.run(["curl", "-s", "--max-time", "30", url],
                         capture_output=True, text=True).stdout
    try:
        matches = json.loads(out)["result"]["addressMatches"]
    except (ValueError, KeyError):
        return None
    if not matches:
        return None
    c = matches[0]["coordinates"]
    return c["x"], c["y"], matches[0]["matchedAddress"]


def _precinct_for(lon, lat):
    from shapely.geometry import Point
    prec = _precincts()
    if prec is None:
        return None
    hit = prec[prec.contains(Point(lon, lat))]
    if hit.empty:
        return None
    row = hit.iloc[0]
    # PrecinctID carries the 3LG## Logan-city code (e.g. 3LG07).
    for key in ("PrecinctID", "VistaID", "AliasName"):
        if key in row and row[key] is not None:
            return str(row[key])
    return None


def district_for_point(lon, lat):
    """lat/long -> in/out of Logan city limits (offline).

    Returns a dict. 'district' is always None (the city has no districts);
    'in_city' is the meaningful field. 'precinct' is informational only.
    """
    from shapely.geometry import Point
    city = _city_limits()
    in_city = bool(city.contains(Point(lon, lat)).any())
    return {
        "in_city": in_city,
        "district": None,                       # Logan has no districts (at-large)
        "council": COUNCIL if in_city else None,
        "precinct": _precinct_for(lon, lat) if in_city else None,
        "lat": lat,
        "lon": lon,
    }


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"in_city": None, "district": None, "council": None,
                "precinct": None, "matched_address": None,
                "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if res.get("in_city"):
        prec = res.get("precinct")
        prec_str = f" (precinct {prec})" if prec else ""
        return (f"  {head}\n"
                f"    -> INSIDE Logan city limits{prec_str}\n"
                f"    -> represented by {COUNCIL}")
    return (f"  {head}\n"
            f"    -> OUTSIDE Logan city limits (no Logan representation)")


def main():
    ap = argparse.ArgumentParser(
        description="Logan address/point -> in/out of city limits "
                    "(council is at-large; there are no districts)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    ap.add_argument("--latlon", nargs=2, type=float, metavar=("LAT", "LON"))
    ap.add_argument("--batch", metavar="FILE", help="file with one address per line")
    args = ap.parse_args()

    if args.latlon:
        lat, lon = args.latlon
        print(_fmt(district_for_point(lon, lat)))
    elif args.batch:
        for line in Path(args.batch).read_text().splitlines():
            line = line.strip()
            if line:
                print(line); print(_fmt(district_for_address(line)))
    elif args.address:
        print(_fmt(district_for_address(args.address)))
    else:
        ap.error("provide an address, --latlon LAT LON, or --batch FILE")


if __name__ == "__main__":
    main()
