#!/usr/bin/env python3
"""
extract_votes.py — Copperton Town/Metro-Township COUNCIL vote extraction (PURE deterministic).

Reads the council minutes markdown listed in meeting_minutes/minutes_index.csv, finds each
recorded motion (mover / seconder / numeric tally / named roll call), and emits:
  - one JSON per meeting -> meeting_minutes/votes/<year>/<date>/<file>.json
  - a rebuilt long CSV   -> meeting_minutes/all_votes.csv (13-col standard)
  - roster.csv           -> meeting_minutes/roster.csv (observed)
NO LLM, NO network. Resumable: skips meetings whose JSON exists unless --force.

CARDINAL RULE — never fabricate.
  Copperton council votes are NARRATIVE-TALLY. Three source forms:
   A) metro-township (2018-2024), dominant: "<role> X, seconded by <role> Y, moved to <...>.
      The motion passed unanimously."  -> mover/seconder NAMED, roll is a collective
      "unanimously" with NO per-member names and NO number -> TALLY-ONLY (blank member).
   B) town (2025-2026): "<role> X moved to <...>. <role> Y seconded the motion; vote was
      5-0, unanimous in favor."  -> mover/seconder named + a NUMERIC tally (max 5 = the 4
      Council Members + the VOTING Mayor) -> TALLY-ONLY with tally_ayes/tally_nays stored.
   C) named roll call (both eras, ~48 motions): "... Council Member X voting 'Aye,' Council
      Member Y voting 'Nay,' ... and Mayor Clayton voting 'Aye'." -> per-member Aye/Nay/
      Abstain rows (names_recorded:true). The MAYOR VOTES (appears as "Mayor <name> voting").
  Tally-only motions keep member/vote BLANK — five individual votes are NEVER fabricated
  from a collective "unanimously". A motion that "failed for lack of a second" never came
  to a vote and is skipped.

FORM SEAM: metro township (2017-2024, at-large seats A-E, council-elected chair titled
"Mayor") -> TOWN (2024-05-01+, separately-elected VOTING Mayor + 4 Council Members). Max
tally = 5 in BOTH eras. Roster is OBSERVED from mover/seconder/named-vote slots (never a
fixed list); residents/staff never occupy those slots so they never enter the roster.
"""
import os, re, csv, json, sys, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# Observed roster: surname(lower) -> canonical display full name. Built from names seen in
# mover/seconder/named-vote slots + attendance blocks (high-confidence membership evidence).
CANON = {
    "clayton": "Sean Clayton",      # Council Member -> chair/"Mayor" (2022+) -> Town Mayor (2025+)
    "stitzer": "Tessa Stitzer",     # Deputy Mayor / Mayor Pro Tempore
    "bailey": "Kathleen Bailey",
    "severson": "Kevin Severson",
    "pazell": "Apollo Pazell",
    "olsen": "Dave Olsen",
    "mccalmon": "Linda McCalmon",
    "pratt": "Jonathan Pratt",
    "patrick": "Ron Patrick",
    "sorensen": "Sorensen",
}
# people who serve/served as the voting Mayor/chair (for the mayor-vote flag)
MAYORS = {"Sean Clayton"}
# OCR variants -> canonical surname key
ALIASES = {"stieer": "stitzer", "stieer": "stitzer", "sti8er": "stitzer",
           "mccalman": "mccalmon", "mccaimon": "mccalmon", "seversen": "severson",
           "paull": "pazell", "olson": "olsen"}

ROLE = (r"(?:Deputy\s+Mayor|Mayor\s+Pro\s+Tempore|Mayor\s+Pro\s+Tem|Mayor|"
        r"Council\s*Members?|Councilmembers?|Council\s*member|Chair(?:person)?|Vice\s+Chair)")
NAME = r"([A-Z][A-Za-z’'\-]+(?:\s+[A-Z][A-Za-z’'\-]+)?)"


def canon(token):
    """Map a captured name phrase to a roster full name, else None."""
    if not token:
        return None
    words = re.findall(r"[A-Za-z’'\-]{2,}", token)
    for w in reversed(words):                 # surname is usually the last capitalized word
        wl = re.sub(r"[^a-z]", "", w.lower())
        wl = ALIASES.get(wl, wl)
        if wl in CANON:
            return CANON[wl]
    for w in reversed(words):                 # first-name fallback (rare full-name forms)
        wl = w.lower()
        for sn, full in CANON.items():
            if full.lower().split()[0] == wl:
                return full
    return None


def is_mayor_slot(role):
    return bool(re.match(r"\s*(?:Deputy\s+Mayor|Mayor\s+Pro|Mayor)\b", role or "", re.I)) \
        and "council" not in (role or "").lower()


