#!/usr/bin/env python3
"""Regenerate ordinances/index.csv for Bluffdale.

Linkage method (see CLAUDE.md): the council MINUTES are the backbone. Every
council motion that cites an ``Ordinance <YYYY-NN>`` (regex tolerant of
``No.``/``Number``/``#`` and the no-space form) yields a number -> adoption-date
-> subject -> motion row DERIVED FROM THE MOTION ITSELF. Those rows are
``within_source`` (high BY CONSTRUCTION, NOT an independent cross-match).

Independent corroboration = the city's Municipal Code Online public S3 archive
of signed adopted-ordinance PDFs
(s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/bluffdale/ordinances/documents/).
A motion-cited number that ALSO has an adopted PDF in that archive is upgraded to
``high``. Archived 2020+ ordinances NOT cited in any motion are matched by
adoption-date + subject where possible (``medium``) or left unmatched (``none``)
- these are FLAGGED extraction leads, never forced.

Regenerates from: archive_backcatalog.csv (the S3 enumeration) +
../meeting_minutes/all_votes.csv + the text/ sidecars. Idempotent.
"""
import csv, re, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
BACKCAT = os.path.join(HERE, "archive_backcatalog.csv")
RETRIEVED = "2026-07-12"

# scanned (OCR'd) vs born-digital, from extraction pass
SCANNED = set("2023-20 2023-22 2023-24 2023-26 2024-05 2024-08 2024-09 2024-10 "
              "2024-19 2024-20 2024-21 2025-19 2025-20 2025-24 2025-25 2025-26 "
              "2025-27 2025-28 2026-01 2026-03 2026-05".split())

CITE = re.compile(r'Ordinance\s*(?:No\.?|Number|#)?\s*#?\s*(20\d{2})\s*[-–]\s*(\d{1,3})', re.I)

LU_KW = re.compile(r'\b(land use|land-use|zoning|zone\b|rezone|subdivision|\bplat\b|'
                   r'annex|boundary adjustment|common municipal boundary|general plan|'
                   r'title 11|accessory dwelling|\badu\b|permitted.{0,15}use|conditional use|'
                   r'site plan|setback|density|development agreement|moratorium|'
                   r'sd-x|sd-c|gw-r|gateway|overlay|11\.\d)', re.I)
NON_LU_KW = re.compile(r'\b(budget|fee schedule|appointing|appointment|procurement|'
                       r'audit committee|health insurance|proclaim|religious freedom|'
                       r'robert.?s rules|interference with an employee|business license)', re.I)


def load_minutes_urls():
    """minutes md path -> the city ViewFile source_url (for within_source rows, whose
    only source IS the minutes doc that cites the ordinance number). §9 requires a
    non-empty source_url; the minutes doc is the honest, correct pointer."""
    m = {}
    for rel in ("meeting_minutes/minutes_index.csv", "planning_commission/minutes_index.csv"):
        p = os.path.join(os.path.dirname(HERE), rel)
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for r in csv.DictReader(f):
                if r.get("path") and r.get("source_url"):
                    m[r["path"]] = r["source_url"]
    return m


def load_backcatalog():
    """number -> (latest source_url, subject-from-sidecar)."""
    best = {}
    with open(BACKCAT) as f:
        for r in csv.DictReader(f):
            num = r["ordinance_no"]
            if not num:
                continue
            lm = r["last_modified"]
            if num not in best or lm > best[num][0]:
                best[num] = (lm, r["source_url"])
    return {n: v[1] for n, v in best.items()}


def sidecar_title(num):
    p = os.path.join(HERE, "text", f"{num}.txt")
    if not os.path.exists(p):
        return ""
    t = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r'AN ORDINANCE[^\n]{0,140}', t)
    if m:
        return re.sub(r'\s+', ' ', m.group(0)).strip()
    return ""


def motion_title(motion, num):
    """Extract the ordinance subject from motion text after the cited number."""
    y, n = num.split("-")
    m = re.search(rf'Ordinance\s*(?:No\.?|Number|#)?\s*#?\s*{y}\s*[-–]\s*0*{int(n)}\b[\s,–-]*([^\n]{{0,160}})', motion, re.I)
    t = (m.group(1) if m else motion)[:160]
    t = re.sub(r'\.?\s*(Council Member|Board Member|The motion|Vote on).*$', '', t, flags=re.I)
    return re.sub(r'\s+', ' ', t).strip(" ,-–")


