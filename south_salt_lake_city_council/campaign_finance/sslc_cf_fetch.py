#!/usr/bin/env python3
"""South Salt Lake campaign-finance ACQUISITION fetcher.

Parses the saved CivicPlus Archive-Center listing HTML (AMID 60/61/62/64) for
ADID->title, adds the 2021 state-tree files, builds a polite_fetch batch, and
downloads every filing into raw/ with a _fetch_log.jsonl.

Sources:
  - City Archive Center (sslc.gov/Archive.aspx?ADID=<n> -> ViewFile/Item/<n>):
      AMID=61  2025 Elections - Campaign Financial Disclosures
      AMID=62  2023 Elections - Campaign Financial Disclosures
      AMID=64  2026 Council Vacancies - Campaign Financial Disclosures (bonus)
      AMID=60  Current Elected Official (Conflict-of-Interest) Disclosures
  - State LG tree (municipal.utah.gov) 2021 South Salt Lake City folder.

Run from the campaign_finance/ dir. GET-only via scripts/polite_fetch.py.
"""
import csv, json, os, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
POLITE = os.path.abspath(os.path.join(HERE, "..", "..", ".claude", "skills",
                                      "expand-city-sources", "scripts", "polite_fetch.py"))
LISTINGS = os.path.join(HERE, "raw", "_listings")
NOW = "2026-07-14T00:00:00Z"

# AMID -> (cycle label used in filename prefix)
AMID_CYCLE = {"61": "2025", "62": "2023", "64": "2026vac", "60": "coi"}

# 2021 state-tree files (dir listing gave backslash paths; rewrite to https+/+encode)
STATE_2021 = [
    "Bynum, Sharla.pdf", "Christensen, Jake.pdf", "Garfield, Sam.pdf",
    "Hampton, Aileen.pdf", "Siwik, Shane.pdf", "Spencer, Olivia.pdf",
    "Thomas, Corey.pdf", "Williams, Clarissa.pdf", "Wood, Cherie.pdf",
]
STATE_BASE = "https://municipal.utah.gov/salt%20lake/2021/South%20Salt%20Lake%20City/"


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w]+", "-", s).strip("-").lower()
    return s


def parse_listing(amid):
    path = os.path.join(LISTINGS, f"archive_{amid}.html")
    html = open(path, encoding="utf-8", errors="replace").read()
    return re.findall(r'Archive\.aspx\?ADID=(\d+)".*?<span>([^<]+)</span>', html, re.S)


def main():
    entries = []  # dict: adid, cycle, title, url, name, source
    for amid, cycle in AMID_CYCLE.items():
        for adid, title in parse_listing(amid):
            title = re.sub(r"\s+", " ", title).strip()
            name = f"{cycle}_adid{adid}_{slug(title)}.pdf"
            entries.append(dict(adid=adid, amid=amid, cycle=cycle, title=title,
                                url=f"https://sslc.gov/Archive.aspx?ADID={adid}",
                                name=name, source="city_archive_center"))
    for fn in STATE_2021:
        surname = fn.split(",")[0]
        entries.append(dict(adid="", amid="", cycle="2021", title=fn[:-4],
                            url=STATE_BASE + fn.replace(", ", ",%20").replace(" ", "%20"),
                            name=f"2021_state_{slug(fn[:-4])}.pdf",
                            source="state_lg_municipal_disclosures"))

    # write metadata sidecar for the index builder
    with open(os.path.join(HERE, "_fetch_manifest.json"), "w") as f:
        json.dump(entries, f, indent=2)

    # batch file for polite_fetch (url,name)
    batch = os.path.join(HERE, "_batch.csv")
    with open(batch, "w", newline="") as f:
        w = csv.writer(f)
        for e in entries:
            w.writerow([e["url"], e["name"]])

    print(f"{len(entries)} files queued -> raw/")
    rc = subprocess.call([sys.executable, POLITE, "--batch", batch,
                          "--out", os.path.join(HERE, "raw"), "--now", NOW,
                          "--delay", "1.0"])
    sys.exit(rc)


if __name__ == "__main__":
    main()
