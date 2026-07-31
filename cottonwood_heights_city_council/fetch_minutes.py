#!/usr/bin/env python3
"""
Cottonwood Heights minutes acquisition — BOTH bodies (Council + Planning Commission).

CMS = Granicus / CivicPlus CivicEngage Central (www.cottonwoodheights.utah.gov). The
site 403s bare UAs -> needs the FULL browser header set (Accept + Accept-Language +
Sec-Fetch-Mode). Portal retains a rolling ~4-5 yr window (council minutes ~2022+, PC
~2024+), and the 2022 portal column has since decayed to 4 docs, so we UNION the portal
with Utah PMN (entity 111; body Council 2147, PC 2148) to reach the 2020 floor and fill
the thin recent years. Preference on a (date, meeting-type) collision = the portal
born-digital doc (source=civicplus); else PMN (source=pmn).

Resumable: a raw PDF / md already on disk is reused.

⚠️ DESTRUCTIVE — REGENERATES minutes_index.csv FROM SCRATCH. This is the full
re-acquisition path. It rebuilds each dataset's minutes_index.csv purely from the
CURRENT live portal+PMN harvest, so any on-disk index row the live listing no longer
serves — Wayback-byte docs, PMN docs outside the harvested body/year window, delisted
portal docs, promoted admin-hearing recoveries — is silently DROPPED, and any
deliberately-removed duplicate the listing still serves is RESURRECTED. This is exactly
what happened on 2026-07-19 (dropped 3 council + 39 PC recovered rows; resurrected the
removed 2024-01-02 duplicate). For ROUTINE refresh use the append-only ingest instead:

    python3 fetch_new.py --ingest        # append-only, never regenerates the index

This full rebuild now REFUSES to run without --force-full-rebuild and writes a
timestamped index backup under _backups/ before proceeding. Run:

    python3 fetch_minutes.py --force-full-rebuild            # both datasets
    python3 fetch_minutes.py meeting_minutes --force-full-rebuild
"""
import argparse
import csv
import datetime
import gzip
import re
import shutil
import subprocess
import sys
import urllib.request
import zlib
from pathlib import Path

CITY = Path(__file__).resolve().parent
HOST = "https://www.cottonwoodheights.utah.gov"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research; contact tysonwelsh@gmail.com)")
TODAY = "2026-07-12"
LOWTEXT = 800          # < this many chars of text layer -> image-only scan, OCR
MIN_MINUTES = 1200     # shorter -> a cancellation/stub, not real minutes
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

BODIES = {
    "meeting_minutes": {
        "title": "City Council",
        "portal": f"{HOST}/your-government/elected-officials/council-meeting-agendas-and-minutes",
        "pmn_body": "2147",
        "pmn_years": range(2020, 2025),   # portal covers 2022+ but decayed; union all PMN
    },
    "planning_commission": {
        "title": "Planning Commission",
        "portal": f"{HOST}/your-government/boards-and-commissions/planning-commission/agendas-packets-minutes",
        "pmn_body": "2148",
        "pmn_years": range(2020, 2025),
    },
}


def http_get(url, binary=False, retries=4):
    last = None
    for a in range(retries):
        if a:
            import time
            time.sleep(1.5 * (2 ** a))
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Fetch-Mode": "navigate",
                "Accept-Encoding": "gzip, deflate",
            })
            r = urllib.request.urlopen(req, timeout=90)
            data = r.read()
            enc = r.headers.get("Content-Encoding", "")
            if enc == "gzip":
                data = gzip.decompress(data)
            elif enc == "deflate":
                data = zlib.decompress(data)
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


# ---------------------------------------------------------------- meeting type

def type_slug(text):
    t = text.lower()
    if "oath" in t:
        return "oath-of-office"
    if "breakfast" in t:
        return "legislative-breakfast"
    if "retreat" in t:
        return "retreat"
    if "legislative" in t:
        return "legislative-work-session"
    if "emergency" in t:
        return "emergency"
    if "canvass" in t:
        return "board-of-canvassers"
    if "admin" in t and "hearing" in t:
        return "administrative-hearing"
    if "special" in t:
        return "special-meeting"
    if "planning commission" in t or "chpc" in t or " pc " in t:
        return "planning-commission"
    return "work-session-and-business-meeting"


