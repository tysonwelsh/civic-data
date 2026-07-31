#!/usr/bin/env python3
"""Build the Housing Authority (Housing Connect / HACSL) minutes corpus.

Source of truth for MINUTES is housingconnect.org (the agency's own site), enumerated
via its WordPress media REST API. Utah Public Notice public body 2535 ("Housing Authority
Board") was checked and carries only agendas, board packets and audio recordings for this
body -- NO standalone approved minutes -- so the website is the minutes source. See SOURCES.md.

Meeting DATE is parsed from each PDF's text ("... OF THE BOARD OF COMMISSIONERS  <Month D, YYYY>"),
NOT from the filename: several 2025 filenames encode the finalized/approval date, not the
meeting date. Nothing is fabricated -- an image-only PDF is kept raw, its md skipped, the gap
logged in the index.

Outputs (idempotent):
  raw/<date>_<wpid>_minutes.pdf
  minutes/<year>/<date>_housing_authority.md   (front-matter + pypdf text)
  minutes_index.csv

Run:  python3 build.py        (re-downloads + rebuilds; safe to re-run)
Then: python3 extract_votes.py
"""
import os, re, json, csv, shutil, datetime, urllib.request
from pypdf import PdfReader

HA  = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HA, "raw")
UA  = "Mozilla/5.0 (civic-data research; contact tysonwelsh@gmail.com)"
API = "https://housingconnect.org/wp-json/wp/v2/media?search=minutes&per_page=100&_fields=id,source_url,date"
YEAR_FLOOR = 2020  # repo data floor

MONTHS = {m:i for i,m in enumerate(
    ['january','february','march','april','may','june','july','august',
     'september','october','november','december'],1)}

def http(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode("utf-8","replace")

def enumerate_board_minutes():
    """Return [(wp_id, source_url)] for Board-of-Commissioners minutes PDFs."""
    items = json.loads(http(API))
    out = []
    for m in items:
        u = m["source_url"]; fn = u.rsplit("/",1)[-1].lower()
        if not fn.endswith(".pdf"): continue          # skip .docx duplicates
        if "minute" not in fn: continue
        if not re.search(r"board|commission|boc", fn): continue
        out.append((m["id"], u))
    return out

def parse_meeting_date(text):
    for m in re.finditer(r'\b([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})\b', text[:1500]):
        mon = m.group(1).lower()
        if mon in MONTHS:
            try: return datetime.date(int(m.group(3)), MONTHS[mon], int(m.group(2))).isoformat()
            except ValueError: continue
    return None

def meeting_kind(text):
    h = text[:1500].lower()
    return "Special" if "special" in h else ("Annual" if "annual" in h else "Regular")

def main():
    os.makedirs(RAW, exist_ok=True)
    board = enumerate_board_minutes()
    rows, gaps, seen = [], [], {}
    for wid, url in sorted(board, key=lambda x: x[1]):
        pdf = http(url, binary=True)
        try:
            import io
            reader = PdfReader(io.BytesIO(pdf))
            text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception as e:
            gaps.append((url, "pdf-read-error", str(e)[:60])); continue
        date = parse_meeting_date(text)
        if len(text.strip()) < 200:                    # image-only / unextractable
            fm = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', url.rsplit("/",1)[-1])
            fdate = f"20{fm.group(1)}-{fm.group(2)}-{fm.group(3)}" if fm and int(fm.group(1))>=19 else None
            if fdate: shutil.copyfileobj(__import__("io").BytesIO(pdf), open(os.path.join(RAW, f"{fdate}_{wid}_minutes.pdf"),"wb"))
            gaps.append((url, "image-only", f"date~{fdate}"))
            if fdate and int(fdate[:4]) >= YEAR_FLOOR:
                rows.append(dict(date=fdate, body="Housing Authority", md_path="",
                    source_url=url, minutes_status="image-only",
                    note="PDF has no extractable text (scanned/image-only); raw retained"))
            continue
        if not date or int(date[:4]) < YEAR_FLOOR:
            continue
        year = date[:4]
        open(os.path.join(RAW, f"{date}_{wid}_minutes.pdf"),"wb").write(pdf)
        base = f"{date}_housing_authority" + ("" if date not in seen else f"_{wid}")
        seen.setdefault(date, []).append(wid)
        md_dir = os.path.join(HA, "minutes", year); os.makedirs(md_dir, exist_ok=True)
        header = ("---\njurisdiction: Salt Lake County\nbody: Housing Authority\n"
                  f"date: {date}\nsource_url: {url}\n"
                  "source: housingconnect.org (Housing Authority of the County of Salt Lake / Housing Connect); "
                  "PMN public body 2535 carries agendas/packets/audio only\n"
                  "extraction: pypdf text\n---\n\n")
        open(os.path.join(md_dir, f"{base}.md"),"w",encoding="utf-8").write(header + text.strip() + "\n")
        kind = meeting_kind(text)
        rows.append(dict(date=date, body="Housing Authority",
            md_path=f"agencies/housing_authority/minutes/{year}/{base}.md",
            source_url=url, minutes_status="Final",
            note="" if kind=="Regular" else f"{kind} meeting"))
    rows.sort(key=lambda r:(r["date"], r["md_path"]))
    with open(os.path.join(HA,"minutes_index.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","body","md_path","source_url","minutes_status","note"])
        w.writeheader(); [w.writerow(r) for r in rows]
    conv = [r for r in rows if r["minutes_status"]=="Final"]
    print(f"board-minutes PDFs found: {len(board)}  index rows: {len(rows)}  converted-md: {len(conv)}")
    if conv: print("date range:", conv[0]["date"], "..", conv[-1]["date"])
    for g in gaps: print("  gap:", g)

if __name__ == "__main__":
    main()
