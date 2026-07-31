#!/usr/bin/env python3
"""Text sidecars for draper ordinances/raw/pmn/ — idempotent, offline.

- Every attachment PDF (raw/pmn/ord*_n<nid>_f<fid>.pdf) gets text/<stem>.txt via
  `pdftotext -layout`; if the yield is under MIN_CHARS the page is rendered at
  300dpi and OCR'd with tesseract (labeled per stem in text/_extraction_log.csv).
  NOTE: tesseract in this sandbox cannot read /tmp — intermediate PNGs go to a
  local work dir under text/ and are removed afterward.
- Adoption notices with NO PDF attachment get text/notice_<id>.txt stripped from
  the retained notice HTML (the Recorder's summary text; labeled html-strip).

Run: python3 extract_text.py   (from anywhere; paths are absolute)
"""
import csv, glob, html as h, os, re, subprocess, sys

BASE = "/Users/tysonwelsh/civic-data/draper_city_council/ordinances"
RAW = BASE + "/raw/pmn"
TXT = BASE + "/text"
MIN_CHARS = 200

os.makedirs(TXT, exist_ok=True)
log_path = TXT + "/_extraction_log.csv"
log = {}
if os.path.exists(log_path):
    for r in csv.DictReader(open(log_path)):
        log[r["stem"]] = r

def note(stem, fmt, method, chars):
    log[stem] = {"stem": stem, "format": fmt, "extraction_method": method,
                 "chars": str(chars)}

def pdftotext(pdf):
    p = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""

def ocr(pdf, stem):
    work = TXT + "/_ocr_work"
    os.makedirs(work, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "300", "-png", pdf, work + "/pg"],
                   check=True)
    parts = []
    for png in sorted(glob.glob(work + "/pg*.png")):
        p = subprocess.run(["tesseract", png, "stdout"],
                           capture_output=True, text=True)
        parts.append(p.stdout)
        os.remove(png)
    return "\n".join(parts)

def strip_html(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    i = t.find('class="agenda"')
    seg = t[i:i + 10000] if i >= 0 else t
    j = seg.find("Notice of Special Accommodations")
    seg = seg[:j if j > 0 else 8000]
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", seg, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|li|tr|h\d)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = h.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*", "\n", s).strip()
    s = re.sub(r'^class="agenda">\s*', "", s)
    return s

def main():
    done = ocr_n = pdf_n = html_n = 0
    for pdf in sorted(glob.glob(RAW + "/ord*_n*_f*.pdf")):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        out = TXT + "/" + stem + ".txt"
        if os.path.exists(out) and stem in log:
            done += 1
            continue
        txt = pdftotext(pdf)
        if len(txt.strip()) >= MIN_CHARS:
            open(out, "w").write(txt)
            note(stem, "text", "pdftotext -layout", len(txt))
            pdf_n += 1
        else:
            txt = ocr(pdf, stem)
            open(out, "w").write(txt)
            note(stem, "scanned", "tesseract 5 OCR @300dpi", len(txt))
            ocr_n += 1
    # HTML-only adoption notices (no PDF attachment): sidecar from notice HTML.
    # Which notices lack a PDF is derived from the raws themselves.
    # 785825/1007201: the attached PDF is a Recorder mis-upload of the sibling
    # ordinance's notice (see build_index.py ATTACHMENT_MISMATCH) — force the
    # HTML sidecar so the row's correct body text is extracted.
    have_pdf_nids = {re.search(r"_n(\d+)_f", p).group(1)
                     for p in glob.glob(RAW + "/ord*_n*_f*.pdf")}
    have_pdf_nids -= {"785825", "1007201"}
    for nh in sorted(glob.glob(RAW + "/notice_*.html")):
        nid = re.search(r"notice_(\d+)\.html", nh).group(1)
        if nid in have_pdf_nids:
            continue
        body = strip_html(nh)
        if not re.search(r"Notice of (Ordinance )?Adoption|[Aa]dopted|[Aa]pproved Ordinance",
                         body[:400]):
            continue  # hearing/other notices get no sidecar
        stem = "notice_" + nid
        out = TXT + "/" + stem + ".txt"
        if os.path.exists(out) and stem in log:
            done += 1
            continue
        open(out, "w").write(
            "RECORDER ADOPTION NOTICE (summary only — the full ordinance text "
            "is not attached on PMN)\n\n" + body)
        note(stem, "html", "html-strip", len(body))
        html_n += 1
    with open(log_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stem", "format", "extraction_method", "chars"])
        w.writeheader()
        for k in sorted(log):
            w.writerow(log[k])
    print(f"sidecars: {pdf_n} pdftotext, {ocr_n} OCR, {html_n} html-strip, "
          f"{done} already present; log -> {log_path}")

if __name__ == "__main__":
    main()
