#!/usr/bin/env python3
"""
Sandy City Council vote extractor.

Reads the 274 council-meeting markdown files under meeting_minutes/minutes/<year>/<week>/,
parses every recorded roll-call / voice motion, tags the governing `body`
(Council default; RDA/CRA/MBA for agency-board agenda blocks), normalizes member
names, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<date>_*.json  (resumable)
  - meeting_minutes/all_votes.csv  (long format, one row per member-vote, WITH body column)

Roll-call form in Sandy minutes (text + OCR):
    A motion was made by <mover>, seconded by <seconder>, to <text>...
    The motion carried by the following [roll call] vote:
        Yes:   7-  <name>
                   <name> ...
        No:    1-  <name>
        Abstain: 1 <name>
        Excused: 1 <name>      (treated as Absent)
    Voice form: "...carried by a unanimous voice vote." -> names_recorded:false
    Inline form: "...failed by a vote of 4 Nay to 3 Yah (Dekeyzer, Mecham, Stroud)."

The Mayor does NOT vote (strong-mayor form). Mayor names are excluded from member lists.
RDA/MBA substantive business is held in SEPARATE agency meetings whose minutes are not on
disk; inside these council files the only agency-related motion recorded is the procedural
"recess the Council and convene the RDA" vote (taken AS the Council). See CLAUDE.md.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
REPO_ROOT = ROOT.parent

# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------
# Canonical voting-member spellings. Keys are lowercased surname/firstname tokens.
NAME_CANON = {
    "brooke christensen": "Brooke Christensen",
    "christensen": "Brooke Christensen",
    "kristin coleman-nicholl": "Kristin Coleman-Nicholl",
    "kristin coleman nicholl": "Kristin Coleman-Nicholl",
    "kris coleman nicholl": "Kristin Coleman-Nicholl",
    "kris coleman-nicholl": "Kristin Coleman-Nicholl",
    "kris nicholl": "Kristin Coleman-Nicholl",
    "coleman-nicholl": "Kristin Coleman-Nicholl",
    "coleman nicholl": "Kristin Coleman-Nicholl",
    "nicholl": "Kristin Coleman-Nicholl",
    "monica zoltanski": "Monica Zoltanski",
    "zoltanski": "Monica Zoltanski",
    "marci houseman": "Marci Houseman",
    "houseman": "Marci Houseman",
    "alison stroud": "Alison Stroud",
    "stroud": "Alison Stroud",
    "cyndi sharkey": "Cyndi Sharkey",
    "sharkey": "Cyndi Sharkey",
    "zach robinson": "Zach Robinson",
    "robinson": "Zach Robinson",
    "brooke d'sousa": "Brooke D'Sousa",
    "brooke d'souza": "Brooke D'Sousa",
    "d'sousa": "Brooke D'Sousa",
    "d'souza": "Brooke D'Sousa",
    "dsousa": "Brooke D'Sousa",
    "ryan mecham": "Ryan Mecham",
    "mecham": "Ryan Mecham",
    "aaron dekeyzer": "Aaron Dekeyzer",
    "dekeyzer": "Aaron Dekeyzer",
    # Scott Earl: appointed District 4 council member (2022 - 2023, after
    # Zoltanski became Mayor; lost the 2023 D4 race to Houseman). Legitimate voter.
    "scott earl": "Scott Earl",
    "earl": "Scott Earl",
    # Source clerk typos (verbatim in the official minutes; normalized like the
    # other spelling variants above — never guessed, each verified against the PDF):
    "cyndi shakey": "Cyndi Sharkey",   # 2021-08-17, 2025-08-26
    "shakey": "Cyndi Sharkey",
    "ryan mecahm": "Ryan Mecham",      # 2024-02-13 (twice)
    "mecahm": "Ryan Mecham",
    "alison stoud": "Alison Stroud",   # 2021-07-13, 2023-05-30
    "stoud": "Alison Stroud",
}

# People who served as MAYOR (non-voting) and the year they took office.
# Mayor never appears in a member vote list; guard anyway.
MAYORS = {"kurt bradburn", "monica zoltanski"}  # Zoltanski only as Mayor from 2022-01

# The set of valid council surnames for token matching
KNOWN_SURNAMES = {
    "christensen", "coleman-nicholl", "nicholl", "zoltanski", "houseman",
    "stroud", "sharkey", "robinson", "d'sousa", "d'souza", "dsousa",
    "mecham", "dekeyzer", "earl", "shakey", "mecahm", "stoud",
}


def _clean_name(raw):
    s = raw.strip()
    s = s.strip(".,;:()")
    s = re.sub(r"\s+", " ", s)
    # strip leading role words
    s = re.sub(r"^(Council\s*Member|Councilmember|Board\s*Member|Agency\s*Member|"
               r"Chair|Vice[- ]?Chair|Member|Mr\.|Ms\.|Mrs\.)\s+", "", s, flags=re.I)
    s = s.strip()
    s = re.sub(r"[’]", "'", s)
    return s


def normalize_name(raw):
    """Return canonical name, or None if not a recognizable council member."""
    s = _clean_name(raw)
    if not s:
        return None
    key = s.lower()
    if key in NAME_CANON:
        return NAME_CANON[key]
    # try surname-only match (last token)
    toks = key.split()
    if toks:
        last = toks[-1]
        if last in NAME_CANON:
            return NAME_CANON[last]
    # try first-two-token match
    if len(toks) >= 2:
        two = " ".join(toks[:2])
        if two in NAME_CANON:
            return NAME_CANON[two]
    return None  # never guess


# ---------------------------------------------------------------------------
# Motion-type taxonomy
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"budget amendment|amend the budget|budget adjustment", t):
        return "Budget Amendment"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bappoint|appointment|consent for the appointment|ratify the results|"
                 r"liaison", t):
        return "Appointment"
    if re.search(r"rezone|zoning|zone change|annex|annexation|subdivision|plat|"
                 r"conditional use|land use|general plan|master plan|preliminary plat", t):
        return "Land-Use/Zoning"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|professional services|"
                 r"agreement with|services agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing|open the public hearing|close the public hearing|"
                 r"continue the public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|approve the consent|"
                 r"approve the agenda|approve the minutes|table|continue|postpone|"
                 r"suspend the rules|amend the agenda|move to|ratify", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
VOTE_LABELS = {
    "yes": "aye", "aye": "aye", "ayes": "aye",
    "no": "nay", "nay": "nay", "nays": "nay",
    "abstain": "abstain", "abstaining": "abstain", "abstained": "abstain",
    "excused": "absent", "absent": "absent",
    "recuse": "recuse", "recused": "recuse",
}
# Label line e.g. "Yes:    7-   Alison Stroud"  or  "Yes: 6 Alison Stroud"
# Label must be followed by ":" or "-<digit>" or " <digit>" so we don't swallow prose
# lines that merely start with "No ..." or "Present ...".
def label_names(blob):
    """Names after a Yes:/No: label — either ONE name or a 'Council Members A, B,
    and C.' list (2020-06-16 narrative rolls; T3.1(m) sandy m80)."""
    blob = re.sub(r"^\s*(?:Council\s*Members?|Councilmembers?)\s+", "", blob.strip(), flags=re.I)
    out = []
    for part in re.split(r",|\band\b", blob):
        nm = normalize_name(part)
        if nm and nm not in out:
            out.append(nm)
    return out


