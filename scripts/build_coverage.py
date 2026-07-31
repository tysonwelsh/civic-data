#!/usr/bin/env python3
"""build_coverage.py — regenerate coverage.json, the machine-readable manifest.

Usage: python3 scripts/build_coverage.py   (from anywhere; writes <repo>/coverage.json)

Everything countable (records, date ranges) is MEASURED from the actual files —
never copied from documentation. `method` strings come from each city's documented
provenance (its CLAUDE.md / dataset docs) where stated, else "see city docs";
`caveats` are the audit-documented coverage caveats (short forms of
_audits/2026-07-02/report.md + each city's CLAUDE.md). Stdlib only; never mutates
city data.

TWO SECTIONS (2026-07-29, TODO high (k)) — this file used to be CITIES ONLY
(`from cities import SLUGS`, the level=='city' shim), so the 8 counties, 2 MPOs and
ut_state were invisible in a manifest root CLAUDE.md presents as the repo's measured
coverage:

  "cities"   — UNCHANGED, back-compat. The 31 city entries exactly as before
               (same builder, same keys, same values). Every existing reader keeps
               working; a byte-diff of this subtree is the regression gate.
  "entities" — NEW, complete. Every row of registry/entities.csv (44), driven by
               scripts/entities.py, in fed_index order, with registry metadata +
               the same measured `datasets` payloads. For the 31 cities the
               datasets object is the SAME object emitted under "cities" (one
               measurement, written twice — they cannot disagree).

COVERAGE MEANS DIFFERENT THINGS PER TIER, and this manifest says which. Every
non-city dataset entry carries a `status`:

  measured           — counted from the files on disk.
  source-ceiling     — the layer EXISTS and is complete as published, but the
                       source publishes less than a city's (e.g. both MPOs' vote
                       tables are empty because MPO minutes are tally-only: dissent
                       is count-only, dissenters never named).
  deferred-by-design — the layer was deliberately NOT built at this entity's tier
                       (washington_county LIGHT+ / juab_county CHEAP-ONLY are
                       db-less BY DESIGN; ut_state has no motion_std by owner
                       ruling). An honest property, not a gap — never a silent 0.

The deliberate-absence entries are keyed with the SAME labels gov.db's `v_coverage`
view emits for them — "(no vote layer)" and "(no motion_std layer)" — and their text
is imported from build_cities_db.CAVEATS (the `caveat` table's own rows), so the
manifest and the database state the ceiling in identical words instead of drifting.

Registered-only entities (wasatch_county, udot, uta) have `built: false` and
`datasets: null` — never an empty dataset map, which would read as built-but-empty.
"""
import csv
import datetime
import json
import os
import re
import sqlite3
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# City list comes from the shared registry (scripts/cities.py).
from cities import SLUGS as CITIES
# ...and the FULL entity list from the registry it shims (all 4 levels).
from entities import ENTITIES

EXPANSION = ["packets", "housing_plans", "ordinances", "pmn_backfill",
             "transcripts", "campaign_finance"]

# --- documented provenance (from city CLAUDE.md files; default = see city docs) ---
VOTE_METHOD = {
    ("slc", "meeting_minutes"): "LLM-batch-extracted from 2021+ minutes (spot-verified; see meeting_minutes/CLAUDE.md)",
    ("slc", "planning_commission"): "pure-regex extraction (planning_commission/extract_votes.py)",
    ("sandy", "planning_commission"): "Legistar API harvest (EventItemVote, body 140)",
}
VOTE_METHOD_DEFAULT = "deterministic extraction from minutes (see the dataset's extract_votes.py + CLAUDE.md)"

COMMENT_METHOD = {
    "slc": "Claude Vision extraction of slcdocs.com weekly comment PDFs",
    "provo": "page-walk extraction of comment letters from agenda packets (raw/packet_txt retained)",
}
COMMENT_METHOD_DEFAULT = "see city public_comments/CLAUDE.md"
COMMENT_METHOD_EMPTY = "availability audit — city publishes no written public comments (public_comments/AVAILABILITY.md)"

