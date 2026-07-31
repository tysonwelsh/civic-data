#!/usr/bin/env python3
"""Harvest Utah County Board of Commissioners MINUTES -> markdown corpus + index.

Utah County has NO Legistar/Granicus vote API (recon.md). The commission runs a bespoke
Next.js portal whose JSON API drives the archive dropdown:

    GET https://commission.utahcounty.gov/api/meetings/archive?year=<YYYY>&type=CM
        -> [{filename, file_descr, min_year, min_category, audiofile, ...}]
    PDF: https://www.utahcounty.gov/dept/commish/data/minutes/<min_category>/<min_year>/<filename>

Vote grammar is ERA-SPLIT (recon.md):
  * 2015-2016 : BORN-DIGITAL pdf, NAMED roll ("AYE: <names> / NAY: <names>")
  * 2017+     : SCANNED images (OCR), TALLY-ONLY (mover/seconder named, "ALL IN FAVOR: AYE"
                / "Result: Motion passed 2/0").

So this fetcher extracts born-digital text with pypdf, and OCRs (pdftoppm 200dpi +
tesseract, pages in parallel) any PDF whose text layer is empty. Attachments/exhibits
(*ATTACH*, .pptx/.jpg/.png/.docx) are EXCLUDED; multi-part meeting minutes (Part1..N) are
concatenated into one markdown. Writes:

    legislative/minutes/<year>/<date>_<bodyslug>.md   (+ provenance front-matter)
    legislative/minutes_index.csv                     (human index)
    legislative/minutes/_catalog.csv                  (machine catalog for extract_votes.py)

DERIVED + idempotent (skips PDFs already downloaded and markdown already written unless
--force). Floor: FLOOR_DATE (2015-01-01).
"""
import csv, io, json, os, re, subprocess, sys, tempfile, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
MODULE = os.path.join(COUNTY, "legislative")
RAW = os.path.join(MODULE, "raw")
API = "https://commission.utahcounty.gov/api/meetings/archive?year=%d&type=CM"
PDFBASE = "https://www.utahcounty.gov/dept/commish/data/minutes/%s/%s/%s"
FLOOR_DATE = "2015-01-01"
YEARS = (range(int(os.environ["UC_Y0"]), int(os.environ["UC_Y1"]) + 1)
         if os.environ.get("UC_Y0") else range(2015, 2027))
UA = {"User-Agent": "Mozilla/5.0 civic-data/1.0"}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}
FORCE = "--force" in sys.argv


def http(url, binary=True):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read() if binary else r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == 3:
                print("  ! fetch failed:", url, repr(e)[:80]); return None
            time.sleep(2 * (i + 1))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def is_attachment(fn, desc):
    t = (fn + " " + desc)
    if re.search(r"attach|exhibit|presentation|overview\b", t, re.I):
        return True
    if os.path.splitext(fn)[1].lower() not in (".pdf",):
        return True
    return False


