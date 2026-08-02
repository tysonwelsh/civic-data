#!/usr/bin/env python3
"""Second-chance pass for Wayback rows that returned 404 at the timestamp we asked for.

The CDX index lists a URL under several captures; some are `warc/revisit` pointers whose
`id_` replay 404s even though ANOTHER capture of the same URL serves the bytes.  This pass
re-queries CDX for every timestamp of each 404'd URL and tries them oldest-first.  A URL
that 404s at EVERY capture is a genuine gap and stays in unrecovered.csv.
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
RAW = os.path.join(os.path.dirname(HERE), "raw")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0"


def get(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def main():
    todo = []
    for lp in glob.glob(os.path.join(RAW, "*", "_fetch_log*.jsonl")):
        for line in open(lp):
            rec = json.loads(line)
            if rec.get("status") == 404:
                todo.append((lp, rec))
    print(f"{len(todo)} URLs to retry")
    for lp, rec in todo:
        url = rec["original_url"]
        cdx = ("https://web.archive.org/cdx/search/cdx?url="
               + urllib.parse.quote(url, safe="") + "&output=text&fl=timestamp,statuscode&limit=60")
        stamps = []
        for attempt in range(4):
            try:
                _, body = get(cdx, 120)
                stamps = [l.split()[0] for l in body.decode().splitlines() if l.strip()]
                break
            except Exception:                                   # noqa: BLE001
                time.sleep(8 * (attempt + 1))
        got = False
        for ts in stamps:
            if ts == rec["url"].split("/web/")[1].split("id_/")[0]:
                continue
            enc = urllib.parse.quote(url, safe=":/?&=%")
            try:
                st, body = get(f"https://web.archive.org/web/{ts}id_/{enc}")
            except Exception:                                   # noqa: BLE001
                time.sleep(5)
                continue
            if st == 200 and body[:5] in (b"%PDF-",) or (st == 200 and len(body) > 2000):
                d = os.path.dirname(lp)
                name = re.sub(r"[^A-Za-z0-9._ ()@,;+-]", "_",
                              urllib.parse.unquote(url.rsplit("/", 1)[-1]))
                if not re.search(r"\.(pdf|xls|xlsx)$", name, re.I):
                    name += ".pdf"
                open(os.path.join(d, name), "wb").write(body)
                out = dict(rec)
                out.update(url=f"https://web.archive.org/web/{ts}id_/{enc}", status=200,
                           bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                           retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                           file=name, retry_of_404=True)
                open(lp, "a").write(json.dumps(out) + "\n")
                print(f"  RECOVERED @{ts}  {name}", flush=True)
                got = True
                break
            time.sleep(1)
        if not got:
            print(f"  still gone ({len(stamps)} captures tried)  {url.rsplit('/', 1)[-1][:60]}",
                  flush=True)
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
