#!/usr/bin/env python3
"""Extract Council motions from the WFRC minutes markdown -> legislative/all_motions.csv.

THE RECORDING CEILING (verified across 2016-2026): WFRC minutes name the MOVER and the
SECONDER of every action and print a narrative tally result ("passed unanimously", "the
affirmative vote was unanimous", "there were two dissenting votes; however the affirmative
vote was the majority and the amendment was approved"). Dissent is COUNT-ONLY: dissenters
are NEVER named and there is NO roll call. So we capture mover/seconder (person-linked by
FULL name) + verbatim result + outcome, and named individual vote rows are essentially
ABSENT by construction (an honest ceiling, like nephi / west_jordan PC).

Committee actions (Regional Growth Committee, Trans Com, WFRC Budget Committee) fold into
the single Council minutes doc; the `body` column walks the agenda section headers
(the SLC in-session pattern).

DERIVED + idempotent. Never hand-edit the output; fix the parser.
"""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEG = os.path.join(ROOT, "legislative")
IDX = os.path.join(LEG, "minutes_index.csv")
OUT = os.path.join(LEG, "all_motions.csv")

# leading office/title tokens stripped so full_name resolves across the repo
TITLE = re.compile(
    r"^(?:the\s+)?(?:hon\.?|honorable|mayor|commissioner|councilman|councilwoman|"
    r"councilmember|council\s*member|councilperson|senator|representative|rep\.?|sen\.?|"
    r"trustee|chair|chairman|chairwoman|vice[-\s]?chair|director|executive|deputy|"
    r"mr\.?|ms\.?|mrs\.?|dr\.?|uta|udot|slco|gopb|ulct|fhwa|county)\s+",
    re.I)

# Google-Docs -> Skia PDF exports (2024+) lace every word with Unicode directional /
# zero-width formatting chars; strip them before parsing.
JUNK = re.compile("[​-‏‪-‮⁦-⁩­﻿]")

# active: "<Name> made a motion / moved to / motioned to";  passive: "motion was made by <Name>"
# (bare "moved" is EXCLUDED — "Mayor Ramsey moved on to the next item" is navigation).
# The name run may span "of <Jurisdiction>" — WFRC seats are held by mayors and
# commissioners OF a city, and the lowercase "of" used to break the run so that
# "Mayor Brandon Stanger of Clinton City made a motion" captured only "Clinton City",
# recording a person literally named "Clinton". Allowing the connector lets clean_name()
# take the name after the LAST title token and stop at "of" -> "Brandon Stanger".
# 2026-07-29: the run required WHITESPACE after every token, and "," is not in the token
# class — so a name closed by a comma lost its LAST token: "seconded by Mayor Bob
# Stevenson, and the vote..." captured only "Mayor Bob " and minted a person called "Bob"
# (likewise Carlton/Jeff/Joe/Mark/Monica/Rob/Shawn, and "Rob Dahle" was lost entirely).
# Same fabrication class as the sentence run-on below, opposite direction. Fix: allow ONE
# optional final token closed by , ; or : — never inside the repeat group, so the run can
# still never span a comma into a following "Mayor <Someone-else>" (clean_name() takes the
# name after the LAST title token, so a comma-spanning run would misattribute).
# ...and the comma-tolerant form is used ONLY where an explicit cue ("seconded by",
# "motion was made by") or the motion verb already proves the run is a name. It must NOT be
# used in the bare "<run>seconded" alternative: there a trailing comma means the preceding
# text is a CLAUSE, not the seconder, and the comma-tolerant run made an earlier position
# win — "…certify the Farmington FrontRunner Station Area Plan, seconded by Mayor Troy
# Walker" recorded the seconder as "Station Area Plan" and shadowed the real one.
_NAMERUN = r"[A-Z][A-Za-z.'\-]+\s+(?:[A-Z][A-Za-z.'\-]+\s+|(?:of|from)\s+){0,7}"
_NAMERUN_C = _NAMERUN + r"(?:[A-Z][A-Za-z.'\-]+[,;:]\s+)?"
ANCHOR = re.compile(
    r"(?P<n1>" + _NAMERUN_C + r")(?:made a motion|moved to|motioned to|motioned)\b"
    r"|(?:motion was made by|a motion by|motion by|motion made by)\s+"
    r"(?P<n2>" + _NAMERUN_C + r")")
