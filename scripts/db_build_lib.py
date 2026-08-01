#!/usr/bin/env python3
"""
db_build_lib.py — the SHARED within-body exact core for per-city db builds
(REFACTOR_PLAN 4.3). Formerly 10 copy-pasted per-city db/build_db.py files
(6 × 347-line + 4 × 397-line — the two differed ONLY by the fail-loud
vote-override reconciliation block, which is now standard for all callers).

Per-city db/build_db.py is a thin driver:  from db_build_lib import main; main(HERE).
The six genuinely divergent cities (slc, sandy, park_city, south_jordan, millcreek,
taylorsville) keep their own forks — each documents its delta in its header.

VENDOR-AGNOSTIC TEMPLATE for PDF/prose portals (CivicClerk, Granicus, Revize,
CivicPlus, PrimeGov-PDF, OnBase). It consumes the per-body denormalized vote CSVs
(meeting_minutes/all_votes.csv + planning_commission/all_votes.csv, both the standard
13-col schema) and produces a normalized SQLite DB (body/person/meeting/application/
motion/vote/role). Run db/build_referrals.py AFTER this for the reconstructed
cross-body PC->Council referral layer.

TWO LAYERS, NEVER CONFLATED: the project `application_id` is resolved WITHIN EACH BODY
(body-scoped) — a Council "Foo" and a PC "Foo" are DISTINCT applications here; the
cross-body tie lives ONLY in the separate `referral` table.

Resolution tiers (recorded on every motion as app_match_method + app_confidence):
  override (high)  — db/overrides.csv row forces it (source_file,motion_no,app_key)
  name     (medium)— a named development/annexation/rezone grouped by normalized name
  singleton(high)  — unnamed land-use/policy motion -> its own application
  (NULL)           — non-land-use motion -> no application

Vote-conflict resolution (REMEDIATION_PLAN 3.1; park_city pattern): identical
duplicate (motion, person) rows merge; CONTRADICTORY pairs MUST have a documented
resolution in db/vote_overrides.csv — any uncovered conflict fails the build loudly.

Idempotent. Run per city:  python3 db/build_db.py
"""
import csv, glob, os, re, sqlite3, sys

# --------------------------------------------------------- body kind (keyword-based, vendor-agnostic)
def kind_of(name):
    n = (name or "").lower()
    if "planning" in n or ("commission" in n and "redevelop" not in n): return "commission"
    if "adjust" in n or "appeal" in n or n.strip() in ("boa",): return "commission"
    if any(k in n for k in ("redevelop", "reinvest", "rda", "cra", "agency")): return "agency"
    if any(k in n for k in ("building authority", "mba", "lba", "housing", "ha")): return "agency"
    if "board" in n or "committee" in n: return "committee"
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
    # No-vote/no-result rows: outcome is honestly unknown, never a default Pass.
    # Exact-string matches, each verified unique to its emitter (2026-07-12):
    #   alta  "RECORDED (no vote line)" — deferred/restated motions; the operative vote
    #         lives on the restated/called-question row (T3.1(a))
    #   magna "No result recorded" — a seconded motion whose minutes print no result
    #         sentence (T3.1(e); e.g. the 2023-11-14 fee-schedule hearing motion)
    #   st_george "Withdrawn (no vote)" / "No vote recorded (superseded)" — motions
    #         withdrawn or superseded by a restated sibling before any vote (T3.1(i))
    if r.strip() in ("recorded (no vote line)", "no result recorded",
                     "withdrawn (no vote)", "no vote recorded (superseded)"): return None
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
_REC_STRONG_NEG_RE = re.compile(
    # v2.3: STRONG denial phrasings — unambiguous direction of the motion itself
    r"recommend\w*\s+(?:a\s+|of\s+|the\s+)?(?:decision\s+to\s+)?(?:denial|deny\b)"
    r"|recommend\w*\s+to\s+(?:the\s+\w[\w ]*?council\s+to\s+)?(?:deny|reject)\b"
    r"|denial\s+recommendation"
    r"|\bfor\s+denial\b"
    r"|^\s*(?:to\s+)?deny\b"
    r"|\bmo(?:ve[ds]?|tion(?:ed)?)\s+(?:that\s+we\s+)?(?:to\s+)?deny\b"
    r"|recommend\w*\s+against"
    r"|unfavorable\s+recommendation", re.I)