def clean(frag):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", frag)).strip()


# ---------------------------------------------------------------- portal harvest

def harvest_portal(cfg):
    html = http_get(cfg["portal"])
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 2:
            continue
        desc = clean(tds[0])
        m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})", desc)
        if not m or m.group(1).lower() not in MONTHS:
            continue
        iso = f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
        anchors = re.findall(
            r'<a\s+href="([^"]*showpublisheddocument/[^"]+)"[^>]*>(.*?)</a>', tds[1], re.S)
        for url, lab in anchors:
            # tolerant label match (2026-07-19): the CMS fragments anchor labels
            # across child tags ("M" + "inutes") and appends entities
            # ("Minutes&nbsp;"), which the old exact == "minutes" silently
            # skipped — that is why several delisted-but-live minutes never
            # surfaced via the probe (Q3-2026 finding). Compare on the
            # entity-stripped, letters-only collapse, still requiring the label
            # to be exactly the word so "Agenda & Minutes Packet" never matches.
            lab_norm = re.sub(r"[^a-z]", "",
                              re.sub(r"&[a-z#0-9]+;", " ", clean(lab).lower()))
            if lab_norm in ("minutes", "minute"):
                out.append({"date": iso, "type": type_slug(desc), "url": url,
                            "source": "civicplus", "desc": desc})
                break
    return out


# ------------------------------------------------------------------ PMN harvest

def _fdate(label, row_iso):
    m = re.match(r"\s*(\d{2})(\d{2})(\d{2})\b", label)
    if m:
        mo, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= dd <= 31:
            return f"20{yy:02d}-{mo:02d}-{dd:02d}"
    m = re.search(r"(\d{1,2})[-_.](\d{1,2})[-_.](20\d{2}|\d{2})", label)
    if m:
        mo, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        yy = int(yy) if len(yy) == 4 else 2000 + int(yy)
        if 1 <= mo <= 12 and 1 <= dd <= 31:
            return f"{yy}-{mo:02d}-{dd:02d}"
    return row_iso


def harvest_pmn(cfg):
    html = http_get(f"https://www.utah.gov/pmn/list/notices.html?id={cfg['pmn_body']}&page=300")
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        txt = clean(tr)
        dm = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})", txt)
        row_iso = (f"{dm.group(3)}-{MONTHS[dm.group(1).lower()]:02d}-{int(dm.group(2)):02d}"
                   if dm and dm.group(1).lower() in MONTHS else None)
        for m in re.finditer(r'files/(\d+)\.pdf"[^>]*>([^<]*)</a>', tr):
            fid, label = m.group(1), m.group(2)
            low = label.lower()
            if "minute" not in low or "agenda" in low:
                continue
            iso = _fdate(label, row_iso)
            if not iso:
                continue
            if int(iso[:4]) not in cfg["pmn_years"]:
                continue
            out.append({"date": iso, "type": type_slug(label),
                        "url": f"https://www.utah.gov/pmn/files/{fid}.pdf",
                        "source": "pmn", "desc": label.strip(), "fid": fid})
    # dedupe within source: same (date,type) -> keep highest file id (latest approved)
    best = {}
    for it in out:
        k = (it["date"], it["type"])
        if k not in best or int(it["fid"]) > int(best[k]["fid"]):
            best[k] = it
    return list(best.values())


# --------------------------------------------------------------------- convert

def pdf_text(p):
    return subprocess.run(["pdftotext", "-layout", str(p), "-"],
                          capture_output=True, timeout=300).stdout.decode("utf-8", "replace")


def ocr(p):
    import tempfile
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-png", "-r", "300", str(p), str(Path(td) / "pg")],
                       check=True, timeout=1800)
        for png in sorted(Path(td).glob("pg*.png")):
            r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
    return "\n".join(out)


