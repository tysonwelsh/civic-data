#!/usr/bin/env python3
"""Build kearns_city_council/campaign_finance/index.csv (SCHEMA_SPEC.md §9 contract).

ACQUISITION-ONLY layer (source type 6 of /expand-city-sources). Raw filings are the
Salt Lake County Clerk's redacted candidate financial-disclosure (campaign-finance)
PDFs for the Kearns Metro Township Council, retained verbatim under raw/. No OCR/vision
extraction and no dollar totals are computed here (all filings are scanned/image PDFs).

Metadata provenance (NOT fabricated):
  - source_url + sha256 : raw/_fetch_log.jsonl (sha recomputed from disk here).
  - month (reporting period) : the display text of each PDF's anchor on the county page
    https://www.saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/
  - election_year + district : the county page groups links by candidate under a
    "Metro Township Council N" heading; the pre-2022 static page holds ONLY 2016-2021
    filings (2022+ moved to the EasyVote portal). Year within {2017,2019,2021} is fixed
    by the Kearns staggered cycle (even seats D2/D4 -> 2017/2021; odd seats D1/D3/D5 ->
    2019), cross-checked against election_results/kearns_races.csv winners/runners-up.
  - date : first-of-labeled-month (day not published on the listing) -> date_precision
    = 'county_page_month_label'.

filing_type: December filing = 'summary' (year-end); every other month = 'interim'.
is_incremental is left BLANK (not recorded) — determining cumulative-vs-incremental
requires reading the (scanned) forms, which is the deferred extraction pass; do NOT sum
across a candidate's filings before that pass (double-count trap, SKILL §6).

Idempotent: re-run to regenerate index.csv from raw/ + the SPEC table below.
"""
import csv, hashlib, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
BASE = "https://www.saltlakecounty.gov"

