#!/usr/bin/env python3
"""v3 Summit County PC vote extractor.

Ceiling (PUBLISHED text): mover+seconder always named; unanimous motions tally-only
(ayes not enumerated); DIVIDED votes name voters; abstentions named in both eras.
names_recorded=True iff any individual voter named.

Four divided-vote grammars are recognised (v3, 2026-07-25):
  1. modern roll      "Tyann Mooney voted AYE" / "John Kucera voted NAY"
  2. dissent list     "MOTION CARRIED (5-2) Commissioner Clyde and Commissioner Hanson opposed."
  3. both-sides       "MOTION FAILED (4-3) Commissioners Willoughby ... voted in approval
                       Commissioners Henrie ... opposed."   <- note the tally is
                       PREVAILING-SIDE-FIRST here; the names are authoritative, not the digits
  4. poll grid        "Commissioner Stevens- Nay    Commissioner Simons- Yea"  (2020 era,
                       two columns, may be interrupted by a running page header)
Grammars 3 and 4, and wrapped/dotted-leader continuations of 2, were previously unparsed.

NOT ingested by design: the Granicus HTML retains a `<!-- AYES:/NOES:/ABSENTS: -->` block
that the portal never renders. It is real (520/520 blocks agree with the published tally)
but it is unpublished, and it adds NO dissent attribution — all 25 divided motions already
name their dissenter in the rendered text. Owner ruling 2026-07-25: published prose only.
See _audits/2026-07-25/remediation.md.
"""
import re, os, glob, csv, json

ROOT="/Users/tysonwelsh/civic-data/summit_county/land_use"
MINDIR=os.path.join(ROOT,"minutes")
NAMEC=r"[A-Z][a-zA-Z'’-]+(?:\s+[A-Z][a-zA-Z'’-]+){0,2}"
TITLE=r"(?:\*\s*)?(?:Commissioners?\s+|Vice[- ]?Chair(?:man)?\s+|Chair(?:man)?\s+|Chair\s+|Mr\.?\s+|Ms\.?\s+|Chairman\s+)?"
# NOTE the \s+ between every word: several OCR'd minutes (e.g. 2016-11-03 eastern) are
# TAB-separated, so a literal-space "made a motion" matched nothing and the whole meeting
# yielded zero motions. Same whitespace-tolerance lesson as the utah_county anchor bug.
ANCHOR=re.compile(r"(?:^|[.\s•)])"+TITLE+r"("+NAMEC+r")\s+(?:made\s+(?:a|the)\s+motion|moved)\b", re.M)
STOP={'the','motion','commissioner','commissioners','staff','report','cup','absent','abstain','abstained',
      'chair','chairman','vice','and','county','planning','commission','a','all','mr','ms','who','she','he',
      'they','members','member','vote','voted','aye','nay','no','opposed','against','none','director','planner',
      # 2026-07-25: verbs that trail a name and were riding into it ("Henrie said",
      # "Christopher Conabee seconded" became person names).
      'seconded','second','said','moved','made','asked','stated','noted','added','agreed','wondered',
      'answered','explained','replied','felt','thought','believed','is','was','were','in','on','as','to'}
TITLE_TOKENS={'commissioner','commissioners','chair','chairman','vice','vice-chair','mr','mr.','ms','ms.','chair.'}

# Dash class covers ASCII '-', en/em dash, and U+2010 HYPHEN — OCR'd files print "(7‐0)"
# with U+2010, which the ASCII-only class silently failed to read as a tally.
_D=r'(?:-|‐|‑|‒|–|—|to)'
TALLY=re.compile(r'\((\d+)\s*'+_D+r'\s*(\d+)(?:\s*'+_D+r'\s*(\d+))?\)')
# The outcome word the clerk prints alongside the tally. Bound the result to THIS marker.
RESULT_MARKER=re.compile(
    r'(?:•\s*)?MOTION\s+(?:CARRIED|FAILED|DENIED|PASSED)\b'
    r'|motion\s+(?:carried|failed|denied|passed|did not (?:carry|pass))\b'
    r'|all voted in favor|passed unanimously|carried unanimously|voted unanimous', re.I)
