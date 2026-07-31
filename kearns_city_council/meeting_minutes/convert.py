#!/usr/bin/env python3
"""convert.py — Kearns minutes PDF -> markdown (PURE, deterministic; resumable).

Reads a manifest CSV (meeting_date,file_id,filename,notice_date,meeting_type,url)
and for each retained raw/ PDF:
  * extracts text with `pdftotext -layout`; if the narrative is missing (scanned
    minutes / image-only) it OCRs with pdftoppm+tesseract and marks format=ocr;
  * writes minutes/<year>/<week-monday>/<date>_<slug>.md with a provenance header;
  * (re)builds minutes_index.csv (8-col standard) + logs scanned files.

Source = Utah PMN (utah.gov/pmn). Body is a CLI arg (Council / PlanningCommission).
Run:  python3 convert.py            # uses the sibling manifest + raw/
"""
import os, re, csv, sys, subprocess, tempfile, glob
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
BODY = "PlanningCommission" if "planning_commission" in ROOT else "Council"
RAW = os.path.join(ROOT, "raw")
MIN = os.path.join(ROOT, "minutes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
MANIFEST = os.path.join(ROOT, "manifest.csv")
PREFIX = "pc_minutes_" if BODY == "PlanningCommission" else "minutes_"

NARR = re.compile(r"motion|moved|second|\bvote\b|commissioner|council member|present",
                  re.I)

def extract_text(pdf):
    try:
        return subprocess.run(["pdftotext", "-layout", pdf, "-"],
                              capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return ""

def docx_text(path):
    """Born-digital .docx minutes (2017-era back-catalog) -> plain text."""
    try:
        return subprocess.run(["textutil", "-convert", "txt", "-stdout", path],
                              capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return ""

def portfolio_minutes_text(pdf):
    """If pdf is a PDF Portfolio, extract the embedded *Minutes* file (not the
    *Attachments* file) and return its text; else None."""
    try:
        lst = subprocess.run(["pdfdetach", "-list", pdf], capture_output=True,
                             text=True, timeout=60).stdout
    except Exception:
        return None
    m = re.match(r"\s*(\d+)\s+embedded", lst)
    if not m or int(m.group(1)) == 0:
        return None
    names = re.findall(r"^\s*\d+:\s*(.+)$", lst, re.M)
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdfdetach", "-saveall", "-o", td, pdf],
                       capture_output=True, timeout=120)
        cand = sorted(glob.glob(os.path.join(td, "*")),
                      key=lambda p: ("minute" in os.path.basename(p).lower()
                                     and "attach" not in os.path.basename(p).lower()),
                      reverse=True)
        for p in cand:
            if "minute" in os.path.basename(p).lower() and \
               "attach" not in os.path.basename(p).lower():
                return extract_text(p)
    return None

def ocr(pdf):
    out = []
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "p")
        subprocess.run(["pdftoppm", "-r", "300", "-png", pdf, base],
                       capture_output=True, timeout=1200)
        for img in sorted(glob.glob(base + "*.png")):
            r = subprocess.run(["tesseract", img, "-", "--psm", "6"],
                               capture_output=True, text=True, timeout=300)
            out.append(r.stdout)
    return "\n".join(out)

def week_monday(d):
    return (d - timedelta(days=d.weekday())).isoformat()

def title_for(mtype):
    if BODY == "PlanningCommission":
        return "Planning Commission Meeting"
    return {"Regular": "City Council Meeting",
            "Special": "City Council Special Meeting",
            "WorkSession": "City Council Work Session",
            "BoardOfCanvassers": "Board of Canvassers Meeting",
            "CRA": "Community Reinvestment Agency Meeting"}.get(mtype,
                                                                 "City Council Meeting")

def slug_for(mtype):
    if BODY == "PlanningCommission":
        return "planning-commission-meeting"
    return {"Regular": "city-council-meeting",
            "Special": "city-council-special-meeting",
            "WorkSession": "city-council-work-session",
            "BoardOfCanvassers": "board-of-canvassers-meeting",
            "CRA": "cra-meeting"}.get(mtype, "city-council-meeting")

def date_in_body(text, d):
    months = ["January","February","March","April","May","June","July","August",
              "September","October","November","December"]
    t = text.lower()
    mo = months[d.month-1].lower()
    variants = [d.strftime("%m-%d-%Y"), d.strftime("%m/%d/%Y"), d.strftime("%-m/%-d/%Y"),
                f"{mo} {d.day}, {d.year}", f"{mo} {d.day} {d.year}", f"{mo} {d.day}",
                d.strftime("%Y-%m-%d")]
    return any(v.lower() in t for v in variants)

def main():
    rows = list(csv.DictReader(open(MANIFEST)))
    os.makedirs(MIN, exist_ok=True)
    index = []
    scanned = []
    for r in rows:
        md = r["meeting_date"]
        d = date.fromisoformat(md)
        mtype = r.get("meeting_type", "Regular")
        # raw file: stem defaults to the meeting date; the PMN back-catalog uses
        # per-meeting stems (date + type suffix for same-date meetings) and may be
        # .pdf OR .docx (2017-era born-digital minutes).
        stem = r.get("raw_stem") or md
        pdf = None; raw_ext = None
        for ext in ("pdf", "docx"):
            cand = os.path.join(RAW, f"{PREFIX}{stem}.{ext}")
            if os.path.exists(cand):
                pdf = cand; raw_ext = ext; break
        if pdf is None:
            print("MISSING RAW", os.path.join(RAW, f"{PREFIX}{stem}.*"),
                  file=sys.stderr); continue
        slug = slug_for(mtype)
        wk = week_monday(d)
        rel = f"minutes/{d.year}/{wk}/{md}_{slug}.md"
        dest = os.path.join(ROOT, rel)

        # resumable: reuse an already-converted md body (avoids costly re-OCR)
        if os.path.exists(dest) and "--force" not in sys.argv:
            prev = open(dest, encoding="utf-8").read()
            fm = re.search(r"\*\*Format:\*\*\s*(\w+)", prev)
            fmt = fm.group(1) if fm else "text"
            parts = prev.split("\n\n---\n\n", 2)
            text = parts[2] if len(parts) > 2 else prev
            if fmt == "ocr":
                scanned.append(md)
        elif raw_ext == "docx":
            fmt = "text"
            text = docx_text(pdf)    # born-digital .docx minutes (2017-era)
        else:
            fmt = "text"
            pf = portfolio_minutes_text(pdf)
            if pf is not None:
                text = pf            # born-digital minutes embedded in a portfolio
            else:
                text = extract_text(pdf)
                narrative = (("members present" in text.lower() and date_in_body(text, d))
                             or ("commissioner" in text.lower() and "motion" in text.lower()
                                 and date_in_body(text, d)))
                # scanned minutes (narrative is an image; any text is attachments only)
                if not narrative or len(re.sub(r"\s", "", text)) < 1500:
                    octext = ocr(pdf)
                    if len(re.sub(r"\s", "", octext)) > 400:
                        text = octext
                        fmt = "ocr"
                        scanned.append(md)
        ibm = "YES" if date_in_body(text, d) else "NO"
        title = title_for(mtype)
        src_url = r["url"]
        # body: the CRA convenes as its own PMN body (9273) with standalone minutes;
        # everything else in this dataset is the Council family (dir-inferred).
        body = "CRA" if mtype == "CRA" else BODY
        # provenance: 'pmn_minutes' for docs promoted from ../pmn_backfill/ (the
        # ogden/vineyard/orem/south_jordan/herriman pattern); blank = audited 'minutes'.
        prov = (r.get("provenance") or "").strip()
        prov_line = f"**Provenance:** {prov}\n" if prov else ""
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        header = (f"# {title}\n> Source: {src_url}\n> Meeting date: {md}\n"
                  f"> Format: {fmt}\n\n---\n\n"
                  f"**Body:** {body}\n**Date:** {md}\n**Source:** pmn\n"
                  f"**Source URL:** {src_url}\n**Format:** {fmt}\n"
                  f"**In-body date match:** {ibm}\n{prov_line}\n---\n\n")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(header + text)
        index.append(dict(date=md, year=d.year, title=title, slug=slug, path=rel,
                          source="pmn", source_url=src_url, format=fmt))
        print(f"{md} {fmt:4} ibm={ibm} {os.path.basename(pdf)}")

    index.sort(key=lambda x: (x["date"], x["slug"]))
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","year","title","slug","path","source",
                                          "source_url","format"])
        w.writeheader(); w.writerows(index)
    print(f"\n{len(index)} indexed; scanned/ocr: {len(scanned)} {scanned}")

if __name__ == "__main__":
    main()
