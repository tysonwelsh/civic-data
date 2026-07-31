#!/usr/bin/env python3
"""Emit midvale_city_council/packets/index.csv (SCHEMA_SPEC §9 packets contract +
St.-George-style INDEX-ONLY extras) from the size-probed harvest."""
import json, os, csv, re

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT = ["date", "title", "body", "meeting_type", "packet_kind",
            "source_url", "retrieved_date", "format", "extraction_method", "path"]
EXTRAS = ["content_length_bytes", "size_mb", "stored_locally"]
RETR = "2026-07-13"

def meeting_type(fn):
    f = fn.lower()
    if "truth in taxation" in f or "truth-in-taxation" in f:
        return "truth_in_taxation"
    if "special" in f:
        return "special"
    if "work" in f or "study" in f:
        return "work_session"
    return "regular"

def title(fn):
    return re.sub(r"\.pdf$", "", fn, flags=re.I).strip()

def main():
    rows = json.load(open(os.path.join(HERE, "_probed.json")))
    # stable sort: body then date desc (newest first, like St. George)
    rows.sort(key=lambda r: (r["body"], r["date"], r["fname"]), reverse=True)
    out = []
    for r in rows:
        live = bool(r["content_length"])
        cl = r["content_length"] if live else ""
        smb = round(r["content_length"] / 1e6, 2) if live else ""
        em = ("not_retrieved (index-only; fetch source_url on demand)" if live
              else "not_retrieved (dead link — city page 404s as-published)")
        out.append({
            "date": r["date"],
            "title": title(r["fname"]),
            "body": r["body"],
            "meeting_type": meeting_type(r["fname"]),
            "packet_kind": "full_packet",
            "source_url": r["source_url"],
            "retrieved_date": RETR,
            "format": "na",
            "extraction_method": em,
            "path": "",
            "content_length_bytes": cl,
            "size_mb": smb,
            "stored_locally": "no",
        })
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRAS)
        w.writeheader()
        w.writerows(out)
    live = [r for r in out if r["content_length_bytes"] != ""]
    print(f"wrote {len(out)} rows ({len(live)} live, {len(out)-len(live)} dead-link)")

if __name__ == "__main__":
    main()
