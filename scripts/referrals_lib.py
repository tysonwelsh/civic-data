#!/usr/bin/env python3
"""
Shared build_referrals logic (REFACTOR_PLAN 4.2) — lifted verbatim from the 13
byte-identical per-city db/build_referrals.py copies (2026-07-07), parameterized to
also cover the 3 case-number forks (south_jordan / millcreek / taylorsville). Each
city's db/build_referrals.py is now a thin stub that calls main(HERE, ...).

Parameters (exactly the observed per-fork deltas — nothing speculative):
  here                  the city's db/ dir (stubs pass the dirname of their own file)
  case_no_re            compiled per-city planning FILE/CASE NUMBER regex, or None
                        (None = the 13-city behavior: no case-number bridge at all).
                        When both sides of a pair cite the same number it is the
                        strongest possible cross-body key (confidence high); some
                        cities' councils cite none, so the bridge is (correctly)
                        empty there — implemented + reported for honesty.
  case_no_method_label  match_method value for case-number links, added to the CHECK
                        constraint ('pl_number' south_jordan; 'case_no' millcreek/
                        taylorsville). Ignored when case_no_re is None.
  case_no_report_label  label in the signal-check report line ('PL file numbers'
                        south_jordan; 'case numbers' millcreek/taylorsville).
  extra_stopwords       per-city additions to STOP (member/mover surnames + motion
                        verbs — attribution boilerplate, not subject).

REFERRAL FALSE-POSITIVE GUARD (opt-in; ported from the 2026-07-19 OGDEN-LOCAL monkeypatch,
2026-07-20). Two independent layers; ALL FOUR params below default to a FAITHFUL NO-OP, so a
city that passes none gets byte-identical output to the pre-guard lib (proven across all 31
entities at port time). ONLY enable per-city after an evidence review — as of 2026-07-20 ONLY
ogden enables it (see TODO "port the ogden referral guard" follow-up for the enable-elsewhere lead):
  member_names          set of member first/last name tokens (lowercased, apostrophe-stripped
                        to match subject_tokens()). Used by BOTH layers as pure ATTRIBUTION
                        tokens — a shared surname is never, by itself, subject evidence
                        (MEMORY: surnames collide; prefer full-name resolution). Empty = no-op.
  template_stopwords    set of motion/plan/agency BOILERPLATE tokens that leak through STOP
                        (ADOPTED, ENTITLED, SECONDED, MASTER, REINVESTMENT ...). Vetoed as
                        non-content alongside member_names. Empty = no-op.
  content_veto          Layer 1. When True, IDF.score()/contain() return 0.0 unless the two
                        titles share >=1 token that is NOT in (member_names | template_stopwords)
                        — i.e. a genuine distinguishing project word (AIRPORT, ADAMS, UNION ...).
                        Blocks BOTH scoring paths (Jaccard + name-anchored containment) when the
                        entire overlap is template+names. When real content IS shared the original
                        weighted scores are used unchanged. False (default) = veto never fires.
  name_anchor_min       Layer 2. The distinctive-shared floor for the asymmetric name-anchored
                        (containment) path: require >=N rare NON-NAME shared tokens, not a lone
                        rare token (kills a shared STREET name across two DIFFERENT parcels).
                        1 (default) + member_names empty == the original any(df<=max_df) test.
                        ogden passes 2.

======================================================================================
build_referrals — reconstruct the CROSS-BODY referral / related-matter linkage among a city's
governing bodies (Planning Commission, City Council, RDA/CRA, Housing/Building Authority, Board of
Adjustment) and write it into db/civic.db as a typed, confidence-scored, auditable `referral` table.
VENDOR-AGNOSTIC TEMPLATE for PDF/prose portals (pairs with templates/build_db.py prose core).

WHY SEPARATE (two layers, never conflated): build_db.py resolves application_id WITHIN each body
(body-scoped) — exact, never merged across bodies. PDF/prose portals share NO key across bodies, so
the real-world relationships ("the Council decided what the PC recommended"; "the RDA funded a project
the Council rezoned") must be RECONSTRUCTED by record linkage: probabilistic, so every link is scored
+ overridable, and the single-body majority is left UNLINKED.

GRAIN: application <-> application, between TWO DIFFERENT bodies. Each link names a `primary_body`
(the higher-authority body: Council > Planning Commission > agency/other) and a `related_body`.
The classic PC->Council referral is the rows WHERE primary_body='Council' AND related_body matches
the planning commission; `v_referral_chain` surfaces exactly those for back-compat.

SIGNALS (recorded in match_method + confidence):
  case_no  — (only when case_no_re is given) same Utah planning FILE/CASE NUMBER cited by both
             sides: the strongest possible cross-body key -> high on its own (temporal-gated).
  address  — same full Utah grid pair / named-street address. NB many Utah minutes give APPROXIMATE
             GRID INTERSECTIONS ("located at approximately 2100 N 2300 W") = whole crossings, not
             parcels -> intersection-ALONE is co-location (low); reserve high for address+subject.
  subject  — IDF-weighted title agreement: symmetric Jaccard (>=SUBJ_MEDIUM) carries policy/code
             amendments; asymmetric name-anchored containment (>=CONTAIN_MEDIUM) catches a terse
             title covered by a richer one. Specific shared code section reinforces.
  temporal — GATE not signal. For a PC->Council pair it is DIRECTIONAL (the PC must precede the
             Council within TEMPORAL_WINDOW_DAYS, small forward slack). For agency/other pairs
             (RDA<->Council, RDA<->PC, HA<->...) financing/project-area can precede OR follow the
             land-use action, so the gate is SYMMETRIC (+/- TEMPORAL_WINDOW_DAYS).
  override — db/referral_overrides.csv forces (link) / kills (suppress) a pair.
CONFIDENCE: high=address+subject+temporal · medium=strong subject+temporal · low=intersection-only/
            gate-uncertain/secondary (flag; review before quoting).

Idempotent. Run AFTER build_db.py:  python3 db/build_referrals.py
"""
import csv, glob, os, re, sqlite3, sys
from datetime import date