SECOND = re.compile(
    r"(?:seconded by|second by|supported by)\s+(" + _NAMERUN_C + r")"
    r"|(" + _NAMERUN + r")seconded\b")

# body-section boundaries in the FLOWED text: a committee name that is either number-
# prefixed ("5. Trans Com") or timestamp-suffixed ("Trans Com [01:30:24]") — the two
# reliable signals of a real agenda-section header (vs the name in running prose).
_COMM = {
    r"Regional\s*Growth\s*Committee|\(RGC\)": "Regional Growth Committee",
    r"Transportation\s*Coordinating\s*Committee|Trans\s*Com": "Transportation Coordinating Committee",
    r"WFRC\s*Budget\s*Committee|Budget\s*Committee": "WFRC Budget Committee",
}
_RETURN = (r"Public\s*Comment|Chair\s*Report|Consent\s*Agenda|Welcome|Reports?\b|"
           r"Other\s*Business|Adjourn")
BOUNDS = []
for pat, name in _COMM.items():
    BOUNDS.append((re.compile(r"(?:\b\d+\s*[.\)]\s*)(?:%s)|(?:%s)[^\n]{0,25}\[\d\d?:\d\d"
                              % (pat, pat), re.I), name))
BOUNDS.append((re.compile(r"(?:\b\d+\s*[.\)]\s*)(?:%s)|(?:%s)[^\n]{0,25}\[\d\d?:\d\d"
                          % (_RETURN, _RETURN), re.I), "Council"))

STOP_NAME = {"the", "and", "a", "an", "to", "of", "for", "as", "it", "who", "there",
             "his", "her", "their", "motion", "second", "seconded", "all",
             # 2026-07-26: sentence-continuation words that were being read as surnames
             # ("Mark Shepherd No", "Bob Stevenson This", "Joy Petro With").
             "no", "this", "that", "with", "amendment", "after", "then", "he", "she",
             "they", "we", "i", "council", "committee", "board", "staff", "discussion"}
# A member is identified by name, not by the jurisdiction they represent: WFRC council
# seats are held by mayors/commissioners "of <City>", and "Mayor Brandon Stanger of
# Clinton City" was being recorded as a person literally called "Clinton City".
JURISDICTION_TOK = {"city", "county", "town", "district", "uta", "udot"}
# 2026-07-29: same principle for ORGAN names. WFRC minutes use appositives — "Mayor Tom
# Dolan, Chair of the Budget Committee, made a motion" — and the name run cannot cross the
# lowercase "of the", so the leftmost run it can match is "Budget Committee,". That is a
# BODY, not a member; recording it would mint a person called "Budget". Treated like a
# jurisdiction: no office title in the run + an organ word => return "" (the motion is then
# skipped as unattributed). Honest gap over invented member — cardinal rule 1.
ORG_TOK = {"committee", "council", "board", "commission", "department", "authority",
           "agency", "association", "wfrc"}

# office/title tokens — the personal name is whatever follows the LAST title token in the
# captured run (the run can trail capitalized words in from the prior sentence, e.g.
# "Budget. Mayor Jeff Silvestrini" -> after 'Mayor' -> "Jeff Silvestrini").
TITLE_TOK = {"mayor", "commissioner", "councilman", "councilwoman", "councilmember",
             "councilperson", "senator", "representative", "rep", "sen", "trustee",
             "chair", "chairman", "chairwoman", "vice", "director", "executive", "deputy",
             "mr", "ms", "mrs", "dr", "uta", "udot", "slco", "gopb", "ulct", "fhwa",
             "county", "hon", "honorable"}


