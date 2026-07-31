#!/usr/bin/env python3
"""Fetch WFRC Council minutes and build the markdown corpus + index.

WFRC is a REGIONAL (MPO) entity, not a Legistar shop. Its Council meets ~5x/year and
publishes born-digital minutes PDFs (Google-Docs -> Skia) at stable paths under
/Committees/Council/<year>/. The live host wfrc.utah.gov (Dec-2025 WordPress rebuild)
still serves the full historical file tree back to 2016; the exact paths were discovered
via the old wfrc.org Wayback CDX index. WebFetch mis-renders these PDFs, so we extract
locally with `pdftotext` (one 2016 file is .docx -> textutil).

Reads legislative/meetings_source.tsv (curated date/body/doc_status/url), downloads each
to legislative/raw/, extracts text, and writes:
    legislative/minutes/<year>/<date>_council.md   (provenance front-matter + text)
    legislative/minutes_index.csv                  (has md_path column)

DERIVED + idempotent (skips already-downloaded raw files). Born-digital text (no OCR).
"""
import csv, os, re, subprocess, urllib.request, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # wfrc_mpo/
LEG = os.path.join(ROOT, "legislative")
SRC = os.path.join(LEG, "meetings_source.tsv")
RAW = os.path.join(LEG, "raw")


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1500:
        return True
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "civic-data/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
                f.write(r.read())
            return os.path.getsize(dest) > 1500
        except Exception as e:
            if i == 3:
                print("  ! download failed:", url, repr(e))
                return False
            time.sleep(3 * (i + 1))
    return False


# Google-Docs -> Skia PDF exports (2024+) wrap EVERY word in Unicode directional /
# zero-width formatting characters (U+202A..U+202E, U+2066..U+2069, U+200B..U+200F,
# U+00AD, U+FEFF). extract_motions.py strips them at parse time, but the MARKDOWN kept
# them — so 7 files sat in fts_minutes with 14-19% of their characters unsearchable and
# every word visually fenced. Strip at write time; the raw PDFs remain untouched.
# (audit F10, 2026-07-26)
_FMT_JUNK = re.compile("[​-‏‪-‮⁦-⁩­﻿]")

def strip_format_marks(text):
    """Replace Unicode directional/zero-width marks with a SPACE, then collapse runs.

    Must be a space, never "": in these exports the marks ARE the word separators — the
    PDF often carries no real space between words, so deleting them glues the line into
    "MayorDustinGettelmadeamotiontoapprove…" and the motion anchors stop matching
    (measured: 323 motions -> 283, two meetings lost entirely). This mirrors what
    extract_motions.py has always done at parse time.
    """
    if not text:
        return text
    text = _FMT_JUNK.sub(" ", text)
    return re.sub(r"[ \t]{2,}", " ", text)


def to_text(path):
    """pdftotext for .pdf, textutil for .docx. Returns extracted text or ''."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            out = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"],
                                 capture_output=True, timeout=120)
            return strip_format_marks(out.stdout.decode("utf-8", "replace"))
        except Exception as e:
            print("  ! pdftotext failed:", path, repr(e)); return ""
    if ext == ".docx":
        try:
            out = subprocess.run(["textutil", "-convert", "txt", "-stdout", path],
                                 capture_output=True, timeout=120)
            return out.stdout.decode("utf-8", "replace")
        except Exception as e:
            print("  ! textutil failed:", path, repr(e)); return ""
    return ""


def main():
    os.makedirs(RAW, exist_ok=True)
    rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"))
    idx = []
    got = missing = 0
    for r in rows:
        date, body, status, url = r["date"], r["body"], r["doc_status"], r["url"]
        year = date[:4]
        ext = ".docx" if url.lower().split("?")[0].endswith(".docx") else ".pdf"
        raw = os.path.join(RAW, date + ext)
        md_dir = os.path.join(LEG, "minutes", year)
        os.makedirs(md_dir, exist_ok=True)
        md = os.path.join(md_dir, "%s_council.md" % date)
        if not fetch(url, raw):
            missing += 1
            idx.append([date, body, "", url, status, "download failed"])
            continue
        text = to_text(raw)
        if len(text.strip()) < 200:
            missing += 1
            idx.append([date, body, "", url, status, "text extraction empty/short"])
            print("  ! short extraction:", date, len(text.strip()))
            continue
        extraction = "pdftotext (born-digital)" if ext == ".pdf" else "textutil (.docx)"
        header = (
            "---\n"
            "jurisdiction: Wasatch Front Regional Council\n"
            "entity: wfrc_mpo\n"
            "level: regional\n"
            "body: %s\n"
            "date: %s\n"
            "doc_status: %s\n"
            "source_url: %s\n"
            "source: WFRC website (wfrc.utah.gov /Committees/Council)\n"
            "extraction: %s\n"
            "---\n\n" % (body, date, status, url, extraction))
        with open(md, "w", encoding="utf-8") as f:
            f.write(header + text)
        idx.append([date, body, os.path.relpath(md, ROOT), url, status, ""])
        got += 1

    idx.sort(key=lambda x: x[0])
    with open(os.path.join(LEG, "minutes_index.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["date", "body", "md_path", "source_url", "doc_status", "note"])
        wr.writerows(idx)
    print("minutes: %d converted, %d missing/short. index -> legislative/minutes_index.csv"
          % (got, missing))


if __name__ == "__main__":
    main()
