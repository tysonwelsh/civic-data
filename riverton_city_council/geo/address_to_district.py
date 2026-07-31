#!/usr/bin/env python3
"""
Resolve a Riverton, Utah address (or lat/long) to its City Council DISTRICT (1-5).

Riverton has a six-member council form: 5 district council seats (Districts 1-5) plus a
separately-elected Mayor (city-wide; the Mayor chairs the council and votes only to break a
tie). There are NO at-large council seats -- the Mayor is the only city-wide elected
official. This tool resolves the DISTRICT seat only; every Riverton resident is additionally
represented by the city-wide Mayor (not returned).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs districts.geojson]--> District 1-5

The district polygons come from Riverton's OWN city ArcGIS Server (the current
"Riverton_City_Council_Districts_2022" layer, post-Ordinance 22-07; field DIST_NAME =
"D1".."D5"), which covers the whole city -- so this resolves directly against the district
outlines, no precinct->district lookup table required. (precinct_to_district.csv is provided
separately as a join aid for by-precinct election data.)

DISTRICT-NUMBER CAVEAT (read before joining people across 2022): Ordinance 22-07 (2022)
renumbered the districts. The authoritative election record shows Tawnee McCay winning
"District 3" and Tish Buroker winning "District 4" (2017 & 2021) -- and the retained
pre-2022 layer (districts_pre2022.geojson) agrees (D3=McCay, D4=Buroker) -- whereas the
CURRENT 2022 layer used here assigns D3/D4 to their successors' geography with the numbers
SWAPPED. So the seat NUMBER is not stable across the 2022 boundary; this tool returns the
CURRENT (2022) district number. Use districts_pre2022.geojson for pre-2022 questions.

CLI:
    python3 address_to_district.py "12830 S 1700 W, Riverton, UT 84065"
    python3 address_to_district.py --latlon "40.5219 -111.9391"   # quote the pair (negative LON)
    python3 address_to_district.py --pre2022 "12830 S 1700 W, Riverton, UT 84065"
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("12830 S 1700 W, Riverton, UT 84065")
    # -> {"district": "3", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - District polygons are Riverton only; points outside the city return district None.
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
DISTRICTS_GEOJSON = BASE / "districts.geojson"
DISTRICTS_PRE2022_GEOJSON = BASE / "districts_pre2022.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


@lru_cache(maxsize=2)
def _districts(pre2022=False):
    import geopandas as gpd
    path = DISTRICTS_PRE2022_GEOJSON if pre2022 else DISTRICTS_GEOJSON
    return gpd.read_file(path).to_crs("EPSG:4326")


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


def district_for_point(lon, lat, pre2022=False):
    """lat/long -> {district, council_member} (offline). district None if outside Riverton.

    The layer stores the district as DIST_NAME ("D1".."D5") and the sitting member as NAME.
    Set pre2022=True to resolve against the pre-Ordinance-22-07 (2019) boundaries/numbers."""
    from shapely.geometry import Point
    dist = _districts(pre2022)
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon,
                "vintage": "pre2022" if pre2022 else "2022"}
    row = hit.iloc[0]
    # field names differ in case between the two layers (DIST_NAME vs dist_name; NAME vs name)
    dn = row.get("DIST_NAME", row.get("dist_name", ""))
    name = str(dn).strip().lstrip("Dd") or None
    member = row.get("NAME", row.get("name", "")) or None
    return {"district": name, "council_member": (str(member).strip() or None),
            "lat": lat, "lon": lon, "vintage": "pre2022" if pre2022 else "2022"}


def district_for_address(address, pre2022=False):
    g = geocode(address)
    if not g:
        return {"district": None, "council_member": None, "matched_address": None,
                "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat, pre2022=pre2022)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    vin = res.get("vintage", "2022")
    if not res.get("district"):
        return f"  ({head}) -> outside Riverton council districts [{vin} boundaries]"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem} [{vin} boundaries]"
            f"\n    (plus the city-wide Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Riverton address/point -> council district (1-5)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs with a negative LON trips argparse's flag parser; accept the pair as one token.
    ap.add_argument("--latlon", nargs="+", type=str, metavar=("LAT", "LON"))
    ap.add_argument("--batch", metavar="FILE", help="file with one address per line")
    ap.add_argument("--pre2022", action="store_true",
                    help="resolve against the pre-Ordinance-22-07 (2019) district lines/numbers")
    args = ap.parse_args()

    if args.latlon:
        nums = [float(x) for tok in args.latlon for x in tok.replace(",", " ").split()]
        if len(nums) != 2:
            ap.error("--latlon needs exactly two numbers: LAT LON")
        lat, lon = nums
        print(_fmt(district_for_point(lon, lat, pre2022=args.pre2022)))
    elif args.batch:
        for line in Path(args.batch).read_text().splitlines():
            line = line.strip()
            if line:
                print(line); print(_fmt(district_for_address(line, pre2022=args.pre2022)))
    elif args.address:
        print(_fmt(district_for_address(args.address, pre2022=args.pre2022)))
    else:
        ap.error("provide an address, --latlon LAT LON, or --batch FILE")


if __name__ == "__main__":
    main()
