#!/usr/bin/env python3
"""Extract Housing Authority (Housing Connect) board votes from the converted minutes.
Recording ceiling is NAMED: each motion records mover, seconder, and a named
'all board members present (...)' in-favor list; dissent/abstention named when it occurs.
Near-unanimous consensus body. One row per (motion x named member); motions whose
outcome is stated without a name list get a single tally row (member blank) -- never fabricated.
Reads the built minutes .md, writes all_votes.csv (13 cols)."""
import os, re, csv, glob

HA = "/Users/tysonwelsh/civic-data/salt_lake_county/agencies/housing_authority"
ROLE = r'(?:Vice\s+Chair|Chair|Comm?issioners?)'

def load_roster(text):
    """surname -> set(full names) from the PRESENT block."""
    m = re.search(r'\bPRESENT\b(.*?)(?:\bEXCUSED\b|\bSTAFF\b|\bGUEST|\bABSENT\b|\bMINUTES\b|\n\d\.)', text, re.S|re.I)
    block = m.group(1) if m else text[:1200]
    ros = {}
    for nm in re.finditer(r'([A-Z][a-zA-Z.\'\-]+(?:\s+[A-Z][a-zA-Z.\'\-]+){1,2})\s*[–—-]\s*(?:Chair|Vice\s+Chair|Commissioner)', block):
        full = re.sub(r'\s+',' ',nm.group(1)).strip()
        sur = full.split()[-1]
        ros.setdefault(sur.lower(), set()).add(full)
    return ros

def resolve(token, ros):
    """map a name token (surname or full) to a full name via roster."""
    token = token.strip(' .,')
    token = re.sub(r'\s+',' ',token)
    parts = token.split()
    sur = parts[-1].lower() if parts else ''
    cand = ros.get(sur, set())
    if len(parts) >= 2:            # full name given
        return token
    if len(cand) == 1:
        return next(iter(cand))
    return token                    # surname-only, ambiguous or unseen: keep as printed

def split_members(chunk, ros):
    """parse 'Chair Jennifer Johnston, Vice Chair Mark Johnston, Commissioners Bernal, Litvack, and Nguyen'"""
    chunk = re.sub(r'\b'+ROLE+r'\b', '', chunk)           # drop role words
    chunk = chunk.replace(' and ', ',').replace(' & ', ',')
    out = []
    for tok in chunk.split(','):
        tok = tok.strip(' .')
        if not tok or len(tok) < 2: continue
        if re.match(r'^[A-Z][a-zA-Z.\'\-]+(\s+[A-Z][a-zA-Z.\'\-]+)?$', tok):
            out.append(resolve(tok, ros))
    # dedupe preserve order
    seen=set(); res=[]
    for x in out:
        if x.lower() not in seen: seen.add(x.lower()); res.append(x)
    return res

def classify(subj):
    s = subj.lower()
    if 'minute' in s: return 'minutes-approval'
    if 'consent agenda' in s: return 'consent-agenda'
    if 'resolution' in s: return 'resolution'
    if 'budget' in s: return 'budget'
    if 'executive session' in s or 'closed' in s: return 'executive-session'
    if 'adjourn' in s: return 'adjourn'
    if 'nominat' in s or 'chair' in s and 'nominat' in s: return 'election-officers'
    if 'election' in s or 'nominat' in s: return 'election-officers'
    return 'other'

NAME = r'[A-Z][a-zA-Z.\'\-]+(?:\s+[A-Z][a-zA-Z.\'\-]+)?'   # 1 or 2 name words
# lookahead MUST use the same 1-or-2-word NAME so a two-word-name mover ("Mark Johnston
# motioned") correctly ends the previous motion's window instead of bleeding into it.
MOVE_RE = re.compile(r'('+ROLE+r'\s+'+NAME+r')\s+(?:motioned|moved)\b(.*?)(?=(?:'+ROLE+r'\s+'+NAME+r'\s+(?:motioned|moved)\b)|$)', re.S)

def _ocr_fix(t):
    # rejoin OCR-split role words ("Com missioner", "Comm issioner", "Vice- Chair")
    t = re.sub(r'\bCom\s*m?\s*issioners?\b', 'Commissioner', t)
    t = re.sub(r'\bComm\s*issioners?\b', 'Commissioner', t)
    t = re.sub(r'\bVice[-\s]+Chair\b', 'Vice Chair', t)
    return t

