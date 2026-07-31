#!/usr/bin/env python3
"""kearns_ord_extract.py — text sidecars for Kearns ordinance/resolution raws.

Born-digital PDFs -> pdftotext -layout. Image-only PDFs (little/no embedded text)
-> tesseract OCR (pages rendered with pdftoppm into the SESSION SCRATCHPAD, never
/tmp). .docx -> textutil (macOS) plain text. Every subprocess has a Python timeout
(no shell `timeout`). The MunicipalCodeOnline copies are mostly SCANS -> OCR-bound.

Writes:
  text/<stem>.txt              (>= MIN_CHARS of real text only)
  text/_extraction_log.csv     filename,method,chars,note

Standing rule: lives INSIDE kearns_city_council/ordinances/, unique kearns_ord_ prefix.
Usage: python3 kearns_ord_extract.py
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
SCRATCH = ("/private/tmp/claude-501/-Users-tysonwelsh-civic-data/"
           "8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad/kearns_ord_ocr")
MIN_CHARS = 200
PDFTOTEXT_TIMEOUT = 120
OCR_PAGE_TIMEOUT = 120
MAX_OCR_PAGES = 40


def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)


def pdftotext(path):
    try:
        r = run(["pdftotext", "-layout", path, "-"], PDFTOTEXT_TIMEOUT)
        return r.stdout or ""
    except (subprocess.TimeoutExpired, Exception):
        return ""


def docx_text(path):
    try:
        r = run(["textutil", "-convert", "txt", "-stdout", path], PDFTOTEXT_TIMEOUT)
        return r.stdout or ""
    except (subprocess.TimeoutExpired, Exception):
        return ""


def ocr(path, stem):
    os.makedirs(SCRATCH, exist_ok=True)
    prefix = os.path.join(SCRATCH, stem)
    try:
        run(["pdftoppm", "-r", "300", "-png", path, prefix], 300)
    except subprocess.TimeoutExpired:
        return "", "ocr_render_timeout"
    base = os.path.basename(stem)
    pages = sorted(f for f in os.listdir(SCRATCH)
                   if f.startswith(base) and f.endswith(".png"))
    out = []
    for pg in pages[:MAX_OCR_PAGES]:
        img = os.path.join(SCRATCH, pg)
        try:
            r = run(["tesseract", img, "-", "--psm", "6"], OCR_PAGE_TIMEOUT)
            out.append(r.stdout or "")
        except subprocess.TimeoutExpired:
            out.append("")
        finally:
            try:
                os.remove(img)
            except OSError:
                pass
    return "\n".join(out), "ocr_tesseract"


def main():
    os.makedirs(TXT, exist_ok=True)
    raws = sorted(f for f in os.listdir(RAW)
                  if f.lower().endswith((".pdf", ".docx")))
    log = []
    for fn in raws:
        stem = os.path.splitext(fn)[0]
        path = os.path.join(RAW, fn)
        note = ""
        if fn.lower().endswith(".docx"):
            txt = docx_text(path)
            method = "textutil_docx"
            if len(txt.strip()) < MIN_CHARS:
                method, note = "none", "docx yielded little text"
        else:
            txt = pdftotext(path)
            method = "pdftotext_layout"
            if len(txt.strip()) < MIN_CHARS:
                octxt, ocmethod = ocr(path, stem)
                if len(octxt.strip()) >= MIN_CHARS:
                    txt, method = octxt, ocmethod
                    note = "image-only PDF; OCR fallback"
                else:
                    method = ocmethod if octxt else "none"
                    note = "no extractable text (image-only, OCR yielded little)"
                    txt = octxt
        outp = os.path.join(TXT, stem + ".txt")
        if txt.strip():
            with open(outp, "w") as f:
                f.write(txt)
        log.append((fn, method, len(txt.strip()), note))
        print(f"{method:16s} {len(txt.strip()):7d}  {fn}")
    with open(os.path.join(TXT, "_extraction_log.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "method", "chars", "note"])
        w.writerows(log)
    n_ocr = sum(1 for r in log if r[1].startswith("ocr"))
    n_docx = sum(1 for r in log if r[1] == "textutil_docx")
    n_none = sum(1 for r in log if r[1] == "none")
    print(f"\n{len(log)} files: {len(log)-n_ocr-n_none-n_docx} born-digital pdf, "
          f"{n_docx} docx, {n_ocr} OCR, {n_none} no-text")


if __name__ == "__main__":
    sys.exit(main())
