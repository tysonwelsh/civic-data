#!/usr/bin/env python3
"""Convert retained Millcreek PC minutes PDFs (raw/<year>/) -> markdown.
Resumable + parallel. pdftotext -layout for text layer (format=pdf-text);
image-only scans -> pdftoppm+tesseract OCR (format=ocr). Preserves garble verbatim.
Builds minutes_index.csv, checks body-hash dups (decoy) + date-in-body.
NO vote extraction.
"""
import csv, glob, hashlib, json, os, re, subprocess, datetime, tempfile
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
LINKS = json.load(open(os.path.join(ROOT, "_pc_links.json")))
TITLE = {}
from collections import Counter as _C
_DATE_DOCS = _C()
for yr, mmdd, docid, label in LINKS:
    iso = f"{mmdd[4:8]}-{mmdd[0:2]}-{mmdd[2:4]}"
    TITLE[(iso, docid)] = label
    _DATE_DOCS[iso] += 1
LOWTEXT = 800

def slug_for(iso, docid):
    # unique slug: append docid only when a date has multiple distinct meetings
    return "planning-commission" + (f"-{docid}" if _DATE_DOCS[iso] > 1 else "")

def week_monday(iso):
    d = datetime.date.fromisoformat(iso)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def clean_title(label):
    t = re.sub(r"\.\s*Minutes\s*$", "", label).strip()
    t = re.sub(r"\s*\((?:PDF|No Agenda)\)\.?$", "", t).strip().rstrip(".")
    t = re.sub(r"^[A-Z][a-z]+ \d{1,2}, \d{4},\s*", "", t)
    return t or "Planning Commission Meeting"

def pdftext(f):
    return subprocess.run(["pdftotext", "-layout", f, "-"],
                          capture_output=True, timeout=300).stdout.decode("utf-8", "replace")

def ocr(f):
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-png", "-r", "200", f, os.path.join(td, "p")],
                       check=True, timeout=1800)
        for png in sorted(glob.glob(os.path.join(td, "p*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(out)

def process(f):
    base = os.path.basename(f)
    m = re.match(r"(\d{4}-\d{2}-\d{2})_pc_(\d+)\.pdf$", base)
    iso, docid = m.group(1), m.group(2)
    yr = iso[:4]; wk = week_monday(iso)
    slug = slug_for(iso, docid)
    mdpath = os.path.join(ROOT, "minutes", yr, wk, f"{iso}_{slug}.md")
    if os.path.exists(mdpath):
        raw = open(mdpath, encoding="utf-8", errors="replace").read()
        fmt = "ocr" if re.search(r"\*\*Format:\*\* ocr", raw) else "pdf-text"
        body = raw.split("\n---\n\n", 1)[-1]
        if len(body.strip()) >= 40:
            return (iso, docid, fmt, body, mdpath, True)
    txt = pdftext(f); fmt = "pdf-text"
    if len(txt.strip()) < LOWTEXT:
        txt = ocr(f); fmt = "ocr"
    title = clean_title(TITLE.get((iso, docid), "Planning Commission Meeting"))
    write_md(iso, docid, fmt, txt, mdpath, title)  # persist immediately (timeout-safe)
    return (iso, docid, fmt, txt, mdpath, False)

def write_md(iso, docid, fmt, txt, mdpath, title):
    os.makedirs(os.path.dirname(mdpath), exist_ok=True)
    src = (f"https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/"
           f"_{iso[5:7]}{iso[8:10]}{iso[:4]}-{docid}")
    header = (f"# Millcreek Planning Commission — {iso}\n\n"
              f"- **Title:** {title}\n- **Date:** {iso}\n- **Body:** Planning Commission\n"
              f"- **Source:** civicplus AgendaCenter — {src}\n"
              f"- **Format:** {fmt} (source OCR garble preserved verbatim)\n\n---\n\n")
    with open(mdpath, "w") as fh:
        fh.write(header + txt.rstrip() + "\n")

def main():
    pdfs = sorted(glob.glob(os.path.join(ROOT, "raw", "*", "*.pdf")))
    results = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        for r in ex.map(process, pdfs):
            results.append(r)
    rows = []; bodyhash = {}; report = []
    for iso, docid, fmt, txt, mdpath, existed in results:
        title = clean_title(TITLE.get((iso, docid), "Planning Commission Meeting"))
        rel = os.path.relpath(mdpath, ROOT)
        src = (f"https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/"
               f"_{iso[5:7]}{iso[8:10]}{iso[:4]}-{docid}")
        norm = re.sub(r"\s+", " ", txt).strip().lower()
        bh = hashlib.sha256(norm.encode()).hexdigest()
        bodyhash.setdefault(bh, []).append((iso, docid))
        d = datetime.date.fromisoformat(iso)
        mon = d.strftime("%B")
        date_ok = bool(re.search(rf"{mon}\s+0?{d.day}\D{{0,4}}{d.year}", txt, re.I))
        loose_ok = (mon.lower() in txt.lower() and str(d.year) in txt)
        rows.append([iso, iso[:4], title, slug_for(iso, docid), rel, "civicplus", src, fmt, docid, bh[:12]])
        report.append((iso, docid, fmt, len(txt.strip()),
                       "OK" if date_ok else ("LOOSE" if loose_ok else "MISSING")))
    rows.sort(key=lambda r: (r[0], r[8]))
    with open(os.path.join(ROOT, "minutes_index.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "year", "title", "slug", "path", "source", "source_url", "format"])
        for r in rows:
            w.writerow(r[:8])
    from collections import Counter
    print("=== DUP BODY HASHES (decoy check) ===")
    dups = {k: v for k, v in bodyhash.items() if len(v) > 1}
    if not dups:
        print("  none")
    for k, v in dups.items():
        print(" ", k[:12], v)
    print("=== DATE-IN-BODY not-strict ===")
    for iso, docid, fmt, n, ds in report:
        if ds != "OK":
            print(" ", iso, docid, fmt, "chars", n, ds)
    print("=== FORMAT SPLIT ===", dict(Counter(r[7] for r in rows)))
    print("=== BY YEAR ===", dict(sorted(Counter(r[1] for r in rows).items())))
    print("total index rows:", len(rows))

if __name__ == "__main__":
    main()