def parse_date(desc, fn):
    m = re.search(r"(january|february|march|april|may|june|july|august|september|"
                  r"october|november|december)\s+(\d{1,2}),?\s+(\d{4})", desc, re.I)
    if m:
        d = "%04d-%02d-%02d" % (int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
        # The county's own file_descr carries typos. "07.16.2019CommissionMeetingMinutes.pdf"
        # is described as "July 16, 2029", which would file a 2019 meeting ten years in the
        # future. When the FILENAME carries a year and the two disagree, the filename wins
        # (it is the document's own identifier, and the URL path repeats it).
        fy = re.search(r"(?:^|\D)(20[0-2]\d)(?:\D|$)", fn)
        if fy and fy.group(1) != m.group(3):
            d = "%s-%02d-%02d" % (fy.group(1), MONTHS[m.group(1).lower()], int(m.group(2)))
        return d
    m = re.match(r"(\d{2})[.](\d{2})[.](\d{4})", fn)          # MM.DD.YYYY
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
    m = re.match(r"(\d{2})(\d{2})(\d{2})[-A-Za-z]", fn)       # MMDDYY-
    if m:
        return "20%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
    return None


def body_of(desc, fn):
    t = desc + " " + fn
    if re.search(r"work session|budget work|worksession|budget retreat", t, re.I):
        return "Commission Work Session"
    return "Board of Commissioners"


def is_special(desc, fn):
    return bool(re.search(r"special", desc + " " + fn, re.I))


def part_no(fn):
    m = re.search(r"part\s*(\d+)", fn, re.I)
    return int(m.group(1)) if m else 1


def ocr_pdf(pdf_path):
    """OCR a scanned PDF: pdftoppm 200dpi -> tesseract per page (parallel)."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "200", "-png", pdf_path, os.path.join(td, "p")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pngs = sorted(p for p in os.listdir(td) if p.endswith(".png"))
        def ocr1(png):
            r = subprocess.run(["tesseract", os.path.join(td, png), "stdout", "--psm", "4"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            return r.stdout.decode("utf-8", "replace")
        with ThreadPoolExecutor(max_workers=8) as ex:
            texts = list(ex.map(ocr1, pngs))
    return "\n".join(texts), len(pngs)


def extract_text(pdf_path):
    """Return (text, method, npages). Born-digital via pypdf; OCR if text layer empty."""
    try:
        reader = PdfReader(pdf_path)
        npages = len(reader.pages)
        txt = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        txt, npages = "", 0
    if len(txt.strip()) >= 800:
        return txt, "minutes", npages          # born-digital primary
    txt, npages = ocr_pdf(pdf_path)
    return txt, "ocr_scan", npages


def main():
    os.makedirs(RAW, exist_ok=True)
    # 1. gather + classify all minutes docs, group by (date, body)
    groups = defaultdict(list)   # (date, body) -> list of doc dicts
    for y in YEARS:
        js = http(API % y, binary=False)
        if not js:
            continue
        for m in json.loads(js).get("meetings", []):
            fn = m["filename"]; desc = re.sub(r"\s+", " ", (m["file_descr"] or "")).strip()
            if is_attachment(fn, desc):
                continue
            date = parse_date(desc, fn)
            if not date or date < FLOOR_DATE:
                continue
            body = body_of(desc, fn)
            groups[(date, body)].append({
                "fn": fn, "desc": desc, "cat": m["min_category"], "yr": m["min_year"],
                "url": PDFBASE % (m["min_category"], m["min_year"], urllib.parse.quote(fn)),
                "part": part_no(fn), "special": is_special(desc, fn),
                "audio": m.get("audiofile") or ""})
    print("meeting-groups (date x body):", len(groups))

    idx_rows = []       # human minutes_index.csv
    cat_rows = []       # machine _catalog.csv
    n_born = n_ocr = n_fail = 0
    for (date, body), docs in sorted(groups.items()):
        # the archive API sometimes lists the SAME filename twice for a date — dedupe so a
        # duplicate entry never gets concatenated as a phantom "part" (would double the text)
        seen = set(); docs = [d for d in docs if not (d["fn"] in seen or seen.add(d["fn"]))]
        docs.sort(key=lambda d: d["part"])
        year = date[:4]
        md_dir = os.path.join(MODULE, "minutes", year)
        os.makedirs(md_dir, exist_ok=True)
        base = "%s_%s" % (date, slug(body))
        md_path = os.path.join(md_dir, base + ".md")
        rel = os.path.relpath(md_path, COUNTY)
        special = any(d["special"] for d in docs)
        if os.path.exists(md_path) and not FORCE:
            # re-read provenance/method from existing front-matter for the index
            head = open(md_path, encoding="utf-8").read(2000)
            meth = (re.search(r"extraction:\s*(\S+)", head) or [None, "minutes"])[1]
            src = (re.search(r"source_url:\s*(\S+)", head) or [None, docs[0]["url"]])[1]
            idx_rows.append([date, body, rel, src, "Final", "special" if special else ""])
            cat_rows.append([date, body, rel, meth, "special" if special else "", src])
            (n_ocr if meth == "ocr_scan" else n_born).__int__()  # no-op
            continue
        # download + extract each part, concatenate
        texts = []; methods = set(); urls = []; npages_tot = 0
        for d in docs:
            pdf = os.path.join(RAW, "%s_%s_%s" % (date, slug(body), d["fn"]))
            if not (os.path.exists(pdf) and os.path.getsize(pdf) > 1000):
                blob = http(d["url"])
                if not blob or len(blob) < 1000:
                    print("  ! download failed:", d["url"]); continue
                open(pdf, "wb").write(blob)
            txt, meth, npages = extract_text(pdf)
            texts.append(txt); methods.add(meth); urls.append(d["url"]); npages_tot += npages
        if not texts or not any(t.strip() for t in texts):
            n_fail += 1
            idx_rows.append([date, body, "", docs[0]["url"], "unrecovered", "text extraction failed"])
            continue
        # The county posts a one-page PLACEHOLDER for meetings whose minutes are not written
        # yet ("Meeting minutes file for this date/item is pending creation."). That is not a
        # minutes document — log the meeting as unrecovered rather than ingest an empty one.
        if re.search(r"minutes file for this date/item is pending creation", " ".join(texts), re.I):
            n_fail += 1
            idx_rows.append([date, body, "", docs[0]["url"], "unrecovered",
                             "county placeholder: minutes pending creation"])
            print("  %s %-24s PLACEHOLDER (minutes pending) — logged unrecovered" % (date, body))
            continue
        method = "ocr_scan" if "ocr_scan" in methods else "minutes"
        if method == "ocr_scan":
            n_ocr += 1
        else:
            n_born += 1
        body_txt = ("\n\n----PART BREAK----\n\n").join(texts)
        header = (
            "---\n"
            "jurisdiction: Utah County\n"
            "body: %s\n"
            "date: %s\n"
            "meeting_kind: %s\n"
            "source_url: %s\n"
            "source: commission.utahcounty.gov (archive API type=CM)\n"
            "extraction: %s\n"
            "n_parts: %d\n"
            "n_pages: %d\n"
            "audio: %s\n"
            "---\n\n" % (body, date, "special" if special else "regular",
                         " | ".join(urls),
                         "pypdf text (born-digital)" if method == "minutes" else "tesseract OCR (scanned)",
                         len(docs), npages_tot, docs[0]["audio"]))
        open(md_path, "w", encoding="utf-8").write(header + body_txt)
        idx_rows.append([date, body, rel, urls[0], "Final", "special" if special else ""])
        cat_rows.append([date, body, rel, method, "special" if special else "", urls[0]])
        print("  %s %-24s %s (%dp, %d part)" % (date, body, method, npages_tot, len(docs)))

    idx_rows.sort(key=lambda r: (r[0], r[1]))
    with open(os.path.join(MODULE, "minutes_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "source_url", "minutes_status", "note"])
        w.writerows(idx_rows)
    cat_rows.sort(key=lambda r: (r[0], r[1]))
    with open(os.path.join(MODULE, "minutes", "_catalog.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "body", "md_path", "provenance", "kind", "source_url"])
        w.writerows(cat_rows)
    print("DONE: born-digital=%d  OCR=%d  failed=%d  total_index=%d"
          % (n_born, n_ocr, n_fail, len(idx_rows)))


if __name__ == "__main__":
    main()