# (raw_filename, election_year, seat_no, seat_word, candidate, month, filing_type,
#  matched_name_or_blank, join_confidence, notes)
# seat_word: 'Seat' (2016/2017 township) or 'District' (2019/2021 township).
SPEC = [
 # ---- 2016 founding township general (below the repo's 2017 minutes floor; the
 #      elections layer covers 2016 — retained as founding-cycle context) ----
 ("2016june_steve_perry_trip_kearns_3_fixed.pdf",2016,3,"Seat","Steve Perry","June","interim","STEVE PERRY","high","2016 founding cycle; Perry won Seat 3."),
 ("2016june_ruby_brown_kearns_3.pdf",2016,3,"Seat","Ruby Brown","June","interim","","medium","2016 Seat 3 primary candidate; in by_candidate, not a general winner/runner-up."),
 ("2016june_christopher_geertsen_trip_kearns_3.pdf",2016,3,"Seat","Christopher James Geertsen","June","interim","CHRISTOPHER JAMES GEERTSEN","high","2016 Seat 3 runner-up (general)."),
 ("2016june_jonatan_lefler_trip_kearns_3.pdf",2016,3,"Seat","Jonatan Lefler","June","interim","","medium","2016 Seat 3 primary candidate; not a general winner/runner-up."),
 ("2016june_matt_welch_dbl_kearns_3.pdf",2016,3,"Seat","Matt Welch","June","interim","","medium","2016 Seat 3 primary candidate; not a general winner/runner-up."),
 ("2016june_dennis_walton_dbl_kearns_3.pdf",2016,3,"Seat","Dennis Walton","June","interim","","medium","2016 Seat 3 primary candidate; not a general winner/runner-up."),
 ("2016july_jonatan_lefler_kearns_3.pdf",2016,3,"Seat","Jonatan Lefler","July","interim","","medium","2016 Seat 3 primary candidate; not a general winner/runner-up."),
 ("2016july_matt_welch_kearns_3.pdf",2016,3,"Seat","Matt Welch","July","interim","","medium","2016 Seat 3 primary candidate; not a general winner/runner-up."),
 ("2016november_h_brett_helsten_kearns_1.pdf",2016,1,"Seat","H. Brett Helsten","November","interim","H. BRETT HELSTEN","high","2016 Seat 1 runner-up (Schaeffer won)."),
 ("2016november_patrick_schaleffer_kearns_1.pdf",2016,1,"Seat","Patrick Schaeffer","November","interim","PATRICK SCHAEFFER","high","2016 Seat 1 winner. Source filename misspells 'Schaleffer'."),
 ("2016november_alan_peterson_dbl_kearns_2.pdf",2016,2,"Seat","Alan Peterson","November","interim","ALAN PETERSON","high","2016 Seat 2 winner (uncontested)."),
 ("2016november_christopher_geertsen_kearns_3.pdf",2016,3,"Seat","Christopher James Geertsen","November","interim","CHRISTOPHER JAMES GEERTSEN","high","2016 Seat 3 runner-up."),
 ("2016november_steve_perry_dbl_kearns.pdf",2016,3,"Seat","Steve Perry","November","interim","STEVE PERRY","high","2016 Seat 3 winner."),
 ("2016november_tina_snow_kearns_4.pdf",2016,4,"Seat","Tina Snow","November","interim","TINA SNOW","high","2016 Seat 4 winner (uncontested)."),
 ("2016november_kelly_bush_kearns_5.pdf",2016,5,"Seat","Kelly F. Bush","November","interim","KELLY F. BUSH","high","2016 Seat 5 winner."),
 ("2016november_brian_richards_trip_kearns_5.pdf",2016,5,"Seat","Brian Richards","November","interim","BRIAN RICHARDS","high","2016 Seat 5 runner-up."),
 # ---- 2017 township general (even seats D2/D4) ----
 ("alan_peterson_trip_kearns.pdf",2017,2,"Seat","Alan Peterson","November","interim","ALAN PETERSON","high","2017 Seat 2 winner (uncontested)."),
 ("tina_snow_trip_kearns.pdf",2017,4,"Seat","Tina Snow","November","interim","TINA SNOW","high","2017 Seat 4 winner (uncontested)."),
 # ---- 2019 township general (odd districts D1/D3/D5) ----
 ("patrick_schaeffer_trip_kearns1.pdf",2019,1,"District","Patrick Daniel Schaeffer","October","interim","PATRICK DANIEL SCHAEFFER","high","2019 District 1 winner (+7 over Higginson)."),
 ("patrick_schaeffer_trip_kearns.pdf",2019,1,"District","Patrick Daniel Schaeffer","December","summary","PATRICK DANIEL SCHAEFFER","high","2019 District 1 winner; year-end summary."),
 ("samuel_higginson_trip_kearns.pdf",2019,1,"District","Samuel J. Higginson","October","interim","SAMUEL J HIGGINSON","high","2019 District 1 runner-up."),
 ("samuel_higginson_trip_kearns_1.pdf",2019,1,"District","Samuel J. Higginson","December","summary","SAMUEL J HIGGINSON","high","2019 District 1 runner-up; year-end summary."),
 ("chrystalbutterfield2019.pdf",2019,3,"District","Chrystal Butterfield","August","interim","CHRYSTAL BUTTERFIELD","high","2019 District 3 winner; pre-primary/August filing (filename has no 'kearns')."),
 ("chrystal_butterfield_trip_kearns.pdf",2019,3,"District","Chrystal Butterfield","October","interim","CHRYSTAL BUTTERFIELD","high","2019 District 3 winner."),
 ("chrystal_butterfield_trip_kearns_1.pdf",2019,3,"District","Chrystal Butterfield","December","summary","CHRYSTAL BUTTERFIELD","high","2019 District 3 winner; year-end summary."),
 ("rubybrown2019.pdf",2019,3,"District","Ruby Brown","August","interim","RUBY BROWN","high","2019 District 3 runner-up; pre-primary/August filing."),
 ("ruby_brown_trip_kearns3.pdf",2019,3,"District","Ruby Brown","October","interim","RUBY BROWN","high","2019 District 3 runner-up."),
 ("christophergeertsen2019.pdf",2019,3,"District","Christopher James Geertsen","August","interim","","low","DISCREPANCY: a 2019 Geertsen finance filing exists, but the certified 2019 District 3 contest was Butterfield vs Ruby Brown ONLY (kearns_races.csv) - Geertsen is not a certified 2019 candidate (declared then withdrew, or filed but not on the general ballot). Flag only; do NOT edit election_results."),
 # ---- 2021 township general (even districts D2/D4) ----
 ("alan_peterson_kearns_2.pdf",2021,2,"District","Alan Peterson","November","interim","ALAN PETERSON","high","2021 District 2 winner (+4 over Gibson, two write-ins)."),
 ("alan_peterson_kearns.pdf",2021,2,"District","Alan Peterson","December","summary","ALAN PETERSON","high","2021 District 2 winner; year-end summary."),
 ("royce_gibson_dbl_kearns_2.pdf",2021,2,"District","Royce Gibson","November","interim","ROYCE GIBSON","high","2021 District 2 runner-up."),
 ("royce_gibson_kearns.pdf",2021,2,"District","Royce Gibson","December","summary","ROYCE GIBSON","high","2021 District 2 runner-up; year-end summary."),
 ("tina_snow_kearns_4.pdf",2021,4,"District","Tina Snow","November","interim","TINA SNOW","high","2021 District 4 winner (uncontested)."),
 ("tina_snow_kearns.pdf",2021,4,"District","Tina Snow","December","summary","TINA SNOW","high","2021 District 4 winner; year-end summary."),
 # ---- 2019 D5 ----
 ("kelly_bush_trip_kearns.pdf",2019,5,"District","Kelly Bush","October","interim","KELLY BUSH","high","2019 District 5 winner."),
 ("kelly_bush_trip_kearns_1.pdf",2019,5,"District","Kelly Bush","December","summary","KELLY BUSH","high","2019 District 5 winner; year-end summary."),
 ("brian_richards_trip_kearns.pdf",2019,5,"District","Brian Richards","October","interim","BRIAN RICHARDS","high","2019 District 5 runner-up."),
 ("brian_richards_trip_kearns_1.pdf",2019,5,"District","Brian Richards","December","summary","BRIAN RICHARDS","high","2019 District 5 runner-up; year-end summary."),
]

