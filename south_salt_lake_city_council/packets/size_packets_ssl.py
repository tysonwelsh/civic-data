#!/usr/bin/env python3
"""HEAD-probe every SSL AgendaCenter packet for Content-Length (no body GET).

Reads raw/_catalog.tsv, sizes each item's Agenda-slot ViewFile URL, writes
raw/_sizes.tsv (item_id -> content_length_bytes) and appends a provenance line per
probe to raw/_fetch_log.jsonl. Sizing drives the stored-vs-index-only decision and
the per-row size_mb in index.csv. GET-only politeness: HEAD, >=1s/host.
"""
import csv, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..",
                ".claude", "skills", "expand-city-sources", "scripts"))
from polite_fetch import content_length, UA
import requests

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
LOG = os.path.join(HERE, "raw", "_fetch_log.jsonl")


def head_full(url):
    """HEAD returning (content_length, status, content_type, final_url)."""
    try:
        r = requests.head(url, headers={"User-Agent": UA}, timeout=30,
                          allow_redirects=True)
        cl = r.headers.get("content-length")
        return (int(cl) if cl and cl.isdigit() else None,
                r.status_code, r.headers.get("content-type"), r.url)
    except requests.RequestException as e:
        return (None, None, str(e), None)


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "raw", "_catalog.tsv")),
                               delimiter="\t"))
    out = []
    with open(LOG, "a") as log:
        for i, r in enumerate(rows):
            # ?packet=true = the FULL assembled agenda packet (agenda + staff reports
            # + attachments). It equals the plain Agenda file when that upload already
            # IS the packet, and is strictly the full one when the plain slot is a thin
            # agenda outline (verified: PC 2022-01-20 plain 2.9 KB vs packet 4.1 MB).
            url = r["agenda_url"] + "?packet=true"
            cl, status, ct, final = head_full(url)
            out.append({"item_id": r["item_id"], "body": r["body"],
                        "packet_url": url,
                        "content_length_bytes": cl if cl is not None else "",
                        "status": status})
            log.write(json.dumps({
                "url": url, "final_url": final, "status": status,
                "content_type": ct, "bytes": cl, "sha256": "", "saved_as": None,
                "ok": bool(cl), "head_size_probe": True,
                "retrieved_utc": NOW}) + "\n")
            if i % 25 == 0:
                print(f"  {i}/{len(rows)} ... {r['body']} {r['date']} "
                      f"{'%.2f MB' % (cl/1e6) if cl else cl}")
            time.sleep(1.0)
    cols = ["item_id", "body", "packet_url", "content_length_bytes", "status"]
    with open(os.path.join(HERE, "raw", "_sizes.tsv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(out)
    total = sum(o["content_length_bytes"] for o in out
                if isinstance(o["content_length_bytes"], int))
    known = sum(1 for o in out if isinstance(o["content_length_bytes"], int))
    print(f"\nSized {known}/{len(out)} items; total known bytes = {total} "
          f"({total/1e9:.2f} GB)")


if __name__ == "__main__":
    main()
