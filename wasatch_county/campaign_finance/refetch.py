#!/usr/bin/env python3
"""refetch.py — re-fetch every filing listed in index.csv and verify it byte-for-byte.

This is the module's reproducibility check, not a builder: index.csv already carries the
canonical `source_url` (the government's own URL), the `archive_url` actually used when the
origin was dead, and the `sha256` of the retained bytes. Re-fetching and comparing the digest
proves the retained PDF is what the government published, and surfaces link rot early.

    python3 refetch.py            # verify only (no writes)
    python3 refetch.py --repair   # re-download any missing raw/ file

Origin hosts, as of 2026-08-01 (see AVAILABILITY.md):
  wasatch.utah.gov          DNN "Portals" host — STILL LIVE and serving 2018/2020/2022/2024-June
  www.wasatchcounty.gov     CivicPlus DocumentCenter — the live 2026 cycle
  municipal.utah.gov        Lt. Governor disclosures file host (backslash paths; quote them)
  web.archive.org           the ONLY channel for the retired Jadu-era 2024 general reports
"""
import argparse, csv, hashlib, os, sys, time, urllib.parse, urllib.request, gzip

ROOT = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36 archive-browser")  # CivicPlus/Akamai 403s a bare fetcher


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*",
                                               "Accept-Encoding": "gzip, deflate"})
    r = urllib.request.urlopen(req, timeout=timeout)
    d = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        d = gzip.decompress(d)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", action="store_true")
    a = ap.parse_args()
    ok = missing = drift = fail = 0
    for r in csv.DictReader(open(os.path.join(ROOT, "index.csv"))):
        p = os.path.join(ROOT, r["path"])
        if os.path.exists(p):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            if h == r["sha256"]:
                ok += 1
            else:
                drift += 1
                print("DIGEST DRIFT", r["path"])
            continue
        missing += 1
        print("MISSING", r["path"])
        if not a.repair:
            continue
        url = r["archive_url"] or urllib.parse.quote(r["source_url"], safe=":/?&=#%")
        try:
            d = get(url)
        except Exception as e:
            fail += 1
            print("  refetch FAILED", type(e).__name__, e)
            continue
        h = hashlib.sha256(d).hexdigest()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(d)
        print("  refetched", len(d), "bytes", "DIGEST MATCH" if h == r["sha256"] else
              "DIGEST DIFFERS (source changed — do NOT overwrite index.csv without review)")
        time.sleep(0.5)
    print("ok=%d missing=%d digest_drift=%d refetch_fail=%d" % (ok, missing, drift, fail))
    return 1 if (drift or fail) else 0


if __name__ == "__main__":
    sys.exit(main())
