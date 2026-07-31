#!/usr/bin/env python3
"""
South Salt Lake minutes harvester (PMN). Downloads the 'Meeting Minutes'-category
PMN attachments, keeps only the ones that actually CONTAIN recorded minutes (roll-call
vote grammar / the minutes header block), trims the leading agenda-packet pages, writes
clean markdown + a provenance header, retains the minutes-bearing PDF in <ds>/raw/, and
records honest gaps in <ds>/minutes_unrecovered.csv.

WHY content-detection: SSL's PMN 'Meeting Minutes' slot is unreliable — the short-form
`YYYY.M.D RC.pdf` labels are frequently the AGENDA PACKET (no roll call). The real minutes,
when posted, are either a small standalone PDF or appended after the agenda inside the same
PDF. Only the roll-call grammar identifies them, so every candidate is downloaded (smallest
first per date+kind), text-extracted, and tested; pure agendas are deleted, not retained.

Bodies: council PMN 1295 -> meeting_minutes/ (body Council); RDA PMN 1296 -> meeting_minutes/
(body RDA); PC PMN 1297 -> planning_commission/ (body PlanningCommission).

Resumable: skips a date+kind whose markdown already exists. Run repeatedly.
"""
import csv, json, re, subprocess, sys, urllib.request, datetime, os, tempfile
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

REPO = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
# Files above this are exhibit-heavy AGENDA PACKETS, never the recorded minutes (minutes,
# even when bundled with a resolution exhibit, ran <=4MB across the whole corpus). Capping
# here avoids downloading the 20-99MB pure-agenda monsters just to reject them; a date-kind
# whose only candidates exceed the cap is logged unrecovered as an agenda-packet gap.
SIZE_CAP = 22_000_000
WORKERS = 8

STREAMS = {
    "council": dict(sizes=REPO/".harvest/council_min_sizes.json", ds=REPO/"meeting_minutes",
                    body_default="Council"),
    "rda":     dict(sizes=REPO/".harvest/rda_min_sizes.json", ds=REPO/"meeting_minutes",
                    body_default="RDA"),
    "pc":      dict(sizes=REPO/".harvest/pc_min_sizes.json", ds=REPO/"planning_commission",
                    body_default="PlanningCommission"),
}

def kind_of(stream, lab):
    L = lab.lower().replace(" ", "")
    if stream == "pc":
        if "work" in L or re.search(r"wkmtg|workmtg", L): return "WM"
        return "PC"
    if "boc" in L or "boardofcanvass" in L or "canvass" in L: return "BoC"
    if L.endswith("sm.pdf") or "special" in L: return "SM"
    if re.search(r"tt\.pdf", L): return "TT"
    if re.search(r"wm|wkmtg|wmmin|workmeeting|work", L): return "WM"
    return "RC"

# minutes signature: the recorded-minutes grammar / header (NOT present in a bare agenda)
VOTE_GRAMMAR = re.compile(r"Roll Call Vote:|Voice Vote:", re.I)
HEADER_SIG = re.compile(r"MEMBERS\s+PRESENT", re.I)
MOTION_SIG = re.compile(r"made a motion|MOTION:\s*[A-Z]", re.I)

def is_minutes(text):
    if VOTE_GRAMMAR.search(text):
        return True
    if HEADER_SIG.search(text) and MOTION_SIG.search(text):
        return True
    return False

# where the minutes section begins (to trim the leading agenda packet)
def minutes_start(text):
    lines = text.split("\n")
    # 1) "CITY OF SOUTH SALT LAKE" header immediately followed by a MEETING title + PRESIDING
    for i, ln in enumerate(lines):
        if re.match(r"\s*CITY OF SOUTH SALT LAKE\s*$", ln, re.I):
            window = "\n".join(lines[i:i+25])
            if re.search(r"MEETING", window, re.I) and re.search(r"PRESIDING", window, re.I):
                return i
    # 2) first PRESIDING line, backed up a couple lines for the title
    for i, ln in enumerate(lines):
        if re.match(r"\s*PRESIDING", ln, re.I):
            return max(0, i-4)
    # 3) first MEMBERS PRESENT
    for i, ln in enumerate(lines):
        if HEADER_SIG.search(ln):
            return max(0, i-4)
    return 0

