#!/usr/bin/env python3
"""
Resolve a Draper, Utah address (or lat/long) to its city-council representation.

Draper elects **ALL AT-LARGE**: a separately-elected **Mayor** (city-wide, executive,
non-voting on the council) + **5 Council Members elected AT-LARGE** — there are **NO
council districts**. So the "which district am I in?" question is degenerate: every
Draper resident is represented by **the same 5 at-large Council Members + the Mayor**.
The only geographic question that matters is **in Draper or not** — and Draper straddles
**two counties** (Salt Lake FIPS 49035 + Utah FIPS 49049), so the city limit itself
crosses the county line. This tool answers in/out by point-in-polygon against the full
two-county **city boundary** (`city_boundary.geojson`) and, when inside, reports the
at-large seat basis and (best-effort) which of Draper's precincts the point falls in.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in Draper? + At-Large seats

CLI:
    python3 address_to_district.py "1020 E Pioneer Rd, Draper, UT 84020"
    python3 address_to_district.py --latlon "40.5247 -111.8638"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_point(-111.8638, 40.5247)
    # -> {"in_draper": True, "seat_basis": "At-Large", "council_members": [...],
    #     "mayor": "...", "precinct": "DRP0..", "county": "Salt Lake", "lat":.., "lon":..}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - There are NO districts — the resolver never returns a district number; it returns the
    at-large body (all 5 seats are city-wide) + the city-wide Mayor.
  - Points outside the Draper city limit return in_draper=False.
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
BOUNDARY_GEOJSON = BASE / "city_boundary.geojson"
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# Draper is AT-LARGE: these 5 Council Members + the Mayor represent EVERY resident
# city-wide (no districts). From the city site (mayor-and-council/) as of the 2026 build;
# hand-maintained — update after each election. T. Lowery (Tasha) != F. Lowry (Fred).
MAYOR = "Troy K. Walker"          # city-wide, executive, non-voting on the council
COUNCIL_AT_LARGE = [
    "Mike Green",
    "Bryn Heather Johnson",
    "Tasha Lowery",
    "Fred Lowry",
    "Kathryn Dahlin",             # new 2025 (succeeded Marsha Vawdrey)
]


@lru_cache(maxsize=1)
def _boundary():
    import geopandas as gpd
    return gpd.read_file(BOUNDARY_GEOJSON).to_crs("EPSG:4326")


@lru_cache(maxsize=1)
def _precincts():
    import geopandas as gpd
    return gpd.read_file(PRECINCTS_GEOJSON).to_crs("EPSG:4326")


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
    """lat/long -> at-large representation (offline). in_draper False if outside the city."""
    from shapely.geometry import Point
    pt = Point(lon, lat)
    bnd = _boundary()
    inside = bnd[bnd.contains(pt)]
    if inside.empty:
        return {"in_draper": False, "seat_basis": None, "council_members": None,
                "mayor": None, "precinct": None, "county": None, "lat": lat, "lon": lon}
    county = str(inside.iloc[0].get("county", "")).strip() or None
    # best-effort precinct (informational; Draper is at-large so it carries no seat)
    prec = pcounty = None
    pr = _precincts()
    hit = pr[pr.contains(pt)]
    if not hit.empty:
        prec = str(hit.iloc[0].get("precinct", "")) or None
        pcounty = str(hit.iloc[0].get("county", "")) or None
    return {"in_draper": True, "seat_basis": "At-Large",
            "council_members": list(COUNCIL_AT_LARGE), "mayor": MAYOR,
            "precinct": prec, "county": pcounty or county, "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"in_draper": None, "seat_basis": None, "council_members": None,
                "mayor": None, "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_draper"):
        return f"  ({head}) -> OUTSIDE Draper city limits"
    prec = f", precinct {res['precinct']}" if res.get("precinct") else ""
    cty = f" [{res['county']} County]" if res.get("county") else ""
    members = ", ".join(res["council_members"])
    return (f"  {head}{cty}{prec}\n"
            f"    -> IN Draper — seat basis: At-Large (no districts)\n"
            f"    -> represented by all 5 at-large Council Members: {members}\n"
            f"    -> plus the city-wide Mayor: {res['mayor']}")


def main():
    ap = argparse.ArgumentParser(
        description="Draper address/point -> in-city + at-large representation (NO districts)")
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
