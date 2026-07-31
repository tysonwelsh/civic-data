#!/usr/bin/env python3
"""
South Salt Lake incremental refresh — Utah Public Notice (PMN), content-detecting
recorded MINUTES vs AGENDA PACKETS.

THE STRUCTURAL FACT (read meeting_minutes/CLAUDE.md + COVERAGE.md first): SSL's recorded
minutes live ONLY on PMN, not the CivicPlus AgendaCenter, and the PMN "Meeting Minutes"
attachment slot is UNRELIABLE — it very often serves the multi-MB AGENDA PACKET (headed
"REGULAR MEETING AGENDA", no roll call) *even when the file is labelled `… RC Minutes.pdf`*
(verified live: 2023-02-22's "RC Minutes"/"WM Minutes" files are agendas). The only reliable
test for "is this minutes" is CONTENT — the roll-call grammar. So this refresh downloads each
candidate (smallest first, and skips the >22 MB pure-agenda monsters), keeps only the one that
actually contains a roll call, trims the leading agenda pages, and logs the rest as HONEST gaps
in `minutes_unrecovered.csv`. Pure-agenda files are NOT retained (a future `packets/` layer).

Three PMN public bodies, TWO datasets:
  council  PMN body 1295 -> meeting_minutes/  (body=Council)
  rda      PMN body 1296 -> meeting_minutes/  (body=RDA)      [same Wednesday, 6:15pm]
  pc       PMN body 1297 -> planning_commission/ (body=PlanningCommission)  [Thursday]

PMN layout: a public-body page (utah.gov/pmn/sitemap/publicbody/<id>.html) lists recent
NOTICES (/pmn/sitemap/notice/<n>.html); each notice page carries the meeting "Start Date"
and its attachment links (/pmn/files/<fid>.pdf) with human labels. PMN exposes only the
most-recent window via GET, so this probes forward from the per-dataset index max.

Modes:
  --probe  (default) list meeting dates newer than the index max per stream (excluding dates
           already indexed or logged in minutes_unrecovered.csv); fetch nothing. Writes
           refresh_probe.json.
  --fetch [--stream council|rda|pc]  download each new date's candidate doc(s) -> raw/,
           content-detect the minutes doc, write markdown + provenance header, append
           minutes_index.csv (or minutes_unrecovered.csv for an agenda-only gap), then run
           each touched dataset's extract_votes.py + validate_votes.py. Rebuild db + weeks +
           motions_std afterwards (the CLI prints the reminder).

Idempotent + resumable: a date+kind whose markdown already exists is skipped; re-runnable.
Stdlib only. Mirrors .harvest/harvest_minutes.py (the original bulk harvester) — that remains
the tool for a full re-harvest; this one is the forward-only incremental driver.
"""
import csv
import datetime
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact tysonwelsh@gmail.com)")
PMN = "https://www.utah.gov/pmn"
SIZE_CAP = 22_000_000   # above this = exhibit-heavy agenda packet, never minutes (see harvest)
WORKERS = 6

STREAMS = {
    "council": dict(body_id="1295", ds=REPO / "meeting_minutes", body="Council"),
    "rda":     dict(body_id="1296", ds=REPO / "meeting_minutes", body="RDA"),
    "pc":      dict(body_id="1297", ds=REPO / "planning_commission",
                    body="PlanningCommission"),
}

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

# minutes signature: the recorded-minutes grammar / header (absent from a bare agenda)
VOTE_GRAMMAR = re.compile(r"Roll Call Vote:|Voice Vote:", re.I)
HEADER_SIG = re.compile(r"MEMBERS\s+PRESENT", re.I)
MOTION_SIG = re.compile(r"made a motion|MOTION:\s*[A-Z]", re.I)
AGENDA_SIG = re.compile(r"REGULAR MEETING AGENDA|MEETING AGENDA|MOTION SHEET", re.I)
# no-quorum / no-meeting-held minutes (the 2024-07-18 PC case): a genuine minutes
# record carrying the minutes header + title but NO vote/motion grammar — the meeting
# never convened. All three signatures are required so PMN quorum NOTICES ("Notice of
# Potential Quorum", no Members-Present header) and agenda packets never match.
MINUTES_TITLE = re.compile(r"Meeting\s+Minutes\b", re.I)
NO_MEETING_SIG = re.compile(
    r"no\s+.{0,60}meeting\s+was\s+held|was\s+not\s+(?:a\s+)?quorum|"
    r"lack\s+of\s+(?:a\s+)?quorum|no\s+quorum|quorum\s+was\s+not\s+present", re.I)