# --- audit-documented caveats (short strings; sources: _audits/2026-07-02/report.md,
#     city CLAUDE.md files). Keyed (city, dataset). ---
CAVEATS = {
    ("slc", "meeting_minutes"): ["2020 files are OCR (Laserfiche); 2021+ born-digital"],
    ("slc", "council_votes"): ["votes 2021+ only (2020 OCR too messy)",
                               "in-session RDA/CRA/LBA bodies share minutes docs (body column)"],
    ("slc", "public_comments"): ["one of only 2 substantive comment corpora in the collection",
                                 "~8 unrecoverable pages documented"],
    ("slc", "election_results"): ["2007-2025 — deeper than the other cities' 2019+"],
    ("lehi", "meeting_minutes"): ["8 Granicus double-event duplicate pairs removed 2026-07-02"],
    ("nephi", "council_votes"): ["mostly tally-only — only ~58 motions name voters (source limit)"],
    ("nephi", "planning_commission_votes"): ["mostly tally-only", "footer-bleed in some motion text (known extractor issue)"],
    ("ogden", "meeting_minutes"): ["carved from year compilation PDFs; 2022 re-OCR'd + re-carved 2026-07-02"],
    ("ogden", "council_votes"): ["separate 2022 and 2023 RDA/MBA meeting sets never acquired (0 RDA/MBA motions those years)"],
    ("orem", "council_votes"): ["records Aye/Nay only — absences/abstentions/recusals never in minutes"],
    ("orem", "planning_commission_minutes"): ["2025-10-15 minutes unrecoverable (city mis-upload; logged)"],
    ("park_city", "council_votes"): ["2 mayoral tie-breaks recorded as 'Nay (Mayor tie-break)'",
                                     "9 contradictory source Aye+Nay pairs resolved via db/vote_overrides.csv"],
    ("provo", "planning_commission_minutes"): ["2025+ only (source limit)"],
    ("provo", "public_comments"): ["letters from agenda packets; truncation defect repaired 2026-07-02"],
    ("sandy", "meeting_minutes"): ["63 PUA-garbled files decoded + re-extracted 2026-07-02 (raw PDFs retained)"],
    ("sandy", "council_votes"): ["narrative tallies name only dissenters (majority unnamed, names_recorded:false)",
                                 "mayor does not vote", "RDA acts in closed session — 1 open RDA row is complete"],
    ("sandy", "planning_commission_votes"): ["from Legistar API — no PC minutes files exist in repo"],
    ("sandy", "db"): ["standard schema since 2026-07-02 (plan 2.6): council votes minutes-primary, PC votes Legistar; full Legistar harvest in legistar_* extension tables (incl. Nonvoting + Board of Adjustment)"],
    ("st_george", "meeting_minutes"): ["2020-21 minutes backfilled from Utah PMN (the Revize archive holds 2022+)",
                                       "2025-10-09 work meeting unrecoverable (source published wrong file; logged)"],
    ("vineyard", "meeting_minutes"): ["wrong/duplicate source documents repaired 2026-07-02"],
    ("west_jordan", "planning_commission_votes"): ["tally-only: source names only dissenters/absentees — zero named Ayes"],
    ("west_jordan", "planning_commission_minutes"): ["36/84 files are OCR"],
    ("west_valley", "council_votes"): ["3 motions where minutes printed 'Unanimous' over a dissenting roll call (truthful roll call retained)"],
}


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def date_range(rows, col="date"):
    dates = sorted(r[col] for r in rows if r.get(col) and len(r[col]) >= 8)
    if not dates:
        return None, None
    return dates[0], dates[-1]


def entry(records, dmin, dmax, method, caveats):
    return {"records": records, "date_min": dmin, "date_max": dmax,
            "method": method, "as_of": AS_OF, "caveats": caveats}


def caveats_for(city, dataset, extra=None):
    out = list(CAVEATS.get((city, dataset), []))
    if extra:
        out.extend(extra)
    return out


def minutes_entry(city, city_dir, ds, ds_key):
    idx = os.path.join(city_dir, ds, "minutes_index.csv")
    if not os.path.exists(idx):
        return None
    rows = read_rows(idx)
    date_col = "date" if rows and "date" in rows[0] else "meeting_date"
    dmin, dmax = date_range(rows, date_col)
    portals = {}
    for r in rows:
        portals[r.get("source", "?")] = portals.get(r.get("source", "?"), 0) + 1
    method = "portal: " + ", ".join(f"{k} ({v})" for k, v in sorted(portals.items(), key=lambda x: -x[1]))
    extra = []
    unrec = os.path.join(city_dir, ds, "minutes_unrecovered.csv")
    if os.path.exists(unrec):
        n = len(read_rows(unrec))
        if n:
            extra.append(f"{n} known meeting(s) with unrecoverable minutes (minutes_unrecovered.csv)")
    return entry(len(rows), dmin, dmax, method, caveats_for(city, ds_key, extra))


def votes_entry(city, city_dir, ds, ds_key):
    path = os.path.join(city_dir, ds, "all_votes.csv")
    if not os.path.exists(path):
        return None
    rows = read_rows(path)
    dmin, dmax = date_range(rows)
    motions = len({(r.get("source"), r.get("motion_no")) for r in rows})
    named = sum(1 for r in rows if r.get("member"))
    method = VOTE_METHOD.get((city, ds), VOTE_METHOD_DEFAULT)
    extra = [f"{motions} motions; {named} named member-vote rows, {len(rows) - named} tally-only rows"] \
        if named < len(rows) else [f"{motions} motions; all rows named"]
    return entry(len(rows), dmin, dmax, method, caveats_for(city, ds_key, extra))


