#!/usr/bin/env python3
"""Assemble packets/index.csv from the parsed catalog + the HEAD-size sweep.

§9 packets contract header (SCHEMA_SPEC.md):
    date,title,body,meeting_type,packet_kind,source_url,retrieved_date,
    format,extraction_method,path
plus city extras (after the contract cols, St. George convention):
    content_length_bytes,size_mb,stored_locally,cancelled

South Salt Lake AgendaCenter serves the agenda PACKET via `?packet=true` (the full
assembled agenda + staff reports + attachments). Recorded roll-call minutes live on
PMN and are NOT here. This dataset is INDEX-ONLY (see AVAILABILITY.md for the size
math): no PDFs on disk, `format=na`, `stored_locally=no`; fetch source_url on demand.
"""
import csv, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-13"

CONTRACT = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
            "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["content_length_bytes", "size_mb", "stored_locally", "cancelled"]


def main():
    cat = list(csv.DictReader(open(os.path.join(HERE, "raw", "_catalog.tsv")),
                              delimiter="\t"))
    sizes = {r["item_id"]: r for r in
             csv.DictReader(open(os.path.join(HERE, "raw", "_sizes.tsv")),
                            delimiter="\t")}
    rows = []
    total = 0
    for r in cat:
        s = sizes.get(r["item_id"], {})
        clb = s.get("content_length_bytes", "")
        clb_i = int(clb) if str(clb).isdigit() else None
        if clb_i:
            total += clb_i
        cancelled = "yes" if any(w in r["title"].lower()
                                 for w in ("cancel", "canceled", "cancelled")) else ""
        # packet_kind: the ?packet=true endpoint assembles the FULL packet.
        packet_kind = "full_packet"
        rows.append({
            "date": r["date"],
            "title": r["title"] or f"{r['body']} meeting packet {r['date']}",
            "body": r["body"],
            "meeting_type": r["meeting_type"],
            "packet_kind": packet_kind,
            "source_url": s.get("packet_url") or (r["agenda_url"] + "?packet=true"),
            "retrieved_date": RETRIEVED,
            "format": "na",
            "extraction_method": "not_retrieved (index-only; fetch source_url on demand)",
            "path": "",
            "content_length_bytes": clb_i if clb_i is not None else "",
            "size_mb": round(clb_i / 1e6, 2) if clb_i else "",
            "stored_locally": "no",
            "cancelled": cancelled,
        })
    rows.sort(key=lambda x: (x["body"], x["date"], x["source_url"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CONTRACT + EXTRA)
        w.writeheader()
        w.writerows(rows)

    # report
    from collections import Counter, defaultdict
    print(f"{len(rows)} rows written -> index.csv")
    print(f"total known bytes = {total:,} ({total/1e9:.2f} GB)")
    known = [r for r in rows if isinstance(r["content_length_bytes"], int)]
    unknown = [r for r in rows if not isinstance(r["content_length_bytes"], int)]
    print(f"sized: {len(known)}   unsized: {len(unknown)}")
    if known:
        szs = sorted(r["content_length_bytes"] for r in known)
        import statistics
        print(f"min {szs[0]/1e6:.2f} MB  median {statistics.median(szs)/1e6:.2f} MB  "
              f"max {szs[-1]/1e6:.2f} MB")
        print(f">50MB: {sum(1 for x in szs if x>50e6)}   "
              f">100MB: {sum(1 for x in szs if x>100e6)}")
    for body in ["Council", "PC", "RDA", "CRB"]:
        yrs = Counter(r["date"][:4] for r in rows if r["body"] == body)
        n = sum(1 for r in rows if r["body"] == body)
        canc = sum(1 for r in rows if r["body"] == body and r["cancelled"])
        print(f"  {body}: {n} ({canc} cancelled)  {dict(sorted(yrs.items()))}")


if __name__ == "__main__":
    main()