# ------------------------------------------------------------------ http / parse

def http_get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print(f"    GET FAIL {url}: {e}", file=sys.stderr)
                return b"" if binary else ""
    return b"" if binary else ""


def today():
    return datetime.date.today().isoformat()


def _label_to_iso(text):
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})', text)
    if m and m.group(1).lower() in _MONTHS:
        return f"{m.group(3)}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return None


def kind_of(stream, label):
    L = label.lower().replace(" ", "")
    if stream == "pc":
        if "work" in L or re.search(r"wkmtg|workmtg", L):
            return "WM"
        return "PC"
    if "boc" in L or "boardofcanvass" in L or "canvass" in L:
        return "BoC"
    if L.endswith("sm.pdf") or "special" in L:
        return "SM"
    if re.search(r"tt\.pdf", L):
        return "TT"
    if re.search(r"wm|wkmtg|wmmin|workmeeting|work", L):
        return "WM"
    return "RC"


def week_monday(dstr):
    d = datetime.date.fromisoformat(dstr)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


# ------------------------------------------------------------------ PMN listing

_NOTICE_RE = re.compile(r'/pmn/sitemap/notice/(\d+)\.html')
_FILE_RE = re.compile(
    r'/pmn/files/(\d+)\.pdf"[^>]*aria-label="Download ([^"]*?)(?: \(opens|")', re.I)
_FILE_FALLBACK = re.compile(r'/pmn/files/(\d+)\.pdf"[^>]*>([^<]*)</a>', re.I)


def list_notices(body_id):
    """Notice ids on a public-body page (most-recent window PMN exposes via GET)."""
    html = http_get(f"{PMN}/sitemap/publicbody/{body_id}.html")
    seen, out = set(), []
    for nid in _NOTICE_RE.findall(html):
        if nid not in seen:
            seen.add(nid)
            out.append(nid)
    return out


def notice_detail(nid):
    """(iso_date, [(fid,label), ...]) for one notice page. Meeting date = 'Start Date'."""
    html = http_get(f"{PMN}/sitemap/notice/{nid}.html")
    iso = None
    m = re.search(r'Start Date[^<]*</dt>\s*<dd[^>]*>\s*([A-Za-z]+ \d{1,2}, 20\d{2})', html)
    if m:
        iso = _label_to_iso(m.group(1))
    if not iso:                       # fallback: first Month D, YYYY on the page
        iso = _label_to_iso(html)
    files = _FILE_RE.findall(html)
    if not files:
        files = _FILE_FALLBACK.findall(html)
    files = [(fid, re.sub(r"\s+", " ", lab).strip()) for fid, lab in files]
    return iso, files


def collect_candidates(stream):
    """{(date, kind): [(fid, label), ...]} from the body's current PMN window."""
    cfg = STREAMS[stream]
    groups = defaultdict(list)
    for nid in list_notices(cfg["body_id"]):
        iso, files = notice_detail(nid)
        if not iso or iso > today():
            continue
        for fid, lab in files:
            groups[(iso, kind_of(stream, lab))].append((fid, lab))
    return groups


# ------------------------------------------------------------------ index i/o

