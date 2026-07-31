#!/usr/bin/env python3
"""
Resolve a Murray, Utah address (or lat/long) to its City Council DISTRICT (1-5).

Murray uses a council-mayor (executive-mayor / "strong mayor") form: 5 district council
seats (Districts 1-5), one member each, plus a separately-elected EXECUTIVE Mayor who
presides over the city but NOT the council and casts NO vote (the council elects its own
Chair/Vice-Chair). There are NO at-large council seats. This tool resolves the DISTRICT
seat only; the Mayor is city-wide, has no district, and is not returned.

Pipeline:
  address --[Census geocoder, free]--> lat/long
  lat/long --[point-in-polygon vs districts.geojson]--> District 1-5

The district polygons come from Murray's OWN city GIS ("Murray City Council Districts",
authoritative, whole-city, redistricted after the 2020 census -- boundaries approved
2022-01-04), so this resolves directly against the official district outlines. No
precinct->district lookup table is required for the address tool (precinct_to_district.csv
is provided separately as a join aid for by-precinct election data).

CLI:
    python3 address_to_district.py "5025 S State St, Murray, UT 84107"
    python3 address_to_district.py --latlon "40.6669 -111.8880"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt          # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("5025 S State St, Murray, UT 84107")
    # -> {"district": "2", "council_member": "...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API, free, no key). lat/long lookups are fully offline.
  - The Mayor is city-wide/executive; has no district and is not returned.
  - District polygons are Murray only; points outside the city return district None.
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

# Current district councilmembers (Murray recon.md roster, as of the 2026-07-11 build).
# The city GIS layer carries a Council_Member field, but D3's is slightly stale (it reads
# "Scott Goodman", the 2025 interim); Clark Bullen won the 2025 D3 2-year special and was
# sworn Jan 2026. Names are attached here for convenience -- update after each election.
# The Mayor (Brett A. Hales) is city-wide/executive and intentionally not part of this map.
COUNCIL_MEMBERS = {
    "1": "Paul Pickett Acevedo",
    "2": "Pam Cotter",
    "3": "Clark Bullen",
    "4": "Diane Turner",
    "5": "Adam Hock",
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
    """lat/long -> {district, council_member} (offline). district None if outside Murray."""
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
        return f"  ({head}) -> outside Murray council districts"
    member = res.get("council_member")
    mem = f" ({member})" if member else ""
    return (f"  {head}\n    -> Council District {res['district']}{mem}"
            f"\n    (plus the city-wide Mayor)")


def main():
    ap = argparse.ArgumentParser(description="Murray address/point -> council district (1-5)")
    ap.add_argument("address", nargs="?", help="a street address to resolve")
    # nargs=2 with a negative LON trips argparse's flag parser; accept the pair as
    # a single token too, e.g. --latlon "40.67 -111.89".
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
