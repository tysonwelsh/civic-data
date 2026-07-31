#!/usr/bin/env python3
"""
extract_votes.py — Emigration Canyon Planning Commission vote extraction (PURE det.).

The PC (Utah PMN body 1562; "Township Planning Commission" pre-2024, "Planning Commission"
after) publishes born-digital **MEETING MINUTE SUMMARY** PDFs with a STRUCTURED motion
grammar (distinct from the Council's narrative tally):

    Motion: To approve application #CUP2025-001542 ... with staff recommendations ...
    Motion by: Commissioner Karkut
    Second by: Commissioner Geroux           (sometimes absent)
    Vote: Commissioners voted unanimously in favor

  Named dissent:
    Vote: Commissioner Wallace voted nay, all other commissioners voted in favor. Motion passed.

  Inline procedural (open/close hearing, adjourn — usually no printed Vote line):
    Commissioner Karkut motioned to open the public hearing, Commissioner Geroux seconded
    that motion.

CARDINAL RULE — never fabricate.
  * "Commissioners voted unanimously in favor" names no individual -> ONE tally-only row
    (blank member), `names_recorded:false`.  Never fabricate individual Ayes.
  * "Commissioner X voted nay ..." -> the named Nay row; the (unnamed) majority stays blank.
  * The PC is a recommending body; a motion that "recommends" a file to the Council is
    tagged Land-Use/Recommendation.  `result` is built from the printed Vote sentence.
  * Born-digital text (no OCR) -> "Commissioner <Surname>" tokens are trusted verbatim;
    a surname not in the observed roster is kept as-is (it is literally in the record),
    never dropped or guessed into a different person.

NO LLM, NO network.  Resumable (skips meetings whose JSON exists unless --force).

PROVENANCE (trailing 14th all_votes.csv column, the collection standard; flows to the db):
  minutes      — the audited primary PMN harvest (58 born-digital docs + this default)
  pmn_minutes  — docs recovered by the pmn_backfill sweep and PROMOTED into this dataset
                 (2026-07-16: PC 2025-11-13, PMN file 1363983, late-posted image-only scan
                 -> tesseract OCR; keyed by pmn_file_id below)
"""
import os, re, csv, json, sys, glob

# minutes_index.csv pmn_file_id values whose docs were recovered via pmn_backfill
# (promoted into this dataset) rather than the original audited harvest.
PMN_RECOVERED_FILE_IDS = {"1363983"}   # PC 2025-11-13

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# OBSERVED commissioner roster (surname -> full name).  Turnover across the record;
# the body is small (~5-7).  Staff (Gurr, Tucker, Gillmor, McLean, Starley) are NOT
# commissioners and never appear as "Commissioner <Name>".
SURNAME_TO_FULL = {
    "wallace": "Andrew Wallace", "karkut": "Jim Karkut", "berreth": "Dale Berreth",
    "nakamura": "Jim Nakamura", "long": "Adam Long", "geroux": "Jodi Geroux",
    "pacanowsky": "Alex Pacanowsky", "woodward": "Curtis Woodward",
    "davies": "Kate Davies", "mcnulty": "Jim McNulty", "tippets": "Brent Tippets",
    "pinon": "Robert Pinon", "harpst": "Tim Harpst", "clark": "Claire Clark",
    "steed": "Jacob Steed", "julian": "Morgan Julian", "mauldin": "Kayla Mauldin",
}
FULLNAMES = set(SURNAME_TO_FULL.values())


