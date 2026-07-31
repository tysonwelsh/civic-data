#!/usr/bin/env python3
"""harvest_ev.py — mirror the Juab County Enhanced Voting (state) results API to
raw/ev/. Channel C of the three official election channels (see recon.md).

For each election slug: fetch /ballot-items (all contests + summary candidate
totals) and, for every contest, /ballot-items/<id> (per-precinct breakdown).
Raws are the immutable source of truth for build_elections.py — never hand-edit.

Host: electionresults.utah.gov/results/public/api ; jurisdiction slug juab-county-ut.
Idempotent: re-running re-fetches and overwrites the raw JSON (verify byte churn).
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "ev")
BASE = "https://electionresults.utah.gov/results/public/api/elections/juab-county-ut"

# (slug, year, election_type) — the governance-relevant Juab elections the EV
# portal carries (2023+). primary09052023_Demo is an EMPTY placeholder (all
# voteTotal=0) — the real 2023 municipal primary lives only in the Clerk PDF
# (build_elections.py hand-keys it). primary03052024 (presidential preference)
# and PrimaryCD2Recount2024 (a CD2 recount) are out of governance scope.
ELECTIONS = [
    ("2023-Nov-General", 2023, "municipal general"),
    ("primary06252024",  2024, "primary"),
    ("general11052024",  2024, "general"),
    ("primary08122025",  2025, "municipal primary"),
    ("general11042025",  2025, "municipal general"),
    ("Primary06232026",  2026, "primary"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "civic-data/juab"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 — API drops connections under load
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    return None


def nm(x):
    if isinstance(x, list):
        for e in x:
            if e.get("languageId") == "en":
                return e["text"]
        return x[0]["text"] if x else ""
    return x


def main():
    os.makedirs(RAW, exist_ok=True)
    for slug, year, etype in ELECTIONS:
        bi_raw = get(f"{BASE}/{slug}/ballot-items")
        bi_path = os.path.join(RAW, f"ev-juab-{slug}-ballot-items.json")
        with open(bi_path, "wb") as f:
            f.write(bi_raw)
        items = json.loads(bi_raw)["data"]
        print(f"{slug} ({year} {etype}): {len(items)} contests")
        for it in items:
            cid = it["id"]
            det = get(f"{BASE}/{slug}/ballot-items/{cid}")
            with open(os.path.join(RAW, f"ev-juab-{slug}-item-{cid}.json"), "wb") as f:
                f.write(det)
            time.sleep(0.05)
        print(f"  fetched {len(items)} contest details")


if __name__ == "__main__":
    main()
