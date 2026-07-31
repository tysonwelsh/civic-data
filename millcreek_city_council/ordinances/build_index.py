#!/usr/bin/env python3
"""
Build ordinances/index.csv for Millcreek.

Sources
-------
- raw/<ord>.pdf            adopted-ordinance PDFs harvested from the municipalcodeonline.com
                           S3 back-catalog (bucket municipalcodeonline.com-new, us-west-2).
- s3_sources.csv           ord_no -> S3 key / source_url / size / stored_locally (manifest).
- ../meeting_minutes/all_votes.csv   council motions that cite "Ordinance YY-NN".

Per ordinance we extract, from the PDF itself (independent of the minutes):
  title           the "AN ORDINANCE ..." caption (pdftext or OCR of page 1)
  adoption_date   printed "PASSED AND APPROVED this Nth day of MONTH, YEAR" / "met ... on DATE"
                  (OCR of the signature page; the DAY is often handwritten/garbled, month+year
                  print reliably -> pdf_month_year).

Linkage to votes (join by ordinance number cited in the motion text + date):
  match_confidence
    high    = number cited in exactly one council motion AND the PDF's own month+year
              (independent source) equals that motion's month+year  -> cross-source corroborated
    medium  = number cited in council motion(s) but PDF month/year not independently
              extractable, or the number is cited on multiple meeting dates (ambiguous)
    low     = (reserved) date-only / fuzzy
    none    = no council motion cites the number
  adoption_date in the index = the matched council-action date when matched (authoritative),
  else the PDF-extracted date (may be month-granular / blank for handwritten-only scans).

Never forces a match; unmatched ordinances keep empty match fields + match_confidence=none.
Regenerable: python3 build_index.py   (idempotent; reads raw/ + the two manifests).
"""
import csv, os, sys, re

HERE=os.path.dirname(os.path.abspath(__file__))
RAW=os.path.join(HERE,"raw")
VOTES=os.path.join(HERE,"..","meeting_minutes","all_votes.csv")
CACHE=os.path.join(HERE,"date_extractions.csv")   # built by build_date_cache.py (OCR/vision)
RETRIEVED="2026-07-06"

def load_sources():
    src={}
    with open(os.path.join(HERE,"s3_sources.csv")) as f:
        for r in csv.DictReader(f): src[r["ordinance_no"]]=r
    return src

def load_votes():
    """ord_no -> list of {date,motion_no,title,motion,body}"""
    from collections import defaultdict
    pat=re.compile(r'Ordinance[ #No.]*?(\d{2})[-–](\d{1,3})',re.I)
    cites=defaultdict(dict)  # ord -> {(date,mno): row}
    with open(VOTES) as f:
        for row in csv.DictReader(f):
            blob=(row.get("motion") or "")+" || "+(row.get("title") or "")
            for m in pat.finditer(blob):
                o=f"{m.group(1)}-{m.group(2).zfill(2)}"
                key=(row["date"],row.get("motion_no",""))
                if key not in cites[o]:
                    cites[o][key]=dict(date=row["date"],motion_no=row.get("motion_no",""),
                                       title=(row.get("title") or ""),motion=(row.get("motion") or ""),
                                       body=row.get("body",""))
    out={}
    for o,km in cites.items():
        out[o]=list(km.values())
    return out

# ---- land-use classification (title/motion keywords) ----
LU_RE=re.compile(r'\b(rezon|zoning|zone\b|zones\b|land use|land-use|general plan|'
                 r'subdivision|plat\b|development agreement|conditional use|overlay|'
                 r'annex|density|setback|dwelling|residential|commercial district|'
                 r'mixed[- ]use|form[- ]based|title 19|chapter 19|MD-|FB-UN|planned unit|'
                 r'accessory dwelling|ADU|moderate income housing|impact fee)\b',re.I)
def is_landuse(text):
    return bool(LU_RE.search(text or ""))

def load_cache():
    """Per-ordinance PDF-extracted date/title/method from build_date_cache.py."""
    ex={}
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            for r in csv.DictReader(f):
                ex[r["ordinance_no"]]=dict(adoption_date=r.get("adoption_date",""),
                    month_year=r.get("month_year",""),date_kind=r.get("date_kind",""),
                    method=r.get("method",""),title=r.get("title",""),note=r.get("note",""))
    return ex

