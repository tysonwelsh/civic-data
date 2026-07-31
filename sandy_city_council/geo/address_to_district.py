#!/usr/bin/env python3
"""
Resolve a Sandy, Utah address (or lat/long) to its City Council DISTRICT (1-4).

Sandy elects a 7-member council: 4 district seats + 3 at-large seats, plus a
separately-elected Mayor. The three at-large councilmembers and the Mayor represent
the WHOLE city, so this tool only resolves the DISTRICT seat -- every Sandy resident
is additionally represented by all three at-large members and the Mayor (city-wide,
not returned here).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs council_districts.geojson]--> District 1-4

The district polygons come from Sandy's OWN city GIS (authoritative, covers the whole
city), so this resolves directly against the district outlines -- no precinct->district
lookup table is required.

CLI:
    python3 address_to_district.py "10000 Centennial Pkwy, Sandy, UT 84070"
    python3 address_to_district.py --latlon "40.5689 -111.8958"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("10000 Centennial Pkwy, Sandy, UT 84070")
    # -> {"district": "2", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - At-large seats and the Mayor are city-wide; they have no district and are not returned.
  - District polygons are Sandy only; points outside Sandy return district None.
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
DISTRICTS_GEOJSON = BASE / "council_districts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


@lru_cache(maxsize=1)
def _districts():
    import geopandas as gpd
    return gpd.read_file(DISTRICTS_GEOJSON).to_crs("EPSG:4326")


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
    """lat/long -> {district, council_member} (offline). district None if outside Sandy."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    # "District 1" -> "1"
    name = str(row.get("Name", "")).replace("District", "").strip() or None
    return {"district": name, "council_member": row.get("Council_Member"),
            "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "council_member": None, "matched_address": None,
                "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("district"):
        return f"  ({head}) -> outside Sandy council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus 3 city-wide At-Large councilmembers + the Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Sandy address/point -> council district (1-4)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs=2 with a negative LON trips argparse's flag parser; accept the pair as
    # a single token too, e.g. --latlon "40.58 -111.86".
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
