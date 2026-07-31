#!/usr/bin/env python3
"""
Salt Lake City incremental refresh — PrimeGov portal (slc.primegov.com) +
slcdocs.com (Planning Commission minutes PDFs, weekly public-comment PDFs).

Datasets:
  meeting_minutes      Council + CRA/RDA/LBA minutes (PrimeGov "HTML Minutes")
  planning_commission  PC minutes on slcdocs.com. NOTE: SLC's PrimeGov portal
                       does NOT list Planning Commission meetings (verified
                       2026-07-02: the 2026 listing carries only
                       council-family bodies), so the probe projects candidate
                       meeting dates itself — every Wednesday after the index
                       max (PC regularly meets 2nd & 4th Wednesdays; probing
                       all Wednesdays also catches specials) — and HEADs the
                       known slcdocs URL variants for each.
  public_comments      weekly comment PDFs — WRAPS the existing
                       public_comments/check_new_comments.py (delegates; the
                       proven pipeline is not duplicated here)

Portal patterns (recon.md, verified in production):
  * List:  GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY -> JSON
           (title, dateTime, documentList[] with templateName/templateId).
  * Council minutes doc = templateName == "HTML Minutes" (SLC minutes are
    born-digital HTML; scrape_primegov.py converts them to Markdown).
  * PC minutes: slcdocs.com/Planning/Planning%20Commission/<year>/<folder>/
    PC<MM>.<DD>.<YYYY>minutes.pdf — the <folder> naming drifts
    ("PC 5.13.2026", "PC 06.10.2026", "PC 4.8.2026 Meeting Docs", or no
    folder at all pre-2021), so the probe HEADs each known variant.

Modes:
  --probe   (default) report what's new on the portals vs the indexes;
            fetches nothing (PC probe = HEAD requests only; comments probe =
            check_new_comments.py --dry-run, itself HEAD-only)
  --fetch   meeting_minutes: delegate to scrape_primegov.py --years ...
            (resumable; rebuilds minutes_index.csv itself), then run
            extract_votes.py (LLM batch — needs ANTHROPIC_API_KEY in .env)
            + validate_votes.py.
            planning_commission: download new PDFs -> raw/, pdftotext
            -layout -> .md, append index rows, extract + validate votes.
            public_comments: run check_new_comments.py (no --dry-run); it
            downloads + prints the vision_extract/clean_comments next steps.

Probe verified live 2026-07-02 (all three datasets, HTTP 200; 0 new items —
3 June council meetings + 3 June PC Wednesdays pending publication, comments
current through 2026-04-07).

Caveat (inherited from check_new_comments.py by design): the comments probe
stops after ~8 consecutive empty weeks (GAP_WEEKS, recess handling). If the
city ever resumes posting after a longer silent gap, run
`check_new_comments.py` again later or extend GAP_WEEKS there — not here.
"""

import re
import subprocess
import sys
import urllib.error
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

sys.path.insert(0, str(CITY_DIR / "public_comments"))
import check_new_comments as cnc  # noqa: E402  (baseline reuse; no side effects)

HOST = "https://slc.primegov.com"
LIST_API = HOST + "/api/v2/PublicPortal/ListArchivedMeetings?year={year}"
MEETING_URL = HOST + "/Portal/Meeting?meetingTemplateId={tid}"
SLCDOCS_PC = "https://www.slcdocs.com/Planning/Planning%20Commission"

# Same body scope as meeting_minutes/scrape_primegov.py
BODY_RE = re.compile(
    r"council|community reinvestment|\bcra\b|redevelopment agency|\brda\b|"
    r"local building authority|\blba\b", re.IGNORECASE)
PC_RE = re.compile(r"planning commission", re.IGNORECASE)


def list_meetings(y0, y1):
    for year in range(y0, y1 + 1):
        for m in rl.http_get_json(LIST_API.format(year=year)):
            yield m


def has_html_minutes(meeting):
    for d in meeting.get("documentList", []):
        if d.get("templateName") == "HTML Minutes":
            return d.get("templateId")
    return None


# ------------------------------------------------------------ meeting_minutes

def probe_minutes(max_date):
    y0 = int(max_date[:4]) if max_date else 2021
    y1 = int(rl.today()[:4])
    new, pending = [], 0
    for m in list_meetings(y0, y1):
        date = (m.get("dateTime") or "")[:10]
        if not date or (max_date and date <= max_date):
            continue
        if not BODY_RE.search(m.get("title", "")):
            continue
        tid = has_html_minutes(m)
        if not tid:
            pending += 1
            continue
        new.append({"date": date, "title": m.get("title", ""),
                    "url": MEETING_URL.format(tid=tid)})
    new.sort(key=lambda x: x["date"])
    notes = f"{pending} newer meeting(s) have no HTML Minutes yet (unapproved)" if pending else ""
    return {"new_items": new, "endpoint": LIST_API.format(year=y1), "notes": notes}


def fetch_minutes(items):
    years = sorted({it["date"][:4] for it in items})
    arg = f"{years[0]}-{years[-1]}" if len(years) > 1 else years[0]
    mm = CITY_DIR / "meeting_minutes"
    rl.run_pipeline_step(["python3", "scrape_primegov.py", "--years", arg],
                         mm, "scrape_primegov (resumable; rebuilds index)")
    return len(items)


def post_fetch_minutes():
    mm = CITY_DIR / "meeting_minutes"
    rl.run_pipeline_step(["python3", "extract_votes.py"], mm,
                         "meeting_minutes extract_votes (LLM batch, .env key)")
    rl.run_pipeline_step(["python3", "validate_votes.py"], mm,
                         "meeting_minutes validate_votes")


