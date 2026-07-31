#!/usr/bin/env python3
"""build_packets_index_ec.py — Emigration Canyon agenda-packets / supporting-documents
dataset (expand-city-sources source 1).

Emigration Canyon is PMN-ONLY (no city document CMS). Every meeting notice on Utah
Public Notice carries labeled attachments — Agenda, Approved Minutes, one or more
"Supporting Documents" / item handouts (all under the PMN category label
`Public Information Handout`), and often an Audio Recording (.MP3). The PACKET is the
Supporting-Documents bundle + the item-level handouts (resolution/ordinance drafts,
interlocal agreements, exhibits, staff reports) attached to a meeting. This script
harvests those for both bodies, keyed by `date` + `body` (+ `meeting_type` for the
same-day Workshop vs Regular) so a packet joins the minutes/votes layers.

  * COUNCIL             -> PMN body 5809   (`.../list/notices.html?id=5809&page=N`)
  * PLANNING COMMISSION -> PMN body 1562   (`.../list/notices.html?id=1562&page=N`)

⚠ NOT pmn.utah.gov — the file store is www.utah.gov/pmn/files/<id>.pdf. The bare
`?id=` list endpoint 500s "Technical Difficulties"; the `&page=N` form is REQUIRED and
is CUMULATIVE — walk page 0,1,2,... until the (notice,file) set stops growing.

DROPPED (not packets — recorded in AVAILABILITY.md, never stored as non-packets):
  - Meeting Minutes (they are the meeting_minutes/ + planning_commission/ datasets)
  - Agenda-ONLY documents (a bare agenda with no supporting content)
  - Audio recordings (.MP3/.wav/.m4a)
  - Cancellation / no-meeting / annual meeting-schedule notices
  - Branding / images (logos, IMG_*)

PURGE FLOOR: data floor is 2017, but PMN purges bulky handout/packet attachments
older than ~mid-2018 (file-id ceiling ≈ 450000 → HTTP 404). Recovered minutes begin
2018-10 (council) / 2018-11 (PC); supporting-doc attachments are purged at least as
aggressively. Purged-era candidates are NOT fetched (they 404); their count is surfaced
in AVAILABILITY.md as the honest floor, never fabricated.

Stages (idempotent; run in order):
    python3 build_packets_index_ec.py --harvest   # walk PMN lists -> _candidates.csv (+ raw/_pages/)
    python3 build_packets_index_ec.py --fetch      # download docs -> raw/<date>/ (+ _fetch_log.jsonl)
    python3 build_packets_index_ec.py --index      # -> index.csv (reads text/_extraction_log.csv)

Then: python3 /Users/tysonwelsh/civic-data/scripts/extract_packet_text.py emigration_canyon
and re-run `--index` to finalize format/extraction_method from the extraction log.
"""
import argparse, csv, datetime, hashlib, html, os, re, subprocess, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RAW = os.path.join(HERE, "raw")
PAGES = os.path.join(RAW, "_pages")
CAND = os.path.join(HERE, "_candidates.csv")
sys.path.insert(0, os.path.join(REPO, ".claude", "skills", "expand-city-sources", "scripts"))

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0")
NOW = "2026-07-14T00:00:00Z"
RETRIEVED = "2026-07-14"
FLOOR = datetime.date(2017, 1, 1)
PURGE_FILE_ID_CEILING = 450000   # file ids below this 404 (PMN handout retention purge)

BODIES = {"5809": "Council", "1562": "PlanningCommission"}
MAX_PAGES = 80

MINUTELIKE = re.compile(r'minute', re.I)
AGENDA = re.compile(r'agenda', re.I)
SUPPORTING = re.compile(r'supporting\s*doc', re.I)
PACKET = re.compile(r'\bpacket\b|binder', re.I)
STAFFREPORT = re.compile(r'staff\s*report', re.I)
# meeting-cancellation notices ONLY — NOT substantive resolutions that happen to say
# "cancel" ("Resolution to Cancel Election", "R2025-10 Canceling the Mayoral Race" are kept).
CANCEL = re.compile(r'(?:meeting|mtg|ws|cc|pc)\s*cancel|cancel+ed\b|'
                    r'no[\s_-]*meeting|meeting\s*schedule', re.I)
BRANDING = re.compile(r'\b(logo|logos|img_)\b|\.(jpg|jpeg|png|gif)$', re.I)
AUDIO = {"mp3", "wav", "m4a"}


# ------------------------------------------------------------------ fetch pages
def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl", "-k", "-sL", "--max-time", "90", "-A", UA, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
    return ""


