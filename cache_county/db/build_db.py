#!/usr/bin/env python3
"""build_db.py — build cache_county.db, the STANDARD relational schema (SCHEMA_SPEC §5),
for Cache County from the prose-extracted vote CSVs.

Cache County is a self-hosted-CMS PROSE county (NOT Legistar), so — unlike the Salt Lake
County reference (Legistar API) — motions and votes are parsed from minutes text. The
legislative layer is the NAMED-ROLL-CALL centerpiece: born-digital minutes (~2021+) print
every member's Aye/Nay on every motion (`names_recorded=1`); scanned 2015-2020 minutes are
tally-only (`names_recorded=0`, an honest recording ceiling). See ../recon.md.

This adapts salt_lake_county/db/build_db.py to a prose county by reusing the repo's proven,
federation-compatible city-db core (scripts/db_build_lib.py) — the SAME 8-table schema
(body/person/meeting/application/motion/vote/role + the motion_std/views layer) every
per-city db has, so scripts/build_cities_db.py federates it UNCHANGED (gov_level='county',
fed_index 104). db_build_lib is imported READ-ONLY and never modified.

APPENDABLE + IDEMPOTENT: sources are read in a FIXED order — legislative first, then the
land_use (Planning Commission) layer if/when it exists — so the closing pass can ingest PC
votes later WITHOUT renumbering the legislative motion_ids (new bodies get higher ids).
Rerun any time; the db is fully rebuilt from the flat CSVs.

    python3 db/build_db.py
"""
import csv, glob, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                       # cache_county/
ROOT = os.path.dirname(REPO)                        # civic-data/
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import db_build_lib as L                            # read-only import of the shared core

DB = os.path.join(HERE, "cache_county.db")


def _tokkey(nm):
    """Token key: lowercase alpha-only, DROPPING single-letter middle initials so the
    born-digital minutes' interchangeable 'Gordon A. Zilles'/'Gordon Zilles',
    'Karl B. Ward'/'Karl Ward' resolve to ONE member."""
    toks = [t for t in re.sub(r"[^A-Za-z ]", " ", nm or "").split() if len(t) > 1]
    return "".join(toks).lower()


# Canonical roster (born-digital full-name forms). CANON_BY_PKEY selects the canonical
# DISPLAY name for each token-key (so middle-initial variants converge on one spelling).
CANON_NAMES = [
    "Barbara Tidwell", "Brady Christensen", "Chris Sands", "David Erickson",
    "Gina H. Worthen", "Gordon A. Zilles", "Jason Watterson", "JoAnn Bennett",
    "Karl B. Ward", "Kathryn Beus", "Keegan Garrity", "Kurt Bankhead", "Lane Parker",
    "Mark Hurd", "Morris Poole", "Nate Daugs", "Nolan Gunnell", "Paul Borup",
    "Sandi Goodlander", "Val Jay Rigby",
]
CANON_BY_PKEY = {_tokkey(c): c for c in CANON_NAMES}


def load_aliases():
    """db/person_aliases.csv — the DOCUMENTED person-key canonicalization path (cardinal
    rule: corrections via documented override files, never in-place edits). Maps OCR typos
    ('David Ericksqn'), role-prefix leakage ('Councilmembers Nolan Gunnell'), and
    mover/seconder surname fragments ('Erickson') onto the canonical member. The flat
    all_votes.csv keeps every verbatim name; unification is a db concern."""
    p = os.path.join(HERE, "person_aliases.csv")
    d = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            d[r["raw_name"].strip()] = r["canonical_name"].strip()
    return d


ALIAS = load_aliases()


# prefixes ROLE_PREFIX (shared lib) misses: hyphenated 'Vice-Chair'/'Vice- Chair' and the
# plural 'Councilmembers' (both require a trailing name — the bare generic tokens 'Vice-Chair'
# / 'Councilmember' have no following name and are deliberately KEPT as honest unattributed).
_XPFX = re.compile(r"^(vice[-\s]*chair|councilmembers)\s+", re.I)


def canon(nm):
    """Canonical DISPLAY name for a raw member/mover/seconder string."""
    if not nm:
        return None
    raw = nm.strip()
    if raw in ALIAS:
        return ALIAS[raw]
    n = L.norm_person(raw) or raw
    if n in ALIAS:
        return ALIAS[n]
    n2 = _XPFX.sub("", n).strip() or n
    if n2 in ALIAS:
        return ALIAS[n2]
    return CANON_BY_PKEY.get(_tokkey(n2), n2)


def pkey(nm):
    c = canon(nm)
    return _tokkey(c) if c else ""
# fixed source order (legislative spine first; land_use PC appended later, no renumber):
SOURCES = [
    os.path.join(REPO, "legislative", "all_votes.csv"),
    os.path.join(REPO, "land_use", "all_votes.csv"),   # tolerated-absent (other agent)
]