LABEL_RE = re.compile(
    r"^\s*(Yes|Ayes?|No|Nays?|Abstain(?:ing|ed)?|Excused|Absent|Recused?|Nonvoting|Present)"
    r"(?:\s*:\s*|\s*-\s*(?=\d)|\s+(?=\d))"
    r"(?:(\d+)\s*[-\.]?\s*)?(.*)$",
    re.I,
)
MOVER_RE = re.compile(
    r"motion was made by\s+(.+?)(?:,?\s+seconded by\s+(.+?))?(?:[,.]|\s+to\s|\.\.\.|$)",
    re.I,
)
MADE_MOTION_RE = re.compile(
    r"([A-Z][A-Za-z'’.\- ]+?)\s+made a motion(?:,?\s+seconded by\s+(.+?))?(?:[,.]|\s+to\s|$)",
    re.I,
)
# 2020 narrative form: "There was a motion [to <action>] by <Name> and seconded by
# <Name>" — used for call-the-question / substitute motions inside a budget debate
# (T3.1(m) sandy m80, 2026-07-12). Anchoring these lets the sub-motion's vote resolve
# separately, with the ORIGINAL motion parked in `deferred` until "A vote was taken
# on the main motion" arrives.
THERE_WAS_RE = re.compile(
    r"There was a motion(?:\s+(to\s+.+?))?\s+by\s+(?:Council\s*Member\s+)?"
    r"([A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)\s*,?\s+and\s+seconded\s+by\s+"
    r"(?:Council\s*Member\s+)?([A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)", re.I)