def build_city(city):
    city_dir = os.path.join(REPO, f"{city}_city_council")
    ds = {}

    ds["meeting_minutes"] = minutes_entry(city, city_dir, "meeting_minutes", "meeting_minutes")
    ds["council_votes"] = votes_entry(city, city_dir, "meeting_minutes", "council_votes")
    pcm = minutes_entry(city, city_dir, "planning_commission", "planning_commission_minutes")
    if pcm:
        ds["planning_commission_minutes"] = pcm
    pcv = votes_entry(city, city_dir, "planning_commission", "planning_commission_votes")
    if pcv:
        ds["planning_commission_votes"] = pcv

    # public comments
    cpath = os.path.join(city_dir, "public_comments", "all_comments_clean.csv")
    if os.path.exists(cpath):
        rows = read_rows(cpath)
        # `date` is verbatim free text in some cities; prefer the normalized column
        dcol = "date_normalized" if (rows and rows[0].get("date_normalized")) else "date"
        dmin, dmax = date_range(rows, dcol)
        if len(rows) == 0:
            method = COMMENT_METHOD_EMPTY
            cav = caveats_for(city, "public_comments",
                              ["honest empty — absence is the documented finding"])
        else:
            method = COMMENT_METHOD.get(city, COMMENT_METHOD_DEFAULT)
            cav = caveats_for(city, "public_comments")
        ds["public_comments"] = entry(len(rows), dmin, dmax, method, cav)

    # elections
    for f in os.listdir(os.path.join(city_dir, "election_results")):
        if f.endswith("_races.csv"):
            rows = read_rows(os.path.join(city_dir, "election_results", f))
            years = sorted({r["year"] for r in rows if r.get("year")})
            ds["election_results"] = entry(
                len(rows), years[0] if years else None, years[-1] if years else None,
                "county canvass results filtered to city council + mayor races",
                caveats_for(city, "election_results"))
            break

    # db
    db_dir = os.path.join(city_dir, "db")
    if os.path.isdir(db_dir):
        dbs = sorted(f for f in os.listdir(db_dir) if f.endswith(".db"))
        if dbs:
            p = os.path.join(db_dir, dbs[0])
            try:
                conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
                votes = conn.execute("SELECT COUNT(*) FROM vote").fetchone()[0]
                motions = conn.execute("SELECT COUNT(*) FROM motion").fetchone()[0]
                try:
                    referrals = conn.execute("SELECT COUNT(*) FROM referral").fetchone()[0]
                except sqlite3.Error:
                    referrals = None
                conn.close()
                method = "built from the vote CSVs (db/build_db.py + db/build_referrals.py)"
                extra = [f"{motions} motions" + (f"; {referrals} scored cross-body referrals" if referrals is not None else "")]
                ds["db"] = entry(votes, None, None, method, caveats_for(city, "db", extra))
            except sqlite3.Error as e:
                ds["db"] = entry(None, None, None, f"unreadable: {e}", caveats_for(city, "db"))

    # weeks
    weeks_dir = os.path.join(city_dir, "weeks")
    if os.path.isdir(weeks_dir):
        weeks = sorted(d for d in os.listdir(weeks_dir)
                       if os.path.isdir(os.path.join(weeks_dir, d)))
        ds["weeks"] = entry(len(weeks), weeks[0] if weeks else None,
                            weeks[-1] if weeks else None,
                            "derived weekly bundles (build_weeks.py) — regenerable",
                            caveats_for(city, "weeks"))

    # expansion datasets (lehi pilot; additive elsewhere over time)
    for exp in EXPANSION:
        idx = os.path.join(city_dir, exp, "index.csv")
        if not os.path.exists(idx):
            continue
        rows = read_rows(idx)
        dmin, dmax = date_range(rows)
        extra = ["expansion dataset (expand-city-sources) — in progress across cities; raw/ retained"]
        unrec = os.path.join(city_dir, exp, "unrecovered.csv")
        if os.path.exists(unrec):
            n = len(read_rows(unrec))
            if n:
                extra.append(f"{n} unrecovered item(s) logged")
        ds[exp] = entry(len(rows), dmin, dmax,
                        f"see {exp}/CLAUDE.md + AVAILABILITY.md", caveats_for(city, exp, extra))

    return {"dir": f"{city}_city_council", "datasets": {k: v for k, v in ds.items() if v}}


