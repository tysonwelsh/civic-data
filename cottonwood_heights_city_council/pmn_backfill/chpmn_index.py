#!/usr/bin/env python3
"""Emit index.csv for the Cottonwood Heights pmn_backfill dataset from _work/recover_manifest.csv.
§9 pmn_backfill contract header + one extra column (orig_filename)."""
import csv, os

HERE = os.path.dirname(__file__)
RET = "2026-07-13"
HDR = ["date", "year", "title", "slug", "body", "path", "source", "source_url",
       "notice_url", "pmn_body_id", "pmn_file_id", "retrieved_date", "format",
       "extraction_method", "orig_filename"]

def main():
    man = list(csv.DictReader(open(os.path.join(HERE, "_work/recover_manifest.csv"))))
    out = os.path.join(HERE, "index.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader()
        for r in sorted(man, key=lambda x: (x["mdate"], x["slug"], x["file_id"])):
            d = r["mdate"]; fid = r["file_id"]
            name = f"{d}__{r['slug']}__{fid}.pdf"
            assert os.path.exists(os.path.join(HERE, "raw", name)), name
            w.writerow({
                "date": d, "year": d[:4],
                "title": f"Planning Commission — {r['filename']}",
                "slug": r["slug"], "body": r["outbody"],
                "path": f"raw/{name}", "source": "pmn",
                "source_url": f"https://www.utah.gov/pmn/files/{fid}.pdf",
                "notice_url": f"https://www.utah.gov/pmn/sitemap/notice/{r['notice_id']}.html",
                "pmn_body_id": r["body"], "pmn_file_id": fid,
                "retrieved_date": RET, "format": "text",
                "extraction_method": "pdftotext-layout",
                "orig_filename": r["filename"],
            })
    print("wrote", out, "rows:", len(man))

if __name__ == "__main__":
    main()
