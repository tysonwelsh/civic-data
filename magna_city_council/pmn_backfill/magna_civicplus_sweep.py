#!/usr/bin/env python3
"""Magna CivicPlus AgendaCenter sweep (angle a: ArchivedMinutes probe).

The AgendaCenter/Search endpoint is GET-accessible (no POST needed):
  /AgendaCenter/Search?term=&CIDs=3&startDate=MM/DD/YYYY&endDate=MM/DD/YYYY
Enumerate every meeting's Minutes-slot ViewFile id across all years, and for each
meeting also record whether a PreviousVersions page exposes an ArchivedMinutes slot
(the SSL lesson: recorded minutes hiding behind a packet/draft in the Minutes slot).

Outputs work/civicplus_minutes.json (date -> [{id, kind}]).
"""
import subprocess, sys, os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
FETCH = "/Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/polite_fetch.py"

def fetch(url, name):
    subprocess.run([sys.executable, FETCH, "--out", WORK, "--name", name, url],
                   check=True, capture_output=True)
    return open(os.path.join(WORK, name), encoding="utf-8", errors="replace").read()

def mmddyyyy_to_iso(s):
    m, d, y = s[:2], s[2:4], s[4:8]
    return f"{y}-{m}-{d}"

def main():
    minutes = {}   # iso date -> set of viewfile ids
    archived = {}  # iso date -> set of archivedminutes ids
    for yr in range(2022, 2027):
        html = fetch(f"https://magna.utah.gov/AgendaCenter/Search?term=&CIDs=3"
                     f"&startDate=01/01/{yr}&endDate=12/31/{yr}", f"ac_search_{yr}.html")
        for m in re.finditer(r'ViewFile/Minutes/_(\d{8})-(\d+)', html):
            minutes.setdefault(mmddyyyy_to_iso(m.group(1)), set()).add(m.group(2))
        for m in re.finditer(r'ViewFile/ArchivedMinutes/_(\d{8})-(\d+)', html):
            archived.setdefault(mmddyyyy_to_iso(m.group(1)), set()).add(m.group(2))
    out = {"minutes": {k: sorted(v) for k, v in minutes.items()},
           "archived_in_search": {k: sorted(v) for k, v in archived.items()}}
    json.dump(out, open(os.path.join(WORK, "civicplus_minutes.json"), "w"), indent=1)
    print(f"CivicPlus Minutes-slot dates 2022-2026: {len(minutes)}")
    print(f"ArchivedMinutes seen directly in Search listings: {len(archived)}")
    print("dates:", ", ".join(sorted(minutes)))

if __name__ == "__main__":
    main()
