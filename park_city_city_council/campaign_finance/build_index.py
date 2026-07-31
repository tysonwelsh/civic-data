#!/usr/bin/env python3
"""Regenerate campaign_finance/index.csv from the retained raw PDFs + the download
manifest + the text sidecars, and join every filer to ../election_results/.

Idempotent: reads only files already on disk. Does NOT fetch. Re-run after adding raw
files (update batch/manifest.json first) or re-running extract_text.py.

Inputs
  raw/<year>/*.pdf            the retained filings (filename = <year>_<period>_<stem>)
  batch/manifest.json         href/source_url/period per outname (download provenance)
  text/<year>/<stem>.txt      text sidecar per filing (format decided from its length)
  ../election_results/park_city_results_by_candidate.csv   join target

Output
  index.csv                   one row per filing (schema documented in CLAUDE.md)
"""
import csv, json, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
ELECT = os.path.abspath(os.path.join(HERE, "..", "election_results",
                                     "park_city_results_by_candidate.csv"))
RETRIEVED = "2026-07-05"

# ---- qualifier tokens stripped when recovering a candidate name from a filename ----
QUAL = re.compile(r"\b(amended|final|finalx|disclosure|disclosures|campaign|financial|"
                  r"finance|mayoral|mayor|city|council|councilmember|primary|general|"
                  r"election|municipal|report|redacted|conflict|of|interest|statement|"
                  r"cima|form|withdrawn|candidacy|january|february|march|april|may|june|"
                  r"july|august|september|october|november|december)\b", re.I)


def clean_candidate(stem):
    """Recover the filer name from a filename stem like
    'Andy Beerman Mayoral FINAL Campaign Financial Disclosure' -> 'Andy Beerman'."""
    s = stem.replace("_", " ")
    s = s.split(" - ")[0]                       # drop trailing " - October 28 2025" / " - Withdrawn"
    s = re.sub(r"(FINAL)([A-Z])", r"\1 \2", s)  # split source run-on: FINALCampaign -> FINAL Campaign
    s = re.sub(r"\bC?Ity\b", " ", s)            # source typo "CIty Council"
    s = re.sub(r"\d[\d.,\-]*", " ", s)          # drop dates/version numbers (10.24.23, 2, 3)
    s = QUAL.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip(" .-,")
    return s


def norm(name):
    """first+last normalization for joining (drops middle initials, nicknames, suffixes)."""
    n = re.sub(r'"[^"]*"', " ", name)          # drop "J.K." / "Pickleball Traffic"
    n = re.sub(r"\b(III|II|IV|Jr|Sr)\b\.?", " ", n)
    n = re.sub(r"\b[A-Z]\.", " ", n)           # drop middle initials A.
    n = re.sub(r"[^A-Za-z ]", " ", n)
    toks = n.lower().split()
    if not toks:
        return ("", "")
    return (toks[0], toks[-1])


def load_manifest():
    p = os.path.join(HERE, "batch", "manifest.json")
    m = json.load(open(p))
    by_out = {r["outname"]: r for r in m}
    return by_out


