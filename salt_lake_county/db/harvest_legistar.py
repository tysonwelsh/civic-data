#!/usr/bin/env python3
"""Harvest the Salt Lake County Legistar structured record into db/staging/.

Salt Lake County Council is Legistar (client 'slco', webapi.legistar.com/v1/slco).
Recon 2026-07-11: the Council is TALLY-PRIMARY — minutes record "the motion carried
by a unanimous vote" (mover/seconder named, members NOT enumerated) EXCEPT where a
division is called, and those divided votes ARE the sparse EventItemVote records the
API exposes. So the Legistar harvest is the COMPLETE structured record: motion-level
spine (title/mover/seconder/passed/matter) for every action + named member votes for
the (few) divided votes. No minutes-prose vote parsing is needed or possible.

Emits staging CSVs (verbatim API fields): bodies, persons, events, eventitems, votes.
Idempotent full pull. Governance bodies only (growth-relevant): Council + its working
bodies (legislative module) and RDA + MBA (agencies module).
"""
import csv, json, os, time, urllib.request, urllib.error

B = "https://webapi.legistar.com/v1/slco"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "staging")
os.makedirs(OUT, exist_ok=True)

# body_id -> (module, canonical name). Legislative = Council + its own working bodies;
# agencies = the county's RDA + Municipal Building Authority.
# First pass: the vote-taking bodies (Council legislative + RDA/MBA agencies). The
# discussion/procedural bodies (Work Session 265, Committee of the Whole 180, Board of
# Canvassers 260) are backfilled in a later pass.
BODIES = {
    138: ("legislative", "County Council"),
    257: ("agencies",    "Redevelopment Agency"),
    258: ("agencies",    "Municipal Building Authority"),
}
SINCE = "2020-01-01"


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                data = json.load(r)
            time.sleep(0.05)   # light throttle — the API drops connections under load
            return data
        except Exception as e:                       # incl. RemoteDisconnected / ConnReset
            if i == tries - 1:
                print("  ! give up:", url, repr(e))
                return []
            time.sleep(3 * (i + 1))
    return []


def w(name, rows, cols):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    print("  wrote %-16s %d rows" % (name, len(rows)))


EVENT_COLS = ["EventId", "EventDate", "EventBodyId", "EventBodyName",
              "EventMinutesStatusName", "EventMinutesFile", "EventAgendaFile",
              "EventInSiteURL", "_module"]
ITEM_COLS = ["EventItemId", "EventItemEventId", "_body_id", "EventItemTitle",
             "EventItemMatterId", "EventItemMatterName", "EventItemMatterType",
             "EventItemMover", "EventItemSeconder", "EventItemPassedFlagName",
             "EventItemActionName", "EventItemAgendaSequence", "EventItemMinutesSequence"]
VOTE_COLS = ["EventItemId", "_event_id", "_body_id", "VotePersonId", "VotePersonName",
             "VoteValueId", "VoteValueName"]


def main():
    bodies = get(B + "/bodies?$select=BodyId,BodyName,BodyTypeName,BodyActiveFlag")
    w("bodies.csv", bodies, ["BodyId", "BodyName", "BodyTypeName", "BodyActiveFlag"])
    persons = get(B + "/persons?$select=PersonId,PersonFullName,PersonLastName,PersonActiveFlag")
    w("persons.csv", persons, ["PersonId", "PersonFullName", "PersonLastName", "PersonActiveFlag"])

    # --- Phase A: structure (events + eventitems) — flush IMMEDIATELY so the rest of
    #     the build (minutes, motion spine, federation) can proceed before votes finish.
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
            print(f"  eventitems: {i}/{len(all_events)} events -> {len(all_items)} items",
                  flush=True)
    w("eventitems.csv", all_items, ITEM_COLS)
    print(f"STRUCTURE DONE: {len(all_events)} events, {len(all_items)} items", flush=True)

    # --- Phase B: votes — resumable + incremental (only passed items carry any; most
    #     return empty, so a disconnect must not lose accumulated rows).
    vpath = os.path.join(OUT, "votes.csv")
    all_votes, done = [], set()
    if os.path.exists(vpath):
        all_votes = list(csv.DictReader(open(vpath, encoding="utf-8")))
        done = {v["EventItemId"] for v in all_votes}
    passed = [it for it in all_items
              if it.get("EventItemPassedFlagName") and it["EventItemId"] not in done]
    print(f"VOTES: {len(passed)} passed items to check", flush=True)
    for i, it in enumerate(passed, 1):
        vs = get(f"{B}/eventitems/{it['EventItemId']}/votes")
        for v in vs:
            v["EventItemId"] = it["EventItemId"]
            v["_event_id"] = it["EventItemEventId"]
            v["_body_id"] = it["_body_id"]
        all_votes += vs
        if i % 50 == 0:
            w("votes.csv", all_votes, VOTE_COLS)
            print(f"  votes: {i}/{len(passed)} items -> {len(all_votes)} vote rows", flush=True)
    w("votes.csv", all_votes, VOTE_COLS)
    print(f"DONE. vote rows={len(all_votes)}", flush=True)


if __name__ == "__main__":
    main()
