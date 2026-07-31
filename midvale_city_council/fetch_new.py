#!/usr/bin/env python3
"""
Midvale incremental refresh — Revize "Document Center" (static files, NO API;
midvale.utah.gov).

Datasets:
  meeting_minutes      City Council (+ in-session RDA) minutes
  planning_commission  Planning & Zoning Commission minutes

Portal pattern (recon.md §Portal / §Planning Commission; SOURCES.md — verified at
build time 2026-07-12):
  * Council listing: a single flat Revize page listing every year in-line —
    /government/departments/recorder_s_office/agendas___minutes.php
    Minutes files live under
      Document Center/Agendas & Minutes/Recorders Office/<YEAR>/Minutes/
    named "CC Minutes <M-D-YYYY>.pdf" (recent) — plus a few flat-path
    "Document Center/Agendas & Minutes/CC Minutes <M-D-YYYY>.pdf" (no year folder)
    and SEPARATOR-LESS "CC Minutes <MDYYYY>.pdf" / .docx (2020-2023, not just
    pre-floor — see "Ambiguous separator-less dates" below).
  * PC listing: /government/departments/community_development/planning_and_zoning/
    planning___zoning_commission.php (itself the flat listing). Files under
      Document Center/Agendas & Minutes/Planning & Zoning Commission/<YEAR>/Minutes/
    named "<M.D.YY>_Minutes_APPROVED.pdf" (dot-dates, 2-digit year; sometimes
    "_w_votes").
  * All Document Center hrefs carry spaces + a literal "&" and a ?t=<token>
    cache-buster — the driver URL-encodes and uses refresh_lib.BROWSER_UA.

Ambiguous separator-less dates (the phantom-meeting trap, fixed 2026-07-31)
  Midvale files many minutes under separator-less date runs — "CC Minutes
  11723001.pdf", "11123 Approved PC Minutes.pdf", "CC Minutes 1212020.pdf".
  Those are genuinely AMBIGUOUS: 11723 reads as 1-17-23 OR 11-7-23; 11123 as
  1-11-23 OR 11-1-23; 1212020 as 1-21-2020 OR 12-1-2020. The 2026-07-12 build
  guessed the wrong branch four times and produced PHANTOM meetings — January
  sessions filed under November/December dates on which no meeting was ever
  held, double-counting the real meeting's motions (removed 2026-07-31; the
  originals are retained under each dataset's raw/_misdated/ with a README).
  This driver therefore NEVER guesses: _date_candidates() enumerates every
  calendar-valid reading, and when more than one survives the date is resolved
  from the document's OWN header text after download (_date_from_text). If the
  document can't confirm a date, the file is left RAW-ONLY and reported rather
  than indexed under a guess.

Conversion mirrors convert_minutes.py: pdftotext -layout, OCR fallback
(pdftoppm 300dpi + tesseract) for scanned PDFs, .docx via macOS textutil; each
doc gets the standard provenance header the extractor expects, filed under
<dataset>/minutes/<year>/<week-monday>/<date>_<slug>.md, source="revize".

Modes:
  --probe   (default) list minutes newer than each dataset's index max date;
            fetch nothing. Writes refresh_probe.json.
  --fetch   download new minutes -> <dataset>/raw/, convert -> .md, append
            minutes_index.csv rows (+ fetch_log.csv), then run the dataset's
            extract_votes.py + validate_votes.py.

After --fetch, rebuild the derived layers:
    python3 db/build_db.py && python3 db/build_referrals.py
    python3 build_weeks.py
"""

import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

CITY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY_DIR.parent / "scripts"))
import refresh_lib as rl  # noqa: E402

BASE = "https://www.midvale.utah.gov/"
COUNCIL_LIST = BASE + "government/departments/recorder_s_office/agendas___minutes.php"
PC_LIST = (BASE + "government/departments/community_development/"
           "planning_and_zoning/planning___zoning_commission.php")

