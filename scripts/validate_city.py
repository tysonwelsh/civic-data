#!/usr/bin/env python3
"""validate_city.py — check a city directory against SCHEMA_SPEC.md.

Usage: python3 scripts/validate_city.py <city>_city_council/ [--quiet]

Validation only — never mutates data. Stdlib only.

Checks (letters match SCHEMA_SPEC.md §9 / REMEDIATION_PLAN.md 2.1):
  a. standard layout presence (WARN on missing optional datasets)
  b. all_votes.csv header conformance (13-column standard)
  c. vote-value vocabulary
  d. minutes_index.csv header + paths exist + dates parse/plausible
  e. all_votes.csv source paths exist
  f. tally-vs-member-row consistency rate (reported, soft threshold)
  g. motions_std.csv contract conformance (only if present)
  h. db presence + named-row reconciliation (honors db/vote_overrides.csv)
  i. weeks/ freshness + weekly row sums vs flat totals
  j. per-city council-vote validator (meeting_minutes/validate_votes.py) present + runs
     clean (plan item 3.1; the script writes its own detailed report)

Exit code: number of FAILs (0 = clean; WARNs never affect exit code).
"""
import csv
import datetime
import os
import re
import sqlite3
import sys

VOTE_COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
             "result", "mover", "seconder", "member", "vote", "source"]
INDEX_COLS = ["date", "year", "title", "slug", "path", "source", "source_url", "format"]
VOTE_VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}
# Documented city extensions (SCHEMA_SPEC.md §2) — tolerated with a WARN, not a FAIL.
VOTE_VALUE_EXTENSIONS = {"Nay (Mayor tie-break)",   # park_city; split to Nay+note in its db
                         "Aye (Mayor tie-break)"}   # riverton; normalized to Aye in its db

MOTIONS_STD_COLS = ["source", "motion_no", "date", "body", "motion_type_native",
                    "motion_type_std", "land_use_type", "action_class", "outcome",
                    "tally_aye", "tally_nay", "tally_other", "vote_mode", "result_raw",
                    "classify_method", "classify_confidence"]
MOTION_TYPE_STD = {"Land-Use", "Ordinance", "Resolution", "Budget", "Appointment",
                   "Contract-Purchase", "Grant-Funding", "Interlocal", "Ceremonial",
                   "Procedural-Administrative", "Public-Hearing", "Legislative-Intent",
                   "Other"}
LAND_USE_TYPE = {"Rezone", "Text-Amendment", "General-Plan-Amendment", "Subdivision-Plat",
                 "Conditional-Use", "Site-Plan-Design-Review", "Vacation", "Annexation",
                 "Variance-Exception", "Development-Agreement", "Other-Land-Use", ""}
ACTION_CLASS = {"recommendation", "final-action", "procedural"}
OUTCOME = {"pass", "fail", "died", "withdrawn", "unknown"}
VOTE_MODE = {"roll-call", "voice", "unanimous-declared", "tally-only", "unknown"}
CLASSIFY_CONF = {"high", "medium", "low"}

DATE_MIN = datetime.date(2000, 1, 1)
DATE_MAX = datetime.date.today() + datetime.timedelta(days=60)

VOTE_DATASETS = ["meeting_minutes", "planning_commission"]


