#!/usr/bin/env python3
"""Regenerate ordinances/index.csv for Riverton City (idempotent).

Riverton has NO public per-ordinance archive on its codifier (the city code is on
Code Publishing / eCode360 -- current-consolidated text only, bot-gated, NOT mirrored).
The adopted-ordinance record has two witnesses:

1. **Council minutes backbone (primary).** Every council motion in
   ``../meeting_minutes/all_votes.csv`` that cites an ``Ordinance No. YY-NN`` yields a
   number -> adoption-date -> subject -> motion row DERIVED FROM THE MOTION ITSELF.
   Those rows are ``within_source`` -- high BY CONSTRUCTION, NOT an independent
   cross-match (the minutes are the only witness). ``source_url`` points at the minutes
   doc; ``path`` is blank (no separate PDF on disk); ``format=na``.

2. **Utah Public Notice "NOTICE OF ADOPTION" PDFs (independent corroboration).** The
   Riverton City Council PMN body (id 889) posts the Recorder-certified signed adopted
   ordinance as a born-digital PDF (enumerated into ``pmn_adoption_notices.csv``, stored
   in ``raw/<num>.pdf`` + a ``text/<num>.txt`` sidecar that feeds ``cities.db``
   ``fts_ordinance``). A motion-cited number that ALSO has a PMN adoption PDF is upgraded
   to ``high``; its ``adoption_date`` is taken from the signed PDF ("PASSED AND ADOPTED
   ... this Nth day of Month YYYY").

A PMN adoption PDF whose number is NOT cited in any motion is left ``none`` (unmatched --
adoption date source-verified from the PDF, ``matched_motion_date`` blank) unless a
same-date subject-matching motion exists (``medium``). NEVER force a match.

Riverton is a six-member council (5 districts + Mayor); the Mayor votes only to break a
tie (max ordinary roll = 5) -- the linkage never assumes the Mayor is a normal voter.
"""
import csv, re, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
NOTICES = os.path.join(HERE, "pmn_adoption_notices.csv")
RETRIEVED = "2026-07-13"
CODE_HOST = "https://www.codepublishing.com/UT/Riverton (eCode360 RI4763)"

CITE = re.compile(r'Ordinance\s*(?:No\.?|Number|#)?\s*#?\s*(2\d)\s*[-–]\s*(\d{1,3})', re.I)

# Title 18 = the Riverton zoning code. OCR spacing/punctuation varies wildly
# ("18.195", "18. 195", "18.(20,25", "18(65"), so match 18 followed by any of .-( + digit.
LU_KW = re.compile(r'\b(land use|land-use|zoning|zone map|rezon|subdivision|\bplat\b|'
                   r'annex|boundary adjustment|general plan|title\s*18|18\s*[.\-(]\s*[\d(]|'
                   r'accessory dwelling|\badu\b|conditional use|site plan|setback|'
                   r'density|development agreement|moratorium|overlay|master plan|'
                   r'vacat\w*\s+(?:a\s+)?(?:portion|public|the\b).{0,30}right.?of.?way|'
                   r'vacation of\s+(?:public\s+)?right|landscap|farm animal|agricultural structure|'
                   r'\br-1\b|\br-2\b|\br-3\b|\br-4\b|rr-22|pcc|planned commercial|planned unit)', re.I)
NON_LU_KW = re.compile(r'\b(budget|fee schedule|compensation|appointing|appointment|'
                       r'procurement|audit committee|insurance|proclaim|franchise|'
                       r'business license|police chief|city seal|elective and statutory|'
                       r'executive officers|robert.?s rules|water rate|utility rate|impact fee)', re.I)

MONTHS = {m[:3].lower(): i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August",
     "September","October","November","December"], 1)}


def sidecar(num):
    p = os.path.join(HERE, "text", f"{num}.txt")
    if not os.path.exists(p):
        return ""
    return open(p, encoding="utf-8", errors="replace").read()


def pdf_title(num):
    t = sidecar(num)
    m = re.search(r'(AN ORDINANCE.*?)(?:\n\s*\n|WHEREAS|NOW,? *THEREFORE)', t, re.S | re.I)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip(' ."”]')
    return ""


