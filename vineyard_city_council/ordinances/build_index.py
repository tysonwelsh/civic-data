#!/usr/bin/env python3
"""Build Vineyard adopted-ordinance index from motion-text citations (backbone) +
independent PMN signed-ordinance PDFs (corroboration). Additive; reads only."""
import csv, re, os, json
from collections import defaultdict

CITY = "/Users/tysonwelsh/civic-data/vineyard_city_council"
OUT = os.path.join(CITY, "ordinances", "index.csv")
RETRIEVED = "2026-07-05"

# space/dash-tolerant ordinance-number matcher (handles "2021- 08")
NUM = re.compile(r'ordinance\s*(?:no\.?|number|#)?\s*:?\s*(20\d{2})\s*[-–]\s*(\d{1,3})', re.I)
PASS_RE = re.compile(r'carr|pass|approv|adopt', re.I)
FAIL_RE = re.compile(r'fail|denied|reject|table|continu|postpon', re.I)

def norm(y, n): return f"{y}-{int(n):02d}"

# ---- documented source-typo corrections (linkage layer only) ----
# The city-faithful motion text in all_votes.csv is NEVER edited: the verbatim
# "APPROVE ORDINANCE 2021-02" row on 2021-09-08 stays exactly as the clerk printed it.
# But that 2021-09-08 item-9.3 motion is a clerk TYPO — the agenda item header reads
# "(Ordinance 2021-12)", the subject is Chapter 2.30 Commissions, and the signed PMN
# ordinance PDF (file 758099) is "PASSED AND ADOPTED ... SEPTEMBER 08, 2021" as
# Ordinance 2021-12. So for LINKAGE we re-key that one motion event from the mistyped
# "2021-02" to the true "2021-12". This removes the false 2021-09-08 event from Ord
# 2021-02 (whose real, distinct adoption is 2021-02-10 #4, ZTA 15.34.100 Parking) and
# supplies Ord 2021-12 its adopting-motion match (previously the dataset's lone "none").
MOTION_ORD_OVERRIDE = {
    # (source_file all_votes date, motion_no, body): corrected ordinance_no
    ("2021-09-08", "4", "Council"): "2021-12",
}
OVERRIDE_NOTE = {
    "2021-12": (" SOURCE-TYPO OVERRIDE: the 2021-09-08 item-9.3 adopting motion prints "
                "\"APPROVE ORDINANCE 2021-02\" (clerk typo); the agenda item header reads "
                "\"(Ordinance 2021-12)\" and the signed PMN PDF is ADOPTED 2021-09-08 for "
                "Chapter 2.30 Commissions. Re-keyed here for linkage only — the verbatim "
                "motion text in all_votes.csv is unchanged."),
}

# ---- 1. backbone: ordinance numbers cited in motion text ----
events = defaultdict(list)   # ordno -> list of dict(date,motion_no,body,result,motion,source)
for path, body in [("meeting_minutes/all_votes.csv", "Council"),
                   ("planning_commission/all_votes.csv", "PlanningCommission")]:
    fp = os.path.join(CITY, path)
    if not os.path.exists(fp): continue
    with open(fp) as f:
        motseen = set()
        for row in csv.DictReader(f):
            m = NUM.search(row["motion"] or "")
            if not m: continue
            ordno = norm(m.group(1), m.group(2))
            ordno = MOTION_ORD_OVERRIDE.get((row["date"], row["motion_no"], body), ordno)
            key = (ordno, row["date"], row["motion_no"], body)
            if key in motseen: continue
            motseen.add(key)
            events[ordno].append(dict(date=row["date"], motion_no=row["motion_no"],
                                      body=body, result=row["result"],
                                      motion=row["motion"], source=row["source"]))

