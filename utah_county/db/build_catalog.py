#!/usr/bin/env python3
"""Rebuild legislative/minutes/_catalog.csv + legislative/minutes_index.csv directly from the
on-disk minutes markdown front-matter.

fetch_legislative.py writes these indexes at the END of a full run, but the harvest's genuine
404 gaps (mislabeled archive rows, unpublished dates) trigger slow retry backoff that makes a
clean end-of-run index costly. Since every harvested markdown already carries a provenance
front-matter block (body/date/extraction/source_url/meeting_kind), this derives the two index
files by scanning the tree — instant, and it reflects exactly what was fetched (missing dates
are honestly absent, not invented).

DERIVED + idempotent.
"""
import csv, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
MDIR = os.path.join(COUNTY, "legislative", "minutes")


def fm_get(head, key, default=""):
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), head, re.M)
    return m.group(1).strip() if m else default


def main():
    idx = []; cat = []
    for path in glob.glob(os.path.join(MDIR, "20*", "*.md")):
        head = open(path, encoding="utf-8").read(1200)
        date = fm_get(head, "date"); body = fm_get(head, "body")
        extraction = fm_get(head, "extraction")
        prov = "ocr_scan" if "OCR" in extraction else "minutes"
        kind = "special" if fm_get(head, "meeting_kind") == "special" else ""
        src = fm_get(head, "source_url").split(" | ")[0]
        rel = os.path.relpath(path, COUNTY)
        idx.append([date, body, rel, src, "Final", kind])
        cat.append([date, body, rel, prov, kind, src])
    idx.sort(key=lambda r: (r[0], r[1])); cat.sort(key=lambda r: (r[0], r[1]))
    with open(os.path.join(COUNTY, "legislative", "minutes_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "source_url", "minutes_status", "note"]); w.writerows(idx)
    with open(os.path.join(MDIR, "_catalog.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "provenance", "kind", "source_url"]); w.writerows(cat)
    born = sum(1 for r in cat if r[3] == "minutes"); ocr = sum(1 for r in cat if r[3] == "ocr_scan")
    print("catalog rebuilt from disk: %d minutes docs (born-digital=%d, OCR=%d)" % (len(cat), born, ocr))


if __name__ == "__main__":
    main()