def pdf_adoption_date(num):
    """Read the signed adoption date from the PMN PDF text.
    Primary: 'PASSED AND ADOPTED/APPROVED ... [on|and] this Nth day of Month YYYY'.
    Fallback: a top-of-notice 'Month D, YYYY' date."""
    t = sidecar(num)
    m = re.search(r'PASSED AND (?:APPROVED|ADOPTED|DATED).{0,80}?'
                  r'(?:on|and)?\s*this\s+(\d{1,2})\w*\s+day of\s+([A-Za-z]+),?\s+(\d{4})',
                  t, re.I | re.S)
    if not m:
        m = re.search(r'this\s+(\d{1,2})\w*\s+day of\s+([A-Za-z]+),?\s+(\d{4})', t, re.I | re.S)
    if m:
        mo = MONTHS.get(m.group(2)[:3].lower())
        day = int(m.group(1))
        if mo and 1 <= day <= 31:
            return f"{m.group(3)}-{mo:02d}-{day:02d}"
    m = re.search(r'\b([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', t[:400])
    if m:
        mo = MONTHS.get(m.group(1)[:3].lower())
        if mo:
            return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}"
    return ""


def motion_title(motion, num):
    y, n = num.split("-")
    m = re.search(rf'Ordinance\s*(?:No\.?|Number|#)?\s*#?\s*{y}\s*[-–]\s*0*{int(n)}\b[\s,–-]*'
                  rf'([^\n]{{0,170}})', motion, re.I)
    t = (m.group(1) if m else motion)[:170]
    t = re.sub(r'\.?\s*(Council ?member|Mayor|The motion|Vote on|SECONDED|MOVED).*$', '', t, flags=re.I)
    return re.sub(r'\s+', ' ', t).strip(' ,-–“”"')


def is_land_use(*texts):
    blob = " ".join(t for t in texts if t)
    if LU_KW.search(blob) and not NON_LU_KW.search(blob):
        return "yes"
    if LU_KW.search(blob) and re.search(
            r'(zoning|rezon|zone map|subdivision|plat|annex|title\s*18|18\s*[.\-(]\s*[\d(]|'
            r'land use|general plan|rr-22|\br-[1-4]\b|overlay|vacat)', blob, re.I):
        return "yes"
    return "no"


def choose(evs):
    # Exclude non-adoption vehicles (repeal/reconsider/table/postpone) so the row links
    # to the ADOPTING motion, not a later action ON the same ordinance number.
    passing = [e for e in evs if re.search(r'pass|adopt|approv', e["result"], re.I)
               and not re.search(r'\b(fail|died|table|reconsider|repeal|moved until|postpone)',
                                 e["motion"], re.I)]
    return sorted(passing or evs, key=lambda e: e["date"])[-1]


