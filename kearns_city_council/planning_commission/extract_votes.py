#!/usr/bin/env python3
"""
extract_votes.py — Kearns City Council + CRA / Planning Commission vote extraction
(PURE deterministic — no LLM, no network; resumable).

Body is inferred from this file's directory:
  * meeting_minutes/   -> Council (+ CRA in-recess brackets, + Board of Canvassers)
  * planning_commission/ -> PlanningCommission

Kearns records NARRATIVE-TALLY votes (the collection's South-Jordan / Millcreek family):
  Council:  "Council Member Schaeffer moved to approve ... Council Member Butterfield
             seconded the motion; vote was 5-0, unanimous in favor."
            named dissent/abstain: "... with Council Member Colby abstaining from the vote."
  PC:       "Motion by: Commissioner Thomas / 2nd by: Commissioner Reynolds /
             Vote: Commissioners voted unanimously in favor"

So the MAJORITY is honestly UNNAMED (only mover + seconder are named). Every full-council
motion tallies out of **5** — 4 Council Members + the presiding officer, who VOTES in BOTH
eras (township Chair "Kelly Bush, Mayor" presided/voted; city Mayor Jesse Valdez presides/
votes). Named dissenters/abstainers ARE captured. This is TALLY-ONLY attribution, not a
per-member roll call: a unanimous motion emits ONE placeholder row (member/vote blank);
a motion with named dissent emits the named dissent rows.

CARDINAL RULE — never fabricate. Unnamed majority members are NEVER listed as individual
Ayes. Council names garbled by OCR are fuzzy-matched to the fixed 8-name roster; unresolved
-> BLANK. PC names (born-digital) are captured verbatim from the "Commissioner <Name>" role.

Outputs (millcreek-standard):
  votes/<year>/<week-monday>/<file>.json   (resumable intermediate; skip unless --force)
  all_votes.csv     13-col standard + documented trailing `provenance` column
                    ('minutes' = audited primary; 'pmn_minutes' = doc promoted from
                    ../pmn_backfill/, read from the md front-matter **Provenance:** line
                    — the ogden/vineyard/orem/south_jordan/herriman promotion pattern)
  roster.csv        observed members
"""
import os, re, csv, json, sys, glob, difflib
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
BODY = "PlanningCommission" if "planning_commission" in ROOT else "Council"
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# COUNCIL fixed roster (surname -> full name), observed across the 2025/2026
# township->city seam.  Township: Bush(Chair,presiding/voting), Snow(ViceChair),
# Peterson, Schaeffer, Butterfield.  City (Jan 2026+): Mayor Valdez(presiding/
# voting) + Schaeffer, Butterfield, Longtin, Colby.  Max full-council tally = 5.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "bush": "Kelly Bush",
    "snow": "Tina Snow",
    "peterson": "Alan Peterson",
    "schaeffer": "Patrick Schaeffer",
    "butterfield": "Chrystal Butterfield",
    "longtin": "Lyndsay Longtin",
    "colby": "Lorrin Colby Jr.",
    "valdez": "Jesse Valdez",
}
MAYORS = {"Kelly Bush", "Jesse Valdez"}  # presiding officers who vote
# OCR variants -> canonical surname key
SURNAME_ALIASES = {
    "scaheffer": "schaeffer", "schaefer": "schaeffer", "schaffer": "schaeffer",
    "butterfietd": "butterfield", "butterfeld": "butterfield", "ajtterfieta": "butterfield",
    "butterfield": "butterfield", "buiterfield": "butterfield",
    "vaidez": "valdez", "vatdez": "valdez", "jesses": "valdez",
    "longtín": "longtin", "tongtin": "longtin", "longtin": "longtin",
    "petersen": "peterson", "peterson": "peterson",
    "snovv": "snow", "colbv": "colby",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())

ROLE_WORDS = (r"Council\s*Members?|Councilmembers?|Council\s*Mem\w*|"
              r"Board\s*Members?|Commissioners?|Mayor|"
              r"Chair(?:man|person|woman)?|Vice[\s-]?Chair(?:man|person)?")
ROLEG = r"(?:" + ROLE_WORDS + r")"
NAME = r"([A-Z][A-Za-z'\-\.]{2,}(?:\s+[A-Z][A-Za-z'\-\.]{1,})?)"