EXCLUDE = ("agenda", "packet", "presentation", "notice", "ordinance", "resolution")
MINUTES_RE = re.compile(r"minut", re.I)

# ---------------------------------------------------------------- date parsing
# SEPARATED forms are unambiguous by construction.
YMD_RE = re.compile(r"(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})")   # 2025.12.02 / 2025-12-02
MDY_RE = re.compile(r"(\d{1,2})[.\-](\d{1,2})[.\-](20\d{2})")   # 12-2-2025 / 12.2.2025
MDYY_RE = re.compile(r"(\d{1,2})[.\-](\d{1,2})[.\-](\d{2})(?!\d)")  # 3.12.25 / 6.24.26_Minutes
# fixed-width month+day, then a space, then a 2-digit year: "0928 22 Approved PC
# Minute.pdf" / "1214 22 ...". Unambiguous because the widths are fixed.
MMDD_YY_RE = re.compile(r"(?<!\d)(\d{2})(\d{2})\s+(\d{2})(?!\d)")

# SEPARATOR-LESS runs are ambiguous — see the module docstring. A trailing "001"
# (Revize's duplicate-upload suffix, "CC Minutes 1-17-23001.pdf") is stripped so
# it can't be mistaken for date digits.
SEPLESS_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")
YEAR_DIR_RE = re.compile(r"/(20\d{2})/")
# Revize appends "001" to re-uploaded files ("CC Minutes 1-17-23001.pdf",
# "CC Minutes 1182022001.pdf") — it is NOT part of the date.
REUPLOAD_RE = re.compile(r"(?<=\d)001(?=\D|$)")

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
_MON_ALT = "|".join(MONTHS)
# In-body header dates: "JANUARY 17,2023" and "the 17th day of January 2023".
INBODY_RES = (
    (re.compile(rf"\b({_MON_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(20\d{{2}})\b", re.I),
     "mdy"),
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+day\s+of\s+({_MON_ALT})\s*,?\s*(20\d{{2}})\b",
                re.I), "dmy"),
)


def _iso(y, mo, d):
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return None


def _sepless_candidates(run, year_hint=None):
    """Every calendar-valid reading of a separator-less digit run.

    Covers YYYYMMDD / YYMMDD (leading-year) and M|MM + D|DD + YY|YYYY
    (leading-month). Returns a sorted list of distinct ISO dates.
    """
    out, n = set(), len(run)
    for ylen in (4, 2):
        for mlen in (1, 2):
            dlen = n - ylen - mlen
            if dlen not in (1, 2):
                continue
            # leading month:  MDYY / MMDDYYYY / ...
            mo, d, ytxt = int(run[:mlen]), int(run[mlen:mlen + dlen]), run[n - ylen:]
            y = int(ytxt) if ylen == 4 else 2000 + int(ytxt)
            iso = _iso(y, mo, d)
            if iso and 2000 <= y <= 2035:
                out.add(iso)
            # leading year:  YYYYMMDD / YYMMDD  (only when month+day are fixed-width)
            if mlen == 2 and dlen == 2:
                ytxt2 = run[:ylen]
                y2 = int(ytxt2) if ylen == 4 else 2000 + int(ytxt2)
                iso2 = _iso(y2, int(run[ylen:ylen + 2]), int(run[ylen + 2:ylen + 4]))
                if iso2 and 2000 <= y2 <= 2035:
                    out.add(iso2)
    if year_hint:
        narrowed = [d for d in out if d.startswith(str(year_hint))]
        if narrowed:
            return sorted(narrowed)
    return sorted(out)


def _stem_variants(name):
    """Filename stems to try, most literal first: the stem itself, the stem with
    stray space after a separator closed up ("12-11- 2024"), and each of those
    with a Revize "001" re-upload suffix stripped. Nothing is assumed correct —
    every variant that yields a reading is considered."""
    stem = re.sub(r"\.(pdf|docx?|txt)$", "", name, flags=re.I)
    out = [stem]
    for v in (re.sub(r"([.\-])\s+", r"\1", stem),):
        if v not in out:
            out.append(v)
    for v in [REUPLOAD_RE.sub("", s) for s in list(out)]:
        if v not in out:
            out.append(v)
    return out