TEMPORAL_WINDOW_DAYS = 400
FORWARD_SLACK_DAYS = 60
SUBJ_MEDIUM = 0.30; CONTAIN_MEDIUM = 0.50; SUBJ_SECONDARY = 0.45; SECONDARY_MARGIN = 0.80

DIRWORD = r'(?:north|south|east|west|n|s|e|w)'
GRID_PAIR = re.compile(rf'\b(\d{{2,5}})\s+({DIRWORD})\.?\s+(\d{{2,5}})\s+({DIRWORD})\b', re.I)
NAMED = re.compile(rf'\b(\d{{2,5}})\s+(?:({DIRWORD})\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+'
    r'(street|st|avenue|ave|drive|dr|lane|ln|road|rd|way|circle|cir|court|ct|boulevard|blvd|parkway|pkwy)\b', re.I)
DABBR = {'north':'n','south':'s','east':'e','west':'w','n':'n','s':'s','e':'e','w':'w'}
def addresses(t):
    t = t or ""; out = set()
    for m in GRID_PAIR.finditer(t):
        out.add(f"{m.group(1)} {DABBR[m.group(2).lower()]} {m.group(3)} {DABBR[m.group(4).lower()]}")
    for m in NAMED.finditer(t):
        out.add(f"{m.group(1)} {DABBR.get((m.group(2) or '').lower(),'')} {m.group(3).lower().strip()}".replace("  "," ").strip())
    return out
CODE_RE = re.compile(r'\b(?:title|chapter|chap|section|sec|table|§)\s*([0-9]{1,2}[-.][0-9a-z\-.]+)\b', re.I)
def code_sections(t): return set(re.sub(r'\s+','',c.lower()) for c in CODE_RE.findall(t or ""))
def pl_numbers(t, rx):
    return set(m.group(0).upper() for m in rx.finditer(t or "")) if rx else set()
STOP = set("""the a an and or of to for on in at by with from is are be this that consider consideration
approve approval approving adopt adoption adopting deny denial request requesting applicant application
city council councilor commissioner office planning commission staff report public hearing ordinance
resolution amending amendment motion item agenda meeting minutes recommend recommending recommendation
positive negative forward vote elect chair vice annual schedule present presented presenting presentation
discussion action staff report findings as located location property project proposed propose
approximately acres acre lot lots unit units zone
zoning rezone district map general plan land use development subdivision plat phase final preliminary
utah ut number no file case intent annex agreement redevelopment agency authority board""".split())
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'&]+|\d{2,5}")
YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")
def subject_tokens(t, stop):
    # strip apostrophes so possessives unify (Founder's==Founders, King's==Kings, Carla's==Carlas)
    return set(w for w in (x.lower().replace("'", "").replace("’", "") for x in TOKEN_RE.findall(t or ""))
               if w not in stop and len(w) > 2 and not YEAR_RE.match(w))
