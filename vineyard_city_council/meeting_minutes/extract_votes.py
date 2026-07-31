#!/usr/bin/env python3
"""
Vineyard, UT — council vote extraction.

Reads the minutes markdown under meeting_minutes/minutes/<year>/<week>/<date>_<slug>.md,
parses recorded roll-call motions, and emits:
  - per-meeting JSON  -> meeting_minutes/votes/<year>/<week>/<date>_<slug>.json
  - long-format CSV   -> meeting_minutes/all_votes.csv  (rebuilt from the JSONs)

Two roll-call formats exist in the corpus:
  (A) "ALL-CAPS INLINE" (dominant, ~2020-2025):
        Motion: COUNCILMEMBER X MOVED TO ... COUNCILMEMBER Y SECONDED THE MOTION.
        [ROLL CALL WENT AS FOLLOWS:] MAYOR FULLMER, COUNCILMEMBERS A, B, AND C
        VOTED AYE/YES.  COUNCILMEMBER D VOTED NAY/NO.  COUNCILMEMBER E ABSTAINED.
        COUNCILMEMBER F WAS ABSENT.  THE MOTION CARRIED UNANIMOUSLY / CARRIED 3-2 /
        CARRIED FOUR (4) TO ONE (1) / CARRIED WITH TWO ABSENT.
  (B) "STRUCTURED" (2026 / OCR files):
        Motion: Council Member X motioned to ...
        Second/Seconded: Council Member Y
        Yes: Council Members A, B, and C.   No: None.   Absent: Council Member D.
        Motion Passed 5-0.

Names are normalized to a canonical Last-name spelling via NAME_MAP.
Where the minutes give NO per-member names (rare; tally-only/"unanimous" w/o a list),
member lists are left empty and names_recorded=false. Never guess who voted which way.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MIN_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
ALL_VOTES_CSV = ROOT / "all_votes.csv"

# ---- name normalization ------------------------------------------------------
# Canonical = the surname as it should appear in the dataset.
SURNAMES = [
    "Fullmer", "Stratton",                       # mayors
    "Earnest", "Flake", "Judd", "Welsh",         # 2020-21 era
    "Sifuentes", "Rasmussen", "Cameron",         # 2022-23 era
    "Holdaway", "Clawson",                       # 2024-25 era
    "Lauret", "Wood", "McCumber", "Nair",        # 2026 era
]
# uppercase surname -> canonical
SURNAME_BY_UPPER = {s.upper(): s for s in SURNAMES}
# OCR / spelling variants seen in the text -> canonical surname
NAME_MAP = {
    "FULLMER": "Fullmer", "STRATTON": "Stratton", "STATTON": "Stratton",
    "EARNEST": "Earnest", "ERNEST": "Earnest",
    "FLAKE": "Flake", "JUDD": "Judd", "WELSH": "Welsh",
    "SIFUENTES": "Sifuentes", "RASMUSSEN": "Rasmussen", "CAMERON": "Cameron",
    "CAMREON": "Cameron", "CAMRON": "Cameron",   # OCR/source typos in 2025 recovered minutes
    "HOLDAWAY": "Holdaway", "HOLAWAY": "Holdaway", "HOLDWAY": "Holdaway",
    "CLAWSON": "Clawson",
    "LAURET": "Lauret", "WOOD": "Wood", "MCCUMBER": "McCumber",
    "MCCUMMBER": "McCumber", "NAIR": "Nair",
}
ROLE_PREFIX = re.compile(
    r"^(?:MAYOR\s+PRO\s+TEM(?:PORE|PORARY|PORE\.)?\s+|MAYOR\s+PRO\s+TEMP?\s+|"
    r"MAYOR\s+|COUNCIL\s*MEMBERS?\s+|COUNCILMEMBERS?\s+|CITY\s+ATTORNEY\s+|"
    # board-capacity role synonyms (RDA/CRA): Chair / Acting Chair / Vice Chair /
    # Board Member / Boardmember / Board Members / Agency Member — same people.
    r"ACTING\s+CHAIR\s+|VICE\s+CHAIR\s+|CHAIR(?:PERSON|MAN|WOMAN)?\s+|"
    r"BOARD\s*MEMBERS?\s+|AGENCY\s+MEMBERS?\s+|"
    r"MR\.?\s+|MS\.?\s+|MRS\.?\s+)",
    re.I,
)

# How the minutes name a person in board (RDA/CRA) capacity, for mover/seconder and
# motion-text stripping. Same people — these are role synonyms, not new members.
BOARD_ROLE = (r"(?:ACTING\s+CHAIR|VICE\s+CHAIR|CHAIR(?:PERSON|MAN|WOMAN)?|"
              r"BOARD\s*MEMBERS?|AGENCY\s+MEMBERS?)")
COUNCIL_ROLE = (r"(?:MAYOR\s+PRO\s+TEM\w*\s+)?(?:MAYOR|COUNCILMEMBERS?|"
                r"COUNCIL\s*MEMBERS?|" + BOARD_ROLE + r")")


def norm_name(raw):
    """Map a raw name token to canonical surname, or None if not a council member."""
    if not raw:
        return None
    s = raw.strip().strip(".,'’“” ")
    s = ROLE_PREFIX.sub("", s).strip()
    # collapse to the last alphabetic token (surname)
    toks = re.findall(r"[A-Za-z]+", s)
    if not toks:
        return None
    up = toks[-1].upper()
    if up in NAME_MAP:
        return NAME_MAP[up]
    if up in SURNAME_BY_UPPER:
        return SURNAME_BY_UPPER[up]
    # try the whole string token-by-token (handles "MAYOR FULLMER" already stripped)
    for t in toks:
        u = t.upper()
        if u in NAME_MAP:
            return NAME_MAP[u]
        if u in SURNAME_BY_UPPER:
            return SURNAME_BY_UPPER[u]
    return None


def split_names(blob):
    """Split a 'A, B, AND C' style member list into canonical surnames (de-duped, ordered)."""
    if not blob:
        return []
    blob = re.sub(r"\bAND\b", ",", blob, flags=re.I)
    blob = blob.replace("&", ",")
    out, seen = [], set()
    for piece in blob.split(","):
        n = norm_name(piece)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ---- motion-type classification ---------------------------------------------
def classify(text):
    t = text.lower()
    if re.search(r"\bopen the public hearing|close the public hearing|"
                 r"open.{0,15}public hearing|close.{0,15}public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\badjourn|recess|go into a closed session|closed session|"
                 r"enter (a |an )?executive|reconvene|convene as|"
                 r"mayor pro tem|approve the agenda|amend the agenda|"
                 r"continue|table\b|postpone|ratify the agenda|excuse", t):
        return "Procedural/Administrative"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bbudget amendment|amend.{0,20}budget|tentative budget|"
                 r"final budget|adopt.{0,20}budget|cdba|certified tax rate", t):
        return "Budget Amendment"
    if re.search(r"\bgrant\b|cdbg|funding application|apply for", t):
        return "Grant-Funding"
    if re.search(r"\binterlocal|cooperative agreement|mutual aid|joint resolution", t):
        return "Interlocal"
    if re.search(r"\bappoint|reappoint|nominat|mayor pro tempore|ratify.{0,20}appoint|"
                 r"swear", t):
        return "Appointment"
    if re.search(r"\brezone|rezoning|zoning map|general plan|plat\b|subdivision|"
                 r"site plan|land use|annex|conditional use|preliminary|final plat|"
                 r"development agreement|setback|density|overlay", t):
        return "Land-Use/Zoning"
    if re.search(r"\bcontract|agreement|purchase|bid\b|award.{0,20}(bid|contract)|"
                 r"professional services|task order|change order|lease|"
                 r"approve.{0,15}purchase", t):
        return "Contract/Purchase"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"\bproclaim|proclamation|recogniz|honor|commend|in memoriam", t):
        return "Ceremonial"
    if re.search(r"\bconsent (item|agenda|calendar)|approve.{0,15}minutes|"
                 r"approval of.{0,20}minutes|approve.{0,10}consent", t):
        return "Procedural/Administrative"
    return "Other"


# ---- result/tally extraction -------------------------------------------------
WORDNUM = {"ZERO": 0, "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
           "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10}


def find_result(tail):
    """Return the verbatim result string (e.g. 'Carried unanimously', '3-2 Pass')."""
    # 2026 structured: "Motion Passed 5-0" / "Motion Failed 2-3"
    m = re.search(r"Motion\s+(Passed|Failed|Carried|Tied)\s+(\d+)\s*[-–]\s*(\d+)",
                  tail, re.I)
    if m:
        verb = "Pass" if m.group(1).lower() in ("passed", "carried") else (
            "Fail" if m.group(1).lower() == "failed" else m.group(1).title())
        return f"{m.group(2)}-{m.group(3)} {verb}", verb
    # caps inline: "THE MOTION CARRIED 3-2." / "PASSED 4-1"
    m = re.search(r"MOTION\s+(CARRIED|PASSED|FAILED)\s+(\d+)\s*[-–]\s*(\d+)", tail, re.I)
    if m:
        verb = "Fail" if m.group(1).upper() == "FAILED" else "Pass"
        return f"{m.group(2)}-{m.group(3)} {verb}", verb
    # word-number: "CARRIED FOUR (4) TO ONE (1)" or "CARRIED THREE TO TWO"
    m = re.search(
        r"(CARRIED|PASSED|FAILED)\s+([A-Z]+)\s*(?:\((\d+)\))?\s*TO\s+([A-Z]+)\s*(?:\((\d+)\))?",
        tail, re.I)
    if m:
        a = m.group(3) or str(WORDNUM.get(m.group(2).upper(), "?"))
        b = m.group(5) or str(WORDNUM.get(m.group(4).upper(), "?"))
        verb = "Fail" if m.group(1).upper() == "FAILED" else "Pass"
        return f"{a}-{b} {verb}", verb
    # unanimous
    if re.search(r"CARRIED\s+UNANIMOUSLY|PASSED\s+UNANIMOUSLY|MOTION\s+(CARRIED|PASSED)\b"
                 r"(?!.{0,8}(WITH|\d|[A-Z]+\s+TO))", tail, re.I) or \
       re.search(r"carried unanimously|passed unanimously|unanimous", tail, re.I):
        if re.search(r"unanimous", tail, re.I):
            return "Carried unanimously", "Pass"
    # carried/passed with N absent
    m = re.search(r"(?:CARRIED|PASSED)\s+WITH\s+([A-Z]+)\s+ABSENT", tail, re.I)
    if m:
        return f"Carried with {m.group(1).lower()} absent", "Pass"
    # bare carried/passed
    if re.search(r"\bMOTION\s+(CARRIED|PASSED)\b", tail, re.I):
        return "Carried", "Pass"
    if re.search(r"\bMOTION\s+FAILED\b|FAILED\s+FOR\s+LACK", tail, re.I):
        return "Failed", "Fail"
    return None, None


# ---- vote-list extraction ----------------------------------------------------
def extract_votes_inline(tail):
    """Parse the ALL-CAPS inline vote phrasing. Returns dict of lists (may be empty).

    Works clause-by-clause so a 'VOTED NO' clause can't reach back across a period
    and swallow the names from a preceding 'VOTED YES' clause. Each clause is the run
    of text ending at a vote verb; the names are whatever precedes the verb *within
    that clause* (i.e. after the previous clause boundary).
    """
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    # Vote verbs in priority order; first alternative that matches the clause tail wins.
    # Affirmative phrasings: "VOTED AYE/YES" and (2024+) "VOTED IN FAVOR / IN SUPPORT /
    # IN THE AFFIRMATIVE". Negative: "VOTED NAY/NO" and "VOTED IN OPPOSITION / AGAINST /
    # IN THE NEGATIVE". The named member run precedes the verb within the same clause
    # (handled below by taking the trailing name run after the last clause boundary), so
    # "MAYOR FULLMER AND COUNCILMEMBERS A, B, AND C VOTED IN FAVOR" captures the mayor too.
    verb_pat = re.compile(
        r"\bVOTED\s+(AYE|YES)\b"
        r"|\bVOTED\s+IN\s+(?:FAVOR|SUPPORT|THE\s+AFFIRMATIVE)\b"
        r"|\bVOTED\s+(NAY|NO)\b"
        r"|\bVOTED\s+(?:IN\s+OPPOSITION(?:\s+TO)?|AGAINST|IN\s+THE\s+NEGATIVE)\b"
        r"|\bABSTAINED\b"
        r"|\b(?:WAS|WERE)\s+(?:ABSENT|EXCUSED)\b"
        r"|\bRECUSED\b",
        re.I,
    )
    # Strip the leading "ROLL CALL WENT AS FOLLOWS:" marker noise but keep names.
    last = 0
    for m in verb_pat.finditer(tail):
        clause = tail[last:m.start()]
        last = m.end()
        # names = trailing name-ish run of this clause (after the last period)
        seg = re.split(r"[.;:]", clause)[-1]
        names = split_names(seg)
        if not names:
            continue
        verb = m.group(0).upper()
        if "AYE" in verb or "YES" in verb or "FAVOR" in verb or "SUPPORT" in verb \
                or "AFFIRMATIVE" in verb:
            res["aye"] += names
        elif "NAY" in verb or "NO" in verb or "OPPOSITION" in verb \
                or "AGAINST" in verb or "NEGATIVE" in verb:
            res["nay"] += names
        elif verb.startswith("ABSTAIN"):
            res["abstain"] += names
        elif "ABSENT" in verb or "EXCUSED" in verb:
            res["absent"] += names
        else:
            res["recuse"] += names
    return _dedupe(res)


def extract_votes_structured(tail):
    """Parse the 2026 'Yes:/No:/Absent:/Abstain:' phrasing."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    flat = re.sub(r"\s+", " ", tail)  # un-wrap newline-broken member lists
    labels = [("aye", r"Yes"), ("nay", r"No"), ("abstain", r"Abstain(?:ed)?"),
              ("absent", r"Absent"), ("recuse", r"Recus(?:ed|al)?")]
    for key, lab in labels:
        for m in re.finditer(
            rf"\b{lab}\s*:\s*(.*?)(?=(?:\s*(?:Yes|No|Absent|Abstain|Recus|"
            rf"Motion|Second)\b\s*[:\.])|$)", flat, re.I):
            blob = m.group(1)
            # stop at first sentence end so trailing narrative isn't slurped in
            blob = re.split(r"\.\s", blob)[0]
            if re.match(r"^\s*(none|n/?a)\b", blob, re.I):
                continue
            res[key] += split_names(blob)
    return _dedupe(res)


