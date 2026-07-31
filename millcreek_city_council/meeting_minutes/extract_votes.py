#!/usr/bin/env python3
"""
extract_votes.py — Millcreek City Council + CRA vote extraction (PURE deterministic).

Reads the 372 council/CRA minutes markdown files listed in `meeting_minutes/
minutes_index.csv`, finds each recorded motion (mover / seconder / named roll call
or tally verdict), tags the governing `body` (Council or CRA), normalizes member
names against the fixed roster (OCR-fuzzy), and emits:

  - one JSON per meeting  -> meeting_minutes/votes/<year>/<week>/<file>.json
  - a rebuilt long CSV    -> meeting_minutes/all_votes.csv  (13-col standard)
  - roster.csv            -> meeting_minutes/roster.csv
  - a validation report is produced separately by validate_votes.py.

NO LLM, NO network.  Resumable: skips meetings whose JSON exists unless --force.

CARDINAL RULE — never fabricate.
  * NAMED roll call (each member "voted yes/no", incl. "Mayor X voted yes") ->
    named member rows (Aye/Nay/Abstain/Absent/Recuse).  MAX tally = 5 (4 districts
    + the mayor, who VOTES in Millcreek).
  * UNANIMOUS shorthand ("All Council Members voted yes. The motion passed
    unanimously.") and bare "Motion passed unanimously" -> names NOT listed ->
    names_recorded:false, EMPTY member lists.  The seated count is DERIVED from the
    PRESENT block (context / the >5 outlier check) but individuals are never named.
  * "<Name> was not present for the vote" -> Absent (not a Nay).
  * A motion that "failed for lack of a second" never came to a vote -> skipped.
  * An OCR-garbled surname is fuzzy-matched to the roster; unrecoverable -> BLANK
    (never guessed).

MILLCREEK VOTE GRAMMAR (built to this; verified across 2016-2026)
----------------------------------------------------------------
 A) Named prose (dominant 2019+; every seated member named even when unanimous):
      "Council Member Uipi moved to adopt item 2.2. Council Member DeSirant seconded.
       The Recorder called for the vote. Council Member DeSirant voted yes, Council
       Member Jackson voted yes, Councn Member Uipi voted yes, and Mayor Silvestrini
       voted yes. The motion passed unanimously."
    Grouped/dissent variant: "Council Members Marchant, Jackson, and Catten voted
       yes. Council Member Uipi voted no. Mayor Silvestrini abstained (counted as a
       no vote). The motion passed."
    Absent-from-vote: "Council Member DeSirant was not present for the vote."
 B) Unanimous shorthand (no names): "... called for the vote. All Council Members
       voted yes. The motion passed unanimously."  (CRA: "All Board Members voted yes")
 C) Early tally-only (2016-2017): "MOTION was made by Councilmember Catten, seconded
       by Councilmember Marchant to approve the Resolution. Motion passed unanimously."
    and "Councilmember Uipi moved to open the public hearing, seconded by
       Councilmember Marchant. Motion passed unanimously."

CRA body: the front-matter `**Body:**` field (harvested at acquisition) is authoritative
-> 314 Council files, 58 CRA files.  In CRA capacity the minutes say "Board Member <Name>"
= the councilmember and "Chair <Name>" = the mayor -> SAME five people.  A council file
that recesses INTO a genuine "convened as the Community Reinvestment Agency ...
reconvened as the City Council" block has that span re-tagged CRA by a bracket detector
(none carry recorded votes in this corpus — the recess motion itself stays Council).
"""
import os, re, csv, json, sys, glob, difflib

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")

FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Roster.  surname(lower) -> canonical full display name.  The mayor VOTES in
# Millcreek (max ordinary tally = 5 = 4 districts + mayor).  Cheri Jackson held
# D3 through Nov-2025 then became MAYOR (2025-11-10); Nicole Handy took D3
# (2025-11-24).  Either way surname "jackson" is the SAME person, so mapping is
# unambiguous.  Dwight Marchant held D2 early -> Thom DeSirant.  Jeff Silvestrini
# was mayor through 2025 -> Cheri Jackson.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "catten": "Silvia Catten",        # D1
    "marchant": "Dwight Marchant",    # D2 (early)
    "desirant": "Thom DeSirant",      # D2
    "jackson": "Cheri Jackson",       # D3 -> Mayor (Nov 2025)
    "handy": "Nicole Handy",          # D3 (Nov 2025+)
    "uipi": "Bev Uipi",               # D4
    "silvestrini": "Jeff Silvestrini",# Mayor (through 2025)
}
# people who are mayors (for the mayor-vote count in the report)
MAYORS = {"Jeff Silvestrini", "Cheri Jackson"}

# OCR / spelling variants seen in the corpus -> canonical surname key.
SURNAME_ALIASES = {
    "snvestrini": "silvestrini", "silvesatrini": "silvestrini",
    "silvestrmi": "silvestrini", "sllvestrini": "silvestrini",
    "sirant": "desirant", "sirani": "desirant", "desirant": "desirant",
    "marcliant": "marchant", "marchand": "marchant",
    "jaekson": "jackson", "jaclcson": "jackson", "clheri": "jackson",
    "cheri": "jackson", "clieri": "jackson", "cherr": "jackson",
    "ttipi": "uipi", "uipl": "uipi", "uij": "uipi",
    "catteii": "catten", "cattoi": "catten",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())

# role words (incl. common OCR corruptions of "Council"/"Member")
ROLE_WORDS = (r"Council\s*Members?|Councilmembers?|C[o0][un]{1,3}cn?\s*Members?|"
              r"Board\s*Members?|Coiuicil\s*Members?|Councn\s*Members?|"
              r"Council\s*Mennbers?|Council\s*Mem\w*|Board\s*Mem\w*|"
              r"Mayor|Chair(?:man|person|woman)?|Vice[\s-]?Chair(?:man|person)?")


