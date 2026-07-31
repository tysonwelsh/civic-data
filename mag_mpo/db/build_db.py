#!/usr/bin/env python3
"""Build mag_mpo.db — the STANDARD 8-table civic-data schema (SCHEMA_SPEC §5) for the
Mountainland MPO (MPO Board + MPO TAC), extracted from the harvested minutes markdown
(legislative/minutes/, indexed by legislative/minutes_index.csv).

THE RECORDING CEILING (recon.md, verified): these bodies are ex-officio and
high-consensus. Minutes name the MOVER and SECONDER and record a tally-only result
("the motion passed all in favor") — NO roll call, NO per-member vote. So the `vote`
table is HONESTLY EMPTY (names_recorded=0 on every motion), an attribution ceiling
exactly like alta / nephi voice votes / west_jordan PC — never fabricated. Motions carry
full-name mover/seconder person links, a verbatim `result_raw`, a derived `outcome`, and
a keyword `disposition` (approve/deny/continue/table/procedural; NULL = unclassified).

Same 8 standard tables every per-city db has (body/person/meeting/application/motion/
vote/role/referral) + the post-2026-07 `provenance` and `disposition` motion columns, so
the repo-root build_cities_db.py federates it unchanged (gov_level='regional',
fed_index 202). `application`/`vote`/`role`/`referral` are empty by design (no structured
matter keys; no named votes; the project pipeline is the sibling projects/ module).
DERIVED + idempotent — rerun after a harvest; never hand-edit.
"""
import csv, os, re, sqlite3
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IDX = os.path.join(ROOT, "legislative", "minutes_index.csv")
DB = os.path.join(HERE, "mag_mpo.db")
CITY = "mag_mpo"

BODY_KIND = {"MPO Board": "council", "MPO TAC": "commission"}

TITLES = (r"Mayor|Commissioner|Councilmember|Council\s?Member|Councilman|Councilwoman|"
          r"Representative|Rep\.?|Senator|Sen\.?|Trustee|Vice[-\s]?Chair|Chairman|"
          r"Chairwoman|Co[-\s]?Chair|Chair|Mr\.?|Ms\.?|Mrs\.?|Dr\.?|BG|Director|"
          r"Executive Director|Commander")
TITLE_RE = re.compile(r"^(?:%s)\s+" % TITLES, re.I)

DDL = """
CREATE TABLE body (city TEXT, body_id INTEGER PRIMARY KEY, name TEXT, kind TEXT, UNIQUE(name));
CREATE TABLE person (city TEXT, person_id INTEGER PRIMARY KEY, full_name TEXT, name_key TEXT, UNIQUE(name_key));
CREATE TABLE meeting (city TEXT, meeting_id INTEGER PRIMARY KEY, body_id INTEGER, meeting_date TEXT,
    title TEXT, source_file TEXT, UNIQUE(body_id, source_file));
CREATE TABLE application (city TEXT, application_id INTEGER PRIMARY KEY, app_key TEXT, body_id INTEGER,
    name TEXT, rep_title TEXT, UNIQUE(app_key));
CREATE TABLE motion (city TEXT, motion_id INTEGER PRIMARY KEY, meeting_id INTEGER, body_id INTEGER,
    motion_no INTEGER, motion_text TEXT, motion_type TEXT, result_raw TEXT,
    outcome TEXT CHECK(outcome IN ('Pass','Fail','Unknown')),
    stage TEXT, recommendation TEXT,
    disposition TEXT, disposition_method TEXT, disposition_confidence TEXT,
    application_id INTEGER, app_match_method TEXT, app_confidence TEXT,
    mover_person_id INTEGER, seconder_person_id INTEGER, names_recorded INTEGER,
    source_file TEXT, provenance TEXT);
CREATE TABLE vote (city TEXT, vote_id INTEGER PRIMARY KEY, motion_id INTEGER, person_id INTEGER,
    vote_value TEXT, UNIQUE(motion_id, person_id));
CREATE TABLE role (city TEXT, role_id INTEGER PRIMARY KEY, person_id INTEGER, body_id INTEGER,
    first_seen TEXT, last_seen TEXT, n_votes INTEGER, UNIQUE(person_id, body_id));
CREATE TABLE referral (city TEXT, referral_id INTEGER PRIMARY KEY, primary_application_id INTEGER,
    primary_body TEXT, related_application_id INTEGER, related_body TEXT, match_method TEXT,
    confidence TEXT, shared_address TEXT, subject_score REAL, primary_date TEXT, related_date TEXT,
    gap_days INTEGER, note TEXT);
"""

# ---- name handling -------------------------------------------------------------
STOP = {"the", "of", "and", "a", "an", "to", "for", "on", "at", "by", "with", "board",
        "committee", "mpo", "motion", "he", "she", "it", "they", "there", "this",
        "that", "staff", "all", "page"}


def strip_title(name):
    prev = None
    n = name.strip()
    while n != prev:
        prev = n
        n = TITLE_RE.sub("", n).strip()
    return n


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


