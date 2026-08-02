#!/usr/bin/env python3
"""build_search_layer.py — add the LLM search layer to cities.db (REFACTOR_PLAN Phase 2).

    python3 scripts/build_search_layer.py     # (re)build the layer on an existing cities.db

Also invoked automatically at the end of `python3 scripts/build_cities_db.py`, so one
rebuild command produces the whole federated db. Read-only on every per-city file;
only writes tables inside <repo>/cities.db. Idempotent (drops + recreates its tables).

What it adds (everything carries a leading `city` column, like the core):

  comment           union of every public_comments/all_comments_clean.csv (verbatim cols)
  cf_filing         union of campaign_finance/filing_totals.csv   — one row PER FILING
                    (every entity with a campaign_finance/ dataset: cities AND counties
                    since 2026-08-01; the `city` column carries the entity slug):
                    NEVER sum dollar columns across rows (interim+summary double-counts);
                    use cf_cycle for any per-candidate/race total (repo rule).
  cf_contribution   union of campaign_finance/contributions.csv (+ amount_num REAL parsed)
  cf_expenditure    union of campaign_finance/expenditures.csv  (+ amount_num REAL parsed)
  cf_cycle          union of campaign_finance/cycle_totals.csv — the deduped rollup
  cf_candidate_person  (city, candidate) → person_id crosswalk, exact name-key matches
                    only; person_id NULL where no safe match (never forced)
  ordinance         union of every ordinances/index.csv (SCHEMA_SPEC §9 contract
                    columns since the 2026-07-06 migration), with the existing
                    matched_motion_* linkage resolved to a `motion_id` where
                    (city, matched_motion_date, matched_motion_no) identifies exactly
                    one motion (resolution method recorded; never forced)
  document          one row per source artifact across minutes / planning-commission
                    minutes / packets / housing_plans / ordinances / transcripts /
                    pmn_backfill, with `has_text`/`text_path` (what an LLM can read
                    directly) and `meeting_id` where the artifact IS a meeting's minutes
  fts_minutes       FTS5 over the full text of every minutes markdown file (both bodies)
  fts_motion        FTS5 external-content index over motion.motion_text
  fts_comment       FTS5 external-content index over comment subject/topic/text
  fts_ordinance     FTS5 over ordinance titles + text sidecars (deduped per source file)

Amounts: dollar strings are kept VERBATIM in `amount`; `amount_num` is the parsed
REAL alongside (blank/unparseable → NULL), per the values-alongside rule.
"""
import csv
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cities import CITIES
from entities import ENTITIES
# slug -> dir for EVERY entity (cities + counties/regional/state) — build_fts and the
# document loader resolve paths for non-city entities through this.
ENT_DIR = {e.slug: e.dir for e in ENTITIES}
# non-city entities carry minutes under module dirs (legislative/land_use/agencies)
NONCITY_MINUTES_MODULES = ("legislative", "land_use", "agencies",
                           "agencies/housing_authority")
from roster_lib import TERM_COLUMNS, DISTRICT_COLUMNS, PRECINCT_COLUMNS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "gov.db")   # renamed from cities.db 2026-07-20 (Phase 6)

csv.field_size_limit(10_000_000)


def log(msg):
    print(msg, flush=True)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_amount(s):
    if s is None:
        return None
    s = s.strip().replace("$", "").replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def name_key(name):
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def first(row, *cols):
    for c in cols:
        v = (row.get(c) or "").strip()
        if v:
            return v
    return None


PLACEHOLDER_BODY = re.compile(
    r"\[SCANNED\b|OCR\s*\+?\s*vote extraction DEFERRED|OCR pending"
    r"|minutes file for this date/item is pending creation", re.I)


def readable(abs_path, min_body=200):
    """True only if the file carries real body text.

    2026-07-26 (audit S5): `has_text` used to mean "a text-shaped file exists", so 195
    documents that were front-matter-only stubs or "[SCANNED … DEFERRED]" placeholders
    were all flagged has_text=1 AND indexed into fts_minutes. That overstated the repo's
    searchable coverage twice over — a keyword sweep counted them as covered and returned
    nothing from them.
    """
    try:
        t = open(abs_path, encoding="utf-8", errors="replace").read()
    except Exception:
        return False
    m = re.match(r"---\n.*?\n---\n", t, re.S)
    body = t[m.end():] if m else t
    if PLACEHOLDER_BODY.search(body):
        return False
    # min_body=200 guards stub/placeholder minutes; statutes get a lower floor
    # (G5, 2026-07-31): a 140-char LUDMA section is real law, and the old flat
    # 200 silently dropped 4 genuine sections from fts_minutes.
    return len(body.strip()) >= min_body


def text_sidecar(city_dir, dataset, path):
    """(has_text, text_path) for an artifact: the file itself if it carries real body
    text, else a text/<stem>.txt|.md sidecar in the dataset dir."""
    if not path:
        return 0, None
    rel = path if path.startswith(dataset + "/") else "%s/%s" % (dataset, path)
    absoluteish = os.path.join(ROOT, city_dir, rel)
    stem = os.path.splitext(os.path.basename(path))[0]
    if os.path.splitext(path)[1].lower() in (".md", ".txt") and os.path.exists(absoluteish):
        return (1, rel) if readable(absoluteish) else (0, None)
    for ext in (".txt", ".md"):
        cand = os.path.join(city_dir, dataset, "text", stem + ext)
        if os.path.exists(os.path.join(ROOT, cand)):
            return ((1, "%s/text/%s%s" % (dataset, stem, ext))
                    if readable(os.path.join(ROOT, cand)) else (0, None))
    return 0, None


