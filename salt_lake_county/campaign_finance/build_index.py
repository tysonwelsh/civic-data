#!/usr/bin/env python3
"""Regenerate index.csv from the THREE acquisition channels' fetch logs. One row per acquired
filing. sha256 + format are read from the files on disk (never trusted from the log alone).
Also detects text/ sidecar presence.

Channels:
  clerk_legacy  - legacy per-candidate PDFs, slco.org/clerk/financialDisclosurePDF/ (~2004-2015)
  easyvote      - county EasyVote portal redacted PDFs (2022-2026)
  globalassets  - 2015-2021 paper-filed county PDFs on the county CMS (harvested 2026-08-20)

THE globalassets CHANNEL IS DOCUMENT-DERIVED, NOT LOG-DERIVED.
In that era every filename-level signal LIES: folder years put 2018 documents in a
`2016_disclosures/` folder, a `2014ye` filename holds a 2015 year-end, form-title years are
stock reuse (8 cases), and the clerk's own listing labels disagree with the form on 26 of 130
filings (one anchor points at the wrong document entirely). So `candidate`, `date`, `office`,
`seat`, `filing_type` and `reporting_period` come from EACH DOCUMENT'S OWN COVER, as recorded
per filing -- with the basis of every field -- in
`_audits/2026-08-20-globalassets-harvest/characterisation.csv`. That file is the provenance
record for this channel and the only authority this builder will accept for those fields:
a PDF with no characterisation row is an UNREAD document, and an unread document is an honest
gap -- it is reported and SKIPPED, never indexed off its filename.

`filing_type` is not stored-and-copied: it is DERIVED here from the verbatim checked
Type-of-Report box label(s) via `build_lib.filing_type_from_report_boxes`, using the form's own
three printed headings (INTERIM REPORTS / YEAR-END REPORT / FINAL / DISSOLUTION REPORT) as the
vocabulary. The derivation is then cross-checked against the recorded `index_filing_type` and
the build HARD-FAILS on any disagreement, so neither the rule nor the record can drift alone,
and an unrecognised box label raises instead of being silently classed.

Row ORDER: the two log-derived channels are sorted (source, election_year, candidate, path);
the globalassets block keeps its fetch-log order, which is the clerk listing's own anchor
order and is stable on disk.
"""
import json, os, csv, hashlib, subprocess, re, sys
import build_lib as BL

HERE = os.path.dirname(os.path.abspath(__file__))

COLS = ["date", "candidate", "office", "seat", "election_year", "filing_type",
        "reporting_period", "title", "source_url", "retrieved_date", "format",
        "extraction_method", "path", "source", "document_id", "sha256", "filer_type",
        "has_text", "has_itemized"]

CHAR_CSV = os.path.join("_audits", "2026-08-20-globalassets-harvest", "characterisation.csv")


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def pdf_has_text(p):
    """True if the PDF has an embedded font layer (born-digital), else image-only scan."""
    try:
        out = subprocess.run(["pdffonts", p], capture_output=True, text=True, timeout=30).stdout
        lines = [l for l in out.splitlines()[2:] if l.strip()]
        return len(lines) > 0
    except Exception:
        return False


def itemized_document_ids():
    """EasyVote document ids whose filing ACTUALLY CARRIES ITEMIZED ROWS.

    NOT "has a filing_totals row" -- that is a different question and answering it here was a
    live defect: filing_totals also holds 670 vision STATED-TOTALS rows with no itemized side,
    so membership alone would have marked 97 row-less 2022 filings has_itemized='yes'. Those
    filings are the audited row-less residue (_audits/2026-08-20-easyvote-residue/), i.e. the
    detail is in the PDF and UNTRANSCRIBED -- claiming itemization for them would be a
    fabrication. The test is the filing's own itemized row counts.
    """
    ids, ftp = set(), os.path.join(HERE, "filing_totals.csv")
    if not os.path.exists(ftp):
        return ids
    for r in csv.DictReader(open(ftp)):
        did = (r.get("document_id") or "").upper()
        if not did:
            continue
        n = 0
        for k in ("n_contrib_rows", "n_expend_rows"):
            try:
                n += int(r.get(k) or 0)
            except ValueError:
                pass
        if n > 0:
            ids.add(did)
    return ids


