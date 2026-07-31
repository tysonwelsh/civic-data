#!/usr/bin/env python3
"""
extract_votes.py — White City PLANNING COMMISSION vote extraction
(PURE deterministic; no LLM, no network; resumable — skips meetings whose JSON
exists unless --force).

SOURCE. The PC minutes were recovered from Utah Public Notice body 5879
(promoted from ../pmn_backfill/ on 2026-07-16 — the city's Streamline site
publishes no PC minutes). They are Greater Salt Lake MSD "Planning and
Development Services" MEETING MINUTE SUMMARY documents (recorder Wendy Gurr) —
the same MSD document family as the Kearns PC — so every all_votes.csv row
carries provenance=pmn_minutes (the collection's trailing-14th-column standard).

TWO motion grammars, stable 2019→2025 (one clerk pool):

 A) STRUCTURED BLOCK (dominant — the MSD form):
      Motion: To recommend approval of file #30939 to the White City Metro
              Township Council as presented.
            Motion by: Commissioner Frailey
            2nd by: Commissioner Mitchell
            Vote: Commissioners voted unanimous in favor (of commissioners present)
    Fields may be BLANK (one 2019-06-25 block prints empty Motion by:/2nd by:/
    Vote: lines) -> emitted with blank mover/seconder and an EMPTY result (the
    source printed no outcome; honest NULL, magna-precedent).
    Named abstention (single observed case, 2021-05-25):
      "Vote: Commissioner Millen abstained, all other commissioners voted in
       favor (of commissioners present)" -> one named Abstain row; the majority
    is honestly UNNAMED.

 B) INLINE PROCEDURAL (hearing open/close, adjourn, recess):
      "Commissioner Wilson motioned to close the public hearing, Commissioner
       Millen seconded that motion."
    These print NO vote outcome -> emitted with an EMPTY result (real motions,
    outcome never recorded; do NOT read an empty result as failure).

NAMING CEILING — the MSD form names only mover + seconder (+ a named
abstainer); a "voted unanimous in favor" roll is NEVER individually named ->
one tally-only placeholder row (blank member/vote). Commissioners are resolved
to full names via the attendance-grid roster below ("Hunsaker" is a recurring
clerk spelling of Christopher Huntzinger — the attendance grids in the same
documents list only Huntzinger).

CARDINAL RULE — never fabricate. Unnamed majorities stay unnamed; an
unresolvable name is kept verbatim (surname), never guessed.
"""
import os, re, csv, json, sys, difflib

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Roster — surname(lower) -> full display name, built from the attendance grids
# of the 22 recovered minutes (2019-2025).  The commission drifts across the
# window; every voter/mover surname observed maps here.
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "seiger-webster": "Christy Seiger-Webster",
    "spagnuolo":      "Christopher Spagnuolo",
    "frailey":        "Robert Frailey",
    "mitchell":       "Jim Mitchell",
    "wilson":         "Gene Wilson",
    "blair":          "Antoinette Blair",
    "millen":         "Weston Millen",
    "huntzinger":     "Christopher Huntzinger",
}
SURNAME_ALIASES = {
    # clerk variants observed in the corpus
    "hunsaker": "huntzinger",   # 2023-03-23 / 2024-09-26 / 2025-05-20 (attendance grids list only Huntzinger)
    "webster": "seiger-webster",
    "seiger": "seiger-webster",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())


def canon(token):
    """Map a commissioner name fragment to the roster full name; keep an
    unresolvable surname verbatim (Title case) rather than guessing."""
    if not token:
        return None
    t = re.sub(r"\s*-\s*", "-", token)             # rejoin line-wrapped "Seiger- Webster"
    t = re.sub(r"[^A-Za-z'\-]", " ", t).strip().lower()
    words = [w for w in re.split(r"\s+", t)
             if len(w) >= 2 and w not in ("commissioner", "commissioners", "chair", "vice")]
    if not words:
        return None
    for w in reversed(words):
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    for w in reversed(words):
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES + list(SURNAME_ALIASES), n=1, cutoff=0.85)
        if m:
            key = SURNAME_ALIASES.get(m[0], m[0])
            return SURNAME_TO_FULL[key]
    # honest verbatim fallback (never invent a roster identity)
    return "-".join(p.capitalize() for p in words[-1].split("-"))