DDL = """
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS cf_filing;
DROP TABLE IF EXISTS cf_contribution;
DROP TABLE IF EXISTS cf_expenditure;
DROP TABLE IF EXISTS cf_cycle;
DROP TABLE IF EXISTS cf_candidate_person;
DROP TABLE IF EXISTS ordinance;
DROP TABLE IF EXISTS document;
DROP TABLE IF EXISTS fts_minutes;
DROP TABLE IF EXISTS fts_motion;
DROP TABLE IF EXISTS fts_comment;
DROP TABLE IF EXISTS fts_ordinance;
DROP TABLE IF EXISTS fts_packet;
DROP VIEW IF EXISTS v_council_current;
DROP VIEW IF EXISTS v_term_provenance;
DROP TABLE IF EXISTS term;
DROP TABLE IF EXISTS district_version;
DROP TABLE IF EXISTS district_precinct;

CREATE TABLE comment (
    city TEXT NOT NULL, comment_id INTEGER PRIMARY KEY,
    date TEXT, contact_name TEXT, subject TEXT, topic TEXT, comment TEXT,
    district TEXT, source TEXT, has_attachment TEXT, source_file TEXT,
    page_numbers TEXT, period_start TEXT, period_end TEXT,
    date_normalized TEXT, quality_flag TEXT
);
CREATE TABLE cf_filing (
    city TEXT NOT NULL, candidate TEXT, office TEXT, election_year TEXT,
    filing_date TEXT, reporting_period TEXT, filing_type TEXT,
    stated_total_contributions TEXT, stated_total_expenditures TEXT,
    stated_beginning_balance TEXT, stated_ending_balance TEXT,
    itemized_contrib_sum TEXT, itemized_expend_sum TEXT,
    reconciles_contrib TEXT, reconciles_expend TEXT,
    recon_delta_contrib TEXT, recon_delta_expend TEXT, self_funded_amount TEXT,
    n_contrib_rows TEXT, n_expend_rows TEXT, source_filing TEXT,
    document_id TEXT, extraction_confidence TEXT, notes TEXT, filing_regime TEXT
);
CREATE TABLE cf_contribution (
    city TEXT NOT NULL, candidate TEXT, office TEXT, seat TEXT,
    election_year TEXT, filing_date TEXT, reporting_period TEXT, date TEXT,
    donor_raw TEXT, donor_normalized TEXT, donor_type TEXT, donor_city TEXT,
    donor_state TEXT, donor_district TEXT, amount TEXT, amount_num REAL,
    in_kind TEXT, is_incremental TEXT, source_filing TEXT, document_id TEXT,
    line_no TEXT, extraction_confidence TEXT, extract_method TEXT, needs_review TEXT
);
CREATE TABLE cf_expenditure (
    city TEXT NOT NULL, candidate TEXT, office TEXT, seat TEXT,
    election_year TEXT, filing_date TEXT, reporting_period TEXT, date TEXT,
    vendor_raw TEXT, vendor_normalized TEXT, purpose TEXT, amount TEXT,
    amount_num REAL, in_kind TEXT, is_incremental TEXT, source_filing TEXT,
    document_id TEXT, line_no TEXT, extraction_confidence TEXT,
    extract_method TEXT, needs_review TEXT
);
CREATE TABLE cf_cycle (
    city TEXT NOT NULL, candidate TEXT, election_year TEXT, office TEXT,
    seat TEXT, raised REAL, spent REAL, n_filings TEXT, n_live TEXT,
    basis TEXT, review_flag TEXT
);
CREATE TABLE cf_candidate_person (
    city TEXT NOT NULL, candidate TEXT NOT NULL,
    person_id INTEGER REFERENCES person(person_id),
    match_method TEXT, confidence TEXT,
    UNIQUE(city, candidate)
);
CREATE TABLE ordinance (
    city TEXT NOT NULL, ordinance_id INTEGER PRIMARY KEY,
    ordinance_no TEXT, adoption_date TEXT, title TEXT, land_use TEXT,
    result TEXT, source_url TEXT, retrieved_date TEXT, format TEXT,
    extraction_method TEXT, path TEXT, has_text INTEGER, text_path TEXT,
    matched_motion_date TEXT, matched_motion_no TEXT, match_confidence TEXT,
    motion_id INTEGER REFERENCES motion(motion_id), motion_resolution TEXT
);
CREATE TABLE document (
    city TEXT NOT NULL, document_id INTEGER PRIMARY KEY,
    doc_type TEXT NOT NULL, dataset TEXT NOT NULL, date TEXT, body TEXT,
    title TEXT, path TEXT, format TEXT, has_text INTEGER, text_path TEXT,
    doc_class TEXT,  -- primary-docs pilot taxonomy (staff_report/member_memo/
                     -- plan_amendment/development_agreement/...); NULL = unclassified
    source_url TEXT, meeting_id INTEGER REFERENCES meeting(meeting_id)
);

CREATE VIRTUAL TABLE fts_minutes USING fts5(
    text, city UNINDEXED, dataset UNINDEXED, date UNINDEXED, path UNINDEXED,
    tokenize='porter unicode61'
);
CREATE VIRTUAL TABLE fts_motion USING fts5(
    motion_text, content='motion', content_rowid='motion_id',
    tokenize='porter unicode61'
);
CREATE VIRTUAL TABLE fts_comment USING fts5(
    subject, topic, comment, content='comment', content_rowid='comment_id',
    tokenize='porter unicode61'
);
CREATE VIRTUAL TABLE fts_ordinance USING fts5(
    title, text, city UNINDEXED, ordinance_no UNINDEXED, text_path UNINDEXED,
    tokenize='porter unicode61'
);
CREATE VIRTUAL TABLE fts_packet USING fts5(
    title, text, city UNINDEXED, date UNINDEXED, packet_kind UNINDEXED,
    doc_class UNINDEXED, text_path UNINDEXED, tokenize='porter unicode61'
);

CREATE INDEX IF NOT EXISTS idx_comment_city_date ON comment(city, date_normalized);
CREATE INDEX IF NOT EXISTS idx_cfc_city_cand ON cf_contribution(city, candidate);
CREATE INDEX IF NOT EXISTS idx_cfe_city_cand ON cf_expenditure(city, candidate);
CREATE INDEX IF NOT EXISTS idx_ord_city_no ON ordinance(city, ordinance_no);
CREATE INDEX IF NOT EXISTS idx_doc_city_type_date ON document(city, doc_type, date);

-- Roster layer (scripts/roster_lib.py + <city>/roster/*.csv). Federated from
-- every city that HAS a roster/ dir (all 16 cities as of 2026-07-11); the CSV `city`
-- column is kept as-is. All-TEXT, no FK (roster person_key is a first_last slug,
-- not the offset-namespaced person.name_key — no clean join key).
CREATE TABLE term (
    city TEXT NOT NULL, body TEXT, seat_id TEXT, district TEXT,
    person_name TEXT, person_key TEXT, start_date TEXT, end_date TEXT,
    start_event TEXT, end_event TEXT, election_year TEXT,
    first_vote TEXT, last_vote TEXT, sources TEXT, confidence TEXT, note TEXT
);
CREATE TABLE district_version (
    city TEXT NOT NULL, district_id TEXT, plan_id TEXT, effective_start TEXT,
    effective_end TEXT, geometry_ref TEXT, adopted_by TEXT, source_url TEXT,
    confidence TEXT, note TEXT
);
CREATE TABLE district_precinct (
    city TEXT NOT NULL, plan_id TEXT, district_id TEXT, precinct_id TEXT,
    effective_start TEXT, effective_end TEXT, source TEXT, confidence TEXT, note TEXT
);
CREATE INDEX IF NOT EXISTS idx_term_city_seat ON term(city, seat_id, start_date);

-- v_council_current — current seat-holders across all rostered cities: term rows
-- whose interval is still open (end_date empty/null = currently serving). For a
-- point-in-time roster on an arbitrary date use the parameterized AS-OF pattern:
--   SELECT * FROM term
--   WHERE city=:city AND start_date<=:d AND (end_date='' OR end_date>:d);
CREATE VIEW v_council_current AS
SELECT city, body, seat_id, district, person_name, person_key,
       start_date, start_event, election_year, confidence, sources
FROM term
WHERE end_date IS NULL OR end_date = '';

-- v_term_provenance — per (city, confidence) tenure counts (a quick honesty
-- read on how much of each roster is election/minutes-anchored vs inferred).
CREATE VIEW v_term_provenance AS
SELECT city, confidence, COUNT(*) AS n_terms
FROM term
GROUP BY city, confidence;
"""


