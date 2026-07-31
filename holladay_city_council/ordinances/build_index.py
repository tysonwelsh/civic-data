#!/usr/bin/env python3
"""Build Holladay ordinances/index.csv (expand-city-sources Source 3).

Holladay's codified code is on American Legal (bot-gated, current-consolidated
text only -> NOT mirrored). The Recorder's "Adopted Ordinances" web page is
current-year-only. So the number->date->subject->motion backbone is DERIVED
from the council/RDA/LBA motions in ../meeting_minutes/all_votes.csv (read-only),
and UPGRADED where an independent Recorder-certified adopted-ordinance PDF exists
(21 PDFs for 2025-2026, pulled from the live Revize Document Center).

Linkage confidence:
  high         - an independent adopted-ordinance PDF exists AND a council motion
                 cites the same number (date agrees / no conflict).
  medium       - independent PDF + subject agreement but a number/date wrinkle
                 (e.g. the 2025-02 posting certificate misprints "2025-03").
  within_source- witnessed ONLY by the citing motion (no independent doc);
                 high BY CONSTRUCTION, NOT corroborated. path blank, format=na.
  none         - independent PDF with no extracted council motion.

No network. Idempotent: run holladay_ord_ocr.py first for the text/ sidecars.
"""
import csv
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOTES = HERE.parent / "meeting_minutes" / "all_votes.csv"
MINDEX = HERE.parent / "meeting_minutes" / "minutes_index.csv"
EXTRACT_LOG = HERE / "text" / "_extraction_log.csv"
RETRIEVED = "2026-07-13"
DC_BASE = "https://holladayut.gov/Document Center/"

# --- The 21 independent Recorder-certified adopted-ordinance PDFs -------------
# number -> (raw filename, page-label subject, land_use, note)
# Numbers verified against each PDF's own "ORDINANCE NO. YYYY-NN" header.
PDFS = {
    "2026-01": ("2026-01__2026.01_Historic_Designation.pdf",
                "Historic designation (4659 S Highland Dr)", "yes", ""),
    "2026-02": ("2026-02__2026.02_Budget_Amends.March.pdf",
                "Budget amendments FY 2025-26 (March)", "no", ""),
    "2026-03": ("2026-03__2026.03_Fireworks.pdf",
                "Fireworks restrictions", "no", ""),
    "2026-04": ("2026-04__Ord_2026-04.pdf",
                "Right-of-way vacation", "yes", ""),
    "2026-05": ("2026-05__Ord_2026-05.pdf",
                "Street vacation at 1720 E Bunkerhill Rd", "yes", ""),
    "2026-06": ("2026-06__Ord_2026-06.pdf",
                "Chapter 3.32 Community Clean Energy", "no", ""),
    "2025-02": ("2025-02__Ordinance_02.25.pdf",
                "Amending Title 17 stormwater regulations", "yes",
                "posting certificate in this PDF misprints the number as "
                "'2025-03'; the ordinance header reads ORDINANCE NO. 2025-02 "
                "(stormwater) - city clerical error, preserved verbatim"),
    "2025-03": ("2025-03__Ordinance_-_03.25.pdf",
                "Home-based micro-schools (Title 13)", "yes", ""),
    "2025-04": ("2025-04__Ordinance_-_04.25.pdf",
                "Budget amendments", "no", ""),
    "2025-05": ("2025-05__Ordinance_-_05.25.pdf",
                "Repeals Titles 10 & 11 and adopts new Titles 10 & 11", "no", ""),
    "2025-06": ("unk__06-_FIreworks.pdf",
                "Firework restrictions", "no", ""),
    "2025-08": ("unk__budget_amends.June.adopted.pdf",
                "2024-25 budget amendments", "no", ""),
    "2025-09": ("unk__Certified_Tax_rate.adopted.pdf",
                "Certified tax rate for 2025-26", "no", ""),
    "2025-10": ("unk__compensation.adopted.pdf",
                "Compensation schedule", "no", ""),
    "2025-11": ("unk__2025-26_Final_Budgets.adopted.pdf",
                "Adopts the 2025-26 fiscal year budgets", "no", ""),
    "2025-14": ("2025-14__Ordinance_-_14.25.pdf",
                "Historic designation list", "yes", ""),
    "2025-15": ("unk__13.84_Outdoor_Lighting_CLEAN_VERSION.pdf",
                "Outdoor lighting standards (13.84)", "yes",
                "posted as the clean codified 13.84 text; the certified "
                "ordinance number is not printed in the document (assigned "
                "2025-15 from the Recorder page label)"),
    "2025-16": ("2025-16__Ordinance_-_16.25.pdf",
                "Vacating a portion of right-of-way", "yes", ""),
    "2025-20": ("2025-20__Ordinance_-_20.25.pdf",
                "Title 3 (revenue & finance) amendments", "no", ""),
    "2025-21": ("2025-21__Ordinance_-_21.25.pdf",
                "2025-26 budget amendments", "no", ""),
    "2025-22": ("2025-22__Ordinance_-_22.25.pdf",
                "Wildland Urban Interface overlay", "yes", ""),
}

