#!/usr/bin/env python3
"""
Resolve a Vineyard, Utah address (or lat/long) to its City Council representation.

  *** Vineyard City Council is ENTIRELY AT-LARGE — there are ZERO districts. ***

The council is Mayor + 5 at-large members (UCA "six-member council" form, effective
Jan 2026; Mayor chairs and votes), all elected citywide. There is no ward/district
map, so the classic "address -> council district" lookup is DEGENERATE: every address
inside the city is represented by the same six officials (Mayor + all 5 at-large
councilmembers), and an address outside the city has no Vineyard representation.

This tool therefore answers the only meaningful geographic question:
  "Is this address (or point) INSIDE the Vineyard city limits?"

Pipeline:
  address --[Census geocoder, free, needs internet]--> lat/long
  lat/long --[point-in-polygon vs geo/city_limits.geojson]--> in-city True/False

For context it also reports which voter precinct the point falls in
(geo/precincts.geojson, the Utah County / UGRC VistaBallotAreas subset that overlaps
Vineyard — precincts 25VI01..25VI09) — but precinct does NOT map to a district here;
it is purely informational / useful for joining the by-precinct election data.

CLI:
    python3 address_to_district.py "125 S Main St, Vineyard, UT 84059"
    python3 address_to_district.py --latlon 40.3035 -111.7545
    python3 address_to_district.py --batch addresses.txt        # one address per line

As a module:
    from address_to_district import district_for_address, district_for_point
    info = district_for_address("125 S Main St, Vineyard, UT 84059")
    # -> {"in_city": True, "council": "at-large (Mayor + 5 citywide)",
    #     "precinct": "25VI0N", "matched_address": "...", "lat":..., "lon":...}

Notes:
  - Geocoding needs internet (Census API). lat/long lookups are fully offline.
  - CRS: geo/*.geojson are stored in EPSG:4326 (lon/lat). The UGRC source was
    requested with outSR=4326; coords verified as Utah lon/lat (~ -111.75, 40.30),
    NOT UTM meters.
  - GIS NAME-match note: UGRC Municipal Boundaries has AliasName empty for Vineyard,
    so the city polygon was fetched by FIPS=80420 (NAME='Vineyard'), and precincts by
    CountyID=25 spatially intersected with the city polygon (VistaBallotAreas
    AliasName is also empty for Vineyard — name matching fails, spatial intersect works).
  - "district" keys are kept in the return dict for API parity with the SLC/St. George
    tools, but they are always None / "at-large" for Vineyard (no districts).
"""

import argparse
import functools
import json
import subprocess
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent
CITY_LIMITS_GEOJSON = BASE / "city_limits.geojson"
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

COUNCIL = "at-large (Mayor + 5 citywide councilmembers — no districts)"


@functools.lru_cache(maxsize=1)
def _city_limits():
    import geopandas as gpd
    gdf = gpd.read_file(CITY_LIMITS_GEOJSON)
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
    # AliasName is empty for Vineyard; VistaID/PrecinctID carry the 25VI0N code.
    for key in ("VistaID", "PrecinctID", "AliasName"):
        if key in row and row[key] is not None:
            return str(row[key])
    return None


def district_for_point(lon, lat):
    """lat/long -> in/out of Vineyard city limits (offline).

    Returns a dict. 'district' is always None (the city has no districts);
    'in_city' is the meaningful field. 'precinct' is informational only.
    """
    from shapely.geometry import Point
    city = _city_limits()
    in_city = bool(city.contains(Point(lon, lat)).any())
    return {
        "in_city": in_city,
        "district": None,                       # Vineyard has no districts (at-large)
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
                f"    -> INSIDE Vineyard city limits{prec_str}\n"
                f"    -> represented by {COUNCIL}")
    return (f"  {head}\n"
            f"    -> OUTSIDE Vineyard city limits (no Vineyard representation)")


def main():
    ap = argparse.ArgumentParser(
        description="Vineyard address/point -> in/out of city limits "
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
