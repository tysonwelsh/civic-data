#!/usr/bin/env python3
"""Build the STRUCTURED campaign-finance layer for Salt Lake County COUNTY offices from the
EasyVote portal's ITEMIZED advanced-search JSON (the genuinely-structured source — not PDF
text). Writes contributions.csv / expenditures.csv / filing_totals.csv per
scripts/campaign_finance/SCHEMA.md.

Source of truth: raw/easyvote_api/advancedsearch_{contributions,distributions}.json
(itemized per-transaction rows straight from the county EasyVote API), joined to
documentsearch.json (filer + filing metadata) and the downloaded redacted PDFs (raw/easyvote/).

Design notes (honest caveats, see CLAUDE.md):
- The API exposes NO in-kind flag and NO donor address -> in_kind=False for all rows;
  donor_city/state/district blank. Extraction is `high` (structured API, not OCR).
- The API does NOT return each filing's PRINTED (stated) totals; those live only in the
  image-only redacted PDFs. So filing_totals carries itemized sums with BLANK stated_* and
  BLANK reconciles_* (unknown, never a fabricated mismatch). The integrity signal here is
  "authoritative structured itemized source", documented in notes.
- election_year is the EVEN-year proxy (build_lib.election_year_from_date).

SECOND, ADDITIVE PATH (2026-08-01 vision totals tranche) — `build_totals_tranche()`:
the two NON-STRUCTURED eras (the ~2006-2015 clerk legacy PDFs and the 2022 EasyVote cycle)
have no itemized source at all, so their filings are given **stated-totals-only**
filing_totals rows read off each filing's own cover + Summary Page by Read-tool vision
(caches in `vision/`, schema documented in CLAUDE.md). Those rows are APPENDED after the
EasyVote-JSON rows, which are emitted first and unchanged — the 2024/2026 structured layer
is byte-identical across this change. No contributions/expenditures rows are produced for
these eras this tranche (itemization deferred), so their `itemized_*` / `reconciles_*` stay
BLANK: the honest "unknown" state, never a fabricated reconciliation.
"""
import json, os, sys, csv, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance")))
import build_lib as BL
import vision_lib as VL
import common
from common import ContribRow, ExpendRow, FilingTotals, CONTRIB_HEADER, EXPEND_HEADER, TOTALS_HEADER, money_str, row_to_dict
from normalize_donors import tier1, classify_donor_type, normalize_contrib, normalize_vendor, load_aliases

API = os.path.join(HERE, "raw", "easyvote_api")
VISION = os.path.join(HERE, "vision")


def load_json(name):
    return json.load(open(os.path.join(API, name)))


# =====================================================================================
# VISION TOTALS TRANCHE (2026-08-01) — the two non-structured eras
# =====================================================================================
# Salt Lake County ran ONE county C&E form from 2006 through 2022 (page 1 = cover with
# candidate / Office Sought / the checked "Type of Report" box; page 2 = "Summary Page"
# with Column A "Total this Period" + Column B "Sum Total to Date"). Both non-structured
# eras — the clerk legacy PDFs and the 2022 EasyVote cycle — print that form and nothing
# machine-readable, so the stated totals are transcribed by Read-tool vision into
# `vision/<sha1(index path)[:8]>.json` (the repo-standard key, vision_lib.cache_key).
#
# Discipline (SCHEMA.md §4/§6 + the repo cardinal rules):
#   * every value is the form's own PRINTED figure, verbatim — nothing is computed here
#     (Line 7 is never derived from Lines 5-6, Column B is never filled from Column A);
#   * the cache's three-state convention is preserved: a string = printed, "" = the filer
#     left the cell blank, null = printed but ILLEGIBLE -> stays blank + drops confidence;
#   * `reporting_period` prefers the FORM's own checked report-type label over the clerk
#     listing-page label (GOTCHAS: portal/listing labels lie); the listing label is kept in
#     `notes` whenever the two disagree;
#   * interim and summary/final filings OVERLAP by design — `filing_type` records which is
#     which so cycle_totals.py can dedup. NEVER sum these rows for a candidate-cycle total.

