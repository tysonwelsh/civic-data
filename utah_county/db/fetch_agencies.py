#!/usr/bin/env python3
"""Harvest Housing Authority of Utah County (HAUC) board MINUTES -> markdown + index.

HAUC is a SEPARATE legal entity (housinguc.org), NOT in the county commission portal
(recon.md / agencies/README.md). It publishes born-digital board minutes on its own site
under yearly pages https://housinguc.org/<year>-public-notices-and-documents/. Vote grammar
is tally-only, mover/seconder named by FIRST NAME ("April made a motion... Amelia seconded
the motion. The motion passed unanimously.") -> names_recorded=0.

Utah County has NO separate RDA/MBA (the 3-member board acts directly) -> HAUC is the only
agency body. Writes:

    agencies/housing_authority/minutes/<year>/<date>_housing_authority.md
    agencies/housing_authority/minutes_index.csv
    agencies/housing_authority/minutes/_catalog.csv   (for extract_votes.py)

DERIVED + idempotent. Born-digital (pypdf); no OCR needed.
"""
import csv, os, re, urllib.request, time

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
MODULE = os.path.join(COUNTY, "agencies", "housing_authority")
RAW = os.path.join(MODULE, "raw")
INDEX_PAGES = [
    "https://housinguc.org/2026-public-notices-and-documents/",
    "https://housinguc.org/2025-public-notices-and-documents/",
    "https://housinguc.org/2024-public-notices-and-documents/",
    "https://housinguc.org/2023-public-notices-and-documents/",
    "https://housinguc.org/archived-public-notices-and-documents/",
]
UA = {"User-Agent": "Mozilla/5.0 civic-data/1.0"}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}


def http(url, binary=True):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read() if binary else r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == 3:
                print("  ! fetch failed:", url, repr(e)[:80]); return None
            time.sleep(2 * (i + 1))


def parse_date(fn):
    b = os.path.basename(fn)
    m = re.search(r"(january|february|march|april|may|june|july|august|september|"
                  r"october|november|december)-(\d{1,2})-(\d{4})", b, re.I)
    if m:
        return "%s-%02d-%02d" % (m.group(3), MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.search(r"(\d{2})(\d{2})(\d{4})", b)               # MMDDYYYY
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2,4})", b)        # M-D-YY(YY)
    if m:
        y = m.group(3); y = ("20" + y) if len(y) == 2 else y
        return "%s-%02d-%02d" % (y, int(m.group(1)), int(m.group(2)))
    return None


def main():
    os.makedirs(RAW, exist_ok=True)
    # discover minutes PDFs across all year pages
    found = {}      # url -> None (dedup)
    for page in INDEX_PAGES:
        html = http(page, binary=False)
        if not html:
            continue
        for m in re.finditer(r'href="([^"]+\.pdf)"', html, re.I):
            u = m.group(1)
            if re.search(r"minute", u, re.I) and "hauc" in u.lower():
                found[u.replace("http://", "https://")] = None
    print("HAUC minutes PDFs discovered:", len(found))

    idx_rows = []; cat_rows = []; got = 0
    for url in sorted(found):
        fn = os.path.basename(url)
        date = parse_date(fn)
        if not date:
            print("  ! undated, skipping:", fn); continue
        year = date[:4]
        pdf = os.path.join(RAW, fn)
        if not (os.path.exists(pdf) and os.path.getsize(pdf) > 1000):
            blob = http(url)
            if not blob or len(blob) < 1000:
                print("  ! download failed:", url); continue
            open(pdf, "wb").write(blob)
        try:
            reader = PdfReader(pdf)
            txt = "\n".join((p.extract_text() or "") for p in reader.pages)
            npages = len(reader.pages)
        except Exception as e:
            print("  ! parse failed:", fn, repr(e)[:60]); continue
        if len(txt.strip()) < 200:
            print("  ! low-text (image scan?):", fn, len(txt));
        md_dir = os.path.join(MODULE, "minutes", year)
        os.makedirs(md_dir, exist_ok=True)
        md = os.path.join(md_dir, "%s_housing_authority.md" % date)
        header = (
            "---\n"
            "jurisdiction: Utah County\n"
            "body: Housing Authority of Utah County\n"
            "date: %s\n"
            "source_url: %s\n"
            "source: housinguc.org (own site)\n"
            "extraction: pypdf text (born-digital)\n"
            "n_pages: %d\n"
            "---\n\n" % (date, url, npages))
        open(md, "w", encoding="utf-8").write(header + txt)
        rel = os.path.relpath(md, COUNTY)
        idx_rows.append([date, "Housing Authority of Utah County", rel, url, "Final", ""])
        cat_rows.append([date, "Housing Authority of Utah County", rel, "minutes", "", url])
        got += 1
        print("  %s HAUC (%dp)" % (date, npages))

    idx_rows.sort(); cat_rows.sort()
    with open(os.path.join(MODULE, "minutes_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "source_url", "minutes_status", "note"])
        w.writerows(idx_rows)
    with open(os.path.join(MODULE, "minutes", "_catalog.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "provenance", "kind", "source_url"])
        w.writerows(cat_rows)
    print("HAUC minutes: %d fetched" % got)


if __name__ == "__main__":
    main()
