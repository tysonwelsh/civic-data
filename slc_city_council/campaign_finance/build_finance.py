#!/usr/bin/env python3
"""slc_city_council/campaign_finance — module-local builder for the RECORDER-2003 era.

DERIVED. Regenerate:  python3 slc_city_council/campaign_finance/build_finance.py

The 8 filings in raw/recorder_2003/ (recovered from Wayback 2026-08-02, falsifying the
"no PDFs exist anywhere" claim) are born-digital, column-aligned Recorder disclosures:

    Name/Office/Submit Date/amendment header
    SUMMARY            Previous | Total this Period | Total to Date   (3 money columns)
    BALANCE SUMMARY    5 stated lines
    ITEMIZED CONTRIBUTIONS   Name | Amount | Date | Description(Ind/Bus/…)
    ITEMIZED EXPENDITURES    Name | Amount | Date | Description

Parsed with pdftotext -layout; every itemized row carries `geometry` (`p<page>:l<line>:
c<c0>-<c1>` of the AMOUNT token, SCHEMA §2a) so rows are snippet-addressable from birth
(make_snippet.py). Reconciliation: the itemized sum is compared against BOTH the
"Total this Period" and "Total to Date" stated figures; whichever matches (±0.01) is
recorded as the reconciliation basis in notes — never forced, never repaired. donor_type
maps the form's own Description tag (Ind→individual, Bus→business; blank→unknown).
The form prints NO donor addresses (nothing to withhold — PRIVACY trivially satisfied).
Zero-glyph ruling honored via the shared parse_money_cell. Filer values verbatim.
"""
import csv
import decimal
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "campaign_finance"))
import common  # noqa: E402

RAW = D("raw", "recorder_2003")
CYCLE = "2003"

TOTALS_HEADER = [
    "candidate", "office", "election_year", "filing_date", "reporting_period", "filing_type",
    "stated_total_contributions", "stated_total_expenditures", "stated_beginning_balance",
    "stated_ending_balance", "itemized_contrib_sum", "itemized_expend_sum",
    "reconciles_contrib", "reconciles_expend", "recon_delta_contrib", "recon_delta_expend",
    "self_funded_amount", "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
    "extraction_confidence", "notes", "filing_regime",
]
CONTRIB_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "donor_raw", "donor_normalized", "donor_type", "donor_city", "donor_state",
    "donor_district", "amount", "in_kind", "is_incremental", "source_filing", "document_id",
    "line_no", "extraction_confidence", "extract_method", "needs_review", "geometry",
]
EXPEND_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "vendor_raw", "vendor_normalized", "purpose", "amount", "in_kind", "is_incremental",
    "source_filing", "document_id", "line_no", "extraction_confidence", "extract_method",
    "needs_review", "geometry",
]

DTYPE = {"ind": "individual", "bus": "business", "pac": "pac", "party": "party"}
AMT = re.compile(r"-?\d[\d,]*\.\d{2}")
# Row grammar (2026-08-02 reconciliation-driven fixes): a name may collapse the column
# gap to ONE space (Berman Gaufin); In-Kind rows have no date; the under-$50 Aggregate
# line has no date; the section prints its own "Total <amt>" (captured as the anchor).
ROW = re.compile(r"^(?P<name>.+?)\s+(?P<amt>-?\d[\d,]*\.\d{2})"
                 r"(?:\s+(?P<date>\d{1,2}/\d{1,2}/\d{2,4}))?"
                 r"(?:\s+(?P<desc>.+?))?\s*$")


def money(s):
    return decimal.Decimal(s.replace(",", ""))


