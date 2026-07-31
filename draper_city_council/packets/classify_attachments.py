#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Draper packets/index.csv.

PRIMARY_DOCS_PILOT_SPEC.md §5 / SKILL.md Source 7. Deterministic + rerunnable.
Adapted from sandy_city_council/packets/classify_attachments.py, but Draper has
NO matter table — the classifier keys purely on the row's own signals:
attachment `title`, `body`, `packet_kind`, `delivery`, plus an ordinance-number
→ land_use join against ../ordinances/index.csv (READ-ONLY) to land-use-scope
the era-C Council staff memos whose title only names an ordinance number.

Draper portal reality (see packets/CLAUDE.md — three delivery eras):
  - era C staff report  = `delivery=cloudfront_memo` (packet_kind=staff_report):
                          a born-digital ~60 KB MEMO PDF, the staff analysis. Its
                          `title` is the AGENDA-ITEM description (e.g. "Public
                          Hearing: Ordinance #1586"), NOT the words "staff report".
  - era A/B staff report= an EXHIBIT PDF titled "*_Staff_Report.pdf" (the Novus
                          coversheet, delivery=novus_coversheet, is thin boilerplate
                          — the analysis lives in the attached exhibit, so
                          coversheets are NOT classified).
  - DA / plan-amendment instruments ride as EXHIBIT PDFs ("Ord NNNN ... DA.pdf",
                          "Ordinance NNNN LUMA.pdf", "... Development Agreement.pdf").

Target classes (Sandy taxonomy; first match wins):
  staff_report          LAND-USE staff reports only (a budget/interlocal memo is NOT
                        staff_report). Two channels: era-C cloudfront memos scoped to
                        land use (PC body, or a land-use token, or an ordinance# that
                        joins to ordinances/ land_use=yes) + era-A/B/C exhibits whose
                        title carries a staff-report marker.
  member_memo           council-member proposal/amendment memos (the Sharkey class).
                        EMPTY for Draper 2020-26 — honest empty class (see AVAILABILITY.md).
  plan_amendment        GP / land-use-map amendment exhibit substance (LUMA ordinance
                        exhibits, MIHP, adopted station-area plans) — NOT the staff
                        report about them, NOT a DA.
  development_agreement DA/MDA instrument exhibits (the agreement text itself) — NOT a
                        staff report ABOUT a DA (those are staff_report).
Blank doc_class = honestly unclassified — NEVER force-bucketed.

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts + samples, write nothing
"""
import csv, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
ORD_INDEX = os.path.join(HERE, "..", "ordinances", "index.csv")

# --- regexes (all case-insensitive) --------------------------------------

# Administrative / ceremonial / procedural items that are never a land-use
# primary document, even when they ride an era-C memo.
RE_NONDOC = re.compile(
    r"\bminutes\b|recognition|recogniz|proclamation|\boath\b|swearing|"
    r"retirement|scholarship|eagle\s+scout|resignation|\bcanvass|"
    r"annual\s+planning\s+commiss|planning\s+commissioner\s+training|"
    r"2023\s+annual\s+planning|meeting\s+(?:dates|schedule)|"
    r"planning\s+commission\s+meeting\s+dates|coordination\s+between|"
    r"employee\s+(?:of|appreciation|recognition)", re.I)

# Staff-report document marker (title-level). Catches "Staff_Report", "Staff Report",
# the "Staf Report" typo, "PC Staff Report", "Planning Commission Report", "PC Report".
RE_STAFF_TOKEN = re.compile(
    r"staf{1,2}\s*_?\s*report|planning\s+commission\s+report|\bpc\s+report\b", re.I)

# Positive land-use tokens (scopes era-C memos to land use).
RE_LANDUSE = re.compile(
    r"rezone|zoning|zone\s*chang|zone\s*map|land\s*use|site\s*plan|subdivision|"
    r"\bplat\b|conditional\s+use|\bcup\b|master\s+area\s+plan|\bMAP\b\s+amend|"
    r"general\s+plan|annex|deannex|deviation|home\s+occupation|\bADU\b|\bI-ADU\b|"
    r"\bPUD\b|planned\s+unit|density|setback|variance|preliminary\s+(?:plat|subdivision)|"
    r"final\s+plat|concept\s+plan|development\s+agreement|text\s+amendment|overlay|"
    r"design\s+review|lot\s+line|boundary\s+line|street\s+vacat|station\s+area|"
    r"landscape\s+ordinance|tree\s+maintenance\s+ordinance|moderate\s+income\s+housing|"
    r"\bLUMA\b|\bZMA\b|\bZUMA\b|master\s+area\s+plan", re.I)

# Non-land-use exclusion guard for the "staff report" exhibit channel (belt &
# suspenders — 0 hits in the 2020-26 corpus, protects reruns as data grows).
RE_STAFF_NONLU = re.compile(
    r"\bbudget\b|salary|personnel|human\s+resource|\bHR\b|financ|\baudit\b|"
    r"compensation|pay\s+plan|fee\s+schedule|utility\s+rate|water\s+rate|"
    r"impact\s+fee|\bCDBG\b", re.I)

# Development-agreement instrument marker + the "this is ABOUT a DA, not the
# instrument" exclusion (staff report / presentation / minutes / memo / etc.).
RE_DA_INSTRUMENT = re.compile(r"development\s*agreement|\bMDA\b|\bDA\b", re.I)
RE_DA_NOT_INSTRUMENT = re.compile(
    r"staf|\breport\b|presentation|briefing|minutes|\bmemo\b|ecomment|notice|"
    r"recommendation|application|\bcomment\b|agenda", re.I)

# Plan-amendment substance marker + its exclusion (a staff report / notice /
# presentation ABOUT the amendment is not the amendment exhibit itself).
RE_PA_INSTRUMENT = re.compile(
    r"general\s+plan|land\s+use\s+map|\bLUMA\b|master\s+area\s+plan|"
    r"station\s+area\s+plan|moderate\s+income\s+housing\s+plan|\bMIHP\b", re.I)
RE_PA_NOT_INSTRUMENT = re.compile(
    r"staf|\breport\b|presentation|briefing|minutes|notice|ecomment|\bmemo\b|"
    r"application|\bcomment\b|agenda|recommendation", re.I)
# The amendment exhibit itself is either an adopting ORDINANCE PDF or a NAMED plan
# document. Requiring one of these keeps agenda-item slide decks (e.g. "5.a City
# Initiated ... LUMA and ZMA", a vicinity/aerial-map presentation) OUT of the class.
RE_PA_ORD_OR_NAMED = re.compile(
    r"\bordinance\b|\bord\b|\bMIHP\b|moderate\s+income\s+housing\s+plan|"
    r"station\s+area\s+plan", re.I)

RE_ORD = re.compile(r"ordinance", re.I)
RE_NUM = re.compile(r"(\d{3,4})")

EXT_COLS = ("doc_class", "fetch_status", "sha256", "text_path", "text_chars")


def load_ord_landuse():
    """{ordinance_no_digits: land_use} from ../ordinances/index.csv (READ-ONLY)."""
    m = {}
    if not os.path.exists(ORD_INDEX):
        return m
    with open(ORD_INDEX, newline="") as f:
        for r in csv.DictReader(f):
            no = re.sub(r"\D", "", r.get("ordinance_no", "") or "")
            if no:
                m[no] = (r.get("land_use", "") or "").strip().lower()
    return m


def ordinance_is_landuse(title, omap):
    """True if the title names an ordinance number that joins to land_use=yes."""
    if not RE_ORD.search(title):
        return False
    nums = RE_NUM.findall(title)
    return any(omap.get(n) == "yes" for n in nums)


def classify(row, omap):
    t = row.get("title", "") or ""
    kind = row.get("packet_kind", "")
    delivery = row.get("delivery", "")

    # only attachment-bearing rows are in scope (agenda / full_packet -> blank)
    if kind not in ("staff_report", "exhibit"):
        return ""
    if RE_NONDOC.search(t):
        return ""

    # 1. development_agreement — the instrument PDF, not a staff report about a DA
    if kind == "exhibit" and RE_DA_INSTRUMENT.search(t) \
            and not RE_DA_NOT_INSTRUMENT.search(t):
        return "development_agreement"

    # 2. staff_report
    #    (a) era-A/B/C exhibit explicitly titled as a staff report (land-use only)
    if kind == "exhibit" and RE_STAFF_TOKEN.search(t) \
            and not RE_STAFF_NONLU.search(t):
        return "staff_report"
    #    (b) era-C cloudfront memo, land-use scoped
    if delivery == "cloudfront_memo":
        if row.get("body") == "PlanningCommission":     # PC = land-use body
            return "staff_report"
        if RE_LANDUSE.search(t):
            return "staff_report"
        if ordinance_is_landuse(t, omap):
            return "staff_report"
        return ""   # Council admin memo (resolution / consent / non-LU ord) — honest blank

    # 3. plan_amendment — GP/LU-map amendment substance exhibit (adopting ordinance
    #    PDF or a named plan document; slide-deck presentations stay unclassified)
    if kind == "exhibit" and RE_PA_INSTRUMENT.search(t) \
            and RE_PA_ORD_OR_NAMED.search(t) \
            and not RE_PA_NOT_INSTRUMENT.search(t):
        return "plan_amendment"

    # 4. member_memo — empty for Draper (no member-authored proposal memos in packets)
    return ""


def main():
    dry = "--dry-run" in sys.argv
    omap = load_ord_landuse()

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in EXT_COLS:
        if col not in fields:
            fields.append(col)

    counts, samples = {}, {}
    for r in rows:
        for col in EXT_COLS:
            r.setdefault(col, "")
        r["doc_class"] = classify(r, omap)
        if r["doc_class"]:
            counts[r["doc_class"]] = counts.get(r["doc_class"], 0) + 1
            samples.setdefault(r["doc_class"], []).append(r["title"])

    inscope = sum(1 for r in rows if r["packet_kind"] in ("staff_report", "exhibit"))
    nclass = sum(counts.values())
    print(f"in-scope rows (staff_report|exhibit): {inscope}  classified: {nclass}  "
          f"unclassified: {inscope - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    if dry:
        for k in sorted(samples):
            print(f"\n--- {k} sample ---")
            for t in samples[k][:8]:
                print("   ", repr(t))
        print("\n(dry run — index.csv not written)")
        return

    tmp = INDEX + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, INDEX)
    print(f"wrote {INDEX} ({len(rows)} rows, {len(fields)} cols)")


if __name__ == "__main__":
    main()