MONTH_NO = {"June":"06","July":"07","August":"08","October":"10","November":"11","December":"12"}
PERIOD = {
 "June":"Pre-primary interim (June)","July":"Pre-primary interim (July)",
 "August":"Pre-primary interim (August)","October":"Report prior to general election (October)",
 "November":"General-election report (November)","December":"Year-end summary (December)",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def is_scanned(p):
    try:
        txt = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True,
                             timeout=60).stdout
        return len("".join(chr(c) for c in txt if c not in (9,10,13,32)).strip()) < 40
    except Exception:
        return True


def load_source_urls():
    urls = {}
    log = os.path.join(RAW, "_fetch_log.jsonl")
    for line in open(log):
        try:
            j = json.loads(line)
        except Exception:
            continue
        if j.get("ok") and str(j.get("saved_as", "")).endswith(".pdf"):
            urls[j["saved_as"]] = j["url"]
    return urls


def main():
    urls = load_source_urls()
    cols = ["date","candidate","office","election_year","filing_type","reporting_period",
            "title","source_url","retrieved_date","format","extraction_method","path",
            "source","date_precision","is_incremental","matched_election_candidate",
            "join_confidence","sha256","notes"]
    out = []
    for (fn, yr, seatno, seatword, cand, month, ftype, matched, conf, notes) in SPEC:
        p = os.path.join(RAW, fn)
        assert os.path.exists(p), f"missing raw file: {fn}"
        office = f"Metro Township Council {seatword} {seatno}"
        date = f"{yr}-{MONTH_NO[month]}-01"
        fmt = "scanned" if is_scanned(p) else "text"
        title = f"{yr} {cand} ({office}) - candidate campaign-finance disclosure ({PERIOD[month]})"
        out.append({
            "date": date, "candidate": cand, "office": office, "election_year": yr,
            "filing_type": ftype, "reporting_period": PERIOD[month], "title": title,
            "source_url": urls.get(fn, ""), "retrieved_date": "2026-07-13",
            "format": fmt, "extraction_method": "none (raw acquisition; OCR/vision deferred)",
            "path": f"raw/{fn}", "source": "slco_clerk_static",
            "date_precision": "county_page_month_label", "is_incremental": "",
            "matched_election_candidate": matched, "join_confidence": conf,
            "sha256": sha256(p), "notes": notes,
        })
    out.sort(key=lambda r: (r["election_year"], r["office"], r["date"], r["candidate"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f"wrote index.csv with {len(out)} rows "
          f"({sum(1 for r in out if r['format']=='scanned')} scanned / "
          f"{sum(1 for r in out if r['format']=='text')} text)")


if __name__ == "__main__":
    main()