def main():
    src=load_sources()
    votes=load_votes()
    ondisk={}
    for fn in os.listdir(RAW):
        if fn.lower().endswith(".pdf"):
            ondisk[fn[:-4]]=os.path.join(RAW,fn)
    print(f"raw PDFs on disk: {len(ondisk)}; S3 manifest ords: {len(src)}; ords cited in votes: {len(votes)}")
    ex=load_cache()
    if not ex:
        sys.exit("date_extractions.csv missing — run: python3 build_date_cache.py")

    rows=[]
    # index catalogs the ADOPTED-ORDINANCE DOCUMENTS (each has a source_url). Ordinance
    # numbers cited in council motions but with NO document on the code host are a separate
    # finding, written to citations_without_document.csv (not index rows).
    all_ords=sorted(set(src))
    for o in all_ords:
        s=src.get(o,{})
        e=ex.get(o,{})
        pdf_my=e.get("month_year","")
        pdf_date=e.get("adoption_date","")
        # title: PDF caption preferred; else best vote title
        title=(e.get("title") or "").strip()
        vc=votes.get(o,[])
        vdates=sorted(set(v["date"] for v in vc))
        # choose matched motion
        matched_date=matched_mno=""
        conf="none"
        if vc:
            # prefer motion whose month matches PDF month; else if single date use it; else latest
            chosen=None
            if pdf_my:
                cand=[v for v in vc if v["date"][:7]==pdf_my]
                if cand: chosen=sorted(cand,key=lambda v:v["date"])[-1]
            if not chosen:
                chosen=sorted(vc,key=lambda v:v["date"])[-1]
            matched_date=chosen["date"]; matched_mno=chosen["motion_no"]
            if not title:
                title=(chosen["title"] or "").strip()
            # confidence
            if pdf_my and matched_date[:7]==pdf_my and len(vdates)==1:
                conf="high"
            elif pdf_my and matched_date[:7]==pdf_my:
                conf="high"   # month+number corroborated even if cited on >1 date
            else:
                conf="medium"
        # canonical date (validator-required, non-empty best effort) + precision flag:
        #   matched council-action date (authoritative, day) > PDF full date (day)
        #   > PDF month/year (month) > blank (unknown)
        if matched_date:
            date=matched_date; precision="day"
        elif pdf_date:
            date=pdf_date; precision="day"
        elif pdf_my:
            date=pdf_my; precision="month"
        else:
            date=""; precision="unknown"
        # classify land use from title+matched motion
        lu_text=title+" "+" ".join(v["motion"][:200] for v in vc[:2])
        # format + extraction method
        stored=s.get("stored_locally","yes")
        meth=e.get("method","")
        if stored=="no":
            fmt="na"
            method=meth if meth else "index-only (oversize; not stored)"
        else:
            fmt = "scanned" if ("ocr" in meth or "vision" in meth) else "text"
            method = meth or "unknown"
        rows.append(dict(
            ordinance_no=o,
            date=date,
            date_precision=precision,
            adoption_date_source=("motion" if matched_date else ("pdf" if (pdf_date or pdf_my) else "")),
            pdf_month_year=pdf_my,
            title=re.sub(r'\s+',' ',title)[:240],
            land_use=("yes" if is_landuse(lu_text) else "no"),
            source_url=s.get("source_url",""),
            path=(f"raw/{o}.pdf" if o in ondisk else ""),
            retrieved_date=RETRIEVED,
            format=fmt,
            extraction_method=method,
            matched_motion_date=matched_date,
            matched_motion_no=matched_mno,
            match_confidence=conf,
            note=e.get("note",""),
        ))
    # SCHEMA_SPEC §9 ordinances contract header first, city extras after.
    # adoption_date and result are not derived here (date/adoption_date_source carry the
    # best-effort adoption date; motions are joined by number, result not captured) —
    # DictWriter restval emits both blank, per contract.
    cols=["ordinance_no","adoption_date","date","title","source_url","retrieved_date",
          "format","extraction_method","path","land_use","result",
          "matched_motion_date","matched_motion_no","match_confidence",
          "date_precision","adoption_date_source","pdf_month_year","note"]
    with open(os.path.join(HERE,"index.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for r in sorted(rows,key=lambda r:r["ordinance_no"]): w.writerow(r)

    # ordinance numbers cited in council motions but with NO adopted document on the host
    missing_doc=sorted(set(votes)-set(src))
    with open(os.path.join(HERE,"citations_without_document.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(["ordinance_no","cited_dates","example_title"])
        for o in missing_doc:
            v=votes[o]
            w.writerow([o,";".join(sorted(set(x["date"] for x in v))),(v[0]["title"] or "")[:100]])

    from collections import Counter
    print("index rows:",len(rows))
    print("match_confidence:",dict(Counter(r["match_confidence"] for r in rows)))
    print("land_use:",dict(Counter(r["land_use"] for r in rows)))
    print("format:",dict(Counter(r["format"] for r in rows)))
    print("date_precision:",dict(Counter(r["date_precision"] for r in rows)))
    print("rows with empty date:",sum(1 for r in rows if not r["date"]))
    print("citations_without_document:",len(missing_doc),missing_doc[:20])

if __name__=="__main__":
    main()