RESULT_RE = re.compile(
    r"motion\s+(carried|passed|failed|died)\b(.*)$", re.I
)
INLINE_TALLY_RE = re.compile(
    r"vote of\s+(\d+)\s+(Nay|Aye|Yah|Yea|No|Yes)\s+to\s+(\d+)\s+(Nay|Aye|Yah|Yea|No|Yes)\s*"
    r"(?:\(([^)]*)\))?",
    re.I,
)
# "...carried by a roll call vote of 5 - 2." -> aye-nay tally, no per-name detail
INLINE_NUM_RE = re.compile(
    r"(?:roll call )?vote of\s+(\d+)\s*[-–]\s*(\d+)", re.I
)
# Minority callout: "Monica Zoltanski and Marci Houseman opposed." / "X dissenting" /
# "X voted no/nay/against" / "X in opposition"
MINORITY_RE = re.compile(
    r"([A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?"
    # continuation between names: a bare comma OR "and" OR ", and" — earlier this required
    # "and", so comma-only lists ("Zoltanski, Christensen opposed") dropped all but the last.
    r"(?:(?:\s*,\s*|\s*,?\s*and\s+)[A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)*)\s+"
    r"(?:opposed|dissent(?:ed|ing)?|voted (?:no|nay|against)|in opposition|"
    r"voting (?:no|nay|against))",
    re.I,
)


def is_name_line(line):
    """A bare name-continuation line under a vote label: a short, name-only line.

    Must reject prose (mover sentences, narrative) that merely *ends* in a surname
    token, e.g. "A motion was made by ... seconded by Marci Houseman," which would
    otherwise normalize to a member and contaminate the vote bucket.
    """
    s = line.strip().rstrip(".,;")
    if not s:
        return False
    if LABEL_RE.match(line):
        return False
    # name-only lines are short
    if len(s) > 40:
        return False
    toks = s.split()
    if len(toks) > 4:
        return False
    # reject any line containing sentence/verb words
    if re.search(r"\b(motion|made|second(ed)?|moved|approve|adopt|carried|"
                 r"vote|council|meeting|resolution|the|by|to|that|and|of|for|"
                 r"recess|convene)\b", s, re.I):
        # allow "and" only if it joins names handled elsewhere; here be strict
        return False
    return normalize_name(s) is not None


