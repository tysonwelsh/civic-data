#!/usr/bin/env python3
"""Build the text/ sidecar layer for washington_county/campaign_finance.

Three source shapes, three honest methods:
  * born-digital PDF   -> pdftotext -layout
  * image-only PDF     -> pdftoppm 200dpi + tesseract  (EVERY county PDF era is this)
  * .xls workbook      -> xlrd cell dump (2014-2015 era; the only born-structured material)

Writes text/<channel>__<stem>.txt and the manifest text_extraction.csv.
Idempotent: skips a sidecar that already exists and is non-empty.
Never writes outside campaign_finance/.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
TEXT = os.path.join(ROOT, "text")
# A PDF that carries embedded text FONTS is born-digital, however little text it holds --
# several of this county's born-digital tables are legitimately EMPTY (a candidate who
# reported no contributions), and OCR'ing them produced pure noise ("es es ee").  pdffonts
# is the discriminator; a character-count threshold is not.
def has_fonts(path):
    try:
        out = subprocess.run(["pdffonts", path], capture_output=True, timeout=60
                             ).stdout.decode("utf-8", "replace").splitlines()
        return len(out) > 2 and any(l.strip() for l in out[2:])
    except Exception:                                    # noqa: BLE001
        return False


def sidecar_name(channel, fname):
    stem = os.path.splitext(fname)[0]
    stem = re.sub(r"[^A-Za-z0-9._ ()@,;+-]", "_", stem)
    return f"{channel}__{stem}.txt"[:200]


def pdftotext(path):
    try:
        return subprocess.run(["pdftotext", "-layout", path, "-"],
                              capture_output=True, timeout=180).stdout.decode("utf-8", "replace")
    except Exception:                                    # noqa: BLE001
        return ""


def ocr(path):
    out = []
    with tempfile.TemporaryDirectory() as td:
        pre = os.path.join(td, "p")
        try:
            subprocess.run(["pdftoppm", "-r", "200", "-png", path, pre],
                           capture_output=True, timeout=900)
        except Exception:                                # noqa: BLE001
            return ""
        for png in sorted(os.listdir(td)):
            if not png.endswith(".png"):
                continue
            try:
                r = subprocess.run(["tesseract", os.path.join(td, png), "stdout", "--psm", "6"],
                                   capture_output=True, timeout=300)
                out.append(r.stdout.decode("utf-8", "replace"))
            except Exception:                            # noqa: BLE001
                pass
    return "\n\n".join(out)


def xls_dump(path):
    import xlrd
    book = xlrd.open_workbook(path, formatting_info=False)
    lines = []
    for sh in book.sheets():
        lines.append(f"### SHEET: {sh.name}  ({sh.nrows}x{sh.ncols})")
        for r in range(sh.nrows):
            cells = []
            for c in range(sh.ncols):
                v = sh.cell_value(r, c)
                if isinstance(v, float) and v == int(v):
                    v = int(v)
                cells.append(str(v).strip())
            if any(cells):
                lines.append("\t".join(cells))
    return "\n".join(lines)


def main():
    os.makedirs(TEXT, exist_ok=True)
    only = set(sys.argv[1:])
    rows = []
    for channel in sorted(os.listdir(RAW)):
        if only and channel not in only:
            continue
        cdir = os.path.join(RAW, channel)
        if not os.path.isdir(cdir):
            continue
        for fname in sorted(os.listdir(cdir)):
            if fname.startswith("_"):
                continue
            src = os.path.join(cdir, fname)
            out = os.path.join(TEXT, sidecar_name(channel, fname))
            head = open(src, "rb").read(8)
            is_pdf = head.startswith(b"%PDF")
            is_ole = head.startswith(b"\xd0\xcf\x11\xe0")          # legacy .xls (BIFF/OLE2)

            if os.path.exists(out) and os.path.getsize(out) > 0:
                txt = open(out, encoding="utf-8", errors="replace").read()
                fmt, meth = _label(src, txt, is_pdf, is_ole, cached=True)
            elif is_pdf:
                if has_fonts(src):
                    txt = pdftotext(src)
                    fmt, meth = "text", "pdftotext -layout"
                else:
                    txt = ocr(src)
                    fmt, meth = "scanned", "tesseract OCR (pdftoppm 200dpi, --psm 6)"
                open(out, "w", encoding="utf-8").write(txt)
            elif is_ole:
                try:
                    txt = xls_dump(src)
                    fmt, meth = "spreadsheet", "xlrd cell dump"
                except Exception as exc:                            # noqa: BLE001
                    txt, fmt, meth = "", "spreadsheet", f"xlrd FAILED: {exc}"
                open(out, "w", encoding="utf-8").write(txt)
            else:
                txt, fmt, meth = "", "unknown", "not attempted (unrecognised container)"
                open(out, "w", encoding="utf-8").write(txt)

            rows.append(dict(channel=channel, raw_path=f"raw/{channel}/{fname}",
                             text_path=f"text/{os.path.basename(out)}",
                             format=fmt, extraction_method=meth,
                             bytes=os.path.getsize(src),
                             text_chars=len(re.sub(r"\s", "", txt))))
            print(f"{fmt:12} {rows[-1]['text_chars']:>7}  {channel}/{fname}", flush=True)

    if only:                       # partial run: manifest is written by the full pass
        print(f"\n{len(rows)} sidecars (partial run, manifest NOT rewritten)")
        return
    with open(os.path.join(ROOT, "text_extraction.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} sidecars")


def _label(src, txt, is_pdf, is_ole, cached=False):
    if is_ole:
        return "spreadsheet", "xlrd cell dump"
    if not is_pdf:
        return "unknown", "not attempted (unrecognised container)"
    # a cached sidecar: re-derive which path produced it
    if has_fonts(src):
        return "text", "pdftotext -layout"
    return "scanned", "tesseract OCR (pdftoppm 200dpi, --psm 6)"


if __name__ == "__main__":
    sys.exit(main())
