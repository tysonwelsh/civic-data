#!/usr/bin/env python3
# NOTE (REFACTOR_PLAN 4.3, 2026-07-07): this city's build_db.py is a DOCUMENTED FORK.
# The 10 template cities share scripts/db_build_lib.py; this city diverges for real
# reasons (see its docstring/db/SCHEMA.md). When fixing a core-build bug, fix the lib
# FIRST, then port the fix here by diffing against the lib.
"""
build_db.py — normalized relational database for a Utah city's civic vote data (VENDOR-AGNOSTIC
TEMPLATE for PDF/prose portals: CivicClerk, Granicus, Revize, CivicPlus, PrimeGov-PDF, OnBase).

This is the WITHIN-BODY EXACT CORE. It consumes the per-body denormalized vote CSVs
(meeting_minutes/all_votes.csv + planning_commission/all_votes.csv, both the standard 13-col
schema) and produces a normalized SQLite DB (body/person/meeting/application/motion/vote/role).
Run db/build_referrals.py AFTER this for the reconstructed cross-body PC->Council referral layer.

Use this template for vendors that give NO structured agenda/matter key (so the project key is
RESOLVED FROM PROSE). For Legistar cities use the Sandy build_db.py instead (exact MatterId).

TWO LAYERS, NEVER CONFLATED: the project `application_id` is resolved WITHIN EACH BODY
(body-scoped) — a Council "Foo" and a PC "Foo" are DISTINCT applications here; the cross-body tie
lives ONLY in the separate `referral` table. `build_db.py` therefore reports 0 apps spanning >1 body.

Resolution tiers (recorded on every motion as app_match_method + app_confidence):
  override (high)  — db/overrides.csv row forces it (source_file,motion_no,app_key)
  name     (medium)— a named development/annexation/rezone grouped by normalized name (heuristic)
  singleton(high)  — unnamed land-use/policy motion (generic rezone/GPA, code/text amendment) -> its
                     own application (exact identity, name unknown; kept granular for referrals)
  (NULL)           — non-land-use motion (budget/appointments/contracts/procedural) -> no application

Idempotent. Run:  python3 db/build_db.py
"""
import csv, glob, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# Shared v_contested column-shape parity (2026-07-19): this fork imports ONLY the
# three parity pieces from the shared lib — the motion_std table DDL, its loader,
# and the reshaped v_contested view — everything else remains this city's fork.
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "scripts"))
from db_build_lib import MOTION_STD_DDL, V_CONTESTED_DDL, load_motion_std

_existing = sorted(glob.glob(os.path.join(HERE, "*.db")))   # reuse an existing db name; else civic.db
DB = _existing[0] if _existing else os.path.join(HERE, "civic.db")
TABLES = os.path.join(HERE, "tables")
OVERRIDES = os.path.join(HERE, "overrides.csv")
VOTE_OVERRIDES = os.path.join(HERE, "vote_overrides.csv")
DISP_OVERRIDES = os.path.join(HERE, "disposition_overrides.csv")
# standard per-body vote CSVs (skip any that don't exist yet)
SOURCES = [os.path.join(REPO, "meeting_minutes", "all_votes.csv"),
           os.path.join(REPO, "planning_commission", "all_votes.csv")]

# --------------------------------------------------------- body kind (keyword-based, vendor-agnostic)
def kind_of(name):
    n = (name or "").lower()
    if "planning" in n or ("commission" in n and "redevelop" not in n): return "commission"
    if "adjust" in n or "appeal" in n or n.strip() in ("boa",): return "commission"
    if any(k in n for k in ("redevelop", "reinvest", "rda", "cra", "agency")): return "agency"
    if any(k in n for k in ("building authority", "mba", "lba", "housing", "ha")): return "agency"
    if "board" in n: return "committee"
    return "council"

# --------------------------------------------------------- person helpers
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

# --------------------------------------------------------- land-use / project resolution
LU_TYPES = {"land-use/zoning"}                 # the taxonomy's inherently-land-use motion_type
LANDUSE_RE = re.compile(
    r"\b(rezone|zone change|subdivision|\bplat\b|annex|general plan|conditional use|site plan|"
    r"development agreement|vacat|planned unit|\bpud\b|condominium|project area|reinvestment|"
    r"development code amendment|code amendment|amending (?:title|chapter|section)|"
    # T1.4 (2026-07-12): admit legislative items the rezone/text-amendment taxonomy missed —
    # historic-district designations, landmark sites, small/station-area + master plans (the
    # PC forwards these to Council; Yalecrest-Laird Heights divergence was invisible without
    # them). "historic preservation" is deliberately NOT admitted (matches board APPOINTMENTS
    # and proclamations, not designations).
    r"historic district|landmark site|(?:small|station) area plan|master plan|table \d)\b", re.I)
