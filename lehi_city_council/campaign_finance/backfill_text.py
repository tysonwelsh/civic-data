#!/usr/bin/env python3
"""backfill_text.py — generate the missing text/ sidecars for Lehi campaign_finance.

Source-6 conformance backfill (Lehi shipped ZERO text/ sidecars). For every raw filing:
  * born-digital PDF (has a real text layer) -> `pdftotext -layout` -> text/<stem>.txt
  * image-only PDF (no text layer)           -> pdftoppm 300dpi + tesseract -> text/<stem>.txt
  * .jpg scan                                -> tesseract -> text/<stem>.txt

Writes text_extraction.csv (path, stem, format, extraction_method, chars) which build_index.py
reads to set each row's `format`/`extraction_method` HONESTLY (the original index guessed by
file extension and mislabeled 64 image-only PDFs as born-digital `text`).

Idempotent. Temp page images go to the session scratchpad, never /tmp or the repo.
"""
import csv, os, subprocess, sys, tempfile, glob

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_DIR = os.path.join(HERE, "text")
SCRATCH = os.environ.get("CLAUDE_SCRATCH",
    "/private/tmp/claude-501/-Users-tysonwelsh-civic-data/f43a66e4-730f-4ca8-a53a-f0b8118a953b/scratchpad")
MIN_CHARS = 40  # a real born-digital text layer yields far more; image PDFs yield ~0

def pdftotext(pdf):
    try:
        out = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                             capture_output=True, timeout=120).stdout
        return out.decode("utf-8", "replace")
    except Exception:
        return ""

def ocr_pdf(pdf, stem):
    with tempfile.TemporaryDirectory(dir=SCRATCH) as td:
        prefix = os.path.join(td, "pg")
        subprocess.run(["pdftoppm", "-png", "-r", "300", pdf, prefix],
                       capture_output=True, timeout=600)
        pages = sorted(glob.glob(prefix + "*.png"))
        chunks = []
        for pg in pages:
            r = subprocess.run(["tesseract", pg, "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            chunks.append(r.stdout.decode("utf-8", "replace"))
        return "\n".join(chunks)

def ocr_image(img):
    r = subprocess.run(["tesseract", img, "-", "--psm", "6"],
                       capture_output=True, timeout=300)
    return r.stdout.decode("utf-8", "replace")

def main():
    os.makedirs(TEXT_DIR, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "index.csv"))))
    manifest = []
    for i, r in enumerate(rows, 1):
        rel = r["path"]
        pdf = os.path.join(HERE, rel)
        stem = os.path.splitext(os.path.basename(rel))[0]
        out_txt = os.path.join(TEXT_DIR, stem + ".txt")
        low = rel.lower()
        if low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png"):
            text = ocr_image(pdf); fmt, method = "scanned", "tesseract OCR (image)"
        else:
            text = pdftotext(pdf)
            if len(text.strip()) >= MIN_CHARS:
                fmt, method = "text", "pdftotext -layout"
            else:
                text = ocr_pdf(pdf, stem)
                fmt, method = "scanned", "tesseract OCR (pdftoppm 300dpi)"
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write(text)
        manifest.append(dict(path=rel, stem=stem, format=fmt,
                             extraction_method=method, chars=len(text.strip())))
        print(f"[{i}/{len(rows)}] {fmt:7} {len(text.strip()):6} {stem}", flush=True)
    with open(os.path.join(HERE, "text_extraction.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "stem", "format", "extraction_method", "chars"])
        w.writeheader(); w.writerows(manifest)
    from collections import Counter
    print("DONE. format:", dict(Counter(m["format"] for m in manifest)))

if __name__ == "__main__":
    main()