# ---- 2. independent PMN signed ordinance PDFs ----
PMN = {  # ordno -> (fileid, filename, adoption_date, title, land_use)
 "2021-07": ("748935","ORD_2021-07_ZC_Amend_Swimming_Pools.pdf","2021-08-11",
   "AN ORDINANCE OF THE CITY OF VINEYARD UTAH AMENDING THE VINEYARD ZONING ORDINANCE SECTION 15.34.030 'ACCESSORY BUILDINGS'","yes"),
 "2021-09": ("748941","ORD_2021-09_MC_Amend_City_Manager_Duties.pdf","2021-08-11",
   "AN ORDINANCE OF THE VINEYARD CITY COUNCIL AMENDING MUNICIPAL CODE 2.08.020 CITY MANAGER; POWERS AND DUTIES; OBLIGATIONS","no"),
 "2021-10": ("748943","ORD_2021-10_MC_Amend_Election_Code.pdf","2021-08-11",
   "AN ORDINANCE OF THE VINEYARD CITY COUNCIL AMENDING THE VINEYARD MUNICIPAL CODE CHAPTER 2.14 ELECTIONS","no"),
 "2021-11": ("753599","ORD_2021-11_SC_Amend_Subdivision_Applications.pdf","2021-08-25",
   "AN ORDINANCE OF THE CITY OF VINEYARD UTAH AMENDING THE VINEYARD SUBDIVISION CODE SECTION 14.06.020 AND SECTION 14.08.030","yes"),
 "2021-12": ("758099","ORD_2021-12_MC_Amend_Admin_Commissions_Committees.pdf","2021-09-08",
   "AN ORDINANCE OF THE VINEYARD CITY, UTAH ADOPTING CHAPTER 2.30 OF THE CITY'S MUNICIPAL CODE RELATING TO COMMITTEES AND COMMISSION","no"),
}
PMN_URL = "https://www.utah.gov/pmn/files/{}.pdf"

# ---- land-use classifier on subject text ----
def classify(text):
    t = (text or "").lower()
    rules = [
        ("zone_change", r'\bzone change\b|\bzoning map\b|\brezone|\bzone map|map amendment|\bfrom .* to .*(zone|residential|commercial)'),
        ("zoning_text_amendment", r'zoning ordinance|zoning code|title 15|land use code|development code|\bsetback|accessory building|overlay'),
        ("general_plan_amendment", r'general plan|land use map|future land use'),
        ("subdivision", r'subdivision'),
        ("annexation", r'annex'),
        ("development_agreement", r'development agreement|master development'),
        ("plat", r'\bplat\b'),
        ("impact_fee", r'impact fee'),
    ]
    for cat, rx in rules:
        if re.search(rx, t): return cat
    return ""
LU_CATS = {"zone_change","zoning_text_amendment","general_plan_amendment","subdivision",
           "annexation","development_agreement","plat"}

# ---- choose adopting motion per ordinance ----
def pick_adoption(evs):
    council = [e for e in evs if e["body"] == "Council"]
    pool = council if council else evs
    passing = [e for e in pool if PASS_RE.search(e["result"] or "") and not
               (FAIL_RE.search(e["result"] or "") and not PASS_RE.search(e["result"] or ""))]
    passing = [e for e in pool if PASS_RE.search(e["result"] or "")]
    chosen_pool = passing if passing else pool
    chosen = sorted(chosen_pool, key=lambda e: (e["date"], int(e["motion_no"]) if e["motion_no"].isdigit() else 0))[-1]
    return chosen

