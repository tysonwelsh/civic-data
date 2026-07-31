import json, re, sys

MONTHS = {m.lower():i for i,m in enumerate(
    ['January','February','March','April','May','June','July','August',
     'September','October','November','December'],1)}
MONTHS.update({'jan':1,'feb':2,'mar':3,'apr':4,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,
               'oct':10,'nov':11,'dec':12})

def yr(y):
    y=int(y)
    return y+2000 if y<100 else y

def parse(title):
    """Return (iso_date, precision) or (None,None). precision=day|month."""
    t=title
    # Month DD, YYYY  (e.g. July 8, 2026 ; December12, 2013)
    m=re.search(r'([A-Za-z]{3,9})\.?\s*(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})',t)
    if m and m.group(1).lower() in MONTHS:
        mo=MONTHS[m.group(1).lower()]; d=int(m.group(2)); y=int(m.group(3))
        if 1<=d<=31 and 2013<=y<=2027:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # YYYY - M-D spaced (e.g. "2023 - 1-11", "2015 - 6-5")
    m=re.search(r'\b(20\d{2})\s*-\s*(\d{1,2})-(\d{1,2})\b',t)
    if m:
        y=int(m.group(1)); mo=int(m.group(2)); d=int(m.group(3))
        if 1<=mo<=12 and 1<=d<=31:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # YYYY-M-D or YYYY.M.D or YYYY_M_D  (trailing may be _ or end; e.g. 2025-8-27, 2025-7-9_Council, 2015.11.02)
    m=re.search(r'\b(20\d{2})[-._](\d{1,2})[-._](\d{1,2})(?![\d])',t)
    if m:
        y=int(m.group(1)); mo=int(m.group(2)); d=int(m.group(3))
        if 1<=mo<=12 and 1<=d<=31:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # M/D/YY or M/D/YYYY  (e.g. 10/14/20, 6/16/2021)
    m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',t)
    if m:
        mo=int(m.group(1)); d=int(m.group(2)); y=yr(m.group(3))
        if 1<=mo<=12 and 1<=d<=31 and 2013<=y<=2027:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # M.D.YY / M.D.YYYY  (e.g. 4.18.19, 3.27.2018, 11.27.2018, 8.10.2017)
    m=re.search(r'\b(\d{1,2})[.\-](\d{1,2})[.\-](\d{2,4})\b',t)
    if m:
        mo=int(m.group(1)); d=int(m.group(2)); y=yr(m.group(3))
        if 1<=mo<=12 and 1<=d<=31 and 2013<=y<=2027:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # M_D_YY  (e.g. 3_12_15)
    m=re.search(r'\b(\d{1,2})_(\d{1,2})_(\d{2,4})\b',t)
    if m:
        mo=int(m.group(1)); d=int(m.group(2)); y=yr(m.group(3))
        if 1<=mo<=12 and 1<=d<=31 and 2013<=y<=2027:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # gmt YYYYMMDD  (e.g. gmt20250312, GMT20231128)
    m=re.search(r'[Gg][Mm][Tt](20\d{2})(\d{2})(\d{2})',t)
    if m:
        y,mo,d=int(m.group(1)),int(m.group(2)),int(m.group(3))
        if 1<=mo<=12 and 1<=d<=31:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # YYMMDD prefix (e.g. 250415_..., 241113_...)
    m=re.search(r'\b(\d{2})(\d{2})(\d{2})_',t)
    if m:
        y=yr(m.group(1)); mo=int(m.group(2)); d=int(m.group(3))
        if 2013<=y<=2027 and 1<=mo<=12 and 1<=d<=31:
            return f"{y:04d}-{mo:02d}-{d:02d}","day"
    # Month YYYY (month precision, no day)  (e.g. August 2016, March 2018)
    m=re.search(r'([A-Za-z]{3,9})\.?\s+(\d{4})\b',t)
    if m and m.group(1).lower() in MONTHS:
        mo=MONTHS[m.group(1).lower()]; y=int(m.group(2))
        if 2013<=y<=2027:
            return f"{y:04d}-{mo:02d}","month"
    return None,None

def body_of(title):
    t=title.lower()
    # catch PC + common title typos (Planninng, Commmssion, Commisison)
    if 'planning' in t or 'commiss' in t or 'commis' in t or re.search(r'\bapc\b',t) or re.search(r'\bpc\b',t):
        return 'PlanningCommission'
    if 'budget' in t or 'finance committee' in t:
        return 'BudgetCommittee'
    if 'canvass' in t:
        return 'Council'  # election canvass = council
    if 'dog' in t and 'drawing' in t:
        return 'Other'
    if 'test' in t or 'open house' in t or 'listening session' in t or 'information mtg' in t or 'mountain accord' in t or 'northside' in t or 'north side' in t:
        return 'Other'
    if 'town council' in t or 'council' in t or 'work session' in t or 'town hall' in t or 'retreat' in t:
        return 'Council'
    return 'Unknown'

if __name__=='__main__':
    src=sys.argv[1]
    undated=[]
    for line in open(src):
        try:d=json.loads(line)
        except:continue
        title=d.get('title') or ''
        iso,prec=parse(title)
        if src.endswith('sc_tracks.jsonl'):
            ident=d.get('url')
        else:
            ident=d.get('id')
        if not iso:
            undated.append((ident,title))
    print(f"UNDATED in {src}: {len(undated)}")
    for i,t in undated:
        print(i,'|',t)
