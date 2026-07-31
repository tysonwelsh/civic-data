#!/usr/bin/env python3
"""Append the prose-extracted county Planning Commission layer to utah_county.db.

The Board of Commissioners / Work Session / Housing Authority come from the minutes
prose extraction (build_db.py). The county Planning Commission is NOT in that stream —
its votes were transcribed from the PMN minutes prose (land_use/all_votes.csv +
motions_tally.csv). Unlike the tally-only legislative OCR era, this PC is HIGH-attribution:
almost every motion prints the full "Aye <names> / Nay <names>" roll (71 of 73 motions
fully named), so names_recorded=1 on the named rows.

Runs AFTER build_db.py (which recreates the db fresh with legislative + agency only);
idempotent (drops any existing PC rows first). Continues the db's id counters so the
legislative motion_ids (1..10016) are NEVER renumbered — the closing pass only APPENDS
higher ids. PC-append-safe by construction.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "utah_county.db")
LU = os.path.join(COUNTY, "land_use")
CITY = "utah_county"

BODY_NAME = "Planning Commission"     # federated name; body kind 'planning'
VMAP = {"aye": "Aye", "yes": "Aye", "nay": "Nay", "no": "Nay", "abstain": "Abstain",
        "recuse": "Recuse", "recused": "Recuse", "absent": "Absent", "excused": "Excused"}


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def name_key(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def main():
    db = sqlite3.connect(DB)

    # ---- idempotent: remove any prior PC layer (body by name + dependents) ----
    row = db.execute("SELECT body_id FROM body WHERE name=?", (BODY_NAME,)).fetchone()
    if row:
        bid = row[0]
        mids = [r[0] for r in db.execute("SELECT motion_id FROM motion WHERE body_id=?", (bid,))]
        if mids:
            qs = ",".join("?" * len(mids))
            db.execute(f"DELETE FROM vote WHERE motion_id IN ({qs})", mids)
        db.execute("DELETE FROM motion WHERE body_id=?", (bid,))
        db.execute("DELETE FROM meeting WHERE body_id=?", (bid,))
        db.execute("DELETE FROM role WHERE body_id=?", (bid,))
        db.execute("DELETE FROM body WHERE body_id=?", (bid,))

    # verify legislative floor before append
    leg_max_before = db.execute("SELECT MAX(motion_id) FROM motion").fetchone()[0]

    nb = db.execute("SELECT COALESCE(MAX(body_id),0) FROM body").fetchone()[0]
    npx = db.execute("SELECT COALESCE(MAX(person_id),0) FROM person").fetchone()[0]
    nm = db.execute("SELECT COALESCE(MAX(meeting_id),0) FROM meeting").fetchone()[0]
    nmo = db.execute("SELECT COALESCE(MAX(motion_id),0) FROM motion").fetchone()[0]
    nv = db.execute("SELECT COALESCE(MAX(vote_id),0) FROM vote").fetchone()[0]
    pkey = {nk: pid for pid, nk in db.execute("SELECT person_id, name_key FROM person")}

    nb += 1
    body_id = nb
    db.execute("INSERT INTO body VALUES (?,?,?,?)", (CITY, body_id, BODY_NAME, "planning"))

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

    # ---- meetings from the minutes index (authoritative meeting list) ----
    meet = {}   # date -> meeting_id
    for r in rd(os.path.join(LU, "minutes_index.csv")):
        mp = (r.get("md_path") or "").strip()
        if not mp:
            continue                      # cancelled / no-minutes dates carry no meeting row
        if r["date"] in meet:
            continue
        nm += 1
        db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                   (CITY, nm, body_id, r["date"], "%s — %s" % (BODY_NAME, r["date"]), mp))
        meet[r["date"]] = nm

    def meeting_for(date, src=""):
        nonlocal nm
        if date not in meet:
            nm += 1
            db.execute("INSERT INTO meeting VALUES (?,?,?,?,?,?)",
                       (CITY, nm, body_id, date, "%s — %s" % (BODY_NAME, date),
                        src or ("pmn:%s" % date)))
            meet[date] = nm
        return meet[date]

    # ---- motions: tally rows (all) + named-vote motion fields ----
    votes = rd(os.path.join(LU, "all_votes.csv"))
    named_keys = {}   # (date, motion_no) -> motion fields (first seen)
    for v in votes:
        named_keys.setdefault((v["date"], v["motion_no"]),
                              {"motion": v["motion"], "result": v["result"],
                               "mover": v["mover"], "seconder": v["seconder"],
                               "source": v["source"]})

    motion_id = {}    # (date, motion_no) -> motion_id

    def add_motion(date, mno, text, result, mover, sec, named, src):
        nonlocal nmo
        key = (date, mno)
        if key in motion_id:
            return motion_id[key]
        mid = meeting_for(date, src)
        nmo += 1
        db.execute("INSERT INTO motion VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (CITY, nmo, mid, body_id, int(mno) if str(mno).isdigit() else 0,
                    (text or "").strip(), "", (result or "").strip(),
                    "Pass", "", "recommend", None, "", "",
                    person(mover), person(sec), 1 if named else 0,
                    src or "", "minutes"))
        motion_id[key] = nmo
        return nmo

    for t in rd(os.path.join(LU, "motions_tally.csv")):
        named = str(t.get("names_recorded", "")).strip().lower() in ("1", "true", "yes")
        add_motion(t["date"], t["motion_no"], t["motion"], t["result"],
                   t.get("mover"), t.get("seconder"), named, "")
    # any named-vote motion not already present in the tally sheet
    for (date, mno), info in named_keys.items():
        add_motion(date, mno, info["motion"], info["result"],
                   info["mover"], info["seconder"], True, info["source"])

    # ---- votes (named roll rows) + roles ----
    role_ct, role_span = {}, {}
    for v in votes:
        key = (v["date"], v["motion_no"])
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
        role_ct[(pid, body_id)] = role_ct.get((pid, body_id), 0) + 1
        sp = role_span.get((pid, body_id), [v["date"], v["date"]])
        sp[0] = min(sp[0], v["date"]); sp[1] = max(sp[1], v["date"])
        role_span[(pid, body_id)] = sp

    nr = db.execute("SELECT COALESCE(MAX(role_id),0) FROM role").fetchone()[0]
    for (pid, bid), n in role_ct.items():
        nr += 1
        sp = role_span[(pid, bid)]
        db.execute("INSERT INTO role VALUES (?,?,?,?,?,?,?)", (CITY, nr, pid, bid, sp[0], sp[1], n))

    db.commit()

    leg_max_after = db.execute(
        "SELECT MAX(motion_id) FROM motion m JOIN body b ON b.body_id=m.body_id "
        "WHERE b.name<>?", (BODY_NAME,)).fetchone()[0]
    assert leg_max_after == leg_max_before, \
        "legislative motion ids changed! %s -> %s" % (leg_max_before, leg_max_after)

    pcm = db.execute("SELECT COUNT(*) FROM motion WHERE body_id=?", (body_id,)).fetchone()[0]
    pcn = db.execute("SELECT COUNT(*) FROM motion WHERE body_id=? AND names_recorded=1",
                     (body_id,)).fetchone()[0]
    pcv = db.execute("SELECT COUNT(*) FROM vote v JOIN motion m ON m.motion_id=v.motion_id "
                     "WHERE m.body_id=?", (body_id,)).fetchone()[0]
    print("PC layer appended (Planning Commission, kind=planning):")
    print("  motions: %d (%d named-roll / %d tally-only), named vote rows: %d"
          % (pcm, pcn, pcm - pcn, pcv))
    print("  legislative motion_id ceiling unchanged: %d" % leg_max_after)
    print("  new max motion_id: %d | max meeting_id: %d"
          % (db.execute("SELECT MAX(motion_id) FROM motion").fetchone()[0],
             db.execute("SELECT MAX(meeting_id) FROM meeting").fetchone()[0]))
    db.close()


if __name__ == "__main__":
    main()