def cache_pages():
    """Walk each body's cumulative notice list until the (notice) id set stops growing.
    Cache every page HTML under raw/_pages/ (re-parseable; delete to force a fresh pull)."""
    os.makedirs(PAGES, exist_ok=True)
    for body in BODIES:
        seen, stale, page = set(), 0, 0
        while page < MAX_PAGES and stale < 3:
            p = os.path.join(PAGES, f"pmn_{body}_p{page}.html")
            if os.path.exists(p):
                htmltext = open(p, encoding="utf-8", errors="replace").read()
            else:
                htmltext = curl(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page={page}")
                open(p, "w", encoding="utf-8").write(htmltext)
            before = len(seen)
            for m in re.finditer(r'/pmn/sitemap/notice/(\d+)\.html', htmltext):
                seen.add(m.group(1))
            stale = stale + 1 if len(seen) == before else 0
            page += 1
        print(f"  body {body} ({BODIES[body]}): walked {page} pages, {len(seen)} notices")


# ------------------------------------------------------------------ parse
def parse_body(body):
    """Yield dicts per attachment file across all cached list pages for a body:
    date, fid, ext, filename, label, notice_url."""
    seen = {}
    for fn in sorted(os.listdir(PAGES)):
        if not fn.startswith(f"pmn_{body}_p"):
            continue
        htmltext = open(os.path.join(PAGES, fn), encoding="utf-8", errors="replace").read()
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', htmltext, re.S):
            dt = re.search(r'(\d{4})/(\d{2})/(\d{2})', row)
            if not dt:
                continue
            date = f"{dt.group(1)}-{dt.group(2)}-{dt.group(3)}"
            nu = re.search(r'/pmn/sitemap/notice/(\d+)\.html', row)
            notice = f"https://www.utah.gov/pmn/sitemap/notice/{nu.group(1)}.html" if nu else ""
            for li in re.findall(r'<li>(.*?)</li>', row, re.S):
                fm = re.search(r'/pmn/files/(\d+)\.(\w+)', li)
                if not fm:
                    continue
                fid, ext = fm.group(1), fm.group(2).lower()
                nm = re.search(r'aria-label="Download (.*?)(?: \(opens|")', li, re.S)
                name = html.unescape(re.sub(r'\s+', ' ', nm.group(1)).strip()) if nm else ""
                after = li.split('</a>')[-1]
                lbl = re.search(r'\(([^)]*)\)', after)
                lbl = lbl.group(1).strip() if lbl else ""
                seen[fid] = {"date": date, "fid": fid, "ext": ext,
                             "filename": name, "label": lbl, "notice_url": notice}
    return list(seen.values())


def kind_for(name):
    if PACKET.search(name):
        return "full_packet"
    if SUPPORTING.search(name):
        return "supporting_docs"
    if STAFFREPORT.search(name):
        return "staff_report"
    return "supporting_docs"


def meeting_type_for(name):
    t = name.lower()
    if "special" in t:
        return "Special"
    if "work session" in t or "worksession" in t or "workshop" in t:
        return "Workshop"
    if "emergency" in t:
        return "Emergency"
    if "canvass" in t:
        return "Canvass"
    return ""


BAREDATE = re.compile(r'^\s*\d{1,2}[-.]\d{1,2}[-.]\d{2,4}\s*(\(\d+\))?\s*$')


def _filename_date(name):
    m = re.match(r'\s*(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})', name)
    if not m:
        return None
    mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if yy < 100:
        yy += 2000
    try:
        return datetime.date(yy, mm, dd)
    except ValueError:
        return None


def is_packet(a):
    """True if this attachment is a genuine packet/supporting-doc (not minutes/agenda/audio)."""
    name, lbl, ext = a["filename"], a["label"], a["ext"]
    if ext in AUDIO:
        return False
    if lbl.lower() == "meeting minutes" or MINUTELIKE.search(name):
        return False
    if CANCEL.search(name):
        return False
    if BRANDING.search(name):
        return False
    # agenda-ONLY: an agenda that is not also a supporting-docs bundle / packet
    if AGENDA.search(name) and not (SUPPORTING.search(name) or PACKET.search(name)):
        return False
    # bare "MM-DD-YY.ext" whose date != the notice date = a prior meeting's own doc
    # (minutes/agenda) re-posted for approval — duplicates the minutes layer, drop it
    base = os.path.splitext(name)[0]
    if BAREDATE.match(base):
        fd = _filename_date(name)
        try:
            nd = datetime.date.fromisoformat(a["date"])
        except ValueError:
            nd = None
        if fd and nd and fd != nd:
            return False
    return True


# ------------------------------------------------------------------ filenames
def safe_name(fid, title, ext):
    stem = os.path.splitext(title)[0]
    stem = re.sub(r'[^\w.\- ]+', '_', stem).strip().replace(' ', '_')
    stem = re.sub(r'_+', '_', stem)[:100].strip('_')
    if not stem:
        stem = "doc"
    return f"{fid}_{stem}.{ext}"


CAND_FIELDS = ["date", "body", "meeting_type", "packet_kind", "title", "label",
               "pmn_body", "fid", "ext", "source_url", "notice_url",
               "purged", "raw_rel", "raw_name"]


def harvest():
    cache_pages()
    rows, purged = [], []
    for body, bodyname in BODIES.items():
        for a in parse_body(body):
            try:
                d = datetime.date.fromisoformat(a["date"])
            except ValueError:
                continue
            if d < FLOOR:
                continue
            if not is_packet(a):
                continue
            rec = {
                "date": a["date"], "body": bodyname,
                "meeting_type": meeting_type_for(a["filename"]),
                "packet_kind": kind_for(a["filename"]),
                "title": a["filename"] or f"{a['fid']}.{a['ext']}",
                "label": a["label"], "pmn_body": body, "fid": a["fid"], "ext": a["ext"],
                "source_url": f"https://www.utah.gov/pmn/files/{a['fid']}.{a['ext']}",
                "notice_url": a["notice_url"],
                "purged": "1" if int(a["fid"]) < PURGE_FILE_ID_CEILING else "",
            }
            (purged if rec["purged"] else rows).append(rec)
    # Assign raw paths to ALL candidates (incl. purged-era). We still ATTEMPT the
    # purged ones in --fetch so the fetch log carries the real 200/404 evidence for
    # the purge floor (the fid<450000 flag is only a heuristic; borderline late-2018
    # files may in fact be live).
    allrows = rows + purged
    used = {}
    for r in allrows:
        name = safe_name(r["fid"], r["title"], r["ext"])
        key = (r["date"], name.lower())
        used[key] = used.get(key, 0) + 1
        if used[key] > 1:
            stem, e = os.path.splitext(name)
            name = f"{stem}_{used[key]}{e}"
        r["raw_name"] = name
        r["raw_rel"] = f"raw/{r['date']}/{name}"
    allrows.sort(key=lambda r: (r["date"], r["body"], r["title"]))
    with open(CAND, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAND_FIELDS)
        w.writeheader()
        w.writerows(allrows)
    by = Counter((r["body"], r["purged"] or "live") for r in allrows)
    print(f"harvested {len(allrows)} candidate packet docs ({len(rows)} live, "
          f"{len(purged)} purged-era) -> {CAND}")
    for k, v in sorted(by.items()):
        print(f"  {k[0]:18s} {k[1]:6s} {v}")


def load_cand():
    with open(CAND, newline="") as f:
        return list(csv.DictReader(f))


def fetch():
    import polite_fetch
    rows = load_cand()   # attempt ALL (purged-era included) so 404s are logged as evidence
    done = 0
    for r in rows:
        outdir = os.path.join(HERE, "raw", r["date"])
        dest = os.path.join(outdir, r["raw_name"])
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        rec = polite_fetch.save(r["source_url"], outdir, name=r["raw_name"],
                                referer=None, delay=1.0, now=NOW)
        done += 1
        tag = "ok " if rec["ok"] else "FAIL"
        print(f'{tag} {rec["status"]} {rec["bytes"]:>9} {r["date"]}/{r["raw_name"]}')
    print(f"fetched {done} new files")


def load_extraction_log():
    p = os.path.join(HERE, "text", "_extraction_log.csv")
    out = {}
    if os.path.exists(p):
        for row in csv.DictReader(open(p)):
            out[row.get("stem", "")] = row.get("status", "")
    return out


INDEX_FIELDS = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
                "retrieved_date", "format", "extraction_method", "path",
                "source", "pmn_body", "notice_url", "bytes", "sha256"]


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def index():
    rows = load_cand()   # index whatever landed on disk (200); purged 404s are skipped
    xlog = load_extraction_log()
    out, missing = [], 0
    for r in rows:
        disk = os.path.join(HERE, r["raw_rel"])
        if not (os.path.exists(disk) and os.path.getsize(disk) > 0):
            missing += 1
            continue
        ext = r["ext"].lower()
        stem = os.path.splitext(r["raw_name"])[0]
        status = xlog.get(stem, "")
        if ext in ("docx", "doc"):
            fmt, method = "text", "none (docx raw retained)"
        elif status in ("extracted", "skipped-exists"):
            fmt, method = "text", "pdftotext -layout"
        elif status == "image_only":
            fmt, method = "scanned", "none (image-only PDF; vision/OCR to read)"
        elif status == "too_big":
            fmt, method = "text", "none (oversize; raw retained)"
        else:
            fmt, method = ("text", "pdftotext -layout") if ext == "pdf" else ("text", "none (raw retained)")
        out.append({
            "date": r["date"], "title": r["title"], "body": r["body"],
            "meeting_type": r["meeting_type"], "packet_kind": r["packet_kind"],
            "source_url": r["source_url"], "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": method, "path": r["raw_rel"],
            "source": "pmn", "pmn_body": r["pmn_body"], "notice_url": r["notice_url"],
            "bytes": os.path.getsize(disk), "sha256": sha256_16(disk),
        })
    out.sort(key=lambda x: (x["date"], x["body"], x["title"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS)
        w.writeheader()
        w.writerows(out)
    total = sum(x["bytes"] for x in out)
    print(f"index.csv: {len(out)} rows, {total/1e6:.1f} MB stored"
          + (f" ({missing} candidates had no file on disk)" if missing else ""))
    by = Counter((x["body"], x["date"][:4]) for x in out)
    for k, v in sorted(by.items()):
        print(f"  {k[0]:18s} {k[1]} {v}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--index", action="store_true")
    a = ap.parse_args()
    if a.harvest:
        harvest()
    if a.fetch:
        fetch()
    if a.index:
        index()
    if not (a.harvest or a.fetch or a.index):
        ap.print_help()
