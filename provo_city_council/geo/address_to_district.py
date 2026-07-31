#!/usr/bin/env python3
"""
Resolve a Provo, Utah address (or lat/long) to its Municipal Council DISTRICT.

Provo Municipal Council = 7 members: Districts 1-5 (geographic) + 2 citywide seats
(Citywide I & II) + a separately elected Mayor. This tool returns the DISTRICT (1-5)
for a location. The two citywide councilmembers and the Mayor represent everyone, so
they are not returned here.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs geo/precincts.geojson]--> PRECINCT (e.g. 25PR04)
  PRECINCT --[precinct_to_district.csv]--> Council District (1-5)

precincts.geojson already carries COUNCIL_DISTRICT (it's the city GIS layer), but we go
through precinct_to_district.csv so the same lookup can be rebuilt from election data for
historical/redistricting questions (python3 build_precinct_district_map.py).

CLI:
    python3 address_to_district.py "445 W Center St, Provo, UT 84601"
    python3 address_to_district.py --latlon 40.2338 -111.6585      # offline
    python3 address_to_district.py --batch addresses.txt           # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("445 W Center St, Provo, UT 84601")
    # -> {"district": "3", "precinct": "25PR...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The district map is CURRENT (post-2023-cycle redistricting). Rebuild for historical
    questions. Provo redistricted between 2021 and 2025; precinct numbering changed.
  - Citywide I/II councilmembers and the Mayor are citywide and are not returned.
  - Boundaries cover only Provo's precincts; points outside Provo return district None.
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
        sys.exit(f"Missing {MAP_CSV.name}. Run: python3 build_precinct_district_map.py")
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
    """lat/long -> {district, precinct} (offline). district None if outside Provo precincts."""
    from shapely.geometry import Point
    prec = _precincts()
    hit = prec[prec.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "precinct": None, "lat": lat, "lon": lon}
    pid = str(hit.iloc[0]["PRECINCT"])
    return {"district": _precinct_to_district().get(pid), "precinct": pid,
            "lat": lat, "lon": lon}


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
        return f"  ({res.get('matched_address','')}) -> outside Provo council precincts"
    d = res["district"] or "(precinct not in council map)"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    return f"  {head}\n    -> precinct {res['precinct']} -> Council District {d}"


def main():
    ap = argparse.ArgumentParser(description="Provo address/point -> council district")
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