def _dedupe(res):
    for k in res:
        seen, out = set(), []
        for n in res[k]:
            if n not in seen:
                seen.add(n)
                out.append(n)
        res[k] = out
    # If a member is captured in both 'aye' and a more-specific bucket (a source
    # repetition like "...HOLDAWAY VOTED YES. ... HOLDAWAY VOTED NO."), the explicit
    # nay/abstain/absent/recuse statement is the operative one — drop from aye.
    specific = set(res["nay"]) | set(res["abstain"]) | set(res["recuse"]) | set(res["absent"])
    res["aye"] = [n for n in res["aye"] if n not in specific]
    return res


def extract_mover_seconder(block):
    mover = seconder = None
    m = re.search(COUNCIL_ROLE + r"\s+[A-Z][A-Za-z’']+"
                  r"(?:\s+[A-Z][A-Za-z’']+)?\s+(?:MOVED|MOTIONED|NOMINATED)",
                  block, re.I)
    if m:
        mover = norm_name(m.group(0))
    if mover is None:
        m = re.search(r"Motion:\s*((?:Council\s*Member|Councilmember|Mayor|"
                      r"Board\s*member|Boardmember|Chair|Acting\s+Chair|"
                      r"Agency\s+Member)[^,.\n]*?)\s+"
                      r"(?:motioned|moved|nominated)", block, re.I)
        if m:
            mover = norm_name(m.group(1))
    m = re.search(COUNCIL_ROLE + r"\s+[A-Z][A-Za-z’']+"
                  r"(?:\s+[A-Z][A-Za-z’']+)?\s+SECONDED", block, re.I)
    if m:
        seconder = norm_name(m.group(0))
    if seconder is None:
        m = re.search(r"Second(?:ed)?\s*:\s*([^\n,.]*)", block, re.I)
        if m:
            seconder = norm_name(m.group(1))
    return mover, seconder


