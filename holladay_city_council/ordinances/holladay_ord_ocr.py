#!/usr/bin/env python3
"""Holladay ordinances OCR helper (Source 3, expand-city-sources).

Extracts text sidecars for raw/docs/*.pdf into text/<stem>.txt.

Born-digital PDFs (pdftotext -layout yields >= MIN_BORN chars) are kept as-is
and labeled extraction_method=pdftotext. Image-only / wet-signature scans are
OCR'd with tesseract at 300 dpi (pages rendered to a scratchpad temp dir, NOT
/tmp) and labeled extraction_method=tesseract-ocr.

Writes text/_extraction_log.csv (stem,method,chars,pages,note). Idempotent.
macOS has no `timeout` on PATH -> per-page subprocess timeout via Python.
"""
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw" / "docs"
TEXT = HERE / "text"
SCRATCH = Path(
    "/private/tmp/claude-501/-Users-tysonwelsh-civic-data/"
    "8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad/holladay_ord_ocr"
)
MIN_BORN = 1200  # chars from pdftotext to accept as born-digital


def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def pdftotext(pdf):
    try:
        r = run(["pdftotext", "-layout", str(pdf), "-"], 180)
        return r.stdout or ""
    except Exception:
        return ""


def ocr(pdf, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    prefix = workdir / "pg"
    try:
        run(["pdftoppm", "-r", "300", "-png", str(pdf), str(prefix)], 900)
    except subprocess.TimeoutExpired:
        return "", 0
    pages = sorted(workdir.glob("pg*.png"))
    out = []
    for pg in pages:
        try:
            r = run(["tesseract", str(pg), "-", "--psm", "6"], 300)
            out.append(r.stdout or "")
        except subprocess.TimeoutExpired:
            out.append("")
        pg.unlink(missing_ok=True)
    return "\n".join(out), len(pages)


def main():
    TEXT.mkdir(exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    log = []
    for pdf in sorted(RAW.glob("*.pdf")):
        stem = pdf.stem
        born = pdftotext(pdf)
        if len(born.strip()) >= MIN_BORN:
            (TEXT / f"{stem}.txt").write_text(born)
            log.append((stem, "pdftotext", len(born), "", "born-digital"))
            print(f"[born] {stem}: {len(born)} chars")
            continue
        work = SCRATCH / stem
        txt, npages = ocr(pdf, work)
        (TEXT / f"{stem}.txt").write_text(txt)
        log.append((stem, "tesseract-ocr", len(txt), npages,
                    "image-only scan; OCR @300dpi psm6"))
        print(f"[ocr ] {stem}: {len(txt)} chars over {npages} pages")
    with open(TEXT / "_extraction_log.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stem", "extraction_method", "chars", "pages", "note"])
        w.writerows(log)
    print(f"\nWrote {len(log)} sidecars + _extraction_log.csv")


if __name__ == "__main__":
    main()
