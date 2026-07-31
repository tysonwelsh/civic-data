#!/usr/bin/env python3
"""
harvest_packet_true.py — Millcreek IN-PACKETS public-comment harvest, LARGE-PACKET route.

Companion to harvest_packets.py (which scans the RETAINED AgendaCenter *Minutes-view*
PDFs already on disk).  This driver fetches the DIFFERENT, much larger `?packet=true`
land-use agenda packets — the combined staff-report bundles whose appendices carry the
standalone "Public Comments from Residents" resident letters AND forwarded resident-email
blocks that the minutes-view docs omit.  Documented ceiling in AVAILABILITY.md (2026-07-06
§3): those are a live re-fetch, never retained on disk.

URL route (CivicPlus AgendaCenter, confirmed 2026-07-19 HEAD probe, HTTP 200 application/pdf):
  https://www.millcreekut.gov/AgendaCenter/ViewFile/Agenda/_<MMDDYYYY>-<docId>?packet=true
built from each PlanningCommission full_packet row in ../packets/index.csv.

§9 DISCARD-BINARY DISCIPLINE (SCHEMA_SPEC §9; millcreek packets/ is an index-only / no-raw-
duplication dataset by documented convention — see packets/CLAUDE.md).  Each packet is
fetched, sha256'd, text-extracted with `pdftotext -layout`, and the BINARY IS DISCARDED.
Only the extracted TEXT is kept, and only for comment-bearing packets (moved into
raw/packet_txt/ by the extractor).  Provenance for every fetch — sha256, bytes, pages,
fetch_status — lives in packet_true_fetch.csv; the packet is public + re-fetchable via
source_url.

fetch_status vocabulary (closed): ok | needs_ocr | <http-code> | not_pdf | error:<kind> | missing_pdf
Resumable: text already in the scan dir is skipped.  Network required.
"""
import csv, os, re, subprocess, sys, hashlib, tempfile, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
INDEX = os.path.join(CITY, "packets", "index.csv")
SCAN_DIR = os.path.join(HERE, "raw", "packet_true_txt")   # full pdftotext, one per fetched packet
FETCH_LOG = os.path.join(HERE, "packet_true_fetch.csv")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def packet_true_url(date, docid):
    mm, dd, yy = date[5:7], date[8:10], date[0:4]
    return (f"https://www.millcreekut.gov/AgendaCenter/ViewFile/Agenda/"
            f"_{mm}{dd}{yy}-{docid}?packet=true")


def fetch(url, dst):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://www.millcreekut.gov/AgendaCenter",
        "Accept": "application/pdf,*/*",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    with open(dst, "wb") as f:
        f.write(data)
    return len(data), ctype


def pdftotext(pdf_path, txt_path):
    subprocess.run(["pdftotext", "-layout", pdf_path, txt_path],
                   capture_output=True, text=True)


def main():
    os.makedirs(SCAN_DIR, exist_ok=True)
    # carry forward binary provenance (sha256/bytes) for already-fetched packets so a resume
    # never blanks it — the binary itself was discarded, the hash is the only record left.
    prior = {}
    if os.path.exists(FETCH_LOG):
        for pr in csv.DictReader(open(FETCH_LOG, encoding="utf-8")):
            prior[(pr["date"], pr["docid"])] = pr
    rows = [r for r in csv.DictReader(open(INDEX, encoding="utf-8"))
            if r["body"] == "PlanningCommission" and r["packet_kind"] == "full_packet"]
    rows.sort(key=lambda r: r["date"])
    log = []
    for r in rows:
        date, docid = r["date"], r["docid"]
        url = packet_true_url(date, docid)
        txt_path = os.path.join(SCAN_DIR, f"packet_{date}.txt")
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
            text = open(txt_path, encoding="utf-8", errors="replace").read()
            p = prior.get((date, docid), {})
            log.append(dict(date=date, docid=docid, url=url,
                            fetch_status=p.get("fetch_status") or "ok",
                            bytes=p.get("bytes", ""), sha256=p.get("sha256", ""),
                            pages=text.count("\x0c") + 1, text_chars=len(text)))
            continue
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        fetch_status = "ok"; nbytes = 0; sha = ""; pages = ""; tchars = 0
        try:
            nbytes, ctype = fetch(url, tmp)
            sha = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
            if "pdf" not in ctype.lower() and not open(tmp, "rb").read(5).startswith(b"%PDF"):
                fetch_status = "not_pdf"
            else:
                pdftotext(tmp, txt_path)
                if os.path.exists(txt_path):
                    text = open(txt_path, encoding="utf-8", errors="replace").read()
                    pages = text.count("\x0c") + 1
                    tchars = len(text)
                    # needs_ocr heuristic: image-only scan yields near-empty text layer
                    if pages and tchars / pages < 80:
                        fetch_status = "needs_ocr"
                else:
                    fetch_status = "error:no_text"
        except urllib.error.HTTPError as e:
            fetch_status = str(e.code)
        except Exception as e:
            fetch_status = f"error:{type(e).__name__}"
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)   # §9: DISCARD the binary
        log.append(dict(date=date, docid=docid, url=url, fetch_status=fetch_status,
                        bytes=nbytes, sha256=sha, pages=pages, text_chars=tchars))
        print(f"{date} doc{docid}: {fetch_status}  {nbytes/1e6:.1f}MB  pages={pages} chars={tchars}",
              flush=True)
    cols = ["date", "docid", "url", "fetch_status", "bytes", "sha256", "pages", "text_chars"]
    with open(FETCH_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(log)
    print(f"\nfetched/scanned {len(rows)} PC packet=true; log -> {FETCH_LOG}")


if __name__ == "__main__":
    main()
