#!/usr/bin/env python3
"""ec_ord_index.py — build ordinances/index.csv (SCHEMA_SPEC §9 contract) for
Emigration Canyon.

Inputs
  _s3_manifest.csv          the MunicipalCodeOnline S3 objects (all retained in raw/)
  text/<stem>.txt           extracted sidecars (for caption classification / decoy check)
  text/_extraction_log.csv  method + char count per raw
  ../meeting_minutes/all_votes.csv   council motions that cite instrument numbers

Output
  index.csv  — one row per DISTINCT adopted instrument (instrument_type, canonical_no);
               byte/format twins collapse to one row (alternates -> dup_raw).

Motion linkage (independent cross-match; NOT within_source — the instrument PDFs are
published separately from the minutes):
  high    number cited in a recorded council motion (same instrument_type)
  medium  no number match, but same year + subject-term overlap with a motion
  none    unmatched

Adoption date: motion date on a high match (clean born-digital minutes win); else the
instrument-number's encoded year-month (kearns lesson); else the S3 upload date, flagged.

Usage: python3 ec_ord_index.py
"""
import csv
import os
import re
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
RETRIEVED = "2026-07-14"

# Files retained in raw/ but NOT adopted-instrument rows (exhibits / catalog / plans).
EXCLUDE = {
    "1759415224_Ordinance_Log.xlsx",           # the clerk's ordinance-log spreadsheet
    "1583253130_Dominion_Energy_-_Emigration_Canyon_Agreement_-_signed_-_Final.pdf",  # franchise agreement exhibit to Ord 19-05-02
    "1774037031_Salt_Lake_County_Emigration_Canyon_Annex_2026-01-12.pdf",  # HMP plan exhibit to R2026-02
    "1774037100_SLCo_MJHMP_Volume1_2026-01-12.pdf",                        # HMP plan volume exhibit to R2026-02
}

def localname(fn):
    """The on-disk raw filename: same sanitizer as ec_ord_build_batch.py."""
    return re.sub(r"[^0-9A-Za-z._-]+", "_", fn).strip("_")


# Tight land-use / zoning signal set (advisory flag). Deliberately excludes bare
# "residential/commercial/dwelling/building" which fire on boilerplate; requires a
# genuine zoning/subdivision/land-use context term.
LANDUSE_RE = re.compile(
    r"\b(zoning|rezone|zone map|zoning map|subdivision|subdivid\w*|"
    r"land[\s-]?use|general plan|\bplat\b|setback|density|"
    r"accessory dwelling|\badu\b|floodplain|flood damage|"
    r"nonconforming|noncomplying|wildland|\bwui\b|night lighting|"
    r"encroach\w*|title 18|title 19|19\.\d|forestry zone|residential zone|"
    r"commercial zone|building and land use|conditional use)\b", re.I)

DECOY_TOWNS = ["white city", "kearns", "magna", "copperton"]


def norm_no(s):
    """Canonicalize an instrument number to a comparable form.
    City ordinance -> YYYY-O-NN ; city resolution -> RYYYY-NN ;
    YYYY-MM-NN -> YYYY-MM-NN ; YY-MM-NN -> YY-MM-NN (segments zero-padded)."""
    s = s.strip().upper().replace(" ", "")
    m = re.match(r"^R?(20\d\d)-([O0])-(\d{1,2})$", s)  # city ordinance 2025-O-13 / 2025-0-13
    if m:
        return f"{m.group(1)}-O-{int(m.group(3)):02d}"
    m = re.match(r"^R(20\d\d)-(\d{1,2})[A-Z]?$", s)     # city resolution R2026-03A
    if m:
        return f"R{m.group(1)}-{int(m.group(2)):02d}"
    m = re.match(r"^(20\d\d)-(\d{1,2})-(\d{1,2})$", s)  # YYYY-MM-NN
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"^(\d{2})-(\d{1,2})-(\d{1,2})$", s)   # YY-MM-NN
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s


