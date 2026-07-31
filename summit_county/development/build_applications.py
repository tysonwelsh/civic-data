#!/usr/bin/env python3
"""Reconstruct the Summit County land-use development pipeline (one row per PC application item)
from land_use minutes. Fields per SLCo model + Summit-native application detail.
Honest: unknowable fields blank; outcome from the item's motion where present; per-row source."""
import re, os, glob, csv, importlib.util

ROOT="/Users/tysonwelsh/civic-data/summit_county"
MINDIR=os.path.join(ROOT,"land_use","minutes")

# Regenerate motions from the authoritative land_use vote extractor (self-contained; no
# scratchpad dependency). build_votes.parse_file returns the same motion dicts.
_spec=importlib.util.spec_from_file_location("build_votes", os.path.join(ROOT,"land_use","build_votes.py"))
_bv=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_bv)
MOTIONS=[]
for _f in sorted(glob.glob(os.path.join(MINDIR,'*','*.md'))):
    MOTIONS.extend(_bv.parse_file(_f))
BYMEET={}
for _m in MOTIONS:
    BYMEET.setdefault((_m['date'],_m['body_slug']),[]).append(_m)

def link_motion(date, slug, keys, dt):
    """Find the best action-motion in this meeting matching the application (by parcel/project/loc tokens)."""
    cands=BYMEET.get((date,slug),[])
    if not cands: return None
    keyset=set(k.lower() for k in keys if k and len(k)>3)
    best=None; bestscore=0
    typewords={'conditional_use_permit':'conditional use','plat_amendment':'plat amendment','subdivision':'subdivision',
      'rezone':'rezone','master_planned_development':'master planned','specially_planned_area':'specially planned',
      'low_impact_permit':'low impact','general_plan_amendment':'general plan','code_amendment':'code','annexation':'annexation'}
    for m in cands:
        mt=m['motion'].lower()
        if not re.search(r'approv|den|recommend|continue|table|forward|adopt|reject|postpone', mt): continue
        score=0
        for k in keyset:
            if k in mt: score+=3
        tw=typewords.get(dt,'')
        if tw and tw in mt: score+=1
        if score>bestscore: bestscore=score; best=m
    if bestscore>=3: return best
    return None

# dev_type detection (ordered; first match wins) — verified from body, not label
TYPES=[
 ('general_plan_amendment', r'General Plan Amendment|amendment[s]? to the .{0,40}General Plan|General Plan .{0,30}amendment'),
 ('rezone', r'\bRe-?zone\b|\brezoning\b|Zone (?:Map )?Amendment|zone change'),
 ('master_planned_development', r'Master Planned Development|\bMPD\b'),
 ('specially_planned_area', r'Specially Planned Area|\bSPA\b(?!\w)'),
 ('subdivision', r'\bSubdivision\b|Preliminary Plat|Final Plat'),
 ('plat_amendment', r'Plat Amendment|Amended Plat|plat amendment'),
 ('conditional_use_permit', r'Conditional Use Permit|\bCUP\b'),
 ('low_impact_permit', r'Low Impact Permit|\bLIP\b'),
 ('code_amendment', r'(?:Development Code|Land Use Code|Snyderville Basin Development Code|Eastern Summit County Development Code) .{0,40}amendment|amendment[s]? to .{0,40}(?:Development Code|Land Use Code)|Code Amendment'),
 ('annexation', r'\bAnnexation\b'),
 ('lot_line_adjustment', r'Lot Line Adjustment|Boundary Line Adjustment'),
]
def dev_type(txt):
    for name,pat in TYPES:
        if re.search(pat, txt, re.I): return name
    return ''

def dev_type_scoped(title, block):
    """Classify from the item TITLE, choosing the EARLIEST-matching type.

    2026-07-25 (audit D7): classifying over the whole 2,500-char block let a project's
    NAME and even public-comment text outrank the actual application —
      "Conditional Use Permit for a 'Vehicle control gate' … Mountain Top Subdivision"
        was typed `subdivision` (first-match order put subdivision above CUP), and
      "Final Subdivision Plat (1 Lot) and Final Site Plan (40 Units)"
        was typed `specially_planned_area` because 'SPA' appeared in a comment below.
    The application's own kind leads its title ("a Conditional Use Permit FOR …"), so take
    the type whose pattern matches earliest there; fall back to the block only when the
    title names no type at all.
    """
    best=None
    for name,pat in TYPES:
        m=re.search(pat, title or '', re.I)
        if m and (best is None or m.start()<best[0]): best=(m.start(), name)
    return best[1] if best else dev_type(block)

def frontmatter(t):
    m=re.match(r'---\n(.*?)\n---\n', t, re.S); d={}
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line: k,v=line.split(':',1); d[k.strip()]=v.strip()
        t=t[m.end():]
    return d,t
def clean(s): return re.sub(r'\s+',' ',s).strip(' .,;:•*')

