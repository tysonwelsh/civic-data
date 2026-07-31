#!/usr/bin/env python3
"""Build campaign_finance/index.csv for Sandy City from the harvested EasyVote filings.

Reproducible: reads raw/easyvote/_manifest.json (produced by the EasyVote harvest) and
raw/easyvote/_api_documentsearch.json (verbatim API listing), derives per-filing metadata,
and left-joins each (candidate, election_year) to the existing election_results dataset.
Additive only — never writes outside campaign_finance/.

election_year rule (documented in CLAUDE.md):
  effective_year = (filing month==Jan/Feb) ? filing_year-1 : filing_year
  election_year  = effective_year if effective_year is odd else effective_year-1
  (Sandy municipal cycles are odd years 2019/2021/2023/2025. A January-filed annual
   report covers the prior calendar year; off-cycle annuals map to the seating cycle.)
"""
import csv, json, os, re

DS  = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(DS, "raw", "easyvote")
MAN = json.load(open(os.path.join(RAW, "_manifest.json")))
PUBLIC_URL = "https://sandycityut.easyvotecampaignfinance.com/home/publicfilings"

# ---- election_results candidate universe -------------------------------------
ER = "/Users/tysonwelsh/civic-data/sandy_city_council/election_results/sandy_results_by_candidate.csv"

def norm(name):
    if not name: return ("","")
    n = name.upper()
    n = re.sub(r"\"[^\"]*\"", " ", n)      # strip "MONICA Z" nickname
    n = re.sub(r"'[^']*'", " ", n)          # strip 'MONICA Z'
    n = n.replace("'", "").replace(".", " ")
    n = re.sub(r"\(NP\)", " ", n)
    n = re.sub(r"[^A-Z ]", " ", n)
    toks = [t for t in n.split() if t]
    if not toks: return ("","")
    return (toks[0], toks[-1])            # (first, last)

er_by_year = {}
for r in csv.DictReader(open(ER)):
    y = r["year"]
    er_by_year.setdefault(y, []).append((norm(r["candidate"]), r["candidate"], r))

def join(first, last, year):
    """Return (matched_name, confidence) against election_results for that year."""
    cands = er_by_year.get(str(year), [])
    f, l = first.upper(), last.upper().replace("'", "")
    # exact first+last
    for (nf, nl), raw, row in cands:
        if nf == f and nl == l:
            return raw, "exact"
    # last only
    lastmatch = [(raw, row) for (nf, nl), raw, row in cands if nl == l]
    if len(lastmatch) == 1:
        return lastmatch[0][0], "medium"
    if len(lastmatch) > 1:
        # disambiguate by first initial
        fi = [(raw, row) for (nf, nl), raw, row in cands if nl == l and nf[:1] == f[:1]]
        if len(fi) == 1:
            return fi[0][0], "medium"
    return "", "none"

def election_year(datesubmitted):
    mm, dd, yy = datesubmitted.split("/")
    fy = 2000 + int(yy); m = int(mm)
    eff = fy - 1 if m in (1, 2) else fy
    return eff if eff % 2 == 1 else eff - 1

def iso_date(datesubmitted):
    mm, dd, yy = datesubmitted.split("/")
    return f"20{yy}-{mm}-{dd}"

def filing_type(name, rp):
    s = (name + " " + rp).lower()
    if "annual" in s or "year end" in s or "year-end" in s or "yr end" in s:
        return "summary"        # year-end annual C&E report
    if re.search(r"\bfinal\b|30 ?day|after (the )?(general|election|primary)|post ?primary|post ?general", s):
        return "summary"        # final/post-election report
    return "interim"            # 28/7-day-before and other periodic C&E reports

def office_norm(o):
    o = o or ""
    if "Mayor" in o: return "Mayor"
    if "At Large" in o or "At-Large" in o: return "Council At-Large"
    m = re.search(r"District\s*(\d)", o)
    if m: return f"Council District {m.group(1)}"
    return o.strip()

rows = []
for m in MAN:
    if not m.get("ok"): continue
    ds = m["datesubmitted"]
    cand = (m["firstname"] + " " + m["lastname"]).strip()
    ey = election_year(ds)
    matched, conf = join(m["firstname"], m["lastname"], ey)
    ftype = filing_type(m["documentname"], "")
    rows.append({
        "date": iso_date(ds),
        "candidate": cand,
        "office": office_norm(m["office"]),
        "election_year": ey,
        "filing_type": ftype,
        "title": f"{cand} — Sandy City Report of Contributions & Expenditures ({m['documentname'].strip()})",
        "source_url": PUBLIC_URL,
        "retrieved_date": "2026-07-05",
        "format": "scanned",
        "extraction_method": "ocr_tesseract",
        "path": os.path.join("raw", "easyvote", m["fname"]),
        "reporting_period": m["documentname"].strip(),
        "document_id": m["documentid"],
        "sha256": m.get("sha256", ""),
        "matched_election_candidate": matched,
        "join_confidence": conf,
        "provider": "EasyVote (ecf-api.easyvoteapp.com)",
    })

# stable sort: candidate, date
rows.sort(key=lambda r: (r["candidate"], r["date"]))

# SCHEMA_SPEC §9 campaign_finance contract header first, city extras after
cols = ["date","candidate","office","election_year","filing_type","reporting_period",
        "title","source_url","retrieved_date","format","extraction_method","path",
        "document_id","sha256","matched_election_candidate","join_confidence","provider"]
with open(os.path.join(DS, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows: w.writerow(r)

# ---- report --------------------------------------------------------------------
from collections import Counter
print(f"rows: {len(rows)}")
print("by election_year:", dict(Counter(r["election_year"] for r in rows)))
print("by filing_type:", dict(Counter(r["filing_type"] for r in rows)))
print("by join_confidence:", dict(Counter(r["join_confidence"] for r in rows)))
pairs = {(r["candidate"], r["election_year"]) for r in rows}
joined = {(r["candidate"], r["election_year"]) for r in rows if r["join_confidence"] != "none"}
print(f"distinct (candidate,year) pairs: {len(pairs)}; joined: {len(joined)}")
for c in sorted(pairs - joined):
    print("   UNJOINED:", c)