def canon_council(token):
    """Map a council name fragment to the fixed roster (OCR-fuzzy), else None."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip().lower()
    words = [w for w in re.split(r"\s+", t) if len(w) >= 2]
    for w in reversed(words):
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    for w in reversed(words):
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.8)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


def canon_pc(token):
    """PC minutes are born-digital: keep the commissioner surname verbatim (Title
    case).  No fixed roster (the commission drifts 2019-2026); role word disambiguates."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip()
    words = [w for w in t.split() if len(w) >= 2 and w.lower() not in
             ("commissioner", "commissioners", "chair", "vice")]
    if not words:
        return None
    return words[-1].capitalize()   # surname


canon = canon_pc if BODY == "PlanningCommission" else canon_council


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories — millcreek/collection standard).
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|reorder|"
                 r"approve the agenda|work meeting|work session|closed session|"
                 r"closed meeting|executive session|\btable\b|continue|postpone|"
                 r"consent agenda)\b", t):
        return "Procedural/Administrative"
    if re.search(r"mayor pro tem|pro tempore", t):
        return "Appointment"
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|land-use|general plan|master plan|"
                 r"development agreement|overlay|site plan|street vacation|"
                 r"reinvestment (?:project )?area|project area|community reinvestment|"
                 r"redevelop|blight|planned (?:unit )?development|\boam\d|"
                 r"fee schedule|density", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"amending the \d{4}|tentative budget|final budget|adopt\w*.*budget|"
                 r"budget for|appropriat|certified tax|tax rate", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat|representative", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating", t):
        return "Ceremonial"
    return "Other"


# ---------------------------------------------------------------------------
# Tally digit normalization (OCR: S->5, O/Q->0, l/I->1 ...).
# ---------------------------------------------------------------------------
DIG = {"s": "5", "o": "0", "q": "0", "d": "0", "l": "1", "i": "1", "z": "2",
       "b": "8", "g": "6", "t": "1"}
def dfix(s):
    return "".join(DIG.get(c.lower(), c) for c in s)


# ===========================================================================
# COUNCIL extraction
# ===========================================================================
PRESENT_RE = re.compile(r"MEMBERS PRESENT:?(.*?)(?:STAFF|OTHERS|OTHER OFFICIALS|"
                        r"EXCUSED|ABSENT|PUBLIC|CALL TO ORDER|\bORDER OF BUSINESS)",
                        re.S | re.I)

def parse_present_council(flat):
    m = PRESENT_RE.search(flat)
    present = []
    if m:
        for sn in SURNAMES:
            if re.search(r"\b" + sn + r"\b", m.group(1), re.I):
                present.append(SURNAME_TO_FULL[sn])
    return present

