#!/usr/bin/env python3
"""Build campaign_finance/index.csv from the OCR'd disclosure packets.

Each raw PDF is a *combined packet* of individual state "Campaign Finance Report"
forms, one candidate per report. We emit one index row per (candidate, packet),
mapping OCR'd candidate names to the canonical election_results spelling so the
dataset joins to ../election_results/st_george_results_by_candidate.csv.

Candidate identity was read from the OCR sidecar field "Full Name of Candidate".
Where OCR mangled a name, it is assigned by set-elimination against the known
per-cycle candidate roster (candidate_match=inferred); clean OCR matches are
candidate_match=direct. NO amounts are transcribed here (see raw PDFs / text/).
"""
import csv, os

RETRIEVED = "2026-07-02"
FMT = "scanned"
XM = "ocr:tesseract-psm6@200dpi"

# canonical spelling per election_results (exact strings for a clean join)
C = {
    "randall": "MICHELE RANDALL",
    "hughes21": "JIMMIE B. HUGHES", "hughes23": "JIMMIE B. HUGHES", "hughes25": "JIMMIE B HUGHES",
    "woody": "WOODY WOODBURY", "tolly": "BRETT TOLLY",
    "larsen": "NATALIE LARSEN", "tanner": "MICHELLE TANNER", "aldred": "GREG ALDRED",
    "curtis": "VARDELL H CURTIS", "erickson": "M. RICK ERICKSON", "smethurst": "BRYAN S SMETHURST",
    "winder": "KENT L. WINDER", "rwoodbury": "RONALD WOODBURY", "mcdonald": "CAROLYN MCDONALD",
    "novick": "KATHERYNE NOVICK", "bush": "TORI BUSH",
    "kemp": "STEVE KEMP", "larkin": "DANNIELLE LARKIN", "bennett": "BRAD BENNETT",
    "smith": "PAULA SMITH", "mcarthur": "GREGG MCARTHUR", "bulkley": "WENDI PRINCE BULKLEY",
    "mackey": "AROS MACKEY", "jennings": "STEVEN G JENNINGS", "heaton": "MATTHEW L HEATON",
    "knight": "KATHERYNE KNIGHT", "hodges": "AUSTIN HODGES", "willard": "KIMBALL WILLARD",
    "leavitt": "JAMI LEAVITT", "caplin": "NATHAN CAPLIN", "losee": "SHANE LOSEE",
    "thiriot": "BRYAN D. THIRIOT", "razo": "BRANNON R RAZO",
}
M, CO = "Mayor", "Council"
DIR, INF = "direct", "inferred"

SG = "https://sgcityutah.gov"
EIB = SG + "/Documents/Government/Mayor%20And%20Council/Election%20Information"
WB = "https://web.archive.org/web"
SGC = "https://www.sgcity.org/pdf/administration/general/campaignfinancialreports"

