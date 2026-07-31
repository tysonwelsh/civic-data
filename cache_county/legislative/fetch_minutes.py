#!/usr/bin/env python3
"""fetch_minutes.py — harvest Cache County Council minutes (floor 2015-01-01) from the
self-hosted CMS at cachecounty.gov into legislative/minutes/<year>/*.md with provenance
front-matter, plus minutes_index.csv and minutes_unrecovered.csv.

Cache County is NOT a hosted-vendor portal. Documents live at
  https://cachecounty.gov/assets/meetings/countycouncil/<year>/Minutes/<irregular>.pdf
Directory listings 403; the year `<select>` renders server-side at
  https://cachecounty.gov/countycouncil/countycouncil.html?year=<YYYY>
so this script scrapes each year page for the Minutes links (filenames are irregular and
must never be guessed).

TWO VOTE ERAS (see recon.md): born-digital NAMED roll calls (~2021+) vs scanned TALLY-ONLY
narrative (2015-2020). Detection is PER DOCUMENT by pdftotext char-density; scanned docs are
tesseract-OCR'd (front-matter `format: ocr`, `ocr: true`) and their vote layer is honestly
low-confidence tally-only. Raw PDFs are LINK-only (bundled media packets make them bulk);
the extracted text is embedded in the markdown as the searchable/provenance corpus.

Idempotent + resumable: existing markdown is skipped unless --force.

    python3 fetch_minutes.py --scan-only         # just (re)build the URL inventory
    python3 fetch_minutes.py --era born          # born-digital docs (pdftotext) only
    python3 fetch_minutes.py --era scanned --ocr  # scanned docs, OCR (slow); --page-cap N
    python3 fetch_minutes.py --ocr                # everything
"""
import argparse, csv, hashlib, html, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("CACHE_PDF_DIR", "")   # optional persistent PDF cache (scratchpad)
MIN_DIR = os.path.join(HERE, "minutes")
INDEX = os.path.join(HERE, "minutes_index.csv")
UNREC = os.path.join(HERE, "minutes_unrecovered.csv")
BASE = "https://cachecounty.gov"
YEAR_URL = BASE + "/countycouncil/countycouncil.html?year=%s"
YEARS = list(range(2015, 2027))
FLOOR = "2015-01-01"
UA = "Mozilla/5.0 (civic-data harvester; cache_county)"
DENSITY_BORN = 300      # >= chars/page => born-digital (text); else scanned (OCR)


