#!/usr/bin/env python3
"""Convert Bluffdale raw minutes (PDF text layer / scanned PDF / DOCX) -> markdown.

Resumable: skips any doc whose markdown already exists. OCR runs SYNCHRONOUSLY, one
document at a time, deleting each doc's temp PNGs immediately. Prints a progress line
per doc. Also (re)writes each body's minutes_index.csv from what is on disk.

Categories (auto-detected):
  docx  -> textutil -convert txt         (format=text, born-digital Word)
  text  -> pdftotext -layout             (format=text, embedded text layer)
  ocr   -> pdftoppm -r 300 png + tesseract  (format=ocr, scanned image)
"""
import csv, glob, os, re, subprocess, sys, tempfile, shutil
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import json
MANIFEST = json.load(open(ROOT.parent / "bluffdale_city_council" / "_manifest.json")) \
    if (ROOT / "_manifest.json").exists() else json.load(open("/private/tmp/claude-501/-Users-tysonwelsh-civic-data/fda1bfdf-21b1-423c-99e2-e46b5a13a615/scratchpad/enum/manifest.json"))
META = {(r["body"], r["date"], r["id"]): r for r in MANIFEST}

BODY_DIR = {"council": ROOT / "meeting_minutes", "pc": ROOT / "planning_commission"}


def week_monday(iso):
    y, m, d = map(int, iso.split("-"))
    dt = date(y, m, d)
    return (dt - timedelta(days=dt.weekday())).isoformat()


def detect(fpath):
    with open(fpath, "rb") as fh:
        head = fh.read(4)
    if head[:2] == b"PK":
        return "docx"
    n = len(subprocess.run(["pdftotext", "-layout", fpath, "-"],
                           capture_output=True, text=True).stdout.strip())
    return "text" if n >= 200 else "ocr"


def convert_text(fpath):
    return subprocess.run(["pdftotext", "-layout", fpath, "-"],
                          capture_output=True, text=True).stdout


def convert_docx(fpath):
    # textutil needs a .docx extension to sniff the type
    tmp = fpath + ".docx"
    shutil.copy(fpath, tmp)
    try:
        out = subprocess.run(["textutil", "-convert", "txt", "-stdout", tmp],
                             capture_output=True, text=True).stdout
    finally:
        os.remove(tmp)
    return out


def convert_ocr(fpath):
    tdir = tempfile.mkdtemp(prefix="blf_ocr_")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", fpath, os.path.join(tdir, "p")],
                       check=False, capture_output=True)
        pages = sorted(glob.glob(os.path.join(tdir, "p*.png")))
        if not pages:
            raise RuntimeError(f"pdftoppm produced no pages for {fpath}")
        chunks = []
        for pg in pages:
            r = subprocess.run(["tesseract", pg, "-", "--psm", "6"],
                               capture_output=True, text=True)
            chunks.append(r.stdout)
        return "\n\n".join(chunks)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)  # delete PNGs immediately


def process():
    todo = []
    for body in ("council", "pc"):
        for f in sorted(glob.glob(str(BODY_DIR[body] / "raw" / f"{body}_*.pdf"))):
            base = os.path.basename(f)[:-4]                # council_2024-01-10_1331
            _, iso, iid = base.split("_")
            wk = week_monday(iso)
            y = iso[:4]
            outdir = BODY_DIR[body] / "minutes" / y / wk
            md = outdir / f"{base}.md"
            todo.append((body, f, base, iso, iid, y, wk, md))

    total = len(todo)
    done = sum(1 for t in todo if t[7].exists())
    print(f"{total} docs; {done} already converted; {total-done} to do", flush=True)
    ocr_budget = int(os.environ.get("OCR_BATCH", "10000"))
    ocr_used = 0

    for k, (body, f, base, iso, iid, y, wk, md) in enumerate(todo, 1):
        if md.exists():
            continue
        fmt = detect(f)
        if fmt == "ocr":
            if ocr_used >= ocr_budget:
                continue
            ocr_used += 1
        if fmt == "docx":
            text = convert_docx(f); fmt = "text"; engine = "textutil-docx"
        elif fmt == "text":
            text = convert_text(f); engine = "pdftotext"
        else:
            print(f"  [{k}/{total}] OCR {base} ...", flush=True)
            text = convert_ocr(f); engine = "tesseract-ocr"
        meta = META.get((body, iso, iid), {})
        title = meta.get("title", "").strip() or f"{body} meeting {iso}"
        url = meta.get("url", "")
        md.parent.mkdir(parents=True, exist_ok=True)
        hdr = (f"# {iso} {title}\n"
               f"> Source: {url}\n"
               f"> Meeting date: {iso}\n"
               f"> Body: {'City Council' if body=='council' else 'Planning Commission'}\n"
               f"> Format: {fmt} ({engine})\n\n---\n\n")
        md.write_text(hdr + text, encoding="utf-8")
        print(f"  [{k}/{total}] {fmt:4s} {base} -> {md.relative_to(ROOT)} ({len(text)} chars)", flush=True)

    build_indexes()


def build_indexes():
    for body in ("council", "pc"):
        bd = BODY_DIR[body]
        rows = []
        for md in sorted((bd / "minutes").rglob("*.md")):
            base = md.stem
            _, iso, iid = base.split("_")
            meta = META.get((body, iso, iid), {})
            txt = md.read_text(encoding="utf-8")
            fmt = "ocr" if "Format: ocr" in txt else "text"
            rows.append(dict(date=iso, year=iso[:4], title=meta.get("title", ""),
                             slug=base, path=str(md.relative_to(bd)),
                             source="civicplus", source_url=meta.get("url", ""),
                             format=fmt))
        rows.sort(key=lambda r: (r["date"], r["slug"]))
        idx = bd / "minutes_index.csv"
        with idx.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["date", "year", "title", "slug", "path",
                                               "source", "source_url", "format"])
            w.writeheader(); w.writerows(rows)
        print(f"{body}: wrote {idx} ({len(rows)} rows; ocr={sum(1 for r in rows if r['format']=='ocr')})")


if __name__ == "__main__":
    process()
