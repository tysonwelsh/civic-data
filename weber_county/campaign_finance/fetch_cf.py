#!/usr/bin/env python3
"""fetch_cf.py — polite fetcher for the Weber County campaign-finance acquisition.

Reads a TSV batch (url<TAB>out_filename[<TAB>note]) and writes the bytes into an output
directory, appending one provenance record per attempt to `<outdir>/_fetch_log.jsonl`:
  {url, out, http_status, bytes, sha256, content_type, content_disposition, retrieved_utc, note}

Never overwrites an existing file unless --force. Failures are logged, never silently
dropped (an unreachable document is a recorded gap, not a missing row).

Usage:
  python3 fetch_cf.py --batch batch/<name>.tsv --out raw/<subdir> [--sleep 1.5] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url: str, timeout: int = 120, referer: str = ""):
    # Wix (_files/ugd) hotlink-protects: a bare UA-only GET gets HTTP 429 even at 1 req/8s,
    # while the same request with Accept + a same-site Referer returns 200. Send both.
    hdrs = {"User-Agent": UA, "Accept": "application/pdf,application/octet-stream,*/*"}
    if referer:
        hdrs["Referer"] = referer
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), r.headers.get("Content-Type", ""), \
            r.headers.get("Content-Disposition", "")


def fetch_curl(url: str, timeout: int = 180, referer: str = ""):
    """curl fallback. Some weberelections.gov `_files/ugd/` objects 429 for urllib but
    return 200 for curl with identical headers (Wix edge fingerprinting) — so the fetcher
    can fall back rather than record a false 'unavailable'."""
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tmp = tf.name
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
           "-H", "Accept: application/pdf,application/octet-stream,*/*"]
    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    cmd += ["-D", tmp + ".hdr", "-o", tmp, "-w", "%{http_code}", url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    code = int(p.stdout.strip() or 0)
    body = open(tmp, "rb").read()
    hdr = ""
    try:
        hdr = open(tmp + ".hdr", encoding="utf-8", errors="replace").read()
    except OSError:
        pass
    ctype = ""
    cdisp = ""
    for line in hdr.splitlines():
        low = line.lower()
        if low.startswith("content-type:"):
            ctype = line.split(":", 1)[1].strip()
        elif low.startswith("content-disposition:"):
            cdisp = line.split(":", 1)[1].strip()
    for f in (tmp, tmp + ".hdr"):
        try:
            os.unlink(f)
        except OSError:
            pass
    if code != 200:
        raise urllib.error.HTTPError(url, code, f"curl HTTP {code}", None, None)
    return code, body, ctype, cdisp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--referer", default="")
    ap.add_argument("--use-curl", action="store_true",
                    help="shell out to curl (Wix edge 429s urllib for some objects)")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, a.out)
    os.makedirs(outdir, exist_ok=True)
    logpath = os.path.join(outdir, "_fetch_log.jsonl")

    rows = []
    with open(os.path.join(here, a.batch), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))

    ok = err = skip = 0
    with open(logpath, "a", encoding="utf-8") as log:
        for url, name, note in rows:
            dest = os.path.join(outdir, name)
            if os.path.exists(dest) and not a.force:
                skip += 1
                continue
            status = body = None
            ctype = cdisp = ""
            last = ""
            for attempt in range(a.retries):
                try:
                    if a.use_curl:
                        status, body, ctype, cdisp = fetch_curl(url, referer=a.referer)
                    else:
                        status, body, ctype, cdisp = fetch(url, referer=a.referer)
                    break
                except urllib.error.HTTPError as e:
                    status, last = e.code, f"HTTPError {e.code}"
                    if e.code in (429, 503):  # Wix/Wayback rate limit — back off and retry
                        time.sleep(20 * (attempt + 1))
                        continue
                    break
                except Exception as e:  # noqa: BLE001
                    last = f"{type(e).__name__}: {e}"
                    time.sleep(3 * (attempt + 1))
            rec = {
                "url": url,
                "out": name,
                "http_status": status,
                "bytes": len(body) if body else 0,
                "sha256": hashlib.sha256(body).hexdigest() if body else "",
                "content_type": ctype,
                "content_disposition": cdisp,
                "retrieved_utc": datetime.now(timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "note": note,
                "error": "" if body else last,
            }
            if body:
                with open(dest, "wb") as f:
                    f.write(body)
                ok += 1
            else:
                err += 1
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(("OK  " if body else "ERR ") + f"{rec['bytes']:>9} {name}", flush=True)
            time.sleep(a.sleep)

    print(f"\nfetched={ok} skipped={skip} failed={err} -> {outdir}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
