#!/usr/bin/env python3
"""Append the prose-extracted Planning Commission layer to salt_lake_county.db.

The County Council/RDA/MBA come from Legistar (build_db.py). The two Planning
Commissions (unincorporated PC + Mountainous Planning District PC) are NOT in the
County Council's Legistar — their votes were extracted from the PMN minutes prose
(land_use/all_votes.csv + motions_tally.csv). Like West Jordan / South Jordan PC,
they are TALLY-PRIMARY: only dissenters/abstainers are named (16 named rows across
310 land-use motions; the rest carry `names_recorded=0`).

Runs AFTER build_db.py (which recreates the db fresh); idempotent (drops any existing
PC rows first). Continues the db's id counters so federation offsets stay valid.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "salt_lake_county.db")
LU = os.path.join(COUNTY, "land_use")
CITY = "salt_lake_county"

BODYNAME = {"PlanningCommission": "Planning Commission",
            "MountainousPlanningCommission": "Mountainous Planning District Planning Commission"}
VMAP = {"aye": "Aye", "yes": "Aye", "nay": "Nay", "no": "Nay", "abstain": "Abstain",
        "recuse": "Recuse", "recused": "Recuse", "absent": "Absent", "excused": "Excused"}


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def body_code_from_path(p):
    return "MountainousPlanningCommission" if "mountainous" in (p or "").lower() else "PlanningCommission"


def main():
    db = sqlite3.connect(DB)

    # idempotent: remove any prior PC layer (bodies by name + their dependent rows)
    pc_bodies = [r[0] for r in db.execute(
        "SELECT body_id FROM body WHERE name IN (?,?)", tuple(BODYNAME.values()))]
    if pc_bodies:
        qs = ",".join("?" * len(pc_bodies))
        mids = [r[0] for r in db.execute(
            f"SELECT motion_id FROM motion WHERE body_id IN ({qs})", pc_bodies)]
        if mids:
            mqs = ",".join("?" * len(mids))
            db.execute(f"DELETE FROM vote WHERE motion_id IN ({mqs})", mids)
        db.execute(f"DELETE FROM motion WHERE body_id IN ({qs})", pc_bodies)
        db.execute(f"DELETE FROM meeting WHERE body_id IN ({qs})", pc_bodies)
        db.execute(f"DELETE FROM role WHERE body_id IN ({qs})", pc_bodies)
        db.execute(f"DELETE FROM body WHERE body_id IN ({qs})", pc_bodies)

    nb = db.execute("SELECT COALESCE(MAX(body_id),0) FROM body").fetchone()[0]
    npx = db.execute("SELECT COALESCE(MAX(person_id),0) FROM person").fetchone()[0]
    nm = db.execute("SELECT COALESCE(MAX(meeting_id),0) FROM meeting").fetchone()[0]
    nmo = db.execute("SELECT COALESCE(MAX(motion_id),0) FROM motion").fetchone()[0]
    nv = db.execute("SELECT COALESCE(MAX(vote_id),0) FROM vote").fetchone()[0]
    pkey = {nk: pid for pid, nk in db.execute("SELECT person_id, name_key FROM person")}

    # bodies
    body_id = {}
    for code, name in BODYNAME.items():
        nb += 1
        db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, nb, name, "planning"))
        body_id[code] = nb

    def person(nm_):
        nonlocal npx
        k = name_key(nm_)
        if not k:
            return None
        if k not in pkey:
            npx += 1
            db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, npx, nm_.strip(), k))
            pkey[k] = npx
        return pkey[k]

    # meetings from the minutes index (authoritative meeting list); key (date, body_code)
    meet = {}
    for r in rd(os.path.join(LU, "minutes_index.csv")):
        mp = r.get("md_path") or ""
        if not mp:
            continue
        code = body_code_from_path(mp)
        key = (r["date"], code)
        if key in meet:
            continue
        nm += 1
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, nm, body_id[code], r["date"], BODYNAME[code], mp))
        meet[key] = nm

    def meeting_for(date, code, src=""):
        nonlocal nm
        key = (date, code)
        if key not in meet:
            nm += 1
            db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                       (CITY, nm, body_id[code], date, BODYNAME[code], src or ("pmn:%s" % date)))
            meet[key] = nm
        return meet[key]

    # motions: tally-only (motions_tally.csv) + named (distinct from all_votes.csv)
    votes = rd(os.path.join(LU, "all_votes.csv"))
    named_keys = {}   # (date, body_code, motion_no) -> row (first seen, for motion fields)
    for v in votes:
        code = v["body"]
        named_keys.setdefault((v["date"], code, v["motion_no"]),
                              {"motion": v["motion"], "result": v["result"],
                               "mover": v["mover"], "seconder": v["seconder"],
                               "source": v["source"]})

    motion_id = {}   # (date, body_code, motion_no) -> motion_id

    def add_motion(date, code, mno, text, result, mover, sec, named, src):
        nonlocal nmo
        key = (date, code, mno)
        if key in motion_id:
            return motion_id[key]
        mid = meeting_for(date, code, src)
        nmo += 1
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (CITY, nmo, mid, body_id[code], int(mno) if str(mno).isdigit() else 0,
                    (text or "").strip(), "", (result or "").strip(),
                    "Pass", "", "recommend", None, "", "",
                    person(mover), person(sec), 1 if named else 0,
                    src or "", "minutes"))
        motion_id[key] = nmo
        return nmo

    for t in rd(os.path.join(LU, "motions_tally.csv")):
        add_motion(t["date"], t["body"], t["motion_no"], t["motion"], t["result"],
                   t.get("mover"), t.get("seconder"), False, "")
    for k, info in named_keys.items():
        add_motion(k[0], k[1], k[2], info["motion"], info["result"],
                   info["mover"], info["seconder"], True, info["source"])

    # votes (named dissent/abstain rows)
    role_ct, role_span = {}, {}
    for v in votes:
        key = (v["date"], v["body"], v["motion_no"])
        mid = motion_id.get(key)
        pid = person(v["member"])
        val = VMAP.get((v["vote"] or "").strip().lower())
        if not (mid and pid and val):
            continue
        nv += 1
        try:
            db.execute("INSERT INTO vote VALUES (?,?,?,?,?)", (CITY, nv, mid, pid, val))
        except sqlite3.IntegrityError:
            nv -= 1
            continue
        bid = body_id[v["body"]]
        role_ct[(pid, bid)] = role_ct.get((pid, bid), 0) + 1
        sp = role_span.get((pid, bid), [v["date"], v["date"]])
        sp[0] = min(sp[0], v["date"]); sp[1] = max(sp[1], v["date"])
        role_span[(pid, bid)] = sp

    nr = db.execute("SELECT COALESCE(MAX(role_id),0) FROM role").fetchone()[0]
    for (pid, bid), n in role_ct.items():
        nr += 1
        sp = role_span[(pid, bid)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)", (CITY, nr, pid, bid, sp[0], sp[1], n))

    db.commit()
    pcm = db.execute("SELECT b.name, COUNT(*) FROM motion m JOIN body b ON b.body_id=m.body_id "
                     "WHERE b.kind='planning' GROUP BY b.name").fetchall()
    pcv = db.execute("SELECT COUNT(*) FROM vote v JOIN motion m ON m.motion_id=v.motion_id "
                     "JOIN body b ON b.body_id=m.body_id WHERE b.kind='planning'").fetchone()[0]
    print("PC layer appended:")
    for name, n in pcm:
        print("  %-52s %d motions" % (name, n))
    print("  named PC vote rows: %d" % pcv)
    db.close()


if __name__ == "__main__":
    main()
