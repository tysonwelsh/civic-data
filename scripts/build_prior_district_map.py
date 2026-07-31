#!/usr/bin/env python3
"""build_prior_district_map.py — reconstruct a city's PRIOR-plan (pre-2022) council-district
geometry + composition from repo data alone (no external fetch), the same way the CURRENT map
was derived: dissolve the current `geo/precincts.geojson` precinct shapes by the OLD
precinct->district assignment read from the pre-2022 DISTRICT-contest rows of
`election_results/<city>_results_by_precinct.csv`.

Outputs (committed to <city>/geo/):
  council_districts_pre2022.geojson   dissolved prior-plan district polygons
  precinct_to_district_pre2022.csv    precinct,district  (the prior-plan composition)

Vintage caveat (why the roster marks these `medium`, not `high`): the precinct SHAPES are
current-vintage (UGRC 2025), so this is the OLD assignment over CURRENT precinct shapes —
faithful where the county moved only DISTRICT lines along stable precincts, approximate where
precincts themselves were reshaped in 2022. Retired/renumbered old codes leave honest edge holes.

Usage:
  python3 scripts/build_prior_district_map.py --city taylorsville_city_council --years 2017,2021
  # a city whose precinct layer is not named geo/precincts.geojson (e.g. slc's countywide
  # geo/slco_precincts_current.geojson) passes it explicitly:
  python3 scripts/build_prior_district_map.py --city slc_city_council --years 2019,2021 \
      --precincts geo/slco_precincts_current.geojson
"""
import argparse
import csv
import json
import os
import sys

import geopandas as gpd


def load_old_assignment(byprecinct_path, years):
    """precinct -> district from pre-2022 Council DISTRICT-contest rows (numeric district only).
    A precinct appearing under >1 district across the combined years is a CONFLICT (reassigned/
    split); resolve to the LATEST year's assignment (closest to the plan-window end) and log it."""
    by_year = {}   # (precinct) -> {year: district}
    for r in csv.DictReader(open(byprecinct_path, newline="")):
        if r.get("office") != "Council":
            continue
        d = (r.get("district") or "").strip()
        if not d.isdigit():
            continue
        y = (r.get("year") or "").strip()
        if y not in years:
            continue
        prec = (r.get("precinct") or "").strip()
        if not prec:
            continue
        by_year.setdefault(prec, {})[y] = d
    assign, conflicts = {}, []
    for prec, yd in by_year.items():
        dists = set(yd.values())
        if len(dists) > 1:
            latest = yd[max(yd)]
            conflicts.append((prec, dict(yd), latest))
            assign[prec] = latest
        else:
            assign[prec] = next(iter(dists))
    return assign, conflicts


def precinct_id_field(gdf):
    for f in ("PrecinctID", "precinct", "VistaID", "SubPrecinctID", "PRECINCT", "AreaID"):
        if f in gdf.columns:
            return f
    raise SystemExit("no precinct-id field found in precincts.geojson: %s" % list(gdf.columns))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, help="<city>_city_council dir")
    ap.add_argument("--years", required=True, help="comma list of pre-2022 election years")
    ap.add_argument("--precincts", default="geo/precincts.geojson",
                    help="precinct-geometry geojson relative to the city dir "
                         "(default geo/precincts.geojson; slc uses geo/slco_precincts_current.geojson)")
    a = ap.parse_args()
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), a.city)
    city = a.city.replace("_city_council", "")
    byp = os.path.join(base, "election_results", "%s_results_by_precinct.csv" % city)
    precincts_gj = os.path.join(base, a.precincts)
    out_gj = os.path.join(base, "geo", "council_districts_pre2022.geojson")
    out_csv = os.path.join(base, "geo", "precinct_to_district_pre2022.csv")
    years = set(a.years.split(","))

    assign, conflicts = load_old_assignment(byp, years)
    if not assign:
        raise SystemExit("no pre-2022 district-contest rows for years %s in %s" % (a.years, byp))

    gdf = gpd.read_file(precincts_gj).to_crs("EPSG:4326")
    pid = precinct_id_field(gdf)
    gdf["_pid"] = gdf[pid].astype(str)
    present = set(gdf["_pid"])
    matched = {p: d for p, d in assign.items() if p in present}
    missing = sorted(p for p in assign if p not in present)

    gdf["district"] = gdf["_pid"].map(matched)
    dissolved = gdf.dropna(subset=["district"]).dissolve(by="district").reset_index()
    dissolved = dissolved[["district", "geometry"]].sort_values("district")
    dissolved.to_file(out_gj, driver="GeoJSON")

    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district"])
        for p, d in sorted(matched.items()):
            w.writerow([p, d])

    print("%s: %d precincts assigned (%d/%d matched geometry, %d missing), "
          "%d districts, %d conflict(s)"
          % (city, len(assign), len(matched), len(assign), len(missing),
             dissolved["district"].nunique(), len(conflicts)))
    print("  districts: %s" % sorted(dissolved["district"].tolist()))
    if conflicts:
        for p, yd, chosen in conflicts:
            print("  CONFLICT %s across years %s -> chose %s (latest)" % (p, yd, chosen))
    if missing:
        print("  MISSING geometry (edge holes): %s" % (", ".join(missing[:20]) + (" …" if len(missing) > 20 else "")))
    print("  wrote %s + %s" % (os.path.basename(out_gj), os.path.basename(out_csv)))


if __name__ == "__main__":
    main()
