#!/usr/bin/env python3
"""
Build Kearns packets/index.csv (SCHEMA_SPEC §9 packets contract) from the crawl
+ fetch artifacts. Idempotent — safe to re-run after text extraction to pick up
the real format/extraction_method per file.

Inputs (all in this dir):
  _sized_keep.csv         one row per fetchable packet (event_date, body_label,
                          file_id, ext, filename, class, content_length, relpath)
  raw/_fetch_log.jsonl    polite_fetch provenance (ok, bytes, sha256, retrieved_utc)
  text/_extraction_log.csv (optional) pdftotext outcome per stem

Output: index.csv with the §9 header, extras appended:
  date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
  extraction_method,path,pmn_body_id,pmn_file_id,size_mb,stored_locally

Only STORED (fetched-ok) rows are written here. The 41 purged (404) pre-2018-12
packets are recorded in unrecovered.csv, not index.csv.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_fetchlog():
    """map source_url -> record (last write wins)."""
    log = {}
    p = os.path.join(HERE, "raw", "_fetch_log.jsonl")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            log[r["url"]] = r
    return log


def load_extraction():
    """map stem -> status."""
    ext = {}
    p = os.path.join(HERE, "text", "_extraction_log.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            ext[r["stem"]] = r["status"]
    return ext


def meeting_type(fname):
    n = fname.lower()
    if "special" in n:
        return "special"
    if "cra" in n:
        return "regular"  # CRA is a body, cadence regular
    return "regular"


def body_of(row):
    n = row["filename"].lower()
    if row["body_label"] == "PC":
        return "PC"
    if "cra" in n:
        return "CRA"
    return "Council"


def packet_kind(cls):
    return {"PACKET": "full_packet", "STAFF_REPORT": "staff_report"}.get(cls, "full_packet")


def main():
    keep = list(csv.DictReader(open(os.path.join(HERE, "_sized_keep.csv"))))
    log = load_fetchlog()
    ext = load_extraction()

    HEADER = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
              "retrieved_date", "format", "extraction_method", "path",
              "pmn_body_id", "pmn_file_id", "size_mb", "stored_locally"]
    out = []
    for r in keep:
        url = f"https://www.utah.gov/pmn/files/{r['file_id']}.{r['ext']}"
        rec = log.get(url)
        if not rec or not rec.get("ok"):
            continue  # only stored rows in index.csv
        rel = r["relpath"]
        stem = os.path.splitext(os.path.basename(rel))[0]
        status = ext.get(stem)
        if status in ("extracted", "skipped-exists"):
            fmt, method = "text", "pdftotext -layout"
        elif status == "image_only":
            fmt, method = "scanned", "none (image-only PDF; vision/OCR required)"
        elif status == "too_big":
            fmt, method = "scanned", "none (>120MB bundle; not text-extracted)"
        else:  # not yet extracted
            fmt, method = "", ""
        retrieved = (rec.get("retrieved_utc") or "2026-07-13")[:10]
        out.append({
            "date": r["event_date"],
            "title": r["filename"].strip(),
            "body": body_of(r),
            "meeting_type": meeting_type(r["filename"]),
            "packet_kind": packet_kind(r["class"]),
            "source_url": url,
            "retrieved_date": retrieved,
            "format": fmt,
            "extraction_method": method,
            "path": f"raw/{rel}",
            "pmn_body_id": r["pmn_body_id"],
            "pmn_file_id": r["file_id"],
            "size_mb": r.get("size_mb", ""),
            "stored_locally": "yes",
        })
    out.sort(key=lambda x: (x["body"], x["date"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(out)
    print(f"index.csv: {len(out)} rows "
          f"(Council={sum(1 for r in out if r['body']=='Council')}, "
          f"CRA={sum(1 for r in out if r['body']=='CRA')}, "
          f"PC={sum(1 for r in out if r['body']=='PC')})")


if __name__ == "__main__":
    main()
