#!/usr/bin/env python3
"""Build campaign_finance/index.csv for Nephi City from the harvested raw/ filings.

Filing-level index (NOT a structured contribution/expenditure table — that is a
separate planned layer). Every row points at a retained raw scan in raw/ and its
OCR text sidecar in text/. Candidate names are given in the UPPER-CASE form used by
election_results/nephi_results_by_candidate.csv so the join is exact; see
`candidate_match` for join status per row.

Source of truth for the mappings below: the Nephi City DocumentCenter (pages 680
/Disclosures, 618/Candidates, 269/Elections) plus Wayback CDX for de-linked older
cycles. All filings are handwritten scanned "NEPHI CITY CAMPAIGN FINANCIAL REPORT"
forms (format=scanned, OCR'd). Reproducible: re-run after re-harvest.

Idempotent: rewrites index.csv from the tables here.
"""
import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-05"
VURL = "https://www.nephi.utah.gov/DocumentCenter/View/{}"

# ---- columns -------------------------------------------------------------
# SCHEMA_SPEC §9 campaign_finance contract header first, city extras after
COLS = ["date", "candidate", "office", "election_year", "filing_type", "reporting_period",
        "title", "source_url", "retrieved_date", "format", "extraction_method", "path",
        "candidate_match", "date_precision", "view_id", "page_range", "notes"]

# extraction_method: dpi differed by OCR batch (background run used 150 dpi for the
# large Canon scans; everything else 200 dpi).
OCR200 = "ocr:tesseract --psm 6 @200dpi"
OCR150 = "ocr:tesseract --psm 6 @150dpi"
DPI150 = {"3810", "3832", "3833", "3834", "3835", "3836", "3871", "3872", "3873", "3874", "3879"}

rows = []

def add(view_id, filename, candidate, office, year, ftype, date, date_prec,
        period, match, page_range="", notes="", title=None):
    vid = str(view_id)
    method = OCR150 if vid in DPI150 else OCR200
    path = "raw/" + filename
    if title is None:
        ylabel = {"interim": "interim", "summary": "final/summary"}.get(ftype, ftype)
        title = f"{year} {ylabel} campaign financial report — {candidate} ({office})"
    rows.append({
        "date": date, "title": title, "source_url": VURL.format(vid),
        "retrieved_date": RETRIEVED, "format": "scanned", "extraction_method": method,
        "candidate": candidate, "office": office, "election_year": year,
        "filing_type": ftype, "path": path, "candidate_match": match,
        "date_precision": date_prec, "reporting_period": period, "view_id": vid,
        "page_range": page_range, "notes": notes,
    })

# ======================================================================
# 2019 cycle — individual reports (one candidate per PDF). De-linked from the
# live nav but still served live; also present in Wayback (2020-03-05 capture).
# ======================================================================
Y19 = ("2019-11-05", "inferred", "post-general (2019 municipal general)")
add("1199", "cf_1199_Memmott-Financial-Disclosure-Report.pdf", "NATHAN H. MEMMOTT",
    "Council", "2019", "summary", *Y19, match="matched")
add("1200", "cf_1200_Goode-Financial-Disclosure-Report.pdf", "SARAH GOODE",
    "Council", "2019", "summary", *Y19, match="matched")
add("1201", "cf_1201_Ostler-Financial-Disclosure-Report.pdf", "LARRY O. OSTLER",
    "Council", "2019", "summary", *Y19, match="matched")
add("1202", "cf_1202_Seely-Financial-Disclosure-Report.pdf", "JUSTIN D. SEELY",
    "Council", "2019", "summary", *Y19, match="matched")

# ======================================================================
# 2021 cycle — one compilation PDF (View 2118, 12 pp = 6 candidates, 2 pp each).
# Split per candidate; all point at the same raw scan with a page_range.
# Pre-general filings (OCR dates Sept–Oct 2021); Nephi biennial cycle.
# ======================================================================
F21 = "cf_2118_2021-Campaign-Financial-Report.pdf"
Y21 = ("2021-11-02", "inferred", "pre-general interim (Sept–Oct 2021 filings)")
add("2118", F21, "JUSTIN D. SEELY", "Mayor", "2021", "interim", *Y21,
    match="matched", page_range="1-2")
add("2118", F21, "SKIP F. WORWOOD", "Council", "2021", "interim", *Y21,
    match="matched", page_range="3-4")
add("2118", F21, "J.D. PARADY", "Council", "2021", "interim", *Y21,
    match="matched", page_range="5-6")
add("2118", F21, "L. NYLE ROBINSON", "Council", "2021", "interim", *Y21,
    match="matched", page_range="7-8")
add("2118", F21, "JERAMIE L. CALLAWAY", "Council", "2021", "interim", *Y21,
    match="matched", page_range="9-10")
add("2118", F21, "GLADE R. NIELSON", "Mayor", "2021", "interim", *Y21,
    match="matched", page_range="11-12")

