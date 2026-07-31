#!/usr/bin/env python3
"""build_packets_index_copperton.py — build the Town of Copperton agenda-packets /
supporting-documents dataset (expand-city-sources source 1).

Copperton publishes the "Supporting Documents" / packet behind each meeting on TWO
portals; this script harvests both, on a CLEAN NON-OVERLAPPING date/body split:

  * COUNCIL, dates <= 2023-12-31 (metro-township era) -> Utah PMN body 5831
    `[Public Information Handout]`/`[Other]` per-meeting supporting docs.
  * COUNCIL, dates >= 2024-01-01 (town era)            -> the town GoDaddy year pages
    (copperton.utah.gov/<YEAR>-agendas...), docs on img1.wsimg.com. The town packages
    these as combined "Agenda with Supporting Documents" / "Meeting Packet" / "Agenda
    Packet" PDFs + item-level staff reports.
  * PLANNING COMMISSION, all dates                     -> Utah PMN body 1560
    (`*_Packet.pdf`, `*_Agenda.pdf`, staff reports, hearing notices).

Rationale for the split (documented in AVAILABILITY.md): PMN body 5831 mirrors the
GoDaddy 2023 page but with cleaner per-meeting date labels, so 2023 is taken from PMN;
the GoDaddy combined-packet bundles are the town's own packaging for 2024+, so those
years are taken from GoDaddy. No meeting is sourced from both.

Floor: 2017 (repo data floor). PMN attachments older than ~mid-2018 are 404-purged
(the honest 2017-02 -> 2018-06 gap) — surfaced but NOT counted as recoverable.

The listing pages are fetched with `curl -k` + a browser UA (the copperton.utah.gov
GoDaddy cert covers secureserversites.net, so plain requests/WebFetch fail on the
LISTING host only). The actual documents live on img1.wsimg.com and www.utah.gov/pmn,
both with valid certs, so they download through scripts/polite_fetch.py (requests).

Stages (idempotent; run in order):
    python3 build_packets_index_copperton.py --harvest   # -> _candidates.csv (+ raw/_pages/)
    python3 build_packets_index_copperton.py --fetch      # download docs -> raw/<date>/ (+ logs)
    python3 build_packets_index_copperton.py --index      # -> index.csv (reads text/_extraction_log.csv if present)

Then: python3 /Users/tysonwelsh/civic-data/scripts/extract_packet_text.py copperton
and re-run `--index` to finalize format/extraction_method from the extraction log.

EXCLUSIONS (kept out of the packet dataset, recorded in AVAILABILITY.md):
  - minutes & audio (minutes are in meeting_minutes/ / planning_commission/; audio out of scope)
  - PC cancellation / no-meeting notices (the "PC mostly cancelled" story is quantified
    in AVAILABILITY.md instead of stored as ~non-packets)
  - re-posted PRIOR-meeting minutes attached to a later notice for approval
  - branding/images (logos, IMG_*, ballots) and bare annual meeting-schedule PDFs
  - GoDaddy loose docs with no determinable MEETING date (undated budgets/ordinance texts)
"""
import argparse, csv, datetime, glob, hashlib, html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RAW = os.path.join(HERE, "raw")
PAGES = os.path.join(RAW, "_pages")
CAND = os.path.join(HERE, "_candidates.csv")
sys.path.insert(0, os.path.join(REPO, ".claude", "skills", "expand-city-sources", "scripts"))

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36')
NOW = "2026-07-14T00:00:00Z"
RETRIEVED = "2026-07-14"
FLOOR = datetime.date(2017, 1, 1)
PURGE_CUTOFF = datetime.date(2018, 7, 1)   # PMN attachments older than ~this 404 (retention purge)
COUNCIL_GODADDY_FROM = datetime.date(2024, 1, 1)