CODE_AMEND_RE = re.compile(
    r"\b(development code amendment|code amendment|amending (?:title|chapter|section)|"
    r"amendment to (?:chapter|section|table)|table \d{2}\.\d)\b", re.I)
_GRID = re.compile(r"\b\d{2,5}\s+(?:north|south|east|west|n|s|e|w)\.?\s+\d{2,5}\s+(?:north|south|east|west|n|s|e|w)\b", re.I)
def is_landuse(motion_type, title):
    return (motion_type or "").strip().lower() in LU_TYPES or bool(LANDUSE_RE.search(title or ""))
def application_worthy(body, motion_type, title):
    # Council/PC: only true land-use/policy motions get a project application (budgets/appointments
    # stay app-less). Agency bodies (RDA/CRA/HA/MBA) are inherently development/finance bodies, so any
    # motion naming a project OR citing an address is development-related and worth an application
    # (so RDA project-area/loan actions can link to the council rezone / PC rec for the same site).
    if is_landuse(motion_type, title): return True
    if kind_of(body) == "agency":
        if (motion_type or "").strip().lower() == "appointment": return False
        if AGENCY_PROCEDURAL.search(title or ""): return False   # meeting-date/budget/canvass/consent
        return True   # substantive agency motion (mitigation plan, disposition, grant, easement, purchase)
    return False
AGENCY_PROCEDURAL = re.compile(
    r"regular meeting date|meeting date,? time|fiscal year|revised budget|adjusted budget|annual budget|"
    r"board of canvass|certifying the official canvass|consent agenda|approve the minutes|"
    r"^.{0,40}\bminutes\b.{0,30}$", re.I)

# --------------------------------------------------------- SLC-LOCAL land-use taxonomy adaptation
# (shared template left pristine; SLC uses a RICH motion_type taxonomy that the generic template's
# single "land-use/zoning" type + Lehi-tuned title regex don't cover). SLC's Planning Commission tags
# every motion with a specific land-use category, and the Council/agencies phrase zoning actions as
# "Zoning Map Amendment", "Master Plan Amendment", "Planned Development", "Design Review", etc. Without
# this the land-use universe (and thus the PC->Council referral layer) is drastically under-detected.
SLC_LU_TYPES = {"planned development", "conditional use", "zoning map amendment", "zoning text amendment",
    "design review", "master plan amendment", "subdivision/plat", "street/alley closure", "special exception"}
SLC_LANDUSE_RE = re.compile(r"\b(zoning map amendment|zoning map|master plan amendment|planned development|"
    r"design review|conditional use|special exception|street/?\s?alley closure|alley vacation|street vacation|"
    r"text amendment|zoning text)\b", re.I)
_tmpl_is_landuse = is_landuse
def is_landuse(motion_type, title):
    if (motion_type or "").strip().lower() in SLC_LU_TYPES: return True
    if SLC_LANDUSE_RE.search(title or ""): return True
    return _tmpl_is_landuse(motion_type, title)
# Tighten the agency "substantive motion" gate: SLC's RDA/CRA/LBA sessions carry many PURELY procedural
# motions (adjourn/reconvene transitions, closed-session entries, remote-meeting ratifications, and
# whole-agency budget amendments) that are NOT project applications and would pollute referrals.
SLC_AGENCY_PROCEDURAL = re.compile(r"ratify .*(remot|anchor location)|"
    r"continue (?:to )?meet(?:ing)? (?:remotely|without)|"
    r"budget amendment|amending the (?:final|adjusted|tentative) budget|capital projects fund budget", re.I)
# Pure housekeeping that must NEVER be a project application in ANY body. NB SLC's in-session body
# transitions ("Adjourn as the Community Reinvestment Agency and convene as the City Council") contain
# the word "reinvestment"/"project area" that would otherwise trip the land-use regex; closed-session
# and minutes-approval motions likewise. Guard them globally before any land-use test.
SLC_PROCEDURAL_NEVER = re.compile(r"\b(adjourn|reconvene|convene as|closed session)\b|"
    r"enter into closed session|approve the (?:meeting )?minutes|the (?:meeting )?minutes of|"
    r"ratify .*(?:remot|anchor location)", re.I)