def _date_candidates(name, year_hint=None):
    """All ISO dates `name` could denote. len()>1 means AMBIGUOUS — never guess;
    resolve from the document text (_date_from_text) after download."""
    variants = _stem_variants(name)
    for stem in variants:                        # separated forms are unambiguous
        for rx, order in ((YMD_RE, "ymd"), (MDY_RE, "mdy"), (MDYY_RE, "mdyy"),
                          (MMDD_YY_RE, "mdyy")):
            m = rx.search(stem)
            if not m:
                continue
            if order == "ymd":
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            elif order == "mdy":
                mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3)) + 2000
            iso = _iso(y, mo, d)
            if iso and 2000 <= y <= 2035:
                return [iso]
    best = []
    for stem in variants:
        for m in SEPLESS_RE.finditer(stem):
            cands = _sepless_candidates(m.group(1), year_hint)
            if cands and (not best or len(cands) < len(best)):
                best = cands
        if best:
            break
    return best


def _parse_date(name, year_hint=None):
    """The single UNAMBIGUOUS date for `name`, else None."""
    c = _date_candidates(name, year_hint)
    return c[0] if len(c) == 1 else None


def _date_from_text(text, window=1800):
    """ISO dates printed in the document's own header block, most frequent first.

    Only the header window is scanned — later prose ("approve the minutes of
    December 14, 2022") names OTHER meetings and must never re-date this one.
    """
    head, found = text[:window], []
    for rx, order in INBODY_RES:
        for m in rx.finditer(head):
            if order == "mdy":
                mo, d, y = MONTHS[m.group(1).lower()], int(m.group(2)), int(m.group(3))
            else:
                d, mo, y = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
            iso = _iso(y, mo, d)
            if iso:
                found.append(iso)
    return sorted(set(found), key=lambda x: (-found.count(x), found.index(x)))


def _abs_url(href):
    return urllib.parse.urljoin(BASE, urllib.parse.quote(href, safe="/:?=&%"))


def _hrefs(page_url):
    page = rl.http_get(page_url, ua=rl.BROWSER_UA)
    return re.findall(r'href="([^"]+)"', page)


def _candidates(page_url, path_needle):
    """(dates, basename, href) for every minutes-looking file whose decoded href
    contains `path_needle`. `dates` is the CANDIDATE list — len>1 = ambiguous."""
    out = []
    for href in _hrefs(page_url):
        dec = urllib.parse.unquote(href)
        if path_needle.lower() not in dec.lower():
            continue
        name = dec.split("/")[-1].split("?")[0]
        low = name.lower()
        if not MINUTES_RE.search(low) and "cc minutes" not in low:
            continue
        if any(x in low for x in EXCLUDE):
            continue
        yh = YEAR_DIR_RE.search(dec)
        dates = _date_candidates(name, int(yh.group(1)) if yh else None)
        if dates:
            out.append((dates, name, href))
    return out


def _new_item(dates, max_date, name, href, title, slug):
    """Probe row for a candidate set, or None if nothing in it is newer than the
    index max. Ambiguous rows carry every reading; fetch() resolves from text."""
    fresh = [d for d in dates if not max_date or d > max_date]
    if not fresh:
        return None
    return {"date": fresh[0], "title": title, "slug": slug,
            "url": _abs_url(href), "file": name,
            "date_ambiguous": len(dates) > 1, "date_candidates": dates}


