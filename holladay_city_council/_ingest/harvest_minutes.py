import json, sys, time, os
import importlib.util
spec=importlib.util.spec_from_file_location("h","pmn_harvest.py"); H=importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
rows=json.load(open("all_notices.json"))
BODIES={"City Council":"Council","Planning Commission":"PlanningCommission","Redevelopment Agency (RDA)":"RDA","Local Building Authority (LBA)":"LBA"}
targets=[r for r in rows if r["public_body"] in BODIES]
HTMLDIR="notice_html"; os.makedirs(HTMLDIR,exist_ok=True)
# fetch raw HTML to disk (resumable)
done=0
for r in targets:
    nid=r["notice_id"]; p=f"{HTMLDIR}/{nid}.html"
    if os.path.exists(p) and os.path.getsize(p)>1000: continue
    try:
        h=H.get(f"https://www.utah.gov/pmn/sitemap/notice/{nid}.html")
        open(p,"w").write(h)
    except Exception as e:
        open(p,"w").write(f"ERR {e}")
    done+=1
    if done%60==0: print(f"  fetched {done}",file=sys.stderr)
    time.sleep(0.08)
print("fetch done, new:",done)
# parse from disk
minutes=[]
for r in targets:
    p=f"{HTMLDIR}/{r['notice_id']}.html"
    if not os.path.exists(p): continue
    h=open(p).read()
    atts,pb,st=H.parse_notice_html(h)
    for a in atts:
        if "minute" in a["category"].lower():
            minutes.append({**r,"body":BODIES[r["public_body"]],"pb_id":pb,
                            "start_dt":st,"file_id":a["file_id"],
                            "file_name":a["name"],"category":a["category"]})
json.dump(minutes,open("minutes_manifest.json","w"),indent=1)
from collections import Counter
print("MINUTES ATTACHMENTS:",len(minutes),dict(Counter(m["body"] for m in minutes)))
print("unique files:",len({m["file_id"] for m in minutes}))
EOF=0
