#!/usr/bin/env python3
# NOTE (REFACTOR_PLAN 4.3, 2026-07-07): this city's build_db.py is a DOCUMENTED FORK.
# The 10 template cities share scripts/db_build_lib.py; this city diverges for real
# reasons (see its docstring/db/SCHEMA.md). When fixing a core-build bug, fix the lib
# FIRST, then port the fix here by diffing against the lib.
"""
build_db.py — normalized relational database for Sandy City (STANDARD SCHEMA + Legistar
extension layer). Rewritten for REMEDIATION_PLAN.md 2.6 (2026-07-02): the previous build
was a Legistar schema fork (staging CSVs only); this build produces the SAME standard
core as every other city (body/person/meeting/application/motion/vote/role, west_valley
template semantics) while PRESERVING the full Legistar structured harvest in clearly
named `legistar_*` extension tables. Cross-city db queries now behave on sandy.db.

SOURCES (two layers, never conflated):
  STANDARD CORE  <- meeting_minutes/all_votes.csv       (council + RDA; minutes-derived,
                                                          PUA-repaired, verified vs raw PDFs)
                 <- planning_commission/all_votes.csv    (Legistar EventItemVote body 140 —
                                                          the only PC source; no PC minutes)
  EXTENSION      <- db/staging/*.csv                     (the full Legistar API harvest:
                                                          10 bodies, 2,825 matters, all
                                                          event items and raw vote rows,
                                                          incl. Board of Adjustment and the
                                                          `Nonvoting` rows the flat CSVs
                                                          exclude)

COUNCIL-VOTE SOURCING DECISION (2026-07-02, see db/SCHEMA.md for the full numbers):
  minutes-primary. The repaired minutes CSV records MORE meetings (240 vote dates vs
  Legistar's 214; 33 minutes-only dates vs 7 Legistar-only, 3 of which are meetings whose
  minutes aren't published yet) and MORE dissent (292 Nays vs 173 — Legistar omits
  narrative voice votes and even whole contested roll calls, e.g. the failed 2021-08-17
  tabling motion and the 6-0-1 Resolution 21-31C adoption). Legistar remains the exact
  enrichment layer: matter linkage, agenda numbers, action names, and every raw vote row
  are preserved in legistar_* tables and cross-linked to the standard core.

MOTION <-> LEGISTAR LINKAGE:
  * PC: deterministic — planning_commission/all_votes.csv was generated from staging by
    build_from_legistar.py; this build replays the same enumeration, so every PC motion
    maps 1:1 to its EventItem (title-verified). app_match_method='matter_id' (exact).
  * Council: roll-call signature matching — Legistar EventItems sharing one VoteId set are
    ONE physical roll call (Legistar duplicates the consent-calendar roll onto every
    consent item); a motion matches a roll-call group when the (Aye-set, Nay-set) member
    signatures agree on the same date (name alias: Kris Nicholl = Kristin Coleman-Nicholl),
    disambiguated by title-token overlap then minutes order. A matched group with exactly
    one MatterId yields app_match_method='matter_id'; land-use motions without a unique
    matter fall back to the standard prose tiers (name/singleton), like every prose city.

DUPLICATE VOTE ROWS: the flat CSVs carry 11 duplicate (source,motion_no,date,member)
pairs (8 identical, 3 conflicting — Legistar duplicated-roster-slot artifacts and one
clerk double-listing in the 2021-08-17 minutes). Every pair MUST have a row in
db/vote_overrides.csv (fail-loud otherwise); conflicts resolve per that file, never
arbitrarily. Reconciliation is printed on every build:
  CSV named rows = db vote rows + merged override pairs.

Idempotent. Run:  python3 db/build_db.py   (then python3 db/build_referrals.py)
"""
import csv, glob, os, re, sqlite3, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# Shared v_contested column-shape parity (2026-07-19): this fork imports ONLY the
# three parity pieces from the shared lib — the motion_std table DDL, its loader,
# and the reshaped v_contested view — everything else remains this city's fork.
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "scripts"))
from db_build_lib import (MOTION_STD_DDL, load_motion_std,
                          V_CONTESTED_DDL_NO_PROVENANCE as V_CONTESTED_DDL)
# (this fork's motion table has no `provenance` column — its flat CSVs are a
#  single-channel corpus — so the view emits an honest NULL provenance)

_existing = sorted(glob.glob(os.path.join(HERE, "*.db")))
DB = _existing[0] if _existing else os.path.join(HERE, "sandy.db")
TABLES = os.path.join(HERE, "tables")
OVERRIDES = os.path.join(HERE, "overrides.csv")              # app_key overrides (standard tier)
VOTE_OVERRIDES = os.path.join(HERE, "vote_overrides.csv")    # duplicate-row resolutions
DISP_OVERRIDES = os.path.join(HERE, "disposition_overrides.csv")  # disposition corrections
S = os.path.join(HERE, "staging")
SOURCES = [os.path.join(REPO, "meeting_minutes", "all_votes.csv"),
           os.path.join(REPO, "planning_commission", "all_votes.csv")]
LEGISTAR_CLIENT = "sandyutah"   # webapi.legistar.com client (recon.md)
PC_BODY_ID = 140                # Legistar BodyIds
COUNCIL_BODY_ID = 138

# --------------------------------------------------------- body kind (west_valley template)
def kind_of(name):
    n = (name or "").lower()
    if "planning" in n or ("commission" in n and "redevelop" not in n): return "commission"
    if "adjust" in n or "appeal" in n or n.strip() in ("boa",): return "commission"
    if any(k in n for k in ("redevelop", "reinvest", "rda", "cra", "agency")): return "agency"
    if any(k in n for k in ("building authority", "mba", "lba", "housing", "ha")): return "agency"
    if "board" in n: return "committee"
    return "council"

# --------------------------------------------------------- person helpers (template)
ROLE_PREFIX = re.compile(r"^(council\s*member|councilmember|councilor|commissioner|board\s*member|"
                         r"vice\s*chair|acting\s*chair|chair(?:person)?|mayor(?:\s+pro\s+tempore)?|"
                         r"mr\.?|ms\.?|mrs\.?|dr\.?)\s+", re.I)
def norm_person(name):
    if not name: return None
    n = name.strip()
    while True:
        m = ROLE_PREFIX.sub("", n)
        if m == n: break
        n = m
    n = re.sub(r"\s+", " ", n).strip(" .,")
    return n or None
def person_key(name):
    return re.sub(r"[^a-z]", "", name.lower()) if name else None
# Legistar-name -> minutes-name alias (same official, two recorded spellings)
LEG_ALIAS = {"krisnicholl": "kristincolemannicholl"}
def leg_key(name):
    k = person_key(norm_person(name) or "")
    return LEG_ALIAS.get(k, k)

# --------------------------------------------------------- land-use / project resolution (template
# + sandy native labels: council 'Land-Use/Zoning', PC 'Planning Item')
LU_TYPES = {"land-use/zoning", "planning item"}
LANDUSE_RE = re.compile(   # west_valley template set UNION the old sandy referral set
    r"\b(rezone|zone change|zoning|subdivisions?|plats?|annex(?:ation|ing)?|general plan|land use|"
    r"conditional use|site plan|development agreement|vacat(?:e|ing|ion)|planned (?:unit|community)|"
    r"pud|condominium|project area|reinvestment|master plan|development code amendment|"
    r"code amendments?|amending (?:title|chapter|section)|text amendment|land development code|"
    r"ordinance amending|right.?of.?way|"
    r"historic district|landmark site|(?:small|station) area plan|table \d)\b", re.I)   # T1.4: legislative Others (master plan already present)
CODE_AMEND_RE = re.compile(
    r"\b(development code amendment|code amendment|amending (?:title|chapter|section)|"
    r"amendment to (?:chapter|section|table)|table \d{2}\.\d)\b", re.I)
