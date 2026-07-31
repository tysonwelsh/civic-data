#!/usr/bin/env python3
"""Build the Magna agenda-packet catalog from two portals into raw/_catalog.tsv.

TWO SOURCES (see AVAILABILITY.md):
  1. CivicPlus AgendaCenter cat3 (`magna.utah.gov`), 2022-2026 — the ONLY category
     the portal exposes (cat 1/2/4/5 all 404). It carries BOTH City Council and the
     in-session CRA (Community Reinvestment Agency) meetings; body is classified from
     the item TITLE ("CRA" -> CRA, else Council). Packet endpoint = the item's
     Agenda-slot ViewFile with `?packet=true` (the assembled full packet; >= plain).
  2. Utah PMN (`www.utah.gov/pmn`) — the deep archive + the ONLY source of Planning
     Commission packets (CivicPlus has no PC category). Body 5803 = Magna Council
     (used here for PRE-2022 council packets only; 2022+ council is CivicPlus); body
     1559 = Magna Planning Commission (ALL years, floor 2017 = Magna incorporation).
     PMN attachment TYPE LABELS are unreliable ("Public Information Handout"/"Other")
     so packet files are classified by FILENAME: priority packet > supporting >
     staff report > agenda; minutes/audio/ordinance-only notices carry no packet and
     are skipped. One best packet file is selected per notice (highest file id within
     the top-priority class = the final/amended upload).

Reads (already fetched by the run, browser UA):
  raw/_listings/cat3_2022.html .. cat3_2026.html         (CivicPlus AJAX listings)
  raw/_listings/pmn_5803_notices.html  (council)          (PMN cumulative page=400)
  raw/_listings/pmn_1559_notices.html  (planning)
Writes raw/_catalog.tsv (one row per packet: source, body, key, date, meeting_type,
title, packet_url, packet_kind).
"""
import re, os, glob, csv, html as htmlmod

HERE = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(HERE, "raw", "_listings")
CP_HOST = "https://magna.utah.gov"
PMN_FILE = "https://www.utah.gov/pmn/files/%s.pdf"
DATA_FLOOR = 2017  # Magna incorporated (metro township) 2017-01-01

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}

# ---------- CivicPlus cat3 ----------
ROW_RE = re.compile(r'<tr[^>]*class="catAgendaRow"[^>]*>(.*?)</tr>', re.S)
DATE_RE = re.compile(r'aria-label="Agenda for ([A-Za-z]+) (\d{1,2}), (\d{4})"')
AGENDA_ID_RE = re.compile(r'href="/AgendaCenter/ViewFile/Agenda/_(\d{8}-\d+)"')
ANCHOR_RE = re.compile(
    r'<a [^>]*href="/AgendaCenter/ViewFile/Agenda/_(\d{8}-\d+)(?:\?[^"]*)?"[^>]*>(.*?)</a>',
    re.S)
_SKIP_TITLES = {"pdf", "html", "packet", "agenda", "", "(pdf)"}


def _clean(s):
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def meeting_type(title):
    t = title.lower()
    if "work" in t or "study" in t or "retreat" in t:
        return "work"
    if "special" in t or "emergency" in t:
        return "special"
    return "regular"


def parse_civicplus():
    out = []
    for path in sorted(glob.glob(os.path.join(LIST, "cat3_*.html"))):
        txt = open(path, encoding="utf-8", errors="replace").read()
        for block in ROW_RE.findall(txt):
            am = AGENDA_ID_RE.search(block)
            if not am:
                continue
            item_id = am.group(1)
            mmddyyyy = item_id.split("-")[0]
            dm = DATE_RE.search(block)
            if dm:
                mo, day, yr = MONTHS[dm.group(1)], int(dm.group(2)), int(dm.group(3))
            else:
                mo, day, yr = int(mmddyyyy[0:2]), int(mmddyyyy[2:4]), int(mmddyyyy[4:8])
            date = f"{yr:04d}-{mo:02d}-{day:02d}"
            title = ""
            for _id, txt2 in ANCHOR_RE.findall(block):
                if _id != item_id:
                    continue
                clean = _clean(txt2)
                if clean.lower() not in _SKIP_TITLES:
                    title = clean
                    break
            body = "CRA" if re.search(r'\bCRA\b|Reinvestment', title, re.I) else "Council"
            out.append({
                "source": "civicplus", "body": body, "key": item_id, "date": date,
                "meeting_type": meeting_type(title),
                "title": title or f"{body} meeting {date}",
                "packet_url": f"{CP_HOST}/AgendaCenter/ViewFile/Agenda/_{item_id}?packet=true",
                "packet_kind": "full_packet",
            })
    # de-dupe by item id
    seen, uniq = set(), []
    for r in out:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        uniq.append(r)
    return uniq