# ---- motion-type taxonomy (compact) --------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|accept|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|approve the agenda|"
                 r"closed session|closed meeting|executive session|\btable\b|postpone|"
                 r"continue to|electronic meeting)\b", t):
        return "Procedural/Administrative"
    if re.search(r"mayor pro tem|deputy mayor|as mayor|as chair|elect", t):
        return "Appointment"
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development agreement|"
                 r"overlay|site plan|street vacation|easement vacation|lot line", t):
        return "Land-Use/Zoning"
    if re.search(r"budget|appropriat|expenditure|fee schedule|attorney (?:bill|fee)|legal fee|"
                 r"financial report|pay the|approve the .*bill", t):
        return "Budget/Fiscal"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat|representative", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award|professional services|"
                 r"agreement with|services agreement|enter into an agreement|donation", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|pledge", t):
        return "Ceremonial"
    return "Other"


# ---- anchors -------------------------------------------------------------
# mover [, seconded by seconder ] , (moved|nominated|made a motion|made by ...)
MOVE_RE = re.compile(
    r"(?:A\s+motion\s+was\s+made\s+by\s+)?"
    r"(" + ROLE + r"\s+" + NAME[1:-1] + r")"          # 1: mover phrase
    r"(?:\s*,?\s*seconded\s+by\s+(" + ROLE + r"\s+" + NAME[1:-1] + r"))?"  # 2: inline seconder
    r"\s*,?\s*(?:moved|nominated|made\s+a\s+motion|motioned)\b", re.I)

SECOND_AFTER = re.compile(r"(" + ROLE + r"\s+" + NAME[1:-1] + r")\s+seconded", re.I)
TALLY_RE = re.compile(r"vote\s+was\s+(?:unanimous(?:ly)?\s+)?(\d+)\s*[-–]\s*(\d+)", re.I)
OUTCOME_RE = re.compile(r"motion\s+(passed|carried|failed|did\s+not\s+(?:pass|carry))", re.I)
UNANIMOUS = re.compile(r"unanimous", re.I)
LACK_SECOND = re.compile(r"(?:fail\w*|died)\s+(?:for|due\s+to)\s+(?:a\s+)?lack\s+of\s+a?\s*second|"
                         r"no\s+second|lack\s+of\s+a\s+second", re.I)
# named per-member vote: "<role> <name> vot(ing|ed) 'Aye'/'Nay'"
NAMED_VOTE = re.compile(
    r"(?:and\s+)?(" + ROLE + r")\s+" + NAME + r"\s+vot(?:ing|ed)\s+[“‘\"']?"
    r"(Aye|Nay|No|Yes|in\s+favor|against|abstain\w*)", re.I)
ABSTAIN_RE = re.compile(r"(" + ROLE + r")\s+" + NAME + r"\s+(abstain\w*|recus\w*)", re.I)


def norm_vote(word):
    w = word.lower()
    if w.startswith("abstain"):
        return "Abstain"
    if w.startswith("recus"):
        return "Recuse"
    if w.startswith(("aye", "yes", "in favor")) or "favor" in w:
        return "Aye"
    return "Nay"


def clean_motion(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:,?\s*seconded\s+by\s+.*?,\s*)", "", s, flags=re.I)
    s = re.sub(r"^(?:to\s+)?", "to ", s) if not s.lower().startswith(("to ", "that ")) else s
    s = re.sub(r"\s*[.;]\s*(?:the\s+)?motion\s+(?:passed|carried|failed).*$", "", s, flags=re.I)
    s = re.sub(r"\s*" + ROLE + r"\s+[A-Z][A-Za-z]+\s+seconded.*$", "", s, flags=re.I)
    s = re.sub(r"[.;,]\s*The\s*$", "", s)          # trailing dangling "The (motion...)"
    s = re.sub(r"\s+The$", "", s)
    s = s.strip(" .,;:—-")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


FOOTER_RE = re.compile(r"\x0c|Page\s+\d+\s+of\s+\d+", re.I)


def split_body(raw):
    parts = re.split(r"\n---\n", raw, maxsplit=1)
    return parts[1] if len(parts) > 1 else raw


