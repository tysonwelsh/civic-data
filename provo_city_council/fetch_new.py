#!/usr/bin/env python3
"""
Provo incremental refresh — two portals (recon.md §1):

  meeting_minutes      Hyland OnBase Agenda Online at https://agendas.provo.gov
                       (Municipal Council: Council Meeting + Work Session, plus
                       council one-offs like retreats/town halls/canvassers).
  planning_commission  CivicPlus AgendaCenter at https://www.provo.gov/AgendaCenter
                       (category "Planning Commission"; the separate
                       "Planning Commission Administrative Hearings" category
                       is a different body and is excluded).

OnBase pattern (verified live 2026-07-02):
  * GET  /Meetings                      -> __RequestVerificationToken + cookie
  * POST /Meetings  (DateRangeOptionID=11, DateRangeCustomStartDate/EndDate)
    -> 302 -> results HTML. Minutes = anchors with documentType=2 whose title
    attr is 'Download Minutes for <name> on <M/D/YYYY ...>'. IMPORTANT: OnBase
    keeps unpublished minutes links inside HTML comments — strip <!-- --> blocks
    before parsing or you'll report minutes that aren't published yet.
  * Download: rewrite DownloadFile -> DownloadFileBytes, send the session
    cookie + Referer https://agendas.provo.gov/Meetings (the plain DownloadFile
    URL returns a JS interstitial, not the PDF).

AgendaCenter pattern (verified live 2026-07-02):
  * GET /AgendaCenter/Search/?term=&CIDs=all&startDate=MM/DD/YYYY&endDate=MM/DD/YYYY
    -> results grouped under <h2> category headers; minutes links are
    /AgendaCenter/ViewFile/Minutes/_MMDDYYYY-<id> (date is in the ref).

The probe uses a 21-day overlap window behind each index max and treats an item
as new only if its (date, slug) pair is absent from minutes_index.csv — Provo
publishes same-day pairs (Work Session + Regular Meeting) whose minutes appear
weeks apart, so a strict date > max(date) cutoff would miss stragglers (e.g.
the 2026-05-26 Council Regular minutes, unpublished while the same-day Work
Session minutes are already indexed).

Modes: --probe (default, read-only listing GETs) / --fetch (download new
minutes -> raw/, pdftotext -layout -> .md, append index rows incl. the
packet_url column, then run extract_votes.py + validate_votes.py).
"""

import datetime
import html as htmllib
import http.cookiejar
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

ONBASE = "https://agendas.provo.gov"
AGENDACENTER = "https://www.provo.gov/AgendaCenter"
OVERLAP_DAYS = 21

# Municipal-Council filename prefixes -> (index title, slug). Anything not
# matching and not on the exclude list keeps its own name, slugified.
MM_PREFIXES = {
    "Council_Meeting": ("Council Regular Meeting", "council-regular-meeting"),
    "Work_Meeting": ("Council Work Session", "council-work-session"),
}
# Non-council bodies that share the OnBase portal.
MM_EXCLUDE = re.compile(r"Planning_Commission|Stormwater|Redevelopment|^RDA_|"
                        r"Board_of_Adjustment", re.I)


# --------------------------------------------------- OnBase session plumbing