def load_comments(out):
    n_by_city = {}
    for c in CITIES:
        rows = read_csv(os.path.join(ROOT, c.dir, "public_comments",
                                     "all_comments_clean.csv"))
        for r in rows:
            out.execute(
                "INSERT INTO comment (city,date,contact_name,subject,topic,comment,"
                "district,source,has_attachment,source_file,page_numbers,"
                "period_start,period_end,date_normalized,quality_flag) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (c.slug, r.get("date"), r.get("contact_name"), r.get("subject"),
                 r.get("topic"), r.get("comment"), r.get("district"),
                 r.get("source"), r.get("has_attachment"), r.get("source_file"),
                 r.get("page_numbers"), r.get("period_start"), r.get("period_end"),
                 r.get("date_normalized"), r.get("quality_flag")))
        n_by_city[c.slug] = len(rows)
    return n_by_city


CF_FILING_COLS = ["candidate", "office", "election_year", "filing_date",
                  "reporting_period", "filing_type", "stated_total_contributions",
                  "stated_total_expenditures", "stated_beginning_balance",
                  "stated_ending_balance", "itemized_contrib_sum",
                  "itemized_expend_sum", "reconciles_contrib", "reconciles_expend",
                  "recon_delta_contrib", "recon_delta_expend", "self_funded_amount",
                  "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
                  "extraction_confidence", "notes", "filing_regime"]