def fetch_bytes(url, timeout=120):
    enc = urllib.parse.quote(url, safe=":/?=&%")
    req = urllib.request.Request(enc, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_with_fallback(url):
    """Return (bytes, provenance_suffix). Try the live CMS; on failure fall back to the
    Wayback Machine (the county's 2024 folder went dead on the live server — the born-digital
    originals survive only in web.archive.org). Raises on total failure."""
    try:
        return fetch_bytes(url), ""
    except Exception as e_live:
        # Wayback availability API -> raw-bytes snapshot (the `id_` modifier)
        import json as _json
        try:
            api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
            j = _json.loads(fetch_bytes(api, timeout=60).decode("utf-8", "replace"))
            snap = j.get("archived_snapshots", {}).get("closest")
            if snap and snap.get("available"):
                ts = snap["timestamp"]
                wb = "https://web.archive.org/web/%sid_/%s" % (ts, url)
                return fetch_bytes(wb, timeout=180), "wayback"
        except Exception:
            pass
        raise e_live


def scrape_year(y):
    """Return list of (year, abs_url, basename) minutes links from a year page.
    Retries: the self-hosted CMS intermittently drops connections under rapid sequential
    fetches (this once silently shrank the inventory 312->123), so retry with backoff."""
    import time
    h = None
    for attempt in range(4):
        try:
            h = fetch_bytes(YEAR_URL % y).decode("utf-8", "replace")
            break
        except Exception as e:
            if attempt == 3:
                print("  year %s scrape FAILED after retries: %s" % (y, e), file=sys.stderr)
                return []
            time.sleep(1.5 * (attempt + 1))
    if h is None:
        return []
    out = []
    for m in re.finditer(r'href="([^"]+\.[Pp][Dd][Ff])"', h):
        url = html.unescape(m.group(1)).replace("/./", "/")
        low = url.lower()
        if "minute" not in low:
            continue
        if any(k in low for k in ("agenda", "media", "packet")):
            continue
        absu = url if url.startswith("http") else BASE + "/" + url.lstrip("/")
        out.append((str(y), absu, os.path.basename(url)))
    return out


def inventory():
    seen, rows = set(), []
    for y in YEARS:
        for r in scrape_year(y):
            if r[1] in seen:
                continue
            seen.add(r[1])
            rows.append(r)
    return rows


DATE_PATS = [
    r"(\d{1,2})[-.](\d{1,2})[-.](\d{4})",     # MM-DD-YYYY / MM.DD.YYYY
    r"(\d{1,2})[-.](\d{1,2})[-.](\d{2})\b",    # MM-DD-YY
    r"(\d{4})[-.](\d{1,2})[-.](\d{1,2})",     # YYYY-MM-DD
]


def parse_date(basename, page_year):
    for i, pat in enumerate(DATE_PATS):
        m = re.search(pat, basename)
        if not m:
            continue
        a, b, c = m.groups()
        if i == 2:
            yr, mo, dy = int(a), int(b), int(c)
        elif i == 1:
            mo, dy, yr = int(a), int(b), 2000 + int(c)
        else:
            mo, dy, yr = int(a), int(b), int(c)
        if not (1 <= mo <= 12 and 1 <= dy <= 31 and 2010 <= yr <= 2027):
            continue
        return "%04d-%02d-%02d" % (yr, mo, dy)
    return None


def classify_body(basename):
    b = basename.lower()
    if "canvass" in b:
        return "BoardOfCanvassers"
    if "service area" in b or "service-area" in b:
        return "ServiceArea1"
    if "workshop" in b or "work session" in b or "workshop meeting" in b:
        return "Workshop"
    return "Council"


def doc_status(basename):
    b = basename.lower()
    for kw in ("finalized", "final", "approved", "amended", "signed", "draft", "combined"):
        if kw in b:
            return kw
    return ""


def slugbody(b):
    return re.sub(r"[^a-z0-9]+", "-", b.lower()).strip("-")


def pdf_pages(path):
    try:
        out = subprocess.check_output(["pdfinfo", path], stderr=subprocess.DEVNULL).decode()
        m = re.search(r"Pages:\s+(\d+)", out)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def pdftotext(path):
    try:
        out = subprocess.check_output(["pdftotext", "-layout", path, "-"],
                                      stderr=subprocess.DEVNULL)
        return out.decode("utf-8", "replace")
    except Exception:
        return ""


def ocr_pdf(path, pages, page_cap, dpi=150):
    """OCR up to page_cap pages (the minutes body precedes any appended media packet)."""
    n = min(pages, page_cap) if page_cap else pages
    texts = []
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", "1", "-l", str(n),
                            path, os.path.join(td, "p")],
                           check=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            return "", n, "ocr-render-failed:%s" % e
        for img in sorted(os.listdir(td)):
            if not img.endswith(".png"):
                continue
            try:
                t = subprocess.check_output(["tesseract", os.path.join(td, img), "stdout"],
                                            stderr=subprocess.DEVNULL).decode("utf-8", "replace")
                texts.append(t)
            except Exception:
                pass
    return "\n".join(texts), n, ""


FRONT = """---
# Cache County Council minutes — provenance
source_url: %(url)s
meeting_date: %(date)s
body: %(body)s
doc_status: %(status)s
format: %(fmt)s
ocr: %(ocr)s
pages: %(pages)s
ocr_pages: %(ocr_pages)s
text_chars: %(chars)s
extraction_confidence: %(conf)s
provenance: %(prov)s
harvested: 2026-07-20
---

# Cache County Council — %(body)s — %(date)s
> Source: %(url)s
> Format: %(fmt)s%(ocrnote)s

"""


