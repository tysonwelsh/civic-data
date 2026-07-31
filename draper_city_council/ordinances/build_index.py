#!/usr/bin/env python3
"""Build draper ordinances/index.csv — offline, idempotent.

Inputs (all local, read-only outside this dataset):
  raw/pmn/notice_*.html            226 PMN City Council (body 5555) notices verbatim
  raw/pmn/ord<num>_n<nid>_f<fid>.* attachment PDFs (mostly the 1-page Recorder
                                   adoption-summary; a few full/longer docs)
  text/_extraction_log.csv         per-stem format + extraction_method (extract_text.py)
  ../meeting_minutes/all_votes.csv the council-motion backbone (READ-ONLY)

Outputs:
  index.csv        SCHEMA_SPEC §9 ordinances contract + extras
                   (pmn_notice_id,pmn_notice_url,adoption_date_source,linkage_note)
  pmn_notices.csv  the raw PMN crawl catalog (all 226 notices incl. the 7
                   pre-adoption HEARING notices excluded from index rows)
  unrecovered.csv  series holes: numbers in the 2020+ range witnessed nowhere

Linkage rubric — see CLAUDE.md. Key documented city-error overrides:
  NOTICE_NUM_OVERRIDES  Recorder printed the wrong number in the notice body
  POSTED_DATE_RULE      several notices state the notice POSTING date (a
                        Wednesday, no council meeting) as the adoption date;
                        when council minutes exist 1-2 days before the stated
                        date with an approve-motion citing the number, and the
                        stated date equals the posting date, the motion date is
                        taken as the adoption date (linkage_note records both).
"""
import csv, glob, html as h, json, os, re, sys, datetime, collections

BASE = "/Users/tysonwelsh/civic-data/draper_city_council/ordinances"
RAW = BASE + "/raw/pmn"
VOTES = "/Users/tysonwelsh/civic-data/draper_city_council/meeting_minutes/all_votes.csv"
MINUTES_IDX = "/Users/tysonwelsh/civic-data/draper_city_council/meeting_minutes/minutes_index.csv"
RETRIEVED = "2026-07-13"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
MONTH_RE = "January|February|March|April|May|June|July|August|September|October|November|December"

# ---- documented Recorder-error overrides (sources kept verbatim) -----------
# 723375: body — Ord adopted 2021-12-14 "was erroneously numbered" #1514; the
#   Recorder states "The correct ordinance number is Ordinance #1520".
#   (#1514 itself was ALSO genuinely adopted that night — separate motion m5 —
#   so this notice belongs to 1520 only.)
# 947383: title + attachment = "Ordinance #1625" / Ord 1625.pdf, but the body
#   (and the attached PDF, which repeats it) prints the WRONG number (#1624)
#   and the WRONG date ("On September 17, 2024" — #1624 is the land-use text
#   amendment adopted that day per notice 941337). The SUBJECT is correct:
#   "vacating a city Right-of-Way located at approximately 984 E. Rosefield
#   Lane" matches the 2024-10-15 minutes agenda item 7.a for #1625 verbatim.
#   The 2024-10-15 council motion m3 (3-2 Pass — the mayoral tie-break, see
#   the city CLAUDE.md) establishes #1625 adopted 2024-10-15.
NOTICE_NUM_OVERRIDES = {"723375": "1520", "947383": "1625"}
NOTICE_DATE_OVERRIDES = {"947383": "2024-10-15"}
# 947383's attached PDF repeats the mis-copied body (headline #1625, body
# describes #1624) — the independent witness is imperfect, so the row is
# capped at medium even though number+date resolve cleanly.
NOTICE_CONF_CAP = {"947383": "medium"}
# minutes-side number corrections, (motion_date, printed_num) -> real num;
# rows matched through a remap are held at MEDIUM (imperfect number linkage).
CITE_REMAPS = {("2021-12-14", "1514"): "1520"}
# Recorder attached the WRONG PDF to these notices (byte-identical to the
# sibling ordinance's notice PDF, verified 2026-07-13): 785825 (#1556) carries
# #1555's PDF; 1007201 (#1661) carries #1662's. The raws are retained, but the
# row's document is the notice HTML (whose body text is correct).
ATTACHMENT_MISMATCH = {"785825", "1007201"}