# WEAK negation — "not (be) approve(d)" also appears in condition carve-outs and
# quoted discussion, so it fires only AFTER the positive checks (v2.3)
_REC_WEAK_NEG_RE = re.compile(r"not\s+(?:be\s+)?approv", re.I)
_REC_APPROVE_INITIAL_RE = re.compile(r"^\s*(?:to\s+)?approve\b", re.I)


def recommendation_of(body, res, title):
    """Direction of a PC recommendation motion — an INDEPENDENT keyword derivation
    that serves as the validation oracle against _compose_dir(disposition, outcome).

    v2 (2026-08-01, DEBT '56-row recommendation-oracle' adjudication):
    - The RESULT string's explicit label ('Negative recommendation 8:1') is checked
      FIRST and alone — it names what the body actually did and must not be
      overridden by direction words in the agenda TITLE (the provo/slc class where
      motion text is the APPLICANT's request wording).
    - Denial phrasings tightened to _REC_NEG_RE: the old ("deny" in s) token never
      matched 'denial'/'recommendation of denial' (the herriman/murray/south_jordan
      Positive-on-a-denial class) while the loose ('deny' AND 'recommend') clause
      false-fired on agenda titles mentioning a previously-denied application
      (the logan/park_city flips).
    - Callers gate the returned direction on the motion CARRYING (outcome=='Pass'):
      a failed/died/continued rec motion produced NO recommendation — orem's own
      minutes convention ('a 3:2/3:3 forward is no recommendation') generalized.
    """
    if not is_pc(body): return None
    r = (res or "").lower()
    t = (title or "").lower()
    # v2.1 precedence (2026-08-01): an EXPLICIT direction in the MOTION TEXT rules
    # first (the motion sentence names what was moved; orem/millcreek result labels
    # were derived-wrong against their own motion text); the RESULT label rules
    # where the motion text carries no explicit direction (the provo class, whose
    # motion text is the applicant's request wording); bare tokens come last.
    if "neutral recommendation" in t or "forwarded neutral" in t: return None
    # dual-direction motions ("positive rec for X AND negative rec for Y" —
    # park_city/slc): the clerk's RESULT label rules; skip the text path.
    if not ("positive recommendation" in t and "negative recommendation" in t):
        # v2.3 precedence: strong denial > approve-initial motion > explicit
        # positive > weak negation ("not approved" also lives in condition
        # carve-outs and quoted discussion — EC/herriman/st_george classes)
        if _REC_STRONG_NEG_RE.search(t) or "negative recommendation" in t:
            return "Negative"
        if _REC_APPROVE_INITIAL_RE.search(t): return "Positive"
        if ("positive recommendation" in t or "recommendation of approval" in t
                or "recommend approval" in t): return "Positive"
        # weak negation ranks BELOW the result label (v2.3.1): quoted-discussion
        # "not approved" text must not beat an explicit 'Positive recommendation
        # N:M' label (the st_george class) — it fires only in the final s-path
    if "neutral recommendation" in r or "forwarded neutral" in r: return None
    if "negative recommendation" in r: return "Negative"
    if "positive recommendation" in r: return "Positive"
    s = (r + " " + t)
    if _REC_STRONG_NEG_RE.search(s) or _REC_WEAK_NEG_RE.search(s): return "Negative"
    if "forward" in s or "recommend" in s:
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
def stage_of(body, res, title):
    if is_pc(body):
        s = ((res or "") + " " + (title or "")).lower()
        if "final action" in (res or "").lower(): return "pc_final_action"
        return "pc_recommendation" if "recommend" in s or "forward" in s else "pc_final_action"
    n = (body or "").lower()
    if "adjust" in n or "appeal" in n or n.strip() == "boa": return "boa_action"
    if kind_of(body) == "agency":
        if "housing" in n or n.strip() == "ha": return "ha_vote"
        if any(x in n for x in ("building authority","mba","lba")): return "mba_vote"
        return "rda_vote"
    if kind_of(body) == "council": return "council_vote"
    return "other_action"

# --------------------------------------------------------- read source motions
def read_motions(sources, repo):
    motions, votes, present = {}, [], []
    for path in sources:
        if not os.path.exists(path):
            print(f"  (skipping absent source: {os.path.relpath(path, repo)})"); continue
        present.append(path)
        for r in csv.DictReader(open(path)):
            key = (r["source"], r["motion_no"])
            if key not in motions:
                motions[key] = dict(date=r["date"], body=r["body"], title=r["title"],
                                    motion_no=int(r["motion_no"]), motion=r["motion"],
                                    motion_type=r.get("motion_type",""), result=r.get("result",""),
                                    mover=norm_person(r.get("mover")), seconder=norm_person(r.get("seconder")),
                                    source=r["source"], provenance=r.get("provenance") or "minutes")
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
  provenance TEXT NOT NULL DEFAULT 'minutes');
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

