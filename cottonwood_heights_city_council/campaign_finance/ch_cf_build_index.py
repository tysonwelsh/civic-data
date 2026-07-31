#!/usr/bin/env python3
"""Build campaign_finance/index.csv for Cottonwood Heights (ACQUISITION-ONLY).

Header = SCHEMA_SPEC §9 campaign_finance contract, then city-specific extras.
Derives source_url + sha256 from raw/_fetch_log.jsonl and format (text/scanned)
from the PDF itself; all human classification (candidate/office/district/
filing_type/period/date) is the explicit per-file table below. No dollars are
extracted (extraction deferred). Idempotent: re-run to regenerate index.csv.
"""
import os, re, json, csv, glob, fitz

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"
EXTRACT = "none (raw acquisition; OCR/vision deferred)"

# --- provenance from the fetch log: name -> (url, sha256) -------------------
LOG = {}
with open(os.path.join(RAW, "_fetch_log.jsonl")) as fh:
    for line in fh:
        d = json.loads(line)
        nm = d.get("saved_as") or os.path.basename(d.get("url", ""))
        LOG[nm] = (d.get("url", ""), d.get("sha256", ""))


def fmt_of(path):
    doc = fitz.open(path)
    txt = ""
    for pg in doc:
        txt += pg.get_text()
        if len(txt) > 400:
            break
    return "text" if len(txt.strip()) >= 200 else "scanned"


# --- election-roster match (UPPER names in cottonwood_heights_races.csv) -----
MATCH = {
    (2017, "peterson"): "MIKE PETERSON",
    (2019, "petersen"): "DOUGLAS PETERSEN", (2019, "case"): "DEBORAH CASE",
    (2019, "bracken"): "SCOTT BRACKEN", (2019, "hallbeck"): "TIM HALLBECK",
    (2021, "newell"): "SHAWN E. NEWELL", (2021, "hanson"): "MIKE HANSON",
    (2021, "birrell"): "ELLEN BIRRELL", (2021, "kim"): "ERNIE KIM",
    (2021, "weichers"): "MIKE WEICHERS", (2021, "wiechers"): "MIKE WEICHERS",
    (2021, "kraan"): "ERIC KRAAN",
    (2023, "holton"): "MATT HOLTON", (2023, "cottam"): "JEN COTTAM",
    (2023, "cottham"): "JEN COTTAM", (2023, "hyland"): "SUZANNE HYLAND",
    (2023, "daurelle"): "SHARON DAURELLE",
    (2025, "newell"): "SHAWN NEWELL", (2025, "prazen"): "RANDY PRAZEN",
    (2025, "birrell"): "ELLEN BIRRELL", (2025, "kim"): "ERNIE KIM",
    (2025, "bennion"): "GAY LYNN BENNION", (2025, "weichers"): "MIKE WEICHERS",
}


def match(year, lastkey):
    nm = MATCH.get((year, lastkey))
    return (nm, "high") if nm else ("", "none")


# columns after path: district,source,date_precision,is_incremental,
#                     matched_election_candidate,join_confidence,sha256
# ROW = (fname, date, candidate, office, year, filing_type, period, title,
#        district, source, date_precision, lastkey)
ST = "state_lg_municipal_disclosures"
CY = "city_elections_page"


def R(fname, date, cand, office, year, ftype, period, title, district, source, prec, lastkey):
    return dict(fname=fname, date=date, candidate=cand, office=office, year=year,
                filing_type=ftype, period=period, title=title, district=district,
                source=source, prec=prec, lastkey=lastkey)


ROWS = []

# ============================ 2017 (bonus, aggregate combined filings) =======
ROWS += [
    R("2017_state_candidates-financial-disclosures-for-october-31-2017.pdf",
      "2017-10-31", "(multiple candidates — combined filing)", "", 2017, "interim",
      "Pre-general combined disclosures (Oct 31 2017)",
      "Cottonwood Heights 2017 candidates — combined pre-general financial disclosures (Oct 31 2017)",
      "", ST, "filename_filing_date", None),
    R("2017_state_ch-municipal-campaign-financial-reports-12-7-2017.pdf",
      "2017-12-07", "(multiple candidates — combined filing)", "", 2017, "summary",
      "Year-end combined final reports (Dec 7 2017)",
      "Cottonwood Heights 2017 candidates — combined year-end campaign financial reports (Dec 7 2017)",
      "", ST, "filename_filing_date", None),
    R("2017_state_financial-report-dist-3-and-amended-dist-4-new.pdf",
      "2017-12-07", "(multiple candidates — combined filing)", "Council", 2017, "summary",
      "District 3 + amended District 4 combined report",
      "Cottonwood Heights 2017 — District 3 and AMENDED District 4 combined financial report",
      "", ST, "cycle_anchor_year_end", None),
    R("2017_state_tonia-dalton-financial-disclosure-8-31-17.pdf",
      "2017-08-31", "Tonia Dalton", "Council", 2017, "statement",
      "Pre-primary financial disclosure (Aug 31 2017)",
      "Tonia Dalton — Cottonwood Heights campaign financial disclosure (Aug 31 2017)",
      "", ST, "filename_filing_date", "dalton"),
]

