#!/usr/bin/env python3
"""Build Herriman City (Salt Lake County, UT) geo/ layer.

Outputs (reproducible; re-run after refetching the two source layers):
  precincts.geojson         44 HER-prefixed SLCo precincts (UGRC VistaBallotAreas)
  districts.geojson         Herriman's OFFICIAL 4 council-district polygons
  precinct_to_district.csv  precinct -> council district (1-4)

SOURCES
  districts.geojson  -- Herriman City's OWN ArcGIS (owner HCPublicWorks), layer
    HerrimanDistricts (item f59497536e834761b5c376db68a47134). 4 polygons, field
    `District` (1-4) + `Label` ("District N"). AUTHORITATIVE, current/post-2020-census.
      https://services2.arcgis.com/XBmqwOHlPh25M7aJ/arcgis/rest/services/HerrimanDistricts/FeatureServer/0
  precincts.geojson  -- UGRC VistaBallotAreas FeatureServer, internal **CountyID = 18**
    (Salt Lake County; the UGRC service keys county by an internal id, NOT the 49035 FIPS
    -- matched to the sibling south_jordan/sandy builds), filtered to HER-prefixed precincts.
      https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0

Refetch (browser UA), then run this script:
  UA="Mozilla/5.0 ... Chrome/120 Safari/537.36"
  curl -sA "$UA" ".../HerrimanDistricts/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson" -o districts.geojson
  curl -sA "$UA" ".../VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson" -o _slco_precincts.geojson
  python3 build_geo.py

precinct->district method: representative-interior-point in the official district polygon
(centroid_in_district), QA'd by largest-area-overlap fraction. Cross-checked against which
DISTRICT-N contest each precinct actually voted in (2021+ election_results) -- 0 mismatches
on the 39 precincts with modern district votes. HER904 falls OUTSIDE every current polygon
(a mail/special sub-precinct) but cast ballots in the D1 contest -> assigned D1 by that
electoral evidence (method=electoral_only_outside_polygon).
"""
import json, csv, os
import geopandas as gpd
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(BASE, *a)

# --- precincts: filter HER-prefixed out of the SLCo CountyID=18 pull ---
slco = json.load(open(p('_slco_precincts.geojson')))
her = [f for f in slco['features']
       if str(f['properties'].get('PrecinctID', '')).upper().startswith('HER')]
her.sort(key=lambda f: f['properties']['PrecinctID'])
json.dump({"type": "FeatureCollection", "features": her}, open(p('precincts.geojson'), 'w'))

dist = gpd.read_file(p('districts.geojson')).to_crs('EPSG:4326')
prec = gpd.read_file(p('precincts.geojson')).to_crs('EPSG:4326')

# --- electoral evidence: which DISTRICT-N contest each precinct voted in (2021+) ---
elect = defaultdict(set)
byprec = p('..', 'election_results', 'herriman_results_by_precinct.csv')
if os.path.exists(byprec):
    for r in csv.DictReader(open(byprec)):
        if r['office'] == 'Council' and r['district'] in {'1', '2', '3', '4'} \
                and int(r['year']) >= 2021:
            elect[r['precinct']].add(r['district'])

rows = []
for _, pr in prec.iterrows():
    pid = pr['PrecinctID']
    geom = pr.geometry
    rep = geom.representative_point()
    hit = dist[dist.contains(rep)]
    if not hit.empty:
        d = hit.iloc[0]
        frac = geom.intersection(d.geometry).area / geom.area if geom.area else 0
        rows.append((pid, int(d['District']), round(frac, 4),
                     'centroid_in_district', 'no' if frac > 0.9 else 'yes'))
    else:
        ev = elect.get(pid, set())
        if len(ev) == 1:
            rows.append((pid, int(next(iter(ev))), 0.0,
                         'electoral_only_outside_polygon', 'na'))
        else:
            rows.append((pid, '', 0.0, 'outside_all_districts', 'na'))

with open(p('precinct_to_district.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['precinct', 'district', 'district_area_frac', 'method', 'split'])
    w.writerows(rows)

# --- QA: geometric vs electoral cross-check ---
geo = {r[0]: str(r[1]) for r in rows}
mism = sum(1 for pid, ev in elect.items()
           if geo.get(pid, '') and geo[pid] not in ev)
c = Counter(r[1] for r in rows if r[1] != '')
print(f"precincts.geojson: {len(her)}  districts: 4  precinct_to_district rows: {len(rows)}")
print(f"by district: {dict(sorted(c.items()))}")
print(f"electoral cross-check mismatches: {mism}  (0 = geometric map agrees with votes)")
