#!/usr/bin/env python3
"""build_index.py — regenerate summit_county/campaign_finance/index.csv (DERIVED).

Inputs (all on disk, never network):
  batch/manifest.json          candidate -> url -> file manifest (the acquisition record)
  raw/<year>/*.pdf             the retained filings
  text/*.txt                   the text sidecars (pdftotext -layout, or tesseract)
  ../elections/election_results_by_contest.csv   for the office/candidate join

Outputs:
  index.csv                    one row per filing
  unrecovered.csv              listed-but-not-retrievable filings + on-ballot candidates with
                               zero filings (honest gaps)

Never hand-edit index.csv — edit the manifest / this script and rerun:
    python3 summit_county/campaign_finance/build_index.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ELECTIONS = os.path.join(HERE, "..", "elections", "election_results_by_contest.csv")
RETRIEVED = "2026-08-01"

# ---------------------------------------------------------------- office normalization

_OFFICE_PATTERNS = [
    (re.compile(r"council", re.I), "County Council"),
    (re.compile(r"attorney", re.I), "County Attorney"),
    (re.compile(r"auditor", re.I), "County Auditor"),
    (re.compile(r"\bclerk\b", re.I), "County Clerk"),
    (re.compile(r"sheriff", re.I), "County Sheriff"),
    (re.compile(r"assessor", re.I), "County Assessor"),
    (re.compile(r"recorder|surveyor", re.I), "County Recorder/Surveyor"),
    (re.compile(r"treasurer", re.I), "County Treasurer"),
]
_SEAT = re.compile(r"(?:seat|district|dist\.?)\s*[\"']?\s*([A-E]|\d)\b", re.I)


def norm_office(raw: str):
    """(office, seat) or (None, '') when the string is too garbled to classify.

    Deliberately conservative: an OCR string that matches no keyword returns None rather
    than a guess (cardinal rule 1)."""
    if not raw:
        return None, ""
    for pat, canon in _OFFICE_PATTERNS:
        if pat.search(raw):
            seat = ""
            m = _SEAT.search(raw)
            if m:
                seat = m.group(1).upper()
            elif canon == "County Council":
                # "County Council 4" / "Council E:" forms with no seat/district word
                m2 = re.search(r"council\s*[-:]?\s*([A-E]|\d)\b", raw, re.I)
                if m2:
                    seat = m2.group(1).upper()
            return canon, seat
    return None, ""


# "Office Filed For: X   Party: Y"  /  "Name of Office: X"
_OFFICE_LINE = re.compile(
    r"(?:office\s*filed\s*for|name\s*of\s*office|office\s*filed\s*for)\s*[:.]?\s*(.{0,80})",
    re.I)


def office_from_text(txt: str):
    for m in _OFFICE_LINE.finditer(txt.replace("!", " ")):
        frag = re.split(r"\bpart?y\b|\bportY\b", m.group(1), flags=re.I)[0]
        off, seat = norm_office(frag)
        if off:
            return off, seat
    return None, ""


# ---------------------------------------------------------------- elections join

def _clean_name(s: str) -> str:
    s = re.sub(r"\(([A-Z]{3})\)", " ", s)
    s = re.sub(r"^(?:DEM|REP|IAM|CON|LIB|UNA|GRN|Write-In:)\s+", "", s.strip(), flags=re.I)
    s = re.sub(r"\b(?:DEM|REP|IAM|CON|LIB|UNA|GRN)\b", " ", s)
    s = re.sub(r"[^A-Za-z ]", " ", s)
    return " ".join(s.split()).upper()


COUNTY_OFFICES = {"County Council", "County Attorney", "County Auditor", "County Clerk",
                  "County Sheriff", "County Assessor", "County Recorder/Surveyor",
                  "County Treasurer"}


def load_ballot():
    """(year, SURNAME) -> [(office, seat, canonical_name)] for county contests."""
    out = {}
    rows = list(csv.DictReader(open(ELECTIONS)))
    for r in rows:
        off, seat = norm_office(r.get("office", "") or "")
        if off not in COUNTY_OFFICES:
            continue
        if not seat:
            _, seat = norm_office(r.get("contest", "") or "")
        name = _clean_name(r["candidate"])
        if not name or name in ("WRITE IN VOTES", "WRITE IN TOTALS", "NOT ASSIGNED",
                                "INVALID", "WITHDRAWN", "TOTALS"):
            continue
        key = (r["year"], name.split()[-1])
        out.setdefault(key, []).append((off, seat, r["candidate"], r["election_type"]))
    return out


# ---------------------------------------------------------------- text quality

_MONEY = re.compile(r"\$\s?[\d,]+\.\d{2}|\b\d{1,3}(?:,\d{3})*\.\d{2}\b")


def text_quality(txt: str, surname: str) -> str:
    """high  = the filer's own name AND >=2 money tokens are legible in the sidecar
       medium= one of the two
       low   = neither (handwriting/scan floor — the filing's numbers are NOT machine-readable)"""
    has_name = bool(surname) and surname.upper() in re.sub(r"[^A-Za-z]", " ", txt).upper()
    n_money = len(_MONEY.findall(txt))
    if has_name and n_money >= 2:
        return "high"
    if has_name or n_money >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------- pdf probes

def probe_pdf(path):
    """(format, n_pages) — 'scanned' when any page carries a full-width raster image."""
    try:
        li = subprocess.run(["pdfimages", "-list", path], capture_output=True, text=True,
                            timeout=120).stdout
    except Exception:
        li = ""
    big = 0
    for ln in li.splitlines()[2:]:
        parts = ln.split()
        if len(parts) > 4 and parts[2] in ("image", "smask"):
            try:
                if int(parts[3]) > 900:
                    big += 1
            except ValueError:
                pass
    try:
        info = subprocess.run(["pdfinfo", path], capture_output=True, text=True,
                              timeout=60).stdout
    except Exception:
        info = ""
    pages = re.search(r"Pages:\s*(\d+)", info)
    created = re.search(r"CreationDate:\s*(.+)", info)
    return ("scanned" if big else "text"), (pages.group(1) if pages else ""), \
           (created.group(1).strip() if created else "")


_MONTHS = {m: i + 1 for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def iso_creation(raw: str, cycle_year: str) -> str:
    """PDF CreationDate -> ISO, ONLY when its year equals the cycle year (else blank).
    This is a scan/save-date PROXY, never the statutory filing date."""
    m = re.search(r"(\w{3})\s+(\w{3})\s+(\d{1,2})\s+[\d:]+\s+(\d{4})", raw)
    if not m:
        return ""
    mon, day, yr = m.group(2), int(m.group(3)), m.group(4)
    if yr != str(cycle_year) or mon not in _MONTHS:
        return ""
    return f"{yr}-{_MONTHS[mon]:02d}-{day:02d}"


# ---------------------------------------------------------------- period / filing type

def norm_period(label: str) -> str:
    l = " ".join(label.split())
    if not l:
        return ""
    low = l.lower()
    if "appointment" in low:
        return "Appointment Report"
    if "withdraw" in low:
        return "Withdrawn"
    if "out at convention" in low:
        return "Out at Convention"
    if "out at primary" in low:
        return "Out at Primary"
    if "final" in low:
        return "Final"
    if "pre-election" in low or "pre election" in low:
        return "Pre-Election"
    if "post" in low:
        return "Post-Election"
    if "pre-primary" in low or "pre primary" in low:
        return "Pre-Primary"
    if "primary" in low:
        return "Primary"
    return l


HEADER = ["date", "date_basis", "candidate", "office", "seat", "election_year",
          "filing_type", "reporting_period", "title", "source_url", "retrieved_date",
          "format", "extraction_method", "path", "text_path", "bytes", "sha256",
          "document_id", "channel", "listing_url", "office_source",
          "matched_election_candidate", "join_confidence", "text_quality",
          "needs_review", "notes"]


def main():
    man = json.load(open(os.path.join(HERE, "batch", "manifest.json")))
    ballot = load_ballot()
    extraction = {}
    tep = os.path.join(HERE, "text_extraction.csv")
    if os.path.exists(tep):
        for r in csv.DictReader(open(tep)):
            extraction[r["path"]] = r["extraction_method"]
    else:
        sys.exit("text_extraction.csv missing — run backfill_text.py first")
    overrides = {}
    ovp = os.path.join(HERE, "office_overrides.csv")
    if os.path.exists(ovp):
        for r in csv.DictReader(open(ovp)):
            overrides[r["document_id"]] = r

    rows, missing = [], []
    for m in man:
        path = m["path"]
        abspath = os.path.join(HERE, path)
        if not os.path.exists(abspath):
            missing.append(dict(election_year=m["election_year"],
                                candidate=m["candidate_listed"],
                                document_id=m["document_id"],
                                source_url=m["source_url"],
                                reason="listed on the county page; file not on disk"))
            continue
        b = open(abspath, "rb").read()
        sha = hashlib.sha256(b).hexdigest()
        stem = os.path.splitext(os.path.basename(path))[0]
        tpath = os.path.join("text", stem + ".txt")
        txt = ""
        if os.path.exists(os.path.join(HERE, tpath)):
            txt = open(os.path.join(HERE, tpath), errors="replace").read()

        fmt, pages, created = probe_pdf(abspath)
        method = extraction.get(path, "")
        if fmt == "scanned" and method == "pdftotext -layout":
            # the scan carries a text layer the clerk's scanner (not this repo) produced
            method = "embedded OCR text layer (pdftotext -layout)"

        cand = m.get("candidate_override") or m["candidate_listed"]
        if "," in cand and cand.count(",") == 1:            # "Brickey, David R." -> natural
            last, first = [x.strip() for x in cand.split(",")]
            cand = f"{first} {last}".strip()
        surname = _clean_name(cand).split()[-1] if _clean_name(cand) else ""

        # ---- office: filing text (primary source) > portal listing > elections join
        off, seat = office_from_text(txt)
        src = "filing_text" if off else ""
        l_off, l_seat = norm_office(m.get("office_listed", ""))
        if not off:
            off, seat, src = l_off, l_seat, ("portal_listing" if l_off else "")
        elif off == l_off and not seat and l_seat:
            seat = l_seat                       # office verbatim from the filing, seat from listing
        matched, conf = "", "none"
        hits = ballot.get((str(m["election_year"]), surname), [])
        if hits:
            matched = hits[0][2]
            conf = "surname+year" if len({h[0] for h in hits}) == 1 else "ambiguous"
            if not off and len({h[0] for h in hits}) == 1:
                off, seat = hits[0][0], hits[0][1]
                src = "elections_join"
            if off == "County Council" and not seat and len({h[1] for h in hits}) == 1:
                seat = hits[0][1]
        if m["document_id"] in overrides:
            o = overrides[m["document_id"]]
            off, seat, src = o["office"], o["seat"], "override:" + o["evidence"]
        if not off:
            off, src = "", src or "unresolved"

        tq = text_quality(txt, surname)
        period = norm_period(m["period_label"])
        date = iso_creation(created, m["election_year"])
        notes = []
        if not off:
            notes.append("office not recoverable from filing text, portal listing or "
                         "elections join")
        if tq == "low":
            notes.append("sidecar illegible (handwritten/scan floor) — read the raw PDF")
        rows.append({
            "date": date or "", "date_basis": "pdf_creation_date (proxy)" if date else "",
            "candidate": cand, "office": off, "seat": seat,
            "election_year": m["election_year"], "filing_type": "statement",
            "reporting_period": period,
            "title": f"{cand} — {m['election_year']} Summit County campaign financial report"
                     + (f" ({period})" if period else ""),
            "source_url": m["source_url"], "retrieved_date": RETRIEVED,
            "format": fmt, "extraction_method": method, "path": path, "text_path": tpath,
            "bytes": str(len(b)), "sha256": sha, "document_id": m["document_id"],
            "channel": m["channel"], "listing_url": m["listing_url"],
            "office_source": src, "matched_election_candidate": matched,
            "join_confidence": conf, "text_quality": tq,
            "needs_review": "1" if (tq != "high" or not off) else "0",
            "notes": "; ".join(notes),
        })

    rows.sort(key=lambda r: (r["election_year"], r["office"], r["candidate"],
                             r["document_id"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)

    # ---- honest gaps: on-ballot county candidates with ZERO filings in this dataset
    have = {(str(r["election_year"]), _clean_name(r["candidate"]).split()[-1])
            for r in rows if _clean_name(r["candidate"])}
    for (yr, surname), hits in sorted(ballot.items()):
        if int(yr) % 2 or int(yr) < 2014:
            continue
        if (yr, surname) in have:
            continue
        off, seat, canon, etype = hits[0]
        missing.append(dict(election_year=yr, candidate=canon, document_id="",
                            source_url="",
                            reason=f"on the {yr} {etype} ballot for {off}"
                                   f"{' seat ' + seat if seat else ''}; "
                                   f"no campaign financial report published"))
    gp = os.path.join(HERE, "listed_gaps.csv")
    if os.path.exists(gp):
        for g in csv.DictReader(open(gp)):
            missing.append(dict(election_year=g["election_year"], candidate=g["candidate"],
                                document_id=g["document_id"], source_url=g["source_url"],
                                reason=g["reason"]))
    with open(os.path.join(HERE, "unrecovered.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["election_year", "candidate", "document_id",
                                          "source_url", "reason"])
        w.writeheader()
        w.writerows(sorted(missing, key=lambda r: (str(r["election_year"]),
                                                   r["candidate"])))
    print(f"index.csv: {len(rows)} filings   unrecovered.csv: {len(missing)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
