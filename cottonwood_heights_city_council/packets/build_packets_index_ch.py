#!/usr/bin/env python3
"""Build Cottonwood Heights packets/index.csv (SCHEMA_SPEC §9 contract).

Contract header (exact, in order):
  date,title,body,meeting_type,packet_kind,source_url,retrieved_date,
  format,extraction_method,path
Extras (after contract): size_mb,stored_locally,docid

Run AFTER fetch. format/extraction_method are refined from
text/_extraction_log.csv if present (call --patch after extraction).
"""
import json, csv, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-13"
HEADER = ["date", "title", "body", "meeting_type", "packet_kind",
          "source_url", "retrieved_date", "format", "extraction_method",
          "path", "size_mb", "stored_locally", "docid"]

def load_extraction_log():
    """stem -> (status, chars)"""
    log = os.path.join(BASE, "text", "_extraction_log.csv")
    out = {}
    if os.path.exists(log):
        for r in csv.DictReader(open(log)):
            out[r["stem"]] = (r["status"], int(r.get("chars") or 0))
    return out

def clean_title(body, date, meeting_type):
    # Human title keyed to body + date; verbatim landing text is noisy, so a
    # normalized, faithful title is used.
    d = date
    if body == "Council":
        return f"{d} Council Work Session and Business Meeting — Agenda Packet"
    if meeting_type == "admin_hearing":
        return f"{d} Planning Commission Administrative Hearing — Agenda Packet"
    return f"{d} Planning Commission — Agenda Packet"

def main():
    manifest = json.load(open("/tmp/ch_manifest.json"))
    exlog = load_extraction_log()
    rows = []
    for m in manifest:
        rel = f"raw/{m['date']}/{m['filename']}"
        disk = os.path.join(BASE, rel)
        size_mb = round(os.path.getsize(disk) / 1e6, 2) if os.path.exists(disk) else ""
        stem = os.path.splitext(m["filename"])[0]
        status, chars = exlog.get(stem, (None, 0))
        if status == "extracted":
            fmt, em = "text", "pdftotext-layout"
        elif status in ("image_only", "too_big"):
            fmt, em = "scanned", "none (image-only bundle; vision/OCR required)"
        else:
            # pre-extraction default: born-digital council/PC packets
            fmt, em = "text", "pdftotext-layout"
        body = "PlanningCommission" if m["body"] == "PC" else m["body"]
        rows.append({
            "date": m["date"],
            "title": clean_title(m["body"], m["date"], m["meeting_type"]),
            "body": body,
            "meeting_type": m["meeting_type"],
            "packet_kind": m["packet_kind"],
            "source_url": m["url"],
            "retrieved_date": RETRIEVED,
            "format": fmt,
            "extraction_method": em,
            "path": rel,
            "size_mb": size_mb,
            "stored_locally": "yes",
            "docid": m["docid"],
        })
    rows.sort(key=lambda r: (r["date"], r["body"], r["meeting_type"]))
    with open(os.path.join(BASE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "rows to index.csv")

if __name__ == "__main__":
    main()