def clean_name(run):
    """Return the personal name after the LAST title token; cap at 3 name tokens."""
    toks = [t for t in re.split(r"\s+", run.strip()) if t]
    last = -1
    for i, t in enumerate(toks):
        if t.lower().strip(".,") in TITLE_TOK:
            last = i
    # No office title anywhere in the run, but a jurisdiction word in it => this is a PLACE,
    # not a person ("Mayor Stanger, Clinton City seconded" leaves only "Clinton City").
    # Returning "" drops the attribution honestly rather than inventing a member.
    if last < 0 and any(t.lower().strip(".,") in JURISDICTION_TOK | ORG_TOK for t in toks):
        return ""
    cand = toks[last + 1:] if last >= 0 else toks[-3:]
    out = []
    for t in cand:
        tw = t.strip(".,'\"-")
        if not tw or not tw[0].isupper() or tw.lower() in STOP_NAME or tw.lower() in TITLE_TOK:
            break
        if tw.lower() in JURISDICTION_TOK and out:
            break                       # "Mayor Stanger of Clinton City" — City is a place
        out.append(tw)
        # 2026-07-26 (audit F5): STOP AT THE SENTENCE BOUNDARY. Punctuation was stripped
        # before the test, so "seconded by Mayor Mark Shepherd. No discussion" ran on into
        # the next sentence and minted a person called "Mark Shepherd No" — 12 such
        # non-existent people were in the federated person table, each with a role row.
        if t.rstrip("'\"").endswith((".", ";", ":", "!", "?", ",")):
            break
        if len(out) >= 3:
            break
    return " ".join(out)


# ---------------------------------------------------------------------------
# 2026-07-31: APPOSITIVE MOVER RECOVERY (the 4 motions the 2026-07-29 pass measured
# as an honest gap and deliberately left).
#
# WFRC writes some movers with an appositive between the name and the verb:
#   "Mayor Tom Dolan, Chair of the Budget Committee, made a motion"
#   "Carlton Christensen, UTA Board Trustee, made a motion"
#   "Mayor Mike Caldwell, Ogden City, made a motion"
# The name run cannot cross the lowercase "of the" and cannot span a comma mid-run,
# so the LEFTMOST run the anchor can reach is the appositive itself ("Budget
# Committee, ", "Ogden City, "), which the ORG/JURISDICTION guard correctly refuses
# to mint as a person. Result: the whole motion was dropped.
#
# WHY THIS IS A SEPARATE BACKWARD RULE AND NOT A WIDER ANCHOR:
# the original entry warned this regex is collateral-damage-prone, and it is —
# `movers` doubles as the WINDOW-BOUNDARY list (`end = movers[i+1].start()`), so any
# change to ANCHOR silently re-cuts every motion window in the corpus. ANCHOR is
# therefore UNTOUCHED. This rule runs only in the branch where the primary run
# already yielded NO mover, so it cannot alter a single existing row.
#
# THREE GUARDS, so it recovers movers without inventing any:
#  1. ACTIVE form only (the `n1` alternative). The passive "motion was made by X"
#     puts the name AFTER the cue; there is nothing behind the verb to recover.
#  2. STRUCTURAL: immediately behind the captured run there must be a comma whose
#     trailing remainder (the unconsumed head of the appositive) is short and free
#     of sentence punctuation — i.e. we are still inside one sentence, mid-appositive.
#  3. ATTESTATION: the recovered name must ALREADY be a mover/seconder somewhere in
#     the corpus (pass 1). A name this rule cannot corroborate is dropped, not
#     recorded — cardinal rule 1. All four real cases are attested; the fifth dropped
#     anchor, "With no further business, the Commissioner moved to the next item"
#     (navigation, must STAY dropped), fails guard 2/3 — the text behind it ends in
#     the lowercase "business", so no name run exists to recover.
_APPOS_MAX_TAIL = 60
_TRAILNAME = re.compile(r"([A-Z][A-Za-z.'\-]*(?:\s+[A-Z][A-Za-z.'\-]*){0,3})\s*$")