# ======================================================================
# 2023 cycle — two compilation PDFs.
#   View 2706 (20 pp): pre-election *interim* filings (OCR dates Jun–Oct 2023).
#                      Contains ~9–10 filer forms — MORE than the 6 general-election
#                      candidates in election_results — incl. names not in that
#                      roster (OCR-read 'Vanessa Goode', 'Carolyn Louise …').
#                      => evidence of a 2023 primary field the elections dataset
#                      does not record. FLAGGED, not edited. See AVAILABILITY.md.
#   View 2803 (11 pp): post-general *final* filings, all dated 11/14/23 = the full
#                      6-candidate general roster.
# ======================================================================
F2706 = "cf_2706_Campaign-Financial-Reports-2023.pdf"
P23i = ("2023-08-15", "inferred", "pre-election interim (Jun–Oct 2023 filings)")
# confidently roster-matched pages
add("2706", F2706, "BART STANLEY MILLER", "Council", "2023", "interim", *P23i,
    match="matched", page_range="1-4", notes="OCR name 'Bart Stanley Miller'; form date 08/28/2023")
add("2706", F2706, "TRAVIS L WORWOOD", "Council", "2023", "interim", *P23i,
    match="matched", page_range="5-6", notes="OCR name 'Travis Larsen Worwood'; form date 10/23/2023")
add("2706", F2706, "SHARI COWAN", "Council", "2023", "interim", *P23i,
    match="matched", page_range="11-12", notes="OCR name 'Shari Cowan'")
add("2706", F2706, "JOHN BRADLEY", "Council", "2023", "interim", *P23i,
    match="matched", page_range="17-18", notes="OCR name 'John Bradley'")
# OCR-read names NOT in election_results (candidate-record gap — flagged)
add("2706", F2706, "VANESSA GOODE", "Council", "2023", "interim", *P23i,
    match="ocr_uncertain;not_in_election_results", page_range="7-8",
    notes="OCR name 'Vanessa Goode'; not in nephi_results_by_candidate.csv — possible 2023 primary-only candidate. FLAG.",
    title="2023 interim campaign financial report — VANESSA GOODE (Council) [OCR-uncertain]")
add("2706", F2706, "CAROLYN LOUISE (surname unclear)", "Council", "2023", "interim", *P23i,
    match="ocr_uncertain;not_in_election_results", page_range="13-14",
    notes="OCR name 'Carolyn Louise …'; not in election_results — possible 2023 primary-only candidate. FLAG.",
    title="2023 interim campaign financial report — CAROLYN LOUISE (Council) [OCR-uncertain]")
# remaining pages: handwritten names illegible — recorded honestly, not attributed
add("2706", F2706, "(unidentified filers)", "Council", "2023", "interim", *P23i,
    match="unreadable", page_range="9-10,15-16,19-20",
    notes="~3 additional filer forms in the compilation with illegible handwritten candidate names; recorded as present, not attributed. See raw scan.",
    title="2023 interim campaign financial reports — 3 unidentified filers (compilation)")

F2803 = "cf_2803_11-14-23-Election-Disclosures.pdf"
P23f = ("2023-11-14", "exact", "post-general final (all forms dated 11/14/2023)")
add("2803", F2803, "J.D. PARADY", "Council", "2023", "summary", *P23f,
    match="matched", page_range="1-2")
add("2803", F2803, "LARRY OSTLER", "Council", "2023", "summary", *P23f,
    match="matched", page_range="3-4")
add("2803", F2803, "JOHN BRADLEY", "Council", "2023", "summary", *P23f,
    match="matched", page_range="5-6")
add("2803", F2803, "SHARI COWAN", "Council", "2023", "summary", *P23f,
    match="matched", page_range="7-8")
add("2803", F2803, "BART STANLEY MILLER", "Council", "2023", "summary", *P23f,
    match="matched", page_range="9-10")
add("2803", F2803, "TRAVIS L WORWOOD", "Council", "2023", "summary", *P23f,
    match="inferred", page_range="11",
    notes="page 11 name illegible; TRAVIS L WORWOOD inferred by elimination (only 2023 general candidate not otherwise present) + leading 'W'.")

