#!/usr/bin/env python3
"""cop_ord_index.py — build ordinances/index.csv (SCHEMA_SPEC §9 contract) for the
Town of Copperton adopted ordinances + resolutions harvested from
MunicipalCodeOnline (public S3 bucket, 7 subprefixes).

Joins are keyed by URL (manifest <-> fetch log) so the collision-proof saved names
never conflate two distinct instruments. The ordinance NUMBER comes from the
MunicipalCodeOnline ORIGINAL filename (authoritative on the host); the OCR header is
only a fallback (headers carry scanner noise + clerk typos).

Copperton number grammars (all normalized in canon()):
  township / early town : YY-MM-NN  and  YYYY-MM-NN   (e.g. 17-02-01, 2021-10-01)
  town-era ordinances   : YYYY-O-NN                    (e.g. 2025-O-01, 2026-O-03)
  town-era resolutions   : R-YYYY-NN                    (e.g. R2026-02)
The town-era O-series is frequently mis-printed in minutes as a ZERO
(`2025-0-01`) — a single "0" middle segment is normalized to "O" (a real month is
never 0), so an OCR `0<->O` slip still links.

Linkage to meeting_minutes/all_votes.csv (TYPE-AWARE — Copperton runs PARALLEL
ord/res numbering: the 2024-05-15 meeting adopted BOTH `resolution 2024-05-01` and
`ordinance 2024-05-01`, so an ordinance PDF must match the ordinance motion):
  high    = instrument number cited in a recorded motion of the SAME instrument type
  medium  = year (+/-2 months when the number encodes a month) + subject-term overlap
  low     = header adoption date falls on a meeting date whose only ord/res-type
            approving motion is unnumbered (date-only, no number/subject corroboration)
  none    = unmatched
`within_source` is NOT used — every indexed row is backed by an independently
published PDF, so a match is a genuine cross-match, never a minutes-only derivation.

Byte-identical S3 re-uploads (sha256) collapse to ONE row; alternates stay on disk
and are named in the `dup_raw` extra column.

Usage: python3 cop_ord_index.py
"""
import csv
import json
import os
import re
import collections
import urllib.parse
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
BUCKET = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/"
RETRIEVED = "2026-07-14"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

# standard YY-MM-NN / YYYY-MM-NN and the O-series (middle "O" or a mis-OCR'd "0")
NUMRE = re.compile(r'(?<!\d)(\d{2,4})\s*-\s*(O|0|\d{1,2})\s*-\s*(\d{1,3})(?!\d)', re.I)
# town-era resolution R-series: R2026-02 / R 2026 - 2
RRE = re.compile(r'\bR\s*-?\s*(20\d{2})\s*-\s*(\d{1,3})\b', re.I)

# genuine cross-entity decoys (authored by another MSD entity per the caption) —
# retained as raw, EXCLUDED from the index. Populated after caption screening.
# 1597946761_Ordinance_20-08-01.pdf: caption reads "AN ORDINANCE OF THE KEARNS
# METRO TOWNSHIP COUNCIL ... conditional use ... Title 19 of the Kearns Metro
# Township Code" — a KEARNS land-use ordinance mis-filed in Copperton's bucket
# (same 20-08-01 number as Copperton's own fee-schedule ordinance, hence the slip).
# Shared-MSD hazard, confirmed by full-caption sweep of all 153 sidecars (only 1).
EXCLUDE_FILES = {"1597946761_Ordinance_20-08-01.pdf"}

LAND = [r"zoning", r"subdivision", r"rezone", r"land[ -]use", r"general plan",
        r"\bplat\b", r"setback", r"density", r"\bannex\w*", r"home occupation",
        r"title 18", r"title 19", r"accessory dwelling", r"\badu\b",
        r"wildland", r"\bwui\b", r"floodplain", r"\bzone\b", r"impact fee",
        r"engineering standard", r"infrastructure"]
LANDRE = re.compile("|".join(LAND), re.I)

# entities whose ordinances could be mis-filed into Copperton's bucket
OTHER_ENTITIES = re.compile(
    r"\b(WHITE CITY|KEARNS|MAGNA|EMIGRATION CANYON)\b", re.I)


def canon(y, mid, seq):
    y = int(y)
    if y < 100:
        y += 2000
    mid = str(mid).upper()
    if mid == "0":            # OCR/typo of the town-era O-series
        mid = "O"
    return f"{y}-{mid}-{int(seq):02d}"


def canon_r(y, seq):
    return f"R{int(y)}-{int(seq):02d}"


