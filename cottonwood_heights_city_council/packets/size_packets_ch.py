#!/usr/bin/env python3
"""HEAD-probe Content-Length for all CH packet URLs. Writes /tmp/ch_sizes.txt."""
import sys, time, json, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
}

urls = [l.strip() for l in open(sys.argv[1]) if l.strip()]
out = open(sys.argv[2], "w")
for i, url in enumerate(urls):
    cl = ""
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            cl = r.headers.get("Content-Length", "")
    except Exception as e:
        cl = "ERR:" + type(e).__name__
    out.write(f"{cl}|{url}\n")
    out.flush()
    print(i + 1, cl, url.split("/")[-2])
    time.sleep(1.0)
out.close()