# ======================================================================
# 2025 cycle — one PDF per candidate per reporting round. Four upload batches by
# View-id cluster; each batch = one filing deadline, anchored by the date-stamped
# Canon scans of Bart Miller (3750=Aug5, 3810=Oct7, 3834=Oct28, 3879=Dec8).
#   primary 2025-08-12, general 2025-11-04.
# ======================================================================
# batch A — pre-primary interim (anchor 3750 = 2025-08-05)
BA = ("2025-08-05", "batch_inferred", "pre-primary interim (~Aug 5 2025)")
add("3746", "cf_3746_Jeramie-Callaway-Financial-Disclosure-2025.pdf", "JERAMIE L. CALLAWAY", "Council", "2025", "interim", *BA, match="matched")
add("3748", "cf_3748_Scott-Jackson-Financial-Disclosure-2025.pdf", "SCOTT L. JACKSON", "Council", "2025", "interim", *BA, match="matched", notes="only filing on record; lost 2025 primary, did not advance")
add("3749", "cf_3749_Tate-Douglas-Financial-Disclosure-2025.pdf", "TATE T. DOUGLAS", "Council", "2025", "interim", *BA, match="matched")
add("3750", "cf_3750_Bart-Miller-Financial-Disclosure-2025.pdf", "BART STANLEY MILLER", "Council", "2025", "interim", "2025-08-05", "exact", "pre-primary interim", match="matched", notes="CreationDate 2025-08-05 (Canon scan)")
add("3751", "cf_3751_Skip-Worwood-1.pdf", "SKIP F. WORWOOD", "Council", "2025", "interim", *BA, match="matched")
# batch B — early-October filing (anchor 3810 = 2025-10-07; 3809 slug '100625' = Oct 6)
BB = ("2025-10-07", "batch_inferred", "pre-general interim (early Oct 2025)")
add("3804", "cf_3804_Seely-FD.pdf", "JUSTIN D. SEELY", "Mayor", "2025", "interim", *BB, match="matched")
add("3805", "cf_3805_Worwood-FD.pdf", "SKIP F. WORWOOD", "Council", "2025", "interim", *BB, match="matched")
add("3808", "cf_3808_Tate-Douglas.pdf", "TATE T. DOUGLAS", "Council", "2025", "interim", *BB, match="matched")
add("3809", "cf_3809_Jeramie-Callaway-Financial-Disclosure-Form-100625-1.pdf", "JERAMIE L. CALLAWAY", "Council", "2025", "interim", "2025-10-06", "exact", "pre-general interim (early Oct 2025)", match="matched", notes="filename slug '100625' = 2025-10-06")
add("3810", "cf_3810_Bart-Miller-FINANCIAL-REPORT.pdf", "BART STANLEY MILLER", "Council", "2025", "interim", "2025-10-07", "exact", "pre-general interim (early Oct 2025)", match="matched", notes="CreationDate 2025-10-07 (Canon scan)")
# batch C — 7-day pre-general interim (anchor 3834 = 2025-10-28)
BC = ("2025-10-28", "batch_inferred", "pre-general interim (~Oct 28 2025)")
add("3832", "cf_3832_Jeramie-Callaway-Financial-Disclosure.pdf", "JERAMIE L. CALLAWAY", "Council", "2025", "interim", *BC, match="matched")
add("3833", "cf_3833_Tate-Douglas-Financial-Disclosure.pdf", "TATE T. DOUGLAS", "Council", "2025", "interim", *BC, match="matched")
add("3834", "cf_3834_Bart-Miller-Financial-Disclosure.pdf", "BART STANLEY MILLER", "Council", "2025", "interim", "2025-10-28", "exact", "pre-general interim (~Oct 28 2025)", match="matched", notes="CreationDate 2025-10-28 (Canon scan)")
add("3835", "cf_3835_Justin-Seely-Financial-Disclosure.pdf", "JUSTIN D. SEELY", "Mayor", "2025", "interim", *BC, match="matched")
add("3836", "cf_3836_Skip-F-Worwood-Financial-Disclosure.pdf", "SKIP F. WORWOOD", "Council", "2025", "interim", *BC, match="matched")
# batch D — final / year-end summary (anchor 3879 = 2025-12-08)
BD = ("2025-12-08", "batch_inferred", "final/year-end summary (~Dec 8 2025)")
add("3871", "cf_3871_Tate-Douglas-Financial-Disclosure-2025.pdf", "TATE T. DOUGLAS", "Council", "2025", "summary", *BD, match="matched")
add("3872", "cf_3872_Skip-Worwood-Financial-Disclosure-2025.pdf", "SKIP F. WORWOOD", "Council", "2025", "summary", *BD, match="matched")
add("3873", "cf_3873_Jeremie-Callaway-Financial-Disclosure-2025.pdf", "JERAMIE L. CALLAWAY", "Council", "2025", "summary", *BD, match="matched")
add("3874", "cf_3874_Justin-Seely-Financial-Disclosures-2025.pdf", "JUSTIN D. SEELY", "Mayor", "2025", "summary", *BD, match="matched")
add("3879", "cf_3879_Bart-Stanley-Miller-Disclosure.pdf", "BART STANLEY MILLER", "Council", "2025", "summary", "2025-12-08", "exact", "final/year-end summary", match="matched", notes="CreationDate 2025-12-08 (Canon scan)")

# ---- write ---------------------------------------------------------------
out = os.path.join(BASE, "index.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(f"wrote {out}: {len(rows)} rows")

# sanity: every path exists
missing = [r["path"] for r in rows if not os.path.exists(os.path.join(BASE, r["path"]))]
if missing:
    print("MISSING RAW:", missing)
