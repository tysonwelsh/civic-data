#!/usr/bin/env python3
"""
Resolve an Emigration Canyon, Utah address (or lat/long) to its council representation.

Emigration Canyon (Salt Lake County) has a **5-member council, ALL elected AT-LARGE**
(no wards/districts); the council selects one of its five as Mayor, who presides and
VOTES. There is therefore **no district to resolve** — every resident inside the city
boundary is represented by the same at-large body. This tool answers the only meaningful
geographic question here: **is this address inside Emigration Canyon?** — by
point-in-polygon against the UGRC municipal boundary. If inside, `district` is the sentinel
string **"At-Large"** (there is exactly one, city-wide seat class); if outside, None.

Emigration Canyon was a Metro Township (2017-2024) and is a CITY since 2024-05-01 — the
same at-large body throughout; this boundary/point test is unaffected by that change.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in Emigration Canyon? -> At-Large

CLI:
    python3 address_to_district.py "5025 E Emigration Canyon Rd, Salt Lake City, UT 84108"
    python3 address_to_district.py --latlon "40.7700 -111.7600"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_point(-111.76, 40.77)
    # -> {"district": "At-Large", "in_city": True, "council": [...5 members...], "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - There are NO districts and NO separately-elected mayor; the mayor is one of the five
    at-large members (council-selected) and is returned in the council list.
  - Points outside Emigration Canyon return district None / in_city False.
"""

import argparse
import json
from functools import lru_cache
from pathlib import Path
import subprocess
import urllib.parse

BASE = Path(__file__).resolve().parent
BOUNDARY_GEOJSON = BASE / "city_boundary.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# The current 5-member at-large council (from the 2026-05-19 council-minutes header;
# see recon.md / roster). All are city-wide; the Mayor is council-selected from the five.
# Update after each election (elections are at-large — no district field to maintain).
COUNCIL = [
    "David Brems (Mayor)",
    "Catherine Harris",
    "Jennifer Hawkes",
    "Robert Pinon",
    "Nicholas Griffith",
]


@lru_cache(maxsize=1)
def _boundary():
    import geopandas as gpd
    return gpd.read_file(BOUNDARY_GEOJSON).to_crs("EPSG:4326")


def district_for_point(lon, lat):
    """lat/long -> representation dict (offline). Inside Emigration Canyon -> 'At-Large'."""
    from shapely.geometry import Point
    b = _boundary()
    inside = bool(b.contains(Point(lon, lat)).any())
    return {
        "district": "At-Large" if inside else None,
        "in_city": inside,
        "council": list(COUNCIL) if inside else None,
        "lat": lat, "lon": lon,
    }


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


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "in_city": False, "council": None,
                "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_city"):
        return f"  ({head}) -> outside Emigration Canyon"
    members = "; ".join(res["council"])
    return (f"  {head}\n    -> inside Emigration Canyon (At-Large — no districts)"
            f"\n    represented by the 5-member at-large council: {members}")


def main():
    ap = argparse.ArgumentParser(
        description="Emigration Canyon address/point -> in-city? (At-Large; no districts)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs>=1 with a negative LON trips argparse's flag parser; accept the pair as one token.
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
