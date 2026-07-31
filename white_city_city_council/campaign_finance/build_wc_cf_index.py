#!/usr/bin/env python3
"""Build White City campaign_finance/index.csv from the retained raw/ PDFs.

ACQUISITION-ONLY layer (source type 6 of expand-city-sources). No OCR/vision
extraction, no dollar totals — extraction_method is a deferred-note on every row.
sha256 is pulled from raw/_fetch_log.jsonl by matching the source_url.

§9 campaign_finance contract prefix (exact order):
  date,candidate,office,election_year,filing_type,reporting_period,title,
  source_url,retrieved_date,format,extraction_method,path
White City extras (after the contract, mirrors the Alta CF schema):
  source,date_precision,is_incremental,matched_election_candidate,
  join_confidence,sha256,notes

Idempotent. Run: python3 build_wc_cf_index.py
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"
EXM = "none (raw acquisition; OCR/vision deferred)"
BASE = "https://whitecity.utah.gov"

# sha256 lookup keyed by source_url (from the fetch log)
sha_by_url = {}
with open(os.path.join(RAW, "_fetch_log.jsonl")) as f:
    for line in f:
        d = json.loads(line)
        if d.get("sha256"):
            sha_by_url[d["url"]] = d["sha256"]

CONTRACT = ["date", "candidate", "office", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "retrieved_date",
            "format", "extraction_method", "path"]
EXTRAS = ["source", "date_precision", "is_incremental",
          "matched_election_candidate", "join_confidence", "sha256", "notes"]

# Each spec row: (raw_file, url_path, date, candidate, office, election_year,
#   filing_type, reporting_period, title, fmt, date_precision, is_incremental,
#   matched_election_candidate, join_confidence, notes)
CF = "none (raw acquisition; OCR/vision deferred)"

def cf_rows():
    # 2025 city-era campaign-finance money reports (Utah Code 10-3-208).
    # Three reports per candidate: Prior-to-General (Oct 7), Prior-to-General
    # (Oct 28), Final (Dec 4). These forms restate cycle-to-date figures
    # (confirmed cumulative for Flint) -> is_incremental=no; the Dec-4 Final is
    # the authoritative per-candidate total. DO NOT sum the three (double-count).
    people = [
        # candidate, office, elect_name (UPPER), files: (raw, urlpath, date, per, title-suffix, fmt, note)
        ("Allan Perry", "Mayor", "ALLAN PERRY", [
            ("2025_perry_cf_10-07.pdf", "/files/155e47ca3/AllanPerry_WC_FinancialDisclosure_October7.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "scanned", ""),
            ("2025_perry_cf_10-28.pdf", "/files/e61af8130/AllanPerry_WC_FinancialDisclosure_October28.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "text", ""),
            ("2025_perry_cf_12-04_final.pdf", "/files/b1de31d5b/AllanPerry_WC_FinancialDisclosure_December4.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "scanned", "Won mayor 61.9%."),
        ]),
        ("Paulina Flint", "Mayor", "PAULINA FLINT", [
            ("2025_flint_cf_10-07.pdf", "/files/9bc82467c/10-07-2025+Paulina+Flint+Signed+Campaign+Disclosure.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "text",
             "Contributions incl. $820 self-loan, $500 Yianni Ioannou, $80 Lina Barkey."),
            ("2025_flint_cf_10-28.pdf", "/files/7bcf89e18/10-28-2025+Paulina+Flint+Signed+Campaign+Disclosure.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "text", ""),
            ("2025_flint_cf_12-04_final.pdf", "/files/24515f623/12-04-2025+Paulina+Flint+Signed+Final+Campaign+Disclosure.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "text",
             "Restates same entries as Oct 7 (cumulative filer). Lost mayor race."),
        ]),
        ("Linda Price", "Council At-Large B", "LINDA PRICE", [
            ("2025_price_cf_10-07.pdf", "/files/c1ee93e31/Linda+Price+Oct+7+Financial+Disclosure.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "scanned", ""),
            ("2025_price_cf_10-28.pdf", "/files/ef3fa56a8/Linda+Price+October+28th+Report.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "scanned", ""),
            ("2025_price_cf_12-04_final.pdf", "/files/d949aa9fa/Linda+Price+Dec+4+Report.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "scanned", "Won Seat B 70.4%."),
        ]),
        ("Douglas Denning", "Council At-Large B", "DOUGLAS DENNING", [
            ("2025_denning_cf_10-07.pdf", "/files/2207ea15b/Doug+Denning+WC+Campaign+Financial+Disc+10-7-2025.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "scanned", ""),
            ("2025_denning_cf_10-28.pdf", "/files/0fd4f97b8/Doug+Denning+Oct+28th+Report.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "text", ""),
            ("2025_denning_cf_12-04_final.pdf", "/files/50c15823b/Doug+Denning+Dec+4th+Report.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "text",
             "Write-in candidate; ~$978 self-funded printing/flyer expenditures. Lost."),
        ]),
        ("Neil Mahoney", "Council At-Large C", "NEIL MAHONEY", [
            ("2025_mahoney_cf_10-07.pdf", "/files/67f5d3b0f/White+city+disclosure+10-07-2025+Neil+Mahoney+.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "scanned", ""),
            ("2025_mahoney_cf_10-28.pdf", "/files/42f1768d6/Neil+Mahoney+Oct+28th+Report.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "scanned", ""),
            ("2025_mahoney_cf_12-04_final.pdf", "/files/96da033b4/White+City+Disclosure+12-4-2025+Neil+Mahoney.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "scanned",
             "Won Seat C, unseated incumbent Cardenaz."),
        ]),
        ("Phillip Cardenaz", "Council At-Large C", "PHILLIP CARDENAZ", [
            ("2025_cardenaz_cf_10-07.pdf", "/files/9228dc6ee/PCardenaz_WC+Financial+Disclosure+Form.pdf",
             "2025-10-07", "interim", "Report Prior to General Election (Oct 7)", "text",
             "Contributions $1,050 (Greg Shelton $400, Misty Stoakes $300, Ashtree Legal $250, +$100); "
             "expenditures incl. Victory Signs $389.48, Hobby Lobby $121.40."),
            ("2025_cardenaz_cf_10-28.pdf", "/files/a5012825a/Phil+Cardenaz+Oct+28th+Report.pdf",
             "2025-10-28", "interim", "Report Prior to General Election (Oct 28)", "scanned", ""),
            ("2025_cardenaz_cf_12-04_final.pdf", "/files/42e0a1288/Phill_Cardenaz_Financial_Disclosure_3.pdf",
             "2025-12-04", "summary", "Final Report (Dec 4)", "text",
             "Final under-filled ($0 totals; activity reported on his Oct 7). Incumbent; lost seat."),
        ]),
    ]
    for cand, office, ename, files in people:
        for raw, up, date, ftype, per, fmt, note in files:
            url = BASE + up
            yield dict(date=date, candidate=cand, office=office, election_year="2025",
                       filing_type=ftype, reporting_period=per,
                       title=f"2025 {cand} ({office}) - campaign finance report ({per})",
                       source_url=url, retrieved_date=RETRIEVED, format=fmt,
                       extraction_method=EXM, path=f"raw/{raw}",
                       source="city_website", date_precision="report_type_box",
                       is_incremental="no", matched_election_candidate=ename,
                       join_confidence="high", sha256=sha_by_url.get(url, ""), notes=note)

def coi_rows():
    # Conflict-of-interest disclosures (Utah Code 10-3-1301 / 67-16-1) - a SEPARATE
    # statutory ethics instrument, NOT campaign finance; captured here per the SKILL
    # COI note (classify as filing_type=coi_disclosure). is_incremental blank (not money).
    rows = [
        # raw, urlpath, date, cand, office, elyear, per, fmt, dprec, ename, jconf, note
        ("2025_perry_coi_candidate.pdf", "/files/c2d7a4461/Allan+Perry+-+Mayoral+Candidate.pdf",
         "2025-06-02", "Allan Perry", "Mayor", "2025", "2025 candidate COI", "scanned",
         "candidate_filing_anchor", "ALLAN PERRY", "high",
         "Filename 'Allan Perry - Mayoral Candidate'; candidate ethics disclosure. Date anchored to the June candidacy window."),
        ("2025_denning_coi.pdf", "/files/d9a379caf/Douglas+R+Denning+Conflict+of+Interest+Form.pdf",
         "2025-06-02", "Douglas Denning", "Council At-Large B", "2025", "2025 candidate COI", "scanned",
         "candidate_filing_anchor", "DOUGLAS DENNING", "high", "Date anchored to June candidacy window."),
        ("2025_cardenaz_coi.pdf", "/files/0a7c8b326/phillip_cardenaz_wc_2025_conflict_of_interest.pdf",
         "2025-06-02", "Phillip Cardenaz", "Council At-Large C", "2025", "2025 candidate COI", "scanned",
         "candidate_filing_anchor", "PHILLIP CARDENAZ", "high", "Date anchored to June candidacy window."),
        ("2025_price_coi.pdf", "/files/9db6e5d5f/linda_price_0.pdf",
         "2025-06-02", "Linda Price", "Council At-Large B", "2025", "2025 candidate COI", "scanned",
         "candidate_filing_anchor", "LINDA PRICE", "high", "Date anchored to June candidacy window."),
        ("2025_shelton_coi.pdf", "/files/799c2f6a8/greg_shelton.pdf",
         "2025-01-15", "Greg Shelton", "Council At-Large", "2023", "Elected-officer annual COI (2025)", "text",
         "coi_annual_anchor", "GREG SHELTON", "high",
         "Sitting officer (elected 2023); annual ethics COI. Household fields left blank on the form. Date anchored to the Jan 1-31 filing window."),
        ("2025_huish_coi.pdf", "/files/316207171/tyler_huish.pdf",
         "2025-01-15", "Tyler Huish", "Council At-Large", "2023", "Elected-officer annual COI (2025)", "scanned",
         "coi_annual_anchor", "TYLER HUISH", "high",
         "Sitting officer (elected 2023); annual ethics COI. Date anchored to the Jan 1-31 filing window."),
        ("2026_price_coi.pdf", "/files/c7cd8f6e8/2025+Conflict+of+Interest+%281%29.pdf",
         "2026-01-15", "Linda Price", "Council At-Large B", "2025", "Elected-officer annual COI (2026)", "text",
         "coi_annual_anchor", "LINDA PRICE", "high",
         "Source filename '2025 Conflict of Interest (1)' but the form content is the 2026 annual filing "
         "(Price seated Jan 2026). Date anchored to the Jan 1-31 window."),
        ("2026_perry_coi.pdf", "/files/39aadfb6e/2026+Conflict+of+Interest+-+Allan+Perry+%282%29.pdf",
         "2026-01-15", "Allan Perry", "Mayor", "2025", "Elected-officer annual COI (2026)", "text",
         "coi_annual_anchor", "ALLAN PERRY", "high", "First-term annual officer COI (seated Jan 2026)."),
        ("2026_shelton_coi.pdf", "/files/cc935355a/Greg+Shelton+2026+Conflict+of+Interest.pdf",
         "2026-01-29", "Greg Shelton", "Council At-Large", "2023", "Elected-officer annual COI (2026)", "text",
         "form_signature_date", "GREG SHELTON", "high", "Form dated 1/29/2026."),
        ("2026_huish_coi.pdf", "/files/45eeb3e9b/White+City+2026+Conflict+of+Interest+-+Tyler+Huish.pdf",
         "2026-01-28", "Tyler Huish", "Council At-Large", "2023", "Elected-officer annual COI (2026)", "text",
         "form_signature_date", "TYLER HUISH", "high", "Form dated 1/28/2026."),
    ]
    for raw, up, date, cand, office, elyear, per, fmt, dprec, ename, jconf, note in rows:
        url = BASE + up
        yield dict(date=date, candidate=cand, office=office, election_year=elyear,
                   filing_type="coi_disclosure", reporting_period=per,
                   title=f"{elyear} {cand} ({office}) - conflict-of-interest disclosure ({per})",
                   source_url=url, retrieved_date=RETRIEVED, format=fmt,
                   extraction_method=EXM, path=f"raw/{raw}",
                   source="city_website", date_precision=dprec, is_incremental="",
                   matched_election_candidate=ename, join_confidence=jconf,
                   sha256=sha_by_url.get(url, ""), notes=note)

def main():
    rows = list(cf_rows()) + list(coi_rows())
    # sanity: every path must exist
    for r in rows:
        fp = os.path.join(HERE, r["path"])
        assert os.path.exists(fp), f"missing raw file: {r['path']}"
        assert r["sha256"], f"missing sha256 for {r['source_url']}"
    out = os.path.join(HERE, "index.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRAS)
        w.writeheader()
        # order: CF by candidate then date; COIs after
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows "
          f"({sum(1 for r in rows if r['filing_type']!='coi_disclosure')} CF money reports, "
          f"{sum(1 for r in rows if r['filing_type']=='coi_disclosure')} coi_disclosure)")
    from collections import Counter
    print("format:", dict(Counter(r["format"] for r in rows)))
    print("filing_type:", dict(Counter(r["filing_type"] for r in rows)))

if __name__ == "__main__":
    main()
