#!/usr/bin/env python3
"""kearns_ord_index.py — build ordinances/index.csv (SCHEMA_SPEC §9 contract) for
Kearns adopted ordinances + resolutions harvested from MunicipalCodeOnline.

Number families (all normalized by canon()):
  * township 3-part  YY-MM-NN / YYYY-MM-NN   e.g. 17-02-01, 2024-05-01
  * city ordinance   YYYY-O-NN               e.g. 2025-O-08  (OCR 0<->O tolerated)
  * city resolution  RYYYY-NN                e.g. R2026-12

Linkage to meeting_minutes/all_votes.csv (independently-published PDFs -> genuine
cross-matches, NOT motion-derived, so `within_source` is intentionally UNUSED):
  high    = instrument number cited in a recorded motion (exact canon match)
  medium  = same-year + subject-term overlap (number not exactly matched)
  none    = unmatched
Mayor/Chair VOTES in both eras (max roll tally = 5) — linkage never assumes the mayor
is a non-voter.

Byte-identical S3 re-uploads (sha256) collapse to ONE row; the alternate raw stays on
disk, named in `dup_raw`. Cross-entity decoys + non-instrument attachments are retained
as raw but EXCLUDED from the index (EXCLUDE_FILES).

Standing rule: lives INSIDE kearns_city_council/ordinances/, unique kearns_ord_ prefix.
Usage: python3 kearns_ord_index.py
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

# Non-instrument attachments + cross-entity/test decoys: retained as raw, NOT indexed.
# (Screened by authoring caption / obvious attachment role — see CLAUDE.md.)
EXCLUDE_FILES = {
    "Ord_COP_Test.pdf",  # Kearns "ORDINANCE COP TEST" placeholder/test upload, no real number
    "Kearns_R2025-10_Attachment_A_-_Salt_Lake_County_Kearns_Annex.pdf",
    "Kearns_R2025-10_Attachment_B_-_SLC_HMP_Volume_1_-_July_2025_Revised.pdf",
    "Kearns_R2025-10_Attachment_C_-_SLC_HMP_Volume_2_-_July_2025_Revised.pdf",
}

LAND = [r"zoning", r"subdivision", r"rezone", r"land[ -]use", r"general plan",
        r"\bplat\b", r"setback", r"density", r"\bannex\w*", r"title 18", r"title 19",
        r"19\.46", r"19\.48", r"19\.50", r"\bwui\b", r"wildland", r"accessory dwelling",
        r"\badu\b", r"floodplain", r"\bzone\b", r"overlay", r"landscap", r"conditional use"]
LANDRE = re.compile("|".join(LAND), re.I)


def canon(s):
    """Normalize any Kearns instrument number to a canonical key, or None."""
    if not s:
        return None
    s = s.strip()
    # R-series city resolution: R2025-10 / R 2026-2
    m = re.search(r'\bR\s*-?\s*(\d{4})\s*-\s*(\d{1,3})\b', s, re.I)
    if m:
        return f"R{int(m.group(1))}-{int(m.group(2)):02d}"
    # O-series city ordinance: 2025-O-08 (letter O or OCR 0 as single mid char)
    m = re.search(r'(?<!\d)(\d{4})\s*-\s*([Oo0])\s*-\s*(\d{1,3})(?!\d)', s)
    if m and (m.group(2) in ("O", "o") or int(m.group(1)) >= 2025):
        return f"{int(m.group(1))}-O-{int(m.group(3)):02d}"
    # 3-part township month-seq: 17-02-01 / 2024-05-01 / 2024-7-01
    m = re.search(r'(?<!\d)(\d{2,4})\s*-\s*(\d{1,2})\s*-\s*(\d{1,3})(?!\d)', s)
    if m:
        y = int(m.group(1))
        if y < 100:
            y += 2000
        return f"{y}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


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


# ---------- citation index from motions ----------
def build_citations():
    cites = collections.defaultdict(list)
    rows = list(csv.DictReader(open(VOTES)))
    seen = set()
    numpat = re.compile(
        r'(R\s*-?\s*\d{4}\s*-\s*\d{1,3}'
        r'|\d{4}\s*-\s*[Oo0]\s*-\s*\d{1,3}'
        r'|\d{2,4}\s*-\s*\d{1,2}\s*-\s*\d{1,3})')
    for r in rows:
        k = (r["date"], r["motion_no"])
        if k in seen:
            continue
        seen.add(k)
        text = r["motion"] or ""
        for m in numpat.finditer(text):
            c = canon(m.group(1))
            if not c:
                continue
            pre = text[max(0, m.start() - 22):m.start()].lower()
            hint = ("ordinance" if "ordinance" in pre else
                    "resolution" if "resolution" in pre else "")
            cites[c].append({"date": r["date"], "motion_no": r["motion_no"],
                             "motion_type": r["motion_type"], "result": r["result"],
                             "text": text, "hint": hint})
    return cites


# ---------- per-document header parse (date + caption) ----------
def parse_header(text):
    date = None
    title = ""
    if text:
        head = text[:1800]
        region = head[:300]
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
    return date, title


def is_land_use(title, num, fn):
    blob = (title + " " + (num or "") + " " + fn.replace("_", " "))
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
    # source_url + last_modified keyed by LOCAL saved filename (manifest 'name')
    man = {}
    for r in csv.DictReader(open(os.path.join(HERE, "kearns_ord_manifest.csv"))):
        man[r["name"]] = (r["url"], r["lastmodified"][:10], r["s3_prefix"])

    # sha256 dedup from the fetch log
    sha_first, dup_of = {}, {}
    with open(os.path.join(RAW, "_fetch_log.jsonl")) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            fn = os.path.basename(d.get("saved_as") or d.get("name") or "")
            s = d.get("sha256")
            if not fn or not s:
                continue
            if s in sha_first:
                dup_of[fn] = sha_first[s]
            else:
                sha_first[s] = fn

    cites = build_citations()
    all_cites = [c for lst in cites.values() for c in lst]

    raws = sorted(f for f in os.listdir(RAW)
                  if f.lower().endswith((".pdf", ".docx")))
    out, excluded = [], []
    for fn in raws:
        if fn in dup_of:
            continue
        if fn in EXCLUDE_FILES:
            excluded.append(fn)
            continue
        stem = os.path.splitext(fn)[0]
        tf = os.path.join(TXT, stem + ".txt")
        text = open(tf).read() if os.path.exists(tf) else ""
        src, lastmod, pref = man.get(fn, ("", "", ""))
        # instrument type from filename, then S3 prefix
        lo = fn.lower()
        if re.search(r'\br\d{4}-', lo) or "resolution" in lo or "resoluiton" in lo:
            itype = "resolution"
        elif "-o-" in lo or "ordinance" in lo:
            itype = "ordinance"
        elif pref == "resolutions":
            itype = "resolution"
        else:
            itype = "ordinance"
        # number from the MunicipalCodeOnline filename (authoritative)
        desc = re.sub(r'^\d+_', '', stem).replace("_", " ")
        num = canon(desc) or ""
        if not num and re.search(r'title[ _]*1[89]', lo):
            num = "TITLE-19" if re.search(r'title[ _]*19', lo) else "TITLE-18"
        # header date + caption
        hdate, htitle = parse_header(text)
        title = htitle or desc.strip()
        # linkage
        mconf, mdate, mno, mresult, lnote = "none", "", "", "", ""
        cands = cites.get(num, []) if num else []
        typed = [c for c in cands if c["hint"] in ("", itype)]
        cands = typed or cands
        if cands:
            def score(c):
                t = (c["text"] + " " + c["motion_type"]).lower()
                return (("approve" in t or "adopt" in t),
                        c["result"].lower().startswith(("pass", "unanim", "approv")))
            best = sorted(cands, key=score, reverse=True)[0]
            mconf, mdate, mno, mresult = "high", best["date"], best["motion_no"], best["result"]
            lnote = "number cited in recorded motion"
        elif num and text:
            ym = re.match(r'(?:R)?(\d{4})-', num)
            if ym:
                yr = ym.group(1)
                mo = None
                mm = re.match(r'\d{4}-(\d{2})-', num)
                if mm:
                    mo = int(mm.group(1))
                kws = set(re.findall(r'[a-z]{5,}', title.lower())) - {
                    "resolution", "ordinance", "kearns", "council", "metro",
                    "township", "approving", "adopting", "amending", "certain",
                    "hereby", "authorizing", "providing", "relating"}
                bestc, bestov = None, 0
                for c in all_cites:
                    if not c["date"].startswith(yr):
                        continue
                    if mo is not None and abs(int(c["date"][5:7]) - mo) > 2:
                        continue
                    ov = len(kws & set(re.findall(r'[a-z]{5,}', c["text"].lower())))
                    if ov > bestov:
                        bestov, bestc = ov, c
                if bestc and bestov >= 2:
                    mconf, mdate, mno, mresult = ("medium", bestc["date"],
                                                  bestc["motion_no"], bestc["result"])
                    lnote = f"subject match (same-year), {bestov} shared terms"
        # adoption date
        if mconf == "high":
            adopt = mdate or hdate or lastmod
            if hdate and mdate and hdate != mdate:
                lnote += f"; header DATE {hdate} differs from motion date (source typo?)"
        elif mconf == "medium":
            adopt = hdate or mdate or lastmod
        else:
            adopt = hdate
            # guard: a header date whose year disagrees with the number's encoded
            # year is a misparse (stray body/effective date) — discard it.
            nyr0 = re.match(r'(?:R)?(\d{4})-', num or "")
            if adopt and nyr0 and adopt[:4] != nyr0.group(1):
                adopt = None
                lnote = (lnote + f"; header date {hdate} disagrees w/ number year "
                         f"{nyr0.group(1)} — discarded").strip("; ")
            if not adopt:
                # township numbers encode YYYY-MM-NN: use the number's year+month
                # (far truer than the batch S3 upload date) with a placeholder day.
                mmn = re.match(r'(\d{4})-(\d{2})-\d', num or "")
                if mmn:
                    adopt = f"{mmn.group(1)}-{mmn.group(2)}-01"
                    lnote = (lnote + "; date=YYYY-MM from instrument number, day "
                             "placeholder 01 (exact adoption date not in doc)").strip("; ")
                else:
                    adopt = lastmod
                    lnote = (lnote + "; date=upload_date(no adoption date in doc)").strip("; ")
        nyr = re.match(r'(?:R)?(\d{4})-', num or "")
        if nyr and adopt and adopt != lastmod and adopt[:4] != nyr.group(1):
            lnote = (lnote + f"; adoption_date year != number year {nyr.group(1)} "
                     "(source-stated date kept)").strip("; ")
        el = read_ext_method(stem)
        if el.startswith("ocr"):
            fmt = "scanned"
        elif el == "none":
            fmt = "scanned"
        else:
            fmt = "text"
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
    from collections import Counter
    print("rows:", len(out))
    print("by type:", dict(Counter(r["instrument_type"] for r in out)))
    print("by confidence:", dict(Counter(r["match_confidence"] for r in out)))
    print("land_use=yes:", sum(1 for r in out if r["land_use"] == "yes"))
    print("format:", dict(Counter(r["format"] for r in out)))
    print("adoption_date blank:", sum(1 for r in out if not r["adoption_date"]))
    print("no canonical number:", sum(1 for r in out if not r["ordinance_no"]))
    print("upload-date fallback:", sum(1 for r in out if "upload_date" in r["linkage_note"]))
    print("dedup collapsed:", len(dup_of))
    print("excluded (raw retained):", excluded)


if __name__ == "__main__":
    main()