def main():
    motions, votes, present = L.read_motions(SOURCES, REPO)
    if not motions:
        print("no source motions found", file=sys.stderr); return 1

    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(L.DDL); con.executescript(L.MOTION_STD_DDL)
    cur = con.cursor()

    # bodies
    bid = {}
    for b in sorted({m["body"] for m in motions.values()}):
        cur.execute("INSERT INTO body(name,kind) VALUES(?,?)", (b, L.kind_of(b)))
        bid[b] = cur.lastrowid
    # persons (movers, seconders, named voters) — unified by name_key
    names = set()
    for _, _, nm, _ in votes:
        if nm:
            names.add(nm)
    for m in motions.values():
        for nm in (m["mover"], m["seconder"]):
            if nm:
                names.add(nm)
    pid, canon_name = {}, {}
    for nm in sorted(names):
        k = pkey(nm)
        if not k or k in pid:
            continue
        canon_name[k] = canon(nm)          # deterministic: all raws sharing k canon() alike
        cur.execute("INSERT INTO person(full_name,name_key) VALUES(?,?)", (canon_name[k], k))
        pid[k] = cur.lastrowid

    def pers(nm):
        return pid.get(pkey(nm)) if nm else None

    # meetings (body, source_file) unique
    mtg = {}
    for m in motions.values():
        key = (m["body"], m["source"])
        if key not in mtg:
            cur.execute("INSERT OR IGNORE INTO meeting(body_id,meeting_date,title,source_file) "
                        "VALUES(?,?,?,?)", (bid[m["body"]], m["date"], m["title"], m["source"]))
            cur.execute("SELECT meeting_id FROM meeting WHERE body_id=? AND source_file=?",
                        (bid[m["body"]], m["source"]))
            mtg[key] = cur.fetchone()[0]

    # applications (light land-use resolution: singleton/name for land-use motions only —
    # legislative motions are mostly ordinances/resolutions/appointments -> app_id NULL)
    app, apptitle = {}, {}

    def get_app(app_key, body, nm, title):
        if app_key not in app:
            cur.execute("INSERT INTO application(app_key,body_id,name,rep_title) VALUES(?,?,?,?)",
                        (app_key, bid[body], nm, title))
            app[app_key] = cur.lastrowid; apptitle[app_key] = title or ""
        return app[app_key]

    vbym = {}
    for src, mno, nm, vv in votes:
        vbym.setdefault((src, mno), []).append((nm, vv))

    mid = {}
    for (src, mno), m in motions.items():
        body, title = m["body"], m["motion"]
        app_id = method = conf = None
        if L.application_worthy(body, m["motion_type"], title):
            nm = None if L.CODE_AMEND_RE.search(title or "") else L.project_name(title)
            nk = L.name_key(nm)
            if nk:
                app_id = get_app("%s|%s" % (body, nk), body, nm, title); method, conf = "name", "medium"
            else:
                app_id = get_app("%s|s|%s|%s" % (body, src, mno), body, None, title)
                method, conf = "singleton", "high"
        disp, dmeth, dconf = L.disposition_of(title)
        mvotes = vbym.get((src, mno), [])
        cur.execute(
            """INSERT INTO motion(meeting_id,body_id,motion_no,motion_text,motion_type,result_raw,
               outcome,stage,recommendation,disposition,disposition_method,disposition_confidence,
               application_id,app_match_method,app_confidence,mover_person_id,seconder_person_id,
               names_recorded,source_file,provenance)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (mtg[(body, src)], bid[body], mno, title, m["motion_type"], m["result"],
             L.outcome_of(m["result"], disp), L.stage_of(body, m["result"], title),
             L.recommendation_of(body, m["result"], title), disp, dmeth, dconf,
             app_id, method, conf, pers(m["mover"]), pers(m["seconder"]),
             1 if mvotes else 0, src, m["provenance"]))
        mid[(src, mno)] = cur.lastrowid

    # votes — identical duplicate rows merge silently; CONTRADICTORY (motion, person) pairs
    # (the source listed a member under two labels, e.g. a full-roster AYE template line plus
    # a deliberate NAY/ABSTAIN dissent line) MUST have a documented resolution in
    # db/vote_overrides.csv (the repo's park_city/city conflict-resolution convention). Any
    # uncovered conflict FAILS the build loudly — a value is never silently arbitrated.
    LEGAL_VALUES = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}
    vote_ov = {}
    vp = os.path.join(HERE, "vote_overrides.csv")
    if os.path.exists(vp):
        for r in csv.DictReader(open(vp)):
            vote_ov[(r["source_file"], r["motion_no"].strip(), pkey(r["member"]))] = r["resolution"].strip()
    ov_consumed = set()
    n_ins = n_merged = n_excluded = n_noperson = 0
    conflicts_unresolved = []
    for (src, mno), vs in vbym.items():
        by_person = {}
        for nm, vv in vs:
            p = pers(nm)
            if p is None:
                n_noperson += 1; continue
            by_person.setdefault(pkey(nm), []).append((p, vv))
        for k, pv in by_person.items():
            p = pv[0][0]
            vals = [vv for _, vv in pv]
            distinct = sorted(set(vals))
            if len(distinct) == 1:
                vv = distinct[0]; n_merged += len(vals) - 1
            else:
                res = vote_ov.get((src, str(mno), k))
                if res is None:
                    conflicts_unresolved.append((src, mno, canon_name.get(k, k), distinct)); continue
                ov_consumed.add((src, str(mno), k))
                if res.lower() == "exclude":
                    n_excluded += len(vals); continue
                if res not in LEGAL_VALUES:
                    sys.exit("BUILD FAILED: vote_overrides.csv resolution %r is not a legal "
                             "vote value (or 'exclude') for %s on %s motion %s"
                             % (res, canon_name.get(k, k), src, mno))
                vv = res; n_merged += len(vals) - 1
            cur.execute("INSERT INTO vote(motion_id,person_id,vote_value) VALUES(?,?,?)",
                        (mid[(src, mno)], p, vv))
            n_ins += 1
    if conflicts_unresolved:
        for src, mno, nm, distinct in conflicts_unresolved:
            print("UNRESOLVED VOTE CONFLICT: %s motion %s %s: %s"
                  % (src, mno, nm, "+".join(distinct)), file=sys.stderr)
        sys.exit("BUILD FAILED: %d contradictory (motion, person) vote pair(s) not covered "
                 "by db/vote_overrides.csv" % len(conflicts_unresolved))
    for k in vote_ov:
        if k not in ov_consumed:
            sys.exit("BUILD FAILED: db/vote_overrides.csv row %r matched no contradictory "
                     "CSV pair (stale/mis-keyed row)" % (k,))
    print("  votes: %d inserted, %d merged (duplicate/override), %d excluded (override), "
          "%d unresolvable-person" % (n_ins, n_merged, n_excluded, n_noperson))

    # roles
    cur.execute("""INSERT INTO role(person_id,body_id,first_seen,last_seen,n_votes)
                   SELECT v.person_id, mo.body_id, MIN(m.meeting_date), MAX(m.meeting_date), COUNT(*)
                   FROM vote v JOIN motion mo ON mo.motion_id=v.motion_id
                     JOIN meeting m ON m.meeting_id=mo.meeting_id
                   GROUP BY v.person_id, mo.body_id""")

    # standard referral table (federation requires it in every built db).
    # EMPTY by design: no cross-body PC->Council referral layer has been
    # computed for cache_county (honest absence, not a gap in the source).
    cur.execute("""CREATE TABLE IF NOT EXISTS referral (city TEXT,
        referral_id INTEGER PRIMARY KEY, primary_application_id INTEGER,
        primary_body TEXT, related_application_id INTEGER, related_body TEXT,
        match_method TEXT, confidence TEXT, shared_address TEXT,
        subject_score REAL, primary_date TEXT, related_date TEXT,
        gap_days INTEGER, note TEXT)""")

    # normalization layer + views (tolerant of absent motions_std.csv)
    L.load_motion_std(cur, REPO)
    con.executescript(L.VIEWS); con.executescript(L.V_CONTESTED_DDL)
    con.commit()

    # integrity gates
    problems = []
    if cur.execute("PRAGMA foreign_key_check").fetchall():
        problems.append("FK violations")
    if cur.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        problems.append("integrity_check not ok")
    if cur.execute("SELECT COUNT(*) FROM motion").fetchone()[0] != len(motions):
        problems.append("motion count drift")

    # exports (tables/ CSVs — mirrors the city convention)
    tables = os.path.join(HERE, "tables"); os.makedirs(tables, exist_ok=True)
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' "
                            "AND name NOT LIKE 'sqlite_%'").fetchall():
        rows = cur.execute("SELECT * FROM %s" % t).fetchall()
        cols = [dd[0] for dd in cur.description]
        with open(os.path.join(tables, t + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)

    def n(t):
        return cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("== built db/cache_county.db from %d source(s) ==" % len(present))
    for t in ("body", "person", "meeting", "application", "motion", "vote", "role"):
        print("  %-12s %d" % (t, n(t)))
    named = cur.execute("SELECT COUNT(*) FROM motion WHERE names_recorded=1").fetchone()[0]
    print("  motions with NAMED roll call: %d / %d (rest tally-only — recording ceiling)"
          % (named, n("motion")))
    print("  bodies:", dict(cur.execute("SELECT name,COUNT(*) FROM motion JOIN body USING(body_id) GROUP BY 1")))
    print("  outcome:", dict(cur.execute("SELECT outcome,COUNT(*) FROM motion GROUP BY 1")))
    print("  contested (named dissent):", n("v_contested"))
    print("  INTEGRITY:", "OK" if not problems else problems)
    con.close()
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