# ============================ 2019 (bonus, D1/D2 cycle) ======================
# general 2019-11-05; primary 2019-08-13
ROWS += [
    R("2019_state_petersen-douglas-financial-reporting-oct-2019.pdf", "2019-10-01",
      "Douglas Petersen", "Council", 2019, "interim", "Pre-general report (Oct 2019)",
      "Douglas Petersen — Cottonwood Heights campaign financial report (Oct 2019)", "1", ST, "label_month", "petersen"),
    R("2019_state_douglas-petersen-financial-reporting-for-dec-5-2019.pdf", "2019-12-05",
      "Douglas Petersen", "Council", 2019, "summary", "Year-end report (Dec 5 2019)",
      "Douglas Petersen — Cottonwood Heights campaign financial report (Dec 5 2019)", "1", ST, "filename_filing_date", "petersen"),
    R("2019_state_douglas-petersen-amended-financial-disclosure.pdf", "2019-11-05",
      "Douglas Petersen", "Council", 2019, "statement", "AMENDED financial disclosure statement",
      "Douglas Petersen — AMENDED Cottonwood Heights financial disclosure statement", "1", ST, "cycle_anchor_general_election_day", "petersen"),
    R("2019_state_case-deborah-financial-reporting-oct-2019.pdf", "2019-10-01",
      "Deborah Case", "Council", 2019, "interim", "Pre-general report (Oct 2019)",
      "Deborah Case — Cottonwood Heights campaign financial report (Oct 2019)", "1", ST, "label_month", "case"),
    R("2019_state_deborah-case-financial-reporting-for-dec-5-2019.pdf", "2019-12-05",
      "Deborah Case", "Council", 2019, "summary", "Year-end report (Dec 5 2019)",
      "Deborah Case — Cottonwood Heights campaign financial report (Dec 5 2019)", "1", ST, "filename_filing_date", "case"),
    R("2019_state_deborah-case-amended-campaign-financial-report-8-23-19.pdf", "2019-08-23",
      "Deborah Case", "Council", 2019, "interim", "AMENDED pre-primary report (Aug 23 2019)",
      "Deborah Case — AMENDED Cottonwood Heights campaign financial report (Aug 23 2019)", "1", ST, "filename_filing_date", "case"),
    R("2019_state_deborah-case-financial-disclosure-primary.pdf", "2019-08-13",
      "Deborah Case", "Council", 2019, "statement", "PRIMARY financial disclosure statement",
      "Deborah Case — Cottonwood Heights PRIMARY financial disclosure statement (2019)", "1", ST, "cycle_anchor_primary_election_day", "case"),
    R("2019_state_christopher-mchugh-financial-disclosure-primary.pdf", "2019-08-13",
      "Christopher McHugh", "Council", 2019, "statement", "PRIMARY financial disclosure statement",
      "Christopher McHugh — Cottonwood Heights PRIMARY financial disclosure statement (2019)", "1", ST, "cycle_anchor_primary_election_day", "mchugh"),
    R("2019_state_christopher-mchugh-municipal-campaign-financial-reporting-september-10-2019.pdf", "2019-09-10",
      "Christopher McHugh", "Council", 2019, "interim", "Report (Sept 10 2019, primary season)",
      "Christopher McHugh — Cottonwood Heights municipal campaign financial report (Sept 10 2019)", "1", ST, "filename_filing_date", "mchugh"),
    R("2019_state_bracken-scott-financial-reporting-oct-2019.pdf", "2019-10-01",
      "Scott Bracken", "Council", 2019, "interim", "Pre-general report (Oct 2019)",
      "Scott Bracken — Cottonwood Heights campaign financial report (Oct 2019)", "2", ST, "label_month", "bracken"),
    R("2019_state_scott-bracken-financial-reporting-for-dec-5-2019.pdf", "2019-12-05",
      "Scott Bracken", "Council", 2019, "summary", "Year-end report (Dec 5 2019)",
      "Scott Bracken — Cottonwood Heights campaign financial report (Dec 5 2019)", "2", ST, "filename_filing_date", "bracken"),
    R("2019_state_hallbeck-timothy-e-financial-reporting-oct-2019.pdf", "2019-10-01",
      "Timothy E. Hallbeck", "Council", 2019, "interim", "Pre-general report (Oct 2019)",
      "Timothy E. Hallbeck — Cottonwood Heights campaign financial report (Oct 2019)", "2", ST, "label_month", "hallbeck"),
]

