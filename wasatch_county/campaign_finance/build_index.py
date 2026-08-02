#!/usr/bin/env python3
"""Build wasatch_county/campaign_finance/index.csv (+ out_of_scope.csv, unrecovered.csv).

Office/seat assignments come from the COUNTY'S OWN published candidate listings (the clerk's
elections pages, per cycle) and, where the listing is silent or a portal label is untrustworthy,
from the FORM HEADER inside the filing itself (county form = Utah Code 17-16-6.5 "FINANCIAL
CAMPAIGN REPORT ... County Clerk"; school-board form = 20A-11-1301 "SCHOOL BOARD CANDIDATE").
"""
import csv, hashlib, json, os, glob, shutil

ROOT = "/Users/tysonwelsh/civic-data/wasatch_county/campaign_finance"

NOTES = {  # curated per-filing notes (moved from the hand-extended index, 2026-08-01)
    'raw/2020/2020_OctJGranger.pdf':
        'AcroForm text layer carries the typed VALUES only (no template text) — form family undetectable from text; read the PDF for the form header.',
    'raw/2024/202403_state_Adams.pdf':
        "Lt. Governor site copy (disclosures.utah.gov /Municipal/wasatch_2024) — the ONLY county-office filing the state system holds for Wasatch in an even year after 2012. Not a duplicate of the county's June copy (different report date, 03-26-24).",
    'raw/2024/202406_ToriBroughton.pdf':
        'Image-only scan; OCR too degraded to read the form header — form family left blank (honest gap).',
    'raw/2024/202411_727_b-adams-10-29-24.pdf':
        'Recovered from the Internet Archive with no pinned timestamp (the retired Jadu CMS 404s); its sibling b-adams-9-30-24 was never archived — see unrecovered.csv.',
    'raw/2026/202606_S-Farrell-elimination.pdf':
        "Portal label says 'Elimination Report'; the FILING ITSELF has BOTH the 'Partisan Convention Report' and the 'Candidate Withdrawal/Disqualification/Elimination Report' boxes checked (signed 6/16/2026). Period recorded as published; the form is internally ambiguous — verified from the page image 2026-08-01.",
}


def _form_family(path):
    """Per-filing form family from the VISION cache (the page-read variant is the
    primary-document evidence; the old statute-header classifier misfiled 6 rows because
    the 2024 sheet still cites 17-16-6.5 — coordinator fix 2026-08-01)."""
    import hashlib as _h, json as _j
    fp = os.path.join(ROOT, "vision", _h.sha1(path.encode()).hexdigest()[:8] + ".json")
    if os.path.exists(fp):
        return _j.load(open(fp)).get("_meta", {}).get("form_variant_vision", "")
    return ""