# packet: (path, date, date_prec, year, filing_type, period, source_url, orig_url, roster)
# roster entries: (canon_key, office, match)
PACKETS = [
 # ---- 2021 cycle (recovered from Wayback; original host www.sgcity.org) ----
 ("raw/wb20210803_campaignfinancialreports.pdf","2021-08-03","exact",2021,"interim","",
  f"{WB}/20210807165937id_/{SGC}/08032021campaignfinancialreports.pdf",
  f"{SGC}/08032021campaignfinancialreports.pdf",
  [("randall",M,DIR),("hughes21",M,DIR),("woody",M,INF),("tolly",M,INF),
   ("erickson",CO,DIR),("rwoodbury",CO,DIR),("winder",CO,INF),("bush",CO,DIR),
   ("novick",CO,DIR),("aldred",CO,DIR),("smethurst",CO,DIR),("curtis",CO,DIR),
   ("mcdonald",CO,DIR),("larsen",CO,DIR),("tanner",CO,DIR)]),
 ("raw/wb20210909_campaignfinancialreports.pdf","2021-09-09","exact",2021,"summary","",
  f"{WB}/20211230092356id_/{SGC}/09092021campaignfinancialreports.pdf",
  f"{SGC}/09092021campaignfinancialreports.pdf",
  [("woody",M,DIR),("tolly",M,INF),("erickson",CO,DIR),("rwoodbury",CO,DIR),
   ("winder",CO,INF),("bush",CO,DIR),("novick",CO,DIR),("smethurst",CO,DIR),("mcdonald",CO,INF)]),
 ("raw/wb20211026_campaignfinancialdisclosures.pdf","2021-10-26","exact",2021,"interim","",
  f"{WB}/20211228222439id_/{SGC}/10262021campaignfinancialdisclosures.pdf",
  f"{SGC}/10262021campaignfinancialdisclosures.pdf",
  [("randall",M,DIR),("hughes21",M,DIR),("aldred",CO,DIR),("curtis",CO,DIR),
   ("larsen",CO,DIR),("tanner",CO,DIR)]),
 ("raw/wb20211202_campaignfinancialdisclosures.pdf","2021-12-02","exact",2021,"summary","",
  f"{WB}/20211228222338id_/{SGC}/12022021campaignfinancialdisclosures.pdf",
  f"{SGC}/12022021campaignfinancialdisclosures.pdf",
  [("randall",M,DIR),("hughes21",M,DIR),("aldred",CO,DIR),("curtis",CO,DIR),("tanner",CO,DIR)]),
 # ---- 2023 cycle (live on sgcityutah.gov) ----
 ("raw/20230829_campaignfinancedisclosures.pdf","2023-08-29","exact",2023,"interim","2023-01-01..2023-08-24",
  f"{EIB}/20230829campaignfinancedisclosures.pdf", "",
  [("mcarthur",CO,DIR),("mackey",CO,DIR),("hughes23",CO,DIR),("heaton",CO,DIR),("hodges",CO,DIR),
   ("knight",CO,INF),("kemp",CO,DIR),("larkin",CO,DIR),("willard",CO,DIR),("aldred",CO,DIR),
   ("bulkley",CO,DIR),("bennett",CO,DIR),("smith",CO,DIR),("jennings",CO,DIR)]),
 ("raw/2023_financialcampaigndisclosures.pdf","2023-08-29","inferred",2023,"interim","2023-01-01..2023-08-24",
  f"{EIB}/2023financialcampaigndisclosures.pdf", "",
  [("mackey",CO,DIR),("heaton",CO,DIR),("hodges",CO,DIR),("knight",CO,INF),
   ("willard",CO,DIR),("aldred",CO,DIR),("bulkley",CO,DIR),("jennings",CO,DIR)]),
 ("raw/20231024_october242023financialdisclosures.pdf","2023-10-24","exact",2023,"interim","2023-08-25..2023-10-19",
  f"{EIB}/october242023financialdisclosures.pdf", "",
  [("hughes23",CO,DIR),("kemp",CO,DIR),("larkin",CO,DIR),("bennett",CO,DIR),("smith",CO,DIR)]),
 ("raw/20231114_financialdisclosures.pdf","2023-11-14","exact",2023,"interim","2023-10-20..2023-11-09",
  f"{EIB}/20231114financialdisclosures.pdf", "",
  [("hughes23",CO,DIR),("kemp",CO,DIR),("larkin",CO,DIR),("bennett",CO,DIR),("smith",CO,DIR)]),
 ("raw/20231221_campaignfinancedisclosures.pdf","2023-12-21","exact",2023,"summary","2023-11-10..2023-12-21",
  f"{EIB}/20231221campaignfinancedisclosures.pdf", "",
  [("hughes23",CO,DIR),("kemp",CO,DIR),("larkin",CO,DIR),("bennett",CO,DIR),("smith",CO,DIR)]),
 # ---- 2025 cycle (live on sgcityutah.gov) ----
 ("raw/20250805_campaign_finance_reports.pdf","2025-08-05","exact",2025,"interim","",
  f"{SG}/2025.08.05%20Campaign%20Finance%20Reports.pdf", "",
  [("razo",M,INF),("randall",M,DIR),("mackey",M,DIR),("hughes25",M,DIR),
   ("caplin",CO,DIR),("aldred",CO,DIR),("leavitt",CO,INF),("larsen",CO,INF),
   ("losee",CO,INF),("tanner",CO,DIR),("thiriot",CO,INF)]),
 ("raw/20250911_campaign_finance_reports.pdf","2025-09-11","exact",2025,"summary","",
  f"{SG}/2025.09.11%20%20Campaign%20Finance%20Reports.pdf", "",
  [("caplin",CO,DIR),("losee",CO,DIR),("thiriot",CO,INF)]),
 ("raw/20251007_campaign_finance_disclosures.pdf","2025-10-07","exact",2025,"interim","",
  f"{SG}/2025.10.07%20%20Campaign%20Finance%20Disclosures.pdf", "",
  [("randall",M,DIR),("hughes25",M,DIR),("aldred",CO,DIR),("leavitt",CO,DIR),
   ("larsen",CO,DIR),("tanner",CO,DIR)]),
 ("raw/20251028_campaign_finance_disclosures.pdf","2025-10-28","exact",2025,"interim","",
  f"{SG}/Documents/Government/Elections/2025/2025.10.28%20%20Campaign%20Finance%20Disclosures.pdf", "",
  [("randall",M,DIR),("hughes25",M,DIR),("aldred",CO,DIR),("leavitt",CO,DIR),
   ("larsen",CO,DIR),("tanner",CO,DIR)]),
 ("raw/20251204_campaign_finance_disclosures.pdf","2025-12-04","exact",2025,"summary","",
  f"{SG}/2025.12.04%20%20Campaign%20Finance%20Disclosures.pdf", "",
  [("randall",M,DIR),("hughes25",M,DIR),("aldred",CO,DIR),("leavitt",CO,DIR),
   ("larsen",CO,DIR),("tanner",CO,DIR)]),
 # ---- 2023 cycle AMENDMENTS (state channel, DEBT fix 2026-08-01) ----
 # The Lt. Governor Municipal tree (disclosures.utah.gov -> municipal.utah.gov) holds two
 # AMENDED 2023 St. George filings the city site never posted (received 2024-04-01).
 # Single-candidate standalone PDFs, not compilation packets. Larkin's restates the
 # 2023-08-29 pre-primary (contributions $24,690.00 -> $22,555.00); Kemp's restates the
 # 2023-10-24 pre-general with unchanged figures.
 ("raw/municipal20240401_larkin_amended.pdf","2024-04-01","exact",2023,"amended",
  "2023-01-01..2023-08-24 (amended)",
  "http://municipal.utah.gov/washington%5C2024%5CSt.%20George%5C"
  "2024.04.01%20%20Larkin%20Amended%2008.29.2023%20Form.pdf", "",
  [("larkin",CO,DIR)]),
 ("raw/municipal20240401_kemp_amended.pdf","2024-04-01","exact",2023,"amended",
  "2023-08-25..2023-10-19 (amended)",
  "http://municipal.utah.gov/washington%5C2024%5CSt.%20George%5C"
  "2024.04.01%20%20Kemp%20Amended%2010.24.2023%20Form.pdf", "",
  [("kemp",CO,DIR)]),
]

