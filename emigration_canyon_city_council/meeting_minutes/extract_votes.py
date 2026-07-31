#!/usr/bin/env python3
"""
extract_votes.py — Emigration Canyon City Council vote extraction (PURE deterministic).

Emigration Canyon incorporated as a **Metro Township** effective 2017-01-01 and converted
to a **City** effective 2024-05-01 (H.B. 35).  The same 5-member, all-at-large council
governs throughout; one member is peer-selected **Mayor**, who **PRESIDES AND VOTES**
(the Millcreek pattern — mayor counted in the 5, **max tally = 5**).

Votes are **NARRATIVE TALLY** (mover + seconder named, a printed count, majority unnamed):

  City era (2024+):
    "Council Member Griffith moved to approve Resolution R2026-10 ... Council Member Harris
     seconded the motion; vote was 5-0, unanimous in favor."
  Township era (2017-2024):
    "Council Member Harris, seconded by Council Member Pinon, moved to accept the ...
     The motion passed unanimously."
  Contested (rare):
    "... The motion passed 4 to 1, showing Mayor Smolka voted in opposition."
    "... The motion passed 4 to 1, showing that Mayor Smolka abstained from the vote."

CARDINAL RULE — never fabricate.
  * A unanimous / tally-only motion names no individual voters -> ONE tally-only row
    (blank member), never five fabricated Ayes.  `names_recorded:false`.
  * Named dissent ("... showing <role> <Name> voted in opposition/abstained") -> the named
    Nay/Abstain row(s) are emitted; the (unnamed) majority stays unnamed.
  * The presiding **Mayor VOTES** and is counted in the tally (max 5).
  * OCR-garbled surnames are fuzzy-matched to the observed roster; unresolved -> BLANK.

NO LLM, NO network.  Resumable (skips meetings whose JSON exists unless --force).
Reads minutes_index.csv + minutes/*.md, writes votes/*.json, all_votes.csv, roster.csv.
"""
import os, re, csv, json, sys, glob, difflib

# minutes_index.csv pmn_file_id values whose docs were recovered by a later PMN sweep
# and PROMOTED into this dataset (rather than the original audited harvest).  These carry
# provenance=pmn_minutes in all_votes.csv (the collection-standard trailing 14th column);
# every other audited-primary row is provenance=minutes.
#   692675  Council 2021-01-28   (PMN sweep 2026-07-17; the 3 township-era leads the
#   717575  Council 2021-02-25    crosscheck engine flagged missing_minutes — actual
#   950381  Council 2023-01-24    [Meeting Minutes] docs the original pull missed)
PMN_RECOVERED_FILE_IDS = {"692675", "717575", "950381"}

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# OBSERVED roster (surname -> canonical full name).  The mayor VOTES; the seat
# is peer-selected and shifts by era (Joe Smolka mayor in the township era; David
# Brems mayor in the city era).  The presiding mayor is detected per-document from
# the PRESENT block / "Mayor <X>, Chair, presided", not hard-coded here.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "smolka": "Joe Smolka",
    "hawkes": "Jennifer Hawkes",
    "brems": "David Brems",
    "harris": "Catherine Harris",
    "bowen": "Gary Bowen",
    "pinon": "Robert Pinon",
    "paine": "Robert Paine",
    "hook": "Steve Hook",
    "griffith": "Nicholas Griffith",
    "tippetts": "Tyler Tippetts",
}
# OCR / spelling variants -> canonical surname key
SURNAME_ALIASES = {
    "haurkes": "hawkes", "hawkcs": "hawkes", "hawlkes": "hawkes",
    "harrii": "harris", "harrls": "harris", "harri": "harris",
    "brem": "brems", "brens": "brems", "bremis": "brems",
    "pinion": "pinon", "pinnon": "pinon", "pinou": "pinon",
    "payne": "paine", "paine": "paine",
    "smolke": "smolka", "smoika": "smolka", "smoltka": "smolka",
    "bowon": "bowen", "griffth": "griffith", "griffith": "griffith",
    "tippets": "tippetts", "tippett": "tippetts",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())

