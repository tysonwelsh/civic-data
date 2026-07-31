#!/usr/bin/env python3
"""Build emigration_canyon_city_council/campaign_finance/index.csv (SCHEMA_SPEC.md §9 contract).

ACQUISITION-ONLY layer (source type 6 of /expand-city-sources). No OCR/vision dollar
extraction and no totals are computed here: `extraction_method` is uniform
`none (raw acquisition; text/OCR/vision deferred)` on every row.

The SPEC table below is hard-coded from:
  * the SLCo Clerk static metro-township-councils archive's "Emigration Canyon Township /
    Emigration Township Council At Large" section — each PDF anchor is grouped under an
    explicit "<YYYY> Financial Disclosure Reporting" year header AND a "Last, First"
    candidate header on the page itself (raw/_slco_metro_township_archive.html), so the
    election_year is read from the COUNTY PAGE structure, not OCR of the form
    (date_precision = county_page_year_label; the 2016 files also carry the year in their
    /2016_disclosures/ URL path -> county_folder_ym), and
  * the City of Emigration Canyon Wix site (emigration.utah.gov):
      - /election-information  -> 2025 candidate CAMPAIGN-FINANCE statements
        ("Report of Contributions and Expenditures", Utah Code 10-3-208; primary report
        DUE Aug 5 2025) for the four named 2025 primary candidates.
      - /copy-of-disclosure-statements -> current elected-officer CONFLICT-OF-INTEREST
        forms (Utah Code 10-3-1301 / 10-3-1313) -> filing_type=coi_disclosure (SKILL COI note).

Everything mechanical (sha256, format = born-digital-text vs scanned via pdftotext char
count, source_url) is recomputed from disk + raw/_fetch_log.jsonl, never hard-coded. Idempotent.

    python3 build_emigration_cf_index.py
"""
import csv, hashlib, json, os, subprocess, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-14"
EXTRACTION = "none (raw acquisition; text/OCR/vision deferred)"

