import json, csv, collections, re
SP="/private/tmp/claude-501/-Users-tysonwelsh-civic-data/f43a66e4-730f-4ca8-a53a-f0b8118a953b/scratchpad/slc_pmn"
REPO="/Users/tysonwelsh/civic-data/slc_city_council"
verify={r["file_id"]:r for r in json.load(open(f"{SP}/verify2020.json"))}
repo=[r for r in csv.DictReader(open(f"{REPO}/meeting_minutes/minutes_index.csv")) if r["date"][:4]=="2020"]
def repo_sess(t):
    t=t.lower(); return "ws" if ("work session" in t or "retreat" in t) else "formal"
def pmn_sess(v):
    b=v["filename"].lower().replace(".pdf","")
    if "retreat" in b or "ws" in b or "work session" in b: return "ws"
    return "formal"
repo_by=collections.defaultdict(list)
for r in repo: repo_by[(r["date"],repo_sess(r["title"]))].append(r)
pmn_min={fid:v for fid,v in verify.items() if v["is_minutes"]}
agendas=[fid for fid,v in verify.items() if not v["is_minutes"]]
pmn_by=collections.defaultdict(list)
for fid,v in pmn_min.items(): pmn_by[(v["meeting_date"],pmn_sess(v))].append(fid)
# stable order within a date-sess: sort by filename so "r" before "r T-n-T" -> Formal, Formal 2
for k in pmn_by: pmn_by[k].sort(key=lambda fid: pmn_min[fid]["filename"])
for k in repo_by: repo_by[k].sort(key=lambda r: r["title"])
url_rows=[]; new_recover=[]; repo_no_url=[]
for key in sorted(set(list(repo_by)+list(pmn_by))):
    rl=repo_by.get(key,[]); pl=pmn_by.get(key,[]); date,sess=key
    for i in range(max(len(rl),len(pl))):
        r=rl[i] if i<len(rl) else None
        p=pl[i] if i<len(pl) else None
        if r and p:
            url_rows.append({"date":date,"body":"Salt Lake City Council","meeting_type":r["title"],
                "pmn_url":f"https://www.utah.gov/pmn/files/{p}.pdf","pmn_file_id":p,
                "matches_repo_file":"meeting_minutes/"+r["path"],"match_confidence":"high"})
        elif p and not r:
            new_recover.append({"date":date,"sess":sess,"file_id":p,"filename":pmn_min[p]["filename"]})
        elif r and not p:
            repo_no_url.append({"date":date,"sess":sess,"file":r["path"],"title":r["title"]})
url_rows.sort(key=lambda x:(x["date"],x["meeting_type"]))
with open(f"{SP}/url_recovery_2020.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["date","body","meeting_type","pmn_url","pmn_file_id","matches_repo_file","match_confidence"])
    w.writeheader(); w.writerows(url_rows)
print("URL rows:",len(url_rows),"| distinct repo files:",len(set(r['matches_repo_file'] for r in url_rows)))
print("NEW recoveries (PMN minutes, no repo row):")
for x in new_recover: print("   ",x["date"],x["sess"],x["file_id"],x["filename"])
print("Agendas excluded:",[(a,verify[a]['filename']) for a in agendas])
print("Repo rows with NO PMN url:")
for x in repo_no_url: print("   ",x["date"],x["title"])
json.dump({"new_recover":new_recover,"repo_no_url":repo_no_url,"agendas":agendas},open(f"{SP}/final_meta.json","w"),indent=1)
