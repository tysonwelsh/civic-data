#!/usr/bin/env python3
"""Build Nephi ordinances/index.csv from the minutes (numbers are date-form MM-DD-YYYY)."""
import re, glob, os, csv
from collections import defaultdict, Counter

ROOT="/Users/tysonwelsh/civic-data/nephi_city_council"
RET="2026-07-05"
NUM=re.compile(r'Ordinance\s+(?:No\.?\s*)?#?\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(20\d{2})\s*[-–]?\s*([A-Z])?\b', re.I)

def norm(mm,dd,yy,suf):
    if not(1<=int(mm)<=12 and 1<=int(dd)<=31): return None
    n=f"{int(mm):02d}-{int(dd):02d}-{yy}"
    # real Nephi suffixes are UPPERCASE (A/B/C/S/Z); a lowercase letter here is a
    # truncated word ("...2023 a[mending]") not a suffix -> ignore it.
    if suf and suf.isupper(): n+="-"+suf
    return n

def addate(no): return f"{no[6:10]}-{no[0:2]}-{no[3:5]}"

PMN={
 "07-11-2023": ("raw/1006347.pdf","https://www.utah.gov/pmn/files/1006347.pdf","text"),
 "02-07-2023-A":("raw/940961.pdf","https://www.utah.gov/pmn/files/940961.pdf","scanned"),
 "12-02-2025-A":("raw/1360627.pdf","https://www.utah.gov/pmn/files/1360627.pdf","text"),
 "12-02-2025":  ("raw/1360629.pdf","https://www.utah.gov/pmn/files/1360629.pdf","text"),
 "01-20-2026":  ("raw/1380331.pdf","https://www.utah.gov/pmn/files/1380331.pdf","text"),
}

votes=list(csv.DictReader(open(f"{ROOT}/meeting_minutes/all_votes.csv")))
motions={}
for r in votes:
    k=(r['date'], r.get('body',''), r['motion_no'])
    motions.setdefault(k,r)
by_date=defaultdict(list)
for k,r in motions.items():
    by_date[r['date']].append(r)

def motion_num(text):
    m=NUM.search(text or "")
    return norm(*m.groups()) if m else None

STATUS=re.compile(r'\b(ADOPTED|APPROVED|TABLED|FAILED|DENIED|RESCISSION|RESCINDED|CONTINUED|WITHDRAWN|POSTPONED)\b', re.I)
info=defaultdict(lambda:{"subjects":[], "status":set(), "files":set()})
for f in sorted(glob.glob(f"{ROOT}/meeting_minutes/minutes/**/*.md",recursive=True)):
    lines=open(f,errors="replace").read().splitlines()
    for i,line in enumerate(lines):
        for m in NUM.finditer(line):
            n=norm(*m.groups())
            if not n: continue
            info[n]["files"].add(os.path.relpath(f,ROOT))
            # context window: this line + next 2 lines (Nephi wraps headers)
            L=" ".join(x.strip() for x in lines[i:i+3]).strip()
            st=STATUS.search(L)
            if st: info[n]["status"].add(st.group(1).upper())
            info[n]["subjects"].append(L)
for k,r in motions.items():
    n=motion_num(r['motion'])
    if n: _=info[n]

NARR=re.compile(r'\b(?:Mr\.|Mrs\.|Ms\.|City Administrator|Administrator|Seth Atkinson|Atkinson|'
    r'Councilor|Council Member|Council member|Mayor|moved to|made a motion|presented|'
    r'reviewed|explained|introduced|updated|described|stated|noted|recommended|'
    r'reported|discussed|has been|was written)\b')
def _strip(s):
    t=NUM.sub("", s)
    t=re.sub(r'^\s*(ORDINANCE|Ordinance)\b','',t)
    t=re.sub(r'^[\s:\-–\.]+','',t)
    t=STATUS.sub("", t)
    t=re.sub(r'^(adopt|approve|approving|adopting|the amended|amended|the|a|an)\s+','',t,flags=re.I)
    return re.sub(r'\s{2,}',' ',t).strip(" .:-–")
def _cut(t):
    h=NARR.split(t)[0]
    if " : " in h:
        head=h.split(" : ",1)[0].strip()
        if len(head)>6: h=head
    return re.sub(r'\s{2,}',' ',h).strip(" .:-–")[:220]
def clean_subject(no, subs, motion_text):
    # candidate 1: a caps-header subject line, narrative-cut
    best=None
    for s in subs:
        if re.search(r'ORDINANCE',s,re.I) and STATUS.search(s): best=s; break
    if not best:
        for s in subs:
            if re.search(r'ORDINANCE',s,re.I) and len(s)>25: best=s; break
    c1=_cut(_strip(best)) if best else ""
    if len(c1)>=8: return c1
    # candidate 2: the matched motion text description (keep more; light narrative cut)
    c2=_cut(_strip(motion_text or "")) if motion_text else ""
    if len(c2)>=8: return c2
    # candidate 3: uncut best line (keep narrative rather than emit empty)
    c3=_strip(best or motion_text or (subs[0] if subs else ""))
    return c3[:200]

