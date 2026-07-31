#!/usr/bin/env python3
"""FLOOR-vote recovery for the SHELL sessions (2025GS + 2026GS).

The 2025GS and 2026GS bill STATIC pages (le.utah.gov/~<YR>/bills/static/*.html) are broken
SHELLS: their served HTML is a JS-injected skeleton whose only vote links sit inside HTML
COMMENTS as stale 2024 placeholder rows (harvest_bills.py strips comments, so those pages
correctly yield ZERO roll calls — never fabricate). The real vote pages exist and are
reachable directly: `DynaBill/svotes.jsp?sessionid=<SESSION>&voteid=<N>&house=<H|S>`, and
each self-identifies its bill in the page header. voteid is scoped PER HOUSE, so both are
crawled. We sweep the voteid space, keep only roll calls whose bill is in the land-use/
housing subset, and emit rollcalls_recovered.csv / votes_recovered.csv (same columns as the
main CSVs; string rollcall_ids 'REC_<session>_<H>_<voteid>' so they never collide).
build_db.py concatenates them.

COMMITTEE (mtgvotes) votes for these two sessions are a residual gap — that global voteid
sequence is not session-scoped — left for the closing pass (see recon.md / CLAUDE.md).
Resumable (cached pages reused). cp1252-safe.
"""
import csv, os, re
from harvest_bills import fetch, parse_svotes, BASE, VOTEPAGES

HERE = os.path.dirname(os.path.abspath(__file__))
SESSIONS = ["2025GS", "2026GS"]
MAXVOTE = 1900     # observed floor voteids top out well under this


def subset_bills(session):
    return {r["bill_no"] for r in csv.DictReader(open(os.path.join(HERE, "bills_all.csv")))
            if r["session"] == session and r["relevance"]}


def parse_header(html):
    lines = [l.strip() for l in re.sub(r"<[^>]+>", "\n", html).split("\n") if l.strip()]
    bill = lines[1] if len(lines) > 1 and re.match(r"[HS][BJC]R?\d{4}", lines[1]) else ""
    date = ""
    for l in lines[:8]:
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", l)
        if m:
            date = m.group(1); break
    return bill, date


def crawl(session, rc_out, v_out):
    subset = subset_bills(session)
    found = set()
    print("%s subset bills: %d" % (session, len(subset)))
    for house in ("H", "S"):
        misses = 0
        for vid in range(1, MAXVOTE + 1):
            url = "%s/DynaBill/svotes.jsp?sessionid=%s&voteid=%d&house=%s" % (BASE, session, vid, house)
            cache = os.path.join(VOTEPAGES, "rec_%s_%s_%d.html" % (session, house, vid))
            html = fetch(url, cache)
            bill, date = parse_header(html) if html else ("", "")
            if not bill:
                misses += 1
                if misses > 120 and vid > 300:
                    break
                continue
            misses = 0
            if bill not in subset:
                continue
            p = parse_svotes(html)
            if p["yeas"] is None:
                continue
            rc_id = "REC_%s_%s_%d" % (session, house, vid)
            found.add(bill)
            chamber = "House" if house == "H" else "Senate"
            rc_out.append(dict(rollcall_id=rc_id, session=session, bill_no=bill, date=date,
                               chamber=chamber, committee="", body_name=chamber,
                               vote_type="floor", motion_desc=p["motion"] or "Floor vote",
                               action="",
                               result="Pass" if (p["yeas"] or 0) > (p["nays"] or 0) else "Fail",
                               yeas=p["yeas"], nays=p["nays"], absent=p["absent"],
                               recorded=1, source_url=url))
            for val, lst in (("Yea", p["yea"]), ("Nay", p["nay"]), ("Absent", p["absent_n"])):
                for nm in lst:
                    v_out.append(dict(rollcall_id=rc_id, session=session, bill_no=bill,
                                      legislator_verbatim=nm, chamber=chamber,
                                      district="", party="", vote_value=val))
    print("  %s recovered: bills %d/%d (no floor roll call for: %s)"
          % (session, len(found), len(subset), sorted(subset - found)))


def main():
    rc_out, v_out = [], []
    for s in SESSIONS:
        crawl(s, rc_out, v_out)
    with open(os.path.join(HERE, "rollcalls_recovered.csv"), "w", newline="") as f:
        cols = ["rollcall_id", "session", "bill_no", "date", "chamber", "committee",
                "body_name", "vote_type", "motion_desc", "action", "result",
                "yeas", "nays", "absent", "recorded", "source_url"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in rc_out:
            w.writerow(r)
    with open(os.path.join(HERE, "votes_recovered.csv"), "w", newline="") as f:
        cols = ["rollcall_id", "session", "bill_no", "legislator_verbatim",
                "chamber", "district", "party", "vote_value"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in v_out:
            w.writerow(r)
    print("\nSHELL-SESSION FLOOR recovery: %d rollcalls, %d votes" % (len(rc_out), len(v_out)))


if __name__ == "__main__":
    main()
