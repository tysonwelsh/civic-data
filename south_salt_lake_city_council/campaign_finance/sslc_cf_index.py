#!/usr/bin/env python3
"""Build South Salt Lake campaign_finance/index.csv (SCHEMA_SPEC §9, ACQUISITION-only).

Reads _fetch_manifest.json (ADID/title/url/name/cycle/source), _textmeta.json
(born-digital vs scanned), and the fetch log (sha256), and emits index.csv with the
exact §9 contract header + documented extension columns.

Dates/periods are ACQUISITION-layer inferences from the archive report LABEL and,
where a born-digital text layer allowed it, the internal transaction-date window
(see CLAUDE.md). No dollar figures are extracted here — that is the deferred pass.
"""
import csv, json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"

man = json.load(open(os.path.join(HERE, "_fetch_manifest.json")))
tm = json.load(open(os.path.join(HERE, "_textmeta.json")))
sha = {}
for line in open(os.path.join(RAW, "_fetch_log.jsonl")):
    r = json.loads(line)
    if r.get("saved_as"):
        sha[r["saved_as"]] = r.get("sha256", "")

# Verified roster mapping: (cycle, surname_lower) -> office, district, election_name,
# join_confidence, in_election_results. From election_results by-candidate roster.
ROSTER = {
    # 2021 general (Mayor + D2 + D3 + At-Large)
    ("2021", "wood"): ("Mayor", "", "CHERIE WOOD", "exact", "yes"),
    ("2021", "christensen"): ("Mayor", "", "JAKE CHRISTENSEN", "exact", "yes"),
    ("2021", "siwik"): ("Mayor", "", "L. SHANE SIWIK", "exact", "yes"),
    ("2021", "thomas"): ("Council", "2", "COREY THOMAS", "exact", "yes"),
    ("2021", "garfield"): ("Council", "2", "SAM GARFIELD", "exact", "yes"),
    ("2021", "bynum"): ("Council", "3", "SHARLA BYNUM", "exact", "yes"),
    ("2021", "hampton"): ("Council", "3", "AILEEN E. HAMPTON", "exact", "yes"),
    ("2021", "williams"): ("Council", "At-Large", "CLARISSA J. WILLIAMS", "exact", "yes"),
    ("2021", "spencer"): ("Council", "At-Large", "OLIVIA SPENCER", "exact", "yes"),
    # 2023 general (At-Large + D1 + D4 + D5)
    ("2023", "pinkney"): ("Council", "At-Large", "NATALIE PINKNEY", "exact", "yes"),
    ("2023", "campos"): ("Council", "At-Large", "CONRAD N. CAMPOS", "exact", "yes"),
    ("2023", "huff"): ("Council", "1", "LEANNE HUFF", "normalized", "yes"),
    ("2023", "potter"): ("Council", "1", "JEANETTE POTTER", "exact", "yes"),
    ("2023", "mitchell"): ("Council", "4", "NICK MITCHELL", "normalized", "yes"),
    ("2023", "mila"): ("Council", "4", "PORTIA MILA", "exact", "yes"),
    ("2023", "sanchez"): ("Council", "5", "PAUL SANCHEZ", "exact", "yes"),
    # 2025 general (Mayor + D2 + D3 + At-Large + At-Large 2-yr special)
    ("2025", "wood"): ("Mayor", "", "CHERIE WOOD", "exact", "yes"),
    ("2025", "karzen"): ("Mayor", "", "BRITTANY KARZEN", "exact", "yes"),
    ("2025", "thomas"): ("Council", "2", "COREY THOMAS", "exact", "yes"),
    ("2025", "bynum"): ("Council", "3", "SHARLA BYNUM", "exact", "yes"),
    ("2025", "hampton"): ("Council", "3", "AILEEN HAMPTON", "exact", "yes"),
    ("2025", "dewolfe"): ("Council", "At-Large-2yr", "G. RAY DEWOLFE", "normalized", "yes"),
    ("2025", "campos"): ("Council", "At-Large-2yr", "CONRAD CAMPOS", "exact", "yes"),
    ("2025", "williams"): ("Council", "At-Large", "CLARISSA J. WILLIAMS", "exact", "yes"),
}
# 2026 council-vacancy appointment applicants (NOT an election). Serving appointees:
# Glad -> D1, Jones -> D5 (per CLAUDE.md). Others = unsuccessful applicants.
VACANCY = {
    "glad": ("Council", "1", "no", "appointed D1 (2026); not an in-scope election winner"),
    "jones": ("Council", "5", "yes", "IRVIN JONES appears in election roster (2011 D5); 2026 D5 appointee"),
    "robinson": ("Council", "", "no", "2026 vacancy applicant"),
    "shivers": ("Council", "", "no", "2026 vacancy applicant"),
    "connelley": ("Council", "", "no", "2026 vacancy applicant"),
    "tate": ("Council", "", "no", "2026 vacancy applicant"),
    "mcdonald": ("Council", "", "no", "2026 vacancy applicant"),
}
# COI elected-officer names -> serving seat
COI_SEAT = {
    "wood": ("Mayor", ""), "thomas": ("Council", "2"), "bynum": ("Council", "3"),
    "mitchell": ("Council", "4"), "williams": ("Council", "At-Large"),
    "dewolfe": ("Council", "At-Large"), "glad": ("Council", "1"), "jones": ("Council", "5"),
}


def surname(candidate):
    return candidate.strip().split()[-1].lower().replace(".", "")


