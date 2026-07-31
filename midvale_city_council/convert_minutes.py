#!/usr/bin/env python3
"""Midvale (Revize) raw -> markdown converter with OCR fallback. Resumable.

For each raw file <date>_<slug>.<pdf|docx> in <body>/raw/: get text (docx via
textutil; pdf via pdftotext -layout, else OCR via pdftoppm+tesseract), wrap with
the staged header block the extractor expects, file under
minutes/<year>/<week-monday>/, and build minutes_index.csv. Corrupt PDFs are
gs-repaired or logged to minutes_unrecovered.csv. Skips markdown already written.

Usage: python3 convert_minutes.py <body_dir> <manifest.json> <City Council|Planning Commission>
"""
import os, sys, csv, re, json, subprocess, datetime, urllib.parse, tempfile, glob, shutil

BASE = "https://www.midvale.utah.gov/"

def full_url(href): return BASE + urllib.parse.quote(href, safe="/?=&:%")

def week_monday(d): return (d - datetime.timedelta(days=d.weekday())).isoformat()

def titleize(slug): return slug.replace("-", " ").title()

def pdftotext(p):
    r = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def ocr_pdf(p):
    tmp = tempfile.mkdtemp(prefix="mvocr_")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", p, os.path.join(tmp, "pg")],
                       capture_output=True, timeout=1200)
        out = []
        for png in sorted(glob.glob(os.path.join(tmp, "pg*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"], capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
        return "\n".join(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def get_text(path):
    """Return (text, format). format in {text, ocr}. Raises on unrecoverable."""
    if path.endswith(".docx"):
        r = subprocess.run(["textutil", "-convert", "txt", "-stdout", path], capture_output=True)
        return r.stdout.decode("utf-8", "replace"), "text"
    txt = pdftotext(path)
    if len(re.sub(r"\s", "", txt)) >= 200:
        return txt, "text"
    # scanned -> OCR (repair first if pdftoppm can't read it)
    try:
        otxt = ocr_pdf(path)
    except Exception:
        otxt = ""
    if len(re.sub(r"\s", "", otxt)) < 50:
        # attempt gs repair then re-OCR
        rp = path + ".repaired.pdf"
        subprocess.run(["gs", "-o", rp, "-sDEVICE=pdfwrite", path], capture_output=True, timeout=300)
        if os.path.exists(rp) and os.path.getsize(rp) > 0:
            otxt = ocr_pdf(rp)
            os.remove(rp)
    if len(re.sub(r"\s", "", otxt)) < 50:
        raise RuntimeError("unrecoverable (corrupt/blank scan)")
    return otxt, "ocr"

def main():
    body_dir, manifest, body_name = sys.argv[1], sys.argv[2], sys.argv[3]
    raw_dir = os.path.join(body_dir, "raw")
    man = json.load(open(manifest))
    url_by_date = {}
    for m in man:
        url_by_date.setdefault(m["date"], full_url(m["href"]))
    index, unrec = [], []
    files = sorted(f for f in os.listdir(raw_dir) if f.endswith((".pdf", ".docx"))
                   and not f.endswith(".repaired.pdf"))
    for i, fn in enumerate(files):
        m = re.match(r"(\d{4}-\d{2}-\d{2})_(.+)\.(pdf|docx)$", fn)
        if not m:
            continue
        date, slug, ext = m.group(1), m.group(2), m.group(3)
        d = datetime.date.fromisoformat(date)
        rel = f"minutes/{d.year}/{week_monday(d)}/{date}_{slug}.md"
        out = os.path.join(body_dir, rel)
        url = url_by_date.get(date, "")
        if os.path.exists(out) and os.path.getsize(out) > 400:
            hdrtxt = open(out, encoding="utf-8").read(600)
            fm = re.search(r"> Format:\s*(\w+)", hdrtxt)
            index.append(dict(date=date, year=d.year, title=titleize(slug), slug=slug,
                              path=rel, source="revize", source_url=url,
                              format=fm.group(1) if fm else "text"))
            continue
        try:
            text, fmt = get_text(os.path.join(raw_dir, fn))
        except Exception as e:
            unrec.append(dict(date=date, year=d.year, title=titleize(slug), body=body_name,
                              reason=str(e), raw=fn))
            print(f"  [{i+1}/{len(files)}] UNREC {fn}: {e}", flush=True)
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        hdr = (f"# {titleize(slug)}\n> Body: {body_name}\n> Meeting date: {date}\n"
               f"> Source: {url}\n> Source vendor: revize\n> Raw file: raw/{fn}\n"
               f"> Format: {fmt}\n> Retrieved: 2026-07-12\n\n---\n\n")
        open(out, "w", encoding="utf-8").write(hdr + text)
        index.append(dict(date=date, year=d.year, title=titleize(slug), slug=slug,
                          path=rel, source="revize", source_url=url, format=fmt))
        print(f"  [{i+1}/{len(files)}] {fmt} {rel}", flush=True)
    index.sort(key=lambda r: (r["date"], r["path"]))
    with open(os.path.join(body_dir, "minutes_index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","year","title","slug","path","source","source_url","format"])
        w.writeheader(); w.writerows(index)
    if unrec:
        with open(os.path.join(body_dir, "minutes_unrecovered.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date","year","title","body","reason","raw"])
            w.writeheader(); w.writerows(unrec)
    nocr = sum(1 for r in index if r["format"] == "ocr")
    print(f"DONE {body_name}: {len(index)} indexed ({nocr} ocr), {len(unrec)} unrecoverable", flush=True)

if __name__ == "__main__":
    main()
