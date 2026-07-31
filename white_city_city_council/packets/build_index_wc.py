#!/usr/bin/env python3
"""build_index_wc.py — assemble White City packets/index.csv from _candidates.csv +
the fetched raw/ PDFs + the text/_extraction_log.csv sidecar log.

§9 packets contract header (exact, in order):
  date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
  extraction_method,path
City-specific extras AFTER the contract columns: era,bytes

era: metro_township (date < 2024-05-01, HB35 city conversion) | city (>= 2024-05-01)
format: text (born-digital, sidecar produced) | scanned (image-only, no sidecar)
Run AFTER extract_packet_text.py so the extraction log exists.
"""
import csv, os, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_SEAM = "2024-05-01"  # HB35 metro-township -> city
RETRIEVED = "2026-07-13"

CONTRACT = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
            "retrieved_date", "format", "extraction_method", "path"]
EXTRA = ["era", "bytes"]


def clean_name(url):
    return urllib.parse.unquote(url.rsplit("/", 1)[-1]).replace(" ", "_")


def title_from(fname):
    stem = fname[:-4] if fname.lower().endswith(".pdf") else fname
    stem = stem[:-4] if stem.lower().endswith(".pdf") else stem  # .pdf.pdf
    return stem.replace("_", " ").replace("+", " ").strip()


def load_extraction_log():
    """stem -> status from text/_extraction_log.csv (extracted/image_only/...)."""
    log = {}
    p = os.path.join(HERE, "text", "_extraction_log.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            log[r.get("stem", "")] = r.get("status", "")
    return log


def main():
    cands = list(csv.DictReader(open(os.path.join(HERE, "_candidates.csv"))))
    exlog = load_extraction_log()
    rows = []
    for c in cands:
        date = c["date"]
        name = clean_name(c["url"])
        rel = os.path.join("raw", date, name)
        full = os.path.join(HERE, rel)
        if not os.path.exists(full):
            print("MISSING on disk, skipping:", rel)
            continue
        size = os.path.getsize(full)
        stem = name[:-4] if name.lower().endswith(".pdf") else name
        stem = stem[:-4] if stem.lower().endswith(".pdf") else stem
        status = exlog.get(stem, "")
        sidecar = os.path.join(HERE, "text", stem + ".txt")
        if os.path.exists(sidecar):
            fmt, method = "text", "pdftotext -layout"
        elif status == "image_only":
            fmt, method = "scanned", "none (image-only; vision/OCR)"
        elif status == "too_big":
            fmt, method = "scanned", "none (oversize; vision/OCR)"
        else:
            fmt, method = "text", "pdftotext -layout"
        era = "metro_township" if date < CITY_SEAM else "city"
        rows.append({
            "date": date,
            "title": title_from(name),
            "body": c["body"],
            "meeting_type": c["meeting_type"],
            "packet_kind": c["packet_kind"],
            "source_url": c["url"],
            "retrieved_date": RETRIEVED,
            "format": fmt,
            "extraction_method": method,
            "path": rel,
            "era": era,
            "bytes": size,
        })
    rows.sort(key=lambda r: (r["date"], r["body"], r["path"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRA)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote index.csv: {len(rows)} rows")
    from collections import Counter
    print("format:", dict(Counter(r["format"] for r in rows)))
    print("era:", dict(Counter(r["era"] for r in rows)))
    print("body:", dict(Counter(r["body"] for r in rows)))


if __name__ == "__main__":
    main()
