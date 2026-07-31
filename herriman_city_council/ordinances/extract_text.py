#!/usr/bin/env python3
"""Extract text/ sidecars for the ordinances dataset. Idempotent.

- raw/archive/<num>.pdf  -> text/<num>.txt  (pdftotext -layout; tesseract OCR
  @300dpi when the text layer is absent/thin — labeled per stem in
  text/_extraction_log.csv, which build_index.py reads for format/extraction_method)
- raw/pmn/notice_<id>.html -> text/notice_<id>.txt (the Recorder's
  Description/Agenda block, tag-stripped; summary notice, NOT full ordinance text)
"""
import csv, glob, html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(HERE, "text")
os.makedirs(TEXT, exist_ok=True)

def real_chars(t):
    return len(re.sub(r"\s", "", t))

def pdftotext(pdf):
    r = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""

def ocr(pdf):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", pdf,
                        os.path.join(td, "p")], check=True)
        out = []
        for png in sorted(glob.glob(os.path.join(td, "p-*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--dpi", "300"],
                               capture_output=True, text=True)
            out.append(r.stdout)
        return "\n".join(out)

def main():
    log = []
    for pdf in sorted(glob.glob(os.path.join(HERE, "raw", "archive", "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        dst = os.path.join(TEXT, stem + ".txt")
        txt = pdftotext(pdf)
        if real_chars(txt) >= 200:
            fmt, meth = "text", "pdftotext -layout"
        else:
            if os.path.exists(dst) and real_chars(open(dst, encoding="utf-8", errors="replace").read()) >= 200:
                log.append({"stem": stem, "format": "scanned",
                            "extraction_method": "tesseract OCR @300dpi (no text layer)"})
                continue
            sys.stderr.write(f"OCR {stem}\n")
            txt = ocr(pdf)
            fmt, meth = "scanned", "tesseract OCR @300dpi (no text layer)"
        open(dst, "w", encoding="utf-8").write(txt)
        log.append({"stem": stem, "format": fmt, "extraction_method": meth})

    for fn in sorted(glob.glob(os.path.join(HERE, "raw", "pmn", "notice_*.html"))):
        stem = os.path.splitext(os.path.basename(fn))[0]
        t = open(fn, encoding="utf-8", errors="replace").read()
        t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
        t = re.sub(r"<[^>]+>", " ", t)
        t = re.sub(r"[ \t]+", " ", html.unescape(t))
        i = t.find("Description/Agenda")
        j = t.find("Notice of Special Accommodations")
        body = t[i + len("Description/Agenda"):j].strip() if 0 <= i < j else t
        body = re.sub(r"\n\s*\n+", "\n\n", body).strip()
        open(os.path.join(TEXT, stem + ".txt"), "w", encoding="utf-8").write(
            "PMN RECORDER ADOPTION NOTICE (summary only - not the full ordinance text)\n\n"
            + body + "\n")
        log.append({"stem": stem, "format": "html",
                    "extraction_method": "html-strip (PMN notice Description/Agenda)"})

    with open(os.path.join(TEXT, "_extraction_log.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stem", "format", "extraction_method"])
        w.writeheader()
        w.writerows(log)
    n_ocr = sum(1 for r in log if r["format"] == "scanned")
    print(f"{len(log)} sidecars ({n_ocr} OCR)")

if __name__ == "__main__":
    main()