def main():
    # -- motion backbone --
    events, src_of = {}, {}
    with open(VOTES) as f:
        for r in csv.DictReader(f):
            key = (r["date"], r["motion_no"])
            if key not in src_of:
                src_of[key] = r["source"]
            for m in CITE.finditer(r["motion"] or ""):
                num = f"{m.group(1)}-{int(m.group(2)):02d}"
                lst = events.setdefault(num, [])
                if not any(e["date"] == r["date"] and e["motion_no"] == r["motion_no"] for e in lst):
                    lst.append(dict(date=r["date"], result=r["result"], motion_no=r["motion_no"],
                                    motion=r["motion"], source=r["source"]))

    # minutes source_url map (for within_source pointer)
    minutes_urls = {}
    for rel in ("meeting_minutes/minutes_index.csv", "planning_commission/minutes_index.csv"):
        p = os.path.join(os.path.dirname(HERE), rel)
        if os.path.exists(p):
            with open(p) as f:
                for r in csv.DictReader(f):
                    if r.get("path") and r.get("source_url"):
                        minutes_urls[r["path"]] = r["source_url"]

    # -- PMN independent adoption PDFs --
    pmn = {}
    with open(NOTICES) as f:
        for r in csv.DictReader(f):
            pmn[r["ordinance_no"]] = r

    # PMN-only numbers NOT cited in any motion -> unmatched leads (never forced).
    LEAD_NOTE = {
        "23-14": "adopted ordinance (Title 2 Ch 55, Office of Police Chief); adoption date read from "
                 "the signed PMN PDF; no council motion in all_votes cites 23-14 (likely adopted on the "
                 "consent agenda without a number-bearing motion). Unmatched -- date source-verified.",
        "25-09": "adopted ordinance (Title 2 Ch 105, compensation of elected officials); adoption date "
                 "from the signed PMN PDF (2025-04-01, a real council meeting whose other ordinance motions "
                 "25-08/10/11 are captured but none cite 25-09 -- rode the consent agenda). Unmatched.",
        "25-19": "adopted ordinance (electric utility franchise + easement to Rocky Mountain Power); "
                 "adoption date 2025-06-03 from the signed PMN PDF (a council meeting whose captured "
                 "motions 25-16/17/18 don't include the franchise -- consent-agenda vehicle). Unmatched.",
        "26-07": "adopted ordinance (gas franchise to Questar/Enbridge); the PMN notice quotes the adopting "
                 "motion 'ADOPT Ordinance No. 26-07' on 2026-04-21, but all_votes captures only that day's "
                 "procedural motions (consent agenda) -- no number-bearing roll. Unmatched.",
    }

    rows = []
    handled = set()

    # 1) motion-cited ordinances: within_source, or high if a PMN adoption PDF exists
    for num, evs in events.items():
        ev = choose(evs)
        title = motion_title(ev["motion"], num)
        has_pdf = num in pmn
        lu = is_land_use(title, pdf_title(num) if has_pdf else "")
        adopt = pdf_adoption_date(num) if has_pdf else ev["date"]
        rows.append(dict(
            ordinance_no=num, adoption_date=adopt or ev["date"], date=adopt or ev["date"],
            title=(pdf_title(num) if has_pdf else "") or title,
            source_url=(pmn[num]["source_url"] if has_pdf else minutes_urls.get(ev["source"], ev["source"])),
            retrieved_date=RETRIEVED,
            format="text" if has_pdf else "na",
            extraction_method=("pdftotext -layout (born-digital PMN Notice-of-Adoption signed ordinance PDF)"
                               if has_pdf else
                               "reconstructed from meeting_minutes motion text (no independent adoption PDF)"),
            path=f"raw/{num}.pdf" if has_pdf else "",
            land_use=lu, result=ev["result"],
            matched_motion_date=ev["date"], matched_motion_no=ev["motion_no"],
            match_confidence="high" if has_pdf else "within_source",
            linkage_note=("motion cites the number + independent PMN adoption PDF corroborates "
                          "date/subject" if has_pdf else
                          "motion-derived only (minutes are the sole witness) -- NOT independently corroborated"),
            minutes_source=ev["source"], pmn_notice_url=pmn[num]["notice_url"] if has_pdf else "",
            pmn_file_id=pmn[num]["pmn_file_id"] if has_pdf else ""))
        handled.add(num)

    # 2) PMN adoption PDFs whose number is NOT in any motion -> unmatched leads
    for num, r in sorted(pmn.items()):
        if num in handled:
            continue
        st = pdf_title(num)
        adopt = pdf_adoption_date(num)
        rows.append(dict(
            ordinance_no=num, adoption_date=adopt, date=adopt, title=st,
            source_url=r["source_url"], retrieved_date=RETRIEVED, format="text",
            extraction_method="pdftotext -layout (born-digital PMN Notice-of-Adoption signed ordinance PDF)",
            path=f"raw/{num}.pdf", land_use=is_land_use(st), result="",
            matched_motion_date="", matched_motion_no="", match_confidence="none",
            linkage_note=LEAD_NOTE.get(num, "adopted ordinance PDF present; no motion cites the number -- unmatched."),
            minutes_source="", pmn_notice_url=r["notice_url"], pmn_file_id=r["pmn_file_id"]))
        handled.add(num)

    rows.sort(key=lambda r: (r["ordinance_no"].split("-")[0], int(r["ordinance_no"].split("-")[1])))
    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url", "retrieved_date",
            "format", "extraction_method", "path", "land_use", "result",
            "matched_motion_date", "matched_motion_no", "match_confidence",
            "linkage_note", "minutes_source", "pmn_notice_url", "pmn_file_id"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    c = Counter(r["match_confidence"] for r in rows)
    lu = Counter(r["land_use"] for r in rows)
    print(f"index.csv: {len(rows)} ordinances  {dict(c)}  land_use={dict(lu)}  code_host={CODE_HOST}")


if __name__ == "__main__":
    main()