def parse_filename(fn):
    """Return (instrument_type, raw_no) or (None, None) if not parseable from name.
    instrument_type in {ordinance, resolution, ''} ('' = decide from caption)."""
    base = os.path.splitext(fn)[0]
    # strip leading S3 upload-id prefix (10-digit epoch) for readability
    core = re.sub(r"^\d{9,10}_", "", base).replace("_", " ")
    itype = ""
    if re.search(r"\bOrdinance\b", core, re.I) or re.search(r"20\d\d-O-\d", core, re.I) \
            or re.search(r"\d\d-O-\d", core, re.I):
        itype = "ordinance"
    if re.search(r"\bResolution\b", core, re.I) or re.search(r"\bR20\d\d-\d", core):
        # resolution keyword or R-number; if BOTH ord+res keywords, prefer explicit R-num
        if re.search(r"\bR20\d\d-\d", core) or itype == "":
            itype = "resolution"
    # number token
    no = None
    for pat in (r"R20\d\d-\d{1,2}[A-Z]?", r"20\d\d-[O0]-\d{1,2}",
                r"20\d\d-\d{2}-\d{1,2}", r"\b\d{2}-\d{2}-\d{1,2}\b"):
        m = re.search(pat, core)
        if m:
            no = m.group(0)
            break
    return itype, no


def _caption_head(stem):
    p = os.path.join(TXT, stem + ".txt")
    if not os.path.exists(p):
        return ""
    return open(p, errors="replace").read(3000)


def caption_type_and_entity(stem):
    """Peek the text sidecar: return (type_from_caption, is_decoy).
    Picks whichever of ORDINANCE / RESOLUTION appears FIRST as a header word."""
    head = _caption_head(stem)
    if not head:
        return "", False
    low = head.lower()
    io = low.find("ordinance")
    ir = low.find("resolution")
    ctype = ""
    if io >= 0 and (ir < 0 or io < ir):
        ctype = "ordinance"
    elif ir >= 0:
        ctype = "resolution"
    is_decoy = ("emigration" not in low) and any(t in low for t in DECOY_TOWNS)
    return ctype, is_decoy


def caption_number(stem):
    """Extract an instrument number from the sidecar caption (filename had none)."""
    head = _caption_head(stem)
    for pat in (r"R20\d\d-\d{1,2}[A-Z]?", r"20\d\d-[O0]-\d{1,2}",
                r"20\d\d[-\s#]+\d{2}[-\s]+\d{1,2}", r"\b\d{2}-\d{2}-\d{1,2}\b"):
        m = re.search(pat, head)
        if m:
            return re.sub(r"[\s#]+", "-", m.group(0))
    return None


# ---- build the minutes citation index -------------------------------------
def load_citations():
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "meeting_minutes",
                                                  "all_votes.csv"))))
    cites = {}   # (type, canonical_no) -> list of (date, motion_no, result, motion)
    cite_re = re.compile(
        r"(Ordinance|Resolution|Ord\.|Res\.)\s*(?:No\.?\s*)?"
        r"(R?\d{2,4}[-\s]?[O0]?[-\s]?\d{1,2}(?:-\d{1,2})?)", re.I)
    for r in rows:
        text = r.get("motion") or ""
        for m in cite_re.finditer(text):
            kw = m.group(1).lower()
            itype = "ordinance" if kw.startswith("ord") else "resolution"
            raw = m.group(2)
            key = (itype, norm_no(raw))
            cites.setdefault(key, []).append(
                (r["date"], r["motion_no"], r["result"], text))
    return cites, rows


def load_ord_log():
    """Parse the clerk's 'Ordinance Log.xlsx' -> {canonical_no: 'YYYY-MM-DD'} for
    ordinances that were PASSED with a real Date Signed. Authoritative first-party
    day-precision dates (better than the number's encoded month). Ordinances only
    (the log has no resolutions)."""
    import glob
    out = {}
    hits = glob.glob(os.path.join(RAW, "*Ordinance_Log*.xlsx"))
    if not hits:
        return out
    try:
        import openpyxl
    except ImportError:
        return out
    try:
        wb = openpyxl.load_workbook(hits[0], data_only=True)
    except Exception:
        return out
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            if not row or not row[0]:
                continue
            no = str(row[0]).strip()
            if not re.match(r"^R?\d", no) or "ordinance no" in no.lower():
                continue
            passed = str(row[2]).strip().lower() if len(row) > 2 and row[2] else ""
            dsigned = row[3] if len(row) > 3 else None
            if passed.startswith("y") and dsigned and hasattr(dsigned, "year"):
                out[norm_no(no)] = f"{dsigned.year:04d}-{dsigned.month:02d}-{dsigned.day:02d}"
    return out


