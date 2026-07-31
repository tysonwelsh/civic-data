#!/usr/bin/env python3
"""fetch_extract_text.py — fetch classified Logan packet docs, extract text, discard binary.

Adapted from sandy_city_council/packets/fetch_extract_text.py for Logan's Revize
static CMS (loganutah.gov -> cms9files.revize.com). For every index.csv row with a
non-blank doc_class and blank fetch_status (rerunnable/resumable):

  1. polite GET of source_url (>=1.0 s/host delay, browser UA, honor 404/429/503);
  2. sha256 the binary;
  3. extract text — pdftotext -layout (Logan packets are all PDF) — into
     text/attachments/<date>_<slug>_<urlhash8>.txt;
  4. DISCARD the binary (disk design: text + source_url + sha256 are the durable
     record; stored_locally stays 'no' — it describes the binary);
  5. write per-row fetch_status / sha256 / text_path / text_chars back to index.csv
     and append a provenance line to text/_fetch_log.jsonl.

Logan specifics vs Sandy:
  - source_url ends in `<Human Filename>.pdf?t=<cachebuster>` — the query is stripped
    before taking the extension; the sidecar name uses a sha1(url)[:8] suffix (Logan
    filenames are human text, not GUIDs) so distinct URLs never collide.
  - Same title can appear at both WORKSHOP and ACTION stages with DIFFERENT URLs —
    those are genuinely different documents, fetched independently. Only byte-identical
    URLs dedup via the `seen` map.
  - Image-heavy plats/site-exhibits are common -> a substantial needs_ocr share is an
    HONEST recorded OCR floor, not a failure.

fetch_status values:
  ok           fetched + text extracted (text_chars over threshold)
  needs_ocr    fetched, PDF has no usable text layer (scan) — honest OCR floor
  no_extractor fetched, format has no CLI extractor here
  404 / 4xx/5xx  HTTP failure (dated honest gap — no retry loop)
  error:<...>  transport/extraction error

Run:  python3 fetch_extract_text.py [--limit N] [--tmp DIR]
"""
import argparse, csv, hashlib, json, os, re, subprocess, time
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXT_DIR = os.path.join(HERE, "text", "attachments")
LOG = os.path.join(HERE, "text", "_fetch_log.jsonl")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact repo owner)")
DELAY = 1.0
MIN_CHARS_PER_PAGE = 15   # below this a PDF is treated as scan -> needs_ocr
MIN_CHARS_ABS = 40


def slug(s, n=50):
    return re.sub(r"_+", "_", "".join(c if c.isalnum() else "_" for c in s))[:n].strip("_")


def url_ext(url):
    path = urlparse(url).path            # drops ?t=<cachebuster>
    ext = os.path.splitext(unquote(path))[1].lower()
    return ext if ext else ".pdf"


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=120).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def extract(binpath, ext, txtpath):
    """Returns (status, chars). Writes txtpath on success."""
    if ext == ".pdf":
        r = subprocess.run(["pdftotext", "-layout", binpath, txtpath],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0 and not os.path.exists(txtpath):
            return ("error:pdftotext", 0)
        text = open(txtpath, encoding="utf-8", errors="replace").read()
        chars = len(text.strip())
        pages = pdf_pages(binpath) or 1
        if chars < MIN_CHARS_ABS or chars / pages < MIN_CHARS_PER_PAGE:
            os.remove(txtpath)
            return ("needs_ocr", chars)
        return ("ok", chars)
    if ext in (".doc", ".docx"):
        r = subprocess.run(["textutil", "-convert", "txt", "-output", txtpath, binpath],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not os.path.exists(txtpath):
            return ("error:textutil", 0)
        chars = len(open(txtpath, encoding="utf-8", errors="replace").read().strip())
        if chars < MIN_CHARS_ABS:
            os.remove(txtpath)
            return ("needs_ocr", chars)
        return ("ok", chars)
    return ("no_extractor", 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()

    os.makedirs(TEXT_DIR, exist_ok=True)
    import tempfile
    tmpdir = a.tmp or tempfile.mkdtemp(prefix="logan_att_")
    os.makedirs(tmpdir, exist_ok=True)

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)

    todo = [r for r in rows
            if r.get("doc_class") and not r.get("fetch_status")]
    if a.limit:
        todo = todo[:a.limit]
    print(f"to fetch: {len(todo)}")

    sess = requests.Session()
    sess.headers["User-Agent"] = UA
    done = 0
    seen = {}   # url -> dict of result fields (byte-identical doc listed twice)
    logf = open(LOG, "a")
    try:
        for r in todo:
            url = r["source_url"]
            if url in seen:
                for k, v in seen[url].items():
                    r[k] = v
                done += 1
                continue
            ext = url_ext(url)
            urlhash = hashlib.sha1(url.encode()).hexdigest()[:8]
            base = f"{r['date']}_{slug(r['title'])}_{urlhash}"
            binpath = os.path.join(tmpdir, base + ext)
            txtpath = os.path.join(TEXT_DIR, base + ".txt")
            t0 = time.time()
            status, sha, nbytes, chars = "", "", 0, 0
            try:
                resp = sess.get(url, timeout=180)
                if resp.status_code in (429, 503):
                    time.sleep(30)
                    resp = sess.get(url, timeout=180)
                if resp.status_code != 200:
                    status = str(resp.status_code)
                else:
                    data = resp.content
                    nbytes = len(data)
                    sha = hashlib.sha256(data).hexdigest()
                    with open(binpath, "wb") as bf:
                        bf.write(data)
                    status, chars = extract(binpath, ext, txtpath)
            except requests.RequestException as e:
                status = "error:" + type(e).__name__
            except subprocess.TimeoutExpired:
                status = "error:extract_timeout"
            finally:
                if os.path.exists(binpath):
                    os.remove(binpath)          # DISCARD the binary — by design
            r["fetch_status"] = status
            r["sha256"] = sha
            if status == "ok":
                r["text_path"] = os.path.relpath(txtpath, HERE)
                r["text_chars"] = str(chars)
            seen[url] = {"fetch_status": r["fetch_status"], "sha256": r["sha256"],
                         "text_path": r.get("text_path", ""),
                         "text_chars": r.get("text_chars", "")}
            logf.write(json.dumps({
                "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "url": url, "doc_class": r["doc_class"], "status": status,
                "bytes": nbytes, "sha256": sha, "text_chars": chars,
                "text_path": r.get("text_path", ""), "binary_retained": False}) + "\n")
            logf.flush()
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(todo)}  last={status}")
            time.sleep(max(0, DELAY - (time.time() - t0)))
    finally:
        logf.close()
        # checkpoint index.csv even on interrupt
        tmp = INDEX + ".tmp"
        with open(tmp, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, INDEX)
        print(f"wrote {INDEX}; processed {done} rows")


if __name__ == "__main__":
    main()
