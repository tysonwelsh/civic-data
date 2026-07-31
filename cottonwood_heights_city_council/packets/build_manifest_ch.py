#!/usr/bin/env python3
"""Build the CH packets fetch manifest from the parsed landing JSON + sizes.

Writes /tmp/ch_manifest.json: one record per Packet anchor with
date, body, meeting_type, packet_kind, title, url, docId, size, filename.
"""
import json, re

sizes = {}
for line in open("/tmp/ch_sizes.txt"):
    line = line.strip()
    if not line:
        continue
    sz, url = line.split("|", 1)
    sizes[url] = int(sz) if sz.isdigit() else None

def meeting_type(body, title):
    t = title.lower()
    if body == "Council":
        if "special" in t:
            return "special"
        if "retreat" in t:
            return "retreat"
        return "regular"  # Work Session and Business Meeting
    # PC
    if "administrative hearing" in t:
        return "admin_hearing"
    return "regular"

manifest = []
seen = set()
for body, f in [("Council", "/tmp/ch_council.json"), ("PC", "/tmp/ch_pc.json")]:
    d = json.load(open(f))
    for r in d:
        for l in r["links"]:
            if l["label"].strip().lower() != "packet":
                continue
            url = l["url"]
            if url in seen:
                continue
            seen.add(url)
            m = re.search(r"showpublisheddocument/(\d+)", url)
            docid = m.group(1)
            mt = meeting_type(body, r["title"])
            fn = f"{docid}_{body.lower()}_{mt}.pdf"
            manifest.append({
                "date": r["date"],
                "body": body,
                "meeting_type": mt,
                "packet_kind": "full_packet",
                "title": r["title"],
                "url": url,
                "docid": docid,
                "size": sizes.get(url),
                "filename": fn,
            })

manifest.sort(key=lambda x: (x["date"], x["body"], x["meeting_type"]))
json.dump(manifest, open("/tmp/ch_manifest.json", "w"), indent=1)
print("manifest records:", len(manifest))
# dupe filename check
fns = [m["filename"] for m in manifest]
print("unique filenames:", len(set(fns)), "of", len(fns))
