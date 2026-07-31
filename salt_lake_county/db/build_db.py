#!/usr/bin/env python3
"""Build salt_lake_county.db — the standard relational schema (SCHEMA_SPEC §5) for
Salt Lake County, from the Legistar structured harvest (db/staging/).

The County Council is TALLY-PRIMARY (recon.md): Legistar records the motion-level spine
(title/mover/seconder/passed/matter) for every action and named member votes ONLY for
divided votes. So `motion` rows come from passed eventitems, `vote` rows from the sparse
EventItemVote records, and `names_recorded=0` marks the (majority) tally-only motions —
an honest recording ceiling, exactly like nephi / west_jordan PC.

This db carries the SAME 8 standard tables every per-city db has, so the repo-root
build_cities_db.py federates it unchanged (gov_level='county', offset fed_index 101).
DERIVED + idempotent — rerun after a harvest; never hand-edit.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
STG = os.path.join(HERE, "staging")
DB = os.path.join(HERE, "salt_lake_county.db")

VMAP = {"yes": "Aye", "aye": "Aye", "no": "Nay", "nay": "Nay", "abstain": "Abstain",
        "recused": "Recuse", "recuse": "Recuse", "absent": "Absent",
        "excused": "Excused", "conflict": "Recuse"}
# body kind: the county's own legislative bodies vs its agencies
BODY_KIND = {"County Council": "council", "Committee of the Whole": "council",
             "Council Work Session": "council", "Board of Canvassers": "council",
             "Redevelopment Agency": "agency", "Municipal Building Authority": "agency",
             "Salt Lake County Municipal Building Authority": "agency"}

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
    # main staging first, then the isolated work-session/COW backfill (staging_ws) — the
    # order keeps existing Council/RDA/MBA motion_ids stable (new bodies get higher ids),
    # so the 67 ordinance→motion links never break. bodies/persons live only in staging/.
    rows = []
    for base in (STG, os.path.join(HERE, "staging_ws")):
        p = os.path.join(base, n)
        if os.path.exists(p):
            rows += list(csv.DictReader(open(p, encoding="utf-8")))
    return rows


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def vv(x):
    return VMAP.get((x or "").strip().lower(), "")


def outcome_of(passed):
    p = (passed or "").strip().lower()
    if p == "pass":
        return "Pass"
    if p == "fail":
        return "Fail"
    return "Unknown"


def main():
    bodies_raw = {b["BodyId"]: b for b in rd("bodies.csv")}
    persons_raw = {p["PersonId"]: p for p in rd("persons.csv")}
    events = {e["EventId"]: e for e in rd("events.csv")}
    items = rd("eventitems.csv")
    votes = rd("votes.csv")

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(DDL)
    CITY = "salt_lake_county"

    # bodies present in the harvest (by name; the harvester tagged canonical names via events)
    body_names = {}   # canonical name -> body_id
    for e in events.values():
        body_names.setdefault(e["EventBodyName"], None)
    bid_map = {}
    for i, name in enumerate(sorted(n for n in body_names if n), start=1):
        db.execute("INSERT INTO body VALUES (?,?,?,?)",
                   (CITY, i, name, BODY_KIND.get(name, "council")))
        bid_map[name] = i

    # persons: everyone who moves/seconds/votes
    used = set()
    for it in items:
        for k in ("EventItemMover", "EventItemSeconder"):
            if it.get(k):
                used.add(it[k].strip())
    for v in votes:
        nm = (v.get("VotePersonName") or "").strip()
        if nm:
            used.add(nm)
    pid_map = {}   # name_key -> person_id
    pid = 0
    for nm in sorted(used):
        k = name_key(nm)
        if not k or k in pid_map:
            continue
        pid += 1
        pid_map[k] = pid
        db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, pid, nm, k))

    def person_id(nm):
        return pid_map.get(name_key(nm))

    # meetings — source_file points at the real minutes markdown where we have it
    # (module/minutes/<year>/<date>_<bodyslug>_<eid>.md; matches fetch_minutes.py naming),
    # else the Legistar minutes-file URL, else an InSite placeholder.
    county_dir = os.path.dirname(HERE)
    mid_map = {}
    for i, (eid, e) in enumerate(sorted(events.items(), key=lambda x: x[1]["EventDate"]), start=1):
        date = e["EventDate"][:10]
        module = e.get("_module") or "legislative"
        rel = os.path.join(module, "minutes", date[:4],
                           "%s_%s_%s.md" % (date, slug(e["EventBodyName"]), eid))
        if os.path.exists(os.path.join(county_dir, rel)):
            src = rel
        else:
            src = e.get("EventMinutesFile") or e.get("EventInSiteURL") or ("legistar:event:%s" % eid)
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, i, bid_map[e["EventBodyName"]], date, e["EventBodyName"], src))
        mid_map[eid] = i

    # applications (matters)
    app_map = {}
    aid = 0
    for it in items:
        mt = it.get("EventItemMatterId")
        if mt and mt not in app_map:
            aid += 1
            app_map[mt] = aid
            ev = events.get(it["EventItemEventId"])
            body_id = bid_map[ev["EventBodyName"]] if ev else None
            db.execute("INSERT INTO application VALUES (?,?,?,?,?,?)",
                       (CITY, aid, "matter:%s" % mt, body_id,
                        (it.get("EventItemMatterName") or "").strip(), ""))

    # votes indexed by eventitem
    from collections import defaultdict, Counter
    v_by_item = defaultdict(list)
    for v in votes:
        v_by_item[v["EventItemId"]].append(v)

    # motions = passed eventitems; motion_no per meeting by sequence
    def seq(it):
        for k in ("EventItemMinutesSequence", "EventItemAgendaSequence"):
            try:
                return int(float(it.get(k) or 0))
            except ValueError:
                pass
        return 0
    items_by_ev = defaultdict(list)
    for it in items:
        if it.get("EventItemPassedFlagName"):
            items_by_ev[it["EventItemEventId"]].append(it)

    motion_id = vote_id = 0
    role_ct = Counter()
    role_span = {}
    for eid, its in items_by_ev.items():
        if eid not in mid_map:
            continue
        ev = events[eid]
        date = ev["EventDate"][:10]
        body_id = bid_map[ev["EventBodyName"]]
        for mno, it in enumerate(sorted(its, key=seq), start=1):
            motion_id += 1
            vs = v_by_item.get(it["EventItemId"], [])
            names_recorded = 1 if vs else 0
            app_id = app_map.get(it.get("EventItemMatterId"))
            db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                CITY, motion_id, mid_map[eid], body_id, mno,
                (it.get("EventItemTitle") or "").strip().replace("\n", " "),
                it.get("EventItemMatterType") or "",
                it.get("EventItemPassedFlagName") or "",
                outcome_of(it.get("EventItemPassedFlagName")),
                "", "", app_id,
                "matter_id" if app_id else "", "high" if app_id else "",
                person_id(it.get("EventItemMover")), person_id(it.get("EventItemSeconder")),
                names_recorded,
                "legistar:eventitem:%s" % it["EventItemId"], "legistar"))
            for v in vs:
                val = vv(v.get("VoteValueName"))
                p = person_id(v.get("VotePersonName"))
                if not val or not p:
                    continue
                vote_id += 1
                try:
                    db.execute("INSERT INTO vote VALUES (?,?,?,?,?)",
                               (CITY, vote_id, motion_id, p, val))
                except sqlite3.IntegrityError:
                    vote_id -= 1
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
    c = lambda t: db.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("salt_lake_county.db built:")
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role"):
        print("  %-12s %d" % (t, c(t)))
    named = db.execute("SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions with named roll call: %d / %d (rest tally-only — recording ceiling)"
          % (named, c("motion")))
    db.close()


if __name__ == "__main__":
    main()