class IDF:
    def __init__(self, docs, member_names=frozenset(), template_stopwords=frozenset(),
                 content_veto=False, name_anchor_min=1):
        import math; from collections import Counter
        df = Counter()
        for toks in docs:
            for t in set(toks): df[t] += 1
        n = max(1, len(docs)); self.df = df
        self.w = {t: math.log((n+1)/(c+0.5)) for t,c in df.items()}; self.default = math.log((n+1)/0.5)
        # --- referral false-positive guard (OPT-IN; the defaults below reproduce the pre-guard
        #     behavior EXACTLY: content_veto off -> score/contain untouched; member_names empty +
        #     name_anchor_min=1 -> distinctive_shared == the original any(df<=max_df) test). Ported
        #     from the 2026-07-19 OGDEN-LOCAL monkeypatch. See main()'s docstring + role_of header.
        self._member_names = frozenset(member_names)               # attribution tokens (member first/last names)
        self._veto_strip = frozenset(member_names) | frozenset(template_stopwords)  # names+boilerplate: never subject content
        self._content_veto = content_veto                          # Layer 1: subject link needs >=1 genuine content token
        self._name_anchor_min = name_anchor_min                    # Layer 2: distinctive non-name shared-token floor
    def wt(self,t): return self.w.get(t,self.default)
    def _real_shared(self,a,b): return (a & b) - self._veto_strip   # shared tokens that are genuine subject content
    def score(self,a,b):
        if not a or not b: return 0.0
        if self._content_veto and not self._real_shared(a,b): return 0.0   # veto: overlap is only template+names
        return sum(self.wt(t) for t in a&b)/ (sum(self.wt(t) for t in a|b) or 1)
    def contain(self,a,b):
        if not a or not b: return 0.0
        if self._content_veto and not self._real_shared(a,b): return 0.0   # veto: overlap is only template+names
        d = min(sum(self.wt(t) for t in a), sum(self.wt(t) for t in b))
        return sum(self.wt(t) for t in a&b)/d if d else 0.0
    def distinctive_shared(self,a,b,max_df=5):
        # sole caller is evaluate()'s name_anchored test; count only rare NON-NAME shared tokens.
        return sum(1 for t in a&b if self.df.get(t,1)<=max_df and t not in self._member_names) >= self._name_anchor_min
def datekey(s): return (s or "")[:10]
def load_overrides(OVERRIDES, con=None):
    """Override rows key either by STABLE `primary_app_key`/`related_app_key`
    columns (preferred since Q3-2026: integer application_ids are assigned at
    build time and DRIFT whenever a rebuild adds motions — west_valley's
    suppress set silently detached twice this way; app_key is content-derived
    and survives rebuilds) or by the legacy integer id columns. app_keys are
    resolved against the live application table; an unresolvable key is a STALE
    override and fails the build loudly rather than being silently ignored."""
    force, suppress, stale = {}, set(), []
    if os.path.exists(OVERRIDES):
        key2id = {}
        if con is not None:
            key2id = dict(con.execute(
                "SELECT app_key, application_id FROM application").fetchall())
        for r in csv.DictReader(open(OVERRIDES)):
            ka = (r.get("primary_app_key") or "").strip()
            kb = (r.get("related_app_key") or "").strip()
            if ka or kb:
                a, b = key2id.get(ka), key2id.get(kb)
                if a is None or b is None:
                    stale.append((ka if a is None else kb)); continue
            else:
                try: a=int(r["primary_application_id"]); b=int(r["related_application_id"])
                except (ValueError,KeyError):
                    try: a=int(r["council_application_id"]); b=int(r["pc_application_id"])   # legacy header
                    except (ValueError,KeyError): continue
            if (r.get("action") or "link").strip().lower()=="suppress": suppress.add((a,b))
            else: force[(a,b)]=(r.get("note") or "").strip()
    if stale:
        sys.exit(f"BUILD FAILED: {len(stale)} referral override app_key(s) do not "
                 f"resolve against the application table (stale/mis-typed): "
                 f"{stale[:4]} — fix referral_overrides.csv")
    return force, suppress

# body role classification (priority: lower number = more authoritative -> the "primary" side)
def role_of(name, kind):
    n = (name or "").lower()
    if kind == "council": return ("council", 0)
    if "planning" in n: return ("pc", 1)
    if kind == "agency": return ("agency", 2)
    return ("other", 3)

