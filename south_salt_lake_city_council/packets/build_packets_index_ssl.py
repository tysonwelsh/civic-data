#!/usr/bin/env python3
"""Parse South Salt Lake CivicPlus AgendaCenter listing HTML into a packet catalog.

SSL's AgendaCenter serves the AGENDA PACKET in BOTH the "Agenda" and "Minutes"
slots (recon.md HEADLINE FINDING) — the recorded roll-call minutes live on PMN and
are handled by the core repo. So every ViewFile row here is a packet, keyed by its
CivicPlus item id (MMDDYYYY-<id>); two ids on one council date = Work + Regular.

Reads raw/_listings/cat{2,3,4,5}_{2020..2026}.html (fetched by curl during the run),
emits _catalog.tsv with one row per (cat, id): body, date, meeting_type, title,
agenda_url, minutes_url. Sizing + final index.csv assembly happen in later steps.
"""
import re, os, glob, csv, html as htmlmod

CAT_BODY = {"4": "Council", "3": "PC", "5": "RDA", "2": "CRB"}
HERE = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(HERE, "raw", "_listings")

MONTHS = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August",
     "September","October","November","December"], 1)}

# One catAgendaRow block per meeting item.
ROW_RE = re.compile(r'<tr[^>]*class="catAgendaRow"[^>]*>(.*?)</tr>', re.S)
DATE_RE = re.compile(r'aria-label="Agenda for ([A-Za-z]+) (\d{1,2}), (\d{4})"')
AGENDA_RE = re.compile(r'href="/AgendaCenter/ViewFile/Agenda/_(\d{8}-\d+)"')
MIN_RE = re.compile(r'href="/AgendaCenter/ViewFile/Minutes/_(\d{8}-\d+)"')
# Every agenda-slot anchor (plain, ?html=true, ?packet=true) + its link text.
ANCHOR_RE = re.compile(
    r'<a [^>]*href="/AgendaCenter/ViewFile/Agenda/_(\d{8}-\d+)(\?[^"]*)?"[^>]*>(.*?)</a>',
    re.S)
# Generic/non-descriptive anchor labels to skip when choosing a title.
_SKIP_TITLES = {"pdf", "html", "packet", "", "(pdf)"}


def meeting_type(title):
    t = title.lower()
    if "work" in t or "study" in t or "special work" in t:
        return "work"
    if "special" in t:
        return "special"
    if "regular" in t:
        return "regular"
    return "regular"  # AgendaCenter default label; refined per-title below


def parse_file(path):
    cat = re.search(r'cat(\d)_', os.path.basename(path)).group(1)
    body = CAT_BODY[cat]
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = []
    for block in ROW_RE.findall(txt):
        am = AGENDA_RE.search(block)
        if not am:
            continue
        item_id = am.group(1)          # MMDDYYYY-<id>
        mmddyyyy, seq = item_id.split("-")
        dm = DATE_RE.search(block)
        if dm:
            mo, day, yr = MONTHS[dm.group(1)], int(dm.group(2)), int(dm.group(3))
        else:  # fall back to the id's MMDDYYYY
            mo, day, yr = int(mmddyyyy[0:2]), int(mmddyyyy[2:4]), int(mmddyyyy[4:8])
        date = f"{yr:04d}-{mo:02d}-{day:02d}"
        # Choose the most descriptive anchor text as the title. The plain PDF anchor
        # often reads just "PDF"; the ?html=true / ?packet=true siblings carry the real
        # "… Meeting Material(s)" label.
        title = ""
        for _id, _q, txt in ANCHOR_RE.findall(block):
            if _id != item_id:
                continue
            clean = htmlmod.unescape(re.sub(r"<[^>]+>", "", txt))
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean.lower() not in _SKIP_TITLES:
                title = clean
                break
        min_ids = MIN_RE.findall(block)
        out.append({
            "body": body, "cat": cat, "item_id": item_id, "seq": seq,
            "date": date, "meeting_type": meeting_type(title),
            "title": title,
            "agenda_url": f"https://sslc.gov/AgendaCenter/ViewFile/Agenda/_{item_id}",
            "minutes_url": (f"https://sslc.gov/AgendaCenter/ViewFile/Minutes/_{item_id}"
                            if item_id in min_ids else ""),
        })
    return out


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(LIST, "cat*_*.html"))):
        rows.extend(parse_file(f))
    # de-dupe by (body,item_id) — a page can't list the same id twice, but be safe
    seen, uniq = set(), []
    for r in rows:
        k = (r["body"], r["item_id"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    uniq.sort(key=lambda r: (r["body"], r["date"], r["seq"]))
    cols = ["body", "cat", "item_id", "seq", "date", "meeting_type",
            "title", "agenda_url", "minutes_url"]
    with open(os.path.join(HERE, "raw", "_catalog.tsv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(uniq)
    # summary
    from collections import Counter
    byb = Counter(r["body"] for r in uniq)
    print(f"{len(uniq)} packet items:", dict(byb))
    for body in ["Council", "PC", "RDA", "CRB"]:
        yrs = Counter(r["date"][:4] for r in uniq if r["body"] == body)
        print(f"  {body}: {dict(sorted(yrs.items()))}")
    has_min = sum(1 for r in uniq if r["minutes_url"])
    print(f"  rows with a Minutes-slot link too: {has_min}/{len(uniq)}")


if __name__ == "__main__":
    main()
