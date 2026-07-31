#!/usr/bin/env python3
"""Sandy PC subtree from the Legistar structured harvest (db/staging). Sandy is Legistar — PC votes
are EXACT EventItemVote records (body 140), not prose-parsed. Emits all_votes.csv (13-col, matching
the other cities) + roster.csv. (Minutes documents aren't separately retrievable: Legistar webapi is
disabled for 'sandy' and staging carries no minutes-file URLs — see CLAUDE.md.)"""
import csv, os, collections
HERE=os.path.dirname(os.path.abspath(__file__)); S=os.path.join(os.path.dirname(HERE),"db","staging")
def rd(n): return list(csv.DictReader(open(os.path.join(S,n))))
PC=140
events={e["EventId"]:e for e in rd("events.csv") if e.get("EventBodyId")==str(PC)}
persons={p["PersonId"]:p["PersonFullName"] for p in rd("persons.csv")}
votes=collections.defaultdict(list)
for v in rd("votes.csv"): votes[v["EventItemId"]].append(v)
VMAP={"yes":"Aye","aye":"Aye","no":"Nay","nay":"Nay","abstain":"Abstain","recused":"Recuse","recuse":"Recuse","absent":"Absent","excused":"Excused","conflict":"Recuse"}
def vn(x): return VMAP.get((x or "").strip().lower(),"")
def pname(x):
    if not x: return ""
    return persons.get(str(x), x if not str(x).isdigit() else "")
items=[it for it in rd("eventitems.csv") if it.get("EventItemEventId") in events]
# order items per meeting by minutes/agenda sequence
def seq(it):
    for k in ("EventItemMinutesSequence","EventItemAgendaSequence"):
        try: return int(it.get(k) or 0)
        except: return 0
    return 0
bymtg=collections.defaultdict(list)
for it in items: bymtg[it["EventItemEventId"]].append(it)
rows=[]; rostercount=collections.Counter(); rosterspan={}
for eid,its in bymtg.items():
    ev=events[eid]; date=(ev.get("EventDate") or "")[:10]; year=date[:4]
    its=sorted(its,key=seq)
    mno=0
    for it in its:
        vs=votes.get(it["EventItemId"],[])
        if not vs: continue  # only emit motions with recorded per-member roll calls
        mno+=1
        ayes=sum(1 for v in vs if vn(v["VoteValueName"])=="Aye"); nays=sum(1 for v in vs if vn(v["VoteValueName"])=="Nay")
        passed=(it.get("EventItemPassedFlagName") or "")
        result=f"{ayes}:{nays} {passed}".strip()
        title=(it.get("EventItemTitle") or "").strip().replace("\n"," ")
        mtype=it.get("EventItemMatterType") or ""
        mover=pname(it.get("EventItemMover")); seconder=pname(it.get("EventItemSeconder"))
        for v in vs:
            nm=v.get("VotePersonName") or pname(v.get("VotePersonId")); val=vn(v["VoteValueName"])
            if not nm or not val: continue
            rows.append([date,year,"Planning Commission","PlanningCommission",mno,title,mtype,result,mover,seconder,nm,val,"db/staging (Legistar EventItemVote, body 140)"])
            rostercount[nm]+=1
            d=rosterspan.get(nm,[date,date]); d[0]=min(d[0],date); d[1]=max(d[1],date); rosterspan[nm]=d
rows.sort(key=lambda r:(r[0],r[4]))
with open(os.path.join(HERE,"all_votes.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["date","year","title","body","motion_no","motion","motion_type","result","mover","seconder","member","vote","source"]); w.writerows(rows)
with open(os.path.join(HERE,"roster.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["commissioner","first_seen","last_seen","n_votes"])
    for nm in sorted(rosterspan): w.writerow([nm,rosterspan[nm][0],rosterspan[nm][1],rostercount[nm]])
print(f"PC events(body140)={len(events)} | motions w/ rollcall={len({(r[0],r[4]) for r in rows})} | vote rows={len(rows)} | commissioners={len(rosterspan)}")
print(f"date range: {min(r[0] for r in rows)} -> {max(r[0] for r in rows)}")
