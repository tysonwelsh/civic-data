#!/usr/bin/env python3
"""
Resolve a Town of Copperton, Utah address (or lat/long) to its representation.

Copperton uses Utah's **Town** form (converted from a metro township 2024-05-01):
a separately-elected **Mayor** plus a **4-member Town Council, ALL elected AT-LARGE**.
There are **NO council districts** — every resident is represented by the single at-large
council body (seats A-E, lettered but town-wide) and the town-wide Mayor. So the only
geographic question is binary: is a point **inside the Town of Copperton** or not.

This tool answers that by point-in-polygon against the town boundary
(`city_boundary.geojson`, UGRC UtahMunicipalBoundaries NAME='Copperton', COUNTYNBR 18).
A point inside returns district "At-Large"; a point outside returns None.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in Copperton? -> "At-Large"

CLI:
    python3 address_to_district.py "8725 Hillcrest St, Copperton, UT 84006"
    python3 address_to_district.py --latlon "40.5668 -112.0987"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_point(-112.0987, 40.5668)
    # -> {"district": "At-Large", "in_copperton": True, "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - Copperton is AT-LARGE — there are no sub-districts; the return is "At-Large" or None.
  - The council body (2026): Mayor Sean Clayton (voting) + Mayor Pro Tem Tessa Stitzer,
    Kathleen Bailey, Linda McCalmon, Jonathan Pratt. All at-large / town-wide.
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

# Town-wide elected officials (from copperton.utah.gov/meet-copperton-council + 2025 minutes
# + Jan-2026 swearing-in, as of the 2026-07-12 build). All AT-LARGE / town-wide; there are
# no districts. Names are attached for convenience and need updating after each election.
COUNCIL_AT_LARGE = [
    "Sean Clayton (Mayor)",
    "Tessa Stitzer (Mayor Pro Tempore)",
    "Kathleen Bailey",
    "Linda McCalmon",
    "Jonathan Pratt",
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
    """lat/long -> {district, in_copperton} (offline). district None if outside Copperton."""
    from shapely.geometry import Point
    b = _boundary()
    inside = bool(b.contains(Point(lon, lat)).any())
    return {"district": "At-Large" if inside else None,
            "in_copperton": inside,
            "council": COUNCIL_AT_LARGE if inside else None,
            "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "in_copperton": False, "council": None,
                "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_copperton"):
        return f"  ({head}) -> outside the Town of Copperton"
    return (f"  {head}\n    -> Town of Copperton (At-Large council; no districts)"
            f"\n    represented by: {', '.join(res['council'])}")


def main():
    ap = argparse.ArgumentParser(
        description="Copperton address/point -> in Town of Copperton (At-Large) or None")
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
                print(line)
                print(_fmt(district_for_address(line)))
    elif args.address:
        print(_fmt(district_for_address(args.address)))
    else:
        ap.error("provide an address, --latlon LAT LON, or --batch FILE")


if __name__ == "__main__":
    main()