class OnBaseSession:
    """Cookie-carrying opener with the same politeness discipline as
    refresh_lib.http_get (>=1s throttle, research UA)."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self._last = 0.0

    def request(self, url, data=None, referer=None, binary=False):
        wait = rl.THROTTLE_SECONDS - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        headers = {"User-Agent": rl.RESEARCH_UA}
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, data=data, headers=headers)
        with self.opener.open(req, timeout=60) as resp:
            body = resp.read()
        return body if binary else body.decode("utf-8", "replace")


def onbase_search(session, start, end):
    """POST the /Meetings search form; return the results HTML with all
    HTML comments stripped (unpublished minutes live inside comments)."""
    page = session.request(ONBASE + "/Meetings")
    m = re.search(r'__RequestVerificationToken"[^>]*value="([^"]+)"', page)
    if not m:
        raise RuntimeError("OnBase /Meetings: no __RequestVerificationToken found")
    data = urllib.parse.urlencode({
        "__RequestVerificationToken": m.group(1),
        "Keywords": "",
        "DateRangeOptionID": "11",
        "DateRangeCustomStartDate": start.strftime("%m/%d/%Y"),
        "DateRangeCustomEndDate": end.strftime("%m/%d/%Y"),
    }).encode()
    results = session.request(ONBASE + "/Meetings", data=data,
                              referer=ONBASE + "/Meetings")
    return re.sub(r"<!--.*?-->", "", results, flags=re.S)


def parse_iso(mdy):
    mo, d, y = mdy.split("/")
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def known_keys(dataset_dir):
    return {(r["date"], r["slug"]) for r in rl.load_index(dataset_dir)}


# ---------------------------------------------------------- meeting_minutes

def mm_probe(max_date):
    session = OnBaseSession()
    start = datetime.date.fromisoformat(max_date) - datetime.timedelta(days=OVERLAP_DAYS)
    end = datetime.date.today()
    page = onbase_search(session, start, end)
    known = known_keys(CITY_DIR / "meeting_minutes")

    new, seen = [], set()
    for m in re.finditer(
            r'<a href="(/Documents/DownloadFile/([A-Za-z_]+?)_\d+[^"]*documentType=2[^"]*)"'
            r'[^>]*title="Download Minutes for ([^"]+?) on (\d{1,2}/\d{1,2}/\d{4})', page):
        url, fname_prefix, name, mdy = m.groups()
        prefix = fname_prefix.rstrip("_")
        if MM_EXCLUDE.search(prefix):
            continue
        date = parse_iso(mdy)
        title, slug = MM_PREFIXES.get(
            prefix, (name.strip(), rl.slugify(name)))
        if (date, slug) in known or (date, slug) in seen:
            continue
        seen.add((date, slug))
        full = ONBASE + htmllib.unescape(url)
        # matching agenda-packet link for the same meetingId, for packet_url
        mid = re.search(r"meetingId=(\d+)", full).group(1)
        pk = re.search(
            r'<a href="(/Documents/DownloadFile/[^"]*Agenda_Packet[^"]*meetingId=%s[^"]*)"' % mid,
            page)
        new.append({"date": date, "title": title, "slug": slug, "url": full,
                    "packet_url": ONBASE + htmllib.unescape(pk.group(1)) if pk else ""})

    # meetings in the window that still have no published minutes (honesty note)
    pending = set()
    for m in re.finditer(r'title="View Agenda for ([^"]+?) on (\d{1,2}/\d{1,2}/\d{4})', page):
        name, mdy = m.groups()
        date = parse_iso(mdy)
        if date > max_date and not MM_EXCLUDE.search(name.replace(" ", "_")):
            pending.add((date, name))
    pending_n = len({d for d, _ in pending} - {it["date"] for it in new})
    new.sort(key=lambda x: x["date"])
    notes = (f"{pending_n} newer council meeting date(s) have no published minutes yet "
             "(OnBase comments the link out until approval)") if pending_n else ""
    # Secondary-portal cross-check: the AgendaCenter's "City Council Meetings"
    # category sometimes publishes council minutes before OnBase does. Report
    # (never fetch) those — the dataset's canonical route stays OnBase.
    try:
        ahead = sorted(d for d in agendacenter_minutes_dates(start, "City Council Meetings")
                       if d > max_date and d not in {it["date"] for it in new})
        if ahead:
            extra = ("secondary AgendaCenter portal already lists council minutes for: "
                     + ", ".join(ahead))
            notes = f"{notes}; {extra}" if notes else extra
    except Exception:
        pass
    return {"new_items": new, "endpoint": ONBASE + "/Meetings (POST, DateRangeOptionID=11)",
            "notes": notes}


def mm_fetch(items):
    ds_dir = CITY_DIR / "meeting_minutes"
    session = OnBaseSession()
    session.request(ONBASE + "/Meetings")   # prime the session cookie
    rows, n = [], 0
    for it in items:
        url = it["url"].replace("/DownloadFile/", "/DownloadFileBytes/")
        pdf = session.request(url, referer=ONBASE + "/Meetings", binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {it['date']}: not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{it['date']}_{it['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(it["date"], it["slug"], "md",
                                  prefix="meeting_minutes/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": it["date"], "year": it["date"][:4], "title": it["title"],
                     "slug": it["slug"], "path": rel, "source": "onbase",
                     "source_url": url, "format": "pdf",
                     "packet_url": (it.get("packet_url") or "").replace(
                         "/DownloadFile/", "/DownloadFileBytes/")})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


# ------------------------------------------------------- planning_commission

_ac_cache = {}


def agendacenter_search(start):
    """One cached AgendaCenter search per run (start date -> today).
    Returns (page HTML, endpoint URL)."""
    key = start.isoformat()
    if key not in _ac_cache:
        endpoint = (f"{AGENDACENTER}/Search/?term=&CIDs=all"
                    f"&startDate={start:%m/%d/%Y}&endDate={datetime.date.today():%m/%d/%Y}")
        _ac_cache[key] = (rl.http_get(endpoint), endpoint)
    return _ac_cache[key]


def agendacenter_minutes(start, category):
    """[(iso date, ViewFile ref), ...] for one AgendaCenter category."""
    page, _ = agendacenter_search(start)
    cats = [(m.start(), re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip())
            for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", page, re.S)]

    def cat_for(pos):
        prev = [c for p, c in cats if p < pos]
        return prev[-1] if prev else ""

    out = []
    for m in re.finditer(r'href="/AgendaCenter/ViewFile/Minutes/(_(\d{2})(\d{2})(\d{4})-\d+)"', page):
        if cat_for(m.start()) != category:
            continue
        ref, mo, d, y = m.groups()
        out.append((f"{y}-{mo}-{d}", ref))
    return out


def agendacenter_minutes_dates(start, category):
    return {d for d, _ in agendacenter_minutes(start, category)}


def pc_probe(max_date):
    start = datetime.date.fromisoformat(max_date) - datetime.timedelta(days=OVERLAP_DAYS)
    _, endpoint = agendacenter_search(start)
    known = known_keys(CITY_DIR / "planning_commission")
    new, seen = [], set()
    for date, ref in agendacenter_minutes(start, "Planning Commission"):
        slug = "planning-commission-meeting"
        if (date, slug) in known or (date, slug) in seen:
            continue
        seen.add((date, slug))
        new.append({"date": date, "title": "Planning Commission", "slug": slug,
                    "url": f"https://www.provo.gov/AgendaCenter/ViewFile/Minutes/{ref}",
                    "packet_url": f"https://www.provo.gov/AgendaCenter/ViewFile/Agenda/{ref}"})
    new.sort(key=lambda x: x["date"])
    return {"new_items": new, "endpoint": endpoint, "notes": ""}


def pc_fetch(items):
    ds_dir = CITY_DIR / "planning_commission"
    rows, n = [], 0
    for it in items:
        pdf = rl.http_get(it["url"], binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {it['date']}: not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(ds_dir, f"{it['date']}_{it['slug']}.pdf", pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(it["date"], it["slug"], "md",
                                  prefix="planning_commission/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": it["date"], "year": it["date"][:4], "title": it["title"],
                     "slug": it["slug"], "path": rel, "source": "agendacenter",
                     "source_url": it["url"], "format": "text",
                     "packet_url": it.get("packet_url", "")})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    "meeting_minutes": {
        "portal": "onbase",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": mm_probe,
        "fetch": mm_fetch,
        "post_fetch": lambda: post_fetch("meeting_minutes"),
    },
    "planning_commission": {
        "portal": "civicplus-agendacenter",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": pc_probe,
        "fetch": pc_fetch,
        "post_fetch": lambda: post_fetch("planning_commission"),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Provo refresh (OnBase + AgendaCenter)")
