#!/usr/bin/env python3
"""Build Magna campaign_finance/index.csv (ACQUISITION-ONLY, expand-city-sources source 6).

Emits the SCHEMA_SPEC.md §9 campaign_finance contract header exactly, then Magna extras
(source, date_precision, is_incremental, matched_election_candidate, join_confidence,
sha256, notes). Idempotent: recomputes sha256 + format from disk and reads each row's
source_url from raw/_fetch_log.jsonl (never hard-coded), so it stays honest to the bytes.

Two eras / two hosts (the whole story — see AVAILABILITY.md):
  * 2016 founding + 2017/2019/2021 township filings  -> SLCo Clerk STATIC metro-township
    archive (source=slco_clerk_static). Root-file YEARS are OCR-verified from each form's
    printed "<YYYY> Financial Disclosure" header (3 of my path-guesses were corrected).
  * 2025 first city-era election (Mayor + D2 + D4)    -> magna.utah.gov DocumentCenter
    (source=magna_city_site): 9 per-candidate PRIMARY disclosures + 3 multi-candidate
    BUNDLES (Oct-7 / Oct-28 general + primary-eliminated) + 1 candidate COI-forms packet.
  * 2023 township (D1/D3/D5)  -> NONE retrieved: SLCo EasyVote SPA (2022+) HTTP-500/auth
    -gated under polite GET (honest gap; see unrecovered.csv).

extraction_method is uniform "none (raw acquisition; text/OCR/vision deferred)" — no dollar
totals are computed in this layer (double-count trap; a later /cf-vision-transcribe +
cycle_totals.py pass owns that). BUNDLE rows are one row per PDF artifact (per-candidate
split within a bundle is the deferred pass); the candidates each bundle contains are named
in AVAILABILITY.md.
"""
import csv, hashlib, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

CONTRACT = ["date", "candidate", "office", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "retrieved_date", "format",
            "extraction_method"]
EXTRAS = ["path", "source", "date_precision", "is_incremental",
          "matched_election_candidate", "join_confidence", "sha256", "notes"]

EM = "none (raw acquisition; text/OCR/vision deferred)"
RET = "2026-07-13"

# reporting_period phrasings
RP = {
    "jun": "Pre-primary interim (June)", "jul": "Pre-primary interim (July)",
    "oct": "Report prior to general election (October)",
    "nov": "General-election report (November)",
    "dec": "Year-end summary (December)",
}