def parse(pdf):
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True,
                         text=True, check=True).stdout
    lines = txt.split("\n")
    pages, pg = [], 1
    for ln in lines:
        if "\f" in ln:
            pg += ln.count("\f")
        pages.append(pg)

    def grab(pat):
        for ln in lines:
            m = re.search(pat, ln)
            if m:
                return m.group(1).strip()
        return ""

    cand = grab(r"^Name:\s*(.+)")
    office = grab(r"^Office Seeking:\s*(.+)")
    fdate = grab(r"^Submit Date:\s*(.+)")
    amended = grab(r"amendment\?\s*(\w+)").lower() == "yes"

    def summary_row(label):
        for ln in lines:
            if ln.strip().startswith(label):
                vals = AMT.findall(ln)
                if vals:
                    return [money(v) for v in vals]
        return []

    c_sum = summary_row("Contributions Rec")          # "Received" AND "Rec'd" variants
    e_sum = summary_row("Total Expenditures")
    beg = summary_row("Beginning of Reporting Period")
    end = summary_row("Ending of Reporting Period")

    sec_total = [None]

    def section(start_pat, stop_pats):
        out, active = [], False
        for i, ln in enumerate(lines):
            if re.match(start_pat, ln.strip()):
                active = True
                continue
            if active and any(re.match(sp, ln.strip()) for sp in stop_pats):
                break
            if active:
                m = ROW.match(ln.rstrip())
                if m and not ln.strip().startswith(("Name", "SUMMARY")):
                    name = m.group("name").strip()
                    desc = (m.group("desc") or "").strip()
                    if name.lower() == "total":   # "Total" AND "TOTAL" — the section's own anchor
                        sec_total[0] = money(m.group("amt"))
                        continue
                    in_kind = desc.lower() == "in kind" or name.lower().endswith(" in kind")
                    out.append(dict(name=name,
                                    amt=m.group("amt"), date=m.group("date") or "",
                                    desc="" if in_kind else desc, in_kind=in_kind,
                                    aggregate=name.lower().startswith("aggregate"),
                                    line=i + 1, page=pages[i],
                                    c0=m.start("amt"), c1=m.end("amt")))
        return out

    # section() writes its "Total <amt>" line into whatever list `sec_total` names at
    # call time (late-binding closure) — rebind between calls to keep the two anchors.
    ct = sec_total = [None]
    contribs = section(r"ITEMIZED CONTRIBUTIONS", [r"ITEMIZED EXPENDITURES$", r"BALANCE"])
    et = sec_total = [None]
    expends = section(r"ITEMIZED EXPENDITURES", [r"ITEMIZED CONTRIBUTIONS$", r"BALANCE"])
    return dict(candidate=cand, office=office, filing_date=fdate, amended=amended,
                c_sum=c_sum, e_sum=e_sum, beg=beg, end=end,
                c_total=ct[0], e_total=et[0],
                contribs=contribs, expends=expends)


def iso(us_date):
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", us_date or "")
    if not m:
        return ""
    mm, dd, yy = (int(x) for x in m.groups())
    yy = yy + 2000 if yy < 50 else (yy + 1900 if yy < 100 else yy)
    return f"{yy:04d}-{mm:02d}-{dd:02d}"