def is_landuse(motion_type, title):
    return (motion_type or "").strip().lower() in LU_TYPES or bool(LANDUSE_RE.search(title or ""))
AGENCY_PROCEDURAL = re.compile(
    r"regular meeting date|meeting date,? time|fiscal year|revised budget|adjusted budget|annual budget|"
    r"board of canvass|certifying the official canvass|consent agenda|approve the minutes|"
    r"^.{0,40}\bminutes\b.{0,30}$", re.I)
def application_worthy(body, motion_type, title):
    if is_landuse(motion_type, title): return True
    if kind_of(body) == "agency":
        if (motion_type or "").strip().lower() == "appointment": return False
        if AGENCY_PROCEDURAL.search(title or ""): return False
        return True
    return False

NAME_TYPE = (r"(Annexation|Zone Change|Rezone|General Plan (?:Land Use )?Amendment|Plat Amendment|"
             r"Community Reinvestment Project Area(?: Plan)?(?: Amendment)?|Project Area Plan|"
             r"Area Plan(?: Amendment)?|Site Plan|Master Plan|Subdivision)")
_ACTIONWORD = {"consideration","final","preliminary","subdivision","plat","amendment","approval",
               "concept","revisions","revision","ordinance","resolution","development","code","the",
               "a","an","and","of","for","intent","annex","public","facility","general","land","use"}
def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("’", "'")).strip(" .,'\"-–—")
def _good(name):
    if not name or len(name) < 3: return None
    core = [t for t in name.split() if t.lower() not in _ACTIONWORD]
    if not any(len(t) >= 3 and t[:1].isupper() for t in core): return None
    return name
_NAME_PATS = [
    rf"\bthe\s+([A-Z][A-Za-z0-9'.&\-]*(?:\s+[A-Z0-9][A-Za-z0-9'.&\-]*){{0,5}})\s+{NAME_TYPE}\b",
    rf"\b([A-Z][A-Za-z0-9'.&\-]*(?:\s+[A-Z0-9][A-Za-z0-9'.&\-]*){{0,5}})\s+{NAME_TYPE}\b",
    r"\bapprov(?:al|e|ing)\s+(?:for|of)\s+(?:the\s+|an?\s+(?:amended version of\s+)?)?"
    r"([A-Z][A-Za-z0-9'.&\- ]+?)(?=,|\s+an?\s+\d|\s+located|\s+including|\s+on\s+\d|\s+phases?\b|\s+lots?\b|\.|$)",
    r"\bannex\s+the\s+([A-Z][A-Za-z0-9'.&\- ]+?)(?=,|\s+approximately|\s+of\s+[\d.]|\s+located|\.|$)",
    r"\bdevelopment agreement\s+(?:for|with|between)\s+(?:the\s+)?"
    r"([A-Z][A-Za-z0-9'.&\- ]+?)(?=,|\s+and\s+|\s+located|\s+related|\.|$)",
]
def project_name(title):
    t = (title or "").replace("’", "'")
    for i, p in enumerate(_NAME_PATS):
        m = re.search(p, t)
        if m:
            name = _clean(m.group(1) + " " + m.group(2)) if i < 2 else _clean(m.group(1))
            g = _good(name)
            if g: return g
    return None