# Dotted leaders wrap continued name lists in the 2015-16 eastern minutes:
#   "MOTION FAILED (3-4) Chair Ure, Commissioner Wharton, Commissioner Hanson,
#    ,……..…………………………    Commissioner Clyde voted against."
LEADERS=re.compile(r'[.…]{3,}|[,;]\s*(?=[.…])')
def deleader(s):
    """Join a wrapped, dotted-leader name list into one line so name regexes can see it."""
    return re.sub(r'\s+',' ',LEADERS.sub(' ',s))

# A comma/and-separated list of titled names.
_NL=r'((?:'+TITLE+NAMEC+r'(?:\s*,\s*|\s*,?\s*and\s+|\s*&\s*))*'+TITLE+NAMEC+r')'
# The 2015-16 eastern clerk names the divided sides in six interchangeable forms — three
# LEADING ("Opposed were X, Y and Z") and three TRAILING ("X, Y and Z voted against").
# Leading forms are tried first so their names aren't re-consumed by a trailing pattern.
SIDE_PATTERNS=[
    (r'(?:Those\s+)?(?:voting|voted)\s+in\s+(?:approval|favor)\s+were[:\s]+'+_NL, 'Aye'),
    (r'In\s+(?:approval|favor)\s+were[:\s]+'+_NL,                                 'Aye'),
    (r'(?:Those\s+)?(?:voting|voted)\s+against\s+were[:\s]+'+_NL,                 'Nay'),
    (r'(?:Those\s+)?Opposed\s+were[:\s]+'+_NL,                                    'Nay'),
    (_NL+r'\s+voted\s+in\s+(?:approval|favor)\b',                                 'Aye'),
    # trailing, explicit verb — permissive (this is the original v2 form, plus 'objected')
    (_NL+r'\s+(?:voted\s+against|opposed|objected|voted\s+in\s+opposition)\b',    'Nay'),
    # trailing, BARE 'against' ("... and Commissioner Hanson against.") — requires
    # terminal punctuation, otherwise it swallows ordinary prose ("argued against the plan")
    (_NL+r'\s+against\s*[.;]',                                                    'Nay'),
]

# Roll-call poll grid: "Commissioner Stevens- Nay    Commissioner Kucera-Nay".
# NAMEC cannot be reused here — it admits internal hyphens and spans newlines via \s+, so
# it swallowed "Kucera-Nay \nCommissioner Harte" as a single name and lost 4 of 7 voters.
# This pattern keeps the name hyphen-free and confined to one line (literal space, not \s).
_VOTE_TOK=r'(?:Yea|YEA|Aye|AYE|Nay|NAY|No|NO|Abstain(?:ed)?|ABSTAIN(?:ED)?)'
POLL_ROW=re.compile(TITLE+r"([A-Z][A-Za-z'’]+(?: [A-Z][A-Za-z'’]+)?)[ \t]*[-–‐‑][ \t]*("+_VOTE_TOK+r")\b")

def clean(s): return re.sub(r'\s+',' ',s).strip(" .,;:•*")
def valid_name(n):
    if not n: return None
    n=clean(n)
    # cut at a period (don't cross sentence boundary)
    n=n.split('.')[0].strip()
    toks=[t for t in n.split() if t]
    # drop leading title tokens
    while toks and toks[0].lower().strip('.') in TITLE_TOKENS: toks.pop(0)
    # trim trailing stopword tokens
    while toks and toks[-1].lower().strip('.,') in STOP: toks.pop()
    if not toks: return None
    if any(t.lower().strip('.,') in STOP for t in toks): return None
    if len(toks)>3: toks=toks[:2]
    return ' '.join(toks)