# ---- motion text -------------------------------------------------------------
def motion_text(block):
    """First ~1 sentence(s) describing what was moved."""
    m = re.search(r"Motion:\s*(.*?)(?:SECONDED|Second(?:ed)?\s*:|ROLL\s+CALL|"
                  r"\bVOTED\s+(?:AYE|YES|NAY|NO)|\bYes\s*:|\bNo\s*:)",
                  block, re.I | re.S)
    raw = m.group(1) if m else block[:400]
    raw = re.sub(r"\s+", " ", raw).strip()
    # strip leading "COUNCILMEMBER X MOVED TO " / "Council Member X motioned to " /
    # "BOARDMEMBER X MOVED TO " / "ACTING CHAIR X MOVED TO "
    raw = re.sub(r"^" + COUNCIL_ROLE + r"\s+[A-Za-z’']+(?:\s+[A-Za-z’']+)?\s+"
                 r"(?:MOVED|MOTIONED|NOMINATED)\s+(?:TO\s+)?",
                 "", raw, flags=re.I).strip()
    # strip a trailing seconder-name fragment the lookahead left in
    # (e.g. "...6.2. COUNCILMEMBER FLAKE" before "SECONDED")
    raw = re.sub(COUNCIL_ROLE + r"\s+[A-Za-z’']+\s*$", "", raw, flags=re.I).strip()
    raw = raw.rstrip(". ").strip()
    if len(raw) > 300:
        raw = raw[:297].rstrip() + "..."
    return raw or "(motion text not captured)"


