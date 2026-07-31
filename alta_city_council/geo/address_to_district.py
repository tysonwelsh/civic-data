#!/usr/bin/env python3
"""
Resolve a Town of Alta, Utah address (or lat/long) to its representation.

⚠ Alta is AT-LARGE — there are NO council districts. The Town of Alta uses Utah's
**town** form of government: a town-wide (VOTING) **Mayor** plus a **4-member Town
Council, ALL elected AT-LARGE** (every council seat is filled town-wide; there are no
single-member districts to resolve). So unlike the district cities (South Jordan,
Taylorsville, Sandy...), the "address → district" question degenerates to a single
**point-in-polygon membership test**: *is this point inside the Town of Alta?* Every
Alta resident is represented by the entire council + the mayor, on an **At-Large** basis.

This tool therefore returns:
  { "in_alta": bool, "seat_basis": "At-Large" | None, "precinct": "ALT001"/"ALT002"/None,
    "representation": "Mayor + 4 at-large Town Council members" | None, lat, lon }

Geometry sources (true EPSG:4326):
  city_boundary.geojson  — UGRC Utah Municipal Boundaries, NAME='Alta' (COUNTYNBR=18,
                           Salt Lake County), single Polygon (Little Cottonwood Canyon).
  precincts.geojson      — UGRC VistaBallotAreas, CountyID=18, the 2 Alta precincts
                           (ALT001, ALT002). Optional: reports which precinct a point
                           falls in (both map to At-Large — see precinct_to_district.csv).

Pipeline:
  address --[Census geocoder, free, needs internet]--> lat/long
  lat/long --[point-in-polygon vs city_boundary.geojson]--> in_alta (offline)

CLI:
    python3 address_to_district.py "10230 E State Highway 210, Alta, UT 84092"
    python3 address_to_district.py --latlon "40.5884 -111.6386"   # quote the pair (neg LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_point(-111.6386, 40.5884)   # -> {"in_alta": True, "seat_basis": "At-Large", ...}

Notes:
  - Geocoding needs internet (Census API, free, no key); lat/long lookups are fully offline.
  - `district` is intentionally NOT a concept here (at-large). The key is `seat_basis`
    ("At-Large") and `in_alta`. A `district` alias == "At-Large" is included for callers
    that expect the sibling-city key.
  - Points outside the Town of Alta return in_alta=False (seat_basis None).
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

# Current elected officials (from townofalta.utah.gov/town-council/ + the 2026-06-17
# council-minutes header). Alta is at-large, so ALL of these represent EVERY resident;
# names are informational and need updating after each election. The Mayor VOTES.
MAYOR = "Roger Bourke"
COUNCIL_AT_LARGE = ["Elise Morgan (Mayor Pro Tem)", "Carolyn Anctil",
                    "Dan Schilling", "Craig Heimark"]


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


def _precinct_for(lon, lat):
    from shapely.geometry import Point
    try:
        prec = _precincts()
    except Exception:
        return None
    hit = prec[prec.contains(Point(lon, lat))]
    if hit.empty:
        return None
    row = hit.iloc[0]
    return str(row.get("PrecinctID") or row.get("VistaID") or "").strip() or None


def district_for_point(lon, lat):
    """lat/long -> at-large membership result (offline). in_alta False if outside the Town."""
    from shapely.geometry import Point
    inside = bool(_boundary().contains(Point(lon, lat)).any())
    if not inside:
        return {"in_alta": False, "seat_basis": None, "district": None,
                "precinct": None, "representation": None, "lat": lat, "lon": lon}
    return {"in_alta": True, "seat_basis": "At-Large", "district": "At-Large",
            "precinct": _precinct_for(lon, lat),
            "representation": "Mayor + 4 at-large Town Council members",
            "mayor": MAYOR, "council_at_large": COUNCIL_AT_LARGE,
            "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"in_alta": None, "seat_basis": None, "district": None,
                "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if not res.get("in_alta"):
        return f"  ({head}) -> OUTSIDE the Town of Alta"
    prec = res.get("precinct")
    ptxt = f" [precinct {prec}]" if prec else ""
    return (f"  {head}\n    -> IN the Town of Alta — seat basis: At-Large{ptxt}"
            f"\n    represented by: Mayor {MAYOR} (voting) + Council "
            f"{', '.join(COUNCIL_AT_LARGE)}"
            f"\n    (Alta elects all council seats town-wide; there are NO districts)")


def main():
    ap = argparse.ArgumentParser(
        description="Town of Alta address/point -> at-large membership (no districts)")
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