# ============================ 2021 (D3/D4/Mayor) =============================
# general 2021-11-02; final due ~2022-01-10
def two21(lastkey, cand, office, district, cand_file, final_file=None, amended_file=None):
    out = [R(cand_file, "2021-11-02", cand, office, 2021, "interim",
             "Pre-general financial statement",
             f"{cand} — Cottonwood Heights candidate financial statement (2021, pre-general)",
             district, ST, "cycle_anchor_general_election_day", lastkey)]
    if amended_file:
        out.append(R(amended_file, "2021-11-02", cand, office, 2021, "interim",
                     "AMENDED pre-general financial statement",
                     f"{cand} — AMENDED Cottonwood Heights candidate financial statement (2021)",
                     district, ST, "cycle_anchor_general_election_day", lastkey))
    if final_file:
        out.append(R(final_file, "2022-01-10", cand, office, 2021, "summary",
                     "Year-end final financial report",
                     f"{cand} — Cottonwood Heights final financial report (2021 cycle)",
                     district, ST, "statutory_year_end_deadline", lastkey))
    return out

ROWS += two21("newell", "Shawn Newell", "Council", "3",
              "2021_state_shawn-newell-cottonwood-heights-candidate-for-district-3.pdf",
              "2021_state_shawn-newell-final-financial-report.pdf",
              "2021_state_shawn-newell-amended-cottonwood-heights-candidate-for-district-3.pdf")
ROWS += two21("hanson", "Michael Hanson", "Council", "3",
              "2021_state_michael-hanson-cottonwood-heights-candidate-for-district-3.pdf",
              "2021_state_michael-hanson-final-financial-report.pdf")
ROWS += two21("rawlings", "David Rawlings", "Council", "3",
              "2021_state_david-rawlings-cottonwood-heights-candidate-for-district-3.pdf",
              "2021_state_david-rawlings-final-financial-report.pdf",
              "2021_state_david-rawlings-amended-cottonwood-heights-candidate-for-district-3.pdf")
ROWS += two21("boman", "Runar Boman", "Council", "3",
              "2021_state_runar-boman-cottonwood-heights-candidate-for-district-3.pdf",
              "2021_state_runar-boman-final-financial-report.pdf")
# McShaffrey: candidate statement only, no final
ROWS += two21("mcshaffrey", "E. Samuel McShaffrey", "Council", "3",
              "2021_state_e-samuel-mcshaffrey-cottonwood-heights-candidate-for-district-3.pdf")
ROWS += two21("birrell", "Ellen Birrell", "Council", "4",
              "2021_state_ellen-birrell-cottonwood-heights-candidate-for-district-4.pdf",
              "2021_state_ellen-birrell-final-financial-report.pdf")
ROWS += two21("kim", "Ernie Kim", "Council", "4",
              "2021_state_ernie-kim-cottonwood-heights-candidate-for-district-4.pdf",
              "2021_state_ernie-kim-final-financial-report.pdf",
              "2021_state_ernie-kim-amended-cottonwood-heights-candidate-for-district-4.pdf")
ROWS += two21("walker", "Lee Anne Walker", "Council", "4",
              "2021_state_lee-anne-walker-cottonwood-heights-candidate-for-district-4.pdf",
              "2021_state_lee-anne-walker-final-financial-report.pdf")
ROWS += two21("weichers", "Mike Weichers", "Mayor", "",
              "2021_state_michael-wiechers-cottonwood-heights-candidate-for-mayor.pdf",
              "2021_state_mike-weichers-fina-financial-report.pdf")
ROWS += two21("kraan", "Eric Kraan", "Mayor", "",
              "2021_state_eric-kraan-cottonwood-heights-candidate-for-mayor.pdf",
              "2021_state_eric-kraan-final-financial-report.pdf")
ROWS += two21("evans", "Maile Evans", "Mayor", "",
              "2021_state_maile-evans-cottonwood-heights-candidate-for-mayor.pdf",
              "2021_state_maile-evans-final-financial-report.pdf")
