#!/usr/bin/env python3
"""Discovery helper for the Cottonwood Heights campaign_finance build.
Extracts (anchor_text, href) pairs from a saved CivicEngage HTML page so the
opaque /home/showpublisheddocument/<id>/<ver> links can be mapped to candidate
filing labels. Discovery-only; not part of any derived layer."""
import re, sys, html

path = sys.argv[1]
needle = sys.argv[2] if len(sys.argv) > 2 else "showpublisheddocument"
data = open(path, encoding="utf-8", errors="replace").read()
# grab <a ... href="...">TEXT</a>
for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', data, re.I | re.S):
    href, text = m.group(1), m.group(2)
    if needle.lower() not in href.lower():
        continue
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    print(f"{text}\t{href}")