def parse_meeting(path, rel_source):
    text = path.read_text(encoding="utf-8", errors="replace")
    raw_lines = text.split("\n")

    # Drop page-break footer/header noise so roll-call regions flatten.
    lines = []
    for ln in raw_lines:
        s = ln.strip()
        if re.match(r"^Sandy City, Utah\b", s):
            continue
        if re.match(r"^City Council\s+Meeting Minutes", s):
            continue
        if re.match(r"^City Council Meeting Minutes\b", s):
            continue
        if s == "City Council":          # lone continuation-page header (splits roll calls)
            continue
        if re.match(r"^Sandy,\s*UT\s*\d{5}\b", s):   # standalone address footer fragment
            continue
        if re.match(r"^Page\s*\d+\b", s):
            continue
        if re.match(r"^Printed on\b", s):
            continue
        lines.append(ln)

    # Stitch wrapped result phrases so the verb + "following vote:" land on one line.
    # Common wraps: a line ending in "...The motion" followed by "carried by the
    # following vote:"; or "carried" at line end followed by "by the following vote:".
    stitched = []
    k = 0
    while k < len(lines):
        cur = lines[k]
        # join forward while the joined fragment is an in-progress result phrase:
        # we have started "...the motion [carried/failed]" but have not yet reached the
        # "vote:" / "voice vote" / "lack of a second" terminus.
        joins = 0
        while k + 1 < len(lines) and joins < 4:
            low = cur.lower().rstrip()
            # in-progress result phrase = ends mid "the motion ... <result clause>"
            m_started = re.search(
                r"the motion( (carried|passed|failed|died)?\b[\w ]*)?$", low)
            terminated = re.search(
                r"vote:?\s*$|voice vote\.?\s*$|lack of a second\.?\s*$|"
                r"died\b.*\.\s*$|unanimous\b.*\.\s*$", low)
            if m_started and not terminated:
                cur = cur.rstrip() + " " + lines[k + 1].strip()
                k += 1
                joins += 1
                continue
            break
        stitched.append(cur)
        k += 1
    lines = stitched

    # Identify RDA/CRA/MBA agenda blocks: between a "convened as / convene a meeting of the
    # Redevelopment Agency / Community Reinvestment / Municipal Building Authority" marker and
    # the next "reconvened the (City) Council" marker. Motions inside -> body tag.
    body_at = {}  # line index -> body
    cur_body = "Council"
    convene_re = re.compile(
        r"(convened as|convene a meeting of|reconvened as).*"
        r"(redevelopment agency|community reinvestment|municipal building authority|"
        r"\brda\b|\bcra\b|\bmba\b)", re.I)
    reconvene_re = re.compile(
        r"reconvened? the (sandy )?city council|reconvened the council meeting|"
        r"council (meeting )?reconvened|the council reconvened", re.I)
    for i, ln in enumerate(lines):
        low = ln.lower()
        if convene_re.search(low):
            if "redevelopment" in low or re.search(r"\brda\b", low):
                cur_body = "RDA"
            elif "community reinvestment" in low or re.search(r"\bcra\b", low):
                cur_body = "CRA"
            elif "municipal building" in low or re.search(r"\bmba\b", low):
                cur_body = "MBA"
        elif reconvene_re.search(low):
            cur_body = "Council"
        body_at[i] = cur_body

    votes = []
    n = len(lines)
    i = 0
    pending = None   # dict holding mover/seconder/text awaiting a result
    deferred = None  # a MAIN motion superseded by a procedural sub-motion (call the
                     # question / substitute) — reclaimed at "vote ... on the main motion"

    def body_for(idx):
        return body_at.get(idx, "Council")

    while i < n:
        line = lines[i]

        # capture mover/seconder when a motion is introduced
        # the "...by X and seconded by Y" clause may wrap to the next line; the match
        # must START in THIS line (else the probe would double-fire on the next pass
        # and clobber the deferred main motion)
        tw = THERE_WAS_RE.search(line + " " + (lines[i + 1].strip() if i + 1 < n else ""))
        if tw and tw.start() < len(line):
            if pending is not None:
                deferred = pending      # park the main motion; its vote comes later
            pending = {"mover": normalize_name(tw.group(2)),
                       "seconder": normalize_name(tw.group(3)),
                       "text_lines": [line.strip()], "start": i}
            i += 1
            continue
        m = MOVER_RE.search(line)
        if not m:
            m2 = MADE_MOTION_RE.search(line)
            if m2:
                mover = normalize_name(m2.group(1))
                seconder = normalize_name(m2.group(2)) if m2.group(2) else None
                if pending is not None:
                    deferred = pending   # park an unresolved motion (call-the-question
                                         # sequences); reclaimed at "vote ... main motion"
                pending = {"mover": mover, "seconder": seconder,
                           "text_lines": [line.strip()], "start": i}
                i += 1
                continue
        else:
            mover = normalize_name(m.group(1))
            seconder = normalize_name(m.group(2)) if m.group(2) else None
            if pending is not None:
                deferred = pending
            pending = {"mover": mover, "seconder": seconder,
                       "text_lines": [line.strip()], "start": i}
            i += 1
            continue

        # a parked main motion resumes at its own vote sentence
        if pending is None and deferred is not None and \
                re.search(r"vote was taken on the (?:main|original|amended) motion", line, re.I):
            pending = deferred
            deferred = None

        # accumulate motion text until a result statement
        rm = RESULT_RE.search(line)
        if rm and pending is not None:
            pending["text_lines"].append(line.strip())
            verb = rm.group(1).lower()
            tail = rm.group(2) or ""
            outcome = "Pass" if verb in ("carried", "passed") else "Fail"

            # gather full text
            motion_text = " ".join(pending["text_lines"])
            motion_text = re.sub(r"\s+", " ", motion_text).strip()
            # trim everything from "The motion carried/failed..." for the stored motion text
            motion_text = re.split(r"\.\.\.\s*the motion|the motion (carried|passed|failed|died)",
                                   motion_text, flags=re.I)[0].strip(" .")

            block_body = body_for(pending["start"])
            # The procedural motion to "recess the City Council and convene/reconvene the
            # RDA/CRA/MBA" is itself a COUNCIL vote (taken before the body actually changes).
            # Likewise the motion to reconvene the Council. Keep these as Council so `body`
            # marks only business conducted in board capacity. (In Sandy's minutes the agency's
            # substantive votes live in separate, un-acquired RDA meeting minutes — see CLAUDE.md.)
            if re.search(r"(recess|adjourn|reconvene|convene).*"
                         r"(redevelopment|reinvestment|building authority|city council|"
                         r"\brda\b|\bcra\b|\bmba\b)", motion_text, re.I):
                block_body = "Council"

            # ---- determine vote detail ----
            lower_tail = (line + " ").lower()
            buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
            names_recorded = False
            result_str = ""

            # died for lack of a second
            if "lack of a second" in line.lower() or "not second" in line.lower() \
                    or "no second" in line.lower():
                result_str = "Died (no second)"
                votes.append(_mk(pending, motion_text, block_body, result_str,
                                 buckets, False))
                pending = None
                i += 1
                continue

            # inline tally form
            inl = INLINE_TALLY_RE.search(line)
            if inl:
                a_ct, a_lab, b_ct, b_lab = inl.group(1), inl.group(2).lower(), \
                    inl.group(3), inl.group(4).lower()
                names_in = inl.group(5)
                yes_ct = a_ct if a_lab in ("aye", "yah", "yea", "yes") else b_ct
                no_ct = b_ct if a_lab in ("aye", "yah", "yea", "yes") else a_ct
                result_str = f"{yes_ct}-{no_ct} {outcome}"
                # we know minority names sometimes; do not guess majority -> names_recorded False
                votes.append(_mk(pending, motion_text, block_body, result_str,
                                 buckets, False))
                pending = None
                i += 1
                continue

            # inline numeric tally: "...carried by a roll call vote of 5 - 2." possibly with
            # a trailing minority callout ("X and Y opposed."). Capture tally + minority names.
            inl2 = INLINE_NUM_RE.search(line)
            if inl2 and "following" not in lower_tail:
                n1, n2 = int(inl2.group(1)), int(inl2.group(2))
                # look for minority names on this line (and the next continuation line)
                scan = line
                if i + 1 < n and lines[i + 1].strip():
                    scan = line + " " + lines[i + 1].strip()
                mm = MINORITY_RE.search(scan)
                if mm:
                    for part in re.split(r",|\band\b", mm.group(1)):
                        nm = normalize_name(part)
                        if nm and nm not in buckets["nay"]:
                            buckets["nay"].append(nm)
                # capture "<name> abstaining" callouts too
                for am in re.finditer(
                        r"([A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)\s+"
                        r"abstain(?:ing|ed)?", scan):
                    nm = normalize_name(am.group(1))
                    if nm and nm not in buckets["abstain"] and nm not in buckets["nay"]:
                        buckets["abstain"].append(nm)
                # Orient the bare "vote of A - B" tally. The phrasing names only the losing
                # minority, so a *failed* motion's first number is the count AGAINST (e.g.
                # "failed by a vote of 5-2 with <5 names> opposed" = 5 nay, 2 aye). Prefer the
                # captured named-dissenter count when it disambiguates which number is the nays.
                k_nay = len(buckets["nay"])
                if k_nay and k_nay in (n1, n2):
                    nay_ct = k_nay
                    aye_ct = n2 if k_nay == n1 else n1
                elif outcome == "Fail":
                    aye_ct, nay_ct = n2, n1
                else:
                    aye_ct, nay_ct = n1, n2
                result_str = f"{aye_ct}-{nay_ct} {outcome}"
                votes.append(_mk(pending, motion_text, block_body, result_str,
                                 buckets, False))  # majority unnamed -> keep False
                pending = None
                i += 1
                continue

            # roll-call: look ahead for label lines — either the "by the following
            # vote:" lead-in OR a bare "The motion failed:/passed:" directly followed
            # by Yes:/No: label lines (2020-06-25 adjourn motions)
            _jj = i + 1
            while _jj < n and not lines[_jj].strip():
                _jj += 1
            next_is_label = _jj < n and bool(LABEL_RE.match(lines[_jj]))
            if ("following" in lower_tail and "vote" in lower_tail) or next_is_label:
                j = i + 1
                cur_bucket = None          # which buckets[] key, or "present"/None
                consumed_any = False
                blanks = 0
                present_names = []
                while j < n:
                    lj = lines[j]
                    lm = LABEL_RE.match(lj)
                    if lm:
                        label = lm.group(1).lower()
                        rest = lm.group(3).strip()
                        if label == "nonvoting":
                            cur_bucket = None
                        elif label == "present":
                            cur_bucket = "present"
                        else:
                            cur_bucket = VOTE_LABELS.get(label)
                        consumed_any = True
                        blanks = 0
                        if rest:
                            for nm in label_names(rest):
                                if cur_bucket == "present":
                                    present_names.append(nm)
                                elif cur_bucket:
                                    buckets[cur_bucket].append(nm)
                        j += 1
                        continue
                    s = lj.strip()
                    if not s:
                        blanks += 1
                        if blanks >= 3 and consumed_any:
                            break
                        j += 1
                        continue
                    blanks = 0
                    if cur_bucket and is_name_line(lj):
                        nm = normalize_name(s)
                        if nm:
                            if cur_bucket == "present":
                                present_names.append(nm)
                            else:
                                buckets[cur_bucket].append(nm)
                        j += 1
                        continue
                    if consumed_any:
                        break
                    if j - i > 4:
                        break
                    j += 1

                # de-dup within bucket preserving order
                def _dedup(seq):
                    seen, out = set(), []
                    for nm in seq:
                        if nm not in seen:
                            seen.add(nm)
                            out.append(nm)
                    return out
                for k in buckets:
                    buckets[k] = _dedup(buckets[k])
                present_names = _dedup(present_names)

                total_named = sum(len(buckets[k]) for k in ("aye", "nay", "abstain"))
                # Present/Excused-only roll-call (no Yes/No labels): present members all
                # voted with the (passing) motion -> aye; excused -> absent already captured.
                if total_named == 0 and present_names and outcome == "Pass":
                    buckets["aye"] = present_names
                    total_named = len(buckets["aye"])

                if total_named > 0:
                    names_recorded = True
                    result_str = f"{len(buckets['aye'])}-{len(buckets['nay'])} {outcome}"
                    i = max(j, i + 1)
                else:
                    result_str = outcome
                    i += 1
                votes.append(_mk(pending, motion_text, block_body, result_str,
                                 buckets, names_recorded))
                pending = None
                continue

            # voice / unanimous / generic
            if "voice vote" in line.lower() or "unanimous" in line.lower():
                result_str = "Unanimous (voice)" if "unanimous" in line.lower() else "Voice"
            else:
                result_str = outcome
            votes.append(_mk(pending, motion_text, block_body, result_str,
                             buckets, False))
            pending = None
            i += 1
            continue

        # if we have a pending motion and this is plain text, accumulate it (cap length)
        if pending is not None:
            if len(pending["text_lines"]) < 12 and line.strip():
                pending["text_lines"].append(line.strip())
            # abandon a pending motion if it runs too long with no result
            # (40: a 2020 budget-debate motion carries ~25 lines of citizen comment
            # between motion and vote — T3.1(m) sandy, 2026-07-12). PARK it rather
            # than drop it: a long debate can end with a call-the-question sequence
            # whose "The vote was taken on the main motion" reclaims exactly this.
            if i - pending["start"] > 40:
                deferred = pending
                pending = None
        i += 1

    return votes