def parse_date(s):
    m = re.search(r"(%s)\s+(\d{1,2}),?\s+(\d{4})" % MONTH_RE, s)
    if not m:
        return ""
    return "%s-%02d-%02d" % (m.group(3), MONTHS[m.group(1)], int(m.group(2)))

def text_of(fragment):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|li|tr|h\d)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = h.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*", "\n", t)
    return t.strip()

def parse_notice(path):
    nid = re.search(r"notice_(\d+)\.html", path).group(1)
    t = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r'<div class="notice_title"[^>]*>(.*?)</div>', t, re.S)
    title = text_of(m.group(1)) if m else ""
    i = t.find('class="agenda"')
    body = ""
    if i >= 0:
        seg = t[i:i + 10000]
        j = seg.find("Notice of Special Accommodations")
        body = text_of(seg[:j if j > 0 else 8000])
        body = re.sub(r'^class="agenda">\s*', "", body)
    # posted-on date (first line of the body)
    posted = parse_date(body[:200])
    atts = []
    for a in re.finditer(r'href="(/pmn/files/(\d+)\.(pdf|docx?|xlsx?))"[^>]*>\s*([^<]*)', t):
        atts.append({"url": "https://www.utah.gov" + a.group(1),
                     "fid": a.group(2), "ext": a.group(3),
                     "name": h.unescape(a.group(4)).strip()})
    seen = set()
    atts = [a for a in atts if not (a["fid"] in seen or seen.add(a["fid"]))]
    zone = title + "\n" + body
    nums = sorted(set(re.findall(r"[Oo]rdinances?\s*(?:[Nn]os?\.?\s*)?#?\s*(\d{3,4})", zone)))
    if re.search(r"Notice of (Ordinance )?Adoption|Adoption of Ordinance|"
                 r"(approved|adopted)( the)? Ordinance|was adopted by the Draper City Council|"
                 r"Council (adopted|approved)", zone, re.I):
        kind = "adoption"
    elif re.search(r"public hearing", body[:800], re.I):
        kind = "hearing"
    else:
        kind = "other"
    primary = ""
    m = (re.search(r"(?:[Aa]pproved|[Aa]dopted)(?: the)? Ordinance\s*(?:No\.?\s*)?#?\s*(\d{3,4})", body)
         or re.search(r"Ordinance\s*(?:No\.?\s*)?#?\s*(\d{3,4})[^.]{0,120}?was adopted by the Draper City Council", body)
         or re.search(r"Ordinance\s*#?\s*(\d{3,4})", title))
    if m:
        primary = m.group(1)
    elif len(nums) == 1:
        primary = nums[0]
    ad, ad_src = "", ""
    m = (re.search(r"On\s+((?:%s)\s+\d{1,2},?\s+\d{4})\s*,?\s+(?:the\s+)?Draper\s+City\s+Council\s+(?:[Aa]pproved|[Aa]dopted)" % MONTH_RE, body)
         or re.search(r"was adopted by the Draper City Council on\s+((?:%s)\s+\d{1,2},?\s+\d{4})" % MONTH_RE, body))
    if m:
        ad = parse_date(m.group(1)); ad_src = "pmn-notice"
    else:
        m = re.search(r"On\s+((?:%s)\s+\d{1,2})\s*,?\s+(?:the\s+)?Draper\s+City\s+Council\s+(?:[Aa]pproved|[Aa]dopted)" % MONTH_RE, body)
        if m and posted:
            mo, day = m.group(1).split()
            py, pm, pd = int(posted[:4]), int(posted[5:7]), int(posted[8:10])
            mm = MONTHS[mo]
            cand = datetime.date(py, mm, int(day))
            if cand > datetime.date(py, pm, pd):
                cand = datetime.date(py - 1, mm, int(day))
            ad = cand.isoformat(); ad_src = "pmn-notice+posted-year"
    # subject: the clause after "Ordinance #NNNN" in the adoption sentence
    subject = ""
    m = re.search(r"(?:[Aa]pproved|[Aa]dopted)(?: the)? Ordinance\s*(?:No\.?\s*)?#?\s*\d{3,4}\s*[,;]?\s*(.+?)(?:\.\s*The complete ordinance|\.\s*Published|$)", body, re.S)
    if m:
        subject = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".")[:300]
    if not subject:
        m = re.search(r"Ordinance\s*#?\s*\d{3,4}\s*[,;—-]?\s*(.+?)(?:\n|$)", title)
        if m:
            subject = re.sub(r"\s+", " ", m.group(1)).strip()[:300]
    return {"notice_id": nid, "title": title, "body": body, "posted": posted,
            "nums": nums, "primary": primary, "kind": kind,
            "adoption_date": ad, "adoption_date_source": ad_src,
            "subject": subject, "attachments": atts}