# ===========================================================================
# NON-CITY TIER (counties / MPOs / the state) — 2026-07-29, TODO high (k)
# ===========================================================================
# The city path above is FILE-CONTRACT driven: every city has the same folders.
# The non-city tier does not and must not — an MPO is programmed projects, a
# db-less county is elections + text corpora — so this half is MODULE-DRIVEN:
# it measures the modules an entity actually has, and records the ones it
# deliberately does NOT have as explicit deferrals rather than silent zeros.

# The ceiling texts are IMPORTED from the federation builder's CAVEATS list —
# the same rows that become gov.db's `caveat` table — so coverage.json and the
# database state each ceiling in identical words. Guarded: build_cities_db is a
# shared file under concurrent edit, and a manifest that honestly says "the
# caveat source was unreadable" beats one that quietly paraphrases from memory.
try:
    from build_cities_db import CAVEATS as DB_CAVEATS
    CAVEAT_SOURCE = ("scripts/build_cities_db.py CAVEATS — the same rows loaded "
                     "into gov.db's `caveat` table")
except Exception as _exc:            # pragma: no cover - defensive
    DB_CAVEATS = []
    CAVEAT_SOURCE = ("UNAVAILABLE — could not import scripts/build_cities_db.py "
                     "(%s: %s); entity caveat text is OMITTED, not paraphrased"
                     % (type(_exc).__name__, _exc))

# Dataset entries whose whole content is an honest absence. Keyed by the label
# gov.db's v_coverage view emits for the same entity, so the two agree literally.
DELIBERATE_ABSENCE = {
    "washington_county": [(
        "(no vote layer)", "vote-ceiling",
        "NOT BUILT — LIGHT+ tier: the vote layer and the development pipeline are "
        "explicitly DEFERRED. db-less BY DESIGN; the canonical layers are elections, "
        "the minutes FTS corpora, and plans/ordinances/gis.")],
    "juab_county": [(
        "(no vote layer)", "vote-ceiling",
        "NOT BUILT — CHEAP-ONLY tier: no legislative/land_use/plans modules were built, "
        "so this entity contributes elections + projections + a GIS catalog only. "
        "db-less BY DESIGN.")],
    "ut_state": [(
        "(no motion_std layer)", "motion-std-deferred",
        "NOT BUILT — the municipal motion_type_std vocabulary does not describe "
        "legislative bill-stage votes (owner ruling 2026-07-29). ut_state is in "
        "build_cities_db.EXCLUDED_FROM_MOTION_STD; its roll calls federate as "
        "motion/vote rows with no normalization layer above them.")],
}

# module dir -> (file, date column, year-grain?, method sentence)
INDEX_MODULES = [
    ("elections", "election_results_by_contest.csv", "year", True,
     "county canvass, audited into the 14-column by-contest schema (elections/)"),
    ("ordinances", "index.csv", "adoption_date", False,
     "adopted-instrument catalog; motion_id links the enacting motion where unique"),
    ("plans", "index.csv", "adopted_date", False,
     "plan / policy document catalog (paths + text_path where recovered)"),
    ("gis", "index.csv", None, False,
     "GIS layer catalog — links and endpoints, not vendored geodata"),
    ("packets", "index.csv", "date", False,
     "agenda-packet / staff-report catalog"),
    ("development", "applications.csv", "date", False,
     "development-application pipeline carved from the land-use record"),
]


def pick_col(rows, *names):
    """First of `names` present in the header (entities spell columns differently)."""
    if not rows:
        return None
    for n in names:
        if n in rows[0]:
            return n
    return None


def top_counts(counter, limit=8):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    out = ", ".join(f"{k or '(blank)'} ({v})" for k, v in items[:limit])
    if len(items) > limit:
        out += f", +{len(items) - limit} more"
    return out


def year_range(rows, col):
    years = sorted({(r.get(col) or "").strip() for r in rows} - {""})
    return (years[0], years[-1]) if years else (None, None)


ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def dated(rows, col, extra):
    """ISO-only date range, with everything it could NOT range over counted.

    Non-city indexes are not uniform: several carry a VERBATIM source date
    ("1/16/2024 (3:56:46 PM)" in ut_state rollcalls, "2016 (updated 2019-11-19)"
    in weber plans). Sorting those lexically yields a nonsense range — e.g. a
    date_min LATER than the date_max — so non-ISO values are EXCLUDED from the
    range and reported as a count instead of being guessed at or silently sorted.
    """
    if not rows or not pick_col(rows, col):
        return None, None
    vals = [(r.get(col) or "").strip() for r in rows]
    iso = sorted(v for v in vals if ISO_DATE.match(v))
    other = sum(1 for v in vals if v and not ISO_DATE.match(v))
    blank = sum(1 for v in vals if not v)
    if other:
        extra.append(f"{other} row(s) carry a non-ISO verbatim `{col}` value — excluded "
                     "from the date range rather than guessed at")
    if blank:
        extra.append(f"{blank} row(s) have an empty `{col}`")
    dmin = iso[0][:10] if iso else None
    dmax = iso[-1][:10] if iso else None
    if dmax and dmax > TODAY:
        n = sum(1 for v in iso if v[:10] > TODAY)
        extra.append(f"date_max is in the FUTURE: {n} row(s) are scheduled / not-yet-held "
                     "meetings catalogued ahead of time, not recovered records")
    return dmin, dmax


