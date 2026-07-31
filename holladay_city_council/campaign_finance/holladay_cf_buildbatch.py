#!/usr/bin/env python3
"""Holladay campaign-finance acquisition — build the polite_fetch batch (url,name).

Reads the saved discovery HTML in _disc/ and emits _disc/batch.csv:
  - city page (2023 + 2025 filings, Revize Document Center)
  - state disclosures.utah.gov folders (2021, 2017-bonus)
Names are collision-safe: <year>_<src>_<slug>.pdf
Run: python3 holladay_cf_buildbatch.py
"""
import re, os, urllib.parse, csv

HERE = os.path.dirname(os.path.abspath(__file__))
DISC = os.path.join(HERE, "_disc")
CITY_BASE = "https://www.holladayut.gov/"

def slug(s):
    s = s.rsplit("/", 1)[-1]
    s = s.split("?")[0]
    s = s.replace(".pdf", "").replace(".PDF", "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
    return s.lower()

rows = []  # (url, name, year, src)

# ---- City page: Document Center PDFs (2023 + 2025 + COI) ----
html = open(os.path.join(DISC, "city_disclosure.html"), encoding="utf-8", errors="replace").read()
for m in re.findall(r'href="([^"]+)"', html):
    if ".pdf" not in m.lower():
        continue
    if m.startswith("http") or m.startswith("/revize/plugins"):
        continue
    if "Document Center" not in m and "fee schedule" in m.lower():
        continue
    # skip non-CF doc-center files
    low = m.lower()
    if "fee schedule" in low or "good neighbor" in low:
        continue
    href = m  # relative
    url = CITY_BASE + urllib.parse.quote(href, safe="/?=&:%")
    rows.append((url, "CITY::" + href))

# ---- State folders: 2021, 2017 ----
for year, fname in [("2021", "statehol_2021.html"), ("2017", "statehol_2017.html")]:
    p = os.path.join(DISC, fname)
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="replace").read()
    for m in re.findall(r'href="([^"]+\.pdf)"', h, re.I):
        # windows backslash path -> https + forward slash + encode
        raw = m.replace("http://municipal.utah.gov/", "").replace("\\", "/")
        url = "https://municipal.utah.gov/" + urllib.parse.quote(raw, safe="/")
        rows.append((url, f"STATE{year}::" + raw))

# de-dup
seen = set(); out = []
for url, tag in rows:
    if url in seen:
        continue
    seen.add(url); out.append((url, tag))

with open(os.path.join(DISC, "batch.csv"), "w", newline="") as f:
    w = csv.writer(f)
    for url, tag in out:
        # derive on-disk name
        if tag.startswith("CITY::"):
            href = tag[6:]
            base = href.rsplit("/", 1)[-1].split("?")[0]
            # infer year from name
            yr = "2025" if re.search(r"2025|Aug2025|Oct2025|10282025|Sept2025", href) else \
                 ("2023" if ("Financial disclosures/Drew" in href or "Financial disclosures/Tracy" in href or "Financial disclosures/Gray" in href or "10242023" in href) else "coi")
            name = f"{yr}_city_{slug(base)}.pdf"
        else:
            yr = tag[5:9]
            rest = tag.split("::", 1)[1]
            name = f"{yr}_state_{slug(rest)}.pdf"
        w.writerow([url, name])

print(f"{len(out)} files -> {os.path.join(DISC,'batch.csv')}")
for url, tag in out:
    print("  ", tag)
