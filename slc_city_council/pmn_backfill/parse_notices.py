import re, json, sys, collections
def parse(path):
    html=open(path,encoding="utf-8",errors="replace").read()
    m=re.search(r'<tbody>(.*)</tbody>',html,re.S)
    body=m.group(1) if m else html
    rows=re.split(r'<tr class="(?:on|off)">',body)[1:]
    out=[]
    for r in rows:
        nm=re.search(r'/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>',r,re.S)
        if not nm: continue
        nid=nm.group(1); title=re.sub(r'\s+',' ',nm.group(2)).strip()
        dm=re.search(r'(\d{4}/\d{2}/\d{2})\s+([\d:]+\s*[AP]M)',r)
        date=dm.group(1).replace('/','-') if dm else ''
        atts=[]
        for am in re.finditer(r'/pmn/files/(\d+)\.pdf"[^>]*>(.*?)</a>\s*(?:&nbsp;)?\s*\(([^)]*)\)',r,re.S):
            atts.append({"file_id":am.group(1),"filename":re.sub(r'\s+',' ',am.group(2)).strip(),"type":am.group(3).strip()})
        out.append({"notice_id":nid,"title":title,"date":date,"attachments":atts})
    return out
bodies={"1360":"Council","1274":"PlanningCommission","1277":"RDA","9033":"CRA","3475":"LBA"}
for bid,label in bodies.items():
    data=parse(f"{SP}/notices_{bid}.html".replace("SP",SP)) if False else parse(f"{sys.argv[1]}/notices_{bid}.html")
    json.dump(data,open(f"{sys.argv[1]}/notices_{bid}.json","w"),indent=1)
    dates=[d["date"] for d in data if d["date"]]
    withmin=sum(1 for d in data if any(a["type"]=="Meeting Minutes" for a in d["attachments"]))
    # count attachment types
    types=collections.Counter(a["type"] for d in data for a in d["attachments"])
    print(f"{label} ({bid}): {len(data)} notices, dates {min(dates) if dates else '-'}..{max(dates) if dates else '-'}, notices_with_Meeting_Minutes={withmin}")
    print("   att types:", dict(types))
