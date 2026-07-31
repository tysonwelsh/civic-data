#!/usr/bin/env python3
"""Build park_city_city_council/ordinances/index.csv (additive; read-only on all
existing datasets). See CLAUDE.md for the linkage method and independence caveat.

Two inputs:
  1. raw/  — signed ordinance PDFs harvested from Park City's Municode "MunicipalCodeOnline"
     public ordinance archive (S3 bucket municipalcodeonline.com-new/parkcity/ordinances/
     documents/). Born-digital; each states its number, full title, and a
     "PASSED AND ADOPTED this <day> day of <Month>, <Year>" clause — an INDEPENDENT
     adoption record. text/*.txt is pdftotext -layout of each.
  2. meeting_minutes/all_votes.csv — the audited council vote layer. Council motions cite
     "Ordinance YYYY-NN" in their text.

Output: one row per adopted ordinance (union of S3 archive numbers and minutes-cited
numbers), linked to the adopting council motion with an honest confidence tier:
  high         number appears in BOTH the S3 signed PDF AND a council motion.
  medium       S3 PDF (independent) matched to a council motion by adoption date + subject
               (no shared number restated in the motion).
  low          S3 PDF matched to a motion on the adoption date but weak subject overlap.
  within_source number known only from council motion text (no S3 PDF) — NOT corroborated.
  none         S3 signed ordinance with NO matching council vote row (audit signal).
Match fields are left EMPTY when unmatched — never forced.
"""
import csv, re, os, glob, subprocess, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
REPO = os.path.dirname(CITY)
VOTES = os.path.join(CITY, "meeting_minutes", "all_votes.csv")
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
RETRIEVED = "2026-07-05"
S3_BASE = "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/parkcity/ordinances/documents/"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}

def norm(y, n):
    return f"{int(y)}-{int(n):02d}"

def clean_motion_title(text):
    """Strip the procedural prefix from a council motion so the stored title is the
    ordinance subject (e.g. 'Council Member Joyce moved to approve Ordinance No. 2020-13,
    an ordinance approving the ...' -> 'approving the ...')."""
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"^Council Member[^,]*?\bmoved to \w+\s+"
               r"(?:the\s+)?Ordinance\s+(?:No\.?\s*)?20[12][0-9]-\d{1,3}\s*,?\s*"
               r"(?:an?\s+ordinance\s+)?", "", t, flags=re.I)
    return t.strip()[:400]

# ---- land-use classifier (informational; regex on subject) ----
LU = [
    ("zone_change", r"zoning map amend|zone (change|map)|rezone|map amendment|zoning amendment"),
    ("general_plan_amendment", r"general plan"),
    ("annexation", r"annex"),
    ("subdivision_plat", r"subdivision|\bplat\b|condominium record"),
    ("lmc_text_amendment", r"land management code|\blmc\b|amending chapter 15|title 15"),
    ("overlay_sensitive_lands", r"overlay|sensitive land|steep slope|wildland|hillside"),
    ("historic_preservation", r"historic (district|site|preservation)|historic"),
    ("housing", r"affordable housing|accessory (apartment|dwelling)|\badu\b|deed restrict|nightly rental|density"),
    ("design_review", r"design review|design standard|sign code|setback|building height"),
    ("annex_area_plan", r"area plan|master plan"),
]
def classify(subject):
    s = (subject or "").lower()
    for cat, rx in LU:
        if re.search(rx, s):
            return cat
    return ""
LANDUSE_CATS = {"zone_change","general_plan_amendment","annexation","subdivision_plat",
                "lmc_text_amendment","overlay_sensitive_lands","historic_preservation",
                "housing","design_review","annex_area_plan"}