# ---- body (governing-body) tagging -------------------------------------------
# In Utah the council sits AS the RDA/CRA board — same people, a different capacity.
# Two ways the body shows up in Vineyard's minutes:
#   (1) a SEPARATE meeting whose title is "Redevelopment Agency …" (post-2024 Vineyard
#       holds a distinct RDA Board Meeting event) -> whole file is body=RDA.
#   (2) an AGENDA BLOCK inside a council meeting: "adjourned … and convened as the …
#       Redevelopment Agency" / "convene as the … RDA" … later "reconvened as the City
#       Council". Motions between those markers are body=RDA; everything else Council.
# CRA (Community Reinvestment Agency, post-2016 name) is handled the same way.
TITLE_BODY = [
    ("CRA", re.compile(r"community\s+reinvestment", re.I)),
    ("RDA", re.compile(r"redevelopment\s+agency|\bredevelopment\s+board\b", re.I)),
]
# markers that switch capacity mid-meeting
INTO_RDA = re.compile(
    r"convene[ds]?\s+as\s+the\s+(?:vineyard\s+)?redevelopment\s+agency"
    r"|convene[ds]?\s+as\s+the\s+(?:governing\s+board\s+of\s+the\s+)?redevelopment"
    r"|reconvene[ds]?\s+as\s+the\s+(?:vineyard\s+)?redevelopment"
    r"|governing\s+board\s+of\s+the\s+redevelopment\s+agency"
    r"|recess(?:ed)?\s+(?:and\s+)?(?:re)?convene[ds]?\s+as\s+the\s+redevelopment"
    r"|adjourn(?:ed)?\s+(?:the\s+)?(?:regular\s+)?city\s+council[^\n.]{0,60}"
    r"convene[ds]?\s+as\s+the[^\n.]{0,40}redevelopment",
    re.I)
