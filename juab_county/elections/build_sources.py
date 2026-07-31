#!/usr/bin/env python3
"""build_sources.py — regenerate sources.csv: a byte-verified provenance row for
EVERY retained raw in raw/ (zero unrecorded files). Each row carries the live
source URL, the on-disk byte count + sha256, and the channel (A Clerk / B Lt-Gov
/ C Enhanced-Voting API). Rerun after harvest_ev.py or adding a canvass PDF.
"""
import csv
import glob
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "sources.csv")
EV_BASE = "https://electionresults.utah.gov/results/public/api/elections/juab-county-ut"

# slug -> (election label). Mirrors harvest_ev.ELECTIONS.
EV_LABEL = {
    "2023-Nov-General": "2023 municipal general",
    "primary06252024": "2024 primary",
    "general11052024": "2024 general",
    "primary08122025": "2025 municipal primary",
    "general11042025": "2025 municipal general",
    "Primary06232026": "2026 primary",
}
# hand-recorded source URLs for the Channel A/B canvass PDFs
PDF_URLS = {
    "clerk/2023-09-05-primary-official.pdf":
        "https://juabcounty.gov/wp-content/uploads/2023/09/Official-Results-Prim-23.pdf",
    "clerk/2023-11-general-official.pdf":
        "https://juabcounty.gov/wp-content/uploads/2023/11/Gen-Election-Results-11-29.pdf",
    "clerk/2024-06-25-primary-canvass.pdf":
        "https://juabcounty.gov/wp-content/uploads/2024/07/24P-Canvass-Rpt.pdf",
    "clerk/2024-11-05-general-post-canvass.pdf":
        "https://juabcounty.gov/wp-content/uploads/2024/11/24G-Post-Canvass-Rpt.pdf",
    "ltgov/2024-primary-P24_Juab.pdf":
        "https://vote.utah.gov/wp-content/uploads/2024/08/P24_Juab.pdf",
    "ltgov/2024-general-G24_Canvass_Juab.pdf":
        "https://vote.utah.gov/wp-content/uploads/2024/11/G24_Canvass_Juab.pdf",
    "ltgov/2025-primary-P25_Canvass_Juab.pdf":
        "https://vote.utah.gov/wp-content/uploads/2025/08/P25_Canvass_Juab.pdf",
    "ltgov/2025-general-G25_Canvass_Juab.pdf":
        "https://vote.utah.gov/wp-content/uploads/2025/11/G25_Canvass_Juab.pdf",
}
PDF_CHANNEL = {"clerk": "A Juab County Clerk", "ltgov": "B Lt. Governor canvass cert"}
RETRIEVED = "2026-07-20"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ev_url(fname):
    # ev-juab-<slug>-ballot-items.json  |  ev-juab-<slug>-item-<id>.json
    stem = fname[len("ev-juab-"):]
    for slug in EV_LABEL:
        pre = slug + "-"
        if stem.startswith(pre):
            rest = stem[len(pre):]
            if rest == "ballot-items.json":
                return slug, f"{EV_BASE}/{slug}/ballot-items"
            if rest.startswith("item-"):
                cid = rest[len("item-"):-len(".json")]
                return slug, f"{EV_BASE}/{slug}/ballot-items/{cid}"
    return None, None


def main():
    rows = []
    # Channel C — EV JSON
    for p in sorted(glob.glob(os.path.join(RAW, "ev", "ev-juab-*.json"))):
        fname = os.path.basename(p)
        slug, url = ev_url(fname)
        rows.append(dict(
            source_file=os.path.relpath(p, HERE), channel="C Enhanced Voting API",
            election=EV_LABEL.get(slug, ""), url=url, bytes=os.path.getsize(p),
            sha256=sha256(p), retrieved=RETRIEVED,
            notes="ballot-items list" if fname.endswith("ballot-items.json")
                  else "per-contest precinct breakdown"))
    # Channels A + B — canvass PDFs
    for rel, url in PDF_URLS.items():
        p = os.path.join(RAW, rel)
        if not os.path.exists(p):
            continue
        chan = PDF_CHANNEL[rel.split("/")[0]]
        rows.append(dict(
            source_file=os.path.join("raw", rel), channel=chan, election="",
            url=url, bytes=os.path.getsize(p), sha256=sha256(p),
            retrieved=RETRIEVED,
            notes="official canvass PDF (raw retention + reconciliation)"))

    rows.sort(key=lambda r: (r["channel"], r["source_file"]))
    cols = ["source_file", "channel", "election", "url", "bytes", "sha256",
            "retrieved", "notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT}: {len(rows)} source rows")


if __name__ == "__main__":
    main()
