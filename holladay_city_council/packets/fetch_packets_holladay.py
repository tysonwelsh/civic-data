#!/usr/bin/env python3
"""fetch_packets_holladay.py — download SuiteOne agenda packets into raw/<date>/.

Reads events_inscope.tsv (from parse_suiteone_events_holladay.py); for every row with
an `apid`, GETs the whole-meeting agenda packet
    https://holladayut.suiteonemedia.com/event/GetAgendaPacketFile/Packet?apid=<APID>
via the shared polite_fetch.save() (browser UA, throttled, logged) into
    raw/<date>/<body>_e<eventid>_packet.pdf
with a per-date _fetch_log.jsonl. A running BUDGET guard flips remaining packets to
index-only (stored=no) once cumulative stored bytes would exceed the cap — nothing is
ever silently dropped; every event is emitted to fetch_results.tsv.

SuiteOne quirks (verified 2026-07-13):
  - HEAD -> 404 and Range is ignored, so Content-Length is only knowable from a full GET.
  - Both path labels work: .../GetAgendaPacketFile/Packet?apid= == .../Agenda%20Packet?apid=
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "expand-city-sources", "scripts"))
import polite_fetch  # noqa: E402

BASE = "https://holladayut.suiteonemedia.com"
BUDGET = 1_450_000_000  # ~1.45 GB stored ceiling for this dataset
NOW = "2026-07-13T00:00:00Z"


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "events_inscope.tsv")), delimiter="\t")
            if r["apid"]]
    rows.sort(key=lambda r: (r["date"], r["body"]))
    out = csv.writer(open(os.path.join(HERE, "fetch_results.tsv"), "w"), delimiter="\t")
    out.writerow(["date", "body", "eventid", "apid", "bytes", "sha256", "status",
                  "content_type", "stored", "path"])
    total = 0
    stored_n = idx_n = 0
    for r in rows:
        date, body, eid, apid = r["date"], r["body"], r["eventid"], r["apid"]
        url = f"{BASE}/event/GetAgendaPacketFile/Packet?apid={apid}"
        ref = f"{BASE}/event/?id={eid}"
        name = f"{body}_e{eid}_packet.pdf"
        outdir = os.path.join(HERE, "raw", date)
        if total >= BUDGET:
            out.writerow([date, body, eid, apid, "", "", "budget_skip", "", "no", ""])
            idx_n += 1
            continue
        rec = polite_fetch.save(url, outdir, name=name, referer=ref, now=NOW)
        if rec["ok"]:
            total += rec["bytes"]
            stored_n += 1
            path = f"raw/{date}/{name}"
            out.writerow([date, body, eid, apid, rec["bytes"], rec["sha256"],
                          rec["status"], rec["content_type"], "yes", path])
            print(f"ok   {date} {body:16s} {rec['bytes']/1e6:7.2f}MB  total={total/1e6:8.1f}MB")
        else:
            out.writerow([date, body, eid, apid, rec["bytes"], "", rec["status"],
                          rec.get("content_type", ""), "no", ""])
            print(f"FAIL {date} {body:16s} status={rec['status']}")
    print(f"\nstored={stored_n} index_only(budget)={idx_n} total={total/1e6:.1f}MB")


if __name__ == "__main__":
    main()