_tmpl_application_worthy = application_worthy
def application_worthy(body, motion_type, title):
    if SLC_PROCEDURAL_NEVER.search(title or ""): return False
    if kind_of(body) == "agency" and not is_landuse(motion_type, title) and SLC_AGENCY_PROCEDURAL.search(title or ""):
        return False
    return _tmpl_application_worthy(body, motion_type, title)

# named-project extractor (general Utah land-use phrasing; tune NAME_TYPE/patterns per city if needed)
NAME_TYPE = (r"(Annexation|Zone Change|Rezone|General Plan (?:Land Use )?Amendment|Plat Amendment|"
             r"Community Reinvestment Project Area(?: Plan)?(?: Amendment)?|Project Area Plan|"
             r"Area Plan(?: Amendment)?|Site Plan|Master Plan|Subdivision|"
             r"(?:Local )?Historic District)")
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
def outcome_of(res, disp=None):
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
            return word if (word and word != t) else t   # carriage word beats a suspect tally
        return word or "Fail"                            # tie: word if any, else a tie fails
    if word: return word
    if "den" in r:
        return "Pass" if disp == "deny" else "Fail"      # tally-less "Denied": deny motion carried
    return "Pass"
def is_pc(name): return "planning" in (name or "").lower()
def recommendation_of(body, res, title):
    if not is_pc(body): return None
    s = ((res or "") + " " + (title or "")).lower()
    if "negative recommendation" in s or "recommend denial" in s or ("deny" in s and "recommend" in s):
        return "Negative"
    if "positive recommendation" in s or "recommend approval" in s or "forward" in s or "recommend" in s:
        return "Positive"
    return None
# --------------------------------------------------------- disposition (PROPOSED action)
# `disposition` records what a motion PROPOSES for the matter — approve / deny / continue /
# table / procedural — a DISTINCT axis from `outcome` (did the motion carry). It is NOT
# pre-composed with the outcome (that was the whole root-cause lesson: keep the two facts
# separable). Compose at query time: disposition='approve' AND outcome='Pass' => matter
# approved; 'approve' AND 'Fail' => not approved; 'deny' AND 'Pass' => denied. For PC
# recommendation motions this is cross-checked against the independently-derived
# `recommendation` field via _compose_dir() below (a free validation oracle). Read from
# `motion_text` (the verbatim proposed action); corrections go in db/disposition_overrides.csv.
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
def stage_of(body, res, title):
    if is_pc(body):
        s = ((res or "") + " " + (title or "")).lower()
        return "pc_recommendation" if "recommend" in s or "forward" in s else "pc_final_action"
    n = (body or "").lower()
    if "adjust" in n or "appeal" in n or n.strip() == "boa": return "boa_action"
    if kind_of(body) == "agency":
        if "housing" in n or n.strip() == "ha": return "ha_vote"
        if any(x in n for x in ("building authority","mba","lba")): return "mba_vote"
        return "rda_vote"
    if kind_of(body) == "council": return "council_vote"
    return "other_action"

# --------------------------------------------------------- SLC-LOCAL body-derivation shim
# NOTE (SLC adaptation — the shared template in skills/ is left pristine): Salt Lake City's council
# minutes interleave FOUR governing bodies in ONE vote stream — the City Council convenes, then
# adjourns/reconvenes in-session as the Local Building Authority (LBA), Redevelopment Agency (RDA), and
# Community Reinvestment Agency (CRA). The protected meeting_minutes/all_votes.csv (immutable per task)
# therefore has NO per-row `body` column (unlike the PC CSV / Lehi's clean 13-col schema). We RECOVER
# body per motion here by WALKING THE SOURCE MARKDOWN MINUTES (the authoritative section structure the
# votes were extracted from): each meeting's ALL-CAPS bold section headers ("LBA OPENING CEREMONY",
# "REDEVELOPMENT AGENCY ...", "SALT LAKE CITY COUNCIL MEETING", "...reconvene as the City Council")
# delimit the body sections, and each voted motion ends with a "Final Result" line — so the i-th
# "Final Result" in markdown order maps to the i-th motion_no for that source file. 294/302 files match
# exactly; where the markdown/CSV motion counts diverge (8 files, mostly pure-body) we fall back to the
# last-seen / title-initial body. Read-time normalization only — no file is modified.
_BODY_LBA = "Local Building Authority"; _BODY_RDA = "Redevelopment Agency"
_BODY_CRA = "Community Reinvestment Agency"; _BODY_COUNCIL = "Council"
def _initial_body(title):
    # A COMBINED meeting (title names the Council alongside agencies) is walked starting as Council:
    # whichever section comes first carries its own header marker, so an agency-first combined meeting
    # switches before its first motion, while a council-first one (agencies tacked on at the end, e.g.
    # "LBA RDA and Council" minutes that actually open with the Council) stays correct. Only a
    # PURE-agency meeting (no "council" in the title) starts as that agency.
    t = (title or "").lower()
    for p in ("revised ", "limited ", "special "):
        if t.startswith(p): t = t[len(p):]
    if "council" in t: return _BODY_COUNCIL
    if t.startswith("lba") or "building authority" in t: return _BODY_LBA
    if t.startswith("rda") or "redevelopment" in t: return _BODY_RDA
    if t.startswith("cra") or "community reinvestment" in t: return _BODY_CRA
    return _BODY_COUNCIL