# filename (in raw/) -> spec tuple
# (date, candidate, office, election_year, filing_type, reporting_period,
#  source, date_precision, matched_election_candidate, join_confidence, notes)
SPEC = {
    # ================= SLCo Clerk static archive (source=slco_clerk_static) =================
    # ---- 2016 founding metro-township council cohort (page header "Emigration Township
    #      Council At Large", year header "2016 Financial Disclosure Reporting"). The
    #      founding contest is Nov 2016 (terms began 2017-01-01). election_results labels
    #      the founding @LRG contest 2017 and preserves only Smolka+Bowen -> the broad 2016
    #      founding field is ABSENT (flag #1). Seat is at-large (no seat letter). ----
    "2016_nov_jennifer-hawkes.pdf": ("2016-11-01", "Jennifer Hawkes", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "JENNIFER HAWKES", "medium", "2016 founding cohort (county page 'Emigration Township Council At Large' / '2016 Financial Disclosure Reporting'). Hawkes is a certified 2023 winner; the 2016 founding contest is absent from election_results (labeled 2017 there) - flag #1."),
    "2016_dec-dissolution_jennifer-hawkes.pdf": ("2016-12-01", "Jennifer Hawkes", "Metro Township Council (founding, at-large)", "2016", "summary", "Dissolution report (December)", "slco_clerk_static", "county_folder_ym", "JENNIFER HAWKES", "medium", "2016 founding cohort; committee-dissolution/closing report (county 'dissolutions' folder). See flag #1."),
    "2016_nov_steve-hook.pdf": ("2016-11-01", "Steve Hook", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort. Steve Hook is an early council member of record (meeting_minutes/roster 'Steve Hook, brief') but is NOT in election_results council rows - flag #1. NOT the Improvement District (county filed this under the township council)."),
    "2016_dec-dissolution_steve-hook.pdf": ("2016-12-01", "Steve Hook", "Metro Township Council (founding, at-large)", "2016", "summary", "Dissolution report (December)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort; dissolution/closing report. Hook not in election_results - flag #1."),
    "2016_nov_bob-staggers.pdf": ("2016-11-01", "Bob Staggers", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort. The county filed this under the Emigration TOWNSHIP COUNCIL section (NOT the Emigration Improvement District, though B. Staggers later appears on the ID board - do not conflate). Not in election_results council rows - flag #1."),
    "2016_dec-dissolution_bob-staggers.pdf": ("2016-12-01", "Bob Staggers", "Metro Township Council (founding, at-large)", "2016", "summary", "Dissolution report (December)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort; dissolution/closing report. Township-council filing, not Improvement District. Flag #1."),
    "2016_nov_joe-smolka.pdf": ("2016-11-01", "Joe Smolka", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "JOE SMOLKA", "medium", "2016 founding cohort. Smolka is the 2017 @LRG WINNER and township-era presiding Mayor. Founding contest absent from election_results (flag #1)."),
    "2016_dec_joe-smolka.pdf": ("2016-12-01", "Joe Smolka", "Metro Township Council (founding, at-large)", "2016", "summary", "Year-end summary (December)", "slco_clerk_static", "county_folder_ym", "JOE SMOLKA", "medium", "2016 founding cohort year-end summary (county '2016_year_end' folder). See flag #1."),
    "2016_nov_gary-bowen.pdf": ("2016-11-01", "Gary Bowen", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "GARY BOWEN", "medium", "2016 founding cohort. Bowen is a 2017 @LRG WINNER. Founding contest absent from election_results (flag #1)."),
    "2016_dec_gary-bowen.pdf": ("2016-12-01", "Gary Bowen", "Metro Township Council (founding, at-large)", "2016", "summary", "Year-end summary (December)", "slco_clerk_static", "county_folder_ym", "GARY BOWEN", "medium", "2016 founding cohort year-end summary ('gary-bowen_final'). See flag #1."),
    "2016_nov_david-paul-brems.pdf": ("2016-11-01", "David Paul Brems", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "DAVID PAUL BREMS", "medium", "2016 founding cohort. Brems is a certified 2023 winner and current city Mayor. Founding contest absent from election_results (flag #1)."),
    "2016_dec_david-paul-brems.pdf": ("2016-12-01", "David Paul Brems", "Metro Township Council (founding, at-large)", "2016", "summary", "Year-end summary (December)", "slco_clerk_static", "county_folder_ym", "DAVID PAUL BREMS", "medium", "2016 founding cohort year-end summary. See flag #1."),
    "2016_nov_rick-raile.pdf": ("2016-11-01", "Rick Raile", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort. Rickey Raile is not in election_results council rows - flag #1."),
    "2016_dec-dissolution_rick-raile.pdf": ("2016-12-01", "Rick Raile", "Metro Township Council (founding, at-large)", "2016", "summary", "Dissolution report (December)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort; dissolution/closing report. Not in election_results - flag #1."),
    "2016_nov_kathryn-christensen.pdf": ("2016-11-01", "Kathryn Christensen", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort. Kathryn Christensen is not in election_results council rows - flag #1."),
    "2016_dec_kathryn-christensen.pdf": ("2016-12-01", "Kathryn Christensen", "Metro Township Council (founding, at-large)", "2016", "summary", "Year-end summary (December)", "slco_clerk_static", "county_folder_ym", "", "", "2016 founding cohort year-end summary. Not in election_results - flag #1."),

    # ---- 2017 @LRG contest (page year header "2017 Financial Disclosure Reporting").
    #      Seats KNOWN from election_results (both winners). ----
    "2017_nov_joe-smolka.pdf": ("2017-11-01", "Joe Smolka", "Metro Township Council At-Large (2017 @LRG)", "2017", "interim", "Interim (November)", "slco_clerk_static", "county_page_year_label", "JOE SMOLKA", "high", "2017 @LRG WINNER (338 votes, 51.4%) in election_results. Township-era presiding Mayor."),
    "2017_dec_joe-smolka.pdf": ("2017-12-01", "Joe Smolka", "Metro Township Council At-Large (2017 @LRG)", "2017", "summary", "Year-end summary (December)", "slco_clerk_static", "county_page_year_label", "JOE SMOLKA", "high", "2017 @LRG WINNER year-end summary."),
    "2017_nov_gary-bowen.pdf": ("2017-11-01", "Gary Bowen", "Metro Township Council At-Large (2017 @LRG)", "2017", "interim", "Interim (November)", "slco_clerk_static", "county_page_year_label", "GARY BOWEN", "high", "2017 @LRG WINNER (320 votes, 48.6%) in election_results."),
    "2017_dec_gary-bowen.pdf": ("2017-12-01", "Gary Bowen", "Metro Township Council At-Large (2017 @LRG)", "2017", "summary", "Year-end summary (December)", "slco_clerk_static", "county_page_year_label", "GARY BOWEN", "high", "2017 @LRG WINNER year-end summary."),

    # ---- 2019 cycle (page year header "2019 Financial Disclosure Reporting"). THIS CYCLE
    #      IS ABSENT FROM election_results (which has NO 2019 Emigration council rows and
    #      recon.md §6 says "no council contest 2019") -> finance CONFIRMS 2019 candidacy/
    #      campaign activity for these four (all later the 2023 winners/runner-up) - flag #2.
    #      Same documented "2019 SLCo drop" pattern as Copperton/South Jordan/Millcreek. ----
    "2019_oct_jennifer-hawkes.pdf": ("2019-10-01", "Jennifer Hawkes", "Metro Township Council At-Large (2019 cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_page_year_label", "JENNIFER HAWKES", "medium", "2019 filing (county page '2019 Financial Disclosure Reporting'). The 2019 council contest is ABSENT from election_results - finance surfaces the documented 2019 gap (flag #2). Hawkes is a certified 2023 winner."),
    "2019_oct_david-paul-brems.pdf": ("2019-10-01", "David Paul Brems", "Metro Township Council At-Large (2019 cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_page_year_label", "DAVID PAUL BREMS", "medium", "2019 filing; 2019 contest absent from election_results (flag #2). Brems is a certified 2023 winner and current city Mayor."),
    "2019_oct_tyler-tippets.pdf": ("2019-10-01", "Tyler Tippets", "Metro Township Council At-Large (2019 cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_page_year_label", "TYLER TIPPETTS", "medium", "2019 filing; 2019 contest absent from election_results (flag #2). Tippetts is the 2023 runner-up."),
    "2019_dec_tyler-tippets.pdf": ("2019-12-01", "Tyler Tippets", "Metro Township Council At-Large (2019 cycle)", "2019", "summary", "Year-end summary (December)", "slco_clerk_static", "county_page_year_label", "TYLER TIPPETTS", "medium", "2019 filing year-end summary; flag #2. Tippetts is the 2023 runner-up."),
    "2019_oct_catherine-harris.pdf": ("2019-10-01", "Catherine Harris", "Metro Township Council At-Large (2019 cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_page_year_label", "CATHERINE M HARRIS", "medium", "2019 filing (source file titled 'candidates report'); 2019 contest absent from election_results (flag #2). Harris is a certified 2023 winner."),
    "2019_dec_catherine-harris.pdf": ("2019-12-01", "Catherine Harris", "Metro Township Council At-Large (2019 cycle)", "2019", "summary", "Year-end summary (December)", "slco_clerk_static", "county_page_year_label", "CATHERINE M HARRIS", "medium", "2019 filing year-end summary; flag #2. Harris is a certified 2023 winner."),

    # ================= City of Emigration Canyon Wix site (source=city_website) =================
    # ---- 2025 candidate CAMPAIGN-FINANCE statements (emigration.utah.gov/election-information):
    #      "City of Emigration Canyon Municipal Elections - Campaign Finance Statement -
    #      Report of Contributions and Expenditures (Utah Code 10-3-208)", type-of-report box
    #      "All Primary Election Candidates - DUE Aug 5, 2025". Only the PRIMARY report is
    #      posted per candidate (no Oct/Dec general-election reports on the site). ----
    "city_electioninfo_robert-pinon.pdf": ("2025-08-05", "Robert Pinon", "City of Emigration Canyon Council (2025, at-large)", "2025", "interim", "Report Prior to Primary Election (Aug 5)", "city_website", "form_report_box", "ROBERTO PINON", "high", "2025 municipal primary campaign-finance statement (10-3-208), received 08-05-2025. Pinon is the 2025 general WINNER (324 votes, 61.7%). Born-digital fillable PDF (text). Office Seeking = Council Member (4-yr)."),
    "city_electioninfo_jacob-steed.pdf": ("2025-08-05", "Jacob Steed", "City of Emigration Canyon Council (2025, at-large)", "2025", "interim", "Report Prior to Primary Election (Aug 5)", "city_website", "form_report_box", "JACOB STEED", "high", "2025 municipal primary campaign-finance statement (10-3-208), received 08-05-2025. Steed is the 2025 general runner-up (201) and primary 2nd (116). Scanned form (image; ~0 char text layer)."),
    "city_electioninfo_zachary-posner.pdf": ("2025-08-01", "Zachary Posner", "City of Emigration Canyon Council (2025, at-large)", "2025", "interim", "Report Prior to Primary Election (Aug 5)", "city_website", "form_report_box", "ZACHARY POSNER", "high", "2025 municipal primary campaign-finance statement (10-3-208), signed 8/1/2025, received 08-01-2025. Posner placed 3rd in the primary (53). Scanned form. Council Member (4-yr)."),
    "city_electioninfo_dillon-wheelock.pdf": ("2025-08-05", "Dillon Wheelock", "City of Emigration Canyon Council (2025, at-large)", "2025", "interim", "Report Prior to Primary Election (Aug 5)", "city_website", "form_report_box", "DILLON WHEELOCK", "high", "2025 municipal primary campaign-finance statement (10-3-208), signed 08/05/25, received 08-05-2025. Wheelock placed 4th in the primary (14). Scanned form. Council Member (4-yr)."),

    # ---- Current elected-officer CONFLICT-OF-INTEREST forms (emigration.utah.gov/
    #      copy-of-disclosure-statements). Utah Code 10-3-1301 / 10-3-1313; filed Jan 1-31.
    #      SKILL: COI note -> filing_type=coi_disclosure. NOT campaign-finance dollar reports.
    #      Date anchored to the Jan filing window; election_year left blank (annual, not a cycle).
    #      These are scanned filled forms with an OCR/embedded text layer (pdftotext yields text). ----
    "city_coi_david-brems.pdf": ("2026-01-15", "David Brems", "City of Emigration Canyon - Mayor (annual COI)", "", "coi_disclosure", "Annual elected-officer COI (Jan window)", "city_website", "city_page_label", "DAVID PAUL BREMS", "medium", "Annual elected-officer Conflict-of-Interest disclosure (Utah Code 10-3-1301), NOT a campaign-finance report. Brems = current city Mayor (2023 winner). Date anchored to the Jan 1-31 filing window."),
    "city_coi_jennifer-hawkes.pdf": ("2026-01-15", "Jennifer Hawkes", "City of Emigration Canyon - Council (annual COI)", "", "coi_disclosure", "Annual elected-officer COI (Jan window)", "city_website", "city_page_label", "JENNIFER HAWKES", "medium", "Annual elected-officer COI (10-3-1301), not campaign finance. Hawkes = current council member (2023 winner)."),
    "city_coi_catherine-harris.pdf": ("2026-01-15", "Catherine Harris", "City of Emigration Canyon - Council (annual COI)", "", "coi_disclosure", "Annual elected-officer COI (Jan window)", "city_website", "city_page_label", "CATHERINE M HARRIS", "medium", "Annual elected-officer COI (10-3-1301), not campaign finance. Harris = current council member (2023 winner); form lists spouse John Bird."),
    "city_coi_robert-pinon.pdf": ("2026-01-15", "Robert Pinon", "City of Emigration Canyon - Council (annual COI)", "", "coi_disclosure", "Annual elected-officer COI (Jan window)", "city_website", "city_page_label", "ROBERTO PINON", "medium", "Annual elected-officer COI (10-3-1301), not campaign finance. Pinon = current council member (2025 winner)."),
    "city_coi_nicholas-griffith.pdf": ("2026-01-15", "Nicholas Griffith", "City of Emigration Canyon - Council (candidate/officeholder COI)", "", "coi_disclosure", "Candidate/officeholder COI", "city_website", "city_page_label", "", "", "Candidate/officeholder Conflict-of-Interest disclosure (10-3-1313), not campaign finance. Griffith is NOT among the certified 2025 candidates (2025 field: Pinon/Steed/Posner/Wheelock) yet holds a 2026 council seat -> APPOINTED, not elected (roster nuance) - flag #3. 'Retired Diplomat / U.S. Foreign Service' on form."),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def pdf_format(p):
    """born-digital text vs scanned image, by pdftotext char yield (>=200 -> text)."""
    try:
        out = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, timeout=60).stdout
        n = len("".join(out.decode("utf-8", "replace").split()))
    except Exception:
        n = 0
    return "text" if n >= 200 else "scanned"


def load_fetchlog():
    """map saved basename -> source_url from raw/_fetch_log.jsonl (last write wins)."""
    m = {}
    fl = os.path.join(RAW, "_fetch_log.jsonl")
    if os.path.exists(fl):
        for line in open(fl):
            try:
                d = json.loads(line)
            except Exception:
                continue
            sa = d.get("saved_as") or d.get("name")
            if sa and d.get("url"):
                m[sa] = d["url"]
    return m


def main():
    urls = load_fetchlog()
    cols = ["date", "candidate", "office", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "retrieved_date", "format",
            "extraction_method", "path", "source", "date_precision", "is_incremental",
            "matched_election_candidate", "join_confidence", "sha256", "notes"]
    rows, missing = [], []
    for fn, spec in SPEC.items():
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            missing.append(fn)
            continue
        (date, cand, office, eyear, ftype, rperiod, source, dprec,
         mcand, jconf, notes) = spec
        fmt = pdf_format(p)
        url = urls.get(fn, "")
        if not url:
            print("WARN: no source_url in fetch log for", fn, file=sys.stderr)
        kind = "Conflict-of-Interest disclosure" if ftype == "coi_disclosure" else "campaign-finance disclosure"
        title = f"{eyear or '(annual)'} {cand} ({office}) - {kind} ({rperiod})"
        rows.append({
            "date": date, "candidate": cand, "office": office, "election_year": eyear,
            "filing_type": ftype, "reporting_period": rperiod, "title": title,
            "source_url": url, "retrieved_date": RETRIEVED, "format": fmt,
            "extraction_method": EXTRACTION, "path": f"raw/{fn}", "source": source,
            "date_precision": dprec, "is_incremental": "",
            "matched_election_candidate": mcand, "join_confidence": jconf,
            "sha256": sha256(p), "notes": notes,
        })
    if missing:
        print("ERROR: SPEC files not on disk:", missing, file=sys.stderr)
        sys.exit(1)
    rows.sort(key=lambda r: (r["election_year"] or "9999", r["date"], r["candidate"]))
    out = os.path.join(HERE, "index.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    by_year = Counter(r["election_year"] or "(annual COI)" for r in rows)
    by_fmt = Counter(r["format"] for r in rows)
    by_type = Counter(r["filing_type"] for r in rows)
    by_src = Counter(r["source"] for r in rows)
    print(f"wrote {out}: {len(rows)} rows")
    print("  by election_year:", dict(sorted(by_year.items())))
    print("  by source:", dict(by_src))
    print("  by filing_type:", dict(by_type))
    print("  by format:", dict(by_fmt))


if __name__ == "__main__":
    main()