def collapse_markers(seg, marks):
    """A single vote is often announced twice — a prose restatement then the clerk's formal
    record line ('A vote was called for. The motion carried.' … '• MOTION CARRIED (5-1) …').
    Collapse a run into ONE marker, keeping the tally-bearing member, so restatements do not
    manufacture extra motions. Markers further apart than GAP are separate votes."""
    GAP=300
    out=[]
    for m in marks:
        if out and m.start()-out[-1][-1].end() <= GAP: out[-1].append(m)
        else: out.append([m])
    def tally_pos(m):
        """Absolute offset of the tally this marker binds to (None if it has none).
        Two markers that bind to the SAME tally are one vote announced twice —
        '• MOTION CARRIED (7-0)  All voted in favor.' is a single outcome, not two."""
        ls,_le,scope = marker_scope(seg,m)
        t=TALLY.search(scope)
        return None if not t else ls+t.start()
    picked=[]
    for run in out:
        seen={}
        for m in run:
            tp=tally_pos(m)
            if tp is None: continue
            seen.setdefault(tp, m)          # first marker binding to this tally wins
        # Distinct tallies close together are DISTINCT votes on consecutive short items —
        # never merge those, or the second item silently loses its outcome.
        if seen: picked.extend(seen[k] for k in sorted(seen))
        else:    picked.append(run[0])      # bare prose outcome, no tally printed
    return picked

def marker_scope(seg, m):
    """(line_start, line_end, text) for a marker's own line + the next line when that line
    is not itself a new marker (a tally can wrap: 'MOTION FAILED\\n(3-4) …')."""
    ls=seg.rfind('\n',0,m.start())+1
    le=seg.find('\n',m.end());  le=len(seg) if le<0 else le
    scope=seg[ls:le]
    nl=seg.find('\n',le+1);  nl=len(seg) if nl<0 else nl
    nxt=seg[le+1:nl]
    if nxt and not RESULT_MARKER.search(nxt): scope+=' '+nxt
    return ls, le, scope

# A sentence that reads like the substance of a motion, for items whose "made a motion"
# phrasing the clerk omitted (the item is real — the clerk printed a vote for it).
ACTION=re.compile(r'\b(approve|approval|deny|denial|recommend|recommendation|continue|table|'
                  r'adopt|forward|amend|grant|reject|ratif|rezone|conditional use|plat)\w*\b', re.I)

PAGE_MARK=re.compile(r'Page\s+(\d+)\s+of\s+(\d+)', re.I)
def strip_duplicate_body(body):
    """Some source PDFs contain the SAME meeting twice (2015-01-08 eastern runs pages
    2..22 and then 2..22 again), which doubles every motion. Detect it from the running
    page-footer sequence restarting at the same page TOTAL, and keep only the first copy.
    Conservative on purpose: a restart with a different total is a different document
    (an appended exhibit) and is left alone."""
    marks=[(m.start(), int(m.group(1)), int(m.group(2))) for m in PAGE_MARK.finditer(body)]
    for i in range(1, len(marks)):
        prev_pos, prev_pg, prev_tot = marks[i-1]
        pos, pg, tot = marks[i]
        if tot==prev_tot and pg<prev_pg and prev_pg>=tot-1:
            # cut at the start of the line carrying the restarting footer
            ls=body.rfind('\n', 0, pos)+1
            return body[:ls], True
    return body, False

def frontmatter(t):
    m=re.match(r'---\n(.*?)\n---\n', t, re.S); d={}
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line: k,v=line.split(':',1); d[k.strip()]=v.strip()
        t=t[m.end():]
    return d,t

