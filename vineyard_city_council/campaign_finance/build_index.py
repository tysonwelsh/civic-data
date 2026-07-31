#!/usr/bin/env python3
"""Build the Vineyard campaign-finance filing index + text sidecars.

Reproducible, idempotent. For every PDF under raw/<cycle>/:
  * extract born-digital text with pdftotext; if the page carries no text layer,
    OCR it (pdftoppm@300dpi -> tesseract) and label it `scanned`.
  * write a text sidecar to text/<cycle>/<basename>.txt (Source-6 rule: a sidecar
    for EVERY filing).
  * emit one index.csv row with provenance (source_url from raw/<cycle>/_fetch_log.jsonl)
    and the candidate/office/election_year/filing_type facets, joined to
    election_results/vineyard_results_by_candidate.csv.

Never edits election_results. Never invents a value it cannot source.
Usage:  python3 build_index.py
"""
import csv, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
CITY = os.path.abspath(os.path.join(HERE, ".."))
ELECT = os.path.join(CITY, "election_results", "vineyard_results_by_candidate.csv")
RETRIEVED = "2026-07-05"

# ---- per-file metadata -------------------------------------------------------
# Full candidate display names keyed by (cycle, surname-token as it appears in file).
NAMES = {
 "holdaway": "Wayne T. Holdaway", "riley": "Nathan Riley", "booth": "James Booth",
 "flake": "G. Tyce Flake", "judd": "Chris Judd", "simpson": "Simpson",
 "farnworth": "Randy E. Farnworth", "fullmer": "Julie Fullmer",
 "gillespie": "Jeff R. Gillespie", "goodman": "Dale E. Goodman",
 "herring": "Shawn Scott Herring", "earnest": "John Earnest", "mehner": "Kevin Mehner",
 "jenkins": "Anthony Jenkins", "hernandez": "Hector Hernandez", "kuder": "Keith Kuder",
 "gudmundson": "Tay Gudmundson", "gudmundon": "Tay Gudmundson",
 "gudmundsom": "Tay Gudmundson", "welsh": "Cristy Welsh", "lauret": "David Lauret",
 "brimhall": "Marc Brimhall", "cane": "Maria Guadalupe Cane", "sifuentes": "Mardi Sifuentes",
 "rasmussen": "Amber Rasmussen", "price": "Kristal C. Price", "pacheco": "Nef Pacheco",
 "terry": "Steve Terry", "ewing": "Terry Ewing",
}
# Office by (cycle, surname). "verified" cycles come from election_results + repo notes;
# 2015/2017 are pre-floor -> office INFERRED from public record (flagged office_confidence).
OFFICE = {
 (2015, "*"): ("Council", "inferred"),          # small at-large field; office not in election_results
 (2015, "farnworth"): ("Mayor", "inferred"),    # Farnworth was Vineyard mayor pre-Fullmer
 (2017, "*"): ("Council", "inferred"),
 (2017, "fullmer"): ("Mayor", "verified"),       # Fullmer elected mayor 2017 (repo-documented incumbent)
 (2019, "*"): ("Council", "verified"),           # 2019 ballot: council race only, no mayor
 (2021, "fullmer"): ("Mayor", "verified"), (2021, "brimhall"): ("Mayor", "verified"),
 (2021, "cane"): ("Mayor", "verified"),
 (2021, "*"): ("Council", "verified"),
 (2025, "*"): ("Council", "verified"),
}

def surname(fn):
    """Resolve the candidate token. Vineyard filenames are Surname-First, so when
    several known tokens appear (e.g. 'Ewing-Terry' where Terry is also a candidate),
    prefer the one that appears EARLIEST — the surname."""
    toks = re.split(r"[^a-z]+", fn.lower())
    best, bestpos = None, 1e9
    for i, t in enumerate(toks):
        if t in NAMES and i < bestpos:
            best, bestpos = t, i
    return best

def office_for(cycle, sur):
    return OFFICE.get((cycle, sur)) or OFFICE.get((cycle, "*")) or ("unknown", "unverified")

def filing_type(fn):
    b = fn.lower()
    if "final" in b:
        return "summary"          # 30-day post-election final/summary report
    return "interim"              # pre-primary / pre-general interim statement

