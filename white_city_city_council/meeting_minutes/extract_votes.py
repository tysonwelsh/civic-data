#!/usr/bin/env python3
"""
extract_votes.py — White City Council / Planning Commission vote extraction
(PURE deterministic; no LLM, no network; resumable — skips meetings whose JSON
exists unless --force).

White City is a 5-member VOTING body across BOTH governance eras:
  * 2017-04 .. 2024-04  White City METRO TOWNSHIP — 5 at-large councilmembers, one
    selected as CHAIR who carries the courtesy title "Mayor" (Paulina Flint) and
    VOTES as a member.
  * 2024-05 .. present   CITY (mayor-council form; HB35) — directly-elected executive
    Mayor (Allan Perry, 2026+) who ALSO VOTES.
Either way MAX TALLY = 5 (mayor/chair + 4 members).  ALL AT-LARGE (no districts).

THREE vote-recording formats across the record — the parser handles all three:

 A) NARRATIVE-TALLY (2017-2025, dominant).  Mover-first grammar:
      "Council Member Price, seconded by Council Member Cutler, moved to adopt ...
       The motion passed unanimously."
    Named dissent (2020-2021, Scott Little):
      "... The motion passed 4 to 1, showing Council Member Little voted 'Nay'."
      "... The motion passed 3 to 1, showing Council Member Little voting in opposition."
    Named abstention (trailing):
      "The motion passed unanimously. Council Member Little abstained from the vote."
    -> the DISSENTER/ABSTAINER is named; the majority is NOT individually named
       (tally-only majority).  The printed tally ("X to Y") is the verbatim result.

 B) NAMED ROLL CALL (2026+, city era).  Per-member line, the Mayor included:
      "Mayor Allan Perry  Aye / Council Member Neil Mahoney Aye / ...  The motion
       passed unanimously."  -> every voter named, MAX 5.

 C) CHECKBOX ROLL-CALL TABLE (a single 2019 resolution-adoption certification):
      "AYE  NAY  ABSENT  ABSTAIN ; Councilmember Cutler ____ ____ _X__ ____ ; ..."
    -> the X column gives each member's vote.

CARDINAL RULE — never fabricate.  A tally-only majority is left UNNAMED (blank member,
placeholder row); only voters the source actually names are emitted.  "failed for lack
of a second" never came to a vote -> skipped.  An unresolvable name is left BLANK.
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
# Roster — surname(lower) -> canonical full display name.  The chair/mayor VOTES
# in BOTH eras (max ordinary tally = 5).  All at-large; no districts.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "dickerson": "Kay Dickerson",
    "price":     "Linda Price",
    "perry":     "Allan Perry",     # councilmember 2019-2025 -> elected Mayor 2026
    "cutler":    "Cody Cutler",
    "flint":     "Paulina Flint",   # Chair / courtesy "Mayor" 2018-2025 (VOTES)
    "little":    "Scott Little",
    "shelton":   "Greg Shelton",
    "cardenaz":  "Phillip Cardenaz",
    "huish":     "Tyler Huish",
    "mahoney":   "Neil Mahoney",
}
# people who hold(held) the voting chair/mayor seat (for the mayor-vote report);
# Perry only from the city-mayor era (2026-01+), handled date-aware below.
MAYOR_CHAIR = {"Paulina Flint", "Allan Perry"}

# OCR / spelling variants -> canonical surname key
SURNAME_ALIASES = {
    "cardenas": "cardenaz", "cardenez": "cardenaz",
    "culter": "cutler", "cutier": "cutler",
    "dickersen": "dickerson", "dickinson": "dickerson",
    "mahony": "mahoney", "mahoncy": "mahoney",
    "sheiton": "shelton", "sbelton": "shelton",
    "huish": "huish", "hulsh": "huish",
    "flit": "flint", "fint": "flint",
    "prlce": "price",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())
FIRST_TO_SUR = {full.split()[0].lower(): sur for sur, full in SURNAME_TO_FULL.items()}

ROLE_WORDS = (r"Council\s*Members?|Councilmembers?|Council\s*Mem\w*|Board\s*Members?|"
              r"Mayor|Chair(?:man|person|woman)?|Vice[\s-]?Chair(?:man|person)?|Council")


def canon(token):
    """Map a name fragment to a roster full name, or None."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip().lower()
    if not t:
        return None
    words = [w for w in re.split(r"\s+", t) if len(w) >= 2]
    if not words:
        return None
    for w in reversed(words):
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
        if w2 in FIRST_TO_SUR:
            return SURNAME_TO_FULL[FIRST_TO_SUR[w2]]
    for w in reversed(words):
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.82)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — shared collection taxonomy.
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt|accept", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|approve the "
                 r"agenda|reorder|work ?(?:meeting|session)|workshop|closed session|"
                 r"closed meeting|executive session|\btable\b|continue the|postpone|"
                 r"suspend the rules|go into (?:a )?closed)\b", t):
        return "Procedural/Administrative"
    if re.search(r"mayor pro tem|pro-tem|pro tempore", t):
        return "Appointment"
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|"
                 r"\bplat\b|conditional use|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|street vacation|"
                 r"\badu\b|dadu|accessory dwelling|density|setback", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"tentative budget|final budget|adopt\w*.*budget|budget for|"
                 r"appropriat|certified tax rate|property tax", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement|"
                 r"master interlocal", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|board of canvassers|"
                 r"nominat|swear", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|license agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating|oath of office", t):
        return "Ceremonial"
    return "Other"