# ---------------------------------------------------------------------------
# Motion-type taxonomy — the council extractor's fixed 12 categories, with the
# PC-specific land-use keys added (MSD OAM case numbers + SLCo file # keys).
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt|accept|continue", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|convene|amend the agenda|approve the "
                 r"agenda|reorder|work ?(?:meeting|session)|workshop|closed session|"
                 r"closed meeting|executive session|\btable\b|continue the|continue to|postpone|"
                 r"suspend the rules|go into (?:a )?closed|meeting schedule|"
                 r"(?:open|close|reopen)\s+the\s+(?:business\s+|public\s+)?meeting)\b", t):
        return "Procedural/Administrative"
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|"
                 r"\bplat\b|conditional use|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|street vacation|"
                 r"\badu\b|dadu|accessory dwelling|density|setback|"
                 r"\boam\s?\d|\bexp\s?\d|\bwvr\s?\d|file\s?#\s?\d|flood ?plain|housing element|waiver|"
                 r"special exception|nonconforming use|variance", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend\w*\s+the\s+(?:fiscal|fy|20)\S*\s*budget|"
                 r"tentative budget|final budget|adopt\w*.*budget|budget for|"
                 r"appropriat|certified tax rate|property tax", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|liaison|canvass|nominat|swear", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|license agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|proclaim|recogniz|honor|\bcommend|ceremonial|"
                 r"awareness (?:week|month)|designating|oath of office", t):
        return "Ceremonial"
    return "Other"


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------
# a commissioner name (allows the line-wrapped "Seiger- Webster" hyphen split)
CNAME = r"[A-Z][A-Za-z'’]+(?:\s?-\s?[A-Za-z]+)?"

# A) structured MSD block; every field individually optional (blank-safe: the
#    name atom starts [A-Z] so a following "2nd by:"/"Vote:" is never swallowed).
#    mtext/vote use TEMPERED dots so backtracking can never merge two adjacent
#    blocks (the untempered form once fused 2021-05-25's two blocks, attributing
#    the minutes-approval abstention to the OAM continuance).
_T = r"(?:(?!Motion\s*:|Motion\s+by\s*:|2\s*nd\s+by\s*:|Vote\s*:)."   # tempered atom
PC_STRUCT = re.compile(
    r"Motion\s*:\s*(?P<mtext>" + _T + r"){3,900}?)\s*"
    r"Motion\s+by\s*:\s*(?:Commissioners?\s+|Chair\s+)?(?P<mover>" + CNAME + r")?\s*"
    r"2\s*nd\s+by\s*:\s*(?:Commissioners?\s+|Chair\s+)?(?P<sec>" + CNAME + r")?\s*"
    r"Vote\s*:\s*(?P<vote>" + _T + r"){0,300})",
    re.S)

# post-trim of the greedily-captured vote text: cut at the first token that
# clearly belongs to the NEXT agenda item / section (kearns-PC T3.1(f) lesson —
# a bleeding item title can read as a false tally)
VOTE_TRIM = re.compile(
    r"\s+\d{1,2}\)\s|\s[a-e]\.\s|\s[A-Z]{3,}[A-Z ]{5,}|\sOAM\s?\d|\sSpeaker\s*#|"
    r"\s(?:Ms|Mr|Mrs|Dr)\.|\sCommissioner\s+" + CNAME +
    r"\s+(?:said|asked|confirmed|stated|read|motioned)")

# B) inline procedural: "Commissioner X motioned to <action>[, Commissioner Y
#    seconded [that motion]]."
PC_INLINE = re.compile(
    r"Commissioner\s+(?P<mover>" + CNAME + r")\s+motioned\s+"
    r"(?P<mtext>to\s+[^.;]{3,220}?)"
    r"(?:[,;]\s*(?:and\s+)?Commissioner\s+(?P<sec>" + CNAME + r")\s+seconded\b[^.]{0,80})?"
    r"\s*(?:[.]|$)", re.I)

VOTE_AFTER_INLINE = re.compile(r"^\s*Commissioners\s+voted\b[^.]{0,160}", re.I)

