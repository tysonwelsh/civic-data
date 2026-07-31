#!/usr/bin/env python3
"""Convert Town of Alta raw minutes PDFs -> cleaned markdown + minutes_index.csv.

Deterministic. Born-digital PDFs -> pdftotext -layout. Image-only scans -> OCR
(pdftoppm 300dpi + tesseract), cached in <body>/raw_text/<slug>.txt for resume.
Writes <body>/minutes/<year>/<week-monday>/<date>_<slug>.md with a provenance header,
and <body>/minutes_index.csv (8-col standard, source=pmn).
Resumable: skips a meeting whose .md already exists.
"""
import subprocess, os, sys, json, csv, re, glob, tempfile
from datetime import date, timedelta

ROOT = "/Users/tysonwelsh/civic-data/alta_city_council"
SCRATCH = "/private/tmp/claude-501/-Users-tysonwelsh-civic-data/fda1bfdf-21b1-423c-99e2-e46b5a13a615/scratchpad"
PT = "/opt/homebrew/bin/pdftotext"
PTOPPM = "/opt/homebrew/bin/pdftoppm"
TESS = "/opt/homebrew/bin/tesseract"

CFG = {
    "council": {"dir": f"{ROOT}/meeting_minutes", "manifest": f"{SCRATCH}/final_council.json",
                "title_body": "Alta Town Council"},
    "pc": {"dir": f"{ROOT}/planning_commission", "manifest": f"{SCRATCH}/final_pc.json",
           "title_body": "Alta Planning Commission"},
}

def week_monday(iso):
    y, m, d = map(int, iso.split("-"))
    dt = date(y, m, d)
    return (dt - timedelta(days=dt.weekday())).isoformat()

def is_image_only(pdf):
    out = subprocess.run([PT, "-layout", pdf, "-"], capture_output=True, text=True).stdout
    return len(out.strip()) < 200

def ocr_pdf(pdf, cache):
    if os.path.exists(cache) and os.path.getsize(cache) > 50:
        return open(cache, encoding="utf-8", errors="replace").read()
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "pg")
        subprocess.run([PTOPPM, "-r", "300", "-gray", "-png", pdf, base],
                       check=True, timeout=1200)
        pngs = sorted(glob.glob(base + "*.png"))
        parts = []
        for png in pngs:
            r = subprocess.run([TESS, png, "-", "--psm", "6"],
                               capture_output=True, text=True, timeout=300)
            parts.append(r.stdout)
    txt = "\n".join(parts)
    open(cache, "w", encoding="utf-8").write(txt)
    return txt

def get_text(pdf, cache):
    if is_image_only(pdf):
        return ocr_pdf(pdf, cache), "ocr"
    return subprocess.run([PT, "-layout", pdf, "-"], capture_output=True, text=True).stdout, "pdf-text"

def clean(txt):
    # normalize dashes/quotes, drop bare form-feed
    txt = txt.replace("\x0c", "\n")
    lines = [ln.rstrip() for ln in txt.split("\n")]
    # collapse >2 blank lines
    out = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(ln)
    return "\n".join(out).strip() + "\n"

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    tags = ["council", "pc"] if which == "both" else [which]
    force = "--force" in sys.argv
    for tag in tags:
        cfg = CFG[tag]
        d = cfg["dir"]
        rows = json.load(open(cfg["manifest"]))
        os.makedirs(f"{d}/minutes", exist_ok=True)
        os.makedirs(f"{d}/raw_text", exist_ok=True)
        index = []
        made = skipped = ocred = 0
        for dt, mtype, fn, fid in rows:
            slug_fn = re.sub(r'\.pdf$', '', fn, flags=re.I)
            slug_fn = re.sub(r'[^A-Za-z0-9]+', '_', slug_fn).strip('_').lower()[:70]
            slug = f"{dt}_{slug_fn}"
            raw = f"{d}/raw/{slug}.pdf"
            if not os.path.exists(raw):
                print("MISSING RAW", raw, file=sys.stderr); continue
            wk = week_monday(dt)
            year = dt[:4]
            md_dir = f"{d}/minutes/{year}/{wk}"
            md_path = f"{md_dir}/{slug}.md"
            rel = os.path.relpath(md_path, d)
            title = f"{cfg['title_body']} — {mtype.title()} Meeting {dt}"
            src_url = f"https://www.utah.gov/pmn/files/{fid}.pdf"
            if os.path.exists(md_path) and not force:
                skipped += 1
                # still record index from existing
                fmt = "ocr" if os.path.exists(f"{d}/raw_text/{slug}.txt") else "pdf-text"
                index.append([dt, year, title, slug, rel, "pmn", src_url, fmt])
                continue
            cache = f"{d}/raw_text/{slug}.txt"
            text, fmt = get_text(raw, cache)
            if fmt == "ocr":
                ocred += 1
            body_md = clean(text)
            os.makedirs(md_dir, exist_ok=True)
            header = (f"---\n"
                      f"title: {title}\n"
                      f"date: {dt}\n"
                      f"meeting_type: {mtype}\n"
                      f"body: {'Council' if tag=='council' else 'PlanningCommission'}\n"
                      f"source: pmn\n"
                      f"source_url: {src_url}\n"
                      f"source_file: {fn}\n"
                      f"pmn_file_id: {fid}\n"
                      f"format: {fmt}\n"
                      f"---\n\n")
            open(md_path, "w", encoding="utf-8").write(header + body_md)
            index.append([dt, year, title, slug, rel, "pmn", src_url, fmt])
            made += 1
            print(f"  [{tag}] {slug}  ({fmt})")
        # write index
        idx_path = f"{d}/minutes_index.csv"
        with open(idx_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "year", "title", "slug", "path", "source", "source_url", "format"])
            for r in sorted(index, key=lambda x: (x[0], x[3])):
                w.writerow(r)
        print(f"{tag}: made={made} skipped={skipped} ocr={ocred} indexed={len(index)}")

if __name__ == "__main__":
    main()
