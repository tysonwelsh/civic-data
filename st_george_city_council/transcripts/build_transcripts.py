#!/usr/bin/env python3
"""Build transcripts/index.csv + unrecovered.csv for St. George council meeting
ASR caption tracks. Cleans any raw en-orig .vtt lacking a text/<date>.md sidecar.
Idempotent: re-run after fetching more captions to pick them up automatically."""
import os, csv, subprocess, sys
D=os.path.dirname(os.path.abspath(__file__))
RAW=os.path.join(D,'raw'); TXT=os.path.join(D,'text')
RET='2026-07-02'
# --- The ~10-meeting recent sample (2025 + early-2026) that HAS YouTube ASR captions ---
# id, date, body, title, channel
SAMPLE=[
 ('HvhkphWhCP0','2025-05-01','CityCouncil','St. George City Council May 1, 2025','CEC'),
 ('uen4Nusw1kY','2025-04-24','CityCouncil','St. George City Council April 24, 2025','CEC'),
 ('4FxtOqSLpZE','2025-04-03','CityCouncil','St. George City Council April 3, 2025','CEC'),
 ('FNhh-onItZI','2025-03-20','CityCouncil','St. George City Council March 20, 2025','CEC'),
 ('pQVQ0BYgxX4','2025-03-06','CityCouncil','St. George City Council March 6, 2025','CEC'),
 ('9o0NbsuD7QI','2025-12-04','CityCouncil','St. George City Council December 4, 2025','SGCITY'),
 ('7cVdHkX2xbo','2025-12-18','CityCouncil','St. George City Council December 18, 2025','SGCITY'),
 ('s8jpJSvwgWw','2026-01-08','CityCouncil','St. George City Council January 8, 2026','SGCITY'),
 ('WHoHV-to2zE','2026-01-15','CityCouncil','St. George City Council January 15, 2026','SGCITY'),
 ('YF5zStdWDqA','2026-01-22','CityCouncil','St. George City Council January 22, 2026','SGCITY'),
]
CHAN={'CEC':'https://www.youtube.com/channel/UCYqm-7xA_iN8IlX4uX3HtNg',
      'SGCITY':'https://www.youtube.com/channel/UCssI3y3sYbIAySKA8M_8dRw'}
def watch(vid): return f"https://www.youtube.com/watch?v={vid}"

# --- clean any raw vtt missing its text sidecar ---
for vid,date,body,title,ch in SAMPLE:
    vtt=os.path.join(RAW,f"{vid}.en-orig.vtt")
    md=os.path.join(TXT,f"{date}.md")
    if os.path.exists(vtt) and not os.path.exists(md):
        subprocess.run([sys.executable,os.path.join(D,'clean_vtt.py'),
                        vtt,md,date,title,watch(vid),vid],check=True)

# --- index rows ---
EM_ASR='yt-dlp --write-auto-sub (YouTube ASR, en-orig) + clean_vtt.py dedupe'
idx=[]; unrec=[]
for vid,date,body,title,ch in SAMPLE:
    vtt_rel=f"raw/{vid}.en-orig.vtt"
    got=os.path.exists(os.path.join(RAW,f"{vid}.en-orig.vtt"))
    if got:
        idx.append(dict(date=date,title=title,body=body,video_url=watch(vid),video_id=vid,
            caption_type='asr',source_url=CHAN[ch],retrieved_date=RET,format='caption',
            extraction_method=EM_ASR,path=vtt_rel))
    else:
        idx.append(dict(date=date,title=title,body=body,video_url=watch(vid),video_id=vid,
            caption_type='none',source_url=CHAN[ch],retrieved_date=RET,format='na',
            extraction_method='none',path=''))
        unrec.append(dict(date=date,title=title,body=body,video_url=watch(vid),video_id=vid,
            reason='ASR caption track exists (probe=HAS) but download blocked by YouTube bot-rate-limit during this run; ret/retry'))

# --- 2023-2024 no-caption gap meetings (video exists, YouTube generated no ASR track) ---
import json
meetings=json.load(open(f"{os.environ['SP']}/meetings.json"))
sample_ids={s[0] for s in SAMPLE}
for m in meetings:
    d=m['date']
    if not d: continue
    if m['vid'] in sample_ids: continue
    if '2023-01-01'<=d<'2025-01-01' and m['hascap']=='NO':
        ch='CEC'
        idx.append(dict(date=d,title=m['title'],body='CityCouncil',video_url=watch(m['vid']),
            video_id=m['vid'],caption_type='none',source_url=CHAN[ch],retrieved_date=RET,
            format='na',extraction_method='none',path=''))
        unrec.append(dict(date=d,title=m['title'],body='CityCouncil',video_url=watch(m['vid']),
            video_id=m['vid'],reason='YouTube has NOT auto-generated an ASR caption track for this video (probe=NO captions); would require Whisper'))

idx.sort(key=lambda r:(r['date'],r['video_id']))
unrec.sort(key=lambda r:(r['date'],r['video_id']))
cols=['date','title','body','video_url','video_id','caption_type','source_url',
      'retrieved_date','format','extraction_method','path']
with open(os.path.join(D,'index.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(idx)
ucols=['date','title','body','video_url','video_id','reason']
with open(os.path.join(D,'unrecovered.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=ucols); w.writeheader()
    for r in unrec: w.writerow({k:r.get(k,'') for k in ucols})
n_asr=sum(1 for r in idx if r['caption_type']=='asr')
n_none=sum(1 for r in idx if r['caption_type']=='none')
print(f"index.csv: {len(idx)} rows ({n_asr} asr retrieved, {n_none} none)")
print(f"unrecovered.csv: {len(unrec)} rows")
