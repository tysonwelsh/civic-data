#!/usr/bin/env python3
"""Text sidecars for wasatch_county/campaign_finance: born-digital via pdftotext -layout,
image-only via pdftoppm 300dpi + tesseract. Writes text/<year>/<slug>.txt + text_extraction.csv."""
import csv, os, subprocess, tempfile, glob

ROOT = "/Users/tysonwelsh/civic-data/wasatch_county/campaign_finance"
rows = []
for pdf in sorted(glob.glob(os.path.join(ROOT, "raw", "*", "*.pdf"))):
    year = os.path.basename(os.path.dirname(pdf))
    slug = os.path.splitext(os.path.basename(pdf))[0]
    out = os.path.join(ROOT, "text", year, slug + ".txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        native = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                                capture_output=True, timeout=300).stdout.decode("utf-8", "replace")
    except Exception:
        native = ""
    alpha = sum(c.isalnum() for c in native)
    npages = 0
    try:
        info = subprocess.run(["pdfinfo", pdf], capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
        for l in info.splitlines():
            if l.startswith("Pages:"):
                npages = int(l.split()[1])
    except Exception:
        pass
    if alpha >= 200:
        fmt, method, text = "text", "pdftotext -layout", native
    else:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["pdftoppm", "-r", "300", "-png", pdf, os.path.join(td, "p")],
                           capture_output=True, timeout=900)
            parts = []
            for img in sorted(glob.glob(os.path.join(td, "p*.png"))):
                r = subprocess.run(["tesseract", img, "-", "--psm", "6"],
                                   capture_output=True, timeout=600)
                parts.append(r.stdout.decode("utf-8", "replace"))
            text = "\n\f\n".join(parts)
        fmt, method = "scanned", "tesseract OCR (pdftoppm 300dpi, psm 6)"
    open(out, "w").write(text)
    rows.append(dict(path="raw/%s/%s.pdf" % (year, slug), text_path="text/%s/%s.txt" % (year, slug),
                     pages=npages, native_alnum=alpha, out_chars=len(text),
                     format=fmt, extraction_method=method))
    print(fmt, year, slug, npages, alpha, len(text))

with open(os.path.join(ROOT, "text_extraction.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("rows", len(rows))
