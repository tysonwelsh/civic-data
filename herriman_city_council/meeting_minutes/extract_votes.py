#!/usr/bin/env python3
"""
extract_votes.py — Herriman City Council / CDRA / Planning Commission vote
extraction (PURE deterministic; NO LLM, NO network).  One file, installed in both
meeting_minutes/ and planning_commission/; the governing body is read per-file from
the markdown front-matter `**Body:**` field, so the same code serves both datasets.

Reads the minutes markdown listed in this dataset's minutes_index.csv, finds each
recorded motion (mover / seconder / named roll call or short-form unanimous), and
emits:
  - one JSON per meeting  -> votes/<year>/<week>/<file>.json   (resumable; --force to redo)
  - a rebuilt long CSV    -> all_votes.csv   (13-col SCHEMA_SPEC §2)
  - roster.csv            -> observed voters (member,role,first_seen,last_seen,n_votes)

HERRIMAN VOTE GRAMMAR (born-digital minutes, 2020 S3 + 2021+ PrimeGov)
---------------------------------------------------------------------
  A) Named roll call (dominant):
        Councilmember Shields moved to approve Ordinance No 2025-01 ...
        Councilmember Hodges seconded the motion.
        The vote was recorded as follows:
        Councilmember Jared Henderson            Aye
        Councilmember Teddy Hodges               Aye
        Councilmember Sherrie Ohrn               Aye
        Councilmember Steven Shields             Aye
        Mayor Lorin Palmer                       Aye
        The motion passed unanimously.
     Each roll-call row is "<role> <Full Name>   <Vote>"; the FULL name is taken
     verbatim (clean text) — no surname guessing on vote rows.  A page-header/footer
     line ("September 8, 2021 – City Council Minutes  Page 11 of 12") can fall BETWEEN
     two roll-call rows, so the block is scanned from "recorded as follows" all the way
     to the outcome sentence, skipping non-matching lines.
     Contested: "The motion failed with a vote 3:2." / "passed with a vote 4:1" — Nay
     rows are named in the same table.
  B) Short-form unanimous (no names): "... seconded the motion, and all [present ]voted
     aye." (PC: "Seconded by Commissioner X and all voted Aye.") -> names_recorded:false,
     one tally-only placeholder row (member/vote blank).  Never fabricates the 4-5 names.
  C) Absent named in the outcome prose ("... passed unanimously with Mayor Watts being
     absent") -> that member is recorded Absent (named, faithful) when resolvable.
  D) "failed for lack of a second" -> recorded motion, no vote (never came to a vote).

THE MAYOR VOTES.  Herriman is a council-mayor form in which the separately-elected
Mayor is a full voting member: every named roll call includes "Mayor <Name>  Aye/Nay"
(max ordinary tally = 5 = 4 districts + mayor), confirmed 2021 (Watts) and 2025
(Palmer).  The mayor is NEVER excluded (unlike West Jordan / South Jordan).  When the
mayor is absent the roll shows the 4 councilmembers only.  [This corrects recon.md,
which mis-read the mayor as non-voting from unanimous samples that happened to elide or
omit the mayor row.]  CDRA/PC use "Board Member"/"Chair"/"Commissioner"/"Alternate" —
all mapped to the same people; the mayor sits as CDRA Chair.
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# role is matched case-insensitively (inline (?i:)); NAME captures are strictly
# case-SENSITIVE (proper-noun tokens starting uppercase) — a global re.I would let
# [A-Z] match lowercase filler words like "and"/"being" (a real source typo:
# "Councilmember Hodges and being absent").
ROLE = (r"(?i:Councilmembers?|Council\s+Members?|Commissioners?|Alternate|"
        r"Vice[\s-]?Chair(?:man|woman|person)?|Chair(?:man|woman|person)?|"
        r"Mayor(?:\s+Pro\s+Tem)?|Board\s+Members?|Trustees?|Directors?)")
NAME = r"[A-Z][a-zA-Z.'\-]+(?:[ \t]+[A-Z][a-zA-Z.'\-]+){0,2}"
VOTE_WORDS = r"(?i:Ayes?|Nays?|Yea|Yes|No|Abstain(?:ed)?|Absent|Recuse[d]?|Excused)"

# One roll-call row: "<role> <Full Name>   <Vote>".  The vote token is anchored to
# END OF LINE (the aligned roll-call column) so a single-space separator is accepted
# — pdftotext collapses the column gap to one space when a long name fills the width
# ("Councilmember Jared Henderson Yes").  The mandatory role prefix + EOL vote token
# keep narrative sentences from matching.  Vote words vary: Aye/Nay AND Yes/No.
# In roll-call rows tolerate clerk misspellings of the role token (OCR/typo files print
# "Comissioner"/"Commisisoner"/"Commissioner Alternate ..."); a leading word starting
# "Com" is accepted as the role so a typo'd row is not silently dropped.  The role is
# consumed, never captured, so the NAME group stays clean.
ROLL_ROLE = r"(?:" + ROLE + r"|(?i:Com[a-z]+))"
# One roll-call row.  Between the name and the vote allow an optional "=" separator
# ("Forest Sickles = Aye"); after the vote allow a trailing parenthetical
# ("No (online)") — both are real votes some clerks annotate.
ROLLROW_RE = re.compile(
    r"^[ \t\f]*" + ROLL_ROLE + r"[ \t]+(" + NAME + r")[ \t]+(?:=[ \t]+)?(" + VOTE_WORDS
    + r")(?:[ \t]*\([^)\n]*\))?[ \t\f]*$",
    re.M,
)
# Roll-call header: council/PC print "The vote WAS recorded as follows"; the in-session
# CDRA minutes use present tense "The vote IS recorded as follows" (same table below,
# with Director/Chair roles) -> accept both tenses.
RECORDED_RE = re.compile(r"vote\s+(?:was|is)\s+recorded\s+as\s+follows", re.I)
# Outcome sentence: "The motion passed/failed …" and also the bare "Motion passed …"
# form (2026 PC PrimeGov minutes drop the leading "The").
# the outcome sentence runs to its period — it may WRAP across a line break
# ("The motion\npassed with a vote 3:2."), which the old [^\n.]* cut mid-phrase
# (11 wrap-truncated result strings; T3.1(j) 2026-07-12)
OUTCOME_RE = re.compile(
    r"(?:[Tt]he\s+)?[Mm]otion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))"
    r"(?:[^.\n]|\n(?![ \t]*\n))*", re.I)
ALLVOTED_RE = re.compile(r"\ball\s+(?:present\s+)?voted\s+(aye|yes|in\s+favor)", re.I)
# inline narrative roll (2021 era): "Mayor Watts, Councilmember Shields, and Councilmember
# Smith voted aye, and Councilmember Ohrn and Councilmember Henderson voted nay. The motion
# passed with a vote 3:2." — every list item is ROLE-prefixed, so prose can't leak in
# (T3.1(j) 2026-07-12: three 3:2 public-hearing votes carried 0 vote rows).
_NARR_ITEM = r"(?:" + ROLE + r")\s+[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+)?"
NARR_LIST_RE = re.compile(
    r"(" + _NARR_ITEM + r"(?:\s*,\s*(?:and\s+)?" + _NARR_ITEM + r")*"
    r"(?:\s*,?\s+and\s+" + _NARR_ITEM + r")?)"
    r"\s+voted\s+(aye|yes|nay|no|abstain\w*)\b", re.I)
LACK_SECOND_RE = re.compile(r"(?:fail\w*|died)\s+(?:due\s+to|for)\s+(?:a\s+)?lack\s+of\s+"
                            r"a?\s*second|for\s+lack\s+of\s+(?:a\s+)?second|no\s+second",
                            re.I)
# name is proper-case only (no re.I) so "and"/"being" can't be captured
ABSENT_PROSE_RE = re.compile(
    r"with\s+" + ROLE + r"?\s*([A-Z][a-z'\-]+(?:\s+[A-Z][a-z'\-]+)?)"
    r"\s+being\s+(?i:absent|excused)")

# Dropped-verb motion lead-in (source clerk typo, 2026-07-16): three real motions in
# the corpus print "<Role> <Name> to approve …" with the verb "moved" omitted
# (2021-08-11 Ordinances 2021-19 + 2021-21; 2023-08-02 PC item 4.1) — each followed by
# a genuine seconded sentence + full named roll call.  Healed by inserting "moved"
# BEFORE anchoring so MOVE_RE finds them; the emitted motion text is unchanged (it
# starts after the verb).  Line-anchored + role-prefixed + specific verbs so narrative
# ("asked Councilmember X to review") can never match.  Verified corpus-wide: exactly
# 3 occurrences, all real motions.
# NEGATIVE-LOOKAHEAD GUARD (2026-07-19): only fire when the motion verb is GENUINELY
# omitted.  Without it, NAME (which matches uppercase tokens) swallows an all-caps
# "MOVED"/"Moved" as a name token on the COMMON "<Role> <Name> MOVED to approve" line,
# so the healer double-inserts "moved" and the mover capture becomes "<Name> MOVED" ->
# resolve_person() blanks it.  This corrupted 58 movers on a --force / backfill
# re-extract (1 mm-audited, 51 pc-audited, 6 pmn-recovered — a latent non-idempotency:
# resumable JSON hid it for the audited layer, but the always-reparsed pmn layer already
# carried blank movers).  The lookahead rejects any line that already prints
# "<Role> <Name> moved/motioned", leaving a real "MOVED" line for MOVE_RE and healing
# ONLY a truly verb-less line (2021-08-11 council Ord 2021-19/-21; 2023-08-02 PC 4.1).
DROPPED_VERB_RE = re.compile(
    r"^(?![ \t]*" + ROLE + r"[ \t]+" + NAME + r"[ \t]+(?i:moved|motioned)\b)"
    r"([ \t]*" + ROLE + r"[ \t]+" + NAME + r")[ \t]+to[ \t]+"
    r"((?i:approve|adopt|deny|continue|table))\b", re.M)

# Motion lead-in: "<Role> <Name> moved/MOVED …" OR "<Name> motioned …".  The VERB is
# matched case-insensitively (inline (?i:…)) so uppercase "MOVED" (many 2021 PC files)
# and the synonym "motioned" (2025-26 PC PrimeGov style) both anchor a motion; the NAME
# capture stays case-SENSITIVE so lowercase filler words can't be grabbed as a name.
MOVE_RE = re.compile(r"(?:" + ROLE + r"[ \t]+)?(" + NAME + r")\s+(?i:moved|motioned)\b")
# Seconder: "seconded by <Name>" (name may be role-less, anchored on the left by "by")
# OR "<Role> <Name> seconded".  The trailing form REQUIRES a role prefix — without it a
# greedy NAME would swallow the tail of the preceding motion sentence ("…Fiscal Year
# Budget. Councilmember Shields seconded" -> "Budget. Councilmember Shields").  Verb
# case-insensitive to catch uppercase "SECONDED".
SECOND_RE = re.compile(
    r"(?i:seconded)\s+by\s+(?:" + ROLE + r"\s+)?(" + NAME + r")"
    r"|" + ROLE + r"\s+(" + NAME + r")\s+(?i:seconded)")


def norm_vote(w):
    w = w.lower()
    if w.startswith("aye") or w.startswith("yea") or w.startswith("yes"):
        return "Aye"
    if w.startswith("nay") or w.startswith("no"):
        return "Nay"
    if w.startswith("abstain"):
        return "Abstain"
    if w.startswith("recuse"):
        return "Recuse"
    if w.startswith("excused"):
        return "Excused"
    if w.startswith("absent"):
        return "Absent"
    return None


# Confident same-person spelling variants -> canonical (source typos where the target
# is unambiguous).  NOT included: "Lorin Powell" (a source typo blending the two real
# people who both sat on the 2020 PC — Commissioner Lorin Palmer and Chair Andy Powell;
# unresolvable, so it is kept verbatim as printed).
CANON_FULL = {
    "daryl fenn": "Darryl Fenn",     # Commissioner Fenn — first-name spelling variant
    "steve shields": "Steven Shields",  # HCFSA board minutes call him "Steve"; same person
    "forrest sickles": "Forest Sickles",  # double-r clerk typo of Commissioner Forest Sickles
    "adam jacobosn": "Adam Jacobson",   # transposition typo (mover line)
    "adam jacbson": "Adam Jacobson",    # dropped-'o' typo (roll row) — same commissioner
    "darryl finn": "Darryl Fenn",       # i-for-e typo (2021-06-17 PC roll row m7; the same
                                        # doc prints "Darryl Fenn" in 9 other rolls)
    "sheri ohrn": "Sherrie Ohrn",       # short-spelling variant (mover line)
}
# Surname-only spelling typos (mover/seconder captures that print just a misspelled
# surname) -> the canonical surname, which the corpus name map then upgrades to the full
# name.  Unambiguous same-person corrections only.
SUR_CANON = {
    "sheilds": "shields",     # Councilmember Steven Shields
    "henerson": "henderson",  # Councilmember Jared Henderson
    "garica": "garcia",       # Commissioner Heather Garcia
    "jacobosn": "jacobson",   # Commissioner Adam Jacobson
    "jacbson": "jacobson",    # dropped-'o' typo, same commissioner
    "sickle": "sickles",      # Commissioner Forest Sickles
}


def strip_title(name):
    n = re.sub(r"^(?:" + ROLE + r")\s+", "", name.strip(), flags=re.I)
    n = re.sub(r"\s+", " ", n).strip(" .,;:")
    return CANON_FULL.get(n.lower(), n)


# --------------------------------------------------------- global name map
def build_name_map(files):
    """surname(lower) -> full name, from every roll-call full name in the corpus.
    Ambiguous surnames (>1 full name) are dropped from the map so movers/seconders
    are never mis-resolved; unique ones let us upgrade surname-only movers to full."""
    by_sur = {}
    fulls = set()
    for path in files:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        for m in ROLLROW_RE.finditer(text):
            full = strip_title(m.group(1))
            toks = full.split()
            if len(toks) < 2:
                continue
            fulls.add(full)
            sur = toks[-1].lower()
            by_sur.setdefault(sur, set()).add(full)
    surmap = {s: next(iter(v)) for s, v in by_sur.items() if len(v) == 1}
    surnames = set(by_sur)  # every surname seen in a roll (incl. ambiguous ones)
    return surmap, fulls, surnames


NAME_MAP = {}       # unambiguous surname(lower) -> full name
FULLS = set()       # every full roll-call name in the corpus
SURNAMES = set()    # every surname (lower) seen in a roll, incl. ambiguous


def resolve(name):
    """Resolve a mover/seconder token to a full name via the corpus map; else return
    the cleaned token (surname) as-is.  (Used for absent-in-prose roll members.)"""
    if not name:
        return ""
    c = strip_title(name)
    toks = c.split()
    if len(toks) >= 2:
        return c
    sur = c.lower()
    return NAME_MAP.get(sur, c)


def resolve_person(name):
    """Resolve a MOVER/SECONDER capture to a clean roster name, or "" if it is not a
    real member (a motion-text fragment, a staff role, an unknown token).  Guards the
    db `person` table against over-capture pollution: every returned value is either a
    full corpus name, a known roster surname, or blank — never a sentence fragment.

    Scans trailing windows (last 2 tokens, then last 1) from the right so an
    over-captured prefix ("Budget. Councilmember Shields") is skipped down to the real
    name; applies the documented full-name / surname typo corrections."""
    if not name:
        return ""
    c = strip_title(name)                 # strip a LEADING role + CANON_FULL on the whole
    toks = c.split()
    if not toks:
        return ""
    for k in (2, 1):
        if len(toks) < k:
            continue
        tail = toks[-k:]
        cand = " ".join(tail)
        lc = cand.lower()
        if lc in CANON_FULL:              # documented full-name typo
            return CANON_FULL[lc]
        if k == 2 and cand in FULLS:      # exact corpus full name
            return cand
        if k == 1:
            sur = SUR_CANON.get(tail[0].lower(), tail[0].lower())
            if sur in NAME_MAP:           # unambiguous surname -> upgrade to full name
                return NAME_MAP[sur]
            if sur in SURNAMES:           # real but ambiguous surname -> keep verbatim
                return tail[0]
    return ""                            # not a resolvable member -> blank (never a fragment)


# --------------------------------------------------------- motion classify
def classify(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|approve the "
                 r"agenda|work meeting|work session|closed session|closed meeting|"
                 r"executive session|\btable\b|continue the|postpone|ratif\w*\s+the\s+"
                 r"agenda|consent agenda)\b", t):
        return "Procedural/Administrative"
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development "
                 r"agreement|overlay|site plan|street vacation|preliminary|final plat|"
                 r"planned (?:unit )?development|\bcup\b", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"tentative budget|final budget|adopt\w*.*budget|appropriat|"
                 r"certified tax rate|truth in taxation", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|liaison|canvass|nominat|mayor pro tem", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|task order|change order", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating|in memoriam", t):
        return "Ceremonial"
    return "Other"


def clean_motion(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:to\s+)?", "", s)
    s = re.sub(r"\s*,?\s*seconded\s+by\s+.*$", "", s, flags=re.I)
    s = re.sub(r"\s*\.?\s*(?:" + ROLE + r")\s+[A-Z][A-Za-z.'\-]+\s+seconded.*$", "", s,
               flags=re.I)
    s = s.strip(" .,;:")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def get_body(text):
    m = re.search(r"\*\*Body:\*\*\s*(\w+)", text[:600])
    return m.group(1) if m else "Council"


def parse_roll(block):
    """All (full_name, vote) rows in a roll-call block."""
    out = []
    seen = set()
    for m in ROLLROW_RE.finditer(block):
        full = strip_title(m.group(1))
        # upgrade a surname-only roll row (some 2020 files) to the full name
        if len(full.split()) == 1:
            full = NAME_MAP.get(full.lower(), full)
        v = norm_vote(m.group(2))
        if not v or not full or full in seen:
            continue
        seen.add(full)
        out.append((full, v))
    return out


def extract_meeting(path, rel_source, date, year, title):
    text = open(path, encoding="utf-8").read()
    body = get_body(text)
    # drop the front-matter header
    text = re.split(r"\n---\n", text, maxsplit=1)[-1]
    # heal the documented dropped-verb lead-ins (see DROPPED_VERB_RE) so those
    # motions anchor; motion text itself is captured after the verb, unchanged
    text = DROPPED_VERB_RE.sub(r"\1 moved to \2", text)

    # motion anchors = every "<name> moved"
    anchors = [m.start() for m in MOVE_RE.finditer(text)]
    anchors.sort()
    votes = []
    for i, a in enumerate(anchors):
        nxt = anchors[i + 1] if i + 1 < len(anchors) else len(text)
        region = text[a:nxt]
        mv = MOVE_RE.search(region)
        if not mv:
            continue
        after = region[mv.end():]

        # find the vote apparatus in this region
        rec = RECORDED_RE.search(region)
        allv = ALLVOTED_RE.search(region)
        out_m = OUTCOME_RE.search(region)

        # skip lack-of-second non-votes
        if LACK_SECOND_RE.search(region) and not rec:
            if not (out_m and re.search(r"passed|carried", out_m.group(0), re.I)):
                continue

        # motion text: from after "moved" up to seconded / recorded / all-voted / outcome
        cut = len(after)
        for c in (rec, allv, out_m, SECOND_RE.search(after)):
            pass
        cut_candidates = []
        for pat in (RECORDED_RE, ALLVOTED_RE, OUTCOME_RE, SECOND_RE):
            mm = pat.search(after)
            if mm:
                cut_candidates.append(mm.start())
        if cut_candidates:
            cut = min(cut_candidates)
        motion_text = clean_motion(after[:cut])
        if len(motion_text) < 3:
            continue

        # mover / seconder — resolved to a clean roster name or blank (never a fragment)
        mover = resolve_person(mv.group(1))
        seconder = ""
        sm = SECOND_RE.search(region)
        if sm:
            seconder = resolve_person(sm.group(1) or sm.group(2))

        # result string (verbatim outcome sentence) + vote rows
        result = ""
        if out_m:
            # a wrap-crossing outcome (T3.1) can swallow the NEXT PAGE's running
            # header across a form-feed page break ("... unanimously \x0c August 2,
            # 2023 Planning Commission Meeting Minutes  Page 6 of 9") — a result
            # sentence never spans a page break, so cut at the form-feed FIRST
            # (2026-07-19; the wrap-heal's page-header tail guard)
            result = re.sub(r"\s+", " ", out_m.group(0).split("\f")[0]).strip(" .")
            # cut a trailing NEW-SPEAKER narrative that follows a tally ("3:2
            # Councilmember Smith explained ...", "4:1 11"); require a CAPITALIZED
            # name after the role so a WORD-FORM tally clause is KEPT ("...and one
            # Commissioner abstaining" — 2026-07-19; the bare role-strip ate it);
            # "with/and <Role>" named-absence clauses stay, as before
            result = re.sub(r"\s+(?<!with )(?<!and )(?:" + ROLE + r")\s+[A-Z].*$", "", result)
            result = re.sub(r"\s+\d{1,3}$", "", result)

        members = []  # (name, vote)
        names_recorded = False
        if rec:
            end = out_m.start() if (out_m and out_m.start() > rec.end()) else len(region)
            block = region[rec.end():end]
            members = parse_roll(block)
        elif not allv:
            # header-less roll: some PC minutes drop the "recorded as follows" line and
            # list the roll rows directly after the seconded sentence.  Take the run of
            # aligned roll rows between the seconder (or mover) and the outcome; require
            # >=3 rows so a stray narrative line can never be mistaken for a roll call.
            start = sm.end() if sm else mv.end()
            end = out_m.start() if (out_m and out_m.start() > start) else len(region)
            cand = parse_roll(region[start:end])
            if len(cand) >= 3:
                members = cand
        if not members and not allv:
            # inline narrative roll ("<Role Name>, <Role Name> voted aye, and <Role
            # Name> voted nay") between the motion sentence and the outcome
            seg_start = sm.end() if sm else mv.end()
            seg_end = out_m.end() if out_m else len(region)
            seg = re.sub(r"\s+", " ", region[seg_start:seg_end])
            narr = []
            for lm in NARR_LIST_RE.finditer(seg):
                v = norm_vote(lm.group(2))
                if not v:
                    continue
                for piece in re.split(r"(?=" + ROLE + r")", lm.group(1)):
                    piece = re.sub(r"[,\s]*(?:\band\b)?[,\s]*$", "", piece.strip(" ,"))
                    if not piece:
                        continue
                    nm2 = resolve_person(piece)
                    if nm2 and nm2 not in [x[0] for x in narr]:
                        narr.append((nm2, v))
            if len(narr) >= 2:
                members = narr
        if members:
            names_recorded = True
            # absent named in the outcome prose
            if out_m:
                am = ABSENT_PROSE_RE.search(out_m.group(0))
                if am:
                    nm = resolve(am.group(1))
                    if nm and nm not in [x[0] for x in members]:
                        members.append((nm, "Absent"))
        if not names_recorded and allv:
            # short-form unanimous, no names
            result = result or "passed (all voted aye)"

        if not names_recorded and not allv and not out_m:
            continue  # not a real recorded motion

        if not result:
            result = "recorded (no tally)"

        rec_obj = {
            "motion_no": len(votes) + 1,
            "motion": motion_text,
            "body": body,
            "motion_type": classify(motion_text),
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": [n for n, v in members if v == "Aye"],
            "nay": [n for n, v in members if v == "Nay"],
            "abstain": [n for n, v in members if v == "Abstain"],
            "absent": [n for n, v in members if v == "Absent"],
            "recuse": [n for n, v in members if v == "Recuse"],
            "excused": [n for n, v in members if v == "Excused"],
        }
        votes.append(rec_obj)

    return {"date": date, "year": int(year), "title": title, "body": body,
            "source": rel_source, "votes": votes}


def json_path_for(rel_path, year):
    parts = rel_path.split("/")
    week = parts[-2]
    return os.path.join(VOTES_DIR, str(year), week, parts[-1].replace(".md", ".json"))


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    files = [os.path.join(ROOT, r["path"]) for r in rows]
    global NAME_MAP, FULLS, SURNAMES
    NAME_MAP, FULLS, SURNAMES = build_name_map(files)

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
            meeting = extract_meeting(path, r["path"], r["date"], r["year"], r["title"])
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        json.dump(meeting, open(jp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

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
                             ("absent", "Absent"), ("recuse", "Recuse"),
                             ("excused", "Excused")):
                for mem in v.get(key, []):
                    row = dict(base, member=mem, vote=lab)
                    out.append(row)
                    emitted = True
            if not emitted:
                out.append(dict(base, member="", vote=""))
    out.sort(key=lambda x: (x["date"], x["motion_no"]))
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
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
        date = obj["date"]
        for v in obj["votes"]:
            people = set()
            for k in ("aye", "nay", "abstain", "absent", "recuse", "excused"):
                people.update(v.get(k, []))
            for p in people:
                d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
                d["first"] = min(d["first"], date)
                d["last"] = max(d["last"], date)
                d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_votes"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, "", d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