ROLE_WORDS = (r"Council\s*Members?|Councilmembers?|C[o0]uncn?l?\s*Members?|"
              r"Deputy\s*Mayor|Mayor|Chair(?:man|person|woman)?|Vice[\s-]?Chair")
ROLEG = r"(?:" + ROLE_WORDS + r")"
NAME = r"([A-Z][A-Za-z'\-]{2,})"


def canon(token):
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip().lower()
    words = [w for w in t.split() if len(w) >= 2]
    for w in reversed(words):
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    for w in reversed(words):
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.82)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories).
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|approve the "
                 r"agenda|closed session|closed meeting|executive session|\btable\b|"
                 r"continue|postpone|strategy session|litigation)\b", t):
        return "Procedural/Administrative"
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development "
                 r"agreement|overlay|site plan|street vacation|dwelling|setback|"
                 r"lot line|hillside|sensitive lands|watershed|slope", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"tentative budget|final budget|adopt\w*.*budget|budget for|appropriat|"
                 r"fee schedule", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat|swear|oath|"
                 r"vice[\s-]?chair|deputy mayor|select.*mayor", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b|\bo-\d|\d{4}-o-", t):
        return "Ordinance"
    if re.search(r"\bresolution\b|\br-?\d|\br20\d", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|commend|ceremonial|"
                 r"awareness (?:week|month)|designating", t):
        return "Ceremonial"
    return "Other"


# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(r"\x0c|Page\s+\d+\s+of\s+\d+", re.I)


def split_frontmatter(raw):
    parts = re.split(r"\n---\n", raw)
    head = "\n".join(parts[:3]) if len(parts) >= 3 else parts[0]
    body = parts[-1]
    bm = re.search(r"\*\*Body:\*\*\s*(\w+)", head)
    mt = re.search(r"\*\*Meeting type:\*\*\s*(\w+)", head)
    return (bm.group(1) if bm else "Council"), (mt.group(1) if mt else "Regular"), body


# ---------------------------------------------------------------------------
# Attendance sub-block labels that OPEN the NON-COUNCIL attendee list — staff, legal
# counsel, the recorder, outside-agency liaisons (UPD/UFA/SLCo Animal Services) and
# residents.  A roster surname under one of these labels is an attendee, NOT a seated
# member: Gary Bowen left the council after 2021-12-14 but keeps appearing at every
# city-era meeting as the "Salt Lake County Animal Services Representative/Liaison"
# under "Others Present:".  A bare name-anywhere-in-the-window match credited him with
# 9 phantom meetings through 2026-04-21 (fixed 2026-07-29).
# ---------------------------------------------------------------------------
NONCOUNCIL_BLOCK_RE = re.compile(
    r"\b(?:STAFF|OTHERS?|GUESTS?|PUBLIC|ALSO|VISITORS?|CITIZENS?)\s+"
    r"(?:PRESENT|IN\s+ATTENDANCE|ATTENDING)\s*:", re.I)


def _has_surname(s):
    return any(re.search(r"\b" + sn + r"\b", s, re.I) for sn in SURNAMES)


def trim_to_council_block(region):
    """Cut a PRESENT region at the staff/others attendance label that follows the roll.

    EC minutes come in TWO layouts and the cut must respect both:
      * CITY era — the blocks are STACKED ("Council Members Present: <names> Staff
        Present: <names> Others Present: <names>").  The label follows the seated
        members, so cutting at it is exactly right.
      * TOWNSHIP era — the blocks are TWO-COLUMN ("COUNCIL MEMBERS ELECRONICALLY
        PRESENT:" | "OTHERS IN ATTENDANCE:" side by side).  Flattening the text puts
        the *label* AHEAD of every name, so a blind cut would drop the whole council.

    So the cut is applied only at a label that already has a roster surname before it —
    i.e. only where the block genuinely is stacked.  Strictly restrictive: it can only
    ever remove names, and only names printed after the council roll ended.
    """
    for lm in NONCOUNCIL_BLOCK_RE.finditer(region):
        if _has_surname(region[:lm.start()]):
            return region[:lm.start()]
    return region


