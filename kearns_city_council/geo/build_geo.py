#!/usr/bin/env python3
import json, csv, os
import geopandas as gpd

GEO = "/Users/tysonwelsh/civic-data/kearns_city_council/geo"
ARCHIVE = os.path.expanduser("~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson")

# 2025 SOVC precinct -> city council district (authoritative for D2/D4; residual = D1 or D3,
# unsplit because those seats were not on the 2025 ballot).
D2 = ["KRN003", "KRN005", "KRN009", "KRN016"]
D4 = ["KRN008", "KRN012", "KRN013", "KRN014", "KRN015"]

# ---- 1. city boundary (fetched from UGRC Utah Municipal Boundaries) ----
import urllib.request, urllib.parse
BND_URL = ("https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/"
           "UtahMunicipalBoundaries/FeatureServer/0/query?"
           + urllib.parse.urlencode({"where": "NAME='KEARNS'", "outFields": "*",
                                     "outSR": "4326", "f": "geojson"}))
cache = "/tmp/kearns_bnd.json"
if not os.path.exists(cache):
    urllib.request.urlretrieve(BND_URL, cache)
bnd = json.load(open(cache))
feat = bnd["features"][0]
keep = {k: feat["properties"][k] for k in ("NAME", "SHORTDESC", "COUNTYNBR", "FIPS",
                                           "ENTITYNBR", "POPLASTCENSUS")}
keep["source"] = "UGRC Utah Municipal Boundaries (NAME=KEARNS, CountyNBR=18)"
out_bnd = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": keep, "geometry": feat["geometry"]}]}
json.dump(out_bnd, open(os.path.join(GEO, "city_boundary.geojson"), "w"))
print("city_boundary.geojson written (pop", keep["POPLASTCENSUS"], ")")

# ---- 2. precincts (KRN) from the UGRC VistaBallotAreas archive slice ----
allp = gpd.read_file(ARCHIVE)
krn = allp[(allp["CountyID"] == 18) & (allp["PrecinctID"].astype(str).str.startswith("KRN"))].copy()
krn = krn.to_crs("EPSG:4326")
krn = krn[["PrecinctID", "VistaID", "CountyID", "geometry"]].sort_values("PrecinctID").reset_index(drop=True)

def dist_of(pid):
    if pid in D2:
        return "2"
    if pid in D4:
        return "4"
    return "1/3"

krn["district"] = krn["PrecinctID"].map(dist_of)
if os.path.exists(os.path.join(GEO, "precincts.geojson")):
    os.remove(os.path.join(GEO, "precincts.geojson"))
krn.to_file(os.path.join(GEO, "precincts.geojson"), driver="GeoJSON")
print("precincts.geojson:", len(krn), "KRN precincts;",
      krn["district"].value_counts().to_dict())

# ---- 3. districts.geojson (dissolve precincts by district) ----
diss = krn.dissolve(by="district", as_index=False)[["district", "geometry"]]
LABEL = {"2": "Kearns City Council District 2",
         "4": "Kearns City Council District 4",
         "1/3": "Kearns City Council District 1 or 3 (residual, unsplit)"}
MEMBER = {"2": "Lyndsay Longtin", "4": "Lorrin Colby Jr.",
          "1/3": "Patrick Schaeffer / Chrystal Butterfield (hold D1 & D3; which-is-which undetermined)"}
CONF = {"2": "high (2025 SOVC)", "4": "high (2025 SOVC)",
        "1/3": "residual — 2025 ballot omitted D1/D3; the D1-vs-D3 line is undetermined"}
diss["label"] = diss["district"].map(LABEL)
diss["council_member"] = diss["district"].map(MEMBER)
diss["confidence"] = diss["district"].map(CONF)
diss["source"] = "precinct-derived from 2025 SLCo SOVC precinct->contest assignment"
diss = diss[["district", "label", "council_member", "confidence", "source", "geometry"]]
if os.path.exists(os.path.join(GEO, "districts.geojson")):
    os.remove(os.path.join(GEO, "districts.geojson"))
diss.to_file(os.path.join(GEO, "districts.geojson"), driver="GeoJSON")
print("districts.geojson:", sorted(diss["district"]))

# ---- 4. precinct_to_district.csv ----
PLACEHOLDER = {"KRN901"}  # 0-registered-voter placeholder precinct (per SOVC)
with open(os.path.join(GEO, "precinct_to_district.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["precinct", "district", "method", "note"])
    for _, r in krn.iterrows():
        pid = r["PrecinctID"]; d = r["district"]
        if d == "1/3":
            method = "residual (not on 2025 ballot)"
            note = "District 1 or 3 — 2025 SOVC did not distinguish; needs city district map"
        else:
            method = "2025 SOVC precinct->contest"
            note = ""
        if pid in PLACEHOLDER:
            note = (note + "; " if note else "") + "0-registered-voter placeholder precinct"
        w.writerow([pid, d, method, note])
print("precinct_to_district.csv written")