def parse_candidate_and_label(e):
    """Return (candidate_display, label, surname_lower) from a manifest entry."""
    t = e["title"]
    if e["source"] == "state_lg_municipal_disclosures":
        # "Surname, Given"
        last, _, given = t.partition(",")
        return f"{given.strip()} {last.strip()}".strip(), "state_filing", last.strip().lower()
    # city archive title: "<Candidate> - <Label> Campaign Financial Disclosure"
    #                 or  "2026 Disclosure - <Candidate>"
    if e["cycle"] == "coi":
        cand = t.split("-", 1)[1].strip() if "-" in t else t
        return cand, "coi", surname(cand)
    cand = t.split(" - ")[0].strip()
    label = t.split(" - ")[1].strip() if " - " in t else ""
    label = re.sub(r"\s*Campaign Financial Disclosure\s*$", "", label, flags=re.I).strip()
    return cand, label, surname(cand)


def classify(e, label, sname):
    """Return (office, district, election_year, filing_type, reporting_period, date,
    date_precision, in_er, matched, jconf, is_incr)."""
    cyc = e["cycle"]
    if cyc == "coi":
        office, district = COI_SEAT.get(sname, ("Council", ""))
        return (office, district, "", "coi_disclosure", "FY2026 annual conflict-of-interest",
                "2026-01-31", "label_year", "n/a", "", "n/a", "")
    if cyc == "2026vac":
        office, district, in_er, note = VACANCY.get(sname, ("Council", "", "no", "2026 vacancy applicant"))
        matched = "IRVIN JONES" if sname == "jones" else ""
        jconf = "person_only" if sname == "jones" else "none"
        return (office, district, "", "summary",
                "2026 council-vacancy appointment disclosure", "2026-01-15",
                "label_inferred", in_er, matched, jconf, "no")
    # election-cycle filing
    office, district, ename, jconf, in_er = ROSTER.get((cyc, sname), ("", "", "", "none", "no"))
    if cyc == "2021":
        return (office, district, "2021", "summary",
                "2021 cycle filing (state LG tree; single per-candidate file)",
                "2021-11-30", "label_inferred", in_er, ename, jconf, "no")
    ll = label.lower()
    if cyc == "2023":
        if "election" in ll:  # "Electionl" = election-period report
            rp, dt = "Election-period report (~Oct 23-Nov 8)", "2023-11-15"
        elif e["adid"] and int(e["adid"]) >= 336:  # second Final group = year-end
            rp, dt = "Final report (year-end; transactions Nov 15+)", "2023-12-31"
        else:  # first Final group = pre-general
            rp, dt = "Final report (pre-general; through ~Oct 22)", "2023-10-31"
        ft = "interim" if "election" in ll else "summary"
        return (office, district, "2023", ft, rp, dt, "label_inferred", in_er, ename, jconf, "no")
    if cyc == "2025":
        if "post election" in ll:
            rp, dt, ft = "Post-general final (Dec 4 filing)", "2025-12-04", "summary"
        elif "election" in ll:
            rp, dt, ft = "Pre-general report (Oct 28 filing)", "2025-10-28", "interim"
        else:  # "Final"
            rp, dt, ft = "Pre-general report (Oct 7 / 28-day filing)", "2025-10-07", "interim"
        return (office, district, "2025", ft, rp, dt, "label_inferred", in_er, ename, jconf, "no")
    return ("", "", "", "", "", "", "", "no", "", "none", "")


CONTRACT = ["date", "candidate", "office", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "retrieved_date", "format",
            "extraction_method", "path"]
EXTRA = ["district", "source", "adid", "is_incremental", "date_precision",
         "in_election_results", "matched_election_candidate", "join_confidence", "sha256"]

rows = []
for e in man:
    cand, label, sname = parse_candidate_and_label(e)
    (office, district, eyear, ftype, rp, date, dprec, in_er, matched, jconf, isincr) = classify(e, label, sname)
    scanned = tm[e["name"]]["scanned"]
    fmt = "scanned" if scanned else "text"
    em = ("none (acquisition-only; scanned image PDF, OCR/vision deferred)" if scanned
          else "none (acquisition-only; born-digital text PDF)")
    title = f"{cand} — South Salt Lake {e['cycle'] if e['cycle'] not in ('coi','2026vac') else ('2026 COI' if e['cycle']=='coi' else '2026 vacancy')} campaign-finance filing ({rp})"
    rows.append({
        "date": date, "candidate": cand, "office": office, "election_year": eyear,
        "filing_type": ftype, "reporting_period": rp, "title": title,
        "source_url": e["url"], "retrieved_date": RETRIEVED, "format": fmt,
        "extraction_method": em, "path": f"raw/{e['name']}",
        "district": district, "source": e["source"], "adid": e["adid"],
        "is_incremental": isincr, "date_precision": dprec,
        "in_election_results": in_er, "matched_election_candidate": matched,
        "join_confidence": jconf, "sha256": sha.get(e["name"], ""),
    })

rows.sort(key=lambda r: (r["election_year"] or "9", r["date"], r["candidate"]))
with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRA)
    w.writeheader()
    w.writerows(rows)
print(f"wrote index.csv: {len(rows)} rows")
from collections import Counter
print("by cycle:", Counter(e["cycle"] for e in man))
print("filing_type:", Counter(r["filing_type"] for r in rows))
print("format:", Counter(r["format"] for r in rows))