def load_election():
    rows = []
    with open(ELECT) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def main():
    manifest = load_manifest()
    elect = load_election()
    # index election by (first,last,year) -> office(s)
    ekey = {}
    for r in elect:
        k = norm(r["candidate"]) + (r["year"],)
        ekey.setdefault(k, r)
    # also (first,last) any-year for firstlast fallback
    ekey_any = {}
    for r in elect:
        ekey_any.setdefault(norm(r["candidate"]), r)
    # surname+year -> row, for filenames that carry only a last name (Zegarra, Dobkin, Whitesides)
    elast = {}
    for r in elect:
        elast.setdefault((norm(r["candidate"])[1], r["year"]), r)

    rows = []
    for pdf in sorted(glob.glob(os.path.join(RAW, "20*", "*.pdf"))):
        fn = os.path.basename(pdf)
        year_dir = os.path.basename(os.path.dirname(pdf))
        m = re.match(r"^(\d{4})_([a-z]+)_(.*)\.pdf$", fn)
        if not m:
            print("SKIP (unparsed):", fn); continue
        year, period, stem = m.group(1), m.group(2), m.group(3)
        man = manifest.get(fn, {})
        source_url = man.get("url", "")
        if not source_url:  # recovered / manually added files
            source_url = "MANUAL:" + fn
        candidate = clean_candidate(stem)

        # office
        office = ""
        low = stem.lower()
        if "mayor" in low:
            office = "Mayor"
        elif "council" in low:
            office = "Council"

        # filing_type
        if period == "coi":
            filing_type = "conflict_of_interest"
        elif "final" in low or period == "final":
            filing_type = "summary"
        else:
            filing_type = "interim"
        amended = "yes" if "amended" in low else "no"

        # report period label
        plabel = {"primary": "Primary", "general": "General",
                  "final": "Final", "coi": "Conflict of Interest"}.get(period, period)

        # election-year for campaign filings (COI years are governance years, keep as-is)
        election_year = year

        # join
        fl = norm(candidate)
        first, last = fl
        matched, conf = "", "none"
        er = ekey.get(fl + (year,))
        elr = elast.get((last, year)) if last else None
        if er:
            matched, conf = er["candidate"], ("exact" if period != "coi" else "coi-officeholder")
        elif first and elr:
            # same last name + same year (surname-only filename, or minor first-name variant)
            matched, conf = elr["candidate"], ("firstlast" if period != "coi" else "coi-officeholder")
        else:
            era = ekey_any.get(fl) or (elast.get((last, "")) if last else None)
            if era:
                matched, conf = era["candidate"], ("firstlast" if period != "coi" else "coi-officeholder")
        if not office:
            erow = er or elr or ekey_any.get(fl)
            if erow:
                office = erow["office"]

        # format from text sidecar
        stem_txt = os.path.join(TXT, year, os.path.splitext(fn)[0] + ".txt")
        fmt, method = "na", "none"
        if os.path.exists(stem_txt):
            n = len(open(stem_txt, errors="ignore").read().strip())
            if n >= 100:
                # decide text vs scanned via textmap if available
                fmt = "text"; method = "pdftotext -layout"
            else:
                fmt = "scanned"; method = "tesseract OCR (pdftoppm 300dpi, psm6)"
        # refine using textmap.json if present (authoritative on which path was OCR)
        rows.append(dict(
            date=f"{year}-01-01", candidate=candidate, office=office,
            election_year=election_year, filing_type=filing_type,
            title=f"{candidate} — {year} Park City {plabel} campaign financial disclosure"
                  + (" [amended]" if amended == "yes" else ""),
            source_url=source_url, retrieved_date=RETRIEVED, format=fmt,
            extraction_method=method,
            path=os.path.relpath(pdf, HERE),
            matched_election_candidate=matched, join_confidence=conf,
            reporting_period=plabel, amended=amended))

    # apply textmap for authoritative format/method
    tm_path = "/tmp/pc_textmap.json"
    if os.path.exists(tm_path):
        tm = json.load(open(tm_path))
        tm_by = {os.path.basename(k): v for k, v in tm.items()}
        for r in rows:
            b = os.path.basename(r["path"])
            if b in tm_by:
                f0, meth, n = tm_by[b]
                r["format"] = f0
                if f0 == "scanned":
                    r["extraction_method"] = "tesseract OCR (pdftoppm jpeg 200-300dpi, psm6)"
                else:
                    r["extraction_method"] = "pdftotext -layout"

    # SCHEMA_SPEC §9 contract header, extras after
    cols = ["date", "candidate", "office", "election_year", "filing_type",
            "reporting_period", "title", "source_url", "retrieved_date", "format",
            "extraction_method", "path", "matched_election_candidate",
            "join_confidence", "amended"]
    rows.sort(key=lambda r: (r["election_year"], r["reporting_period"], r["candidate"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote index.csv: {len(rows)} rows")
    # join stats
    camp = [r for r in rows if r["filing_type"] != "conflict_of_interest"]
    joined = [r for r in camp if r["join_confidence"] in ("exact", "firstlast")]
    print(f"campaign filings: {len(camp)}  joined: {len(joined)} "
          f"({100*len(joined)/len(camp):.0f}%)")
    from collections import Counter
    print("by format:", Counter(r["format"] for r in rows))
    print("unmatched campaign filers:",
          sorted({r["candidate"] for r in camp if r["join_confidence"] == "none"}))


if __name__ == "__main__":
    main()
