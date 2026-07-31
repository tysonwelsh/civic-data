#!/usr/bin/env python3
"""(Re)build the text/ sidecars — ONE per raw filing (Source-6 requirement).

For each raw/<year>/*.pdf:
  1. pdftotext -layout. If it yields >=100 non-space chars -> born-digital, format=text.
  2. else OCR: pdftoppm -r 300 -jpeg  ->  tesseract --psm 6 per page  -> format=scanned.

NOTE on the image format: this repo's leptonica/tesseract build (5.5.0 / leptonica 1.85)
fails to read pdftoppm's PNG and TIFF output ("image file not found" / "tif open failed")
but reads JPEG fine — so OCR goes through `-jpeg`. Don't "optimize" it back to PNG.

Writes /tmp/pc_textmap.json (pdf -> [format, method, n_chars]); build_index.py reads it to
stamp the authoritative format/extraction_method per row. Idempotent; does not fetch.
"""
import os, subprocess, glob, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")


def ocr(pdf):
    ppmbase = "/tmp/pc_ocr_img"
    for old in glob.glob(ppmbase + "*"):
        os.remove(old)
    subprocess.run(["pdftoppm", "-r", "300", "-jpeg", pdf, ppmbase], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    out = []
    for pg in sorted(glob.glob(ppmbase + "*.jpg")):
        r = subprocess.run(["tesseract", pg, "-", "--psm", "6"],
                           capture_output=True, timeout=300)
        out.append(r.stdout.decode("utf-8", "ignore"))
        os.remove(pg)
    return "\n".join(out).strip()


def main():
    results = {}
    for pdf in sorted(glob.glob(os.path.join(RAW, "20*", "*.pdf"))):
        year = os.path.basename(os.path.dirname(pdf))
        base = os.path.splitext(os.path.basename(pdf))[0]
        outdir = os.path.join(TXT, year)
        os.makedirs(outdir, exist_ok=True)
        txtpath = os.path.join(outdir, base + ".txt")
        try:
            subprocess.run(["pdftotext", "-layout", pdf, txtpath], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        except Exception:
            open(txtpath, "w").write("")
        txt = open(txtpath, errors="ignore").read()
        if len(txt.strip()) >= 100:
            results[pdf] = ["text", "pdftotext -layout", len(txt.strip())]
            continue
        try:
            o = ocr(pdf)
            open(txtpath, "w").write(o)
            results[pdf] = ["scanned", "tesseract OCR (pdftoppm 300dpi jpeg, psm6)", len(o)]
        except Exception as e:
            results[pdf] = ["scanned", "OCR-failed: " + str(e)[:50], len(txt.strip())]
    json.dump(results, open("/tmp/pc_textmap.json", "w"), indent=1)
    print("extracted:", len(results),
          dict(collections.Counter(v[0] for v in results.values())))
    empty = [os.path.basename(k) for k, v in results.items() if v[2] < 50]
    print("still-empty:", empty)


if __name__ == "__main__":
    main()