# ---------------------------------------------------------------------------
# PRESENT-block parsing (context / >5 outlier check; never used to NAME a voter
# on a tally-only motion).  Two header styles: the township "COUNCIL MEMBERS
# PRESENT:" block and the 2025+ "City Council: Council Member X" block.
# ---------------------------------------------------------------------------
def parse_present(flat):
    m = re.search(r"\bPRESENT\b|City\s+Council\s*:", flat, re.I)
    start = m.end() if m else 0
    e = re.search(r"OTHERS?\s+IN\s+ATTENDANCE|Staff\s*:|EXCUSED|Workshop|WORKSHOP|"
                  r"called\s+the\s+(?:meeting|workshop)|BUSINESS\s+MEETING|presided",
                  flat[start:], re.I)
    region = flat[start: start + (e.start() if e else 600)]
    present = []
    for sn in SURNAMES:
        for mm in re.finditer(r"\b" + sn + r"\b", region, re.I):
            tail = region[mm.end(): mm.end() + 30].lower()
            if re.search(r"\bexcused|\babsent", tail):
                continue
            nm = SURNAME_TO_FULL[sn]
            if nm not in present:
                present.append(nm)
            break
    return present


# ---------------------------------------------------------------------------
# Name anchoring
# ---------------------------------------------------------------------------
NAME = r"([A-Z][A-Za-z'\.\-]{2,}(?:\s+[A-Z][A-Za-z'\.\-]{2,})?)"
ROLEG = r"(?:" + ROLE_WORDS + r")"

MOVE_CONT = (r"to|that|for|approv|deny|denial|adopt|accept|open|close|continu|"
             r"recess|adjourn|reconvene|table|forward|recommend|ratify|nominat|"
             r"appoint|reappoint|amend|authoriz|direct|grant|support|instruct|make|"
             r"schedule|suspend|set|call|hold|postpone|delete|add|remove|approve")