INTO_CRA = re.compile(
    r"convene[ds]?\s+as\s+the\s+community\s+reinvestment\s+agency"
    r"|reconvene[ds]?\s+as\s+the\s+community\s+reinvestment",
    re.I)
BACK_TO_COUNCIL = re.compile(
    r"reconvene[ds]?\s+as\s+the\s+city\s+council"
    r"|adjourn(?:ed)?\s+(?:as\s+)?the\s+(?:redevelopment\s+agency|rda|"
    r"community\s+reinvestment\s+agency|cra)[^\n.]{0,60}"
    r"(?:re)?convene[ds]?\s+as\s+the\s+city\s+council"
    r"|reconvene[ds]?\s+(?:back\s+)?(?:as|to)\s+(?:the\s+)?(?:regular\s+)?council",
    re.I)


def file_body(title):
    """Default body for a whole meeting based on its title (separate RDA/CRA meeting)."""
    for tag, pat in TITLE_BODY:
        if pat.search(title or ""):
            return tag
    return "Council"


def body_segments(text):
    """Return a list of (start_offset, body) capacity changes in document order for the
    in-council 'convened as the RDA/CRA' agenda-block case. Position 0 is always the
    file default; subsequent entries flip the body at the marker's offset."""
    events = []
    for pat, tag in ((INTO_RDA, "RDA"), (INTO_CRA, "CRA"),
                     (BACK_TO_COUNCIL, "Council")):
        for m in pat.finditer(text):
            events.append((m.start(), tag))
    events.sort()
    return events


