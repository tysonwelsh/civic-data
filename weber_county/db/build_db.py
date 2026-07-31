#!/usr/bin/env python3
"""Build weber_county.db — the STANDARD 8-table relational schema (SCHEMA_SPEC §5) for
Weber County, from the prose-extracted staging CSVs (db/staging/, produced by
extract_votes.py which parses legislative/minutes/**/*.md).

Weber County is a 3-member Board of Commissioners (NOT Legistar). Its minutes carry NAMED
roll-call votes even on unanimous motions ("Chair Froerer – aye; Commissioner Harvey – aye;
Commissioner Bolos – aye"), so unlike Salt Lake County (tally-primary, votes from Legistar),
Weber's `motion`/`vote` layer is NAMED-primary straight from the minutes. A motion with no
printed roll call gets names_recorded=0 — an honest recording ceiling, never fabricated.

Same 8 standard tables every per-city db has, so the repo-root build_cities_db.py federates
it unchanged (gov_level='county'). DERIVED + idempotent — rerun after extract_votes.py.
"""
import csv, os, re, sqlite3
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STG = os.path.join(HERE, "staging")
DB = os.path.join(HERE, "weber_county.db")
CITY = "weber_county"

# meeting_type -> body name (regular commission meetings vs posted work sessions)
BODY_FOR = {"regular": "Board of Commissioners",
            "work_session": "Board of Commissioners Work Session"}

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


