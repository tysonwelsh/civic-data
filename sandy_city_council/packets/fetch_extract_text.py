#!/usr/bin/env python3
"""fetch_extract_text.py — fetch classified attachments, extract text, discard binary.

PRIMARY_DOCS_PILOT_SPEC.md §6. For every index.csv row with a non-blank
doc_class and blank fetch_status (rerunnable/resumable):

  1. polite GET of source_url (shared conventions: ≥1.0 s/host delay, browser
     UA, honor 404/429/503) to a TEMP dir;
  2. sha256 the binary;
  3. extract text — pdftotext -layout for .pdf, textutil for .doc/.docx —
     into text/attachments/<date>_<slug>_<guid8>.txt;
  4. DISCARD the binary (disk design: text + source_url + sha256 are the
     durable record; stored_locally stays 'no' — it describes the binary);
  5. write per-row fetch_status / sha256 / text_path / text_chars back to
     index.csv and append a provenance line to text/_fetch_log.jsonl.

fetch_status values:
  ok           fetched + text extracted (text_chars > threshold)
  needs_ocr    fetched, PDF has no usable text layer (scan) — honest OCR floor
  no_extractor fetched, format has no CLI extractor here (e.g. .pptx)
  404 / 4xx/5xx  HTTP failure (dated honest gap — no retry loop)
  error:<...>  transport/extraction error

Run:  python3 fetch_extract_text.py [--limit N] [--tmp DIR]
"""
import argparse, csv, hashlib, json, os, re, subprocess, sys, tempfile, time
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXT_DIR = os.path.join(HERE, "text", "attachments")
LOG = os.path.join(HERE, "text", "_fetch_log.jsonl")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact repo owner)")
DELAY = 1.0
MIN_CHARS_PER_PAGE = 15   # below this a PDF is treated as scan → needs_ocr
MIN_CHARS_ABS = 40


def slug(s, n=50):
    return re.sub(r"_+", "_", "".join(c if c.isalnum() else "_" for c in s))[:n].strip("_")


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
    if ext == ".pptx":
        # slide decks: pull the XML text runs (no external tools needed)
        import zipfile, re as _re
        try:
            with zipfile.ZipFile(binpath) as z:
                slides = sorted(n for n in z.namelist()
                                if _re.match(r"ppt/slides/slide\d+\.xml$", n))
                parts = []
                for n in slides:
                    xml = z.read(n).decode("utf-8", "replace")
                    runs = _re.findall(r"<a:t>(.*?)</a:t>", xml, _re.S)
                    if runs:
                        parts.append("\n".join(runs))
                text = "\n\n".join(parts).strip()
        except Exception:
            return ("error:pptx", 0)
        if len(text) < MIN_CHARS_ABS:
            return ("needs_ocr", len(text))
        with open(txtpath, "w", encoding="utf-8") as tf:
            tf.write(text)
        return ("ok", len(text))
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
    tmpdir = a.tmp or tempfile.mkdtemp(prefix="sandy_att_")
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
    seen = {}   # url -> dict of result fields (same doc listed under 2 matters)
    logf = open(LOG, "a")
    try:
        for r in todo:
            url = r["source_url"]
            if url in seen:
                for k, v in seen[url].items():
                    r[k] = v
                done += 1
                continue
            ext = os.path.splitext(url)[1].lower() or ".pdf"
            guid8 = re.sub(r"[^0-9a-f]", "", url.rsplit("/", 1)[-1].split(".")[0])[:8]
            base = f"{r['date']}_{slug(r['title'])}_{guid8}"
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
