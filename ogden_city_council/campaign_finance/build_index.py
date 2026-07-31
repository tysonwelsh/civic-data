#!/usr/bin/env python3
"""Build text/ sidecars + index.csv for Ogden campaign-finance disclosures.

Idempotent. Reads manifest.json + the PDFs already fetched into raw/<year>/ (via
polite_fetch), extracts a text sidecar for EVERY filing (pdftotext -layout for
born-digital; pdftoppm 300dpi + tesseract for image-only scans), joins each filer to
election_results/ogden_results_by_candidate.csv by normalized name+year, and writes
index.csv. Retains raw verbatim; never edits election_results.

Run: python3 build_index.py
"""
import csv, json, os, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
RETRIEVED = "2026-07-05"
ELECTIONS = os.path.join(HERE, "..", "election_results", "ogden_results_by_candidate.csv")

# ---- name normalization (match election_results UPPER-CASE names) ----
SUFFIX = {"jr", "sr", "ii", "iii", "iv"}
def norm(name):
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    s = s.upper()
    s = re.sub(r"[.,'`]", " ", s)
    toks = [t for t in s.split() if t and t not in {x.upper() for x in SUFFIX}]
    return toks

def firstlast(name):
    t = norm(name)
    return (t[0], t[-1]) if len(t) >= 2 else (tuple(t))

def load_elections():
    rows = []
    with open(ELECTIONS, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def join(cand, year, elec):
    """Return (matched_name, office, district, confidence)."""
    cn = norm(cand); cfl = firstlast(cand)
    yr = str(year)
    yearrows = [r for r in elec if r["year"] == yr]
    # exact: same normalized token set (order-independent)
    for r in yearrows:
        if set(norm(r["candidate"])) == set(cn):
            return r["candidate"], r["office"], r["district"], "exact"
    # firstlast fallback
    for r in yearrows:
        if firstlast(r["candidate"]) == cfl:
            return r["candidate"], r["office"], r["district"], "firstlast"
    return "", "", "", "none"

# ---- text extraction ----
def pdftotext_layout(pdf):
    try:
        out = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                             capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", "replace")
    except Exception as e:
        return ""

def ocr(pdf, workdir):
    """pdftoppm 300dpi -> tesseract per page, concatenated."""
    base = os.path.join(workdir, "p")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", pdf, base],
                       capture_output=True, timeout=1200, check=True)
    except Exception:
        return ""
    pages = sorted(f for f in os.listdir(workdir) if f.startswith("p") and f.endswith(".png"))
    chunks = []
    for pg in pages:
        try:
            r = subprocess.run(["tesseract", os.path.join(workdir, pg), "-"],
                              capture_output=True, timeout=300)
            chunks.append(r.stdout.decode("utf-8", "replace"))
        except Exception:
            pass
        os.remove(os.path.join(workdir, pg))
    return "\n\f\n".join(chunks)

def alnum_len(s):
    return sum(c.isalnum() for c in s)

def main():
    man = json.load(open(os.path.join(HERE, "manifest.json")))
    elec = load_elections()
    textdir = os.path.join(HERE, "text")
    os.makedirs(textdir, exist_ok=True)
    tmp = os.path.join(HERE, ".ocr_tmp")
    os.makedirs(tmp, exist_ok=True)

    rows = []
    for f in man["filings"]:
        vid = f["viewid"]; year = f["year"]
        fname = "%d_%s.pdf" % (vid, f["slug"])
        rel = "raw/%d/%s" % (year, fname)
        pdf = os.path.join(HERE, rel)
        if not os.path.exists(pdf):
            print("MISSING (skip):", rel); continue

        # extract text: born-digital via fast pdftotext; OCR only image-only scans.
        # Idempotent: reuse an existing OCR sidecar instead of re-OCR'ing.
        sidecar = os.path.join(textdir, "%d_%s.txt" % (vid, f["slug"]))
        txt = pdftotext_layout(pdf)
        if alnum_len(txt) >= 200:
            fmt, method = "text", "pdftotext -layout"
            with open(sidecar, "w") as fh:
                fh.write(txt)
        else:
            fmt, method = "scanned", "tesseract OCR (pdftoppm 300dpi)"
            if not (os.path.exists(sidecar) and alnum_len(open(sidecar, encoding="utf-8", errors="replace").read()) >= 200):
                for g in os.listdir(tmp):
                    os.remove(os.path.join(tmp, g))
                txt = ocr(pdf, tmp)
                with open(sidecar, "w") as fh:
                    fh.write(txt)

        matched, e_office, e_district, conf = join(f["candidate"], year, elec)
        # prefer election office/district when matched, else manifest (page-transcribed)
        office = e_office if matched else f["office"]
        district = e_district if matched else f["district"]

        src_page = man["source_pages"][str(year)]
        ptag = " (placeholder — no substantive report filed)" if f.get("placeholder") else ""
        if office == "Council" and district:
            seat = (" At-Large %s" % district.split()[-1]) if district.lower().startswith("at-large") \
                   else (" District %s" % district)
        else:
            seat = ""
        title = "%s — %d Ogden %s%s campaign financial disclosure (Combined Report of Contributions & Expenditures)%s" % (
            f["candidate"], year, office, seat, ptag)

        rows.append({
            "date": "%d-01-01" % year,
            "candidate": f["candidate"],
            "office": office,
            "election_year": year,
            "district": district,
            "filing_type": "summary",
            "title": title,
            "source_url": "https://www.ogdencity.com/DocumentCenter/View/%d/%s" % (vid, f["slug"]),
            "source_page": src_page,
            "retrieved_date": RETRIEVED,
            "format": fmt,
            "extraction_method": method,
            "path": rel,
            "matched_election_candidate": matched,
            "join_confidence": conf,
            "is_winner": (next((r["is_winner"] for r in elec
                                if r["year"] == str(year)
                                and set(norm(r["candidate"])) == set(norm(f["candidate"]))), "")),
            "placeholder": "yes" if f.get("placeholder") else "no",
        })
        print("%-22s %s  fmt=%-7s join=%-9s -> %s" % (f["candidate"], year, fmt, conf, matched or "(none)"))

    # sort by year, office, candidate
    rows.sort(key=lambda r: (r["election_year"], r["office"], r["candidate"]))
    # SCHEMA_SPEC §9 campaign_finance contract header first, city extras after.
    # reporting_period is not populated (whole-cycle packets) — DictWriter restval
    # emits it blank, per contract.
    cols = ["date","candidate","office","election_year","filing_type","reporting_period",
            "title","source_url","retrieved_date","format","extraction_method","path",
            "district","source_page","matched_election_candidate","join_confidence",
            "is_winner","placeholder"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    try:
        os.rmdir(tmp)
    except OSError:
        pass

    # summary
    print("\n== %d filings ==" % len(rows))
    from collections import Counter
    print("format:", dict(Counter(r["format"] for r in rows)))
    print("join:", dict(Counter(r["join_confidence"] for r in rows)))

if __name__ == "__main__":
    main()
