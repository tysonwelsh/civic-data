#!/usr/bin/env python3
"""Build ut_state.db — the STANDARD 8-table civic-data schema (SCHEMA_SPEC §5) for the
State of Utah LEGISLATION module, from the public-website harvest in
../legislation/{bills,rollcalls,votes}.csv.

Model mapping (state legislation -> standard schema):
  body        = House, Senate, and named standing committees (kind: chamber | committee).
  person      = legislators, verbatim "Last, F." — DISJOINT population, city='ut_state',
                NEVER merged with municipal persons (a state legislator is not a councilmember).
  meeting     = a roll-call EVENT: (body, date). Multiple roll calls the same body+date
                share one meeting. source_file = the bill static page / vote-source URL.
  application = one row per BILL (the application-analog). app_key = 'bill:<session>:<bill>'.
  motion      = one row per roll call (floor svotes OR committee mtgvotes OR voice-vote row):
                motion_text = action/reading, result_raw = verbatim "Y-N-A" tally (or
                "Voice vote"), outcome = Pass/Fail (blank for voice — honest unknown).
                application_id links the roll call to its bill. names_recorded = 1 for a
                recorded roll call, 0 for a voice vote (honest recording ceiling).
  vote        = one row per legislator per RECORDED roll call (Yea/Nay/Absent). Party and
                district are NOT on the public vote pages -> not stored here (honest gap).
  role        = per person per body: vote span + count.
  referral    = present but EMPTY (the repo federator hard-fails without the table).

STANDARD schema => the repo-root federator ingests it unchanged (gov_level='state').
DERIVED + idempotent — rerun after a harvest; never hand-edit.
"""
import csv, os, re, sqlite3
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LEG = os.path.join(os.path.dirname(HERE), "legislation")
DB = os.path.join(HERE, "ut_state.db")
CITY = "ut_state"

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
    p = os.path.join(LEG, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def name_key(s):
    # key on the FULL verbatim "Last, F." — DISJOINT + do not surname-merge (memory:
    # surnames collide across eras). Over-split is safer than wrong-merge.
    return re.sub(r"\s+", " ", re.sub(r"[^a-z, .]", "", (s or "").lower())).strip()


def iso(d):
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", (d or "").strip())
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(1)), int(m.group(2)))
    return (d or "").strip()


def main():
    bills = rd("bills.csv")
    # main harvest + the shell-session (2025GS/2026GS) floor-vote recovery supplement
    # (harvest_shell_recovery.py; those static pages are broken shells — see recon.md).
    # String rollcall_ids ('REC_...') don't collide with the main integer ids.
    rcs = rd("rollcalls.csv") + rd("rollcalls_recovered.csv")
    votes = rd("votes.csv") + rd("votes_recovered.csv")
    bill_meta = {(b["session"], b["bill_no"]): b for b in bills}

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)

    # ---- bodies ----
    body_id = {}
    def get_body(name, kind):
        if name not in body_id:
            body_id[name] = len(body_id) + 1
            db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, body_id[name], name, kind))
        return body_id[name]
    # ensure chambers exist first (stable low ids)
    get_body("House", "chamber")
    get_body("Senate", "chamber")
    for rc in rcs:
        bn = rc["body_name"] or (rc["chamber"] or "Unknown")
        kind = "chamber" if bn in ("House", "Senate") else "committee"
        get_body(bn, kind)

    # ---- persons ----
    pid = {}
    def get_person(nm):
        k = name_key(nm)
        if not k:
            return None
        if k not in pid:
            pid[k] = len(pid) + 1
            db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, pid[k], nm.strip(), k))
        return pid[k]
    for v in votes:
        get_person(v["legislator_verbatim"])

    # ---- applications (one per bill) ----
    aid = {}
    for b in bills:
        key = "bill:%s:%s" % (b["session"], b["bill_no"])
        aid[(b["session"], b["bill_no"])] = len(aid) + 1
        origin = "House" if b["bill_no"].startswith("H") else "Senate"
        db.execute("INSERT INTO application VALUES (?,?,?,?,?,?)",
                   (CITY, aid[(b["session"], b["bill_no"])], key, body_id.get(origin),
                    ("%s %s: %s" % (b["session"], b["bill_no"], b["title"])).strip(),
                    b.get("sponsor", "")))

    # ---- meetings: (body, date) ----
    mid = {}
    def get_meeting(body, date, src):
        k = (body, date)
        if k not in mid:
            mid[k] = len(mid) + 1
            db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                       (CITY, mid[k], body_id[body], date,
                        "%s — %s" % (body, date), src))
        return mid[k]

    # ---- motions + votes ----
    votes_by_rc = defaultdict(list)
    for v in votes:
        votes_by_rc[v["rollcall_id"]].append(v)

    motion_no_ctr = Counter()   # per meeting
    role_ct = Counter()
    role_span = {}
    motion_id = vote_id = 0
    for rc in rcs:
        bn = rc["body_name"] or (rc["chamber"] or "Unknown")
        date = iso(rc["date"])
        src = rc["source_url"]
        meeting_id = get_meeting(bn, date, src)
        motion_no_ctr[meeting_id] += 1
        motion_id += 1
        recorded = rc["recorded"] == "1"
        # verbatim result tally
        if recorded and rc["yeas"] != "":
            result_raw = "%s-%s-%s" % (rc["yeas"], rc["nays"], rc["absent"])
        else:
            result_raw = "Voice vote"
        outcome = ""
        if recorded and rc["result"]:
            outcome = rc["result"]
        app = aid.get((rc["session"], rc["bill_no"]))
        vote_type = rc["vote_type"]   # floor | committee
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            CITY, motion_id, meeting_id, body_id[bn], motion_no_ctr[meeting_id],
            (rc["motion_desc"] or "").strip(),
            vote_type,                       # motion_type = floor/committee
            result_raw, outcome, "", "",     # stage, recommendation blank
            app, "bill_id" if app else "", "high" if app else "",
            None, None,                      # no mover/seconder in this channel
            1 if (recorded and votes_by_rc.get(rc["rollcall_id"])) else 0,
            src, "le_utah_website"))
        # votes
        for v in votes_by_rc.get(rc["rollcall_id"], []):
            p = get_person(v["legislator_verbatim"])
            if not p:
                continue
            try:
                vote_id += 1
                db.execute("INSERT INTO vote VALUES (?,?,?,?,?)",
                           (CITY, vote_id, motion_id, p, v["vote_value"]))
            except sqlite3.IntegrityError:
                vote_id -= 1
                continue
            b_id = body_id[bn]
            role_ct[(p, b_id)] += 1
            sp = role_span.get((p, b_id), [date, date])
            sp[0] = min(sp[0], date) if date else sp[0]
            sp[1] = max(sp[1], date) if date else sp[1]
            role_span[(p, b_id)] = sp

    rid = 0
    for (p, b_id), n in role_ct.items():
        rid += 1
        sp = role_span[(p, b_id)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)",
                   (CITY, rid, p, b_id, sp[0], sp[1], n))

    db.commit()
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("ut_state.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role", "referral"):
        print("  %-12s %d" % (t, c(t)))
    named = c("motion") and db.execute(
        "SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions w/ named roll call: %d / %d (rest voice-vote — recording ceiling)"
          % (named, c("motion")))
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    print("  foreign_key_check:", "OK (0)" if not fk else fk)
    print("  integrity_check:", db.execute("PRAGMA integrity_check").fetchone()[0])
    db.close()


if __name__ == "__main__":
    main()