def parse_num(s):
    """Return (canonical_no, kind, month_or_None) from a string, or None.
    kind in {std, oseries, rseries}."""
    mr = RRE.search(s)
    if mr:
        return canon_r(mr.group(1), mr.group(2)), "rseries", None
    m = NUMRE.search(s)
    if m:
        c = canon(m.group(1), m.group(2), m.group(3))
        mid = str(m.group(2)).upper()
        if mid == "0" or mid == "O":
            return c, "oseries", None
        return c, "std", int(m.group(2))
    return None


# ---------- citation index from motions (type-aware) ----------
def build_citations():
    cites = collections.defaultdict(list)
    by_date = collections.defaultdict(list)
    rows = list(csv.DictReader(open(VOTES)))
    seen = set()
    for r in rows:
        k = (r["date"], r["motion_no"])
        if k in seen:
            continue
        seen.add(k)
        text = r["motion"] or ""
        mtype = (r["motion_type"] or "")
        entry = {"date": r["date"], "motion_no": r["motion_no"],
                 "motion_type": mtype, "result": r["result"], "text": text}
        by_date[r["date"]].append(entry)
        found = []
        for m in NUMRE.finditer(text):
            c = canon(m.group(1), m.group(2), m.group(3))
            pre = text[max(0, m.start() - 20):m.start()].lower()
            hint = ("ordinance" if "ordinance" in pre else
                    "resolution" if "resolution" in pre else
                    ("ordinance" if "ordinance" in mtype.lower() else
                     "resolution" if "resolution" in mtype.lower() else ""))
            found.append((c, hint))
        for m in RRE.finditer(text):
            c = canon_r(m.group(1), m.group(2))
            found.append((c, "resolution"))   # R-series is always a resolution
        for c, hint in found:
            e = dict(entry)
            e["hint"] = hint
            cites[c].append(e)
    return cites, by_date