# --------------------------------------------------------- motion_std (2026-07-19)
# The SCHEMA_SPEC §8 normalization layer, loaded per city so v_contested can expose
# AUTHORITATIVE printed tallies alongside the named vote rows (the cities.db
# v_contested_all column shape — TODO "v_contested_all redefinition" follow-up (2)).
# Same 16 contract columns as cities.db's motion_std minus the `city` column
# (single-city db). Forks import MOTION_STD_DDL / load_motion_std / V_CONTESTED_DDL.
MOTION_STD_DDL = """
CREATE TABLE motion_std (
    dataset             TEXT NOT NULL CHECK (dataset IN
                            ('meeting_minutes','planning_commission')),
    source              TEXT NOT NULL,
    motion_no           INTEGER NOT NULL,
    date                TEXT NOT NULL,
    body                TEXT,
    motion_type_native  TEXT,
    motion_type_std     TEXT,
    land_use_type       TEXT,
    action_class        TEXT,
    outcome             TEXT,
    tally_aye           INTEGER,
    tally_nay           INTEGER,
    tally_other         INTEGER,
    vote_mode           TEXT,
    result_raw          TEXT,
    classify_method     TEXT,
    classify_confidence TEXT,
    motion_id           INTEGER REFERENCES motion(motion_id)  -- joined; NULL = unmatched
);
CREATE INDEX ix_std_motion ON motion_std(motion_id);
"""


def load_motion_std(cur, repo):
    """Load the city's (up to) two motions_std.csv files and join to motion.

    Join key: (source, motion_no, date) against motion.source_file + motion_no +
    meeting.meeting_date; falls back to (source, motion_no) where that pair is
    unique on both sides — mirrors scripts/build_cities_db.load_motion_std (the
    date key is primary because sandy PC's constant Legistar-staging `source`
    makes the 2-key degenerate). Returns {dataset: (n_rows, n_matched)}."""
    key3, key2 = {}, {}
    for mid_, src, mno, mdate in cur.execute(
            "SELECT m.motion_id, m.source_file, m.motion_no, mt.meeting_date "
            "FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id"):
        key3[(src, mno, mdate)] = mid_
        key2.setdefault((src, mno), []).append(mid_)
    stats = {}
    for dataset in ("meeting_minutes", "planning_commission"):
        path = os.path.join(repo, dataset, "motions_std.csv")
        if not os.path.exists(path):
            continue
        n = matched = 0
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                n += 1
                mno = int(r["motion_no"])
                mid_ = key3.get((r["source"], mno, r["date"]))
                if mid_ is None:            # date-mismatch fallback: unique 2-key
                    cands = key2.get((r["source"], mno), [])
                    if len(cands) == 1:
                        mid_ = cands[0]
                if mid_ is not None:
                    matched += 1
                rows.append((
                    dataset, r["source"], mno, r["date"], r["body"],
                    r["motion_type_native"], r["motion_type_std"],
                    r["land_use_type"], r["action_class"], r["outcome"],
                    int(r["tally_aye"]) if r["tally_aye"] else None,
                    int(r["tally_nay"]) if r["tally_nay"] else None,
                    int(r["tally_other"]) if r["tally_other"] else None,
                    r["vote_mode"], r["result_raw"], r["classify_method"],
                    r["classify_confidence"], mid_))
        cur.executemany(
            "INSERT INTO motion_std VALUES (" + ",".join("?" * 18) + ")", rows)
        stats[dataset] = (n, matched)
    return stats


