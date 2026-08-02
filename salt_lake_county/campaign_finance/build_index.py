#!/usr/bin/env python3
"""Regenerate index.csv from the two fetch logs (raw/clerk_legacy + raw/easyvote) plus the
EasyVote documentsearch metadata. One row per acquired filing. sha256 + format are read from
the files on disk (never trusted from the log alone). Also detects text/ sidecar presence.

Channels:
  clerk_legacy  — legacy per-candidate PDFs, slco.org/clerk/financialDisclosurePDF/ (~2004-2015)
  easyvote      — county EasyVote portal redacted PDFs (2022-2026)
"""
import json, os, csv, hashlib, subprocess, re
import build_lib as BL

HERE = os.path.dirname(os.path.abspath(__file__))

COLS = ["date", "candidate", "office", "seat", "election_year", "filing_type",
        "reporting_period", "title", "source_url", "retrieved_date", "format",
        "extraction_method", "path", "source", "document_id", "sha256", "filer_type",
        "has_text", "has_itemized"]


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


def main():
    rows = []
    # itemized filing ids (county) -> from filing_totals if present
    itemized_ids = set()
    ftp = os.path.join(HERE, "filing_totals.csv")
    if os.path.exists(ftp):
        for r in csv.DictReader(open(ftp)):
            itemized_ids.add(r["document_id"].upper())

    # ---- clerk_legacy ----
    legacy_log = os.path.join(HERE, "raw", "clerk_legacy", "_fetch_log.jsonl")
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
            rows.append({
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
            rows.append({
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

    rows.sort(key=lambda x: (x["source"], x["election_year"], x["candidate"], x["path"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    import collections
    print(f"index.csv rows: {len(rows)}")
    print("by source:", dict(collections.Counter(r["source"] for r in rows)))
    print("by format:", dict(collections.Counter(r["format"] for r in rows)))
    print("has_itemized=yes:", sum(1 for r in rows if r["has_itemized"] == "yes"))


if __name__ == "__main__":
    main()
