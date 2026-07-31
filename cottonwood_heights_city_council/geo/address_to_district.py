#!/usr/bin/env python3
"""
Resolve a Cottonwood Heights, Utah address (or lat/long) to its City Council
DISTRICT (1-4).

Cottonwood Heights uses a **4-district council + a separately-elected Mayor who
VOTES as a full member of the council** (there are NO at-large council seats).
This tool resolves the DISTRICT seat only; every CH resident is *also*
represented by the city-wide Mayor (Gay Lynn Bennion) — who has no district and
is not returned.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs districts.geojson]--> District 1-4

The district polygons come from Cottonwood Heights' OWN city GIS ("Council
Districts", authoritative, whole-city, current post-2020-census map), fetched via
the public gis.cwh.utah.gov mirror (see build_geo.py). The resolver reads the
district id from the layer's `DistrictID` field and the member name from `Member`
(both baked into districts.geojson) — no precinct lookup is needed for the
address tool. (precinct_to_district.csv is a separate join aid for by-precinct
election data.)

CLI:
    python3 address_to_district.py "2277 E Bengal Blvd, Cottonwood Heights, UT 84121"
    python3 address_to_district.py --latlon "40.6197 -111.8113"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("2277 E Bengal Blvd, Cottonwood Heights, UT 84121")
    # -> {"district": "2", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - District polygons are Cottonwood Heights only; points outside return district None.
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
DISTRICTS_GEOJSON = BASE / "districts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# Fallback member names by district (the districts.geojson `Member` field is the
# primary source; this map is only used if that field is blank). From the city's
# Council Districts layer + Elected Officials page (2026 build). The Mayor
# (Gay Lynn Bennion, 2026-2029) is city-wide and intentionally not part of this map.
COUNCIL_MEMBERS = {
    "1": "Matt Holton",
    "2": "Suzanne Hyland",
    "3": "Shawn Newell",
    "4": "Ellen Birrell",
}


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
    """lat/long -> {district, council_member} (offline). district None if outside CH."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    name = str(row.get("DistrictID", "")).strip() or None
    if name and name.endswith(".0"):
        name = name[:-2]
    member = (str(row.get("Member", "")).strip() or COUNCIL_MEMBERS.get(name))
    return {"district": name, "council_member": member or None,
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
        return f"  ({head}) -> outside Cottonwood Heights council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Cottonwood Heights address/point -> council district (1-4)")
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