def parse_file(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    fm,body=frontmatter(t)
    body,_dedup=strip_duplicate_body(body)
    date=fm.get('date',''); bodyname=fm.get('body',''); slug=fm.get('body_slug','')
    src=os.path.relpath(path,'/Users/tysonwelsh/civic-data/summit_county')
    # ---- v4 (2026-07-25): MARKER-ANCHORED segmentation -------------------------------
    # v3 found items by their "X made a motion" verb and then hunted for a result. Where a
    # clerk phrased an item differently the item vanished, and its printed outcome was
    # inherited by whichever item WAS found — 43% of meetings had more printed outcomes
    # than found items. v4 pairs the two streams in document order instead: every printed
    # outcome gets its own item, and an item with no printed outcome keeps an honest blank.
    anchors=list(ANCHOR.finditer(body))
    markers=collapse_markers(body, list(RESULT_MARKER.finditer(body)))
    events=sorted([(a.start(),'A',a) for a in anchors]+[(m.start(),'R',m) for m in markers])
    pairs=[]           # (anchor_or_None, marker_or_None)
    pending=None
    for _pos,kind,obj in events:
        if kind=='A':
            if pending is not None: pairs.append((pending,None))   # item, no printed outcome
            pending=obj
        else:
            pairs.append((pending,obj)); pending=None              # pending may be None →
            #                                       an outcome whose verb the clerk omitted
    if pending is not None: pairs.append((pending,None))

    motions=[]
    for i,(anc,mk) in enumerate(pairs):
        mover=valid_name(anc.group(1)) if anc else None
        # segment: from this item's start to the start of the NEXT item
        start=(anc.end() if anc else max(0, (pairs[i-1][1].end() if i and pairs[i-1][1] else 0)))
        if i+1<len(pairs):
            nxt_a,nxt_m=pairs[i+1]
            end=nxt_a.start() if nxt_a else nxt_m.start()
        else:
            end=min(len(body), (mk.end()+400) if mk else start+1600)
        # never let a segment stop before its own outcome line
        if mk: end=max(end, marker_scope(body,mk)[1]+1)
        seg=body[start:end]
        # re-locate this item's own marker inside the segment
        rm_fixed=None
        if mk:
            for _m in RESULT_MARKER.finditer(seg):
                if start+_m.start()==mk.start(): rm_fixed=_m; break
        # action
        if anc:
            # "…made the motion, which was seconded by Commissioner Clyde to approve X"
            # — v2/v3 required a comma after the seconder, so with none the strip failed and
            # the split left the fragment "which was" as the motion text (26 rows).
            # every gap is \s+ : tab-separated OCR files broke the literal-space forms
            # "…seconded by X, TO approve …" and "…seconded by X, THAT the Commission
            # approves …" are both in use; requiring 'to' left the latter as "which was".
            head=re.sub(r'^\s*,?\s*(?:which\s+was\s+)?seconded\s+by\s+'+TITLE+NAMEC+r'\s*,?\s*(?:to|that)\s+','',seg[:800])
            act=re.sub(r'^\s*(?:,?\s*which\s+was\s+seconded\s+by[^,]*,\s*)?(?:to|that)\s+','',head)
            act=re.split(r'(?:\.\s|\b'+NAMEC+r'\s+seconded\b|The\s+motion\s+was\s+seconded|seconded\s+the\s+motion|\bseconded\s+by\b)', act)[0]
            act=clean(act)[:1000]
        else:
            # No motion verb was printed for this item, but the clerk recorded a vote for
            # it, so the item is real. Take the last action-bearing sentence before the
            # outcome line; if none reads like a motion, leave it blank rather than invent
            # one (the vote and tally are still faithfully recorded).
            head=seg[:rm_fixed.start()] if rm_fixed else seg
            sents=[s.strip() for s in re.split(r'(?<=[.!?])\s+', head) if s.strip()]
            # never take the outcome line itself as the motion's substance
            # never take an outcome statement as the motion's substance. RESULT_MARKER alone
            # is not enough — variants like "All voted in approval" are outcome sentences
            # that ACTION matches on the word "approval".
            outcome=re.compile(r'\ball\s+voted\s+in\s+(?:favor|approval)\b|\bmotion\s+(?:carried|failed|passed)\b'
                               r'|\bMOTION\s+(?:CARRIED|FAILED|DENIED|PASSED)\b', re.I)
            cand=[s for s in sents[-6:]
                  if ACTION.search(s) and not RESULT_MARKER.search(s) and not outcome.search(s)]
            act=clean(cand[-1])[:1000] if cand else ''
        # seconder
        sec=None
        for pat in [r'seconded by '+TITLE+'('+NAMEC+')',
                    r'('+NAMEC+r')\s+seconded the motion',
                    r'('+NAMEC+r')\s+seconded\b',
                    r'which was seconded by '+TITLE+'('+NAMEC+')']:
            ms=re.search(pat, seg)
            if ms: sec=valid_name(ms.group(1));
            if sec: break
        # result + tally — anchored on the NEAREST result marker after the motion.
        # 2026-07-25 fix: previously this searched the whole segment (which runs to the next
        # motion anchor, sometimes 40k+ chars) and took the FIRST Pass keyword anywhere,
        # so a motion could harvest the tally/outcome of a different, later motion
        # (2020-06-23 m1 took "MOTION CARRIED (6-1)" from ~10k chars downstream while its
        # own item had failed). Source prints the outcome word and the tally on the SAME
        # line, so bind them to that line. No marker within the window => honest blank.
        # Prefer the marker whose own line carries the tally — the clerk's formal record
        # line ("MOTION CARRIED (5-1) Commissioner Klingenstein opposed.") is often preceded
        # by a bare prose restatement ("A vote was called for. The motion carried."), and
        # anchoring on the prose one cuts the trailing name list out of the window.
        def _tally_scope(mstart, mend):
            """The marker's own line, plus the next line only if that line is not itself
            a new result marker (a tally may wrap: 'MOTION FAILED\n(3-4) ...')."""
            ls=seg.rfind('\n',0,mstart)+1
            le=seg.find('\n',mend);  le=len(seg) if le<0 else le
            scope=seg[ls:le]
            nl=seg.find('\n',le+1);  nl=len(seg) if nl<0 else nl
            nxtline=seg[le+1:nl]
            if nxtline and not RESULT_MARKER.search(nxtline): scope+=' '+nxtline
            return ls, le, scope
        # v4: the marker is assigned by the document-order pairing above, not re-hunted.
        rm=rm_fixed
        res=''; tally=None; yes=no=abst_ct=None
        if rm:
            ls, le, scope = _tally_scope(rm.start(), rm.end())
            rline=seg[ls:le]
            tally=TALLY.search(scope)
            if tally:
                yes=int(tally.group(1)); no=int(tally.group(2))
                abst_ct=int(tally.group(3)) if tally.group(3) else None
            rl=rline.lower()
            if re.search(r'(?:motion\s+)?(?:carried|passed)\b|all voted in favor|unanimous', rl): res='Pass'
            elif re.search(r'(?:motion\s+)?(?:failed|denied|did not (?:carry|pass))\b', rl): res='Fail'
            elif tally: res='Pass' if (yes or 0)>(no or 0) else 'Fail'
        # named individual votes
        votes=[]  # (member, vote)
        # modern rolls
        for mm in re.finditer(r'('+NAMEC+r')\s+voted\s+(AYE|NAY|NO|ABSTAIN|ABSTAINED)\b', seg):
            nm=valid_name(mm.group(1)); v=mm.group(2).upper()
            if nm: votes.append((nm,'Aye' if v=='AYE' else ('Abstain' if v.startswith('ABSTAIN') else 'Nay')))
        rolled=set(n for n,_ in votes)
        # 2026-07-25: roll-call POLL GRID (2020 snyderville era). The chair calls each
        # member in a two-column grid terminated by the result marker:
        #   "Commissioner Stevens- Nay    Commissioner Cooke- Nay
        #    Commissioner Simons- Yea    Commissioner Kucera-Nay"
        # A running page header can interrupt the grid mid-poll, so scan the whole window
        # up to (and not past) this motion's own result marker.
        if not votes:
            poll_end=rm.start() if rm else len(seg)
            # NOTE: no re.I — it would defeat NAMEC's leading-capital requirement and let
            # sentence fragments ("is going into", "on") be captured as voters.
            for pm in re.finditer(POLL_ROW, seg[:poll_end]):
                nm=valid_name(pm.group(1)); v=pm.group(2).lower()
                if not nm: continue
                votes.append((nm,'Aye' if v in ('yea','aye') else ('Abstain' if v.startswith('abstain') else 'Nay')))
            rolled=set(n for n,_ in votes)
        # older dissent lists: '<names> voted against' / '<names> opposed' / 'Opposed were <names>'
        # 2026-07-25: run over a de-leadered window so wrapped lists join, and capture the
        # APPROVING side too ('... voted in approval  ... opposed.') — both sides are named
        # in the 2016 eastern form, which previously yielded no rows at all.
        if not votes:
            # The dissent/approval list trails its result marker ("MOTION CARRIED (5-2)
            # Commissioner Clyde and Commissioner Hanson opposed.") and may wrap over
            # several dotted-leader lines, so the window must extend PAST the marker —
            # but never into the next motion's result.
            if rm:
                nxt=RESULT_MARKER.search(seg, rm.end())
                wnd=deleader(seg[:nxt.start() if nxt else min(len(seg), rm.end()+600)])
            else:
                wnd=deleader(seg[:2000])
            for pat,val in SIDE_PATTERNS:
                for dm in re.finditer(pat, wnd):   # no re.I — see note above
                    for nm in re.split(r'\s*,\s*|\s+and\s+|\s*&\s*', dm.group(1)):
                        nm2=valid_name(re.sub(TITLE,'',nm))
                        if nm2 and nm2 not in set(n for n,_ in votes): votes.append((nm2,val))
        # abstentions (both eras) '<Name> abstained' / 'Abstain: <names>'
        for am in re.finditer(r'('+NAMEC+r')\s+abstained\b', seg):
            nm=valid_name(am.group(1))
            if nm and nm not in set(n for n,_ in votes): votes.append((nm,'Abstain'))
        for am in re.finditer(r'Abstain(?:ed)?[:\s]+('+NAMEC+r')', seg):
            nm=valid_name(am.group(1))
            if nm and nm not in set(n for n,_ in votes): votes.append((nm,'Abstain'))
        # dedupe votes by member (keep first)
        seen=set(); dv=[]
        for nm,v in votes:
            if nm in seen: continue
            seen.add(nm); dv.append((nm,v))
        votes=dv
        names_recorded=len(votes)>0
        # Tally ORIENTATION. On failed motions this clerk sometimes prints the prevailing
        # side first ("MOTION FAILED (6-1)" over a roll of 1 Yea / 6 Nay), which would
        # otherwise store yes=6/no=1 against a roll that says the opposite. Where a full
        # named roll exists and contradicts the parsed orientation, the NAMES win — the
        # verbatim `tally` string is still kept exactly as printed (cardinal rule 2).
        if votes and yes is not None and no is not None:
            n_aye=sum(1 for _,v in votes if v=='Aye'); n_nay=sum(1 for _,v in votes if v=='Nay')
            if n_aye+n_nay==(yes+no) and (n_aye,n_nay)==(no,yes) and yes!=no:
                yes,no=n_aye,n_nay
        motions.append(dict(date=date,body=bodyname,body_slug=slug,motion_no=i+1,
            motion=act,result=res,tally=(tally.group(0) if tally else ''),
            yes='' if yes is None else yes,no='' if no is None else no,
            mover=mover or '',seconder=sec or '',votes=votes,names_recorded=names_recorded,source=src))
    return motions

def main():
    files=sorted(glob.glob(os.path.join(MINDIR,'*','*.md')))
    allm=[]
    for f in files: allm.extend(parse_file(f))
    named=sum(1 for m in allm if m['names_recorded'])
    voterows=sum(len(m['votes']) for m in allm)
    print(f"motions={len(allm)} names_recorded={named} named_vote_rows={voterows}")
    # write motions_tally.csv (ALL motions)
    with open(os.path.join(ROOT,'motions_tally.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['date','body','body_slug','motion_no','motion','result','tally','yes','no','mover','seconder','names_recorded','source'])
        for m in allm:
            w.writerow([m['date'],m['body'],m['body_slug'],m['motion_no'],m['motion'],m['result'],
                m['tally'],m['yes'],m['no'],m['mover'],m['seconder'],str(m['names_recorded']).lower(),m['source']])
    # write all_votes.csv (one row per NAMED voter)
    with open(os.path.join(ROOT,'all_votes.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['date','year','title','body','body_slug','motion_no','motion','motion_type','result','mover','seconder','member','vote','source'])
        for m in allm:
            for member,vote in m['votes']:
                w.writerow([m['date'],m['date'][:4],m['body'],m['body'],m['body_slug'],m['motion_no'],
                    m['motion'],'',m['result'],m['mover'],m['seconder'],member,vote,m['source']])
    print("wrote motions_tally.csv + all_votes.csv")

if __name__=='__main__': main()