GODADDY_YEAR_PAGES = {
    2023: "https://copperton.utah.gov/2023-agendas-%26-minutes",
    2024: "https://copperton.utah.gov/2024-agendas-%26-minutes-1",
    2025: "https://copperton.utah.gov/2025-agendas-%26-minutes-1",
    2026: "https://copperton.utah.gov/2026-agendas-%26-minutes",
}
PMN_PAGES = [1, 20, 48]   # cumulative notices list depths (union reaches oldest rows)


# ------------------------------------------------------------------ fetch pages
def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl", "-k", "-sL", "--max-time", "90", "-A", UA, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
    return ""


def cache_pages():
    os.makedirs(PAGES, exist_ok=True)
    for yr, url in GODADDY_YEAR_PAGES.items():
        p = os.path.join(PAGES, f"godaddy_{yr}.html")
        if not os.path.exists(p):
            open(p, "w", encoding="utf-8").write(curl(url))
    for body in (5831, 1560):
        for pg in PMN_PAGES:
            p = os.path.join(PAGES, f"pmn_{body}_p{pg}.html")
            if not os.path.exists(p):
                open(p, "w", encoding="utf-8").write(
                    curl(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page={pg}"))


# ------------------------------------------------------------------ date parse
def date_from_prefix(s):
    """Meeting date at the START of a GoDaddy title: MM-DD-YYYY / MM-DD-YY / M.D.YYYY."""
    m = re.match(r'\s*(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})\b', s)
    if not m:
        return None
    mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if yy < 100:
        yy += 2000
    try:
        return datetime.date(yy, mm, dd)
    except ValueError:
        return None


def date_from_filename(fn):
    """Any embedded date in a filename: YYMMDD_ (PMN PC) or MM-DD-YY(YY)."""
    m = re.match(r'(\d{2})(\d{2})(\d{2})[_\.]', fn)   # 190312_ -> 2019-03-12
    if m:
        yy, mm, dd = 2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(yy, mm, dd)
        except ValueError:
            pass
    m = re.search(r'(\d{1,2})[-\.](\d{1,2})[-\.](\d{2,4})', fn)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yy < 100:
            yy += 2000
        try:
            return datetime.date(yy, mm, dd)
        except ValueError:
            pass
    return None


BRANDING = re.compile(r'\b(logo|logos|img_|kids read|ballot type|\.jpg|\.jpeg|\.png)\b', re.I)
MINUTELIKE = re.compile(r'minute', re.I)
CANCEL = re.compile(r'cancel+ed|no_meeting|meeting schedule', re.I)


def kind_for(title):
    t = title.lower()
    if 'packet' in t:
        return 'full_packet'
    if 'agenda with supporting' in t or 'binder' in t:
        return 'full_packet'
    if 'supporting doc' in t:
        return 'supporting_docs'
    if 'staff report' in t or re.search(r'\bitem\b', t):
        return 'staff_report'
    if 'agenda' in t:
        return 'agenda_packet'
    if 'notice' in t or 'hearing' in t:
        return 'supporting_docs'
    return 'supporting_docs'


def meeting_type_for(title):
    t = title.lower()
    if 'special' in t:
        return 'Special'
    if 'worksession' in t or 'work session' in t or 'workshop' in t:
        return 'Work'
    if 'public hearing' in t and 'agenda' not in t:
        return 'PublicHearing'
    return ''


# ------------------------------------------------------------------ GoDaddy parse (council >= 2024)
def harvest_godaddy():
    out = []
    for yr in GODADDY_YEAR_PAGES:
        page = os.path.join(PAGES, f"godaddy_{yr}.html")
        if not os.path.exists(page):
            continue
        htmltext = open(page, encoding="utf-8", errors="replace").read()
        pairs = re.findall(
            r'aria-label="Download ([^"]*)"[^>]*href="(//img1\.wsimg\.com/blobby/go/07a53a68[^"]*?/downloads/[^"]+)"',
            htmltext)
        for label, href in pairs:
            label = html.unescape(label).strip()
            d = date_from_prefix(label)
            if not d or d < COUNCIL_GODADDY_FROM:
                continue
            if MINUTELIKE.search(label) or BRANDING.search(label):
                continue
            if not re.search(r'packet|supporting doc|\bitem\b|staff report|agenda', label, re.I):
                continue
            url = "https:" + href
            ext = os.path.splitext(url.split("?")[0])[1].lstrip(".").lower() or "pdf"
            out.append({
                "date": d.isoformat(), "body": "Council",
                "meeting_type": meeting_type_for(label),
                "packet_kind": kind_for(label), "title": label,
                "source": "godaddy", "pmn_body": "", "source_url": url, "ext": ext,
            })
    return out


# ------------------------------------------------------------------ PMN parse
def parse_pmn(body):
    """Return list of dicts: date, filename, ext, label, fid, notice_url."""
    seen = {}
    for pg in PMN_PAGES:
        page = os.path.join(PAGES, f"pmn_{body}_p{pg}.html")
        if not os.path.exists(page):
            continue
        htmltext = open(page, encoding="utf-8", errors="replace").read()
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', htmltext, re.S):
            dt = re.search(r'<td>(\d{4})/(\d{2})/(\d{2})', row)
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
                fn = re.search(r'aria-label="Download (.*?)(?: \(opens)', li, re.S)
                fn = html.unescape(re.sub(r'\s+', ' ', fn.group(1)).strip()) if fn else ""
                after = li.split('</a>')[-1]
                lbl = re.search(r'\(([^)]*)\)', after)
                lbl = lbl.group(1).strip() if lbl else ""
                seen[fid] = {"date": date, "filename": fn, "ext": ext, "label": lbl,
                             "fid": fid, "notice_url": notice}
    return list(seen.values())


def harvest_pmn_council():
    out = []
    for a in parse_pmn(5831):
        d = datetime.date.fromisoformat(a["date"])
        if d < FLOOR or d >= COUNCIL_GODADDY_FROM:      # 2024+ comes from GoDaddy
            continue
        if d < PURGE_CUTOFF:                             # 404-purged retention gap
            continue
        if a["ext"] in ("mp3", "wav", "m4a"):
            continue
        fn, lbl = a["filename"], a["label"]
        if lbl.lower() == "meeting minutes" or MINUTELIKE.search(fn):
            continue
        if BRANDING.search(fn):
            continue
        # prior-minutes-copy: a bare date-only filename whose date != the notice date
        fd = date_from_filename(fn)
        base = re.sub(r'\.(pdf|docx?|)$', '', fn, flags=re.I)
        bare = re.fullmatch(r'\s*\d{1,2}[-\.]\d{1,2}[-\.]\d{2,4}\s*(\(\d+\))?\s*', base)
        if bare and fd and fd != d:
            continue
        out.append({
            "date": a["date"], "body": "Council", "meeting_type": meeting_type_for(fn),
            "packet_kind": kind_for(fn), "title": fn, "source": "pmn", "pmn_body": "5831",
            "source_url": f"https://www.utah.gov/pmn/files/{a['fid']}.{a['ext']}",
            "notice_url": a["notice_url"], "ext": a["ext"],
        })
    return out


def harvest_pmn_pc():
    out = []
    for a in parse_pmn(1560):
        d = datetime.date.fromisoformat(a["date"])
        if d < FLOOR:
            continue
        if a["ext"] in ("mp3", "wav", "m4a"):
            continue
        fn, lbl = a["filename"], a["label"]
        # classify by FILENAME (PMN mislabels some agendas/packets as "Meeting Minutes")
        if re.search(r'minutes?approved|_minutes|^\w*minutes|\bminutes\b', fn, re.I):
            continue
        if CANCEL.search(fn):                            # cancellation / no-meeting / schedule
            continue
        if BRANDING.search(fn):
            continue
        out.append({
            "date": a["date"], "body": "PlanningCommission", "meeting_type": meeting_type_for(fn),
            "packet_kind": kind_for(fn), "title": fn, "source": "pmn", "pmn_body": "1560",
            "source_url": f"https://www.utah.gov/pmn/files/{a['fid']}.{a['ext']}",
            "notice_url": a["notice_url"], "ext": a["ext"],
        })
    return out


# ------------------------------------------------------------------ dedup
def dedup(rows):
    """Within (date, body): if a full_packet exists, drop bare agenda_packet siblings
    (an agenda is a subset of its packet). Keep everything else (staff reports, notices,
    amended-packet variants)."""
    from collections import defaultdict
    grp = defaultdict(list)
    for r in rows:
        grp[(r["date"], r["body"])].append(r)
    kept = []
    for (dte, body), items in grp.items():
        has_packet = any(i["packet_kind"] == "full_packet" for i in items)
        for i in items:
            if has_packet and i["packet_kind"] == "agenda_packet":
                # drop bare agenda only when a same-day packet supersedes it
                continue
            kept.append(i)
    kept.sort(key=lambda r: (r["date"], r["body"], r["title"]))
    return kept


# ------------------------------------------------------------------ filenames
def safe_name(title, ext):
    stem = os.path.splitext(title)[0]
    stem = re.sub(r'[^\w.\- ]+', '_', stem).strip().replace(' ', '_')
    stem = re.sub(r'_+', '_', stem)[:110].strip('_')
    if not stem:
        stem = "doc"
    return f"{stem}.{ext}"


# ------------------------------------------------------------------ stages
CAND_FIELDS = ["date", "body", "meeting_type", "packet_kind", "title", "source",
               "pmn_body", "source_url", "notice_url", "ext", "raw_rel", "raw_name"]


def harvest():
    cache_pages()
    rows = harvest_godaddy() + harvest_pmn_council() + harvest_pmn_pc()
    rows = dedup(rows)
    # assign raw paths + de-collide identical basenames within a date folder
    used = {}
    for r in rows:
        r.setdefault("notice_url", "")
        name = safe_name(r["title"], r["ext"])
        key = (r["date"], name.lower())
        if key in used:
            used[key] += 1
            stem, e = os.path.splitext(name)
            name = f"{stem}_{used[key]}{e}"
        else:
            used[key] = 1
        r["raw_name"] = name
        r["raw_rel"] = f"raw/{r['date']}/{name}"
    with open(CAND, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAND_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CAND_FIELDS})
    # summary
    from collections import Counter
    by = Counter((r["source"], r["body"]) for r in rows)
    print(f"harvested {len(rows)} candidate packet docs -> {CAND}")
    for k, v in sorted(by.items()):
        print(f"  {k[0]:8s} {k[1]:18s} {v}")


def load_cand():
    with open(CAND, newline="") as f:
        return list(csv.DictReader(f))


def fetch():
    import polite_fetch
    rows = load_cand()
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
    """stem -> status from packets/text/_extraction_log.csv (if extraction has run)."""
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
    rows = load_cand()
    xlog = load_extraction_log()
    out = []
    missing = 0
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
        elif status == "extracted" or status == "skipped-exists":
            fmt, method = "text", "pdftotext -layout"
        elif status == "image_only":
            fmt, method = "scanned", "none (image-only PDF; vision/OCR to read)"
        elif status == "too_big":
            fmt, method = "text", "none (oversize; raw retained)"
        else:  # not yet extracted -> assume born-digital pdf (refine after extraction)
            fmt, method = ("text", "pdftotext -layout") if ext == "pdf" else ("text", "none (raw retained)")
        out.append({
            "date": r["date"], "title": r["title"], "body": r["body"],
            "meeting_type": r["meeting_type"], "packet_kind": r["packet_kind"],
            "source_url": r["source_url"], "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": method, "path": r["raw_rel"],
            "source": r["source"], "pmn_body": r["pmn_body"],
            "notice_url": r.get("notice_url", ""),
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
