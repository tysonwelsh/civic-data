import csv,os,sys,json
from concurrent.futures import ProcessPoolExecutor
OD="/Users/tysonwelsh/civic-data/millcreek_city_council/ordinances"
sys.path.insert(0,OD)
import extract_ordinance as E
RAW=os.path.join(OD,"raw")

def one(o):
    r=E.process(os.path.join(RAW,f"{o}.pdf"))
    return (o,r["adoption_date"],r["month_year"],r["date_kind"],r["method"],r["title"])

# supplements from re-OCR (all-pages), oversize text-layer, and vision reads
SUPP={}
# oversize (index-only, dated from text layer)
SUPP["20-46"]=("2020-08-24","2020-08","passed","text-layer(oversize)","AN ORDINANCE ADOPTING THE MILLCREEK TRANSPORTATION MASTER PLAN","")
SUPP["22-22"]=("2022-05-09","2022-05","passed","text-layer(oversize)","AN ORDINANCE APPROVING A DEVELOPMENT AGREEMENT FOR A MIXED-USE PROJECT","")
SUPP["22-32"]=("2022-06-27","2022-06","passed","text-layer(oversize)","AN ORDINANCE AMENDING THE 2021-2022 FISCAL YEAR BUDGET","")
SUPP["22-51"]=("2022-12-12","2022-12","passed","text-layer(oversize)","AN ORDINANCE ADOPTING THE 3300 SOUTH CORRIDOR STUDY AS AN ELEMENT OF THE GENERAL PLAN","")
# vision-read (Read tool) dates
SUPP["17-07"]=("2017-01-17","2017-01","meeting","vision","AN ORDINANCE GRANTING A CABLE FRANCHISE TO QWEST BROADBAND SERVICES (CENTURYLINK)","meeting/consideration date from p1 WHEREAS; signature-page adoption clause left blank")
SUPP["17-08"]=("2017-01-09","2017-01","meeting","vision","AN ORDINANCE GRANTING A CABLE LICENSE TO COMCAST OF UTAH II","meeting/consideration date from p1 WHEREAS; acceptance-date blank")
SUPP["17-11"]=("2017-02-06","2017-02","passed","vision","AN ORDINANCE OF MILLCREEK IMPLEMENTING AUTHORITY (Certificate: passed by Council Feb 6 2017)","date from Certificate of City Recorder")
SUPP["17-99"]=("2017-12-30","2017-12","passed","vision","MILLCREEK ORDINANCE 2017-99 FIREARMS WITHIN THE CITY","APPARENT TEST/TEMPLATE DOC on code host: 'John Doe/Jane Doe/Betsy Ross' voters, '(joke)' text, fictitious U.C.A. cite - NOT an authentic adopted ordinance")
SUPP["24-02"]=("2024-02-12","2024-02","meeting","vision","AN ORDINANCE REZONING CERTAIN PROPERTY FROM FR-1/FR-2.5/FR-5/FR-10/FR-20 TO THE FORESTRY RECREATION ESTATE (FRE) ZONE","")
SUPP["26-46"]=("2026-06-22","2026-06","meeting","vision","AN ORDINANCE ESTABLISHING A TRANSPORTATION UTILITY AND FEE","")

if __name__=="__main__":
    ords=sorted(f[:-4] for f in os.listdir(RAW) if f.endswith(".pdf"))
    rows={}
    with ProcessPoolExecutor(max_workers=6) as pool:
        for o,ad,my,kind,meth,title in pool.map(one,ords):
            rows[o]=dict(ordinance_no=o,adoption_date=ad,month_year=my,date_kind=kind,method=meth,title=title,note="")
    # overlay re-OCR (all-pages) where main pass is dateless
    reocr=json.load(open("/private/tmp/claude-501/-Users-tysonwelsh-civic-data/f43a66e4-730f-4ca8-a53a-f0b8118a953b/scratchpad/reocr.json"))
    for o,(iso,my,kind) in reocr.items():
        if o in rows and not rows[o]["adoption_date"] and not rows[o]["month_year"]:
            if iso or my:
                rows[o]["adoption_date"]=iso or ""; rows[o]["month_year"]=my or ""
                rows[o]["date_kind"]=kind or ""; rows[o]["method"]=rows[o]["method"]+"+ocrAll"
    # overlay supplements (authoritative for these ords)
    for o,(ad,my,kind,meth,title,note) in SUPP.items():
        r=rows.get(o) or dict(ordinance_no=o,title="")
        r.update(dict(ordinance_no=o,adoption_date=ad,month_year=my,date_kind=kind,method=meth,note=note))
        if title: r["title"]=title
        rows[o]=r
    cols=["ordinance_no","adoption_date","month_year","date_kind","method","title","note"]
    with open(os.path.join(OD,"date_extractions.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for o in sorted(rows): w.writerow({k:rows[o].get(k,"") for k in cols})
    dated=sum(1 for o in rows if rows[o].get("adoption_date") or rows[o].get("month_year"))
    print("cache rows:",len(rows),"with date/month:",dated,"empty:",len(rows)-dated)