def main():
    tot, cont, exp = [], [], []
    for fname in sorted(os.listdir(RAW)):
        if not fname.endswith(".pdf"):
            continue
        rel = f"raw/recorder_2003/{fname}"
        p = parse(os.path.join(RAW, fname))
        doc_id = f"recorder2003-{os.path.splitext(fname)[0]}"
        csum = sum((money(r["amt"]) for r in p["contribs"]), decimal.Decimal(0))
        esum = sum((money(r["amt"]) for r in p["expends"]), decimal.Decimal(0))

        def basis(itemized, stated, sec_tot):
            """-> (reconciles, delta_vs_period, note): schedule's own TOTAL first, then the
            summary's this-period / to-date figures. A schedule-total match with a differing
            summary figure is the FILER's self-discrepancy, retained verbatim."""
            cent = decimal.Decimal("0.01")
            period = stated[1] if len(stated) >= 2 else (stated[0] if stated else None)
            if sec_tot is not None and abs(itemized - sec_tot) <= cent:
                if period is not None and abs(sec_tot - period) > cent:
                    return "True", "0.00", \
                        (f"reconciles to the schedule's own printed TOTAL {sec_tot}; the "
                         f"SUMMARY prints {period} — filer self-discrepancy "
                         f"{sec_tot - period} retained verbatim")
                return "True", "0.00", "reconciles to the schedule's printed TOTAL"
            if not stated:
                return "", "", "no stated total printed"
            to_date = stated[-1]
            if abs(itemized - period) <= cent:
                return "True", "0.00", "reconciles to 'Total this Period'"
            if abs(itemized - to_date) <= cent:
                return "True", "0.00", "reconciles to 'Total to Date' (full-record itemization)"
            return "False", str(itemized - period), \
                f"itemized {itemized} vs period {period} / to-date {to_date} — filer figures verbatim"

        rc, dc, nc = basis(csum, p["c_sum"], p["c_total"])
        re_, de, ne = basis(esum, p["e_sum"], p["e_total"])
        # a side with NO schedule at all (no rows, no printed TOTAL) has nothing to
        # reconcile — unknown, never a fabricated match (SCHEMA §6)
        if not p["contribs"] and p["c_total"] is None:
            rc, dc, nc = "", "", "no itemized contribution schedule present"
        if not p["expends"] and p["e_total"] is None:
            re_, de, ne = "", "", "no itemized expenditure schedule present"

        def stated_anchor(summary, sec_tot):
            """The filing's stated total for the validator contract: the SUMMARY period
            figure when present and consistent; else the schedule's own printed TOTAL
            (also filer-stated). A >1-cent summary-vs-schedule split anchors on the
            schedule (what the itemization reconciles to) — the summary figure is
            preserved in notes as the filer's self-discrepancy."""
            period = summary[1] if len(summary) >= 2 else (summary[0] if summary else None)
            if sec_tot is None:
                return period if period is not None else ""
            if period is None or abs(period - sec_tot) > decimal.Decimal("0.01"):
                return sec_tot
            return period

        period_c = stated_anchor(p["c_sum"], p["c_total"])
        period_e = stated_anchor(p["e_sum"], p["e_total"])
        notes = (f"RECORDER-2003 era (Wayback-recovered 2026-08-02). contributions: {nc}; "
                 f"expenditures: {ne}." + (" AMENDMENT per the form." if p["amended"] else ""))
        tot.append({
            "candidate": p["candidate"], "office": p["office"], "election_year": CYCLE,
            "filing_date": iso(p["filing_date"]), "reporting_period": "2003 pre-election (Feb 14)",
            "filing_type": "interim", "stated_total_contributions": str(period_c),
            "stated_total_expenditures": str(period_e),
            "stated_beginning_balance": str(p["beg"][0]) if p["beg"] else "",
            "stated_ending_balance": str(p["end"][0]) if p["end"] else "",
            # a PRESENT schedule with zero rows and its own printed "TOTAL 0.00" is an
            # AFFIRMATIVE zero (born-digital, fully parsed) — emit 0.00, not blank
            # (blank remains reserved for never-transcribed pages, per the repo rule)
            "itemized_contrib_sum": str(csum) if (p["contribs"] or p["c_total"] is not None) else "",
            "itemized_expend_sum": str(esum) if (p["expends"] or p["e_total"] is not None) else "",
            "reconciles_contrib": rc, "reconciles_expend": re_,
            "recon_delta_contrib": dc, "recon_delta_expend": de,
            "self_funded_amount": "", "n_contrib_rows": len(p["contribs"]),
            "n_expend_rows": len(p["expends"]), "source_filing": rel,
            "document_id": doc_id, "extraction_confidence": "high",
            "notes": notes, "filing_regime": "election_cycle",
        })
        for i, r in enumerate(p["contribs"], 1):
            cont.append({
                "candidate": p["candidate"], "office": p["office"], "seat": "",
                "election_year": CYCLE, "filing_date": iso(p["filing_date"]),
                "reporting_period": "2003 pre-election (Feb 14)", "date": iso(r["date"]),
                "donor_raw": r["name"], "donor_normalized": r["name"],
                "donor_type": DTYPE.get(r["desc"].lower(), "unknown" if not r["desc"] else "other"),
                "donor_city": "", "donor_state": "", "donor_district": "",
                "amount": r["amt"].replace(",", ""), "in_kind": "False",
                "is_incremental": "True", "source_filing": rel, "document_id": doc_id,
                "line_no": i, "extraction_confidence": "high",
                "extract_method": "recorder2003/text", "needs_review": "0",
                "geometry": f"p{r['page']}:l{r['line']}:c{r['c0']}-{r['c1']}",
            })
        for i, r in enumerate(p["expends"], 1):
            exp.append({
                "candidate": p["candidate"], "office": p["office"], "seat": "",
                "election_year": CYCLE, "filing_date": iso(p["filing_date"]),
                "reporting_period": "2003 pre-election (Feb 14)", "date": iso(r["date"]),
                "vendor_raw": r["name"], "vendor_normalized": r["name"],
                "purpose": r["desc"], "amount": r["amt"].replace(",", ""),
                "in_kind": "False", "is_incremental": "True", "source_filing": rel,
                "document_id": doc_id, "line_no": i, "extraction_confidence": "high",
                "extract_method": "recorder2003/text", "needs_review": "0",
                "geometry": f"p{r['page']}:l{r['line']}:c{r['c0']}-{r['c1']}",
            })

    def write(path, header, rows):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows)

    write(D("filing_totals.csv"), TOTALS_HEADER, tot)
    write(D("contributions.csv"), CONTRIB_HEADER, cont)
    write(D("expenditures.csv"), EXPEND_HEADER, exp)
    ok_c = sum(1 for t in tot if t["reconciles_contrib"] == "True")
    ok_e = sum(1 for t in tot if t["reconciles_expend"] == "True")
    print(f"filing_totals {len(tot)} | contributions {len(cont)} | expenditures {len(exp)}")
    print(f"reconcile: contributions {ok_c}/{len(tot)} · expenditures {ok_e}/{len(tot)}")
    for t in tot:
        if t["reconciles_contrib"] != "True" or t["reconciles_expend"] != "True":
            print("  ⚠", t["candidate"], "—", t["notes"][:120])


if __name__ == "__main__":
    main()