ROWS += two21("hallbeck", "Timothy Hallbeck", "Mayor", "",
              "2021_state_timothy-hallbeck-cottonwood-heights-candidate-for-mayor.pdf",
              "2021_state_timothy-hallbeck-final-financial-report.pdf")
# Schwartz: candidate statement only, no final
ROWS += two21("schwartz", "Edward Schwartz", "Mayor", "",
              "2021_state_edward-schwartz-cottonwood-heights-candidate-for-mayor.pdf")

# ============================ 2023 (D1/D2) ==================================
# general 2023-11-21; primary 2023-08-15; final due ~2024-01-10
ROWS += [
    # D1 Holton (winner) vs Cottam
    R("2023_state_matt-holton.pdf", "2023-11-21", "Matt Holton", "Council", 2023, "interim",
      "Pre-general financial statement",
      "Matt Holton — Cottonwood Heights candidate financial statement (2023, pre-general)", "1", ST, "cycle_anchor_general_election_day", "holton"),
    R("2023_state_matt-holton-final.pdf", "2024-01-10", "Matt Holton", "Council", 2023, "summary",
      "Year-end final financial report",
      "Matt Holton — Cottonwood Heights final financial report (2023 cycle)", "1", ST, "statutory_year_end_deadline", "holton"),
    R("2023_state_jen-cottam.pdf", "2023-11-21", "Jen Cottam", "Council", 2023, "interim",
      "Pre-general financial statement",
      "Jen Cottam — Cottonwood Heights candidate financial statement (2023, pre-general)", "1", ST, "cycle_anchor_general_election_day", "cottam"),
    R("2023_state_jen-cottham-financial-disclosure-report-10-24-2023.pdf", "2023-10-24", "Jen Cottam", "Council", 2023, "interim",
      "Interim financial disclosure report (Oct 24 2023)",
      "Jen Cottam — Cottonwood Heights financial disclosure report (Oct 24 2023)", "1", ST, "filename_filing_date", "cottham"),
    R("2023_state_jen-cottham-campaign-contributions-expenditure-10-24-23.pdf", "2023-10-24", "Jen Cottam", "Council", 2023, "interim",
      "Contributions/expenditures schedule (Oct 24 2023)",
      "Jen Cottam — Cottonwood Heights campaign contributions/expenditure schedule (Oct 24 2023)", "1", ST, "filename_filing_date", "cottham"),
    R("2023_state_jen-cottam-final.pdf", "2024-01-10", "Jen Cottam", "Council", 2023, "summary",
      "Year-end final financial report",
      "Jen Cottam — Cottonwood Heights final financial report (2023 cycle)", "1", ST, "statutory_year_end_deadline", "cottam"),
    # D2 Hyland (winner) vs Daurelle; Bracken = eliminated 3rd primary candidate
    R("2023_state_suzanne-hyland.pdf", "2023-11-21", "Suzanne Hyland", "Council", 2023, "interim",
      "Pre-general financial statement",
      "Suzanne Hyland — Cottonwood Heights candidate financial statement (2023, pre-general)", "2", ST, "cycle_anchor_general_election_day", "hyland"),
    R("2023_state_suzanne-hyland-financial-disclosure-report-10-24-2023.pdf", "2023-10-24", "Suzanne Hyland", "Council", 2023, "interim",
      "Interim financial disclosure report (Oct 24 2023)",
      "Suzanne Hyland — Cottonwood Heights financial disclosure report (Oct 24 2023)", "2", ST, "filename_filing_date", "hyland"),
    R("2023_state_suzanne-hyland-final.pdf", "2024-01-10", "Suzanne Hyland", "Council", 2023, "summary",
      "Year-end final financial report",
      "Suzanne Hyland — Cottonwood Heights final financial report (2023 cycle)", "2", ST, "statutory_year_end_deadline", "hyland"),
    R("2023_state_sharon-daurelle.pdf", "2023-11-21", "Sharon Daurelle", "Council", 2023, "interim",
      "Pre-general financial statement",
      "Sharon Daurelle — Cottonwood Heights candidate financial statement (2023, pre-general)", "2", ST, "cycle_anchor_general_election_day", "daurelle"),
    R("2023_state_sharon-daurelle-final.pdf", "2024-01-10", "Sharon Daurelle", "Council", 2023, "summary",
      "Year-end final financial report",
      "Sharon Daurelle — Cottonwood Heights final financial report (2023 cycle)", "2", ST, "statutory_year_end_deadline", "daurelle"),
    R("2023_state_scott-bracken.pdf", "2023-09-05", "Scott Bracken", "Council", 2023, "statement",
      "Pre-primary financial statement (eliminated D2 primary candidate)",
      "Scott Bracken — Cottonwood Heights candidate financial statement (2023 D2 primary)", "2", ST, "cycle_anchor_primary_election_day", "bracken"),
    R("2023_state_scott-bracken-district-2.pdf", "2023-09-05", "Scott Bracken", "Council", 2023, "statement",
      "Pre-primary financial statement — District 2 (eliminated D2 primary candidate)",
      "Scott Bracken — Cottonwood Heights District 2 candidate financial statement (2023 primary)", "2", ST, "cycle_anchor_primary_election_day", "bracken"),
]

