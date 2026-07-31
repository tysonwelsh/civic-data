#!/usr/bin/env python3
"""Regenerate ordinances/index.csv for Herriman. Idempotent, no network.

Three evidence sources, merged per normalized ordinance number (YYYY-NN):

1. **Municipal Code Online public S3 archive** (independent, full signed text):
   s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/herriman/ordinances/documents/
   enumerated verbatim into ``archive_backcatalog.csv``; latest upload per number
   stored as ``raw/archive/<num>.pdf`` with a ``text/<num>.txt`` sidecar.
2. **Utah Public Notice (PMN) Recorder adoption notices** (independent, summary +
   authoritative adoption-meeting date): bodies 1287 "Public Hearings and Notices"
   and 1155 "City Council" (entity 155). HTML notice pages retained verbatim in
   ``raw/pmn/notice_<id>.html`` (catalog: ``pmn_notices.csv``); no PDF attachments
   exist on Herriman's PMN notices. Sidecars ``text/notice_<id>.txt``.
3. **Council minutes backbone** (../meeting_minutes/all_votes.csv): motions citing
   an ordinance number (both grammars: ``Ordinance No. 2020-07`` and the early-2020
   ``01-2020`` form). Rows witnessed ONLY here are ``within_source`` — high by
   construction, NOT independently corroborated.

Confidence (see CLAUDE.md): high = independent doc + motion citing the number with
date agreement; medium = independent doc + same-date subject match (number not in
motion); low = independent doc + date-only; none = independent doc, unmatched
(incl. everything below the 2020 vote floor); within_source = motion-derived only.
Never forced.
"""
import csv, glob, html, os, re
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
RETRIEVED = "2026-07-13"

CONTRACT = ["ordinance_no", "adoption_date", "date", "title", "source_url",
            "retrieved_date", "format", "extraction_method", "path", "land_use",
            "result", "matched_motion_date", "matched_motion_no", "match_confidence"]
EXTRAS = ["pmn_notice_id", "pmn_notice_url", "adoption_date_source", "case_no",
          "linkage_note", "minutes_source"]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

# ---------- number normalization (three grammars across the record) ----------
def norm_num(a, b):
    """Return YYYY-NN from any of (YYYY,NN) (NN,YYYY) (YY,NN)."""
    a, b = a.strip(), b.strip()
    if len(a) == 4 and a.startswith("20"):
        return f"{a}-{int(b):02d}"
    if len(b) == 4 and b.startswith("20"):
        return f"{b}-{int(a):02d}"
    if len(a) == 2 and a.isdigit() and int(a) >= 7:          # 14-25 -> 2014-25
        return f"20{a}-{int(b):02d}"
    return None

# ---------- land-use classifier ----------
LU_KW = re.compile(
    r"\b(land.?use|zoning|zone\b|rezone|rezoning|subdivision|\bplat\b|annex|"
    r"general plan|master development agreement|development agreement|"
    r"development code|title 10\b|10-\d{1,2}\b|accessory dwelling|\badu\b|"
    r"conditional use|site plan|setback|density|overlay|moratorium|"
    r"open space|sensitive land|billboard|signs? ordinance|water efficiency "
    r"standards|planned development|heliport|land development)", re.I)
NON_LU_KW = re.compile(
    r"\b(budget|rate of tax|levying taxes|fee schedule|fireworks|cemetery|"
    r"animal|parking (permit|violation)|compensation|salary|election|"
    r"procurement|surplus propert|alcohol|business licens|court|franchise|"
    r"garbage|solid waste|emergency (management|operations))", re.I)

def classify_lu(text):
    if not text:
        return ""
    if LU_KW.search(text):
        return "yes"
    return "no"

# ---------- 1. archive backcatalog ----------
def load_archive():
    out = {}
    with open(os.path.join(HERE, "archive_backcatalog.csv")) as f:
        for r in csv.DictReader(f):
            n = r["ordinance_no"]
            # latest upload per number is the stored one
            if n not in out or r["filename"] > out[n]["filename"]:
                out[n] = r
    return out

# ---------- 2. PMN notices ----------
NOTICE_DATE = re.compile(
    r"meet-?\s*ing held on\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})", re.I)
