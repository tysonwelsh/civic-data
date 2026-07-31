#!/usr/bin/env python3
"""Build the Cottonwood Heights geo layer (address/point -> council district 1-4).

Cottonwood Heights elects a **4-district council + a citywide VOTING Mayor**
(the mayor has no district and is never returned by the resolver). This script
fetches the two source layers, writes the three geo artifacts, and derives the
precinct->district crosswalk. Idempotent; needs internet.

SOURCES
-------
1. District polygons — the city's OWN "Council Districts" layer (AUTHORITATIVE,
   current post-2020-census map). The city GIS lives on two hosts:
     * gis.chcity.org  -- the catalogued `CityData/CityCouncilDistricts_SD`
       service, but it is FIREWALLED from outside the city network (connection
       times out; confirmed in recon and this build).
     * gis.cwh.utah.gov -- a PUBLIC mirror that IS reachable, exposing the
       districts as **layer 15 "Council Districts"** of
       `PublicData/City_Base_Data/MapServer`. Used here. The layer carries the
       current members/terms inline (D1 Holton, D2 Hyland, D3 Newell, D4 Birrell).
   -> geo/districts.geojson (4 polygons, EPSG:4326, field DistrictID = 1..4).

2. Precincts — UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt
   Lake County; CH elections are county-run), filtered to the **COT-prefixed**
   precincts. -> geo/precincts.geojson (44 features, EPSG:4326).

precinct_to_district.csv — each precinct assigned by point-in-polygon
(representative interior point) against the current district layer, CROSS-CHECKED
against the current-map elections (2023 D1/D2 + 2025 D3/D4): all 43 election
precincts agree with containment (0 disagreements). NOTE a **post-2020
redistricting seam**: the 2021 (old-map) SOVC assigns several precincts to a
different district than the current layer — those rows are the old plan and are
NOT used for the current crosswalk (documented in CLAUDE.md).
"""
import csv, json, os, subprocess, urllib.parse
from shapely.geometry import shape

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'raw')
BYPREC = os.path.join(BASE, '..', 'election_results',
                      'cottonwood_heights_results_by_precinct.csv')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

DISTRICTS_URL = ('https://gis.cwh.utah.gov/server/rest/services/PublicData/'
                 'City_Base_Data/MapServer/15/query')
PRECINCTS_URL = ('https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/'
                 'services/VistaBallotAreas/FeatureServer/0/query')


def fetch(url, params, dest):
    q = url + '?' + urllib.parse.urlencode(params)
    out = subprocess.run(['curl', '-sS', '--max-time', '90', '-A', UA, q],
                         capture_output=True, text=True).stdout
    json.loads(out)  # validate
    with open(dest, 'w') as fh:
        fh.write(out)
    return dest


def main():
    os.makedirs(RAW, exist_ok=True)
    # 1. official districts
    draw = fetch(DISTRICTS_URL,
                 dict(where='1=1', outFields='*', outSR=4326, f='geojson'),
                 os.path.join(RAW, 'council_districts_official.geojson'))
    dj = json.load(open(draw))
    feats = []
    for f in sorted(dj['features'], key=lambda x: x['properties']['DistrictID']):
        p = f['properties']
        feats.append(dict(type='Feature', geometry=f['geometry'], properties=dict(
            DistrictID=int(p['DistrictID']),
            District=str(p.get('Label', '')).replace('  ', ' ').strip(),
            Member=(p.get('Member') or '').strip(),
            Term=(p.get('Term') or '').strip(),
            email=(p.get('email') or '').strip(),
            office=(p.get('office') or '').strip())))
    json.dump(dict(type='FeatureCollection', features=feats),
              open(os.path.join(BASE, 'districts.geojson'), 'w'))
    polys = {f['properties']['DistrictID']: shape(f['geometry']) for f in feats}

    # 2. precincts
    praw = fetch(PRECINCTS_URL,
                 {'where': "CountyID=18 AND PrecinctID LIKE 'COT%'",
                  'outFields': 'PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr',
                  'outSR': 4326, 'f': 'geojson'},
                 os.path.join(RAW, 'precincts_ugrc.geojson'))
    pj = json.load(open(praw))
    json.dump(pj, open(os.path.join(BASE, 'precincts.geojson'), 'w'))

    # 3. current-map election assignment (2023 D1/D2 + 2025 D3/D4)
    cur = {}
    for r in csv.DictReader(open(BYPREC)):
        if r['office'] != 'Council':
            continue
        if (r['year'] == '2023' and r['district'] in ('1', '2')) or \
           (r['year'] == '2025' and r['district'] in ('3', '4')):
            cur.setdefault(r['precinct'], set()).add(r['district'])

    rows, disagree = [], 0
    for f in sorted(pj['features'], key=lambda x: x['properties']['PrecinctID']):
        pid = f['properties']['PrecinctID']
        g = shape(f['geometry'])
        rp = g.representative_point()
        hit = [d for d, poly in polys.items() if poly.contains(rp)]
        if not hit:  # edge point -> max area overlap
            hit = [max(polys, key=lambda d: polys[d].intersection(g).area)]
        pdist = hit[0]
        elect = sorted(cur.get(pid, []))
        match = 'n/a' if not elect else ('yes' if str(pdist) in elect else 'NO')
        if match == 'NO':
            disagree += 1
        rows.append(dict(precinct=pid, district=pdist,
                         election_district=';'.join(elect),
                         method='point_in_polygon',
                         agrees_with_current_election=match))
    with open(os.path.join(BASE, 'precinct_to_district.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['precinct', 'district', 'election_district',
                                           'method', 'agrees_with_current_election'])
        w.writeheader(); w.writerows(rows)

    from collections import Counter
    print(f"districts.geojson: {len(feats)} polygons "
          f"({', '.join(f['properties']['Member'] for f in feats)})")
    print(f"precincts.geojson: {len(pj['features'])} COT precincts")
    print(f"precinct_to_district.csv: {len(rows)} rows; "
          f"district counts {dict(Counter(r['district'] for r in rows))}; "
          f"election disagreements: {disagree}")


if __name__ == '__main__':
    main()