def rd(name):
    p = os.path.join(STG, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


# Source-verbatim surname misspellings that denote the SAME commissioner. Person
# unification is the sanctioned normalization layer (SCHEMA_SPEC §8): the verbatim value
# stays untouched in staging/votes.csv (city-faithful), and is merged onto its canonical
# person only here at name-key resolution. "Freorer" is a clerk typo for Chair Gage
# Froerer that appears in the roll-call lines of three Jan-2023 meetings —
# legislative/minutes/2023/2023-01-10_commission.md, 2023-01-17_commission.md, and
# 2023-01-24_commission.md (all three docs also print the correct "Froerer" elsewhere).
# Keyed by the misspelled name_key -> the canonical name_key.
PERSON_ALIASES = {"freorer": "froerer"}


def name_key(s):
    k = re.sub(r"[^a-z]", "", (s or "").lower()).strip()
    return PERSON_ALIASES.get(k, k)


def main():
    meetings = rd("meetings.csv")
    motions = rd("motions.csv")
    votes = rd("votes.csv")
    fullnames = {r["lastname_key"]: r["full_name"] for r in rd("person_fullnames.csv")}

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # bodies — present meeting_types map to canonical body names
    present = sorted({BODY_FOR.get(m["meeting_type"], "Board of Commissioners")
                      for m in meetings})
    bid_map = {}
    for i, name in enumerate(present, start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, i, name, "council"))
        bid_map[name] = i

    def body_of(meeting_type):
        return bid_map[BODY_FOR.get(meeting_type, "Board of Commissioners")]

    # persons — built from Weber VOTERS only (resolve by last-name key, enrich full_name
    # from the commissioners header). Movers/seconders resolve against this same set, so a
    # visiting mover in a joint Weber+Davis boundary meeting (e.g. a Davis commissioner)
    # never becomes a Weber person — the verbatim name stays in motion_text.
    used = set()
    for v in votes:
        if v.get("person"):
            used.add(v["person"].strip())
    pid_map, pid = {}, 0
    for nm in sorted(used):
        k = name_key(nm)
        if not k or k in pid_map:
            continue
        pid += 1
        pid_map[k] = pid
        db.execute("INSERT INTO person VALUES (?,?,?,?)",
                   (CITY, pid, fullnames.get(k, nm), k))

    def person_id(nm):
        return pid_map.get(name_key(nm))

    # meetings — keyed by (meeting_date); one commission doc per date
    mid_map = {}
    for i, mt in enumerate(sorted(meetings, key=lambda x: x["meeting_date"]), start=1):
        bid = body_of(mt["meeting_type"])
        title = BODY_FOR.get(mt["meeting_type"], "Board of Commissioners")
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, i, bid, mt["meeting_date"], title, mt["source_file"]))
        mid_map[mt["meeting_date"]] = (i, bid, mt["meeting_type"])

    # votes indexed by (date, motion_no)
    from collections import defaultdict
    v_by_m = defaultdict(list)
    for v in votes:
        v_by_m[(v["meeting_date"], v["motion_no"])].append(v)

    motion_id = vote_id = 0
    dropped = []      # UNIQUE(motion_id,person_id) collisions — reported, never silent
    role_ct = Counter()
    role_span = {}
    for m in sorted(motions, key=lambda x: (x["meeting_date"], int(x["motion_no"]))):
        date = m["meeting_date"]
        if date not in mid_map:
            continue
        meeting_id, body_id, _mtype = mid_map[date]
        motion_id += 1
        vs = v_by_m.get((date, m["motion_no"]), [])
        names_recorded = int(m.get("names_recorded") or (1 if vs else 0))
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            CITY, motion_id, meeting_id, body_id, int(m["motion_no"]),
            (m.get("motion_text") or "").strip(),
            "",  # motion_type — Weber prints no native type label
            (m.get("result_raw") or "").strip(),
            m.get("outcome") or "", m.get("stage") or "", "",
            None, "", "",  # application linkage — land_use/dev pass fills this
            person_id(m.get("mover")), person_id(m.get("seconder")),
            names_recorded,
            (m.get("source_file") or "").strip(), m.get("provenance") or "county_portal"))
        for v in vs:
            p = person_id(v.get("person"))
            val = (v.get("vote_value") or "").strip()
            if not p or not val:
                continue
            vote_id += 1
            try:
                db.execute("INSERT INTO vote VALUES (?,?,?,?,?)",
                           (CITY, vote_id, motion_id, p, val))
            except sqlite3.IntegrityError:
                # 2026-07-26 (audit F13): this used to `continue` silently, so 9 vote rows
                # vanished between the flat CSV and the db with nothing to show for it —
                # the Park City UNIQUE-drop class. Every one traces to a SOURCE clerk typo
                # naming the same commissioner twice on one roll ("Commissioner Harvey –
                # aye; Commissioner Froerer – aye; Chair Froerer – aye"). The CSV keeps the
                # typo verbatim; the db records the collision loudly and counts it.
                vote_id -= 1
                dropped.append((motion_id, p, val))
                continue
            role_ct[(p, body_id)] += 1
            sp = role_span.get((p, body_id), [date, date])
            sp[0] = min(sp[0], date); sp[1] = max(sp[1], date)
            role_span[(p, body_id)] = sp

    rid = 0
    for (p, body_id), n in role_ct.items():
        rid += 1
        sp = role_span[(p, body_id)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)",
                   (CITY, rid, p, body_id, sp[0], sp[1], n))

    db.commit()

    # integrity gates
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    integ = db.execute("PRAGMA integrity_check").fetchone()[0]
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("weber_county.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role", "referral"):
        print("  %-12s %d" % (t, c(t)))
    named = c("motion") and db.execute(
        "SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions with named roll call: %d / %d (%.1f%%)"
          % (named, c("motion"), 100 * named / max(1, c("motion"))))
    if dropped:
        print("  ! %d DUPLICATE vote rows dropped by UNIQUE(motion_id,person_id) — each is a"
              % len(dropped))
        print("    SOURCE clerk typo naming one member twice on one roll call. The flat CSV")
        print("    keeps them verbatim; listed here so the loss is never silent:")
        for mid, pid, val in dropped:
            print("      motion_id=%s person_id=%s value=%s" % (mid, pid, val))
    print("  foreign_key_check:", "OK" if not fk else fk)
    print("  integrity_check:", integ)
    db.close()


if __name__ == "__main__":
    main()
