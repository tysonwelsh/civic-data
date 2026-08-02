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
