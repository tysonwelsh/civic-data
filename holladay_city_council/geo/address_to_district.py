#!/usr/bin/env python3
"""
Resolve a Holladay, Utah address (or lat/long) to its City Council DISTRICT (1-5).

Holladay has a Council-Manager form: 5 district council seats (Districts 1-5) plus a
Mayor elected at-large. There are NO at-large council seats -- the Mayor is the only
city-wide elected official (and, unlike an executive-mayor city, the Holladay Mayor also
VOTES on the council). This tool resolves the DISTRICT seat only; every Holladay resident
is additionally represented by the city-wide Mayor (not returned).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs council_districts.geojson]--> District 1-5

The district polygons are Holladay's OWN official ArcGIS layer -- "Holladay City Council
Districts, as amended 2022" (item d0cb510277ee4f0f989c9a5de4d0a6da) -- so this resolves
directly against the authoritative district outlines. No precinct->district lookup table is
needed for the address tool (precinct_to_district.csv is a separate join aid for by-precinct
election data).

CLI:
    python3 address_to_district.py "4580 S 2300 E, Holladay, UT 84117"
    python3 address_to_district.py --latlon "40.6592 -111.8210"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("4580 S 2300 E, Holladay, UT 84117")
    # -> {"district": "...", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - District polygons are Holladay only; points outside the city return district None.
  - Boundaries are the "as amended 2022" (post-2020-census) lines; pre-2022 address-history
    questions near a moved boundary may mis-assign.
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

# Current district councilmembers, seated Jan 2026 (from the official district layer's
# "Representative" field, corroborated by the 2026-02-05 council-minutes attendance block).
# The layer stores the district NUMBER ("District") and the representative name; both are
# used here. Update after each election. The Mayor (Paul Fotheringham) is city-wide and
# intentionally not part of this district map.
COUNCIL_MEMBERS = {
    "1": "David Sundwall",
    "2": "Matt Durham",
    "3": "Natalie Bradley",
    "4": "Drew Quinn",
    "5": "Emily Gray",
}
MAYOR = "Paul Fotheringham"


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
    """lat/long -> {district, council_member} (offline). district None if outside Holladay."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
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
        return f"  ({head}) -> outside Holladay council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor, {MAYOR})")


def main():
    ap = argparse.ArgumentParser(description="Holladay address/point -> council district (1-5)")
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