# Form A (mover-first): "<A>[,] seconded by [role] <B>[,] moved|motioned [to ...]"
MOVER_FIRST = re.compile(
    r"(?:Motion\s*:?\s*)?" + ROLEG + r"\s+" + NAME +
    r"\s*,?\s*seconded\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"\s*,?\s*(?:moved|motioned)\b", re.I)

# Form B (moved-first / MOVED caps): "<A> moved|motioned|MOVED to ..."
MOVED_FIRST = re.compile(
    ROLEG + r"\s+" + NAME + r"\s+(?:moved|motioned|MOVED)"
    r"(?=\s+(?:in\s+a\s+substitute\s+motion\s+)?(?:" + MOVE_CONT + r")\b)", re.I)

SECOND_RE = re.compile(
    r"(?:The\s+motion\s+was\s+)?[Ss][Ee][Cc][Oo][Nn][Dd][Ee][Dd]\s+by\s+" +
    ROLEG + r"?\s*" + NAME +
    r"|" + ROLEG + r"\s+" + NAME + r"\s+seconded", re.I)

OUTCOME_RE = re.compile(
    r"[Tt]he\s+motion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))"
    r"|[Mm]otion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))"
    r"|[Tt]he\s+motion\s+was\s+(approved|denied)", re.I)

LACK_SECOND = re.compile(
    r"(?:fail\w*|die[sd]?)\s+(?:due\s+to|for)\s+(?:the\s+|a\s+)?lack\s+of\s+a?\s*second"
    r"|for\s+lack\s+of\s+(?:a\s+)?second|(?:received|was)\s+no\s+second", re.I)

UNANIMOUS = re.compile(r"unanimous", re.I)
# printed tally — White City prints it as the WORD form "passed 4 to 1"; the hyphen
# form is NEVER used for tallies (hyphens are resolution/ordinance numbers, so a
# hyphen pattern would false-match "21-12-01" -> "1-1").  Bound digits to 0..5 (max
# seat = 5) and require the literal word "to".
TALLY_RE = re.compile(r"\b([0-5])\s+to\s+([0-5])\b|\b([0-5])\s+in\s+favor\s+and\s+([0-5])\s+opposed")

# Named dissent/abstention in narrative:
#   "showing/with Council Member <Name> voted 'Nay' / voting in opposition / voted in
#    opposition / opposed / abstained"
NAMED_DISSENT = re.compile(
    r"(?:showing|with)?\s*(?:that\s+)?" + ROLEG + r"\s+" + NAME +
    r"\s+(?:voted|voting)\s+(?:“|\"|')?\s*"
    r"(nay|no|in\s+opposition|against|“nay”|aye|yes|in\s+favor)", re.I)
NAMED_OPPOSED = re.compile(
    ROLEG + r"\s+" + NAME + r"\s+(?:voted\s+in\s+opposition|voting\s+in\s+opposition|"
    r"in\s+opposition|opposed|dissent\w*|cast(?:ing)?\s+the\s+opposing\s+vote)", re.I)
# dissenter LIST: "showing that Mayor Flint, Council Member Little, and Council Member
# Cardenaz, voted in opposition" (T3.1(g) 2026-07-12 — the single-name handlers above
# dropped all 3 of m267's named Nays)
_WC_ITEM = ROLEG + r"\s+[A-Z][A-Za-z.'\-]+"
OPPOSED_LIST = re.compile(
    r"(" + _WC_ITEM + r"(?:\s*,\s*(?:and\s+)?" + _WC_ITEM + r")*"
    r"(?:\s*,?\s+and\s+" + _WC_ITEM + r")?)\s*,?\s+vot(?:ed|ing)\s+in\s+opposition", re.I)
NAMED_ABSTAIN = re.compile(
    ROLEG + r"\s+" + NAME + r"\s+abstain\w*", re.I)

# 2026 named roll call line: "(Mayor|Council Member) <Name> Aye|Nay|Absent|Abstain"
ROLLCALL_LINE = re.compile(
    r"(?:Mayor|Council\s*Member|Councilmember|Chair)\s+([A-Z][A-Za-z'\.\-]+"
    r"(?:\s+[A-Z][A-Za-z'\.\-]+){0,2}?)\s+(Aye|Nay|Absent|Abstain|Abstained|"
    r"Recuse[d]?|Yes|No|Present)\b", re.I)


def norm_rc(tok):
    t = tok.lower()
    if t in ("aye", "yes"):
        return "Aye"
    if t in ("nay", "no"):
        return "Nay"
    if t.startswith("abstain"):
        return "Abstain"
    if t.startswith("recuse"):
        return "Recuse"
    if t == "absent":
        return "Absent"
    return None


def parse_rollcall(region):
    """2026-style: pair each roster name with its Aye/Nay/... token.  Returns dict
    name->vote if >=3 distinct roster voters found (a real roll call), else {}."""
    members = {}
    for m in ROLLCALL_LINE.finditer(region):
        nm = canon(m.group(1))
        v = norm_rc(m.group(2))
        if nm and v:
            members[nm] = v
    return members if len(members) >= 3 else {}


def clean_motion_text(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:Motion\s*:?\s*)", "", s, flags=re.I)
    s = re.sub(r"\s*,?\s*seconded\s+by\s+.*$", "", s, flags=re.I)
    s = re.sub(r"^(?:the\s+)?motion\s*:?\s*", "", s, flags=re.I)
    s = s.strip(" .,;:")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def build_result(names_recorded, ayes, nays, tally, passed, unanimous):
    outcome = "Pass" if passed else "Fail"
    if tally:
        return f"{tally[0]}-{tally[1]} {outcome}"
    if names_recorded:
        return f"{ayes}-{nays} {outcome}"
    if unanimous:
        return f"{outcome} (unanimous)"
    return outcome


# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"\x0c|White\s+City\s+Council\s+Meeting\s+Minutes\s*[–-]\s*Page\s+\d+|"
    r"DATE\s+THURSDAY\b.*?\d{4}", re.I)


def split_frontmatter(raw):
    parts = re.split(r"\n\s*---\s*\n", raw, maxsplit=2)
    head = parts[0] + (parts[1] if len(parts) > 1 else "")
    body = parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 else raw)
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    body_tag = bm.group(1) if bm else "Council"
    fmt = re.search(r"\*\*Format:\*\*\s*(\w+)", head)
    return body_tag, body, (fmt.group(1) if fmt else "text")


