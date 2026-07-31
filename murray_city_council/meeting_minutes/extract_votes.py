#!/usr/bin/env python3
"""
Murray City Council vote extractor  (PURE deterministic — no LLM, no network).

Reads the council-meeting markdown under meeting_minutes/minutes/<year>/<week>/, parses
every recorded motion, resolves each named voter against the fixed council roster, and
emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<slug>.json  (resumable)
  - meeting_minutes/all_votes.csv   (13-col long format, one row per member-vote)
  - meeting_minutes/roster.csv      (OBSERVED members: member,first_seen,last_seen,n_votes)

MURRAY COUNCIL VOTE GRAMMAR (built to this; verified 2020->2026, both eras)
--------------------------------------------------------------------------
 A) PROSE roll call (2020-2023 dominant):
      "MOTION: Councilmember Cox moved to approve both sets of minutes. The motion was
       SECONDED by Councilmember Turner.
       Council roll call vote:
       Ayes: Councilmember Martinez, Councilmember Cox, Councilmember Dominguez
             Councilmember Turner and Councilmember Hales      (wraps across page footers)
       Nays: None
       Abstentions: None
       Motion passed 5-0"
    2023 lists FULL NAMES ("Ayes: Rosalba Dominguez, Diane Turner, ...") — resolver handles both.
 B) TABULAR roll call (2024-2026 dominant):
      "MOTION: Ms. Cotter moved ... Mr. Pickett SECONDED the motion.
       Council Roll Call Vote:
       Mr. Hock       Aye
       Ms. Cotter     Aye
       ...
       Motion passed: 5-0"
 C) VOICE-VOTE tally-only (no names):
      'Voice vote taken, all "ayes." Approved 5-0'  ->  ONE placeholder row, blank member/vote.
 D) NOMINATIONS:
    - prose confirm (Ayes: named) -> normal named roll call, result "X was elected ...".
    - candidate-selection roll call, prose ("Councilmember X voted in favor of Y.
      ... Philip Markham wins 3-2.") or tabular ("Mr. Hock  Mr. Hock" ... "Vote: 3-2 ...")
      -> members vote for PEOPLE, not Aye/Nay -> recorded TALLY-ONLY (result verbatim).
 E) DIED: "The motion was not seconded." / "MOTION FAILED: There was no second" -> no members.

COUNCIL COMPOSITION — the MAYOR DOES NOT VOTE (max roll = 5 = D1-D5, no at-large).
The mayor never appears in a roll call. NOTE: "Councilmember Hales" (Brett Hales, D5,
2020-2021) is a real council member and is DISTINCT from Mayor Brett A. Hales (mayor 2022+);
"Councilmember Philip Markham" (D1, 2023) shares a surname with PC Chair Phil Markham but is
a different roster (separate body/script).  Only the roster surnames below map to a vote;
guests (e.g. "Councilmember Ann Granato", a Salt Lake County councilmember) never do.
"""
import csv
import json
import re
import sys
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Roster (OBSERVED across 2020-2026).  surname / first-name -> canonical display.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "martinez": "Kat Martinez",       # D1 2020-2022
    "markham": "Philip Markham",      # D1 2023
    "pickett": "Paul Pickett",        # D1 2024+
    "rodgers": "David Rodgers",       # D1 (late)
    "cox": "Dale Cox",                # D2 2020-2021
    "cotter": "Pamela Cotter",        # D2 2022+
    "dominguez": "Rosalba Dominguez", # D3 2020-2024
    "goodman": "Scott Goodman",       # D3
    "bullen": "Clark Bullen",         # D3 2026
    "turner": "Diane Turner",         # D4 (throughout)
    "hales": "Brett Hales",           # D5 2020-2021 (later Mayor — kept as councilmember)
    "hrechkosy": "Garry Hrechkosy",   # D5 2022-2023
    "hock": "Adam Hock",              # D5 2024+
}
FIRST_TO_FULL = {
    "kat": "Kat Martinez", "philip": "Philip Markham", "phil": "Philip Markham",
    "paul": "Paul Pickett", "david": "David Rodgers", "dale": "Dale Cox",
    "pam": "Pamela Cotter", "pamela": "Pamela Cotter", "rosalba": "Rosalba Dominguez",
    "scott": "Scott Goodman", "clark": "Clark Bullen", "diane": "Diane Turner",
    "brett": "Brett Hales", "garry": "Garry Hrechkosy", "adam": "Adam Hock",
}
# OCR / clerk-typo surname variants -> canonical surname key
SURNAME_ALIASES = {
    "dominquez": "dominguez", "domingez": "dominguez", "dominguz": "dominguez",
    "hreckhosy": "hrechkosy", "hrechosy": "hrechkosy", "hrechkosky": "hrechkosy",
    "hale": "hales", "markam": "markham", "pikett": "pickett", "cotler": "cotter",
    "roaslaba": "rosalba",  # first-name typo, handled below
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())