def docx_text(p):
    """Extract plain text from a .docx (some CivicEngage 'Minutes' anchors serve Word,
    not PDF). No python-docx available -> unzip word/document.xml, paragraph breaks on
    </w:p>, tabs on <w:tab/>, then strip all remaining tags + unescape."""
    import io
    import zipfile
    from html import unescape
    z = zipfile.ZipFile(io.BytesIO(p.read_bytes()))
    xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = xml.replace("</w:p>", "\n").replace("<w:tab/>", "\t").replace("<w:br/>", "\n")
    xml = re.sub(r"<[^>]+>", "", xml)
    return unescape(xml)


def convert(p):
    if p.suffix == ".docx":
        return docx_text(p), "docx-text"
    txt = pdf_text(p)
    if len(txt.strip()) < LOWTEXT:
        return ocr(p), "ocr"
    return txt, "pdf-text"


def looks_like_minutes(txt):
    if len(txt.strip()) < MIN_MINUTES:
        return False
    low = txt.lower()
    if "moved" in low and "second" in low:
        return True
    if re.search(r"motion|vote on motion|adjourn", low) and "minutes" in low[:1500]:
        return True
    return False


# ----------------------------------------------------------------------- build

def week_monday(iso):
    d = datetime.date.fromisoformat(iso)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def md_header(title, iso, url, fmt, source):
    return (f"# Cottonwood Heights {title} — {iso}\n\n"
            f"> Source URL: {url}\n"
            f"> Meeting date: {iso}  ·  Retrieved: {TODAY}  ·  Format: {fmt}  ·  Source: {source}\n\n"
            f"---\n\n")


def build_body(ds, cfg):
    ds_dir = CITY / ds
    (ds_dir / "raw").mkdir(parents=True, exist_ok=True)
    (ds_dir / "minutes").mkdir(parents=True, exist_ok=True)

    portal = harvest_portal(cfg)
    pmn = harvest_pmn(cfg)
    # union by (date,type); portal (civicplus) wins a collision
    merged = {}
    for it in pmn:
        merged[(it["date"], it["type"])] = it
    for it in portal:
        merged[(it["date"], it["type"])] = it            # portal overrides pmn
    items = sorted(merged.values(), key=lambda x: (x["date"], x["type"]))

    index_path = ds_dir / "minutes_index.csv"
    existing = {}
    if index_path.exists():
        for r in csv.DictReader(index_path.open()):
            existing[r["path"]] = r

    rows = []
    unrecovered = []
    for it in items:
        iso, typ, src = it["date"], it["type"], it["source"]
        year = iso[:4]
        slug = typ
        rel = f"minutes/{year}/{week_monday(iso)}/{iso}_{slug}.md"
        out = ds_dir / rel

        if out.exists():
            # already built -> keep its index row (rebuild below from disk)
            r = existing.get(rel)
            if r:
                rows.append(r)
                continue

        import time
        time.sleep(0.6)                                    # be polite between GETs
        try:
            data = http_get(it["url"], binary=True)
        except Exception as e:  # noqa: BLE001
            print(f"  FETCH-FAIL {iso} {slug} [{src}]: {e}")
            unrecovered.append((iso, year, it["desc"], f"fetch error: {e}", it["url"]))
            continue
        if data.startswith(b"%PDF"):
            ext = ".pdf"
        elif data.startswith(b"PK\x03\x04"):
            ext = ".docx"                                  # CivicEngage sometimes serves Word
        else:
            print(f"  NOT-DOC   {iso} {slug} [{src}] ({len(data)}b)")
            unrecovered.append((iso, year, it["desc"], "not a PDF/DOCX (portal returned HTML/stub)", it["url"]))
            continue
        raw_pdf = ds_dir / "raw" / f"{src}_{iso}_{slug}{ext}"
        raw_pdf.write_bytes(data)                          # raw retention
        txt, fmt = convert(raw_pdf)
        if not looks_like_minutes(txt):
            print(f"  STUB      {iso} {slug} [{src}] ({len(txt.strip())} chars) -> unrecovered")
            unrecovered.append((iso, year, it["desc"], "doc too short / not minutes prose", it["url"]))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md_header(cfg["title"], iso, it["url"], fmt, src) + txt.rstrip() + "\n",
                       encoding="utf-8")
        title = f"{cfg['title']} — {it['desc'][:80]}".rstrip()
        rows.append({"date": iso, "year": year, "title": title, "slug": slug,
                     "path": rel, "source": src, "source_url": it["url"], "format": fmt})
        print(f"  built {rel} [{src}/{fmt}]")

    # write index (sorted by date, path)
    rows = sorted(rows, key=lambda r: (r["date"], r["path"]))
    with index_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "year", "title", "slug", "path",
                                          "source", "source_url", "format"])
        w.writeheader()
        w.writerows(rows)
    print(f"{ds}: {len(rows)} minutes indexed  "
          f"(civicplus {sum(1 for r in rows if r['source']=='civicplus')}, "
          f"pmn {sum(1 for r in rows if r['source']=='pmn')})")

    if unrecovered:
        up = ds_dir / "minutes_unrecovered.csv"
        with up.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "year", "description", "reason", "source_url"])
            for u in sorted(set(unrecovered)):
                w.writerow(u)
        print(f"{ds}: {len(set(unrecovered))} unrecovered logged")
    return rows


