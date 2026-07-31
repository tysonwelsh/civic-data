#!/usr/bin/env python3
"""Build campaign_finance/index.csv for Orem City from manifest.tsv + harvested files.

Reproducible & additive. Reads:
  - manifest.tsv          (candidate/office/election_year/label/source per filing)
  - text/_extract.json    (format + extraction_method per raw file, from make_text.py)
  - raw/_fetch_log.jsonl  (sha256 + bytes per download)
and left-joins each (candidate, election_year) to
  ../election_results/orem_results_by_candidate.csv  (the full ballot universe).
Never writes outside campaign_finance/. Never invents filing amounts.
"""
import csv, json, os, re
from collections import Counter

DS  = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-05"
ER  = "/Users/tysonwelsh/civic-data/orem_city_council/election_results/orem_results_by_candidate.csv"

# ---- filing_type from the city's report label ---------------------------------
SUMMARY_LABELS = {"final", "post", "final report", "post primary report"}
def filing_type(label):
    l = label.strip().lower()
    if l.startswith("annual"):
        return "summary"
    if l in SUMMARY_LABELS:
        return "summary"
    return "interim"   # primary / general / 28-day / 7-day / primary report

# ---- date + precision ---------------------------------------------------------
MONTHS = {m: i+1 for i, m in enumerate(
    ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"])}
STAGE = {  # (election_year, label) -> statutory-ish stage date
    (2023,"primary"):"2023-08-29",(2023,"general"):"2023-10-24",
    (2023,"final"):"2023-11-14",(2023,"post"):"2023-12-21",
    (2025,"primary report"):"2025-08-05",(2025,"post primary report"):"2025-08-20",
    (2025,"28 days before election"):"2025-10-07",
    (2025,"7 days before election"):"2025-10-28",
    (2025,"final report"):"2025-11-25",
}

def parse_date(basename, election_year, label):
    b = basename
    # explicit numeric M.D.YY / M-D-YYYY / M.D.YYYY
    m = re.search(r'(?<!\d)(\d{1,2})[.\-](\d{1,2})[.\-](\d{2,4})(?!\d)', b)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yr < 100: yr += 2000
        if 1 <= mo <= 12 and 1 <= da <= 31 and 2018 <= yr <= 2026:
            return f"{yr:04d}-{mo:02d}-{da:02d}", "day"
    # explicit YYYY-MM-DD
    m = re.search(r'(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})', b)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", "day"
    # Month-name D, YYYY  (e.g. Oct-24-2023, Nov-14-2023, Dec-21-2023)
    m = re.search(r'([A-Za-z]{3})[a-z]*[.\-\s]+(\d{1,2})[.\-,\s]+(20\d{2})', b)
    if m and m.group(1).lower()[:3] in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()[:3]]:02d}-{int(m.group(2)):02d}", "day"
    # annual: label "Annual YYYY" -> Jan 10 statutory deadline of YYYY
    ma = re.match(r'annual\s+(20\d{2})', label.strip().lower())
    if ma:
        return f"{ma.group(1)}-01-10", "annual_deadline"
    # cycle-stage default
    key = (election_year, label.strip().lower())
    if key in STAGE:
        return STAGE[key], "cycle_stage"
    return None, None

# ---- election_results join ----------------------------------------------------
def norm(name):
    n = name.upper()
    n = re.sub(r'"[^"]*"', ' ', n)
    n = n.replace('.', ' ').replace(',', ' ').replace("'", "")
    n = re.sub(r'\b(III|II|JR|SR)\b', ' ', n)
    toks = [t for t in re.sub(r'[^A-Z ]', ' ', n).split() if t]
    return (toks[0], toks[-1]) if toks else ("", "")

er_by_year = {}
_seen = set()
for r in csv.DictReader(open(ER)):
    y = str(r["year"])
    key = (y, r["candidate"])          # one entry per person per year (drop primary/general dup)
    if key in _seen:
        continue
    _seen.add(key)
    er_by_year.setdefault(y, []).append((norm(r["candidate"]), r["candidate"]))

