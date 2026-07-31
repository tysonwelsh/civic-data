#!/usr/bin/env python3
"""Entity-aware conformance validator (Phase 6, 2026-07-20).

Usage:  python3 scripts/validate_entity.py <slug-or-dir> [...]
        python3 scripts/validate_entity.py --all
        python3 scripts/validate_entity.py --federation   (staleness gate only)

Dispatches by registry level: CITY entities delegate unchanged to the proven
scripts/validate_city.py; non-city entities (county/regional/state) get
module-aware checks. Like validate_city.py this NEVER mutates anything —
PASS/WARN/FAIL report only.

Non-city checks:
  registry   — row parses, fed_index band (county 101-199 / regional 201-299 /
               state 301+), dir exists unless registered-only
  db         — if db_rel_path set: file exists, STANDARD 8 tables present
               (incl. referral — the federator hard-fails without it),
               foreign_key_check 0, integrity_check ok
  modules    — every present module index parses with its loader-facing
               columns: projections (9-col repo schema), gis (SLCo catalog
               cols), projects (15-col cross-MPO schema), elections
               by-contest (14 load_election_result cols), ordinances index
               (non-city motion_id convention), minutes_index md_paths
               resolve on disk, advisory_opinions/statutes indexes

Every entity (city included) additionally gets the FEDERATION STALENESS gate —
see federation_rows() below.
"""
import csv
import datetime as _dt
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from entities import ENTITIES  # noqa: E402

STANDARD_TABLES = {"body", "person", "meeting", "application", "motion",
                   "vote", "role", "referral"}
PROJ_COLS = {"geography", "geography_type", "year", "metric", "value",
             "scenario", "source", "source_url", "vintage"}
GIS_COLS = {"layer", "publisher", "url"}
PROJECT_COLS = {"entity", "plan_kind", "plan_vintage", "project_id", "name",
                "mode", "improvement_type", "jurisdiction", "county",
                "phase_or_year", "cost", "status", "description",
                "source_layer", "source_url"}
ELECT_COLS = {"year", "election_type", "contest", "jurisdiction_slug",
              "office", "district", "seats", "candidate", "party", "votes",
              "rank_in_contest", "n_precincts", "suppressed", "source_file"}
BANDS = {"county": (101, 199), "regional": (201, 299), "state": (301, 399)}


class Rep:
    def __init__(self):
        self.rows = []

    def add(self, status, check, msg):
        self.rows.append((status, check, msg))

    def emit(self, slug):
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        print("== %s" % slug)
        for status, check, msg in self.rows:
            counts[status] += 1
            print("  %-4s %-18s %s" % (status, check, msg))
        print("  -> %d PASS / %d WARN / %d FAIL" %
              (counts["PASS"], counts["WARN"], counts["FAIL"]))
        return counts["FAIL"]


def header(path):
    with open(path, newline="", encoding="utf-8") as f:
        return set(next(csv.reader(f)))


def n_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


PLACEHOLDER_MARK = re.compile(
    r"\[SCANNED\b|OCR\s*\+?\s*vote extraction DEFERRED|OCR pending"
    r"|minutes file for this date/item is pending creation", re.I)