# ---- land-use convenience classifier (keyword filter, not a legal category) -
LU_PAT = re.compile(
    r"zoning map|land use map|land use and development code|rezon|zone change|"
    r"zoning text|subdivision|master area plan|development agreement|"
    r"conditional use|annex|boundary adjustment|general plan|"
    r"accessory dwelling|planned development|right[- ]of[- ]way vacat|"
    r"vacating a (city )?right[- ]of[- ]way|land use|zoning", re.I)
NON_LU_GUARD = re.compile(
    r"compensation schedule|fee schedule|water rates|alcohol|beer|"
    r"business licens|fireworks|parade route|election|budget adopt|"
    r"personnel|employment of relatives|committee", re.I)

def classify_land_use(*texts):
    t = " ".join(x for x in texts if x)
    if LU_PAT.search(t) and not (NON_LU_GUARD.search(t) and not
                                 re.search(r"zoning map|land use map|rezon|subdivision", t, re.I)):
        return "yes"
    return "no"

def main():
    notices = [parse_notice(p) for p in sorted(glob.glob(RAW + "/notice_*.html"))]
    for o in notices:
        if o["notice_id"] in NOTICE_NUM_OVERRIDES:
            o["primary"] = NOTICE_NUM_OVERRIDES[o["notice_id"]]
            o["num_overridden"] = True
        if o["notice_id"] in NOTICE_DATE_OVERRIDES:
            o["adoption_date"] = NOTICE_DATE_OVERRIDES[o["notice_id"]]
            o["adoption_date_source"] = "motion+attachment (notice body mis-copied)"

    # crawl catalog
    with open(BASE + "/pmn_notices.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["notice_id", "notice_url", "kind", "primary_ordinance_no",
                    "stated_adoption_date", "posted_date", "title_or_first_body_line"])
        for o in notices:
            first = (o["title"] if o["title"] and o["title"] != "Utah.gov"
                     else o["body"].split("\n")[1][:160] if "\n" in o["body"] else o["body"][:160])
            w.writerow([o["notice_id"],
                        "https://www.utah.gov/pmn/sitemap/notice/%s.html" % o["notice_id"],
                        o["kind"], o["primary"], o["adoption_date"], o["posted"], first])

    adoption = [o for o in notices if o["kind"] == "adoption"]

    # extraction log -> stem info
    xlog = {}
    lp = BASE + "/text/_extraction_log.csv"
    if os.path.exists(lp):
        for r in csv.DictReader(open(lp)):
            xlog[r["stem"]] = r

    # attachment files on disk, keyed by notice id
    disk = collections.defaultdict(list)
    for p in sorted(glob.glob(RAW + "/ord*_n*_f*.*")):
        m = re.search(r"_n(\d+)_f(\d+)\.", p)
        if m:
            disk[m.group(1)].append(os.path.basename(p))

    # ---- motion backbone ----------------------------------------------------
    motions = {}
    for r in csv.DictReader(open(VOTES)):
        motions.setdefault((r["date"], r["motion_no"]), r)
    minutes_dates = set()
    for r in csv.DictReader(open(MINUTES_IDX)):
        minutes_dates.add(r["date"])
    unrecovered_dates = set()
    unrec_path = os.path.dirname(MINUTES_IDX) + "/minutes_unrecovered.csv"
    if os.path.exists(unrec_path):
        for r in csv.DictReader(open(unrec_path)):
            unrecovered_dates.add(r["date"])

    num_list = re.compile(r"[Oo]rdinances?\s*(?:[Nn]os?\.?\s*)?(#?\s*\d{3,4}(?:(?:\s|,|and|&)+#?\s*\d{3,4})*)")
    cite = collections.defaultdict(list)          # num -> [(date, mno, row)]
    for (dt, mn), r in sorted(motions.items()):
        zone = r["motion"] + " " + r["title"]
        nums = set()
        for m in num_list.finditer(zone):
            nums.update(re.findall(r"\d{3,4}", m.group(1)))
        for n in nums:
            # CITE_REMAPS — the MINUTES printed a number the Recorder later
            # corrected: the 2021-12-14 m5 "approve Ordinance 1514" enacted the
            # ordinance the Recorder renumbered #1520 (notice 723375: "was
            # erroneously numbered. The correct ordinance number is Ordinance
            # #1520"). Without the remap, 1514 double-counts as a phantom
            # within_source ordinance and 1520 loses its motion.
            n = CITE_REMAPS.get((dt, n), n)
            cite[n].append((dt, mn, r))

    APPROVE = re.compile(r"\b(approv|adopt)", re.I)
    DENY = re.compile(r"\b(deny|denie|reject)", re.I)
    CONTINUE = re.compile(r"\b(continu|table|postpon|defer)", re.I)

    def head_of(row):
        # the operative clause: up to the seconder sentence (trailing narrative
        # in the motion field otherwise triggers false continue/deny hits)
        t = row["motion"]
        m = re.search(r"\bseconded\b|\bsecond(ed)? the motion\b", t, re.I)
        return t[:m.start()] if m else t[:250]

    VERB = re.compile(r"\b(?:moved|motioned|made a motion|motion(?: was made)?)\s+to\s+(?:re-?)?([a-z]+)", re.I)

    def operative_verb(row):
        # Draper grammar is consistent: "moved to <verb> ..." — classify by the
        # motion's operative verb, NOT by keywords anywhere in the clause
        # (subjects like "Use Tables Text Amendment" / "Notice of Continued
        # Item" otherwise false-positive as table/continue motions).
        m = VERB.search(head_of(row))
        return m.group(1).lower() if m else ""

    def is_approving(row):
        v = operative_verb(row)
        if v:
            return v.startswith(("approv", "adopt"))
        t = head_of(row)
        return bool(APPROVE.search(t)) and not DENY.search(t) and not CONTINUE.search(t)

    def is_denying(row):
        v = operative_verb(row)
        if v:
            return v.startswith(("deny", "denie", "reject"))
        return bool(DENY.search(head_of(row)))

    def passed(row):
        return "Pass" in row["result"] or "Unanimous" in row["result"]

    # ---- build rows: one per distinct adopted ordinance number --------------
    byord = collections.defaultdict(list)
    for o in adoption:
        byord[o["primary"]].append(o)

    HDR = ["ordinance_no", "adoption_date", "date", "title", "source_url",
           "retrieved_date", "format", "extraction_method", "path", "land_use",
           "result", "matched_motion_date", "matched_motion_no",
           "match_confidence", "pmn_notice_id", "pmn_notice_url",
           "adoption_date_source", "linkage_note"]
    rows = []
    stats = collections.Counter()
    for num in sorted(byord, key=lambda x: int(x)):
        group = sorted(byord[num], key=lambda o: o["posted"] or "9999")
        # primary notice = the one with an attachment if any, else first posted
        prim = next((o for o in group if disk.get(o["notice_id"])), group[0])
        extra_ids = [o["notice_id"] for o in group if o is not prim]
        ad = prim["adoption_date"]
        ad_src = prim["adoption_date_source"]
        note_parts = []
        if prim.get("num_overridden"):
            note_parts.append("Recorder number/body error corrected (see build_index.py NOTICE_NUM_OVERRIDES)")
        if extra_ids:
            note_parts.append("also noticed: " + ",".join(extra_ids))
        # motion match
        cands = cite.get(num, [])
        exact = [c for c in cands if c[0] == ad]
        mdate = mno = res = ""
        conf = "none"
        if exact:
            best = [c for c in exact if is_approving(c[2]) and passed(c[2])] or exact
            mdate, mno, mrow = best[-1]
            res = mrow["result"]
            conf = "high"
            if (mdate, num) in {(d, tgt) for (d, _), tgt in CITE_REMAPS.items()}:
                conf = "medium"
                note_parts.append("motion printed the erroneous number the Recorder later "
                                  "corrected (CITE_REMAPS) — number linkage imperfect")
            if len(exact) > 1:
                note_parts.append("multiple motions cite %s on %s (%s); kept the final approving motion" %
                                  (num, ad, ",".join(c[1] for c in exact)))
        elif cands and ad:
            # POSTED_DATE_RULE: stated date == posting date, no minutes that
            # day, approve-motion 1-2 days earlier -> Recorder posted-date
            # artifact; adoption date := motion date.
            near = [c for c in cands
                    if 0 < (datetime.date.fromisoformat(ad) -
                            datetime.date.fromisoformat(c[0])).days <= 2
                    and is_approving(c[2]) and passed(c[2])]
            if near and ad == prim["posted"] and ad not in minutes_dates:
                mdate, mno, mrow = near[-1]
                res = mrow["result"]
                note_parts.append("notice states the posting date %s as the adoption date; "
                                  "no council meeting that day — adoption date taken from the "
                                  "approving motion (POSTED_DATE_RULE)" % ad)
                ad = mdate
                ad_src = "motion (notice stated posting date)"
                conf = "high"
            else:
                mdate, mno, mrow = cands[-1]
                res = mrow["result"]
                conf = "medium"
                note_parts.append("motion date %s conflicts with notice-stated adoption date %s" %
                                  (mdate, ad))
        elif ad and ad in minutes_dates:
            conf = "low"
            mdate = ad
            note_parts.append("minutes exist for the stated adoption date but no extracted "
                              "motion cites #%s (consent/unattributed item)" % num)
        if conf == "none" and ad in unrecovered_dates:
            note_parts.append("council minutes for the stated adoption date are "
                              "unrecovered/withheld (see meeting_minutes/minutes_unrecovered.csv) "
                              "— no motion extractable; the notice independently witnesses "
                              "the lost meeting's action")
        # doc columns
        files = disk.get(prim["notice_id"], [])
        nurl = "https://www.utah.gov/pmn/sitemap/notice/%s.html" % prim["notice_id"]
        if prim["notice_id"] in ATTACHMENT_MISMATCH:
            files = []
            note_parts.append("PMN PDF attachment is a Recorder mis-upload of the sibling "
                              "ordinance's notice (byte-identical; retained in raw/ under this "
                              "notice's stem) — the notice HTML body is this row's witness")
        if files:
            path = "raw/pmn/" + files[0]
            stem = os.path.splitext(files[0])[0]
            att = next((a for a in prim["attachments"] if "_f" + a["fid"] + "." in files[0]), None)
            src = att["url"] if att else nurl
            fmt = xlog.get(stem, {}).get("format", "text")
            meth = xlog.get(stem, {}).get("extraction_method", "")
        else:
            path = "raw/pmn/notice_%s.html" % prim["notice_id"]
            src = nurl
            fmt = "html"
            meth = xlog.get("notice_" + prim["notice_id"], {}).get("extraction_method", "html-strip")
            note_parts.append("no PDF attachment on PMN — HTML notice only")
        if prim["notice_id"] in NOTICE_CONF_CAP and conf == "high":
            conf = NOTICE_CONF_CAP[prim["notice_id"]]
            note_parts.append("confidence capped: the notice/attachment body text was "
                              "mis-copied from the #1624 notice (headline + motion agree on the number)")
        title = ("Ordinance #%s" % num) + (" — " + prim["subject"] if prim["subject"] else "")
        lu = classify_land_use(title, prim["body"][:1500],
                               motions.get((mdate, mno), {}).get("motion", ""))
        rows.append(dict(zip(HDR, [num, ad, ad, title, src, RETRIEVED, fmt, meth,
                                   path, lu, res, mdate, mno, conf,
                                   prim["notice_id"], nurl, ad_src,
                                   "; ".join(note_parts)])))
        stats[conf] += 1

    # ---- within_source rows: adopted per the motions, no PMN notice ---------
    noticed = set(byord)
    for num in sorted(cite, key=lambda x: int(x)):
        if num in noticed or not (1300 <= int(num) <= 1900):
            continue
        approving = [c for c in cite[num] if is_approving(c[2]) and passed(c[2])]
        if not approving:
            stats["cited-not-adopted"] += 1
            continue
        mdate, mno, mrow = approving[-1]
        other = [c[0] for c in cite[num] if c[0] != mdate]
        note = "witnessed only by the citing council motion (no PMN notice)"
        if other:
            note += "; also discussed " + ",".join(sorted(set(other)))
        # subject from the motion text after the number (skipping co-cited
        # numbers, e.g. "approve Ordinance #1468 and 1469, Shadow Mountain ...")
        m = re.search(r"[Oo]rdinances?\s*(?:[Nn]os?\.?\s*)?#?\s*%s(?:\s*(?:,|and|&)\s*#?\s*\d{3,4})*\s*[,;]?\s*(.{10,200}?)(?:\.\s|$)" % num,
                      mrow["motion"])
        subject = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        if re.match(r"(?:and|&)\b", subject, re.I):
            subject = ""
        generic = mrow["title"].strip() in ("", "City Council", "City Council Meeting")
        title = ("Ordinance #%s" % num) + (
            " — " + subject if subject else
            ("" if generic else " (agenda item: %s)" % mrow["title"][:120]))
        lu = classify_land_use(title, mrow["motion"], mrow["title"])
        rows.append(dict(zip(HDR, [num, mdate, mdate, title,
                                   "../meeting_minutes/" + mrow["source"],
                                   RETRIEVED, "na", "", "", lu, mrow["result"],
                                   mdate, mno, "within_source", "", "",
                                   "motion", note])))
        stats["within_source"] += 1

    rows.sort(key=lambda r: (int(r["ordinance_no"]), r["adoption_date"]))
    with open(BASE + "/index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR)
        w.writeheader()
        w.writerows(rows)

    # ---- unrecovered: series holes in the 2020+ number range ----------------
    known = {int(r["ordinance_no"]) for r in rows}
    denied, cited_only = set(), set()
    for num in cite:
        if 1300 <= int(num) <= 1900 and int(num) not in known:
            if any(is_denying(c[2]) for c in cite[num]):
                denied.add(int(num))
            else:
                cited_only.add(int(num))
    lo_n = min(k for k in known if k >= 1410)  # 2020 floor era starts ~1410
    hi_n = max(known)
    holes = [n for n in range(lo_n, hi_n + 1)
             if n not in known and n not in denied and n not in cited_only]
    with open(BASE + "/unrecovered.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ordinance_no", "reason", "checked"])
        for n in holes:
            w.writerow([n, "number in the 2020+ series witnessed by no PMN notice and no "
                           "council motion (possibly unassigned, vetoed, or a numbering skip)",
                        RETRIEVED])
        for n in sorted(cited_only):
            w.writerow([n, "cited in council motions (continued/discussed) but no approving "
                           "motion extracted and no PMN adoption notice — adoption unwitnessed",
                        RETRIEVED])
        for n in sorted(denied):
            w.writerow([n, "proposed ordinance DENIED by council motion — never adopted "
                           "(not a gap; listed for series completeness)", RETRIEVED])

    print("index rows:", len(rows), dict(stats))
    print("land_use=yes:", sum(1 for r in rows if r["land_use"] == "yes"))
    print("2020+ rows:", sum(1 for r in rows if r["adoption_date"] >= "2020-01-01"))
    print("series holes:", holes); print("cited-only (no approving motion):", sorted(cited_only))
    print("denied numbers:", sorted(denied))

if __name__ == "__main__":
    main()