# The interim deadlines the county form has printed across its versions (April 5 · June 20 /
# June 21 / "seven days before a primary" · September 15 · October 31 / "seven days before a
# general"), matched tolerantly because the transcriber records the checkbox label VERBATIM
# and the wording drifted between form years ("Sept 15", "Nov 1"). Checked only AFTER the
# summary / final / year-end tests, so "January 31" can never fall through to a month match.
_INTERIM_RE = re.compile(r"(?i)\b(apr|jun|jul|aug|sep|oct|nov|dec|seven days|interim|primary|general)")
_CONF_NAME = {3: "high", 2: "medium", 1: "low"}
_CONF_RANK = {"high": 3, "medium": 2, "low": 1}


def filing_type_from_report_type(report_type):
    """The form's OWN checked 'Type of Report' label -> the `filing_type` vocabulary
    cycle_totals.py reads (its SUMMARY_TYPES = summary|final|year-end|yearend|annual|
    combined; anything else is treated as an interim). The verbatim label itself is kept
    in `reporting_period`. Unchecked / unreadable -> '' (honest unknown, never guessed)."""
    s = (report_type or "").strip().lower()
    if not s:
        return ""
    if "dissolution" in s or "final" in s:
        return "final"
    if "january 31" in s or "year-end" in s or "year end" in s:
        return "year-end"
    if "summary" in s:
        return "summary"
    if _INTERIM_RE.search(s):
        return "interim"
    return ""


def tranche_confidence(cache):
    """Filing-level confidence for a vision-transcribed totals row.

    CAPPED AT `medium`: SCHEMA §6 reserves `high` for a born-digital / structured source,
    and this era is a page image read by vision (the same tier as OCR). A stated total that
    came back ILLEGIBLE (null), or that the transcriber flagged `low`, drops the filing to
    `low`. A cell the filer left BLANK ("") is not a confidence problem. No Summary Page
    found (or no cache) -> '' (not attempted / nothing to grade)."""
    if not cache or not cache.get("_meta", {}).get("summary_page_found"):
        return ""
    conf = cache.get("confidence") or {}
    ranks = []
    for f in ("total_contributions", "total_expenditures"):
        v = cache.get(f)
        if v is None:
            ranks.append(1)                       # printed but illegible
        else:
            ranks.append(min(2, _CONF_RANK.get(str(conf.get(f, "medium")).lower(), 2)))
    return _CONF_NAME[min(ranks)] if ranks else ""


def verbatim_money(printed):
    """A VERBATIM printed figure from a vision cache -> (decimal string, repaired_flag).

    Handwritten county forms use a decimal COMMA often enough to matter ("1920,00" for
    $1,920.00, seen on the 2006 Morgan amendment). Read naively that becomes $192,000 — a
    100x fabrication. So the figure is run through the SHARED, whitelisted currency repair
    (`common.repair_money_line`: final-comma-as-decimal, dot-as-thousands) before parsing;
    a 3-digit trailing group ("2,500") is still read as thousands, and anything the repair
    cannot make unambiguous stays BLANK. Repaired values are flagged so the filing's note
    records it (SCHEMA §6: every repaired value is marked)."""
    if printed is None or str(printed).strip() == "":
        return "", False
    raw = str(printed).strip()
    # repair_money_line only rewrites $-prefixed tokens, so add a `$` when the printed
    # figure has none — but never in front of a parenthesised negative ("(11,592.46)",
    # the accounting-style negative the 2022 forms print for an overdrawn balance) or a
    # value that already carries one.
    tok = raw if ("$" in raw or raw.startswith(("-", "("))) else "$" + raw
    fixed, changed = common.repair_money_line(tok)
    val = VL.vmoney(fixed)
    if val is None:
        return "", False
    return money_str(val), (changed and VL.vmoney(tok) != val)