# per-packet overrides for the state-channel amendments (fetched 2026-08-01, born text layer)
RETRIEVED_OVERRIDE = {"raw/municipal20240401_larkin_amended.pdf": "2026-08-01",
                      "raw/municipal20240401_kemp_amended.pdf": "2026-08-01"}
XM_OVERRIDE = {p: "pdftotext-layout(embedded text layer)" for p in RETRIEVED_OVERRIDE}

FT_TITLE = {"interim":"Interim campaign finance report",
            "summary":"Final/year-end campaign finance report",
            "amended":"Amended campaign finance report (supersedes same-period original)"}

def main():
    rows=[]
    for path,date,dprec,year,ft,period,src,orig,roster in PACKETS:
        arch = ("state_disclosures" if "municipal.utah.gov" in src
                else "wayback" if "web.archive.org" in src else "city_live")
        for key,office,match in roster:
            cand=C[key]
            title=f"{FT_TITLE[ft]} — {cand} ({office}, {year})"
            rows.append({
                "date":date,"candidate":cand,"office":office,"election_year":year,
                "filing_type":ft,"title":title,"source_url":src,
                "retrieved_date":RETRIEVED_OVERRIDE.get(path, RETRIEVED),"format":FMT,
                "extraction_method":XM_OVERRIDE.get(path, XM),
                "path":path,"candidate_match":match,"date_precision":dprec,
                "reporting_period":period,"source_archive":arch,"original_url":orig,
            })
    # SCHEMA_SPEC §9 contract header, extras after
    cols=["date","candidate","office","election_year","filing_type","reporting_period",
          "title","source_url","retrieved_date","format","extraction_method","path",
          "candidate_match","date_precision","source_archive","original_url"]
    out=os.path.join(os.path.dirname(__file__),"index.csv")
    with open(out,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows to index.csv")
    # summary
    from collections import Counter
    print("by year:",dict(Counter(r["election_year"] for r in rows)))
    print("by filing_type:",dict(Counter(r["filing_type"] for r in rows)))
    print("inferred names:",sum(1 for r in rows if r["candidate_match"]=="inferred"))

if __name__=="__main__":
    main()
