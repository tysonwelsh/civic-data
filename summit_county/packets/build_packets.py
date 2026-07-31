#!/usr/bin/env python3
"""Summit County land-use agenda-packet harvest (staff-report text corpus).
Per SCHEMA_SPEC §9: fetch the Granicus agenda-packet PDF, sha256 it, extract text to a
sidecar, DISCARD the binary (bulky 7-20MB; public + re-fetchable via source_url). doc_class=staff_report.
Also catalogs per-item staff-report ATTACHMENT labels from the minutes (index-only rows).

REPRODUCIBILITY: this reads the Granicus PC inventory (granicus_pc.json) — the list of
each meeting's agenda-packet cloudfront URL parsed from
`summitcounty.granicus.com/ViewPublisher.php?view_id=1` (CollapsiblePanel rows for the two
PC bodies). Regenerate that inventory by re-parsing ViewPublisher, then point INVENTORY at
it. The canonical outputs are index.csv + text/; source_url on each row is re-fetchable."""
import os as _os
INVENTORY=_os.environ.get('GRANICUS_PC_JSON','/private/tmp/claude-501/-Users-tysonwelsh-civic-data/5c14a1ef-7013-4132-a1b1-da1b3914221e/scratchpad/granicus_pc.json')
import json, re, os, io, csv, hashlib, time, urllib.request
from pypdf import PdfReader

ROOT="/Users/tysonwelsh/civic-data/summit_county"
PKROOT=os.path.join(ROOT,"packets"); TEXT=os.path.join(PKROOT,"text")
os.makedirs(TEXT,exist_ok=True)
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BODYNAME={'snyderville_basin_pc':'Snyderville Basin Planning Commission',
          'eastern_summit_pc':'Eastern Summit County Planning Commission'}

_DICT=set()
_dp='/usr/share/dict/words'
if os.path.exists(_dp):
    _DICT={w.strip().lower() for w in open(_dp) if len(w.strip())>3}

def _wordish(s):
    toks=re.findall(r"[A-Za-z]{4,}", s)
    return (sum(1 for t in toks if t.lower() in _DICT)/len(toks)) if toks else 0.0

def decode_cmap(text):
    """Repair two font-cmap pathologies that pdf text extraction leaves behind.

    1. PUA block  — U+F0xx glyphs map to ASCII by subtracting 0xF000 (the Sandy pathology).
    2. CID offset — some embedded sheets/exhibits are shifted DOWN by 0x1D, so
       "J-U-B SHALL RETAIN ALL COMMON LAW, STATUTORY, COPYRI…" is stored as
       "-\\x108\\x10%\\x036+$//\\x035(7$,1…". Applied PER LINE and only when the shift
       raises the line's dictionary-word ratio, so correctly-extracted lines are never
       touched (the guard makes this self-verifying — it can only improve a line).
    """
    if not text: return text
    text=''.join(chr(ord(c)-0xF000) if 0xF000<=ord(c)<=0xF0FF else c for c in text)
    out=[]
    for line in text.split('\n'):
        if any(0x00<ord(c)<0x20 and c not in '\t' for c in line):
            shifted=''.join(chr(ord(c)+0x1D) if 0x00<ord(c)<0x60 else c for c in line)
            line=shifted if _wordish(shifted)>_wordish(line) else line
        out.append(line)
    return '\n'.join(out)

def fetch(url, tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':UA})
            with urllib.request.urlopen(req, timeout=120) as r: return r.read()
        except Exception:
            if i==tries-1: raise
            time.sleep(1.5+i)

def main():
    gr=json.load(open(INVENTORY))
    packs=[x for x in gr if x['packet'] and not x['cancelled'] and x['date']]
    # dedupe by (body,date)
    seen={}
    for x in packs:
        seen.setdefault((x['body'],x['date']),x)
    packs=list(seen.values())
    rows=[]; ok=0; fail=0
    for n,x in enumerate(packs):
        body=x['body']; date=x['date']; slug=body
        tname=f"{date}_{slug}_packet.txt"
        tpath=os.path.join(TEXT,tname)
        rel_text=f"packets/text/{tname}"
        title=f"{BODYNAME[body]} Agenda Packet {date}"
        try:
            data=fetch(x['packet'])
            sha=hashlib.sha256(data).hexdigest()
            try:
                r=PdfReader(io.BytesIO(data))
                text=decode_cmap('\n'.join(p.extract_text() or '' for p in r.pages))
            except Exception:
                text=''
            status='ok' if len(text)>500 else 'needs_ocr'
            if len(text)>200:
                open(tpath,'w',encoding='utf-8').write(text)
                tp=rel_text; tc=len(text)
            else:
                tp=''; tc=len(text)
            rows.append(dict(date=date,body=BODYNAME[body],body_slug=slug,packet_kind='agenda_packet',
                title=title,clip_id=x['clip_id'],path='',text_path=tp,format='pdf',
                source_url=x['packet'],stored_locally='no',doc_class='staff_report',
                fetch_status=status,sha256=sha,text_chars=tc))
            ok+=1
        except Exception as e:
            rows.append(dict(date=date,body=BODYNAME[body],body_slug=slug,packet_kind='agenda_packet',
                title=title,clip_id=x['clip_id'],path='',text_path='',format='pdf',
                source_url=x['packet'],stored_locally='no',doc_class='staff_report',
                fetch_status=f'error',sha256='',text_chars=0))
            fail+=1
        if n%20==0: print(f"[{n}/{len(packs)}] ok={ok} fail={fail}", flush=True)
    cols=['date','body','body_slug','packet_kind','title','clip_id','path','text_path','format','source_url','stored_locally','doc_class','fetch_status','sha256','text_chars']
    rows.sort(key=lambda r:(r['body_slug'],r['date']))
    with open(os.path.join(PKROOT,'index.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"DONE packets ok={ok} fail={fail} rows={len(rows)}")

if __name__=='__main__': main()