def canon(token):
    """Resolve a 'Commissioner <token>' surname to a full name.  Born-digital text is
    trusted: an unmapped surname is Title-cased and kept (it is in the record)."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", "", token).strip()
    if len(t) < 2:
        return None
    low = t.lower()
    if low in SURNAME_TO_FULL:
        return SURNAME_TO_FULL[low]
    if low in ("vote", "voted", "voting", "and", "said", "asked", "training",
               "meeting", "chair", "vice", "commissioner", "commissioners",
               "commission", "member", "members", "the"):
        return None
    return t.title()  # unmapped but explicitly a "Commissioner <X>" surname


def classify_motion(text):
    t = text.lower()
    if re.search(r"recommend", t):
        return "Land-Use/Recommendation"
    if re.search(r"(?:open|close|continue)\w*\s+the\s+public\s+hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|amend the agenda|approve the agenda|"
                 r"\btable\b|continue|postpone|elect\w* .*chair|chair for)\b", t):
        return "Procedural/Administrative"
    if re.search(r"conditional use|\bcup\b|dwelling|subdivision|\bplat\b|lot line|"
                 r"setback|rezon|zone|hillside|sensitive lands|site plan|grading|"
                 r"variance|land use|\boam\b|ordinance|general plan|watershed|slope|"
                 r"accessory|freeze creek|building permit", t):
        return "Land-Use/Zoning"
    if re.search(r"appoint|reappoint|nominat|liaison|vice[\s-]?chair", t):
        return "Appointment"
    return "Other"


def split_body(raw):
    parts = re.split(r"\n---\n", raw)
    return parts[-1]


ROLE = r"(?:Commissioners?|Chair|Vice[\s-]?Chair)"
NAME = r"([A-Z][A-Za-z'\-]{2,})"

# structured block: Motion: ... Motion by: Commissioner X [2nd by: Commissioner Y] Vote: ...
# The clerk writes the seconder label three ways: "Second by:", "Seconded by:", and — in
# ~125 blocks across 51 docs (the dominant PC form) — "2nd by:".  All three are matched
# here; a "2nd by: Commissioner" line with NO surname stays honestly blank (NAME fails →
# canon() rejects the stopword that follows, e.g. "Vote").
SECOND_LABEL = r"(?:Second(?:ed)?|2\s?nd)\s+by:"
MOTION_BLOCK = re.compile(
    r"Motion:\s*(.*?)\s*"
    r"Motion\s+by:\s*" + ROLE + r"?\s*" + NAME +
    r"(?:.*?" + SECOND_LABEL + r"\s*" + ROLE + r"?\s*" + NAME + r")?"
    r"(?:.*?Vote:\s*(.*?)(?:\.\s|\n|$))?",
    re.I | re.S)

# inline procedural: "Commissioner X motioned to ..., Commissioner Y seconded that motion."
INLINE = re.compile(
    ROLE + r"\s+" + NAME + r"\s+motioned\s+(to\s+.*?)(?:,|\.)\s*(?:" + ROLE + r"\s+" +
    NAME + r"\s+seconded)?", re.I)

VOTE_UNAN = re.compile(r"voted\s+unanimously|unanimous(?:ly)?\s+in\s+favor|"
                       r"all\s+commissioners\s+voted", re.I)
VOTE_NAY = re.compile(ROLE + r"?\s*" + NAME +
                      r"\s+voted\s+(nay|no|against|in\s+opposition)", re.I)
VOTE_ABSTAIN = re.compile(ROLE + r"?\s*" + NAME + r"\s+abstain", re.I)
FAILED = re.compile(r"motion\s+(?:failed|did\s+not\s+(?:pass|carry))|failed\s+for\s+lack",
                    re.I)


def clean(s):
    s = re.sub(r"\s+", " ", s).strip(" .,;:—-")
    if len(s) > 400:
        s = s[:400].rsplit(" ", 1)[0] + "…"
    return s


def parse_present(body):
    present = []
    m = re.search(r"\bCommissioners\b(.*?)(?:Public|Planning\s+Staff|Staff|Absent|"
                  r"BUSINESS|AGENDA|Motion:)", body, re.S | re.I)
    region = m.group(1) if m else body[:600]
    for sn, full in SURNAME_TO_FULL.items():
        if re.search(r"\b" + sn + r"\b", region, re.I) and full not in present:
            present.append(full)
    return present


def parse_vote(votetext, block):
    """Return (names_recorded, nay[list], abstain[list], unanimous, passed)."""
    vt = votetext or ""
    passed = not bool(FAILED.search(block))
    unanimous = bool(VOTE_UNAN.search(vt)) or bool(VOTE_UNAN.search(block[:400]))
    nay, abstain = [], []
    for m in VOTE_NAY.finditer(vt or block):
        nm = canon(m.group(1))
        if nm:
            nay.append(nm)
    for m in VOTE_ABSTAIN.finditer(vt or block):
        nm = canon(m.group(1))
        if nm and nm not in nay:
            abstain.append(nm)
    if nay:
        unanimous = False
        passed = True  # "all other commissioners voted in favor. Motion passed."
        if FAILED.search(block):
            passed = False
    return (bool(nay or abstain), sorted(set(nay)), sorted(set(abstain)),
            unanimous, passed)


def build_result(names_recorded, nay, abstain, unanimous, passed):
    outcome = "Pass" if passed else "Fail"
    if names_recorded:
        parts = []
        if nay:
            parts.append(f"{len(nay)} nay")
        if abstain:
            parts.append(f"{len(abstain)} abstain")
        return f"{outcome} ({', '.join(parts)})"
    if unanimous:
        return f"{outcome} (unanimous)"
    return outcome


def extract_meeting(path, rel_source, date, year, title, mtype):
    body = split_body(open(path, encoding="utf-8").read())
    flat = re.sub(r"[ \t]+", " ", body)
    present = parse_present(flat)
    votes = []
    used_spans = []

    # 1) structured Motion: blocks
    for m in re.finditer(r"Motion:\s*(.*?)(?=\n\s*Motion:|\Z)", flat, re.S):
        seg = m.group(0)
        bm = MOTION_BLOCK.match(seg)
        if not bm:
            continue
        motion_text = clean(bm.group(1))
        mover = canon(bm.group(2))
        seconder = canon(bm.group(3)) if bm.group(3) else None
        votetext = bm.group(4)
        if not motion_text:
            continue
        nr, nay, abstain, unan, passed = parse_vote(votetext, seg[:600])
        votes.append({
            "motion": motion_text, "body": "PlanningCommission",
            "motion_type": classify_motion(motion_text),
            "result": build_result(nr, nay, abstain, unan, passed),
            "mover": mover or "", "seconder": seconder or "",
            "names_recorded": nr, "nay": nay, "abstain": abstain,
            "unanimous": unan, "_pos": m.start(),
        })
        used_spans.append((m.start(), m.end()))

    # 2) inline procedural motions (open/close hearing, adjourn) OUTSIDE structured blocks
    for m in INLINE.finditer(flat):
        pos = m.start()
        if any(s <= pos < e for s, e in used_spans):
            continue
        action = clean(m.group(2))
        if not action:
            continue
        mover = canon(m.group(1))
        seconder = canon(m.group(3)) if m.group(3) else None
        # procedural inline motions carry no printed tally -> tally-only, passed
        votes.append({
            "motion": clean(action), "body": "PlanningCommission",
            "motion_type": classify_motion(action),
            "result": "Pass", "mover": mover or "", "seconder": seconder or "",
            "names_recorded": False, "nay": [], "abstain": [],
            "unanimous": False, "_pos": pos,
        })

    votes.sort(key=lambda v: v["_pos"])
    for v in votes:
        del v["_pos"]
    for n, v in enumerate(votes, 1):
        v2 = {"motion_no": n}; v2.update(v); votes[n - 1] = v2

    return {"date": date, "year": int(year), "title": title, "meeting_type": mtype,
            "file_body": "PlanningCommission", "present": present,
            "source": rel_source, "votes": votes}


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
                                      r.get("meeting_type", "Regular"))
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
            for nm in v.get("nay", []):
                row = dict(base); row["member"] = nm; row["vote"] = "Nay"
                out.append(row); emitted = True
            for nm in v.get("abstain", []):
                row = dict(base); row["member"] = nm; row["vote"] = "Abstain"
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
        people = set(obj.get("present", []))
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k):
                    people.add(v[k])
            people.update(v.get("nay", [])); people.update(v.get("abstain", []))
        for p in people:
            if not p:
                continue
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date); d["last"] = max(d["last"], date)
            d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            known = "Commissioner" if nm in FULLNAMES else "Commissioner (observed)"
            w.writerow([nm, known, d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