def parse_present(flat):
    """Seated members + the presiding mayor from the PRESENT block."""
    present, mayor = [], None
    m = re.search(r"(?:COUNCIL\s+MEMBERS?|MEMBERS?)\s+PRESENT[:\s]", flat, re.I)
    region = flat[m.end(): m.end() + 500] if m else flat[:600]
    region = trim_to_council_block(region)
    # mayor markers
    mm = re.search(r"Mayor\s+" + NAME, flat[:1500]) or None
    # scan present region for roster surnames
    for sn in SURNAMES:
        if re.search(r"\b" + sn + r"\b", region, re.I):
            nm = SURNAME_TO_FULL[sn]
            if nm not in present:
                present.append(nm)
    # mayor: "<Name>, Mayor" / "Mayor <Name>, Chair, presided"
    md = re.search(NAME + r"\s*,?\s*Mayor\b", flat[:1500]) or \
        re.search(r"\bMayor\s+" + NAME, flat[:1500])
    if md:
        mayor = canon(md.group(1))
    return present, mayor


# ---------------------------------------------------------------------------
# Motion anchoring — two grammars merged, scanned in document order.
# ---------------------------------------------------------------------------
# Township form: "<role> <Name>, seconded by <role> <Name>, moved to ..."
# The clerk usually writes "seconded by"; ONE township doc (2019-06-19, the Stormwater
# Maintenance Agreement motion) writes the label "second by" (no -ed).  Accepting the
# optional -ed recovers that otherwise-dropped motion; "second by" occurs exactly once
# corpus-wide, so the change is strictly additive (a single recovered motion).
TWP_RE = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s*,\s*second(?:ed)?\s+by\s+" + ROLEG + r"?\s*" + NAME +
    r"\s*,\s*moved\b", re.I)
# City form: "<role> <Name> moved to ..."
CITY_RE = re.compile(ROLEG + r"?\s*" + NAME + r"\s+moved\b(?!\s+by)", re.I)
# seconder for city form: "<role> <Name> seconded the motion"
SECOND_RE = re.compile(ROLEG + r"?\s*" + NAME + r"\s+seconded\b|seconded\s+by\s+" +
                       ROLEG + r"?\s*" + NAME, re.I)

OUTCOME_RE = re.compile(
    r"[Tt]he\s+motion\s+(passed|failed|carried|did\s+not\s+(?:pass|carry))|"
    r"vote\s+was\s+(\d+)\s*-\s*(\d+)|motion\s+(passed|failed|carried)", re.I)
TALLY_RE = re.compile(r"vote\s+was\s+(\d+)\s*-\s*(\d+)|"
                      r"passed\s+(\d+)\s*(?:-|to)\s*(\d+)|"
                      r"(\d+)\s*-\s*(\d+)\s*,?\s*unanimous", re.I)
UNAN_RE = re.compile(r"unanimous|passed\s+unanimously|carried\s+unanimously", re.I)
# A motion that dies for lack of a second never reaches a vote -> it is SKIPPED (not a
# recorded Fail).  The clerk writes both "failed FOR lack of a second" and "failed DUE TO
# a lack of a second"; the guard window (region[:om.start()+40]) truncates the trailing
# "second", so require only "...lack of" (the "a second" tail is optional).
LACK_SECOND = re.compile(r"(?:fail\w*|died)\s+(?:for|due\s+to)\s+(?:a\s+)?lack\s+of"
                         r"(?:\s+a?\s*second)?|no\s+second", re.I)
# named dissent: "showing [that] <role> <Name> voted in opposition|abstained|opposed|voted no"
DISSENT_RE = re.compile(
    r"showing\s+(?:that\s+)?" + ROLEG + r"?\s*" + NAME +
    r"\s+(voted\s+in\s+opposition|abstained|opposed|voted\s+no|voted\s+nay|"
    r"voted\s+against|recused(?:\s+him|\s+her)?\w*|dissent\w*)", re.I)
DISSENT2_RE = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s+(voted\s+no|voted\s+nay|voted\s+against|"
    r"voted\s+in\s+opposition|abstained|recused(?:\s+him|\s+her)?\w*|"
    r"opposed\s+the\s+motion)", re.I)