def find_motions(flat):
    """Yield (start, mover, seconder_or_None, action_start) for each motion anchor."""
    anchors = []
    for m in MOVER_FIRST.finditer(flat):
        mover = canon(m.group(1))
        seconder = canon(m.group(2))
        if mover:
            anchors.append((m.start(), mover, seconder, m.end()))
    for m in MOVED_FIRST.finditer(flat):
        mover = canon(m.group(1))
        if mover:
            anchors.append((m.start(), mover, None, m.end()))
    anchors.sort(key=lambda a: a[0])
    out = []
    for a in anchors:
        if out and abs(a[0] - out[-1][0]) < 8:
            continue
        out.append(a)
    return out


def extract_meeting(path, rel_source, date, year, title, file_body):
    raw = open(path, encoding="utf-8").read()
    _bt, body, fmt = split_frontmatter(raw)
    flat = FOOTER_RE.sub(" ", body)
    flat = re.sub(r"\s+", " ", flat)
    present = parse_present(flat)

    body_code = "PlanningCommission" if file_body.lower().startswith("planning") else "Council"
    anchors = find_motions(flat)
    votes = []
    for i, (astart, mover, sec0, aend) in enumerate(anchors):
        nxt = anchors[i + 1][0] if i + 1 < len(anchors) else len(flat)
        region = flat[aend:nxt]

        seconder = sec0
        if not seconder:
            sm = SECOND_RE.search(region[:200])
            if sm:
                seconder = canon(sm.group(1) or sm.group(2))

        om = OUTCOME_RE.search(region)
        lm = LACK_SECOND.search(region)
        # died for lack of a second -> a REAL motion that never came to a vote —
        # record it as Died (T3.1(g) 2026-07-12: the old skip dropped 7 died motions,
        # and a [:om.start()+30] slice truncated the lack-phrase mid-match so 6 more
        # slipped through as bare "Fail")
        if lm and (om is None or lm.start() < om.start() or lm.start() - om.start() < 60):
            motion_text = clean_motion_text(region[:lm.start()])
            if len(motion_text) >= 3:
                votes.append({
                    "motion": motion_text[:600],
                    "body": body_code,
                    "motion_type": classify_motion(motion_text),
                    "result": "Died (no second)",
                    "mover": mover, "seconder": None,
                    "names_recorded": False, "vote_mode": "none",
                    "aye": [], "nay": [], "abstain": [], "recuse": [], "absent": [],
                })
            continue
        if not om:
            continue

        outcome_word = next((g for g in om.groups() if g), "").lower()
        passed = not (outcome_word.startswith("fail") or outcome_word.startswith("did")
                      or outcome_word == "denied")

        motion_text = clean_motion_text(region[:om.start()])
        if len(motion_text) < 3:
            motion_text = clean_motion_text(region[:200])

        # look-window after the outcome for tally / named dissent / trailing abstain /
        # a roll-call block
        post = region[om.start(): om.start() + 600]
        vote_mode = "narrative"

        members = {}
        rc = parse_rollcall(region[max(0, om.start() - 400): om.start() + 600])
        if rc:
            members = rc
            vote_mode = "rollcall"
            passed = sum(1 for v in members.values() if v == "Aye") > \
                     sum(1 for v in members.values() if v == "Nay") if members else passed
        else:
            # tally "X to Y" immediately after "passed/failed"
            tally = None
            tm = TALLY_RE.search(post[:60])
            if tm:
                g = [x for x in tm.groups() if x is not None]
                tally = (int(g[0]), int(g[1]))
            # named dissent / opposition
            for m in NAMED_DISSENT.finditer(post):
                nm = canon(m.group(1))
                val = m.group(2).lower()
                if not nm:
                    continue
                if "opposition" in val or val in ("nay", "no", "against") or "nay" in val:
                    members[nm] = "Nay"
                elif val in ("aye", "yes") or "favor" in val:
                    members.setdefault(nm, "Aye")
            for m in NAMED_OPPOSED.finditer(post):
                nm = canon(m.group(1))
                if nm:
                    members[nm] = "Nay"
            for m in OPPOSED_LIST.finditer(post):
                for piece in re.split(r"(?=" + ROLEG + r")", m.group(1)):
                    piece = piece.strip(" ,")
                    if not piece:
                        continue
                    nm = canon(re.sub(r"^" + ROLEG + r"\s+", "", piece, flags=re.I))
                    if nm:
                        members[nm] = "Nay"
            for m in NAMED_ABSTAIN.finditer(post):
                nm = canon(m.group(1))
                if nm:
                    members[nm] = "Abstain"
            if members:
                vote_mode = "narrative-named-dissent"

        unanimous_printed = bool(UNANIMOUS.search(post[:120]))
        names_recorded = bool(members)

        aye = sorted(n for n, v in members.items() if v == "Aye")
        nay = sorted(n for n, v in members.items() if v == "Nay")
        abstain = sorted(n for n, v in members.items() if v == "Abstain")
        recuse = sorted(n for n, v in members.items() if v == "Recuse")
        absent = sorted(n for n, v in members.items() if v == "Absent")

        # result string — verbatim-faithful: a printed roll-call gives counts; a printed
        # "X to Y" tally is quoted as-is; a printed "unanimous" is quoted as such (a named
        # abstention is recorded as its own row but does NOT overwrite the clerk's
        # "unanimous" wording); otherwise the bare outcome.
        tally = None
        if vote_mode != "rollcall":
            tm = TALLY_RE.search(post[:60])
            if tm:
                g = [x for x in tm.groups() if x is not None]
                tally = (int(g[0]), int(g[1]))
        ayes, nays = len(aye), len(nay)
        outcome = "Pass" if passed else "Fail"
        if vote_mode == "rollcall":
            result = f"{ayes}-{nays} {outcome}"
        elif tally:
            result = f"{tally[0]}-{tally[1]} {outcome}"
        elif unanimous_printed:
            result = f"{outcome} (unanimous)"
        elif names_recorded:
            result = f"{ayes}-{nays} {outcome}"
        else:
            result = outcome

        present_count = len(present) if not names_recorded else None
        mayor_voted = any(
            n == "Paulina Flint" or (n == "Allan Perry" and date >= "2026-01-01")
            for n in (aye + nay + abstain + recuse + absent))

        rec = {
            "motion": motion_text,
            "body": body_code,
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": names_recorded,
            "vote_mode": vote_mode,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
            "mayor_voted": mayor_voted,
        }
        if not names_recorded:
            rec["tally_only"] = {"unanimous": unanimous_printed,
                                 "present_count": present_count,
                                 "tally": list(tally) if tally else None}
        votes.append(rec)

    for n, v in enumerate(votes, 1):
        v_no = {"motion_no": n}
        v_no.update(v)
        votes[n - 1] = v_no

    return {
        "date": date, "year": int(year), "title": title,
        "file_body": body_code, "format": fmt, "present": present,
        "source": rel_source, "votes": votes,
    }


