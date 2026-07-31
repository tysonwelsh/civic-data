#!/usr/bin/env python3
"""Build pmn_backfill/index.csv per SCHEMA_SPEC §9 pmn_backfill contract:
date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,
retrieved_date,format,extraction_method  (+ orig_filename extra col).
One row per recovered raw document."""
import csv, os, re

HERE = os.path.dirname(__file__)
CONTRACT = ["date","year","title","slug","body","path","source","source_url",
            "notice_url","pmn_body_id","pmn_file_id","retrieved_date","format",
            "extraction_method","orig_filename"]

BODY_LABEL = {"council":("Council","753"), "rda":("RDA","756"), "mba":("MBA","757")}
BODY_TITLE = {"council":"City Council Regular Meeting", "rda":"Redevelopment Agency Meeting",
              "mba":"Municipal Building Authority Meeting"}

def slugify(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def main():
    man = {r["saved_name"]: r for r in csv.DictReader(open(os.path.join(HERE,"_work/target_manifest.csv")))}
    meth = {r["stem"]: r for r in csv.DictReader(open(os.path.join(HERE,"_work/extract_method.csv")))}
    # retrieved date from fetch log
    import json
    ret = {}
    for l in open(os.path.join(HERE,"raw/_fetch_log.jsonl")):
        try: j=json.loads(l)
        except: continue
        if j.get("saved_as"): ret[j["saved_as"]] = j.get("retrieved_utc","")[:10]
    rows=[]
    for saved, m in man.items():
        stem = os.path.splitext(saved)[0]
        bc = m["bodycode"]
        blabel, bid = BODY_LABEL[bc]
        date = m["date"]; year = date[:4]
        # title: special-meeting / budget-retreat detection from orig filename
        of = m["orig_filename"].lower()
        base_title = BODY_TITLE[bc]
        if "special" in of: base_title = f"{blabel} Special Meeting" if bc!="council" else "City Council Special Meeting"
        if "budget retreat" in of: base_title = "City Council Budget Retreat"
        mrow = meth.get(stem, {})
        fmt = mrow.get("format","text")
        em = mrow.get("extraction_method","pdftotext")
        rows.append({
            "date": date, "year": year, "title": base_title,
            "slug": slugify(f"{date}-{blabel}-{base_title}"),
            "body": blabel,
            "path": f"raw/{saved}",
            "source": "pmn",
            "source_url": f"https://www.utah.gov/pmn/files/{m['file_id']}.pdf",
            "notice_url": f"https://www.utah.gov/pmn/sitemap/notice/{m['notice_id']}.html",
            "pmn_body_id": bid,
            "pmn_file_id": m["file_id"],
            "retrieved_date": ret.get(saved,"2026-07-13"),
            "format": fmt,
            "extraction_method": em,
            "orig_filename": m["orig_filename"],
        })
    rows.sort(key=lambda r:(r["date"], r["body"]))
    with open(os.path.join(HERE,"index.csv"),"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=CONTRACT); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"wrote index.csv with {len(rows)} rows")
    for r in rows: print(" ",r["date"],r["body"],r["format"],r["extraction_method"],r["path"])

if __name__=="__main__":
    main()