# full inline roll call (rare): "... with a roll call vote showing Council Member Pinon
# voting "Aye," ... Council Member Harris voting "Nay," ..." (2023-08-22) — every member
# named with a vote word; >=2 hits = a genuine roll, all buckets recorded.
ROLLCALL_RE = re.compile(
    ROLEG + r"?\s*" + NAME + r"\s+voting\s+[\"“”']*(Aye|Yes|Nay|No|Abstain\w*|Recus\w*)",
    re.I)


def clean_motion_text(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^,?\s*seconded\s+by\s+.*?,\s*moved\s+", "", s, flags=re.I)
    s = re.sub(r"\s*,?\s*seconded\s+by\s+" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+.*$", "",
               s, flags=re.I)
    s = re.sub(r"\s*" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+\s+seconded.*$", "", s, flags=re.I)
    s = re.sub(r"^(?:to\s+)", "", s)
    s = s.strip(" .,;:—-")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def find_anchors(flat):
    anchors = []
    for m in TWP_RE.finditer(flat):
        mover = canon(m.group(1)); seconder = canon(m.group(2))
        if mover:
            anchors.append((m.start(), m.end(), mover, seconder, "twp"))
    for m in CITY_RE.finditer(flat):
        mover = canon(m.group(1))
        if mover:
            anchors.append((m.start(), m.end(), mover, None, "city"))
    anchors.sort(key=lambda a: a[0])
    out = []
    for a in anchors:
        if out and abs(a[0] - out[-1][0]) < 8:
            continue
        out.append(a)
    return out


def build_result(tally, unanimous, passed):
    if tally:
        a, n = tally
        base = f"{a}-{n}"
        if unanimous:
            base += " (unanimous)"
        return base + (" Pass" if passed else " Fail")
    if unanimous:
        return "Pass (unanimous)"
    return "Pass" if passed else "Fail"


def extract_meeting(path, rel_source, date, year, title, file_body, mtype):
    raw = open(path, encoding="utf-8").read()
    _b, _mt, body = split_frontmatter(raw)
    flat = re.sub(r"\s+", " ", FOOTER_RE.sub(" ", body))
    present, mayor = parse_present(flat)

    anchors = find_anchors(flat)
    votes = []
    for i, (astart, aend, mover, sec0, form) in enumerate(anchors):
        nxt = anchors[i + 1][0] if i + 1 < len(anchors) else len(flat)
        region = flat[aend:nxt]

        om = OUTCOME_RE.search(region[:1200]) or OUTCOME_RE.search(region)
        if not om:
            continue
        if LACK_SECOND.search(region[:om.start() + 40]):
            continue

        # seconder
        seconder = sec0
        if not seconder:
            sm = SECOND_RE.search(region[:om.start() + 5] if om else region[:300])
            if sm:
                seconder = canon(sm.group(1) or sm.group(2))

        # motion text
        if form == "twp":
            motion_text = clean_motion_text(flat[aend:aend + (om.start())][:500])
        else:
            cut = region[:om.start()]
            cut = re.split(r"\.?\s*" + ROLEG + r"?\s*[A-Z][A-Za-z'\-]+\s+seconded",
                           cut, 1)[0]
            motion_text = clean_motion_text(cut)
        if len(motion_text) < 3:
            motion_text = clean_motion_text(region[:200])

        # outcome window: this motion's result sentence + a little tail for the tally
        win = region[max(0, om.start() - 5): om.start() + 200]
        outcome_word = (om.group(1) or om.group(4) or "").lower()
        if om.group(2):  # "vote was N-M"
            outcome_word = "passed"
        passed = not (outcome_word.startswith("fail") or outcome_word.startswith("did"))

        tm = TALLY_RE.search(win)
        tally = None
        if tm:
            g = [x for x in tm.groups() if x is not None]
            tally = (int(g[0]), int(g[1]))
        unanimous = bool(UNAN_RE.search(win))
        if tally and tally[1] == 0:
            unanimous = True
        if unanimous and not tally:
            tally = None

        # named dissent — ONLY when the printed tally shows dissent (n>0).  A motion
        # that "passed unanimously" names no dissenter, so we never scan its tail
        # (which would bleed the next item's names into this vote).
        dissent = {}
        aye = []
        if tally and tally[1] > 0 and not unanimous:
            dwin = region[max(0, om.start() - 5): om.start() + 160]
            # full inline roll call first ("<Name> voting "Aye/Nay"" x members):
            rolls = list(ROLLCALL_RE.finditer(region[max(0, om.start() - 5):
                                                     om.start() + 400]))
            if len(rolls) >= 2:
                for rm in rolls:
                    nm = canon(rm.group(1))
                    if not nm:
                        continue
                    w = rm.group(2).lower()
                    if w.startswith(("aye", "yes")):
                        if nm not in aye:
                            aye.append(nm)
                    elif w.startswith("abstain"):
                        dissent[nm] = "Abstain"
                    elif w.startswith("recus"):
                        dissent[nm] = "Recuse"
                    else:
                        dissent[nm] = "Nay"
            else:
                for dm in list(DISSENT_RE.finditer(dwin)) + list(DISSENT2_RE.finditer(dwin)):
                    nm = canon(dm.group(1))
                    act = dm.group(2).lower()
                    if not nm:
                        continue
                    dissent[nm] = ("Abstain" if "abstain" in act
                                   else "Recuse" if "recus" in act else "Nay")

        names_recorded = bool(dissent) or bool(aye)
        nay = sorted(n for n, v in dissent.items() if v == "Nay")
        abstain = sorted(n for n, v in dissent.items() if v == "Abstain")
        recuse = sorted(n for n, v in dissent.items() if v == "Recuse")

        if tally:
            passed = tally[0] > tally[1]
        result = build_result(tally, unanimous, passed)

        # mayor votes and is counted in the tally (max 5) whenever a mayor is seated
        mayor_voted = mayor is not None

        rec = {
            "motion": motion_text,
            "body": "Council",
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse,
            "tally": list(tally) if tally else None,
            "unanimous": unanimous,
            "mayor": mayor or "",
            "mayor_voted": mayor_voted,
        }
        votes.append(rec)

    for n, v in enumerate(votes, 1):
        v2 = {"motion_no": n}; v2.update(v); votes[n - 1] = v2

    return {"date": date, "year": int(year), "title": title, "meeting_type": mtype,
            "file_body": "Council", "present": present, "mayor": mayor or "",
            "source": rel_source, "votes": votes}


# ---------------------------------------------------------------------------
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
            meeting = extract_meeting(path, r["path"], r["date"], r["year"], r["title"],
                                      "Council", r.get("meeting_type", "Regular"))
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr); continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        json.dump(meeting, open(jp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    rebuild_csv(rows)
    build_roster(rows)
    print("done")


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        prov = ("pmn_minutes" if r.get("pmn_file_id") in PMN_RECOVERED_FILE_IDS
                else "minutes")
        for v in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=obj["title"],
                        body=v["body"], motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v.get("mover", ""), seconder=v.get("seconder", ""),
                        source=obj["source"], provenance=prov)
            emitted = False
            for key, label in (("aye", "Aye"), ("nay", "Nay"),
                               ("abstain", "Abstain"), ("recuse", "Recuse")):
                for nm in v.get(key, []):
                    row = dict(base); row["member"] = nm; row["vote"] = label
                    out.append(row); emitted = True
            if not emitted:  # tally-only / unanimous -> one placeholder row (blank member)
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
        people = set(obj.get("present", []))
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k) in FULLNAMES:
                    people.add(v[k])
            people.update(v.get("nay", [])); people.update(v.get("abstain", []))
            people.update(v.get("aye", [])); people.update(v.get("recuse", []))
        for p in people:
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0,
                                    "mayor": False})
            d["first"] = min(d["first"], date); d["last"] = max(d["last"], date)
            d["n"] += 1
            if obj.get("mayor") == p:
                d["mayor"] = True
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            role = "Council Member (served as Mayor)" if d["mayor"] else "Council Member"
            w.writerow([nm, role, d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
