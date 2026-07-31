#!/usr/bin/env python3
"""HEAD-probe every catalogued Magna packet URL for Content-Length (no body GET).

Reads raw/_catalog.tsv, sizes each packet_url, writes raw/_sizes.tsv
(key -> content_length_bytes,status,content_type) and appends one provenance line
per probe to raw/_fetch_log.jsonl. Politeness: HEAD only, >=1s/host, (connect,read)
timeout tuple so a stalling CivicPlus ?packet=true HEAD can't hang the sweep.
Drives the stored-vs-index-only decision and per-row size_mb in index.csv.
"""
import csv, json, os, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
LOG = os.path.join(HERE, "raw", "_fetch_log.jsonl")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def head(url):
    try:
        r = requests.head(url, headers={"User-Agent": UA}, timeout=(10, 20),
                          allow_redirects=True)
        cl = r.headers.get("content-length")
        return (int(cl) if cl and cl.isdigit() else None,
                r.status_code, r.headers.get("content-type"), r.url)
    except requests.RequestException as e:
        return (None, None, str(e)[:120], None)


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "raw", "_catalog.tsv")),
                               delimiter="\t"))
    out = []
    with open(LOG, "a") as log:
        for i, r in enumerate(rows):
            url = r["packet_url"]
            cl, status, ct, final = head(url)
            out.append({"key": r["key"], "source": r["source"], "body": r["body"],
                        "content_length_bytes": cl if cl is not None else "",
                        "status": status})
            log.write(json.dumps({
                "url": url, "final_url": final, "status": status,
                "content_type": ct, "bytes": cl, "sha256": "", "saved_as": None,
                "ok": bool(cl), "head_size_probe": True, "retrieved_utc": NOW}) + "\n")
            if i % 25 == 0:
                print(f"  {i}/{len(rows)}  {r['source']} {r['body']} {r['date']} "
                      f"{'%.2f MB' % (cl/1e6) if cl else cl} (http {status})")
            time.sleep(1.0)
    cols = ["key", "source", "body", "content_length_bytes", "status"]
    with open(os.path.join(HERE, "raw", "_sizes.tsv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(out)
    known = [o["content_length_bytes"] for o in out
             if isinstance(o["content_length_bytes"], int)]
    total = sum(known)
    print(f"\nSized {len(known)}/{len(out)}; total known = {total:,} bytes "
          f"({total/1e9:.2f} GB)")
    bad = [o for o in out if o["status"] not in (200,) or not isinstance(
        o["content_length_bytes"], int)]
    if bad:
        print(f"non-200 or unsized: {len(bad)}")
        for o in bad[:20]:
            print("   ", o["source"], o["key"], o["status"],
                  o["content_length_bytes"])


if __name__ == "__main__":
    main()