def is_redacted(fn):
    return "yes" if re.search(r"redact|diclosure|discloure", fn, re.I) and "redact" in fn.lower() else ("yes" if "redact" in fn.lower() else "no")

MONTHS = {m: i+1 for i, m in enumerate(
 ["january","february","march","april","may","june","july","august",
  "september","october","november","december"])}

def embedded_date(fn):
    b = fn
    # ISO 2025-09-08 (already canonical) — check first so it isn't misparsed below
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", b)
    if m:
        y, mo, d = m.groups(); return f"{y}-{mo}-{d}", "exact"
    # 9.8.2025  -> 2025-09-08
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(20\d{2})", b)
    if m:
        mo, d, y = m.groups(); return f"{y}-{int(mo):02d}-{int(d):02d}", "exact"
    # 1252019 -> 12/5/2019 ; 12-4-19
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2})\b", b)
    if m:
        mo, d, y = m.groups(); return f"20{y}-{int(mo):02d}-{int(d):02d}", "exact"
    m = re.search(r"statement-(\d)(\d{2})(20\d{2})", b)   # 1252019
    if m:
        mo1, d, y = m.groups(); return f"{y}-{int(mo1):02d}-{int(d):02d}", "exact"
    return None

def cycle_date(cycle, ft, fn):
    ed = embedded_date(fn)
    if ed:
        return ed
    b = fn.lower()
    # 2025 primary interim statements carry a statutory "Due by August 5, 2025"
    if cycle == 2025 and ft == "interim":
        return "2025-08-05", "deadline"
    if ft == "summary":
        return f"{cycle}-12-05", "cycle"          # ~30 days after Nov general
    # interim
    if "primary" in b:
        return f"{cycle}-08-15", "cycle"          # ~ 7 days before mid-Aug primary
    return f"{cycle}-10-29", "cycle"              # ~ 7 days before Nov general

# ---- text extraction / OCR ---------------------------------------------------
def pdftotext(path):
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return ""

def _tess(img, psm):
    r = subprocess.run(["tesseract", img, "-", "--psm", str(psm)],
                       capture_output=True, timeout=300)
    return r.stdout.decode("utf-8", "replace")

def _nonblank(s):
    return len(s.replace(" ", "").replace("\n", "")) >= 15

def ocr(path):
    """Render + OCR. Falls back to pdfimages extraction and OSD auto-orient (--psm 1)
    for rotated/landscape scans that psm-6 on a pdftoppm render returns blank for."""
    import tempfile, glob
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-png", path, os.path.join(td, "p")],
                       capture_output=True, timeout=300)
        pages = sorted(glob.glob(os.path.join(td, "p*.png")))
        out = [_tess(im, 6) for im in pages]
        if _nonblank("".join(out)):
            return "\n".join(out)
        # fallback 1: embedded-image extraction (handles rotated page CTMs)
        subprocess.run(["pdfimages", "-png", path, os.path.join(td, "img")],
                       capture_output=True, timeout=300)
        imgs = sorted(glob.glob(os.path.join(td, "img*.png")))
        out = [_tess(im, 6) for im in imgs]
        if _nonblank("".join(out)):
            return "\n".join(out)
        # fallback 2: OSD auto page-segmentation on the renders
        out = [_tess(im, 1) for im in pages]
        return "\n".join(out)

def extract(path):
    # corrupt/truncated capture (e.g. Internet-Archive 1-MiB crawler cap) — unreadable
    if subprocess.run(["pdfinfo", path], capture_output=True).returncode != 0:
        return "", "scanned", "unreadable:archive_capture_truncated"
    born = pdftotext(path)
    if len(born.replace(" ", "").replace("\n", "")) >= 30:
        return born, "text", "pdftotext_layout"
    return ocr(path), "scanned", "ocr:tesseract-psm6@300dpi"

# ---- election join -----------------------------------------------------------
def load_election():
    rows = {}
    with open(ELECT) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["year"]), []).append(r)
    return rows