def extract_meeting(path, rel_source, date, year, title):
    raw = open(path, encoding="utf-8").read()
    body = split_body(raw)
    flat = FOOTER_RE.sub(" ", body)
    flat = re.sub(r"[ \t]+", " ", flat)
    flat = re.sub(r"\s+", " ", flat)

    anchors = list(MOVE_RE.finditer(flat))
    votes = []
    for i, m in enumerate(anchors):
        astart = m.start()
        aend = m.end()
        nxt = anchors[i + 1].start() if i + 1 < len(anchors) else len(flat)
        window = flat[aend:nxt]

        mover = canon(m.group(1))
        seconder = canon(m.group(2)) if m.group(2) else None
        if not seconder:
            sm = SECOND_AFTER.search(window[:300])
            if sm:
                seconder = canon(sm.group(1))

        # find outcome / tally within a bounded lookahead
        look = window[:600]
        om = OUTCOME_RE.search(look)
        tm = TALLY_RE.search(look)
        named = list(NAMED_VOTE.finditer(look))
        abst = list(ABSTAIN_RE.finditer(look))
        if not (om or tm or named):
            # no recorded verdict near this move verb -> not a real recorded vote
            continue
        if LACK_SECOND.search(look[:120]) and not (tm or named or om):
            continue

        # motion text = from move-verb to the outcome / second / tally / roll call
        cut = len(window)
        rollcue = re.search(r"[Rr]oll\s+was\s+called|showing\s+the\s+vote|"
                            r"[Tt]he\s+(?:vote|voting)\s+(?:was|to be)|"
                            r"[Cc]alled\s+for\s+(?:a|the)\s+vote", window)
        for c in (om, tm, SECOND_AFTER.search(window), rollcue):
            if c:
                cut = min(cut, c.start())
        if named:
            cut = min(cut, named[0].start())
        if abst:
            cut = min(cut, abst[0].start())
        motion_text = clean_motion(window[:cut])
        if len(motion_text) < 3:
            motion_text = clean_motion(window[:200])

        # ---- votes ----
        # A genuine ROLL CALL = per-member Aye/Nay named. A lone "X abstained"/"recused"
        # alongside a collective "passed unanimously" is NOT a roll call -> the motion is
        # tally-only, but the named dissenter is still recorded (never fabricate the
        # unnamed majority as five individual Ayes).
        roll = {}
        mayor_voted = False
        for nm in named:
            person = canon(nm.group(2))
            if person:
                roll[person] = norm_vote(nm.group(3))
                if is_mayor_slot(nm.group(1)):
                    mayor_voted = True
        abstainers = {}
        for ab in abst:
            person = canon(ab.group(2))
            if person and person not in roll:
                abstainers[person] = "Recuse" if ab.group(3).lower().startswith("recus") else "Abstain"
                if is_mayor_slot(ab.group(1)):
                    mayor_voted = True

        has_rollcall = len(roll) >= 1
        members = dict(roll)
        members.update(abstainers)   # abstain/recuse rows are always emitted (named dissent)
        aye = sorted(n for n, v in members.items() if v == "Aye")
        nay = sorted(n for n, v in members.items() if v == "Nay")
        abstain = sorted(n for n, v in members.items() if v == "Abstain")
        recuse = sorted(n for n, v in members.items() if v == "Recuse")
        names_recorded = has_rollcall

        # tally + outcome
        tally_ayes = tally_nays = None
        if tm:
            tally_ayes, tally_nays = int(tm.group(1)), int(tm.group(2))
        outcome = None
        if om:
            ow = (om.group(1) or "").lower()
            outcome = "Fail" if ow.startswith(("fail", "did")) else "Pass"
        unanimous = bool(UNANIMOUS.search(look[:200]))

        if has_rollcall:
            passed = len(aye) > len(nay)
            result = f"{len(aye)}-{len(nay)} {'Pass' if passed else 'Fail'}"
        elif tally_ayes is not None:
            passed = tally_ayes > tally_nays
            result = f"{tally_ayes}-{tally_nays} {'Pass' if passed else 'Fail'}" + \
                     (" (unanimous)" if unanimous and tally_nays == 0 else "")
        else:
            passed = (outcome != "Fail")
            result = ("Pass" if passed else "Fail") + (" (unanimous)" if unanimous else "")
        if abstainers and not has_rollcall:
            result += " (w/ named abstention)"

        rec = {
            "motion": motion_text,
            "body": "Council",
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse,
            "mayor_voted": mayor_voted or (any(p in MAYORS for p in members)),
        }
        if not names_recorded:
            rec["tally_only"] = {"unanimous": unanimous,
                                 "tally_ayes": tally_ayes, "tally_nays": tally_nays}
        votes.append(rec)

    for n, v in enumerate(votes, 1):
        vv = {"motion_no": n}
        vv.update(v)
        votes[n - 1] = vv
    return {"date": date, "year": int(year), "title": title, "body": "Council",
            "source": rel_source, "votes": votes}


# ---- driver --------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.split("/")
    return os.path.join(VOTES_DIR, str(year), parts[-2], parts[-1].replace(".md", ".json"))


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
            meeting = extract_meeting(path, r["path"], r["date"], r["year"], r["title"])
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr); continue
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
                             ("recuse", "Recuse")):
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
        date = obj["date"]
        people = set()
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k):
                    people.add(v[k])
            for k in ("aye", "nay", "abstain", "recuse"):
                people.update(v.get(k, []))
        for p in people:
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date); d["last"] = max(d["last"], date); d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            role = "Mayor/Chair" if nm in MAYORS else "Council Member"
            w.writerow([nm, role, d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