def body_at(offset, default, events):
    """The active body at a character offset given the ordered capacity-change events."""
    cur = default
    for pos, tag in events:
        if pos <= offset:
            cur = tag
        else:
            break
    return cur


# ---- per-file processing -----------------------------------------------------
MOTION_SPLIT = re.compile(r"(?=^\s*Motion:)", re.M | re.I)


def process_file(md_path, default_body="Council"):
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # drop page-footer noise lines that can appear mid-vote
    text = re.sub(r"(?m)^\s*Page \d+ of \d+;.*$", " ", text)

    # capacity-change markers (convened-as-RDA / reconvened-as-Council) by offset
    cap_events = body_segments(text)

    # split into motion blocks while keeping each block's start offset in the document
    # (case-insensitive: some minutes write the header as ALL-CAPS "MOTION:")
    anchors = [m.start() for m in re.finditer(r"(?m)^\s*Motion:", text, re.I)]
    blocks = []
    for j, start in enumerate(anchors):
        end = anchors[j + 1] if j + 1 < len(anchors) else len(text)
        blocks.append((start, text[start:end]))

    votes = []
    motion_no = 0
    for start, part in blocks:
        if not re.match(r"\s*Motion:", part, re.I):
            continue
        # block extends to next Motion: . Trim trailing huge narrative
        block = part
        # cut the block at the result sentence + a little, to avoid pulling next-item names
        cut = re.search(r"(THE\s+)?MOTION\s+(CARRIED|PASSED|FAILED)[^\n]*?(?:\.|\n)",
                        block, re.I)
        if not cut:
            cut = re.search(r"Motion\s+(Passed|Failed|Carried)[^\n]*", block, re.I)
        tail = block[:cut.end() + 60] if cut else block[:1200]

        is_structured = bool(re.search(r"\bYes\s*:", tail)) or bool(
            re.search(r"Motion\s+(Passed|Failed)\s+\d", tail, re.I))
        has_inline_vote = bool(re.search(
            r"VOTED\s+(AYE|YES|NAY|NO)|VOTED\s+IN\s+(FAVOR|SUPPORT|THE\s+AFFIRMATIVE|"
            r"OPPOSITION|THE\s+NEGATIVE)|VOTED\s+AGAINST|ABSTAINED|"
            r"(?:WAS|WERE)\s+(?:ABSENT|EXCUSED)|CARRIED|PASSED|FAILED", tail, re.I))
        # skip "Motion:" lines that are not actual recorded votes
        if not has_inline_vote and not is_structured:
            continue

        mover, seconder = extract_mover_seconder(block)
        result, _verb = find_result(tail)

        # If a member changed their vote mid-motion, only the FINAL roll call counts.
        vote_src = tail
        if re.search(r"CHANGED\s+(?:HER|HIS|THEIR)\s+VOTE", tail, re.I):
            rolls = list(re.finditer(r"ROLL\s+CALL\s+WENT\s+AS\s+FOLLOWS", tail, re.I))
            if rolls:
                vote_src = tail[rolls[-1].end():]

        if is_structured:
            lists = extract_votes_structured(vote_src)
            if not any(lists.values()):
                lists = extract_votes_inline(vote_src)
        else:
            lists = extract_votes_inline(vote_src)

        names_recorded = any(lists[k] for k in ("aye", "nay", "abstain"))
        mtext = motion_text(block)

        # body: separate-meeting default, overridden by any in-meeting capacity change
        # active at this motion's position in the document.
        body = body_at(start, default_body, cap_events)

        motion_no += 1
        votes.append({
            "motion_no": motion_no,
            "body": body,
            "motion": mtext,
            "motion_type": classify(mtext),
            "result": result or "(result not captured)",
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": lists["aye"],
            "nay": lists["nay"],
            "abstain": lists["abstain"],
            "absent": lists["absent"],
            "recuse": lists["recuse"],
        })
    return votes


