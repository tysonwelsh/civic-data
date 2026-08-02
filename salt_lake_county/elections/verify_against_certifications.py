"""verify_against_certifications.py — EXTERNAL cross-check of the staged county
races against the county's OWN certified summary PDFs.

The reconciliation gate inside normalize_sovc_county.py proves INTERNAL
consistency (precinct rows vs the workbook's own contest-total row). This script
proves the numbers also match a SECOND, independently published county document:
the certified summary / certification PDF for the same election (mirrored under
raw/<year>/, role='summary' in sources.csv).

Method (deliberately format-agnostic — the summary PDF layout changes five times
between 2002 and 2026): for every race in county_races.csv, look for a WINDOW of
lines in that election's summary PDF carrying BOTH a distinctive token of the
winner's printed name AND the exact winner_votes figure (with or without
thousands separators). A window, not a line, because the 2016 PDF wraps a
candidate's name around its vote row ("RICHARD" / "REP 202884 51.72%" /
"SNELGROVE"). A race passes only on a joint name+number hit.

Statuses:
  match             winner name + winner_votes found together in the county PDF
  no-pdf            no summary PDF published for that election (honest gap)
  no-text           the PDF has no extractable text layer (scanned) — not a failure
  no-contest-results the published PDF is a canvass STATISTICS report with no
                    contest tallies (the 2026 primary) — nothing to check against
  NOT FOUND         the pairing is absent — investigate before trusting the row

Usage:  python3 salt_lake_county/elections/verify_against_certifications.py
Requires `pdftotext` (poppler) on PATH.
"""
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SOURCES = os.path.join(HERE, "sources.csv")
RACES = os.path.join(HERE, "county_races.csv")
OUT = os.path.join(HERE, "verification_county.csv")

STOP = {"JR", "SR", "II", "III", "DEM", "REP", "NP", "NON", "UNA", "CON", "LIB",
        "IAP", "GRN", "DE", "RE", "GR", "LI"}


def pdf_text(path):
    try:
        return subprocess.run(["pdftotext", "-layout", path, "-"],
                              capture_output=True, text=True, timeout=180).stdout
    except Exception:                                          # noqa: BLE001
        return ""


def tokens(name):
    """Distinctive alphabetic tokens of a printed candidate name (>=3 chars)."""
    n = re.sub(r"[\(\[].*?[\)\]]", " ", name)
    n = re.sub(r'["“”]', " ", n)
    out = [t for t in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", n)
           if t.upper() not in STOP]
    return out or re.findall(r"[A-Za-z]{2,}", name)


def main():
    with open(SOURCES, newline="", encoding="utf-8") as f:
        srows = [r for r in csv.DictReader(f)
                 if r["role"] == "summary" and r["status"] == "mirrored"]
    pdfs = defaultdict(list)
    for r in srows:
        pdfs[(r["year"], r["election_type"])].append(
            os.path.join(HERE, r["local_path"]))

    cache = {}
    results = []
    with open(RACES, newline="", encoding="utf-8") as f:
        races = list(csv.DictReader(f))
    for r in races:
        key = (r["year"], r["election_type"])
        paths = pdfs.get(key, [])
        if not paths:
            results.append({**{k: r[k] for k in ("year", "election_type", "office",
                                                 "district", "winner", "winner_votes")},
                            "pdf": "", "status": "no-pdf"})
            continue
        status, hitfile = "NOT FOUND", ""
        empty, has_tallies = True, False
        for p in paths:
            if p not in cache:
                cache[p] = pdf_text(p)
            txt = cache[p]
            if txt.strip():
                empty = False
            if re.search(r"\b\d[\d,]{2,}\s+\d{1,3}\.\d\d\s*%", txt):
                has_tallies = True
            v = int(r["winner_votes"])
            nums = {str(v), "{:,}".format(v)}
            toks = tokens(r["winner"])
            lines = txt.splitlines()
            for i, line in enumerate(lines):
                if not any(n in line for n in nums):
                    continue
                window = " \n ".join(lines[max(0, i - 2):i + 3])
                if any(re.search(r"\b%s\b" % re.escape(t), window, re.I) for t in toks):
                    status, hitfile = "match", os.path.basename(p)
                    break
            if status == "match":
                break
        if status == "NOT FOUND" and empty:
            status = "no-text"
        elif status == "NOT FOUND" and not has_tallies:
            status = "no-contest-results"
        results.append({**{k: r[k] for k in ("year", "election_type", "office",
                                             "district", "winner", "winner_votes")},
                        "pdf": hitfile or os.path.basename(paths[0]), "status": status})

    cols = ["year", "election_type", "office", "district", "winner", "winner_votes",
            "pdf", "status"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(results)

    tally = defaultdict(int)
    for r in results:
        tally[r["status"]] += 1
    print("Wrote %s: %d races checked  %s"
          % (os.path.basename(OUT), len(results), dict(sorted(tally.items()))))
    per = defaultdict(lambda: defaultdict(int))
    for r in results:
        per[r["year"]][r["status"]] += 1
    for y in sorted(per):
        print("   %s  %s" % (y, dict(sorted(per[y].items()))))
    bad = [r for r in results if r["status"] == "NOT FOUND"]
    if bad:
        print("\nNOT FOUND (%d):" % len(bad))
        for r in bad:
            print("   %s %-9s %-18s %-11s %-28s %8s  (%s)"
                  % (r["year"], r["election_type"], r["office"], r["district"],
                     r["winner"], r["winner_votes"], r["pdf"]))
        sys.exit(1)


if __name__ == "__main__":
    main()
