#!/usr/bin/env python3
"""Extract a text sidecar for every raw/ ordinance PDF.

Born-digital PDFs -> `pdftotext -layout`. Image-only/scanned PDFs (near-zero text
layer) -> tesseract OCR at 300 dpi via a pymupdf render into the session scratchpad
(NOT /tmp/system; temp images are deleted after). Per-file method is logged to
text/_extraction_log.csv so index.csv can label `extraction_method` honestly.

Idempotent, no network. Preserves source text verbatim (no cleanup).

Usage: python3 ch_ord_extract_text.py [--scratch DIR]
"""
import csv
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
LOG = os.path.join(TEXT, "_extraction_log.csv")
MIN_REAL = 200  # chars of a real text layer before we trust pdftotext over OCR

SCRATCH = "/private/tmp/claude-501/-Users-tysonwelsh-civic-data/8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad/ord_ocr"


def pdftotext(pdf):
    try:
        out = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                             capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", "replace")
    except Exception as e:
        return ""


def ocr(pdf, scratch):
    """Render each page to a PNG with pymupdf, OCR with tesseract."""
    import fitz  # pymupdf
    os.makedirs(scratch, exist_ok=True)
    doc = fitz.open(pdf)
    parts = []
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            tmp = os.path.join(scratch, f"p{i}.png")
            pix.save(tmp)
            try:
                out = subprocess.run(["tesseract", tmp, "-", "--psm", "6"],
                                     capture_output=True, timeout=300)
                parts.append(out.stdout.decode("utf-8", "replace"))
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
    finally:
        doc.close()
    return "\n".join(parts)


def main():
    scratch = SCRATCH
    if "--scratch" in sys.argv:
        scratch = sys.argv[sys.argv.index("--scratch") + 1]
    os.makedirs(TEXT, exist_ok=True)
    rows = []
    pdfs = sorted(f for f in os.listdir(RAW) if f.lower().endswith(".pdf"))
    for fn in pdfs:
        pdf = os.path.join(RAW, fn)
        stem = os.path.splitext(fn)[0]
        txt = pdftotext(pdf)
        real = len(txt.strip())
        method = "pdftotext -layout (born-digital)"
        fmt = "text"
        if real < MIN_REAL:
            try:
                txt = ocr(pdf, scratch)
                method = "tesseract 5 OCR @300dpi (scanned/image PDF)"
                fmt = "scanned"
            except Exception as e:
                txt = txt or ""
                method = f"OCR-failed:{e}"
                fmt = "na"
        with open(os.path.join(TEXT, stem + ".txt"), "w") as f:
            f.write(txt)
        rows.append({"file": fn, "chars": len(txt.strip()),
                     "format": fmt, "extraction_method": method})
        print(f"{fn}: {len(txt.strip())} chars [{fmt}]")
    with open(LOG, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "chars", "format", "extraction_method"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} sidecars -> {TEXT}; log -> {LOG}")


if __name__ == "__main__":
    main()
