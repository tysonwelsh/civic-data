#!/usr/bin/env python3
"""
Sandy incremental refresh — Granicus Legistar (sandyutah.legistar.com + webapi).

Datasets:
  meeting_minutes      City Council minutes (born-digital PDFs behind
                       Calendar.aspx `View.ashx?M=M` links)
  planning_commission  PC votes — Legistar API EventItemVote records (body 140);
                       Sandy publishes NO PC minutes corpus (see
                       planning_commission/CLAUDE.md)

Portal pattern (recon.md §1, verified live 2026-07-02):
  * PROBE (both datasets): Legistar Web API, client name `sandyutah`
      GET https://webapi.legistar.com/v1/sandyutah/events?$filter=EventDate ge datetime'...'
    -> JSON events with EventBodyName, EventDate, EventMinutesStatusName
    (Draft/Final). (The `build_from_legistar.py` docstring's "webapi is
    disabled for 'sandy'" refers to the client name `sandy`; `sandyutah` works.)
    The API does NOT expose minutes PDF URLs (EventMinutesFile is null).
  * COUNCIL FETCH: Calendar.aspx defaults to "This Month" — the year filter is
    an ASP.NET postback (__EVENTTARGET=ctl00$ContentPlaceHolder1$lstYears +
    RadComboBox ClientState). The posted-back grid rows carry
    `View.ashx?M=M&ID=<id>&GUID=<guid>` minutes-only links (M=M; never M=A
    agendas / M=AP packets). Verified live: 2026 postback -> 28 minutes links.
  * PC FETCH: pulls the new events' EventItems + Votes from the API, appends
    them to db/staging/{events,eventitems,votes}.csv (the canonical Legistar
    harvest; raw JSON retained under planning_commission/raw/legistar/), then
    re-runs planning_commission/build_from_legistar.py which regenerates
    all_votes.csv + roster.csv deterministically from staging. fetch_new.py
    NEVER touches sandy.db — rebuild it afterwards with db/build_db.py (the
    build reads staging + the flat CSVs and reconciles fail-loud).

Modes:
  --probe   (default) API listing only; reports newer events + minutes status
  --fetch   council: download new M=M PDFs -> raw/, pdftotext -layout -> .md,
            append minutes_index.csv (+ fetch_log.csv), run extract_votes.py +
            validate_votes.py. PC: staging append + build_from_legistar.py.
            Events whose minutes are still Draft/unposted are reported+skipped.
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

API = "https://webapi.legistar.com/v1/sandyutah"
CAL = "https://sandyutah.legistar.com/Calendar.aspx"

BODY_FOR = {"meeting_minutes": "City Council", "planning_commission": "Planning Commission"}


# ------------------------------------------------------------------ probe

def api_events(since_date):
    flt = urllib.parse.quote(f"EventDate ge datetime'{since_date}'")
    return rl.http_get_json(f"{API}/events?$filter={flt}&$orderby=EventDate")


def probe(dataset, max_date):
    body = BODY_FOR[dataset]
    events = api_events(max_date or "2020-01-01")
    new = []
    for e in events:
        date = (e.get("EventDate") or "")[:10]
        if e.get("EventBodyName") != body:
            continue
        if not date or (max_date and date <= max_date) or date > rl.today():
            continue
        status = e.get("EventMinutesStatusName") or "?"
        new.append({"date": date, "title": f"{body} (minutes: {status})",
                    "url": f"{API}/events/{e['EventId']}", "event_id": e["EventId"],
                    "minutes_status": status})
    new.sort(key=lambda x: x["date"])
    notes = ""
    drafts = sum(1 for n in new if n["minutes_status"] != "Final")
    if drafts:
        notes = (f"{drafts} of {len(new)} still have Draft minutes — the M=M PDF "
                 "is typically posted only once approved (council) / votes may be "
                 "incomplete until finalized (PC)")
    return {"new_items": new, "endpoint": f"{API}/events", "notes": notes}


# --------------------------------------------------- council fetch (Calendar)

def _hidden(page, name):
    m = re.search(r'id="%s" value="([^"]*)"' % name, page)
    return m.group(1) if m else ""


def calendar_minutes_links(year):
    """(body, iso_date) -> View.ashx?M=M URL, via the year-filter postback."""
    page = rl.http_get(CAL)
    fields = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$lstYears",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": _hidden(page, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _hidden(page, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _hidden(page, "__EVENTVALIDATION"),
        "ctl00$ContentPlaceHolder1$lstYears": str(year),
        "ctl00_ContentPlaceHolder1_lstYears_ClientState":
            json.dumps({"logEntries": [], "value": str(year), "text": str(year), "enabled": True}),
        "ctl00$ContentPlaceHolder1$lstBodies": "All",
        "ctl00_ContentPlaceHolder1_lstBodies_ClientState":
            json.dumps({"logEntries": [], "value": "", "text": "All", "enabled": True}),
    }
    grid = rl.http_get(CAL, method="POST", referer=CAL,
                       headers={"Content-Type": "application/x-www-form-urlencoded"},
                       data=urllib.parse.urlencode(fields).encode())
    links = {}
    for row in re.split(r'<tr class="rg(?:Row|AltRow)"', grid)[1:]:
        m = re.search(r'View\.ashx\?M=M&amp;ID=(\d+)&amp;GUID=([0-9A-Fa-f-]+)', row)
        b = re.search(r'<td[^>]*>(?:<font[^>]*>)?\s*(?:<a [^>]*>)?([^<]{2,60})</', row)
        d = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row)
        if not (m and b and d):
            continue
        mm, dd, yy = d.group(1).split("/")
        iso = f"{yy}-{int(mm):02d}-{int(dd):02d}"
        links[(b.group(1).strip(), iso)] = (
            f"https://sandyutah.legistar.com/View.ashx?M=M&ID={m.group(1)}&GUID={m.group(2)}")
    if not links:
        raise RuntimeError("Calendar.aspx year postback returned no M=M links — markup changed?")
    return links


def fetch_council(items):
    ds_dir = CITY_DIR / "meeting_minutes"
    links = {}
    for year in sorted({it["date"][:4] for it in items}):
        links.update(calendar_minutes_links(year))
    rows, n = [], 0
    for it in items:
        url = links.get(("City Council", it["date"]))
        if not url:
            print(f"  SKIP {it['date']}: no minutes PDF on Calendar.aspx yet "
                  f"(status {it.get('minutes_status')})")
            continue
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {it['date']}: response not a PDF")
            continue
        slug = "city-council-meeting"
        raw = rl.save_raw(ds_dir, f"{it['date']}_{slug}.pdf", pdf)
        rel = rl.minutes_rel_path(it["date"], slug, "md", prefix="meeting_minutes/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rl.pdf_to_text(raw), encoding="utf-8")
        rows.append({"date": it["date"], "year": it["date"][:4],
                     "title": "City Council Meeting", "slug": slug, "path": rel,
                     "source": "legistar", "source_url": url, "format": "text"})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch_council():
    ds_dir = CITY_DIR / "meeting_minutes"
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, "council extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, "council validate_votes")


# ---------------------------------------------------------- PC fetch (API)

def _append_staging(name, new_rows, key):
    import csv
    path = CITY_DIR / "db" / "staging" / name
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames
        have = {r[key] for r in reader}
    added = [r for r in new_rows if str(r.get(key, "")) not in have]
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        for r in added:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})
    return len(added)


def fetch_pc(items):
    raw_dir = CITY_DIR / "planning_commission" / "raw" / "legistar"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ev_rows, it_rows, vt_rows = [], [], []
    for it in items:
        eid = it["event_id"]
        ev = rl.http_get_json(f"{API}/events/{eid}")
        eitems = rl.http_get_json(f"{API}/events/{eid}/eventitems")
        votes_by_item = {}
        for ei in eitems:
            if ei.get("EventItemRollCallFlag") or ei.get("EventItemPassedFlag") is not None:
                votes_by_item[ei["EventItemId"]] = rl.http_get_json(
                    f"{API}/eventitems/{ei['EventItemId']}/votes")
        (raw_dir / f"{it['date']}_event{eid}.json").write_text(json.dumps(
            {"event": ev, "eventitems": eitems, "votes": votes_by_item}, indent=1))
        ev_rows.append(ev)
        it_rows.extend(eitems)
        for vs in votes_by_item.values():
            vt_rows.extend(vs)
    n_e = _append_staging("events.csv", ev_rows, "EventId")
    n_i = _append_staging("eventitems.csv", it_rows, "EventItemId")
    n_v = _append_staging("votes.csv", vt_rows, "VoteId")
    print(f"  staging: +{n_e} events, +{n_i} eventitems, +{n_v} votes (raw JSON in {raw_dir})")
    return n_e


def post_fetch_pc():
    ds_dir = CITY_DIR / "planning_commission"
    rl.run_pipeline_step(["python3", "build_from_legistar.py"], ds_dir,
                         "PC rebuild all_votes from staging")
    print("    (PC has no standalone validate_votes.py; run "
          "../scripts/validate_city.py sandy after the db/weeks rebuild)")


DATASETS = {
    "meeting_minutes": {
        "portal": "legistar",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": lambda mx: probe("meeting_minutes", mx),
        "fetch": fetch_council,
        "post_fetch": post_fetch_council,
    },
    "planning_commission": {
        "portal": "legistar-api",
        "baseline": lambda: rl.csv_max_date(CITY_DIR / "planning_commission" / "all_votes.csv"),
        "probe": lambda mx: probe("planning_commission", mx),
        "fetch": fetch_pc,
        "post_fetch": post_fetch_pc,
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Sandy refresh (Legistar)")