def index_dates(ds_dir):
    p = ds_dir / "minutes_index.csv"
    if not p.exists():
        return set(), None
    dates = set()
    with open(p, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("date"):
                dates.add(r["date"])
    return dates, (max(dates) if dates else None)


def unrecovered_dates(ds_dir, body):
    p = ds_dir / "minutes_unrecovered.csv"
    if not p.exists():
        return set()
    with open(p, newline="", encoding="utf-8") as fh:
        return {r["date"] for r in csv.DictReader(fh)
                if r.get("date") and r.get("body", body) == body}


# ------------------------------------------------------------------ content test

def pdftotext(data):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
        tf.write(data)
        tf.flush()
        return subprocess.run(["pdftotext", "-layout", tf.name, "-"],
                              capture_output=True, text=True, errors="replace").stdout


def is_minutes(text):
    if VOTE_GRAMMAR.search(text):
        return True
    if HEADER_SIG.search(text) and MOTION_SIG.search(text):
        return True
    # no-quorum minutes: header + "… Meeting Minutes" title + explicit no-meeting/
    # no-quorum statement, no vote lines required (2026-07-17 ingestion fix)
    if (HEADER_SIG.search(text) and MINUTES_TITLE.search(text)
            and NO_MEETING_SIG.search(text)):
        return True
    return False


def minutes_start(text):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"\s*CITY OF SOUTH SALT LAKE\s*$", ln, re.I):
            window = "\n".join(lines[i:i + 25])
            if re.search(r"MEETING", window, re.I) and re.search(r"PRESIDING", window, re.I):
                return i
    for i, ln in enumerate(lines):
        if re.match(r"\s*PRESIDING", ln, re.I):
            return max(0, i - 4)
    for i, ln in enumerate(lines):
        if HEADER_SIG.search(ln):
            return max(0, i - 4)
    return 0


# ------------------------------------------------------------------ probe / fetch

def new_dates(stream):
    cfg = STREAMS[stream]
    ds_dir, body = cfg["ds"], cfg["body"]
    indexed, mx = index_dates(ds_dir)
    unrec = unrecovered_dates(ds_dir, body)
    # this stream's own indexed dates (a shared dataset holds Council + RDA)
    have = _stream_dates_on_disk(ds_dir, stream) | (unrec if body else set())
    groups = collect_candidates(stream)
    out = []
    for (iso, kind), cands in sorted(groups.items()):
        if mx and iso <= mx:
            continue
        if (iso, kind) in have or iso in unrec:
            continue
        out.append({"date": iso, "kind": kind,
                    "candidates": [{"fid": f, "label": l} for f, l in cands]})
    return out, mx


def _stream_dates_on_disk(ds_dir, stream):
    """(date, kind) already present as markdown for this stream."""
    have = set()
    for md in (ds_dir / "minutes").rglob(f"*_{stream}_*.md"):
        m = re.match(r"(20\d\d-\d\d-\d\d)_" + stream + r"_([A-Za-z]+)", md.name)
        if m:
            have.add((m.group(1), m.group(2)))
    return have


def probe():
    report = {}
    for stream in STREAMS:
        items, mx = new_dates(stream)
        report[stream] = {"index_max": mx, "body_id": STREAMS[stream]["body_id"],
                          "new_meeting_dates": items,
                          "note": ("PMN Meeting-Minutes slot often serves the AGENDA PACKET; "
                                   "each candidate is content-detected at --fetch (roll-call "
                                   "grammar), agenda-only dates logged unrecovered.")}
    (REPO / "refresh_probe.json").write_text(json.dumps(report, indent=2))
    for stream, r in report.items():
        n = len(r["new_meeting_dates"])
        print(f"[{stream}] PMN body {r['body_id']} · index_max={r['index_max']} · "
              f"{n} new meeting date(s) to resolve")
        for it in r["new_meeting_dates"]:
            print(f"    {it['date']} {it['kind']} ({len(it['candidates'])} candidate file(s))")
    print("\nWrote refresh_probe.json. Run --fetch to content-detect & ingest.")
    return report