def name_key(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip() if name else None

# --------------------------------------------------------- outcome / stage / recommendation
# --------------------------------------------------------- outcome (did the motion CARRY)
# v3 (T1.3 cross-city audit, 2026-07-12 — 31-city ground-truth). `outcome` = did the MOTION
# carry, distinct from the proposed action's disposition. Signal priority, evidence-weighted:
#   1. Deferral/death words (Continued / Died — incl. "not seconded", "lack of a second").
#   2. STRICT carriage words — fail/failed/"did not pass" vs pass/passed/carried. These are
#      statements about the MOTION and, in every minutes-derived conflict the audit found
#      (15+ rows: majority-first "failed 4-3" tallies, page-break-truncated rolls, OCR digit
#      noise), the word was right and the tally corrupt. Item-fate words (Approved/Denied)
#      are NOT carriage — they describe the matter, not the motion.
#   3. The yes:no / yes-no tally (clock-times stripped first — "recessed at 7:12pm" read as
#      a 7:12 tally flipped 8 holladay outcomes). A decisive tally rules when no carriage
#      word is present (fixes failed recs like "Positive recommendation 4:5" and passed
#      denials like "5:0 Denied"); a TIE fails (12 audited tie rows stored Pass were wrong).
#   4. Tally-less item-fate 'den': composed with the motion's own disposition — a deny
#      motion whose result says "Denied unanimous" CARRIED (park_city/taylorsville pattern).
_TALLY_RE = re.compile(r'(\d+)\s*[:\-]\s*(\d+)')
_CLOCK_RE = re.compile(r'\b\d{1,2}:\d{2}\s*[ap]\.?\s*m\b|\bat\s+\d{1,2}:\d{2}\b', re.I)
_FAILWORD_RE = re.compile(r'\bfail|did not pass|\bnot carried\b', re.I)
_PASSWORD_RE = re.compile(r'\bpass|\bcarrie[ds]\b', re.I)
def outcome_of(res, disp=None, pc=False):
    r = (res or "").lower()
    if "continu" in r or "tabl" in r or "postpon" in r: return "Continued"
    if ("died" in r or "no second" in r or "not seconded" in r
            or "lack of a second" in r): return "Died"
    word = ("Fail" if _FAILWORD_RE.search(r)
            else ("Pass" if _PASSWORD_RE.search(r) else None))
    m = _TALLY_RE.search(_CLOCK_RE.sub(" ", res or ""))
    if m:
        yes, no = int(m.group(1)), int(m.group(2))
        if yes != no:
            t = "Pass" if yes > no else "Fail"
            if word and word != t:
                # sandy PC result strings are Legistar-synthesized: their Fail/Pass words
                # are PassedFlag ARTIFACTS (clerk noise) and the tally rules; council
                # words are minutes-derived and beat a suspect (truncated/majority-
                # first) tally. T1.3 audit evidence: PC ~20/20 tally right, council 4/4 word right.
                return t if pc else word
            return t
        return word or "Fail"                            # tie: word if any, else a tie fails
    if word: return word
    if "den" in r:
        return "Pass" if disp == "deny" else "Fail"      # tally-less "Denied": deny motion carried
    return "Pass"
def is_pc(name): return "planning" in (name or "").lower()
def stage_and_rec(body, res, title, action_name):
    """Sandy PC direction comes from the Legistar EventItemActionName of the mapped item
    ('recommended for approval/denial' vs 'approved'/'adopted'/'tabled'); fall back to the
    template's phrasing test if unmapped."""
    if is_pc(body):
        a = (action_name or "").lower()
        if "recommend" in a:
            return "pc_recommendation", ("Negative" if "denial" in a or "deny" in a else "Positive")
        if a:
            return "pc_final_action", None
        s = ((res or "") + " " + (title or "")).lower()
        if "recommend" in s or "forward" in s:
            return "pc_recommendation", ("Negative" if "denial" in s or "deny" in s else "Positive")
        return "pc_final_action", None
    n = (body or "").lower()
    if "adjust" in n or "appeal" in n or n.strip() == "boa": return "boa_action", None
    if kind_of(body) == "agency":
        if "housing" in n or n.strip() == "ha": return "ha_vote", None
        if any(x in n for x in ("building authority", "mba", "lba")): return "mba_vote", None
        return "rda_vote", None
    if kind_of(body) == "council": return "council_vote", None
    return "other_action", None

# --------------------------------------------------------- disposition (PROPOSED action)
# `disposition` records what a motion PROPOSES for the matter — approve / deny / continue /
# table / procedural — a DISTINCT axis from `outcome` (did the motion carry). It is NOT
# pre-composed with the outcome (that was the whole root-cause lesson: keep the two facts
# separable). Compose at query time: disposition='approve' AND outcome='Pass' => matter
# approved; 'approve' AND 'Fail' => not approved; 'deny' AND 'Pass' => denied. For PC
# recommendation motions this is cross-checked against the independently-derived
# `recommendation` field via _compose_dir() below (a free validation oracle). Read from
# `motion_text` (the verbatim proposed action); corrections go in db/disposition_overrides.csv.
# Ported from the SLC reference build 2026-07-12 (NEXT_SESSION_PLAN T1.1).
# v2 (T1.3 cross-city audit, 2026-07-12): verb-anchored continue/table are checked BEFORE
# the procedural token scan (a "moved to table X" that mentions minutes/appointments must
# not be swallowed by the PROC list); the continue vocabulary covers the dominant native
# frames the SLC-tuned v1 missed in 14 cities ("continue <Item|File|application|Ordinance>
# [#]N [to <date>]", mid-sentence "moved to continue", "continuation of", "delay a
# decision"); and six audited false-positive traps are guarded ("Table of Uses"/"Table
# <digit>" code citations, "defer to the <code/authority>", "deferral agreement", keep-doing
# "continue to <verb>" forms, "not approve/recommend" negations, item-fate "denial" nouns
# behind a continue verb).
_DISP_PROC = ("consent agenda", "consent calendar", "minutes", "closed session",
              "closed meeting", "executive session", "adjourn", "recess", "reconvene",
              "ceremonial", "proclamation", "leave of absence", "reopen",
              "reconsider", "regular agenda", "end of the agenda",
              "public comment", "close the meeting", "close the staff meeting",
              "close the open session", "close the work session", "open the business",
              "reorder the agenda", "amend the agenda", "approve the agenda",
              "adopt the agenda", "the agenda be approved", "cancel the")
_DISP_DENY = ("deny", "denial", "denied", "reject", "negative recommendation",
              "unfavorable", "uphold the denial", "not recommend", "not approve",
              "recommend against")
_DISP_APPR = ("approve", "approval", "approving", "adopt", "adopting", "grant",
              "granting", "positive recommendation", "favorable recommendation",
              "authorize", "authorizing", "vote to approve", "accept", "ratify",
              "to pass ")
# continuance: a continue/postpone/defer VERB aimed at an item — not "continue to <verb>"
# (keep-doing: COVID "continue to hold meetings"), not "continue the emergency declaration/
# board assignments" (keep-in-force), not "defer to <authority>"/"deferral agreement".
_CONT_POS_RE = re.compile(
    r"\b(?:mov\w+|motion\w*)\s+(?:was\s+)?to\s+continue\b"
    r"|\bto\s+continue\s+(?:the|this|these|items?|files?|applications?|ordinances?"
    r"|resolutions?|project|cases?|hearing|consideration|action|agenda|discussion|#|no\."
    r"|\S*\d)"     # case-number objects: "continue PC 20-022", "continue GPZ-3-2020", "continue Z-3-2025"
    r"|\bcontinue\s+(?:items?|files?|applications?|ordinances?|resolutions?|project|cases?)\b"
    r"|\bcontinue\s+to\s+(?:the\s+)?(?:next|a\s+future|[a-z]+\s+\d{1,2})"
    r"|\bcontinuation\s+(?:of|for)\b|\bdelay\s+a\s+decision\b"
    r"|\bto\s+postpone\b|\bpostpone\s+(?:the|this|item|action|until)"
    r"|\bdefer\s+(?:action|consideration|the\s+(?:item|matter|decision|vote))\b", re.I)
_CONT_NEG_RE = re.compile(
    r"\bnot\s+(?:to\s+)?continue\b|\bcontinue\s+to\s+(?:hold|use|allow|meet|work|serve"
    r"|support|be|have|act|operate|fund|run|employ|keep|provide|pay|waive|contract)\b"
    r"|\bcontinue\s+(?:the\s+)?(?:emergency\s+declaration|board\s+assignments)"
    r"|\bdeferral\s+agreement|\bdefer(?:ence)?\s+to\b", re.I)
# table: verb-anchored only; never the noun in code citations ("Table 05-030-B",
# "Table of Uses/Setbacks/Bulk/Allowed Uses", "Land Use Table", "Materials Table").
_TABLE_RE = re.compile(
    r"\b(?:mov\w+|motion\w*)\s+(?:was\s+)?to\s+table\b(?!\s+(?:of\b|\d))"
    r"|\bto\s+table\s+(?:the|this|item|agenda|consideration|action|resolution|ordinance)\b"
    r"|\bwe\s+table\b(?!\s+(?:of\b|\d))"
    r"|\blay\s+on\s+the\s+table\b", re.I)
def disposition_of(text):
    t = (text or "").strip().lower()
    if not t or "not captured" in t: return (None, "uncaptured", "low")
    if _CONT_POS_RE.search(t) and not _CONT_NEG_RE.search(t):
        return ("continue", "keyword", "high")
    if _TABLE_RE.search(t) or (t.startswith("table ") and not re.match(r"table\s+(?:of\b|\d)", t)):
        return ("table", "keyword", "high")
    if any(k in t for k in _DISP_PROC): return ("procedural", "keyword", "high")
    if t.startswith("continue") and not _CONT_NEG_RE.search(t):
        return ("continue", "keyword", "high")
    dhit = min(((t.find(k), k) for k in _DISP_DENY if k in t), default=(-1, ""))
    ahit = min(((t.find(k), k) for k in _DISP_APPR if k in t), default=(-1, ""))
    dpos, dkey = dhit; apos, _ = ahit
    if dpos == -1 and apos == -1:
        # no decision verb: hearing mechanics / set-a-date are procedural, else unknown
        if "public hearing" in t or "set the date" in t: return ("procedural", "keyword", "medium")
        return (None, "unclassified", "low")
    if dpos != -1 and apos != -1:
        if dpos <= apos < dpos + len(dkey):  # approve token INSIDE a negated deny phrase
            return ("deny", "keyword", "high")   # ("not approve", "not recommend ... approval")
        if apos < dpos and ahit[1] in ("ratify", "accept"):
            # meta-verbs adopt their object's direction: "RATIFY the letter DENYING X" /
            # "accept the recommendation of denial" propose a DENIAL (park_city m2098)
            return ("deny", "keyword", "high")
        return (("deny" if dpos < apos else "approve"), "mixed", "low")
    return (("deny", "keyword", "high") if dpos != -1 else ("approve", "keyword", "high"))
def _compose_dir(disp, outcome):
    # effective recommendation/action direction = proposed action composed with carriage
    if disp == "approve": return "Positive" if outcome == "Pass" else "Negative"
    if disp == "deny":    return "Negative" if outcome == "Pass" else "Positive"
    return None

# --------------------------------------------------------- read the flat CSVs
def read_motions():
    """Motions keyed (source, motion_no, date) — date included because sandy PC's `source`
    is one constant provenance string (SCHEMA_SPEC §2 documented degeneracy)."""
    motions, votes, present = {}, [], []
    for path in SOURCES:
        if not os.path.exists(path):
            print(f"  (skipping absent source: {os.path.relpath(path, REPO)})"); continue
        present.append(path)
        for r in csv.DictReader(open(path)):
            key = (r["source"], int(r["motion_no"]), r["date"])
            if key not in motions:
                motions[key] = dict(date=r["date"], body=r["body"], title=r["title"],
                                    motion_no=int(r["motion_no"]), motion=r["motion"],
                                    motion_type=r.get("motion_type", ""), result=r.get("result", ""),
                                    mover=norm_person(r.get("mover")), seconder=norm_person(r.get("seconder")),
                                    source=r["source"])
            if r.get("member") and r.get("vote"):
                votes.append((key, r["member"], r["vote"]))
    return motions, votes, present

def load_vote_overrides():
    """db/vote_overrides.csv: source_file,motion_no,member,date,claimed_values,resolution,reasoning
    (park_city schema). EVERY duplicate (source,motion_no,date,member) pair in the CSVs must
    have a row here; conflicting pairs resolve to `resolution`."""
    out = {}
    if os.path.exists(VOTE_OVERRIDES):
        for r in csv.DictReader(open(VOTE_OVERRIDES)):
            out[(r["source_file"], int(r["motion_no"]), r["date"], r["member"])] = r["resolution"].strip()
    return out

# --------------------------------------------------------- staging (Legistar) readers
def rd_staging(name):
    p = os.path.join(S, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []

def pc_item_mapping(events, items, votes_by_item):
    """Replay planning_commission/build_from_legistar.py's enumeration EXACTLY so each PC
    CSV motion (date, motion_no) maps to its EventItem."""
    pcev = {e["EventId"]: e for e in events if e.get("EventBodyId") == str(PC_BODY_ID)}
    def seq(it):   # replicated verbatim (first key wins; exceptions -> 0)
        for k in ("EventItemMinutesSequence", "EventItemAgendaSequence"):
            try: return int(it.get(k) or 0)
            except Exception: return 0
        return 0
    bymtg = defaultdict(list)
    for it in items:
        if it.get("EventItemEventId") in pcev: bymtg[it["EventItemEventId"]].append(it)
    mapping = {}
    for eid, its in bymtg.items():
        date = (pcev[eid].get("EventDate") or "")[:10]
        mno = 0
        for it in sorted(its, key=seq):
            if not votes_by_item.get(it["EventItemId"]): continue
            mno += 1
            mapping[(date, mno)] = it
    return mapping

_TOK = re.compile(r"[a-z]{4,}")
_TOK_STOP = {"motion", "made", "seconded", "approve", "approval", "adopt", "adopting",
             "council", "city", "sandy", "resolution", "ordinance", "following", "vote"}
def _toks(t):
    return {w for w in _TOK.findall((t or "").lower())} - _TOK_STOP

def council_groups(events, items, votes_by_item):
    """Legistar council EventItems sharing an identical VoteId set are one physical roll
    call (consent-calendar duplication). Returns per-date ordered groups with signatures."""
    ev = {e["EventId"]: e for e in events}
    groups = {}
    for it in items:
        if it.get("EventBodyId") != str(COUNCIL_BODY_ID): continue
        vs = votes_by_item.get(it["EventItemId"])
        if not vs: continue
        fs = frozenset(v["VoteId"] for v in vs)
        g = groups.setdefault(fs, dict(items=[], votes=vs,
                                       date=(ev[it["EventItemEventId"]].get("EventDate") or "")[:10]))
        g["items"].append(it)
    by_date = defaultdict(list)
    for g in groups.values():
        seqs = []
        for it in g["items"]:
            v = it.get("EventItemMinutesSequence") or it.get("EventItemAgendaSequence") or ""
            if str(v).isdigit(): seqs.append(int(v))
        g["seq"] = min(seqs) if seqs else 0
        g["sig"] = (frozenset(leg_key(v["VotePersonName"]) for v in g["votes"] if v["VoteValueName"] == "Yes"),
                    frozenset(leg_key(v["VotePersonName"]) for v in g["votes"] if v["VoteValueName"] == "No"))
        g["toks"] = set()
        for it in g["items"]: g["toks"] |= _toks(it.get("EventItemTitle"))
        by_date[g["date"]].append(g)
    for d in by_date: by_date[d].sort(key=lambda g: g["seq"])
    return by_date

TALLY_RE = re.compile(r"\b(\d+)\s*[-:–]\s*(\d+)\b")

def match_council_motions(motions, votes_by_motion, by_date):
    """Match minutes motions to Legistar roll-call groups, three tiers (values always come
    from the CSV; matching only drives matter/enrichment linkage):
      1. full signature — identical (Aye-set, Nay-set) member signatures on the same date;
      2. dissenter signature — narrative votes name only dissenters: identical Nay-set +
         matching Aye/Nay tally (from the result string);
      3. tally + title — tally-only motions: matching printed tally AND a positive
         title-token overlap that uniquely selects one group.
    Ties within a tier break by title-token overlap, then minutes order. No candidate ->
    no link (Legistar simply doesn't carry many minutes motions)."""
    matches = {}
    used = set()
    def leg_counts(g):
        return (sum(1 for v in g["votes"] if v["VoteValueName"] == "Yes"),
                sum(1 for v in g["votes"] if v["VoteValueName"] == "No"))
    def take(key, m, cands, need_tokens=False):
        if not cands: return
        mt = _toks(m["motion"])
        scores = [len(mt & g["toks"]) for g in cands]
        best = max(scores)
        if need_tokens and (best == 0 or scores.count(best) > 1): return   # tier 3: must be unique+positive
        cands = [g for g, s in zip(cands, scores) if s == best]
        g = cands[0]
        used.add(id(g)); matches[key] = g
    # tier 1 first across all motions (most specific), then tier 2, then tier 3
    ordered = [k for k in sorted(motions, key=lambda k: (k[2], k[1]))
               if motions[k]["body"] in ("Council", "RDA")]
    for key in ordered:
        m = motions[key]
        rows = votes_by_motion.get(key, [])
        if not rows: continue
        sig = (frozenset(person_key(norm_person(mem)) for mem, v in rows if v == "Aye"),
               frozenset(person_key(norm_person(mem)) for mem, v in rows if v == "Nay"))
        take(key, m, [g for g in by_date.get(key[2], []) if g["sig"] == sig and id(g) not in used])
    for key in ordered:
        if key in matches: continue
        m = motions[key]
        rows = votes_by_motion.get(key, [])
        t = TALLY_RE.search(m["result"] or "")
        if not t: continue
        ta, tn = int(t.group(1)), int(t.group(2))
        nays = frozenset(person_key(norm_person(mem)) for mem, v in rows if v == "Nay")
        if rows and not nays: continue           # named non-dissent rows -> tier 1 was authoritative
        cands = [g for g in by_date.get(key[2], []) if id(g) not in used
                 and g["sig"][1] == nays and leg_counts(g) in ((ta, tn), (tn, ta))]
        if rows:
            take(key, m, cands)                                  # tier 2: dissenter signature
        else:
            take(key, m, cands, need_tokens=True)                # tier 3: tally-only + title
    # tier 2b: minutes sometimes record dissent Legistar omits (Legistar shows all-Yes) —
    # a UNIQUE unused group with the identical Aye-set + a positive title-token overlap
    for key in ordered:
        if key in matches: continue
        m = motions[key]
        rows = votes_by_motion.get(key, [])
        ayes = frozenset(person_key(norm_person(mem)) for mem, v in rows if v == "Aye")
        if not ayes: continue
        cands = [g for g in by_date.get(key[2], []) if id(g) not in used and g["sig"][0] == ayes]
        if len(cands) == 1:
            take(key, m, cands, need_tokens=True)
    return matches

# --------------------------------------------------------- schema
DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE body(
  body_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK(kind IN ('council','agency','commission','committee','department')));
CREATE TABLE person(
  person_id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE);
CREATE TABLE meeting(
  meeting_id INTEGER PRIMARY KEY, body_id INTEGER NOT NULL REFERENCES body(body_id),
  meeting_date TEXT NOT NULL, title TEXT, source_file TEXT NOT NULL, UNIQUE(body_id, source_file));
CREATE TABLE application(
  application_id INTEGER PRIMARY KEY, app_key TEXT NOT NULL UNIQUE,
  body_id INTEGER NOT NULL REFERENCES body(body_id), name TEXT, rep_title TEXT);
CREATE TABLE motion(
  motion_id INTEGER PRIMARY KEY,
  meeting_id INTEGER NOT NULL REFERENCES meeting(meeting_id),
  body_id INTEGER NOT NULL REFERENCES body(body_id),
  motion_no INTEGER NOT NULL, motion_text TEXT, motion_type TEXT, result_raw TEXT,
  outcome TEXT CHECK(outcome IN ('Pass','Fail','Continued','Died')),
  stage TEXT CHECK(stage IN ('council_vote','rda_vote','mba_vote','ha_vote','boa_action','other_action','pc_recommendation','pc_final_action')),
  recommendation TEXT CHECK(recommendation IN ('Positive','Negative') OR recommendation IS NULL),
  disposition TEXT CHECK(disposition IN ('approve','deny','continue','table','procedural') OR disposition IS NULL),
  disposition_method TEXT CHECK(disposition_method IN ('keyword','mixed','override','uncaptured','unclassified') OR disposition_method IS NULL),
  disposition_confidence TEXT CHECK(disposition_confidence IN ('high','medium','low') OR disposition_confidence IS NULL),
  application_id INTEGER REFERENCES application(application_id),
  app_match_method TEXT CHECK(app_match_method IN ('matter_id','name','singleton','override') OR app_match_method IS NULL),
  app_confidence TEXT CHECK(app_confidence IN ('high','medium','low') OR app_confidence IS NULL),
  mover_person_id INTEGER REFERENCES person(person_id),
  seconder_person_id INTEGER REFERENCES person(person_id),
  names_recorded INTEGER NOT NULL CHECK(names_recorded IN (0,1)), source_file TEXT NOT NULL);
CREATE TABLE vote(
  vote_id INTEGER PRIMARY KEY,
  motion_id INTEGER NOT NULL REFERENCES motion(motion_id),
  person_id INTEGER NOT NULL REFERENCES person(person_id),
  vote_value TEXT NOT NULL CHECK(vote_value IN ('Aye','Nay','Abstain','Recuse','Absent','Excused')),
  UNIQUE(motion_id, person_id));
CREATE TABLE role(
  role_id INTEGER PRIMARY KEY, person_id INTEGER NOT NULL REFERENCES person(person_id),
  body_id INTEGER NOT NULL REFERENCES body(body_id),
  first_seen TEXT, last_seen TEXT, n_votes INTEGER, UNIQUE(person_id, body_id));
CREATE INDEX ix_motion_app ON motion(application_id);
CREATE INDEX ix_vote_person ON vote(person_id);
CREATE INDEX ix_motion_meeting ON motion(meeting_id);
CREATE INDEX ix_app_body ON application(body_id);

-- ================= sandy-local LEGISTAR EXTENSION LAYER (never conflated with the core;
-- the full structured harvest, incl. bodies/votes the flat CSVs don't carry) =============
CREATE TABLE legistar_body(
  legistar_body_id INTEGER PRIMARY KEY, name TEXT NOT NULL, type_name TEXT,
  body_id INTEGER REFERENCES body(body_id));
CREATE TABLE legistar_person(
  legistar_person_id INTEGER PRIMARY KEY, full_name TEXT NOT NULL,
  person_id INTEGER REFERENCES person(person_id));
CREATE TABLE legistar_event(
  legistar_event_id INTEGER PRIMARY KEY, legistar_body_id INTEGER NOT NULL REFERENCES legistar_body(legistar_body_id),
  event_date TEXT, event_time TEXT, location TEXT,
  agenda_status TEXT, minutes_status TEXT,
  meeting_id INTEGER REFERENCES meeting(meeting_id));
CREATE TABLE legistar_matter(
  legistar_matter_id INTEGER PRIMARY KEY, matter_file TEXT, name TEXT, title TEXT,
  matter_type TEXT, status TEXT, intro_body TEXT, intro_date TEXT,
  agenda_date TEXT, passed_date TEXT, enactment_number TEXT,
  application_id INTEGER REFERENCES application(application_id));
CREATE TABLE legistar_event_item(
  legistar_event_item_id INTEGER PRIMARY KEY,
  legistar_event_id INTEGER NOT NULL REFERENCES legistar_event(legistar_event_id),
  legistar_body_id INTEGER NOT NULL REFERENCES legistar_body(legistar_body_id),
  agenda_sequence INTEGER, minutes_sequence INTEGER, agenda_number TEXT,
  title TEXT, action_name TEXT, passed_flag_name TEXT, roll_call_flag INTEGER, consent INTEGER,
  legistar_matter_id INTEGER REFERENCES legistar_matter(legistar_matter_id),
  matter_file TEXT, matter_type TEXT, matter_status TEXT, mover TEXT, seconder TEXT,
  motion_id INTEGER REFERENCES motion(motion_id));
CREATE TABLE legistar_vote(
  legistar_vote_pk INTEGER PRIMARY KEY,
  legistar_vote_id INTEGER NOT NULL,
  legistar_event_item_id INTEGER NOT NULL REFERENCES legistar_event_item(legistar_event_item_id),
  legistar_person_id INTEGER REFERENCES legistar_person(legistar_person_id),
  person_name TEXT, value_raw TEXT, value_norm TEXT,
  UNIQUE(legistar_vote_id, legistar_event_item_id));
CREATE INDEX ix_lei_event ON legistar_event_item(legistar_event_id);
CREATE INDEX ix_lei_motion ON legistar_event_item(motion_id);
CREATE INDEX ix_lv_item ON legistar_vote(legistar_event_item_id);
"""
VIEWS = """
CREATE VIEW v_project_timeline AS
SELECT a.app_key, a.name AS project, b.name AS body, m.meeting_date AS date,
       mo.stage, mo.outcome, mo.recommendation, mo.result_raw,
       (SELECT group_concat(p.full_name, '; ') FROM vote v JOIN person p ON p.person_id=v.person_id
          WHERE v.motion_id=mo.motion_id AND v.vote_value IN ('Nay','Abstain','Recuse')) AS dissenters,
       mo.app_match_method, mo.app_confidence, mo.motion_id
FROM motion mo JOIN application a ON a.application_id=mo.application_id
  JOIN meeting m ON m.meeting_id=mo.meeting_id JOIN body b ON b.body_id=mo.body_id
ORDER BY a.app_key, m.meeting_date;
CREATE VIEW v_member_record AS
SELECT p.full_name, b.name AS body, COUNT(*) AS votes,
       SUM(v.vote_value='Aye') AS ayes, SUM(v.vote_value='Nay') AS nays,
       SUM(v.vote_value IN ('Abstain','Recuse')) AS abstain_recuse,
       MIN(m.meeting_date) AS first_vote, MAX(m.meeting_date) AS last_vote
FROM vote v JOIN person p ON p.person_id=v.person_id JOIN motion mo ON mo.motion_id=v.motion_id
  JOIN meeting m ON m.meeting_id=mo.meeting_id JOIN body b ON b.body_id=mo.body_id
GROUP BY p.person_id, b.body_id;
-- v_contested is PORTED to the shared cities.db-shape definition
-- (scripts/db_build_lib.V_CONTESTED_DDL, 2026-07-19): split authoritative
-- tally_aye/tally_nay/tally_other (motion_std, COALESCE-fallback to named counts)
-- vs attribution-only named_* columns. MEMBERSHIP UNCHANGED (named dissent only).
-- Executed right after this block; motion_std is loaded by db_build_lib.load_motion_std.
"""

def main():
    motions, votes, present = read_motions()
    if not motions: print("no source motions found", file=sys.stderr); return 1
    ov = {}
    if os.path.exists(OVERRIDES):
        for r in csv.DictReader(open(OVERRIDES)):
            ov[(r["source_file"], r["motion_no"], r["date"])] = r["app_key"].strip()
    disp_ov = {}   # db/disposition_overrides.csv: source_file,motion_no,disposition,note
    if os.path.exists(DISP_OVERRIDES):
        for r in csv.DictReader(open(DISP_OVERRIDES)):
            disp_ov[(r["source_file"], r["motion_no"])] = r["disposition"].strip()
    vote_ov = load_vote_overrides()

    # ---- staging harvest ----
    st_bodies = rd_staging("bodies.csv"); st_persons = rd_staging("persons.csv")
    st_events = rd_staging("events.csv"); st_items = rd_staging("eventitems.csv")
    st_votes = rd_staging("votes.csv");   st_matters = rd_staging("matters.csv")
    votes_by_item = defaultdict(list)
    for v in st_votes: votes_by_item[v["EventItemId"]].append(v)
    matters_by_id = {m["MatterId"]: m for m in st_matters}

    # ---- de-duplicate CSV vote rows (fail-loud on undocumented pairs) ----
    votes_by_motion = defaultdict(list)          # key -> [(member, value)]
    raw_named = defaultdict(int)                 # per dataset: named row count
    seen_pair = {}
    merged_pairs = []                            # (pair_key, first_value, dup_value, resolution)
    unresolved = []
    for key, member, value in votes:
        ds = "planning_commission" if key[0].startswith("db/staging") else "meeting_minutes"
        raw_named[ds] += 1
        pk = (key[0], key[1], key[2], member)
        if pk in seen_pair:
            resolution = vote_ov.get(pk)
            if resolution is None:
                unresolved.append((pk, seen_pair[pk], value)); continue
            votes_by_motion[key] = [(m, (resolution if m == member else v))
                                    for m, v in votes_by_motion[key]]
            merged_pairs.append((pk, seen_pair[pk], value, resolution))
            continue
        seen_pair[pk] = value
        votes_by_motion[key].append((member, value))
    if unresolved:
        print("FATAL: duplicate (source,motion_no,date,member) vote rows without a "
              "db/vote_overrides.csv resolution — never resolved arbitrarily:", file=sys.stderr)
        for pk, a, b in unresolved:
            print(f"  {pk}: {a} + {b}", file=sys.stderr)
        return 1

    # ---- Legistar linkage ----
    pc_map = pc_item_mapping(st_events, st_items, votes_by_item)          # (date, mno) -> item
    by_date = council_groups(st_events, st_items, votes_by_item)
    council_match = match_council_motions(motions, votes_by_motion, by_date)  # key -> group

    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB); con.executescript(DDL); con.executescript(MOTION_STD_DDL); cur = con.cursor()

    # ---- standard core ----
    bid = {}
    for b in sorted({m["body"] for m in motions.values()}):
        cur.execute("INSERT INTO body(name,kind) VALUES(?,?)", (b, kind_of(b))); bid[b] = cur.lastrowid
    names = set()
    for key, rows in votes_by_motion.items():
        for nm, _ in rows:
            n = norm_person(nm)
            if n: names.add(n)
    for m in motions.values():
        for nm in (m["mover"], m["seconder"]):
            if nm: names.add(nm)
    pid = {}
    for nm in sorted(names):
        k = person_key(nm)
        if k in pid: continue
        cur.execute("INSERT INTO person(full_name,name_key) VALUES(?,?)", (nm, k)); pid[k] = cur.lastrowid
    def pers(nm): return pid.get(person_key(nm)) if nm else None

    mtg = {}
    pc_event_by_date = {(e.get("EventDate") or "")[:10]: e for e in st_events
                        if e.get("EventBodyId") == str(PC_BODY_ID)}
    for key in sorted(motions, key=lambda k: (k[2], k[0], k[1])):
        m = motions[key]
        if m["body"] == "PlanningCommission":
            # PC has no minutes files on disk; source_file = the canonical Legistar event
            # resource URL (unique per meeting; provenance of record — SCHEMA_SPEC §5)
            e = pc_event_by_date.get(m["date"])
            src = (f"https://webapi.legistar.com/v1/{LEGISTAR_CLIENT}/events/{e['EventId']}"
                   if e else f"legistar://{LEGISTAR_CLIENT}/pc/{m['date']}")
        else:
            src = m["source"]                     # the minutes .md path (exists on disk)
        mk = (m["body"], src)
        if mk not in mtg:
            cur.execute("INSERT OR IGNORE INTO meeting(body_id,meeting_date,title,source_file) VALUES(?,?,?,?)",
                        (bid[m["body"]], m["date"], m["title"], src))
            cur.execute("SELECT meeting_id FROM meeting WHERE body_id=? AND source_file=?",
                        (bid[m["body"]], src))
            mtg[mk] = cur.fetchone()[0]
        m["_meeting_src"] = src

    app, apptitle = {}, {}
    # matter-backed apps use application_id = MatterId; prose apps live in a disjoint id
    # range (1,000,000+) so the two namespaces can never collide
    prose_id = [1000000]
    def get_app(app_key, body, nm, title, explicit_id=None):
        if app_key not in app:
            if explicit_id is None:
                prose_id[0] += 1; explicit_id = prose_id[0]
            cur.execute("INSERT INTO application(application_id,app_key,body_id,name,rep_title) VALUES(?,?,?,?,?)",
                        (explicit_id, app_key, bid[body], nm, title))
            app[app_key] = explicit_id
            apptitle[app_key] = title or ""
        else:
            if title and len(title) > len(apptitle.get(app_key, "")):
                apptitle[app_key] = title
                cur.execute("UPDATE application SET rep_title=? WHERE application_id=?", (title, app[app_key]))
            if nm: cur.execute("UPDATE application SET name=COALESCE(name,?) WHERE application_id=?", (nm, app[app_key]))
        return app[app_key]

    def matter_app(mid_str, body):
        """Application row backed by a Legistar Matter (exact key; application_id = MatterId)."""
        mt = matters_by_id.get(mid_str)
        if mt is None: return None
        title = re.sub(r"\s+", " ", (mt.get("MatterTitle") or "").strip()) or None
        nm = (mt.get("MatterName") or "").strip() or None
        akey = f"{body}|{mt.get('MatterFile') or 'matter-' + mid_str}"
        return get_app(akey, body, nm, title, explicit_id=int(mid_str))

    # motion insert (deterministic order), with matter / prose application resolution
    mid = {}
    match_stats = defaultdict(int)
    for key in sorted(motions, key=lambda k: (k[2], k[0], k[1])):
        m = motions[key]
        body, title = m["body"], m["motion"]
        mvotes = votes_by_motion.get(key, [])
        # which Legistar item(s) does this motion correspond to?
        leg_items, action_name = [], None
        if body == "PlanningCommission":
            it = pc_map.get((m["date"], m["motion_no"]))
            if it is not None:
                leg_items = [it]; action_name = it.get("EventItemActionName")
        elif key in council_match:
            leg_items = council_match[key]["items"]
        matter_ids = sorted({it["EventItemMatterId"] for it in leg_items if it.get("EventItemMatterId")})
        def lu_matter(mid_s):
            lm = matters_by_id.get(mid_s)
            return lm is not None and (lm.get("MatterTypeName") == "Planning Item"
                                       or is_landuse(lm.get("MatterTypeName"), lm.get("MatterTitle")))
        # a multi-matter roll call (consent calendar) containing exactly ONE land-use matter
        # unambiguously identifies that motion's land-use subject; >1 land-use matters in one
        # roll (e.g. twin annexations) stay unresolved (queryable via legistar_event_item)
        if len(matter_ids) > 1:
            lu = [x for x in matter_ids if lu_matter(x)]
            matter_ids = lu if len(lu) == 1 else matter_ids
        app_id = method = conf = None
        ovkey = ov.get((key[0], str(key[1]), key[2]))
        # worthiness: the standard test on the motion's own fields, EXTENDED by the linked
        # Legistar Matter (council minutes motion text is terse; the matter title carries the
        # land-use substance — this reproduces the old referral population semantics)
        worthy = application_worthy(body, m["motion_type"], title)
        if not worthy and len(matter_ids) == 1 and lu_matter(matter_ids[0]):
            worthy = True
        if ovkey:
            app_id = get_app(f"{body}|{ovkey.lower()}", body, ovkey, title); method, conf = "override", "high"
        elif worthy and len(matter_ids) == 1:
            app_id = matter_app(matter_ids[0], body)
            if app_id is not None: method, conf = "matter_id", "high"
        if worthy and app_id is None:
            nm = None if CODE_AMEND_RE.search(title or "") else project_name(title)
            nk = name_key(nm)
            if nk: app_id = get_app(f"{body}|{nk}", body, nm, title); method, conf = "name", "medium"
            else: app_id = get_app(f"{body}|s|{key[0]}|{key[1]}|{key[2]}", body, None, title); method, conf = "singleton", "high"
        match_stats[method or "(none)"] += 1
        stage, rec = stage_and_rec(body, m["result"], title, action_name)
        if (key[0], str(key[1])) in disp_ov:
            disp, dmeth, dconf = disp_ov[(key[0], str(key[1]))], "override", "high"
        else:
            disp, dmeth, dconf = disposition_of(title)
        cur.execute("""INSERT INTO motion(meeting_id,body_id,motion_no,motion_text,motion_type,result_raw,
                       outcome,stage,recommendation,disposition,disposition_method,disposition_confidence,
                       application_id,app_match_method,app_confidence,
                       mover_person_id,seconder_person_id,names_recorded,source_file)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (mtg[(body, m["_meeting_src"])], bid[body], key[1], title, m["motion_type"], m["result"],
                     outcome_of(m["result"], disp, pc=(body == "PlanningCommission")), stage, rec, disp, dmeth, dconf, app_id, method, conf,
                     pers(m["mover"]), pers(m["seconder"]), 1 if mvotes else 0, key[0]))
        mid[key] = cur.lastrowid
        m["_leg_items"] = leg_items

    dropped = 0
    for key in sorted(votes_by_motion, key=lambda k: (k[2], k[0], k[1])):
        for nm, vv in votes_by_motion[key]:
            p = pers(norm_person(nm))
            if p is None: dropped += 1; continue
            cur.execute("INSERT INTO vote(motion_id,person_id,vote_value) VALUES(?,?,?)",
                        (mid[key], p, vv))
    cur.execute("""INSERT INTO role(person_id,body_id,first_seen,last_seen,n_votes)
                   SELECT v.person_id, mo.body_id, MIN(m.meeting_date), MAX(m.meeting_date), COUNT(*)
                   FROM vote v JOIN motion mo ON mo.motion_id=v.motion_id JOIN meeting m ON m.meeting_id=mo.meeting_id
                   GROUP BY v.person_id, mo.body_id""")

    # ---- Legistar extension layer ----
    std_body_of_leg = {COUNCIL_BODY_ID: "Council", PC_BODY_ID: "PlanningCommission"}
    for b in st_bodies:
        lid = int(b["BodyId"])
        cur.execute("INSERT INTO legistar_body(legistar_body_id,name,type_name,body_id) VALUES(?,?,?,?)",
                    (lid, b["BodyName"], b.get("BodyTypeName"),
                     bid.get(std_body_of_leg.get(lid))))
    for p in st_persons:
        if not p.get("PersonId"): continue
        nm = (p.get("PersonFullName") or "").strip()
        cur.execute("INSERT INTO legistar_person(legistar_person_id,full_name,person_id) VALUES(?,?,?)",
                    (int(p["PersonId"]), nm, pid.get(leg_key(nm))))
    # events (link to a standard meeting when the body+date pair is unambiguous)
    mtg_by_body_date = defaultdict(list)
    for (b, src), mgid in mtg.items():
        d = cur.execute("SELECT meeting_date FROM meeting WHERE meeting_id=?", (mgid,)).fetchone()[0]
        mtg_by_body_date[(b, d)].append(mgid)
    for e in st_events:
        lb = int(e["EventBodyId"]); d = (e.get("EventDate") or "")[:10]
        cand = mtg_by_body_date.get((std_body_of_leg.get(lb, ""), d), [])
        cur.execute("""INSERT INTO legistar_event(legistar_event_id,legistar_body_id,event_date,event_time,
                       location,agenda_status,minutes_status,meeting_id) VALUES(?,?,?,?,?,?,?,?)""",
                    (int(e["EventId"]), lb, d, e.get("EventTime"), e.get("EventLocation"),
                     e.get("EventAgendaStatusName"), e.get("EventMinutesStatusName"),
                     cand[0] if len(cand) == 1 else None))
    app_ids = set(app.values())
    for mt in st_matters:
        if not mt.get("MatterId"): continue
        mid_i = int(mt["MatterId"])
        cur.execute("""INSERT INTO legistar_matter(legistar_matter_id,matter_file,name,title,matter_type,
                       status,intro_body,intro_date,agenda_date,passed_date,enactment_number,application_id)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (mid_i, mt.get("MatterFile"), (mt.get("MatterName") or "").strip() or None,
                     re.sub(r"\s+", " ", (mt.get("MatterTitle") or "").strip()) or None,
                     mt.get("MatterTypeName"), mt.get("MatterStatusName"), mt.get("MatterBodyName"),
                     (mt.get("MatterIntroDate") or "")[:10] or None,
                     (mt.get("MatterAgendaDate") or "")[:10] or None,
                     (mt.get("MatterPassedDate") or "")[:10] or None,
                     mt.get("MatterEnactmentNumber") or None,
                     mid_i if mid_i in app_ids else None))
    # event items (motion link comes from the PC/council matching above)
    item_motion = {}
    for key, m in motions.items():
        for it in m.get("_leg_items", []): item_motion[it["EventItemId"]] = mid[key]
    def _int(x):
        try: return int(x)
        except (TypeError, ValueError): return None
    for it in st_items:
        cur.execute("""INSERT INTO legistar_event_item(legistar_event_item_id,legistar_event_id,legistar_body_id,
                       agenda_sequence,minutes_sequence,agenda_number,title,action_name,passed_flag_name,
                       roll_call_flag,consent,legistar_matter_id,matter_file,matter_type,matter_status,
                       mover,seconder,motion_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (int(it["EventItemId"]), int(it["EventItemEventId"]), int(it["EventBodyId"]),
                     _int(it.get("EventItemAgendaSequence")), _int(it.get("EventItemMinutesSequence")),
                     it.get("EventItemAgendaNumber") or None,
                     re.sub(r"\s+", " ", (it.get("EventItemTitle") or "").strip()) or None,
                     it.get("EventItemActionName") or None, it.get("EventItemPassedFlagName") or None,
                     1 if it.get("EventItemRollCallFlag") in ("1", "True", "true") else 0,
                     1 if it.get("EventItemConsent") in ("1", "True", "true") else 0,
                     _int(it.get("EventItemMatterId")), it.get("EventItemMatterFile") or None,
                     it.get("EventItemMatterType") or None, it.get("EventItemMatterStatus") or None,
                     it.get("EventItemMover") or None, it.get("EventItemSeconder") or None,
                     item_motion.get(it["EventItemId"])))
    VMAP = {"yes": "Aye", "no": "Nay", "abstain": "Abstain", "recused": "Recuse",
            "absent": "Absent", "excused": "Excused", "nonvoting": "Nonvoting"}
    lp_ids = {r[0] for r in cur.execute("SELECT legistar_person_id FROM legistar_person")}
    for v in st_votes:
        pid_i = _int(v.get("VotePersonId"))
        cur.execute("""INSERT INTO legistar_vote(legistar_vote_id,legistar_event_item_id,legistar_person_id,
                       person_name,value_raw,value_norm) VALUES(?,?,?,?,?,?)""",
                    (int(v["VoteId"]), int(v["EventItemId"]), pid_i if pid_i in lp_ids else None,
                     v.get("VotePersonName"), v.get("VoteValueName"),
                     VMAP.get((v.get("VoteValueName") or "").strip().lower())))

    _std = load_motion_std(cur, REPO)
    for _ds, (_n, _m) in sorted(_std.items()):
        print(f"  motion_std [{_ds}]: {_n} rows, {_m} joined to motion"
              + ("" if _m == _n else f"  \u26a0 {_n - _m} UNMATCHED"))
    con.executescript(VIEWS); con.executescript(V_CONTESTED_DDL); con.commit()

    # ---- integrity + reconciliation ----
    problems = []
    if cur.execute("PRAGMA foreign_key_check").fetchall(): problems.append("FK violations")
    if cur.execute("SELECT COUNT(*) FROM motion").fetchone()[0] != len(motions): problems.append("motion count drift")
    span = cur.execute("""SELECT COUNT(*) FROM (SELECT application_id FROM motion WHERE application_id IS NOT NULL
                          GROUP BY application_id HAVING COUNT(DISTINCT body_id)>1)""").fetchone()[0]
    if span: problems.append(f"{span} applications span >1 body")
    # HARD CHECK (T1.1, refined by the T1.3 audit): a motion's outcome must agree with its
    # yes:no / yes-no tally (carriage) UNLESS a strict carriage WORD in the result supports
    # the stored outcome — the audit proved conflicting tallies are usually the corrupt
    # signal (majority-first "failed 4-3", page-break truncation, OCR digits), so
    # word-over-tally rows are printed for review, not failed. Would have caught Yalecrest
    # (a failed 4:5 positive rec stored as Pass). Ignores ties and Continued/Died. A genuine
    # supermajority failure may also carry 'supermajor'/'two-third'/'2/3'.
    tally_violations, word_over_tally = [], 0
    for mo_id, res, oc in cur.execute("SELECT motion_id, result_raw, outcome FROM motion"):
        m = _TALLY_RE.search(_CLOCK_RE.sub(" ", res or ""))
        if not m: continue
        yes, no = int(m.group(1)), int(m.group(2))
        if yes == no or oc in ("Continued", "Died"): continue
        t = "Pass" if yes > no else "Fail"
        if oc == t: continue
        word = ("Fail" if _FAILWORD_RE.search((res or "").lower())
                else ("Pass" if _PASSWORD_RE.search((res or "").lower()) else None))
        if word == oc or re.search(r'supermajor|two-third|2/3', (res or "").lower()):
            word_over_tally += 1; continue
        tally_violations.append((mo_id, res, oc))
    if word_over_tally:
        print(f"  outcome: {word_over_tally} word-over-tally rows (explicit carriage word "
              f"contradicts the printed tally — majority-first/corrupt-tally convention; review)")
    if tally_violations:
        problems.append(f"{len(tally_violations)} outcome/tally contradictions (e.g. {tally_violations[:3]})")
    db_votes = cur.execute("SELECT COUNT(*) FROM vote").fetchone()[0]
    csv_named = sum(raw_named.values())
    if db_votes + len(merged_pairs) != csv_named or dropped:
        problems.append(f"vote reconciliation broken (db {db_votes} + merged {len(merged_pairs)} "
                        f"!= CSV named {csv_named}; dropped {dropped})")

    os.makedirs(TABLES, exist_ok=True)
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        rows = cur.execute(f"SELECT * FROM {t}").fetchall(); cols = [d[0] for d in cur.description]
        with open(os.path.join(TABLES, t + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)

    def n(t): return cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"== built {os.path.relpath(DB, REPO)} from {len(present)} flat source(s) + staging ==")
    print("  STANDARD CORE")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role"):
        print(f"    {t:12} {n(t)}")
    print("    by app method:", dict(cur.execute(
        "SELECT app_match_method,COUNT(*) FROM motion WHERE application_id IS NOT NULL GROUP BY 1")),
        "| no application:", cur.execute("SELECT COUNT(*) FROM motion WHERE application_id IS NULL").fetchone()[0])
    print("    motions by body:", dict(cur.execute("SELECT name,COUNT(*) FROM motion JOIN body USING(body_id) GROUP BY 1")))
    print(f"    apps spanning >1 body (must be 0): {span}")
    print("  RECONCILIATION (CSV named rows = db votes + merged override pairs)")
    for ds in sorted(raw_named):
        print(f"    {ds:22} named rows {raw_named[ds]}")
    print(f"    total {csv_named} = {db_votes} db votes + {len(merged_pairs)} merged duplicate pairs "
          f"(all documented in db/vote_overrides.csv)")
    for pk, a, b, res in merged_pairs:
        tag = "conflict" if a != b else "identical"
        print(f"      [{tag}] {pk[2]} m{pk[1]} {pk[3]}: {a}+{b} -> {res}")
    print("  LEGISTAR EXTENSION")
    for t in ("legistar_body", "legistar_person", "legistar_event", "legistar_matter",
              "legistar_event_item", "legistar_vote"):
        print(f"    {t:20} {n(t)}")
    linked = cur.execute("SELECT COUNT(DISTINCT motion_id) FROM legistar_event_item WHERE motion_id IS NOT NULL").fetchone()[0]
    pc_total = cur.execute("""SELECT COUNT(*) FROM motion mo JOIN body b ON b.body_id=mo.body_id
                              WHERE b.name='PlanningCommission'""").fetchone()[0]
    pc_linked = cur.execute("""SELECT COUNT(DISTINCT lei.motion_id) FROM legistar_event_item lei
                               JOIN motion mo ON mo.motion_id=lei.motion_id
                               JOIN body b ON b.body_id=mo.body_id WHERE b.name='PlanningCommission'""").fetchone()[0]
    print(f"    motions linked to Legistar items: {linked}/{len(motions)} "
          f"(PC {pc_linked}/{pc_total} exact; council = roll-call signature matches; "
          f"unlinked council motions are minutes-only records Legistar doesn't carry)")
    print("  DISPOSITION")
    print("    by disposition:", dict(cur.execute(
        "SELECT COALESCE(disposition,'(null)'),COUNT(*) FROM motion GROUP BY 1 ORDER BY 2 DESC")))
    # CROSS-CHECK (informational, non-fatal): for PC recommendation motions, disposition
    # composed with carriage (approve+Pass / deny+Fail -> Positive; deny+Pass / approve+Fail
    # -> Negative) should equal the legacy `recommendation` field. Mismatches are NOT
    # disposition errors: they expose that recommendation direction was keyword-matched
    # WITHOUT reliably composing with the outcome (the same bug class fixed in outcome_of).
    # disposition (proposed action) + outcome (carriage) are the correct, separable primitives.
    # Surfaced for review, not a build failure.
    rec_rows = cur.execute("""SELECT disposition, outcome, recommendation FROM motion
                              WHERE stage='pc_recommendation' AND recommendation IS NOT NULL
                              AND disposition IN ('approve','deny')""").fetchall()
    mism = [(d, o, rc) for d, o, rc in rec_rows if _compose_dir(d, o) != rc]
    if rec_rows:
        print(f"    disposition vs legacy recommendation: {len(rec_rows)-len(mism)}/{len(rec_rows)} agree"
              + (f" -- {len(mism)} legacy-recommendation inconsistencies (review, not disposition errors)" if mism else ""))
    print("  INTEGRITY:", "OK" if not problems else problems)
    con.close(); return 0 if not problems else 1

if __name__ == "__main__":
    sys.exit(main())
