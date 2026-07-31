#!/usr/bin/env python3
"""Magna housing_plans helper: locate Magna's page range in a state HCD compilation PDF.

Content-scans each page (pdftotext -layout per page) for 'Magna' / 'Magna Metro Township'
and prints the pages that mention it plus alphabetical neighbors (Lindon/Logan before,
Mantua/Mapleton after) so the range can be bracketed by hand. macOS has no `timeout`.
"""
import subprocess, sys, re

def page_text(pdf, n):
    r = subprocess.run(["pdftotext", "-layout", "-f", str(n), "-l", str(n), pdf, "-"],
                       capture_output=True, text=True)
    return r.stdout

def npages(pdf):
    r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True)
    m = re.search(r"Pages:\s+(\d+)", r.stdout)
    return int(m.group(1))

NEIGHBORS = re.compile(r"\b(Lindon|Logan|Mantua|Mapleton|Magna)\b", re.I)

def main():
    pdf = sys.argv[1]
    total = npages(pdf)
    print(f"{pdf}: {total} pages")
    for n in range(1, total + 1):
        t = page_text(pdf, n)
        hits = set(m.group(1).title() for m in NEIGHBORS.finditer(t))
        if hits:
            # Show if 'Magna' appears prominently (as a header vs passing mention)
            magna_ct = len(re.findall(r"Magna", t))
            firstlines = " | ".join(l.strip() for l in t.splitlines()[:3] if l.strip())[:120]
            print(f"  p{n}: {sorted(hits)} magna_ct={magna_ct}  << {firstlines}")

if __name__ == "__main__":
    main()