def write_md(rec, text):
    year = rec["date"][:4]
    d = os.path.join(MIN_DIR, year)
    os.makedirs(d, exist_ok=True)
    base = "%s_%s" % (rec["date"], slugbody(rec["body"]))
    # idempotent + collision-safe: the file for THIS source_url is stable; a different
    # source_url on the same date+body (rare: amended vs approved) bumps a numeric suffix.
    # 2026-07-29 BUGFIX: this compared with `(\S+)`, which stops at the first SPACE — and
    # every Cache source_url contains spaces ("... 12-14-21 APPROVED sm.pdf"). The stored
    # url was therefore always truncated, the equality never held, and a re-fetch of an
    # ALREADY-PRESENT document wrote a `_2.md` second copy instead of overwriting in
    # place. 12 such orphans accumulated and (until extract_votes.py became index-driven)
    # double-counted 107 motions / 640 votes. Match the whole line.
    path = os.path.join(d, base + ".md")
    k = 2
    while os.path.exists(path):
        try:
            head = open(path, encoding="utf-8").read(600)
            m = re.search(r"(?m)^\s*source_url:[ \t]*(.+?)[ \t]*$", head)
            if m and m.group(1) == rec["url"]:
                break                      # same doc -> overwrite in place
        except Exception:
            pass
        path = os.path.join(d, "%s_%d.md" % (base, k))
        k += 1
    rel = os.path.relpath(path, os.path.dirname(HERE))
    ocrnote = ("  (OCR of first %s pages; minutes body precedes appended media packet)"
               % rec["ocr_pages"]) if rec["ocr"] == "true" else ""
    fm = FRONT % dict(url=rec["url"], date=rec["date"], body=rec["body"], status=rec["status"],
                      fmt=rec["fmt"], ocr=rec["ocr"], pages=rec["pages"],
                      ocr_pages=rec["ocr_pages"], chars=rec["chars"], conf=rec["conf"],
                      prov=rec["prov"], ocrnote=ocrnote)
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + text.strip() + "\n")
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--era", choices=["born", "scanned", "all"], default="all")
    ap.add_argument("--ocr", action="store_true", help="OCR scanned docs")
    ap.add_argument("--page-cap", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--years", default="", help="comma list, e.g. 2022,2023 (page-year filter)")
    ap.add_argument("--index-stub", action="store_true",
                    help="fast existence-check only (HEAD, no body download): record scanned "
                         "docs as ocr_pending stubs so the index covers the floor; OCR/vote "
                         "extraction is deferred to a later --ocr pass (the backfill).")
    args = ap.parse_args()

    inv = inventory()
    if args.years:
        keep = set(args.years.split(","))
        inv = [r for r in inv if r[0] in keep]
    print("inventory: %d minutes URLs (2015-2026)" % len(inv))
    if args.scan_only:
        with open(os.path.join(HERE, "minutes_urls.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["page_year", "url", "basename"])
            w.writerows(inv)
        return 0

    # load existing index so we can append/refresh
    index_rows = {}
    if os.path.exists(INDEX):
        for r in csv.DictReader(open(INDEX)):
            index_rows[r["source_url"]] = r
    unrec = []
    os.makedirs(MIN_DIR, exist_ok=True)
    cols = ["date", "year", "body", "doc_status", "pages", "format", "ocr",
            "extraction_confidence", "provenance", "source_url", "md_path", "basename"]

    def flush_index():
        rows = sorted(index_rows.values(), key=lambda r: (r["date"], r["body"]))
        tmpf = INDEX + ".tmp"
        with open(tmpf, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
        os.replace(tmpf, INDEX)     # atomic — a kill never leaves a half-written index
        return len(rows)

    def head_ok(u):
        """True if u resolves (200) live; else try wayback existence. Returns
        (exists, wb_flag)."""
        try:
            enc = urllib.parse.quote(u, safe=":/?=&%")
            req = urllib.request.Request(enc, method="HEAD", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return (200 <= r.status < 400), ""
        except Exception:
            try:
                import json as _json
                api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(u, safe="")
                j = _json.loads(fetch_bytes(api, timeout=45).decode("utf-8", "replace"))
                snap = j.get("archived_snapshots", {}).get("closest")
                return (bool(snap and snap.get("available")), "wayback")
            except Exception:
                return (False, "")

    done = 0
    for page_year, url, basename in inv:
        date = parse_date(basename, page_year)
        if not date:
            unrec.append((page_year, basename, url, "unparseable-date"))
            continue
        if date < FLOOR:
            continue
        body = classify_body(basename)
        status = doc_status(basename)
        existing = index_rows.get(url)
        if existing and not args.force and os.path.exists(
                os.path.join(os.path.dirname(HERE), existing["md_path"])):
            continue
        # -- fast index-stub path (no body download): confirm existence, record ocr_pending
        if args.index_stub:
            ok, wbf = head_ok(url)
            if not ok:
                unrec.append((page_year, basename, url, "not-found (live+wayback)"))
                continue
            prov = ("wayback_scanned" if wbf else "citysite_scanned")
            rec = dict(url=url, date=date, body=body, status=status, fmt="scanned",
                       ocr="true", pages="", ocr_pages="", chars="0", conf="ocr_pending",
                       prov=prov, _ov="")
            rel = write_md(rec, "[SCANNED — image-only PDF; existence confirmed, OCR + "
                                "vote extraction DEFERRED to the backfill pass (run "
                                "fetch_minutes.py --era scanned --ocr).]")
            index_rows[url] = dict(
                date=date, year=date[:4], body=body, doc_status=status, pages="",
                format="scanned", ocr="true", extraction_confidence="ocr_pending",
                provenance=prov, source_url=url, md_path=rel, basename=basename)
            done += 1
            if done % 10 == 0:
                flush_index(); print("  ...%d stubbed (latest %s %s)" % (done, date, body), flush=True)
            continue
        # download (with optional persistent cache to avoid re-fetch across passes)
        cpath = None; wb = ""
        if CACHE:
            os.makedirs(CACHE, exist_ok=True)
            cpath = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".pdf")
        if cpath and os.path.exists(cpath) and os.path.getsize(cpath) > 0:
            tmp = cpath; _cached = True
            if os.path.exists(cpath + ".wb"):
                wb = "wayback"
        else:
            try:
                data, wb = fetch_with_fallback(url)
            except Exception as e:
                unrec.append((page_year, basename, url, "download-failed:%s" % e))
                print("  DOWNLOAD FAIL %s (%s)" % (basename, e), file=sys.stderr)
                continue
            if cpath:
                with open(cpath, "wb") as cf:
                    cf.write(data)
                if wb:
                    open(cpath + ".wb", "w").close()
                tmp = cpath
            else:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                    tf.write(data); tmp = tf.name
            _cached = bool(cpath)
        try:
            pages = pdf_pages(tmp)
            txt = pdftotext(tmp)
            dens = len(txt) / max(pages, 1)
            scanned = dens < DENSITY_BORN
            era = "scanned" if scanned else "born"
            if args.era != "all" and args.era != era:
                continue
            ocr_pages = ""
            if scanned:
                if not args.ocr:
                    # record as scanned/OCR-pending; write a stub md (no body) so the
                    # index is complete and honest, corpus filled on the --ocr pass
                    fmt, ocr, conf, prov = "scanned", "true", "ocr_pending", "citysite_scanned"
                    body_text = ("[SCANNED — image-only PDF; OCR pending. Minutes body "
                                 "precedes appended media packet. Re-run fetch_minutes.py "
                                 "--ocr to fill this corpus.]")
                    chars = 0
                else:
                    otext, npg, err = ocr_pdf(tmp, pages, args.page_cap)
                    if err:
                        unrec.append((page_year, basename, url, err)); continue
                    fmt, ocr, conf, prov = "ocr", "true", "low", "citysite_ocr"
                    body_text = otext
                    ocr_pages = str(npg)
                    chars = len(otext)
            else:
                fmt, ocr, conf, prov = "text", "false", "high", "citysite_minutes"
                body_text = txt
                chars = len(txt)
            if wb:
                prov = "wayback_minutes" if not scanned else "wayback_ocr"
            rec = dict(url=url, date=date, body=body, status=status, fmt=fmt, ocr=ocr,
                       pages=str(pages), ocr_pages=ocr_pages, chars=str(chars), conf=conf,
                       prov=prov, _ov=(existing["md_path"] if existing else ""))
            # preserve prior md path on refresh
            if existing:
                prior = os.path.join(os.path.dirname(HERE), existing["md_path"])
                rec["_ov"] = prior
            rel = write_md(rec, body_text)
            index_rows[url] = dict(
                date=date, year=date[:4], body=body, doc_status=status, pages=str(pages),
                format=fmt, ocr=ocr, extraction_confidence=conf, provenance=prov,
                source_url=url, md_path=rel, basename=basename)
            done += 1
            if done % 5 == 0:
                flush_index()      # incremental — resumable across a mid-run kill
                print("  ...%d written (latest %s %s %s)" % (done, date, body, fmt), flush=True)
        finally:
            if not _cached:
                os.unlink(tmp)

    nrows = flush_index()
    # merge + dedupe the unrecovered ledger by url (keep the latest reason). A url that was
    # unrecovered earlier but is now indexed (e.g. recovered via wayback) is DROPPED.
    ledger = {}
    if os.path.exists(UNREC):
        for r in csv.reader(open(UNREC)):
            if r and r[0] != "page_year" and len(r) >= 4:
                ledger[r[2]] = r
    for py, bn, u, why in unrec:
        ledger[u] = [py, bn, u, why]
    ledger = {u: r for u, r in ledger.items() if u not in index_rows}
    with open(UNREC, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["page_year", "basename", "url", "reason"])
        w.writerows(sorted(ledger.values()))
    print("== fetch done: %d markdown written this run; index now %d rows; %d unrecovered this run =="
          % (done, nrows, len(unrec)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