# ---------- PMN ----------
NOTICE_RE = re.compile(r'sitemap/notice/(\d+)\.html">(.*?)</a>', re.S)
EVDATE_RE = re.compile(r'<td>([^<]*\d{2}:\d{2}[^<]*)</td>')
ATT_RE = re.compile(
    r'/pmn/files/(\d+)\.pdf"[^>]*aria-label="Download (.*?)\s*\(opens', re.S)

# Filename-based packet classifier: (priority, packet_kind). Lower priority num wins.
def classify_att(name):
    n = name.lower()
    if "packet" in n:
        return (0, "full_packet")
    if "supporting" in n:
        return (1, "full_packet")
    if "staff report" in n or "staffreport" in n:
        return (2, "full_packet")
    if "agenda" in n:
        # skip pure public-hearing notices masquerading; a real agenda is a thin packet
        return (3, "agenda_packet")
    return (9, None)  # minutes / audio / notice / ordinance -> not a packet


def parse_pmn(fn, body, min_year=None, max_year=None):
    txt = open(os.path.join(LIST, fn), encoding="utf-8", errors="replace").read()
    tbody = re.search(r'<tbody>(.*)</tbody>', txt, re.S).group(1)
    out = []
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.S):
        nt = NOTICE_RE.search(r)
        if not nt:
            continue
        notice_id = nt.group(1)
        title = _clean(nt.group(2))
        dm = EVDATE_RE.search(r)
        if not dm:
            continue
        m = re.match(r'(\d{4})/(\d{2})/(\d{2})', dm.group(1).strip())
        if not m:
            continue
        yr = int(m.group(1))
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if min_year and yr < min_year:
            continue
        if max_year and yr > max_year:
            continue
        atts = [(fid, _clean(nm)) for fid, nm in ATT_RE.findall(r)]
        # choose best packet-like attachment
        best = None  # (priority, -fileid_int, fid, name, kind)
        for fid, nm in atts:
            pr, kind = classify_att(nm)
            if kind is None:
                continue
            cand = (pr, -int(fid), fid, nm, kind)
            if best is None or cand < best:
                best = cand
        if best is None:
            continue
        pr, _, fid, nm, kind = best
        b = "CRA" if re.search(r'\bCRA\b|Reinvestment', title, re.I) else body
        out.append({
            "source": "pmn", "body": b, "key": fid, "date": date,
            "meeting_type": meeting_type(title + " " + nm),
            "title": title, "packet_url": PMN_FILE % fid, "packet_kind": kind,
            "pmn_notice_id": notice_id, "pmn_filename": nm,
        })
    return out


def main():
    rows = []
    rows += parse_civicplus()
    # PMN council: PRE-2022 only (2022+ council = CivicPlus), floor 2017
    rows += parse_pmn("pmn_5803_notices.html", "Council",
                      min_year=DATA_FLOOR, max_year=2021)
    # PMN planning commission: ALL years >= floor (no CivicPlus PC)
    rows += parse_pmn("pmn_1559_notices.html", "PC", min_year=DATA_FLOOR)

    rows.sort(key=lambda r: (r["body"], r["date"], r["source"], r["key"]))
    cols = ["source", "body", "key", "date", "meeting_type", "title",
            "packet_url", "packet_kind", "pmn_notice_id", "pmn_filename"]
    with open(os.path.join(HERE, "raw", "_catalog.tsv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    from collections import Counter
    print(f"{len(rows)} packet items catalogued")
    for src in ("civicplus", "pmn"):
        n = sum(1 for r in rows if r["source"] == src)
        print(f"  source={src}: {n}")
    for body in ("Council", "CRA", "PC"):
        sub = [r for r in rows if r["body"] == body]
        yrs = Counter(r["date"][:4] for r in sub)
        kinds = Counter(r["packet_kind"] for r in sub)
        print(f"  {body}: {len(sub)}  years={dict(sorted(yrs.items()))} kinds={dict(kinds)}")


if __name__ == "__main__":
    main()
