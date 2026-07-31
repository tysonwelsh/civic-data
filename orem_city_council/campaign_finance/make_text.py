#!/usr/bin/env python3
"""Produce a text sidecar for EVERY harvested filing (Source-6 conformance).

Strategy per raw file:
  - PDF: try `pdftotext -layout`. If it yields real text (>= MIN_CHARS non-space) the
    PDF is born-digital  -> format=text,    method="pdftotext -layout".
    Otherwise it is a scanned image PDF     -> OCR (pdftoppm 200dpi + tesseract)
                                            -> format=scanned, method="ocr:tesseract".
  - JPG/JPEG image: OCR directly with tesseract -> format=scanned, method="ocr:tesseract".

Writes text/<rawbasename>.txt for each, and text/_extract.json mapping
rawbasename -> {format, extraction_method, chars} so build_index.py stays consistent.
"""
import glob, json, os, re, subprocess, tempfile

DS  = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(DS, "raw")
TXT = os.path.join(DS, "text")
os.makedirs(TXT, exist_ok=True)
MIN_CHARS = 120


def nonspace(s):
    return len(re.sub(r"\s", "", s or ""))


def pdftotext(pdf):
    r = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    return r.stdout or ""


def ocr_pdf(pdf):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "200", "-png", pdf, os.path.join(td, "pg")],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out = []
        for img in sorted(glob.glob(os.path.join(td, "pg*.png"))):
            r = subprocess.run(["tesseract", img, "stdout"], capture_output=True, text=True)
            out.append(r.stdout)
        return "\n\f\n".join(out)


def ocr_image(img):
    r = subprocess.run(["tesseract", img, "stdout"], capture_output=True, text=True)
    return r.stdout or ""


def main():
    files = sorted(f for f in os.listdir(RAW)
                   if not f.startswith(("_", ".")) and os.path.isfile(os.path.join(RAW, f)))
    meta = {}
    for i, name in enumerate(files, 1):
        src = os.path.join(RAW, name)
        base = os.path.splitext(name)[0]
        ext = os.path.splitext(name)[1].lower()
        if ext == ".pdf":
            txt = pdftotext(src)
            if nonspace(txt) >= MIN_CHARS:
                fmt, method = "text", "pdftotext -layout"
            else:
                txt = ocr_pdf(src)
                fmt, method = "scanned", "ocr:tesseract"
        elif ext in (".jpg", ".jpeg", ".png"):
            txt = ocr_image(src)
            fmt, method = "scanned", "ocr:tesseract"
        else:
            txt, fmt, method = "", "na", "none"
        with open(os.path.join(TXT, base + ".txt"), "w") as f:
            f.write(txt)
        meta[name] = {"format": fmt, "extraction_method": method, "chars": nonspace(txt)}
        print(f"[{i}/{len(files)}] {fmt:7s} {meta[name]['chars']:6d}  {name}")
    with open(os.path.join(TXT, "_extract.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("TEXT DONE")


if __name__ == "__main__":
    main()
