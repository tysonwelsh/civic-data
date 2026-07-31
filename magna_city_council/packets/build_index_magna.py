#!/usr/bin/env python3
"""Assemble packets/index.csv (+ unrecovered.csv) from the catalog, sizes, fetch
manifest, and text-extraction log.

§9 packets contract header (SCHEMA_SPEC.md, exact, validator-enforced):
    date,title,body,meeting_type,packet_kind,source_url,retrieved_date,
    format,extraction_method,path
plus Magna extras (AFTER the contract cols):
    source,content_length_bytes,size_mb,stored_locally,pmn_notice_id,pmn_filename

STORED dataset (total live set 1.33 GB < 1.5 GB budget; disk ample; matches the
metro-township siblings kearns/white_city which also store packets). Every LIVE
packet is downloaded to raw/<date>/<key>.<ext> (fetch_packets_magna.py) with a
packets/text/<stem>.txt sidecar where born-digital text extracts.

Sources: CivicPlus AgendaCenter cat3 `?packet=true` (Council + in-session CRA, 2022+)
and Utah PMN (council 2019-2021, Planning Commission 2019-2026). The 52 PMN PC
2017-2018 packet files that HEAD-404 (documented 2017–mid-2018 PMN blob purge) are
NOT index rows — they go to unrecovered.csv as honest gaps.
"""
import csv, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-14"
CONTRACT = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
            "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["source", "content_length_bytes", "size_mb", "stored_locally",
         "pmn_notice_id", "pmn_filename"]


def load_extraction():
    """stem -> status from packets/text/_extraction_log.csv (if extraction ran)."""
    p = os.path.join(HERE, "text", "_extraction_log.csv")
    if not os.path.exists(p):
        return {}
    return {r["stem"]: r["status"] for r in csv.DictReader(open(p))}


def main():
    cat = list(csv.DictReader(open(os.path.join(RAW, "_catalog.tsv"), newline=""),
                              delimiter="\t"))
    sizes = {s["key"]: s for s in
             csv.DictReader(open(os.path.join(RAW, "_sizes.tsv")), delimiter="\t")}
    fetched = {}
    fp = os.path.join(RAW, "_fetched.tsv")
    if os.path.exists(fp):
        fetched = {r["key"]: r for r in csv.DictReader(open(fp), delimiter="\t")}
    extr = load_extraction()

    idx_rows, unrec_rows = [], []
    for r in cat:
        s = sizes.get(r["key"], {})
        live = s.get("status") == "200" and s.get("content_length_bytes", "").isdigit()
        if not live:
            unrec_rows.append({
                "date": r["date"], "title": r["title"], "body": r["body"],
                "meeting_type": r["meeting_type"], "packet_kind": r["packet_kind"],
                "source_url": r["packet_url"], "source": r["source"],
                "reason": "pmn_purged_404", "http_status": s.get("status", ""),
                "pmn_notice_id": r.get("pmn_notice_id", ""),
                "pmn_filename": r.get("pmn_filename", ""),
            })
            continue
        clb_i = int(s["content_length_bytes"])
        f = fetched.get(r["key"], {})
        path = f.get("path", "")
        stored = "yes" if path else "no"
        if not path:
            fmt, method = "na", "not_retrieved (fetch pending/failed)"
        elif path.lower().endswith(".docx"):
            # born-digital Word doc; §9 format vocab has no docx variant -> 'text'.
            # Sidecar written by hand (word/document.xml strip) since
            # extract_packet_text.py only handles .pdf.
            fmt, method = "text", "docx-xml (born-digital; word/document.xml strip)"
        else:
            stem = os.path.splitext(os.path.basename(path))[0]
            st = extr.get(stem)
            if st == "extracted":
                fmt, method = "text", "pdftotext-layout"
            elif st == "image_only":
                fmt, method = "scanned", "pdftotext-layout (image-only; vision/OCR to read)"
            elif st == "too_big":
                fmt, method = "text", "pdftotext-skipped (>120MB bundle scan)"
            else:
                fmt, method = "text", "pdftotext-layout"
        idx_rows.append({
            "date": r["date"],
            "title": r["title"] or f"{r['body']} meeting packet {r['date']}",
            "body": r["body"], "meeting_type": r["meeting_type"],
            "packet_kind": r["packet_kind"], "source_url": r["packet_url"],
            "retrieved_date": RETRIEVED, "format": fmt,
            "extraction_method": method, "path": path,
            "source": r["source"], "content_length_bytes": clb_i,
            "size_mb": round(clb_i / 1e6, 2), "stored_locally": stored,
            "pmn_notice_id": r.get("pmn_notice_id", ""),
            "pmn_filename": r.get("pmn_filename", ""),
        })

    idx_rows.sort(key=lambda x: (x["body"], x["date"], x["source"], x["source_url"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CONTRACT + EXTRA)
        w.writeheader()
        w.writerows(idx_rows)

    unrec_rows.sort(key=lambda x: (x["body"], x["date"]))
    with open(os.path.join(HERE, "unrecovered.csv"), "w", newline="") as fh:
        cols = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
                "source", "reason", "http_status", "pmn_notice_id", "pmn_filename"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(unrec_rows)

    tot = sum(r["content_length_bytes"] for r in idx_rows)
    print(f"index.csv: {len(idx_rows)} rows, {tot/1e9:.2f} GB indexed")
    print(f"unrecovered.csv: {len(unrec_rows)} rows")
    for body in ("Council", "CRA", "PC"):
        sub = [r for r in idx_rows if r["body"] == body]
        yrs = Counter(r["date"][:4] for r in sub)
        src = Counter(r["source"] for r in sub)
        print(f"  {body}: {len(sub)}  src={dict(src)}  years={dict(sorted(yrs.items()))}")
    print("  meeting_type:", dict(Counter(r["meeting_type"] for r in idx_rows)))
    print("  packet_kind:", dict(Counter(r["packet_kind"] for r in idx_rows)))
    print("  format:", dict(Counter(r["format"] for r in idx_rows)))
    print("  stored:", dict(Counter(r["stored_locally"] for r in idx_rows)))
    if unrec_rows:
        uy = Counter((r["body"], r["date"][:4]) for r in unrec_rows)
        print("  unrecovered by body/year:", dict(sorted(uy.items())))


if __name__ == "__main__":
    main()