def _council_kind(name):
    low = name.lower()
    if "truth" in low:
        return "City Council Truth In Taxation", "city-council-truth-in-taxation"
    if "budget" in low and "retreat" in low:
        return "City Council Budget Retreat", "city-council-budget-retreat"
    if "budget" in low:
        return "City Council Budget Meeting", "city-council-budget-meeting"
    if "legislative" in low or "breakfast" in low:
        return "City Council Legislative Breakfast", "city-council-legislative-breakfast"
    if "special" in low:
        return "City Council Special Meeting", "city-council-special-meeting"
    if "work" in low or "study" in low:
        return "City Council Work Meeting", "city-council-work-meeting"
    return "City Council Regular Meeting", "city-council-regular-meeting"


def probe_council(max_date):
    seen, new = set(), []
    # year-folder form and flat "CC Minutes" form both live off the same page
    for needle in ("Recorders Office", "Agendas & Minutes/CC Minutes"):
        for dates, name, href in _candidates(COUNCIL_LIST, needle):
            if "planning" in urllib.parse.unquote(href).lower():
                continue
            title, slug = _council_kind(name)
            it = _new_item(dates, max_date, name, href, title, slug)
            if not it:
                continue
            key = (it["date"], slug)
            if key in seen:
                continue
            seen.add(key)
            new.append(it)
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": COUNCIL_LIST,
            "notes": ("separator-less filenames are ambiguous; rows with "
                      "date_ambiguous=true are date-resolved from the document "
                      "text at --fetch time, never from the filename")}


def probe_pc(max_date):
    new, seen = [], set()
    for href in _hrefs(PC_LIST):
        dec = urllib.parse.unquote(href)
        name = dec.split("/")[-1].split("?")[0]
        low = name.lower()
        if "minute" not in low:                       # PC minutes files only
            continue
        if any(x in low for x in EXCLUDE):            # drop agenda/packet/notice/cancelled
            continue
        if "cc minutes" in low or "recorders office" in dec.lower():
            continue                                   # not a council file
        yh = YEAR_DIR_RE.search(dec)
        dates = _date_candidates(name, int(yh.group(1)) if yh else None)
        if not dates:
            continue
        slug = ("planning-commission-work-meeting" if "work" in low
                else "planning-commission-special-meeting" if "special" in low
                else "planning-commission-regular-meeting")
        it = _new_item(dates, max_date, name, href, slug.replace("-", " ").title(), slug)
        if not it or it["date"] in seen:
            continue
        seen.add(it["date"])
        # The page sets <base href="https://www.midvale.utah.gov/">, so both the
        # older full Document-Center paths and the recent BARE-RELATIVE root-level
        # minutes (e.g. '6.24.26_Minutes_Approved.pdf', served at site root)
        # resolve correctly via _abs_url. (NB: the build's stored source_url for
        # some recent bare-relative PC files points at a canonical Document-Center
        # path that 404s live — the working URL is the root-level one used here.)
        new.append(it)
    new.sort(key=lambda x: (x["date"], x["slug"]))
    return {"new_items": new, "endpoint": PC_LIST,
            "notes": ("recent PC minutes are bare-relative root-level files served "
                      "at the site root; separator-less filenames are ambiguous and "
                      "are date-resolved from the document text at --fetch time")}


# ------------------------------------------------------------- conversion

def _ocr_pdf(path):
    tmp = tempfile.mkdtemp(prefix="mvocr_")
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(path),
                        os.path.join(tmp, "pg")], capture_output=True, timeout=1200)
        out = []
        for png in sorted(glob.glob(os.path.join(tmp, "pg*.png"))):
            r = subprocess.run(["tesseract", png, "-", "--psm", "6"],
                               capture_output=True, timeout=300)
            out.append(r.stdout.decode("utf-8", "replace"))
        return "\n".join(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _get_text(raw_path):
    """Return (text, format) with format in {text, ocr}. Raises if unrecoverable."""
    if raw_path.suffix.lower() in (".docx", ".doc"):
        r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(raw_path)],
                           capture_output=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("textutil failed; convert manually")
        return r.stdout.decode("utf-8", "replace"), "text"
    txt = rl.pdf_to_text(raw_path)
    if len(re.sub(r"\s", "", txt)) >= 200:
        return txt, "text"
    otxt = _ocr_pdf(raw_path)
    if len(re.sub(r"\s", "", otxt)) < 50:
        raise RuntimeError("unrecoverable (corrupt/blank scan)")
    return otxt, "ocr"


