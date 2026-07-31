#!/usr/bin/env python3
"""Isolated backfill harvest of the Council's other deliberative bodies —
Council Work Session (265) + Committee of the Whole (180) — into db/staging_ws/
(SEPARATE from the main db/staging/, so the existing Council/RDA/MBA harvest is never
clobbered). build_db.py merges staging_ws AFTER the main bodies, so existing motion_ids
(and the 67 ordinance links to them) stay stable. Same 2-phase structure+votes pattern
as harvest_legistar.py.
"""
import csv, json, os, time, urllib.request

B = "https://webapi.legistar.com/v1/slco"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "staging_ws")
os.makedirs(OUT, exist_ok=True)
BODIES = {265: ("legislative", "Council Work Session"),
          180: ("legislative", "Committee of the Whole")}
SINCE = "2020-01-01"

EVENT_COLS = ["EventId", "EventDate", "EventBodyId", "EventBodyName",
              "EventMinutesStatusName", "EventMinutesFile", "EventAgendaFile",
              "EventInSiteURL", "_module"]
ITEM_COLS = ["EventItemId", "EventItemEventId", "_body_id", "EventItemTitle",
             "EventItemMatterId", "EventItemMatterName", "EventItemMatterType",
             "EventItemMover", "EventItemSeconder", "EventItemPassedFlagName",
             "EventItemActionName", "EventItemAgendaSequence", "EventItemMinutesSequence"]
VOTE_COLS = ["EventItemId", "_event_id", "_body_id", "VotePersonId", "VotePersonName",
             "VoteValueId", "VoteValueName"]


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                d = json.load(r)
            time.sleep(0.05)
            return d
        except Exception as e:
            if i == tries - 1:
                print("  ! give up:", repr(e)); return []
            time.sleep(3 * (i + 1))
    return []


def w(name, rows, cols):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader(); wr.writerows(rows)
    print("  wrote %-14s %d" % (name, len(rows)), flush=True)


def main():
    all_events = []
    for bid, (module, name) in BODIES.items():
        evs = get(f"{B}/events?$filter=EventBodyId%20eq%20{bid}%20and%20"
                  f"EventDate%20ge%20datetime'{SINCE}'"
                  f"&$select=EventId,EventDate,EventBodyId,EventBodyName,"
                  f"EventMinutesStatusName,EventMinutesFile,EventAgendaFile,EventInSiteURL")
        for e in evs:
            e["_module"] = module
        all_events += evs
        print(f"body {bid} {name}: {len(evs)} events", flush=True)
    w("events.csv", all_events, EVENT_COLS)

    all_items = []
    for i, e in enumerate(all_events, 1):
        its = get(f"{B}/events/{e['EventId']}/eventitems?$select=EventItemId,"
                  f"EventItemEventId,EventItemTitle,EventItemMatterId,"
                  f"EventItemMatterName,EventItemMatterType,EventItemMover,"
                  f"EventItemSeconder,EventItemPassedFlagName,EventItemActionName,"
                  f"EventItemAgendaSequence,EventItemMinutesSequence")
        for it in its:
            it["_body_id"] = e["EventBodyId"]
            all_items.append(it)
        if i % 25 == 0:
            print(f"  items: {i}/{len(all_events)} -> {len(all_items)}", flush=True)
    w("eventitems.csv", all_items, ITEM_COLS)

    votes = []
    passed = [it for it in all_items if it.get("EventItemPassedFlagName")]
    print(f"votes: {len(passed)} passed items", flush=True)
    for i, it in enumerate(passed, 1):
        for v in get(f"{B}/eventitems/{it['EventItemId']}/votes"):
            v["EventItemId"] = it["EventItemId"]
            v["_event_id"] = it["EventItemEventId"]
            v["_body_id"] = it["_body_id"]
            votes.append(v)
        if i % 50 == 0:
            w("votes.csv", votes, VOTE_COLS)
            print(f"  votes: {i}/{len(passed)} -> {len(votes)}", flush=True)
    w("votes.csv", votes, VOTE_COLS)
    print(f"DONE. events={len(all_events)} items={len(all_items)} votes={len(votes)}", flush=True)


if __name__ == "__main__":
    main()
