#!/usr/bin/env python3
"""
recover_packets.py — recover Vineyard minutes from saved agenda packets.

Background: 29 meetings (2023-10..2026-05) were logged in minutes_unrecovered.csv
because the CivicClerk GetMeetingFileStream(...,plainText=true) endpoint returned an
EMPTY body at build time (the "Minutes" fileId actually serves an oversized bundled
PDF). The PDFs were saved to raw/unrecovered_packets/. It turns out 26 of them carry a
real text layer, so a local `pdftotext -layout` recovers the full minutes — no OCR
needed. 3 files are truncated downloads (missing PDF catalog) and are handled separately.

This script:
  - reads minutes_unrecovered.csv
  - for each packet, runs pdftotext -layout
  - if the output looks like genuine minutes, writes
    minutes/<year>/<week-monday>/<date>_<slug>.md  (matching the existing format)
  - emits _recovered_rows.csv (new minutes_index rows) + prints a status table
It does NOT mutate minutes_index.csv / minutes_unrecovered.csv (done in a reviewed step).
"""
import csv, re, subprocess, sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent            # meeting_minutes/
PKTS = ROOT / "raw" / "unrecovered_packets"
MIN_DIR = ROOT / "minutes"
UNREC = ROOT / "minutes_unrecovered.csv"
OUT_ROWS = ROOT / "_recovered_rows.csv"

MIN_TEXT_LEN = 700        # below this -> not a usable text layer
MARKERS = re.compile(r"MINUTES OF|CALL TO ORDER|Councilmember|Present\b|Mayor\b", re.I)


def slugify(title):
    s = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-")
    return s


def week_monday(d):
    return d - timedelta(days=d.weekday())


def main():
    rows = list(csv.DictReader(open(UNREC, newline="")))
    out_rows = []
    print(f"{'date':12} {'event':>6} {'fileId':>6} {'txtKB':>6}  status")
    for r in rows:
        d = date.fromisoformat(r["date"])
        ev = r["event_id"]
        fid = r["minutes_fileId"]
        title = r["title"].strip()
        pkt = PKTS / f"{r['date']}_event{ev}_packet.pdf"
        status = ""
        if not pkt.exists():
            print(f"{r['date']:12} {ev:>6} {fid:>6} {'--':>6}  MISSING packet file")
            continue
        try:
            txt = subprocess.run(
                ["pdftotext", "-layout", str(pkt), "-"],
                capture_output=True, text=True, timeout=180).stdout
        except Exception as e:
            print(f"{r['date']:12} {ev:>6} {fid:>6} {'ERR':>6}  pdftotext error: {e}")
            continue
        kb = len(txt) // 1024
        if len(txt.strip()) < MIN_TEXT_LEN or not MARKERS.search(txt):
            print(f"{r['date']:12} {ev:>6} {fid:>6} {kb:>6}  NEEDS-OCR/REDOWNLOAD (thin text layer)")
            continue
        slug = slugify(title)
        wk = week_monday(d).isoformat()
        rel = f"minutes/{d.year}/{wk}/{r['date']}_{slug}.md"
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        src_url = (f"https://vineyardut.api.civicclerk.com/v1/Meetings/"
                   f"GetMeetingFileStream(fileId={fid})")
        header = (
            f"# {title} — {r['date']}\n\n"
            f"> Source: CivicClerk (Vineyard, UT) · event {ev} · fileId {fid}\n"
            f"> File: recovered from saved agenda packet via local `pdftotext -layout` "
            f"(CivicClerk plainText endpoint returned empty at build time)\n\n"
            f"---\n\n"
        )
        path.write_text(header + txt)
        out_rows.append({
            "date": r["date"], "year": str(d.year), "title": title, "slug": slug,
            "path": f"meeting_minutes/{rel}", "source": "civicclerk",
            "source_url": src_url, "format": "text",
        })
        print(f"{r['date']:12} {ev:>6} {fid:>6} {kb:>6}  OK -> {rel}")

    with open(OUT_ROWS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "year", "title", "slug", "path",
                                          "source", "source_url", "format"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nrecovered {len(out_rows)}/{len(rows)} -> wrote {OUT_ROWS.name}")


if __name__ == "__main__":
    main()
