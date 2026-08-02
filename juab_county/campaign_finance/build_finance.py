#!/usr/bin/env python3
"""Juab County campaign-finance — module-local builder.

DERIVED layer. Regenerate with:  python3 juab_county/campaign_finance/build_finance.py

Emits, from the two curated inputs:
  vision/_download_log.json  (folder, filename, source_url, status, sha256, bytes)
  vision/transcripts.json    (hand-verified vision transcription of every county-office filing)

  index.csv           one row per ACQUIRED file (all 82), with source URL + fetch timestamp + sha256
  filing_totals.csv   one row per COUNTY-OFFICE filing (schema: scripts/campaign_finance/SCHEMA.md §4)
  contributions.csv   one row per itemized contribution line (§2)
  expenditures.csv    one row per itemized expenditure line (§3)

Why a module-local builder and not the shared engine: `scripts/campaign_finance/` dispatches on
form FAMILY (provo_form / lehi_formab / easyvote_schedab). Juab's filings are the handwritten
**Carr Printing 5-5-PG county form (Utah Code 17-16-6.5)**, a family the shared registry does not
carry, and adding one would mean editing shared code. The COLUMN CONTRACT of SCHEMA.md is honored
exactly so these CSVs drop into the shared model unchanged if the family is ever registered.
"""
import csv, hashlib, json, os, datetime, decimal

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
ENTITY = "juab_county"


def _donor_city_state(address):
    """PRIVACY.md: derive donor city/state from a transcribed address WITHOUT carrying
    the street/PO-box portion into the structured layer. Only a city the filer actually
    wrote is emitted ('' otherwise — blank is honest, never inferred)."""
    import re
    m = re.search(r",?\s*([A-Za-z .]+?)[,\s]+(Utah|UT)\.?\s*(\d{5})?\s*$",
                  (address or "").strip())
    if m:
        return {"donor_city": m.group(1).strip().title(), "donor_state": "UT"}
    return {"donor_city": "", "donor_state": ""}


def money(s):
    if s is None or s == "":
        return None
    try:
        return decimal.Decimal(str(s).replace(",", ""))
    except decimal.InvalidOperation:
        return None


def load():
    dl = json.load(open(D("vision", "_download_log.json")))
    tr = json.load(open(D("vision", "transcripts.json")))
    return dl, tr


