#!/usr/bin/env python3
"""
Resolve a Taylorsville, Utah address (or lat/long) to its City Council DISTRICT (1-5).

Taylorsville uses a council-mayor (executive-mayor) form: 5 district council seats
(Districts 1-5), one member each, plus a separately-elected executive Mayor. There are
NO at-large council seats and the Mayor does NOT vote on ordinary council motions. This
tool resolves the DISTRICT seat only; every resident is additionally represented by the
city-wide Mayor (executive, not returned here).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs council_districts.geojson]--> District 1-5

IMPORTANT — the district polygons are PRECINCT-DERIVED, not an official city layer.
Taylorsville publishes no council-district FeatureServer (recon.md §6), so the polygons in
council_districts.geojson were built by dissolving Salt Lake County precincts (UGRC
VistaBallotAreas, CountyID=18) grouped by the district each precinct voted in, per the
2023 (D1-3) + 2025 (D4-5) general-election district contests. They reflect the CURRENT
post-2020-census redistricting. See geo/CLAUDE.md for the method, vintage, and caveats.

CLI:
    python3 address_to_district.py "2600 W Taylorsville Blvd, Taylorsville, UT 84129"
    python3 address_to_district.py --latlon "40.6677 -111.9388"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("2600 W Taylorsville Blvd, Taylorsville, UT 84129")
    # -> {"district": "3", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide/executive; has no district and is not returned.
  - District polygons are Taylorsville only; points outside the city return district None.
  - Precinct-derived boundaries follow precinct lines, which approximate but do not exactly
    equal the legal district lines (municipal code 13.04.100); treat near-boundary results
    as approximate.
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

# Current district councilmembers (from the 2025-09-03 council-minutes header and
# taylorsvilleut.gov/government/elected-officials/council, as of the 2026-07-06 build).
# The precinct-derived district layer stores only the district NUMBER (field "district");
# member names are attached here for convenience and need updating after each election.
# The Mayor (Kristie Steadman Overson) is the city-wide executive and is intentionally
# not part of this district map.
COUNCIL_MEMBERS = {
    "1": "Ernest (Ernie) Glen Burgess",
    "2": "Curt Cochran",
    "3": "Anna Barbieri",
    "4": "Meredith Harker",   # Council Chair
    "5": "Bob Knudsen",       # Vice Chair
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
    """lat/long -> {district, council_member} (offline). district None if outside Taylorsville."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    # the dissolved layer's district id lives in the "district" field (values "1".."5")
    name = str(row.get("district", "")).strip() or None
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
        return f"  ({head}) -> outside Taylorsville council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide executive Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Taylorsville address/point -> council district (1-5)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs=2 with a negative LON trips argparse's flag parser; accept the pair as
    # a single token too, e.g. --latlon "40.66 -111.94".
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
