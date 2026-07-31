#!/usr/bin/env python3
"""wc_ord_index.py — build ordinances/index.csv (SCHEMA_SPEC §9 contract) for
White City adopted ordinances + resolutions harvested from MunicipalCodeOnline.

Primary metadata per instrument comes from the document's OWN header
(`RESOLUTION NO.: 19-09-02  DATE: SEPTEMBER 23, 2019` + the caption), parsed from
the text sidecar. Linkage to meeting_minutes/all_votes.csv:
  high    = instrument number cited in a recorded motion (date+number)
  medium  = date(year-month from number)+subject agreement, number not matched
  none    = unmatched
(within_source is NOT used — every row is backed by an independently-published PDF,
so matches are genuine cross-matches, not motion-derived.)

Byte-identical S3 re-uploads (sha256) collapse to ONE row; the alternate raw stays
on disk and is named in the `dup_raw` extra column.

Usage: python3 wc_ord_index.py
"""
import csv
import json
import os
import re
import collections
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
RETRIEVED = "2026-07-13"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

NUMRE = re.compile(r'(?<!\d)(\d{2,4})\s*-\s*(O|\d{1,2})\s*-\s*(\d{1,3})(?!\d)', re.I)

# genuine cross-entity decoys sitting inside White City's S3 bucket (authored by
# another entity per the caption) — retained as raw, EXCLUDED from the index.
EXCLUDE_FILES = {"1647891849_Ordinance_2021-10-01.pdf"}  # Copperton ADU (HB82) ord
# land-use / zoning keyword flag (coarse, advisory). Word-boundary matched to avoid
# substring false positives ("sign" in "design/signed", "adu" in unrelated words).
LAND = [r"zoning", r"subdivision", r"rezone", r"land[ -]use", r"general plan",
        r"\bplat\b", r"setback", r"density", r"\bannex\w*", r"title 18", r"title 19",
        r"19\.46", r"\bwui\b", r"wildland", r"accessory dwelling", r"\badu\b",
        r"floodplain", r"\bzone\b"]
LANDRE = re.compile("|".join(LAND), re.I)


def canon(y, mid, seq):
    y = int(y)
    if y < 100:
        y += 2000
    mid = mid.upper()
    return f"{y}-{mid}-{int(seq):02d}"


def parse_num(s):
    m = NUMRE.search(s)
    if not m:
        return None
    return canon(m.group(1), m.group(2), m.group(3)), m


# ---------- citation index from motions ----------
def build_citations():
    cites = collections.defaultdict(list)
    rows = list(csv.DictReader(open(VOTES)))
    seen = set()
    for r in rows:
        k = (r["date"], r["motion_no"])
        if k in seen:
            continue
        seen.add(k)
        text = r["motion"] or ""
        found = []
        # number tokens in motion text (with nearby type hint)
        for m in NUMRE.finditer(text):
            c = canon(m.group(1), m.group(2), m.group(3))
            pre = text[max(0, m.start() - 18):m.start()].lower()
            hint = ("ordinance" if "ordinance" in pre else
                    "resolution" if "resolution" in pre else "")
            found.append((c, hint))
        # township-era motion_no often IS the instrument number
        pm = parse_num(r["motion_no"] or "")
        if pm:
            mt = (r["motion_type"] or "").lower()
            hint = ("ordinance" if "ordinance" in mt else
                    "resolution" if "resolution" in mt else "")
            found.append((pm[0], hint))
        for c, hint in found:
            cites[c].append({"date": r["date"], "motion_no": r["motion_no"],
                             "motion_type": r["motion_type"], "result": r["result"],
                             "text": text, "hint": hint})
    return cites