ANY_TITLE_RE = re.compile(r"^(?:%s)$" % TITLES, re.I)
PREFIX_DROP = {"commission", "council", "member", "meeting", "minutes", "action",
               "report", "draft", "item", "discussion", "update", "presentation",
               "business", "adjournment", "hearing", "consent", "approval",
               "committee", "board", "final", "amendment", "amended"}


def split_glued(tok):
    # PDF extraction sometimes drops the space in a name (BradKennison, ChrisTrusty)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", tok)


def clean_name(raw):
    """Return a canonical full name from a captured phrase, or '' if not name-like.

    The greedy capture can bleed a leading fragment ('Action Mayor X',
    'Meeting Minutes Commissioner Y'); when a TITLE is present we keep only the
    name AFTER the last title. Glued names are un-glued; STOP-word bleed is rejected."""
    toks = []
    for t in raw.split():
        toks += split_glued(t).split()
    # slice from the last title token, if any
    last_title = -1
    for i, t in enumerate(toks):
        if ANY_TITLE_RE.match(t) or ANY_TITLE_RE.match(t.rstrip(".")):
            last_title = i
    if last_title >= 0:
        toks = toks[last_title + 1:]
    # drop leading agenda/section words that bleed in ahead of a name
    while toks and toks[0].lower().strip(".,") in PREFIX_DROP:
        toks = toks[1:]
    toks = [t.strip(" .,-") for t in toks if t.strip(" .,-")]
    if not toks or any(t.lower() in STOP for t in toks):
        return ""
    if len(toks) > 4:
        return ""
    return " ".join(toks)


# capture a Capitalized name-run immediately preceding the verb; NAME tokens are
# Capital+lowercase (excludes ALL-CAPS acronyms TIP/UDOT/UT) and carry NO internal
# or trailing period, so a sentence boundary ('...Provo. Mayor Miller moved') hard-stops
# the run — the name is only what follows the last period.
NAME_RUN = r"((?:[A-Z][a-z][A-Za-z'’-]*\s+){1,5})"
# G8a (2026-07-31): 'mov(?:ed|es|e)' — the clerk's bare-'move' typo ("Mayor Brian
# Wall move that…", 2015-11-05 Elk Ridge) dropped a whole motion. "I move that"
# inside SUGGESTED-MOTION boilerplate cannot false-positive: "I" is not a
# NAME_RUN token (needs Capital+lowercase).
MOVED_RE = re.compile(NAME_RUN + r"mov(?:ed|es|e)\b", re.U)
SEC_RE = re.compile(NAME_RUN + r"second(?:ed|s)\b", re.U)
SEC_BY_RE = re.compile(r"second(?:ed)?\s+by\s+" + NAME_RUN, re.U)
# G8a (2026-07-31): two result-grammar fixes, both cardinal-rule-2 defects.
# (1) 'The ' is OPTIONAL — bare "Motion failed with 10 yes and 12 no votes by
#     [12 named mayors]" (2015-11-05 strike) and "Motion passed with 20 yes and
#     1 no (Mayor Miller)" (2014-09-04) never anchored, dropping whole DIVIDED
#     motions from a body whose only dissent signal is these sentences.
# (2) divided tallies run to SENTENCE end ([^.;]*), not first comma — the old
#     [^.,;]* truncated "passed with 18 yes" and amputated the printed name
#     lists; result_raw is verbatim and must carry them in full.
RESULT_RE = re.compile(
    r"(?:[Tt]he\s+)?[Mm]otion\s+(passed all in favor|passed unanimously|"
    r"passed(?:\s+(?:with|[0-9])[^.;]*)?|carried unanimously|carried|"
    r"failed(?:\s+with[^.;]*)?|failed|did not pass|"
    r"was approved|was denied|was tabled|was continued)", re.U)


def disposition_of(action):
    a = action.lower()
    proc = ("minute" in a or "agenda" in a or "adjourn" in a or
            ("cancel" in a and ("meeting" in a or "session" in a)) or
            "meeting date" in a or "meeting schedule" in a or "closed session" in a or
            "executive session" in a or "consent" in a or "elect" in a or
            "officers" in a or "ratify the" in a or "open the public hearing" in a or
            "close the public hearing" in a or "recess" in a or "public hearing" in a and "open" in a)
    if proc:
        return "procedural"
    if re.search(r"\b(den(y|ied|ies)|reject|not approv|disapprov)", a):
        return "deny"
    if re.search(r"\b(continu|postpon|tabl|defer)", a):
        return "continue"
    if re.search(r"\b(approv|adopt|authoriz|award|accept|amend|recommend|"
                 r"support|endors|ratif|forward|concur|modif|enter into)", a):
        return "approve"
    return ""


def outcome_of(result):
    r = result.lower()
    if "fail" in r or "did not pass" in r or "denied" in r:
        return "Fail"
    if "pass" in r or "carried" in r or "approved" in r:
        return "Pass"
    if "tabled" in r or "continued" in r:
        return "Unknown"
    return "Unknown"


