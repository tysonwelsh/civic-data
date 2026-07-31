#!/usr/bin/env python3
"""Build campaign_finance/index.csv for Holladay (ACQUISITION-ONLY).

§9 contract header first, then documented city extensions. Reads raw/_fetch_log.jsonl
for source_url + sha256, computes born-digital(text)/scanned via pdftotext char count.
No dollar extraction (acquisition layer). Run: python3 holladay_cf_buildindex.py
"""
import os, csv, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"

# name-normalized winner/runner-up set from election_results (for in_election_results)
RACES = os.path.join(HERE, "..", "election_results", "holladay_races.csv")
elect_names = set()
with open(RACES) as f:
    for r in csv.DictReader(f):
        for k in ("winner", "runner_up"):
            v = (r.get(k) or "").strip()
            if v and v.lower() not in ("write-in", ""):
                elect_names.add(v.upper())

def match_election(full_upper):
    # exact, else surname token match against election winner/runner-up names
    if full_upper in elect_names:
        return full_upper, "exact"
    sur = full_upper.split()[-1]
    for e in elect_names:
        if sur and sur in e.split():
            return e, "surname"
    return "", "none"

# per-file metadata: stem -> dict
# fields: candidate, office, district, year, ftype, rp, date, prec, incr
M = {}
def add(stem, candidate, office, district, year, ftype, rp, date, prec, incr="no"):
    M[stem] = dict(candidate=candidate, office=office, district=district, year=year,
                   ftype=ftype, rp=rp, date=date, prec=prec, incr=incr)

# ---- 2017 (BONUS, pre-scope; state folder) ----
add("2017_state_dahle-aug-8","Robert M. Dahle","Mayor","",2017,"interim","Aug 8 2017 (pre-primary/declaration)","2017-08-08","label_date")
add("2017_state_fotheringham-primary","Paul S. Fotheringham","Council","3",2017,"interim","2017 primary declaration","2017-08-08","label_period")
add("2017_state_petersen-aug-8","Sabrina R. Petersen","Council","1",2017,"interim","Aug 8 2017","2017-08-08","label_date")
add("2017_state_roach-aug-8","Dennis Roach","Council","3",2017,"interim","Aug 8 2017","2017-08-08","label_date")

# ---- 2021 (state folder) ----
add("2021_state_dahle-oct","Robert M. Dahle","Mayor","",2021,"interim","Oct 2021 (pre-general)","2021-10-26","inferred_pre_general")
add("2021_state_dahle-final","Robert M. Dahle","Mayor","",2021,"summary","2021 year-end final","2021-11-30","inferred_final")
add("2021_state_brewer-oct","D. Ty Brewer","Council","1",2021,"interim","Oct 2021 (pre-general)","2021-10-26","inferred_pre_general")
add("2021_state_brewer-final","D. Ty Brewer","Council","1",2021,"summary","2021 year-end final","2021-11-30","inferred_final")
add("2021_state_fotheringham-oct","Paul S. Fotheringham","Council","3",2021,"interim","Oct 2021 (pre-general; unopposed)","2021-10-26","inferred_pre_general")
add("2021_state_hilton-oct","Melissa Blackham Hilton","Council","1",2021,"interim","Oct 2021 (pre-general)","2021-10-26","inferred_pre_general")
add("2021_state_hilton-final","Melissa Blackham Hilton","Council","1",2021,"summary","2021 year-end final","2021-11-30","inferred_final")

# ---- 2023 (city page) ----
add("2023_city_drew-7day","Drew B. Quinn","Council","4",2023,"interim","7-day pre-general","2023-10-31","inferred_pre_general")
add("2023_city_drew-10242023","Drew B. Quinn","Council","4",2023,"interim","Oct 24 2023","2023-10-24","label_date")
add("2023_city_drew-final","Drew B. Quinn","Council","4",2023,"summary","2023 year-end final","2023-11-30","inferred_final")
add("2023_city_tracy-7-day","Matthew Collin Tracy","Council","4",2023,"interim","7-day pre-general","2023-10-31","inferred_pre_general")
add("2023_city_tracy","Matthew Collin Tracy","Council","4",2023,"interim","period not stated","2023-11-01","cycle_inferred")
add("2023_city_tracy-final","Matthew Collin Tracy","Council","4",2023,"summary","2023 year-end final","2023-11-30","inferred_final")
add("2023_city_gray","Emily Gray","Council","5",2023,"statement","period not stated (D5 uncontested 2023)","2023-11-01","cycle_inferred")