CF_CONTRIB_COLS = ["candidate", "office", "seat", "election_year", "filing_date",
                   "reporting_period", "date", "donor_raw", "donor_normalized",
                   "donor_type", "donor_city", "donor_state", "donor_district",
                   "amount", "in_kind", "is_incremental", "source_filing",
                   "document_id", "line_no", "extraction_confidence",
                   "extract_method", "needs_review"]
CF_EXPEND_COLS = ["candidate", "office", "seat", "election_year", "filing_date",
                  "reporting_period", "date", "vendor_raw", "vendor_normalized",
                  "purpose", "amount", "in_kind", "is_incremental", "source_filing",
                  "document_id", "line_no", "extraction_confidence",
                  "extract_method", "needs_review"]


def load_cf(out):
    counts = {"cf_filing": 0, "cf_contribution": 0, "cf_expenditure": 0,
              "cf_cycle": 0}
    # Cities first (their row order is unchanged from the city-only era), then every
    # non-city entity with a dir — county campaign_finance/ datasets federate too
    # (2026-08-01 county-acquisition package). Entities without the dataset contribute
    # nothing (read_csv returns [] on missing files).
    cf_entities = list(CITIES) + [e for e in ENTITIES
                                  if e.level != "city" and e.dir]
    for c in cf_entities:
        cf = os.path.join(ROOT, c.dir, "campaign_finance")
        for r in read_csv(os.path.join(cf, "filing_totals.csv")):
            out.execute(
                "INSERT INTO cf_filing VALUES (?%s)" % (",?" * len(CF_FILING_COLS)),
                [c.slug] + [r.get(k) for k in CF_FILING_COLS])
            counts["cf_filing"] += 1
        for r in read_csv(os.path.join(cf, "contributions.csv")):
            vals = [r.get(k) for k in CF_CONTRIB_COLS]
            vals.insert(CF_CONTRIB_COLS.index("amount") + 1,
                        parse_amount(r.get("amount")))
            out.execute("INSERT INTO cf_contribution VALUES (?%s)"
                        % (",?" * (len(CF_CONTRIB_COLS) + 1)), [c.slug] + vals)
            counts["cf_contribution"] += 1
        for r in read_csv(os.path.join(cf, "expenditures.csv")):
            vals = [r.get(k) for k in CF_EXPEND_COLS]
            vals.insert(CF_EXPEND_COLS.index("amount") + 1,
                        parse_amount(r.get("amount")))
            out.execute("INSERT INTO cf_expenditure VALUES (?%s)"
                        % (",?" * (len(CF_EXPEND_COLS) + 1)), [c.slug] + vals)
            counts["cf_expenditure"] += 1
        for r in read_csv(os.path.join(cf, "cycle_totals.csv")):
            out.execute(
                "INSERT INTO cf_cycle VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (c.slug, r.get("candidate"), r.get("election_year"),
                 r.get("office"), r.get("seat"), parse_amount(r.get("raised")),
                 parse_amount(r.get("spent")), r.get("n_filings"),
                 r.get("n_live"), r.get("basis"), r.get("review_flag")))
            counts["cf_cycle"] += 1
    # candidate → person crosswalk (exact name-key only; never forced)
    persons = {}
    for city, pid, nk in out.execute("SELECT city, person_id, name_key FROM person"):
        persons.setdefault(city, {})[nk] = pid
    cands = out.execute(
        "SELECT DISTINCT city, candidate FROM ("
        " SELECT city, candidate FROM cf_filing"
        " UNION SELECT city, candidate FROM cf_cycle) WHERE candidate != ''"
    ).fetchall()
    matched = 0
    for city, cand in cands:
        pid = persons.get(city, {}).get(name_key(cand))
        out.execute("INSERT OR IGNORE INTO cf_candidate_person VALUES (?,?,?,?,?)",
                    (city, cand, pid,
                     "name_key" if pid else None, "high" if pid else None))
        matched += 1 if pid else 0
    return counts, len(cands), matched


# pre-2026-07-06 synonyms retired by the Phase-3 contract migration; the
# contract names are canonical (SCHEMA_SPEC §9)
ORD_LAND_USE = ("land_use",)
ORD_RESULT = ("result",)