def canon(token):
    """Map a name fragment to a roster full name, or None if unresolvable."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip().lower()
    if not t:
        return None
    words = [w for w in re.split(r"\s+", t) if len(w) >= 2]
    if not words:
        return None
    # exact / alias hit on any word (surname or first name)
    for w in reversed(words):
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    # fuzzy fallback (OCR): match each >=4-char word to the surname set
    for w in reversed(words):
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.8)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories).  Land-use + public-hearing checked
# early; open/close hearing is procedural "Public Hearing Action".
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|reorder the "
                 r"agenda|approve the agenda|work meeting|work session|closed session|"
                 r"closed meeting|executive session|\btable\b|continue the|postpone|"
                 r"go back into|go into (?:a )?(?:closed|pending)|strategy session|"
                 r"imminent litigation)\b", t):
        return "Procedural/Administrative"
    if re.search(r"mayor pro tem", t):
        return "Appointment"
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|"
                 r"\bplat\b|conditional use|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|street vacation|"
                 r"reinvestment (?:project )?area|project area|community reinvestment|"
                 r"redevelopment|blight|planned (?:unit )?development", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"amending the \d{4}|tentative budget|final budget|adopt\w*.*budget|"
                 r"budget for|appropriat", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|interlocal", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\s*\d|\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\s*\d|\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating", t):
        return "Ceremonial"
    return "Other"


# ---------------------------------------------------------------------------
# PRESENT-block parsing -> seated members (context / the >5 outlier check; NEVER
# used to name individuals on a tally-only unanimous motion).
# ---------------------------------------------------------------------------
def parse_present(flat):
    m = re.search(r"\bPRESENT\b", flat)
    start = m.end() if m else 0
    e = re.search(r"WORK\s+MEETING|REGULAR\s+MEETING|TIME\s+COMMENCED|Attendees:|"
                  r"called\s+the\s+meeting\s+to\s+order|BUSINESS\s+MEETING",
                  flat[start:])
    region = flat[start: start + (e.start() if e else 1200)]
    present = []
    for sn in SURNAMES:
        for mm in re.finditer(r"\b" + sn + r"\b", region, re.I):
            tail = region[mm.end(): mm.end() + 40].lower()
            if re.search(r"\(?\s*excused|\babsent", tail):
                continue
            nm = SURNAME_TO_FULL[sn]
            if nm not in present:
                present.append(nm)
            break
    return present


# ---------------------------------------------------------------------------
# CRA in-council bracket detector.  OPEN when the council genuinely CONVENES as
# the CRA (not merely a "recess into the CRA meeting at HH:MM" transition motion,
# which is Council business).  CLOSE when it reconvenes as the City Council.
# ---------------------------------------------------------------------------
CRA_OPEN = re.compile(
    r"(?:convened?|reconvened?|met)\s+as\s+the\s+(?:governing\s+board\s+of\s+the\s+)?"
    r"(?:millcreek\s+)?community\s+reinvestment\s+agency", re.I)
CRA_CLOSE = re.compile(
    r"(?:reconvened?|returned?|convened?)\s+as\s+the\s+(?:millcreek\s+)?city\s+council",
    re.I)


def cra_spans(flat):
    """Return list of (start,end) char spans that are CRA business inside a Council
    file.  Empty for the vast majority of files."""
    spans = []
    pos = 0
    while True:
        o = CRA_OPEN.search(flat, pos)
        if not o:
            break
        c = CRA_CLOSE.search(flat, o.end())
        end = c.start() if c else len(flat)
        spans.append((o.end(), end))
        pos = end
    return spans


# ---------------------------------------------------------------------------
# Motion anchoring.
# ---------------------------------------------------------------------------
NAME = r"([A-Z][A-Za-z'\-]{2,}(?:\s+[A-Z][A-Za-z'\-]{2,})?)"
ROLEG = r"(?:" + ROLE_WORDS + r")"

# Form C-struct: "MOTION was made by <role> <name>[, seconded by <role> <name>]"
STRUCT_RE = re.compile(
    r"MOTION\s+was\s+made\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"(?:\s*,?\s*seconded\s+by\s+" + ROLEG + r"?\s*" + NAME + r")?", re.I)

# Form A/B: "<role> <name> moved|motioned|made a motion"
MOVE_CONT = (r"to|that|for|approv|deny|denial|adopt|accept|open|close|continu|"
             r"recess|adjourn|reconvene|table|forward|recommend|ratify|nominat|"
             r"appoint|reappoint|amend|authoriz|direct|grant|support|make")
MOVE_RE = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s+(?:moved|motioned)(?=\s+(?:" + MOVE_CONT + r")\b)"
    r"|" + ROLEG + r"?\s*" + NAME + r"\s+made\s+a\s+motion(?=\s+(?:to|that|for)\b)"
    r"|" + ROLEG + r"?\s*" + NAME +
    r"\s+moved\s+in\s+a\s+substitute\s+motion(?=\s+to\b)"
    r"|" + ROLEG + r"?\s*" + NAME + r"\s+made\s+a\s+substitute\s+motion(?=\s+to\b)",
    re.I)

SECOND_RE = re.compile(
    r"seconded\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"|" + ROLEG + r"?\s*" + NAME + r"\s+seconded", re.I)

# vote-outcome anchors
CALLED_RE = re.compile(r"(?:" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+\s+)?"
                       r"called\s+for\s+the\s+vote", re.I)
OUTCOME_RE = re.compile(
    r"[Tt]he\s+motion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))"
    r"|[Mm]otion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))", re.I)
LACK_SECOND = re.compile(r"(?:fail\w*|died)\s+(?:due\s+to|for)\s+(?:a\s+)?lack\s+of\s+"
                         r"a?\s*second|for\s+lack\s+of\s+(?:a\s+)?second|no\s+second",
                         re.I)

ALLCOUNCIL = re.compile(
    r"All\s+(?:Council|Board)\s+Mem\w*\s+voted\s+(yes|aye|in\s+favor|no|nay)", re.I)
UNANIMOUS = re.compile(r"passed\s+unanimously|carried\s+unanimously|"
                       r"unanimous(?:ly)?", re.I)
FAILED = re.compile(r"motion\s+(?:failed|did\s+not\s+(?:pass|carry))", re.I)

# per-name vote verbs
VOTE_VERB = re.compile(
    r"\bvoted\s+(yes|no|nay|aye|against|in\s+favor)\b"
    r"|\b(abstained|abstains)\b"
    r"|\b(recused)\b"
    r"|\bwas\s+not\s+present\s+for\s+the\s+vote\b", re.I)

# ---------------------------------------------------------------------------
# 2017 en-dash TABULAR roll-call grammar.  Unlike the prose grammar (names BEFORE
# the outcome word), 2017 minutes print the outcome first — "Motion passed
# unanimously by roll call vote with members voting as follows:" — then a tabular
# block, ONE MEMBER PER LINE:
#     Councilmember Uipi – Aye
#     Councilmember Catten – Aye
#     Mayor Silvestrini – Aye
#     Councilmember Jackson – Aye
# The prose parser reads the pre-outcome span, so these motions currently fall
# through to tally-only.  This recovers the NAMED Ayes (incl. the voting mayor).
# Safe-direction: fires ONLY on the explicit "<role> <name> <dash> <vote-word>"
# grammar, which occurs NOWHERE outside 2017 (verified: 384 matches, all 2017,
# all Aye, only the 5 seated members).  Dash = en/em-dash or hyphen; OCR sometimes
# drops the space ("Uipi -Aye").
ENDASH_VOTE_RE = re.compile(
    ROLEG + r"\s+([A-Z][A-Za-z'\-]{2,})\s*[–—-]\s*"
    r"(Aye|Yes|Nay|No|Abstain\w*|Absent|Excused|Recuse\w*)\b", re.I)


def endash_vote_norm(word):
    w = word.lower()
    if w.startswith("ay") or w.startswith("ye"):
        return "Aye"
    if w.startswith("na") or w == "no":
        return "Nay"
    if w.startswith("abstain"):
        return "Abstain"
    if w.startswith("recuse"):
        return "Recuse"
    return "Absent"  # Absent / Excused


def parse_endash_votes(seg):
    """Parse the FIRST contiguous run of en-dash tabular roll-call lines in seg
    (post-outcome text).  Returns {full_name: vote}.  Stops at the first gap wider
    than a whitespace join so a following motion's block is never absorbed."""
    members = {}
    prev_end = None
    for m in ENDASH_VOTE_RE.finditer(seg):
        if prev_end is not None and m.start() - prev_end > 6:
            break  # run ended; do not cross into unrelated / next-motion text
        nm = canon(m.group(1))
        if nm:
            members[nm] = endash_vote_norm(m.group(2))
        prev_end = m.end()
    return members