def build_index(dl, tr):
    """One row per acquired file. Provenance is mandatory: URL, fetch timestamp, sha256."""
    by_path = {}
    for f in tr["filings"]:
        by_path.setdefault(f["path"], []).append(f)

    rows = []
    for folder, fname, url, status, sha, size in dl:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in fname)
        rel = os.path.join("raw", folder.replace(" ", "_").replace("/", "_"), safe)
        abspath = D(rel)
        fetched = ""
        if os.path.exists(abspath):
            fetched = datetime.datetime.fromtimestamp(
                os.path.getmtime(abspath), datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        filings = by_path.get(rel.replace(os.sep, "/"), [])
        base = {
            "state_folder": folder,
            "filename_as_published": fname,
            "path": rel,
            "source_url": url,
            "fetch_status": status,
            "retrieved_utc": fetched,
            "sha256": sha,
            "bytes": size,
        }
        if filings:
            # one index row PER FILING (st_george precedent; validate_finance
            # conformance fix 2026-08-01) — bundle files repeat their path so every
            # (candidate, election_year) in the money layer resolves in the index.
            for f in filings:
                rows.append(dict(base,
                    tier="county_office",
                    classification_basis="form header read from the page image "
                                         "(Utah Code 17-16-6.5, Carr 5-5-PG)",
                    candidate=f["candidate"],
                    office_std=f["office_std"],
                    election_year=str(f["election_year"]),
                    n_filings_in_file=len(filings)))
        else:
            if folder.startswith("juab_2008"):
                basis = ("state folder label 'School Board' + form header verified on 1 of 34 "
                         "sampled (Helen M. Wall) — NOT individually verified")
            else:
                basis = "form header read from the page image (Utah Code 20A-11-1301..1305, Carr 5-4 PG School)"
            rows.append(dict(base,
                tier="school_board",
                classification_basis=basis,
                candidate="", office_std="",
                election_year=folder.split("_")[1].split(" ")[0] if "_" in folder else "",
                n_filings_in_file=""))
    rows.sort(key=lambda r: (r["state_folder"], r["filename_as_published"]))
    write(D("index.csv"), rows)
    return rows


def build_finance(tr):
    cont, exp, tot = [], [], []
    for f in tr["filings"]:
        if f["tier"] != "county_office":
            continue
        doc_id = "%s|%s|%s" % (f["path"], f.get("bundle_pages", ""), f["candidate"])
        # source_filing must resolve to an index.csv path (validate_finance contract,
        # conformance fix 2026-08-01); the bundle page range stays in document_id.
        src = f["path"]
        st = f["stated"]
        # cycle-normalised stated totals: pre-2020 forms split contributions >$50 / <=$50;
        # the 2020 form prints a single named+anon-under-50 line. Sum only what was printed.
        parts = [st.get("contrib_gt50_cum"), st.get("contrib_le50_cum"),
                 st.get("contrib_named_and_anon_lt50_cum")]
        vals = [money(p) for p in parts if p not in (None, "")]
        stated_contrib = sum(vals) if vals else None
        stated_expend = money(st.get("total_expenses_cum"))
        conf = f["confidence"]

        n_c = n_e = 0
        sum_c = decimal.Decimal(0)
        sum_e = decimal.Decimal(0)
        any_blank_c = any_blank_e = False

        for i, c in enumerate(f.get("contributions", []), 1):
            amt = money(c.get("amount"))
            if amt is None:
                any_blank_c = True
            else:
                sum_c += amt
            n_c += 1
            rowconf = c.get("confidence", conf)
            cont.append({
                "candidate": f["candidate"], "office": f["office_std"], "seat": f["office_district"],
                "election_year": f["election_year"], "filing_date": f["filing_date"],
                "reporting_period": "", "date": c.get("date", ""),
                "donor_raw": c.get("donor", ""), "donor_normalized": c.get("donor", ""),
                # PRIVACY.md: structured rows carry donor city/state ONLY (coordinator
                # fix 2026-08-01) — the verbatim address stays in the raw scans and
                # vision/transcripts.json, never in this derived CSV.
                "donor_type": "individual" if c.get("donor") else "unknown",
                **_donor_city_state(c.get("address", "")),
                "donor_district": "",
                "amount": c.get("amount", ""), "in_kind": "False", "is_incremental": "False",
                "source_filing": src, "document_id": doc_id, "line_no": i,
                "extraction_confidence": rowconf,
                "extract_method": "carr_5_5_pg/vision",
                "needs_review": "1" if (rowconf != "high" or not c.get("amount")) else "0",
            })
        for i, e in enumerate(f.get("expenditures", []), 1):
            amt = money(e.get("amount"))
            if amt is None:
                any_blank_e = True
            else:
                sum_e += amt
            n_e += 1
            rowconf = e.get("confidence", conf)
            exp.append({
                "candidate": f["candidate"], "office": f["office_std"], "seat": f["office_district"],
                "election_year": f["election_year"], "filing_date": f["filing_date"],
                "reporting_period": "", "date": e.get("date", ""),
                "vendor_raw": e.get("payee", ""), "vendor_normalized": e.get("payee", ""),
                "purpose": e.get("purpose", ""), "amount": e.get("amount", ""),
                "in_kind": "False", "is_incremental": "False",
                "source_filing": src, "document_id": doc_id, "line_no": i,
                "extraction_confidence": rowconf,
                "extract_method": "carr_5_5_pg/vision",
                "needs_review": "1" if (rowconf != "high" or not e.get("amount")) else "0",
            })

        def recon(stated, isum, n, blank, transcribed):
            # blank = honest unknown, never a fabricated mismatch (SCHEMA.md §"Totals-only filings")
            if not transcribed or n == 0 or blank or stated is None:
                return "", ""
            return ("True" if abs(isum - stated) <= decimal.Decimal("0.01") else "False",
                    str(isum - stated))

        tflag = f["itemized_transcribed"]
        rc, dc = recon(stated_contrib, sum_c, n_c, any_blank_c, tflag)
        re_, de = recon(stated_expend, sum_e, n_e, any_blank_e, tflag)

        notes = f["notes"]
        if not tflag:
            notes = ("itemized Form A/B pages NOT yet transcribed (see AVAILABILITY.md "
                     "'Itemized transcription queue'); stated totals only. " + notes).strip()
        # exact TOTALS_HEADER contract (validate_finance conformance fix 2026-08-01):
        # the module-local face fields (office_verbatim/party/residence_city/addressee/
        # itemized_transcribed) live in vision/transcripts.json + notes, not as extra
        # columns; itemized-not-transcribed is already stated in notes above.
        tot.append({
            "candidate": f["candidate"], "office": f["office_std"],
            "election_year": f["election_year"], "filing_date": f["filing_date"],
            "reporting_period": "", "filing_type": "statement",
            "stated_total_contributions": "" if stated_contrib is None else str(stated_contrib),
            "stated_total_expenditures": "" if stated_expend is None else str(stated_expend),
            "stated_beginning_balance": "",
            "stated_ending_balance": f["stated"].get("ending_balance_cum", ""),
            "itemized_contrib_sum": str(sum_c) if (tflag and n_c) else "",
            "itemized_expend_sum": str(sum_e) if (tflag and n_e) else "",
            "reconciles_contrib": rc, "reconciles_expend": re_,
            "recon_delta_contrib": dc, "recon_delta_expend": de,
            "self_funded_amount": "",
            "n_contrib_rows": n_c, "n_expend_rows": n_e,
            "source_filing": src, "document_id": doc_id,
            "extraction_confidence": conf, "notes": notes,
            "filing_regime": "election_cycle",
        })

    tot.sort(key=lambda r: (r["election_year"], r["office"], r["candidate"]))
    write(D("filing_totals.csv"), tot)
    write(D("contributions.csv"), cont)
    write(D("expenditures.csv"), exp)
    return tot, cont, exp


def write(path, rows):
    if not rows:
        open(path, "w").write("")
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def verify(idx):
    """Re-hash every retained file against index.csv."""
    bad = []
    for r in idx:
        p = D(r["path"])
        if not os.path.exists(p):
            bad.append((r["path"], "MISSING"))
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != r["sha256"]:
            bad.append((r["path"], "SHA MISMATCH"))
    return bad


if __name__ == "__main__":
    dl, tr = load()
    idx = build_index(dl, tr)
    tot, cont, exp = build_finance(tr)
    bad = verify(idx)
    print("index.csv         %3d rows (%d county-office filings, %d school-board files)" % (
        len(idx), sum(1 for r in idx if r["tier"] == "county_office"),
        sum(1 for r in idx if r["tier"] == "school_board")))
    print("filing_totals.csv %3d county-office filings (%d with itemized rows transcribed)" % (
        len(tot), sum(1 for r in tot if r["n_contrib_rows"] or r["n_expend_rows"])))
    print("contributions.csv %3d rows" % len(cont))
    print("expenditures.csv  %3d rows" % len(exp))
    print("byte verification: %s" % ("OK — all sha256 match" if not bad else "FAILED %r" % bad))