UNANIMOUS = re.compile(r"unanimous", re.I)
OF_PRESENT = re.compile(r"of\s+commissioners\s+present", re.I)
TALLY_RE = re.compile(r"\b([0-9])\s*(?:-|–|to)\s*([0-9])\b")
FAIL_RE = re.compile(r"\bfail\w*|\bdenied\b|did\s+not\s+(?:pass|carry)", re.I)
ABSTAIN_RE = re.compile(r"Commissioner\s+(" + CNAME + r")\s+abstain\w*", re.I)
OPPOSE_RE = re.compile(r"Commissioner\s+(" + CNAME + r")\s+"
                       r"(?:oppos\w+|dissent\w+|vot(?:ed|ing)\s+(?:nay|no|against|in\s+opposition))", re.I)
IN_FAVOR = re.compile(r"in\s+favor|voted\s+(?:unanimous|yes|aye)", re.I)


def clean_motion_text(s):
    s = re.sub(r"\s*-\s*(?=[a-z])", "-", re.sub(r"\s+", " ", s)).strip()
    s = s.strip(" .,;:")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def parse_vote_text(vt):
    """-> (has_outcome, passed, unanimous, of_present, abstain[], nay[], tally)"""
    vt = VOTE_TRIM.split(vt or "")[0].strip()
    abstain = [canon(m.group(1)) for m in ABSTAIN_RE.finditer(vt)]
    nay = [canon(m.group(1)) for m in OPPOSE_RE.finditer(vt)]
    unanimous = bool(UNANIMOUS.search(vt))
    of_present = bool(OF_PRESENT.search(vt))
    tally = None
    tm = TALLY_RE.search(vt)
    if tm:
        tally = (int(tm.group(1)), int(tm.group(2)))
    failed = bool(FAIL_RE.search(vt))
    has_outcome = bool(unanimous or tally or failed or abstain or nay or IN_FAVOR.search(vt))
    passed = not failed
    if tally and tally[0] < tally[1]:
        passed = False
    return has_outcome, passed, unanimous, of_present, \
        sorted(set(a for a in abstain if a)), sorted(set(n for n in nay if n)), tally


def build_result(has_outcome, passed, unanimous, of_present, abstain, nay, tally):
    if not has_outcome:
        return ""                        # source printed no outcome — honest NULL
    outcome = "Pass" if passed else "Fail"
    if tally:
        return f"{tally[0]}-{tally[1]} {outcome}"
    if abstain and not unanimous and not nay:
        # the 2021-05-25 form: "Commissioner X abstained, all other
        # commissioners voted in favor"
        return (f"{outcome} ({', '.join(a.split()[-1] for a in abstain)} abstained, "
                f"all others in favor)")
    if unanimous:
        q = ", of commissioners present" if of_present else ""
        return f"{outcome} (unanimous{q})"
    if nay:
        return f"{outcome} (nay: {', '.join(n.split()[-1] for n in nay)})"
    return outcome


# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"\x0c|White\s+City(?:\s+Metro\s+Township)?\s+Planning\s+Commission\s*[–\-]\s*"
    r"[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s*[–\-]\s*Meeting\s+Summary\s*(?:Page\s+\d+\s+of\s+\d+)?",
    re.I)


def split_frontmatter(raw):
    parts = re.split(r"\n\s*---\s*\n", raw, maxsplit=2)
    body = parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 else raw)
    head = parts[0] + (parts[1] if len(parts) > 1 else "")
    fmt = re.search(r"\*\*Format:\*\*\s*(\w+)", head)
    return body, (fmt.group(1) if fmt else "text")


def agenda_subject(pre):
    """Bare Motion: text fallback — the nearest preceding agenda item line."""
    items = re.findall(r"\d{1,2}\)\s*(.+?)(?:\(Motion|\(Discussion|\.\s|$)", pre, re.S)
    if items:
        return clean_motion_text(items[-1])
    return clean_motion_text(pre[-160:])