def main(here, case_no_re=None, case_no_method_label="case_no",
         case_no_report_label="case numbers", extra_stopwords=(),
         member_names=frozenset(), template_stopwords=frozenset(), content_veto=False,
         name_anchor_min=1):
    HERE = here
    _existing = sorted(glob.glob(os.path.join(HERE, "*.db")))
    DB = _existing[0] if _existing else os.path.join(HERE, "civic.db")
    TABLES = os.path.join(HERE, "tables")
    OVERRIDES = os.path.join(HERE, "referral_overrides.csv")
    AUDIT = os.path.join(HERE, "referrals_audit.csv")
    stop = STOP | set(extra_stopwords)
    methods = "'address','subject','address+subject','override'"
    if case_no_re is not None:
        methods = f"'{case_no_method_label}'," + methods
    if not os.path.exists(DB): print("civic.db not found — run build_db.py first", file=sys.stderr); return 1
    con = sqlite3.connect(DB); cur = con.cursor()
    bodies = cur.execute("SELECT body_id,name,kind FROM body").fetchall()
    role = {bid: role_of(nm, k) for bid,nm,k in bodies}                    # body_id -> (role, prio)
    bname = {bid: nm for bid,nm,k in bodies}
    if not any(r[0]=="council" for r in role.values()):
        print("no council body found", file=sys.stderr); return 1

    cur.executescript(f"""
    DROP VIEW IF EXISTS v_referral_chain; DROP TABLE IF EXISTS referral;
    CREATE TABLE referral(
      referral_id INTEGER PRIMARY KEY,
      primary_application_id INTEGER NOT NULL REFERENCES application(application_id),
      primary_body TEXT NOT NULL,
      related_application_id INTEGER NOT NULL REFERENCES application(application_id),
      related_body TEXT NOT NULL,
      match_method TEXT NOT NULL CHECK(match_method IN ({methods})),
      confidence TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
      shared_address TEXT, subject_score REAL,
      primary_date TEXT, related_date TEXT, gap_days INTEGER, note TEXT,
      UNIQUE(primary_application_id, related_application_id));
    CREATE INDEX ix_ref_primary ON referral(primary_application_id);
    CREATE INDEX ix_ref_related ON referral(related_application_id);
    """)
    rows = cur.execute("""SELECT mo.application_id, mo.body_id, MIN(m.meeting_date), MAX(m.meeting_date)
      FROM motion mo JOIN meeting m ON m.meeting_id=mo.meeting_id WHERE mo.application_id IS NOT NULL
      GROUP BY mo.application_id, mo.body_id""").fetchall()
    app_span = {a:(datekey(d0),datekey(d1)) for a,_,d0,d1 in rows}
    apptext = {a:(rt or nm or "") for a,nm,rt in cur.execute("SELECT application_id,name,rep_title FROM application")}
    # build per-body-role feature lists; every application (all land-use, by construction) participates
    feats = {}
    for aid, bod, _, _ in rows:
        txt = apptext.get(aid,"")
        feats[aid] = dict(app_id=aid, body_id=bod, role=role[bod][0], prio=role[bod][1], bname=bname[bod],
                          addr=addresses(txt), code=code_sections(txt), toks=subject_tokens(txt, stop),
                          pls=pl_numbers(txt, case_no_re), first=app_span[aid][0], last=app_span[aid][1])
    allf = list(feats.values())
    primaries = [f for f in allf if f["prio"] < 3 or f["role"]=="council"]   # council/pc/agency anchor
    pc_addr = {a for f in allf if f["role"]!="council" for a in f["addr"]}
    co_addr = {a for f in allf if f["role"]=="council" for a in f["addr"]}
    print("== cross-body signal check ==")
    for rl in ("council","pc","agency","other"):
        g=[f for f in allf if f["role"]==rl]
        if g: print(f"  {rl:8} apps: {len(g):4} ({sum(1 for f in g if f['addr'])} w/ address)  bodies={sorted(set(f['bname'] for f in g))}")
    print(f"  addresses shared council<->non-council: {len(pc_addr & co_addr)}")
    if case_no_re is not None:
        pc_pl = {a for f in allf if f["role"]!="council" for a in f["pls"]}
        co_pl = {a for f in allf if f["role"]=="council" for a in f["pls"]}
        print(f"  {case_no_report_label}: non-council apps citing one = {sum(1 for f in allf if f['role']!='council' and f['pls'])}, "
              f"council apps citing one = {sum(1 for f in allf if f['role']=='council' and f['pls'])}, "
              f"shared council<->non-council = {len(pc_pl & co_pl)}")

    force, suppress = load_overrides(OVERRIDES, con)
    idf = IDF([f["toks"] for f in allf], member_names=member_names,
              template_stopwords=template_stopwords, content_veto=content_veto,
              name_anchor_min=name_anchor_min)
    # index candidates by case/PL number, address and code for cheap generation
    by_addr, by_code, by_pl = {}, {}, {}
    for f in allf:
        for a in f["addr"]: by_addr.setdefault(a,[]).append(f)
        for c in f["code"]: by_code.setdefault(c,[]).append(f)
        for p in f["pls"]: by_pl.setdefault(p,[]).append(f)

    def temporal_ok(primary, related):
        # gap measured from related -> primary (related expected to precede the primary decision)
        try:
            ry,rm,rd = map(int, related["first"][:10].split("-")); pyy,pm,pdd = map(int, primary["last"][:10].split("-"))
            gap = (date(pyy,pm,pdd) - date(ry,rm,rd)).days
        except Exception: return None, None
        directional = (primary["role"]=="council" and related["role"]=="pc")
        if directional:
            return (-FORWARD_SLACK_DAYS <= gap <= TEMPORAL_WINDOW_DAYS), gap   # PC must precede Council
        return (abs(gap) <= TEMPORAL_WINDOW_DAYS), gap                          # symmetric for agency/other

    def evaluate(primary, related):
        a, b = primary["app_id"], related["app_id"]
        if (a, b) in suppress: return None
        ok, gap = temporal_ok(primary, related)
        shared = primary["addr"] & related["addr"]
        shared_pl = primary["pls"] & related["pls"]
        sj = idf.score(primary["toks"], related["toks"]); cn = idf.contain(primary["toks"], related["toks"])
        name_anchored = cn>=CONTAIN_MEDIUM and idf.distinctive_shared(primary["toks"], related["toks"])
        shared_code = primary["code"] & related["code"]; method=conf=None
        if shared_pl and ok:                    # strongest key: same Utah planning FILE/CASE NUMBER
            method,conf = case_no_method_label,"high"
        elif shared and ok:
            if sj>=0.20: method,conf = "address+subject","high"
            else: method,conf = "address","low"
        elif (sj>=SUBJ_MEDIUM or name_anchored or (shared_code and sj>=0.15)) and ok:
            method,conf = "subject","medium"
        elif shared_pl and ok is None: method,conf = case_no_method_label,"low"
        elif shared and ok is None: method,conf = "address","low"
        elif sj>=0.6: method,conf = "subject","low"
        if not method: return None
        if name_anchored: sj = max(sj, round(cn,3))
        return dict(primary_application_id=a, primary_body=primary["bname"], related_application_id=b,
                    related_body=related["bname"], match_method=method, confidence=conf,
                    shared_address="; ".join(sorted(shared_pl)) or "; ".join(sorted(shared)),
                    subject_score=round(sj,3),
                    primary_date=primary["last"], related_date=related["first"], gap_days=gap, note="")
    rank = {"high":3,"medium":2,"low":1}; links = {}
    # for each primary anchor, find related candidates in a DIFFERENT, lower-priority (or equal-but-noncouncil) body
    for p in primaries:
        cands, seen = [], set()
        def probe(q):
            if q["app_id"] in seen or q["app_id"]==p["app_id"]: return
            # only link to a strictly lower-authority body (prio greater), so each pair is emitted once,
            # primary = the more authoritative side; skip same body and equal-prio agency<->agency noise
            if q["prio"] <= p["prio"]: return
            seen.add(q["app_id"]); lk = evaluate(p, q)
            if lk: cands.append(lk)
        for pn in p["pls"]:
            for q in by_pl.get(pn,[]): probe(q)
        for a in p["addr"]:
            for q in by_addr.get(a,[]): probe(q)
        for c in p["code"]:
            for q in by_code.get(c,[]): probe(q)
        for q in allf:
            if q["app_id"] in seen or not q["toks"]: continue
            if p["toks"] & q["toks"]: probe(q)
        if not cands: continue
        # resolve best per related body group to cap fan-out
        from collections import defaultdict
        bygrp = defaultdict(list)
        for lk in cands: bygrp[lk["related_body"]].append(lk)
        for grp in bygrp.values():
            grp.sort(key=lambda x:(rank[x["confidence"]],x["subject_score"]), reverse=True)
            best = grp[0]; bs = best["subject_score"]
            for lk in grp:
                if (lk is best) or lk["confidence"]=="high" or (lk["subject_score"]>=SUBJ_SECONDARY and lk["subject_score"]>=bs*SECONDARY_MARGIN):
                    links[(lk["primary_application_id"],lk["related_application_id"])] = lk
    for (a,b),note in force.items():
        pa, pb = feats.get(a), feats.get(b)
        if not pa or not pb: continue
        # order so primary is the more authoritative
        if pa["prio"] > pb["prio"]: a,b,pa,pb = b,a,pb,pa
        links[(a,b)] = dict(primary_application_id=a, primary_body=pa["bname"], related_application_id=b,
            related_body=pb["bname"], match_method="override", confidence="high", shared_address="",
            subject_score=None, primary_date=pa["last"], related_date=pb["first"], gap_days=None, note=note or "manual override")
    for i,lk in enumerate(sorted(links.values(), key=lambda x:(x["primary_application_id"],x["related_application_id"])),1):
        cur.execute("""INSERT INTO referral(referral_id,primary_application_id,primary_body,related_application_id,
            related_body,match_method,confidence,shared_address,subject_score,primary_date,related_date,gap_days,note)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (i,lk["primary_application_id"],lk["primary_body"],lk["related_application_id"],lk["related_body"],
             lk["match_method"],lk["confidence"],lk["shared_address"] or None,lk["subject_score"],
             lk["primary_date"] or None,lk["related_date"] or None,lk["gap_days"],lk["note"] or None))
    cur.executescript("""
    CREATE VIEW v_referral_chain AS
    SELECT r.referral_id, r.confidence, r.match_method, r.primary_body, r.related_body, r.gap_days,
           rel.app_key related_key, rel.name related_project, r.related_date,
           pri.app_key primary_key, pri.name primary_project, r.primary_date, r.shared_address, r.subject_score
    FROM referral r JOIN application rel ON rel.application_id=r.related_application_id
      JOIN application pri ON pri.application_id=r.primary_application_id
    ORDER BY r.confidence DESC, r.primary_date;""")
    con.commit()
    arows = cur.execute("""SELECT r.referral_id,r.confidence,r.match_method,r.primary_body,r.related_body,r.gap_days,
        r.related_application_id,r.related_date,rel.rep_title,r.primary_application_id,r.primary_date,pri.rep_title,
        r.shared_address,r.subject_score,r.note
        FROM referral r JOIN application rel ON rel.application_id=r.related_application_id
        JOIN application pri ON pri.application_id=r.primary_application_id
        ORDER BY r.confidence DESC, r.subject_score""").fetchall()
    with open(AUDIT,"w",newline="") as f:
        csv.writer(f).writerows([["referral_id","confidence","match_method","primary_body","related_body","gap_days",
            "related_application_id","related_date","related_title","primary_application_id","primary_date",
            "primary_title","shared_address","subject_score","note"]]+list(arows))
    os.makedirs(TABLES, exist_ok=True)
    rr = cur.execute("SELECT * FROM referral").fetchall(); hdr=[d[0] for d in cur.description]
    with open(os.path.join(TABLES,"referral.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(hdr); w.writerows(rr)
    if not os.path.exists(OVERRIDES):
        with open(OVERRIDES,"w",newline="") as f:
            csv.writer(f).writerow(["primary_application_id","related_application_id","action","note"])
    def n(q): return cur.execute(q).fetchone()[0]
    tot = n("SELECT COUNT(*) FROM referral")
    print("== cross-body referral linkage ==")
    print(f"  links: {tot}  by confidence:", dict(cur.execute("SELECT confidence,COUNT(*) FROM referral GROUP BY 1")))
    print("  by body-pair:", dict(cur.execute("SELECT primary_body||' <- '||related_body,COUNT(*) FROM referral GROUP BY 1 ORDER BY 2 DESC")))
    print("  by method:", dict(cur.execute("SELECT match_method,COUNT(*) FROM referral GROUP BY 1")))
    co = len([f for f in allf if f['role']=='council'])
    linked = n("SELECT COUNT(DISTINCT primary_application_id) FROM referral WHERE primary_body IN (SELECT name FROM body WHERE kind='council')")
    print(f"  council apps linked to >=1 other body: {linked} of {co} ({100*linked//max(1,co)}%) — rest correctly UNLINKED")
    print("  INTEGRITY:", "FK!" if cur.execute("PRAGMA foreign_key_check").fetchall() else "OK")
    con.close(); return 0