allnos = set(events) | set(PMN)
rows = []
for ordno in sorted(allnos):
    evs = events.get(ordno, [])
    pmn = PMN.get(ordno)
    matched_date = matched_no = ""; minutes_source = ""; result = ""; conf = "none"
    n_ev = len(evs); note = ""
    if evs:
        adopt = pick_adoption(evs)
        matched_date = adopt["date"]; matched_no = adopt["motion_no"]
        minutes_source = adopt["source"]; result = adopt["result"]
        dates = sorted({e["date"] for e in evs})
        if len(dates) > 1:
            note = "cited in motions on multiple dates: " + "; ".join(
                f"{e['date']} #{e['motion_no']} ({e['body']}, {e['result']})" for e in
                sorted(evs, key=lambda e:(e["date"],e["motion_no"])))
    # confidence
    if pmn and evs:
        conf = "high"; note = ("independently corroborated by signed ordinance PDF on Utah Public "
                               "Notice (body 530) AND matched to council motion. " + note).strip()
    elif pmn and not evs:
        conf = "none"
        note = ("ADOPTED ordinance present as signed PDF on Utah Public Notice (body 530), adopted "
                f"{pmn[2]} per the PDF, but NO council vote row in all_votes.csv cites this number "
                "(consent-agenda item / number not restated in a recorded motion) -> AUDIT SIGNAL.")
    elif evs:
        conf = "within_source"
        note = (("derived from council/PC motion text only; no independent archive retrieved. " + note)
                if note else "derived from council/PC motion text only; no independent archive retrieved.")
    # flag rows whose chosen motion did not pass (number may not have been adopted)
    if evs and result and (not PASS_RE.search(result) or FAIL_RE.search(result)):
        adopting = [e for e in evs if e["body"] == "Council" and PASS_RE.search(e["result"] or "")]
        if not adopting:
            note += (" NOTE: no PASSING council adoption motion cites this number "
                     "(chosen motion is a non-adopting/negative action) -> NOT confirmed adopted "
                     "in the vote record.")
    # documented source-typo linkage note (appended after confidence note is set)
    if ordno in OVERRIDE_NOTE:
        note = (note + OVERRIDE_NOTE[ordno]).strip()
    # richest motion text across all events (PC rec often carries the full subject)
    richest = max((e["motion"] for e in evs), key=len) if evs else ""
    all_text = " ".join(e["motion"] for e in evs)
    # title
    if pmn:
        title = pmn[3]
    else:
        title = re.sub(r'\s+', ' ', richest).strip()
    # land use
    if pmn:
        land_use = pmn[4]; cat = classify(pmn[3]) or ("zoning_text_amendment" if pmn[4]=="yes" else "")
    else:
        cat = classify(all_text); land_use = "yes" if cat in LU_CATS else "no"
    # source_url / path / format / extraction
    if pmn:
        source_url = PMN_URL.format(pmn[0]); path = "raw/" + pmn[1]
        fmt = "text"; extraction = "pdftotext -layout (Utah Public Notice signed ordinance PDF)"
        date = pmn[2]; adoption_date = pmn[2]
    else:
        source_url = minutes_source; path = ""
        fmt = "text"; extraction = "reconstructed from meeting_minutes/planning_commission motion text (CivicClerk minutes)"
        date = matched_date; adoption_date = matched_date
    rows.append(dict(ordinance_no=ordno, adoption_date=adoption_date, date=date, title=title,
        source_url=source_url, retrieved_date=RETRIEVED, format=fmt, extraction_method=extraction,
        path=path, result=result, land_use_category=cat, land_use=land_use,
        matched_motion_date=matched_date, matched_motion_no=matched_no,
        match_confidence=conf, n_motion_events=n_ev, linkage_note=note, minutes_source=minutes_source))

# SCHEMA_SPEC §9 ordinances contract header first, city extras after
cols = ["ordinance_no","adoption_date","date","title","source_url","retrieved_date","format",
        "extraction_method","path","land_use","result","matched_motion_date",
        "matched_motion_no","match_confidence","land_use_category","n_motion_events",
        "linkage_note","minutes_source"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow(r)

from collections import Counter
c = Counter(r["match_confidence"] for r in rows)
lu = sum(1 for r in rows if r["land_use"] == "yes")
print("total ordinances:", len(rows))
print("confidence:", dict(c))
print("land_use yes:", lu)
print("none rows (audit signals):", [r["ordinance_no"] for r in rows if r["match_confidence"]=="none"])