# ---------- per-document header parse ----------
def parse_header(text):
    """Parse the dated instrument header. Date is taken ONLY from the header region
    (near the NO. line / an ADOPTED clause) to avoid grabbing body dates such as
    term-expiration dates."""
    num = None
    date = None
    title = ""
    if text:
        head = text[:1500]
        m = re.search(r'(ordinance|resolution)\s*(?:no\.?|number)?\s*[:\.]?\s*'
                      r'(\d{2,4}\s*-\s*(?:O|\d{1,2})\s*-\s*\d{1,3})', head, re.I)
        if m:
            pn = parse_num(m.group(2))
            if pn:
                num = pn[0]
        # DATE: field within the header line region (first ~250 chars)
        region = head[:250]
        dm = re.search(r'date\s*[:\.]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})', region, re.I)
        if dm:
            date = norm_date(dm.group(1))
        if not date:
            dm = re.search(r'date\s*[:\.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', region, re.I)
            if dm:
                date = norm_date(dm.group(1))
        # else an explicit adoption clause anywhere in the head
        if not date:
            dm = re.search(r'(?:ADOPTED|PASSED|ENACTED)[^.]{0,80}?'
                           r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', head, re.I)
            if dm:
                date = norm_date(dm.group(1))
        # else a STANDALONE date in the top header region (older ordinances print the
        # adoption date as a header line, e.g. "JANUARY 5, 2017", with no DATE label).
        # Guard against term/effective dates ("...TERM ENDING JUNE 30, 2027").
        if not date:
            for dm in re.finditer(r'([A-Za-z]+\s+\d{1,2},?\s*\d{4})', region):
                pre = region[max(0, dm.start() - 22):dm.start()].lower()
                if any(w in pre for w in ("ending", "term", "expir", "through", "until", "effective")):
                    continue
                date = norm_date(dm.group(1))
                if date:
                    break
        cm = re.search(r'\b(A[Nn]?\s+(?:RESOLUTION|ORDINANCE)\b.*?)(?:\n\s*\n|RECITALS|WHEREAS|BE IT)',
                       head, re.S | re.I)
        if cm:
            title = re.sub(r'\s+', ' ', cm.group(1)).strip()[:300]
    return num, date, title


def norm_date(s):
    s = s.strip().rstrip(".")
    m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})', s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', s)
    if m:
        y = int(m.group(3))
        y = y + 2000 if y < 100 else y
        return f"{y:04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def is_land_use(title, num, fn):
    blob = title + " " + num + " " + fn.replace("_", " ")
    return "yes" if LANDRE.search(blob) else "no"