# -------------------------------------------------------- planning_commission

def head_ok(url):
    try:
        rl.http_get(url, method="HEAD")
        return True
    except urllib.error.HTTPError:
        return False


def pc_candidate_urls(iso_date):
    """slcdocs URL variants for one PC meeting date (folder naming drifts)."""
    y, mo, d = iso_date[:4], iso_date[5:7], iso_date[8:10]
    fname = f"PC{mo}.{d}.{y}minutes.pdf"
    folders = [f"PC {mo}.{d}.{y}",                    # padded  (2026-06 style)
               f"PC {int(mo)}.{int(d)}.{y}",          # unpadded (2026-05 style)
               f"PC {int(mo)}.{int(d)}.{y} Meeting Docs",
               f"PC {mo}.{d}.{y} Meeting Docs",
               None]                                  # bare year dir (2020 style)
    seen, urls = set(), []
    for f in folders:
        path = f"{y}/{urllib.parse.quote(f)}/{fname}" if f else f"{y}/{fname}"
        url = f"{SLCDOCS_PC}/{path}"
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def probe_pc(max_date):
    """PC meetings are NOT on SLC's PrimeGov portal — project every Wednesday
    after the index max and HEAD the slcdocs URL variants for each."""
    import datetime
    start = datetime.date.fromisoformat(max_date) if max_date else datetime.date(2020, 1, 1)
    today = datetime.date.today()
    d = start + datetime.timedelta(days=1)
    d += datetime.timedelta(days=(2 - d.weekday()) % 7)   # next Wednesday
    new, probed = [], 0
    while d <= today:
        iso = d.isoformat()
        hit = next((u for u in pc_candidate_urls(iso) if head_ok(u)), None)
        if hit:
            new.append({"date": iso, "title": "Planning Commission", "url": hit})
        probed += 1
        d += datetime.timedelta(days=7)
    notes = (f"probed {probed} candidate Wednesday(s) on slcdocs "
             "(PrimeGov does not list PC meetings — minutes may lag ~1 month behind a meeting)")
    return {"new_items": new, "endpoint": SLCDOCS_PC + "/<year>/...", "notes": notes}


def fetch_pc(items):
    pc = CITY_DIR / "planning_commission"
    rows, n = [], 0
    for it in items:
        date, url = it["date"], it["url"]
        pdf = rl.http_get(url, binary=True)
        if not pdf.startswith(b"%PDF"):
            print(f"  SKIP {date}: response is not a PDF ({len(pdf)} bytes)")
            continue
        raw = rl.save_raw(pc, url.rsplit("/", 1)[-1], pdf)
        text = rl.pdf_to_text(raw)
        rel = rl.minutes_rel_path(date, "planning-commission-meeting", "md",
                                  prefix="planning_commission/minutes")
        out = CITY_DIR / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": "Planning Commission",
                     "slug": "planning-commission-meeting", "path": rel,
                     "source": "slcdocs", "source_url": url, "format": "text"})
        n += 1
        print(f"  fetched {rel}")
    rl.append_index_rows(pc, rows)
    return n


def post_fetch_pc():
    pc = CITY_DIR / "planning_commission"
    rl.run_pipeline_step(["python3", "extract_votes.py"], pc, "PC extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], pc, "PC validate_votes")


# ------------------------------------------------------------ public_comments

COMMENTS_DIR = CITY_DIR / "public_comments"
NEW_LINE_RE = re.compile(r"NEW:\s*(\d{4}-\d{2}-\d{2}) -> (\d{4}-\d{2}-\d{2})\s+\((.+)\)")


def comments_baseline():
    last = cnc.latest_end()
    n = len(list(COMMENTS_DIR.glob("20*/*.pdf")))
    return (last.isoformat() if last else None), n


def probe_comments(_max_date):
    r = subprocess.run(["python3", "check_new_comments.py", "--dry-run"],
                       cwd=str(COMMENTS_DIR), capture_output=True, text=True,
                       timeout=1800)
    out = r.stdout
    if r.returncode != 0:
        raise RuntimeError(f"check_new_comments.py --dry-run exited {r.returncode}: "
                           f"{(r.stderr or out).strip()[:300]}")
    new = [{"date": m.group(2), "title": m.group(3), "url": ""}
           for m in NEW_LINE_RE.finditer(out)]
    notes = ("delegated to check_new_comments.py --dry-run"
             + ("" if new else " — up to date"))
    return {"new_items": new, "endpoint": cnc.SITE, "notes": notes}


def fetch_comments(_items):
    rl.run_pipeline_step(["python3", "check_new_comments.py"], COMMENTS_DIR,
                         "check_new_comments (download + scraper update)")
    print("Next (per public_comments/CLAUDE.md): python3 vision_extract.py --year <year>"
          "  then  python3 clean_comments.py")
    return len(_items)


DATASETS = {
    "meeting_minutes": {
        "portal": "primegov",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": probe_minutes,
        "fetch": fetch_minutes,
        "post_fetch": post_fetch_minutes,
    },
    "planning_commission": {
        "portal": "primegov+slcdocs",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": probe_pc,
        "fetch": fetch_pc,
        "post_fetch": post_fetch_pc,
    },
    "public_comments": {
        "portal": "slcdocs",
        "baseline": comments_baseline,
        "probe": probe_comments,
        "fetch": fetch_comments,
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Salt Lake City refresh (PrimeGov + slcdocs)")
