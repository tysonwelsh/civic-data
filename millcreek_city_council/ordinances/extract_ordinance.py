#!/usr/bin/env python3
"""Extract adoption_date + title from a Millcreek ordinance PDF (text layer or OCR of pg1)."""
import re, subprocess, sys, os, glob

MONTHS=["January","February","March","April","May","June","July","August",
        "September","October","November","December"]
MONTH_RE=r'(Jan\w*|Feb\w*|Mar\w*|Apr\w*|May\b|Jun\w*|Jul\w*|Aug\w*|Sept?\w*|Oct\w*|Nov\w*|Dec\w*)'

def _month(tok):
    tok=tok.lower()[:3]
    for i,name in enumerate(MONTHS,1):
        if name[:3].lower()==tok: return i
    if tok=='sep': return 9
    return None

def pdftext(path,pages=20):
    try:
        return subprocess.run(["pdftotext","-layout","-l",str(pages),path,"-"],
                              capture_output=True,text=True,timeout=90).stdout
    except Exception: return ""

# temp dir for rasterized pages; overridable via ORD_OCR_TMP (defaults to the system tmp).
import tempfile
SCRATCH=os.environ.get("ORD_OCR_TMP",os.path.join(tempfile.gettempdir(),"mc_ord_ocr"))
os.makedirs(SCRATCH,exist_ok=True)
def ocr(path,page=1,dpi=250):
    tmp=f"{SCRATCH}/p_{os.getpid()}"
    for f in glob.glob(tmp+"*"):
        try: os.remove(f)
        except: pass
    try:
        subprocess.run(["pdftoppm","-r",str(dpi),"-f",str(page),"-l",str(page),"-png",path,tmp],
                       capture_output=True,timeout=120)
        pngs=glob.glob(tmp+"*.png")
        if not pngs: return ""
        out=subprocess.run(["tesseract",pngs[0],"-","--psm","6"],
                           stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                           text=True,errors="ignore",timeout=120).stdout
        for f in pngs:
            try: os.remove(f)
            except: pass
        return out
    except Exception: return ""

def _mk_iso(day_raw,mon,yr):
    mi=_month(mon)
    if not mi or not yr: return (None,None)
    my=f"{yr}-{mi:02d}"
    if day_raw:
        d=day_raw.replace('I','1').replace('l','1').replace('O','0').replace('o','0').replace('t','1')
        d=re.sub(r'\D','',d)
        if d and 1<=int(d)<=31:
            return (f"{yr}-{mi:02d}-{int(d):02d}", my)
    return (None,my)

def find_date(text):
    """Returns (iso,month_year,kind,raw). kind: passed|adopted|meeting|monthyear."""
    t=re.sub(r'[ \t]+',' ',text)
    # 1. PASSED AND APPROVED/ADOPTED this Nth day of Month, YEAR
    m=re.search(r'PASSED\s+AND\s+(?:APPROVED|ADOPTED)[^\n]{0,40}?(?:this|the)?\s*([0-9IltOo]{1,3})[\'"a-z]{0,4}\s*day\s*of\s*'+MONTH_RE+r'[.,\s]+(\d{4})',t,re.I)
    if m:
        iso,my=_mk_iso(m.group(1),m.group(2),m.group(3))
        return (iso,my,"passed",m.group(0)[:90])
    # 2. was adopted the Nth day of Month YEAR
    m=re.search(r'adopted\s+(?:the|this)\s*([0-9IltOo]{1,3})[\'"a-z]{0,4}\s*day\s*of\s*'+MONTH_RE+r'[.,\s]+(\d{4})',t,re.I)
    if m:
        iso,my=_mk_iso(m.group(1),m.group(2),m.group(3))
        return (iso,my,"adopted",m.group(0)[:90])
    # 3. met in a regular/special session on Month D, YYYY  (meeting date ~ adoption)
    m=re.search(r'met\s+in\s+a\s+\w+\s+session\s+on\s+'+MONTH_RE+r'\s+([0-9IltOo]{1,3})[,\s]+(\d{4})',t,re.I)
    if m:
        iso,my=_mk_iso(m.group(2),m.group(1),m.group(3))
        return (iso,my,"meeting",m.group(0)[:90])
    # 4. bare 'day of Month YEAR'
    m=re.search(r'([0-9IltOo]{1,3})[\'"a-z]{0,4}\s*day\s*of\s*'+MONTH_RE+r'[.,\s]+(\d{4})',t,re.I)
    if m:
        iso,my=_mk_iso(m.group(1),m.group(2),m.group(3))
        return (iso,my,"monthyear",m.group(0)[:90])
    # 5. garble-tolerant: 'passed/approved/adopted ... <handwritten> of Month, YEAR' (month+year only)
    m=re.search(r'(?:passed|approv|adopt)\w*[^\n]{0,45}?of\s+'+MONTH_RE+r'[.,\s]+(\d{4})',t,re.I)
    if m:
        _,my=_mk_iso(None,m.group(1),m.group(2))
        return (None,my,"monthyear_garbled",m.group(0)[:90])
    return (None,None,None,None)

def find_title(text):
    t=re.sub(r'[ \t]+',' ',text)
    m=re.search(r'\bAN\s+ORDINANCE\b(.{0,320}?)(?:\bWHEREAS\b|;|\bBE IT\b|\bNOW,?\s*THEREFORE\b|\n\s*\n)',t,re.I|re.S)
    if m:
        title="AN ORDINANCE"+m.group(1)
    else:
        m=re.search(r'ORDINANCE\s+N[O0]\.?\s*[\d-]+\s*(AN ORDINANCE.{5,250}?)(?:WHEREAS|;|\n\s*\n)',t,re.I|re.S)
        if not m: return ""
        title=m.group(1)
    return re.sub(r'\s+',' ',title).strip(' ,.-')[:200]

def npages(path):
    try:
        out=subprocess.run(["pdfinfo",path],capture_output=True,text=True,errors="ignore",timeout=30).stdout
        m=re.search(r'Pages:\s+(\d+)',out); return int(m.group(1)) if m else 1
    except Exception: return 1

def process(path, ocr_lastpage=True):
    txt=pdftext(path)
    if len(txt.strip())>150:
        method="pdftext"
    else:
        method="ocr"
        txt=ocr(path,1)
    iso,my,kind,raw=find_date(txt)
    title=find_title(txt)
    if not title and len(txt.strip())<400:
        o=ocr(path,1)
        if o:
            title=title or find_title(o)
            if not iso:
                iso,my,kind,raw=find_date(o); method=(method+"+ocr1") if "ocr" not in method else method
    # last-page OCR fallback for the adoption clause (signature page)
    if not iso and ocr_lastpage:
        n=npages(path)
        if n>1:
            o=ocr(path,n)
            if o:
                iso2,my2,kind2,raw2=find_date(o)
                if iso2 or my2:
                    iso,my,kind=iso2,my2,kind2
                    method=method+"+ocrL"
    return dict(method=method,adoption_date=iso or "",month_year=my or "",date_kind=kind or "",title=title)

if __name__=="__main__":
    for p in sys.argv[1:]:
        r=process(p)
        print(f"{os.path.basename(p):12} [{r['method']:11}] {r['adoption_date'] or '----------':10} my={r['month_year'] or '-------':7} k={r['date_kind']:9} :: {r['title'][:60]}")
