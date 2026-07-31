#!/usr/bin/env python3
"""
Resolve a Bluffdale, Utah address (or lat/long) to its City Council representation.

Bluffdale is an **AT-LARGE** city: a Mayor elected citywide + **5 Council Members, ALL
elected at-large** (NO districts, NO ward/precinct seats). Every Bluffdale resident is
therefore represented by the **same** six officials regardless of address. There is no
"which district am I in?" question to answer -- the only geographic question is
**"is this point inside Bluffdale?"** So this tool is an inside/outside-city test:

  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in Bluffdale?  (seat basis: At-Large)

Bluffdale straddles **two counties**: the populated part is in **Salt Lake County**; a
small southern/western portion falls in **Utah County** (Camp Williams / undeveloped,
essentially unpopulated). The city boundary polygon spans both, so this tool resolves
points in either county's slice of the city. Salt Lake County administers all Bluffdale
municipal elections.

CLI:
    python3 address_to_district.py "2222 W 14400 S, Bluffdale, UT 84065"
    python3 address_to_district.py --latlon "40.489 -111.939"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_point(-111.939, 40.489)
    # -> {"in_bluffdale": True, "seat_basis": "At-Large", "council": {...}, ...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - There are no council districts; the returned "district" is always "At-Large" (or None
    if the point is outside Bluffdale). Every in-city point maps to the same Mayor + 5
    at-large Council Members.
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

# Bluffdale is at-large: these SIX officials represent EVERY address in the city.
# Mayor presides but does NOT vote on ordinary motions (six-member mayor-council form).
# Roster as of the 2026-2029 term (2025 election winners + continuing 2023 winners).
# Update after each election; the boundary layer carries no member field.
MAYOR = "Natalie Hall"
COUNCIL_AT_LARGE = [
    "Wendy Aston",     # 2026-2029 (re-elected 2025)
    "Mackey Smith",    # 2026-2029 (new 2025; seat previously Traci Crockett)
    "Steve Austin",    # 2024-2027 (elected 2023)
    "Alan Lord",       # 2024-2027 (elected 2023)
    "Greg Wilding",    # 2024-2027 (elected 2023)
]


@lru_cache(maxsize=1)
def _boundary():
    import geopandas as gpd
    from shapely.ops import unary_union
    gdf = gpd.read_file(BOUNDARY_GEOJSON).to_crs("EPSG:4326")
    # the municipal-boundaries layer returns Bluffdale as 2 polygons (the Salt Lake +
    # Utah county slices); union them into one city footprint.
    return unary_union(list(gdf.geometry))


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
    """lat/long -> representation dict (offline).

    in_bluffdale True/False; when True, district='At-Large' and the citywide Mayor + 5
    at-large Council Members are returned (they represent every Bluffdale address)."""
    from shapely.geometry import Point
    inside = _boundary().contains(Point(lon, lat))
    if not inside:
        return {"in_bluffdale": False, "district": None, "seat_basis": None,
                "mayor": None, "council_at_large": None, "lat": lat, "lon": lon}
    return {"in_bluffdale": True, "district": "At-Large", "seat_basis": "At-Large",
            "mayor": MAYOR, "council_at_large": list(COUNCIL_AT_LARGE),
            "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"in_bluffdale": None, "district": None, "seat_basis": None,
                "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_bluffdale"):
        return f"  ({head}) -> outside Bluffdale city limits"
    council = ", ".join(res["council_at_large"])
    return (f"  {head}\n    -> in Bluffdale (seat basis: At-Large -- no districts)"
            f"\n    Mayor (citywide, presides, non-voting): {res['mayor']}"
            f"\n    Council (5 at-large, represent every address): {council}")


def main():
    ap = argparse.ArgumentParser(
        description="Bluffdale address/point -> in-city? (at-large: same Mayor + 5 council everywhere)")
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
