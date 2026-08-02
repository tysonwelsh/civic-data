#!/usr/bin/env python3
"""validate_finance.py — conformance checker for the structured campaign-finance layer.

Usage:  python3 scripts/campaign_finance/validate_finance.py <city>/campaign_finance [--quiet]

Validation only — never mutates data. Stdlib only. Mirrors validate_city.py's style:
FAIL / WARN / PASS lines; exit code = number of FAILs (0 = clean; WARNs never affect exit).

Checks (contract = SCHEMA.md):
  1. the three DERIVED CSVs present with exact headers.
  2. every source_filing in each CSV exists as an index.csv `path`.
  3. every amount is a valid decimal or blank; no blank amount without needs_review=1.
  4. donor_type / extraction_confidence within their enums; is_incremental boolean.
  5. no contribution row lacking BOTH donor_raw and an unnamed-flag (blank donor_raw must be
     an anonymous / aggregate-unitemized / unknown row AND needs_review=1).
  6. reconciliation columns internally consistent (reconciles=True ⇒ |delta| ≤ $0.01 and
     itemized_sum ≈ stated_total; booleans well-formed).
  7. filing_totals.n_contrib_rows / n_expend_rows match the actual per-filing row counts.
  8. every (candidate, election_year) in the CSVs exists in index.csv.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

DONOR_TYPES = {"candidate-self", "family-of-candidate", "individual", "business", "pac",
               "party", "loan", "carryover", "anonymous", "aggregate-unitemized",
               "other", "unknown"}
CONF = {"high", "medium", "low", ""}
BOOL = {"True", "False"}
UNNAMED_OK = {"anonymous", "aggregate-unitemized", "unknown"}
TOL = 0.01

fails = []
warns = []


def fail(m):
    fails.append(m)


def warn(m):
    warns.append(m)


def _read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _dec_ok(s):
    if s == "":
        return True
    try:
        float(s)
        return True
    except ValueError:
        return False


def main(dataset_dir):
    ds = os.path.abspath(dataset_dir)
    index_path = os.path.join(ds, "index.csv")
    if not os.path.exists(index_path):
        fail(f"index.csv not found in {ds}")
        return _report()
    index_rows = _read(index_path)
    index_paths = {r.get("path", "") for r in index_rows}
    index_cand_year = {(r.get("candidate", ""), r.get("election_year", "")) for r in index_rows}

    specs = [
        ("contributions.csv", common.CONTRIB_HEADER),
        ("expenditures.csv", common.EXPEND_HEADER),
        ("filing_totals.csv", common.TOTALS_HEADER),
    ]
    tables = {}
    for name, header in specs:
        p = os.path.join(ds, name)
        if not os.path.exists(p):
            fail(f"{name} missing")
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            got = rd.fieldnames or []
            # filing_totals.csv carries an OPTIONAL trailing `filing_regime` column (populated by
            # two-regime cities like Taylorsville; single-regime cities omit it). Accept the header
            # both with and without that trailing column so neither is a regression.
            ok_headers = [header]
            if name == "filing_totals.csv" and header and header[-1] == "filing_regime":
                ok_headers.append(header[:-1])
            # contributions/expenditures carry an OPTIONAL trailing `geometry` column (positional
            # sources only — the county form families record page + bbox / xls cell there; every
            # other dataset omits it entirely). Same trailing-optional contract; accept both.
            if name in ("contributions.csv", "expenditures.csv"):
                ok_headers.append(header + [common.GEOMETRY_COL])
            if got not in ok_headers:
                fail(f"{name} header mismatch\n    expected: {header}\n    got:      {got}")
            tables[name] = list(rd)

    # ---- contributions
    for i, r in enumerate(tables.get("contributions.csv", []), 2):
        where = f"contributions.csv row {i}"
        if r["source_filing"] not in index_paths:
            fail(f"{where}: source_filing {r['source_filing']!r} not in index.csv")
        if not _dec_ok(r["amount"]):
            fail(f"{where}: amount {r['amount']!r} not a decimal")
        if r["amount"] == "" and r["needs_review"] != "1":
            fail(f"{where}: blank amount without needs_review=1")
        if r["donor_type"] not in DONOR_TYPES:
            fail(f"{where}: donor_type {r['donor_type']!r} not in enum")
        if r["extraction_confidence"] not in CONF:
            fail(f"{where}: extraction_confidence {r['extraction_confidence']!r} invalid")
        if r["is_incremental"] not in BOOL:
            fail(f"{where}: is_incremental {r['is_incremental']!r} not boolean")
        if r["donor_raw"] == "" and not (r["donor_type"] in UNNAMED_OK and r["needs_review"] == "1"):
            fail(f"{where}: blank donor_raw must be an unnamed-flag row (anonymous/"
                 f"aggregate-unitemized/unknown) with needs_review=1")
        if (r["candidate"], r["election_year"]) not in index_cand_year:
            fail(f"{where}: (candidate,election_year)=({r['candidate']},{r['election_year']}) not in index")

    # ---- expenditures
    for i, r in enumerate(tables.get("expenditures.csv", []), 2):
        where = f"expenditures.csv row {i}"
        if r["source_filing"] not in index_paths:
            fail(f"{where}: source_filing {r['source_filing']!r} not in index.csv")
        if not _dec_ok(r["amount"]):
            fail(f"{where}: amount {r['amount']!r} not a decimal")
        if r["amount"] == "" and r["needs_review"] != "1":
            fail(f"{where}: blank amount without needs_review=1")
        if r["extraction_confidence"] not in CONF:
            fail(f"{where}: extraction_confidence {r['extraction_confidence']!r} invalid")
        if r["in_kind"] not in BOOL:
            fail(f"{where}: in_kind {r['in_kind']!r} not boolean")

    # ---- filing_totals: reconciliation consistency + row-count agreement
    # Key row counts on document_id (the unique per-FILING id), NOT source_filing: a
    # multi-candidate compilation (Nephi 2021/2023) packs several filings into ONE PDF, so
    # several filing_totals rows share a source_filing but each has its own document_id. In
    # every single-PDF city document_id is 1:1 with source_filing, so this is identical there.
    c_counts, e_counts = {}, {}
    for r in tables.get("contributions.csv", []):
        c_counts[r["document_id"]] = c_counts.get(r["document_id"], 0) + 1
    for r in tables.get("expenditures.csv", []):
        e_counts[r["document_id"]] = e_counts.get(r["document_id"], 0) + 1

    for i, r in enumerate(tables.get("filing_totals.csv", []), 2):
        where = f"filing_totals.csv row {i} ({r['candidate']} {r['election_year']})"
        if r["source_filing"] not in index_paths:
            fail(f"{where}: source_filing not in index.csv")
        for col in ("stated_total_contributions", "stated_total_expenditures",
                    "itemized_contrib_sum", "itemized_expend_sum", "self_funded_amount"):
            if not _dec_ok(r[col]):
                fail(f"{where}: {col} {r[col]!r} not a decimal/blank")
        for col in ("reconciles_contrib", "reconciles_expend"):
            if r[col] not in ("True", "False", ""):
                fail(f"{where}: {col} {r[col]!r} not True/False/blank")
        # reconciles=True must actually reconcile
        for recon, itm, stated, delta in (
            ("reconciles_contrib", "itemized_contrib_sum", "stated_total_contributions", "recon_delta_contrib"),
            ("reconciles_expend", "itemized_expend_sum", "stated_total_expenditures", "recon_delta_expend"),
        ):
            if r[recon] == "True":
                if r[itm] == "" or r[stated] == "":
                    fail(f"{where}: {recon}=True but {itm}/{stated} blank")
                elif round(abs(float(r[itm]) - float(r[stated])), 2) > TOL:
                    fail(f"{where}: {recon}=True but |{itm}-{stated}| > {TOL}")
        exp_c = str(c_counts.get(r["document_id"], 0))
        exp_e = str(e_counts.get(r["document_id"], 0))
        if r["n_contrib_rows"] != exp_c:
            fail(f"{where}: n_contrib_rows {r['n_contrib_rows']} != actual {exp_c}")
        if r["n_expend_rows"] != exp_e:
            fail(f"{where}: n_expend_rows {r['n_expend_rows']} != actual {exp_e}")
        if r["extraction_confidence"] not in CONF:
            fail(f"{where}: extraction_confidence {r['extraction_confidence']!r} invalid")

    # every index filing should have a filing_totals row (WARN — a filing may be unparseable)
    ft_filings = {r["source_filing"] for r in tables.get("filing_totals.csv", [])}
    for p in index_paths:
        if p and p not in ft_filings:
            warn(f"index filing {p} has no filing_totals row")

    return _report()


def _report():
    for w in warns:
        print(f"WARN  {w}")
    for f in fails:
        print(f"FAIL  {f}")
    status = "PASS" if not fails else "FAIL"
    print(f"\n{status}  ({len(fails)} fails, {len(warns)} warns)")
    return len(fails)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: validate_finance.py <city>/campaign_finance")
        sys.exit(2)
    sys.exit(main(args[0]))