def canon(chunk):
    """Resolve a name phrase to a canonical roster name, or None (never guesses)."""
    if not chunk:
        return None
    words = [w for w in re.split(r"[^A-Za-z']+", chunk.lower()) if len(w) >= 2]
    if not words:
        return None
    # 1) surname (exact / alias) — checked first so it wins over first-name collisions
    for w in words:
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    # 2) first name (exact / alias)
    for w in words:
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in FIRST_TO_FULL:
            return FIRST_TO_FULL[w2]
    # 3) fuzzy surname (OCR) on >=5-char words
    for w in words:
        if len(w) < 5:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.84)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — land-use checked FIRST.
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|design review|"
                 r"street vacation|\bvacat|redevelopment|project area|"
                 r"reinvestment|planned (?:unit )?development|\bpud\b|"
                 r"preliminary|final plat", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"tentative budget|final budget|adopt\w*.*budget|budget for|"
                 r"appropriat|certified tax rate", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat|"
                 r"chair|vice-chair|vice chair|elected", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|lease", t):
        return "Contract/Purchase"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating", t):
        return "Ceremonial"
    if re.search(r"\bminutes\b|adjourn|recess|reconvene|convene|amend the agenda|"
                 r"closed session|executive session|\btable\b|continue|postpone|"
                 r"consent agenda|approve the agenda|approve the order", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Line loading — strip page-break footers so wrapped roll-call lists flatten.
# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"^\s*(?:Murray City Municipal Council(?:\s+\w+)* Meeting|"
    r"Committee of the Whole|"
    r"Page\s+\d+|"
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s*$", re.I)


def load_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    # drop the provenance header (everything through the first '---' fence)
    parts = re.split(r"\n---\n", text, maxsplit=1)
    body = parts[1] if len(parts) > 1 else text
    out = []
    for ln in body.split("\n"):
        if FOOTER_RE.match(ln):
            continue
        out.append(ln)
    return out


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
ROLE = r"(?:Councilmember|Council Member|Mr\.|Ms\.|Mrs\.)"
NAME = r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?"

VERB = (r"(?:moved|moves|motioned|made (?:a|the) motion|makes? (?:a|the) motion|nominated)")
INTRO_RE = re.compile(
    r"(" + ROLE + r"\s+)?(" + NAME + r")\s+" + VERB + r"\b", re.I)
# a motion whose verb opens the line, with the mover's name wrapped onto the PRIOR line
VERB_LEAD = re.compile(r"^\s*(" + VERB + r")\b(.*)", re.I)
SEC_BY = re.compile(
    r"secon\w*d(?:ed)?\s+by\s+" + ROLE + r"?\s*(" + NAME + r")", re.I)
SEC_PRE = re.compile(ROLE + r"\s+(" + NAME + r")\s+secon\w*d", re.I)

LABEL_RE = re.compile(
    r"^\s*(Ayes?|Nays?|Abstentions?|Abstains?|Absent|Excused|Recused?)\s*[:,]\s*"
    r"(None\b.*|Councilmember\b.*|[A-Z][a-z]+\s+[A-Z][a-z]+.*|)$", re.I)
LABEL_MAP = {
    "aye": "Aye", "ayes": "Aye",
    "nay": "Nay", "nays": "Nay",
    "abstention": "Abstain", "abstentions": "Abstain", "abstain": "Abstain",
    "abstains": "Abstain",
    "absent": "Absent", "excused": "Excused",
    "recuse": "Recuse", "recused": "Recuse",
}
# tabular one-member-per-line:  "Mr. Hock        Aye"
TAB_RE = re.compile(r"^\s*(?:Mr|Ms|Mrs)\.\s+([A-Z][A-Za-z'\-]+)\s{1,}([A-Za-z][A-Za-z'.\-]*)\s*$")
# same, but a dissent row carries a trailing "– <member> explained ..." clause:
#   "Ms. Dominguez Nay – Ms. Dominguez explained she was voting no ..."
TAB_DISSENT = re.compile(
    r"^\s*(?:Mr|Ms|Mrs)\.\s+([A-Z][A-Za-z'\-]+)\s{1,}"
    r"(Aye|Ayes|Nay|Nays|Yes|No|Abstain(?:ed)?|Absent|Excused|Recuse[d]?)\b\s*[–—-]\s", re.I)
# stand-alone Aye-label variants: "All in favor voted Aye:" / "All in favor: <names>"
# (names may sit on the same line after the colon or wrap onto the next line)
ALT_AYE_RE = re.compile(r"^\s*All in favor(?:\s+voted\s+Aye[s]?)?\s*[:,]?\s*(.*)$", re.I)
VOTE_TOKENS = {
    "aye": "Aye", "ayes": "Aye", "yes": "Aye",
    "nay": "Nay", "nays": "Nay", "no": "Nay",
    "abstain": "Abstain", "abstained": "Abstain", "abstention": "Abstain",
    "absent": "Absent", "excused": "Excused",
    "recuse": "Recuse", "recused": "Recuse",
}
VOTED_FAVOR = re.compile(r"voted in favor of", re.I)
VOTE_HEADER = re.compile(r"roll call vote\s*:|voice vote taken\s*:", re.I)

# result lines (verbatim captured), priority order
RES_PATTERNS = [
    (re.compile(r"MOTION\s+FAILED[:\s]+There was no second[^.\n]*", re.I), "Fail"),
    (re.compile(r"[Tt]he motion was not seconded[^.\n]*", re.I), "Fail"),
    (re.compile(r"Motion\s+(?:passed|passes|carried)\s*:?\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Pass"),
    (re.compile(r"Motion\s+failed\s*:?\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Fail"),
    (re.compile(r"Motion\s+failed[^.\n]*", re.I), "Fail"),
    (re.compile(r"Vote:\s*\d+\s*[-–]\s*\d+[^\n]*", re.I), "Pass"),
    # 2026-07-16: CoW-style/2026 minutes-approval form "... seconded the motion.
    # All in favor 4-0." (2024-02-20, 2024-03-05, 2026 era) — tally-only, no names
    # printed.  Digits required, so the 2021 "All in favor voted Aye:" label lines
    # (handled by ALT_AYE_RE) are untouched.
    (re.compile(r"All in favor[,.]?\s+\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Pass"),
    (re.compile(r"[A-Za-z. ]*\bwins\s+\d+\s*[-–]\s*\d+", re.I), "Pass"),
    (re.compile(r"[A-Za-z. ]*\bwas elected[^.\n]*", re.I), "Pass"),
    (re.compile(r"(?:A\s+)?voice vote was made,\s*motion\s+failed[^.\n]*", re.I), "Fail"),
    (re.compile(r"(?:A\s+)?voice vote was made,\s*motion\s+(?:passed|passes)[^.\n]*", re.I), "Pass"),
    (re.compile(r"Voice vote taken,?\s*all\s*[“”\"']?\s*[Aa]yes[.“”\"']*(?:\s*Approved\s*\d+\s*[-–]\s*\d+)?[^.\n]*", re.I), "Pass"),
    (re.compile(r"Voice vote of\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Pass"),
    (re.compile(r"Motion\s+(?:passed|passes|carried)[^.\n]*", re.I), "Pass"),
]


def match_result(text):
    for rx, outcome in RES_PATTERNS:
        m = rx.search(text)
        if m:
            verbatim = re.sub(r"\s+", " ", m.group(0)).strip(" .")
            return verbatim, outcome
    return None


_NAME_SPLIT = re.compile(
    r",|\band\b|(?=Councilmember)|(?=Council Member)|(?=Mr\.)|(?=Ms\.)|(?=Mrs\.)", re.I)


def add_names(bucket_list, text):
    """Append canonical roster names found in a roll-call name list.  Splits on commas,
    'and', AND before each role word — so a dropped comma ('Councilmember Cox
    Councilmember Dominguez', an OCR artifact) still yields both members."""
    if re.search(r"^\s*none\s*\.?\s*$", text, re.I) or not text.strip():
        return
    for chunk in _NAME_SPLIT.split(text):
        nm = canon(chunk)
        if nm and nm not in bucket_list:
            bucket_list.append(nm)


ROLEWORD_RE = re.compile(r"Councilmember|Council Member|Board Member|Mr\.|Ms\.|Mrs\.", re.I)


def is_namelist(line):
    """A prose roll-call name list continues only across lines that are PURELY roster
    names/roles (so a following discussion sentence never bleeds names into a bucket)."""
    if not line.strip():
        return False
    t = ROLEWORD_RE.sub(" ", line)
    t = re.sub(r"\band\b|\bNone\b", " ", t, flags=re.I)
    toks = re.findall(r"[A-Za-z'][A-Za-z'\-]*", t)
    if not toks:
        return False
    return all(canon(tok) is not None for tok in toks)


def clean_motion(parts):
    s = re.sub(r"\s+", " ", " ".join(parts)).strip()
    s = re.split(r"\.?\s*The motion was\s+secon", s, flags=re.I)[0]
    s = re.split(r"\s+secon\w*d", s, flags=re.I)[0]
    s = re.split(VOTE_HEADER, s)[0]
    s = re.split(r"Voice vote taken", s, flags=re.I)[0]
    s = s.strip(" .,;:")
    return s[:500]


# 2026-07-16 (2023 PMN-promoted corpus): the clerk can DEFER a roll call — 2023-06-27
# prints "SECOND MOTION" (Markham, travel policy), then the THIRD motion with its roll,
# and only afterwards "ROLL CALL FOR SECOND MOTION ... Motion passes 3-2".  A motion
# whose window holds no vote structure is matched to its labeled deferred block instead
# of being dropped.  Occurs exactly once in the corpus; the headings are literal.
ORDINAL_MOTION_RE = re.compile(r"^\s*(FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+MOTION\s*$", re.I)
DEFERRED_ROLL_RE = re.compile(r"^\s*ROLL CALL FOR (?:THE )?(FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+MOTION\s*$", re.I)


# ---------------------------------------------------------------------------
# Parse one meeting
# ---------------------------------------------------------------------------
def parse_meeting(lines):
    n = len(lines)

    def scan_intro(i):
        """Return (mover, first_motion_text) for a motion anchored at line i, else None.
        Accepts a role-prefixed OR a bare roster-surname mover, and a wrapped intro whose
        verb opens line i with the mover's name on line i-1."""
        m = INTRO_RE.search(lines[i])
        if m and (m.group(1) or canon(m.group(2))):
            return canon(m.group(2)), lines[i][m.end():]
        vl = VERB_LEAD.match(lines[i])
        if vl and i > 0:
            m2 = INTRO_RE.search(lines[i - 1].rstrip() + " " + vl.group(1))
            if m2 and canon(m2.group(2)):
                return canon(m2.group(2)), vl.group(2)
        return None

    intros = []
    for i in range(n):
        si = scan_intro(i)
        if si:
            intros.append((i, si[0], si[1]))
    intro_starts = [i for i, _, _ in intros]

    votes = []
    consumed_until = -1
    for k, (idx, mover, first_text) in enumerate(intros):
        if idx <= consumed_until:
            continue
        # scan window bounded by the next intro (+ a small tail for the result line)
        nxt = intro_starts[k + 1] if k + 1 < len(intros) else n
        window_end = min(nxt + 2, n)

        seconder = None
        buckets = {"Aye": [], "Nay": [], "Abstain": [], "Absent": [],
                   "Excused": [], "Recuse": []}
        motion_parts = [first_text]
        nomination = False
        in_vote = False
        cur_label = None
        result = None
        result_line = None

        j = idx
        while j < window_end:
            line = lines[j]

            # seconder (once)
            if seconder is None:
                sm = SEC_BY.search(line) or SEC_PRE.search(line)
                if sm:
                    seconder = canon(sm.group(1))

            # vote-structure lines are handled BEFORE any result probe, so the last
            # roll-call row is never swallowed by a wrapped "Motion passed" on the next line.
            lm = LABEL_RE.match(line)
            if lm:
                in_vote = True
                cur_label = LABEL_MAP.get(lm.group(1).lower())
                if cur_label:
                    add_names(buckets[cur_label], lm.group(2))
                j += 1
                continue

            am = ALT_AYE_RE.match(line)
            if am and (am.group(1).strip() == "" or canon(am.group(1))):
                in_vote = True
                cur_label = "Aye"          # assenting names follow on this / the next line
                add_names(buckets["Aye"], am.group(1))
                j += 1
                continue

            tm = TAB_RE.match(line)
            td = None if tm else TAB_DISSENT.match(line)
            if tm or td:
                in_vote = True
                cur_label = None
                surname = (tm or td).group(1)
                token = (tm or td).group(2).lower().strip(".")
                if token in VOTE_TOKENS:
                    nm = canon(surname)
                    if nm:
                        b = VOTE_TOKENS[token]
                        if nm not in buckets[b]:
                            buckets[b].append(nm)
                elif tm:
                    nomination = True  # candidate-selection roll call (value is a name)
                j += 1
                continue

            if VOTED_FAVOR.search(line):
                in_vote = True
                nomination = True
                cur_label = None
                j += 1
                continue

            if VOTE_HEADER.search(line):
                in_vote = True
                cur_label = None
                j += 1
                continue

            # blank line: skip WITHOUT ending an open name list (footers + blanks split
            # wrapped Ayes lists across page breaks — the continuation resumes below).
            if not line.strip():
                j += 1
                continue

            # single-line result -> stop
            rr = match_result(line)
            if rr:
                result, _ = rr
                result_line = j
                break

            # continuation of a prose name list (wrapped names before the next label)
            if cur_label:
                if is_namelist(line):
                    add_names(buckets[cur_label], line)
                    j += 1
                    continue
                cur_label = None  # block ended; stray later names must not append

            # wrapped result spanning two lines (e.g. 'Voice vote taken, all' + 'ayes.')
            if j + 1 < n:
                rr2 = match_result(line + " " + lines[j + 1])
                if rr2:
                    result, _ = rr2
                    result_line = j + 1
                    break

            # still accumulating motion text (before any vote structure)
            if not in_vote and j > idx and len(motion_parts) < 12:
                motion_parts.append(line)
            j += 1

        # a nomination candidate-selection roll call is not Aye/Nay -> drop named buckets
        if nomination:
            for b in buckets:
                buckets[b] = []

        named = any(buckets[b] for b in buckets)
        if result is None and not named:
            # deferred roll: this intro sits under an "Nth MOTION" heading and its roll
            # is printed later as "ROLL CALL FOR Nth MOTION" (see note above).
            ordinal = None
            for back in range(idx - 1, max(idx - 4, -1), -1):
                if not lines[back].strip():
                    continue
                om = ORDINAL_MOTION_RE.match(lines[back])
                if om:
                    ordinal = om.group(1).upper()
                break
            if ordinal:
                for di in range(idx + 1, n):
                    dm = DEFERRED_ROLL_RE.match(lines[di])
                    if not (dm and dm.group(1).upper() == ordinal):
                        continue
                    cur = None
                    for j2 in range(di + 1, min(di + 12, n)):
                        l2 = lines[j2]
                        lm2 = LABEL_RE.match(l2)
                        if lm2:
                            cur = LABEL_MAP.get(lm2.group(1).lower())
                            if cur:
                                add_names(buckets[cur], lm2.group(2))
                            continue
                        if cur and is_namelist(l2):
                            add_names(buckets[cur], l2)
                            continue
                        rr3 = match_result(l2)
                        if rr3:
                            result, _ = rr3
                            break
                        if l2.strip():
                            cur = None
                    break
            named = any(buckets[b] for b in buckets)
        if result is None:
            # rare: Ayes block with no printed result line (e.g. "Voice vote taken:" header)
            if named:
                a, nn = len(buckets["Aye"]), len(buckets["Nay"])
                result = f"{a}-{nn}"
            else:
                # no result and no names within window -> not a recorded vote; skip
                continue

        motion_text = clean_motion(motion_parts)
        votes.append({
            "motion": motion_text,
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": named,
            "aye": buckets["Aye"], "nay": buckets["Nay"],
            "abstain": buckets["Abstain"], "absent": buckets["Absent"],
            "excused": buckets["Excused"], "recuse": buckets["Recuse"],
        })
        if result_line is not None:
            consumed_until = result_line

    for no, v in enumerate(votes, 1):
        v["motion_no"] = no
    return votes


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
BODY = "Council"


def json_path_for(rel_path, year):
    parts = rel_path.split("/")            # minutes/<year>/<week>/<file>.md
    return VOTES_DIR / str(year) / parts[-2] / parts[-1].replace(".md", ".json")


def main():
    rows = list(csv.DictReader(INDEX.open(encoding="utf-8")))
    VOTES_DIR.mkdir(exist_ok=True)
    processed = skipped = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print("MISSING", r["path"], file=sys.stderr)
            continue
        jp = json_path_for(r["path"], r["year"])
        if jp.exists() and not FORCE:
            skipped += 1
            continue
        jp.parent.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(load_lines(path))
        payload = {"date": r["date"], "year": int(r["year"]), "title": r["title"],
                   "body": BODY, "source": r["path"], "votes": votes}
        jp.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON (skipped {skipped})")
    rebuild_csv(rows)
    build_roster(rows)


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    nrows = 0
    with ALL_VOTES.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            jp = json_path_for(r["path"], r["year"])
            if not jp.exists():
                continue
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], data.get("body", BODY),
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover", ""), v.get("seconder", "")]
                emitted = False
                for key, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                 ("absent", "Absent"), ("excused", "Excused"),
                                 ("recuse", "Recuse")):
                    for mem in v.get(key, []):
                        w.writerow(base + [mem, lab, data["source"]])
                        nrows += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    nrows += 1
    print(f"Wrote {ALL_VOTES} ({nrows} rows)")


def build_roster(rows):
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not jp.exists():
            continue
        data = json.loads(jp.read_text())
        date = data["date"]
        for v in data["votes"]:
            people = set()
            for k in ("aye", "nay", "abstain", "absent", "excused", "recuse"):
                people.update(v.get(k, []))
            for p in people:
                d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
                d["first"] = min(d["first"], date)
                d["last"] = max(d["last"], date)
                d["n"] += 1
    with ROSTER.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "first_seen", "last_seen", "n_votes"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, d["first"], d["last"], d["n"]])
    print(f"Wrote {ROSTER} ({len(seen)} members)")


if __name__ == "__main__":
    main()