def itemized_paths():
    """Filing paths that appear as source_filing in the itemized CSVs (any channel)."""
    out = set()
    for name in ("contributions.csv", "expenditures.csv"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                sf = (r.get("source_filing") or "").strip()
                if sf:
                    out.add(sf)
    return out


def main():
    warnings = []
    itemized_ids = itemized_document_ids()
    item_paths = itemized_paths()
    logged = []          # clerk_legacy + easyvote (sorted)
    ga_rows = []         # globalassets (fetch-log order)

    # ---- clerk_legacy ----
    legacy_log = os.path.join(HERE, "raw", "clerk_legacy", "_fetch_log.jsonl")
    n_legacy_itemized = 0
    if os.path.exists(legacy_log):
        for line in open(legacy_log):
            r = json.loads(line)
            if r.get("error"):
                continue
            path = r["path"]
            ap = os.path.join(HERE, path)
            if not os.path.exists(ap):
                continue
            office, seat = BL.normalize_office(r.get("office"))
            # year: from URL folder or filename digits
            yr = None
            m = re.search(r"/(20\d\d)", r["url"]) or re.search(r"(20\d\d)", os.path.basename(r["url"]))
            if m:
                yr = m.group(1)
            has_text = pdf_has_text(ap)
            txtname = "clerk_legacy__" + os.path.basename(path).replace(".pdf", ".txt")
            if path in item_paths:
                n_legacy_itemized += 1
            logged.append({
                "date": (yr + "-01-01") if yr else "",
                "candidate": r.get("candidate", ""), "office": office, "seat": seat,
                "election_year": (yr if yr and int(yr) % 2 == 0 else (str(int(yr) - 1) if yr else "")),
                "filing_type": "statement",
                "reporting_period": r.get("group", "") + (" / " if r.get("group") and r.get("period_label") else "") + r.get("period_label", ""),
                "title": f"{r.get('candidate','')} ({r.get('office','')}) — {r.get('period_label','')}".strip(" —"),
                "source_url": r["url"], "retrieved_date": "2026-08-01",
                "format": "text" if has_text else "scanned",
                "extraction_method": "pdftotext -layout" if has_text else "tesseract OCR (pdftoppm 300dpi)",
                "path": path, "source": "clerk_legacy", "document_id": "",
                "sha256": sha256_of(ap), "filer_type": "",
                "has_text": "yes" if os.path.exists(os.path.join(HERE, "text", txtname)) else "no",
                # PINNED literal, deliberately NOT the itemization test. `has_itemized` is
                # documented (CLAUDE.md) as an EasyVote-channel acquisition-time flag; the
                # clerk-legacy era's itemization lives in the vision caches and in
                # contributions.csv/expenditures.csv `source_filing`. See the WARN below.
                "has_itemized": "no",
            })

    # ---- easyvote ----
    ev_log = os.path.join(HERE, "raw", "easyvote", "_fetch_log.jsonl")
    if os.path.exists(ev_log):
        for line in open(ev_log):
            r = json.loads(line)
            if r.get("error"):
                continue
            path = r["path"]
            ap = os.path.join(HERE, path)
            if not os.path.exists(ap):
                continue
            office, seat = BL.normalize_office(r.get("officename"))
            fdate = BL.easyvote_iso(r.get("datesubmitted"))
            eyear = BL.election_year_from_date(fdate)
            did = (r.get("documentid") or "")
            has_text = pdf_has_text(ap)
            txtname = "easyvote__" + os.path.basename(path).replace(".pdf", ".txt")
            logged.append({
                "date": fdate, "candidate": r.get("displayname", ""), "office": office,
                "seat": seat, "election_year": eyear, "filing_type": "interim",
                "reporting_period": r.get("documentname") or "",
                "title": f"{r.get('displayname','')} ({r.get('officename','')}) — {r.get('documentname') or ''}".strip(" —"),
                "source_url": f"https://ecf-api.easyvoteapp.com/documents/{did}/viewfinalredactedpdf",
                "retrieved_date": "2026-08-01",
                "format": "text" if has_text else "scanned",
                "extraction_method": "pdftotext -layout" if has_text else "tesseract OCR (pdftoppm 300dpi)",
                "path": path, "source": "easyvote", "document_id": did,
                "sha256": sha256_of(ap), "filer_type": r.get("filertype", ""),
                "has_text": "yes" if os.path.exists(os.path.join(HERE, "text", txtname)) else "no",
                "has_itemized": "yes" if did.upper() in itemized_ids else "no",
            })

    # ---- globalassets (2015-2021 paper-filed county PDFs, harvested 2026-08-20) ----
    ga_log = os.path.join(HERE, "raw", "globalassets", "_fetch_log.jsonl")
    ga_char = os.path.join(HERE, CHAR_CSV)
    if os.path.exists(ga_log):
        if not os.path.exists(ga_char):
            sys.exit(f"FATAL: {CHAR_CSV} is missing. The globalassets channel's index fields "
                     "are DOCUMENT-derived and cannot be reconstructed from the fetch log "
                     "(folder years, filenames and listing labels all lie in this era). "
                     "Refusing to write an index that would silently drop the channel.")
        char, seen = {}, set()
        with open(ga_char) as fh:
            for c in csv.DictReader(fh):
                char[c["path"]] = c
        for line in open(ga_log):
            r = json.loads(line)
            path = r["path"]
            # `fetch_error` in this log records the FIRST attempt; 4 records carry an
            # "HTTP Error 525" note yet completed on the retry (http_status 200, non-empty
            # body, sha256 matched). The delivery test is the outcome, not the note.
            if r.get("error") or r.get("http_status") != 200 or not r.get("bytes"):
                warnings.append(
                    f"globalassets: fetch did not deliver a body (status={r.get('http_status')} "
                    f"bytes={r.get('bytes')}), SKIPPED — {path}")
                continue
            ap = os.path.join(HERE, path)
            if not os.path.exists(ap):
                warnings.append(f"globalassets: logged PDF missing on disk, SKIPPED — {path}")
                continue
            c = char.get(path)
            if c is None:
                # An unread document is an honest gap. Never invent a row for it: every
                # filename-level signal in this era is known to lie, so indexing off the
                # filename would fabricate the candidate, date, office and period.
                warnings.append(
                    f"globalassets: NO characterisation row — document unread, SKIPPED (honest "
                    f"gap; characterise it into {CHAR_CSV} to index it) — {path}")
                continue
            seen.add(path)
            # filing_type: derived from the form's own checked box, then gated against the
            # recorded read. Disagreement is a hard failure, never a silent pick.
            boxes = c.get("doc_report_type_boxes", "")
            try:
                ftype = BL.filing_type_from_report_boxes(boxes)
            except ValueError as e:
                sys.exit(f"FATAL: {path}: {e}")
            if ftype != (c.get("index_filing_type") or ""):
                sys.exit(f"FATAL: {path}: filing_type derived from the checked box "
                         f"({ftype!r}) disagrees with the recorded index_filing_type "
                         f"({c.get('index_filing_type')!r}). Resolve at the DOCUMENT.")
            digest = sha256_of(ap)
            if r.get("sha256") and r["sha256"] != digest:
                warnings.append(f"globalassets: on-disk sha256 differs from the fetch log "
                                f"(disk value indexed) — {path}")
            has_text = pdf_has_text(ap)
            txtname = "globalassets__" + os.path.basename(path).replace(".pdf", ".txt")
            ga_rows.append({
                # --- document-derived (characterisation.csv is the authority) ---
                "date": c.get("index_date", ""),
                "candidate": c.get("index_candidate", ""),
                "office": c.get("index_office", ""),
                "seat": c.get("index_seat", ""),
                "election_year": BL.election_year_from_date(c.get("index_date", "")),
                "filing_type": ftype,
                # the form's OWN checked Type-of-Report label, verbatim. The clerk listing's
                # label is kept in `title` so the two sit side by side in index.csv - they
                # disagree on 26 of 130 filings and the form governs.
                "reporting_period": boxes,
                # --- clerk-listing-derived (the fetch log carries the listing's own strings) ---
                "title": f"{r.get('candidate','')} ({r.get('office','')}) — {r.get('listing_label','')}".strip(" —"),
                # --- acquisition provenance ---
                "source_url": r["url"],
                "retrieved_date": (r.get("retrieved_utc") or "")[:10],
                "format": "text" if has_text else "scanned",
                "extraction_method": "pdftotext -layout" if has_text else "tesseract OCR (pdftoppm 300dpi)",
                "path": path, "source": "globalassets", "document_id": "",
                "sha256": digest, "filer_type": "",
                "has_text": "yes" if os.path.exists(os.path.join(HERE, "text", txtname)) else "no",
                # no itemized layer for this channel yet; the honest test, not a literal.
                "has_itemized": "yes" if path in item_paths else "no",
            })
        for p in sorted(set(char) - seen):
            warnings.append(f"globalassets: characterisation row with no fetched PDF — {p}")

    logged.sort(key=lambda x: (x["source"], x["election_year"], x["candidate"], x["path"]))
    rows = logged + ga_rows
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    import collections
    print(f"index.csv rows: {len(rows)}")
    print("by source:", dict(collections.Counter(r["source"] for r in rows)))
    print("by format:", dict(collections.Counter(r["format"] for r in rows)))
    print("has_itemized=yes:", sum(1 for r in rows if r["has_itemized"] == "yes"))
    if n_legacy_itemized:
        print(f"  NOTE clerk_legacy: {n_legacy_itemized} filings DO carry itemized rows "
              "(wave B2 vision) but keep has_itemized='no' — the column is documented as an "
              "EasyVote acquisition-time flag. Use the vision cache / source_filing instead.")
    for w_ in warnings:
        print("  WARN " + w_)
    print(f"warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