def ym_from_no(canonical_no):
    """Best-effort adoption month from the instrument number's encoded year-month."""
    m = re.match(r"^(20\d\d)-(\d{2})-\d{2}$", canonical_no)   # YYYY-MM-NN
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    m = re.match(r"^(\d{2})-(\d{2})-\d{2}$", canonical_no)    # YY-MM-NN
    if m:
        return f"20{m.group(1)}-{m.group(2)}-01"
    return ""


def subject_terms(text):
    return set(w for w in re.findall(r"[a-z]{5,}", (text or "").lower())
               if w not in STOP)

STOP = {"ordinance", "resolution", "emigration", "canyon", "metro", "township",
        "council", "approve", "adopt", "amending", "amend", "chapter", "title",
        "section", "motion", "seconded", "meeting", "unanimous", "favor",
        "moved", "member", "members", "salt", "county"}


def main():
    manifest = {r["filename"]: r for r in
                csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv")))}
    extlog = {r["filename"]: r for r in
              csv.DictReader(open(os.path.join(TXT, "_extraction_log.csv")))}
    cites, motion_rows = load_citations()
    ordlog = load_ord_log()

    # group raws into distinct instruments
    groups = {}     # (itype, canonical_no) -> list of dict(fn, manifest, ...)
    decoys, excluded, unparsed = [], [], []
    for fn, mrow in manifest.items():
        lname = localname(fn)          # on-disk raw filename (underscores)
        if lname in EXCLUDE:
            excluded.append(lname)
            continue
        stem = os.path.splitext(lname)[0]
        itype, raw_no = parse_filename(fn)
        ctype, is_decoy = caption_type_and_entity(stem)
        if is_decoy:
            decoys.append(lname)
            continue
        if not itype:
            itype = ctype
        if not raw_no:
            raw_no = caption_number(stem)   # number in the text, not the filename
        if not raw_no:
            unparsed.append(lname)
            continue
        cno = norm_no(raw_no)
        groups.setdefault((itype, cno), []).append(
            dict(fn=fn, lname=lname, mrow=mrow, stem=stem, ctype=ctype))

    rows_out = []
    for (itype, cno), members in sorted(groups.items(), key=lambda kv: kv[0][1]):
        # choose canonical raw: prefer born-digital (text) PDF, then largest
        def score(mem):
            ln = mem["lname"]
            meth = extlog.get(ln, {}).get("method", "")
            chars = int(extlog.get(ln, {}).get("chars", 0) or 0)
            born = meth == "pdftotext_layout"
            ispdf = ln.lower().endswith(".pdf")
            return (ispdf, born, chars, int(mem["mrow"]["size"] or 0))
        members.sort(key=score, reverse=True)
        canon = members[0]
        fn = canon["fn"]
        lname = canon["lname"]
        stem = canon["stem"]
        alts = [m["lname"] for m in members[1:]]
        meth = extlog.get(lname, {}).get("method", "none")
        fmt = "text" if meth == "pdftotext_layout" else \
              ("scanned" if meth.startswith("ocr") else
               ("na" if meth.startswith("native") else "na"))
        # title: from ordinance-log-ish filename core, cleaned
        core = re.sub(r"^\d{9,10}_", "", os.path.splitext(lname)[0]).replace("_", " ")
        core = re.sub(r"\.docx$|\.pdf$", "", core, flags=re.I).strip()
        title = core

        # linkage
        matched = cites.get((itype, cno), [])
        if matched:
            matched.sort(key=lambda t: t[0])
            mdate, mno, mresult, mtext = matched[0]
            conf = "high"
            adoption = mdate
            result = mresult
            note = ""
            if len(matched) > 1:
                note = f"cited in {len(matched)} motions; earliest used"
        else:
            # medium: same-year + subject overlap with a citation of same type
            conf, adoption, result, mdate, mno, note = "none", "", "", "", "", ""
            yr = cno[:4] if cno[:2] == "20" else "20" + cno[:2]
            body_terms = subject_terms(title)
            best = None
            for (ct, ccno), lst in cites.items():
                if ct != itype:
                    continue
                cyr = ccno[:4] if ccno[:2] == "20" else "20" + ccno[:2]
                if cyr != yr:
                    continue
                for (d, mnn, res, tx) in lst:
                    overlap = body_terms & subject_terms(tx)
                    if len(overlap) >= 2:
                        cand = (len(overlap), d, mnn, res, ",".join(sorted(overlap))[:60])
                        if not best or cand[0] > best[0]:
                            best = cand
            log_date = ordlog.get(cno) if itype == "ordinance" else None
            if best:
                conf = "medium"
                _, mdate, mno, result, ov = best
                adoption = log_date or ym_from_no(cno)
                note = f"year+subject overlap: {ov}"
                if log_date:
                    note += "; adoption date from ordinance log (Date Signed)"
                elif not adoption:
                    adoption = manifest[fn]["last_modified"][:10]
                    note += "; date=S3 upload_date (number has no encoded month)"
            if conf == "none":
                if log_date:
                    adoption = log_date
                    note = "date from ordinance log (Date Signed); no motion match"
                else:
                    adoption = ym_from_no(cno)
                    if adoption:
                        note = "date from instrument number (no motion match)"
                    else:
                        adoption = manifest[fn]["last_modified"][:10]
                        note = "date=S3 upload_date (no motion match, number has no month)"

        # land_use: trust a descriptive title; only fall back to the body text when
        # the title is a BARE instrument label (just "Ordinance NN" / a number),
        # which avoids body-boilerplate false positives on budgets/appointments/etc.
        stripped = re.sub(r"(emigration|ordinance|resolution|signed|no\.?|fy\d+|"
                          r"[0-9OoR#_.\-])", " ", title, flags=re.I)
        bare = len(re.findall(r"[A-Za-z]{3,}", stripped)) <= 1
        land = "no"
        if LANDUSE_RE.search(title):
            land = "yes"
        elif bare:
            tp = os.path.join(TXT, stem + ".txt")
            if os.path.exists(tp) and LANDUSE_RE.search(open(tp, errors="replace").read(4000)):
                land = "yes"

        url = BUCKET + _urlkey(manifest[fn]["key"])
        rows_out.append(dict(
            ordinance_no=_display_no(itype, cno, fn),
            adoption_date=adoption,
            date=adoption,
            title=title,
            source_url=url,
            retrieved_date=RETRIEVED,
            format=fmt,
            extraction_method=meth,
            path=f"raw/{lname}",
            land_use=land,
            result=result,
            matched_motion_date=mdate,
            matched_motion_no=mno,
            match_confidence=conf,
            instrument_type=itype,
            canonical_no=cno,
            dup_raw=";".join(alts),
            source_last_modified=manifest[fn]["last_modified"][:10],
            linkage_note=note,
        ))

    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no",
            "match_confidence", "instrument_type", "canonical_no", "dup_raw",
            "source_last_modified", "linkage_note"]
    rows_out.sort(key=lambda r: (r["instrument_type"], r["canonical_no"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows_out)

    from collections import Counter
    print(f"index.csv: {len(rows_out)} instruments")
    print("  by type:", Counter(r["instrument_type"] for r in rows_out))
    print("  by confidence:", Counter(r["match_confidence"] for r in rows_out))
    print("  by format:", Counter(r["format"] for r in rows_out))
    print("  land_use=yes:", sum(1 for r in rows_out if r["land_use"] == "yes"))
    print("  excluded (exhibits/catalog):", excluded)
    print("  decoys (cross-entity):", decoys)
    print("  unparsed (no number in name):", unparsed)


def _urlkey(key):
    import urllib.parse
    return urllib.parse.quote(key)


def _display_no(itype, cno, fn):
    """Human-facing instrument number for the row (host-authoritative)."""
    return cno


if __name__ == "__main__":
    main()
