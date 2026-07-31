#!/usr/bin/env python3
"""
extract_votes.py — Ogden City Council vote extractor.

Reads minutes markdown under meeting_minutes/minutes/<year>/<week>/<date>_<slug>.md,
extracts recorded motions + roll-call votes, emits one JSON per meeting under
meeting_minutes/votes/<year>/<week>/<date>_<slug>.json, then rebuilds all_votes.csv
(long format, one row per member-vote, WITH `body`).

Design notes (Ogden specifics):
- Council = 4 districts + 3 at-large = 7 voting seats. The MAYOR DOES NOT VOTE
  (strong-mayor). BUT: in 2020-2023 the people who later became Mayor (Caldwell,
  Nadolski) were sometimes COUNCIL members/chairs and DID vote in that capacity.
  So we exclude the mayor *for the year they hold the mayoralty* via the roster,
  not by name globally.
- Vote phrasings handled:
    * Inline tally: "...ALL VOTING AYE" / "...ALL VOTED AYE" (no names) -> names_recorded False
    * Named roll-call: "VOTING AYE - COUNCIL MEMBERS A, B... VICE CHAIR X, AND CHAIR Y.
      VOTING NO - NONE." (also BOARD MEMBERS / AGENCY for RDA/MBA)
    * "VOTED IN FAVOR" inline name lists
- body tagged from slug (redevelopment-agency->RDA, municipal-building-authority->MBA),
  plus in-meeting "convened/reconvened as" transition markers (rare here).
- Some minutes are OCR'd (the 2022 compilation was a scan; re-OCR'd cleanly with
  tesseract 2026-07-02, but stray spaces / merged words (HY ER, CHAIRLOPEZ) can still
  occur in any OCR'd year). Name matching is space-insensitive + fuzzy on a known
  surname list.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # meeting_minutes/
MIN_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
OUT_CSV = ROOT / "all_votes.csv"

# ---------------------------------------------------------------------------
# Member roster.  Canonical full name -> set of surname/last-token spellings.
# Each member is voting in the years listed.  Mayor (non-voting) excluded per year.
# ---------------------------------------------------------------------------
# Known council/board surnames seen across the corpus (canonical -> display name).
SURNAMES = {
    "BLAIR":     "Bart E. Blair",
    "CHOBERKA":  "Angela Choberka",
    "GRAF":      "Dave Graf",
    "HYER":      "Richard A. Hyer",
    "LOPEZ":     "Lopez",          # disambiguated below (Luis vs Flor) by year
    "MYERS":     "Shaun Myers",
    "NADOLSKI":  "Ben Nadolski",
    "RICHEY":    "Ken Richey",
    "STEPHENS":  "Doug Stephens",
    "WHITE":     "Marcia L. White",
    "CALDWELL":  "Michael P. Caldwell",
    "GADI":      "Gadi Leshem",    # defensive; not expected
    # 2026 incomers
    "WASHINGTON":"Alicia Washington",
    "LUNDELL":   "Kevin Lundell",
    "SATOW":     "Heath Satow",
}

# Per-year voting roster (canonical display names).  The Mayor is EXCLUDED here.
# Sources: election_results + oath-of-office events in the minutes.
#  - Caldwell = Mayor 2020-2023 (non-voting).
#  - Nadolski: Council chair 2020-2023 (VOTING); Mayor from 2024-01-02 (non-voting).
#  - Lopez: "Luis Lopez" At-Large C, voting 2020-2023; "Flor Lopez" District 1 from 2026.
#  - Choberka: D1 2022-2025 (won 2021); Flor Lopez replaces her D1 in 2026.
#  - Graf, Myers sworn 2024-01-02. Stephens departs end of 2021.
ROSTER = {
    2020: {"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer",
           "Luis Lopez","Doug Stephens","Marcia L. White"},
    2021: {"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer",
           "Luis Lopez","Doug Stephens","Marcia L. White"},
    2022: {"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer",
           "Luis Lopez","Ken Richey","Marcia L. White"},
    2023: {"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer",
           "Luis Lopez","Ken Richey","Marcia L. White"},
    2024: {"Angela Choberka","Bart E. Blair","Dave Graf","Richard A. Hyer",
           "Shaun Myers","Ken Richey","Marcia L. White"},
    2025: {"Angela Choberka","Bart E. Blair","Dave Graf","Richard A. Hyer",
           "Shaun Myers","Ken Richey","Marcia L. White"},
    # 2026: White (At-Large A) and Blair (At-Large B) BOTH lost in the 2025 election;
    # replaced by Washington (A) and Lundell (B). Flor Lopez (D1) replaces Choberka.
    2026: {"Flor Lopez","Alicia Washington","Dave Graf","Richard A. Hyer",
           "Shaun Myers","Ken Richey","Kevin Lundell"},
}
# Mayor (non-voting) per year, for reference / sanity.
MAYOR = {2020:"Michael P. Caldwell",2021:"Michael P. Caldwell",2022:"Michael P. Caldwell",
         2023:"Michael P. Caldwell",2024:"Ben Nadolski",2025:"Ben Nadolski",2026:"Ben Nadolski"}

def resolve_lopez(year):
    return "Flor Lopez" if year >= 2026 else "Luis Lopez"

def canon_name(surname_token, year):
    """Map an (OCR-cleaned, uppercase, despaced) surname token to a roster display name."""
    s = re.sub(r"[^A-Z]", "", surname_token.upper())
    if not s:
        return None
    if s == "LOPEZ":
        return resolve_lopez(year)
    # exact
    if s in SURNAMES and s != "LOPEZ":
        return SURNAMES[s]
    # fuzzy: known surname is a subsequence-ish match (OCR drops/garbles a letter)
    best = None; bestscore = 0
    for key in SURNAMES:
        if key == "LOPEZ":
            continue
        score = _similar(s, key)
        if score > bestscore:
            bestscore, best = score, key
    if best and bestscore >= 0.74:
        return resolve_lopez(year) if best == "LOPEZ" else SURNAMES[best]
    return None

def _similar(a, b):
    # cheap ordered-overlap ratio
    if not a or not b:
        return 0.0
    # count matching chars in order
    i = j = m = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            m += 1; i += 1; j += 1
        elif len(a) - i > len(b) - j:
            i += 1
        else:
            j += 1
    return 2.0 * m / (len(a) + len(b))

# ---------------------------------------------------------------------------
# Motion typing
# ---------------------------------------------------------------------------
def motion_type(text):
    t = text.upper()
    if re.search(r"\bADJOURN", t) and "CLOSED SESSION" not in t:
        return "Procedural/Administrative"
    if "CLOSED SESSION" in t or "EXECUTIVE SESSION" in t:
        return "Procedural/Administrative"
    if re.search(r"PUBLIC HEARING (BE )?(CLOSED|OPEN)", t) or "CLOSE THE PUBLIC HEARING" in t:
        return "Public Hearing Action"
    if "APPROVE THE MINUTES" in t or "MINUTES AS PRESENTED" in t:
        return "Procedural/Administrative"
    if "BUDGET AMENDMENT" in t or "AMEND THE BUDGET" in t or "AMENDING THE BUDGET" in t:
        return "Budget Amendment"
    if "ORDINANCE" in t:
        if re.search(r"REZON|ZONING MAP|RECLASSIFY|R-1|R-2|VACAT|ANNEX|SUBDIVI|GENERAL PLAN|LAND USE|ZONE", t):
            return "Land-Use/Zoning"
        return "Ordinance"
    if re.search(r"REZON|ZONING MAP|RECLASSIFY|STREET VACATION|VACAT|ANNEX|CONDITIONAL USE|PLAT|SUBDIVISION|GENERAL PLAN", t):
        return "Land-Use/Zoning"
    if "RESOLUTION" in t:
        return "Resolution"
    if re.search(r"\bGRANT\b|FUNDING|CDBG|HOME FUNDS|AWARD", t):
        return "Grant-Funding"
    if "INTERLOCAL" in t or "COOPERATIVE AGREEMENT" in t:
        return "Interlocal"
    if re.search(r"APPOINT|REAPPOINT|RATIFY THE APPOINTMENT", t):
        return "Appointment"
    if re.search(r"CONTRACT|PURCHASE|AGREEMENT|BID|PROPOSAL|LEASE|CONVEY|SALE|ACQUI", t):
        return "Contract/Purchase"
    if re.search(r"PROCLAMATION|RECOGNI|CEREMON|HONOR", t):
        return "Ceremonial"
    if re.search(r"EXTEND|TABLE|CONTINUE|POSTPONE|RECESS|RECONVENE", t):
        return "Procedural/Administrative"
    return "Other"

# ---------------------------------------------------------------------------
# Agenda-subject enrichment (Phase 3.5, 2026-07-02)
#
# Ogden's adoption motions are terse formulas ("ORDINANCE WAS PASSED AND ADOPTED
# AS OGDEN CITY ORDINANCE 2021-34 AND ORDERED POSTED...") that never state the
# subject. The subject IS printed in the same minutes: every introduced
# ordinance/resolution gets a statutory long-title reading ("introduced in
# writing proposed Ordinance 2021-34, entitled: \"An ordinance of Ogden City...\"")
# and each item sits under a mixed-case agenda heading ("Proposed Ordinance
# 2021-34 amending ..."). For motions matching a bare adoption formula we look
# up that VERBATIM source text (long-title preferred, agenda heading fallback,
# matched by ordinance/resolution number, else nearest preceding introduction)
# and append it to the motion text inside an explicit delimiter:
#   ... [ENTITLED: "<verbatim long title>"]   or   [AGENDA ITEM: "<verbatim heading>"]
# NEVER a summary — only text copied from the document. The native motion_type
# is still computed from the bare motion sentence (clerk-faithful); the enriched
# text is what scripts/normalize_motions.py classifies.
# ---------------------------------------------------------------------------
_NUM = r"(\d[\d\s]{2,5}[-–—]\s*\d[\d\s]{0,2})"

ENTITLED_RX = re.compile(
    r"(?:Joint\s+)?(Ordinance|Resolution)\s*(?:No\.?\s*)?" + _NUM +
    r"[^\n,]{0,24}?,?\s*ent[i1l][tf]led\s*:?", re.I)

HEADING_RX = re.compile(
    r"(?m)^[ \t]{0,8}[)\]|_,.]{0,2}[ \t]{0,4}(?:Proposed|Consideration of proposed)\s+(?:Joint\s+)?"
    r"(Ordinance|Resolution)\s*" + _NUM)

ADOPTION_RXS = [
    re.compile(r"ADOPTED\s+AS\s+(?:OGDEN\s*CITY\s*)?(ORDINANCE|RESOLUTION)\s*" + _NUM, re.I),
    re.compile(r"(ORDINANCE|RESOLUTION)\s+" + _NUM + r"\s*(?:,?\s*AS\s+AMENDED\s*,?)?\s*WAS\s+(?:PASSED\s+AND\s+)?ADOPTED", re.I),
    re.compile(r"MOVED\s+(?:THE\s+)?(?:JOINT\s+)?(RESOLUTION|ORDINANCE)\s+"
               r"(?:" + _NUM + r"\s*)?(?:WITH\b[^.]{0,80}?)?BE\s+ADOPTED", re.I),
]

def _norm_ordnum(s):
    """Normalize an ordinance/resolution number for matching only (2022-07 == 2022-7)."""
    if not s:
        return None
    s = re.sub(r"\s+", "", s).replace("–", "-").replace("—", "-")
    if "-" in s:
        a, b = s.split("-", 1)
        b = b.lstrip("0") or "0"
        s = a + "-" + b
    return s

def _capture_longtitle(tail):
    """Capture the quoted long-title following an 'entitled:' marker, verbatim.
    Tolerates <=2 stray OCR junk chars before the opening quote ('entitled: i')."""
    m = re.match(r'([^"“”]{0,60}?)["“”]', tail)
    if m and len(m.group(1).strip()) > 2:
        m = None
    if m:
        body = tail[m.end():m.end() + 2500]
        q = re.search(r'["“”]', body)
        if q and q.start() >= 10:
            return body[:q.start()]
        # OCR dropped the closing quote: long titles end "...after final passage."
        e = re.search(r"(?:final\s+passage|upon\s+adoption)\s*\.", body, re.I)
        if e:
            return body[:e.end()]
        e = re.search(r"\n\s*\n", body[:1200])
        if e and e.start() >= 10:
            return body[:e.start()]
        return None
    # no opening quote at all (rare OCR loss)
    m2 = re.match(r"\s*((?:AN?\s+(?:ORDINANCE|RESOLUTION)|A\s+RESOLUTION)[\s\S]{10,2000}?)"
                  r'(?:\n\s*\n|["”])', tail, re.I)
    return m2.group(1) if m2 else None

def _clean_subject(s, cap=700):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > cap:
        cut = s.rfind(" ", 0, cap)
        s = s[:cut if cut > 200 else cap] + "…"
    return s

def scan_subjects(flat):
    """Pre-scan a flattened document. Returns (entitled, headings):
    each a list of (pos, kind, normalized_number_or_None, verbatim_text)."""
    ents, heads = [], []
    for m in ENTITLED_RX.finditer(flat):
        lt = _capture_longtitle(flat[m.end():m.end() + 2600])
        if lt:
            ents.append((m.start(), m.group(1).title(), _norm_ordnum(m.group(2)), _clean_subject(lt)))
    for m in HEADING_RX.finditer(flat):
        if "entitled" in flat[m.end():m.end() + 30].lower():
            continue  # that's an introduction line, already covered above
        # heading block: up to a blank line or a deeply-indented narrative line
        tail = flat[m.start():m.start() + 450]
        e = re.search(r"\n\s*\n|\n[ \t]{9,}\S", tail)
        htext = tail[:e.start()] if e else tail
        heads.append((m.start(), m.group(1).title(), _norm_ordnum(m.group(2)), _clean_subject(htext, 400)))
    return ents, heads

def adoption_ref(motion_text):
    """If the motion is a bare adoption formula, return (kind, normalized_num_or_None)."""
    for rx in ADOPTION_RXS:
        m = rx.search(motion_text)
        if m:
            return m.group(1).title(), _norm_ordnum(m.group(2))
    return None

def lookup_subject(ents, heads, kind, num, pos):
    """Return (verbatim_subject, tag) or (None, None). Prefer the long-title;
    match by number; else nearest preceding introduction of the same kind."""
    def pick(cands):
        prior = [e for e in cands if e[0] <= pos]
        return max(prior, key=lambda e: e[0]) if prior else min(cands, key=lambda e: e[0])
    if num:
        for pool, tag in ((ents, "ENTITLED"), (heads, "AGENDA ITEM")):
            cands = [e for e in pool if e[2] == num and e[1] == kind] or \
                    [e for e in pool if e[2] == num]
            if cands:
                return pick(cands)[3], tag
        return None, None
    for pool, tag in ((ents, "ENTITLED"), (heads, "AGENDA ITEM")):
        prior = [e for e in pool if e[0] <= pos and e[1] == kind]
        if prior:
            return max(prior, key=lambda e: e[0])[3], tag
    return None, None

# ---------------------------------------------------------------------------
# Vote-block parsing
# ---------------------------------------------------------------------------
ROLE_SPLIT = re.compile(r"COUNCIL\s*MEMBERS?|COUNCILMEMBERS?|BOARD\s*MEMBERS?|AGENCY\s*MEMBERS?|"
                        r"VICE\s*CHAIR|ACTING\s*CHAIR|CHAIR|MAYOR", re.I)

def extract_names_from_segment(seg, year):
    """Given an AYE or NO segment of a roll-call, return a list of roster display names."""
    if seg is None:
        return []
    up = seg.upper()
    if re.search(r"\bNONE\b", up):
        return []
    # Remove role words, then split on commas / AND / whitespace runs.
    # First insert separators around merged role words for OCR'd text.
    cleaned = ROLE_SPLIT.sub(" ", up)
    # split tokens
    tokens = re.split(r"[,\.;]|\bAND\b", cleaned)
    names = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        # a token may itself be several OCR-split fragments of ONE surname (HY ER)
        joined = re.sub(r"\s+", "", tok)
        nm = canon_name(joined, year)
        if nm and nm not in names:
            names.append(nm)
    return names

def parse_named_rollcall(block, year):
    """block: text containing 'VOTING AYE ... VOTING NO ...'. Returns (aye,nay) or None.
    Only fires for the *named roll-call* form (AYE list explicitly enumerates members,
    typically preceded by COUNCIL/BOARD MEMBERS). Bare 'ALL VOTING AYE' returns None so
    it falls through to the tally-only path."""
    # Must be the roll-call form: "VOTING AYE - COUNCIL MEMBERS ..." / "VOTING AYE: ..."
    # NOT "ALL VOTING AYE." Capture AYE and NO segments INDEPENDENTLY, each able to span line
    # breaks (`[\s\S]`), because the clerk wraps long member lists across lines and the NO list
    # routinely sits on its own line ("... CHAIR BLAIR.\nVOTING NO-\nNONE.").
    #  - AYE: from "VOTING AYE[-:]" up to the next "VOTING NO", a blank line, or end. The blank
    #    line bound keeps a trailing signature/approval block ("... Ogden City Mayor") from leaking.
    #  - NO:  from "VOTING NO[-:]" up to the FIRST sentence-ending period (the member list ends
    #    with a period before the next sentence), a blank line, or end. Earlier this used `[^\n]`,
    #    which silently dropped every line-wrapped NO list — the systematic dissent-undercount bug.
    ma = re.search(r"(?<!ALL\s)VOTING\s*AYE\s*[-–—:]\s*([\s\S]{0,500}?)"
                   r"(?=VOTING\s*NO\b|\n\s*\n|$)", block, re.I)
    if not ma:
        return None
    aye = extract_names_from_segment(ma.group(1), year)
    nay = []
    mn = re.search(r"VOTING\s*NO\s*[-–—:]?\s*([\s\S]{0,200}?)(?=\.\s|\.\n|\.$|\n\s*\n|$)",
                   block, re.I)
    if mn:
        nay = extract_names_from_segment(mn.group(1), year)
    if not aye and not nay:
        return None
    return aye, nay

# Sentence/segment that starts a motion.
MOTION_START = re.compile(
    r"(ON A MOTION BY\b.*?|[A-Z][A-Za-z .]*?\bMOVED\b.*?)", re.S)

def find_motions(text, year, default_body):
    """Yield motion dicts in document order."""
    # Flatten OCR page footers / lone 'Page' markers and collapse blank runs minimally,
    # but keep newlines so we can window. We'll work on a lightly-normalized copy.
    flat = re.sub(r"\n\s*Minutes of .*?Page\s*\n", "\n", text)        # running header
    flat = re.sub(r"\n\s*Page\s*\n", "\n", flat)
    motions = []
    ents, heads = scan_subjects(flat)   # verbatim long-titles + agenda headings

    # Track body transitions via convened/reconvened markers (rare in this corpus).
    # Build a list of (char_index, body) switch points.
    body_switches = []
    for mm in re.finditer(
        r"(convened|reconvened|recessed and reconvened|sitting|acting)\s+as\s+the\s+"
        r"(governing board of the\s+)?(redevelopment agency|community reinvestment agency|"
        r"municipal building authority|city council)", flat, re.I):
        tgt = mm.group(3).lower()
        if "redevelopment" in tgt: b = "RDA"
        elif "reinvestment" in tgt: b = "CRA"
        elif "building authority" in tgt: b = "MBA"
        else: b = "Council"
        body_switches.append((mm.start(), b))
    def body_at(idx):
        cur = default_body
        for pos, b in body_switches:
            if pos <= idx:
                cur = b
            else:
                break
        return cur

    # Find motion anchors: "ON A MOTION BY" or "<NAME> MOVED"
    anchors = []
    for mm in re.finditer(r"ON A MOTION BY|MOVED\b", flat):
        anchors.append(mm.start())
    anchors = sorted(set(anchors))

    for ai, start in enumerate(anchors):
        end = anchors[ai+1] if ai+1 < len(anchors) else len(flat)
        # window for this motion: from a little before the anchor sentence to next anchor,
        # but cap so the vote block (which follows the motion) is captured.
        seg = flat[start:end]
        # The motion sentence: from start up to the vote phrase or end.
        # Identify the outcome phrase.
        # Named roll-call?
        named = None
        if re.search(r"VOTING\s*AYE", seg, re.I):
            named = parse_named_rollcall(seg, year)

        # mover / seconder
        mover = seconder = None
        m_on = re.match(r"ON A MOTION BY\s+(.*?)\s+AND SECONDED BY\s+(.*?)[,\.]",
                        seg, re.I | re.S)
        if m_on:
            mover = first_member(m_on.group(1), year)
            seconder = first_member(m_on.group(2), year)
        else:
            m_mv = re.match(r"(.*?)\bMOVED\b", seg, re.S)
            if m_mv:
                mover = first_member(m_mv.group(1), year)
            m_sec = re.search(r"SECONDED BY\s+(.*?)[,\.]|(.*?)\s+SECONDED THE MOTION",
                              seg, re.I | re.S)
            if m_sec:
                seconder = first_member(m_sec.group(1) or m_sec.group(2) or "", year)

        # motion text: grab up to the outcome phrase, clean whitespace
        mt_text = seg
        cut = re.search(r"(WITH THE FOLLOWING ROLL CALL|UPON THE FOLLOWING ROLL CALL|"
                        r"ALL VOTING AYE|ALL VOTED AYE|VOTING AYE)", seg, re.I)
        if cut:
            mt_text = seg[:cut.start()]
        mt_text = re.sub(r"\s+", " ", mt_text).strip()
        mt_text = mt_text[:600]
        mt_type = motion_type(mt_text)   # native type from the bare motion sentence

        # subject enrichment: bare adoption formulas get the item's verbatim
        # long-title / agenda heading appended (see scan_subjects above)
        subject = subject_tag = None
        ad = adoption_ref(mt_text)
        if ad:
            subject, subject_tag = lookup_subject(ents, heads, ad[0], ad[1], start)
            if subject:
                mt_text = mt_text + ' [' + subject_tag + ': "' + subject + '"]'

        # Determine result + member lists  (distinct list objects -- no aliasing!)
        recorded = False
        aye, nay, absent, abstain, recuse = [], [], [], [], []
        if named is not None:
            aye, nay = list(named[0]), list(named[1])
            recorded = bool(aye or nay)

        # recuse / abstain hints -- ONLY vote-context phrasings (not narrative
        # "recused himself from discussion"). Look near this motion's vote line.
        tail = flat[start:min(len(flat), end + 300)]
        for rm in re.finditer(
                r"\b([A-Z][a-z]+)\s+(?:recused (?:him|her)self|abstained)"
                r"[^.\n]*?\bvot", tail, re.I):
            nm = canon_name(rm.group(1), year)
            if nm:
                verb = rm.group(0).lower()
                if "recus" in verb:
                    if nm not in recuse: recuse.append(nm)
                elif nm not in abstain:
                    abstain.append(nm)
        # "X was not present when this vote was taken" -> absent for this motion
        for rm in re.finditer(r"(?:member|Chair)\s+([A-Z][a-z]+)\s+was not present when this vote", tail, re.I):
            nm = canon_name(rm.group(1), year)
            if nm and nm not in absent: absent.append(nm)

        # remove recuse/abstain/absent from aye/nay if double-counted
        for L in (recuse, abstain, absent):
            for nm in L:
                if nm in aye: aye.remove(nm)
                if nm in nay: nay.remove(nm)

        nvote = len(aye) + len(nay) + len(abstain) + len(recuse)
        if recorded and nvote:
            outcome = "Pass" if len(aye) > len(nay) else ("Fail" if len(nay) >= len(aye) else "Pass")
            result = f"{len(aye)}-{len(nay)}" + (f"-{len(abstain)+len(recuse)}abs" if (abstain or recuse) else "") + f" {outcome}"
            names_recorded = True
        else:
            # tally-only / all voting aye -> no names
            result = "Voice Pass" if re.search(r"ALL VOTING AYE|ALL VOTED AYE|UNANIMOUS|MOTION CARRIED", seg, re.I) else "Recorded"
            names_recorded = False
            aye = nay = absent = abstain = recuse = []

        mo = {
            "body": body_at(start),
            "motion": mt_text,
            "motion_type": mt_type,
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
            "names_recorded": names_recorded,
        }
        if subject:
            mo["subject"] = subject
            mo["subject_source"] = subject_tag
        motions.append(mo)
    # number them
    for i, mo in enumerate(motions, 1):
        mo["motion_no"] = i
    return motions

def first_member(seg, year):
    """Return the first roster member name mentioned in a (possibly role-prefixed) segment."""
    if not seg:
        return None
    up = seg.upper()
    up = ROLE_SPLIT.sub(" ", up)
    for tok in re.split(r"[,\.;]|\bAND\b|\s+", up):
        nm = canon_name(re.sub(r"\s+", "", tok), year)
        if nm:
            return nm
    # try joining consecutive fragments (OCR split surname)
    joined = re.sub(r"[^A-Z]", "", up)
    return canon_name(joined, year)

# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def body_from_slug(slug):
    if "redevelopment-agency" in slug:
        return "RDA"
    if "municipal-building-authority" in slug:
        return "MBA"
    return "Council"

def load_index():
    rows = []
    with open(INDEX, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def main(rebuild_only=False):
    rows = load_index()
    processed = 0
    for r in rows:
        path = ROOT.parent / r["path"]
        if not path.exists():
            # path is repo-relative starting with meeting_minutes/
            path = ROOT.parent / r["path"]
        if not path.exists():
            continue
        year = int(r["year"])
        slug = r["slug"]
        default_body = body_from_slug(slug)
        rel = r["path"]
        # JSON output path mirrors minutes path under votes/
        jrel = rel.replace("meeting_minutes/minutes/", "", 1)
        jpath = VOTES_DIR / jrel
        jpath = jpath.with_suffix(".json")
        if rebuild_only and jpath.exists():
            processed += 1
            continue
        text = path.read_text(errors="replace")
        motions = find_motions(text, year, default_body)
        jpath.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "date": r["date"], "year": year, "title": r["title"],
            "body_default": default_body, "source": rel,
            "votes": motions,
        }
        jpath.write_text(json.dumps(obj, indent=1))
        processed += 1
    rebuild_csv(rows)
    return processed

def rebuild_csv(rows):
    fields = ["date","year","title","body","motion_no","motion","motion_type",
              "result","mover","seconder","member","vote","source"]
    out = []
    for r in rows:
        rel = r["path"]
        jrel = rel.replace("meeting_minutes/minutes/", "", 1)
        jpath = (VOTES_DIR / jrel).with_suffix(".json")
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        for mo in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=obj["title"],
                        body=mo["body"], motion_no=mo["motion_no"], motion=mo["motion"],
                        motion_type=mo["motion_type"], result=mo["result"],
                        mover=mo.get("mover") or "", seconder=mo.get("seconder") or "",
                        source=obj["source"])
            members = ([(m,"Aye") for m in mo["aye"]] + [(m,"Nay") for m in mo["nay"]] +
                       [(m,"Abstain") for m in mo["abstain"]] + [(m,"Absent") for m in mo["absent"]] +
                       [(m,"Recuse") for m in mo["recuse"]])
            if members:
                for mem, v in members:
                    row = dict(base); row["member"] = mem; row["vote"] = v
                    out.append(row)
            else:
                row = dict(base); row["member"] = ""; row["vote"] = ""
                out.append(row)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in out:
            w.writerow(row)
    return len(out)

if __name__ == "__main__":
    n = main(rebuild_only="--rebuild" in sys.argv)
    print(f"processed {n} meetings -> {OUT_CSV}")