# CRA project-area adoption notices: "On May 22, 2019, pursuant to ..."
NOTICE_DATE_CRA = re.compile(r"\bOn\s+(\w+)\s+(\d{1,2}),\s+(\d{4}),", re.I)
# "No." is optional ("Ordinance 2022-43 M2022-108"); the trailing lookahead
# rejects code-section references like "Ordinance 10-20-9".
NOTICE_ORD = re.compile(
    r"Ordinance\s+(?:Nos?\.?\s*)?#?\s*(\d{1,4})\s*[-–]\s*(\d{1,4})(?!\s*[-–]?\d)", re.I)
# Recorder mis-prints, mapped by hand with the evidence spelled out (see
# CLAUDE.md; the verbatim notices stay untouched in raw/):
NOTICE_NUM_OVERRIDES = {
    # prints only the zoning case "Z2022-116"; the signed archive PDF for that
    # case is ORD 2022-40 (AutomallSpecialDistrictTitle).
    "796087": "2022-40",
    # fireworks-ban notice (adopted 2021-04-28) prints "2021-10"; the 2021-04-28
    # motion #5 adopts "ordinance 2021-11" with the identical subject, and
    # 2021-10 (Title 6 fee schedule) was adopted 2021-04-14 - number typo.
    "675239": "2021-11",
    # annexation notice (adopted 2023-03-08) prints "2022-06"; the 2023-03-08
    # motion #8 adopts "Ordinance No. 2023-06" with the identical subject, and
    # 2022-06 (warehouses/churches, Z2021-124) was adopted 2022-02-23.
    "819153": "2023-06",
}
# Notices whose printed meeting date is a demonstrable typo. The 8460xx batch
# prints "July 12, 2022" for 2023-series ordinances: posted 2023-07-14, and the
# 2023-07-12 council meeting's motions #10/#11 cite 2023-13/2023-14 with the
# identical subjects. 1080729 prints "May 14, 2026" (a Thursday); the identical-
# subject motion is 2026-05-13 #7 (the regular 2nd-Wednesday meeting).
NOTICE_DATE_OVERRIDES = {
    "846044": ("2023-07-12", "year typo"),
    "846052": ("2023-07-12", "year typo"),
    "846056": ("2023-07-12", "year typo"),
    "1080729": ("2026-05-13", "off-by-one-day typo"),
}
# Minutes typos: remapped citations stay MEDIUM (the motion does not print the
# corrected number).
# Pre-2020 archive PDFs whose adoption clause didn't parse; dates read from the
# document by hand (Read/grep, 2026-07-13). 2019-20's PDF is the storm-water
# rate-study exhibit with an UNEXECUTED signature block - only the cover month
# is printed, so the date is honestly month-granular.
MANUAL_DATES = {
    "2018-37": ("2018-11-14", "pdf-recital (WHEREAS: City Council public meeting on November 14, 2018)"),
    "2018-38": ("2018-11-14", "pdf-recital (WHEREAS: met in regular session on November 14, 2018)"),
    "2019-20": ("2019-07", "pdf-cover (month only; PDF is the rate-study exhibit, signature block unexecuted)"),
}

CITE_REMAPS = {
    # motion prints "Ordinance Number 2025-18" but its subject (wireless
    # telecommunication facilities, Title 10) is the signed archive PDF ORD
    # 2025-17; the real 2025-18 (Lifetime Fitness MDA) is cited as "18-2025"
    # by motion 2025-08-27 #6.
    ("2025-08-13", "14"): ("2025-18", "2025-17"),
    # motion prints "Ordinance 2023-05" but its subject (Cemetery Rules and
    # Regulations amendment) is the signed archive PDF ORD 2023_08; the real
    # 2023-05 (Transportation Master Plan) was adopted 2023-03-08 #5.
    ("2023-04-12", "3"): ("2023-05", "2023-08"),
}