def join(cand, year):
    f, l = norm(cand)
    cands = er_by_year.get(str(year), [])
    for (nf, nl), raw in cands:
        if nf == f and nl == l:
            return raw, "exact"
    last = [(raw, nf) for (nf, nl), raw in cands if nl == l]
    if len(last) == 1:
        return last[0][0], "medium"
    if len(last) > 1:
        fi = [raw for raw, nf in last if nf[:1] == f[:1]]
        if len(fi) == 1:
            return fi[0], "medium"
    return "", "none"

# ---- build --------------------------------------------------------------------
def local_name(up):
    y, m, base = up.split("/", 2)
    return f"{y}{m}_{base}"

extract = json.load(open(os.path.join(DS, "text", "_extract.json")))
sha = {}
with open(os.path.join(DS, "raw", "_fetch_log.jsonl")) as f:
    for line in f:
        d = json.loads(line)
        if d.get("saved_as"):
            sha[d["saved_as"]] = d.get("sha256", "")

BASE = "https://orem.gov/wp-content/uploads/"
rows = []
for r in csv.DictReader(open(os.path.join(DS, "manifest.tsv")), delimiter="\t"):
    up = r["urlpath"].strip()
    name = local_name(up)
    base = os.path.splitext(name)[0]
    cand, office, ey, label = r["candidate"], r["office"], r["election_year"], r["label"]
    ft = filing_type(label)
    date, prec = parse_date(base, int(ey), label)
    if not date:
        y, mm, _ = up.split("/", 2)
        date, prec = f"{y}-{mm}-01", "upload_month"
    ex = extract.get(name, {"format": "na", "extraction_method": "none"})
    matched, conf = join(cand, ey)
    is_annual = label.strip().lower().startswith("annual")
    title = (f"{cand} — Orem City campaign financial statement "
             f"({'Annual report ' if is_annual else ''}{label}, {ey} cycle)")
    rows.append({
        "date": date, "candidate": cand, "office": office, "election_year": ey,
        "filing_type": ft,
        "title": title,
        "source_url": BASE + up,
        "retrieved_date": RETRIEVED,
        "format": ex["format"], "extraction_method": ex["extraction_method"],
        "path": os.path.join("raw", name),
        "reporting_period": label,
        "date_precision": prec,
        "sha256": sha.get(name, ""),
        "source_page": r["source"],
        "matched_election_candidate": matched,
        "join_confidence": conf,
    })

rows.sort(key=lambda r: (r["election_year"], r["candidate"], r["date"]))
# SCHEMA_SPEC §9 contract header, extras after
cols = ["date","candidate","office","election_year","filing_type","reporting_period",
        "title","source_url","retrieved_date","format","extraction_method","path",
        "date_precision","sha256","source_page","matched_election_candidate","join_confidence"]
with open(os.path.join(DS, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# ---- report -------------------------------------------------------------------
print(f"rows: {len(rows)}")
print("by election_year:", dict(sorted(Counter(r["election_year"] for r in rows).items())))
print("by filing_type:", dict(Counter(r["filing_type"] for r in rows)))
print("by format:", dict(Counter(r["format"] for r in rows)))
print("by join_confidence:", dict(Counter(r["join_confidence"] for r in rows)))
print("by date_precision:", dict(Counter(r["date_precision"] for r in rows)))
pairs = {(r["candidate"], r["election_year"]) for r in rows}
joined = {(r["candidate"], r["election_year"]) for r in rows if r["join_confidence"] != "none"}
print(f"distinct (candidate,year) pairs: {len(pairs)}; joined: {len(joined)}")
for c in sorted(pairs - joined):
    print("   UNJOINED:", c)
print("distinct candidates:", len({r["candidate"] for r in rows}))