def _mk(pending, motion_text, body, result_str, buckets, names_recorded):
    return {
        "body": body,
        "motion": motion_text[:600],
        "motion_type": classify_motion(motion_text),
        "result": result_str,
        "mover": pending.get("mover"),
        "seconder": pending.get("seconder"),
        "aye": buckets["aye"],
        "nay": buckets["nay"],
        "abstain": buckets["abstain"],
        "absent": buckets["absent"],
        "recuse": buckets["recuse"],
        "names_recorded": names_recorded,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    rows = list(csv.DictReader(INDEX.open()))
    processed = 0
    for r in rows:
        path = REPO_ROOT / r["path"]
        if not path.exists():
            # path in index is repo-relative; try under MINUTES
            path = ROOT.parent / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        date = r["date"]
        year = r["year"]
        # week folder = parent dir name
        week = Path(r["path"]).parent.name
        out_dir = VOTES_DIR / year / week
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = Path(r["path"]).stem
        out_json = out_dir / f"{slug}.json"

        votes = parse_meeting(path, r["path"])
        # assign motion_no
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        payload = {
            "date": date,
            "year": int(year),
            "title": r["title"],
            "source": r["path"],
            "votes": votes,
        }
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n_rows = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                bucket_map = [("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")]
                emitted = False
                for key, label in bucket_map:
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"]])
                        n_rows += 1
                        emitted = True
                if not emitted:
                    # tally-only / voice / names not recorded -> single row, empty member
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


if __name__ == "__main__":
    main()