def nc_entry(records, dmin, dmax, method, caveats, status="measured"):
    """Same 6 keys as a city entry, plus the per-tier `status` (see module doc)."""
    return {"records": records, "date_min": dmin, "date_max": dmax,
            "method": method, "as_of": AS_OF, "status": status,
            "caveats": caveats}


def db_caveats(slug, dataset):
    """Caveat rows for this entity scoped to `dataset` ('*' = entity-wide)."""
    return [f"{code}: {text}" for (c_city, c_ds, code, text) in DB_CAVEATS
            if c_city == slug and c_ds == dataset]


def caveat_by_code(slug, code):
    for c_city, _c_ds, c_code, text in DB_CAVEATS:
        if c_city == slug and c_code == code:
            return f"{c_code}: {text}"
    return (f"[{code} caveat for {slug} not found in the caveat source — omitted "
            f"rather than paraphrased]")


def nc_minutes(e, edir, module):
    path = os.path.join(edir, module, "minutes_index.csv")
    if not os.path.exists(path):
        return None
    rows = read_rows(path)
    extra = []
    dcol = pick_col(rows, "date", "meeting_date") or "date"
    dmin, dmax = dated(rows, dcol, extra)
    bcol = pick_col(rows, "body")
    if bcol:
        method = "minutes index — bodies: " + top_counts(
            Counter((r.get(bcol) or "").strip() for r in rows))
    else:
        method = ("minutes index — this entity's index carries no body column "
                  "(single-body module)")
    scol = pick_col(rows, "minutes_status", "doc_status")
    if scol:
        extra.append(f"{scol}: " + top_counts(
            Counter((r.get(scol) or "").strip() for r in rows)))
    for gapfile, label in (("minutes_unrecovered.csv", "known meeting(s) with unrecovered minutes"),
                           ("gaps.csv", "logged gap row(s)")):
        gp = os.path.join(edir, module, gapfile)
        if os.path.exists(gp):
            n = len(read_rows(gp))
            if n:
                extra.append(f"{n} {label} ({module}/{gapfile})")
    return nc_entry(len(rows), dmin, dmax, method,
                    db_caveats(e.slug, module) + extra)


def nc_votes(e, edir, module):
    """The module's flat vote/motion file, when this entity publishes one.

    Several entities (weber, mag_mpo, salt_lake_county's legislative module)
    publish NO flat motion file — their vote layer exists only inside the
    per-entity db, and is measured there. Nothing is emitted here for them
    rather than a misleading zero.
    """
    vpath = os.path.join(edir, module, "all_votes.csv")
    if os.path.exists(vpath):
        rows = read_rows(vpath)
        motions = len({(r.get("source"), r.get("motion_no")) for r in rows})
        named = sum(1 for r in rows if r.get("member"))
        extra = [f"{motions} motions; {named} named member-vote rows, "
                 f"{len(rows) - named} tally-only rows"]
        dmin, dmax = dated(rows, "date", extra)
        if rows and "provenance" in rows[0]:
            extra.append("provenance: " + top_counts(
                Counter((r.get("provenance") or "").strip() for r in rows)))
        return (f"{module}_votes",
                nc_entry(len(rows), dmin, dmax,
                         "deterministic extraction from this entity's minutes "
                         f"(see {module}/ + db/extract_votes.py)",
                         db_caveats(e.slug, module) + extra))
    mpath = os.path.join(edir, module, "all_motions.csv")
    if os.path.exists(mpath):
        rows = read_rows(mpath)
        # A motions file with no member column is a SOURCE ceiling, not a gap:
        # the minutes name a mover/seconder and print a count, never a roll call.
        named_col = pick_col(rows, "member")
        cav = db_caveats(e.slug, module)
        dmin, dmax = dated(rows, "date", cav)
        if not named_col:
            cav = [caveat_by_code(e.slug, "regional-model-note")] + cav \
                if any(c[0] == e.slug and c[2] == "regional-model-note" for c in DB_CAVEATS) else cav
            cav.append("motion-level only: the source prints no per-member rows, "
                       "so no member-vote layer exists to measure")
        return (f"{module}_motions",
                nc_entry(len(rows), dmin, dmax,
                         f"motion-level extraction ({module}/all_motions.csv)",
                         cav, status="measured" if named_col else "source-ceiling"))
    return None