def load_ordinances(out):
    # (city, meeting_date, motion_no) → motion_ids, council-side bodies only
    lookup = {}
    for city, mid, date, mno in out.execute(
            "SELECT m.city, m.motion_id, mt.meeting_date, m.motion_no "
            "FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id "
            "JOIN body b ON b.body_id = m.body_id "
            "WHERE b.name != 'PlanningCommission'"):
        lookup.setdefault((city, date, str(mno)), []).append(mid)
    n = resolved = ambiguous = 0
    for c in CITIES:
        for r in read_csv(os.path.join(ROOT, c.dir, "ordinances", "index.csv")):
            path = first(r, "path")
            has_text, tpath = text_sidecar(c.dir, "ordinances", path)
            mdate = first(r, "matched_motion_date")
            mno = first(r, "matched_motion_no")
            motion_id, resolution = None, None
            if mdate and mno:
                mids = lookup.get((c.slug, mdate, mno.split(".")[0]), [])
                if len(mids) == 1:
                    motion_id, resolution = mids[0], "unique"
                    resolved += 1
                elif len(mids) > 1:
                    resolution = "ambiguous"
                    ambiguous += 1
                else:
                    resolution = "no-motion-on-date"
            out.execute(
                "INSERT INTO ordinance (city,ordinance_no,adoption_date,title,"
                "land_use,result,source_url,retrieved_date,format,"
                "extraction_method,path,has_text,text_path,matched_motion_date,"
                "matched_motion_no,match_confidence,motion_id,motion_resolution) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (c.slug, first(r, "ordinance_no"),
                 first(r, "adoption_date", "date"), first(r, "title"),
                 first(r, *ORD_LAND_USE), first(r, *ORD_RESULT),
                 first(r, "source_url"), first(r, "retrieved_date"),
                 first(r, "format"), first(r, "extraction_method"),
                 path, has_text, tpath, mdate, mno,
                 first(r, "match_confidence"), motion_id, resolution))
            n += 1

    # non-city entities: the ordinance index carries a DIRECT county-db motion_id
    # (not matched_motion_date/no); federate it with the entity offset. Paths are
    # module-relative ("raw/x.pdf" / "text/x.txt") — prefix "ordinances/".
    for e in ENTITIES:
        if e.level == "city" or not e.dir:
            continue
        off = e.fed_index * 10_000_000
        for r in read_csv(os.path.join(ROOT, e.dir, "ordinances", "index.csv")):
            p = first(r, "path")
            tp = first(r, "text_path")
            if p and not p.startswith("ordinances/"):
                p = "ordinances/" + p
            if tp and not tp.startswith("ordinances/"):
                tp = "ordinances/" + tp
            ml = first(r, "motion_id")
            fed_mid = int(ml) + off if ml and str(ml).strip().isdigit() else None
            n += 1
            resolved += 1 if fed_mid else 0
            out.execute(
                "INSERT INTO ordinance (city,ordinance_no,adoption_date,title,"
                "land_use,result,source_url,retrieved_date,format,extraction_method,"
                "path,has_text,text_path,matched_motion_date,matched_motion_no,"
                "match_confidence,motion_id,motion_resolution) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (e.slug, first(r, "ordinance_no"), first(r, "adoption_date", "date"),
                 first(r, "title"), first(r, "land_use_type", "land_use"), "adopted",
                 first(r, "source_url"), "", first(r, "format") or "pdf", "legistar",
                 p, 1 if tp else 0, tp, "", "", first(r, "match_confidence"),
                 fed_mid, "unique" if fed_mid else "unlinked"))
    return n, resolved, ambiguous