def norm_vote(m):
    if m.group(1):
        t = m.group(1).lower()
        if t.startswith("y") or t.startswith("a") or "favor" in t:
            return "Aye"
        return "Nay"
    if m.group(2):
        return "Abstain"
    if m.group(3):
        return "Recuse"
    return "Absent"  # "was not present for the vote"


def names_in(seg):
    """All roster full names in a text segment (role-prefixed or bare roster/alias
    surname), in order, deduped.  Used for grouped lists 'Council Members A, B, and C'."""
    out = []
    for m in re.finditer(ROLEG + r"\s+([A-Z][A-Za-z'\-]{2,})", seg):
        nm = canon(m.group(1))
        if nm and nm not in out:
            out.append(nm)
    for m in re.finditer(r"\b([A-Z][A-Za-z'\-]{2,})\b", seg):
        w = m.group(1).lower()
        w = SURNAME_ALIASES.get(w, w)
        if w in SURNAME_TO_FULL and SURNAME_TO_FULL[w] not in out:
            out.append(SURNAME_TO_FULL[w])
    return out


def parse_named_votes(region):
    """Pair each 'voted X' / 'abstained' / 'recused' / 'not present for the vote'
    with the roster names that precede it since the previous verb."""
    members = {}
    unresolved = 0
    last = 0
    for m in VOTE_VERB.finditer(region):
        seg = region[last:m.start()]
        v = norm_vote(m)
        nms = names_in(seg)
        if nms:
            for nm in nms:
                members[nm] = v
        last = m.end()
    return members


