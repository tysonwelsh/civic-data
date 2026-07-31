#!/usr/bin/env python3
"""Fetch Salt Lake County meeting MINUTES documents and build the markdown corpus.

The Legistar harvest (harvest_legistar.py) gives the structured vote spine; this gives
the full minutes TEXT — the retrieval/full-text-search layer (the other half of the
value: LLM search over what was actually said, not just how it was voted). Reads
db/staging/events.csv (which carries EventMinutesFile), downloads each minutes PDF,
extracts text, and writes a per-module markdown tree with a provenance header + index —
the same shape as every city's meeting_minutes/minutes/.

    <module>/minutes/<year>/<date>_<body>.md   + <module>/minutes_index.csv
    <module>/raw/<EventId>_minutes.pdf         (retained originals; gitignored)

DERIVED + idempotent (skips PDFs already downloaded). Born-digital text (no OCR).
"""
import csv, os, re, urllib.request, time

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
STG = os.path.join(HERE, "staging")

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "civic-data/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                f.write(r.read())
            return os.path.getsize(dest) > 1000
        except Exception as e:
            if i == 3:
                print("  ! download failed:", url, repr(e))
                return False
            time.sleep(3 * (i + 1))
    return False


def main():
    events = []
    for base in (STG, os.path.join(HERE, "staging_ws")):
        p = os.path.join(base, "events.csv")
        if os.path.exists(p):
            events += list(csv.DictReader(open(p, encoding="utf-8")))
    idx = {}   # module -> list of index rows
    got = missing = 0
    for e in events:
        murl = (e.get("EventMinutesFile") or "").strip()
        module = e.get("_module") or "legislative"
        if not murl:
            missing += 1
            idx.setdefault(module, []).append(
                [e["EventDate"][:10], e["EventBodyName"], "", "",
                 e.get("EventMinutesStatusName") or "", "no minutes file published"])
            continue
        year = e["EventDate"][:4]
        raw_dir = os.path.join(COUNTY, module, "raw")
        md_dir = os.path.join(COUNTY, module, "minutes", year)
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(md_dir, exist_ok=True)
        pdf = os.path.join(raw_dir, "%s_minutes.pdf" % e["EventId"])
        # include EventId so two same-day meetings of one body never overwrite each other
        base = "%s_%s_%s" % (e["EventDate"][:10], slug(e["EventBodyName"]), e["EventId"])
        md = os.path.join(md_dir, base + ".md")
        if not fetch(murl, pdf):
            missing += 1
            continue
        try:
            reader = PdfReader(pdf)
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as ex:
            print("  ! parse failed:", pdf, repr(ex))
            missing += 1
            continue
        header = (
            "---\n"
            "jurisdiction: Salt Lake County\n"
            "body: %s\n"
            "date: %s\n"
            "source_url: %s\n"
            "source: Legistar (slco) EventMinutesFile\n"
            "minutes_status: %s\n"
            "extraction: pypdf text (born-digital)\n"
            "---\n\n" % (e["EventBodyName"], e["EventDate"][:10], murl,
                         e.get("EventMinutesStatusName") or ""))
        with open(md, "w", encoding="utf-8") as f:
            f.write(header + text)
        rel = os.path.relpath(md, COUNTY)
        idx.setdefault(module, []).append(
            [e["EventDate"][:10], e["EventBodyName"], rel, murl,
             e.get("EventMinutesStatusName") or "", ""])
        got += 1

    for module, rows in idx.items():
        rows.sort(key=lambda r: (r[0], r[1]))
        with open(os.path.join(COUNTY, module, "minutes_index.csv"), "w",
                  newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["date", "body", "md_path", "source_url", "minutes_status", "note"])
            wr.writerows(rows)
    print("minutes: %d downloaded+converted, %d without a published minutes file" % (got, missing))


if __name__ == "__main__":
    main()
