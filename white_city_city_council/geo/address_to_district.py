#!/usr/bin/env python3
"""
Resolve a White City, Utah address (or lat/long) to its City Council representation.

White City has NO council districts -- the entire city elects ONE at-large body:
a directly-elected Mayor + 4 at-large council seats (A-D) since the 2024 HB35 conversion
to a city (before that, a 5-member all-at-large metro-township council whose Chair carried
the "Mayor" title and voted as a member). So "which district?" has a single answer for
every resident: **At-Large** (the whole city). This tool therefore resolves only
in-White-City vs not; there is no sub-city district geography to return.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in White City? -> "At-Large"

CLI:
    python3 address_to_district.py "999 E Galena Dr, Sandy, UT 84094"
    python3 address_to_district.py --latlon "40.5667 -111.8637"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("999 E Galena Dr, Sandy, UT 84094")
    # -> {"district": "At-Large", "in_white_city": True, "representatives": [...],
    #     "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - Every White City resident is represented by the SAME at-large body (Mayor + 4 seats);
    there is no per-address district. Points outside the city return district None.
  - White City is small (~5,000 people); the Census geocoder may miss some addresses ->
    pass --latlon directly when that happens.
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
BOUNDARY_GEOJSON = BASE / "city_boundary.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# White City is all at-large: one Mayor + 4 at-large council seats (A-D). The whole city
# elects every one of them, so these represent EVERY address (no district split). Names
# from whitecity.utah.gov/city-council + the 2026 minutes headers; update after each
# election. (Metro-township era 2017-2024: a 5-member all-at-large council whose Chair,
# Paulina Flint, held the "Mayor" title and voted as a member.)
AT_LARGE_REPRESENTATIVES = [
    "Mayor Allan Perry (voting; elected 2025)",
    "Council Seat A: Greg Shelton (2023)",
    "Council Seat B: Linda Price (2025)",
    "Council Seat C: Neil Mahoney - Mayor Pro-Tem (2025)",
    "Council Seat D: Tyler Huish (2023)",
]


@lru_cache(maxsize=1)
def _boundary():
    import geopandas as gpd
    return gpd.read_file(BOUNDARY_GEOJSON).to_crs("EPSG:4326")


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


def district_for_point(lon, lat):
    """lat/long -> {district, in_white_city, representatives} (offline).

    district is "At-Large" inside White City, None outside (there are no sub-city
    districts -- the whole city is one at-large constituency)."""
    from shapely.geometry import Point
    b = _boundary()
    inside = bool(b.contains(Point(lon, lat)).any())
    if not inside:
        return {"district": None, "in_white_city": False,
                "representatives": [], "lat": lat, "lon": lon}
    return {"district": "At-Large", "in_white_city": True,
            "representatives": list(AT_LARGE_REPRESENTATIVES), "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "in_white_city": None, "representatives": [],
                "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_white_city"):
        return f"  ({head}) -> outside White City"
    lines = [f"  {head}", "    -> White City (At-Large; whole city elects one body):"]
    lines += [f"       - {r}" for r in res["representatives"]]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="White City address/point -> council representation (all At-Large)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    ap.add_argument("--latlon", nargs="+", type=str, metavar=("LAT", "LON"))
    ap.add_argument("--batch", metavar="FILE", help="file with one address per line")
    args = ap.parse_args()

    if args.latlon:
        nums = [float(x) for tok in args.latlon for x in tok.replace(",", " ").split()]
        if len(nums) != 2:
            ap.error("--latlon needs exactly two numbers: LAT LON")
        lat, lon = nums
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
