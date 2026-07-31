#!/usr/bin/env python3
"""Fetch every LIVE (HEAD-200) Magna packet into raw/<date>/<key>.<ext>.

STORED mode (total live set = 1.33 GB < 1.5 GB budget; see AVAILABILITY.md). Reads
raw/_catalog.tsv + raw/_sizes.tsv; fetches only rows the size sweep found live (200)
via the shared polite fetcher (throttled, retrying). Names each file by its globally
unique source key (CivicPlus item id / PMN file id) so packets/text/<stem>.txt stems
never collide. Appends one provenance line per fetch (url, status, bytes, sha256,
saved_as) to raw/_fetch_log.jsonl and writes raw/_fetched.tsv (key,path,format,bytes,
sha256,status) for the index builder. IDEMPOTENT: a key already on disk is skipped.

The 52 PMN PC 2017-2018 files that HEAD-404 (the documented 2017–mid-2018 PMN blob
purge) are NOT fetched here — build_index_magna.py routes them to unrecovered.csv.
"""
import csv, hashlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..",
                ".claude", "skills", "expand-city-sources", "scripts"))
from polite_fetch import fetch  # throttled + retrying GET

RAW = os.path.join(HERE, "raw")
LOG = os.path.join(RAW, "_fetch_log.jsonl")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ext_for(ct):
    if ct and "wordprocessing" in ct:
        return ".docx"
    return ".pdf"


def main():
    cat = list(csv.DictReader(open(os.path.join(RAW, "_catalog.tsv")), delimiter="\t"))
    sizes = {s["key"]: s for s in
             csv.DictReader(open(os.path.join(RAW, "_sizes.tsv")), delimiter="\t")}
    fetched_path = os.path.join(RAW, "_fetched.tsv")
    done = {}
    if os.path.exists(fetched_path):
        done = {r["key"]: r for r in
                csv.DictReader(open(fetched_path), delimiter="\t")}
    live = [r for r in cat
            if sizes.get(r["key"], {}).get("status") == "200"]
    print(f"{len(live)} live packets to fetch ({len(done)} already done)")
    out = list(done.values())
    logf = open(LOG, "a")
    for i, r in enumerate(live):
        key = r["key"]
        if key in done and os.path.exists(os.path.join(HERE, done[key]["path"])):
            continue
        resp = fetch(r["packet_url"])
        body = resp.content if resp is not None else b""
        ok = resp is not None and resp.status_code == 200 and body
        ct = resp.headers.get("content-type", "") if resp is not None else ""
        ext = ext_for(ct)
        reldir = os.path.join("raw", r["date"])
        os.makedirs(os.path.join(HERE, reldir), exist_ok=True)
        rel = os.path.join(reldir, key + ext)
        sha = hashlib.sha256(body).hexdigest() if body else ""
        if ok:
            with open(os.path.join(HERE, rel), "wb") as f:
                f.write(body)
        fmt = "docx-text" if ext == ".docx" else "text"  # born-digital; refined post-extract
        out.append({"key": key, "path": rel if ok else "", "format": fmt if ok else "",
                    "bytes": len(body), "sha256": sha,
                    "status": resp.status_code if resp is not None else ""})
        logf.write(json.dumps({
            "url": r["packet_url"], "final_url": resp.url if resp is not None else None,
            "status": resp.status_code if resp is not None else None,
            "content_type": ct, "bytes": len(body), "sha256": sha,
            "saved_as": rel if ok else None, "ok": bool(ok),
            "retrieved_utc": NOW}) + "\n")
        logf.flush()
        if i % 20 == 0:
            print(f"  {i}/{len(live)}  {r['source']} {r['body']} {r['date']} "
                  f"{len(body)/1e6:.2f}MB http={resp.status_code if resp else None}",
                  flush=True)
        time.sleep(1.0)
    logf.close()
    # rewrite _fetched.tsv (dedupe by key, keep latest)
    dd = {}
    for r in out:
        dd[r["key"]] = r
    cols = ["key", "path", "format", "bytes", "sha256", "status"]
    with open(fetched_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(dd.values())
    okn = sum(1 for r in dd.values() if r["path"])
    tot = sum(int(r["bytes"]) for r in dd.values() if str(r["bytes"]).isdigit())
    print(f"\nfetched {okn}/{len(dd)} ok; {tot/1e9:.2f} GB on disk")


if __name__ == "__main__":
    main()