# ---------------------------------------------------------------------------
def clean_motion_text(s):
    s = re.sub(r"\s+", " ", s).strip()
    # strip a trailing dangling seconder clause / stray role fragment, both orders
    s = re.split(r"\.\s+" + ROLEG + r"\s+[A-Z][A-Za-z'\-]+\s+seconded", s)[0]
    s = re.sub(r"\s*" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+\s+seconded.*$", "", s)
    s = re.sub(r"\s*,?\s*seconded\s+by\s+.*$", "", s, flags=re.I)
    s = re.sub(r"^(?:the\s+)?motion\s*:?\s*", "", s, flags=re.I)
    s = s.strip(" .,;:")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def build_result(names_recorded, ayes, nays, passed, unanimous):
    outcome = "Pass" if passed else "Fail"
    if names_recorded:
        return f"{ayes}-{nays} {outcome}"
    if unanimous:
        return f"{outcome} (unanimous)"
    return outcome


# ---------------------------------------------------------------------------
# Per-meeting extraction
# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"\x0c|M[fi]llcreek\s+City\s+Council\w*\s+Meeting\s+Minutes.*?Page\s+\d+\s+of\s+\d+|"
    r"M[fi]llcreek\s+.*?Meeting\s+Minutes.*?Page\s+\d+\s+of\s+\d+", re.I)


def split_frontmatter(raw):
    parts = re.split(r"\n\s*---\s*\n", raw, maxsplit=1)
    head = parts[0]
    body = parts[1] if len(parts) > 1 else raw
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    body_tag = bm.group(1) if bm else "Council"
    return body_tag, body


# Agenda item headings ("3.1 Discussion and Consideration of Resolution 22-28, ...")
# used to enrich boilerplate "approve item 3.1" motions whose subject lives only in
# the heading (per extraction_standards.md — capture the agenda subject).
HEADING_RE = re.compile(
    r"(?<![.\d])(\d{1,2}\.\d{1,2})\s+([A-Z][A-Za-z].{6,120}?)"
    r"(?=\s+(?:" + ROLEG + r"\s+[A-Z]|\d{1,2}\.\d{1,2}\s+[A-Z]|The\s+[A-Z]|$))")
ITEM_REF_RE = re.compile(r"\bitems?\s+((?:\d{1,2}\.\d{1,2}|\d{1,2})"
                         r"(?:\s*[,&-]\s*(?:and\s+)?(?:\d{1,2}\.\d{1,2}|\d{1,2})|"
                         r"\s+and\s+(?:\d{1,2}\.\d{1,2}|\d{1,2}))*)", re.I)


def build_headings(flat):
    d = {}
    for m in HEADING_RE.finditer(flat):
        num = m.group(1)
        title = re.sub(r"\s+", " ", m.group(2)).strip(" .,;:")
        d.setdefault(num, title)
    return d


def enrich_motion(motion_text, headings):
    """If the motion is a bare 'approve item(s) N.N' with no substantive subject,
    append the agenda heading title(s) so the subject is captured."""
    if not headings:
        return motion_text
    if re.search(r"resolution|ordinance|contract|agreement|budget|proclamation|"
                 r"interlocal|grant|appoint", motion_text, re.I):
        return motion_text
    ref = ITEM_REF_RE.search(motion_text)
    if not ref:
        return motion_text
    nums = re.findall(r"\d{1,2}\.\d{1,2}", ref.group(1))
    titles = [headings[n] for n in nums if n in headings]
    if not titles:
        return motion_text
    add = "; ".join(titles)
    out = motion_text.rstrip(" .") + " — " + add
    return out[:400]


def find_motions(flat):
    """Yield (start, mover, seconder_or_None, anchor_end) for each motion anchor
    in document order, merging the struct + move-verb forms."""
    anchors = []
    for m in STRUCT_RE.finditer(flat):
        mover = canon(m.group(1))
        seconder = canon(m.group(2)) if m.group(2) else None
        if mover:
            anchors.append((m.start(), mover, seconder, m.end()))
    for m in MOVE_RE.finditer(flat):
        mover = canon(next((g for g in m.groups() if g), None))
        if mover:
            anchors.append((m.start(), mover, None, m.end()))
    anchors.sort(key=lambda a: a[0])
    # dedup near-duplicate anchors (struct + move-verb overlapping) within 5 chars
    out = []
    for a in anchors:
        if out and abs(a[0] - out[-1][0]) < 5:
            continue
        out.append(a)
    return out


