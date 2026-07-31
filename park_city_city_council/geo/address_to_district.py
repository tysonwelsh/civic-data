#!/usr/bin/env python3
"""
Resolve a Park City, Utah address (or lat/long) to its City Council representation.

  *** Park City Council is ENTIRELY AT-LARGE — there are ZERO districts. ***

Park City has a Mayor + 5 council members, and all five council seats are elected
CITYWIDE. There is no ward / district map, so the classic "address -> council district"
lookup is DEGENERATE: every address inside the city is represented by the same six
officials (Mayor + all 5 at-large councilmembers), and an address outside the city has
no Park City representation.

This tool therefore answers the only meaningful geographic question:
  "Is this address (or point) INSIDE the Park City city limits?"

Pipeline:
  address --[Census geocoder, free, needs internet]--> lat/long
  lat/long --[point-in-polygon vs geo/city_boundary.geojson]--> in-city True/False

For context it also reports which voter precinct the point falls in
(geo/precincts.geojson, the Summit County / UGRC VistaBallotAreas subset for Park City)
— but precinct does NOT map to a district here; it is purely informational / useful for
joining the by-precinct election data.

CLI:
    python3 address_to_district.py "445 Marsac Ave, Park City, UT 84060"
    python3 address_to_district.py --latlon 40.6461 -111.4980
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("445 Marsac Ave, Park City, UT 84060")
    # -> {"in_city": True, "district": None, "council": "at-large ...",
    #     "precinct": "22OLDS:25", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API). lat/long lookups are fully offline.
  - CRS: geo/*.geojson are stored in EPSG:4326 (lon/lat). The UGRC source was
    requested with outSR=4326; coords verified as Utah lon/lat (~ -111.50, 40.65),
    NOT UTM meters (the trap that bit the WVC build). The tool still defensively
    set_crs(4326)/to_crs(4326) before any point-in-polygon test.
  - The city polygon was fetched from UGRC Municipal Boundaries by NAME='PARK CITY'.
    Park City is administratively in Summit County (CountyID 22) but a small piece of
    its limits straddles Wasatch County (COUNTYNBR 26) — the muni layer returns BOTH
    polygons and both are kept here as the full city limits.
  - "district" keys are kept in the return dict for API parity with the SLC / Lehi /
    St. George tools, but they are always None / "at-large" for Park City (no districts).
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
    # AliasName carries the human-readable precinct name; VistaID is the code.
    for key in ("VistaID", "PrecinctID", "AliasName"):
        if key in row and row[key] is not None:
            return str(row[key])
    return None


def district_for_point(lon, lat):
    """lat/long -> in/out of Park City city limits (offline).

    Returns a dict. 'district' is always None (the city has no districts);
    'in_city' is the meaningful field. 'precinct' is informational only.
    """
    from shapely.geometry import Point
    city = _city_limits()
    in_city = bool(city.contains(Point(lon, lat)).any())
    return {
        "in_city": in_city,
        "district": None,                       # Park City has no districts (at-large)
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
                f"    -> INSIDE Park City city limits{prec_str}\n"
                f"    -> represented by {COUNCIL}")
    return (f"  {head}\n"
            f"    -> OUTSIDE Park City city limits (no Park City representation)")


def main():
    ap = argparse.ArgumentParser(
        description="Park City address/point -> in/out of city limits "
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