def _body_marker(line):
    u = line.upper()
    if "RECONVENE AS" in u or "CONVENE AS" in u:
        if "COUNCIL" in u: return _BODY_COUNCIL
        if "REDEVELOPMENT" in u or re.search(r"\bRDA\b", u): return _BODY_RDA
        if "COMMUNITY REINVESTMENT" in u or re.search(r"\bCRA\b", u): return _BODY_CRA
        if "BUILDING AUTHORITY" in u or re.search(r"\bLBA\b", u): return _BODY_LBA
    # SECTION-HEADER branch: only SHORT bold/all-caps lines are headers. A long bold line is a "Moved
    # by ... to **adopt ...**" MOTION that may merely NAME an agency as a party (e.g. an ILA "between
    # Salt Lake City, the Community Reinvestment Agency, and UTA") and must NOT switch the body.
    hdr = line.strip().strip("*").strip()
    if len(hdr) <= 70 and ("**" in line or line.strip().isupper()):
        if re.search(r"\bLBA (OPENING|POTENTIAL|ADJOURN|MEETING|UNFINISHED)", u) or "LOCAL BUILDING AUTHORITY" in u: return _BODY_LBA
        if re.search(r"\bRDA (OPENING|POTENTIAL|MEETING|UNFINISHED)", u) or "REDEVELOPMENT AGENCY" in u: return _BODY_RDA
        if re.search(r"\bCRA (OPENING|POTENTIAL|MEETING|UNFINISHED)", u) or "COMMUNITY REINVESTMENT AGENCY" in u: return _BODY_CRA
        if "CITY COUNCIL MEETING" in u: return _BODY_COUNCIL
    return None