def outcome_of(block):
    """Return (outcome, disposition, tally) from the item's motion within block."""
    mo=re.search(r'made (?:a|the) motion (?:to |for |that )?(.{0,80})', block, re.I)
    disp=''
    if mo:
        act=mo.group(1).lower()
        if re.search(r'\bapprov|positive recommendation|adopt|forward.*positive', act): disp='approve'
        elif re.search(r'\bden(y|ial)|negative recommendation|reject', act): disp='deny'
        elif re.search(r'\bcontinue|table|postpone|date certain', act): disp='continue'
    low=block.lower()
    tally=re.search(r'\((\d+)\s*(?:-|to)\s*(\d+)(?:\s*(?:-|to)\s*\d+)?\)', block)
    if re.search(r'motion (?:carried|passed|approved)|all voted in favor|passed unanimously|carried unanimously', low): out='Pass'
    elif re.search(r'motion (?:failed|denied|did not (?:carry|pass))', low): out='Fail'
    elif tally: out='Pass' if int(tally.group(1))>int(tally.group(2)) else 'Fail'
    else: out=''
    return out, disp, (tally.group(0) if tally else '')

def field(block, pat):
    m=re.search(pat, block)
    return clean(m.group(1)) if m else ''

def parse_meeting(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    fm,body=frontmatter(t)
    date=fm.get('date',''); bodyname=fm.get('body',''); slug=fm.get('body_slug','')
    rel=os.path.relpath(path, ROOT)
    # split into agenda-item blocks on 'N)' or 'N.' markers
    parts=re.split(r'(?:(?<=\s)|^)(\d{1,2})[\).]\s', body)
    # parts: [pre, num, block, num, block, ...]
    items=[]
    for i in range(1,len(parts)-1,2):
        num=parts[i]; block=parts[i+1][:2500]
        items.append((int(num), block))
    apps=[]
    for num,block in items:
        # land-use application signal
        if not re.search(r'located at|Parcel|Project #|Applicant:', block): continue
        # title = first sentence of item (computed BEFORE typing — the type is read from
        # the title, not the whole block; see dev_type_scoped)
        title=clean(re.split(r'\.\s|\(\d+:\d+', block)[0])[:400]
        dt=dev_type_scoped(title, block)
        if not dt: continue
        location=field(block, r'located (?:at|in|on)\s+([^;.]+?)(?:,?\s*Summit County|;|\.\s|Parcel)')
        parcel=field(block, r'Parcel[s]?[:#]?\s*([A-Z0-9][A-Z0-9\-]+(?:\s*,\s*[A-Z0-9\-]+)*)')
        applicant=field(block, r'Applicant[s]?:\s*([^;.]+?)(?:;|\.\s|Owner:|Project #)')
        owner=field(block, r'Owner[s]?:\s*([^;.]+?)(?:;|\.\s|Project #|Administrative|Applicant:)')
        project=field(block, r'Project #\s*([0-9][0-9\-, and]*[0-9])')
        # outcome: prefer linked motion from verified motions layer, else in-block
        out, disp, tally = outcome_of(block)
        link_conf=''
        lm=link_motion(date, slug, [parcel, project, location.split(',')[0] if location else '', title[:40]], dt)
        if lm:
            out=lm['result'] or out
            tally=lm['tally'] or tally
            if not disp:
                mt=lm['motion'].lower()
                if re.search(r'approv|positive recommendation|adopt|forward', mt): disp='approve'
                elif re.search(r'\bden|negative recommendation|reject', mt): disp='deny'
                elif re.search(r'continue|table|postpone|date certain', mt): disp='continue'
            link_conf='motion_matched'
        elif out:
            link_conf='in_block'
        names_rec = 'true' if re.search(r'voted (AYE|NAY|NO)|abstained|voted against|opposed', block) else ('true' if (lm and lm['names_recorded']) else 'false')
        # session context
        session = 'work_session' if re.search(r'work session', title, re.I) else 'regular'
        apps.append(dict(date=date,body=bodyname,body_slug=slug,item_no=num,dev_type=dt,
            title=title,location=location,parcel=parcel,applicant=applicant,owner=owner,
            project=project,session=session,pc_recommendation=disp,outcome=out,tally=tally,
            names_recorded=names_rec,link_confidence=link_conf,minutes_path=rel))
    return apps

def main():
    files=sorted(glob.glob(os.path.join(MINDIR,'*','*.md')))
    allapps=[]
    for f in files: allapps.extend(parse_meeting(f))
    # dedupe within a meeting: prefer the block that HAS an outcome (regular session action)
    # key on (date, project or parcel or title-stem)
    best={}
    for a in allapps:
        key=(a['date'], a['body_slug'], a['project'] or a['parcel'] or a['title'][:60])
        cur=best.get(key)
        score=(1 if a['outcome'] else 0, 1 if a['session']=='regular' else 0, len(a['applicant'])+len(a['location']))
        if cur is None or score>cur[0]:
            best[key]=(score,a)
    apps=[v[1] for v in best.values()]
    apps.sort(key=lambda a:(a['body_slug'],a['date'],a['item_no']))
    cols=['date','body','body_slug','item_no','dev_type','title','location','parcel','applicant','owner','project','session','pc_recommendation','outcome','tally','names_recorded','link_confidence','minutes_path']
    outp=os.path.join(ROOT,'development','applications.csv')
    with open(outp,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for a in apps: w.writerow(a)
    from collections import Counter
    print("raw item-rows:", len(allapps), "deduped applications:", len(apps))
    print("by dev_type:", dict(Counter(a['dev_type'] for a in apps)))
    print("with outcome:", sum(1 for a in apps if a['outcome']), "with parcel:", sum(1 for a in apps if a['parcel']), "with applicant:", sum(1 for a in apps if a['applicant']), "with project#:", sum(1 for a in apps if a['project']))
    print("by body:", dict(Counter(a['body_slug'] for a in apps)))

if __name__=='__main__': main()
