#!/usr/bin/env python3
"""Build wfrc_mpo.db — the STANDARD 8-table schema (SCHEMA_SPEC §5) for the Wasatch Front
Regional Council, the repo's first REGIONAL (MPO) entity (gov_level='regional', fed_index
201).

WFRC is a PROSE-MINUTES body (not Legistar). The recording ceiling (verified 2016-2026):
minutes name the MOVER and SECONDER of every action + a narrative tally result; dissent is
COUNT-ONLY and dissenters are NEVER named — there is NO roll call. So:
  * `motion` rows come from the parsed minutes (db/extract_motions.py -> all_motions.csv),
    carrying mover_person_id / seconder_person_id, verbatim result_raw, and outcome.
  * `vote` is EMPTY by construction (no named individual votes) and every motion has
    names_recorded=0 — an honest recording ceiling, like nephi / west_jordan PC.
  * `role` is derived from mover+seconder participation (the ONLY individual attribution the
    minutes provide); n_votes there counts named mover/seconder actions, NOT roll-call votes.
Committee actions (Regional Growth Committee, Trans Com, WFRC Budget Committee) fold into the
Council minutes; the motion.body_id walks section headers (SLC in-session pattern).

This db carries the SAME 8 standard tables every per-city db has, so the repo-root
build_cities_db.py federates it unchanged. DERIVED + idempotent — rerun after
fetch_minutes.py + extract_motions.py; never hand-edit.
"""
import csv, os, re, sqlite3
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEG = os.path.join(ROOT, "legislative")
MOTIONS = os.path.join(LEG, "all_motions.csv")
MINDEX = os.path.join(LEG, "minutes_index.csv")
DB = os.path.join(HERE, "wfrc_mpo.db")
CITY = "wfrc_mpo"

BODY_KIND = {"Council": "council", "Regional Growth Committee": "council",
             "Transportation Coordinating Committee": "council",
             "WFRC Budget Committee": "council"}

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


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def build_canon(names):
    """Canonicalize partial/surname mentions to the fullest name IN THE CORPUS, but ONLY
    when unambiguous (surnames collide — never guess). 'Ramsey' -> 'Dawn Ramsey';
    'Winder Newton' -> 'Aimee Winder Newton'; a bare surname shared by two people stays."""
    names = sorted({n for n in names if n})
    canon = {n: n for n in names}
    # Documented same-person aliases (db/person_aliases.csv) — spelling/OCR variants the
    # suffix rule below cannot reach ("Stevension" is not a suffix of "Stevenson", and
    # "Tami"/"Tamara" differ in the FIRST token). Every row carries its evidence, including
    # a non-co-occurrence check that rules out two people sharing a surname. Audit F5.
    _ap = os.path.join(os.path.dirname(os.path.abspath(__file__)), "person_aliases.csv")
    aliases = {}
    if os.path.exists(_ap):
        for _r in csv.DictReader(open(_ap, encoding="utf-8")):
            if _r.get("raw_name") and _r.get("canonical_name"):
                aliases[_r["raw_name"].strip()] = _r["canonical_name"].strip()
    for n in names:
        toks = n.split()
        sup = {m for m in names
               if m != n and len(m.split()) > len(toks) and m.split()[-len(toks):] == toks}
        if len(sup) == 1:
            canon[n] = next(iter(sup))
    for n, c in aliases.items():
        if n in canon:
            canon[n] = c
    # resolve chains to the terminal fullest name
    for n in list(canon):
        seen = set()
        while canon[n] != n and canon[n] not in seen:
            seen.add(canon[n])
            n2 = canon[n]
            if canon.get(n2, n2) == n2:
                canon[n] = n2
                break
            canon[n] = canon[n2]
    return canon


def main():
    motions = list(csv.DictReader(open(MOTIONS, encoding="utf-8")))
    meetings_idx = {m["date"]: m for m in csv.DictReader(open(MINDEX, encoding="utf-8"))}

    # canonical name authority from all mover/seconder mentions
    raw_names = []
    for m in motions:
        raw_names += [m["mover"], m["seconder"]]
    canon = build_canon(raw_names)

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # bodies
    bid = {}
    for i, name in enumerate(["Council", "Regional Growth Committee",
                              "Transportation Coordinating Committee",
                              "WFRC Budget Committee"], start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, i, name, BODY_KIND[name]))
        bid[name] = i

    # persons (canonicalized)
    pid = {}
    n = 0
    for nm in sorted({canon[x] for x in raw_names if x}):
        k = name_key(nm)
        if not k or k in pid:
            continue
        n += 1
        pid[k] = n
        db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, n, nm, k))

    def person_id(nm):
        c = canon.get(nm, nm)
        return pid.get(name_key(c))

    # meetings — one per meeting date (physical Council meeting), body Council
    mid = {}
    for i, date in enumerate(sorted(meetings_idx), start=1):
        mt = meetings_idx[date]
        src = mt["md_path"] or mt["source_url"]
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, i, bid["Council"], date,
                    "WFRC Council meeting %s" % date, src))
        mid[date] = i

    # motions
    role_ct = Counter()
    role_span = {}
    motion_id = 0
    for m in motions:
        motion_id += 1
        body_id = bid.get(m["body"], bid["Council"])
        prov = "minutes" if m["doc_status"] in ("final", "approved") else "minutes_draft"
        mv = person_id(m["mover"])
        sc = person_id(m["seconder"])
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            CITY, motion_id, mid[m["date"]], body_id, int(m["motion_no"]),
            m["motion_text"], m["motion_type"], m["result_raw"], m["outcome"],
            "", "", None, "", "",
            mv, sc, 0,                       # names_recorded=0: no named roll call (ceiling)
            m["source_md"], prov))
        # role participation from mover+seconder (only individual attribution WFRC records)
        for p in (mv, sc):
            if p:
                role_ct[(p, body_id)] += 1
                sp = role_span.get((p, body_id), [m["date"], m["date"]])
                sp[0] = min(sp[0], m["date"]); sp[1] = max(sp[1], m["date"])
                role_span[(p, body_id)] = sp

    # vote table intentionally EMPTY — dissent is count-only, dissenters never named.

    rid = 0
    for (p, body_id), cnt in sorted(role_ct.items()):
        rid += 1
        sp = role_span[(p, body_id)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)",
                   (CITY, rid, p, body_id, sp[0], sp[1], cnt))

    db.commit()
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    integ = db.execute("PRAGMA integrity_check").fetchone()[0]
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("wfrc_mpo.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role", "referral"):
        print("  %-12s %d" % (t, c(t)))
    print("  named-roll-call motions: %d  (vote rows: %d — recording ceiling: no roll call)"
          % (c("motion WHERE names_recorded=1"), c("vote")))
    print("  outcomes:", dict(db.execute(
        "SELECT outcome, COUNT(*) FROM motion GROUP BY outcome").fetchall()))
    print("  motions by body:", dict(db.execute(
        "SELECT b.name, COUNT(*) FROM motion m JOIN body b ON b.body_id=m.body_id "
        "GROUP BY b.name").fetchall()))
    print("  integrity_check:", integ, "| foreign_key_check rows:", len(fk))
    db.close()


if __name__ == "__main__":
    main()
