"""Shared helpers for the Salt Lake County campaign-finance build (office normalization,
election-year proxy, donor-string construction). No side effects on import."""
import re

# County office category + seat normalization. Maps the many raw office labels (clerk
# legacy parenthetical labels + EasyVote OfficeName strings) to a stable (office, seat).
_ROMAN = {}

def normalize_office(raw):
    """(office_category, seat) from a raw office label. office_category is one of the
    10 county offices; seat carries the district/at-large designation ("" when none)."""
    s = (raw or "").strip()
    low = s.lower()
    seat = ""
    # council
    if "council" in low:
        m = re.search(r"district\s*#?\s*(\d+)", low) or re.search(r"council\s*#\s*(\d+)", low)
        if m:
            seat = "District " + m.group(1)
        else:
            am = re.search(r"at[- ]large\s*([abc])", low)
            if am:
                seat = "At-Large " + am.group(1).upper()
            elif "at-large" in low or "at large" in low:
                seat = "At-Large"
        return "County Council", seat
    if "mayor" in low:
        return "Mayor", ""
    if "sheriff" in low:
        return "Sheriff", ""
    if "attorney" in low:
        return "District Attorney", ""
    if "assessor" in low:
        return "Assessor", ""
    if "recorder" in low:
        return "Recorder", ""
    if "treasurer" in low:
        return "Treasurer", ""
    if "auditor" in low:
        return "Auditor", ""
    if "surveyor" in low:
        return "Surveyor", ""
    if "clerk" in low:
        return "Clerk", ""
    return s, seat  # unrecognized -> passthrough (should not happen for county scope)


COUNTY_OFFICE_SET = {"Mayor", "County Council", "Sheriff", "District Attorney",
                     "Assessor", "Recorder", "Treasurer", "Auditor", "Surveyor", "Clerk"}


def is_county_officename(officename):
    o = (officename or "")
    return o.startswith("Salt Lake County") or o.startswith("County Council")


def election_year_from_date(datestr):
    """Proxy: county offices elect in EVEN years. A report's cycle = its submission year
    rounded DOWN to the nearest even year (odd-year filings are overwhelmingly the
    dissolution/final/annual reports of the just-completed even-year race). Documented as
    a proxy in CLAUDE.md; the office is the strong join key, not the exact cycle."""
    y = _year(datestr)
    if y is None:
        return ""
    return str(y if y % 2 == 0 else y - 1)


def _year(datestr):
    if not datestr:
        return None
    m = re.search(r"(20\d\d)", datestr)
    if m:
        return int(m.group(1))
    # EasyVote datesubmitted mm/dd/yy
    m = re.match(r"\d{1,2}/\d{1,2}/(\d{2})$", datestr.strip())
    if m:
        return 2000 + int(m.group(1))
    return None


def easyvote_iso(datesubmitted):
    """mm/dd/yy -> YYYY-MM-DD (filing/submission date)."""
    if not datesubmitted:
        return ""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2})$", datesubmitted.strip())
    if m:
        mo, da, yy = m.groups()
        return f"20{yy}-{int(mo):02d}-{int(da):02d}"
    return ""


def contributor_raw(row):
    """Build a verbatim donor string from the itemized contribution row."""
    org = (row.get("ContributorOrganizationName") or "").strip()
    if org:
        return re.sub(r"\s+", " ", org)
    fn = (row.get("ContributorFirstName") or "").strip()
    ln = (row.get("ContributorLastName") or "").strip()
    name = re.sub(r"\s+", " ", (fn + " " + ln).strip())
    return name


def payee_raw(row):
    org = (row.get("PayeeOrganizationName") or "").strip()
    if org:
        return re.sub(r"\s+", " ", org)
    fn = (row.get("PayeeFirstName") or "").strip()
    ln = (row.get("PayeeLastName") or "").strip()
    return re.sub(r"\s+", " ", (fn + " " + ln).strip())