def nc_index(e, edir, module, fname, dcol, is_year, method):
    path = os.path.join(edir, module, fname)
    if not os.path.exists(path):
        return None
    rows = read_rows(path)
    extra = []
    if dcol and is_year:
        dmin, dmax = year_range(rows, dcol)
    elif dcol:
        dmin, dmax = dated(rows, dcol, extra)
    else:
        dmin = dmax = None
    if module == "elections":
        extra.append("jurisdictions: %d; contests: %d" % (
            len({r.get("jurisdiction_slug") for r in rows}),
            len({(r.get("year"), r.get("contest")) for r in rows})))
        sup = sum(1 for r in rows if (r.get("suppressed") or "").strip() not in ("", "0"))
        if sup:
            extra.append(f"{sup} privacy-suppressed row(s) retained as such")
    if module == "gis":
        extra.append("publishers: " + top_counts(
            Counter((r.get("publisher") or "").strip() for r in rows), 5))
    gaps = os.path.join(edir, module, "gaps.csv")
    if os.path.exists(gaps):
        n = len(read_rows(gaps))
        if n:
            extra.append(f"{n} logged gap row(s) ({module}/gaps.csv)")
    return nc_entry(len(rows), dmin, dmax, method,
                    db_caveats(e.slug, module) + extra)


def nc_projections(e, edir):
    pdir = os.path.join(edir, "projections")
    if not os.path.isdir(pdir):
        return None
    files = sorted(f for f in os.listdir(pdir) if f.endswith(".csv"))
    if not files:
        return None
    rows, used = [], []
    for f in files:
        rows.extend(read_rows(os.path.join(pdir, f)))
        used.append(f)
    dmin, dmax = year_range(rows, "year")
    extra = ["grain: " + top_counts(Counter(r.get("geography_type", "") for r in rows)),
             "metrics: " + top_counts(Counter(r.get("metric", "") for r in rows), 12),
             "geographies: %d" % len({r.get("geography") for r in rows})]
    return nc_entry(len(rows), dmin, dmax,
                    "projections/" + ", ".join(used) + " (9-column repo schema)",
                    db_caveats(e.slug, "projections") + extra)


def nc_projects(e, edir):
    path = os.path.join(edir, "projects", "projects.csv")
    if not os.path.exists(path):
        return None
    rows = read_rows(path)
    extra = ["plan kinds: " + top_counts(Counter(r.get("plan_kind", "") for r in rows)),
             "vintages: " + top_counts(Counter(r.get("plan_vintage", "") for r in rows), 10),
             "distinct project ids: %d" % len({r.get("project_id") for r in rows})]
    return nc_entry(len(rows), None, None,
                    "programmed-project layer (projects/projects.csv, the 15-column "
                    "cross-MPO schema) — the canonical form is gov.db regional_project",
                    db_caveats(e.slug, "projects") + extra)


def nc_roster(e, edir):
    rdir = os.path.join(edir, "roster")
    if not os.path.isdir(rdir):
        return None
    files = sorted(f for f in os.listdir(rdir) if f.endswith(".csv"))
    if not files:
        return None
    rows = []
    for f in files:
        rows.extend(read_rows(os.path.join(rdir, f)))
    return nc_entry(len(rows), None, None,
                    "seat roster (roster/" + ", ".join(files) + " — see roster/CLAUDE.md)",
                    db_caveats(e.slug, "roster"))


