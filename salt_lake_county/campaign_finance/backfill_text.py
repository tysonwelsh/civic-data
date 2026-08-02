#!/usr/bin/env python3
"""Write text/ sidecars for the acquired PDFs and a text_extraction.csv manifest.

Two tiers:
  - born-digital PDFs (have a font layer) -> `pdftotext -layout` (fast, high quality).
  - image-only scans -> `tesseract` OCR at 300dpi, but ONLY when --ocr is passed AND the
    channel is enabled (default: legacy only — the irreplaceable historical record). The
    EasyVote redacted images are DEFERRED to the planned vision follow-up because their
    money data already lives in the STRUCTURED API layer (contributions/expenditures.csv).

Usage:
  python3 backfill_text.py                 # pdftotext all; manifest; no OCR
  python3 backfill_text.py --ocr legacy    # + tesseract OCR the legacy scans
  python3 backfill_text.py --ocr all       # + OCR every scan (slow)
"""
import os, sys, csv, subprocess, glob, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(HERE, "text")
os.makedirs(TEXT, exist_ok=True)


def has_font(p):
    try:
        out = subprocess.run(["pdffonts", p], capture_output=True, text=True, timeout=30).stdout
        return len([l for l in out.splitlines()[2:] if l.strip()]) > 0
    except Exception:
        return False


def pdftotext(p):
    try:
        r = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True, timeout=60)
        return r.stdout
    except Exception:
        return ""


def ocr(p):
    try:
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "pg")
            subprocess.run(["pdftoppm", "-r", "300", "-png", p, base], timeout=300, check=True)
            texts = []
            for png in sorted(glob.glob(base + "*.png")):
                r = subprocess.run(["tesseract", png, "-", "--psm", "6"], capture_output=True, text=True, timeout=180)
                texts.append(r.stdout)
            return "\n".join(texts)
    except Exception as e:
        return ""


def main():
    ocr_mode = None
    if "--ocr" in sys.argv:
        i = sys.argv.index("--ocr")
        ocr_mode = sys.argv[i + 1] if i + 1 < len(sys.argv) else "legacy"

    manifest = []
    for channel, subdir in [("clerk_legacy", "raw/clerk_legacy"), ("easyvote", "raw/easyvote")]:
        for p in sorted(glob.glob(os.path.join(HERE, subdir, "*.pdf"))):
            name = os.path.basename(p)
            sidecar = f"{channel}__{name.replace('.pdf', '.txt')}"
            sp = os.path.join(TEXT, sidecar)
            born = has_font(p)
            txt = ""
            method = ""
            if born:
                txt = pdftotext(p)
                method = "pdftotext -layout"
            else:
                # scanned: pdftotext usually empty; try it (some have partial), else OCR
                txt = pdftotext(p).strip()
                if txt:
                    method = "pdftotext -layout (partial)"
                elif ocr_mode == "all" or (ocr_mode == "legacy" and channel == "clerk_legacy"):
                    txt = ocr(p)
                    method = "tesseract OCR (pdftoppm 300dpi)"
                else:
                    method = "DEFERRED (image-only; vision follow-up planned)"
            nchars = len(txt.strip())
            if nchars > 0:
                open(sp, "w").write(txt)
            manifest.append({"channel": channel, "path": os.path.join(subdir, name),
                             "sidecar": ("text/" + sidecar) if nchars > 0 else "",
                             "format": "text" if born else "scanned",
                             "extraction_method": method, "n_chars": nchars,
                             "has_text": "yes" if nchars > 0 else "no"})
    with open(os.path.join(HERE, "text_extraction.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["channel", "path", "sidecar", "format",
                                           "extraction_method", "n_chars", "has_text"])
        w.writeheader()
        w.writerows(manifest)
    import collections
    print("sidecars written:", sum(1 for m in manifest if m["has_text"] == "yes"), "/", len(manifest))
    print("by format:", dict(collections.Counter(m["format"] for m in manifest)))
    print("by method:", dict(collections.Counter(m["extraction_method"] for m in manifest)))


if __name__ == "__main__":
    main()
