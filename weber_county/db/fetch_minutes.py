#!/usr/bin/env python3
"""Harvest Weber County Commission minutes (born-digital PDFs) from the county's
self-hosted "Transparency" portal → legislative/minutes/<year>/<date>_commission.md
(with provenance front-matter) + legislative/minutes_index.csv + a missing-meeting ledger.

Weber County is a 3-member Board of Commissioners (NOT Legistar). Minutes are prose PDFs
with NAMED roll-call votes even on unanimous motions. Two portal indexes exist and neither
is complete alone, so we harvest their UNION:
  - commission_meetings.php  — direct min_MMDDYYYY[_N].pdf links (carries revision "_N" files)
  - commission_minutes_archive.php — minute_id links back to 2000 (resolve to the real PDF)

Floor: 2015-01-01 (the 2000-2014 depth is recorded in recon.md for a future backfill).
DERIVED + idempotent — cached PDFs are reused; re-run to pick up new meetings.
"""
import csv, os, re, sys, time, urllib.request, urllib.error, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
LEG = os.path.join(COUNTY, "legislative")
RAW = os.path.join(LEG, "raw")
MIN = os.path.join(LEG, "minutes")
FLOOR = "2015-01-01"

BASE = "https://www.webercountyutah.gov"
PORTAL = BASE + "/Transparency"
PDF_DIR = BASE + "/commission/documents/minutes"
UA = {"User-Agent": "Mozilla/5.0 (civic-data harvest; contact tysonwelsh@gmail.com)"}


def get(url, binary=False, tries=4):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa
            last = e
            time.sleep(0.5 * (t + 1))
    raise last


def mmddyyyy_iso(f):  # "01062026" -> "2026-01-06"
    return "%s-%s-%s" % (f[4:8], f[0:2], f[2:4])


def dash_iso(d):  # "01-06-2026" -> "2026-01-06"
    return "%s-%s-%s" % (d[6:], d[0:2], d[3:5])


def build_index():
    """Return {iso_date: (pdf_filename, source_index, detail_url)} for 2015+."""
    cm = get(PORTAL + "/commission_meetings.php")
    arch = get(PORTAL + "/commission_minutes_archive.php")

    # cm.html: date -> filename (prefer a revision "_N" file when the portal links one)
    cm_map = {}
    for fn in re.findall(r"(min_\d{8}(?:_\d)?\.pdf)", cm):
        m = re.match(r"min_(\d{8})(?:_(\d))?\.pdf", fn)
        iso = mmddyyyy_iso(m.group(1))
        if iso < FLOOR:
            continue
        rev = int(m.group(2) or 0)
        cur = cm_map.get(iso)
        if cur is None or rev > cur[1]:
            cm_map[iso] = (fn, rev)

    # archive: date -> minute_id (for dates cm.html doesn't carry)
    arch_map = {}
    for mid, d in re.findall(
        r'minutes_view\.php\?minute_id=(\d+)&id=1">(\d{2}-\d{2}-\d{4})</a>', arch
    ):
        iso = dash_iso(d)
        if iso >= FLOOR:
            arch_map.setdefault(iso, mid)

    index = {}
    for iso, (fn, _rev) in cm_map.items():
        index[iso] = (fn, "commission_meetings.php", PDF_DIR + "/" + fn)

    # resolve archive-only dates to their real PDF via the minute_id detail page
    for iso, mid in sorted(arch_map.items()):
        if iso in index:
            continue
        try:
            html = get(PORTAL + "/minutes_view.php?minute_id=%s&id=1" % mid)
        except Exception as e:  # noqa
            index[iso] = (None, "archive:minute_id=%s (fetch failed: %s)" % (mid, e), None)
            continue
        m = re.search(r"(min_\d{8}(?:\(\d\)|_\d)?\.pdf)", html)
        if m:
            index[iso] = (m.group(1), "archive:minute_id=%s" % mid,
                          PDF_DIR + "/" + m.group(1))
        else:
            index[iso] = (None, "archive:minute_id=%s (no pdf link)" % mid, None)
        time.sleep(0.05)
    return index


def main():
    os.makedirs(RAW, exist_ok=True)
    index = build_index()
    print("meeting dates 2015+ (union):", len(index))

    rows, missing = [], []
    for iso in sorted(index):
        fn, src, url = index[iso]
        year = iso[:4]
        if not fn or not url:
            missing.append((iso, src))
            continue
        pdf_path = os.path.join(RAW, fn)
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 800:
            try:
                data = get(url, binary=True)
                if not data.startswith(b"%PDF"):
                    missing.append((iso, "not a PDF at %s" % url))
                    continue
                open(pdf_path, "wb").write(data)
                time.sleep(0.05)
            except Exception as e:  # noqa
                missing.append((iso, "download failed: %s (%s)" % (url, e)))
                continue

        # PDF -> text (layout preserved so the roll-call lines stay intact)
        try:
            txt = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"],
                capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
        except Exception as e:  # noqa
            missing.append((iso, "pdftotext failed: %s" % e))
            continue

        # meeting type from the TITLE block only (real work-session docs print
        # "WORK SESSION OF THE / WEBER COUNTY COMMISSION" up top) — not prose mentions.
        title_block = "\n".join([l for l in txt.split("\n") if l.strip()][:6])
        mtype = "work_session" if re.search(r"\bWORK SESSION\b", title_block) else "regular"
        outdir = os.path.join(MIN, year)
        os.makedirs(outdir, exist_ok=True)
        md_name = "%s_commission.md" % iso
        md_path = os.path.join(outdir, md_name)
        rel_md = os.path.relpath(md_path, COUNTY)
        front = (
            "---\n"
            "entity: weber_county\n"
            "body: Board of Commissioners\n"
            "meeting_type: %s\n"
            "meeting_date: %s\n"
            "source_url: %s\n"
            "source_pdf: %s\n"
            "source_index: %s\n"
            "provenance: county_portal\n"
            "---\n\n" % (mtype, iso, url, "legislative/raw/" + fn, src)
        )
        open(md_path, "w", encoding="utf-8").write(front + txt)
        rows.append({
            "meeting_date": iso, "body": "Board of Commissioners",
            "meeting_type": mtype, "minutes_md": rel_md,
            "source_pdf": "legislative/raw/" + fn, "source_url": url,
            "source_index": src, "n_chars": len(txt), "provenance": "county_portal",
        })
        print(" ", iso, mtype, fn, len(txt), "chars")

    with open(os.path.join(LEG, "minutes_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["meeting_date", "body", "meeting_type",
                                          "minutes_md", "source_pdf", "source_url",
                                          "source_index", "n_chars", "provenance"])
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(LEG, "minutes_unrecovered.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["meeting_date", "note"])
        w.writerows(missing)

    print("\nharvested minutes:", len(rows))
    print("unrecovered/missing:", len(missing))
    for iso, note in missing:
        print("  MISSING", iso, note)


if __name__ == "__main__":
    main()