def load_documents(out):
    # meeting lookup: source_file (as stored) and dataset-stripped variants
    meet = {}
    for city, mid, sf in out.execute(
            "SELECT city, meeting_id, source_file FROM meeting"):
        meet[(city, sf)] = mid
        # per-city dbs store source_file either root-relative or dataset-relative
        # (SCHEMA_SPEC §2 "both occur") — register both forms
        for prefix in ("meeting_minutes/", "planning_commission/"):
            if sf.startswith(prefix):
                meet.setdefault((city, sf[len(prefix):]), mid)
            else:
                meet.setdefault((city, prefix + sf), mid)
    counts = {}
    minutes_linked = minutes_total = 0

    def add(city, doc_type, dataset, date, body, title, path, fmt, has_text,
            tpath, url, meeting_id=None, doc_class=None):
        out.execute(
            "INSERT INTO document (city,doc_type,dataset,date,body,title,path,"
            "format,has_text,text_path,doc_class,source_url,meeting_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (city, doc_type, dataset, date, body, title, path, fmt,
             has_text, tpath, doc_class or None, url, meeting_id))
        counts[doc_type] = counts.get(doc_type, 0) + 1

    for c in CITIES:
        for dataset in ("meeting_minutes", "planning_commission"):
            for r in read_csv(os.path.join(ROOT, c.dir, dataset,
                                           "minutes_index.csv")):
                p = r.get("path") or ""
                rel = p if p.startswith(dataset + "/") else "%s/%s" % (dataset, p)
                mid = meet.get((c.slug, rel)) or meet.get((c.slug, p))
                minutes_total += 1
                minutes_linked += 1 if mid else 0
                # has_text from the BODY, same rule as the non-city branch (audit S5)
                _abs = os.path.join(ROOT, c.dir, rel) if rel else ""
                _ht = 1 if (_abs and os.path.exists(_abs) and readable(_abs)) else 0
                add(c.slug, "minutes", dataset, r.get("date"),
                    "PlanningCommission" if dataset == "planning_commission" else "",
                    r.get("title"), rel, r.get("format"), _ht, rel if _ht else None,
                    r.get("source_url"), mid)
        for dataset, default_type in (("packets", "packet"),
                                      ("housing_plans", "housing_plan"),
                                      ("transcripts", "transcript"),
                                      ("pmn_backfill", "pmn_minutes")):
            for r in read_csv(os.path.join(ROOT, c.dir, dataset, "index.csv")):
                path = first(r, "path")
                # an explicit text_path column (primary-docs pilot: fetched-then-
                # discarded binaries whose ONLY artifact is the text sidecar) wins
                # over the stem-named text/ sidecar convention.
                tp = (r.get("text_path") or "").strip()
                if tp:
                    rel = tp if tp.startswith(dataset + "/") else "%s/%s" % (dataset, tp)
                    if os.path.exists(os.path.join(ROOT, c.dir, rel)):
                        has_text, tpath = 1, rel
                    else:
                        has_text, tpath = 0, None
                else:
                    has_text, tpath = text_sidecar(c.dir, dataset, path)
                add(c.slug,
                    first(r, "packet_kind" if dataset == "packets" else "doc_type")
                    or default_type, dataset,
                    first(r, "date"), first(r, "body") or "",
                    first(r, "title"), path, first(r, "format"),
                    has_text, tpath, first(r, "source_url", "video_url"),
                    doc_class=(r.get("doc_class") or "").strip() or None)
    # non-city entities (counties/regional/state): minutes live under module dirs
    # (legislative/land_use/agencies), indexed by minutes_index.csv (md_path column).
    # meeting.source_file already stores that md_path, so linkage is an exact match.
    for e in ENTITIES:
        if e.level == "city" or not e.dir:
            continue
        for module in NONCITY_MINUTES_MODULES:
            for r in read_csv(os.path.join(ROOT, e.dir, module, "minutes_index.csv")):
                # canonical column is md_path; tolerate the Phase-5 variants
                # (mag legislative uses minutes_md; summit legislative uses a
                # module-relative `path`) so no entity's minutes silently skip
                # federation. Module-relative values get the module prefix.
                p = (r.get("md_path") or r.get("minutes_md")
                     or (r.get("path") if str(r.get("path", "")).endswith(".md")
                         else "") or "")
                if not p:
                    continue
                if not p.startswith(module + "/"):
                    p = module + "/" + p
                # try the normalized (module-prefixed) key, then the raw value
                # (summit's db stores module-relative source_file paths)
                raw = (r.get("md_path") or r.get("minutes_md")
                       or r.get("path") or "")
                mid = meet.get((e.slug, p)) or meet.get((e.slug, raw))
                minutes_total += 1
                minutes_linked += 1 if mid else 0
                # has_text must reflect the BODY, not the file's existence — 2026-07-26
                # (audit S5). A front-matter-only stub or "[SCANNED … DEFERRED]" placeholder
                # is catalogued but not readable, and claiming otherwise overstated the
                # repo's searchable coverage.
                _abs = os.path.join(ROOT, e.dir, p) if p else ""
                _ht = 1 if (_abs and os.path.exists(_abs) and readable(_abs)) else 0
                add(e.slug, "minutes", module, r.get("date"), r.get("body") or "",
                    r.get("body") or "", p, "md", _ht, p if _ht else None,
                    r.get("source_url"), mid)

    # county plans (general/township/MIHP) — catalogued with their text sidecar as the
    # searchable artifact (path = the .txt so build_fts indexes it).
    for e in ENTITIES:
        if e.level == "city" or not e.dir:
            continue
        for r in read_csv(os.path.join(ROOT, e.dir, "plans", "index.csv")):
            tp = r.get("text_path") or ""
            # the plans index stores text_path module-relative ("text/x.txt"); make it
            # county-dir-relative ("plans/text/x.txt") so build_fts resolves it.
            if tp and not tp.startswith("plans/"):
                tp = "plans/" + tp
            add(e.slug, "plan", "plans", first(r, "adopted_date", "date"), "",
                first(r, "title"), tp or first(r, "path"), first(r, "format") or "txt",
                1 if tp else 0, tp, first(r, "source_url"))
        # county packets/staff reports — dataset='packets' so they flow into fts_packet
        # (doc_class carried since the 2026-07-17 county §9 backfill — same semantics
        # as the city loop above)
        for r in read_csv(os.path.join(ROOT, e.dir, "packets", "index.csv")):
            tp = r.get("text_path") or ""
            add(e.slug, first(r, "packet_kind") or "packet", "packets", first(r, "date"),
                first(r, "body"), first(r, "title"), first(r, "path") or tp,
                first(r, "format") or "pdf", 1 if tp else 0, tp, first(r, "source_url"),
                doc_class=(r.get("doc_class") or "").strip() or None)
        # state-tier searchable corpora (2026-07-20 Phase 5): Ombudsman advisory
        # opinions + LUDMA statutes. The text sidecar is the searchable artifact
        # (plans pattern); paths in the module indexes are module-relative.
        for module, dtype in (("advisory_opinions", "advisory_opinion"),
                              ("statutes", "statute")):
            for r in read_csv(os.path.join(ROOT, e.dir, module, "index.csv")):
                tp = r.get("text_path") or r.get("path") or ""
                if tp and not tp.startswith(module + "/"):
                    tp = module + "/" + tp
                title = first(r, "title", "heading") or first(r, "section", "opinion_no")
                add(e.slug, dtype, module, first(r, "date", "retrieved_date"),
                    first(r, "jurisdiction", "chapter"), title,
                    tp, "txt" if tp.endswith(".txt") else "pdf",
                    1 if tp.endswith(".txt") else 0,
                    tp if tp.endswith(".txt") else "",
                    first(r, "source_url"),
                    doc_class=(r.get("doc_class") or "").strip() or None)

    # ordinances enter document from the ordinance table (already canonical)
    for city, ono, date, title, path, fmt, has_text, tpath, url in out.execute(
            "SELECT city, ordinance_no, adoption_date, title, path, format, "
            "has_text, text_path, source_url FROM ordinance"):
        add(city, "ordinance", "ordinances", date, "", title or ono, path, fmt,
            has_text, tpath, url)
    return counts, minutes_total, minutes_linked