def main():
    # source_url + last_modified from manifest
    man = {}
    for r in csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv"))):
        san = r["filename"].replace(" ", "_")
        man[san] = (BUCKET + urllib.parse.quote(r["key"]), r["last_modified"][:10])

    # sha256 -> keep first, map dups
    sha_first = {}
    dup_of = {}
    for line in open(os.path.join(RAW, "_fetch_log.jsonl")):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        fn = os.path.basename(d["saved_as"])
        s = d["sha256"]
        if s in sha_first:
            dup_of[fn] = sha_first[s]
        else:
            sha_first[s] = fn

    cites = build_citations()

    raws = sorted(f for f in os.listdir(RAW) if f.lower().endswith(".pdf"))
    out = []
    excluded = []
    for fn in raws:
        if fn in dup_of:
            continue  # byte-identical re-upload; primary row carries dup_raw
        if fn in EXCLUDE_FILES:
            excluded.append(fn)
            continue  # cross-entity decoy (raw retained, not indexed)
        stem = os.path.splitext(fn)[0]
        tf = os.path.join(TXT, stem + ".txt")
        text = open(tf).read() if os.path.exists(tf) else ""
        # instrument type
        lo = fn.lower()
        itype = ("ordinance" if "-o-" in lo or "ordinance" in lo else
                 "resolution" if "resolution" in lo else
                 ("ordinance" if "/ordinances/" in man.get(fn, ("", ""))[0] else
                  "resolution"))
        hnum, hdate, htitle = parse_header(text)
        # number: the MunicipalCodeOnline FILENAME is the authoritative number;
        # header parse (OCR-noisy) is only a fallback.
        desc = re.sub(r'^\d+_', '', stem).replace("_", " ")
        pn = parse_num(desc)
        num = pn[0] if pn else (hnum or "")
        if not num and re.search(r'title\s*1[89]', lo):
            num = "TITLE-19" if "19" in lo else "TITLE-18"
        # title: prefer header caption else cleaned filename descriptor
        title = htitle
        if not title:
            t = re.sub(r'^\d+_', '', stem)
            t = re.sub(r'\.(pdf|PDF)$', '', t)
            title = t.replace("_", " ").strip()
        # linkage
        mconf, mdate, mno, mresult, lnote = "none", "", "", "", ""
        cands = cites.get(num, [])
        cands = [c for c in cands if c["hint"] in ("", itype)] or cites.get(num, [])
        if cands:
            # prefer an approving/adopting motion
            def score(c):
                t = (c["text"] + " " + c["motion_type"]).lower()
                return (("approve" in t or "adopt" in t), c["result"].lower().startswith("pass"))
            best = sorted(cands, key=score, reverse=True)[0]
            mconf, mdate, mno, mresult = "high", best["date"], best["motion_no"], best["result"]
            lnote = "number cited in recorded motion"
        else:
            # medium: same-year (+/-2 month when the number encodes a month) subject
            # overlap. Handles the O-series vs YYYY-MM number drift
            # (e.g. S3 "2025-O-02" cited in a motion as "2025-02-02", Title 8 Animals).
            ym = re.match(r'(\d{4})-(O|\d{1,2})-', num)
            if ym and text:
                yr = ym.group(1)
                mo = None if ym.group(2).upper() == "O" else int(ym.group(2))
                kws = set(re.findall(r'[a-z]{5,}', title.lower())) - {
                    "resolution", "ordinance", "white", "council", "metro", "township",
                    "approving", "adopting", "amending", "certain", "hereby", "authorizing"}
                bestc, bestov = None, 0
                for c in [c for lst in cites.values() for c in lst]:
                    if not c["date"].startswith(yr):
                        continue
                    if mo is not None and abs(int(c["date"][5:7]) - mo) > 2:
                        continue
                    ov = len(kws & set(re.findall(r'[a-z]{5,}', c["text"].lower())))
                    if ov > bestov:
                        bestov, bestc = ov, c
                if bestc and bestov >= 2:
                    mconf, mdate, mno, mresult = "medium", bestc["date"], bestc["motion_no"], bestc["result"]
                    lnote = f"subject match (same-year), {bestov} shared terms"
        # adoption date. For a HIGH (exact-number) match the motion date is the
        # authoritative council-adoption date from clean born-digital minutes and
        # beats the instrument's own typed header (some headers carry a clerk
        # typo, e.g. Res 23-06-02 printed "DATE: June 22, 2022" for a 2023 meeting).
        # For a MEDIUM (fuzzy subject) match the header date is the more accurate
        # one. A broad body-date scan is deliberately NOT used (it grabs term /
        # effective dates, not adoption). Last resort = flagged S3 upload date.
        upload = man.get(fn, ("", ""))[1]
        if mconf == "high":
            adopt = mdate or hdate or upload
            if hdate and mdate and hdate != mdate:
                lnote += f"; header DATE {hdate} differs from motion date (source typo?)"
        elif mconf == "medium":
            adopt = hdate or mdate or upload
        else:
            adopt = hdate or upload
        if adopt == upload and not (hdate or mdate):
            lnote = (lnote + "; date=upload_date(no adoption date in doc)").strip("; ")
        # transparency: instrument number encodes its own year; flag a header-date
        # year that disagrees (source typo or effective-vs-adoption date)
        nyr = re.match(r'(\d{4})-', num)
        if nyr and adopt and adopt != upload and adopt[:4] != nyr.group(1):
            lnote = (lnote + f"; adoption_date year != number year {nyr.group(1)} "
                     "(source-stated date kept)").strip("; ")
        src, lastmod = man.get(fn, ("", ""))
        fmt = "text"
        el = read_ext_method(stem)
        if el.startswith("ocr"):
            fmt = "scanned"
        out.append({
            "ordinance_no": num, "adoption_date": adopt, "date": adopt,
            "title": title, "source_url": src, "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": el, "path": f"raw/{fn}",
            "land_use": is_land_use(title, num, fn), "result": mresult,
            "matched_motion_date": mdate, "matched_motion_no": mno,
            "match_confidence": mconf,
            "instrument_type": itype, "canonical_no": num,
            "dup_raw": ";".join(k for k, v in dup_of.items() if v == fn),
            "source_last_modified": lastmod, "linkage_note": lnote,
        })

    out.sort(key=lambda r: (r["adoption_date"], r["ordinance_no"]))
    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no", "match_confidence",
            "instrument_type", "canonical_no", "dup_raw", "source_last_modified",
            "linkage_note"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    # summary
    from collections import Counter
    print("rows:", len(out))
    print("by type:", dict(Counter(r["instrument_type"] for r in out)))
    print("by confidence:", dict(Counter(r["match_confidence"] for r in out)))
    print("land_use=yes:", sum(1 for r in out if r["land_use"] == "yes"))
    print("format:", dict(Counter(r["format"] for r in out)))
    print("adoption_date blank:", sum(1 for r in out if not r["adoption_date"]))
    print("upload-date fallback:", sum(1 for r in out if "upload_date" in r["linkage_note"]))
    print("excluded cross-entity decoys (raw retained):", excluded)


_EXT = None


def read_ext_method(stem):
    global _EXT
    if _EXT is None:
        _EXT = {}
        p = os.path.join(TXT, "_extraction_log.csv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                _EXT[os.path.splitext(r["filename"])[0]] = r["method"]
    m = _EXT.get(stem, "pdftotext_layout")
    return {"pdftotext_layout": "pdftotext_layout", "ocr_tesseract": "ocr_tesseract",
            "none": "none"}.get(m, m)


if __name__ == "__main__":
    main()
