#!/usr/bin/env python3
"""
Resolve a South Jordan, Utah address (or lat/long) to its City Council DISTRICT (1-5).

South Jordan has a six-member council form: 5 district council seats (Districts 1-5)
plus a separately-elected Mayor. There are NO at-large council seats -- the Mayor is
the only city-wide elected official. This tool resolves the DISTRICT seat only; every
South Jordan resident is additionally represented by the city-wide Mayor (not returned).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs council_districts.geojson]--> District 1-5

The district polygons come from South Jordan's OWN city GIS ("Council Districts 2020",
authoritative, covers the whole city), so this resolves directly against the district
outlines -- no precinct->district lookup table is required for the address tool.
(precinct_to_district.csv is provided separately as a join aid for by-precinct election
data.)

CLI:
    python3 address_to_district.py "1600 W Towne Center Dr, South Jordan, UT 84095"
    python3 address_to_district.py --latlon "40.5622 -111.9297"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("1600 W Towne Center Dr, South Jordan, UT 84095")
    # -> {"district": "3", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - District polygons are South Jordan only; points outside the city return district None.
"""

import argparse
import json
import subprocess
import urllib.parse
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
DISTRICTS_GEOJSON = BASE / "council_districts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# Current district councilmembers (from the 2025-03-18 council-minutes header and
# sjc.utah.gov/241/City-Council, as of the 2026-07-06 build). The city GIS layer stores
# only the district NUMBER (field "District"); member names are attached here for
# convenience and will need updating after each election. The Mayor (Dawn R. Ramsey) is
# city-wide and intentionally not part of this district map.
COUNCIL_MEMBERS = {
    "1": "Patrick Harris",
    "2": "Kathie L. Johnson",
    "3": "Don Shelton",
    "4": "Tamara Zander",
    "5": "Jason T. McGuire",
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
    """lat/long -> {district, council_member} (offline). district None if outside South Jordan."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    # the layer's district id lives in the "District" field (values "1".."5")
    name = str(row.get("District", "")).strip() or None
    return {"district": name, "council_member": COUNCIL_MEMBERS.get(name),
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
        return f"  ({head}) -> outside South Jordan council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor)")


def main():
    ap = argparse.ArgumentParser(description="South Jordan address/point -> council district (1-5)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs=2 with a negative LON trips argparse's flag parser; accept the pair as
    # a single token too, e.g. --latlon "40.56 -111.93".
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