def _body_name(dataset):
    return "Planning Commission" if dataset == "planning_commission" else "City Council"


def fetch(dataset, items):
    ds_dir = CITY_DIR / dataset
    body_name = _body_name(dataset)
    rows, n = [], 0
    for it in items:
        date, url, name, slug = it["date"], it["url"], it["file"], it["slug"]
        cands = it.get("date_candidates") or [date]
        ext = Path(name.split("?")[0]).suffix.lower().lstrip(".") or "pdf"
        blob = rl.http_get(url, binary=True, ua=rl.BROWSER_UA, referer=BASE)
        # provisional raw name; renamed below if the document re-dates itself
        raw_name = f"{date}_{slug}.{ext}"
        raw = rl.save_raw(ds_dir, raw_name, blob)
        try:
            text, fmt = _get_text(raw)
        except Exception as e:
            print(f"  RAW-ONLY {date} ({name}): {e}")
            continue
        # --- the phantom-meeting guard: the DOCUMENT dates itself, not the name
        inbody = _date_from_text(text)
        agree = [d for d in inbody if d in cands]
        if len(cands) > 1:                       # ambiguous filename: must resolve
            if not agree:
                print(f"  RAW-ONLY {name}: filename date is ambiguous {cands} and "
                      f"the document header confirms none of them "
                      f"(header dates seen: {inbody or 'none'}) — NOT indexed")
                continue
            resolved = agree[0]
        else:
            resolved = agree[0] if agree else date
            if inbody and not agree:
                print(f"  WARN {name}: filename says {date} but the document header "
                      f"says {inbody[0]} — keeping {date}; verify by hand")
        if resolved != date:
            print(f"  RE-DATED {name}: {date} -> {resolved} (from document header)")
            date = resolved
            new_raw = ds_dir / "raw" / f"{date}_{slug}.{ext}"
            raw.rename(new_raw)
            raw, raw_name = new_raw, new_raw.name
        rel = rl.minutes_rel_path(date, slug, "md", prefix="minutes")
        out = ds_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        hdr = (f"# {it['title']}\n> Body: {body_name}\n> Meeting date: {date}\n"
               f"> Source: {url}\n> Source vendor: revize\n> Raw file: raw/{raw_name}\n"
               f"> Format: {fmt}\n> Retrieved: {rl.today()}\n\n---\n\n")
        out.write_text(hdr + text, encoding="utf-8")
        rows.append({"date": date, "year": date[:4], "title": it["title"],
                     "slug": slug, "path": rel, "source": "revize",
                     "source_url": url, "format": fmt})
        n += 1
        print(f"  fetched [{fmt}] {rel}")
    rl.append_index_rows(ds_dir, rows)
    return n


def post_fetch(dataset):
    ds_dir = CITY_DIR / dataset
    rl.run_pipeline_step(["python3", "extract_votes.py"], ds_dir, f"{dataset} extract_votes")
    rl.run_pipeline_step(["python3", "validate_votes.py"], ds_dir, f"{dataset} validate_votes")


DATASETS = {
    "meeting_minutes": {
        "portal": "revize",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "meeting_minutes"),
        "probe": probe_council,
        "fetch": lambda items: fetch("meeting_minutes", items),
        "post_fetch": lambda: post_fetch("meeting_minutes"),
    },
    "planning_commission": {
        "portal": "revize",
        "baseline": lambda: rl.index_max_date(CITY_DIR / "planning_commission"),
        "probe": probe_pc,
        "fetch": lambda items: fetch("planning_commission", items),
        "post_fetch": lambda: post_fetch("planning_commission"),
    },
}

if __name__ == "__main__":
    rl.run_cli(CITY_DIR, DATASETS, "Midvale refresh (Revize Document Center)")