# ---------------------------------------------------------------------------
# 1. Parse S3 signed-PDF metadata (independent archive)
# ---------------------------------------------------------------------------
def best_file(files):
    # prefer signed, prefer .pdf over .docx, prefer no "(2)"/"_1" dup marks, then largest
    def score(fn):
        s = 0
        low = fn.lower()
        if low.endswith(".pdf"): s += 100
        if "signed" in low: s += 20
        if re.search(r"\(\d\)|_\d\.pdf$", low): s -= 10
        s += os.path.getsize(os.path.join(RAW, fn)) / 1e7
        return s
    return max(files, key=score)

s3 = {}   # ord_no -> dict
by_num_files = collections.defaultdict(list)
for f in sorted(os.listdir(RAW)):
    if f.startswith("_") or f.startswith("."):
        continue
    m = re.search(r"(20[12][0-9])-(\d{1,3})", f)
    if not m:
        continue
    by_num_files[norm(m.group(1), m.group(2))].append(f)

for num, files in by_num_files.items():
    rep = best_file(files)
    tpath = os.path.join(TXT, rep.rsplit(".", 1)[0] + ".txt")
    text = open(tpath).read() if os.path.exists(tpath) else ""
    tm = re.search(r"(AN ORDINANCE.{0,400}?)(?:\n\s*\n|WHEREAS)", text, re.S | re.I)
    if tm:
        title = re.sub(r"\s+", " ", tm.group(1)).strip().rstrip(";,")
    else:
        # fallback: subject encoded in filename (strip leading epoch + number)
        base = rep.rsplit(".", 1)[0]
        base = re.sub(r"^\d+_?", "", base)
        base = re.sub(r"^20[12][0-9][-_ ]\d{1,3}[-_ ]?", "", base)
        title = base.replace("_", " ").strip()
    pa = re.search(r"PASSED\s+AND\s+ADOPTED\s+this\s+([0-9OoIilSsYy]{1,4})(?:st|nd|rd|th)?\s+day\s+of\s+"
                   r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                   r"[,\s]+(20[12][0-9])", text, re.I)
    adopt_date = ""
    if pa:
        rawday = pa.group(1)
        day = int(rawday) if rawday.isdigit() else None
        mo = MONTHS[pa.group(2).lower()]
        yr = int(pa.group(3))
        if day and 1 <= day <= 31:
            adopt_date = f"{yr:04d}-{mo:02d}-{day:02d}"
        else:
            adopt_date = f"{yr:04d}-{mo:02d}"  # day garbled; month/year only
    s3[num] = {"file": rep, "title": title[:400], "adopt_date": adopt_date,
               "pdf_month": (MONTHS[pa.group(2).lower()] if pa else None),
               "pdf_year": (int(pa.group(3)) if pa else None)}

# ---------------------------------------------------------------------------
# 2. Parse minutes: ordinance-number citations grouped by number
# ---------------------------------------------------------------------------
votes = list(csv.DictReader(open(VOTES)))
pat = re.compile(r"Ordinance\s+No\.?\s*(20[12][0-9])-(\d{1,3})|Ordinance\s+(20[12][0-9])-(\d{1,3})", re.I)

# collapse to one record per (date, motion_no)
motions = {}
for r in votes:
    key = (r["date"], r["motion_no"])
    if key not in motions:
        motions[key] = r

cited = collections.defaultdict(list)   # ord_no -> [motion record]
for (date, mno), r in motions.items():
    # The adopted ordinance is the FIRST number cited in the motion ("moved to approve
    # Ordinance No. X, an ordinance ..."); any later numbers are references to prior
    # ordinances being amended/extended and must not be attributed as adoptions.
    m = pat.search(r["motion"] or "")
    if m:
        y = m.group(1) or m.group(3); n = m.group(2) or m.group(4)
        if 2020 <= int(y) <= 2026:   # dataset window; out-of-window tokens are cross-refs
            cited[norm(y, n)].append(r)

# council meeting subject index for date+subject matching (Council body only)
council_by_date = collections.defaultdict(list)
for (date, mno), r in motions.items():
    if r["body"] == "Council":
        council_by_date[date].append(r)
all_dates = sorted(set(d for d in council_by_date))
MAX_VOTE_DATE = max(r["date"] for r in votes)