def join(cycle, sur, elect):
    """Return (matched_election_candidate, join_confidence).

    Match on the CANONICAL surname (last token of the resolved display name), so
    OCR/clerk misspellings in the source filename (Gudmundsom/Gudmundon) still join."""
    if sur is None:
        return "", "none"
    canon = NAMES.get(sur, sur)                       # full display name
    csur = re.split(r"[^a-z]+", canon.lower())[-1]    # canonical surname token
    cands = elect.get(cycle, [])
    # election names are "FIRST [MIDDLE] LAST" -> match the LAST token (surname), so
    # STEVE TERRY vs TERRY EWING don't collide on the shared token 'terry'.
    for r in cands:
        toks = [t for t in re.split(r"[^a-z]+", r["candidate"].lower()) if t]
        if toks and toks[-1] == csur:
            return r["candidate"], "exact"
    return "", ("no_election_record" if cycle >= 2019 else "pre_floor")

# ---- build -------------------------------------------------------------------
def main():
    elect = load_election()
    rows = []
    for cycle_dir in sorted(os.listdir(RAW)):
        cdir = os.path.join(RAW, cycle_dir)
        if not os.path.isdir(cdir):
            continue
        cycle = int(cycle_dir)
        # map saved filename -> source url from fetch log (last ok record wins)
        srcmap = {}
        logp = os.path.join(cdir, "_fetch_log.jsonl")
        if os.path.exists(logp):
            for line in open(logp):
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("saved_as"):
                    srcmap[rec["saved_as"]] = rec["url"]
        os.makedirs(os.path.join(TEXT, cycle_dir), exist_ok=True)
        for fn in sorted(os.listdir(cdir)):
            if not fn.lower().endswith(".pdf"):
                continue
            path = os.path.join(cdir, fn)
            sidecar = os.path.join(TEXT, cycle_dir, fn[:-4] + ".txt")
            # cache: reuse an existing sidecar (OCR is expensive) unless --force
            if os.path.exists(sidecar) and "--force" not in sys.argv:
                head = open(sidecar).readline()
                mf = re.search(r"format=(\S+) method=(\S+)", head)
                fmt, method = (mf.group(1), mf.group(2)) if mf else ("scanned", "ocr:tesseract-psm6@300dpi")
            else:
                text, fmt, method = extract(path)
                with open(sidecar, "w") as sf:
                    sf.write(f"[format={fmt} method={method} source={fn}]\n\n")
                    sf.write(text)
            sur = surname(fn)
            cand = NAMES.get(sur, sur or "unknown")
            office, oconf = office_for(cycle, sur)
            ft = filing_type(fn)
            date, dprec = cycle_date(cycle, ft, fn)
            matched, jconf = join(cycle, sur, elect)
            src = srcmap.get(fn, "")
            arch = "wayback" if "web.archive.org" in src else ("live" if src else "")
            title = f"{cand} — {cycle} municipal campaign financial disclosure ({ft})"
            if is_redacted(fn) == "yes":
                title += " [redacted]"
            rows.append(dict(
                date=date, title=title, source_url=src, retrieved_date=RETRIEVED,
                format=fmt, extraction_method=method, candidate=cand, office=office,
                election_year=cycle, filing_type=ft,
                path=f"raw/{cycle_dir}/{fn}", matched_election_candidate=matched,
                join_confidence=jconf, office_confidence=oconf, date_precision=dprec,
                redacted=is_redacted(fn), source_archive=arch))
    rows.sort(key=lambda r: (r["election_year"], r["candidate"], r["filing_type"], r["path"]))
    # SCHEMA_SPEC §9 campaign_finance contract header first, city extras after.
    # reporting_period is not populated (period class lives in filing_type/date_precision)
    # — DictWriter restval emits it blank, per contract.
    cols = ["date","candidate","office","election_year","filing_type","reporting_period",
            "title","source_url","retrieved_date","format","extraction_method","path",
            "matched_election_candidate","join_confidence","office_confidence",
            "date_precision","redacted","source_archive"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    # join report
    scope = [r for r in rows if r["election_year"] >= 2019]
    j = sum(1 for r in scope if r["matched_election_candidate"])
    print(f"filings: {len(rows)}  (join-scope 2019+: {len(scope)}, joined: {j})")
    from collections import Counter
    print("by cycle:", dict(Counter(r["election_year"] for r in rows)))
    print("by format:", dict(Counter(r["format"] for r in rows)))
    print("unjoined 2019+:", [(r["election_year"], r["candidate"]) for r in scope
                              if not r["matched_election_candidate"]])

if __name__ == "__main__":
    main()
