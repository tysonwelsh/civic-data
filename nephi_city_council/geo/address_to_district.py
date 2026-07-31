#!/usr/bin/env python3
"""
Resolve a Nephi, Utah address (or lat/long) to its City Council representation.

  *** Nephi City Council is ENTIRELY AT-LARGE — there are ZERO districts. ***

The council is Mayor + 5 at-large members, all elected citywide (standard small-Utah-city
form; confirmed at-large by the 2025 ballot wording "2 seats at large"). There is no
ward/district map, so the classic "address -> council district" lookup is DEGENERATE:
every address inside the city is represented by the same six officials (Mayor + all 5
at-large councilmembers), and an address outside the city has no Nephi representation.

This tool therefore answers the only meaningful geographic question:
  "Is this address (or point) INSIDE the Nephi city limits?"

Pipeline:
  address --[Census geocoder, free, needs internet]--> lat/long
  lat/long --[point-in-polygon vs geo/city_boundary.geojson]--> in-city True/False

For context it also reports which voter precinct the point falls in
(geo/precincts.geojson, the Juab County / UGRC VistaBallotAreas in-city ballot areas that
overlap Nephi — 12NE3:I, 12NE4:I, 12NE5:I, 12NE6:I, 12NE7) — but precinct does NOT map to
a district here; it is purely informational / useful for joining by-precinct election data.

CLI:
    python3 address_to_district.py "21 E 100 N, Nephi, UT 84648"
    python3 address_to_district.py --latlon 39.7106 -111.8345
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("21 E 100 N, Nephi, UT 84648")
    # -> {"in_city": True, "district": None, "council": "at-large ...",
    #     "precinct": "12NE...", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API). lat/long lookups are fully offline.
  - CRS: geo/*.geojson are stored in EPSG:4326 (lon/lat). The UGRC source was
    requested with outSR=4326; coords verified as Utah lon/lat (~ -111.83, 39.71),
    NOT UTM(26912) meters (the WVC/slco-archive UTM-mislabel trap is avoided here).
  - City polygon fetched by NAME='NEPHI' from UGRC Utah Municipal Boundaries
    (1 feature; COUNTYNBR=12 Juab, FIPS=54220). Precincts by CountyID=12 spatially
    intersected with the city polygon (AliasName is blank for Juab precincts — name
    matching fails, spatial intersect works).
  - "district" keys are kept in the return dict for API parity with the SLC/St. George
    tools, but they are always None / "at-large" for Nephi (no districts).
"""

import argparse
import functools
import json
import subprocess
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent
CITY_BOUNDARY_GEOJSON = BASE / "city_boundary.geojson"
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

COUNCIL = "at-large (Mayor + 5 citywide councilmembers — no districts)"


@functools.lru_cache(maxsize=1)
def _city_boundary():
    import geopandas as gpd
    gdf = gpd.read_file(CITY_BOUNDARY_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    return gdf.to_crs("EPSG:4326")


@functools.lru_cache(maxsize=1)
def _precincts():
    import geopandas as gpd
    if not PRECINCTS_GEOJSON.exists():
        return None
    gdf = gpd.read_file(PRECINCTS_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    return gdf.to_crs("EPSG:4326")


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


def _precinct_for(lon, lat):
    from shapely.geometry import Point
    prec = _precincts()
    if prec is None:
        return None
    hit = prec[prec.contains(Point(lon, lat))]
    if hit.empty:
        return None
    row = hit.iloc[0]
    # AliasName is blank for Juab precincts; VistaID/PrecinctID carry the 12NE# code.
    for key in ("VistaID", "PrecinctID", "AliasName"):
        if key in row and row[key] is not None and str(row[key]).strip():
            return str(row[key]).strip()
    return None


def district_for_point(lon, lat):
    """lat/long -> in/out of Nephi city limits (offline).

    Returns a dict. 'district' is always None (the city has no districts);
    'in_city' is the meaningful field. 'precinct' is informational only.
    """
    from shapely.geometry import Point
    city = _city_boundary()
    in_city = bool(city.contains(Point(lon, lat)).any())
    return {
        "in_city": in_city,
        "district": None,                       # Nephi has no districts (at-large)
        "council": COUNCIL if in_city else None,
        "precinct": _precinct_for(lon, lat) if in_city else None,
        "lat": lat,
        "lon": lon,
    }


def district_for_address(address):
    g = geocode(address)
    if not g:
        return {"in_city": None, "district": None, "council": None,
                "precinct": None, "matched_address": None,
                "error": "no geocode match"}
    lon, lat, matched = g
    res = district_for_point(lon, lat)
    res["matched_address"] = matched
    return res


def _fmt(res):
    if res.get("error"):
        return f"  no match ({res['error']})"
    head = res.get("matched_address") or f"{res['lat']}, {res['lon']}"
    if res.get("in_city"):
        prec = res.get("precinct")
        prec_str = f" (precinct {prec})" if prec else ""
        return (f"  {head}\n"
                f"    -> INSIDE Nephi city limits{prec_str}\n"
                f"    -> represented by {COUNCIL}")
    return (f"  {head}\n"
            f"    -> OUTSIDE Nephi city limits (no Nephi representation)")


def main():
    ap = argparse.ArgumentParser(
        description="Nephi address/point -> in/out of city limits "
                    "(council is at-large; there are no districts)")
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