def nc_state_modules(e, edir):
    """ut_state's OWN categories — bills, roll calls, advisory opinions, statutes.

    Deliberately NOT expressed in municipal dataset names: there is no
    meeting_minutes / planning_commission / public_comments layer here, and
    inventing one would be exactly the municipal framing the state tier is
    under review for (TODO "STATE TIER — … ON ITS OWN TERMS").
    """
    ds = {}
    leg = os.path.join(edir, "legislation")
    if os.path.isdir(leg):
        def n_of(fn):
            p = os.path.join(leg, fn)
            return len(read_rows(p)) if os.path.exists(p) else 0

        bills = read_rows(os.path.join(leg, "bills.csv")) if os.path.exists(
            os.path.join(leg, "bills.csv")) else []
        if bills:
            smin, smax = year_range(bills, "session")
            ds["legislation_bills"] = nc_entry(
                len(bills), smin, smax,
                "land-use/housing subset selected from the public le.utah.gov bill "
                "inventory by a title-based classifier (legislation/bills.csv)",
                db_caveats(e.slug, "legislation") + [
                    f"selected from {n_of('bills_all.csv')} catalogued bills "
                    "(legislation/bills_all.csv) — the subset is a classifier recall "
                    "CEILING, not a census of land-use legislation"])
        def rows_of(fn):
            p = os.path.join(leg, fn)
            return read_rows(p) if os.path.exists(p) else []

        rc = rows_of("rollcalls.csv")
        rc_all = rc + rows_of("rollcalls_recovered.csv")
        rc_rec = n_of("rollcalls_recovered.csv")
        if rc:
            # The roll-call `date` column is the VERBATIM source stamp
            # ("1/16/2024 (3:56:46 PM)"), not ISO — the range is taken over the
            # session column instead, and the raw column is described, not sorted.
            smin, smax = year_range(rc_all, "session")
            ds["legislation_rollcalls"] = nc_entry(
                len(rc_all), smin, smax,
                "named roll calls harvested from the public le.utah.gov channel",
                db_caveats(e.slug, "legislation") + [
                    f"{len(rc)} primary + {rc_rec} recovered rows (the two files are "
                    "ADDITIVE, not a subset)",
                    "date_min/date_max are SESSIONS: the file's `date` column is a "
                    "verbatim le.utah.gov timestamp, not an ISO date (the ISO meeting "
                    "dates are in db/ut_state.db `meeting`)",
                    "chambers/committees: " + top_counts(
                        Counter((r.get("chamber") or "").strip() for r in rc), 4)])
        vt = read_rows(os.path.join(leg, "votes.csv")) if os.path.exists(
            os.path.join(leg, "votes.csv")) else []
        vt_rec = n_of("votes_recovered.csv")
        if vt:
            ds["legislation_votes"] = nc_entry(
                len(vt) + vt_rec, None, None,
                "NAMED legislator votes, one row per legislator per roll call",
                db_caveats(e.slug, "legislation") + [
                    f"{len(vt)} primary + {vt_rec} recovered rows (ADDITIVE)",
                    "legislators are a DISJOINT person population from municipal "
                    "officials — never surname-join across tiers"])
    for module, label in (("advisory_opinions",
                           "Office of the Property Rights Ombudsman advisory opinions"),
                          ("statutes", "LUDMA statute sections (per-section text)")):
        idx = os.path.join(edir, module, "index.csv")
        if not os.path.exists(idx):
            continue
        rows = read_rows(idx)
        extra = []
        dmin, dmax = dated(rows, "date", extra)
        have = sum(1 for r in rows if (r.get("text_path") or "").strip())
        extra.append(f"{have}/{len(rows)} rows carry recovered text (text_path)")
        ds[module] = nc_entry(len(rows), dmin, dmax, label,
                              db_caveats(e.slug, module) + extra)
    return ds


def nc_db(e, edir):
    """The per-entity db: the vote spine, measured where it actually lives."""
    if not e.db_rel_path:
        return None
    p = os.path.join(edir, e.db_rel_path)
    if not os.path.exists(p):
        return nc_entry(None, None, None, f"{e.db_rel_path} MISSING on disk", [],
                        status="unreadable")
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
        motions = one("SELECT COUNT(*) FROM motion")
        votes = one("SELECT COUNT(*) FROM vote")
        referrals = one("SELECT COUNT(*) FROM referral")
        dmin, dmax = conn.execute(
            "SELECT MIN(meeting_date), MAX(meeting_date) FROM meeting").fetchone()
        bodies = conn.execute(
            "SELECT b.name, COUNT(m.motion_id) FROM body b "
            "LEFT JOIN motion m ON m.body_id = b.body_id GROUP BY b.name").fetchall()
        try:
            named = one("SELECT COUNT(*) FROM motion WHERE names_recorded = 1")
        except sqlite3.Error:
            named = None
        conn.close()
    except sqlite3.Error as exc:
        return nc_entry(None, None, None, f"unreadable: {exc}", [], status="unreadable")
    extra = [f"{motions} motions; {referrals} scored cross-body referrals",
             "motions by body: " + top_counts(Counter(dict(bodies)))]
    if named is not None:
        extra.append(f"{named} of {motions} motions carry a named roll call "
                     f"(names_recorded=1); {motions - named} are tally-only by source")
    status = "measured"
    cav = db_caveats(e.slug, "db")
    if motions and not votes:
        # The layer is complete as published — the source never names voters.
        status = "source-ceiling"
        if any(c[0] == e.slug and c[2] == "regional-model-note" for c in DB_CAVEATS):
            cav = [caveat_by_code(e.slug, "regional-model-note")] + cav
        extra.insert(0, "0 member-vote rows: this entity's minutes are TALLY-ONLY by "
                        "source (dissent is count-only; dissenters never named) — an "
                        "empty vote table here is a source ceiling, not missing data")
    return nc_entry(votes, dmin, dmax,
                    f"per-entity db ({e.db_rel_path}), built by db/build_db.py",
                    cav + extra, status=status)