def extract_meeting(path, rel_source, date, year, title):
    raw = open(path, encoding="utf-8").read()
    body_text, fmt = split_frontmatter(raw)
    flat = FOOTER_RE.sub(" ", body_text)
    flat = re.sub(r"\s+", " ", flat)

    votes, used_spans = [], []
    for m in PC_STRUCT.finditer(flat):
        mover = canon(m.group("mover")) if m.group("mover") else ""
        seconder = canon(m.group("sec")) if m.group("sec") else ""
        mtext = clean_motion_text(m.group("mtext") or "")
        if len(re.sub(r"\W", "", mtext)) < 4:
            mtext = agenda_subject(flat[max(0, m.start() - 400):m.start()])
        vt = VOTE_TRIM.split(m.group("vote") or "")[0]
        has_outcome, passed, unanimous, of_present, abstain, nay, tally = \
            parse_vote_text(vt)
        votes.append(make_rec(m.start(), mtext, mover, seconder, has_outcome, passed,
                              unanimous, of_present, abstain, nay, tally))
        # span ends at the TRIMMED vote end — the greedy 300-char capture must
        # not suppress a following inline motion (2022-07-28 adjourn)
        used_spans.append((m.start(), m.start("vote") + len(vt)))

    for m in PC_INLINE.finditer(flat):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        mover = canon(m.group("mover")) or ""
        seconder = canon(m.group("sec")) if m.group("sec") else ""
        mtext = clean_motion_text(m.group("mtext"))
        # rare: an outcome sentence directly after the inline motion
        tailm = VOTE_AFTER_INLINE.match(flat[m.end(): m.end() + 170])
        vt = tailm.group(0) if tailm else ""
        has_outcome, passed, unanimous, of_present, abstain, nay, tally = parse_vote_text(vt)
        votes.append(make_rec(m.start(), mtext, mover, seconder, has_outcome, passed,
                              unanimous, of_present, abstain, nay, tally))

    votes.sort(key=lambda v: v["_pos"])
    for v in votes:
        v.pop("_pos")
    for n, v in enumerate(votes, 1):
        v2 = {"motion_no": n}
        v2.update(v)
        votes[n - 1] = v2

    return {"date": date, "year": int(year), "title": title,
            "file_body": "PlanningCommission", "format": fmt, "present": [],
            "source": rel_source, "votes": votes}


def make_rec(pos, mtext, mover, seconder, has_outcome, passed, unanimous,
             of_present, abstain, nay, tally):
    result = build_result(has_outcome, passed, unanimous, of_present, abstain, nay, tally)
    names_recorded = bool(abstain or nay)
    if names_recorded:
        vote_mode = "narrative-named-dissent"
    elif has_outcome:
        vote_mode = "narrative"
    else:
        vote_mode = "none"
    rec = {
        "_pos": pos,
        "motion": mtext,
        "body": "PlanningCommission",
        "motion_type": classify_motion(mtext),
        "result": result,
        "mover": mover or "", "seconder": seconder or "",
        "names_recorded": names_recorded,
        "vote_mode": vote_mode,
        "aye": [], "nay": nay, "abstain": abstain, "absent": [], "recuse": [],
        "mayor_voted": False,
    }
    if not names_recorded:
        rec["tally_only"] = {"unanimous": unanimous,
                             "present_count": None,
                             "tally": list(tally) if tally else None}
    return rec


# ---------------------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.replace("\\", "/").split("/")   # .../minutes/<year>/<date>/<file>.md
    sub = parts[-2]
    return os.path.join(VOTES_DIR, str(year), sub, parts[-1].replace(".md", ".json"))


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    for r in rows:
        rel = re.sub(r"^planning_commission/", "", r["path"])
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("MISSING", r["path"], file=sys.stderr)
            continue
        jp = json_path_for(rel, r["year"])
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
    print("done PlanningCommission")


def rebuild_csv(rows):
    # provenance (trailing 14th column, collection standard): every PC minutes
    # doc was recovered from PMN body 5879 -> pmn_minutes (index source=pmn).
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in rows:
        rel = re.sub(r"^planning_commission/", "", r["path"])
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
        rel = re.sub(r"^planning_commission/", "", r["path"])
        jp = json_path_for(rel, r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        date = obj["date"]
        people = set()
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k):
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
            w.writerow([nm, "Planning Commissioner", d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
