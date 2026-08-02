#!/usr/bin/env python3
"""Fetch every Washington County campaign-finance filing in batch/manifest.json.

Writes raw/<channel>/<file> plus a per-channel _fetch_log.jsonl carrying
url, http status, bytes, sha256, retrieved_utc  (the repo's Source-6 provenance
contract).  Idempotent: a file already on disk with a matching sha256 log row is
skipped.  NEVER writes outside campaign_finance/.
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def safe_name(url):
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1]).strip()
    base = re.sub(r"[^A-Za-z0-9._ ()@,;+-]", "_", base)
    base = re.sub(r"\s+", " ", base).strip()
    if not re.search(r"\.(pdf|xls|xlsx|jpg|png)$", base, re.I):
        base += ".pdf"          # extensionless portal files; real type verified downstream
    return base[:180]


def fetch(url, referer=None, tries=4):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer or "https://www.washco.utah.gov/",
    })
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except Exception as exc:                     # noqa: BLE001
            last = exc
            code = getattr(exc, "code", None)
            if code in (403, 404, 410, 451):
                return code, b""
            time.sleep(10 * (attempt + 1))
    return f"error:{last}", b""


def main():
    manifest = json.load(open(os.path.join(HERE, "manifest.json")))
    # optional channel filter so disjoint workers can run in parallel WITHOUT
    # racing (each channel owns its own _fetch_log.jsonl)
    args = list(sys.argv[1:])
    shard = None
    if args and re.fullmatch(r"\d+/\d+", args[-1]):
        i, n = args.pop().split("/")
        shard = (int(i), int(n))
    only = set(args)
    if only:
        manifest = [e for e in manifest if e["channel"] in only]
    if shard:
        i, n = shard
        manifest = [e for k, e in enumerate(manifest) if k % n == i]
    logs = {}
    done = {}
    for entry in manifest:
        chan = entry["channel"]
        d = os.path.join(RAW, chan)
        os.makedirs(d, exist_ok=True)
        suffix = f".shard{shard[0]}" if shard else ""
        lp = os.path.join(d, f"_fetch_log{suffix}.jsonl")
        if chan not in logs:
            logs[chan] = lp
            for lp2 in sorted(glob.glob(os.path.join(d, "_fetch_log*.jsonl"))):
                for line in open(lp2):
                    try:
                        rec = json.loads(line)
                        # only a SETTLED outcome counts as done; transport errors
                        # (Wayback rate-limiting) must stay retryable
                        if rec.get("status") in (200, 404, 403, 410, 451):
                            done[rec["url"]] = rec
                    except Exception:                # noqa: BLE001
                        pass
        if entry["fetch_url"] in done:
            continue
        name = safe_name(entry["url"])
        path = os.path.join(d, name)
        n = 1
        while os.path.exists(path) and os.path.basename(path) not in (
                r.get("file") for r in done.values()):
            n += 1
            stem, ext = os.path.splitext(name)
            path = os.path.join(d, f"{stem}~{n}{ext}")
        status, body = fetch(entry["fetch_url"])
        rec = {
            "url": entry["fetch_url"],
            "original_url": entry["url"],
            "status": status,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest() if body else "",
            "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "file": os.path.basename(path) if body else "",
            "channel": chan,
        }
        if body and status == 200:
            open(path, "wb").write(body)
        with open(logs[chan], "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        done[entry["fetch_url"]] = rec
        print(f"{status:>6} {len(body):>9} {chan}/{rec['file'] or '(none)'}", flush=True)
        time.sleep(1.2)


if __name__ == "__main__":
    sys.exit(main())