def load_cache(index_path):
    p = os.path.join(VISION, VL.cache_key(index_path) + ".json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def build_totals_tranche():
    """FilingTotals rows for the clerk-legacy (~2006-2015) + EasyVote-2022 eras, from the
    `vision/` stated-totals caches. Returns (rows, stats). One row per index.csv filing in
    those eras — including filings with NO cache, which are emitted as honest
    acquired-but-not-transcribed inventory rows (all stated_* blank)."""
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        idx = list(csv.DictReader(fh))
    rows, stats = [], Counter()
    for r in idx:
        if r["source"] == "clerk_legacy":
            era = "clerk_legacy"
        elif r["source"] == "easyvote" and r["election_year"] == "2022":
            era = "easyvote_2022"
        else:
            continue
        stats[era] += 1
        cache = load_cache(r["path"])
        meta = (cache or {}).get("_meta", {})
        cover = (cache or {}).get("cover", {}) or {}
        notes = []

        # --- office: the form's own "Office Sought" outranks the clerk listing-page header,
        # but only where the listing label did not already normalize to a county office.
        office = r["office"]
        if office not in BL.COUNTY_OFFICE_SET and cover.get("office_sought"):
            o2, _ = BL.normalize_office(cover["office_sought"])
            if o2 in BL.COUNTY_OFFICE_SET:
                notes.append(f"office read from the form's own 'Office Sought' "
                             f"({cover['office_sought']!r}); clerk listing said {office!r}")
                office = o2
                stats["office_from_form"] += 1

        # --- election_year / filing_date: FILL ONLY WHERE index.csv is blank (never
        # overwrite an acquisition-time value). Source = the form's own signature date /
        # title year, then the same EVEN-year proxy the rest of this module uses.
        eyear, fdate = r["election_year"], r["date"]
        form_iso = VL.vdate(cover.get("report_date") or "")
        if not fdate and form_iso:
            fdate = form_iso
            stats["filing_date_from_form"] += 1
        if not eyear:
            ey = (BL.election_year_from_date(form_iso)
                  or BL.election_year_from_date(cover.get("form_year") or ""))
            if ey:
                eyear = ey
                notes.append("election_year absent from the clerk listing; derived from the "
                             "form's own date/title year via the EVEN-year proxy")
                stats["election_year_from_form"] += 1

        # --- reporting_period: the form's checked label wins; keep the listing label when
        # the two disagree (a label is evidence, not truth).
        rp_form = (cover.get("report_type") or "").strip() if cover.get("report_type") else ""
        rp = rp_form or r["reporting_period"]
        if rp_form and r["reporting_period"] and rp_form.lower() not in r["reporting_period"].lower():
            notes.append(f"clerk listing label: {r['reporting_period']}")
        ftype = filing_type_from_report_type(rp_form)

        if str(cover.get("is_amendment") or "").strip().lower().startswith("y"):
            of = (cover.get("amendment_of") or "").strip()
            notes.append("the form marks this an AMENDMENT" + (f" of {of}" if of else ""))
            stats["amendment"] += 1

        # --- stated figures (verbatim printed -> decimal string; illegible stays blank)
        repaired = []

        def m(field):
            if not cache:
                return ""
            v, fixed = verbatim_money(cache.get(field))
            if fixed:
                repaired.append(f"{field}={cache.get(field)!r}")
            return v
        s_c, s_e = m("total_contributions"), m("total_expenditures")
        s_b, s_end = m("beginning_balance"), m("ending_balance")
        if repaired:
            notes.append("whitelisted currency repair applied to the verbatim printed figure "
                         "(decimal-comma / dot-thousands): " + ", ".join(repaired))
            stats["currency_repair"] += 1

        if cache is None:
            notes.append("ACQUIRED, NOT TRANSCRIBED — no vision cache for this filing")
            stats["no_cache"] += 1
        elif not meta.get("summary_page_found"):
            notes.append("no Summary Page found in this document — stated totals unavailable")
            stats["no_summary_page"] += 1
        else:
            stats["transcribed"] += 1
            for field, label in (("total_contributions", "Total Contributions Received"),
                                 ("total_expenditures", "Total Expenditures Made")):
                if cache.get(field) is None:
                    notes.append(f"{label} printed but ILLEGIBLE — left blank, never guessed")
                    stats["illegible_total"] += 1
            agg = cache.get("aggregate") or {}
            colb = [f"{k}={v}" for k, v in (("contrib", agg.get("total_contributions_to_date")),
                                            ("expend", agg.get("total_expenditures_to_date")))
                    if v]
            if colb:
                notes.append("Column B sum-to-date as printed: " + ", ".join(colb))
        if cache and cache.get("_meta", {}).get("notes"):
            notes.append("transcriber: " + str(cache["_meta"]["notes"]))

        head = ("stated totals VISION-TRANSCRIBED from the filing's own cover + Summary Page "
                "(Read-tool, $0 API; 2026-08-01 totals tranche); itemized layer NOT built for "
                f"this era -> reconciliation unknown [{era}]")
        rows.append(FilingTotals(
            candidate=r["candidate"], office=office, election_year=eyear,
            filing_date=fdate, reporting_period=rp, filing_type=ftype,
            stated_total_contributions=s_c, stated_total_expenditures=s_e,
            stated_beginning_balance=s_b, stated_ending_balance=s_end,
            itemized_contrib_sum="", itemized_expend_sum="",
            reconciles_contrib="", reconciles_expend="",
            recon_delta_contrib="", recon_delta_expend="", self_funded_amount="",
            n_contrib_rows="0", n_expend_rows="0",
            source_filing=r["path"],
            document_id=r["document_id"] or VL.cache_key(r["path"]),
            extraction_confidence=tranche_confidence(cache),
            notes="; ".join([head] + notes)))
    return rows, stats


def build():
    offices = {o["OfficeId"].upper(): o["OfficeName"] for o in load_json("offices.json")}
    docsearch = load_json("documentsearch.json")
    contribs = load_json("advancedsearch_contributions.json")
    distribs = load_json("advancedsearch_distributions.json")

    # DocumentFilingId (base GUID) -> filer/filing metadata from documentsearch
    doc_meta = {}
    filer_path = {}
    # map documentid -> download path via the easyvote fetch log
    for line in open(os.path.join(HERE, "raw", "easyvote", "_fetch_log.jsonl")):
        r = json.loads(line)
        if r.get("documentid") and not r.get("error"):
            filer_path[r["documentid"].upper()] = r["path"]
    for f in docsearch:
        for d in f["documents"]:
            did = (d.get("documentid") or "").upper()
            if not did:
                continue
            doc_meta[did] = {
                "displayname": f["displayname"], "officename": f["officename"],
                "filertype": f["filertype"], "datesubmitted": d.get("datesubmitted"),
                "documentname": d.get("documentname"), "documenttype": d.get("documenttype"),
            }

    aliases = load_aliases(os.path.join(HERE, "donor_aliases.csv"))

    def base_fid(r):
        return (r.get("DocumentFilingId") or "").replace("_Redacted", "").upper()

    def county_office(guid):
        return BL.is_county_officename(offices.get((guid or "").upper(), ""))

    def meta_for(fid):
        return doc_meta.get(fid)

    crows, erows = [], []
    # group itemized by filing for line_no + totals
    by_filing_c = defaultdict(list)
    by_filing_e = defaultdict(list)
    for r in contribs:
        if county_office(r.get("OfficeGuid")):
            by_filing_c[base_fid(r)].append(r)
    for r in distribs:
        if county_office(r.get("OfficeGuid")):
            by_filing_e[base_fid(r)].append(r)

    all_fids = set(by_filing_c) | set(by_filing_e)
    filing_rows = []
    skipped_no_meta = []

    def filing_common(fid, sample):
        m = meta_for(fid)
        if m:
            cand = m["displayname"]
            office_raw = m["officename"]
            fdate = BL.easyvote_iso(m["datesubmitted"])
            period = m.get("documentname") or ""
        else:
            # itemized-only filing (no documentsearch doc) -> fall back to itemized name
            cand = sample.get("displayrecipientname") or sample.get("displaycandidatename") or ""
            office_raw = offices.get((sample.get("OfficeGuid") or "").upper(), "")
            fdate = ""
            period = ""
            skipped_no_meta.append(fid)
        office, seat = BL.normalize_office(office_raw)
        eyear = BL.election_year_from_date(fdate) or BL.election_year_from_date(
            sample.get("ContributionDate") or sample.get("DistributionDate"))
        path = filer_path.get(fid, "")
        return cand, office, seat, eyear, fdate, period, path

    skipped_no_pdf = []
    for fid in sorted(all_fids):
        cl = by_filing_c.get(fid, [])
        el = by_filing_e.get(fid, [])
        sample = (cl or el)[0]
        cand, office, seat, eyear, fdate, period, path = filing_common(fid, sample)
        # Skip filings that have no downloaded PDF (itemized-only records with no
        # documentsearch doc — e.g. EasyVote's "Training Candidate" test record). They
        # cannot be keyed to an index.csv path, so they are honestly excluded (logged).
        if not path:
            skipped_no_pdf.append((fid, cand))
            continue
        # contributions
        c_sum = 0.0
        self_funded = 0.0
        for i, r in enumerate(sorted(cl, key=lambda x: (x.get("ContributionDate") or "", x.get("ContributionAmount") or 0)), 1):
            donor = BL.contributor_raw(r)
            amt = r.get("ContributionAmount")
            row = ContribRow(candidate=cand, office=office, seat=seat, election_year=eyear,
                             filing_date=fdate, reporting_period=period,
                             date=(r.get("ContributionDate") or "")[:10], donor_raw=donor,
                             donor_city="", donor_state="", donor_district="",
                             amount=money_str(amt), in_kind="False", is_incremental="True",
                             source_filing=path, document_id=fid, line_no=str(i),
                             extraction_confidence="high", extract_method="easyvote_api/json",
                             needs_review=("1" if (amt is None or not donor) else "0"))
            normalize_contrib(row, cand, aliases)
            crows.append(row)
            if amt:
                c_sum += float(amt)
                if row.donor_type in ("candidate-self", "loan"):
                    self_funded += float(amt)
        # expenditures
        e_sum = 0.0
        for i, r in enumerate(sorted(el, key=lambda x: (x.get("DistributionDate") or "", x.get("DistributionAmount") or 0)), 1):
            vendor = BL.payee_raw(r)
            amt = r.get("DistributionAmount")
            row = ExpendRow(candidate=cand, office=office, seat=seat, election_year=eyear,
                            filing_date=fdate, reporting_period=period,
                            date=(r.get("DistributionDate") or "")[:10], vendor_raw=vendor,
                            purpose="", amount=money_str(amt), in_kind="False",
                            is_incremental="True", source_filing=path, document_id=fid,
                            line_no=str(i), extraction_confidence="high",
                            extract_method="easyvote_api/json",
                            needs_review=("1" if amt is None else "0"))
            normalize_vendor(row)
            erows.append(row)
            if amt:
                e_sum += float(amt)
        ft = FilingTotals(candidate=cand, office=office, election_year=eyear,
                          filing_date=fdate, reporting_period=period,
                          filing_type="interim",
                          stated_total_contributions="", stated_total_expenditures="",
                          stated_beginning_balance="", stated_ending_balance="",
                          itemized_contrib_sum=money_str(c_sum) if cl else "",
                          itemized_expend_sum=money_str(e_sum) if el else "",
                          reconciles_contrib="", reconciles_expend="",
                          recon_delta_contrib="", recon_delta_expend="",
                          self_funded_amount=money_str(self_funded) if self_funded else "",
                          n_contrib_rows=str(len(cl)), n_expend_rows=str(len(el)),
                          source_filing=path, document_id=fid,
                          extraction_confidence="high",
                          notes="itemized from EasyVote structured API; stated totals not in API "
                                "(image-only redacted PDF) -> reconciliation unknown")
        filing_rows.append(ft)

    def write(fname, header, rows):
        with open(os.path.join(HERE, fname), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=header)
            w.writeheader()
            for r in rows:
                d = row_to_dict(r)
                w.writerow({k: d.get(k, "") for k in header})

    # ---- ADDITIVE: the vision stated-totals tranche for the two non-structured eras.
    # APPENDED AFTER the EasyVote-JSON rows (which are written first, untouched), so the
    # 2024/2026 structured block of filing_totals.csv stays byte-identical.
    n_structured = len(filing_rows)
    tranche_rows, tstats = build_totals_tranche()
    filing_rows = filing_rows + tranche_rows

    write("contributions.csv", CONTRIB_HEADER, crows)
    write("expenditures.csv", EXPEND_HEADER, erows)
    write("filing_totals.csv", TOTALS_HEADER, filing_rows)
    print(f"contributions {len(crows)} | expenditures {len(erows)} | filings {len(filing_rows)}"
          f" (EasyVote-JSON structured {n_structured} + vision totals tranche {len(tranche_rows)})")
    print("  vision totals tranche: " + " | ".join(f"{k}={v}" for k, v in sorted(tstats.items())))
    print(f"itemized-only filings (no documentsearch meta): {len(set(skipped_no_meta))}")
    print(f"excluded (no downloaded PDF, e.g. Training Candidate): {len(skipped_no_pdf)} -> {skipped_no_pdf}")
    tot_c = sum(float(r.amount) for r in crows if r.amount)
    tot_e = sum(float(r.amount) for r in erows if r.amount)
    print(f"total itemized contributions ${tot_c:,.2f} | expenditures ${tot_e:,.2f}")


if __name__ == "__main__":
    build()