# ============================ 2025 city (D3/D4/Mayor) ========================
# general 2025-11-04; interims Oct 7 / Oct 28; final Dec 4
CAND25 = [
    ("weichers", "Mike Weichers", "Mayor", ""),
    ("newell", "Shawn Newell", "Council", "3"),
    ("birrell", "Ellen Birrell", "Council", "4"),
    ("prazen", "Randy Prazen", "Council", "3"),
    ("kim", "Ernie Kim", "Council", "4"),
    ("bennion", "Gay Lynn Bennion", "Mayor", ""),
]
for lk, cand, office, district in CAND25:
    ROWS += [
        R(f"2025_city_{lk}_initial-financial-disclosure-statement.pdf", "2025-11-04",
          cand, office, 2025, "statement", "Initial financial disclosure statement",
          f"{cand} — Cottonwood Heights initial financial disclosure statement (2025)",
          district, CY, "cycle_anchor_general_election_day", lk),
        R(f"2025_city_{lk}_conflict-of-interest-disclosure.pdf", "2025-11-04",
          cand, office, 2025, "conflict_of_interest", "Candidate conflict-of-interest disclosure",
          f"{cand} — Cottonwood Heights candidate conflict-of-interest disclosure (2025)",
          district, CY, "cycle_anchor_general_election_day", lk),
        R(f"2025_city_{lk}_interim-oct-7-2025.pdf", "2025-10-07",
          cand, office, 2025, "interim", "Interim report (Oct 7 2025)",
          f"{cand} — Cottonwood Heights campaign financial report (Oct 7 2025)",
          district, CY, "label_report_date", lk),
        R(f"2025_city_{lk}_interim-oct-28-2025.pdf", "2025-10-28",
          cand, office, 2025, "interim", "Interim report (Oct 28 2025)",
          f"{cand} — Cottonwood Heights campaign financial report (Oct 28 2025)",
          district, CY, "label_report_date", lk),
        R(f"2025_city_{lk}_final-dec-4-2025.pdf", "2025-12-04",
          cand, office, 2025, "summary", "Final report (Dec 4 2025)",
          f"{cand} — Cottonwood Heights final campaign financial report (Dec 4 2025)",
          district, CY, "label_report_date", lk),
    ]

# --- emit -------------------------------------------------------------------
HEADER = ["date", "candidate", "office", "election_year", "filing_type",
          "reporting_period", "title", "source_url", "retrieved_date", "format",
          "extraction_method", "path", "district", "source", "date_precision",
          "is_incremental", "matched_election_candidate", "join_confidence", "sha256"]

disk = {os.path.basename(p) for p in glob.glob(os.path.join(RAW, "*.pdf"))}
seen = set()
out = []
missing = []
for r in ROWS:
    fn = r["fname"]
    seen.add(fn)
    if fn not in disk:
        missing.append(fn)
        continue
    url, sha = LOG.get(fn, ("", ""))
    mname, mconf = match(r["year"], r["lastkey"]) if r["lastkey"] else ("", "none")
    out.append([
        r["date"], r["candidate"], r["office"], r["year"], r["filing_type"],
        r["period"], r["title"], url, RETRIEVED, fmt_of(os.path.join(RAW, fn)),
        EXTRACT, f"raw/{fn}", r["district"], r["source"], r["prec"],
        "no", mname, mconf, sha,
    ])

out.sort(key=lambda x: (x[3], x[12], x[1], x[0]))  # year, district, candidate, date
with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(HEADER)
    w.writerows(out)

unindexed = sorted(disk - seen)
print(f"indexed {len(out)} rows; {len(disk)} pdfs on disk")
if missing:
    print("WARN metadata rows with no file on disk:", missing)
if unindexed:
    print("WARN pdfs on disk with no metadata row:", unindexed)