def attendance(md_path):
    """Pull the Present/Absent header roster (canonical surnames) for roster building."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    head = text[:2500]
    present, absent = set(), set()
    # find a Present ... Absent header region
    for m in re.finditer(r"(Mayor|Council\s*member|Councilmember)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                         head):
        n = norm_name(m.group(0))
        if n:
            present.add(n)
    return present, absent


def main():
    md_files = sorted(MIN_DIR.rglob("*.md"))
    rows = []
    roster = {}  # year -> set of surnames seen in votes/attendance
    summary = {"files": 0, "motions": 0, "named": 0, "tally_only": 0,
               "contested": 0, "member_rows": 0,
               "by_body": {}, "contested_by_body": {}}

    for md in md_files:
        rel = md.relative_to(ROOT).as_posix()  # minutes/....
        source = f"meeting_minutes/{rel}"
        parts = md.parts
        year = parts[-3]
        week = parts[-2]
        date = md.name.split("_", 1)[0]
        slug = md.name.split("_", 1)[1].rsplit(".", 1)[0]
        title = derive_title(md)
        default_body = file_body(title)

        votes = process_file(md, default_body=default_body)
        # build per-meeting JSON (body after title; names_recorded as a flag)
        jvotes = []
        for v in votes:
            jv = {"motion_no": v["motion_no"], "body": v["body"]}
            for k in ("motion", "motion_type", "result", "mover", "seconder"):
                jv[k] = v[k]
            jv["names_recorded"] = v["names_recorded"]
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                jv[k] = v[k]
            jvotes.append(jv)
        out_json = VOTES_DIR / year / week / f"{date}_{slug}.json"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(
            {"date": date, "title": title, "body": default_body,
             "source": source, "votes": jvotes},
            indent=2, ensure_ascii=False), encoding="utf-8")

        summary["files"] += 1
        ry = roster.setdefault(year, set())
        pres, _ = attendance(md)
        ry |= pres
        for v in votes:
            summary["motions"] += 1
            summary["by_body"][v["body"]] = summary["by_body"].get(v["body"], 0) + 1
            if v["names_recorded"]:
                summary["named"] += 1
            else:
                summary["tally_only"] += 1
            if v["nay"] or v["abstain"]:
                summary["contested"] += 1
                summary["contested_by_body"][v["body"]] = \
                    summary["contested_by_body"].get(v["body"], 0) + 1
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                for member in v[k]:
                    ry.add(member)
            # emit long rows for every member appearing in any list
            votemap = [("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                       ("absent", "Absent"), ("recuse", "Recuse")]
            for key, label in votemap:
                for member in v[key]:
                    summary["member_rows"] += 1
                    rows.append({
                        "date": date, "year": year, "title": title, "body": v["body"],
                        "motion_no": v["motion_no"], "motion": v["motion"],
                        "motion_type": v["motion_type"], "result": v["result"],
                        "mover": v["mover"] or "", "seconder": v["seconder"] or "",
                        "member": member, "vote": label, "source": source,
                    })

    rows.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    with ALL_VOTES_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "year", "title", "body", "motion_no",
                                          "motion", "motion_type", "result", "mover",
                                          "seconder", "member", "vote", "source"])
        w.writeheader()
        w.writerows(rows)

    # roster file
    roster_out = {y: sorted(s) for y, s in sorted(roster.items())}
    (VOTES_DIR / "_roster_by_year.json").write_text(
        json.dumps(roster_out, indent=2), encoding="utf-8")

    print(json.dumps({**summary, "roster": {y: len(s) for y, s in roster_out.items()}},
                     indent=2))


def derive_title(md):
    text = md.read_text(encoding="utf-8", errors="replace")
    first = text.splitlines()[0] if text else ""
    m = re.match(r"#\s*(.*?)\s*[—-]\s*\d{4}-\d{2}-\d{2}", first)
    if m:
        return m.group(1).strip()
    return md.name.split("_", 1)[1].rsplit(".", 1)[0].replace("-", " ").title()


if __name__ == "__main__":
    main()