def extract_meeting(path, rel_source, date, year, title, file_body):
    raw = open(path, encoding="utf-8").read()
    _bt, body = split_frontmatter(raw)
    flat = FOOTER_RE.sub(" ", body)
    flat = re.sub(r"\s+", " ", flat)
    present = parse_present(flat)
    cra = cra_spans(flat) if file_body == "Council" else []
    headings = build_headings(flat)

    anchors = find_motions(flat)
    votes = []
    for i, (astart, mover, sec0, aend) in enumerate(anchors):
        nxt = anchors[i + 1][0] if i + 1 < len(anchors) else len(flat)
        region = flat[aend:nxt]

        # seconder
        seconder = sec0
        sm = SECOND_RE.search(region[:400])
        sec_end = 0
        if sm:
            if not seconder:
                seconder = canon(sm.group(1) or sm.group(2))
            sec_end = sm.end()

        # outcome anchor
        om = OUTCOME_RE.search(region)
        if not om:
            continue  # no recorded verdict near this move-verb -> not a real vote

        # skip motions that died for lack of a second
        if LACK_SECOND.search(region[:om.start() + 40]) and not VOTE_VERB.search(
                region[:om.start()]):
            continue

        # motion text: anchor-end .. outcome (minus seconder clause / call clause)
        raw_motion = region[:om.start()]
        # cut at "called for the vote" / first per-name vote / "All Council Members"
        cutters = [CALLED_RE.search(raw_motion), ALLCOUNCIL.search(raw_motion),
                   VOTE_VERB.search(raw_motion)]
        cutpos = min([c.start() for c in cutters if c], default=len(raw_motion))
        motion_text = clean_motion_text(raw_motion[:cutpos])
        if not motion_text or len(motion_text) < 3:
            motion_text = clean_motion_text(raw_motion[:200])
        motion_text = enrich_motion(motion_text, headings)

        # vote region: from seconder to the outcome ("was not present for the vote"
        # and every roll-call name sit BEFORE the outcome in this corpus, so no tail
        # is needed — a tail would bleed a following nested motion's names).
        vr_start = max(sec_end, 0)
        v_om = om
        # Nested substitute + "called for the vote on the original motion" (1 file,
        # 2020-02-24): this anchor's motion is the ORIGINAL — capture the SECOND
        # (original) vote block, not the substitute's, so the ordinance's true
        # disposition is recorded (never fabricated).
        orig = re.search(r"on\s+the\s+original\s+motion", region, re.I)
        if orig and re.search(r"substitute", region[:om.start()], re.I):
            om2 = OUTCOME_RE.search(region, orig.end())
            if om2:
                vr_start = orig.end()
                v_om = om2
        outcome_word = (v_om.group(1) or v_om.group(2) or "").lower()
        passed = not (outcome_word.startswith("fail") or outcome_word.startswith("did"))

        # The roll call is the span AFTER the "<caller> called for the vote" clause
        # (so roster names in the intervening discussion are never mistaken for
        # voters), up to the outcome.
        roll_region = region[vr_start:v_om.start()]
        calls = list(CALLED_RE.finditer(roll_region))
        if calls:
            roll_region = roll_region[calls[-1].end():]

        # Tally-only shorthand ("All Council/Board Members voted yes") takes
        # precedence over per-name parsing — it CONTAINS "voted yes" but names no
        # individuals, and discussion names can precede it.
        unanimous = False
        present_count = None
        ac = ALLCOUNCIL.search(roll_region)
        if ac:
            members = {}
            unanimous = ac.group(1).lower() in ("yes", "aye", "in favor")
            passed = passed and unanimous
            present_count = len(present)
        else:
            members = parse_named_votes(roll_region)

        # 2017 en-dash TABULAR roll call: the named block sits AFTER the outcome
        # word (see parse_endash_votes), so the prose parse above found nothing.
        # Recover the named Ayes from the post-outcome span (bounded by the next
        # anchor via `region`).  Additive + safe-direction: only fires when no
        # names were parsed and only on the explicit dash+vote grammar (2017-only).
        if not members:
            ed = parse_endash_votes(region[v_om.end():])
            if ed:
                members = ed
                unanimous = False
                present_count = None

        names_recorded = bool(members)
        aye = sorted(n for n, v in members.items() if v == "Aye")
        nay = sorted(n for n, v in members.items() if v == "Nay")
        abstain = sorted(n for n, v in members.items() if v == "Abstain")
        recuse = sorted(n for n, v in members.items() if v == "Recuse")
        absent = sorted(n for n, v in members.items() if v == "Absent")

        if not names_recorded and present_count is None:
            # the adverb "unanimously" trails the outcome word ("Motion passed
            # unanimously"), so look a little past the outcome match.
            if UNANIMOUS.search(region[max(0, v_om.start() - 10):v_om.end() + 40]):
                unanimous = True
                present_count = len(present)

        ayes = len(aye)
        nays = len(nay)
        if names_recorded:
            passed = ayes > nays if (ayes or nays) else passed

        # body: file-level tag, unless this motion sits inside a CRA bracket span
        body = file_body
        if body == "Council":
            for s, e in cra:
                if s <= astart < e:
                    body = "CRA"
                    break

        result = build_result(names_recorded, ayes, nays, passed, unanimous)
        # date-aware mayor seat: Silvestrini always mayor; Jackson mayor from Nov-2025
        mayor_voted = any(
            n == "Jeff Silvestrini" or (n == "Cheri Jackson" and date >= "2025-11-10")
            for n in (aye + nay + abstain + recuse + absent))

        rec = {
            "motion": motion_text,
            "body": body,
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
            "mayor_voted": mayor_voted,
        }
        if not names_recorded:
            rec["tally_only"] = {"unanimous": unanimous, "present_count": present_count}
        votes.append(rec)

    for n, v in enumerate(votes, 1):
        v_no = {"motion_no": n}
        v_no.update(v)
        votes[n - 1] = v_no

    return {
        "date": date,
        "year": int(year),
        "title": title,
        "file_body": file_body,
        "present": present,
        "source": rel_source,
        "votes": votes,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.split("/")           # minutes/<year>/<week>/<file>.md
    week = parts[-2]
    return os.path.join(VOTES_DIR, str(year), week, parts[-1].replace(".md", ".json"))


def file_body_of(path):
    head = open(path, encoding="utf-8").read(600)
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    return bm.group(1) if bm else "Council"


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    for r in rows:
        path = os.path.join(ROOT, r["path"])
        if not os.path.exists(path):
            print("MISSING", r["path"], file=sys.stderr)
            continue
        jp = json_path_for(r["path"], r["year"])
        if os.path.exists(jp) and not FORCE:
            continue
        try:
            meeting = extract_meeting(path, r["path"], r["date"], r["year"],
                                      r["title"], file_body_of(path))
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(meeting, f, indent=1, ensure_ascii=False)
    rebuild_csv(rows)
    build_roster(rows)
    print("done")


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
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
                        source=obj["source"])
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
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in out:
            w.writerow({k: row.get(k, "") for k in cols})
    return len(out)


def build_roster(rows):
    """member, role, first_seen, last_seen, n_meetings — from anyone who MOVED /
    SECONDED / cast a NAMED vote (unambiguous seat evidence)."""
    ROLE = {"Silvia Catten": "Council D1", "Dwight Marchant": "Council D2",
            "Thom DeSirant": "Council D2", "Cheri Jackson": "Council D3 / Mayor",
            "Nicole Handy": "Council D3", "Bev Uipi": "Council D4",
            "Jeff Silvestrini": "Mayor"}
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        date = obj["date"]
        people = set()
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k) in FULLNAMES:
                    people.add(v[k])
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                people.update(v.get(k, []))
        for p in people:
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date)
            d["last"] = max(d["last"], date)
            d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, ROLE.get(nm, ""), d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
