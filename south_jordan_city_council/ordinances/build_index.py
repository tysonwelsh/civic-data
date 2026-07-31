#!/usr/bin/env python3
"""Build ordinances/index.csv and ordinances/archive_backcatalog.csv for South Jordan.

Two provenance streams are fused (see CLAUDE.md for the full method):

  1. ONLINE BACK-CATALOG — the city's codified-code host, municipalcodeonline.com,
     exposes a publicly-listable S3 bucket of adopted-ordinance PDFs
     (s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/southjordan/ordinances/
     documents/). Enumerated 2026-07-06 → 213 distinct ordinances, 1997–2026.
     The bucket carries ONLY the city's GENERAL ordinance series (`YYYY-NN`);
     the parallel ZONING/rezone series (`YYYY-NN-Z`) is NOT posted there.
     -> archive_backcatalog.csv (the raw enumeration; source of the independent PDFs).

  2. COUNCIL MOTIONS — meeting_minutes/all_votes.csv cites `Ordinance YYYY-NN[-Z]`
     richly. 117 distinct ordinance numbers are cited (82 general + 35 zoning).

index.csv fuses these over the repo's minutes window (2020+):
  * a cited ordinance whose number ALSO appears in the S3 archive  -> match_confidence=high
    (independent adopted PDF corroborates the number cited in the motion; source_url=S3 PDF).
  * a cited ordinance NOT in the S3 archive (all -Z rezones + general ords not yet posted)
    -> match_confidence=within_source (index derived from the motion itself, NOT independently
    corroborated; source_url = the minutes doc).
  * an archived ordinance in-window whose number is NOT cited in any motion, but whose adopted
    date (read from the signed PDF) falls on a recorded council meeting date
    -> match_confidence=low (date-only; matched_motion_no left blank — no numbered motion).
  * an archived ordinance in-window whose adoption date predates the minutes floor
    (first minutes doc = 2020-08-18) -> match_confidence=none (coverage seam).

Adoption dates for the 12 in-window archived-but-uncited ordinances were read from the
"PASSED AND ADOPTED ... ON THIS __ DAY OF __" clause on the signed PDFs (handwritten day +
month). OCR garbled the handwriting, so they were transcribed by vision (Read tool) —
recorded verbatim in ADOPTED_DATES below. NEVER FABRICATED: every value traces to a signature
page image.

Pre-2020 archived ordinances (161) are out of the minutes window (can never link to a 2020+
vote) and are NOT downloaded; they live in archive_backcatalog.csv with a live source_url
(index-only — public + re-fetchable; a documented exception to raw-retention, per SKILL §3).

Regenerate: this script reads the two /tmp inputs produced during the build if present, else
reads the committed archive_backcatalog.csv. It is idempotent given the same inputs.
"""
import csv, json, re, os, subprocess, urllib.parse, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
S3_BASE = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
RETRIEVED = "2026-07-06"

# Adoption dates read by VISION from the signed-ordinance signature pages (handwritten
# day-of-month clause). Ordinance 2026-15's S3 file is internally inconsistent (page-1 title
# vs. page-2 footer read "2026-12") -> excluded from index.csv, flagged in AVAILABILITY.md.
ADOPTED_DATES = {
    "2020-01": "2020-01-07", "2020-02": "2020-01-07", "2020-07": "2020-05-19",
    "2020-08": "2020-05-05", "2020-11": "2020-08-04", "2021-09": "2021-05-04",
    "2024-01": "2024-01-02", "2024-08": "2024-04-02", "2024-10": "2024-05-21",
    "2024-12": "2024-06-04", "2024-17": "2024-09-03", "2024-24": "2024-11-19",
}
MISLABELED = {"2026-15"}  # S3 filename vs. document body disagree

LU_RX = re.compile(r'(zon|rezone|title\s*1[67]|1[67]\.\d|subdiv|general plan|annex|plat|'
                   r'land use|planned|overlay|setback|density|accessory|floating zone|'
                   r'landscap|water share|exaction)', re.I)


def load_archive():
    """ordinance_no -> {key,size,lastmod,fname,fdate}. Prefer committed backcatalog."""
    bc = os.path.join(HERE, "archive_backcatalog.csv")
    if os.path.exists(bc):
        m = {}
        for r in csv.DictReader(open(bc)):
            m[r["ordinance_no"]] = {"key": r["s3_key"], "size": int(r["size_bytes"] or 0),
                                    "lastmod": r["s3_last_modified"], "fname": r["s3_filename"],
                                    "fdate": r["filename_date"]}
        return m
    return json.load(open("/tmp/sjc_ord_map.json"))


def parse_cites():
    pat = re.compile(r'Ordinance\s+(?:No\.?\s*)?(20\d{2})-(\d{1,3})(-Z)?', re.I)
    votes = list(csv.DictReader(open(os.path.join(CITY, "meeting_minutes/all_votes.csv"))))
    midx = {r["path"]: r["source_url"]
            for r in csv.DictReader(open(os.path.join(CITY, "meeting_minutes/minutes_index.csv")))}
    cites = {}
    for r in votes:
        for mm in pat.finditer(r["motion"] or ""):
            num = f"{mm.group(1)}-{int(mm.group(2)):02d}{'-Z' if mm.group(3) else ''}"
            cites.setdefault(num, []).append(r)
    meeting_dates = {r["date"] for r in votes}
    return cites, midx, meeting_dates