# ---------- per-document header parse (fallback only) ----------
def parse_header(text):
    num = None
    date = None
    title = ""
    if text:
        head = text[:1800]
        region = head[:280]
        dm = re.search(r'date\s*[:\.]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})', region, re.I)
        if dm:
            date = norm_date(dm.group(1))
        if not date:
            dm = re.search(r'date\s*[:\.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', region, re.I)
            if dm:
                date = norm_date(dm.group(1))
        if not date:
            dm = re.search(r'(?:ADOPTED|PASSED|ENACTED|APPROVED)[^.]{0,90}?'
                           r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', head, re.I)
            if dm:
                date = norm_date(dm.group(1))
        if not date:
            for dm in re.finditer(r'([A-Za-z]+\s+\d{1,2},?\s*\d{4})', region):
                pre = region[max(0, dm.start() - 24):dm.start()].lower()
                if any(w in pre for w in ("ending", "term", "expir", "through",
                                          "until", "effective")):
                    continue
                date = norm_date(dm.group(1))
                if date:
                    break
        cm = re.search(r'\b(A[Nn]?\s+(?:RESOLUTION|ORDINANCE)\b.*?)'
                       r'(?:\n\s*\n|RECITALS|WHEREAS|BE IT|NOW,? THEREFORE)',
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


_EXT = None


def read_ext_method(stem):
    global _EXT
    if _EXT is None:
        _EXT = {}
        p = os.path.join(TXT, "_extraction_log.csv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                _EXT[os.path.splitext(r["filename"])[0]] = r["method"]
    return _EXT.get(stem, "pdftotext_layout")


def main():
    # url -> (key, original_filename, last_modified, subfolder)
    man = {}
    for r in csv.DictReader(open(os.path.join(HERE, "_s3_manifest.csv"))):
        if r["in_scope"] != "yes":
            continue
        url = BUCKET + urllib.parse.quote(r["key"])
        man[url] = (r["key"], r["filename"], r["last_modified"][:10], r["subfolder"])

    # fetch log: url -> saved_as ; sha256 dedup (keep first)
    url_of_saved = {}
    saved_of_url = {}
    sha_first = {}
    dup_of = {}
    order = []
    for line in open(os.path.join(RAW, "_fetch_log.jsonl")):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if not d.get("ok"):
            continue
        fn = d["saved_as"]
        url_of_saved[fn] = d["url"]
        saved_of_url[d["url"]] = fn
        order.append(fn)
        s = d["sha256"]
        if s in sha_first:
            dup_of[fn] = sha_first[s]
        else:
            sha_first[s] = fn

    cites, by_date = build_citations()

    out = []
    excluded = []
    for fn in sorted(order):
        if fn in dup_of:
            continue
        if fn in EXCLUDE_FILES:
            excluded.append(fn)
            continue
        url = url_of_saved[fn]
        key, origfn, lastmod, subfolder = man.get(url, ("", fn, "", ""))
        stem = os.path.splitext(fn)[0]
        tf = os.path.join(TXT, stem + ".txt")
        text = open(tf).read() if os.path.exists(tf) else ""

        # cross-entity caption screen (shared-MSD hazard)
        cap = text[:600]
        other = OTHER_ENTITIES.search(cap)
        if other and "copperton" not in cap.lower():
            print(f"  ! POSSIBLE cross-entity decoy ({other.group(0)}): {fn}")

        # instrument type from the ORIGINAL filename / subfolder
        lo = origfn.lower()
        if re.search(r'\bR\s*-?\s*20\d{2}\s*-\s*\d', origfn):
            itype = "resolution"
        elif "-o-" in lo or re.search(r'20\d{2}-o-\d', lo):
            itype = "ordinance"
        elif "resolution" in lo:
            itype = "resolution"
        elif "ordinance" in lo or lo.startswith("ord "):
            itype = "ordinance"
        else:
            itype = ("resolution" if subfolder == "resolutions" else "ordinance")

        pn = parse_num(origfn)
        hnum, hdate, htitle = parse_header(text)
        if pn:
            num, kind, month = pn
        elif re.search(r'title\s*1[89]', lo):
            num = "TITLE-19" if "19" in lo else "TITLE-18"
            kind, month = "title", None
        else:
            num, kind, month = (hnum or ""), "std", None

        # title: prefer header caption else cleaned original filename
        title = htitle
        if not title:
            t = re.sub(r'\.(pdf|PDF)$', '', origfn).strip()
            title = re.sub(r'\s+', ' ', t)[:300]

        # ---- linkage (type-aware) ----
        mconf, mdate, mno, mresult, lnote = "none", "", "", "", ""
        cands = cites.get(num, [])
        typed = [c for c in cands if c["hint"] in ("", itype)]
        use = typed or cands
        if num and use:
            def score(c):
                t = (c["text"] + " " + c["motion_type"]).lower()
                return (("approve" in t or "adopt" in t),
                        c["result"].lower().startswith("pass"))
            best = sorted(use, key=score, reverse=True)[0]
            mconf, mdate, mno, mresult = "high", best["date"], best["motion_no"], best["result"]
            lnote = "number cited in recorded motion (type-matched)"
        elif num and text:
            # medium: subject-term overlap with a type-consistent motion. When the
            # instrument carries its OWN header date, the candidate motion must fall
            # within +/-45 days of it (a numbered instrument is adopted at ONE
            # meeting — a same-year match at a distant meeting is a false positive,
            # e.g. an Aug fee ordinance must not link to an Oct motion). Without a
            # header date, fall back to the number's year (+/-2 months if a month is
            # encoded). Year-only (O/R/Title) series need a stronger overlap (>=3).
            ym = re.match(r'(?:R)?(\d{4})', num)
            yr = ym.group(1) if ym else None
            year_only = kind in ("oseries", "rseries", "title") or month is None
            thresh = 3 if year_only else 2

            def dparse(s):
                try:
                    return _date(int(s[:4]), int(s[5:7]), int(s[8:10]))
                except Exception:
                    return None
            hd = dparse(hdate) if hdate else None
            kws = set(re.findall(r'[a-z]{5,}', title.lower())) - {
                "resolution", "ordinance", "copperton", "council", "metro",
                "township", "approving", "adopting", "amending", "certain",
                "hereby", "authorizing", "town"}
            bestc, bestov = None, 0
            for c in [m for lst in by_date.values() for m in lst]:
                cd = dparse(c["date"])
                if hd and cd:
                    if abs((cd - hd).days) > 20:
                        continue
                else:
                    if yr and not c["date"].startswith(yr):
                        continue
                    if month is not None and abs(int(c["date"][5:7]) - month) > 2:
                        continue
                # type-consistent motion
                mt = (c["text"] + " " + c["motion_type"]).lower()
                if itype == "ordinance" and "ordinance" not in mt and "ordinance" not in c["motion_type"].lower():
                    if "resolution" in mt:
                        continue
                ov = len(kws & set(re.findall(r'[a-z]{5,}', mt)))
                if ov > bestov:
                    bestov, bestc = ov, c
            if bestc and bestov >= thresh:
                mconf, mdate, mno, mresult = "medium", bestc["date"], bestc["motion_no"], bestc["result"]
                lnote = f"subject match, {bestov} shared terms" + (
                    " (within 20d of header date)" if hd else " (same-year)")

        # low: header adoption date lands on a meeting that has an unnumbered
        # approving motion of this instrument type, and nothing better matched
        if mconf == "none" and hdate and hdate in by_date:
            for c in by_date[hdate]:
                mt = (c["text"] + " " + c["motion_type"]).lower()
                if itype in mt and ("approve" in mt or "adopt" in mt):
                    mconf, mdate, mno, mresult = "low", c["date"], c["motion_no"], c["result"]
                    lnote = "date-only: header adoption date matches a meeting with an unnumbered approving motion"
                    break

        # ---- adoption date resolution ----
        upload = lastmod
        # instrument-number-encoded year-month fallback (kearns lesson): prefer the
        # number's own YYYY-MM (day placeholder 01) over the S3 upload date.
        num_ym = None
        if kind == "std":
            nm = re.match(r'(\d{4})-(\d{1,2})-', num)
            if nm and 1 <= int(nm.group(2)) <= 12:
                num_ym = f"{nm.group(1)}-{int(nm.group(2)):02d}-01"
        elif kind in ("oseries", "rseries", "title"):
            nm = re.match(r'R?(\d{4})', num)
            num_ym = None  # year-only; no reliable month -> don't fabricate a month

        if mconf in ("high", "low"):
            adopt = mdate or hdate or num_ym or upload
            if hdate and mdate and hdate != mdate:
                lnote += f"; header DATE {hdate} differs from motion date (source typo?)"
        elif mconf == "medium":
            adopt = hdate or mdate or num_ym or upload
        else:
            adopt = hdate or num_ym or upload

        if adopt == num_ym and num_ym and not (hdate or mdate):
            lnote = (lnote + "; date=YYYY-MM from instrument number, day placeholder 01").strip("; ")
        elif adopt == upload and not (hdate or mdate or num_ym):
            lnote = (lnote + "; date=upload_date (no adoption date in doc / number carries no month)").strip("; ")

        # transparency: number encodes its own year; flag a disagreeing adoption year
        nyr = re.match(r'R?(\d{4})-', num)
        if nyr and adopt and adopt != upload and adopt[:4] != nyr.group(1):
            lnote = (lnote + f"; adoption_date year != number year {nyr.group(1)} "
                     "(source-stated date kept)").strip("; ")

        fmt = "scanned" if read_ext_method(stem).startswith("ocr") else \
              ("na" if read_ext_method(stem) == "none" else "text")
        out.append({
            "ordinance_no": num, "adoption_date": adopt, "date": adopt,
            "title": title, "source_url": url, "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": read_ext_method(stem),
            "path": f"raw/{fn}",
            "land_use": is_land_use(title, num, origfn), "result": mresult,
            "matched_motion_date": mdate, "matched_motion_no": mno,
            "match_confidence": mconf,
            "instrument_type": itype, "canonical_no": num,
            "dup_raw": ";".join(k for k, v in dup_of.items() if v == fn),
            "source_last_modified": lastmod, "subfolder": subfolder,
            "linkage_note": lnote,
        })

    out.sort(key=lambda r: (r["adoption_date"] or "9999", r["instrument_type"],
                            r["ordinance_no"]))
    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no", "match_confidence",
            "instrument_type", "canonical_no", "dup_raw", "source_last_modified",
            "subfolder", "linkage_note"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print("rows:", len(out))
    print("by type:", dict(Counter(r["instrument_type"] for r in out)))
    print("by confidence:", dict(Counter(r["match_confidence"] for r in out)))
    print("land_use=yes:", sum(1 for r in out if r["land_use"] == "yes"))
    print("format:", dict(Counter(r["format"] for r in out)))
    print("adoption_date blank:", sum(1 for r in out if not r["adoption_date"]))
    print("num-ym fallback:", sum(1 for r in out if "from instrument number" in r["linkage_note"]))
    print("upload-date fallback:", sum(1 for r in out if "upload_date" in r["linkage_note"]))
    print("byte-identical dups collapsed:", len(dup_of))
    print("excluded cross-entity decoys (raw retained):", excluded)
    print("date window:", min((r["adoption_date"] for r in out if r["adoption_date"]), default=""),
          "->", max((r["adoption_date"] for r in out if r["adoption_date"]), default=""))


if __name__ == "__main__":
    main()