# Adoption dates read from the "PASSED AND APPROVED this Nth day of ..." clause
# of PDFs that have no matching council motion (2026 items post-date available
# minutes; 2025-06 motion did not cite the number). Provenance = pdf-clause.
PDF_ADOPT_DATE = {
    "2025-06": "2025-05-01",
    "2026-03": "2026-04-23",
    "2026-04": "2026-05-21",
    "2026-05": "2026-05-21",
    "2026-06": "2026-05-21",
}

LANDUSE_RE = re.compile(
    r"zon|rezone|land use|subdivision|\bplat\b|general plan|overlay|title 13|"
    r"setback|density|annex|vacat|right.of.way|\brow\b|histor|design review|"
    r"conditional use|development agreement|\bmda\b|\bpud\b|accessory dwelling|"
    r"\badu\b|outdoor lighting|stormwater|wildland|wui|zoning|parcel", re.I)


def norm(num):
    y, n = num.split("-")
    return f"{y}-{int(n):02d}"


def load_minutes_urls():
    """embedded PMN file id -> minutes source_url."""
    m = {}
    for r in csv.DictReader(open(MINDEX)):
        fid = re.search(r"/files/(\d+)\.pdf", r.get("source_url", ""))
        if fid:
            m[fid.group(1)] = r["source_url"]
    return m


def load_motion_citations():
    """ordinance_no -> list of adoption-candidate motion dicts."""
    rows = list(csv.DictReader(open(VOTES)))
    motions = {}
    for r in rows:
        k = (r["date"], r["body"], r["motion_no"])
        motions.setdefault(k, r)
    cites = {}
    for r in motions.values():
        blob = f"{r['motion']} {r['result']}"
        found = set(re.findall(
            r"Ordinance[ \-]?(?:No\.?\s*)?(\d{4}-\d{1,2})", blob, re.I))
        for raw in found:
            cites.setdefault(norm(raw), []).append(r)
    return cites


def pick_adoption(cands):
    """Prefer a motion whose result says the ordinance was adopted; latest date."""
    adopts = [c for c in cands
              if re.search(r"adopt|approv|pass", c["result"], re.I)]
    pool = adopts or cands
    return sorted(pool, key=lambda c: (c["date"], c["motion_no"]))[-1]


def fileid_from_source(src):
    m = re.search(r"_(\d+)\.md$", src)
    return m.group(1) if m else ""


