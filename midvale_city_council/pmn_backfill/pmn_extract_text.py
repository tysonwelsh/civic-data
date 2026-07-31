#!/usr/bin/env python3
"""Extract text sidecars for each recovered PMN raw PDF.
Born-digital -> pdftotext -layout (extraction_method=pdftotext). If the text layer is
near-empty (<200 real chars) the PDF is a scanned image -> OCR via pdftoppm+tesseract
(extraction_method=ocr). Writes text/<stem>.txt and a _method.csv mapping."""
import os, subprocess, csv, glob, tempfile, shutil

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
os.makedirs(TXT, exist_ok=True)

def pdftotext(pdf):
    try:
        out = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                             capture_output=True, text=True, timeout=120)
        return out.stdout
    except Exception as e:
        return ""

def ocr(pdf):
    tmp = tempfile.mkdtemp()
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", pdf, os.path.join(tmp, "p")],
                       capture_output=True, timeout=900)
        chunks = []
        for png in sorted(glob.glob(os.path.join(tmp, "p*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"],
                               capture_output=True, text=True, timeout=300)
            chunks.append(r.stdout)
        return "\n".join(chunks)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def real_chars(s):
    return sum(1 for c in s if c.isalnum())

def main():
    rows = []
    for pdf in sorted(glob.glob(os.path.join(RAW, "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        txt = pdftotext(pdf)
        method = "pdftotext"
        fmt = "text"
        if real_chars(txt) < 200:
            txt2 = ocr(pdf)
            if real_chars(txt2) > real_chars(txt):
                txt = txt2; method = "ocr"; fmt = "scanned"
            else:
                method = "ocr"; fmt = "scanned"  # attempted; sparse
        with open(os.path.join(TXT, stem + ".txt"), "w") as f:
            f.write(txt)
        rows.append((stem, method, fmt, real_chars(txt)))
        print(f"{method:9s} {fmt:8s} chars={real_chars(txt):7d}  {stem}")
    with open(os.path.join(HERE, "_work", "extract_method.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["stem", "extraction_method", "format", "real_chars"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
