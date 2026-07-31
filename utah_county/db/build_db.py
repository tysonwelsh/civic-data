#!/usr/bin/env python3
"""Build utah_county.db — the standard relational schema (SCHEMA_SPEC §5) for Utah County,
from the PROSE-EXTRACTED staging (db/staging/, produced by extract_votes.py).

Utah County has NO Legistar/Granicus vote API (recon.md); its Board of Commissioners is a
prose-extraction body (like the non-Legistar cities). This build therefore reads the minutes
prose extraction — NOT a structured harvest — and emits the SAME 8 standard tables every
per-city / SLCo db has, so the repo-root build_cities_db.py federates it unchanged
(gov_level='county', fed_index 102).

Recording ceiling (era-split, recon.md): 2015-2016 (+ born-digital 2017-18) name each
member's vote (AYE:/NAY: block) -> names_recorded=1; 2017+ scanned & consent items are
tally-only (mover/seconder named, no per-member roll) -> names_recorded=0. Tally-only motions
carry NO vote rows (honest ceiling — never fabricated).

Person resolution unifies a bare surname mover/seconder ("Lee") with the full name that
appears in that era's named votes ("William C. Lee") when the surname is unambiguous across
the corpus; single-token names with no full-name match (later-era surnames, HAUC first names)
stay as their own person — honest.

DERIVED + idempotent — rerun after extract_votes.py. A closing pass (ingest_pc_votes) appends
the county Planning Commission with higher motion_ids; this build never renumbers.
"""
import csv, os, re, sqlite3
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STG = os.path.join(HERE, "staging")
DB = os.path.join(HERE, "utah_county.db")
CITY = "utah_county"

BODY_KIND = {"Board of Commissioners": "council",
             "Commission Work Session": "council",
             "Housing Authority of Utah County": "agency"}

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


def rd(n):
    p = os.path.join(STG, n)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def main():
    meetings = rd("meetings.csv")
    motions = rd("motions.csv")
    votes = rd("votes.csv")

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # ---- bodies ----
    bid_map = {}
    for i, name in enumerate(sorted({m["body"] for m in meetings}), start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, i, name, BODY_KIND.get(name, "council")))
        bid_map[name] = i

    # ---- person resolution: unify bare surname with a unique full name from named votes ----
    voter_names = {v["person"] for v in votes}                 # always full "First [M.] Last"
    fullnames = {n for n in voter_names if " " in n}
    last_to_full = defaultdict(set)
    for fn in fullnames:
        last_to_full[fn.split()[-1].lower()].add(fn)

    # Documented same-person aliases (db/person_aliases.csv). The surname unifier below
    # only reaches BARE surnames, so multi-token variants ("Bill Lee" vs "William C. Lee",
    # OCR garbles like "Ajinge") fragmented one commissioner across several person rows —
    # 2026-07-25 audit D4. Each row in that file carries its own evidence, including the
    # non-co-occurrence test that proves the variants are never two people at once.
    ALIASES = {}
    _apath = os.path.join(HERE, "person_aliases.csv")
    if os.path.exists(_apath):
        for _r in csv.DictReader(open(_apath, encoding="utf-8")):
            if _r.get("raw_name") and _r.get("canonical_name"):
                ALIASES[_r["raw_name"].strip()] = _r["canonical_name"].strip()

    def canonical(name):
        name = (name or "").strip()
        if not name:
            return None
        if name in ALIASES:
            return ALIASES[name]
        if " " in name:
            return name
        cands = last_to_full.get(name.lower())               # surname -> unique full name?
        if cands and len(cands) == 1:
            return next(iter(cands))
        # pypdf sometimes splits a surname ("Ellertson" -> "Ellert son"); unify a >=4-char
        # token that is the unique prefix of exactly one known full-name surname
        if len(name) >= 4:
            pref = [full for last, fulls in last_to_full.items()
                    if last.startswith(name.lower()) and len(fulls) == 1 for full in fulls]
            if len(set(pref)) == 1:
                return pref[0]
        return name                                          # own person (later-era surname / first name)

    pid_map = {}     # name_key -> person_id
    def person_id(name):
        c = canonical(name)
        if not c:
            return None
        k = name_key(c)
        if not k:
            return None
        if k not in pid_map:
            pid_map[k] = len(pid_map) + 1
            db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, pid_map[k], c, k))
        return pid_map[k]

    # pre-create everyone (voters first so full names win canonical slots)
    for v in votes:
        person_id(v["person"])
    for m in motions:
        person_id(m.get("mover")); person_id(m.get("seconder"))

    # ---- meetings ----
    mid_map = {}
    for m in sorted(meetings, key=lambda r: (r["date"], r["body"])):
        mid = int(m["meeting_id"])
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, mid, bid_map[m["body"]], m["date"],
                    "%s — %s" % (m["body"], m["date"]) + (" (special)" if m.get("kind") == "special" else ""),
                    m["md_path"]))
        mid_map[mid] = (bid_map[m["body"]], m["date"])

    # ---- motions ----
    for m in motions:
        mot_id = int(m["motion_id"]); meet_id = int(m["meeting_id"])
        body_id, date = mid_map[meet_id]
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            CITY, mot_id, meet_id, body_id, int(m["motion_no"]),
            m["motion_text"], "", m["result_raw"], m["outcome"],
            "", "", None, "", "",
            person_id(m.get("mover")), person_id(m.get("seconder")),
            int(m["names_recorded"]), m["source_file"], m["provenance"]))

    # ---- votes + roles ----
    role_ct = Counter(); role_span = {}
    mot_body = {int(m["motion_id"]): mid_map[int(m["meeting_id"])] for m in motions}
    vote_id = 0
    for v in votes:
        mot_id = int(v["motion_id"])
        pid = person_id(v["person"])
        if pid is None or mot_id not in mot_body:
            continue
        body_id, date = mot_body[mot_id]
        vote_id += 1
        try:
            db.execute("INSERT INTO vote VALUES (?,?,?,?,?)", (CITY, vote_id, mot_id, pid, v["vote_value"]))
        except sqlite3.IntegrityError:
            vote_id -= 1; continue
        role_ct[(pid, body_id)] += 1
        sp = role_span.get((pid, body_id), [date, date])
        sp[0] = min(sp[0], date); sp[1] = max(sp[1], date); role_span[(pid, body_id)] = sp

    for rid, ((pid, body_id), n) in enumerate(role_ct.items(), start=1):
        sp = role_span[(pid, body_id)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)", (CITY, rid, pid, body_id, sp[0], sp[1], n))

    db.commit()
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("utah_county.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role", "referral"):
        print("  %-12s %d" % (t, c(t)))
    named = c("motion") and db.execute("SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions with named roll call: %d / %d (rest tally-only — recording ceiling)"
          % (named, c("motion")))
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    integ = db.execute("PRAGMA integrity_check").fetchone()[0]
    print("  foreign_key_check: %d issues | integrity_check: %s" % (len(fk), integ))
    db.close()


if __name__ == "__main__":
    main()