# ---------------------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.replace("\\", "/").split("/")   # .../minutes/<year>/<date>/<file>.md
    sub = parts[-2]
    return os.path.join(VOTES_DIR, str(year), sub, parts[-1].replace(".md", ".json"))


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    for r in rows:
        # path in index is relative to city root; MIN files live under this dataset
        p = r["path"]
        # strip the dataset prefix to locate on disk relative to ROOT
        rel = re.sub(r"^(meeting_minutes|planning_commission)/", "", p)
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("MISSING", p, file=sys.stderr)
            continue
        jp = json_path_for(rel, r["year"])
        if os.path.exists(jp) and not FORCE:
            continue
        try:
            meeting = extract_meeting(path, p, r["date"], r["year"], r["title"],
                                      "PlanningCommission" if "planning_commission" in p
                                      else "Council")
        except Exception as e:
            print("PARSE ERROR", p, e, file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        json.dump(meeting, open(jp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    rebuild_csv(rows)
    build_roster(rows)
    print("done")


def rebuild_csv(rows):
    # provenance (trailing 14th column, collection standard for PMN-recovered rows):
    #   minutes     = audited primary (Streamline-published minutes)
    #   pmn_minutes = recovered from Utah Public Notice (index source == 'pmn')
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in rows:
        rel = re.sub(r"^(meeting_minutes|planning_commission)/", "", r["path"])
        jp = json_path_for(rel, r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        prov = "pmn_minutes" if r.get("source") == "pmn" else "minutes"
        for v in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=obj["title"],
                        body=v["body"], motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v.get("mover", ""), seconder=v.get("seconder", ""),
                        source=obj["source"], provenance=prov)
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
    seen = {}
    for r in rows:
        rel = re.sub(r"^(meeting_minutes|planning_commission)/", "", r["path"])
        jp = json_path_for(rel, r["year"])
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
    ROLE = {
        "Paulina Flint": "Chair/'Mayor' (voting), township era 2018-2025",
        "Allan Perry":   "Council at-large 2018-2025 -> elected Mayor 2026+ (voting)",
        "Neil Mahoney":  "Council at-large 2026+ (Mayor Pro-Tem)",
    }
    def role(nm):
        return ROLE.get(nm, "Council (at-large)")
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, role(nm), d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
