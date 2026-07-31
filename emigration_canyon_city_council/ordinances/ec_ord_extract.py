#!/usr/bin/env python3
"""ec_ord_extract.py — text sidecars for Emigration Canyon ordinance/resolution raws.

Born-digital PDFs -> pdftotext -layout. Image-only PDFs (little/no embedded text)
-> tesseract OCR (pages rendered with pdftoppm into the SESSION SCRATCHPAD, never
/tmp). Every subprocess call has a Python timeout (no shell `timeout`).
Non-PDF raws (.docx / .xlsx) are logged but not text-extracted for FTS (the same
instrument's PDF twin carries the searchable text).

Writes:
  text/<stem>.txt              (>= MIN_CHARS of real text only)
  text/_extraction_log.csv     filename,method,chars,note

Usage: python3 ec_ord_extract.py
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
SCRATCH = ("/private/tmp/claude-501/-Users-tysonwelsh-civic-data/"
           "8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad/ec_ord_ocr")
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
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def ocr(path, stem):
    os.makedirs(SCRATCH, exist_ok=True)
    prefix = os.path.join(SCRATCH, stem)
    try:
        run(["pdftoppm", "-r", "300", "-png", path, prefix], 300)
    except subprocess.TimeoutExpired:
        return "", "ocr_render_timeout"
    pages = sorted(f for f in os.listdir(SCRATCH)
                   if f.startswith(os.path.basename(stem)) and f.endswith(".png"))
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
    raws = sorted(os.listdir(RAW))
    log = []
    for fn in raws:
        if fn.startswith("_") or fn.startswith("."):
            continue
        stem = os.path.splitext(fn)[0]
        path = os.path.join(RAW, fn)
        low = fn.lower()
        if not low.endswith(".pdf"):
            # .docx / .xlsx — retained raw, not sidecar'd (PDF twin carries text)
            ext = os.path.splitext(fn)[1].lstrip(".").lower()
            log.append((fn, f"native_{ext}", 0, "non-PDF raw; not text-extracted"))
            print(f"{'native_'+ext:16s} {0:7d}  {fn}")
            continue
        txt = pdftotext(path)
        method = "pdftotext_layout"
        note = ""
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
    n_none = sum(1 for r in log if r[1] == "none")
    n_native = sum(1 for r in log if r[1].startswith("native_"))
    print(f"\n{len(log)} raws: {len(log)-n_ocr-n_none-n_native} born-digital, "
          f"{n_ocr} OCR, {n_none} no-text, {n_native} non-PDF")


if __name__ == "__main__":
    sys.exit(main())