def subject_overlap(a, b):
    stop = set("the of and to a an for in on with amending amend ordinance city park approving "
               "approval an code section chapter title no of related".split())
    wa = set(w for w in re.findall(r"[a-z]{4,}", (a or "").lower()) if w not in stop)
    wb = set(w for w in re.findall(r"[a-z]{4,}", (b or "").lower()) if w not in stop)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa)

def passing(records):
    p = [r for r in records if "pass" in (r["result"] or "").lower()]
    return p or records

# ---------------------------------------------------------------------------
# 3. Merge into index rows
# ---------------------------------------------------------------------------
all_nums = sorted(set(s3) | set(cited),
                  key=lambda x: (int(x.split("-")[0]), int(x.split("-")[1])))

rows = []
for num in all_nums:
    has_pdf = num in s3
    motion_recs = cited.get(num, [])
    title = s3[num]["title"] if has_pdf else ""
    path = f"raw/{s3[num]['file']}" if has_pdf else ""
    source_url = (S3_BASE + s3[num]["file"].replace(" ", "%20")) if has_pdf else ""
    fmt = "text"  # every raw PDF is born-digital; minutes-only rows are text too
    linkage_note = ""
    matched_date = matched_no = ""
    confidence = ""
    n_events = len(motion_recs)
    minutes_source = ""

    if motion_recs:
        # number cited in >=1 council motion → use last passing motion as the adoption
        cand = passing(motion_recs)
        cand.sort(key=lambda r: r["date"])
        chosen = cand[-1]
        matched_date = chosen["date"]
        matched_no = chosen["motion_no"]
        minutes_source = chosen["source"]
        adoption_date = chosen["date"]
        if not title:
            title = clean_motion_title(chosen["motion"])
        result = chosen["result"]
        dates = sorted(set(r["date"] for r in motion_recs))
        if len(dates) > 1:
            linkage_note = f"number cited on {len(dates)} dates: {', '.join(dates)}; last passing motion chosen"
        if has_pdf:
            confidence = "high"
            source_url = S3_BASE + s3[num]["file"].replace(" ", "%20")
            # sanity: compare PDF adoption date to motion date
            pdf_d = s3[num]["adopt_date"]
            if pdf_d and len(pdf_d) == 10 and pdf_d != adoption_date:
                linkage_note = (linkage_note + "; " if linkage_note else "") + \
                    f"PDF PASSED-AND-ADOPTED date {pdf_d} vs motion {adoption_date}"
        else:
            confidence = "within_source"
            source_url = minutes_source
            linkage_note = (linkage_note + "; " if linkage_note else "") + \
                "number known only from council motion text (no independent signed PDF)"
    else:
        # S3-only: no motion restates the number. Match by PDF adoption date + subject.
        adoption_date = s3[num]["adopt_date"]
        result = ""
        pdf_full = len(adoption_date) == 10
        best = None; best_ov = 0.0
        # candidate meeting dates: exact PDF date, else any council meeting in PDF month/yr
        cand_dates = []
        if pdf_full and adoption_date in council_by_date:
            cand_dates = [adoption_date]
        if not cand_dates and s3[num]["pdf_year"]:
            ym = f"{s3[num]['pdf_year']:04d}-{s3[num]['pdf_month']:02d}"
            cand_dates = [d for d in all_dates if d.startswith(ym)]
        for d in cand_dates:
            for r in council_by_date[d]:
                ov = subject_overlap(title, r["motion"])
                if ov > best_ov:
                    best_ov, best = ov, r
        if best and best_ov >= 0.34:
            matched_date = best["date"]; matched_no = best["motion_no"]
            minutes_source = best["source"]; result = best["result"]
            confidence = "medium"
            linkage_note = f"matched to motion by adoption-date+subject (overlap {best_ov:.2f}); number not restated in motion"
            if pdf_full and best["date"] != adoption_date:
                adoption_date = best["date"]
        elif best and best_ov >= 0.20:
            matched_date = best["date"]; matched_no = best["motion_no"]
            minutes_source = best["source"]; result = best["result"]
            confidence = "low"
            linkage_note = f"weak subject overlap ({best_ov:.2f}) with motion on {best['date']}; verify before quoting"
            if pdf_full and best["date"] != adoption_date:
                adoption_date = best["date"]
        else:
            confidence = "none"
            if pdf_full and adoption_date > MAX_VOTE_DATE:
                linkage_note = (f"signed ordinance adopted {adoption_date}, which is beyond the current "
                                f"all_votes.csv coverage (ends {MAX_VOTE_DATE}) — link when votes are refreshed, "
                                f"not an extraction defect")
            elif pdf_full and adoption_date in council_by_date:
                # Adopted en bloc on the consent agenda: no ITEMIZED per-ordinance roll
                # call exists, so match fields stay empty (never forced) and the tier
                # stays `none`. But the adoption IS carried by the meeting's single
                # "approve the Consent Agenda" motion — cite it so the record points at
                # the real en-bloc vote instead of implying no vote occurred.
                consent = next((r for r in council_by_date[adoption_date]
                                if re.search(r"approve the Consent Agenda", r["motion"], re.I)), None)
                if consent:
                    linkage_note = (f"council met {adoption_date} but the ordinance is not itemized in any "
                                    f"numbered motion — adopted EN BLOC on the consent agenda by motion "
                                    f"{consent['motion_no']} (\"{consent['result']}\"), not individually rolled; "
                                    f"no separable per-ordinance roll call to link. AUDIT SIGNAL")
                else:
                    linkage_note = (f"council met {adoption_date} but the ordinance is not itemized in any numbered "
                                    f"motion (adopted on the consent agenda / not individually rolled) — no vote row "
                                    f"to link. AUDIT SIGNAL")
            else:
                linkage_note = ("signed ordinance in the independent archive with NO matching council vote row "
                                "(no number cited, no date+subject match) — AUDIT SIGNAL")
        source_url = S3_BASE + s3[num]["file"].replace(" ", "%20")

    lu_cat = classify(title)
    rows.append({
        "ordinance_no": num,
        "adoption_date": adoption_date,
        "date": adoption_date,
        "title": title,
        "source_url": source_url,
        "retrieved_date": RETRIEVED,
        "format": fmt,
        "extraction_method": ("pdftotext -layout (Municode MunicipalCodeOnline signed ordinance PDF)"
                              if has_pdf else
                              "reconstructed from meeting_minutes motion text (born-digital CivicClerk minutes)"),
        "path": path,
        "result": result,
        "land_use_category": lu_cat,
        "land_use": "yes" if lu_cat in LANDUSE_CATS else "no",
        "matched_motion_date": matched_date,
        "matched_motion_no": matched_no,
        "match_confidence": confidence,
        "n_motion_events": n_events,
        "has_signed_pdf": "yes" if has_pdf else "no",
        "linkage_note": linkage_note,
        "minutes_source": minutes_source,
    })

# SCHEMA_SPEC §9 ordinances contract header first, city extras after
cols = ["ordinance_no","adoption_date","date","title","source_url","retrieved_date","format",
        "extraction_method","path","land_use","result","matched_motion_date",
        "matched_motion_no","match_confidence","land_use_category","n_motion_events",
        "has_signed_pdf","linkage_note","minutes_source"]
with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ---- summary to stdout ----
conf = collections.Counter(r["match_confidence"] for r in rows)
lu = sum(1 for r in rows if r["land_use"] == "yes")
print(f"rows: {len(rows)}  land-use: {lu}")
print("confidence:", dict(conf))
print("signed PDFs (independent):", sum(1 for r in rows if r["has_signed_pdf"] == "yes"))
print("NONE (adopted ord, no vote row):",
      [r["ordinance_no"] for r in rows if r["match_confidence"] == "none"])