DESTRUCTIVE_WARNING = """\
============================================================================
  REFUSING TO RUN — this is the DESTRUCTIVE full index re-acquisition.
============================================================================
It REGENERATES minutes_index.csv from a fresh live portal+PMN harvest, DROPPING
every on-disk row the current listing no longer serves (Wayback-byte docs, PMN
docs outside the harvested body/year window, delisted portal docs, promoted
admin-hearing recoveries) and RESURRECTING deliberately-removed duplicates.

  INCIDENT 2026-07-19: this path dropped 3 council + 39 PC recovered index rows
  and resurrected the removed 2024-01-02 duplicate (see TODO.md HARDENING BUNDLE
  and _removed_duplicates/).

For a ROUTINE refresh, use the APPEND-ONLY ingest — it never regenerates the
index and respects the removal ledger:

    python3 fetch_new.py --ingest

To deliberately run the full rebuild anyway (a timestamped backup of every index
is written first), re-invoke with:

    python3 fetch_minutes.py --force-full-rebuild
============================================================================
"""


def backup_indexes(reason="prefetch-full-rebuild"):
    """Timestamped safety copy of every dataset's index + unrecovered file,
    written BEFORE a destructive rebuild so a bad run is always reversible."""
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    dest = CITY / "_backups" / f"{reason}-{ts}"
    saved = []
    for ds in BODIES:
        for name in ("minutes_index.csv", "minutes_unrecovered.csv"):
            src = CITY / ds / name
            if src.exists():
                out = dest / ds / name
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, out)
                saved.append(out)
    return dest, saved


def main():
    ap = argparse.ArgumentParser(
        description="Cottonwood Heights FULL minutes re-acquisition (DESTRUCTIVE "
                    "index rebuild — see module docstring; prefer fetch_new.py --ingest).")
    ap.add_argument("dataset", nargs="?", choices=list(BODIES),
                    help="limit to one dataset (default: both)")
    ap.add_argument("--force-full-rebuild", action="store_true",
                    help="REQUIRED acknowledgement that this REGENERATES the index "
                         "and may drop recovered/curated rows (2026-07-19 incident).")
    args = ap.parse_args()
    if not args.force_full_rebuild:
        sys.stderr.write(DESTRUCTIVE_WARNING)
        sys.exit(2)
    dest, saved = backup_indexes()
    print(f"pre-rebuild backup written: {dest}  ({len(saved)} file(s))")
    for ds, cfg in BODIES.items():
        if args.dataset and args.dataset != ds:
            continue
        print(f"=== {ds} ===")
        build_body(ds, cfg)


if __name__ == "__main__":
    main()