# v_contested — cities.db v_contested_all COLUMN SHAPE, per-city MEMBERSHIP
# (2026-07-19, TODO "v_contested_all redefinition" follow-up (2)). Membership is
# UNCHANGED: a motion is contested here iff a dissent was NAMED (a Nay/Abstain/
# Recuse vote row) — the per-city dbs stay attribution-anchored; the tally-dissent
# UNION lives only in cities.db v_contested_all. What changed is the COLUMNS:
#   MARGINS: tally_aye/tally_nay/tally_other — authoritative from motion_std
#   (printed tallies), falling back to the named counts only where no std tally
#   exists. tally_other is NULL-encoded upstream (a bare "A:N" source prints no
#   third number; the vote ROW is the authority for abstentions), so the COALESCE
#   correctly supplies the named abstain/recuse count — see normalize_motions.py.
#   ATTRIBUTION: named_ayes/named_nays/named_abstains/named_recuses are who was
#   actually NAMED; they UNDERCOUNT in dissent-only/tally-only cities. Never read
#   named_* as the margin.
V_CONTESTED_DDL = """
CREATE VIEW v_contested AS
SELECT m.meeting_date, b.name AS body, mo.stage, mo.motion_type, mo.outcome, mo.result_raw,
       a.name AS project, mo.motion_text, mo.motion_id,
       mo.motion_no, mo.provenance,
       ms.motion_type_std, ms.land_use_type, ms.vote_mode,
       COALESCE(ms.tally_aye,   SUM(v.vote_value = 'Aye'))                 AS tally_aye,
       COALESCE(ms.tally_nay,   SUM(v.vote_value = 'Nay'))                 AS tally_nay,
       COALESCE(ms.tally_other, SUM(v.vote_value IN ('Abstain','Recuse'))) AS tally_other,
       SUM(v.vote_value = 'Aye')     AS named_ayes,
       SUM(v.vote_value = 'Nay')     AS named_nays,
       SUM(v.vote_value = 'Abstain') AS named_abstains,
       SUM(v.vote_value = 'Recuse')  AS named_recuses
FROM motion mo JOIN meeting m ON m.meeting_id=mo.meeting_id JOIN body b ON b.body_id=mo.body_id
  LEFT JOIN application a ON a.application_id=mo.application_id
  JOIN vote v ON v.motion_id=mo.motion_id
  LEFT JOIN motion_std ms ON ms.motion_id=mo.motion_id
GROUP BY mo.motion_id
HAVING SUM(v.vote_value IN ('Nay','Abstain','Recuse')) > 0;
"""

# Variant for the forks whose motion table carries NO `provenance` column
# (millcreek / park_city / taylorsville / sandy — their flat all_votes.csv have no
# provenance column either: single-channel audited corpora, sandy PC being the
# Legistar API). NULL is the honest value there (provenance not tracked at this
# layer), never a hardcoded 'minutes'.
V_CONTESTED_DDL_NO_PROVENANCE = V_CONTESTED_DDL.replace(
    "mo.motion_no, mo.provenance,", "mo.motion_no, NULL AS provenance,")
