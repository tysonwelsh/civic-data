#!/usr/bin/env python3
"""harvest.py — pull Salt Lake City municipal campaign-finance FILINGS from the city's
own Campaign Finance Reporting System (an Angular SPA backed by a JSON WebAPI).

SOURCE (discovered 2026-07-05):
  Portal shell : https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/#/Candidates/Contribution
  JSON WebAPI  : https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/
  (endpoints reverse-engineered from app/Services/campaign-finance.service.js)

The portal stores NO per-filing PDFs — a "filing" is a candidate's electronic disclosure
for one election cycle, exposed as JSON. This harvester RETAINS the JSON payloads verbatim
as the raw documents (raw/*.json) and logs provenance (raw/_fetch_log.jsonl). It does NOT
parse contributions/expenditures into structured tables — that is a separate planned layer.
build_index.py turns the retained JSON into text/ sidecars + index.csv.

GET-only, browser UA, >=3s between calls, retries with backoff. Public records only.

Usage:
  python3 harvest.py            # full in-scope harvest (council+mayor, 2019-2025)
  python3 harvest.py --probe    # just GetElections, print the election list, save nothing
  python3 harvest.py --all-years # ignore the year scope (grab every election on the portal)
"""
import argparse, json, os, sys, time, hashlib
import urllib.request, urllib.error

BASE = "https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/"
PORTAL = "https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/#/Candidates/Contribution"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact repo owner)")
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
LOG = os.path.join(RAW, "_fetch_log.jsonl")
DELAY = 3.0
SCOPE_YEARS = {2019, 2021, 2023, 2025}
SCOPE_OFFICES = None  # filter applied in build_index (keep all raw)


def now_utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get(endpoint, params=None, save_as=None, retries=4):
    """GET a WebAPI endpoint; return parsed JSON (or None). Saves raw bytes to raw/<save_as>
    and appends a provenance line to _fetch_log.jsonl."""
    url = BASE + endpoint
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    os.makedirs(RAW, exist_ok=True)
    last = None
    for attempt in range(retries):
        if attempt:
            time.sleep(DELAY * (2 ** attempt))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                status = r.status
                ct = r.headers.get("content-type", "")
                final = r.geturl()
                break
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            status, ct, final, last = e.code, e.headers.get("content-type", "") if e.headers else "", url, e
            if status in (429, 503):
                time.sleep(DELAY * (2 ** (attempt + 1)))
                continue
            break
        except Exception as e:
            last = e
            body, status, ct, final = b"", None, "", url
    ok = status == 200 and ct and "json" in ct.lower()
    rec = {"url": url, "final_url": final, "status": status, "content_type": ct,
           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest() if body else "",
           "saved_as": save_as if ok else None, "ok": bool(ok), "retrieved_utc": now_utc()}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    time.sleep(DELAY)
    if not ok:
        sys.stderr.write(f"  ! {endpoint} status={status} ct={ct} bytes={len(body)}\n")
        return None
    if save_as:
        with open(os.path.join(RAW, save_as), "wb") as f:
            f.write(body)
    try:
        return json.loads(body)
    except Exception:
        return None


def election_year(e):
    for k in ("ElectionYear", "electionYear", "Year", "year"):
        if isinstance(e, dict) and e.get(k):
            return int(e[k])
    return None


def election_id(e):
    for k in ("ElectionId", "electionId", "Id", "id"):
        if isinstance(e, dict) and e.get(k) is not None:
            return e[k]
    return None


def cand_id(c):
    for k in ("CandidateId", "candidateId", "Id", "id"):
        if isinstance(c, dict) and c.get(k) is not None:
            return c[k]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--all-years", action="store_true")
    a = ap.parse_args()

    print(f"GetElections ...")
    elections = get("GetElections", save_as="elections.json")
    if elections is None:
        print("PORTAL UNAVAILABLE (GetElections failed — likely 503 maintenance). "
              "Re-run when the .NET backend is up; static assets alone won't do.")
        sys.exit(2)
    if isinstance(elections, dict):
        # some WebAPIs wrap the list
        for k in ("Elections", "elections", "data", "value"):
            if isinstance(elections.get(k), list):
                elections = elections[k]
                break
    print(f"  {len(elections)} elections")
    for e in elections:
        print("   ", election_id(e), election_year(e),
              {k: e.get(k) for k in list(e)[:6]} if isinstance(e, dict) else e)
    if a.probe:
        return

    in_scope = [e for e in elections
                if a.all_years or (election_year(e) in SCOPE_YEARS)]
    print(f"\nHarvesting {len(in_scope)} in-scope elections "
          f"({'ALL years' if a.all_years else sorted(SCOPE_YEARS)})")

    for e in in_scope:
        eid, yr = election_id(e), election_year(e)
        print(f"\n== election {eid} ({yr}) ==")
        get("GetPeriodsByElection", {"pElectionId": eid}, save_as=f"periods_e{eid}.json")
        cands = get("GetCandidatesByElection", {"pElectionId": eid},
                    save_as=f"candidates_e{eid}.json")
        if not isinstance(cands, list):
            if isinstance(cands, dict):
                for k in ("Candidates", "candidates", "data", "value"):
                    if isinstance(cands.get(k), list):
                        cands = cands[k]; break
        if not isinstance(cands, list):
            print("   (no candidate list)"); continue
        print(f"   {len(cands)} candidates")
        cyc_end = ""
        if isinstance(e, dict):
            cyc_end = (e.get("CycleEndDate") or e.get("cycleEndDate") or "")[:10]
        thru = cyc_end or time.strftime("%Y-%m-%d")
        for c in cands:
            cid = cand_id(c)
            name = c.get("FullName") or f"{c.get('FirstName','')} {c.get('LastName','')}".strip() \
                if isinstance(c, dict) else str(cid)
            tag = f"e{eid}_c{cid}"
            # The candidate's overall disclosure summary = the "summary" filing document.
            get("GetElectionSummaryByCandidate", {"pElectionId": eid, "pCandidateId": cid},
                save_as=f"summary_{tag}.json")
            get("GetFinancialInfo", {"pElectionId": eid, "pCandidateId": cid, "pThruDate": thru},
                save_as=f"financial_{tag}.json")
            # Full contribution + expenditure filing lists = retained as raw documents.
            get("GetContributionsByElectionCandidate",
                {"pElectionId": eid, "pCandidateId": cid, "pThruDate": thru},
                save_as=f"contributions_{tag}.json")
            get("GetExpendituresByElectionCandidate",
                {"pElectionId": eid, "pCandidateId": cid, "pThruDate": thru},
                save_as=f"expenditures_{tag}.json")
            print(f"     · {name} (c{cid})")
    print("\nDONE. Next: python3 build_index.py")


if __name__ == "__main__":
    main()
