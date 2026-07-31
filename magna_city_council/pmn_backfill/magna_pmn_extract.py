#!/usr/bin/env python3
"""Magna PMN backfill — extract text sidecars + content-detect real minutes.

For each raw/*.pdf: pdftotext -layout -> char count. If born-digital text is thin
(< 400 chars) treat as scanned and OCR with tesseract (pdftoppm -> tesseract),
labeling format=scanned / extraction_method=tesseract-ocr. Otherwise
format=text / extraction_method=pdftotext-layout.

Content-detect: flag whether the text shows minutes grammar (moved/second/vote/
motion/AYE) vs agenda-only. Prints a per-file report; writes text/<stem>.txt.
"""
import os, re, subprocess, glob, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
os.makedirs(TEXT, exist_ok=True)

MIN_GRAMMAR = re.compile(r'\b(moved|seconded|second the motion|motion carried|'
                         r'roll call|aye|nay|vote was|in favor|unanimous|minutes of)\b', re.I)
AGENDA_HINT = re.compile(r'\bpublic notice is hereby given|agenda\b', re.I)

def pdftotext(path):
    r = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
    return r.stdout

def ocr(path):
    txt = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-png", path, os.path.join(td, "p")],
                       check=True, capture_output=True)
        for png in sorted(glob.glob(os.path.join(td, "p*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"],
                               capture_output=True, text=True)
            txt.append(r.stdout)
    return "\n".join(txt)

def main():
    rows = []
    for pdf in sorted(glob.glob(os.path.join(RAW, "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        txt = pdftotext(pdf)
        nchar = len(txt.strip())
        method, fmt = "pdftotext-layout", "text"
        if nchar < 400:
            txt = ocr(pdf)
            method, fmt = "tesseract-ocr", "scanned"
        with open(os.path.join(TEXT, stem + ".txt"), "w") as f:
            f.write(txt)
        gr0 = len(MIN_GRAMMAR.findall(txt))
        moved = len(re.findall(r'\bmoved\b', txt, re.I))
        secd = len(re.findall(r'\bsecond', txt, re.I))
        is_min = gr0 >= 3 and (moved >= 1 or secd >= 1)
        rows.append((stem, fmt, method, len(txt.strip()), gr0, moved, secd, is_min))
    print(f"{'file':52} {'fmt':7} {'chars':>7} {'gram':>5} {'mov':>4} {'sec':>4}  minutes?")
    for stem, fmt, method, n, g, mv, sc, im in rows:
        print(f"{stem:52} {fmt:7} {n:7} {g:5} {mv:4} {sc:4}  {'YES' if im else 'NO -- CHECK'}")

if __name__ == "__main__":
    main()