def _try_recover(fid_label_size):
    """Download a candidate, return text if it is genuine minutes else None."""
    fid, label = fid_label_size
    data = http_get(f"{PMN}/files/{fid}.pdf", binary=True)
    if not data.startswith(b"%PDF") or len(data) > SIZE_CAP:
        return fid, label, None, None
    txt = pdftotext(data)
    if is_minutes(txt):
        return fid, label, txt, data
    return fid, label, None, data


def fetch(only_stream=None):
    streams = [only_stream] if only_stream else list(STREAMS)
    touched = set()
    for stream in streams:
        cfg = STREAMS[stream]
        ds_dir, body = cfg["ds"], cfg["body"]
        items, _ = new_dates(stream)
        if not items:
            print(f"[{stream}] nothing new")
            continue
        new_rows, gap_rows = [], []
        for it in items:
            iso, kind = it["date"], it["kind"]
            slug = f"{iso}_{stream}_{kind}"
            out = ds_dir / "minutes" / iso[:4] / week_monday(iso) / f"{slug}.md"
            if out.exists():
                continue
            cands = [(c["fid"], c["label"]) for c in it["candidates"]]
            chosen = None
            with ThreadPoolExecutor(max_workers=min(WORKERS, len(cands) or 1)) as ex:
                for fid, label, txt, data in ex.map(_try_recover, cands):
                    if txt:
                        chosen = (fid, label, txt, data)
                        break
            if not chosen:
                gap_rows.append({"date": iso, "body": body, "meeting_kind": kind,
                                 "reason": "agenda-only/minutes-not-posted"})
                print(f"  [{stream}] {iso} {kind}: UNRECOVERED (agenda-only)")
                continue
            fid, label, txt, data = chosen
            start = minutes_start(txt)
            mtext = "\n".join(txt.split("\n")[start:]).strip()
            (ds_dir / "raw").mkdir(parents=True, exist_ok=True)
            (ds_dir / "raw" / f"{slug}_{fid}.pdf").write_bytes(data)
            out.parent.mkdir(parents=True, exist_ok=True)
            src = f"{PMN}/files/{fid}.pdf"
            header = (f"<!-- source: pmn | body: {body} | pmn_file: {fid} | label: {label} | "
                      f"date: {iso} | meeting_kind: {kind} | source_url: {src} | "
                      f"retrieved: {today()} -->\n\n")
            out.write_text(header + mtext, encoding="utf-8")
            rel = out.relative_to(ds_dir).as_posix()
            new_rows.append({"date": iso, "year": iso[:4],
                             "title": f"{body} {kind} Meeting {iso}", "slug": slug,
                             "path": rel, "source": "pmn", "source_url": src,
                             "format": "pdf-text", "body": body, "meeting_kind": kind,
                             "pmn_file": fid})
            print(f"  [{stream}] {iso} {kind}: OK ({len(data)//1024}KB)")
            touched.add(ds_dir)
        _append(ds_dir / "minutes_index.csv",
                ["date", "year", "title", "slug", "path", "source", "source_url",
                 "format", "body", "meeting_kind", "pmn_file"], new_rows)
        _append(ds_dir / "minutes_unrecovered.csv",
                ["date", "body", "meeting_kind", "reason"], gap_rows)

    for ds_dir in touched:
        for step in ("extract_votes.py", "validate_votes.py"):
            print(f"  running {ds_dir.name}/{step}")
            subprocess.run([sys.executable, step], cwd=ds_dir, check=False)
    if touched:
        print("\nDONE. Now rebuild derived layers:\n"
              "  python3 db/build_db.py && python3 db/build_referrals.py\n"
              "  python3 ../scripts/normalize_motions.py --all   # refreshes motions_std.csv\n"
              "  python3 build_weeks.py\n"
              "  python3 ../scripts/build_cities_db.py      # re-federate")


def _append(path, header, rows):
    if not rows:
        return
    exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--fetch" in args:
        st = None
        if "--stream" in args:
            st = args[args.index("--stream") + 1]
            if st not in STREAMS:
                sys.exit(f"--stream must be one of {list(STREAMS)}")
        fetch(st)
    else:
        probe()