def recover_appositive(pre, attested):
    """Mover hidden behind an appositive. Returns (name, abs_offset) or ("", -1).

    `pre` is the text preceding the anchor's captured run; `attested` is the set of
    names pass 1 proved are real WFRC movers/seconders.
    """
    seg = pre[-200:]
    base = len(pre) - len(seg)
    j = seg.rfind(",")
    if j < 0:
        return "", -1
    tail = seg[j + 1:]                       # unconsumed head of the appositive
    if len(tail) > _APPOS_MAX_TAIL or re.search(r"[.;:!?]", tail):
        return "", -1                        # crossed a sentence boundary — not an appositive
    head = seg[:j].rstrip()
    m = _TRAILNAME.search(head)
    if not m:
        return "", -1                        # nothing name-shaped in front of the comma
    run = m.group(1)
    toks = run.split()
    offs, idx = [], 0
    for t in toks:
        idx = run.index(t, idx)
        offs.append(idx)
        idx += len(t)
    # Peel leading non-name words ("1a. ACTION: Minutes Carlton Christensen") until the
    # residue is a corroborated person; the FIRST attested residue wins.
    for k in range(len(toks)):
        cand = clean_name(" ".join(toks[k:]))
        if cand and cand in attested:
            return cand, base + m.start(1) + offs[k]
    return "", -1


def result_and_outcome(win):
    """Find the verbatim result clause + Pass/Fail/Unknown within a motion window."""
    low = win.lower()
    pats = [
        r"there (?:were|was)[^.]*dissent[^.]*?(?:approved|majority|carried|passed|adopted|failed)[^.]*\.",
        # 2026-07-31: "...from the vote." is a RECUSAL clause, not a result clause.
        # This alternative is tried before the generic result patterns, so on
        # 2023-08-24 the preceding sentence "Mayor Dandoy, as Mayor of Roy City,
        # abstained from the vote." beat the real clause and stored result_raw="the
        # vote." / outcome=Unknown for a motion the source says was "approved
        # unanimously with one abstention." Lookbehind only — the 168 genuine
        # "the vote/voting was unanimous" captures are untouched (proved by diff).
        r"(?<!from )the (?:affirmative )?vot(?:e|ing)[^.]*\.",
        # \b on every alternative: the bare "it" matched INSIDE "With", so 13 result_raw
        # values were stored one character short — "ith no further discussion the motion
        # was passed unanimously." That is a cardinal-rule-2 verbatim violation (audit F11).
        r"\b(?:the motion|it|the amendment|the minutes|the resolution|the financial statements)\b[^.]*"
        r"(?:passed|approved|accepted|carried|adopted|failed|certified)[^.]*\.",
        r"(?:passed|approved|accepted|carried|adopted|failed)\s+unanimously[^.]*\.",
        r"[^.]*\bunanimous[^.]*\.",
        r"[^.]*motion (?:passed|carried|failed|was approved)[^.]*\.",
    ]
    result = ""
    for p in pats:
        m = re.search(p, win, re.I)
        if m:
            result = re.sub(r"\s+", " ", m.group(0)).strip()
            break
    lo = result.lower() if result else low
    if re.search(r"\bfail|did not pass|not approved|motion (?:was )?defeated|voted down", lo):
        outcome = "Fail"
    elif re.search(r"unanim|approv|passed|carried|accept|adopt|certif|affirmative", lo):
        outcome = "Pass"
    else:
        outcome = "Unknown"
    return result, outcome


def motion_type(text):
    t = text.lower()
    if "public hearing" in t:
        return "Public Hearing"
    for kw, lab in [("certif", "Certification"), ("adopt", "Adoption"),
                    ("ratif", "Ratification"), ("endorse", "Endorsement"),
                    ("appoint", "Appointment"), ("authoriz", "Authorization"),
                    ("adjourn", "Adjournment"), ("recommend", "Recommendation"),
                    ("accept", "Acceptance"), ("approve", "Approval")]:
        if kw in t:
            return lab
    return "Motion"


