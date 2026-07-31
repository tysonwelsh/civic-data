#!/usr/bin/env python3
"""
Resolve an Ogden, Utah address (or lat/long) to its City Council DISTRICT (1-4).

Ogden elects a 7-member council: 4 DISTRICT seats (Districts 1-4) + 3 AT-LARGE seats
(Seats A, B, C), plus a separately-elected Mayor. The three at-large councilmembers and
the Mayor represent the WHOLE city, so this tool only resolves the DISTRICT seat -- every
Ogden resident is additionally represented by all three at-large members and the Mayor.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs precincts.geojson]--> PrecinctID (e.g. OGD15)
  PrecinctID --[precinct_to_district.csv  (== the MUNIWARD field)]--> Council District 1-4

The precinct->district map is the authoritative MUNIWARD field carried by Ogden City's own
GIS layer (Public/Ogden_Voting_Precincts). Regenerate it (and the polygons) by re-querying
that FeatureServer -- see geo/CLAUDE.md.

CLI:
    python3 address_to_district.py "2549 Washington Blvd, Ogden, UT 84401"
    python3 address_to_district.py --latlon 41.2230 -111.9706
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("2549 Washington Blvd, Ogden, UT 84401")
    # -> {"district": 1, "precinct": "OGD..", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The map is CURRENT (Ogden City GIS, 2025-era precincts). At-large seats (A/B/C) and the
    Mayor are city-wide; they have no district and are not returned.
  - Precinct boundaries are Ogden city only; points outside Ogden return district None.
"""

import argparse
import csv
import functools
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
MAP_CSV = BASE / "precinct_to_district.csv"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


@functools.lru_cache(maxsize=1)
def _precincts():
    import geopandas as gpd
    return gpd.read_file(PRECINCTS_GEOJSON).to_crs("EPSG:4326")


@functools.lru_cache(maxsize=1)
def _precinct_to_district():
    if not MAP_CSV.exists():
        sys.exit(f"Missing {MAP_CSV.name}. See geo/CLAUDE.md to regenerate it.")
    with open(MAP_CSV, newline="", encoding="utf-8") as f:
        return {r["precinct"]: r["district"] for r in csv.DictReader(f)}


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
    """lat/long -> {district, precinct} (offline). district None if outside Ogden precincts."""
    from shapely.geometry import Point
    prec = _precincts()
    hit = prec[prec.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "precinct": None, "lat": lat, "lon": lon}
    pid = str(hit.iloc[0]["PRECINCT"])
    d = _precinct_to_district().get(pid)
    return {"district": int(d) if d not in (None, "") else None,
            "precinct": pid, "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "precinct": None, "matched_address": None,
                "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    if not res.get("precinct"):
        return f"  ({res.get('matched_address','')}) -> outside Ogden city precincts"
    d = res["district"] or "(precinct not in council district map)"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    return (f"  {head}\n    -> precinct {res['precinct']} -> Council District {d}"
            f"\n    (plus 3 city-wide At-Large councilmembers + the Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Ogden address/point -> council district (1-4)")
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