def strip_html(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def load_notices():
    """Return {num: [ {notice_id, meeting_date, subject} ]}."""
    cat = {}
    with open(os.path.join(HERE, "pmn_notices.csv")) as f:
        for r in csv.DictReader(f):
            cat[r["notice_id"]] = r
    out, unparsed = {}, []
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", "pmn", "notice_*.html"))):
        nid = re.search(r"notice_(\d+)\.html", fn).group(1)
        txt = strip_html(open(fn, encoding="utf-8", errors="replace").read())
        i = txt.find("Description/Agenda")
        j = txt.find("Notice of Special Accommodations")
        desc = txt[i + len("Description/Agenda"):j].strip() if i >= 0 else txt
        m = NOTICE_DATE.search(desc) or NOTICE_DATE_CRA.search(desc)
        mdate = ""
        if m and m.group(1).capitalize() in MONTHS:
            mdate = f"{m.group(3)}-{MONTHS[m.group(1).capitalize()]:02d}-{int(m.group(2)):02d}"
        override_note = ""
        if nid in NOTICE_DATE_OVERRIDES:
            newdate, why = NOTICE_DATE_OVERRIDES[nid]
            override_note = (f"notice {nid} prints meeting date {mdate or '?'} - "
                             f"{why}; reconciled to {newdate} (see NOTICE_DATE_OVERRIDES)")
            mdate = newdate
        if nid in NOTICE_NUM_OVERRIDES:
            override_note = (override_note + "; " if override_note else "") + \
                f"ordinance number reconciled from notice {nid} mis-print (see NOTICE_NUM_OVERRIDES)"
        if nid in NOTICE_NUM_OVERRIDES:
            out.setdefault(NOTICE_NUM_OVERRIDES[nid], []).append(
                {"notice_id": nid, "meeting_date": mdate,
                 "subject": desc[desc.find("as follows:") + 11:
                                 max(desc.find("A copy is available"), 0) or None].strip(" ;,."),
                 "desc": desc, "note": override_note})
            continue
        hits = list(NOTICE_ORD.finditer(desc))
        if not hits:
            unparsed.append((nid, desc[:120]))
            continue
        seen_here = set()
        for k, h in enumerate(hits):
            num = norm_num(h.group(1), h.group(2))
            if not num or num in seen_here:
                continue
            seen_here.add(num)
            end = hits[k + 1].start() if k + 1 < len(hits) else desc.find("A copy is available")
            if end < 0:
                end = len(desc)
            subject = desc[h.end():end].strip(" ;,.")
            out.setdefault(num, []).append(
                {"notice_id": nid, "meeting_date": mdate, "subject": subject,
                 "desc": desc, "note": override_note})
    return out, unparsed

# ---------- 3. minutes backbone ----------
CITE = re.compile(r"Ordinance\s*(?:No\.?|Number|#)?\s*#?\s*(\d{1,4})\s*[-–]\s*(\d{1,4})", re.I)

def load_motions():
    motions, cites, remapped = {}, {}, set()
    with open(VOTES) as f:
        for r in csv.DictReader(f):
            key = (r["date"], r["motion_no"])
            if key in motions:
                continue
            motions[key] = r
            for m in CITE.finditer(r["motion"]):
                num = norm_num(m.group(1), m.group(2))
                if not num:
                    continue
                if key in CITE_REMAPS and CITE_REMAPS[key][0] == num:
                    num = CITE_REMAPS[key][1]
                    remapped.add((key, num))
                cites.setdefault(num, []).append(key)
    return motions, cites, remapped

def load_minutes_urls():
    """minutes markdown path -> the source PDF URL, for within_source pointers."""
    out = {}
    p = os.path.join(HERE, "..", "meeting_minutes", "minutes_index.csv")
    with open(p) as f:
        for r in csv.DictReader(f):
            out[r["path"]] = r["source_url"]
    return out

def pick_motion(num, keys, motions, target_date):
    """Choose the enacting motion among candidates. Prefer the stated adoption
    date, then the ordinance's own series year, then the earliest. When several
    motions cite the same number (clerk typos exist: 2021-16, 2022-01, 2023-05,
    2025-18 each appear on two different motions), the rejected co-citations are
    listed in the note so the collision stays visible."""
    def collision_note(chosen):
        others = [k for k in keys if k != chosen]
        if not others:
            return ""
        return ("number also cited by motion(s) "
                + ", ".join(f"{d} #{n}" for d, n in sorted(others))
                + " with a different subject - probable clerk numbering typo; "
                  "kept the date-corroborated motion")
    if target_date:
        exact = [k for k in keys if k[0] == target_date]
        if exact:
            return exact[0], collision_note(exact[0])
    year = num[:4]
    same = sorted(k for k in keys if k[0][:4] == year)
    if same:
        note = collision_note(same[0]) if len(keys) > 1 else ""
        return same[0], note
    return None, f"cited only outside its series year ({', '.join(sorted(set(k[0] for k in keys)))})"

# ---------- subject match for medium/low ----------
STOP = set("the a an of to and for in on at by city herriman ordinance no amending amend adopting adopt approve approving code chapter title section regarding".split())

def tokens(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}

# A motion that only adjourns / recesses / convenes a session (or approves the agenda)
# can never be the motion that ENACTS an ordinance. Excluding it from the subject
# matcher stops generic words ("council", "utah") in a closed-session recess motion from
# out-scoring the real enacting motion — that is what mislinked 2022-36 to the
# 2022-08-24 closed-session recess (found 2026-07-29).
PROCEDURAL_RE = re.compile(
    r"\b(?:adjourn|recess|reconvene|convene\s+(?:in|into)\b|"
    r"(?:approve|adopt)\s+the\s+agenda)\b", re.I)

def subject_match(subject, mdate, motions):
    """Best keyword-overlap motion on mdate. Returns (key, score, runner_up)."""
    cand = [(k, r) for k, r in motions.items()
            if k[0] == mdate and not PROCEDURAL_RE.search(r["motion"] or "")]
    if not cand:
        return None, 0, 0
    st = tokens(subject)
    scored = sorted(((len(st & tokens(r["motion"])), k) for k, r in cand), reverse=True)
    best_s, best_k = scored[0]
    run = scored[1][0] if len(scored) > 1 else 0
    return best_k, best_s, run

# ---------- consent-agenda resolution ----------
# A council routinely ADOPTS an ordinance inside a consent agenda; the consent motion's
# text ("approve the consent agenda as written") carries no subject at all, so the
# subject matcher can never see it. The minutes ENUMERATE the consent items, so resolve
# against that list instead: link only when exactly ONE enumerated item matches the
# ordinance subject — by shared code citation (Title/Chapter/Section N) or >=2 shared
# subject tokens. Anything less stays honestly unlinked (low/none).
CONSENT_MOTION_RE = re.compile(r"\bconsent\s+(?:agenda|calendar)\b", re.I)
CODE_CITE_RE = re.compile(r"\b(title|chapter|section)\s+([0-9]+(?:[.\-][0-9]+)*)", re.I)

def _code_cites(s):
    return {(m.group(1).lower(), m.group(2)) for m in CODE_CITE_RE.finditer(s or "")}

def consent_items(md_relpath):
    """Enumerated consent-agenda items from a minutes markdown doc."""
    p = os.path.join(HERE, "..", "meeting_minutes", md_relpath or "")
    if not md_relpath or not os.path.exists(p):
        return []
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    items, inblock = [], False
    for ln in lines:
        if re.match(r"\s*\d+\.\s*Consent\s+Agenda\s*$", ln, re.I):
            inblock = True
            continue
        if inblock:
            m = re.match(r"\s*\d+\.\d+\.\s*(\S.*?)\s*$", ln)
            if m:
                items.append(m.group(1))
            elif ln.strip():
                break
    return items

def consent_match(subject, mdate, motions):
    """(key, item_text) of the consent-agenda motion on mdate whose enumerated item
    uniquely matches `subject`; (None, "") when the evidence is not unique."""
    cand = [(k, r) for k, r in motions.items()
            if k[0] == mdate and CONSENT_MOTION_RE.search(r["motion"] or "")]
    if len(cand) != 1:
        return None, ""
    key, row = cand[0]
    items = consent_items(row.get("source", ""))
    if not items:
        return None, ""
    sc, sk = tokens(subject), _code_cites(subject)
    hits = [it for it in items
            if (sk and _code_cites(it) & sk) or len(sc & tokens(it)) >= 2]
    if len(hits) != 1:
        return None, ""
    return key, hits[0]

# ---------- sidecar text ----------
def sidecar(num):
    p = os.path.join(HERE, "text", f"{num}.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8", errors="replace").read()
    return ""

ADOPT_CLAUSE = re.compile(
    r"(?:PASSED|ADOPTED)[^.]{0,120}?this\s+(\d{1,2})\S{0,2}\s+day of\s+(\w+),?\s+(\d{4})", re.I)

def pdf_adoption_date(txt):
    m = ADOPT_CLAUSE.search(txt)
    if m and m.group(2).capitalize() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2).capitalize()]:02d}-{int(m.group(1)):02d}"
    return ""