def parse(md_path, date, attested=None):
    raw = open(md_path, encoding="utf-8").read()
    body = raw.split("---\n\n", 1)[-1]
    body = JUNK.sub(" ", body)                         # -> space (not empty: avoids gluing words)
    # cut the attendance roster / member table tail (not motion content)
    for marker in ["A recording of this meeting", "WFRC MEMBERS", "MEMBERS Present"]:
        i = body.find(marker)
        if i > 500:
            body = body[:i]
    text = re.sub(r"[ \t]*\n[ \t]*", " ", body)        # unwrap to flowed text
    text = re.sub(r" {2,}", " ", text)

    # body-section boundaries (position -> body) from number/timestamp-anchored headers
    marks = [(0, "Council")]
    for rx, name in BOUNDS:
        for m in rx.finditer(text):
            marks.append((m.start(), name))
    marks.sort()

    def body_at(pos):
        cur = "Council"
        for p, b in marks:
            if p <= pos:
                cur = b
            else:
                break
        return cur

    movers = list(ANCHOR.finditer(text))
    rows = []
    for i, m in enumerate(movers):
        start = m.start()
        end = movers[i + 1].start() if i + 1 < len(movers) else min(len(text), start + 800)
        mover = clean_name(m.group("n1") or m.group("n2") or "")
        if not mover or len(mover) < 3:
            # Appositive recovery — ONLY here, so no existing row can change. `start`
            # (and therefore the PREVIOUS motion's window end) is left alone; only this
            # row's window reaches back to include the verbatim mover phrase.
            if attested and m.group("n1") is not None:
                mover, at = recover_appositive(text[:m.start("n1")], attested)
                if mover:
                    start = at
            if not mover or len(mover) < 3:
                continue
        win = text[start:end]
        sm = SECOND.search(win)
        seconder = ""
        if sm:
            seconder = clean_name(sm.group(1) or sm.group(2) or "")
        result, outcome = result_and_outcome(win)
        mtext = re.sub(r"\s+", " ", win[:400]).strip()
        rows.append({
            "date": date, "body": body_at(start),
            "mover": mover, "seconder": seconder,
            "motion_type": motion_type(win[:300]),
            "result_raw": result, "outcome": outcome,
            "motion_text": mtext,
        })
    return rows


def main():
    meetings = [mt for mt in csv.DictReader(open(IDX, encoding="utf-8")) if mt["md_path"]]
    paths = [(os.path.join(ROOT, mt["md_path"]), mt["date"]) for mt in meetings]

    # PASS 1 — unaided extraction. Its mover/seconder names are the ONLY persons the
    # appositive rule is allowed to recover (guard 3). One pass, not a fixpoint: a
    # recovered name is by construction already in the set, so iterating cannot add
    # anyone, and refusing to bootstrap keeps the corroboration independent.
    attested = set()
    for md, date in paths:
        for r in parse(md, date):
            for k in ("mover", "seconder"):
                if r[k].strip():
                    attested.add(r[k].strip())

    allrows = []
    for mt in meetings:
        md = os.path.join(ROOT, mt["md_path"])
        rows = parse(md, mt["date"], attested)
        for n, r in enumerate(rows, start=1):
            r["motion_no"] = n
            r["source_md"] = mt["md_path"]
            r["source_url"] = mt["source_url"]
            r["doc_status"] = mt["doc_status"]
        allrows += rows
        bodies = ",".join(sorted({r["body"] for r in rows})) or "-"
        print("  %s  %2d motions  [%s]" % (mt["date"], len(rows), bodies))
    cols = ["date", "body", "motion_no", "mover", "seconder", "motion_type",
            "result_raw", "outcome", "motion_text", "doc_status", "source_md", "source_url"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        wr.writerows(allrows)
    print("\nTOTAL %d motions across %d meetings -> legislative/all_motions.csv"
          % (len(allrows), len({r["date"] for r in allrows})))


if __name__ == "__main__":
    main()