def load_roster(out):
    """Union each rostered city's council_terms / district_versions /
    district_precincts CSVs into term / district_version / district_precinct.
    Cities without a roster/ dir are skipped gracefully. The CSVs already carry a
    leading `city` column, kept verbatim."""
    specs = [("roster/council_terms.csv", "term", TERM_COLUMNS),
             ("roster/district_versions.csv", "district_version", DISTRICT_COLUMNS),
             ("roster/district_precincts.csv", "district_precinct", PRECINCT_COLUMNS)]
    counts = {t: 0 for _, t, _ in specs}
    by_city = {}
    for c in CITIES:
        if not os.path.isdir(os.path.join(ROOT, c.dir, "roster")):
            continue
        for fname, table, cols in specs:
            rows = read_csv(os.path.join(ROOT, c.dir, fname))
            for r in rows:
                out.execute("INSERT INTO %s VALUES (%s)"
                            % (table, ",".join("?" * len(cols))),
                            [r.get(k) for k in cols])
            counts[table] += len(rows)
            by_city.setdefault(c.slug, {})[table] = by_city.get(c.slug, {}).get(table, 0) + len(rows)
    return counts, by_city


def build_fts(out):
    # fts_minutes — full text of every minutes markdown file on disk that HAS text.
    # G5 (2026-07-31): doc_type 'pmn_minutes' is now INDEXED — 935 text-bearing
    # recovered-minutes docs (provo 391, murray 80, vineyard 80, herriman 72, …)
    # were silently absent from the advertised keyword workflow. To avoid indexing
    # the same MEETING twice, a pmn_minutes doc is skipped when an indexed 'minutes'
    # doc exists for the same (city, date, body) — the promoted-copy case. Same-date
    # docs with a DIFFERENT body label are both indexed (a council and a PC can meet
    # the same evening); the `dataset` column keeps the pmn_backfill origin visible.
    n_files = 0
    n_skipped_empty = 0
    n_pmn = 0
    n_pmn_dup = 0
    n_short_statute = 0
    for city, dataset, date, path, text_path, body, doc_type in out.execute(
            "SELECT city, dataset, date, path, text_path, body, doc_type "
            "FROM document WHERE doc_type IN ('minutes','plan',"
            "'advisory_opinion','statute','pmn_minutes')").fetchall():
        # pmn_minutes rows catalog the raw PDF in `path`; the readable artifact
        # is the extracted `text_path` sidecar — index that.
        if doc_type == "pmn_minutes":
            path = text_path
        if not path:
            # link-only catalog rows (e.g. a StoryMap-only general plan) have no
            # on-disk artifact to index — legitimate, not an error.
            continue
        if not path.endswith((".md", ".txt")):
            # only real text artifacts are indexable — a row whose only on-disk
            # form is a scanned/image PDF (e.g. an OCR-failed advisory opinion)
            # stays catalogued in `document` but out of FTS (binary junk guard).
            continue
        if doc_type == "pmn_minutes":
            twin = out.execute(
                "SELECT 1 FROM document WHERE doc_type='minutes' AND city=? "
                "AND date=? AND body=? LIMIT 1", (city, date, body)).fetchone()
            if twin:
                n_pmn_dup += 1
                continue
        cdir = ENT_DIR[city]
        fp = os.path.join(ROOT, cdir, path)
        if not os.path.exists(fp):
            continue
        # statutes get a 40-char floor: short sections are legitimate law text
        min_body = 40 if doc_type == "statute" else 200
        if not readable(fp, min_body=min_body):
            # 2026-07-26 (audit S5): a front-matter-only stub or "[SCANNED … DEFERRED]"
            # placeholder has nothing to match on. Indexing it inflated the corpus figure
            # and made a keyword sweep look like it had covered the document.
            if doc_type == "statute":
                n_short_statute += 1
                print(f"  fts_minutes: statute below even the 40-char floor, "
                      f"SKIPPED (honest gap): {city}/{path}")
            n_skipped_empty += 1
            continue
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = f.read()
        out.execute("INSERT INTO fts_minutes (text,city,dataset,date,path) "
                    "VALUES (?,?,?,?,?)", (text, city, dataset, date, path))
        n_files += 1
        if doc_type == "pmn_minutes":
            n_pmn += 1
    print(f"  fts_minutes: pmn_minutes indexed {n_pmn} "
          f"(skipped {n_pmn_dup} same-(city,date,body) duplicates of indexed minutes)")
    # external-content indexes rebuild straight from their tables
    out.execute("INSERT INTO fts_motion(fts_motion) VALUES('rebuild')")
    out.execute("INSERT INTO fts_comment(fts_comment) VALUES('rebuild')")
    # fts_ordinance — title per ordinance; sidecar text once per distinct file
    seen = set()
    n_ord = 0
    for city, ono, title, tpath in out.execute(
            "SELECT city, ordinance_no, title, text_path FROM ordinance").fetchall():
        text = ""
        if tpath and (city, tpath) not in seen:
            cdir = ENT_DIR[city]
            fp = os.path.join(ROOT, cdir, tpath)
            if os.path.exists(fp):
                with open(fp, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                seen.add((city, tpath))
        out.execute("INSERT INTO fts_ordinance (title,text,city,ordinance_no,"
                    "text_path) VALUES (?,?,?,?,?)",
                    (title or "", text, city, ono, tpath))
        n_ord += 1
    # fts_packet — staff-report/agenda text sidecars (scripts/extract_packet_text.py)
    n_pkt = 0
    for city, date, kind, dclass, title, tpath in out.execute(
            "SELECT city, date, doc_type, doc_class, title, text_path FROM document "
            "WHERE dataset='packets' AND has_text=1 AND text_path IS NOT NULL"
            ).fetchall():
        cdir = ENT_DIR[city]
        fp = os.path.join(ROOT, cdir, tpath)
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = f.read()
        out.execute("INSERT INTO fts_packet (title,text,city,date,packet_kind,"
                    "doc_class,text_path) VALUES (?,?,?,?,?,?,?)",
                    (title or "", text, city, date, kind, dclass, tpath))
        n_pkt += 1
    if n_skipped_empty:
        log("  fts_minutes        %6d empty/placeholder docs EXCLUDED (no body text)" % n_skipped_empty)
    return n_files, n_ord, n_pkt


def main():
    if not os.path.exists(DB):
        sys.exit("cities.db not found — run scripts/build_cities_db.py first")
    out = sqlite3.connect(DB)
    out.executescript(DDL)

    log("Search layer (scripts/build_search_layer.py):")
    n_comments = load_comments(out)
    log("  comment            %6d rows (%s)" % (
        sum(n_comments.values()),
        ", ".join("%s %d" % (k, v) for k, v in sorted(
            n_comments.items(), key=lambda kv: -kv[1]) if v)))
    cf_counts, n_cand, n_matched = load_cf(out)
    for t in ("cf_filing", "cf_contribution", "cf_expenditure", "cf_cycle"):
        log("  %-18s %6d rows" % (t, cf_counts[t]))
    log("  cf_candidate_person %5d candidates, %d matched to person (exact "
        "name-key; unmatched stay NULL)" % (n_cand, n_matched))
    n_ord, n_res, n_amb = load_ordinances(out)
    log("  ordinance          %6d rows (%d resolved to a motion_id, %d ambiguous "
        "— never forced)" % (n_ord, n_res, n_amb))
    doc_counts, mt, ml = load_documents(out)
    log("  document           %6d rows (%s)" % (
        sum(doc_counts.values()),
        ", ".join("%s %d" % (k, v) for k, v in sorted(
            doc_counts.items(), key=lambda kv: -kv[1]))))
    log("  minutes→meeting link: %d/%d (%.1f%%)" % (ml, mt, 100.0 * ml / mt))
    roster_counts, roster_by_city = load_roster(out)
    log("  roster (term / district_version / district_precinct): %s"
        % ", ".join("%s %d" % (t, roster_counts[t])
                    for t in ("term", "district_version", "district_precinct")))
    log("         cities with a roster/ dir: %s"
        % (", ".join("%s(%s)" % (slug, "/".join(
            str(roster_by_city[slug].get(t, 0))
            for t in ("term", "district_version", "district_precinct")))
            for slug in sorted(roster_by_city)) or "none"))
    n_files, n_ford, n_pkt = build_fts(out)
    log("  fts_minutes        %6d files indexed" % n_files)
    log("  fts_motion / fts_comment rebuilt from motion / comment")
    log("  fts_ordinance      %6d rows indexed" % n_ford)
    log("  fts_packet         %6d packet text sidecars indexed" % n_pkt)

    # reconciliation: db rows must equal source csv rows exactly
    checks = [
        ("comment", sum(n_comments.values())),
        ("cf_filing", cf_counts["cf_filing"]),
        ("cf_contribution", cf_counts["cf_contribution"]),
        ("cf_expenditure", cf_counts["cf_expenditure"]),
        ("cf_cycle", cf_counts["cf_cycle"]),
        ("ordinance", n_ord),
        ("term", roster_counts["term"]),
        ("district_version", roster_counts["district_version"]),
        ("district_precinct", roster_counts["district_precinct"]),
    ]
    for table, expect in checks:
        got = out.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
        if got != expect:
            sys.exit("RECONCILIATION FAIL: %s has %d rows, loaded %d"
                     % (table, got, expect))
    out.execute("DELETE FROM build_info WHERE key LIKE 'search:%'")
    info = [("search:built_by", "scripts/build_search_layer.py"),
            ("search:fts_minutes_files", str(n_files)),
            ("search:minutes_meeting_link",
             "%d/%d" % (ml, mt))] + \
           [("search:rows:%s" % t, str(v)) for t, v in checks]
    out.executemany("INSERT INTO build_info VALUES (?,?)", info)
    out.commit()
    out.close()
    log("Search layer done (reconciliation exact).")


if __name__ == "__main__":
    main()
