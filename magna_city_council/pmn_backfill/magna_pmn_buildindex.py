#!/usr/bin/env python3
"""Build pmn_backfill/index.csv (SCHEMA_SPEC §9 pmn_backfill contract + extras).

Recovered set is hard-coded (the 13 verified recoveries); notice_id + orig_filename
are pulled from work/parsed_<body>.json by file_id so provenance is machine-derived.
"""
import csv, json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
RETRIEVED = "2026-07-14"

# (date, body, slug, pmn_body_id, file_id, format, extraction_method, title)
REC = [
    ("2024-02-13", "Council", "council-regular", "5803", "1156839", "scanned", "tesseract-ocr", "Magna Council Meeting"),
    ("2024-02-27", "Council", "council-regular", "5803", "1167191", "scanned", "tesseract-ocr", "Magna Council Meeting"),
    ("2024-11-26", "Council", "council-regular", "5803", "1295979", "text",    "pdftotext-layout", "Magna Council Meeting"),
    ("2026-03-10", "Council", "council-regular", "5803", "1410601", "scanned", "tesseract-ocr", "Magna Council Meeting"),
    ("2026-06-09", "Council", "council-regular", "5803", "1461255", "scanned", "tesseract-ocr", "Magna Council Meeting"),
    ("2024-11-12", "CRA", "cra-regular", "6925", "1219871", "scanned", "tesseract-ocr", "Magna CRA Meeting"),
    ("2025-01-14", "CRA", "cra-regular", "6925", "1231905", "scanned", "tesseract-ocr", "Magna CRA Meeting"),
    ("2025-02-11", "CRA", "cra-regular", "6925", "1261647", "scanned", "tesseract-ocr", "Magna CRA Meeting"),
    ("2025-04-08", "CRA", "cra-regular", "6925", "1283597", "scanned", "tesseract-ocr", "Magna CRA Meeting"),
    ("2025-05-13", "CRA", "cra-regular", "6925", "1284171", "text",    "pdftotext-layout", "Magna CRA Meeting"),
    ("2025-06-10", "CRA", "cra-regular", "6925", "1295977", "text",    "pdftotext-layout", "Magna CRA Meeting"),
    ("2025-09-23", "CRA", "cra-regular", "6925", "1356251", "scanned", "tesseract-ocr", "Magna CRA Meeting"),
    ("2025-11-18", "CRA", "cra-regular", "6925", "1362717", "text",    "pdftotext-layout", "Magna CRA Meeting"),
]

def load_notice_map(body):
    m = {}
    for n in json.load(open(os.path.join(WORK, f"parsed_{body}.json"))):
        for a in n["attachments"]:
            m[a["file_id"]] = (n["notice_id"], a["filename"], a["ext"])
    return m

def main():
    maps = {b: load_notice_map(b) for b in ("5803", "6925")}
    header = ["date", "year", "title", "slug", "body", "path", "source", "source_url",
              "notice_url", "pmn_body_id", "pmn_file_id", "retrieved_date", "format",
              "extraction_method", "recovery_source", "orig_filename", "text_path"]
    rows = []
    for date, body, slug, bid, fid, fmt, meth, title in REC:
        notice_id, orig_fn, ext = maps[bid][fid]
        stem = f"{date}__{slug}__{fid}"
        # confirm the raw file exists
        raw_rel = f"raw/{stem}.{ext}"
        assert os.path.exists(os.path.join(HERE, raw_rel)), raw_rel
        rows.append({
            "date": date, "year": date[:4], "title": title, "slug": slug, "body": body,
            "path": raw_rel, "source": "pmn",
            "source_url": f"https://www.utah.gov/pmn/files/{fid}.pdf",
            "notice_url": f"https://www.utah.gov/pmn/sitemap/notice/{notice_id}.html",
            "pmn_body_id": bid, "pmn_file_id": fid, "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": meth, "recovery_source": "pmn",
            "orig_filename": orig_fn, "text_path": f"text/{stem}.txt",
        })
    rows.sort(key=lambda r: (r["body"], r["date"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote index.csv with {len(rows)} rows "
          f"({sum(1 for r in rows if r['body']=='Council')} Council, "
          f"{sum(1 for r in rows if r['body']=='CRA')} CRA)")

if __name__ == "__main__":
    main()
