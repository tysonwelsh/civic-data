#!/usr/bin/env python3
"""Copperton minutes acquisition: download -> verify -> (OCR if scanned) -> markdown.
Reads a manifest (date -> ranked candidates), writes raw/ + minutes/ + returns index rows.
Resumable: skips dates whose markdown already exists unless --force.
"""
import os,sys,re,csv,json,subprocess,hashlib,zipfile,io
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'

def curl(url):
    r=subprocess.run(["curl","-k","-sL","--max-time","90","-A",UA,url],capture_output=True)
    return r.stdout

def pdf_text(path):
    """Per-page hybrid: use born-digital text where present, OCR only image pages, merge."""
    try:
        import fitz
        d=fitz.open(path)
    except Exception:
        # last resort: pdftotext whole-file
        try:
            out=subprocess.run(["pdftotext","-layout",path,"-"],capture_output=True,timeout=120)
            return out.stdout.decode("utf-8","replace"),"text"
        except Exception:
            return "","fail"
    chunks=[]; n_ocr=0; n_text=0
    for p in d:
        txt=p.get_text()
        if len(txt.strip())<40:
            try:
                png=p.get_pixmap(dpi=250).tobytes("png")
                r=subprocess.run(["tesseract","stdin","stdout","--psm","6"],input=png,
                                 capture_output=True,timeout=180)
                otxt=r.stdout.decode("utf-8","replace")
                if len(otxt.strip())>=40: n_ocr+=1
                txt=otxt
            except Exception: pass
        else:
            n_text+=1
        chunks.append(txt)
    full="\n".join(chunks)
    fmt = "text" if n_ocr==0 else ("ocr" if n_text==0 else "text+ocr")
    return full,fmt

def docx_text(raw_bytes):
    try:
        z=zipfile.ZipFile(io.BytesIO(raw_bytes))
        xml=z.read("word/document.xml").decode("utf-8","replace")
        xml=re.sub(r'</w:p>','\n',xml)
        xml=re.sub(r'<[^>]+>','',xml)
        import html as H
        return H.unescape(xml)
    except Exception:
        return ""

def pdf_meta_title(path):
    try:
        out=subprocess.run(["pdfinfo",path],capture_output=True,timeout=30).stdout.decode("utf-8","replace")
        m=re.search(r'Title:\s*(.*)',out); return (m.group(1).strip() if m else "")
    except Exception: return ""

MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"]
def date_variants(d):
    y,m,day=d.split("-"); mi=int(m)-1
    return [f"{int(m)}/{int(day)}/{y}", f"{int(m)}-{int(day)}-{y}", f"{int(m):02d}-{int(day):02d}-{y}",
            f"{int(m):02d}/{int(day):02d}/{y}", f"{MONTHS[mi]} {int(day)}, {y}", f"{MONTHS[mi]} {int(day)}",
            f"{int(m):02d}-{int(day):02d}-{y[2:]}", f"{y}/{m}/{day}"]

def looks_like_minutes(text):
    t=text.lower()
    markers=('minute','motion','moved','seconded','vote','unanimous','council member',
             'councilmember','commissioner','mayor','aye','nay')
    return sum(1 for k in markers if k in t)

def verify(text,title,date,body):
    """Return (ok, reason). Reject wrong-uploads / agenda-only."""
    n_minutes_markers=looks_like_minutes(text)
    year=date[:4]
    has_year = year in text
    has_date = any(v in text for v in date_variants(date))
    # wrong-doc: metadata title says a DIFFERENT year agenda/spreadsheet and body doesn't match
    if title:
        tl=title.lower()
        if ('agenda' in tl or 'xlsx' in tl or 'budget' in tl) and n_minutes_markers<2 and not has_date:
            return False,f"wrong-doc(meta='{title[:40]}')"
    if n_minutes_markers<2:
        return False,"not-minutes(low-markers)"
    if not (has_year or has_date):
        return False,"date-mismatch"
    return True,("date-in-body" if has_date else "year-only")

def slugify(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:60]