# scanned files (OCR'd) — from the extraction pass; regenerated by extract_text.py
def load_extraction_methods():
    p = os.path.join(HERE, "text", "_extraction_log.csv")
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            out[r["stem"]] = (r["format"], r["extraction_method"])
    return out

def main():
    archive = load_archive()
    notices, unparsed = load_notices()
    motions, cites, remapped = load_motions()
    methods = load_extraction_methods()
    global minutes_urls
    minutes_urls = load_minutes_urls()

    all_nums = sorted(set(archive) | set(notices) | set(cites))
    rows, gaps = [], []
    for num in all_nums:
        arc, nots, cit = archive.get(num), notices.get(num, []), cites.get(num, [])
        row = dict.fromkeys(CONTRACT + EXTRAS, "")
        row["ordinance_no"] = num
        row["retrieved_date"] = RETRIEVED
        notes = []

        # --- stated adoption date (PMN wins; the Recorder prints the meeting date)
        pmn_date = next((n["meeting_date"] for n in nots if n["meeting_date"]), "")
        pdf_txt = sidecar(num) if arc else ""
        pdf_date = pdf_adoption_date(pdf_txt) if pdf_txt else ""

        # --- motion linkage
        mkey, mnote = (None, "")
        if cit:
            mkey, mnote = pick_motion(num, cit, motions, pmn_date or pdf_date)
            if mnote:
                notes.append(mnote)

        independent = bool(arc or nots)
        if independent and mkey:
            stated = pmn_date or pdf_date
            if (mkey, num) in remapped:
                row["match_confidence"] = "medium"
                notes.append("motion prints a different number (minutes typo, see "
                             "CITE_REMAPS) - date+subject match, held at medium")
            elif stated and mkey[0] != stated:
                row["match_confidence"] = "medium"
                notes.append(f"number cited in motion but motion date {mkey[0]} != "
                             f"stated adoption date {stated} - downgraded from high")
            else:
                row["match_confidence"] = "high"
        elif independent and not mkey:
            target = pmn_date or pdf_date
            subj = (nots[0]["subject"] if nots else
                    re.sub(r"[_-]", " ", arc["filename"].split("_", 1)[1]) if arc else "")
            bk, s, run = subject_match(subj, target, motions) if target else (None, 0, 0)
            ck, citem = consent_match(subj, target, motions) if target else (None, "")
            if bk and s >= 2 and s > run:
                row["match_confidence"] = "medium"
                mkey = bk
                notes.append(f"subject-matched (score {s} vs {run}); number not cited in motion")
            elif ck:
                row["match_confidence"] = "medium"
                mkey = ck
                notes.append("adopted within the consent agenda; matched the enumerated "
                             f"consent item \"{citem[:80]}\"; number not cited in motion")
            elif bk is not None and target:
                # motions exist that day but subject evidence weak
                row["match_confidence"] = "low"
                row["matched_motion_date"] = target
                notes.append("adoption date has minutes but subject evidence weak/tied; "
                             "motion_no not attributed")
            else:
                row["match_confidence"] = "none"
                if target and target < "2020-01-01":
                    notes.append("below the 2020 minutes/vote floor")
                elif target:
                    notes.append(f"no extracted motion on {target}")
                else:
                    notes.append("no adoption date recovered; unmatched")
        elif not independent and cit:
            row["match_confidence"] = "within_source"

        if mkey and row["match_confidence"] in ("high", "medium", "within_source"):
            r = motions[mkey]
            row["matched_motion_date"], row["matched_motion_no"] = mkey
            row["result"] = r["result"]
            row["minutes_source"] = r["source"]

        # --- adoption_date + provenance
        if pmn_date:
            row["adoption_date"], row["adoption_date_source"] = pmn_date, "pmn-notice"
            if mkey and mkey[0] != pmn_date and row["match_confidence"] == "high":
                notes.append(f"motion date {mkey[0]} != notice-stated meeting {pmn_date}")
        elif mkey and mkey[0][:4] == num[:4] and (
                row["match_confidence"] in ("high", "within_source")
                or (mkey, num) in remapped):
            row["adoption_date"], row["adoption_date_source"] = mkey[0], "motion"
        elif pdf_date:
            row["adoption_date"], row["adoption_date_source"] = pdf_date, "pdf-clause"
        elif num in MANUAL_DATES:
            row["adoption_date"], row["adoption_date_source"] = MANUAL_DATES[num]
        elif row["match_confidence"] == "within_source":
            notes.append("adoption date left blank (motion cites the number outside "
                         "its series year - may amend/reference, not enact)")
        row["date"] = row["adoption_date"]

        # --- title / subject
        if nots:
            row["title"] = nots[0]["subject"][:200]
        elif arc:
            t = arc["filename"].split("_", 1)[1]
            t = re.sub(r"\.pdf$", "", t)
            t = re.sub(r"^ORD[ _-]*\d{4}[-_]\d{1,3}[A-Za-z]?[ _-]*", "", t)
            t = re.sub(r"^Z\d{4}-\d+[ _-]*", "", t)
            row["title"] = re.sub(r"([a-z])([A-Z])", r"\1 \2", t).replace("_", " ").strip()
        elif mkey:
            row["title"] = motions[mkey]["motion"][:200]

        # --- case number from the archive filename (Z2021-45 etc.)
        if arc:
            zc = re.search(r"(Z\d{4}-\d+)", arc["filename"])
            if zc:
                row["case_no"] = zc.group(1)

        # --- raw doc columns (PDF preferred over notice HTML)
        if arc:
            p = os.path.join("raw", "archive", f"{num}.pdf")
            row["path"] = p
            row["source_url"] = arc["source_url"]
            fmt, meth = methods.get(num, ("text", "pdftotext -layout"))
            row["format"], row["extraction_method"] = fmt, meth
        elif nots:
            nid = nots[0]["notice_id"]
            row["path"] = os.path.join("raw", "pmn", f"notice_{nid}.html")
            row["source_url"] = f"https://www.utah.gov/pmn/sitemap/notice/{nid}.html"
            row["format"] = "html"
            row["extraction_method"] = "html-strip (PMN Recorder adoption notice; summary only, not full ordinance text)"
        else:  # within_source
            row["format"] = "na"
            row["extraction_method"] = "reconstructed from meeting_minutes motion text (no independent document found)"
            if mkey:
                row["source_url"] = minutes_urls.get(motions[mkey]["source"], "")

        if nots:
            for n in nots:
                if n.get("note"):
                    notes.append(n["note"])
            row["pmn_notice_id"] = ";".join(n["notice_id"] for n in nots)
            row["pmn_notice_url"] = f"https://www.utah.gov/pmn/sitemap/notice/{nots[0]['notice_id']}.html"
            if arc:
                notes.append("PMN adoption notice + signed archive PDF both retained")

        # --- land_use
        basis = " ".join(filter(None, [
            row["title"], arc["filename"] if arc else "",
            motions[mkey]["motion"][:400] if mkey else "", pdf_txt[:1500]]))
        lu = classify_lu(basis)
        if lu == "yes" and NON_LU_KW.search(row["title"]) and not LU_KW.search(row["title"]):
            lu = "no"
        row["land_use"] = lu

        row["linkage_note"] = "; ".join(notes)
        rows.append(row)

    rows.sort(key=lambda r: (r["ordinance_no"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTRACT + EXTRAS)
        w.writeheader()
        w.writerows(rows)

    import collections
    c = collections.Counter(r["match_confidence"] for r in rows)
    lu = sum(1 for r in rows if r["land_use"] == "yes")
    print(f"{len(rows)} ordinances; confidence: {dict(c)}; land_use=yes: {lu}")
    if unparsed:
        print(f"NOTE: {len(unparsed)} fetched notices yielded no ordinance number:")
        for nid, head in unparsed:
            print("  ", nid, head[:100])

if __name__ == "__main__":
    main()