# --- globalassets channel (2015-2021 paper-filed county PDFs) -----------------------------
# The county "Financial Disclosure Report For a Candidate" cover carries a "Type of Report"
# block whose checkboxes sit under THREE printed headings. Those headings ARE the repo's
# filing_type vocabulary -- this is the form's own taxonomy, not an inferred one (verified at
# the page on dekeyzer 2020-04, dole 2016-YE, bradley 2018-amendment, guymon 2018-dissolution,
# burdick 2020-09; see _audits/2026-08-20-globalassets-harvest/report.md):
#
#     INTERIM REPORTS: (Required only during election years)
#         [ ] April 5   [ ] Seven days before a primary election
#         [ ] September 15   [ ] Seven days before a general election
#     YEAR-END REPORT:
#         [ ] January 31 of each year (Required by all open campaign committees)
#     FINAL / DISSOLUTION REPORT:
#         [ ] Final / Dissolution Report
#     Is this report an amendment?  [ ] Yes (date of report) ____   [ ] No
#
# The amendment tick is a SEPARATE question, never a report type.
REPORT_TYPE_BOXES = {
    "April 5": ("interim", "INTERIM REPORTS"),
    "Seven days before a primary election": ("interim", "INTERIM REPORTS"),
    "September 15": ("interim", "INTERIM REPORTS"),
    "Seven days before a general election": ("interim", "INTERIM REPORTS"),
    "Year-End (Jan 31)": ("year-end", "YEAR-END REPORT"),
    "Final / Dissolution Report": ("final", "FINAL / DISSOLUTION REPORT"),
    "Final/Dissolution": ("final", "FINAL / DISSOLUTION REPORT"),
}
# When two boxes are ticked together (Year-End AND Final/Dissolution is common) the report is
# the campaign's LAST one, so the final/dissolution class governs.
_FILING_TYPE_RANK = {"final": 3, "year-end": 2, "interim": 1}
# Recorded non-box markers in doc_report_type_boxes. A parenthetical "(...)" whole-value is the
# harvest's record that the document HAS no Type-of-Report block to read.
_NO_BOX_MARKERS = {"NO BOX CHECKED"}


def split_report_type_boxes(boxes):
    """The checked Type-of-Report box labels recorded verbatim in
    characterisation.csv:doc_report_type_boxes, as a list. Amendment clauses and explicit
    no-box markers are dropped (they are not report types). A whole-value parenthetical is a
    recorded absence and yields []. Raises ValueError on a label that is not a box on the form
    -- an unrecognised label must stop the build, never be silently classed."""
    s = (boxes or "").strip()
    if not s:
        return []
    if s.startswith("(") and s.endswith(")"):
        return []          # e.g. "(dissolution notice - no Type-of-Report box)"
    segs = [s]
    for sep in (";", "+", " AND "):
        segs = [p for seg in segs for p in seg.split(sep)]
    out = []
    for seg in (x.strip() for x in segs):
        if not seg or seg in _NO_BOX_MARKERS or seg.lower().startswith("amendment"):
            continue
        if seg not in REPORT_TYPE_BOXES:
            raise ValueError(
                f"unrecognised Type-of-Report box label {seg!r} in {boxes!r} -- add it to "
                "build_lib.REPORT_TYPE_BOXES only after reading it on the form")
        out.append(seg)
    return out


def filing_type_from_report_boxes(boxes):
    """filing_type (interim | year-end | final | '') from the verbatim checked-box label(s).
    '' means the document checks NO Type-of-Report box -- an honest blank, never a guess."""
    cls = [REPORT_TYPE_BOXES[b][0] for b in split_report_type_boxes(boxes)]
    if not cls:
        return ""
    return max(cls, key=lambda c: _FILING_TYPE_RANK[c])


def filing_type_basis(boxes):
    """Human-readable basis string for filing_type: the form heading(s) the class was read
    from, or the recorded reason the class is blank."""
    picked = split_report_type_boxes(boxes)
    if picked:
        parts = [f"{REPORT_TYPE_BOXES[b][1]}: {b}" for b in picked]
        s = " + ".join(parts)
        if len(picked) > 1:
            s += " (final/dissolution governs)" if any(
                REPORT_TYPE_BOXES[b][0] == "final" for b in picked) else ""
        return "checked box -- " + s
    s = (boxes or "").strip()
    if s.startswith("(") and s.endswith(")"):
        return "no Type-of-Report block to read -- " + s.strip("()")
    if not s:
        return "no Type-of-Report box checked"
    return "no Type-of-Report box checked -- " + s
