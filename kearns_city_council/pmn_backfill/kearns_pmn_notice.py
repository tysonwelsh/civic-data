#!/usr/bin/env python3
"""Parse a PMN notice-page HTML (already fetched) -> attachments with the
attachment-TYPE label that sits in the <td> after each file link.
Emits: file_id, ext, filename, type_label  (one per line, tab-sep).
"""
import re, sys, html

def parse(path):
    d = open(path, encoding="utf-8", errors="replace").read()
    out = []
    # attachment rows: <a href="/pmn/files/<id>.<ext>" ...>name</a> ... <td> TYPE </td>
    for m in re.finditer(
        r'/pmn/files/([0-9]+)\.([A-Za-z0-9]+)"[^>]*>([^<]+)</a>(.*?)</tr>',
        d, re.S):
        fid, ext, name, tail = m.groups()
        # the type label is the text content of the next <td>...</td>
        tdm = re.search(r'<td>\s*(.*?)\s*</td>', tail, re.S)
        label = ""
        if tdm:
            label = re.sub(r'<[^>]+>', '', tdm.group(1))
            label = html.unescape(re.sub(r'\s+', ' ', label)).strip()
        out.append((fid, ext, html.unescape(name).strip(), label))
    return out

if __name__ == "__main__":
    for fid, ext, name, label in parse(sys.argv[1]):
        print(f"{fid}\t{ext}\t{name}\t{label}")