class Report:
    def __init__(self, quiet=False):
        self.rows = []          # (status, check, message)
        self.quiet = quiet

    def add(self, status, check, message):
        self.rows.append((status, check, message))

    def emit(self, city):
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        print(f"\n=== {city} ===")
        for status, check, message in self.rows:
            counts[status] += 1
            if self.quiet and status == "PASS":
                continue
            print(f"[{status:4}] {check}: {message}")
        print(f"--- {counts['PASS']} PASS / {counts['WARN']} WARN / {counts['FAIL']} FAIL")
        return counts["FAIL"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows = [dict(zip(header, r)) for r in reader]
    return header, rows


def resolve_path(city_dir, dataset_dir, rel):
    """Paths in CSVs are relative either to the city root or the dataset dir."""
    for base in (city_dir, dataset_dir):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    return None


def parse_date(s):
    try:
        return datetime.date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------- a. layout
def check_layout(city_dir, rep):
    core = ["meeting_minutes/all_votes.csv", "meeting_minutes/minutes_index.csv",
            "meeting_minutes/minutes"]
    optional = ["planning_commission/all_votes.csv",
                "public_comments/all_comments_clean.csv",
                "election_results", "db", "geo", "weeks",
                "README.md", "CLAUDE.md", "recon.md", "VERIFICATION.md",
                "build_weeks.py", "planning_commission/minutes_index.csv"]
    missing_core = [p for p in core if not os.path.exists(os.path.join(city_dir, p))]
    missing_opt = [p for p in optional if not os.path.exists(os.path.join(city_dir, p))]
    if missing_core:
        rep.add("FAIL", "a.layout", f"missing CORE: {', '.join(missing_core)}")
    else:
        rep.add("PASS", "a.layout", "core layout present")
    if missing_opt:
        rep.add("WARN", "a.layout", f"missing optional: {', '.join(missing_opt)}")
    else:
        rep.add("PASS", "a.layout", "all standard optional components present")


# ------------------------------------------------------- b. vote headers
def check_vote_headers(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if not os.path.exists(path):
            continue
        header, _ = read_csv(path)
        if header == VOTE_COLS:
            rep.add("PASS", f"b.header[{ds}]", "standard 13-column schema")
        elif set(VOTE_COLS) <= set(header):
            extras = [c for c in header if c not in VOTE_COLS]
            note = f"extra cols {extras}" if extras else "column order differs"
            rep.add("WARN", f"b.header[{ds}]",
                    f"all 13 standard columns present; {note} (documented extension)")
        else:
            missing = [c for c in VOTE_COLS if c not in header]
            rep.add("FAIL", f"b.header[{ds}]", f"missing standard columns: {missing}")


# ------------------------------------------------------- c. vote vocabulary
def check_vote_vocab(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if not os.path.exists(path):
            continue
        _, rows = read_csv(path)
        bad, ext, blank_named = {}, {}, 0
        for r in rows:
            v = r.get("vote", "")
            if v in VOTE_VOCAB:
                continue
            if v == "":
                if r.get("member", ""):
                    blank_named += 1     # named member with no vote value
                continue                  # blank member+vote = tally-only row (spec §2)
            if v in VOTE_VALUE_EXTENSIONS:
                ext[v] = ext.get(v, 0) + 1
            else:
                bad[v] = bad.get(v, 0) + 1
        if bad:
            rep.add("FAIL", f"c.vocab[{ds}]", f"values outside vocabulary: {bad}")
        elif ext:
            rep.add("WARN", f"c.vocab[{ds}]", f"documented extension values: {ext}")
        else:
            rep.add("PASS", f"c.vocab[{ds}]", f"{len(rows)} rows within vocabulary")
        if blank_named:
            rep.add("WARN", f"c.vocab[{ds}]",
                    f"{blank_named} rows with a named member but blank vote")


# ------------------------------------------------------- d. minutes_index
def check_minutes_index(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "minutes_index.csv")
        if not os.path.exists(path):
            continue
        dataset_dir = os.path.join(city_dir, ds)
        header, rows = read_csv(path)
        date_col, path_col = "date", "path"
        if header[:len(INDEX_COLS)] == INDEX_COLS:
            extras = header[len(INDEX_COLS):]
            if extras:
                rep.add("WARN", f"d.index[{ds}]",
                        f"standard header + extra cols {extras} (documented extension)")
            else:
                rep.add("PASS", f"d.index[{ds}]", "standard header")
        elif set(INDEX_COLS) <= set(header):
            rep.add("WARN", f"d.index[{ds}]", "standard columns present, order differs")
        elif "meeting_date" in header and "file" in header:
            # pre-retrofit legacy schema (slc PC): meeting_date/file for date/path
            date_col, path_col = "meeting_date", "file"
            rep.add("WARN", f"d.index[{ds}]",
                    f"legacy (pre-standard) header {header} — checking via "
                    f"meeting_date/file; migrate to the standard schema")
        else:
            missing = [c for c in INDEX_COLS if c not in header]
            rep.add("FAIL", f"d.index[{ds}]", f"missing columns: {missing}")
            continue
        missing_paths, bad_dates, year_mismatch = [], [], 0
        for r in rows:
            if not resolve_path(city_dir, dataset_dir, r.get(path_col, "")):
                missing_paths.append(r.get(path_col, ""))
            d = parse_date(r.get(date_col, ""))
            if d is None or not (DATE_MIN <= d <= DATE_MAX):
                bad_dates.append(r.get(date_col, ""))
            elif r.get("year", "") and str(d.year) != r["year"].strip():
                year_mismatch += 1
        if missing_paths:
            rep.add("FAIL", f"d.index[{ds}]",
                    f"{len(missing_paths)}/{len(rows)} indexed paths missing "
                    f"(e.g. {missing_paths[0]})")
        else:
            rep.add("PASS", f"d.index[{ds}]", f"{len(rows)} indexed paths all exist")
        if bad_dates:
            rep.add("FAIL", f"d.index[{ds}]",
                    f"{len(bad_dates)} unparseable/implausible dates (e.g. {bad_dates[0]!r})")
        else:
            rep.add("PASS", f"d.index[{ds}]", "all dates parse and are plausible")
        if year_mismatch:
            rep.add("WARN", f"d.index[{ds}]", f"{year_mismatch} rows where year != date's year")


# ------------------------------------------------------- e. vote source paths
def check_vote_sources(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if not os.path.exists(path):
            continue
        dataset_dir = os.path.join(city_dir, ds)
        _, rows = read_csv(path)
        sources = sorted({r.get("source", "") for r in rows})
        missing, nonfile = [], []
        for s in sources:
            if resolve_path(city_dir, dataset_dir, s):
                continue
            # non-path provenance like "db/staging (Legistar EventItemVote, body 140)"
            base = s.split(" (")[0]
            if resolve_path(city_dir, dataset_dir, base):
                nonfile.append(s)
            else:
                missing.append(s)
        if missing:
            rep.add("FAIL", f"e.sources[{ds}]",
                    f"{len(missing)}/{len(sources)} source paths missing (e.g. {missing[0]})")
        else:
            note = f" ({len(nonfile)} as non-file provenance)" if nonfile else ""
            rep.add("PASS", f"e.sources[{ds}]",
                    f"{len(sources)} distinct source refs resolve{note}")
        if nonfile:
            rep.add("WARN", f"e.sources[{ds}]",
                    f"non-file provenance strings (documented): {nonfile[:2]}")


# ------------------------------------------------------- f. tally consistency
TALLY_RE = re.compile(r"\b(\d+)\s*[-:–]\s*(\d+)\b")


def check_tally_consistency(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if not os.path.exists(path):
            continue
        _, rows = read_csv(path)
        motions = {}
        for r in rows:
            # date included: (source, motion_no) alone is degenerate in sandy PC
            key = (r.get("source", ""), r.get("motion_no", ""), r.get("date", ""))
            m = motions.setdefault(key, {"result": r.get("result", ""), "Aye": 0,
                                         "Nay": 0, "named": 0})
            if r.get("member", ""):
                m["named"] += 1
                if r.get("vote") in ("Aye", "Nay"):
                    m[r["vote"]] += 1
        checked = matched = 0
        for m in motions.values():
            if m["named"] == 0:
                continue
            t = TALLY_RE.search(m["result"])
            if not t:
                continue
            a, b = int(t.group(1)), int(t.group(2))
            checked += 1
            if (m["Aye"], m["Nay"]) in ((a, b), (b, a)):
                matched += 1
        if checked == 0:
            rep.add("PASS", f"f.tally[{ds}]",
                    "no motions with both a parseable N-M tally and named rows (nothing to check)")
            continue
        rate = matched / checked
        msg = f"{matched}/{checked} named-roll-call tallies match result string ({rate:.1%})"
        if rate >= 0.90:
            rep.add("PASS", f"f.tally[{ds}]", msg)
        else:
            rep.add("WARN", f"f.tally[{ds}]", msg + " — known source quirks may apply")


# ------------------------------------------------------- g. motions_std.csv
def check_motions_std(city_dir, rep):
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "motions_std.csv")
        if not os.path.exists(path):
            continue   # normalization layer not built yet — tolerated silently
        header, rows = read_csv(path)
        if header != MOTIONS_STD_COLS:
            rep.add("FAIL", f"g.std[{ds}]",
                    f"header does not match the normalization contract: {header}")
            continue
        votes_path = os.path.join(city_dir, ds, "all_votes.csv")
        vote_keys = set()
        degenerate = False
        if os.path.exists(votes_path):
            _, vrows = read_csv(votes_path)
            # Is (source, motion_no) a real motion key here? Not in sandy PC, where
            # `source` is one constant provenance string (documented limitation) —
            # fall back to (source, motion_no, date).
            dates_per_key = {}
            for r in vrows:
                dates_per_key.setdefault((r.get("source", ""), r.get("motion_no", "")),
                                         set()).add(r.get("date", ""))
            degenerate = any(len(v) > 1 for v in dates_per_key.values())
            if degenerate:
                vote_keys = {(r.get("source", ""), r.get("motion_no", ""), r.get("date", ""))
                             for r in vrows}
            else:
                vote_keys = set(dates_per_key)
        bad_enum = {}
        orphan = 0
        seen = set()
        dup = 0
        for r in rows:
            for col, allowed in (("motion_type_std", MOTION_TYPE_STD),
                                 ("land_use_type", LAND_USE_TYPE),
                                 ("action_class", ACTION_CLASS),
                                 ("outcome", OUTCOME),
                                 ("vote_mode", VOTE_MODE),
                                 ("classify_confidence", CLASSIFY_CONF)):
                if r[col] not in allowed:
                    bad_enum.setdefault(col, set()).add(r[col])
            if r["land_use_type"] and r["motion_type_std"] != "Land-Use":
                bad_enum.setdefault("land_use_type(non-Land-Use)", set()).add(r["land_use_type"])
            if not (r["classify_method"].startswith("rule:")
                    or r["classify_method"] in ("crosswalk", "manual")):
                bad_enum.setdefault("classify_method", set()).add(r["classify_method"])
            for col in ("tally_aye", "tally_nay", "tally_other"):
                if r[col] and not r[col].isdigit():
                    bad_enum.setdefault(col, set()).add(r[col])
            key = ((r["source"], r["motion_no"], r["date"]) if degenerate
                   else (r["source"], r["motion_no"]))
            if key in seen:
                dup += 1
            seen.add(key)
            if vote_keys and key not in vote_keys:
                orphan += 1
        if bad_enum:
            rep.add("FAIL", f"g.std[{ds}]",
                    "enum violations: " + "; ".join(f"{k}={sorted(v)[:3]}" for k, v in bad_enum.items()))
        elif orphan or dup:
            rep.add("FAIL", f"g.std[{ds}]",
                    f"{orphan} rows not joinable to all_votes.csv; {dup} duplicate motion keys")
        elif degenerate:
            rep.add("WARN", f"g.std[{ds}]",
                    f"{len(rows)} rows conform, but (source,motion_no) is degenerate in "
                    f"this dataset's all_votes.csv (documented — e.g. sandy PC's constant "
                    f"provenance string); joined on (source,motion_no,date) instead")
        else:
            rep.add("PASS", f"g.std[{ds}]", f"{len(rows)} rows conform to the contract")


# ------------------------------------------------------- h. db reconciliation
def check_db(city_dir, rep):
    db_dir = os.path.join(city_dir, "db")
    if not os.path.isdir(db_dir):
        rep.add("WARN", "h.db", "no db/ directory")
        return
    dbs = [f for f in os.listdir(db_dir) if f.endswith(".db")]
    if not dbs:
        rep.add("WARN", "h.db", "db/ present but no .db file")
        return
    db_path = os.path.join(db_dir, sorted(dbs)[0])
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        db_votes = conn.execute("SELECT COUNT(*) FROM vote").fetchone()[0]
        db_motions = conn.execute("SELECT COUNT(*) FROM motion").fetchone()[0]
        conn.close()
    except sqlite3.Error as e:
        rep.add("FAIL", "h.db", f"cannot read {dbs[0]}: {e}")
        return
    csv_named = 0
    dup_member_rows = 0
    member_keys = set()
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if os.path.exists(path):
            _, rows = read_csv(path)
            seen = {}
            for r in rows:
                if r.get("member", ""):
                    csv_named += 1
                    key = (r.get("source", ""), r.get("motion_no", ""),
                           r.get("date", ""), r["member"])
                    if key in seen:
                        dup_member_rows += 1
                    seen[key] = True
                    member_keys.add((r.get("source", ""),
                                     str(r.get("motion_no", "")).strip(),
                                     " ".join(r["member"].split()).lower()))
    # vote_overrides.csv rows come in two kinds (db_build_lib 2026-07-17):
    #   conflict-resolution — the member HAS CSV rows (a contradictory pair the db
    #     collapses to one vote): each such row means one fewer db vote than CSV rows;
    #   add-member — the member has NO CSV row (garbled source value the extractor
    #     honestly skipped): the build ADDS a db vote the CSV doesn't carry.
    overrides = add_overrides = 0
    ov_path = os.path.join(db_dir, "vote_overrides.csv")
    if os.path.exists(ov_path):
        _, ov_rows = read_csv(ov_path)
        for r in ov_rows:
            mk = (r.get("source_file", ""), str(r.get("motion_no", "")).strip(),
                  " ".join(r.get("member", "").split()).lower())
            if mk in member_keys:
                overrides += 1
            else:
                add_overrides += 1
    expected = db_votes + overrides - add_overrides
    delta = csv_named - expected
    detail = (f"CSV named rows {csv_named} vs db votes {db_votes}"
              + (f" + {overrides} documented overrides" if overrides else "")
              + (f" - {add_overrides} add-member overrides" if add_overrides else "")
              + f" (delta {delta:+d}); {db_motions} motions")
    if delta == 0:
        rep.add("PASS", "h.db", "reconciles exactly — " + detail)
    elif delta == dup_member_rows:
        rep.add("WARN", "h.db",
                f"delta fully explained by {dup_member_rows} duplicate "
                f"(source,motion_no,member) rows in the CSVs, collapsed by the db's "
                f"(motion_id,person_id) UNIQUE — " + detail)
    elif abs(delta) <= max(10, int(0.01 * csv_named)):
        rep.add("WARN", "h.db", "small reconciliation delta — " + detail)
    else:
        rep.add("FAIL", "h.db", "reconciliation mismatch — " + detail)


# ------------------------------------------------------- i. weeks
def check_weeks(city_dir, rep):
    weeks_dir = os.path.join(city_dir, "weeks")
    if not os.path.isdir(weeks_dir):
        rep.add("WARN", "i.weeks", "no weeks/ directory")
        return
    # freshness: canonical CSV mtimes vs newest weeks artifact
    canon = []
    for relpath in ("meeting_minutes/all_votes.csv", "public_comments/all_comments_clean.csv"):
        p = os.path.join(city_dir, relpath)
        if os.path.exists(p):
            canon.append((relpath, os.path.getmtime(p)))
    weeks_mtime = 0.0
    for root, _dirs, files in os.walk(weeks_dir):
        for f in files:
            weeks_mtime = max(weeks_mtime, os.path.getmtime(os.path.join(root, f)))
    stale = [rel for rel, m in canon if m > weeks_mtime]
    if stale:
        rep.add("WARN", "i.weeks",
                f"canonical CSV(s) newer than every weeks/ file (stale?): {stale}")
    else:
        rep.add("PASS", "i.weeks", "weeks/ not older than canonical CSVs")
    # row sums
    def week_sum(name):
        total, found = 0, False
        for entry in os.listdir(weeks_dir):
            p = os.path.join(weeks_dir, entry, name)
            if os.path.isfile(p):
                found = True
                with open(p, newline="", encoding="utf-8") as f:
                    total += max(0, sum(1 for _ in csv.reader(f)) - 1)
        return total, found
    votes_path = os.path.join(city_dir, "meeting_minutes/all_votes.csv")
    if os.path.exists(votes_path):
        _, rows = read_csv(votes_path)
        wsum, found = week_sum("votes.csv")
        if not found:
            rep.add("WARN", "i.weeks", "no weeks/*/votes.csv files found")
        elif wsum == len(rows):
            rep.add("PASS", "i.weeks", f"weekly votes sum {wsum} == flat total")
        else:
            rep.add("FAIL", "i.weeks", f"weekly votes sum {wsum} != flat total {len(rows)}")
    comments_path = os.path.join(city_dir, "public_comments/all_comments_clean.csv")
    if os.path.exists(comments_path):
        _, crows = read_csv(comments_path)
        wsum, found = week_sum("comments.csv")
        if len(crows) == 0 and not found:
            rep.add("PASS", "i.weeks", "no comments corpus; no weekly comments files (consistent)")
        elif wsum == len(crows):
            rep.add("PASS", "i.weeks", f"weekly comments sum {wsum} == flat total")
        else:
            rep.add("FAIL", "i.weeks", f"weekly comments sum {wsum} != flat total {len(crows)}")


# -------------------------------------------- k. expansion contracts (SCHEMA_SPEC §9)
EXPANSION_CONTRACTS = {
    "packets": ["date", "title", "body", "meeting_type", "packet_kind",
                "source_url", "retrieved_date", "format", "extraction_method",
                "path"],
    "housing_plans": ["date", "title", "doc_type", "source_url", "retrieved_date",
                      "format", "extraction_method", "path", "pages", "repository",
                      "notes"],
    "ordinances": ["ordinance_no", "adoption_date", "date", "title", "source_url",
                   "retrieved_date", "format", "extraction_method", "path",
                   "land_use", "result", "matched_motion_date",
                   "matched_motion_no", "match_confidence"],
    "pmn_backfill": ["date", "year", "title", "slug", "body", "path", "source",
                     "source_url", "notice_url", "pmn_body_id", "pmn_file_id",
                     "retrieved_date", "format", "extraction_method"],
    "transcripts": ["date", "title", "body", "video_url", "video_id",
                    "caption_type", "source_url", "retrieved_date", "format",
                    "extraction_method", "path"],
    "campaign_finance": ["date", "candidate", "office", "election_year",
                         "filing_type", "reporting_period", "title", "source_url",
                         "retrieved_date", "format", "extraction_method", "path"],
}


def check_expansion_contracts(city_dir, rep):
    """k. every present expansion dataset's index.csv starts with its §9 contract
    header (adopted 2026-07-06). Absence of a dataset is expected (WARN only when
    the dir exists but has no index)."""
    bad, ok_n = [], 0
    for ds, contract in EXPANSION_CONTRACTS.items():
        ds_dir = os.path.join(city_dir, ds)
        if not os.path.isdir(ds_dir):
            continue
        idx = os.path.join(ds_dir, "index.csv")
        if not os.path.exists(idx):
            rep.add("WARN", "k.expansion", f"{ds}/ exists but has no index.csv")
            continue
        header, _ = read_csv(idx)
        if header[:len(contract)] == contract:
            ok_n += 1
        else:
            bad.append(ds)
    if bad:
        rep.add("FAIL", "k.expansion",
                f"index.csv does not start with the SCHEMA_SPEC §9 contract header: "
                f"{', '.join(bad)}")
    elif ok_n:
        rep.add("PASS", "k.expansion",
                f"{ok_n} expansion index.csv files match the §9 contracts")


# -------------------------------------------- m. election races superset (§9)
RACES_CONTRACT = ["year", "election_type", "office", "district", "contest",
                  "contest_verbatim", "n_seats", "n_candidates", "voting_method",
                  "total_votes", "total_first_choice_votes", "winner",
                  "winner_votes", "winner_pct", "runner_up", "runner_up_votes",
                  "margin_votes", "margin_pct", "registered_voters", "ballots_cast",
                  "turnout_pct", "uncontested", "suppressed_precincts", "note",
                  "source_file"]


def check_races_schema(city_dir, rep):
    """m. <slug>_races.csv exists under the slug-consistent name and starts with the
    25-col superset header (SCHEMA_SPEC §9, adopted 2026-07-07)."""
    slug = os.path.basename(os.path.abspath(city_dir)).replace("_city_council", "")
    p = os.path.join(city_dir, "election_results", f"{slug}_races.csv")
    if not os.path.exists(p):
        rep.add("FAIL", "m.elections",
                f"election_results/{slug}_races.csv missing (slug-consistent name "
                "required since 2026-07-07)")
        return
    header, _ = read_csv(p)
    if header[:len(RACES_CONTRACT)] == RACES_CONTRACT:
        rep.add("PASS", "m.elections", "races.csv matches the 25-col superset")
    else:
        rep.add("FAIL", "m.elections",
                f"races.csv header deviates from the §9 superset: {header[:8]}...")


# -------------------------------------------- l. crosswalk coverage
def check_crosswalk_coverage(city_dir, rep):
    """l. every observed body code and vote value in the flat vote CSVs has a
    crosswalks/ row (city-specific or '*' wildcard); motion_type coverage is a
    WARN (normalize_motions fails loudly on unmapped types at build time)."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    slug = os.path.basename(os.path.abspath(city_dir)).replace("_city_council", "")
    cw = os.path.join(repo, "crosswalks")
    if not os.path.isdir(cw):
        rep.add("WARN", "l.crosswalks", "no repo-level crosswalks/ dir")
        return

    def covered_set(fname, code_col):
        _, rows = read_csv(os.path.join(cw, fname))
        return {(r.get("city"), (r.get(code_col) or "").strip()) for r in rows}

    bodies = covered_set("body_crosswalk.csv", "native_code")
    votes = covered_set("vote_values.csv", "value")
    mtypes = covered_set("motion_type_crosswalk.csv", "native_label")

    def is_covered(cov, value):
        return (slug, value) in cov or ("*", value) in cov

    missing_body, missing_vote, missing_mt = set(), set(), set()
    for ds in VOTE_DATASETS:
        path = os.path.join(city_dir, ds, "all_votes.csv")
        if not os.path.exists(path):
            continue
        _, rows = read_csv(path)
        for r in rows:
            b = (r.get("body") or "").strip()
            if b and not is_covered(bodies, b):
                missing_body.add(b)
            v = (r.get("vote") or "").strip()
            if v and not is_covered(votes, v):
                missing_vote.add(v)
            mt = (r.get("motion_type") or "").strip()
            if mt and not is_covered(mtypes, mt):
                missing_mt.add(mt)
    if missing_body:
        rep.add("FAIL", "l.crosswalks",
                f"body codes with no body_crosswalk row: {sorted(missing_body)}")
    if missing_vote:
        rep.add("FAIL", "l.crosswalks",
                f"vote values with no vote_values row: {sorted(missing_vote)}")
    if missing_mt:
        rep.add("WARN", "l.crosswalks",
                f"motion_type labels with no crosswalk row: {sorted(missing_mt)}")
    if not (missing_body or missing_vote or missing_mt):
        rep.add("PASS", "l.crosswalks",
                "every observed body code, vote value, and motion_type is crosswalked")


def validate(city_dir, quiet=False):
    city_dir = city_dir.rstrip("/")
    rep = Report(quiet=quiet)
    check_layout(city_dir, rep)
    check_vote_headers(city_dir, rep)
    check_vote_vocab(city_dir, rep)
    check_minutes_index(city_dir, rep)
    check_vote_sources(city_dir, rep)
    check_tally_consistency(city_dir, rep)
    check_motions_std(city_dir, rep)
    check_db(city_dir, rep)
    check_weeks(city_dir, rep)
    check_vote_validator(city_dir, rep)
    check_expansion_contracts(city_dir, rep)
    check_crosswalk_coverage(city_dir, rep)
    check_races_schema(city_dir, rep)
    return rep.emit(os.path.basename(city_dir))


def check_vote_validator(city_dir, rep):
    """j. council-vote validator (REMEDIATION_PLAN 3.1): present in meeting_minutes/ and
    exits clean. The per-city script (shared template scripts/validate_votes_template.py
    in 10 cities; bespoke in lehi/ogden/vineyard) writes its own detailed report; here we
    only surface presence + exit status + its one-line summary."""
    import subprocess
    vv = os.path.join(city_dir, "meeting_minutes", "validate_votes.py")
    if not os.path.exists(vv):
        rep.add("WARN", "j.votes", "no meeting_minutes/validate_votes.py (plan item 3.1)")
        return
    try:
        r = subprocess.run([sys.executable, vv], capture_output=True, text=True,
                           timeout=120)
    except subprocess.TimeoutExpired:
        rep.add("FAIL", "j.votes", "validate_votes.py timed out")
        return
    first = (r.stdout or r.stderr or "").strip().splitlines()
    summary = first[0] if first else "(no output)"
    if r.returncode == 0:
        rep.add("PASS", "j.votes", f"validate_votes.py clean — {summary}")
    else:
        rep.add("FAIL", "j.votes",
                f"validate_votes.py exit {r.returncode} — {summary}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    fails = 0
    for city_dir in args:
        if not os.path.isdir(city_dir):
            print(f"[FAIL] {city_dir}: not a directory")
            fails += 1
            continue
        fails += validate(city_dir, quiet=quiet)
    sys.exit(min(fails, 125))


if __name__ == "__main__":
    main()
