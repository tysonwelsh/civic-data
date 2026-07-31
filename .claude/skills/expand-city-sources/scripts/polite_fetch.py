#!/usr/bin/env python3
"""Polite, throttled public-records fetcher for the expand-city-sources skill.

Every raw original this repo keeps must be fetched through a *polite* GET: browser
User-Agent, optional Referer, rate-limited, retried, and LOGGED so provenance is
reproducible. This is the one place that discipline lives — call it, don't reinvent it.

Design rules (see SKILL.md "BE A POLITE SCRAPER"):
  - GET only. No POST, no auth, no bypassing. Public records only.
  - Default >=1.0s between requests to the same host (--delay to raise, never lower for prod).
  - Retries with backoff on transient errors; honors an obvious rate-limit (429/503).
  - Writes bytes verbatim to <outdir>/<name>; never rewrites/normalizes the payload.
  - Appends one JSONL line per attempt to <outdir>/_fetch_log.jsonl (url, status,
    bytes, sha256, content_type, final_url, retrieved_utc). That log IS the provenance.

Usage:
    # single URL -> saved into a raw/ dir, filename inferred or given
    python3 polite_fetch.py --out <raw_dir> [--name file.pdf] [--referer URL] <URL>

    # batch: a CSV/TSV or newline list on stdin, columns: url[,name]
    python3 polite_fetch.py --out <raw_dir> --batch urls.csv

    # just probe (HEAD-like GET, save nothing) to check liveness/content-type
    python3 polite_fetch.py --probe <URL>

Timestamps: pass --now "YYYY-MM-DDTHH:MM:SSZ" to stamp the log deterministically;
otherwise the wall clock is used. (Agents running under a frozen clock must pass --now.)
"""
import argparse, csv, hashlib, json, os, re, sys, time
from urllib.parse import urlparse, unquote

try:
    import requests
except ImportError:
    sys.exit("requests not available: pip install requests")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact repo owner)")


def utc_now(explicit):
    if explicit:
        return explicit
    # time.gmtime is allowed; deterministic-clock agents should pass --now instead.
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def infer_name(url, resp=None):
    # Prefer Content-Disposition, else the URL path tail, else a hash.
    if resp is not None:
        cd = resp.headers.get("content-disposition", "")
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
        if m:
            return unquote(m.group(1)).strip()
    tail = unquote(os.path.basename(urlparse(url).path)) or ""
    tail = re.sub(r"[^\w.\- ]+", "_", tail).strip()
    if tail and "." in tail:
        return tail
    ext = ".pdf"
    if resp is not None:
        ct = resp.headers.get("content-type", "")
        if "html" in ct: ext = ".html"
        elif "json" in ct: ext = ".json"
        elif "pdf" in ct: ext = ".pdf"
        elif "xml" in ct: ext = ".xml"
    return (tail or hashlib.sha1(url.encode()).hexdigest()[:16]) + ext


def s3_normalize(url):
    """Rewrite a virtual-host S3 URL to path-style when the bucket contains an
    underscore. Python `requests`/TLS rejects `bucket_name.s3.amazonaws.com` (the
    underscore makes the cert hostname invalid); path-style `s3.amazonaws.com/bucket_name`
    works. Granicus attachment buckets (e.g. `granicus_production_attachments`) need this.
    No-op for any other URL."""
    m = re.match(r"^(https?)://([a-z0-9.\-_]+)\.s3([.\-][a-z0-9\-]+)?\.amazonaws\.com(/.*)?$",
                 url, re.I)
    if not m:
        return url
    scheme, bucket, region, path = m.group(1), m.group(2), m.group(3) or "", m.group(4) or "/"
    if "_" not in bucket:
        return url
    host = "s3%s.amazonaws.com" % (region if region else "")
    return "%s://%s/%s%s" % (scheme, host, bucket, path)


def content_length(url, referer=None, timeout=30):
    """Best-effort size probe via HEAD; returns int bytes or None if unknown."""
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    try:
        r = requests.head(s3_normalize(url), headers=headers, timeout=timeout,
                          allow_redirects=True)
        cl = r.headers.get("content-length")
        return int(cl) if cl and cl.isdigit() else None
    except requests.RequestException:
        return None


def fetch(url, referer=None, delay=1.0, retries=4, timeout=60):
    url = s3_normalize(url)
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    last = None
    for attempt in range(retries):
        if attempt:
            time.sleep(delay * (2 ** attempt))  # backoff
        try:
            r = requests.get(url, headers=headers, timeout=timeout,
                             allow_redirects=True, stream=False)
            if r.status_code in (429, 503):
                wait = float(r.headers.get("retry-after", delay * (2 ** (attempt + 1))) or 0)
                time.sleep(min(wait, 60))
                last = r
                continue
            return r
        except requests.RequestException as e:
            last = e
    if isinstance(last, requests.Response):
        return last
    raise last if last else RuntimeError("no response")


