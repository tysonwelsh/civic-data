import json, os, re, subprocess, datetime, calendar, collections
SP="/private/tmp/claude-501/-Users-tysonwelsh-civic-data/f43a66e4-730f-4ca8-a53a-f0b8118a953b/scratchpad/slc_pmn"
DEST="/Users/tysonwelsh/civic-data/slc_city_council/pmn_backfill/raw/2020"
notices=json.load(open(f"{SP}/notices_1360.json"))
meta={}  # file_id -> (notice_date, notice_id, filename, title)
for n in notices:
    if n["date"][:4]!="2020": continue
    for a in n["attachments"]:
        if a["type"]=="Meeting Minutes":
            meta[a["file_id"]]=(n["date"],n["notice_id"],a["filename"],n["title"])
MONTHS={m.lower():i for i,m in enumerate(calendar.month_name) if m}
def extract(fid):
    txt=subprocess.run(["pdftotext","-layout",f"{DEST}/{fid}.pdf","-"],capture_output=True,text=True).stdout
    head=txt[:1500]
    # meeting date e.g. "TUESDAY, FEBRUARY 4, 2020" or "February 4, 2020"
    dm=re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d\d)',head)
    mdate=None
    if dm and dm.group(1).lower() in MONTHS:
        try: mdate=datetime.date(int(dm.group(3)),MONTHS[dm.group(1).lower()],int(dm.group(2))).isoformat()
        except: pass
    low=head.lower()
    if "work session" in low: sess="Work Session"
    elif "formal session" in low or "formal meeting" in low or "formal session" in low: sess="Formal Meeting"
    elif "redevelopment" in low and "council" in low: sess="Formal Meeting"
    else: sess="?"
    ismin = "minutes of the salt lake city council" in low or low.strip().startswith("minutes")
    return mdate,sess,ismin,head[:80].replace("\n"," ")
rows=[]
for fid,(nd,nid,fn,title) in meta.items():
    mdate,sess,ismin,snip=extract(fid)
    rows.append({"file_id":fid,"notice_date":nd,"meeting_date":mdate,"session":sess,
                 "is_minutes":ismin,"filename":fn,"snip":snip})
json.dump(rows,open(f"{SP}/verify2020.json","w"),indent=1)
# summary
print("total files:",len(rows))
print("is_minutes True:",sum(1 for r in rows if r["is_minutes"]),"/",len(rows))
print("meeting_date parsed:",sum(1 for r in rows if r["meeting_date"]),"/",len(rows))
print("notice_date == meeting_date:",sum(1 for r in rows if r["meeting_date"]==r["notice_date"]),"/",len(rows))
print("session breakdown:",dict(collections.Counter(r["session"] for r in rows)))
print("\nNON-minutes or unparsed or date-mismatch:")
for r in rows:
    if not r["is_minutes"] or not r["meeting_date"] or r["meeting_date"]!=r["notice_date"] or r["session"]=="?":
        print("  ",r["file_id"],"notice",r["notice_date"],"mtg",r["meeting_date"],r["session"],"ismin",r["is_minutes"],"|",r["snip"][:55])