# ---- school-board filings (OUT OF SCOPE) identified by form header / county listing -----------
DROP = {
    "2010": ["2010_Ann-Horner-6-3-10", "2010_Ann-Horner-8-31-10", "2010_Debra-Jones-6-8-10",
             "2010_Debra-Jones-8-31-10", "2010_Rob-Heywood-6-14-10", "2010_Rob-Heywood-8-31-10"],
    "2012": ["2012_Blaik-T.-Baird-6-13-12-Primary", "2012_Jenifer-Lynn-Kelson-7-16-12-Primary",
             "2012_Jon-Wallace-Jacobsmeyer-6-19-12-Primary", "2012_Mark-Davis-6-19-12-Primary",
             "2012_Shad-Edward-Sorenson-6-19-12-Primary", "2012_Wilma-D.-Cowley-6-12-12-Primary"],
    "2018": ["2018_Financial-Campaign-Report-Cory-Holmes",
             "2018_Financial-Campaign-Report-Tyler-Wilson-Bluth"],
    "2020": ["2020_%s%s" % (p, n) for p in ("June", "Oct", "Dec")
             for n in ("MAllen", "MDavis", "KPaulsen", "KDickerson", "THansen", "AKoumarela")],
}
DROP_META = {  # slug -> (candidate, office/seat as published, evidence)
    "Ann-Horner": ("Ann Horner", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Debra-Jones": ("Debra Jones", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Rob-Heywood": ("Rob Heywood", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Blaik-T.-Baird": ("Blaik T. Baird", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Jenifer-Lynn-Kelson": ("Jenifer Lynn Kelson", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Jon-Wallace-Jacobsmeyer": ("Jon Wallace Jacobsmeyer", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Mark-Davis": ("Mark Davis", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Shad-Edward-Sorenson": ("Shad Edward Sorenson", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Wilma-D.-Cowley": ("Wilma D. Cowley", "Local School Board", "form header: SCHOOL BOARD CANDIDATE / 20A-11-1301"),
    "Cory-Holmes": ("Cory Holmes", "School Board Member", "form field 'Name of Office: School Board Member'"),
    "Tyler-Wilson-Bluth": ("Tyler Wilson Bluth", "Wasatch County School Board", "form field 'Name of Office' (read from page image)"),
    "MAllen": ("Marianne B Allen", "Local School Board County South", "county 2020 candidate listing"),
    "MDavis": ("Mark Davis", "Local School Board County South", "county 2020 candidate listing"),
    "KPaulsen": ("Kimo Paulsen", "Local School Board County East", "county 2020 candidate listing"),
    "KDickerson": ("Kimberly Dickerson", "Local School Board County East", "county 2020 candidate listing"),
    "THansen": ("Tom Hansen", "Local School Board Midway", "county 2020 candidate listing"),
    "AKoumarela": ("Athina Koumarela", "Local School Board Midway", "county 2020 candidate listing"),
}

# ---- per-cycle office/seat tables --------------------------------------------------------------
C2010 = {  # slug-stem -> (candidate, office, seat, period, date)
    "2010_Holly-Yergensen-6-14-10": ("Holly Yergensen", "County Treasurer", "", "June 2010 (pre-primary)", "2010-06-14"),
    "2010_James-Koson-6-15-10": ("James Wade Koson", "County Attorney", "County-wide", "June 2010 (pre-primary)", "2010-06-15"),
    "2010_Karl-Mcdonald-6-10-10": ("Karl McDonald", "County Treasurer", "", "June 2010 (pre-primary)", "2010-06-10"),
    "2010_Scott-Sweat-6-15-10": ("Scott Sweat", "County Attorney", "County", "June 2010 (pre-primary)", "2010-06-15"),
}
C2018 = {
    "2018_Financial-Campaign-Report--Scott-Sweat": ("Scott Sweat", "County Attorney", ""),
    "2018_Financial-Campaign-Report--Tyler-J.-Berg": ("Tyler J. Berg", "County Attorney", ""),
    "2018_Financial-Campaign-Report--Tyler-Richard-Dow": ("Tyler Richard Dow", "County Attorney", ""),
    "2018_Financial-Campaign-Report-Alan-Wane-McDonald": ("Alan Wane McDonald", "County Council", "At Large"),
    "2018_Financial-Campaign-Report-Brent-R.-Titcomb": ("Brent R. Titcomb", "Clerk/Auditor", ""),
    "2018_Financial-Campaign-Report-Danny-Goode": ("Danny Goode", "County Council", "Heber North"),
    "2018_Financial-Campaign-Report-Jeff-Wade": ("Jeff Wade", "County Council", "County East"),
    "2018_Financial-Campaign-Report-Kit-R.-Kosakowski": ("Kit R. Kosakowski", "County Attorney", ""),
}
C2020 = {  # name-suffix -> (candidate, office, seat)
    "SFarrell": ("Steve Farrell", "County Council", "Seat B — At Large"),
    "AArmer": ("Aimee Armer", "County Council", "Seat B — At Large"),
    "KCrittenden": ("Kendall Crittenden", "County Council", "Seat D — Heber South"),
    "EHokanson": ("Elizabeth Hokanson", "County Council", "Seat D — Heber South"),
    "MNelson": ("Mark B Nelson", "County Council", "Seat E — Midway"),
    "SPark": ("Spencer Jason Park", "County Council", "Seat G — County South"),
    "TGriffin": ("Todd Griffin", "County Assessor", ""),
    "JLee": ("Jennifer Lee", "Clerk/Auditor", "2-year term"),
    "JGranger": ("Joey D Granger", "Clerk/Auditor", "2-year term"),
    "XThomas 2020": ("Xela Thomas", "Clerk/Auditor", "2-year term (withdrawn)"),
    "MMurray": ("Marcy Murray", "County Recorder", ""),
    "JKaiserman": ("James C Kaiserman", "County Surveyor", ""),
    "JJenkins": ("Jason G Jenkins", "County Surveyor", ""),
    "DBurgener": ("Diane G Burgener", "County Treasurer", ""),
}
PER2020 = {"June": ("June 2020 (7 days before Primary)", "2020-06-01"),
           "Oct": ("October 2020 (7 days before General)", "2020-10-01"),
           "Dec": ("December 2020 (30 days after General)", "2020-12-01")}

# 2022 / 2024 / 2026 — candidate, office, seat keyed on the raw slug
C2022 = {
    "202206_K.-Facer-Financial-Disclosure": ("Kim Facer", "County Council", "Seat A — At Large"),
    "202206_ERowlandPrimaryFinancialDisclosure": ("Erik Kim Rowland", "County Council", "Seat C — Heber North"),
    "202206_JGrangerPrimaryFinancialCampaignReport": ("Joey D. Granger", "Clerk/Auditor", ""),
    "202206_JRigbyFinancialDisclosure": ("Jared W. Rigby", "County Sheriff", ""),
    "202206_K.-Mcmillan-Financial-Campaign-disclosure": ("Karl G. McMillan", "County Council", "Seat F — County East"),
    "202206_L.-Searle-Financial-Disclosure": ("Luke Searle", "County Council", "Seat A — At Large"),
    "202206_SSweatFinancialDisclosure": ("Scott H. Sweat", "County Attorney", ""),
    "202211_E.-Rowland-Financial-Disclosure": ("Erik Kim Rowland", "County Council", "Seat C — Heber North"),
    "202211_J.-Granger-Financial-Disclosure-General_001": ("Joey D. Granger", "Clerk/Auditor", ""),
    "202211_Jared-Rigbys-Financial-Campaign-Report-11.1.22": ("Jared W. Rigby", "County Sheriff", ""),
    "202211_K.-McMillan-Financial-Disclosure-General_001": ("Karl G. McMillan", "County Council", "Seat F — County East"),
    "202211_L.-Searle-Financial-Disclosure-General": ("Luke Searle", "County Council", "Seat A — At Large"),
    "202211_S.-Sweat-Financial-Disclosure-General_001": ("Scott H. Sweat", "County Attorney", ""),
}
PER2022 = {"202206": "Primary/June 2022", "202211": "General 2022"}

C2024 = {
    "202406_ColleenBonner": ("Colleen Bonner", "County Council", "Seat B"),
    "202406_NickLopez": ("Nick Lopez", "County Council", "Seat B"),
    "202406_KendallCrittenden": ("Kendall Crittenden", "County Council", "Seat D"),
    "202406_JamiSmithHewlett": ("Jami Smith Hewlett", "County Council", "Seat D"),
    "202406_ToriBroughton": ("Tori E. Broughton", "County Council", "Seat D"),
    "202406_MarkNelson": ("Mark B. Nelson", "County Council", "Seat E"),
    "202406_SherrieBercuson": ("Sherrie Bercuson", "County Council", "Seat E"),
    "202406_SpencerPark": ("Spencer J. Park", "County Council", "Seat G"),
    "202406_BobAdams": ("Bob Adams", "County Assessor", ""),
    "202406_ToddGriffin": ("Todd M. Griffin", "County Assessor", ""),
    "202406_MarcyMurray": ("Marcy Murray", "County Recorder", ""),
    "202406_JamesCKaiserman": ("James C. Kaiserman", "County Surveyor", ""),
    "202406_AmberGibbs": ("Amber Gibbs", "County Treasurer", ""),
    "202411_746_colleen-bonner-campaign-001": ("Colleen Bonner", "County Council", "Seat B"),
    "202411_729_j-hewlett-general": ("Jami Smith Hewlett", "County Council", "Seat D"),
    "202411_728_s-bercusson-general-001": ("Sherrie Bercuson", "County Council", "Seat E"),
    "202411_732_s-park-general": ("Spencer J. Park", "County Council", "Seat G"),
    "202411_727_b-adams-10-29-24": ("Bob Adams", "County Assessor", ""),
    "202411_731_m-murray-general": ("Marcy Murray", "County Recorder", ""),
    "202411_735_j-kaiserman-general-001": ("James C. Kaiserman", "County Surveyor", ""),
    "202403_state_Adams": ("Bob Adams", "County Assessor", ""),
}
PER2024 = {"202403": "March 2024 (state-site copy)", "202406": "June 2024 (pre-primary)",
           "202411": "General 2024 (pre-general / post-election)"}

C2026 = {
    "E-Mainord": ("Eric Mainord", "County Sheriff", "(withdrawn)"),
    "E-Rowland": ("Erik K. Rowland", "County Council", "Seat C"),
    "J-Granger": ("Joey D. Granger", "Clerk/Auditor", ""),
    "J-Hales": ("Jeremy M. Hales", "County Sheriff", ""),
    "J-Rigby": ("Jared W. Rigby", "County Sheriff", ""),
    "J-Tugaw": ("Joseph A. Tugaw", "County Council", "Seat F"),
    "J-Woodard": ("Jon Woodard", "County Attorney", ""),
    "K-McMillan": ("Karl McMillan", "County Council", "Seat F (withdrawn)"),
    "L-Forsyth": ("Lauren Forsyth", "County Attorney", ""),
    "M-Kellogg": ("Michelle Kellogg", "Clerk/Auditor", ""),
    "M-Murphy": ("Michael Murphy", "County Council", "Seat F"),
    "P-Saucier": ("Patrick M. Saucier", "County Council", "Seat A"),
    "R-Kahler": ("Rachel Kahler", "County Council", "Seat A"),
    "S-Farrell": ("Steve Farrell", "County Council", "Seat A"),
    "S-Farrell-elimination": ("Steve Farrell", "County Council", "Seat A"),
    "W-Vance": ("William B. Vance", "County Council", "Seat A"),
}
PER2026 = {"202603": "March 2026 (Partisan Convention Report, due 3/31)",
           "202606": "June 2026 (Primary / Elimination Report)"}


def main():
    # ---- drop out-of-scope (school board) ------------------------------------------------------
    oos = []
    logs = {}
    for y in sorted(set(list(DROP) )):
        p = os.path.join(ROOT, "raw", y, "_fetch_log.jsonl")
        if os.path.exists(p):
            logs[y] = {json.loads(l)["slug"]: json.loads(l) for l in open(p)}
    for y, slugs in DROP.items():
        for s in slugs:
            for sub, ext in (("raw", ".pdf"), ("text", ".txt")):
                f = os.path.join(ROOT, sub, y, s + ext)
                if os.path.exists(f):
                    os.remove(f)
            key = [k for k in DROP_META if k in s]
            cand, off, ev = DROP_META[key[0]] if key else ("", "", "")
            rec = logs.get(y, {}).get(s, {})
            oos.append(dict(election_year=y, candidate=cand, office_as_published=off,
                            source_url=rec.get("source_url", ""), evidence=ev,
                            reason="school board — outside the COUNTY-OFFICE scope of this module"))

    with open(os.path.join(ROOT, "out_of_scope.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["election_year", "candidate", "office_as_published",
                                          "source_url", "evidence", "reason"])
        w.writeheader()
        w.writerows(sorted(oos, key=lambda r: (r["election_year"], r["candidate"])))

    # ---- text-extraction manifest --------------------------------------------------------------
    tex = {r["path"]: r for r in csv.DictReader(open(os.path.join(ROOT, "text_extraction.csv")))}

    UNREC = {  # slug -> (candidate, office, seat, period)
        "202411_733_k-crittenden-general-001": ("Kendall Crittenden", "County Council", "Seat D", "General 2024"),
        "202411_737_t-broughton-general-001": ("Tori E. Broughton", "County Council", "Seat D", "General 2024"),
        "202411_738_m-nelson-general-001": ("Mark B. Nelson", "County Council", "Seat E", "General 2024"),
        "202411_724_b-adams-9-30-24": ("Bob Adams", "County Assessor", "", "General 2024 (9-30-24)"),
        "202411_725_a-gibbs-general": ("Amber Gibbs", "County Treasurer", "", "General 2024"),
    }
    rows, unrec = [], []
    for y in sorted(os.listdir(os.path.join(ROOT, "raw"))):
        d = os.path.join(ROOT, "raw", y)
        if not os.path.isdir(d) or not y.isdigit():
            continue  # raw/index_pages/ carries a LISTING-page fetch log (different schema)
        log = {json.loads(l)["slug"]: json.loads(l) for l in open(os.path.join(d, "_fetch_log.jsonl"))}
        for slug, rec in log.items():
            if any(slug in v for v in DROP.values()):
                continue
            path = "raw/%s/%s.pdf" % (y, slug)
            if rec.get("channel") == "unrecovered":
                c, o, s, p = UNREC[slug]
                unrec.append(dict(election_year=y, slug=slug, candidate=c, office=o, seat=s,
                                  reporting_period=p, source_url=rec["source_url"],
                                  reason="origin 404 (Jadu CMS retired) and NEVER captured by the "
                                         "Internet Archive (availability API: no snapshots)"))
                continue
            cand = off = seat = period = date = ""
            if y == "2010":
                cand, off, seat, period, date = C2010[slug]
            elif y == "2018":
                cand, off, seat = C2018[slug]
                period, date = "2018 cycle (as published by the county)", "2018-07-01"
            elif y == "2020":
                per = slug.split("_")[1]
                tag = "June" if per.startswith("June") else "Oct" if per.startswith("Oct") else "Dec"
                key = per[len(tag):]
                cand, off, seat = C2020[key]
                period, date = PER2020[tag]
            elif y == "2022":
                cand, off, seat = C2022[slug]
                period = PER2022[slug[:6]]
                date = "2022-06-01" if slug.startswith("202206") else "2022-11-01"
            elif y == "2024":
                cand, off, seat = C2024[slug]
                period = PER2024[slug[:6]]
                date = {"202406": "2024-06-01", "202411": "2024-11-01",
                        "202403": "2024-03-26"}[slug[:6]]
            elif y == "2026":
                cand, off, seat = C2026[slug.split("_", 1)[1]]
                period = PER2026[slug[:6]]
                date = "2026-03-31" if slug.startswith("202603") else "2026-06-01"
            t = tex.get(path, {})
            rows.append(dict(
                date=date, candidate=cand, office=off, seat=seat, election_year=y,
                filing_type="statement", reporting_period=period,
                title="%s — %s campaign financial report (%s)" % (cand, off or "office unstated", period),
                source_url=rec["source_url"],
                archive_url=rec.get("fetched_from", "") if rec.get("channel", "").startswith("wayback") else "",
                retrieved_date=rec["retrieved_utc"][:10],
                form_family=_form_family(path),
                format=t.get("format", ""), extraction_method=t.get("extraction_method", ""),
                path=path, text_path=t.get("text_path", ""),
                pages=t.get("pages", ""), bytes=rec.get("bytes", ""), sha256=rec.get("sha256", ""),
                channel=rec.get("channel", ""),
                needs_review=1,
                notes=NOTES.get(path, ""),
            ))

    cols = ["date", "candidate", "office", "seat", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "archive_url", "retrieved_date",
            "form_family", "format", "extraction_method", "path", "text_path", "pages",
            "bytes", "sha256", "channel", "needs_review", "notes"]
    rows.sort(key=lambda r: (r["election_year"], r["date"], r["candidate"], r["path"]))
    with open(os.path.join(ROOT, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ROOT, "unrecovered.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["election_year", "slug", "candidate", "office", "seat",
                                          "reporting_period", "source_url", "reason"])
        w.writeheader()
        w.writerows(unrec)

    # prune text_extraction.csv to surviving files
    keep = [r for r in tex.values() if os.path.exists(os.path.join(ROOT, r["path"]))]
    with open(os.path.join(ROOT, "text_extraction.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(keep[0].keys()))
        w.writeheader()
        w.writerows(sorted(keep, key=lambda r: r["path"]))

    import collections
    print("index rows", len(rows), "| out_of_scope", len(oos), "| unrecovered", len(unrec))
    c = collections.Counter((r["election_year"], r["office"]) for r in rows)
    for k in sorted(c):
        print("  ", k, c[k])


if __name__ == "__main__":
    main()
