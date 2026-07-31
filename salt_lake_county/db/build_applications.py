#!/usr/bin/env python3
"""Build the Salt Lake County DEVELOPMENT-APPLICATIONS table — the "development
pipeline": one row per land-use/development action the County Council took, classified
by type and linked to its motion (so outcome + roll-call vote come for free).

Legistar's matter TYPES are generic (Discussion Items / Public Hearings), so land-use
actions are identified by TEXT in the motion title (rezone, planned development,
ordinance-approving-rezone, subdivision, annexation, general-plan amendment, conditional
use). Location is parsed from "located at <...>" where present. Nothing is fabricated:
type/location are extracted from the verbatim title, outcome from the motion.

Output: salt_lake_county/development/applications.csv  (loads into gov.db later).
DERIVED + idempotent.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "salt_lake_county.db")
OUTDIR = os.path.join(COUNTY, "development")

# ordered: first match wins (most specific first)
TYPE_PATTERNS = [
    ("planned_development",    r"planned development|\bP\.?D\.?\b|olympia hills"),
    ("rezone",                 r"rezone|zone change|zoning map amendment|amending the zoning"),
    ("subdivision_plat",       r"subdivision|\bplat\b|final plat|preliminary plat"),
    ("annexation",             r"annex"),
    ("general_plan_amendment", r"general plan"),
    ("conditional_use",        r"conditional use"),
    ("zoning_ord_text",        r"ordinance amending .*(chapter|title|section).*(zon|land use|19\.)"),
    ("development_agreement",  r"development agreement"),
    ("land_use_ordinance",     r"\bordinance\b.*(rezone|zoning|land use|development)"),
]
ANY_LU = re.compile(r"rezone|zoning|zone chang|subdivision|\bplat\b|conditional use|"
                    r"annex|development agreement|general plan|planned development|"
                    r"land use|olympia hills|\bordinance\b", re.I)
LOC = re.compile(r"located at\s+(.+?)(?:[.;]|$|,\s*(?:in|from|to)\b)", re.I)


def classify(title):
    low = title.lower()
    for name, pat in TYPE_PATTERNS:
        if re.search(pat, low):
            return name
    return "other_land_use"


def main():
    db = sqlite3.connect(DB)
    rows = []
    q = ("SELECT m.motion_id, mt.meeting_date, b.name, m.motion_text, m.motion_type, "
         "m.outcome, m.names_recorded, m.source_file, a.name "
         "FROM motion m JOIN meeting mt ON mt.meeting_id=m.meeting_id "
         "JOIN body b ON b.body_id=m.body_id "
         "LEFT JOIN application a ON a.application_id=m.application_id")
    for mid, date, body, title, mtype, outcome, named, src, matter in db.execute(q):
        text = "%s %s" % (title or "", matter or "")
        if not ANY_LU.search(text):
            continue
        dtype = classify(text)
        loc = ""
        mloc = LOC.search(title or "")
        if mloc:
            loc = mloc.group(1).strip()[:120]
        rows.append({
            "date": date, "body": body, "dev_type": dtype,
            "title": (title or "").strip()[:300], "matter": (matter or "").strip()[:200],
            "location": loc, "outcome": outcome, "names_recorded": named,
            "motion_id": mid, "minutes_path": src if str(src).endswith(".md") else "",
        })
    rows.sort(key=lambda r: (r["date"], r["motion_id"]))
    os.makedirs(OUTDIR, exist_ok=True)
    cols = ["date", "body", "dev_type", "title", "matter", "location", "outcome",
            "names_recorded", "motion_id", "minutes_path"]
    with open(os.path.join(OUTDIR, "applications.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    import collections
    bytype = collections.Counter(r["dev_type"] for r in rows)
    passed = sum(1 for r in rows if r["outcome"] == "Pass")
    withloc = sum(1 for r in rows if r["location"])
    print("development/applications.csv: %d land-use actions (%d passed, %d with parsed location)"
          % (len(rows), passed, withloc))
    for t, n in bytype.most_common():
        print("  %-24s %d" % (t, n))
    db.close()


if __name__ == "__main__":
    main()
