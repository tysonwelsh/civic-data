#!/usr/bin/env python3
"""Build copperton_city_council/campaign_finance/index.csv (SCHEMA_SPEC.md §9 contract).

ACQUISITION-ONLY layer (source type 6 of /expand-city-sources). No OCR/vision dollar
extraction and no totals are computed here: `extraction_method` is uniform
`none (raw acquisition; text/OCR/vision deferred)` on every row.

The SPEC table below is hard-coded from:
  * the SLCo Clerk static metro-township-councils archive's per-candidate Copperton links
    (the page shows only a MONTH per link; the YEAR was OCR-read from each form's
    "<YYYY> Financial Disclosure Report" title line — see AVAILABILITY.md), and
  * the Town of Copperton GoDaddy site's /disclosures + /election-information pages
    (2025 candidate + 2026 annual Conflict-of-Interest forms -> filing_type=coi_disclosure).

Everything mechanical (sha256, byte-size-derived nothing, format = born-digital-text vs
scanned via pdftotext char count, source_url) is recomputed from disk + raw/_fetch_log.jsonl,
never hard-coded. Idempotent.

    python3 build_copperton_cf_index.py
"""
import csv, hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-14"
EXTRACTION = "none (raw acquisition; text/OCR/vision deferred)"

# filename (in raw/) -> spec tuple
# (date, candidate, office, election_year, filing_type, reporting_period,
#  source, date_precision, matched_election_candidate, join_confidence, notes)
SPEC = {
    # ---- 2016 founding metro-township cycle (SLCo static /2016_disclosures/november/;
    #      form title line reads "2016 Financial Disclosure Report"). Seat letter is a
    #      handwritten "Council # __ at large" field, not reliably legible -> office kept
    #      at the founding/at-large level, not asserted per seat. ----
    "2016_ron-patrick_copperton.pdf": ("2016-11-01", "Ron Patrick", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "RONALD PATRICK", "medium", "2016 founding cohort. Ronald Patrick is a candidate of record (2021 Seat E runner-up in the election layer); the 2016 founding contest itself is NOT in election_results (labeled 2017 there - see flag #1)."),
    "2016_tessa-stitzer_copperton.pdf": ("2016-11-01", "Tessa Stitzer", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "TESSA STITZER", "medium", "2016 founding cohort. Stitzer is a certified 2023 Seat C winner; 2016 founding contest absent from election_results (flag #1)."),
    "2016_kathleen-bailey_copperton.pdf": ("2016-11-01", "Kathleen Bailey", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "KATHLEEN RAY BAILEY", "medium", "2016 founding cohort. Bailey is a certified 2023 Seat A winner; 2016 founding contest absent from election_results (flag #1)."),
    "2016_jp-baxter_copperton.pdf": ("2016-11-01", "JP Baxter", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "JP BAXTER", "medium", "2016 founding cohort. Baxter is the 2017 @LRG (D/E) first loser in election_results; also filed 2017 (see the 2017 row)."),
    "2016_sean-clayton_copperton.pdf": ("2016-11-01", "Sean Clayton", "Metro Township Council (founding, at-large)", "2016", "interim", "Interim (November)", "slco_clerk_static", "county_folder_ym", "SEAN CLAYTON", "medium", "2016 founding cohort. Clayton = certified 2023 Seat B winner, later first Town Mayor (2025); 2016 founding contest absent from election_results (flag #1)."),

    # ---- 2017 @LRG (D/E) founding-cycle contest (root files; form title reads 2017) ----
    "kevin-severson-copperton_nov-a.pdf": ("2017-11-01", "Kevin Severson", "Metro Township Council At-Large (2017 @LRG / D-E cycle)", "2017", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "KEVIN SEVERSON", "high", "2017 @LRG (vote-for-2) WINNER in election_results (96 votes)."),
    "jp-baxter-copperton_nov.pdf": ("2017-11-01", "JP Baxter", "Metro Township Council At-Large (2017 @LRG / D-E cycle)", "2017", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "JP BAXTER", "high", "2017 @LRG (vote-for-2) first loser in election_results (90 votes)."),
    "apollo-pazell-copperton_nov.pdf": ("2017-11-01", "Apollo Pazell", "Metro Township Council At-Large (2017 @LRG / D-E cycle)", "2017", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "APOLLO PAZELL", "high", "2017 @LRG (vote-for-2) top WINNER in election_results (111 votes)."),

    # ---- 2019 A/B/C cycle (root files; form title reads 2019). THIS CYCLE IS ABSENT FROM
    #      election_results (the documented 2019 county-archive drop) -> finance CONFIRMS
    #      the 2019 contest occurred. Seat mapping (A/B/C) inferred from the same members'
    #      certified 2023 seats; not independently certified for 2019 -> join medium. ----
    "kathleen-bailey-copperton_oct.pdf": ("2019-10-01", "Kathleen Bailey", "Metro Township Council At-Large (2019 A/B/C cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_month_label_year_ocr", "KATHLEEN RAY BAILEY", "medium", "2019 A/B/C-cycle filing (form title reads 2019). Election layer has NO 2019 Copperton rows -> finance surfaces the documented 2019 gap (flag #2). Seat A inferred from Bailey's certified 2023 Seat A; not certified for 2019."),
    "kathleen-bailey-copperton_dec.pdf": ("2019-12-01", "Kathleen Bailey", "Metro Township Council At-Large (2019 A/B/C cycle)", "2019", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "KATHLEEN RAY BAILEY", "medium", "2019 A/B/C-cycle year-end summary. See flag #2 (2019 absent from election_results)."),
    "tessa-stitzer-copperton_oct.pdf": ("2019-10-01", "Tessa Stitzer", "Metro Township Council At-Large (2019 A/B/C cycle)", "2019", "interim", "Interim (October)", "slco_clerk_static", "county_month_label_year_ocr", "TESSA STITZER", "medium", "2019 A/B/C-cycle filing (form title reads 2019). See flag #2. Seat C inferred from Stitzer's certified 2023 Seat C; not certified for 2019."),
    "tessa-stitzer-copperton_dec.pdf": ("2019-12-01", "Tessa Stitzer", "Metro Township Council At-Large (2019 A/B/C cycle)", "2019", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "TESSA STITZER", "medium", "2019 A/B/C-cycle year-end summary. See flag #2."),
    "sean-clayton-copperton_dec.pdf": ("2019-12-01", "Sean Clayton", "Metro Township Council At-Large (2019 A/B/C cycle)", "2019", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "SEAN CLAYTON", "medium", "2019 A/B/C-cycle year-end summary (form title reads 2019). See flag #2. Seat B inferred from Clayton's certified 2023 Seat B; not certified for 2019."),

    # ---- 2021 D/E cycle (root files; form title reads 2021). Seats KNOWN from election_results. ----
    "dave-olsen-copperton-d_nov.pdf": ("2021-11-01", "Dave Olsen", "Metro Township Council At-Large Seat D", "2021", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "DAVID S OLSEN", "high", "2021 Seat D WINNER (unopposed, 89 votes) in election_results."),
    "dave-olsen-copperton_dec.pdf": ("2021-12-01", "Dave Olsen", "Metro Township Council At-Large Seat D", "2021", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "DAVID S OLSEN", "high", "2021 Seat D year-end summary."),
    "kevin-severson-copperton_nov-b.pdf": ("2021-11-01", "Kevin Severson", "Metro Township Council At-Large Seat E", "2021", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "KEVIN SEVERSON", "high", "2021 Seat E WINNER as a qualified WRITE-IN (63 votes) over Ronald Patrick (62) by 1 vote."),
    "kevin-severson-copperton_dec.pdf": ("2021-12-01", "Kevin Severson", "Metro Township Council At-Large Seat E", "2021", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "KEVIN SEVERSON", "high", "2021 Seat E year-end summary (write-in winner)."),
    "ronald-patrick-copperton-e_nov.pdf": ("2021-11-01", "Ronald Patrick", "Metro Township Council At-Large Seat E", "2021", "interim", "Interim (November)", "slco_clerk_static", "county_month_label_year_ocr", "RONALD PATRICK", "high", "2021 Seat E runner-up (62 votes; lost to Severson write-in by 1)."),
    "ron-patrick-copperton_dec.pdf": ("2021-12-01", "Ronald Patrick", "Metro Township Council At-Large Seat E", "2021", "summary", "Year-end summary (December)", "slco_clerk_static", "county_month_label_year_ocr", "RONALD PATRICK", "high", "2021 Seat E runner-up year-end summary."),

    # ---- Town-hosted Conflict-of-Interest forms (GoDaddy copperton.utah.gov; HB80/2024).
    #      SKILL: COI note -> filing_type=coi_disclosure. NOT campaign-finance dollar reports. ----
    "2025_coi_election-candidates_packet.pdf": ("2025-06-09", "2025 election candidates (Clayton, McCalmon)", "Town of Copperton — 2025 candidates (Mayor + Council)", "2025", "coi_disclosure", "2025 candidate Conflict-of-Interest packet", "copperton_town_site", "city_page_label", "", "", "Multi-candidate 2025 candidate COI packet (Utah Code 10-3-1301 / HB80-2024). Certified 2025 candidates were Sean Clayton (Mayor, unopposed) + Linda Marie McCalmon (Seat D, unopposed); Seat C had NO candidate declarations (flag #3). NO campaign-finance contribution/expenditure PDF is posted for 2025 (candidates unopposed/threshold-exempt) - honest empty for 2025 CF."),
    "2026_coi_sean-clayton.pdf": ("2026-01-01", "Sean Clayton", "Town of Copperton — Mayor (annual COI)", "", "coi_disclosure", "2026 annual disclosure statement", "copperton_town_site", "city_page_label", "SEAN CLAYTON", "medium", "2026 annual sitting-official Conflict-of-Interest statement (10-3-1301), not a campaign-finance report. Clayton = first Town Mayor (elected unopposed 2025)."),
    "2026_coi_tessa-stitzer.pdf": ("2026-01-01", "Tessa Stitzer", "Town of Copperton — Council / Mayor Pro Tem (annual COI)", "", "coi_disclosure", "2026 annual disclosure statement", "copperton_town_site", "city_page_label", "TESSA STITZER", "medium", "2026 annual sitting-official COI statement (10-3-1301), not campaign finance."),
    "2026_coi_kathleen-bailey.pdf": ("2026-01-01", "Kathleen Bailey", "Town of Copperton — Council (annual COI)", "", "coi_disclosure", "2026 annual disclosure statement", "copperton_town_site", "city_page_label", "KATHLEEN RAY BAILEY", "medium", "2026 annual sitting-official COI statement (10-3-1301), not campaign finance."),
    "2026_coi_linda-mccalmon.pdf": ("2026-01-01", "Linda McCalmon", "Town of Copperton — Council Seat D (annual COI)", "", "coi_disclosure", "2026 annual disclosure statement", "copperton_town_site", "city_page_label", "", "", "2026 annual sitting-official COI statement (10-3-1301), not campaign finance. McCalmon won Seat D unopposed 2025 (county did not tabulate - not in election_results)."),
    "2026_coi_jonathan-pratt.pdf": ("2026-01-01", "Jonathan Pratt", "Town of Copperton — Council (annual COI)", "", "coi_disclosure", "2026 annual disclosure statement", "copperton_town_site", "city_page_label", "", "", "2026 annual sitting-official COI statement (10-3-1301), not campaign finance. Pratt was NOT a certified 2025 candidate (Seat C had no declarations) -> APPOINTED to the council, not elected (flag #3)."),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def pdf_format(p):
    """born-digital text vs scanned image, by pdftotext char yield."""
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
    rows = []
    missing = []
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
        title = f"{eyear or '2026'} {cand} ({office}) — {'Conflict-of-Interest disclosure' if ftype=='coi_disclosure' else 'campaign-finance disclosure'} ({rperiod})"
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
    # summary
    from collections import Counter
    by_year = Counter(r["election_year"] or "(annual)" for r in rows)
    by_fmt = Counter(r["format"] for r in rows)
    by_type = Counter(r["filing_type"] for r in rows)
    print(f"wrote {out}: {len(rows)} rows")
    print("  by election_year:", dict(sorted(by_year.items())))
    print("  by format:", dict(by_fmt))
    print("  by filing_type:", dict(by_type))


if __name__ == "__main__":
    main()