def save(url, outdir, name=None, referer=None, delay=1.0, now=None, max_bytes=None):
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    # Oversize skip: probe Content-Length first so we never download the big body.
    if max_bytes:
        size = content_length(url, referer=referer)
        if size is not None and size > max_bytes:
            rec = {"url": url, "final_url": None, "status": None, "content_type": None,
                   "bytes": size, "sha256": "", "saved_as": None, "ok": False,
                   "skipped_oversize": True, "max_bytes": max_bytes,
                   "elapsed_s": round(time.time() - t0, 2), "retrieved_utc": utc_now(now)}
            with open(os.path.join(outdir, "_fetch_log.jsonl"), "a") as log:
                log.write(json.dumps(rec) + "\n")
            time.sleep(delay)
            return rec
    r = fetch(url, referer=referer, delay=delay)
    body = r.content if r is not None else b""
    ok = r is not None and r.status_code == 200 and body
    name = name or infer_name(url, r)
    dest = os.path.join(outdir, name)
    sha = hashlib.sha256(body).hexdigest() if body else ""
    if ok:
        with open(dest, "wb") as f:
            f.write(body)
    rec = {
        "url": url,
        "final_url": (r.url if r is not None else None),
        "status": (r.status_code if r is not None else None),
        "content_type": (r.headers.get("content-type") if r is not None else None),
        "bytes": len(body),
        "sha256": sha,
        "saved_as": (name if ok else None),
        "ok": bool(ok),
        "elapsed_s": round(time.time() - t0, 2),
        "retrieved_utc": utc_now(now),
    }
    with open(os.path.join(outdir, "_fetch_log.jsonl"), "a") as log:
        log.write(json.dumps(rec) + "\n")
    time.sleep(delay)  # be polite between calls
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--name")
    ap.add_argument("--referer")
    ap.add_argument("--batch", help="CSV/TSV or newline list; columns url[,name]")
    ap.add_argument("--probe", help="fetch and report headers only; save nothing")
    ap.add_argument("--size-only", dest="size_only",
                    help="HEAD-probe Content-Length only (no body GET) — for sizing large PDFs")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--max-bytes", type=int, dest="max_bytes",
                    help="skip + log files whose Content-Length exceeds this (e.g. 4000000)")
    ap.add_argument("--now", help="freeze retrieved_utc (YYYY-MM-DDTHH:MM:SSZ)")
    a = ap.parse_args()

    if a.size_only:
        size = content_length(a.size_only, referer=a.referer)
        print(json.dumps({"url": a.size_only, "content_length": size,
                          "size_mb": (round(size/1e6, 2) if size is not None else None)}, indent=2))
        return

    if a.probe:
        r = fetch(a.probe, referer=a.referer, delay=a.delay)
        print(json.dumps({"url": a.probe, "final_url": r.url, "status": r.status_code,
                          "content_type": r.headers.get("content-type"),
                          "bytes": len(r.content)}, indent=2))
        return

    if not a.out:
        sys.exit("--out <raw_dir> is required (except --probe)")

    if a.batch:
        with open(a.batch) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Skip a header row ("url,name") — treating it as a URL crashes
                # the whole batch (sandy pilot 2026-07-16).
                if line.split(",", 1)[0].strip().lower() in ("url", "source_url"):
                    continue
                # Parse as real CSV (or TSV) so a quoted, comma-bearing name
                # ("Staff report, documents and map.pdf") arrives WITHOUT its
                # quote characters — the old naive [\t,] split let CSV quoting
                # reach disk, dodging extension filters (magna 2026-07-13 bug).
                if "\t" in line:
                    parts = line.split("\t", 1)
                else:
                    row = next(csv.reader([line]))
                    # >2 fields = an UNQUOTED comma-bearing name; rejoin the tail.
                    parts = [row[0], ",".join(row[1:])] if len(row) > 2 else row
                url = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
                rec = save(url, a.out, name=name, referer=a.referer, delay=a.delay,
                           now=a.now, max_bytes=a.max_bytes)
                tag = "SKIP" if rec.get("skipped_oversize") else ("ok  " if rec["ok"] else "FAIL")
                print(f'{tag} {rec["status"]}  {url}  -> {rec["saved_as"]}')
        return

    if not a.url:
        sys.exit("provide a URL, --batch FILE, or --probe URL")
    rec = save(a.url, a.out, name=a.name, referer=a.referer, delay=a.delay,
               now=a.now, max_bytes=a.max_bytes)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
