#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Sandy packets/index.csv.

PRIMARY_DOCS_PILOT_SPEC.md §5. Deterministic + rerunnable: reads index.csv,
joins attachment rows to db/sandy.db legistar_matter (READ-ONLY, uri mode=ro),
assigns doc_class to the four attachment-borne pilot classes, rewrites
index.csv in place with a doc_class column (blank = honestly unclassified —
NEVER force-bucketed). Existing pipeline columns (text_path, sha256,
text_chars, fetch_status) are preserved if present.

Classes (first match wins):
  member_memo           council-member proposal memos / amendment text (the Sharkey class)
  staff_report          land-use staff reports (matter-scoped, not just the words
                        "staff report" in the title)
  plan_amendment        GP / land-use-map amendment exhibits (the "as shown in
                        Exhibit A" substance)
  development_agreement DA / MDA instruments + their amendments
                        (Sandy 2020-26: zero exist — honest empty class, see
                        AVAILABILITY.md)

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, re, sqlite3, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
DB = os.path.join(HERE, "..", "db", "sandy.db")

# --- council-member surnames (from sandy.db person/vote, council body; the
# roster is small and closed for 2020-26, so it is pinned here for determinism
# and so the classifier does not depend on db joins beyond legistar_matter).
SURNAMES = r"(?:sharkey|houseman|stroud|d.?sousa|dekeyzer|robinson|mecham|earl|coleman.?nicholl|christensen|zoltanski)"

# --- token regexes (all case-insensitive) ---------------------------------
RE_STAFF_REPORT = re.compile(
    r"staf{1,2}\s*_?\s*report"            # Staff Report (+ the 'Staf Report' typo)
    r"|planning\s+commission\s+report"    # PC recommendation report to Council
    r"|\bpc\s+report\b", re.I)
# land-use scope test on the MATTER title ([Community #N] is Sandy's land-use
# case-file convention; Planning Item matter_type is land-use by definition)
RE_MATTER_LANDUSE = re.compile(
    r"rezone|zone\s*change|zoning|conditional\s+use|site\s+plan|subdivision|"
    r"\bplat\b|general\s+plan|annex|land\s+use|variance|\bPUD\b|planned\s+unit|"
    r"accessory\s+apartment|land\s+development\s+code|title\s+21|"
    r"development\s+agreement|station\s+area|street\s+vacation|vacati|"
    r"sign\s+theme|\[community", re.I)
# land-use tokens in the ATTACHMENT title (fallback for rows with no matter join)
RE_ATT_LANDUSE = re.compile(
    r"\bGPA\b|\bREZ\b|rezone|\bzone\b|zoning|site\s+plan|subdivision|\bplat\b|"
    r"conditional\s+use|\bCUP\b|general\s+plan|annex", re.I)

RE_MEMBER_MATTER = re.compile(
    r"^(?:(?:first|second|third)\s+reading:\s*)?council\s+members?\b", re.I)
RE_MEMO_DOC = re.compile(r"\bmemo(?:randum)?\b|\bproposal\b|redline|\bamend", re.I)
RE_MEMBER_AMENDMENT = re.compile(r"^\s*" + SURNAMES + r"\b[^,]*\bamendment", re.I)
# member memos filed under non-member matters (e.g. a member's budget-proposal
# memo attached to the budget public-hearing matter): surname anywhere in the
# attachment title + an explicit memo/proposal token
RE_MEMBER_DOC_ANYWHERE = re.compile(
    r"\b" + SURNAMES + r"\b.*(?:\bmemo(?:randum)?\b|\bproposal\b)|"
    r"(?:\bmemo(?:randum)?\b|\bproposal\b).*\b" + SURNAMES + r"\b", re.I)

RE_GPA_EXCL_CODE = re.compile(r"land\s+development\s+code|title\s+21", re.I)
RE_PA_INCLUDE = re.compile(
    r"exhibit|proposed|\belement\b|implementation\s+plan|amendment|\bdraft\b", re.I)
RE_PA_EXCLUDE = re.compile(
    r"staff\s*report|minutes|notice|presentation|ecomment|survey|signed|"
    r"vicinity|application", re.I)

RE_DA_INSTRUMENT = re.compile(
    r"(?:master\s+)?development\s+agreement|\bMDA\b", re.I)
RE_DA_NOT_INSTRUMENT = re.compile(
    r"presentation|briefing|staff\s*report|\bmemo\b|minutes|ecomment", re.I)

RE_NEVER = re.compile(r"ecomment", re.I)  # portal links, not documents


def gpa_matter(mt_title: str) -> bool:
    """Matter is a GP / land-use-map AMENDMENT (not a code amendment, not the
    draft-GP chapter presentations which are class 3 / housing_plans)."""
    t = mt_title.lower()
    if RE_GPA_EXCL_CODE.search(t):
        return False
    if "land use map" in t and "amend" in t:
        return True
    return "general plan" in t and "amend" in t


def landuse_scope(matter_type: str, mt_title: str, att_title: str) -> bool:
    if matter_type == "Planning Item":
        return True
    if mt_title and RE_MATTER_LANDUSE.search(mt_title):
        return True
    if not mt_title and RE_ATT_LANDUSE.search(att_title):
        return True
    return False


def classify(att_title: str, matter_type: str, mt_title: str) -> str:
    t = att_title or ""
    if RE_NEVER.search(t):
        return ""
    # 1. member_memo — the Sharkey class
    if RE_MEMBER_AMENDMENT.search(t):
        return "member_memo"
    if RE_MEMBER_DOC_ANYWHERE.search(t) \
            and not re.search(r"signed|presentation", t, re.I):
        return "member_memo"
    if mt_title and RE_MEMBER_MATTER.search(mt_title) and RE_MEMO_DOC.search(t) \
            and not re.search(r"signed|presentation|city recorder|staff memorandum|legal memo",
                              t, re.I):
        return "member_memo"
    # 2. staff_report — land-use scoped
    if RE_STAFF_REPORT.search(t) and landuse_scope(matter_type, mt_title, t):
        return "staff_report"
    # 3. plan_amendment — substance docs of GP/land-use-map amendment matters
    if mt_title and gpa_matter(mt_title) \
            and RE_PA_INCLUDE.search(t) and not RE_PA_EXCLUDE.search(t):
        return "plan_amendment"
    # 4. development_agreement — the instrument itself, not briefings about DAs
    if RE_DA_INSTRUMENT.search(t) and not RE_DA_NOT_INSTRUMENT.search(t):
        return "development_agreement"
    return ""


def main():
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect("file:" + os.path.abspath(DB) + "?mode=ro", uri=True)
    matters = {str(r[0]): (r[1] or "", r[2] or "")
               for r in con.execute(
                   "SELECT legistar_matter_id, matter_type, title FROM legistar_matter")}
    con.close()

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
        if col not in fields:
            fields.append(col)

    counts = {}
    for r in rows:
        for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
            r.setdefault(col, "")
        if r["packet_kind"] != "staff_report_or_exhibit":
            r["doc_class"] = ""
            continue
        mtype, mtitle = matters.get(r["matter_id"], ("", ""))
        r["doc_class"] = classify(r["title"], mtype, mtitle)
        if r["doc_class"]:
            counts[r["doc_class"]] = counts.get(r["doc_class"], 0) + 1

    natt = sum(1 for r in rows if r["packet_kind"] == "staff_report_or_exhibit")
    nclass = sum(counts.values())
    print(f"attachments: {natt}  classified: {nclass}  unclassified: {natt - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    if dry:
        print("(dry run — index.csv not written)")
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