def is_land_use(*texts):
    blob = " ".join(t for t in texts if t)
    if LU_KW.search(blob) and not NON_LU_KW.search(blob):
        return "yes"
    if LU_KW.search(blob):
        # both matched -> favor land-use only if a strong land-use token present
        if re.search(r'\b(zoning|rezone|subdivision|plat|annex|title 11|11\.\d|land use|sd-x|gateway)\b', blob, re.I):
            return "yes"
    return "no"


def main():
    # backbone: cited number -> list of motion events
    events = {}
    src_of = {}
    with open(VOTES) as f:
        for r in csv.DictReader(f):
            key = (r["date"], r["motion_no"])
            if key in src_of:
                continue
            src_of[key] = r["source"]
            for m in CITE.finditer(r["motion"] or ""):
                num = f"{m.group(1)}-{int(m.group(2)):02d}"
                events.setdefault(num, []).append(
                    dict(date=r["date"], result=r["result"], motion_no=r["motion_no"],
                         motion=r["motion"], source=r["source"]))

    archive = load_backcatalog()
    minutes_urls = load_minutes_urls()

    # ---- reconcile the 2013-14 typo: motion cites "2013-14" but the adopted
    #      ordinance (subject "Interference with an Employee") is 2023-14. ----
    typo_events = events.pop("2013-14", [])

    rows = []

    def choose(evs):
        passing = [e for e in evs if re.search(r'pass|adopt|approv', e["result"], re.I)
                   and not re.search(r'fail|died', e["result"], re.I)]
        return sorted(passing or evs, key=lambda e: e["date"])[-1]

    handled = set()

    # 1) motion-cited ordinances (within_source or high)
    for num, evs in events.items():
        ev = choose(evs)
        title = motion_title(ev["motion"], num)
        in_arch = num in archive
        lu = is_land_use(title, sidecar_title(num) if in_arch else "")
        row = dict(
            ordinance_no=num, adoption_date=ev["date"], date=ev["date"],
            title=title or sidecar_title(num),
            source_url=(archive.get(num, "") if in_arch
                        else minutes_urls.get(ev["source"], "")),
            retrieved_date=RETRIEVED,
            format=("scanned" if num in SCANNED else "text") if in_arch else "na",
            extraction_method=(
                "tesseract OCR (scanned signed ordinance PDF, Municipal Code Online archive)"
                if in_arch and num in SCANNED else
                "pdftotext -layout (born-digital adopted ordinance PDF, Municipal Code Online archive)"
                if in_arch else
                "reconstructed from meeting_minutes motion text (no independent PDF in archive)"),
            path=f"raw/archive/{num}.pdf" if in_arch else "",
            land_use=lu, result=ev["result"],
            matched_motion_date=ev["date"], matched_motion_no=ev["motion_no"],
            match_confidence="high" if in_arch else "within_source",
            linkage_note="", minutes_source=ev["source"],
        )
        rows.append(row)
        handled.add(num)

    # 2) the 2013-14->2023-14 typo reconciliation (high)
    if typo_events:
        ev = choose(typo_events)
        rows.append(dict(
            ordinance_no="2023-14", adoption_date=ev["date"], date=ev["date"],
            title=sidecar_title("2023-14") or "AN ORDINANCE AMENDING SECTION 5.10 (Interference with an Employee)",
            source_url=archive.get("2023-14", ""), retrieved_date=RETRIEVED,
            format="text", extraction_method="pdftotext -layout (born-digital adopted ordinance PDF, Municipal Code Online archive)",
            path="raw/archive/2023-14.pdf", land_use="no", result=ev["result"],
            matched_motion_date=ev["date"], matched_motion_no=ev["motion_no"],
            match_confidence="high",
            linkage_note=("motion text mis-cites the number as 'Ordinance 2013-14'; the adopted "
                          "ordinance is 2023-14 (subject 'Interference with an Employee' is identical). "
                          "The 2013-14 archive PDF is a different (2013 land-use) ordinance, pre-floor."),
            minutes_source=ev["source"]))
        handled.add("2023-14")

    # 3) archive-only 2020+ ordinances NOT cited in any motion (medium / none leads)
    # Manually curated per lead after cross-checking the minutes (see CLAUDE.md).
    LEADS = {
        # num: (match_conf, matched_motion_date, matched_motion_no, note)
        "2023-30": ("medium", "2023-12-13", "6",
            "codified as Ordinance 2023-30 (amending Title 2 Boards & Commissions); the minutes "
            "adopt it on 2023-12-13 as 'Resolution 2023-30 - Audit Committee Organization' "
            "(instrument-word differs; number+date+subject agree)."),
        "2024-23": ("medium", "2024-10-09", "5",
            "codified as Ordinance 2024-23 (amending Title 2.70 Audit Committee); the minutes "
            "adopt it on 2024-10-09 as 'Resolution 2024-23 - Amending Title...' "
            "(instrument-word differs; number+date+subject agree)."),
        "2024-20": ("medium", "2024-09-11", "",
            "adopted ordinance (amends BCC 11.30.060, land use); signature page dated 2024-09-11, a "
            "council meeting with land-use ordinance motions (2024-18/19/21) but NO motion cites "
            "2024-20 - date+subject match only. LEAD: 2024-18 that day also amends 11.30.060."),
        "2020-01": ("none", "2020-01-29", "",
            "adopted ordinance (procurement, Title 1 Ch 10); adoption date 2020-01-29 read from the "
            "signed PDF signature page ('PASSED AND ADOPTED: January 29, 2020', Read-tool 2026-07-13); "
            "no council motion in all_votes cites 2020-01. LEAD: unmatched (date is source-verified, "
            "not motion-linked)."),
        "2020-06": ("none", "2020-03-11", "",
            "adopted ordinance (Signs/Outdoor Advertising amendment, LAND USE); adoption date 2020-03-11 "
            "read from the signed PDF ('PASSED AND DATED: March 11, 2020', Read-tool 2026-07-13) whose "
            "signature page shows a full 5-0 Aye roll (Aston/Crockett/Gaston/Hales/Kallas); no council "
            "motion in all_votes cites 2020-06. LEAD: real adopted land-use ordinance whose minutes "
            "motion omitted the number - EXTRACTION lead."),
        "2023-29": ("none", "2023-12-13", "",
            "adopted ordinance (common municipal boundary adjustment with Draper, LAND USE); adoption "
            "date 2023-12-13 = the council meeting whose agenda item 8.2 was 'Consideration and Vote on "
            "Ordinance 2023-29' (minutes council_2023-12-13_1320.md), matching the signed ordinance's "
            "'December 2023' (surveyor plat 30 Nov 2023); no vote motion captured the number. LEAD: "
            "real adopted land-use ordinance - EXTRACTION lead."),
        "2025-17": ("none", "2025-06-11", "",
            "adopted ordinance (BCC 2.50.010, term of Healthy Bluffdale Coalition); adoption date "
            "2025-06-11 from the signed PDF ('PASSED AND APPROVED: June 11, 2025'); only the "
            "minutes-approval motion was extracted that day - no ordinance motion cites 2025-17. "
            "LEAD: unmatched / possible extraction gap."),
    }
    for num, (conf, mdate, mno, note) in LEADS.items():
        if num in handled:
            continue
        st = sidecar_title(num)
        rows.append(dict(
            ordinance_no=num, adoption_date=mdate, date=mdate, title=st,
            source_url=archive.get(num, ""), retrieved_date=RETRIEVED,
            format="scanned" if num in SCANNED else "text",
            extraction_method=("tesseract OCR (scanned signed ordinance PDF, Municipal Code Online archive)"
                               if num in SCANNED else
                               "pdftotext -layout (born-digital adopted ordinance PDF, Municipal Code Online archive)"),
            path=f"raw/archive/{num}.pdf", land_use=is_land_use(st),
            result="",
            matched_motion_date=("" if conf == "none" else mdate), matched_motion_no=mno,
            match_confidence=conf, linkage_note=note, minutes_source=""))
        handled.add(num)

    rows.sort(key=lambda r: r["ordinance_no"])
    cols = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no", "match_confidence",
            "linkage_note", "minutes_source"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    from collections import Counter
    c = Counter(r["match_confidence"] for r in rows)
    lu = Counter(r["land_use"] for r in rows)
    print(f"index.csv: {len(rows)} ordinances  {dict(c)}  land_use={dict(lu)}")


if __name__ == "__main__":
    main()