def main():
    methods = {r["stem"]: r["extraction_method"]
               for r in csv.DictReader(open(EXTRACT_LOG))}
    min_urls = load_minutes_urls()
    cites = load_motion_citations()

    all_nums = sorted(set(cites) | set(PDFS),
                      key=lambda x: (int(x[:4]), int(x[5:])))
    out = []
    for num in all_nums:
        has_pdf = num in PDFS
        cands = cites.get(num, [])
        motion = pick_adoption(cands) if cands else None

        row = dict.fromkeys([
            "ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path",
            "land_use", "result", "matched_motion_date", "matched_motion_no",
            "match_confidence", "subject", "subject_source", "minutes_source",
            "linkage_note"], "")
        row["ordinance_no"] = num

        if has_pdf:
            fname, subject, landuse, note = PDFS[num]
            stem = fname[:-4]
            fmt = "text" if methods.get(stem) == "pdftotext" else "scanned"
            row.update(
                source_url=DC_BASE + _dc_path(fname),
                retrieved_date=RETRIEVED,
                format=fmt,
                extraction_method=methods.get(stem, "tesseract-ocr"),
                path=f"raw/docs/{fname}",
                title=subject, subject=subject, subject_source="recorder-pdf",
                land_use=landuse, linkage_note=note)
        else:
            row["subject_source"] = "motion"

        if motion:
            row["matched_motion_date"] = motion["date"]
            row["matched_motion_no"] = motion["motion_no"]
            row["result"] = motion["result"]
            row["adoption_date"] = motion["date"]
            row["date"] = motion["date"]
            row["minutes_source"] = min_urls.get(
                fileid_from_source(motion["source"]), "")
            if not has_pdf:
                row["title"] = _clean_motion_title(motion["motion"])
                row["land_use"] = "yes" if LANDUSE_RE.search(
                    f"{motion['motion']} {motion['title']}") else "no"
                row["source_url"] = row["minutes_source"]
                row["format"] = "na"
                row["extraction_method"] = (
                    "minutes-citation (derived from "
                    "../meeting_minutes/all_votes.csv; no independent "
                    "ordinance document)")

        # confidence
        if has_pdf and motion:
            fname, subject, landuse, note = PDFS[num]
            row["match_confidence"] = "medium" if note else "high"
        elif has_pdf and not motion:
            row["match_confidence"] = "none"
            if num in PDF_ADOPT_DATE:
                row["adoption_date"] = PDF_ADOPT_DATE[num]
                row["date"] = PDF_ADOPT_DATE[num]
                row["subject_source"] = "recorder-pdf"
                nt = ("adoption date from the PDF 'PASSED AND APPROVED' clause; "
                      "no matching council motion in "
                      "../meeting_minutes/all_votes.csv (item post-dates the "
                      "available minutes or the motion did not cite the number)")
                row["linkage_note"] = (row["linkage_note"] + "; " + nt
                                       if row["linkage_note"] else nt)
        else:
            row["match_confidence"] = "within_source"
            if not row["adoption_date"] and motion is None:
                pass
        out.append(row)

    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path",
            "land_use", "result", "matched_motion_date", "matched_motion_no",
            "match_confidence", "subject", "subject_source", "minutes_source",
            "linkage_note"]
    with open(HERE / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    c = Counter(r["match_confidence"] for r in out)
    lu = Counter(r["land_use"] for r in out)
    print(f"{len(out)} ordinances written to index.csv")
    print("confidence:", dict(c))
    print("land_use:", dict(lu))
    print("with independent PDF:", sum(1 for r in out if r["path"]))


def _dc_path(fname):
    if fname.startswith("2026-01"):
        return "Departments/City Recorder/2026 Ord Adopt/2026.01 Historic Designation.pdf"
    return "Ordinances/" + _orig_dc_name(fname)


ORIG = {
    "2026-02__2026.02_Budget_Amends.March.pdf": "2026.02 Budget Amends.March.pdf",
    "2026-03__2026.03_Fireworks.pdf": "2026.03 Fireworks.pdf",
    "2026-04__Ord_2026-04.pdf": "Ord 2026-04.pdf",
    "2026-05__Ord_2026-05.pdf": "Ord 2026-05.pdf",
    "2026-06__Ord_2026-06.pdf": "Ord 2026-06.pdf",
    "2025-02__Ordinance_02.25.pdf": "Ordinance 02.25.pdf",
    "2025-03__Ordinance_-_03.25.pdf": "Ordinance - 03.25.pdf",
    "2025-04__Ordinance_-_04.25.pdf": "Ordinance - 04.25.pdf",
    "2025-05__Ordinance_-_05.25.pdf": "Ordinance - 05.25.pdf",
    "unk__06-_FIreworks.pdf": "06- FIreworks.pdf",
    "unk__budget_amends.June.adopted.pdf": "budget amends.June.adopted.pdf",
    "unk__Certified_Tax_rate.adopted.pdf": "Certified Tax rate.adopted.pdf",
    "unk__compensation.adopted.pdf": "compensation.adopted.pdf",
    "unk__2025-26_Final_Budgets.adopted.pdf": "2025-26 Final Budgets.adopted.pdf",
    "2025-14__Ordinance_-_14.25.pdf": "Ordinance - 14.25.pdf",
    "unk__13.84_Outdoor_Lighting_CLEAN_VERSION.pdf": "13.84 Outdoor Lighting CLEAN VERSION.pdf",
    "2025-16__Ordinance_-_16.25.pdf": "Ordinance - 16.25.pdf",
    "2025-20__Ordinance_-_20.25.pdf": "Ordinance - 20.25.pdf",
    "2025-21__Ordinance_-_21.25.pdf": "Ordinance - 21.25.pdf",
    "2025-22__Ordinance_-_22.25.pdf": "Ordinance - 22.25.pdf",
}


def _orig_dc_name(fname):
    return ORIG.get(fname, fname)


def _clean_motion_title(motion):
    t = re.sub(r"\s+", " ", motion).strip()
    return t[:180]


if __name__ == "__main__":
    main()
