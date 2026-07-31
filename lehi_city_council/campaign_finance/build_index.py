#!/usr/bin/env python3
"""Build campaign_finance/index.csv from downloaded raw filings + batch/manifest.json.

Additive dataset. Retains raw PDFs verbatim (raw/<year>/). This script only writes
index.csv (machine-readable provenance) and joins candidates to election_results/.
It NEVER invents filing amounts — content is left in the raw PDFs.
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-02"

# --- 2025 media-hash -> candidate (from the live financial-disclosures page) ---
H2025 = {
 'izbbd2bf':'Paige Albrecht','kc5pwwiw':'Paige Albrecht','rrfeajfd':'Paige Albrecht',
 'g10dlsmf':'Paige Albrecht','vtll50ue':'Paige Albrecht',
 '1ffk5h4w':'Paul Binns','l04l2bbd':'Paul Binns','zc4k4sl3':'Paul Binns',
 '3t5fjtcj':'Paul Binns','fhohtszx':'Paul Binns',
 'd3tib15l':'Chris Condie','1u2awttt':'Chris Condie','moxd1fjs':'Chris Condie',
 'pb5giuci':'Rachel Freeman','qrxnwz1g':'Rachel Freeman','dradxabs':'Rachel Freeman',
 'bewgny3r':'Rachel Freeman','nm5dtdaz':'Rachel Freeman',
 'tsqbcbiw':'Kenneth Glade','yjippbcb':'Kenneth Glade','epzdqr5o':'Kenneth Glade',
 'xxybhzho':'Paul Hancock','gp3nridr':'Paul Hancock','2crfza1x':'Paul Hancock',
 'gr5jzdfe':'James Harrison','inlkj0ma':'James Harrison','jp5h4eyw':'James Harrison',
 'q1zjmgp4':'James Harrison','1ibebf3i':'James Harrison',
 'soynzfay':'Tyson Hodges','jg3i2pt5':'Tyson Hodges','2tnmgybe':'Tyson Hodges',
 'tu4d1jnh':'Jordan M. Hutchinson','04hpvyvv':'Jordan M. Hutchinson','qibadmnx':'Jordan M. Hutchinson',
 'rjfihlnp':'Emily Lockhart','wtslv1bc':'Emily Lockhart','yo2f5c3y':'Emily Lockhart',
 '1sklztrg':'Emily Lockhart','jyud2nca':'Emily Lockhart',
 'lj4czmvb':'Jared V. Peterson','4iulcekw':'Jared V. Peterson','zgkgevti':'Jared V. Peterson',
 'rk3mp1el':'Jared V. Peterson','kjwbuut4':'Jared V. Peterson',
 'dhlcf0ey':'E. LaRell Stephens','b5sbchbl':'E. LaRell Stephens','f5rjt1zy':'E. LaRell Stephens',
 'cyidicoa':'Charlie Tautuaa','mtapyq2z':'Charlie Tautuaa','5mlplvt2':'Charlie Tautuaa',
}

# Office by year: Mayor filers vs Council (from election_results/lehi_races.csv).
MAYOR = {'2021':{'MARK JOHNSON','JESSE RIDDLE'},
         '2025':{'PAIGE ALBRECHT','PAUL BINNS','CHRIS CONDIE','CHARLIE TAUTUAA'}}
# 2019 & 2023 had NO mayor race -> all Council.

def norm(name):
    n = name.upper().strip()
    n = n.replace('.', ' ').replace(',', ' ')
    n = re.sub(r'\bIII\b|\bJR\b|\bII\b', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n

# candidate-name canonicalization for the join (map filing spelling -> election spelling)
CANON = {
 'IELI CHARLIE TAUTUAA':'IELI CHARLIE TAUTUAA','CHARLIE TAUTUAA':'CHARLIE TAUTUAA',
 'K CASEY GLADE':'K CASEY GLADE','KENNETH GLADE':'KENNETH GLADE',
 'LORI MCINTOSH LE':'LORI MCINTOSH LE','LORI LE':'LORI MCINTOSH LE',
 'MIKE V SOUTHWICK':'MIKE V SOUTHWICK','MIKE SOUTHWICK':'MIKE V SOUTHWICK',
 'JARED V PETERSON':'JARED V PETERSON','JARED PETERSON':'JARED V PETERSON',
 'E LARELL STEPHENS':'E LARELL STEPHENS','LARELL STEPHENS':'E LARELL STEPHENS',
 'JORDAN M HUTCHINSON':'JORDAN M HUTCHINSON','JORDAN HUTCHINSON':'JORDAN M HUTCHINSON',
 'MATTHEW WYNN HEMMERT':'MATTHEW WYNN HEMMERT','MATT HEMMERT':'MATTHEW WYNN HEMMERT',
 'JONATHAN WILLIS':'JOHNATHAN WILLIS',
}

def canon(nm):
    return CANON.get(nm, nm)

# --- load election_results candidate sets per year ---
elec = {}  # year -> {canon_name -> (office, is_winner_any)}
erp = os.path.join(HERE, '..', 'election_results', 'lehi_results_by_candidate.csv')
with open(erp) as f:
    for r in csv.DictReader(f):
        y = r['year']; office = 'Mayor' if r['office']=='Mayor' else 'Council'
        cn = canon(norm(r['candidate']))
        d = elec.setdefault(y, {})
        prev = d.get(cn, (office, False))
        d[cn] = (office, prev[1] or (r['is_winner']=='True'))

# --- filename -> candidate for wayback records (link text can be "Amended") ---
def cand_from_fname(fname):
    b = re.sub(r'^\d{6}_', '', fname)
    b = re.sub(r'\.(pdf|jpg|html)$', '', b, flags=re.I)
    b = re.sub(r'[-_](amended|revised|final|1st|2nd|3rd|final-disclosure|campaign.*|finance.*|disclosure.*|report.*|\d.*)$','',b,flags=re.I)
    return b.replace('-', ' ').replace('_',' ').strip()

# --- report period label from upload path month ---
PERIOD = {
 # (year, month) -> human label ; based on Utah/Lehi municipal filing calendar
 ('2019','08'):'Before Primary (Aug)','2019':'', ('2019','09'):'Before Primary/interim (Sep)',
 ('2019','10'):'Before General (Oct)','2020':'Post-election/annual (following spring)',
 ('2021','10'):'Before General (Oct)',('2021','11'):'Before General/interim (Nov)',('2021','12'):'Final/Post-election (Dec)',
 ('2023','08'):'Before Primary (Aug)',('2023','09'):'Before Primary/amended (Sep)',
 ('2023','10'):'Before General (Oct)',('2023','11'):'Post-election (Nov)',
}

manifest = json.load(open(os.path.join(HERE,'batch','manifest.json')))

# --- text-sidecar backfill manifest (backfill_text.py): honest per-file format/extraction ---
# The original index guessed format by file EXTENSION and mislabeled 64 image-only PDFs as
# born-digital 'text'. text_extraction.csv records what actually extracted (pdftotext text
# layer vs tesseract OCR), so format/extraction_method are corrected per file when present.
TEXTEX = {}
_tx = os.path.join(HERE, 'text_extraction.csv')
if os.path.exists(_tx):
    for _r in csv.DictReader(open(_tx)):
        TEXTEX[_r['path']] = (_r['format'], _r['extraction_method'])

rows = []
for m in manifest:
    year = m['year']; subdir = m['subdir']; out_name = m['out_name']
    relpath = f"raw/{subdir}/{out_name}"
    if not os.path.exists(os.path.join(HERE, relpath)):
        continue  # not downloaded (record separately as unrecovered if any)
    # candidate
    if year == '2025':
        h = out_name.split('_',1)[0]
        cand = H2025.get(h) or cand_from_fname(out_name)
    else:
        cand = m['candidate']
        if not cand or cand.lower() in ('amended','revised','final'):
            cand = cand_from_fname(out_name)
    cn = canon(norm(cand))
    # office
    if year in MAYOR:
        office = 'Mayor' if cn in {canon(norm(x)) for x in MAYOR[year]} else 'Council'
    else:
        office = 'Council'
    # refine office from election_results if candidate present there
    matched = ''; join_conf = 'none'
    if year in elec and cn in elec[year]:
        office = elec[year][cn][0]; join_conf = 'exact'; matched = cn
    elif year in elec:
        # fallback: match on (first token, last token) ignoring middle initials
        def fl(n): t=n.split(); return (t[0], t[-1]) if len(t)>=2 else (n, n)
        want = fl(cn)
        cands = [e for e in elec[year] if fl(e)==want]
        if len(cands)==1:
            office = elec[year][cands[0]][0]; join_conf = 'firstlast'; matched = cands[0]
    # date: upload YYYY-MM-01 for wp-content; election_year for 2025 hashed media
    um = re.match(r'(\d{4})(\d{2})_', out_name)
    if um:
        date = f"{um.group(1)}-{um.group(2)}-01"
        period = PERIOD.get((um.group(1),um.group(2)), f"Filed {um.group(1)}-{um.group(2)}")
    else:
        date = year
        period = m.get('label','') or ''
    # format / extraction
    low = out_name.lower()
    if relpath in TEXTEX:
        fmt, ext = TEXTEX[relpath]           # authoritative: measured text-layer vs OCR
    elif low.endswith('.jpg'):
        fmt, ext = 'scanned', 'image_scan_no_ocr'
    elif low.endswith('.html'):
        fmt, ext = 'html', 'html_attachment_page'
    else:
        fmt, ext = 'text', 'pdf_born_digital_raw_retained'
    amended = 'amended' in low or 'revised' in low
    title = f"{cand} — {year} municipal campaign financial statement" + (f" ({period})" if period else "")
    if amended: title += " [amended/revised]"
    rows.append(dict(
        date=date, candidate=cand, office=office, election_year=year,
        filing_type='statement', title=title,
        source_url=m['source_url'], retrieved_date=RETRIEVED,
        format=fmt, extraction_method=ext, path=relpath,
        matched_election_candidate=matched, join_confidence=join_conf,
        reporting_period=period, amended=('yes' if amended else 'no'),
    ))

rows.sort(key=lambda r:(r['election_year'], r['candidate'], r['date'], r['path']))
# SCHEMA_SPEC §9 contract header, extras after
cols = ['date','candidate','office','election_year','filing_type','reporting_period',
        'title','source_url','retrieved_date','format','extraction_method','path',
        'matched_election_candidate','join_confidence','amended']
with open(os.path.join(HERE,'index.csv'),'w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

# summary
from collections import Counter
print("rows:", len(rows))
print("by year:", dict(Counter(r['election_year'] for r in rows)))
print("by office:", dict(Counter(r['office'] for r in rows)))
print("join none:", sum(1 for r in rows if r['join_confidence']=='none'))
print("candidates joined:", len(set(r['matched_election_candidate'] for r in rows if r['matched_election_candidate'])))
noj = sorted(set((r['election_year'],r['candidate']) for r in rows if r['join_confidence']=='none'))
print("NOT joined to election_results:")
for y,c in noj: print("   ",y,c)
