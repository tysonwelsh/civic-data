#!/usr/bin/env python3
"""build_packets_index_holladay.py — write packets/index.csv (SCHEMA_SPEC §9 packets
contract) from fetch_results.tsv (stored packets) joined to events_inscope.tsv (titles).

Contract header (exact, in order):
  date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
  extraction_method,path
City extras AFTER the contract columns: apid,eventid,size_mb,stored_locally

format/extraction_method are reconciled from text/_extraction_log.csv when present
(pass --with-extraction after running extract_packet_text.py): a real text sidecar =>
format=text, extraction_method='pdftotext -layout'; image-only bundle =>
format=scanned, extraction_method='image_only (vision/OCR required)'.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-13"


def meeting_type(title):
    t = title.lower()
    if "retreat" in t:
        return "retreat"
    if "work" in t:
        return "work"
    if "legislative" in t:
        return "legislative"
    if "special" in t or "appeal" in t:
        return "special"
    if "swearing" in t or "canvass" in t:
        return "special"
    return "regular"


def load_titles():
    return {r["eventid"]: r["title"]
            for r in csv.DictReader(open(os.path.join(HERE, "events_inscope.tsv")), delimiter="\t")}


def load_extraction():
    log = os.path.join(HERE, "text", "_extraction_log.csv")
    out = {}
    if os.path.exists(log):
        for r in csv.DictReader(open(log)):
            out[r["stem"]] = r["status"]
    return out


def main():
    titles = load_titles()
    ext = load_extraction() if "--with-extraction" in sys.argv else {}
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "fetch_results.tsv")), delimiter="\t")
            if r["stored"] == "yes"]
    rows.sort(key=lambda r: (r["date"], r["body"]))
    hdr = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
           "retrieved_date", "format", "extraction_method", "path",
           "apid", "eventid", "size_mb", "stored_locally"]
    w = csv.writer(open(os.path.join(HERE, "index.csv"), "w"))
    w.writerow(hdr)
    for r in rows:
        title = titles.get(r["eventid"], "")
        stem = os.path.splitext(os.path.basename(r["path"]))[0]
        status = ext.get(stem, "")
        if status == "extracted":
            fmt, method = "text", "pdftotext -layout"
        elif status in ("image_only", "too_big"):
            fmt, method = "scanned", "image_only (vision/OCR required)"
        elif ext:
            fmt, method = "text", "pdftotext -layout"   # default when sidecar loop ran
        else:
            fmt, method = "", "pdftotext -layout"        # pre-extraction placeholder
        size_mb = round(int(r["bytes"]) / 1e6, 3) if r["bytes"] else ""
        w.writerow([r["date"], title, r["body"], meeting_type(title), "full_packet",
                    r["source_url"] if r.get("source_url") else
                    f"https://holladayut.suiteonemedia.com/event/GetAgendaPacketFile/Packet?apid={r['apid']}",
                    RETRIEVED, fmt, method, r["path"], r["apid"], r["eventid"],
                    size_mb, "yes"])
    print(f"wrote index.csv: {len(rows)} rows")


if __name__ == "__main__":
    main()
