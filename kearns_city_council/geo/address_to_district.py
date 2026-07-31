#!/usr/bin/env python3
"""
Resolve a Kearns, Utah address (or lat/long) to its CITY Council district.

Kearns became a CITY in 2024 (first city election 2025-11-04). The city form is a
directly-elected **voting Mayor + 4 district Council Members (Districts 1-4)**. This tool
resolves the district seat by point-in-polygon against `districts.geojson`.

⚠ TWO IMPORTANT LIMITS (both honest, documented in geo/CLAUDE.md):
  1. **City districts are 2025+ only.** The metro-township era (2017-2025) used five
     numbered council districts on a different map; this tool is CITY-ERA geography only.
  2. **Only D2 and D4 are known precisely.** The 2025 ballot elected only Mayor + D2 + D4,
     so the SOVC assigns precincts to D2 and D4 authoritatively. Districts 1 and 3 were NOT
     on the 2025 ballot (their holdovers Schaeffer & Butterfield carried 2023 township terms
     into the city seats; next elected ~2027), so the SOVC cannot split D1 from D3. Points in
     that residual area return district "1/3" (District 1 OR 3 — undetermined) until the
     city's official 4-district map is obtained.

Every resident is also represented by the city-wide **Mayor Jesse Valdez** (voting; presides).

Pipeline:  address --[Census geocoder, free]--> lat/long --[point-in-polygon]--> district

CLI:
    python3 address_to_district.py "5624 S Cougar Ln, Kearns, UT 84118"
    python3 address_to_district.py --latlon "40.653 -112.010"   # quote the pair (negative LON)
    python3 address_to_district.py --batch addresses.txt
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

# City-era officeholders (2025 election). D1/D3 holders (Schaeffer, Butterfield) won 2023
# township seats and carried unexpired terms into the city D1/D3 seats; the D1-vs-D3
# assignment is not resolvable from the 2025 SOVC (those seats were not on the ballot).
COUNCIL_MEMBERS = {
    "2": "Lyndsay Longtin",
    "4": "Lorrin Colby Jr.",
    "1/3": "Patrick Schaeffer / Chrystal Butterfield (D1 & D3; which-is-which undetermined)",
}
MAYOR = "Jesse Valdez"  # city-wide, voting


@lru_cache(maxsize=1)
def _districts():
    import geopandas as gpd
    return gpd.read_file(DISTRICTS_GEOJSON).to_crs("EPSG:4326")


def geocode(address):
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
    """lat/long -> {district, council_member, unsplit} (offline). None if outside Kearns."""
    from shapely.geometry import Point
    dist = _districts()
    hit = dist[dist.contains(Point(lon, lat))]
    if hit.empty:
        return {"district": None, "council_member": None, "unsplit": False,
                "lat": lat, "lon": lon}
    row = hit.iloc[0]
    name = str(row.get("district", "")).strip() or None
    return {"district": name, "council_member": COUNCIL_MEMBERS.get(name),
            "unsplit": (name == "1/3"), "mayor": MAYOR, "lat": lat, "lon": lon}


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
        return f"  ({head}) -> outside the Kearns city boundary"
    d = res["district"]; member = res.get("council_member")
    if d == "1/3":
        body = (f"    -> Council District 1 or 3 (UNDETERMINED — 2025 SOVC did not split "
                f"D1/D3)\n       held by {member}")
    else:
        body = f"    -> Council District {d} ({member})"
    return f"  {head}\n{body}\n    (plus the city-wide voting Mayor, {MAYOR})"


def main():
    ap = argparse.ArgumentParser(description="Kearns address/point -> city council district (2, 4, or 1/3)")
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