def pick_adopting(rows):
    def passing(r): return "pass" in (r["result"] or "").lower()
    def approve(r):
        t = (r["motion"] or "").lower()
        return ("approv" in t or "adopt" in t or "enact" in t) and not any(
            w in t for w in ("table", "deny", "continu"))
    cand = [r for r in rows if passing(r) and approve(r)] or \
           [r for r in rows if approve(r)] or rows
    return sorted(cand, key=lambda r: (r["date"], r["motion_no"]))[-1]


def fmt_of(num):
    f = os.path.join(HERE, "raw/ordinances_archive", f"{num}.pdf")
    if not os.path.exists(f):
        return None
    out = subprocess.run(["pdftotext", "-layout", f, "-"], capture_output=True, text=True).stdout
    return "text" if len(out.strip()) >= 200 else "scanned"


def clean_title(fname):
    b = re.sub(r'^\d{9,}_', '', fname)
    b = re.sub(r'\.pdf$', '', b, flags=re.I)
    b = re.sub(r'\b(19|20)\d{2}-\d{1,3}(-Z)?\b', '', b)
    b = re.sub(r'^\s*(Ordinance|ORD|ORDINANCE)\s*(No\.?)?\s*', '', b, flags=re.I)
    b = re.sub(r'[-_]', ' ', b)
    b = re.sub(r'\b(FINAL|Signed|w signatures|with signatures)\b', '', b, flags=re.I)
    return re.sub(r'\s+', ' ', b).strip(' -.()')


def ocr_titles():
    t = {}
    for f in glob.glob(os.path.join(HERE, "text/*.ocr.txt")):
        num = os.path.basename(f).replace(".ocr.txt", "")
        m = re.search(r'AN ORDINANCE\s+(.*?)\s*WHEREAS', open(f).read(), re.S)
        if m:
            t[num] = "AN ORDINANCE " + re.sub(r'\s+', ' ', m.group(1)).strip().rstrip('.')
    return t


def main():
    arch = load_archive()
    cites, midx, meeting_dates = parse_cites()
    octit = ocr_titles()

    nums = sorted(set(arch) | set(cites),
                  key=lambda k: (k[:4], int(k[5:].replace('-Z', '')), '-Z' in k))
    # SCHEMA_SPEC §9 ordinances contract header first, city extras after.
    # adoption_date is not derived here (date carries the best-effort adoption date) —
    # DictWriter restval emits it blank, per contract. result = the matched motion's
    # verbatim result string (canonical name for the retired matched_motion_result).
    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no", "match_confidence",
            "series", "stored_locally"]
    rows = []
    for num in nums:
        if num[:4] < "2020":       # pre-window -> back-catalog only
            continue
        if num in MISLABELED:      # unreliable S3 file -> excluded, see AVAILABILITY.md
            continue
        in_arch, cited = num in arch, num in cites
        adopting = pick_adopting(cites[num]) if cited else None
        series = "zoning" if num.endswith("-Z") else "general"

        if cited and in_arch:
            conf = "high"
        elif cited:
            conf = "within_source"
        elif num in ADOPTED_DATES and ADOPTED_DATES[num] in meeting_dates:
            conf = "low"            # date matches a recorded meeting; no numbered motion
        else:
            conf = "none"           # in-window but no motion / pre-minutes-floor adoption

        # adoption date
        if cited:
            date = adopting["date"]
        elif num in ADOPTED_DATES:
            date = ADOPTED_DATES[num]
        elif in_arch and arch[num]["fdate"]:
            date = arch[num]["fdate"]
        else:
            date = ""

        # title: OCR (best) > filename > motion subject
        title = octit.get(num) or (clean_title(arch[num]["fname"]) if in_arch else "")
        if not title and cited:
            title = re.sub(r'^Council Member \w+ (made a motion|motioned) to '
                           r'(approve|adopt|table)\s*', '', adopting["motion"], flags=re.I)[:160].strip()

        if in_arch:
            source_url = S3_BASE + urllib.parse.quote(arch[num]["key"])
            fmt = fmt_of(num) or "scanned"
            stored, path = "yes", f"raw/ordinances_archive/{num}.pdf"
            extr = "pdftotext-layout" if fmt == "text" else "scanned image PDF (OCR/vision on signature page for date; body OCR deferred)"
            retrieved = RETRIEVED
        else:  # within_source: no independent ordinance doc; source is the minutes
            source_url = midx.get(adopting["source"], "") if adopting else ""
            fmt, stored, path, extr, retrieved = "na", "no", "", "motion-citation (derived from minutes; not independently corroborated)", ""

        landuse = "yes" if (series == "zoning" or (title and LU_RX.search(title))
                            or (cited and LU_RX.search(adopting["motion"]))) else "no"

        rows.append({
            "date": date, "ordinance_no": num, "series": series, "title": title,
            "land_use": landuse, "source_url": source_url, "stored_locally": stored,
            "path": path, "retrieved_date": retrieved, "format": fmt, "extraction_method": extr,
            "matched_motion_date": (adopting["date"] if cited else
                                    (date if conf == "low" else "")),
            "matched_motion_no": adopting["motion_no"] if cited else "",
            "result": adopting["result"] if cited else "",
            "match_confidence": conf,
        })

    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    print("index.csv rows:", len(rows))
    print("  match_confidence:", dict(Counter(r["match_confidence"] for r in rows)))
    print("  land_use share: %d/%d = %.1f%%" % (
        sum(r["land_use"] == "yes" for r in rows), len(rows),
        100 * sum(r["land_use"] == "yes" for r in rows) / len(rows)))
    # empty source_url / date guard
    bad = [r["ordinance_no"] for r in rows if not r["date"] or not r["source_url"]]
    print("  rows missing date/source_url:", bad or "none")


if __name__ == "__main__":
    main()
