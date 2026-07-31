#!/usr/bin/env python3
"""Copperton PMN backfill — write index.csv (SCHEMA_SPEC §9 pmn_backfill contract).

Copperton's PMN sweep yielded ZERO gap-fill minutes recoveries (the audited repo is a
complete superset of both PMN bodies 5831/1560 — see coverage.md). The one tangible new
artifact is a single OCR-UPGRADE LEAD: a born-digital PMN copy of a date the repo currently
holds only as a GoDaddy RICOH scan. It is cataloged here as a LEAD (recovery_source=
pmn_ocr_upgrade_lead), NOT a gap-fill — the date already exists in meeting_minutes/ and is
NOT swapped. Header = §9 contract prefix + extras (recovery_source, orig_filename, text_path),
matching magna_city_council/pmn_backfill/index.csv.

Run: python3 copperton_pmn_buildindex.py  (idempotent; reads raw/_fetch_log.jsonl for the
retrieved_utc date; writes index.csv in this dir).
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER = ["date", "year", "title", "slug", "body", "path", "source", "source_url",
          "notice_url", "pmn_body_id", "pmn_file_id", "retrieved_date", "format",
          "extraction_method", "recovery_source", "orig_filename", "text_path"]

# The single OCR-upgrade lead (2025-10-15 council DRAFT; PMN file 1353103; born-digital,
# 16,436 chars; attached to the 2025-11-19 approval notice 1038579 on body 5831).
LEAD = {
    "date": "2025-10-15",
    "year": "2025",
    "title": ("Copperton Town Council Meeting DRAFT minutes — PMN born-digital copy; "
              "OCR-UPGRADE LEAD for the repo's approved GoDaddy RICOH scan of 2025-10-15 "
              "(NOT a gap-fill: the date is already in meeting_minutes/ as format=ocr; "
              "cataloged as a clean-text lead, not swapped)"),
    "slug": "2025-10-15-council-ocr-upgrade-lead",
    "body": "Council",
    "path": "raw/2025-10-15__council__1353103__pmn-borndigital-ocr-upgrade-lead.pdf",
    "source": "pmn",
    "source_url": "https://www.utah.gov/pmn/files/1353103.pdf",
    "notice_url": "https://www.utah.gov/pmn/sitemap/notice/1038579.html",
    "pmn_body_id": "5831",
    "pmn_file_id": "1353103",
    "retrieved_date": "",  # filled from fetch log below
    "format": "text",
    "extraction_method": "pdftotext-layout",
    "recovery_source": "pmn_ocr_upgrade_lead",
    "orig_filename": "10-15-2025 Copperton Meeting Minutes - DRAFT.pdf",
    "text_path": "text/2025-10-15__council__1353103__pmn-borndigital-ocr-upgrade-lead.txt",
}


def retrieved_date_for(file_id):
    log = os.path.join(HERE, "raw", "_fetch_log.jsonl")
    if os.path.exists(log):
        with open(log) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if f"/{file_id}." in (rec.get("url") or ""):
                    return (rec.get("retrieved_utc") or "")[:10]
    return "2026-07-14"


def main():
    LEAD["retrieved_date"] = retrieved_date_for(LEAD["pmn_file_id"])
    out = os.path.join(HERE, "index.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerow(LEAD)
    print(f"wrote {out} (1 OCR-upgrade lead row; 0 gap-fill recoveries)")


if __name__ == "__main__":
    main()