# authoritative titles from the corroborating PMN Notice-of-Ordinance PDFs
PMN_TITLE={
 "07-11-2023":"Title 10 Zoning Code Amendments (lot size, frontage, setbacks, height; new half-acre residential zone)",
 "02-07-2023-A":"Amending Section 10.15.5 Nephi City Code — regulation of recreational vehicles and RV parks",
 "12-02-2025":"Creation of Industrial 4 Zone (ID4) for data centers with associated buildings, uses and utilities",
 "12-02-2025-A":"Adding 'Modular Data Center' and accessory uses/structures to the Industrial 1 (ID1) zone",
 "01-20-2026":"Jacobson Annexation (400 W) — annexing property and establishing R1-1/2 acre with Agricultural overlay zoning",
}

LU=[("accessory dwelling",'adu'),("adu",'adu'),("short-term rental",'short_term_rental'),
    ("short term rental",'short_term_rental'),("zone change",'zone_change'),("rezone",'zone_change'),
    ("zoning",'zone_change'),("zone",'zone_change'),("plat",'plat'),("subdivision",'subdivision'),
    ("subdiv",'subdivision'),("annex",'annexation'),("general plan",'general_plan'),
    ("land use",'land_use_code'),("title 10",'land_use_code'),("title 11",'subdivision'),
    ("site plan",'site_plan'),("overlay",'overlay'),("street vacation",'street_vacation'),
    ("vacation of",'street_vacation'),("parking lot",'parking'),("id4",'zone_change'),
    ("id1",'zone_change'),("industrial 4",'zone_change'),("public improvement",'subdivision'),
    ("data center",'zone_change'),("development regulations",'land_use_code'),("combined use",'zone_change'),
    ("recreational vehicle",'land_use_code'),("rv park",'land_use_code'),("10.15",'land_use_code'),
    ("home occupation",'land_use_code'),("setback",'land_use_code'),("zone map",'zone_change')]

def land_use(subject, motion_text):
    s=(subject+" "+(motion_text or "")).lower()
    for kw,t in LU:
        if kw in s: return "yes", t
    return "no", ""

# Only ORDINANCE-adoption motions are eligible matches (a plat/CUP/other action on
# the same day is a different vote, not the ordinance) — require the word 'ordinance'.
def is_ord_motion(r):
    return 'ordinance' in ((r['motion_type'] or '')+' '+(r['motion'] or '')).lower()
def rid(r): return (r['date'], r.get('body',''), r['motion_no'])

def carries(text, no):
    """Does motion text clearly carry ordinance `no`? For a base (no suffix), the
    number must NOT be followed by a suffix letter or a dangling '-' (truncated
    suffix in the source). For a suffixed no, the suffix letter must be present."""
    text=text or ""
    base=no[:10]; suf=no[11:] if len(no)>10 else ""
    mm=int(base[0:2]); dd=int(base[3:5]); yy=base[6:10]
    b=rf'0?{mm}\s*-\s*0?{dd}\s*-\s*{yy}'
    if suf:
        return re.search(b+rf'\s*-\s*{suf}\b', text, re.I) is not None
    if not re.search(b, text): return False
    if re.search(b+r'\s*-\s*([A-Za-z]|$)', text): return False  # dangling/suffixed
    return True

STOP=set("""ordinance ordinances adopt adopted adopting approve approved approving zone zones
zoning change changes changing city nephi code section title property council councilor member
motion moved amend amending amendment land development chapter area from that with this page
meeting regular request grant granting establishing revised revise creating creation utah state
the and for plan use uses map second seconded passed unanimous""".split())
def toks(s): return set(w for w in re.findall(r'[a-z]{4,}',s.lower()) if w not in STOP)
_assign={}; _positional=set()
def build_assignments(numbers, subjects_of):
    bydate_nums=defaultdict(list)
    for no in numbers: bydate_nums[addate(no)].append(no)
    for d,nos in bydate_nums.items():
        cands=by_date.get(d,[])
        claimed=set()
        ordm=[r for r in cands if is_ord_motion(r)]
        # pass 1: clean exact-number carry (suffixed first so base can't steal them)
        # ONLY ordinance-adoption motions are eligible (`ordm`) — Nephi's number IS a
        # date, so a consent-agenda row ("...claims dated 9-2-2025", "...Claims dated
        # 1-20- 2026") carries the digits of an ordinance number without enacting it.
        # Matching over every motion let those steal 09-02-2025 and 01-20-2026 from the
        # real adopting motions (found 2026-07-29); the eligibility rule documented in
        # ordinances/CLAUDE.md ("never a plat/CUP/consent-agenda row") now holds in
        # pass 1 as well as passes 2-3.
        for no in sorted(nos, key=lambda x:(len(x)<=10, x)):
            for r in ordm:
                if rid(r) in claimed: continue
                if carries(r['motion'], no):
                    _assign[no]=r; claimed.add(rid(r)); break
        # pass 2: subject-keyword among unclaimed ordinance-flavored motions
        for no in nos:
            if no in _assign: continue
            pool=[r for r in ordm if rid(r) not in claimed]
            if not pool: continue
            sw=toks(subjects_of[no])
            best=None;bestsc=0
            for r in pool:
                sc=len(sw & toks(r['motion'] or ''))
                if sc>bestsc: bestsc=sc;best=r
            if best and bestsc>=1:
                _assign[no]=best; claimed.add(rid(best))
        # pass 3: positional leftover (suffix truncated in source -> ambiguous but present)
        left=[no for no in nos if no not in _assign]
        pool=[r for r in ordm if rid(r) not in claimed]
        for no,r in zip(left, pool):
            _assign[no]=r; claimed.add(rid(r)); _positional.add(no)

