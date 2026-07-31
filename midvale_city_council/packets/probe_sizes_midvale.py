#!/usr/bin/env python3
"""Size-probe (HEAD Content-Length) every harvested Midvale packet URL, resolving
bare-relative links by trying candidate Document Center paths. Writes _probed.json."""
import re, os, json, time, sys
from urllib.parse import quote

sys.path.insert(0, "/Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts")
from polite_fetch import content_length  # HEAD-only Content-Length

BASE = "https://www.midvale.utah.gov/"
HERE = os.path.dirname(os.path.abspath(__file__))

def enc(path):
    # URL-encode the Document-Center path: spaces->%20, & ->%26, keep slashes.
    return BASE + quote(path, safe="/")

def candidates(r):
    """Ordered candidate site-root-relative paths for a link."""
    if not r["bare"]:
        return [r["rel"]]
    y, folder, fn = r["year"], r["folder"], r["fname"]
    base = f"Document Center/Agendas & Minutes/{folder}/{y}"
    return [
        f"{base}/Packets/{fn}",
        f"{base}/{fn}",
        f"Document Center/Agendas & Minutes/{fn}",
    ]

def main():
    rows = json.load(open(os.path.join(HERE, "_harvest.json")))
    out = []
    for r in rows:
        chosen_url = None
        chosen_size = None
        for cand in candidates(r):
            url = enc(cand)
            size = content_length(url)
            time.sleep(1.0)  # polite
            if size is not None and size > 0:
                chosen_url = url
                chosen_size = size
                r["resolved_path"] = cand
                break
        if chosen_url is None:
            # keep the first candidate as the recorded (dead) url for logging
            chosen_url = enc(candidates(r)[0])
            r["resolved_path"] = candidates(r)[0]
        r["source_url"] = chosen_url
        r["content_length"] = chosen_size
        out.append(r)
        tag = "OK " if chosen_size else "DEAD"
        print(f"{tag} {r['body']} {r['date']} {chosen_size} {chosen_url}")
    json.dump(out, open(os.path.join(HERE, "_probed.json"), "w"), indent=1)
    live = [r for r in out if r["content_length"]]
    total = sum(r["content_length"] for r in live)
    print(f"\nlive={len(live)}/{len(out)}  total_bytes={total}  total_GB={total/1e9:.3f}")

if __name__ == "__main__":
    main()
