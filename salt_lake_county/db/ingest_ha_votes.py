#!/usr/bin/env python3
"""Append the Housing Authority (HACSL / Housing Connect) vote layer to
salt_lake_county.db. Source: agencies/housing_authority/ (prose minutes from
housingconnect.org; PMN 2535 carries no minutes). Unlike the tally-primary Council/PC,
this board NAMES its votes (327 motions, ~1,692 named member rows, high-consensus).

Runs AFTER build_db.py + ingest_pc_votes.py; idempotent (drops prior HA rows first).
Continues the db id counters so federation offsets stay valid.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "salt_lake_county.db")
HA = os.path.join(COUNTY, "agencies", "housing_authority")
CITY = "salt_lake_county"
BODY = "Housing Authority"
VMAP = {"aye": "Aye", "yes": "Aye", "nay": "Nay", "no": "Nay", "abstain": "Abstain",
        "recuse": "Recuse", "recused": "Recuse", "absent": "Absent", "excused": "Excused"}


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def main():
    db = sqlite3.connect(DB)
    # idempotent: drop prior HA rows
    ids = [r[0] for r in db.execute("SELECT body_id FROM body WHERE name=?", (BODY,))]
    if ids:
        mids = [r[0] for r in db.execute("SELECT motion_id FROM motion WHERE body_id=?", (ids[0],))]
        if mids:
            db.execute("DELETE FROM vote WHERE motion_id IN (%s)" % ",".join("?" * len(mids)), mids)
        db.execute("DELETE FROM motion WHERE body_id=?", (ids[0],))
        db.execute("DELETE FROM meeting WHERE body_id=?", (ids[0],))
        db.execute("DELETE FROM role WHERE body_id=?", (ids[0],))
        db.execute("DELETE FROM body WHERE body_id=?", (ids[0],))

    nb = db.execute("SELECT COALESCE(MAX(body_id),0) FROM body").fetchone()[0] + 1
    db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, nb, BODY, "agency"))
    npx = db.execute("SELECT COALESCE(MAX(person_id),0) FROM person").fetchone()[0]
    nm = db.execute("SELECT COALESCE(MAX(meeting_id),0) FROM meeting").fetchone()[0]
    nmo = db.execute("SELECT COALESCE(MAX(motion_id),0) FROM motion").fetchone()[0]
    nv = db.execute("SELECT COALESCE(MAX(vote_id),0) FROM vote").fetchone()[0]
    pkey = {nk: pid for pid, nk in db.execute("SELECT person_id, name_key FROM person")}

    def person(nm_):
        nonlocal npx
        k = name_key(nm_)
        if not k:
            return None
        if k not in pkey:
            npx += 1
            db.execute("INSERT INTO person VALUES (?,?,?,?)", (CITY, npx, (nm_ or "").strip(), k))
            pkey[k] = npx
        return pkey[k]

    # meetings from the minutes index (date -> meeting_id, source = md_path)
    meet = {}
    for r in rd(os.path.join(HA, "minutes_index.csv")):
        mp = r.get("md_path") or ""
        if not mp or r["date"] in meet:
            continue
        nm += 1
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)", (CITY, nm, nb, r["date"], BODY, mp))
        meet[r["date"]] = nm

    def meeting_for(date, src):
        nonlocal nm
        if date not in meet:
            nm += 1
            db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                       (CITY, nm, nb, date, BODY, src or ("hacsl:%s" % date)))
            meet[date] = nm
        return meet[date]

    votes = rd(os.path.join(HA, "all_votes.csv"))
    # group rows by (date, motion_no)
    from collections import defaultdict
    by_motion = defaultdict(list)
    for v in votes:
        by_motion[(v["date"], v["motion_no"])].append(v)

    role_ct, role_span = {}, {}
    for (date, mno), rows in by_motion.items():
        first = rows[0]
        mid = meeting_for(date, first.get("source"))
        nmo += 1
        named = any(name_key(r.get("member")) and VMAP.get((r.get("vote") or "").lower()) for r in rows)
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (CITY, nmo, mid, nb, int(mno) if str(mno).isdigit() else 0,
                    (first.get("motion") or "").strip(), first.get("motion_type") or "",
                    (first.get("result") or "").strip(), "Pass", "", "", None, "", "",
                    person(first.get("mover")), person(first.get("seconder")),
                    1 if named else 0, first.get("source") or "", "minutes"))
        for r in rows:
            pid = person(r.get("member"))
            val = VMAP.get((r.get("vote") or "").strip().lower())
            if not (pid and val):
                continue
            nv += 1
            try:
                db.execute("INSERT INTO vote VALUES (?,?,?,?,?)", (CITY, nv, nmo, pid, val))
            except sqlite3.IntegrityError:
                nv -= 1
                continue
            role_ct[pid] = role_ct.get(pid, 0) + 1
            sp = role_span.get(pid, [date, date])
            sp[0] = min(sp[0], date); sp[1] = max(sp[1], date)
            role_span[pid] = sp

    nr = db.execute("SELECT COALESCE(MAX(role_id),0) FROM role").fetchone()[0]
    for pid, n in role_ct.items():
        nr += 1
        sp = role_span[pid]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)", (CITY, nr, pid, nb, sp[0], sp[1], n))

    db.commit()
    m = db.execute("SELECT COUNT(*) FROM motion WHERE body_id=?", (nb,)).fetchone()[0]
    v = db.execute("SELECT COUNT(*) FROM vote v JOIN motion mo ON mo.motion_id=v.motion_id "
                   "WHERE mo.body_id=?", (nb,)).fetchone()[0]
    print("Housing Authority appended: %d motions, %d named votes" % (m, v))
    db.close()


if __name__ == "__main__":
    main()
