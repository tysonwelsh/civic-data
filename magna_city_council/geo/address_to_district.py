#!/usr/bin/env python3
"""
Resolve a Magna, Utah address (or lat/long) to its City Council DISTRICT (1-5).

Magna is a Salt Lake County metro township (2017) -> CITY (2024). It has a 5-member council
elected by single-member DISTRICTS (1-5); since the 2025 cycle there is ALSO a separately-
elected, citywide executive **Mayor** (Mick Sudbury -- presides, does NOT vote). This tool
resolves the DISTRICT seat only; every Magna resident is additionally represented by the
city-wide Mayor (not returned).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs districts.geojson]--> District 1-5

IMPORTANT -- districts are PRECINCT-DERIVED and MIXED-VINTAGE (Magna has no official district
GIS layer). D2/D4 are from the 2025 general (current lines); D1/D3/D5 are from the 2019 general
(PRE-2022 lines -- a redistricting happened between 2021 and 2025). Four precincts (MAG001,
MAG008, MAG009, MAG017) are UNRESOLVED under current lines and are excluded from the polygons:
a point inside Magna but outside every district polygon returns district None with an
"in Magna, district unresolved" note -- never a guess. See geo/CLAUDE.md +
precinct_to_district.csv for the full provenance.

CLI:
    python3 address_to_district.py "8952 W Magna Main St, Magna, UT 84044"
    python3 address_to_district.py --latlon "40.709 -112.101"    # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt         # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("8952 W Magna Main St, Magna, UT 84044")
    # -> {"district": "...", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - Points outside Magna -> district None ("outside Magna"). Points in Magna but in an
    unresolved precinct -> district None ("in Magna, district unresolved").
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
DISTRICTS_GEOJSON = BASE / "districts.geojson"
CITY_GEOJSON = BASE / "city_boundary.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# Current district council members (from magna.utah.gov/171/City-Council + the 2026-05-26
# council-minutes header, as of the 2026-07-12 build). Update after each election. The Mayor
# (Mick "Mickey" Sudbury) is city-wide + non-voting and is intentionally not part of this map.
COUNCIL_MEMBERS = {
    "1": "Steve Prokopis",
    "2": "Megan L. Olsen",
    "3": "Michael H. Jensen",
    "4": "Terry George",       # Mayor Pro Tem
    "5": "Audrey Pierce",
}


@lru_cache(maxsize=1)
def _districts():
    import geopandas as gpd
    return gpd.read_file(DISTRICTS_GEOJSON).to_crs("EPSG:4326")


@lru_cache(maxsize=1)
def _city():
    import geopandas as gpd
    return gpd.read_file(CITY_GEOJSON).to_crs("EPSG:4326")


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
    """lat/long -> {district, council_member, in_magna, note} (offline)."""
    from shapely.geometry import Point
    pt = Point(lon, lat)
    dist = _districts()
    hit = dist[dist.contains(pt)]
    if not hit.empty:
        row = hit.iloc[0]
        name = str(row.get("District", "")).strip() or None
        conf = str(row.get("confidence", "")).strip()
        note = "" if conf == "high" else "district lines PRE-2022 (precinct-derived, medium confidence)"
        return {"district": name, "council_member": COUNCIL_MEMBERS.get(name),
                "in_magna": True, "note": note, "lat": lat, "lon": lon}
    # not in any district polygon -- distinguish "outside Magna" vs "unresolved precinct"
    in_city = not _city()[_city().contains(pt)].empty
    note = ("in Magna, district unresolved (unassigned precinct -- see precinct_to_district.csv)"
            if in_city else "outside Magna")
    return {"district": None, "council_member": None, "in_magna": in_city,
            "note": note, "lat": lat, "lon": lon}


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
        return f"  ({head}) -> {res.get('note', 'no district')}"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    extra = f"\n    [{res['note']}]" if res.get("note") else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor, Mick Sudbury){extra}")


def main():
    ap = argparse.ArgumentParser(description="Magna address/point -> council district (1-5)")
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