def extract_motions(text):
    """Yield (motion_text, mover_raw, seconder_raw, result_raw, disposition, outcome)."""
    out = []
    moves = list(MOVED_RE.finditer(text))
    for res in RESULT_RE.finditer(text):
        rpos = res.start()
        # nearest 'moved' before the result, within 900 chars
        mv = None
        for m in moves:
            if m.end() <= rpos and rpos - m.end() < 900:
                mv = m
            elif m.end() > rpos:
                break
        if not mv:
            continue
        mover_raw = mv.group(1).strip()
        # action text between moved-verb and (seconder|result)
        seg = text[mv.end():rpos]
        sec_raw = ""
        sm = SEC_RE.search(seg)
        smb = SEC_BY_RE.search(seg)
        cut = len(seg)
        if sm:
            sec_raw = sm.group(1).strip(); cut = min(cut, sm.start())
        elif smb:
            sec_raw = smb.group(1).strip(); cut = min(cut, smb.start())
        action = seg[:cut].strip()
        action = re.sub(r"^(to|that)\s+", "", action, flags=re.I).strip(" .,-;:")
        action = re.sub(r"\s+", " ", action)[:400]
        if len(action) < 3:
            continue
        result_raw = res.group(0).strip()
        out.append((action, mover_raw, sec_raw, result_raw,
                    disposition_of(action), outcome_of(result_raw)))
    return out


def read_md(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n.*?\n---\n\n?", txt, re.S)
    return txt[m.end():] if m else txt


def main():
    rows = list(csv.DictReader(open(IDX, encoding="utf-8")))
    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # bodies
    bid = {}
    for i, name in enumerate(sorted({r["body"] for r in rows}), start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, i, name, BODY_KIND.get(name, "council")))
        bid[name] = i

    # --- pass 1: extract every motion, collect raw mover/seconder names ---------
    parsed = []   # (row, [motion tuples])
    raw_names = []
    for r in rows:
        text = read_md(os.path.join(ROOT, r["minutes_md"]))
        ms = extract_motions(text)
        parsed.append((r, ms))
        for action, mv, sc, res, disp, oc in ms:
            for nm in (mv, sc):
                cn = clean_name(nm)
                if cn:
                    raw_names.append(cn)

    # global surname -> {full names} to lift surname-only movers (older era) to full names
    surname_full = defaultdict(set)
    for cn in raw_names:
        toks = cn.split()
        if len(toks) >= 2:
            surname_full[toks[-1].lower()].add(cn)

    def canonical(raw):
        cn = clean_name(raw)
        if not cn:
            return None
        toks = cn.split()
        if len(toks) == 1:                      # surname only -> lift if unambiguous
            full = surname_full.get(toks[0].lower())
            if full and len(full) == 1:
                cn = next(iter(full))
        return cn

    # persons
    pid = {}
    pcount = 0
    def person_id(raw):
        nonlocal pcount
        cn = canonical(raw)
        if not cn:
            return None
        k = name_key(cn)
        if not k:
            return None
        if k not in pid:
            pcount += 1
            pid[k] = pcount
            db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, pcount, cn, k))
        return pid[k]

    # --- pass 2: write meetings + motions --------------------------------------
    mid = 0
    motion_id = 0
    for r, ms in parsed:
        mid += 1
        b = bid[r["body"]]
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, mid, b, r["date"], r["title"][:200], r["minutes_md"]))
        for mno, (action, mv, sc, res, disp, oc) in enumerate(ms, start=1):
            motion_id += 1
            db.execute(
                "INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (CITY, motion_id, mid, b, mno, action, "", res, oc, "", "",
                 disp or None, "keyword" if disp else None, "medium" if disp else None,
                 None, "", "", person_id(mv), person_id(sc), 0,
                 r["minutes_md"], "magutah_site"))

    db.commit()
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("mag_mpo.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role", "referral"):
        print("  %-12s %d" % (t, c(t)))
    with_mv = db.execute("SELECT COUNT(*) FROM motion WHERE mover_person_id IS NOT NULL").fetchone()[0]
    with_sc = db.execute("SELECT COUNT(*) FROM motion WHERE seconder_person_id IS NOT NULL").fetchone()[0]
    disp = db.execute("SELECT COUNT(*) FROM motion WHERE disposition IS NOT NULL").fetchone()[0]
    print("  motions w/ mover %d  seconder %d  disposition %d  (vote table EMPTY — tally-only ceiling)"
          % (with_mv, with_sc, disp))
    for bnm, k in db.execute("SELECT name, kind FROM body"):
        n = db.execute("SELECT COUNT(*) FROM motion m JOIN meeting mt ON mt.meeting_id=m.meeting_id "
                       "JOIN body bd ON bd.body_id=m.body_id WHERE bd.name=?", (bnm,)).fetchone()[0]
        print("    %-10s (%s): %d motions" % (bnm, k, n))
    db.close()


if __name__ == "__main__":
    main()
