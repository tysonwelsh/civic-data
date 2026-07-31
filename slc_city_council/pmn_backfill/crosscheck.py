import json, csv, datetime, collections
SP="/private/tmp/claude-501/-Users-tysonwelsh-civic-data/f43a66e4-730f-4ca8-a53a-f0b8118a953b/scratchpad/slc_pmn"
REPO="/Users/tysonwelsh/civic-data/slc_city_council"
def repo_dates(path):
    ds=set()
    for r in csv.DictReader(open(path)):
        try: ds.add(datetime.date.fromisoformat(r["date"][:10]))
        except: pass
    return ds
council=repo_dates(f"{REPO}/meeting_minutes/minutes_index.csv")
pc=repo_dates(f"{REPO}/planning_commission/minutes_index.csv")
def near(repo,d,tol=4): return any(abs((d-rd).days)<=tol for rd in repo)
def load(bid): return json.load(open(f"{SP}/notices_{bid}.json"))
def analyze(bid,label,repo):
    data=load(bid)
    by_year=collections.Counter(); rec=[]
    for n in data:
        if not n["date"] or n["date"].startswith("00"): continue
        try: d=datetime.date.fromisoformat(n["date"])
        except: continue
        mins=[a for a in n["attachments"] if a["type"]=="Meeting Minutes"]
        if not mins: continue
        by_year[d.year]+=1
        if 2020<=d.year<=2026 and not near(repo,d):
            rec.append({"notice_date":n["date"],"title":n["title"],"notice_id":n["notice_id"],
                        "file_id":mins[0]["file_id"],"filename":mins[0]["filename"],"body":label})
    print(f"\n== {label} ({bid}) ==  minutes-attachment notices by year:")
    for y in sorted(by_year): print(f"   {y}: {by_year[y]}")
    print(f"   RECOVERABLE in-scope (2020-2026, no repo minutes ±4d): {len(rec)}")
    for x in sorted(rec,key=lambda z:z['notice_date']):
        print("     ",x["notice_date"],"| file",x["file_id"],"|",x["title"][:65])
    return rec, by_year
allrec=[]
res={}
for bid,label,repo in [("1360","Council",council),("1274","PlanningCommission",pc),
                       ("1277","RDA",council),("9033","CRA",council),("3475","LBA",council)]:
    r,by=analyze(bid,label,repo); allrec+=r; res[label]={"by_year":dict(by),"rec":r}
json.dump({"recoverable":allrec,"summary":res},open(f"{SP}/recoverable.json","w"),indent=1)
print("\nTOTAL RECOVERABLE in-scope:",len(allrec))