def run(manifest_path, out_root, body, source_label_prefix):
    man=json.load(open(manifest_path))
    idx=[]; unrec=[]; force="--force" in sys.argv
    raw_root=os.path.join(out_root,"raw"); md_root=os.path.join(out_root,"minutes")
    for rec in man:
        date=rec["date"]; year=date[:4]
        md_dir=os.path.join(md_root,year,date)
        md_path=os.path.join(md_dir,f"{date}_{slugify(body+' meeting')}.md")
        if os.path.exists(md_path) and not force:
            # already done; rebuild index row from disk
            idx.append(_index_from_md(md_path,out_root)); continue
        chosen=None
        for c in rec["candidates"]:
            raw=curl(c["url"])
            if not raw or len(raw)<800:
                c["_err"]="empty/small"; continue
            magic=raw[:4]
            tmp=os.path.join("/tmp",f"cop_{hashlib.md5(c['url'].encode()).hexdigest()}")
            if magic==b'%PDF':
                open(tmp+".pdf","wb").write(raw)
                text,fmt=pdf_text(tmp+".pdf"); title=pdf_meta_title(tmp+".pdf")
                ftype="pdf"; blob=tmp+".pdf"
            elif magic[:2]==b'PK':
                text=docx_text(raw); fmt="text"; title=""; ftype="docx";
                open(tmp+".docx","wb").write(raw); blob=tmp+".docx"
            else:
                c["_err"]="not-pdf/docx"; continue
            ok,reason=verify(text,title,date,body)
            if not ok:
                c["_err"]=reason; continue
            chosen=dict(c,text=text,fmt=fmt,ftype=ftype,blob=blob,verify=reason,rawlen=len(raw))
            break
        if not chosen:
            unrec.append({"date":date,"reason":"no candidate verified",
                          "candidates":"; ".join(f"{c['source']}:{c['label']}:{c.get('_err','?')}" for c in rec["candidates"])})
            continue
        # write raw
        os.makedirs(os.path.join(raw_root,year),exist_ok=True)
        fid=chosen["url"].rsplit("/",1)[1].split("?")[0]
        ext=".pdf" if chosen["ftype"]=="pdf" else ".docx"
        raw_name=f"{date}_{body}_{chosen['source']}_{fid}".replace(".pdf","").replace(".docx","")+ext
        raw_path=os.path.join(raw_root,year,raw_name)
        with open(chosen["blob"],"rb") as f: data=f.read()
        open(raw_path,"wb").write(data)
        sha=hashlib.sha256(data).hexdigest()[:16]
        # markdown
        os.makedirs(md_dir,exist_ok=True)
        has_date=any(v in chosen["text"] for v in date_variants(date))
        prov=[
            f"# Copperton {body} Meeting Minutes — {date}","",
            f"**Body:** {body}",
            f"**Date:** {date}",
            f"**Source:** {chosen['source']}",
            f"**Source URL:** {chosen['url']}",
            f"**Source label:** {chosen['label']}",
            f"**Format:** {chosen['fmt']}",
            f"**In-body date match:** {'yes' if has_date else 'year-only'}",
            f"**Raw file:** raw/{year}/{raw_name}",
            f"**Raw sha256(16):** {sha}",
            f"**Provenance:** downloaded {chosen['url']} ; verified={chosen['verify']}",
            "","---","",chosen["text"].strip(),""]
        open(md_path,"w",encoding="utf-8").write("\n".join(prov))
        rel=os.path.relpath(md_path,out_root)
        idx.append({"date":date,"year":year,"title":f"Copperton {body} Meeting",
                    "slug":slugify(f"{date} {body} meeting"),"path":rel,
                    "source":chosen["source"],"source_url":chosen["url"],"format":chosen["fmt"]})
        print(f"OK  {date} [{chosen['source']}] {chosen['fmt']} {chosen['verify']}")
    # write index + unrecovered
    idx.sort(key=lambda r:r["date"])
    with open(os.path.join(out_root,"minutes_index.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["date","year","title","slug","path","source","source_url","format"])
        w.writeheader()
        for r in idx: w.writerow(r)
    with open(os.path.join(out_root,"minutes_unrecovered.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["date","reason","candidates"]); w.writeheader()
        for r in unrec: w.writerow(r)
    print(f"\n{body}: indexed {len(idx)} | unrecovered {len(unrec)}")
    for r in unrec: print("  UNREC",r["date"],r["reason"],"|",r["candidates"][:120])
    return idx,unrec

def _index_from_md(md_path,out_root):
    head=open(md_path,encoding="utf-8").read(2000)
    g=lambda k: (re.search(rf'\*\*{k}:\*\*\s*(.*)',head) or re.search('$^','')).group(1).strip() if re.search(rf'\*\*{k}:\*\*',head) else ""
    date=g("Date");
    return {"date":date,"year":date[:4],"title":f"Copperton Meeting","slug":"",
            "path":os.path.relpath(md_path,out_root),"source":g("Source"),
            "source_url":g("Source URL"),"format":g("Format")}

if __name__=="__main__":
    which=sys.argv[1]
    if which=="council":
        run("council_manifest.json","/Users/tysonwelsh/civic-data/copperton_city_council/meeting_minutes","Council","pmn")
    else:
        run("pc_manifest.json","/Users/tysonwelsh/civic-data/copperton_city_council/planning_commission","PlanningCommission","pmn")