# city-era: "<Name> moved to ..."
MOVE_C = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s+(?:moved|motioned|made\s+a\s+motion)", re.I)
# township-era struct: "<Mover>, seconded by <Seconder>, moved to ..."
STRUCT_C = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s*,\s*seconded\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"\s*,?\s*(?:moved|motioned|made\s+a\s+motion)", re.I)
SECOND_C = re.compile(
    r"seconded\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"|" + ROLEG + r"?\s*" + NAME + r"\s+seconded", re.I)
# tally: "vote was 5-0" (digits may be OCR-garbled single letters)
TALLY_C = re.compile(r"vote[^.]{0,15}?\b([0-9SsOoQlIiZBGt])\s*[-–to]{1,3}\s*"
                     r"([0-9SsOoQlIiZBGt])\b", re.I)
UNAN_C = re.compile(r"unanimous(?:ly)?(?:\s+in\s+favor)?|all\s+in\s+favor", re.I)
OUTCOME_C = re.compile(r"motion\s+(passed|carried|failed|did\s+not\s+(?:pass|carry))"
                       r"|(passed|carried|failed)\b", re.I)
LACK_SECOND = re.compile(r"(?:fail\w*|died)\s+(?:due\s+to|for)\s+(?:a\s+)?lack\s+of\s+"
                         r"a?\s*second|for\s+lack\s+of\s+(?:a\s+)?second|no\s+second", re.I)
# named dissent / abstain / recuse
DISSENT_C = re.compile(
    r"with\s+" + ROLEG + r"?\s*" + NAME +
    r"\s+(abstaining|opposed|opposing|dissenting|voting\s+(?:nay|no|against)|in\s+opposition)"
    r"|" + ROLEG + r"\s+" + NAME +
    r"\s+(abstained|recused|opposed|dissented|voted\s+(?:nay|no|against))", re.I)

CRA_OPEN = re.compile(r"(?:convened?|reconvened?|met|recess\w*)\s+(?:in)?to?\s*(?:the\s+)?"
                      r"(?:kearns\s+)?community\s+reinvestment\s+agency", re.I)
CRA_CLOSE = re.compile(r"(?:reconvened?|returned?|convened?)\s+as\s+the\s+"
                       r"(?:kearns\s+)?city\s+council", re.I)

def cra_spans(flat):
    spans, pos = [], 0
    while True:
        o = CRA_OPEN.search(flat, pos)
        if not o:
            break
        c = CRA_CLOSE.search(flat, o.end())
        end = c.start() if c else len(flat)
        spans.append((o.end(), end))
        pos = end
    return spans

def extract_council(flat, file_body):
    present = parse_present_council(flat)
    cra = cra_spans(flat)
    anchors = []
    for m in STRUCT_C.finditer(flat):     # township "X, seconded by Y, moved to ..."
        mover = canon(m.group(1)); seconder = canon(m.group(2))
        if mover:
            anchors.append((m.start(), m.end(), mover, seconder))
    for m in MOVE_C.finditer(flat):       # city "X moved to ..."
        mover = canon(m.group(1))
        if mover:
            anchors.append((m.start(), m.end(), mover, None))
    anchors.sort()
    # de-dup near-duplicate anchors (a struct match overlaps a bare-move match)
    dedup = []
    for a in anchors:
        if dedup and abs(a[0] - dedup[-1][0]) < 8:
            continue
        dedup.append(a)
    anchors = dedup
    votes = []
    for i, (astart, aend, mover, sec_known) in enumerate(anchors):
        nxt = anchors[i + 1][0] if i + 1 < len(anchors) else len(flat)
        region = flat[aend:nxt]
        # need an outcome (tally or unanimous or passed/failed) to be a real vote
        tally = TALLY_C.search(region[:600])
        unan = UNAN_C.search(region[:600])
        outc = OUTCOME_C.search(region[:600])
        if not (tally or unan or outc):
            continue
        end_out = min([x.end() for x in (tally, unan, outc) if x] + [600])
        if LACK_SECOND.search(region[:end_out + 40]):
            continue
        # seconder (known from a struct anchor, else search the region)
        seconder = sec_known
        sm = SECOND_C.search(region[:400])
        sec_end = 0
        if sm:
            if not seconder:
                seconder = canon(sm.group(1) or sm.group(2))
            sec_end = sm.end()
        # motion text: anchor .. first of (seconder-clause | tally | outcome)
        cut = min([x.start() for x in (SECOND_C.search(region), tally, unan, outc)
                   if x] + [len(region)])
        motion_text = clean_motion(region[:cut])
        if len(motion_text) < 3:
            motion_text = clean_motion(region[:180])
        # tally numbers
        ayes = nays = None
        if tally:
            ayes = int(dfix(tally.group(1)) or 0)
            nays = int(dfix(tally.group(2)) or 0)
        unanimous = bool(unan)
        # outcome word
        passed = True
        if outc:
            w = (outc.group(1) or outc.group(2) or "").lower()
            passed = not (w.startswith("fail") or w.startswith("did"))
        if nays is not None and ayes is not None:
            passed = ayes >= nays
        # named dissent
        abstain, nay_named, recuse = [], [], []
        for dm in DISSENT_C.finditer(region[:end_out + 120]):
            nm = canon(dm.group(1) or dm.group(3))
            act = (dm.group(2) or dm.group(4) or "").lower()
            if not nm:
                continue
            if "abstain" in act:
                abstain.append(nm)
            elif "recus" in act:
                recuse.append(nm)
            else:
                nay_named.append(nm)
        abstain = sorted(set(abstain)); nay_named = sorted(set(nay_named))
        recuse = sorted(set(recuse))
        # verbatim-ish result
        rstr = build_result_council(ayes, nays, unanimous, passed, abstain, nay_named, recuse)
        body = file_body
        for s, e in cra:
            if s <= astart < e:
                body = "CRA"
                break
        # present-count for tally-only (max seat check)
        pc = len(present) if present else None
        mayor_voted = bool(present and any(n in MAYORS for n in present))
        rec = {"motion": motion_text, "body": body,
               "motion_type": classify_motion(motion_text), "result": rstr,
               "mover": mover or "", "seconder": seconder or "",
               "names_recorded": False,
               "aye": [], "nay": nay_named, "abstain": abstain,
               "absent": [], "recuse": recuse,
               "mayor_voted": mayor_voted,
               "tally_only": {"unanimous": unanimous, "ayes": ayes, "nays": nays,
                              "present_count": pc}}
        votes.append(rec)
    return present, votes


def build_result_council(ayes, nays, unanimous, passed, abstain, nay_named, recuse):
    parts = []
    if ayes is not None:
        parts.append(f"{ayes}-{nays}")
    outcome = "Pass" if passed else "Fail"
    if unanimous:
        parts.append("unanimous in favor")
    parts.append(outcome)
    tail = []
    if abstain:
        tail.append("abstain: " + ", ".join(abstain))
    if nay_named:
        tail.append("nay: " + ", ".join(nay_named))
    if recuse:
        tail.append("recuse: " + ", ".join(recuse))
    s = " ".join(parts)
    if tail:
        s += " (" + "; ".join(tail) + ")"
    return s


# ===========================================================================
# PLANNING COMMISSION extraction
# ===========================================================================
# structured block
PC_STRUCT = re.compile(
    r"Motion(?:\s*:\s*(?P<mtext>.+?))?\s*"
    r"Motion\s+by:\s*(?:Commissioner\s+)?(?P<mover>[A-Z][A-Za-z'\-]+)\s*"
    r"2nd\s+by:\s*(?:Commissioner\s+)?(?P<sec>[A-Z][A-Za-z'\-]+)\s*"
    r"Vote:\s*(?P<vote>[^\n]{0,160})", re.S | re.I)
# inline "Commissioner X motioned to <...>, Commissioner Y seconded"
PC_INLINE = re.compile(
    r"Commissioner\s+([A-Z][A-Za-z'\-]+)\s+motioned\s+(to\s+.+?)[,;]\s*"
    r"Commissioner\s+([A-Z][A-Za-z'\-]+)\s+seconded", re.I)
PC_VOTE_LINE = re.compile(r"Vote:\s*([^\n]{0,160})", re.I)
OAM_RE = re.compile(r"OAM\s*\d{4}\s*-\s*\d{4,6}", re.I)

def pc_outcome(votetext):
    t = votetext.lower()
    unanimous = "unanimous" in t
    # NB: "Commissioner X did not vote" is an absence, not a motion failure
    failed = re.search(r"\bfail(?:ed|s)?\b|denied|motion\s+did\s+not|"
                       r"did\s+not\s+(?:pass|carry)", t)
    passed = not failed
    # named dissent: "with Commissioner X opposed/abstaining"
    nay, abstain = [], []
    for dm in re.finditer(r"commissioner\s+([A-Z][A-Za-z'\-]+)\s+"
                          r"(oppos\w+|abstain\w+|vot(?:ed|ing)\s+(?:nay|no|against)|dissent\w+)",
                          votetext, re.I):
        nm = dm.group(1).capitalize()
        if "abstain" in dm.group(2).lower():
            abstain.append(nm)
        else:
            nay.append(nm)
    # numeric tally e.g. "4-1" or "voted 4 to 1"
    ayes = nays = None
    mm = re.search(r"\b(\d+)\s*[-–]\s*(\d+)\b", votetext)
    if mm:
        ayes, nays = int(mm.group(1)), int(mm.group(2))
    return unanimous, passed, sorted(set(nay)), sorted(set(abstain)), ayes, nays

def extract_pc(flat):
    votes = []
    used = set()
    # structured motions first
    for m in PC_STRUCT.finditer(flat):
        mover = canon(m.group("mover"))
        seconder = canon(m.group("sec"))
        vt = m.group("vote") or ""
        # bound the vote text at the next agenda item / motion block — on flattened
        # text the 160-char window bleeds the NEXT item's title into the tally
        # ("...unanimous in favor 5) OAM2022-000724 - Drafted Phase 1-3 Ordinances"
        # read as a 1-3 tally -> false Fail; T3.1(f) 2026-07-12: m596/m598)
        vt = re.split(r"\s+\d{1,2}\)\s|\sMotion\s*:|\sMotion\s+by:", vt)[0]
        mtext = (m.group("mtext") or "").strip()
        # if no explicit "Motion:" text, grab the preceding agenda item line
        if len(re.sub(r"\W", "", mtext)) < 4:
            pre = flat[max(0, m.start() - 400):m.start()]
            mtext = agenda_subject(pre)
        oam = OAM_RE.search(flat[max(0, m.start()-500):m.end()+100])
        if oam and oam.group(0) not in mtext:
            mtext = (mtext + " [" + re.sub(r"\s+", "", oam.group(0)) + "]").strip()
        unanimous, passed, nay, abstain, ayes, nays = pc_outcome(vt)
        votes.append(pc_record(mtext, mover, seconder, vt, unanimous, passed,
                               nay, abstain, ayes, nays))
        used.add(m.start())
    # inline motions not already captured by a structured block nearby
    for m in PC_INLINE.finditer(flat):
        if any(abs(m.start() - u) < 300 for u in used):
            continue
        mover = canon(m.group(1)); seconder = canon(m.group(3))
        mtext = clean_motion(m.group(2))
        # find the following Vote: line
        vm = PC_VOTE_LINE.search(flat, m.end(), m.end() + 500)
        vt = vm.group(1) if vm else ""
        vt = re.split(r"\s+\d{1,2}\)\s|\sMotion\s*:|\sMotion\s+by:", vt)[0]
        oam = OAM_RE.search(flat[max(0, m.start()-400):m.end()+200])
        if oam and oam.group(0) not in mtext:
            mtext = (mtext + " [" + re.sub(r"\s+", "", oam.group(0)) + "]").strip()
        unanimous, passed, nay, abstain, ayes, nays = pc_outcome(vt)
        votes.append(pc_record(mtext, mover, seconder, vt, unanimous, passed,
                               nay, abstain, ayes, nays))
    return votes

def agenda_subject(pre):
    # last "N) Title. (...)" or "Motion: ..." fragment
    items = re.findall(r"\d+\)\s*(.+?)(?:\(Motion|\(Discussion|\.\s|$)", pre, re.S)
    if items:
        return clean_motion(items[-1])
    return clean_motion(pre[-160:])

def pc_record(mtext, mover, seconder, vt, unanimous, passed, nay, abstain, ayes, nays):
    outcome = "Pass" if passed else "Fail"
    rstr = (f"{ayes}-{nays} " if ayes is not None else "")
    rstr += ("unanimous in favor " if unanimous else "") + outcome
    tail = []
    if abstain: tail.append("abstain: " + ", ".join(abstain))
    if nay: tail.append("nay: " + ", ".join(nay))
    if tail: rstr += " (" + "; ".join(tail) + ")"
    return {"motion": mtext, "body": "PlanningCommission",
            "motion_type": classify_motion(mtext), "result": rstr.strip(),
            "mover": mover or "", "seconder": seconder or "",
            "names_recorded": False,
            "aye": [], "nay": nay, "abstain": abstain, "absent": [], "recuse": [],
            "mayor_voted": False,
            "tally_only": {"unanimous": unanimous, "ayes": ayes, "nays": nays,
                           "present_count": None}}


# ---------------------------------------------------------------------------
def clean_motion(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*,?\s*seconded\s+by\s+.*$", "", s, flags=re.I)
    s = re.sub(r"\s*" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+\s+seconded.*$", "", s, flags=re.I)
    s = re.sub(r"^(?:the\s+)?motion\s*:?\s*", "", s, flags=re.I)
    s = re.sub(r"^(?:to\s+)", "to ", s)
    s = s.strip(" .,;:—-")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


FOOTER_RE = re.compile(r"\x0c|Kearns\s+Planning\s+Commission\s*[–-].*?Page\s+\d+\s+of\s+\d+|"
                       r"Page\s+\d+\s+of\s+\d+", re.I)

def split_body(raw):
    parts = raw.split("\n\n---\n\n", 2)
    head = parts[1] if len(parts) > 2 else raw
    body = parts[2] if len(parts) > 2 else raw
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    return (bm.group(1) if bm else BODY), body

def week_monday(d):
    dt = date.fromisoformat(d)
    return (dt - timedelta(days=dt.weekday())).isoformat()

def json_path_for(rel_path, year):
    parts = rel_path.split("/")
    return os.path.join(VOTES_DIR, str(year), parts[-2], parts[-1].replace(".md", ".json"))

def extract_meeting(path, rel_source, d, year, title, file_body):
    raw = open(path, encoding="utf-8").read()
    pm = re.search(r"\*\*Provenance:\*\*\s*([\w-]+)", raw[:700])
    provenance = pm.group(1) if pm else "minutes"
    _bt, body = split_body(raw)
    flat = FOOTER_RE.sub(" ", body)
    flat = re.sub(r"[ \t]+", " ", flat)
    flat = re.sub(r"\s+", " ", flat)
    if BODY == "PlanningCommission":
        present = []
        votes = extract_pc(flat)
    else:
        present, votes = extract_council(flat, file_body)
    for n, v in enumerate(votes, 1):
        v2 = {"motion_no": n}; v2.update(v); votes[n - 1] = v2
    return {"date": d, "year": int(year), "title": title, "file_body": file_body,
            "present": present, "source": rel_source, "provenance": provenance,
            "votes": votes}


def file_body_of(path):
    head = open(path, encoding="utf-8").read(600)
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    return bm.group(1) if bm else BODY


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    for r in rows:
        path = os.path.join(ROOT, r["path"])
        if not os.path.exists(path):
            print("MISSING", r["path"], file=sys.stderr); continue
        jp = json_path_for(r["path"], r["year"])
        if os.path.exists(jp) and not FORCE:
            continue
        try:
            meeting = extract_meeting(path, r["path"], r["date"], r["year"],
                                      r["title"], file_body_of(path))
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr); continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        json.dump(meeting, open(jp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    rebuild_csv(rows)
    build_roster(rows)
    print("done", BODY)


def rebuild_csv(rows):
    # 13-col standard + documented trailing `provenance` column (stale-JSON safe:
    # pre-promotion JSONs lack the key -> 'minutes', the audited default)
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        for v in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=obj["title"],
                        body=v["body"], motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v.get("mover", ""), seconder=v.get("seconder", ""),
                        source=obj["source"],
                        provenance=obj.get("provenance") or "minutes")
            emitted = False
            for key, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                             ("absent", "Absent"), ("recuse", "Recuse")):
                for mem in v.get(key, []):
                    row = dict(base); row["member"] = mem; row["vote"] = lab
                    out.append(row); emitted = True
            if not emitted:
                row = dict(base); row["member"] = ""; row["vote"] = ""
                out.append(row)
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for row in out:
            w.writerow({k: row.get(k, "") for k in cols})
    return len(out)


def build_roster(rows):
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        d = obj["date"]
        people = set(obj.get("present", []))
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k):
                    people.add(v[k])
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                people.update(v.get(k, []))
        for p in people:
            if not p:
                continue
            dd = seen.setdefault(p, {"first": d, "last": d, "n": 0})
            dd["first"] = min(dd["first"], d); dd["last"] = max(dd["last"], d)
            dd["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        role = {}
        if BODY == "Council":
            role = {"Kelly Bush": "Chair/Mayor (township)", "Tina Snow": "Vice Chair (township)",
                    "Alan Peterson": "Council (township)",
                    "Patrick Schaeffer": "Council", "Chrystal Butterfield": "Council",
                    "Lyndsay Longtin": "Council (city)", "Lorrin Colby Jr.": "Council (city)",
                    "Jesse Valdez": "Mayor (city)"}
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            dd = seen[nm]
            w.writerow([nm, role.get(nm, ""), dd["first"], dd["last"], dd["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