def _content_gates(rep, module, paths, dates):
    """Gates the 2026-07-25 audit had to invent by hand because nothing checked them.

    Every defect class below shipped past a clean `validate_entity` run:
      * empty / placeholder bodies  — cache 160 of 307, weber 21 of 533 documents were
        front-matter-only or "[SCANNED … DEFERRED]" stubs while `has_text` said otherwise;
      * duplicate (date, body) documents — a source PDF containing the same meeting twice
        doubled every motion in it (summit 2015-01-08);
      * future-dated meetings — a county file_descr typo ("July 16, 2029") filed a 2019
        meeting ten years ahead.
    Reported as WARN, not FAIL: each can be legitimate in a specific entity (a genuinely
    deferred OCR era, a real second meeting on one date), so this surfaces them for a human
    rather than blocking a build.
    """
    if not paths:
        return
    empty, placeholder = [], []
    for fp in paths:
        try:
            t = open(fp, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        m = re.match(r"---\n.*?\n---\n", t, re.S)
        body = t[m.end():] if m else t
        if PLACEHOLDER_MARK.search(body):
            placeholder.append(fp)
        elif len(body.strip()) < 200:
            empty.append(fp)
    n = len(paths)
    if placeholder:
        rep.add("WARN", module, "%d/%d minutes are PLACEHOLDER bodies (OCR/extraction "
                                "deferred) — they carry no searchable text: %s"
                % (len(placeholder), n, os.path.basename(placeholder[0])))
    if empty:
        rep.add("WARN", module, "%d/%d minutes have an EMPTY body (<200 chars): %s"
                % (len(empty), n, os.path.basename(empty[0])))
    if not placeholder and not empty:
        rep.add("PASS", module, "%d minutes all carry a real body" % n)

    only = [d for d, _s in dates]
    dup = sorted({d for d in only if only.count(d) > 1})
    if dup:
        rep.add("WARN", module, "%d date(s) appear on more than one document (verify they "
                                "are distinct meetings, not a doubled source): %s"
                % (len(dup), ", ".join(dup[:4])))
    # A future date is fine when the row SAYS it is a calendar entry; it is a defect only
    # when the row claims to be a held meeting (a county file_descr typo filed a 2019
    # meeting as 2029).
    today = _dt.date.today().isoformat()
    future = sorted({d for d, s in dates if d > today
                     and not re.search(r"schedul|upcoming|future|pending|cancel", s)})
    if future:
        rep.add("FAIL", module, "%d FUTURE-dated meeting(s) not marked scheduled: %s"
                % (len(future), ", ".join(future[:4])))


# --- federation staleness gate (2026-07-29) ---------------------------------
#
# WHY THIS EXISTS.  gov.db is DERIVED from each entity's own db by
# scripts/build_cities_db.py (cardinal rule 3). Nothing forced the two to stay in
# step: on 2026-07-29 gov.db was found ~3,000 motions BEHIND the entity dbs — the
# 2026-07-25/26 Tier-1 audit fixes (cache_county OCR backfill, weber_county OCR,
# utah_county vote-layer repair) had been built into each county's own db but never
# federated. County motions 24,346 -> 27,376, county votes 35,318 -> 39,237 landed
# only when someone happened to re-run the builder, and the root CLAUDE.md had been
# quoting the stale figures in the meantime. Every cross-entity number is wrong while
# that lasts, and it is silent.
#
# THE SIGNAL.  build_cities_db.copy_standard_tables() copies the 8 standard tables
# 1:1 — ids are offset and (slug, gov_level, state) is stamped on, but no row is
# added, dropped, or filtered. So for a fresh federation the identity
#
#     <entity db>.<table>  ==  gov.db.<table> WHERE city = <slug>
#
# holds EXACTLY, per table. We compare row counts plus, for the four tables that
# carry correctable content, a cheap length-sum digest over columns copied verbatim
# (motion_text/result_raw, vote_value, person.full_name, meeting.title). The digest
# is what catches a value-only repair — an override file applied in place, an OCR
# re-read that fixes text without changing row counts — which a pure count compare
# would sail straight past. Both signals are CONTENT-based and cannot be fooled by a
# build that merely touches a file.
#
# FALSE-POSITIVE CLASSES DELIBERATELY SUPPRESSED (a gate that cries wolf gets ignored):
#   * FILE MTIMES are not consulted at all. Rebuilds rewrite an entity db byte-for-byte
#     with identical content, and this repo has no version control to arbitrate — an
#     "entity db newer than gov.db" rule would fire constantly on nothing. Content
#     equality is the only claim made here.
#   * CSV-vs-db row differences are OUT OF SCOPE by construction. weber_county's
#     `votes 12,594 CSV / 12,585 db` is an expected, itemized 9-row difference
#     (weber_county/CLAUDE.md) — this gate compares db to db, never CSV to db, so that
#     divergence is invisible to it and must stay that way.
#   * DB-LESS BY DESIGN (washington_county, juab_county — no db_rel_path) and
#     REGISTERED-ONLY entities (wasatch_county, udot, uta — no build) are not stale;
#     they are honest tier decisions. Expected federated row count is zero and zero is
#     reported as PASS. (Rows appearing for one WOULD be reported — as a WARN — because
#     that could only mean the registry and gov.db disagree.)
#
# WHY WARN, NOT FAIL.  A stale gov.db is a real correctness problem but it is never the
# validated entity's defect — the entity db is right, the derived layer is behind — and
# it is fixed by one documented command. validate_entity exits non-zero on FAIL, so
# FAILing here would block an entity that is itself perfectly conformant, and would
# blame the wrong artifact. That is also the established idiom in this file: _content_gates
# reserves FAIL for what cannot be legitimate. For anyone who wants a hard gate,
# `--federation` is a dedicated repo-wide mode that DOES exit non-zero when stale.
GOV_DB = os.path.join(ROOT, "gov.db")
FED_TABLES = ("body", "person", "meeting", "application", "motion", "vote",
              "role", "referral")
# Extra content digest per table: expressions over columns copy_standard_tables()
# copies verbatim (never ids — those are offset at federation — and never provenance/
# disposition, which the federator defaults when an older entity db lacks the column).
FED_DIGEST = {
    "motion": "SUM(LENGTH(COALESCE(motion_text,''))), "
              "SUM(LENGTH(COALESCE(result_raw,'')))",
    "vote": "SUM(LENGTH(COALESCE(vote_value,'')))",
    "person": "SUM(LENGTH(COALESCE(full_name,'')))",
    "meeting": "SUM(LENGTH(COALESCE(title,'')))",
}
REFED = "re-federate:  python3 scripts/build_cities_db.py"


def open_gov():
    """gov.db read-only, or None if absent. NEVER opened for write — this
    validator does not mutate anything, least of all the federated db."""
    if not os.path.exists(GOV_DB):
        return None
    return sqlite3.connect("file:%s?mode=ro" % GOV_DB, uri=True)


def _fed_probe(con, table, slug=None):
    """(count, *digest) for a table, scoped to one entity when slug is given."""
    extra = FED_DIGEST.get(table)
    cols = "COUNT(*)" + (", " + extra if extra else "")
    if slug is None:
        return con.execute("SELECT %s FROM %s" % (cols, table)).fetchone()
    return con.execute("SELECT %s FROM %s WHERE city=?" % (cols, table),
                       (slug,)).fetchone()


def federation_rows(e, gov):
    """Rep rows comparing this entity's own db to what gov.db holds for it.

    Returns a list of (status, check, msg). Never FAILs — see the rationale above.
    """
    if gov is None:
        return [("WARN", "federation",
                 "gov.db absent at repo root — federation freshness CANNOT be "
                 "determined (not assumed fresh); %s" % REFED)]

    if not e.db_rel_path:
        # db-less by design, or registered-only: zero federated rows is correct.
        present = [t for t in FED_TABLES if _fed_probe(gov, t, e.slug)[0]]
        kind = ("registered-only" if not os.path.isdir(os.path.join(ROOT, e.dir))
                else "db-less by design")
        if present:
            return [("WARN", "federation",
                     "%s (no db_rel_path in the registry) yet gov.db holds rows "
                     "for it in %s — registry and gov.db disagree"
                     % (kind, ", ".join(present)))]
        return [("PASS", "federation",
                 "%s — 0 federated standard rows expected, 0 found" % kind)]

    dbp = os.path.join(ROOT, e.dir, e.db_rel_path)
    if not os.path.exists(dbp):
        return [("WARN", "federation",
                 "entity db %s missing — cannot compare against gov.db, so "
                 "freshness is UNDETERMINED (the db check above owns this defect)"
                 % e.db_rel_path)]

    src = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    deltas, src_tot, gov_tot = [], 0, 0
    try:
        for t in FED_TABLES:
            try:
                a = _fed_probe(src, t)
            except sqlite3.Error as exc:          # table absent in a custom db
                deltas.append("%s unreadable in entity db (%s)" % (t, exc))
                continue
            b = _fed_probe(gov, t, e.slug)
            src_tot += a[0]
            gov_tot += b[0]
            if a[0] != b[0]:
                deltas.append("%s %d->%d (%+d)" % (t, b[0], a[0], a[0] - b[0]))
            elif a[1:] != b[1:]:
                deltas.append("%s same %d rows but CONTENT differs "
                              "(text digest %s vs %s)" % (t, a[0], b[1:], a[1:]))
    finally:
        src.close()

    built_at = gov.execute(
        "SELECT value FROM build_info WHERE key='built_at'").fetchone()
    built_at = built_at[0] if built_at else "unknown"

    if not deltas:
        return [("PASS", "federation",
                 "gov.db (built %s) matches the entity db on all 8 standard "
                 "tables (%d rows, counts + content digest)"
                 % (built_at, src_tot))]
    if gov_tot == 0:
        return [("WARN", "federation",
                 "entity is BUILT (%d standard rows) but gov.db holds NOTHING for "
                 "'%s' — never federated (gov.db built %s); %s"
                 % (src_tot, e.slug, built_at, REFED))]
    return [("WARN", "federation",
             "gov.db is STALE for this entity (built %s) — %s; %s"
             % (built_at, "; ".join(deltas), REFED))]


def federation_sweep():
    """Repo-level mode: one pass over gov.db for all entities.

    Cheaper than the per-entity path (gov.db is opened once) and usable as a hard
    gate — unlike the in-report WARN, this mode EXITS NON-ZERO when anything is
    stale, so it can front a build or a doc-refresh.
    """
    gov = open_gov()
    print("== federation staleness gate  (entity db  ->  gov.db)")
    if gov is not None:
        row = gov.execute(
            "SELECT value FROM build_info WHERE key='built_at'").fetchone()
        print("   gov.db built_at: %s" % (row[0] if row else "unknown"))
    stale = 0
    for e in ENTITIES:
        for status, _check, msg in federation_rows(e, gov):
            if status != "PASS":
                stale += 1
            print("  %-4s %-20s %s" % (status, e.slug, msg))
    if gov is not None:
        gov.close()
    print("  -> %d/%d entities in step; %d need attention"
          % (len(ENTITIES) - stale, len(ENTITIES), stale))
    if stale:
        print("  -> %s" % REFED)
    return stale


def check_index(rep, path, need, check_name):
    if not os.path.exists(path):
        return False
    try:
        cols = header(path)
    except Exception as exc:
        rep.add("FAIL", check_name, "%s unreadable: %s" % (path, exc))
        return True
    missing = need - cols
    if missing:
        rep.add("FAIL", check_name,
                "%s missing loader columns %s" % (os.path.basename(path),
                                                  sorted(missing)))
    else:
        rep.add("PASS", check_name,
                "%s: %d rows, loader columns present" %
                (os.path.relpath(path, ROOT), n_rows(path)))
    return True


def validate_noncity(e):
    rep = Rep()
    edir = os.path.join(ROOT, e.dir)
    lo, hi = BANDS.get(e.level, (0, 10**9))
    if lo <= int(e.fed_index) <= hi:
        rep.add("PASS", "registry", "level=%s fed_index=%s in band %d-%d"
                % (e.level, e.fed_index, lo, hi))
    else:
        rep.add("FAIL", "registry", "fed_index %s outside %s band %d-%d"
                % (e.fed_index, e.level, lo, hi))
    if not os.path.isdir(edir):
        status = "WARN" if not e.db_rel_path else "FAIL"
        rep.add(status, "layout", "dir %s absent (%s)" %
                (e.dir, "registered-only" if status == "WARN" else "but db_rel_path set"))
        return rep

    # db (when built)
    if e.db_rel_path:
        dbp = os.path.join(edir, e.db_rel_path)
        if not os.path.exists(dbp):
            rep.add("FAIL", "db", "%s missing" % e.db_rel_path)
        else:
            con = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
            tabs = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            missing = STANDARD_TABLES - tabs
            if missing:
                rep.add("FAIL", "db", "standard tables missing: %s"
                        % sorted(missing))
            else:
                nm = con.execute("SELECT COUNT(*) FROM motion").fetchone()[0]
                nv = con.execute("SELECT COUNT(*) FROM vote").fetchone()[0]
                rep.add("PASS", "db", "8 standard tables; motion %d / vote %d"
                        % (nm, nv))
            fk = con.execute("PRAGMA foreign_key_check").fetchall()
            ic = con.execute("PRAGMA integrity_check").fetchone()[0]
            rep.add("PASS" if not fk else "FAIL", "db-fk",
                    "foreign_key_check %d" % len(fk))
            rep.add("PASS" if ic == "ok" else "FAIL", "db-integrity", ic)
            con.close()

    # module indexes (only checked when present — module absence is a tier
    # decision, not a defect)
    found = 0
    for sub in ("projections",):
        for fn in sorted(os.listdir(os.path.join(edir, sub))) \
                if os.path.isdir(os.path.join(edir, sub)) else []:
            if fn.endswith(".csv"):
                found += check_index(rep, os.path.join(edir, sub, fn),
                                     PROJ_COLS, "projections")
    found += check_index(rep, os.path.join(edir, "gis", "index.csv"),
                         GIS_COLS, "gis")
    found += check_index(rep, os.path.join(edir, "projects", "projects.csv"),
                         PROJECT_COLS, "projects")
    found += check_index(rep, os.path.join(
        edir, "elections", "election_results_by_contest.csv"),
        ELECT_COLS, "elections")
    ordp = os.path.join(edir, "ordinances", "index.csv")
    if os.path.exists(ordp):
        found += 1
        cols = header(ordp)
        if "motion_id" not in cols:
            rep.add("WARN", "ordinances",
                    "index.csv has no motion_id column (non-city loader "
                    "convention) — rows federate unlinked")
        else:
            rep.add("PASS", "ordinances", "index.csv: %d rows, motion_id "
                    "column present" % n_rows(ordp))
    for module in ("legislative", "land_use", "agencies",
                   "advisory_opinions", "statutes"):
        idx = os.path.join(edir, module, "index.csv")
        midx = os.path.join(edir, module, "minutes_index.csv")
        if os.path.exists(midx):
            found += 1
            bad = 0
            total = 0
            paths = []
            dates = []
            with open(midx, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    # 2026-07-26 (audit S6): entities name this column differently —
                    # weber and mag use `minutes_md`, so a md_path-only lookup reported
                    # "0 md_paths, 0 unresolved" and silently validated NOTHING for
                    # 533 + 151 documents. Accept every spelling in use.
                    p = (r.get("md_path") or r.get("minutes_md")
                         or r.get("path") or r.get("text_path") or "")
                    d = (r.get("date") or r.get("meeting_date") or "").strip()
                    if d:
                        status = " ".join(str(r.get(k) or "") for k in
                                          ("minutes_status", "doc_status", "note", "status"))
                        dates.append((d, status.lower()))
                    if not p:
                        continue
                    total += 1
                    # the column is relative to different roots per entity: the entity dir
                    # (md_path), the repo root, or the MODULE dir (summit writes
                    # `path=minutes/<yr>/<file>.md`). Try each before calling it unresolved.
                    cands = [p] if os.path.isabs(p) else [
                        os.path.join(edir, p),
                        os.path.join(ROOT, p),
                        os.path.join(edir, module, p),
                    ]
                    fp = next((c for c in cands if os.path.exists(c)), None)
                    if fp is None:
                        bad += 1
                    else:
                        paths.append(fp)
            rep.add("PASS" if bad == 0 else "FAIL", module,
                    "minutes_index: %d md_paths, %d unresolved" % (total, bad))
            _content_gates(rep, module, paths, dates)
        elif os.path.exists(idx) and module in ("advisory_opinions",
                                                "statutes"):
            found += 1
            rep.add("PASS", module, "index.csv: %d rows" % n_rows(idx))
    if found == 0:
        rep.add("WARN", "modules", "no recognized module indexes found")
    return rep


def main():
    args = sys.argv[1:]
    if args == ["--federation"]:
        sys.exit(1 if federation_sweep() else 0)
    by_slug = {e.slug: e for e in ENTITIES}
    by_dir = {e.dir.rstrip("/"): e for e in ENTITIES if e.dir}
    if args == ["--all"]:
        targets = [e for e in ENTITIES]
    else:
        targets = []
        for a in args:
            key = a.rstrip("/")
            e = by_slug.get(key) or by_dir.get(key)
            if not e:
                print("unknown entity: %s" % a)
                sys.exit(2)
            targets.append(e)
    if not targets:
        print(__doc__)
        sys.exit(2)
    fails = 0
    # gov.db is opened ONCE for the whole run (read-only) — the federation gate is
    # per-entity but the federated db is not.
    gov = open_gov()
    for e in targets:
        if e.level == "city":
            # delegate to the proven city validator, unchanged
            rc = os.system("%s %s %s" % (
                sys.executable,
                os.path.join(ROOT, "scripts", "validate_city.py"),
                os.path.join(ROOT, e.dir)))
            fails += 1 if rc else 0
            # validate_city.py knows nothing about gov.db, so the federation gate
            # is reported here as its own block (cities federate exactly like every
            # other entity).
            frep = Rep()
            for row in federation_rows(e, gov):
                frep.add(*row)
            fails += 1 if frep.emit("%s (federation)" % e.slug) else 0
        else:
            rep = validate_noncity(e)
            for row in federation_rows(e, gov):
                rep.add(*row)
            fails += 1 if rep.emit(e.slug) else 0
    if gov is not None:
        gov.close()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
