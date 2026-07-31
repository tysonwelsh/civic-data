#!/usr/bin/env python3
"""
Resolve a Millcreek, Utah address (or lat/long) to its City Council DISTRICT (1-4).

Millcreek uses a COUNCIL-MAYOR form: 4 district council seats (Districts 1-4) plus a
separately-elected, city-wide Mayor. There are NO at-large council seats -- the Mayor is
the only city-wide elected official (and, unlike South Jordan, the Millcreek mayor is a
full VOTING member of the council; that nuance concerns vote extraction, not geography).
This tool resolves the DISTRICT seat only; every Millcreek resident is additionally
represented by the city-wide Mayor (not returned).

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs council_districts.geojson]--> District 1-4

The district polygons come from Millcreek's OWN city GIS ("Millcreek City Council Districts
2022-2032", authoritative, covers the whole city), so this resolves directly against the
district outlines -- no precinct->district lookup table is required for the address tool.
(precinct_to_district.csv is provided separately as a join aid for by-precinct election
data.)

VINTAGE: the district polygons are the 2022-2032 redistricting boundaries. For votes or
elections BEFORE 2022, Millcreek used the original 2016 incorporation lines -- this tool
will mis-assign addresses near a boundary that moved. Source the earlier boundary
separately if pre-2022 address->district accuracy matters.

CLI:
    python3 address_to_district.py "3330 S 1300 E, Millcreek, UT 84106"
    python3 address_to_district.py --latlon "40.6899 -111.8571"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("3330 S 1300 E, Millcreek, UT 84106")
    # -> {"district": "3", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide; has no district and is not returned.
  - District polygons are Millcreek only; points outside the city return district None.
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

# Current district councilmembers. The city GIS district layer DOES carry the sitting
# member per polygon (field "COUNCILMEMBER"); the map below mirrors that layer's values
# (2022-2032 vintage, as of the 2026-07-06 build) so member names resolve even for
# --latlon lookups that never touch the geometry attributes. Update after each election.
# The Mayor (Cheri Jackson, city-wide, a full voting member) has no district and is not
# part of this map.
COUNCIL_MEMBERS = {
    "1": "Silvia Catten",
    "2": "Thom DeSirant",
    "3": "Nicole Handy",
    "4": "Bev Uipi",
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


def _district_id(row):
    """Extract the bare district number ('1'..'4') from the layer's 'DIST' field
    (values 'District 1'.. 'District 4'). Falls back to a plain 'District'/'district' field."""
    for key in ("DIST", "District", "district"):
        val = row.get(key)
        if val is not None and str(val).strip():
            digits = "".join(ch for ch in str(val) if ch.isdigit())
            return digits or str(val).strip()
    return None


def district_for_point(lon, lat):
    """lat/long -> {district, council_member} (offline). district None if outside Millcreek."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "lat": lat, "lon": lon}
    row = hit.iloc[0]
    name = _district_id(row)
    # Prefer the layer's own COUNCILMEMBER value; fall back to the hand-kept map.
    member = row.get("COUNCILMEMBER")
    member = str(member).strip() if member is not None and str(member).strip() else COUNCIL_MEMBERS.get(name)
    return {"district": name, "council_member": member, "lat": lat, "lon": lon}


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
        return f"  ({head}) -> outside Millcreek council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Millcreek address/point -> council district (1-4)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs=2 with a negative LON trips argparse's flag parser; accept the pair as
    # a single token too, e.g. --latlon "40.69 -111.86".
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
