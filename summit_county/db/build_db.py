#!/usr/bin/env python3
"""Build summit_county.db — the standard relational schema (SCHEMA_SPEC §5) for Summit
County, from the prose extraction staging in db/staging/ (produced by
legislative/extract_votes.py).

Summit is a NON-Legistar, TALLY-PRIMARY county: the County Council's born-digital Granicus
minutes name the mover + seconder on every motion and print a tally ("all voted in favor,
(5-0)"), but name individual members ONLY when a division is called. So `motion` rows carry
the verbatim result + parsed outcome and `names_recorded=0` marks the (large) tally-only
majority; `vote` rows exist only for the divided motions. This ceiling is final — Summit has
no Legistar API to recover named rolls (contrast salt_lake_county, where the API is richer
than the minutes).

Same 8 standard tables as every per-city / county db, so the repo-root build_cities_db.py
federates it unchanged (gov_level='county', fed_index 105).

APPENDABLE: Council motions are numbered first from db/staging/ (sorted deterministically by
date, clip, motion_no), so their motion_ids are STABLE. A closing pass that drops Planning
Commission motions into db/staging_pc/ and reruns this script appends them with HIGHER ids —
Council ids never renumber. DERIVED + idempotent — rerun after re-extraction; never hand-edit.
"""
import csv, os, re, sqlite3
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STG = os.path.join(HERE, "staging")
STG_PC = os.path.join(HERE, "staging_pc")   # closing-pass Planning Commission staging (optional)
DB = os.path.join(HERE, "summit_county.db")
CITY = "summit_county"

# Council roster — canonicalize name variants to one identity (matches extract_votes.py).
ROSTER = {'armstrong': 'Roger Armstrong', 'robinson': 'Christopher Robinson',
          'harte': 'Canice Harte', 'hanson': 'Tonja B Hanson', 'stevens': 'Malena Stevens',
          'mckenna': 'Megan McKenna', 'poll': 'Stephanie Poll'}

BODY_KIND = {"County Council": "council", "Planning Commission": "planning",
             "Snyderville Basin Planning Commission": "planning",
             "Eastern Summit County Planning Commission": "planning"}

DDL = """
CREATE TABLE body (city TEXT, body_id INTEGER PRIMARY KEY, name TEXT, kind TEXT, UNIQUE(name));
CREATE TABLE person (city TEXT, person_id INTEGER PRIMARY KEY, full_name TEXT, name_key TEXT, UNIQUE(name_key));
CREATE TABLE meeting (city TEXT, meeting_id INTEGER PRIMARY KEY, body_id INTEGER, meeting_date TEXT,
    title TEXT, source_file TEXT, UNIQUE(body_id, source_file));
CREATE TABLE application (city TEXT, application_id INTEGER PRIMARY KEY, app_key TEXT, body_id INTEGER,
    name TEXT, rep_title TEXT, UNIQUE(app_key));
CREATE TABLE motion (city TEXT, motion_id INTEGER PRIMARY KEY, meeting_id INTEGER, body_id INTEGER,
    motion_no INTEGER, motion_text TEXT, motion_type TEXT, result_raw TEXT, outcome TEXT, stage TEXT,
    recommendation TEXT, application_id INTEGER, app_match_method TEXT, app_confidence TEXT,
    mover_person_id INTEGER, seconder_person_id INTEGER, names_recorded INTEGER, source_file TEXT,
    provenance TEXT);
CREATE TABLE vote (city TEXT, vote_id INTEGER PRIMARY KEY, motion_id INTEGER, person_id INTEGER,
    vote_value TEXT, UNIQUE(motion_id, person_id));
CREATE TABLE role (city TEXT, role_id INTEGER PRIMARY KEY, person_id INTEGER, body_id INTEGER,
    first_seen TEXT, last_seen TEXT, n_votes INTEGER, UNIQUE(person_id, body_id));
CREATE TABLE referral (city TEXT, referral_id INTEGER PRIMARY KEY, primary_application_id INTEGER,
    primary_body TEXT, related_application_id INTEGER, related_body TEXT, match_method TEXT,
    confidence TEXT, shared_address TEXT, subject_score REAL, primary_date TEXT, related_date TEXT,
    gap_days INTEGER, note TEXT);
"""