def _body_seq(md_path, title):
    cur = _initial_body(title); seq = []
    try:
        with open(md_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                mk = _body_marker(line)
                if mk: cur = mk
                if re.search(r"Final Result", line, re.I): seq.append(cur)
    except OSError:
        return None
    return seq
def _derive_bodies(rows, mddir):
    # rows: list of dicts for ONE source file; returns motion_no -> body (walked from the markdown)
    mnos = sorted({r["motion_no"] for r in rows}, key=lambda x: int(x))
    ib = _initial_body(rows[0]["title"])
    seq = _body_seq(os.path.join(mddir, rows[0]["source"]), rows[0]["title"])
    bm = {}
    for i, mno in enumerate(mnos):
        bm[mno] = seq[i] if (seq and i < len(seq)) else ((seq[-1] if seq else ib))
    return bm

# --------------------------------------------------------- read source motions
def read_motions():
    motions, votes, present = {}, [], []
    for path in SOURCES:
        if not os.path.exists(path):
            print(f"  (skipping absent source: {os.path.relpath(path, REPO)})"); continue
        present.append(path)
        with open(path) as fh:
            allrows = list(csv.DictReader(fh))
        has_body = bool(allrows) and "body" in allrows[0]
        if has_body:
            # Phase 2.5 retrofit (2026-07-02): the council CSV now carries the clone-standard SHORT
            # body vocabulary (Council/RDA/CRA/LBA) in a real `body` column — derived from this very
            # build's section-header walk, so it is authoritative. Map short codes back to the db's
            # full body names so the built db is identical to the pre-retrofit build ("Council" and
            # the PC CSV's "PlanningCommission" pass through unchanged). The markdown-walk shim below
            # is retained as the derivation of record / fallback for a body-less CSV.
            _short2full = {"RDA": _BODY_RDA, "CRA": _BODY_CRA, "LBA": _BODY_LBA}
            for r in allrows: r["body"] = _short2full.get(r["body"], r["body"])
        if not has_body:   # SLC council CSV: recover body per source-file by walking the source markdown
            mddir = os.path.dirname(path)   # source paths are relative to the CSV's folder (meeting_minutes/)
            from collections import OrderedDict
            bysrc = OrderedDict()
            for r in allrows: bysrc.setdefault(r["source"], []).append(r)
            bmap = {}
            for src, g in bysrc.items():
                for mno, b in _derive_bodies(g, mddir).items(): bmap[(src, mno)] = b
            for r in allrows: r["body"] = bmap[(r["source"], r["motion_no"])]
        for r in allrows:
            key = (r["source"], r["motion_no"])
            if key not in motions:
                motions[key] = dict(date=r["date"], body=r["body"], title=r["title"],
                                    motion_no=int(r["motion_no"]), motion=r["motion"],
                                    motion_type=r.get("motion_type",""), result=r.get("result",""),
                                    mover=norm_person(r.get("mover")), seconder=norm_person(r.get("seconder")),
                                    source=r["source"],
                                    provenance=r.get("provenance") or "minutes")
            if r.get("member") and r.get("vote"):
                votes.append((r["source"], r["motion_no"], norm_person(r["member"]), r["vote"]))
    return motions, votes, present

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
  app_match_method TEXT CHECK(app_match_method IN ('name','singleton','override') OR app_match_method IS NULL),
  app_confidence TEXT CHECK(app_confidence IN ('high','medium','low') OR app_confidence IS NULL),
  mover_person_id INTEGER REFERENCES person(person_id),
  seconder_person_id INTEGER REFERENCES person(person_id),
  names_recorded INTEGER NOT NULL CHECK(names_recorded IN (0,1)), source_file TEXT NOT NULL,
  provenance TEXT);
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
            ov[(r["source_file"], r["motion_no"])] = r["app_key"].strip()
    disp_ov = {}   # db/disposition_overrides.csv: source_file,motion_no,disposition,note
    if os.path.exists(DISP_OVERRIDES):
        for r in csv.DictReader(open(DISP_OVERRIDES)):
            disp_ov[(r["source_file"], r["motion_no"])] = r["disposition"].strip()
    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB); con.executescript(DDL); con.executescript(MOTION_STD_DDL); cur = con.cursor()

    bid = {}
    for b in sorted({m["body"] for m in motions.values()}):
        cur.execute("INSERT INTO body(name,kind) VALUES(?,?)", (b, kind_of(b))); bid[b] = cur.lastrowid
    names = set()
    for _, _, nm, _ in votes:
        if nm: names.add(nm)
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
    for m in motions.values():
        key = (m["body"], m["source"])
        if key not in mtg:
            cur.execute("INSERT OR IGNORE INTO meeting(body_id,meeting_date,title,source_file) VALUES(?,?,?,?)",
                        (bid[m["body"]], m["date"], m["title"], m["source"]))
            cur.execute("SELECT meeting_id FROM meeting WHERE body_id=? AND source_file=?",
                        (bid[m["body"]], m["source"])); mtg[key] = cur.fetchone()[0]
    app, apptitle = {}, {}
    def get_app(app_key, body, nm, title):
        if app_key not in app:
            cur.execute("INSERT INTO application(app_key,body_id,name,rep_title) VALUES(?,?,?,?)",
                        (app_key, bid[body], nm, title)); app[app_key] = cur.lastrowid; apptitle[app_key] = title or ""
        else:
            if title and len(title) > len(apptitle.get(app_key, "")):
                apptitle[app_key] = title
                cur.execute("UPDATE application SET rep_title=? WHERE application_id=?", (title, app[app_key]))
            if nm: cur.execute("UPDATE application SET name=COALESCE(name,?) WHERE application_id=?", (nm, app[app_key]))
        return app[app_key]
    vbym = {}
    for src, mno, nm, vv in votes:
        vbym.setdefault((src, mno), []).append((nm, vv))
    mid = {}
    for (src, mno), m in motions.items():
        body, title = m["body"], m["motion"]
        app_id = method = conf = None
        ovkey = ov.get((src, str(mno)))
        if ovkey:
            app_id = get_app(f"{body}|{ovkey.lower()}", body, ovkey, title); method, conf = "override", "high"
        elif application_worthy(body, m["motion_type"], title):
            nm = None if CODE_AMEND_RE.search(title or "") else project_name(title)
            nk = name_key(nm)
            if nk: app_id = get_app(f"{body}|{nk}", body, nm, title); method, conf = "name", "medium"
            else: app_id = get_app(f"{body}|s|{src}|{mno}", body, None, title); method, conf = "singleton", "high"
        mvotes = vbym.get((src, mno), [])
        if (src, str(mno)) in disp_ov:
            disp, dmeth, dconf = disp_ov[(src, str(mno))], "override", "high"
        else:
            disp, dmeth, dconf = disposition_of(title)
        cur.execute("""INSERT INTO motion(meeting_id,body_id,motion_no,motion_text,motion_type,result_raw,
                       outcome,stage,recommendation,disposition,disposition_method,disposition_confidence,
                       application_id,app_match_method,app_confidence,
                       mover_person_id,seconder_person_id,names_recorded,source_file,provenance)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (mtg[(body, src)], bid[body], mno, title, m["motion_type"], m["result"],
                     outcome_of(m["result"], disp), stage_of(body, m["result"], title),
                     recommendation_of(body, m["result"], title), disp, dmeth, dconf,
                     app_id, method, conf,
                     pers(m["mover"]), pers(m["seconder"]), 1 if mvotes else 0, src,
                     m.get("provenance", "minutes")))
        mid[(src, mno)] = cur.lastrowid
    # ---- explicit vote-conflict resolution (REMEDIATION_PLAN 3.1; park_city pattern) --
    # The flat all_votes.csv is city-faithful/verbatim: where the source minutes list a
    # member under BOTH the AYES and NAYS/ABSTAIN/ABSENT labels (clerk duplication), the
    # CSV carries two contradictory rows for one (motion, person). INSERT OR IGNORE used
    # to keep whichever row happened to come first (arbitrary, silent). Now: identical
    # duplicates merge; CONTRADICTORY pairs MUST have a documented resolution in
    # db/vote_overrides.csv (source_file,motion_no,member,date,claimed_values,resolution,
    # reasoning) -- resolution is a legal vote value, or 'exclude'. Any conflict NOT
    # covered fails the build loudly; rows are never silently dropped.
    LEGAL_VALUES = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}
    vote_ov = {}
    if os.path.exists(VOTE_OVERRIDES):
        for r in csv.DictReader(open(VOTE_OVERRIDES)):
            vote_ov[(r["source_file"], r["motion_no"],
                     person_key(norm_person(r["member"])))] = r["resolution"].strip()
    n_csv_rows = n_inserted = n_merged = n_excluded = n_no_person = 0
    conflicts_unresolved = []
    for (src, mno), vs in vbym.items():
        by_person = {}
        for nm, vv in vs:
            n_csv_rows += 1
            p = pers(nm)
            if p is None:
                n_no_person += 1; continue
            by_person.setdefault((p, nm), []).append(vv)
        for (p, nm), vals in by_person.items():
            distinct = sorted(set(vals))
            if len(distinct) == 1:
                vv = distinct[0]
                n_merged += len(vals) - 1     # identical duplicates collapse silently
            else:
                res = vote_ov.get((src, str(mno), person_key(nm)))
                if res is None:
                    conflicts_unresolved.append((src, mno, nm, distinct)); continue
                if res.lower() == "exclude":
                    n_excluded += len(vals); continue
                if res not in LEGAL_VALUES:
                    sys.exit(f"BUILD FAILED: vote_overrides.csv resolution {res!r} is not "
                             f"a legal vote value (or 'exclude') for {nm} on {src} "
                             f"motion {mno}")
                vv = res
                n_merged += len(vals) - 1
            cur.execute("INSERT INTO vote(motion_id,person_id,vote_value) VALUES(?,?,?)",
                        (mid[(src, mno)], p, vv))
            n_inserted += 1
    if conflicts_unresolved:
        for src, mno, nm, distinct in conflicts_unresolved:
            print(f"UNRESOLVED VOTE CONFLICT: {src} motion {mno} {nm}: "
                  f"{'+'.join(distinct)}", file=sys.stderr)
        sys.exit(f"BUILD FAILED: {len(conflicts_unresolved)} contradictory (motion, "
                 f"person) vote pair(s) not covered by db/vote_overrides.csv -- add "
                 f"documented resolutions (a legal vote value or 'exclude').")
    print(f"  vote reconciliation: {n_csv_rows} named CSV rows = {n_inserted} inserted "
          f"+ {n_merged} merged (duplicate/override pairs) + {n_excluded} excluded "
          f"(override) + {n_no_person} unresolvable person")
    cur.execute("""INSERT INTO role(person_id,body_id,first_seen,last_seen,n_votes)
                   SELECT v.person_id, mo.body_id, MIN(m.meeting_date), MAX(m.meeting_date), COUNT(*)
                   FROM vote v JOIN motion mo ON mo.motion_id=v.motion_id JOIN meeting m ON m.meeting_id=mo.meeting_id
                   GROUP BY v.person_id, mo.body_id""")
    _std = load_motion_std(cur, REPO)
    for _ds, (_n, _m) in sorted(_std.items()):
        print(f"  motion_std [{_ds}]: {_n} rows, {_m} joined to motion"
              + ("" if _m == _n else f"  \u26a0 {_n - _m} UNMATCHED"))
    con.executescript(VIEWS); con.executescript(V_CONTESTED_DDL); con.commit()

    problems = []
    if cur.execute("PRAGMA foreign_key_check").fetchall(): problems.append("FK violations")
    if cur.execute("SELECT COUNT(*) FROM motion").fetchone()[0] != len(motions): problems.append("motion count drift")
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
    os.makedirs(TABLES, exist_ok=True)
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        rows = cur.execute(f"SELECT * FROM {t}").fetchall(); cols = [d[0] for d in cur.description]
        with open(os.path.join(TABLES, t + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    def n(t): return cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"== built {os.path.relpath(DB, REPO)} from {len(present)} source(s) ==")
    for t in ("body","person","meeting","application","motion","vote","role"): print(f"  {t:12} {n(t)}")
    nullc = cur.execute("SELECT COUNT(*) FROM motion WHERE application_id IS NULL").fetchone()[0]
    print("  by method:", dict(cur.execute("SELECT app_match_method,COUNT(*) FROM motion WHERE application_id IS NOT NULL GROUP BY 1")),
          "| NULL/non-land-use:", nullc)
    print("  bodies:", dict(cur.execute("SELECT name,COUNT(*) FROM motion JOIN body USING(body_id) GROUP BY 1")))
    span = cur.execute("SELECT COUNT(*) FROM (SELECT application_id FROM motion WHERE application_id IS NOT NULL GROUP BY application_id HAVING COUNT(DISTINCT body_id)>1)").fetchone()[0]
    print(f"  apps spanning >1 body (must be 0): {span}")
    print("  disposition:", dict(cur.execute("SELECT COALESCE(disposition,'(null)'),COUNT(*) FROM motion GROUP BY 1 ORDER BY 2 DESC")))
    # CROSS-CHECK (informational, non-fatal): for PC recommendation motions, disposition
    # composed with carriage — approve+Pass / deny+Fail -> Positive; deny+Pass / approve+Fail
    # -> Negative — should equal the legacy `recommendation` field. Mismatches are NOT
    # disposition errors: they expose that `recommendation_of` keyword-matches direction
    # WITHOUT reliably composing with the outcome (the same bug class fixed in outcome_of),
    # so it mislabels failed/tied recs. disposition (proposed action) + outcome (carriage) are
    # the correct, separable primitives; the composed legacy field is the unreliable one.
    # Surfaced for review, not a build failure. See TODO (reconcile `recommendation`).
    rec_rows = cur.execute("""SELECT disposition, outcome, recommendation FROM motion
                              WHERE stage='pc_recommendation' AND recommendation IS NOT NULL
                              AND disposition IN ('approve','deny')""").fetchall()
    mism = [(d, o, rc) for d, o, rc in rec_rows if _compose_dir(d, o) != rc]
    print(f"  disposition vs legacy recommendation: {len(rec_rows)-len(mism)}/{len(rec_rows)} agree"
          + (f" -- {len(mism)} legacy-recommendation inconsistencies (review, not disposition errors)" if mism else ""))
    print("  INTEGRITY:", "OK" if not problems else problems)
    con.close(); return 0 if not problems else 1

if __name__ == "__main__":
    sys.exit(main())
