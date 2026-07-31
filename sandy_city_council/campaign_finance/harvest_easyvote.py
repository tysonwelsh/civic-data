#!/usr/bin/env python3
"""Harvest Sandy City campaign-finance filings from the EasyVote public API.

Replicates polite_fetch.py discipline (browser UA, >=1s throttle, verbatim bytes,
sha256 + JSONL provenance log) but adds the two headers the EasyVote public API
requires (Easy-Vote-Authenticated-User, ZUMO-API-VERSION) which polite_fetch cannot send.
GET-only, public records only.
"""
import json, os, re, time, hashlib, urllib.request, urllib.error

CID  = "07F88007-99BF-4B37-B0D3-2CFDD2EEAED3"
WUSER= "9243025B-A823-469F-B394-E04A7C95BA39"
AUTH = f"UserId:{WUSER}|CustomerId:{CID}|ZumoToken:"
API  = "https://ecf-api.easyvoteapp.com"
ORIGIN = "https://sandycityut.easyvotecampaignfinance.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact repo owner)")
NOW = "2026-07-05T12:00:00Z"
OUTDIR = "/Users/tysonwelsh/civic-data/sandy_city_council/campaign_finance/raw/easyvote"
LOG = os.path.join(OUTDIR, "_fetch_log.jsonl")

os.makedirs(OUTDIR, exist_ok=True)

def req(url, save_path=None):
    r = urllib.request.Request(url, headers={
        "User-Agent": UA, "Origin": ORIGIN,
        "Easy-Vote-Authenticated-User": AUTH, "ZUMO-API-VERSION": "2.0.0",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                body = resp.read()
                rec = {"url": url, "final_url": resp.geturl(), "status": resp.status,
                       "content_type": resp.headers.get("Content-Type",""),
                       "bytes": len(body),
                       "sha256": hashlib.sha256(body).hexdigest(),
                       "retrieved_utc": NOW}
                if save_path:
                    with open(save_path, "wb") as f: f.write(body)
                    rec["saved"] = os.path.relpath(save_path, OUTDIR)
                with open(LOG, "a") as lf: lf.write(json.dumps(rec)+"\n")
                return body, rec
        except urllib.error.HTTPError as e:
            if e.code in (429,503) and attempt < 3:
                time.sleep(3*(attempt+1)); continue
            rec = {"url": url, "status": e.code, "error": str(e), "retrieved_utc": NOW}
            with open(LOG, "a") as lf: lf.write(json.dumps(rec)+"\n")
            return None, rec
        except Exception as e:
            if attempt < 3:
                time.sleep(2*(attempt+1)); continue
            rec = {"url": url, "status": None, "error": str(e), "retrieved_utc": NOW}
            with open(LOG, "a") as lf: lf.write(json.dumps(rec)+"\n")
            return None, rec

def slug(s):
    s = re.sub(r"[^A-Za-z0-9]+","-", (s or "").strip()).strip("-")
    return s[:50] or "doc"

# 1. re-fetch + save the API listing as provenance
body, _ = req(f"{API}/filer/documentsearch/{CID}",
              os.path.join(OUTDIR, "_api_documentsearch.json"))
req(f"{API}/authentication/getwebsiteuser/sandycityut",
    os.path.join(OUTDIR, "_api_getwebsiteuser.json"))
time.sleep(1.2)
filers = json.loads(body)

manifest = []
for f in filers:
    last = slug(f.get("lastname") or f.get("committeename") or "unknown")
    for d in (f.get("documents") or []):
        did = d["documentid"]
        # datesubmitted MM/DD/YY -> YYYYMM
        mm,dd,yy = d["datesubmitted"].split("/")
        yyyymm = f"20{yy}{mm}"
        fname = f"{yyyymm}_{last}_{slug(d['documentname'])}_{did[:8]}.pdf"
        path = os.path.join(OUTDIR, fname)
        url = f"{API}/documents/{did}/viewfinalredactedpdf"
        _, rec = req(url, path)
        ok = rec.get("status")==200 and (rec.get("content_type","").startswith("application/pdf"))
        manifest.append({**d, "filer": f["displayname"].strip(),
                         "firstname": f.get("firstname","").strip(),
                         "lastname": f.get("lastname","").strip(),
                         "office": f.get("officename",""), "filertype": f.get("filertype",""),
                         "fname": fname, "url": url, "status": rec.get("status"),
                         "bytes": rec.get("bytes"), "sha256": rec.get("sha256"),
                         "content_type": rec.get("content_type"), "ok": ok})
        print(("OK " if ok else "!! ") + fname + f"  [{rec.get('status')} {rec.get('bytes')}b]")
        time.sleep(1.2)

with open(os.path.join(OUTDIR, "_manifest.json"),"w") as mf:
    json.dump(manifest, mf, indent=1)
n_ok = sum(1 for m in manifest if m["ok"])
print(f"\nDONE: {n_ok}/{len(manifest)} PDFs OK")
