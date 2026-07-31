#!/usr/bin/env python3
"""
Resolve a South Salt Lake, Utah address (or lat/long) to its City Council DISTRICT (1-5).

South Salt Lake has a SEVEN-member council form: 5 geographic district seats
(Districts 1-5) PLUS 2 AT-LARGE seats, plus a separately-elected executive Mayor. This
tool resolves the geographic DISTRICT seat only (1-5). Every South Salt Lake resident is
ADDITIONALLY represented by BOTH at-large council members AND the city-wide Mayor -- those
three seats are city-wide (no polygon) and are noted, not point-resolved.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs districts.geojson]--> District 1-5

The district polygons come from South Salt Lake's OWN official ArcGIS FeatureServer
("South Salt Lake City Council Districts", field CITY_COUNC = 1..5), authoritative and
whole-city, so this resolves directly against the district outlines -- no precinct->district
lookup is required for the address tool. (precinct_to_district.csv is provided separately as
a join aid for by-precinct election data.)

CLI:
    python3 address_to_district.py "220 E Morris Ave, South Salt Lake, UT 84115"
    python3 address_to_district.py --latlon "40.7089 -111.8883"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("220 E Morris Ave, South Salt Lake, UT 84115")
    # -> {"district": "...", "council_member": "...", "at_large": [...], "mayor": "...", ...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The 2 At-Large members and the Mayor are city-wide; they have no district and are
    returned as context, not resolved by point.
  - District polygons are South Salt Lake only; points outside the city return district None.
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

# Current district councilmembers (from the 2026-06-10 council-minutes header +
# sslc.gov/160/City-Council, as of the 2026-07-12 build). The official GIS layer stores
# only the district NUMBER (field "CITY_COUNC"); member names are attached here for
# convenience and need updating after each election / appointment.
#
# NOTE: the ELECTED 2023 winners for D1 (LeAnne Huff) and D5 (Paul Sanchez) differ from
# the 2026 SERVING members below (Glad / Jones) -- mid-term changes occurred after the
# 2023 election; see ../VERIFICATION.md and ../election_results/CLAUDE.md.
COUNCIL_MEMBERS = {
    "1": "Joy Glad",
    "2": "Corey Thomas",
    "3": "Sharla Bynum",       # Council Chair (presiding)
    "4": "Nick Mitchell",
    "5": "Irvin Jones",
}
# City-wide seats (not point-resolved): 2 At-Large council members + executive Mayor.
AT_LARGE = ["Ray deWolfe", "Clarissa Williams"]
MAYOR = "Cherie Wood"
# The official district layer stores the district number in this field.
DISTRICT_FIELD = "CITY_COUNC"


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
    """lat/long -> {district, council_member, at_large, mayor} (offline).
    district None if outside South Salt Lake."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "at_large": AT_LARGE,
                "mayor": MAYOR, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    raw = row.get(DISTRICT_FIELD, "")
    name = str(int(raw)) if isinstance(raw, float) else str(raw).strip()
    name = name or None
    return {"district": name, "council_member": COUNCIL_MEMBERS.get(name),
            "at_large": AT_LARGE, "mayor": MAYOR, "lat": lat, "lon": lon}


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"district": None, "council_member": None, "at_large": AT_LARGE,
                "mayor": MAYOR, "matched_address": None, "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    tail = (f"\n    (plus 2 city-wide At-Large members: {', '.join(res['at_large'])}"
            f"; and Mayor {res['mayor']})")
    if not res.get("district"):
        return f"  ({head}) -> outside South Salt Lake council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return f"  {head}\n    -> Council District {res['district']}{mem}{tail}"


def main():
    ap = argparse.ArgumentParser(
        description="South Salt Lake address/point -> council district (1-5)")
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
                print(line)
                print(_fmt(district_for_address(line)))
    elif args.address:
        print(_fmt(district_for_address(args.address)))
    else:
        ap.error("provide an address, --latlon LAT LON, or --batch FILE")


if __name__ == "__main__":
    main()