# ---- 2025 (city page) ----
# Mayor Fotheringham (winner)
add("2025_city_fotheringham-aug2025","Paul S. Fotheringham","Mayor","",2025,"interim","Aug 2025 (pre-primary)","2025-08-05","label_month")
add("2025_city_fotheringham-oct2025","Paul S. Fotheringham","Mayor","",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_fotheringham10282025","Paul S. Fotheringham","Mayor","",2025,"interim","Oct 28 2025 (pre-general)","2025-10-28","label_date")
add("2025_city_fotheringham-final","Paul S. Fotheringham","Mayor","",2025,"summary","2025 year-end final","2025-12-04","inferred_final")
# Mayor Watts (runner-up)
add("2025_city_watts-aug2025","Daren A. Watts","Mayor","",2025,"interim","Aug 2025 (pre-primary)","2025-08-05","label_month")
add("2025_city_watts-financial-disclosure","Daren A. Watts","Mayor","",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_watts-oct282025","Daren A. Watts","Mayor","",2025,"interim","Oct 28 2025 (pre-general)","2025-10-28","label_date")
add("2025_city_watts-final","Daren A. Watts","Mayor","",2025,"summary","2025 year-end final","2025-12-04","inferred_final")
# Mayor Wilson (eliminated in primary)
add("2025_city_wilson-aug","Zac Wilson","Mayor","",2025,"interim","Aug 2025 (pre-primary)","2025-08-05","label_month")
add("2025_city_wilson-final-sept2025","Zac Wilson","Mayor","",2025,"summary","Final Sept 11 2025 (eliminated in primary)","2025-09-11","label_date")
# D1 Sundwall (winner) / Bilstad (runner-up)
add("2025_city_sundwall-oct2025","David Sundwall","Council","1",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_sundwall-10282025","David Sundwall","Council","1",2025,"interim","Oct 28 2025 (pre-general)","2025-10-28","label_date")
add("2025_city_sundwall-final","David Sundwall","Council","1",2025,"summary","2025 year-end final","2025-12-03","label_date")
add("2025_city_bilstad-oct2025","Grant Jacob Bilstad","Council","1",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_bilstad-10282025","Grant Jacob Bilstad","Council","1",2025,"interim","Oct 28 2025 (pre-general)","2025-10-28","label_date")
add("2025_city_bilstad-final","Grant Jacob Bilstad","Council","1",2025,"summary","2025 year-end final","2025-12-02","label_date")
# D3 Bradley (winner) / Jones (runner-up)
add("2025_city_bradley-oct2025","Natalie Bellamy Bradley","Council","3",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_bradley-10282025","Natalie Bellamy Bradley","Council","3",2025,"interim","Oct 24 2025 (pre-general; filed for Oct-28 deadline)","2025-10-24","label_date")  # 2026-07-17: date refined from the form (DATE/reporting-period-end/RECEIVED all 10/24/25); tranche-1 "Fotheringham duplicate" claim was a misread — file is genuinely Bradley
add("2025_city_bradley-final","Natalie Bellamy Bradley","Council","3",2025,"summary","2025 year-end final","2025-12-05","inferred_final")
add("2025_city_jones-oct2025","Bailee Jones","Council","3",2025,"interim","Oct 7 2025 (pre-general)","2025-10-07","label_date")
add("2025_city_jones-10282025","Bailee Jones","Council","3",2025,"interim","Oct 28 2025 (pre-general)","2025-10-28","label_date")
add("2025_city_jones-final","Bailee Jones","Council","3",2025,"summary","2025 year-end final","2025-12-04","label_date")

# ---- COI: Elected Officer Annual Conflict-of-Interest Disclosure (NOT campaign finance) ----
for stem, cand, off, dist, yr in [
    ("2025_city_r-dahle","Robert M. Dahle","Mayor","",2025),
    ("2025_city_t-brewer","D. Ty Brewer","Council","1",2025),
    ("2025_city_p-fotheringham","Paul S. Fotheringham","Council","3",2025),
    ("2025_city_m-durham","Matt Durham","Council","2",2025),
    ("2025_city_d-quinn","Drew B. Quinn","Council","4",2025),
    ("2025_city_e-gray","Emily Gray","Council","5",2025),
    ("coi_city_pfotheringham-2026","Paul S. Fotheringham","Mayor","",2026),
    ("coi_city_dsundwall-2026","David Sundwall","Council","1",2026),
    ("coi_city_nbradley-2026","Natalie Bellamy Bradley","Council","3",2026),
    ("coi_city_mdurham-2026","Matt Durham","Council","2",2026),
    ("coi_city_dquinn-2026","Drew B. Quinn","Council","4",2026),
    ("coi_city_egray-2026","Emily Gray","Council","5",2026),
]:
    add(stem, cand, off, dist, yr, "coi_disclosure", f"FY{yr} annual conflict-of-interest disclosure",
        f"{yr}-01-31", "inferred_annual_deadline", incr="")

# ---- fetch log: url + sha keyed by saved name ----
meta = {}
with open(os.path.join(RAW, "_fetch_log.jsonl")) as f:
    for line in f:
        d = json.loads(line)
        nm = d.get("saved_as") or (d.get("name") or "").rsplit("/",1)[-1]
        if nm:
            meta[nm] = d

def charcount(path):
    try:
        out = subprocess.run(["pdftotext","-layout",path,"-"],capture_output=True,timeout=60).stdout
        return len(b"".join(out.split()))
    except Exception:
        return 0

HEADER = ["date","candidate","office","election_year","filing_type","reporting_period",
          "title","source_url","retrieved_date","format","extraction_method","path",
          "district","source","is_incremental","date_precision",
          "in_election_results","matched_election_candidate","join_confidence","sha256"]

rows = []
for stem, m in M.items():
    fn = stem + ".pdf"
    path_disk = os.path.join(RAW, fn)
    if not os.path.exists(path_disk):
        raise SystemExit("MISSING RAW: " + fn)
    fmt = "text" if charcount(path_disk) >= 200 else "scanned"
    if fmt == "text":
        em = "none (acquisition-only; born-digital text PDF)"
    else:
        em = "none (acquisition-only; scanned image PDF, OCR/vision deferred)"
    fm = meta.get(fn, {})
    url = fm.get("url","")
    sha = fm.get("sha256","")
    src = "state_lg_municipal_disclosures" if "_state_" in stem else "city_cf_page"
    is_coi = m["ftype"] == "coi_disclosure"
    me, jc = match_election(m["candidate"].upper())
    ier = "yes" if me else "no"
    dist = m["district"]
    off_lbl = m["office"]
    kind = "Conflict-of-Interest disclosure" if is_coi else "campaign financial disclosure"
    dlabel = f"District {dist}" if dist else off_lbl
    title = f"{m['candidate']} — Holladay {m['year']} {dlabel} {kind} ({m['rp']})"
    rows.append({
        "date": m["date"], "candidate": m["candidate"], "office": off_lbl,
        "election_year": m["year"], "filing_type": m["ftype"], "reporting_period": m["rp"],
        "title": title, "source_url": url, "retrieved_date": RETRIEVED,
        "format": fmt, "extraction_method": em, "path": f"raw/{fn}",
        "district": dist, "source": src, "is_incremental": m["incr"],
        "date_precision": m["prec"], "in_election_results": ier,
        "matched_election_candidate": me, "join_confidence": jc, "sha256": sha,
    })

rows.sort(key=lambda r: (str(r["election_year"]), r["office"], r["district"], r["candidate"], r["date"]))
with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEADER)
    w.writeheader()
    w.writerows(rows)

cf = [r for r in rows if r["filing_type"] != "coi_disclosure"]
coi = [r for r in rows if r["filing_type"] == "coi_disclosure"]
txt = [r for r in rows if r["format"] == "text"]
print(f"{len(rows)} rows  |  {len(cf)} campaign-finance + {len(coi)} COI  |  text={len(txt)} scanned={len(rows)-len(txt)}")
