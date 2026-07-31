#!/usr/bin/env python3
"""Extract meeting dates from PMN minutes-like filenames and diff vs the repo indexes.
CC(753)+RDA(756)+MBA(757) map to the repo COUNCIL session date; PC(754) to the repo PC date.
Filename date is authoritative (the meeting the minutes document); event_date is fallback."""
import csv, re, os, sys
from datetime import date, timedelta
from collections import defaultdict

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))

def load_repo_dates(rel):
    p = os.path.join(REPO, rel)
    ds = set()
    for r in csv.DictReader(open(p)):
        ds.add(r["date"])
    return ds

COUNCIL = load_repo_dates("meeting_minutes/minutes_index.csv")
PC = load_repo_dates("planning_commission/minutes_index.csv")
# repo formats per date (for OCR-upgrade flagging)
def load_fmt(rel):
    d={}
    for r in csv.DictReader(open(os.path.join(REPO,rel))):
        d.setdefault(r["date"],set()).add(r["format"])
    return d
COUNCIL_FMT=load_fmt("meeting_minutes/minutes_index.csv")
PC_FMT=load_fmt("planning_commission/minutes_index.csv")

def parse_date(fn):
    """Return ISO date string from a filename, or None."""
    f = fn
    # strip trailing 001-style dup suffix on the YEAR (e.g. 1-17-23001, 2022001)
    # 1) YYYYMMDD  (Approved Minutes 20160316, CCM20161206, 06142017 has MMDDYYYY though)
    m = re.search(r'(20\d{2})(\d{2})(\d{2})', f)
    if m:
        y,mo,dd = m.groups()
        if 1<=int(mo)<=12 and 1<=int(dd)<=31:
            return f"{y}-{mo}-{dd}"
    # 2) M-D-YYYY or M-D-YY  (allow trailing 001)
    m = re.search(r'\b(\d{1,2})-(\d{1,2})-((?:20)?\d{2})(?:001)?\b', f)
    if m:
        mo,dd,y = m.groups()
        y = y if len(y)==4 else ("20"+y)
        if 1<=int(mo)<=12 and 1<=int(dd)<=31:
            return f"{y}-{int(mo):02d}-{int(dd):02d}"
    # 3) MM.DD.YY  (PC style 01.08.20)
    m = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', f)
    if m:
        mo,dd,y = m.groups()
        y = y if len(y)==4 else ("20"+y)
        if 1<=int(mo)<=12 and 1<=int(dd)<=31:
            return f"{y}-{int(mo):02d}-{int(dd):02d}"
    # 4) MM DD YYYY or MMDDYYYY (06 13 2018, 06142017, 06272018)
    m = re.search(r'\b(\d{2})\s?(\d{2})\s?(20\d{2})\b', f)
    if m:
        mo,dd,y = m.groups()
        if 1<=int(mo)<=12 and 1<=int(dd)<=31:
            return f"{y}-{mo}-{dd}"
    # 5) MM-DD-YY  (01-23-19 PC Workshop)
    return None

def within(d, dateset, tol=4):
    """True if d is within +/-tol days of any date in dateset."""
    try:
        dd = date.fromisoformat(d)
    except Exception:
        return None
    for delta in range(0, tol+1):
        for s in (dd+timedelta(days=delta), dd-timedelta(days=delta)):
            if s.isoformat() in dateset:
                return s.isoformat()
    return None

def main():
    rows=[r for r in csv.DictReader(open(os.path.join(HERE,'_work/attachments_all.csv'))) if r['minutes_like']=='True']
    # build per-attachment meeting date
    recs=[]
    for r in rows:
        d = parse_date(r['filename']) or (r['event_date'] if re.match(r'\d{4}-\d{2}-\d{2}',r['event_date']) else None)
        r['mdate']=d
        recs.append(r)
    nodate=[r for r in recs if not r['mdate']]
    if nodate:
        print("!! filenames with no parseable date (%d):"%len(nodate))
        for r in nodate[:40]: print("   ",r['body_name'],r['filename'],'| event',r['event_date'])

    # council-session bodies vs PC
    council_bodies={'753','756','757'}
    # distinct council-session meeting dates from PMN, keep which body/file
    def collect(bodyset):
        m=defaultdict(list)
        for r in recs:
            if r['body'] in bodyset and r['mdate']:
                m[r['mdate']].append(r)
        return m
    pmn_council=collect(council_bodies)
    pmn_pc=collect({'754'})

    def report(name, pmn_map, repo_dates, repo_fmt):
        print(f"\n########## {name} ##########")
        print(f"repo dates: {len(repo_dates)}   PMN distinct meeting-dates: {len(pmn_map)}")
        missing=[]
        ocr_upgrade=[]
        for d in sorted(pmn_map):
            hit=within(d, repo_dates)
            files=pmn_map[d]
            fnames=sorted(set(f['filename'] for f in files))
            if hit is None:
                # genuinely missing (no repo doc within tolerance)
                # but only count within analysis floor 2020+
                missing.append((d, files, fnames))
            else:
                # covered; check OCR upgrade for 2020-2021 seam
                fmts=repo_fmt.get(hit,set())
                if hit[:4] in ('2020','2021') and 'ocr' in fmts:
                    ocr_upgrade.append((d,hit,fnames))
        print(f"\n-- GENUINELY MISSING (no repo doc +/-4d) : {len(missing)} --")
        for d,files,fnames in missing:
            bodies=sorted(set(f['body_name'] for f in files))
            print(f"   {d}  bodies={bodies}  files={fnames}")
        print(f"\n-- OCR-UPGRADE candidates (repo date is OCR, PMN copy exists) : {len(ocr_upgrade)} --")
        for d,hit,fnames in ocr_upgrade:
            print(f"   PMN {d} -> repo {hit} (OCR)  files={fnames}")
        return missing, ocr_upgrade

    cm,co=report("COUNCIL SESSION (CC+RDA+MBA)", pmn_council, COUNCIL, COUNCIL_FMT)
    pm,po=report("PLANNING COMMISSION", pmn_pc, PC, PC_FMT)

if __name__=="__main__":
    main()