def parse_motions(text, date, ros, md_rel):
    flat = _ocr_fix(re.sub(r'\s+',' ',text))
    rows=[]; n=0
    for m in MOVE_RE.finditer(flat):
        mover_raw = m.group(1)
        window = m.group(0)[:700]          # full: mover + verb + body up to next mover
        # subject
        sm = re.search(r'(?:motioned|moved)\s+(?:to|for the Board to|for the board to|that)?\s*(.*?)(?:,?\s+(?:and\s+)?'+ROLE+r'\s+[A-Z][a-zA-Z.\'\-]+\s+second|\.\s|;|second)', window, re.I)
        subj = re.sub(r'\s+',' ', sm.group(1)).strip(' .,') if sm else ''
        if not subj or len(subj) < 3:
            continue
        # seconder
        sec=''
        s2 = re.search(r'('+ROLE+r'\s+[A-Z][a-zA-Z.\'\-]+)\s+second', window) or \
             re.search(r'second(?:ed)?\s+by\s+('+ROLE+r'\s+[A-Z][a-zA-Z.\'\-]+)', window) or \
             re.search(r'with\s+('+ROLE+r'\s+[A-Z][a-zA-Z.\'\-]+)\s+second', window)
        if s2: sec = resolve(re.sub(r'\b'+ROLE+r'\b','',s2.group(1)), ros)
        mover = resolve(re.sub(r'\b'+ROLE+r'\b','',mover_raw), ros)
        # result
        low = window.lower()
        result = 'Passed'
        if re.search(r'motion\s+failed|did not pass|failed to pass|motion\s+did not', low): result='Failed'
        elif re.search(r'tabled', low): result='Tabled'
        # abstentions
        abst=[]
        for am in re.finditer(r'([A-Z][a-zA-Z.\'\-]+(?:\s+[A-Z][a-zA-Z.\'\-]+)?)\s+abstained', window):
            abst.append(resolve(re.sub(r'\b'+ROLE+r'\b','',am.group(1)), ros))
        # named in-favor list: parenthetical containing a role word, near favor/support/present
        infavor=[]
        pit = None
        for pm in re.finditer(r'\(([^)]{4,320})\)', window):
            if re.search(ROLE, pm.group(1)):
                pit = pm.group(1)   # take last qualifying paren (the vote roster)
        if pit:
            infavor = split_members(pit, ros)
        if not infavor:
            fm = re.search(r'Comm?issioners?\s+([A-Z][a-zA-Z.\'\-]+(?:,?\s+(?:and\s+)?[A-Z][a-zA-Z.\'\-]+)*)\s+voted in favor', window)
            if fm: infavor = split_members('Commissioners '+fm.group(1), ros)
        # drop abstainers from infavor
        infavor = [x for x in infavor if x.lower() not in [a.lower() for a in abst]]
        n += 1
        base = dict(date=date, year=date[:4], title=subj[:200], body="HousingAuthority",
                    motion_no=n, motion=window.strip()[:500], motion_type=classify(subj),
                    result=result, mover=mover, seconder=sec, source=md_rel)
        if infavor or abst:
            for mem in infavor:
                r=dict(base); r['member']=mem; r['vote']='Aye'; rows.append(r)
            for mem in abst:
                r=dict(base); r['member']=mem; r['vote']='Abstain'; rows.append(r)
        else:
            r=dict(base); r['member']=''; r['vote']=''; rows.append(r)
    return rows

allrows=[]
files = sorted(glob.glob(os.path.join(HA,"minutes","*","*.md")))
per_meeting_named=0; per_meeting_total=0
for md in files:
    raw = open(md, encoding='utf-8').read()
    body = raw.split('---',2)[-1]
    date = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', raw).group(1)
    md_rel = "agencies/housing_authority/minutes/%s/%s" % (date[:4], os.path.basename(md))
    ros = load_roster(body)
    rows = parse_motions(body, date, ros, md_rel)
    allrows += rows

# ---- global name normalization: unambiguous surname -> full name ----
def clean_tok(t):
    t = re.sub(r'\b(?:Vice|Chair|Comm?issioners?)\b', '', t)
    t = re.sub(r'[^A-Za-z.\'\- ]', ' ', t)        # drop punct
    t = re.sub(r'(?:^|\s)[-\'.]+(?=\s|$)', ' ', t) # drop standalone hyphen/apostrophe tokens
    return re.sub(r'\s+', ' ', t).strip()

BOGUS = re.compile(r'\b(Board|HCF|Trustee|Session|Agenda|Resolution)\b', re.I)

full_by_sur = {}
for r in allrows:
    for fld in ('member','mover','seconder'):
        t = clean_tok(r.get(fld,''))
        if len(t.split()) >= 2:
            full_by_sur.setdefault(t.split()[-1].lower(), set()).add(t)
sur_map = {s: next(iter(v)) for s,v in full_by_sur.items() if len(v)==1}

def norm(t):
    t = clean_tok(t)
    if not t: return ''
    if len(t.split()) == 1:            # surname only
        return sur_map.get(t.lower(), t)
    return t
for r in allrows:
    for fld in ('member','mover','seconder'):
        if r.get(fld): r[fld] = norm(r[fld])
# drop member rows whose token is bogus (caught false name); keep motion via other rows
allrows = [r for r in allrows if not (r.get('member') and BOGUS.search(r['member']))]

cols=["date","year","title","body","motion_no","motion","motion_type","result","mover","seconder","member","vote","source"]
with open(os.path.join(HA,"all_votes.csv"),"w",newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in allrows: w.writerow({k:r.get(k,'') for k in cols})

motions = {(r['date'],r['motion_no']) for r in allrows}
named = {(r['date'],r['motion_no']) for r in allrows if r['member']}
tally = motions - named
members = [r for r in allrows if r['member']]
print(f"meetings parsed: {len(files)}")
print(f"motions: {len(motions)}  (named: {len(named)}, tally-only rows: {len(tally)})")
print(f"member vote rows: {len(members)}  total rows: {len(allrows)}")
from collections import Counter
print("vote values:", dict(Counter(r['vote'] for r in allrows)))
print("motion_type:", dict(Counter(r['motion_type'] for r in motions.__class__() or []) ) if False else '')
mt=Counter();
for (d,no) in motions:
    pass