def week_monday(dstr):
    d = datetime.date.fromisoformat(dstr)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def fetch_bytes(fid):
    url = f"https://www.utah.gov/pmn/files/{fid}.pdf"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=150) as r:
                return r.read()
        except Exception as e:
            if attempt == 2:
                print(f"    DL FAIL {fid}: {e}", file=sys.stderr)
                return None
    return None

def pdftotext_bytes(data):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tf:
        tf.write(data); tf.flush()
        return subprocess.run(["pdftotext", "-layout", tf.name, "-"],
                              capture_output=True, text=True, errors="replace").stdout

def try_recover(args):
    """Worker: smallest-first over candidates <=CAP; return the first that is real minutes."""
    stream, date, kind, cands = args
    skipped_big = 0
    for s, fid, lab in cands:
        if s > SIZE_CAP:
            skipped_big += 1
            continue
        data = fetch_bytes(fid)
        if not data:
            continue
        txt = pdftotext_bytes(data)
        if is_minutes(txt):
            start = minutes_start(txt)
            mtext = "\n".join(txt.split("\n")[start:]).strip()
            return (date, kind, fid, lab, mtext, data, None)
    reason = (f"only candidate(s) >{SIZE_CAP//1_000_000}MB (agenda packet)"
              if skipped_big == len(cands) else "agenda-only/minutes-not-posted")
    return (date, kind, None, None, None, None, reason)

def run_stream(stream, cfg, year_filter=None):
    ds = cfg["ds"]; body = cfg["body_default"]
    raw = ds/"raw"; mind = ds/"minutes"
    raw.mkdir(parents=True, exist_ok=True); mind.mkdir(parents=True, exist_ok=True)
    sizes = json.load(open(cfg["sizes"]))
    groups = defaultdict(list)
    for s, date, fid, lab in sizes:
        if s < 0: s = 3_000_000
        groups[(date, kind_of(stream, lab))].append((s, fid, lab))
    work = []; skipped = 0
    for (date, kind), cands in sorted(groups.items()):
        if year_filter and date[:4] != year_filter:
            continue
        cands.sort()
        slug = f"{date}_{stream}_{kind}"
        if (mind/date[:4]/week_monday(date)/f"{slug}.md").exists():
            skipped += 1
            continue
        work.append((stream, date, kind, cands))
    recovered = 0; unrec = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for (date, kind, fid, lab, mtext, data, reason) in ex.map(try_recover, work):
            if reason:
                unrec.append((date, kind, reason))
                print(f"  [{stream}] {date} {kind}: UNRECOVERED ({reason})", flush=True)
                continue
            slug = f"{date}_{stream}_{kind}"
            (raw/f"{slug}_{fid}.pdf").write_bytes(data)
            md_path = mind/date[:4]/week_monday(date)/f"{slug}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            header = (f"<!-- source: pmn | body: {body} | pmn_file: {fid} | label: {lab} | "
                      f"date: {date} | meeting_kind: {kind} | "
                      f"source_url: https://www.utah.gov/pmn/files/{fid}.pdf | "
                      f"retrieved: {datetime.date.today().isoformat()} -->\n\n")
            md_path.write_text(header + mtext, encoding="utf-8")
            recovered += 1
            print(f"  [{stream}] {date} {kind}: OK ({len(data)//1024}KB) {lab[:30]}", flush=True)
    return [], unrec, recovered, skipped

def main():
    args = sys.argv[1:]
    year_filter = None; only = None
    for a in args:
        if re.match(r"20\d\d$", a): year_filter = a
        elif a in STREAMS: only = a
    streams = [only] if only else list(STREAMS)
    for st in streams:
        print(f"=== stream {st} (year={year_filter or 'all'}) ===")
        rows, unrec, rec, sk = run_stream(st, STREAMS[st], year_filter)
        print(f"  -> recovered {rec}, skipped(existing) {sk}, unrecovered {len(unrec)}")

if __name__ == "__main__":
    main()
