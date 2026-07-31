#!/usr/bin/env python3
"""Harvest Orem City campaign-finance filings listed in manifest.tsv.

Orem publishes candidate campaign-finance disclosures directly on its elections page
(orem.gov/elections) as PDFs/images under orem.gov/wp-content/uploads/YYYY/MM/. This
downloads each verbatim, mirroring polite_fetch.py discipline: browser User-Agent,
>=1s throttle, retries/backoff, bytes written verbatim, and one JSONL provenance line
per attempt (url, status, bytes, sha256, content_type, final_url, retrieved_utc).
GET-only, public records only. Filenames are prefixed with the upload YYYYMM (from the
/uploads/YYYY/MM/ path) so basenames never collide across reporting periods.
"""
import csv, hashlib, json, os, time, urllib.request, urllib.error

DS   = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(DS, "raw")
LOG  = os.path.join(RAW, "_fetch_log.jsonl")
BASE = "https://orem.gov/wp-content/uploads/"
NOW  = "2026-07-05T12:00:00Z"
UA   = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
        "(+public records research; contact repo owner)")
os.makedirs(RAW, exist_ok=True)


def local_name(urlpath):
    yyyy, mm, base = urlpath.split("/", 2)
    return f"{yyyy}{mm}_{base}"


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*",
                                               "Referer": "https://orem.gov/elections/"})
    for attempt in range(4):
        if attempt:
            time.sleep(1.0 * (2 ** attempt))
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
                rec = {"url": url, "final_url": resp.geturl(), "status": resp.status,
                       "content_type": resp.headers.get("Content-Type", ""),
                       "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                       "saved_as": os.path.basename(dest), "ok": bool(body),
                       "retrieved_utc": NOW}
                if body:
                    with open(dest, "wb") as f:
                        f.write(body)
                return rec
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                continue
            return {"url": url, "status": e.code, "error": str(e), "ok": False,
                    "saved_as": None, "retrieved_utc": NOW}
        except Exception as e:
            if attempt < 3:
                continue
            return {"url": url, "status": None, "error": str(e), "ok": False,
                    "saved_as": None, "retrieved_utc": NOW}


def main():
    with open(os.path.join(DS, "manifest.tsv")) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    ok = 0
    for r in rows:
        up = r["urlpath"].strip()
        url = BASE + up
        dest = os.path.join(RAW, local_name(up))
        rec = fetch(url, dest)
        with open(LOG, "a") as lf:
            lf.write(json.dumps(rec) + "\n")
        tag = "ok  " if rec.get("ok") else "FAIL"
        print(f"{tag} {rec.get('status')} {rec.get('bytes','')}\t{local_name(up)}")
        if rec.get("ok"):
            ok += 1
        time.sleep(1.1)
    print(f"\nDONE {ok}/{len(rows)} downloaded")


if __name__ == "__main__":
    main()