def rd(base, n):
    p = os.path.join(base, n)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def canon(name, planning=False):
    if not name:
        return None
    # Planning-Commission names are a DIFFERENT roster, recorded surname-only in the PC
    # minutes. Do NOT canonicalize them through the Council ROSTER — a PC "Harte"/"Stevens"/
    # "Hanson" is not asserted to be the like-surnamed Council member (cardinal rule: never
    # fabricate cross-body identity). PC names are kept verbatim (whitespace-normalized).
    if planning:
        return name.strip()
    last = re.sub(r"[^A-Za-z]", "", name.split()[-1]).lower() if name.split() else ""
    return ROSTER.get(last, name.strip())


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def main():
    # staging read order: Council first (stable ids), then the optional PC closing pass.
    meets, motions, votes = [], [], []
    for base in (STG, STG_PC):
        for m in rd(base, "meetings.csv"):
            m["_base"] = base
            meets.append(m)
        for m in rd(base, "motions.csv"):
            m["_base"] = base
            motions.append(m)
        for v in rd(base, "votes.csv"):
            v["_base"] = base
            votes.append(v)

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # bodies
    bid_map = {}
    for i, name in enumerate(sorted({m["body"] for m in meets}), start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, i, name, BODY_KIND.get(name, "council")))
        bid_map[name] = i

    # planning flag per staging-meeting (keyed by base+clip) so PC names skip the Council ROSTER
    meet_planning = {(m["_base"], m["clip_id"]): BODY_KIND.get(m["body"]) == "planning"
                     for m in meets}

    # persons — movers, seconders, named voters (canonicalized; PC roster kept separate)
    used = set()
    for m in motions:
        planning = BODY_KIND.get(m["body"]) == "planning"
        for k in ("mover", "seconder"):
            c = canon(m.get(k), planning)
            if c:
                used.add(c)
    for v in votes:
        planning = meet_planning.get((v["_base"], v["clip_id"]), False)
        c = canon(v.get("member"), planning)
        if c:
            used.add(c)
    pid_map = {}
    for pid, nm in enumerate(sorted(used), start=1):
        pid_map[name_key(nm)] = pid
        db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, pid, nm, name_key(nm)))

    def person_id(nm, planning=False):
        return pid_map.get(name_key(canon(nm, planning) or ""))

    # meetings — one per clip; ordered by (date, clip) so meeting_id is stable
    mid_map = {}
    for i, m in enumerate(sorted(meets, key=lambda x: (x["date"], int(x["clip_id"]))), start=1):
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, i, bid_map[m["body"]], m["date"],
                    "Summit County %s — %s" % (m["body"], m["meeting_type"]), m["source_file"]))
        mid_map[m["clip_id"]] = i

    # motions — Council staging first (stable ids), then PC. Sort within each base by
    # (date, clip, motion_no) for determinism.
    def msort(x):
        return (x["_base"] != STG, x["date"], int(x["clip_id"]), int(x["motion_no"]))
    votes_by = defaultdict(list)
    for v in votes:
        votes_by[(v["_base"], v["clip_id"], v["motion_no"])].append(v)

    motion_id = vote_id = 0
    role_ct = Counter()
    role_span = {}
    for m in sorted(motions, key=msort):
        motion_id += 1
        body_id = bid_map[m["body"]]
        meeting_id = mid_map[m["clip_id"]]
        planning = BODY_KIND.get(m["body"]) == "planning"
        nr = int(m.get("names_recorded") or 0)
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            CITY, motion_id, meeting_id, body_id, int(m["motion_no"]),
            m["motion_text"], m["motion_type"], m["result_raw"], m["outcome"],
            "", "", None, "", "",
            person_id(m.get("mover"), planning), person_id(m.get("seconder"), planning), nr,
            m["source_file"], "minutes"))
        for v in votes_by.get((m["_base"], m["clip_id"], m["motion_no"]), []):
            p = person_id(v["member"], planning)
            val = v["vote_value"]
            if not p or not val:
                continue
            try:
                db.execute("INSERT INTO vote VALUES (?,?,?,?,?)", (CITY, vote_id + 1, motion_id, p, val))
            except sqlite3.IntegrityError:
                continue
            vote_id += 1
            role_ct[(p, body_id)] += 1
            sp = role_span.get((p, body_id), [m["date"], m["date"]])
            sp[0] = min(sp[0], m["date"]); sp[1] = max(sp[1], m["date"])
            role_span[(p, body_id)] = sp

    rid = 0
    for (p, body_id), n in role_ct.items():
        rid += 1
        sp = role_span[(p, body_id)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)", (CITY, rid, p, body_id, sp[0], sp[1], n))

    db.commit()
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    integ = db.execute("PRAGMA integrity_check").fetchone()[0]
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("summit_county.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role"):
        print("  %-12s %d" % (t, c(t)))
    named = c("motion") and db.execute("SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions with named roll call: %d / %d (rest tally-only — recording ceiling)" % (named, c("motion")))
    print("  foreign_key_check: %s | integrity_check: %s" % ("OK" if not fk else fk, integ))
    db.close()


if __name__ == "__main__":
    main()