assert V_CONTESTED_DDL_NO_PROVENANCE != V_CONTESTED_DDL
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
"""
# NB v_contested moved to V_CONTESTED_DDL above (2026-07-19 column-shape change) —
# executed alongside VIEWS in main(); forks import it.

def main(here):
    """Build the city's db. `here` = the city's db/ directory (the caller's location)."""
    repo = os.path.dirname(here)
    _existing = sorted(glob.glob(os.path.join(here, "*.db")))   # reuse an existing db name; else civic.db
    db = _existing[0] if _existing else os.path.join(here, "civic.db")
    tables = os.path.join(here, "tables")
    overrides = os.path.join(here, "overrides.csv")
    vote_overrides = os.path.join(here, "vote_overrides.csv")
    disp_overrides = os.path.join(here, "disposition_overrides.csv")
    sources = [os.path.join(repo, "meeting_minutes", "all_votes.csv"),
               os.path.join(repo, "planning_commission", "all_votes.csv")]

    motions, votes, present = read_motions(sources, repo)
    if not motions: print("no source motions found", file=sys.stderr); return 1
    ov = {}
    if os.path.exists(overrides):
        for r in csv.DictReader(open(overrides)):
            ov[(r["source_file"], r["motion_no"])] = r["app_key"].strip()
    disp_ov = {}   # db/disposition_overrides.csv: source_file,motion_no,disposition,note
    if os.path.exists(disp_overrides):
        for r in csv.DictReader(open(disp_overrides)):
            disp_ov[(r["source_file"], r["motion_no"])] = r["disposition"].strip()
    if os.path.exists(db): os.remove(db)
    con = sqlite3.connect(db); con.executescript(DDL); con.executescript(MOTION_STD_DDL)
    cur = con.cursor()

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
                     # a recommendation exists only if the rec motion CARRIED (v2 gate)
                     (recommendation_of(body, m["result"], title)
                      if outcome_of(m["result"], disp) == "Pass" else None),
                     disp, dmeth, dconf, app_id, method, conf,
                     pers(m["mover"]), pers(m["seconder"]), 1 if mvotes else 0, src, m["provenance"]))
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
    vote_ov, vote_ov_rows = {}, {}
    if os.path.exists(vote_overrides):
        for r in csv.DictReader(open(vote_overrides)):
            k = (r["source_file"], r["motion_no"], person_key(norm_person(r["member"])))
            vote_ov[k] = r["resolution"].strip()
            vote_ov_rows[k] = r
    ov_consumed = set()
    n_csv_rows = n_inserted = n_merged = n_excluded = n_no_person = n_added = 0
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
                ov_consumed.add((src, str(mno), person_key(nm)))
                if res.lower() == "exclude":
                    n_excluded += len(vals); continue
                if res not in LEGAL_VALUES:
                    sys.exit(f"BUILD FAILED: vote_overrides.csv resolution {res!r} is not "
                             f"a legal vote value (or 'exclude') for {nm} on {src} "
                             f"motion {mno}")
                vv = res
                n_merged += len(vals) - 1
            # Normalize the documented mayor-tie-break annotation (park_city / riverton:
            # "Aye (Mayor tie-break)" / "Nay (Mayor tie-break)") to its base vote value —
            # the flat all_votes.csv keeps the verbatim annotated value (city-faithful);
            # the db vote_value is the normalized form (the annotation is recoverable from
            # the CSV / result string).
            if vv.endswith(" (Mayor tie-break)"):
                vv = vv[:-len(" (Mayor tie-break)")]
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
    # ---- ADD-MEMBER overrides (2026-07-17 wave follow-up (a)) --------------------
    # An override row NOT consumed by the conflict loop is either (a) an ADD-MEMBER
    # row — the source printed a garbled/unparseable value the audited extractor
    # honestly left unrecorded, so the flat CSV has NO row for that (motion, member);
    # the documented resolution supplies the corrected value for the relational db
    # (SSL Huff 'Ye'/'Y/es' pattern) — or (b) STALE (key typo, member already has a
    # clean recorded value): fail loudly, never silently ignore a documented override.
    mid_str = {(s, str(n)): v for (s, n), v in mid.items()}
    for k, res in vote_ov.items():
        if k in ov_consumed:
            continue
        src, mno, pk = k
        r = vote_ov_rows[k]
        nm = norm_person(r["member"])
        if (src, mno) not in mid_str:
            sys.exit(f"BUILD FAILED: vote_overrides.csv row for {nm} references "
                     f"unknown motion ({src!r}, motion {mno}) -- stale key.")
        if res.lower() == "exclude":
            sys.exit(f"BUILD FAILED: vote_overrides.csv 'exclude' row for {nm} on "
                     f"{src} motion {mno} matched no contradictory CSV pair -- "
                     f"there is nothing to exclude (stale row).")
        if res not in LEGAL_VALUES:
            sys.exit(f"BUILD FAILED: vote_overrides.csv resolution {res!r} is not "
                     f"a legal vote value (or 'exclude') for {nm} on {src} "
                     f"motion {mno}")
        # person's existing CSV rows for this motion (vbym keys carry the native mno type)
        vb_key = next(((s2, n2) for (s2, n2) in vbym
                       if s2 == src and str(n2) == mno), None)
        existing = [vv for vnm, vv in vbym.get(vb_key, []) if person_key(vnm) == pk] if vb_key else []
        if existing:
            sys.exit(f"BUILD FAILED: vote_overrides.csv row for {nm} on {src} motion "
                     f"{mno} is neither a conflict resolution nor an add (the CSV "
                     f"already records {sorted(set(existing))!r} for this member) -- "
                     f"stale or mis-keyed row.")
        p = pers(nm)
        if p is None:
            pk_new = person_key(nm)
            cur.execute("INSERT INTO person(full_name,name_key) VALUES(?,?)", (nm, pk_new))
            pid[pk_new] = cur.lastrowid; p = pid[pk_new]
        cur.execute("INSERT INTO vote(motion_id,person_id,vote_value) VALUES(?,?,?)",
                    (mid_str[(src, mno)], p, res))
        n_added += 1
    print(f"  vote reconciliation: {n_csv_rows} named CSV rows = {n_inserted} inserted "
          f"+ {n_merged} merged (duplicate/override pairs) + {n_excluded} excluded "
          f"(override) + {n_no_person} unresolvable person"
          + (f"; +{n_added} added by override (missing-member)" if n_added else ""))
    cur.execute("""INSERT INTO role(person_id,body_id,first_seen,last_seen,n_votes)
                   SELECT v.person_id, mo.body_id, MIN(m.meeting_date), MAX(m.meeting_date), COUNT(*)
                   FROM vote v JOIN motion mo ON mo.motion_id=v.motion_id JOIN meeting m ON m.meeting_id=mo.meeting_id
                   GROUP BY v.person_id, mo.body_id""")
    std_stats = load_motion_std(cur, repo)
    for ds, (n_, m_) in sorted(std_stats.items()):
        print(f"  motion_std [{ds}]: {n_} rows, {m_} joined to motion"
              + ("" if m_ == n_ else f"  ⚠ {n_ - m_} UNMATCHED"))
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
    # LINT (informational, T3.1(m) 2026-07-12): IMPOSSIBLE tallies — aye+nay larger than
    # the body's maximum observed roll means a double-counted contradictory roll line
    # (e.g. ogden's full-roster AYE template + a named NO line; resolve the member rows
    # via db/vote_overrides.csv — the verbatim result string is left as printed).
    named_counts = dict(cur.execute("SELECT motion_id, COUNT(*) FROM vote GROUP BY motion_id"))
    impossible = []
    for mo_id, res in cur.execute("SELECT motion_id, result_raw FROM motion"):
        t = _TALLY_RE.search(_CLOCK_RE.sub(" ", res or ""))
        n = named_counts.get(mo_id, 0)
        # n >= 5 = a substantially-named roll (dissent-only cities are exempt); vote
        # rows include Absent/Abstain, so a tally larger than ALL rows is impossible
        if t and n >= 5 and int(t.group(1)) + int(t.group(2)) > n:
            impossible.append((mo_id, res))
    if impossible:
        print(f"  LINT: {len(impossible)} impossible tallies (aye+nay > the motion's own "
              f"roll rows — double-counted roll lines; member rows resolved via "
              f"vote_overrides): {impossible[:4]}")
    os.makedirs(tables, exist_ok=True)
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        rows = cur.execute(f"SELECT * FROM {t}").fetchall(); cols = [d[0] for d in cur.description]
        with open(os.path.join(tables, t + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    def n(t): return cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"== built {os.path.relpath(db, repo)} from {len(present)} source(s) ==")
    for t in ("body","person","meeting","application","motion","vote","role"): print(f"  {t:12} {n(t)}")
    nullc = cur.execute("SELECT COUNT(*) FROM motion WHERE application_id IS NULL").fetchone()[0]
    print("  by method:", dict(cur.execute("SELECT app_match_method,COUNT(*) FROM motion WHERE application_id IS NOT NULL GROUP BY 1")),
          "| NULL/non-land-use:", nullc)
    print("  bodies:", dict(cur.execute("SELECT name,COUNT(*) FROM motion JOIN body USING(body_id) GROUP BY 1")))
    span = cur.execute("SELECT COUNT(*) FROM (SELECT application_id FROM motion WHERE application_id IS NOT NULL GROUP BY application_id HAVING COUNT(DISTINCT body_id)>1)").fetchone()[0]
    print(f"  apps spanning >1 body (must be 0): {span}")
    print("  disposition:", dict(cur.execute("SELECT COALESCE(disposition,'(null)'),COUNT(*) FROM motion GROUP BY 1 ORDER BY 2 DESC")))
    # CROSS-CHECK (informational, non-fatal): for PC recommendation motions, disposition
    # composed with carriage (approve+Pass / deny+Fail -> Positive; deny+Pass / approve+Fail
    # -> Negative) should equal the legacy `recommendation` field. Mismatches are NOT
    # disposition errors: they expose that `recommendation_of` keyword-matches direction
    # WITHOUT reliably composing with the outcome (the same bug class fixed in outcome_of).
    # disposition (proposed action) + outcome (carriage) are the correct, separable primitives.
    # Surfaced for review, not a build failure. See TODO (reconcile `recommendation`).
    rec_rows = cur.execute("""SELECT disposition, outcome, recommendation FROM motion
                              WHERE stage='pc_recommendation' AND recommendation IS NOT NULL
                              AND disposition IN ('approve','deny')""").fetchall()
    mism = [(d, o, rc) for d, o, rc in rec_rows if _compose_dir(d, o) != rc]
    if rec_rows:
        print(f"  disposition vs legacy recommendation: {len(rec_rows)-len(mism)}/{len(rec_rows)} agree"
              + (f" -- {len(mism)} legacy-recommendation inconsistencies (review, not disposition errors)" if mism else ""))
    print("  INTEGRITY:", "OK" if not problems else problems)
    con.close(); return 0 if not problems else 1