def build_noncity(e):
    """Measured datasets for one county / MPO / state entity."""
    edir = os.path.join(REPO, e.dir)
    ds = {}
    for module in ("legislative", "land_use", "agencies"):
        m = nc_minutes(e, edir, module)
        if m:
            ds[f"{module}_minutes"] = m
        v = nc_votes(e, edir, module)
        if v:
            ds[v[0]] = v[1]
    for module, fname, dcol, is_year, method in INDEX_MODULES:
        got = nc_index(e, edir, module, fname, dcol, is_year, method)
        if got:
            ds[module] = got
    for key, fn in (("projections", nc_projections), ("projects", nc_projects),
                    ("roster", nc_roster)):
        got = fn(e, edir)
        if got:
            ds[key] = got
    if e.level == "state":
        ds.update(nc_state_modules(e, edir))
    got = nc_db(e, edir)
    if got:
        ds["db"] = got
    # ...and the layers this entity's tier deliberately does NOT have.
    for label, code, method in DELIBERATE_ABSENCE.get(e.slug, []):
        ds[label] = nc_entry(None, None, None, method, [caveat_by_code(e.slug, code)],
                             status="deferred-by-design")
    return ds


def build_entity(e, city_payloads):
    """One registry row -> its manifest record (all four levels)."""
    built = bool(e.dir) and os.path.isdir(os.path.join(REPO, e.dir))
    rec = {"name": e.name, "level": e.level, "state": e.state,
           "dir": e.dir or None, "fed_index": e.fed_index,
           "db": e.db_rel_path or None, "built": built,
           "caveats": db_caveats(e.slug, "*")}
    if not built:
        # Registered-only: in the registry to carry relationships / act as a
        # reference entity. `datasets: null` (never {}) so it can never be read
        # as a built entity that measured empty.
        rec["status"] = "registered-only"
        rec["registry_note"] = e.notes
        rec["datasets"] = None
        return rec
    rec["status"] = "built"
    if e.level == "city":
        # The SAME object emitted under "cities" — one measurement, two places.
        rec["datasets"] = city_payloads[e.slug]["datasets"]
    else:
        rec["datasets"] = build_noncity(e)
    return rec


def main():
    global AS_OF, TODAY
    AS_OF = TODAY = datetime.date.today().isoformat()
    cities = {c: build_city(c) for c in CITIES}
    entities = {e.slug: build_entity(e, cities) for e in ENTITIES}
    by_level = Counter(e.level for e in ENTITIES)
    n_built = sum(1 for v in entities.values() if v["built"])
    manifest = {
        "description": "Measured per-entity x dataset coverage manifest for the civic-data "
                       "repo. Regenerate: python3 scripts/build_coverage.py. "
                       "Spec: SCHEMA_SPEC.md.",
        "as_of": AS_OF,
        "generated_by": "scripts/build_coverage.py",
        "note": "records/date ranges measured from the files; caveats are the documented "
                "coverage caveats (see _audits/2026-07-02/report.md and city CLAUDE.md files). "
                "geo/ is a tool (address->district), not a dataset, and is not listed.",
        "sections": {
            "cities": "The 31 level=='city' entities, unchanged since this manifest was "
                      "city-only — kept verbatim for back-compat.",
            "entities": "Every row of registry/entities.csv (all 4 levels), in registry "
                        "order, with registry metadata + the same measured datasets. City "
                        "dataset payloads here are the SAME objects as under 'cities'.",
        },
        "dataset_status_values": {
            "measured": "counted from the files on disk",
            "source-ceiling": "the layer is complete AS PUBLISHED but the source publishes "
                              "less than a city's (e.g. tally-only minutes -> an empty vote "
                              "table) — a ceiling, not missing data",
            "deferred-by-design": "the layer was deliberately not built at this entity's "
                                  "tier — an honest property, not a gap",
            "unreadable": "the artifact exists but could not be read at build time",
        },
        "caveat_source": CAVEAT_SOURCE,
        "entity_counts": {"total": len(ENTITIES), "built": n_built,
                          "registered_only": len(ENTITIES) - n_built,
                          "by_level": dict(sorted(by_level.items()))},
        "cities": cities,
        "entities": entities,
    }
    out = os.path.join(REPO, "coverage.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")
    n_ds = sum(len(v["datasets"]) for v in cities.values())
    n_nc = sum(len(v["datasets"]) for v in entities.values()
               if v["datasets"] and v["level"] != "city")
    print(f"wrote {out}: {len(CITIES)} cities, {n_ds} city dataset entries; "
          f"{len(ENTITIES)} registry entities ({n_built} built, "
          f"{len(ENTITIES) - n_built} registered-only), {n_nc} non-city dataset entries")
    if not DB_CAVEATS:
        print("WARNING: caveat source unavailable — %s" % CAVEAT_SOURCE)


if __name__ == "__main__":
    main()