# --- SLCo static archive filings (2016 founding + 2017/2019/2021 township) ---
# fields: filename: (candidate, office, year, filing_type, reporting_period, date,
#                     date_precision, matched, join_conf, notes)
SLCO = {
 # 2016 founding cycle (below the 2017 data floor; retained as roster context, like Kearns)
 "201606_toni-sears---magna-1_redacted.pdf": ("Toni Sears","Metro Township Council Seat 1",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D1 primary-field candidate (not general winner/runner)."),
 "201607_toni-sears-magna-1-redacted.pdf": ("Toni Sears","Metro Township Council Seat 1",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D1 primary-field candidate."),
 "201606_steve-prokopis-magna-1_redacted.pdf": ("Steve Prokopis","Metro Township Council Seat 1",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","STEVE PROKOPIS","high","2016 D1 winner (later D1 2019 winner; current D1)."),
 "201611_steve-prokopis-magna-1_redacted.pdf": ("Steve Prokopis","Metro Township Council Seat 1",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","STEVE PROKOPIS","high","2016 D1 winner."),
 "201606_dan-johnson-magna-1_redacted.pdf": ("Dan Johnson","Metro Township Council Seat 1",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D1 primary-field candidate."),
 "201607_dan-johnson-magna-1_redacted.pdf": ("Dan Johnson","Metro Township Council Seat 1",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D1 primary-field candidate."),
 "201606_georgia-york-magna-1_redacted.pdf": ("Georgia York","Metro Township Council Seat 1",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","GEORGIA YORK","high","2016 D1 runner-up."),
 "201611_georgia-york---magna_redacted.pdf": ("Georgia York","Metro Township Council Seat 1",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","GEORGIA YORK","high","2016 D1 runner-up."),
 "201606_brint-d.-peel-magna-2_redacted.pdf": ("Brint D. Peel","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","BRINT D. PEEL","high","2016 D2 winner."),
 "201611_brint-peel-magna-2_redacted.pdf": ("Brint D. Peel","Metro Township Council Seat 2",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","BRINT D. PEEL","high","2016 D2 winner."),
 "201606_leon-kelly-peterson-magna-2_redacted.pdf": ("Leon Kelly Peterson","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201607_kelly-peterson-magna-2_redacted.pdf": ("Leon Kelly Peterson","Metro Township Council Seat 2",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D2 primary-field candidate (Nov-folder link, July label)."),
 "201606_mark-elieson--magna-2_redacted.pdf": ("Mark E. Elieson","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","MARK E ELIESON","high","2016 D2 runner-up."),
 "201611_mark-elieson---magna_redacted.pdf": ("Mark E. Elieson","Metro Township Council Seat 2",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","MARK E ELIESON","high","2016 D2 runner-up."),
 "201606_paul-kunz-magna-2_redacted.pdf": ("Paul A. Kunz","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201607_paul-kunz-magna-2_redacted.pdf": ("Paul A. Kunz","Metro Township Council Seat 2",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201606_troy-larsen-magna-2_redacted.pdf": ("Troy Larsen","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201607_troy-larsen-magna-2_redacted.pdf": ("Troy Larsen","Metro Township Council Seat 2",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201606_dustin-white--magna-2_redacted.pdf": ("Dustin Chad White","Metro Township Council Seat 2",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201607_dustin-white-magna-2_redacted.pdf": ("Dustin Chad White","Metro Township Council Seat 2",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D2 primary-field candidate."),
 "201606_dan-w.-peay-magna-3_redacted.pdf": ("Dan W. Peay","Metro Township Council Seat 3",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","DAN W. PEAY","high","2016 D3 winner (later D3 2019 winner)."),
 "201606_renee-m.-anderson-magna-3_redacted.pdf": ("Renee M. Anderson","Metro Township Council Seat 3",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D3 primary-field candidate."),
 "201607_renee-anderson-magna-3_redacted.pdf": ("Renee M. Anderson","Metro Township Council Seat 3",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D3 primary-field candidate."),
 "201606_bennion-gardner-magna-3_redacted.pdf": ("Bennion Gardner","Metro Township Council Seat 3",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","BENNION GARDNER","high","2016 D3 runner-up."),
 "201611_bennion-gardner-magna-3_redacted.pdf": ("Bennion Gardner","Metro Township Council Seat 3",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","BENNION GARDNER","high","2016 D3 runner-up."),
 "201606_stuart-lawrence-magna-3_redacted.pdf": ("Stuart Lawrence","Metro Township Council Seat 3",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D3 primary-field candidate."),
 "201607_stuart-lawrence---magna-3-redacted.pdf": ("Stuart Lawrence","Metro Township Council Seat 3",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D3 primary-field candidate."),
 "201606_trish-hull---magna-4_redacted.pdf": ("Trish Hull","Metro Township Council Seat 4",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","TRISH HULL","high","2016 D4 winner (D4 2017/2021 winner; 2025 D4 runner-up)."),
 "201611_trish-hull-magna-4_redacted.pdf": ("Trish Hull","Metro Township Council Seat 4",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","TRISH HULL","high","2016 D4 winner."),
 "201606_john-sudbury-magna-4_redacted.pdf": ("John Sudbury","Metro Township Council Seat 4",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","JOHN SUDBURY","high","2016 D4 runner-up."),
 "201611_john-sudbury-magna-4_redacted.pdf": ("John Sudbury","Metro Township Council Seat 4",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","JOHN SUDBURY","high","2016 D4 runner-up."),
 "201606_ladell-bishop--magna-4_redacted.pdf": ("LaDell Bishop","Metro Township Council Seat 4",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201607_ladell-bishop-magna-4_redacted.pdf": ("LaDell Bishop","Metro Township Council Seat 4",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201606_daniel-r.-cripps-magna-4_redacted.pdf": ("Daniel R. Cripps","Metro Township Council Seat 4",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201607_daniel-cripps-magna-4_redacted.pdf": ("Daniel R. Cripps","Metro Township Council Seat 4",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201606_christopher-aaron-weight-magna-4_redacted.pdf": ("Christopher Aaron Weight","Metro Township Council Seat 4",2016,"interim",RP["jun"],"2016-06-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201607_christopher-weight-magna-4_redacted.pdf": ("Christopher Aaron Weight","Metro Township Council Seat 4",2016,"interim",RP["jul"],"2016-07-01","county_folder_ym","","medium","2016 D4 primary-field candidate."),
 "201611_eric-ferguson-magna5_redacted.pdf": ("Eric Ferguson","Metro Township Council Seat 5",2016,"interim",RP["nov"],"2016-11-01","county_folder_ym","ERIC FERGUSON","high","2016 D5 winner."),
 # 2017 township (D2/D4 cycle) — year OCR-verified from form header
 "201711_brint-peel---magna.pdf": ("Brint D. Peel","Metro Township Council Seat 2",2017,"interim",RP["nov"],"2017-11-01","county_month_label_year_ocr","BRINT D. PEEL","high","2017 D2 winner (uncontested). Year OCR-verified '2017 Financial Disclosure'."),
 "201711_trish-hull---magna.pdf": ("Trish Hull","Metro Township Council Seat 4",2017,"interim",RP["nov"],"2017-11-01","county_month_label_year_ocr","TRISH HULL","high","2017 D4 winner (uncontested). Year OCR-verified '2017 Financial Disclosure'."),
 # 2019 township (D1/D3/D5 cycle) — year OCR-verified
 "201910_steve-prokopis---magna.pdf": ("Steve Prokopis","Metro Township Council District 1",2019,"interim",RP["oct"],"2019-10-01","county_month_label_year_ocr","STEVE PROKOPIS","high","2019 D1 winner (uncontested). Year OCR-verified."),
 "201910_dan-peay---magna.pdf": ("Dan W. Peay","Metro Township Council District 3",2019,"interim",RP["oct"],"2019-10-01","county_month_label_year_ocr","DAN W. PEAY","high","2019 D3 winner (uncontested). Year OCR-verified."),
 "201912_dan-peay---magna-1.pdf": ("Dan W. Peay","Metro Township Council District 3",2019,"summary",RP["dec"],"2019-12-01","county_month_label_year_ocr","DAN W. PEAY","high","2019 D3 year-end summary. Year OCR-verified."),
 "201910_audrey-pierce---magna5.pdf": ("Audrey Pierce","Metro Township Council District 5",2019,"interim",RP["oct"],"2019-10-01","county_month_label_year_ocr","AUDREY PIERCE","high","2019 D5 winner (uncontested; current D5). Born-digital text layer (form template)."),
 # 2021 township (D2/D4 cycle) — year OCR-verified; 3 files were path-mis-guessed then corrected
 "202111_eric-barney-magna-2.pdf": ("Eric Barney","Metro Township Council District 2",2021,"interim",RP["nov"],"2021-11-01","county_month_label_year_ocr","ERIC G BARNEY","high","2021 D2 winner (later 2024-25 council chair-'Mayor'; 2025 D2 loser). Year OCR-verified."),
 "202112_eric-barney-magna.pdf": ("Eric Barney","Metro Township Council District 2",2021,"summary",RP["dec"],"2021-12-01","county_month_label_year_ocr","ERIC G BARNEY","high","2021 D2 year-end summary. Year OCR-verified '2021 Financial Disclosure'."),
 "202111_paris-ramos-magna-2.pdf": ("Paris Ramos","Metro Township Council District 2",2021,"interim",RP["nov"],"2021-11-01","county_month_label_year_ocr","","medium","2021 D2 third candidate (not winner/runner). Year OCR-verified."),
 "202112_brint-peel-magna.pdf": ("Brint D. Peel","Metro Township Council District 2",2021,"summary",RP["dec"],"2021-12-01","county_month_label_year_ocr","BRINT D. PEEL","high","2021 D2 runner-up (lost to Barney). Year CORRECTED via OCR to '2021' (path label read 2017)."),
 "202111_trish-hull--magna-4.pdf": ("Trish Hull","Metro Township Council District 4",2021,"interim",RP["nov"],"2021-11-01","county_month_label_year_ocr","TRISH HULL","high","2021 D4 winner (uncontested). Year CORRECTED via OCR to '2021'."),
 "202112_trish-hull-magna.pdf": ("Trish Hull","Metro Township Council District 4",2021,"summary",RP["dec"],"2021-12-01","county_month_label_year_ocr","TRISH HULL","high","2021 D4 year-end summary. Year CORRECTED via OCR to '2021'."),
}

# --- Magna city site 2025 first city-era election ---
CITY = {
 # per-candidate PRIMARY disclosures (Aug 12 2025 primary)
 "202508_sudbury_magna-mayor_primary_v574.pdf": ("Mickey M. Sudbury","City Mayor",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","MICKEY M SUDBURY","high","Mayor winner (Magna's first elected mayor; seated Jan 2026)."),
 "202508_adriano_magna-mayor_primary_v567.pdf": ("Alexander J. Adriano","City Mayor",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","ALEXANDER J. ADRIANO","high","Mayor runner-up."),
 "202508_romero_magna-mayor_primary_v573.pdf": ("Michael Romero","City Mayor",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","","medium","Mayor primary field (eliminated); not winner/runner."),
 "202508_white_magna-mayor_primary_v571.pdf": ("Maxwell White","City Mayor",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","","medium","Mayor primary field (eliminated); not winner/runner. Born-digital."),
 "202508_olsen_magna-d2_primary_v572.pdf": ("Megan L. Olsen","City Council District 2",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","MEGAN L. OLSEN","high","D2 winner (current D2)."),
 "202508_barney_magna-d2_primary_v570.pdf": ("Eric Gordon Barney","City Council District 2",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","ERIC GORDON BARNEY","high","D2 runner-up (former township chair-'Mayor'). Born-digital."),
 "202508_rodriguez_magna-d2_primary_v569.pdf": ("Cisco Rodriguez","City Council District 2",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","","medium","D2 primary field (eliminated); not winner/runner."),
 "202508_george_magna-d4_primary_v575.pdf": ("Terry George","City Council District 4",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","TERRY GEORGE","high","D4 winner (current D4, Mayor Pro Tem)."),
 "202508_hull_magna-d4_primary_v576.pdf": ("Trish A. Hull","City Council District 4",2025,"interim","Primary-election disclosure (August)","2025-08-01","city_primary_cycle","TRISH A. HULL","high","D4 runner-up (long-time township D4)."),
 # multi-candidate BUNDLES (per-candidate split is the deferred pass — see AVAILABILITY.md)
 "202510_magna_general-oct07_bundle_v642.pdf": ("General-election finalists (bundle)","City Mayor / Council D2 / D4",2025,"interim","Pre-general report (October 7 bundle)","2025-10-07","city_report_date","","","Multi-candidate bundle: general-election finalists (Sudbury, Adriano, Olsen, Barney, George, Hull). Mixed born-digital + scanned pages. One artifact = one row; per-candidate split deferred."),
 "202510_magna_general-oct28_bundle_v643.pdf": ("General-election finalists (bundle)","City Mayor / Council D2 / D4",2025,"interim","Pre-general report (October 28 bundle)","2025-10-28","city_report_date","","","Multi-candidate bundle: general-election finalists' Oct-28 reports. Mixed born-digital + scanned pages. One artifact = one row; per-candidate split deferred."),
 "202508_magna_primary-eliminated_bundle_v644.pdf": ("Primary-eliminated candidates (bundle)","City Mayor / Council D2 / D4",2025,"summary","Primary-eliminated final disclosures (bundle)","2025-08-01","city_primary_cycle","","","Multi-candidate bundle: candidates eliminated at the primary (expected: Romero, Maxwell White, C. Rodriguez, Brooks Jones). Brooks Jones (D4) has NO per-candidate primary file — his filing is here. Mixed pages."),
 # candidate conflict-of-interest forms packet -> coi_disclosure (SKILL: COI note -> coi_disclosure)
 "2025_magna_candidate_coi_forms_v533.pdf": ("2025 Magna candidates (all)","City candidates (all offices)",2025,"coi_disclosure","Candidate conflict-of-interest forms","2025-06-01","city_filing_period","","","Bundled Utah Code 10-3-1301 candidate conflict-of-interest disclosure forms for all 2025 Magna candidates (33 pp, born-digital). Not a campaign-finance dollar report."),
}

# --- Bundle-contained candidates with NO standalone artifact -----------------
# A multi-candidate BUNDLE PDF can contain a candidate who filed no per-candidate PDF of
# their own. Brooks Jones (2025 D4, eliminated at the primary) is the sole such case: his
# 10-3-208 final disclosure ($958.44 self-funded) exists ONLY inside the primary-eliminated
# bundle v644 (transcribed verbatim in vision/0a3cfc7e.json). build_finance.py expands that
# bundle's vision cache into per-candidate filings, but validate_finance requires every
# (candidate, election_year) in the derived CSVs to exist in index.csv — a gate the OTHER
# bundle candidates (White, Romero, the general finalists) meet via their OWN standalone
# primary index rows. Jones has none, so we emit an honest MEMBERSHIP row that points at the
# SAME bundle artifact (path / source_url / sha256) his report lives in. It is NOT a second
# copy of the bundle: build_finance.py de-dups bundle rows by path and expands the reports[]
# exactly once. Its date / date_precision / source / election_year / filing_type mirror the
# bundle artifact row so the two are interchangeable as the expansion template.
# fields: (bundle_filename, candidate, office, year, filing_type, reporting_period, matched,
#          join_conf, notes)
BUNDLE_MEMBERS = [
 ("202508_magna_primary-eliminated_bundle_v644.pdf", "Brooks Jones",
  "City Council District 4", 2025, "summary",
  "Primary-eliminated final disclosure (in bundle v644)", "", "medium",
  "2025 D4 primary-eliminated candidate; filed NO standalone per-candidate PDF. His "
  "10-3-208 final disclosure ($958.44 self-funded) lives INSIDE the primary-eliminated "
  "bundle v644 (transcribed in vision/0a3cfc7e.json). Membership-only row so his "
  "bundle-expanded filing satisfies validate_finance's (candidate,election_year)-in-index "
  "gate; build_finance.py de-dups by bundle path (one expansion). Same artifact as the "
  "'Primary-eliminated candidates (bundle)' row."),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_of(path):
    """Born-digital (text) vs scanned image, from real extractable char count."""
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, timeout=60).stdout
        n = len("".join(out.decode("utf-8", "replace").split()))
    except Exception:
        n = 0
    return "text" if n > 100 else "scanned"


def load_urls():
    urls = {}
    log = os.path.join(RAW, "_fetch_log.jsonl")
    for line in open(log):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("saved_as") and d.get("url"):
            urls[d["saved_as"]] = d["url"]
    return urls


def main():
    urls = load_urls()
    rows = []
    for src, spec in (("slco_clerk_static", SLCO), ("magna_city_site", CITY)):
        for fn, (cand, office, yr, ftype, rperiod, date, dprec, matched, jconf, notes) in spec.items():
            fp = os.path.join(RAW, fn)
            if not os.path.exists(fp):
                raise SystemExit(f"MISSING raw file: {fn}")
            url = urls.get(fn, "")
            if not url:
                raise SystemExit(f"no source_url in _fetch_log for {fn}")
            title = f"{yr} {cand} ({office}) — campaign-finance disclosure ({rperiod})"
            rows.append({
                "date": date, "candidate": cand, "office": office,
                "election_year": yr, "filing_type": ftype, "reporting_period": rperiod,
                "title": title, "source_url": url, "retrieved_date": RET,
                "format": fmt_of(fp), "extraction_method": EM,
                "path": f"raw/{fn}", "source": src, "date_precision": dprec,
                "is_incremental": "", "matched_election_candidate": matched,
                "join_confidence": jconf, "sha256": sha256(fp), "notes": notes,
            })
    # Bundle-contained membership rows (candidate whose ONLY filing is inside a bundle PDF —
    # Brooks Jones). Each references the SAME bundle artifact (path/url/sha256), mirroring the
    # bundle row's date/date_precision/source so build_finance.py can use either as the
    # per-candidate expansion template. format is read from disk (the bundle PDF) like any row.
    for (fn, cand, office, yr, ftype, rperiod, matched, jconf, notes) in BUNDLE_MEMBERS:
        fp = os.path.join(RAW, fn)
        if not os.path.exists(fp):
            raise SystemExit(f"MISSING raw file: {fn}")
        if fn not in CITY:
            raise SystemExit(f"BUNDLE_MEMBERS references {fn} which is not a CITY bundle row")
        _b_date, _b_dprec = CITY[fn][5], CITY[fn][6]
        url = urls.get(fn, "")
        if not url:
            raise SystemExit(f"no source_url in _fetch_log for {fn}")
        title = f"{yr} {cand} ({office}) — campaign-finance disclosure ({rperiod})"
        rows.append({
            "date": _b_date, "candidate": cand, "office": office,
            "election_year": yr, "filing_type": ftype, "reporting_period": rperiod,
            "title": title, "source_url": url, "retrieved_date": RET,
            "format": fmt_of(fp), "extraction_method": EM,
            "path": f"raw/{fn}", "source": "magna_city_site", "date_precision": _b_dprec,
            "is_incremental": "", "matched_election_candidate": matched,
            "join_confidence": jconf, "sha256": sha256(fp), "notes": notes,
        })
    # sort by election_year, then date, then candidate for a stable file
    rows.sort(key=lambda r: (r["election_year"], r["date"], r["candidate"]))
    out = os.path.join(HERE, "index.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRAS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} with {len(rows)} rows")
    from collections import Counter
    print("by year:", dict(sorted(Counter(r["election_year"] for r in rows).items())))
    print("by source:", dict(Counter(r["source"] for r in rows)))
    print("by format:", dict(Counter(r["format"] for r in rows)))
    print("by filing_type:", dict(Counter(r["filing_type"] for r in rows)))


if __name__ == "__main__":
    main()