def match_motion(no, subject):
    return _assign.get(no)

# map meeting date -> a minutes markdown path (for provenance fallback)
DATE2MIN={}
for f in glob.glob(f"{ROOT}/meeting_minutes/minutes/**/*.md",recursive=True):
    m=re.search(r'(20\d{2}-\d{2}-\d{2})', os.path.basename(f))
    if m: DATE2MIN.setdefault(m.group(1), os.path.relpath(f,ROOT))
PMN_BODY="https://www.utah.gov/pmn/sitemap/publicbody/1788.html"

_nums=sorted(info.keys(), key=lambda n:(addate(n),n))
_subj={n:" ".join(info[n]["subjects"]) for n in _nums}
build_assignments(_nums, _subj)

rows=[]
for no in _nums:
    d=addate(no)
    mr=match_motion(no, " ".join(info[no]["subjects"]))
    subject=PMN_TITLE.get(no) or clean_subject(no, info[no]["subjects"], mr['motion'] if mr else "")
    lu,lut=land_use(subject, mr['motion'] if mr else "")
    status=";".join(sorted(info[no]["status"]))
    matched_no=matched_date=result=""
    if mr:
        matched_no=mr['motion_no']; matched_date=mr['date']; result=mr['result']
    if no in PMN and mr:
        conf="high"; path=PMN[no][0]; src=PMN[no][1]; fmt=PMN[no][2]
        xm="PMN Notice-of-Ordinance PDF corroborates number+subject; linked to council motion"
    elif no in PMN and not mr:
        conf="none"; path=PMN[no][0]; src=PMN[no][1]; fmt=PMN[no][2]
        xm="PMN Notice-of-Ordinance PDF; no matching vote row (audit signal)"
    elif mr:
        conf="within_source"; path=""
        src=mr['source'] or (sorted(info[no]["files"])[0] if info[no]["files"] else "")
        fmt="text"
        if no in _positional:
            xm="reconstructed from meeting_minutes; same-day multi-ordinance, motion linked POSITIONALLY (suffix letter truncated in all_votes source)"
        else:
            xm="reconstructed from meeting_minutes (ordinance number in minutes header/motion text)"
    else:
        conf="none"; path=""; src=sorted(info[no]["files"])[0] if info[no]["files"] else ""
        fmt="text"; xm="minutes header/motion text only; no discrete vote row on adoption date (audit signal)"
    if not src:
        src=DATE2MIN.get(d) or PMN_BODY
    rows.append({"ordinance_no":no,"adoption_date":d,"date":d,"title":subject,
        "source_url":src,"retrieved_date":RET,"format":fmt,"extraction_method":xm,"path":path,
        "result":result,"land_use":lu,"land_use_type":lut,"status":status,
        "matched_motion_date":matched_date,"matched_motion_no":matched_no,
        "match_confidence":conf,"minutes_files":";".join(sorted(info[no]["files"]))})

# SCHEMA_SPEC §9 ordinances contract header first, city extras after
cols=["ordinance_no","adoption_date","date","title","source_url","retrieved_date","format",
      "extraction_method","path","land_use","result","matched_motion_date",
      "matched_motion_no","match_confidence","land_use_type","status","minutes_files"]
with open(f"{ROOT}/ordinances/index.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
    for r in rows: w.writerow(r)

print("total:",len(rows))
print("confidence:",dict(Counter(r['match_confidence'] for r in rows)))
print("land_use=yes:",sum(1 for r in rows if r['land_use']=='yes'))
tabled=[r for r in rows if re.search(r'TABLED|FAILED|DENIED|WITHDRAWN|POSTPONED',r['status'])]
print("non-adopted (tabled/failed/etc):",len(tabled))
print("\n-- audit: no motion match --")
for r in rows:
    if not r['matched_motion_no']:
        print(f"  {r['ordinance_no']}  lu={r['land_use']}  conf={r['match_confidence']}  st={r['status']}  {r['title'][:55]}")
print("\n-- non-adopted rows --")
for r in tabled:
    print(f"  {r['ordinance_no']}  st={r['status']}  res={r['result']}  {r['title'][:50]}")
